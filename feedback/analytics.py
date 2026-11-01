from collections import defaultdict

from django.db.models import Count, Max, Min
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek

from .models import AspectResult, Feedback

SENTIMENTS = ["Positive", "Neutral", "Negative"]
ISSUE_MIN_CONFIDENCE = 0.5     # Top Issues mein sirf itne+ confidence wale negative segments
TOP_N = 8


def _pct(part, total):
    return round(100 * part / total, 1) if total else 0.0


def build_dashboard(user, upload_id=None, start=None, end=None, aspect=None):
    fb = Feedback.objects.filter(upload__user=user)          # sirf is user ka data
    if upload_id:
        fb = fb.filter(upload_id=upload_id)
    if start:
        fb = fb.filter(feedback_date__date__gte=start)
    if end:
        fb = fb.filter(feedback_date__date__lte=end)
    if aspect:
        fb = fb.filter(id__in=AspectResult.objects.filter(aspect=aspect).values("feedback_id"))

    total = fb.count()
    if total == 0:
        return {"total": 0}

    # 1) Sentiment split
    counts = {r["overall_sentiment"]: r["n"]
              for r in fb.values("overall_sentiment").annotate(n=Count("id"))}
    sentiment = [{"label": s, "count": counts.get(s, 0), "pct": _pct(counts.get(s, 0), total)}
                 for s in SENTIMENTS]

    # 2) Aspect-wise sentiment
    ar = AspectResult.objects.filter(feedback_id__in=fb.values("id")).exclude(aspect="General")

    per_aspect = defaultdict(lambda: {s: 0 for s in SENTIMENTS})
    for r in ar.values("aspect", "sentiment").annotate(n=Count("feedback", distinct=True)):
        per_aspect[r["aspect"]][r["sentiment"]] = r["n"]
    ranked = sorted(per_aspect.items(), key=lambda kv: -sum(kv[1].values()))[:TOP_N]
    aspects = [{"aspect": name, **c, "total": sum(c.values())} for name, c in ranked]

    # 3) Top issues (negative mentions ka share)
    issues_all = list(
        ar.filter(sentiment="Negative", confidence__gte=ISSUE_MIN_CONFIDENCE)
        .values("aspect").annotate(n=Count("feedback", distinct=True)).order_by("-n")
    )
    issue_total = sum(r["n"] for r in issues_all)
    issues = [{"aspect": r["aspect"], "count": r["n"],
               "pct": _pct(r["n"], issue_total), "width": round(100 * r["n"] / issue_total)}
              for r in issues_all[:TOP_N]]

    # Phase 9: Top issue ke 3 sabse confident negative comments
    issue_examples = []
    if issues:
        seen = set()
        top_comments = (ar.filter(aspect=issues[0]["aspect"], sentiment="Negative",
                                  confidence__gte=ISSUE_MIN_CONFIDENCE)
                        .order_by("-confidence")
                        .values_list("segment_text", flat=True)[:20])
        for text in top_comments:
            key = text.strip().lower()
            if key not in seen:
                seen.add(key)
                issue_examples.append(text.strip())
            if len(issue_examples) == 3:
                break

    # 4) Trend
    span = fb.aggregate(first=Min("feedback_date"), last=Max("feedback_date"))
    days = (span["last"] - span["first"]).days
    if days <= 62:
        trunc, fmt = TruncDate, "%d %b"
    elif days <= 400:
        trunc, fmt = TruncWeek, "%d %b"
    else:
        trunc, fmt = TruncMonth, "%b %Y"

    rows = (fb.annotate(period=trunc("feedback_date"))
              .values("period", "overall_sentiment")
              .annotate(n=Count("id"))
              .order_by("period"))
    periods = {}
    for r in rows:
        bucket = periods.setdefault(r["period"], {s: 0 for s in SENTIMENTS})
        bucket[r["overall_sentiment"]] += r["n"]

    labels, series = [], {s: [] for s in SENTIMENTS}
    for period in sorted(periods):
        c = periods[period]
        t = sum(c.values())
        labels.append(period.strftime(fmt))
        for s in SENTIMENTS:
            series[s].append(_pct(c[s], t))

    # Negative feedback badh raha hai ya ghat raha hai (pehla aadha vs doosra aadha)
    trend_delta = None
    if len(periods) >= 2:
        keys = sorted(periods)
        mid = len(keys) // 2

        def neg_pct(ks):
            tot = sum(sum(periods[k].values()) for k in ks)
            return _pct(sum(periods[k]["Negative"] for k in ks), tot)

        trend_delta = round(neg_pct(keys[mid:]) - neg_pct(keys[:mid]), 1)

    return {
        "total": total,
        "sentiment": sentiment,
        "issues": issues,
        "issue_examples": issue_examples,
        "aspects": aspects,
        "trend_delta": trend_delta,
        "has_trend": len(labels) > 1,
        "chart": {
            "sentiment": {"labels": SENTIMENTS, "counts": [x["count"] for x in sentiment]},
            "aspects": {"labels": [a["aspect"] for a in aspects],
                        **{s: [a[s] for a in aspects] for s in SENTIMENTS}},
            "trend": {"labels": labels, **series},
        },
    }