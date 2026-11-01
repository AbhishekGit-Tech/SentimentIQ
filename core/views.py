from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from feedback.analytics import build_dashboard
from feedback.models import AspectResult

from feedback.insights import build_insights

def home(request):
    return render(request, "core/home.html")


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


@login_required
def dashboard(request):
    upload_id = request.GET.get("upload", "")
    if not upload_id.isdigit():
        upload_id = ""
    aspect = request.GET.get("aspect", "")
    start_raw = request.GET.get("start", "")
    end_raw = request.GET.get("end", "")

    data = build_dashboard(
        request.user,
        upload_id=int(upload_id) if upload_id else None,
        start=_parse_date(start_raw),
        end=_parse_date(end_raw),
        aspect=aspect or None,
    )

    insights = build_insights(data)
    aspect_options = (AspectResult.objects.filter(feedback__upload__user=request.user)
                      .exclude(aspect="General")
                      .values_list("aspect", flat=True).distinct().order_by("aspect"))

    context = {
        "data": data,
        "insights": insights,
        "uploads": request.user.uploads.all(),
        "aspect_options": aspect_options,
        "filters": {"upload": upload_id, "aspect": aspect, "start": start_raw, "end": end_raw},
    }
    return render(request, "core/dashboard.html", context)