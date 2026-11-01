from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .csv_utils import (DATE_HINTS, MAX_ROWS, TEXT_HINTS, fallback_text_column,
                        pick_column, prepare_rows, read_csv_safely)
from .forms import CSVUploadForm, ManualFeedbackForm
from .models import Upload
from .services import analyze_csv_rows, analyze_manual
import random


@login_required
def upload_list(request):
    uploads = request.user.uploads.annotate(n=Count("feedbacks"))
    return render(request, "feedback/upload_list.html", {"uploads": uploads})


@login_required
def manual_feedback(request):
    result = None
    if request.method == "POST":
        form = ManualFeedbackForm(request.POST)
        if form.is_valid():
            _, result = analyze_manual(request.user, form.cleaned_data["text"])
            form = ManualFeedbackForm()
    else:
        form = ManualFeedbackForm()
    return render(request, "feedback/manual.html", {"form": form, "result": result})


@login_required
def csv_upload(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data["file"]
            try:
                df = read_csv_safely(f)
                text_col = (pick_column(df, form.cleaned_data["text_column"], TEXT_HINTS)
                            or fallback_text_column(df))
                if text_col is None:
                    raise ValueError("Could not find the feedback column. Type its name in 'Feedback column'.")
                date_col = pick_column(df, form.cleaned_data["date_column"], DATE_HINTS)

                rows, date_used = prepare_rows(df, text_col, date_col)
                if not rows:
                    raise ValueError("No usable feedback text found in that column.")
                total_rows = len(rows)
                sampled = total_rows > MAX_ROWS
                if sampled:
                    keep = sorted(random.Random(42).sample(range(total_rows), MAX_ROWS))
                    rows = [rows[i] for i in keep]

                upload = analyze_csv_rows(request.user, f.name, rows)
            except FileNotFoundError:
                form.add_error(None, "ML model files not found in ml/models. Check tfidf_v2.pkl and sentiment_lr_v2.pkl.")
            except ValueError as exc:
                form.add_error(None, str(exc))
            else:
                msg = f"Analysed {len(rows)} feedbacks from column '{text_col}'."
                if sampled:
                    msg += f" The file had {total_rows} rows, so a random sample of {MAX_ROWS} was analysed."
                msg += " Dates taken from the file." if date_used else " No usable date column, so upload time was used."
                messages.success(request, msg)
                return redirect("upload_detail", pk=upload.pk)
    else:
        form = CSVUploadForm()
    return render(request, "feedback/csv_upload.html", {"form": form, "max_rows": MAX_ROWS})


@login_required
def upload_detail(request, pk):
    upload = get_object_or_404(Upload, pk=pk, user=request.user)   # sirf apna data
    counts = {r["overall_sentiment"]: r["n"]
              for r in upload.feedbacks.values("overall_sentiment").annotate(n=Count("id"))}
    total = sum(counts.values())
    summary = [{"label": label,
                "count": counts.get(label, 0),
                "pct": round(100 * counts.get(label, 0) / total) if total else 0}
               for label in ("Positive", "Neutral", "Negative")]

    feedbacks = upload.feedbacks.prefetch_related("aspect_results").order_by("-feedback_date", "-id")
    page = Paginator(feedbacks, 50).get_page(request.GET.get("page"))
    return render(request, "feedback/upload_detail.html",
                  {"upload": upload, "summary": summary, "page": page, "total": total})


@login_required
@require_POST
def upload_delete(request, pk):
    upload = get_object_or_404(Upload, pk=pk, user=request.user)
    upload.delete()
    messages.success(request, "Upload deleted.")
    return redirect("upload_list")