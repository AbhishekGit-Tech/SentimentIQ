from django.db import transaction
from django.utils import timezone

from analyzer import analyze_many    # type: ignore[reportMissingImports]       # ml/src/analyzer.py (settings mein path add kiya tha)
from .models import AspectResult, Feedback, Upload

BATCH_SIZE = 500


def _store(upload, rows):
    """rows = [(text, datetime)] -> analyze karo, DB mein save karo, results return karo."""
    all_results = []
    for start in range(0, len(rows), BATCH_SIZE):
        chunk = rows[start:start + BATCH_SIZE]
        results = analyze_many([text for text, _ in chunk])

        feedbacks = [
            Feedback(upload=upload, text=text, feedback_date=date,
                     overall_sentiment=res["overall"], confidence=res["confidence"])
            for (text, date), res in zip(chunk, results)
        ]
        Feedback.objects.bulk_create(feedbacks)

        aspect_rows = [
            AspectResult(feedback=fb, segment_text=seg["text"], aspect=aspect,
                         sentiment=seg["sentiment"], confidence=seg["confidence"])
            for fb, res in zip(feedbacks, results)
            for seg in res["segments"]
            for aspect in seg["aspects"]
        ]
        AspectResult.objects.bulk_create(aspect_rows, batch_size=1000)
        all_results.extend(results)
    return all_results


@transaction.atomic
def analyze_csv_rows(user, name, rows):
    upload = Upload.objects.create(user=user, name=name, source="csv")
    _store(upload, rows)
    return upload


@transaction.atomic
def analyze_manual(user, text):
    upload = (Upload.objects.filter(user=user, source="manual").first()
              or Upload.objects.create(user=user, name="Manual entries", source="manual"))
    results = _store(upload, [(text, timezone.now())])
    return upload, results[0]