from pathlib import Path
import joblib

from aspects import detect_aspects
from splitter import split_feedback
from text_cleaning import clean_text

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"      # = ml/models
TFIDF_FILE = "tfidf_v2.pkl"
MODEL_FILE = "sentiment_lr_v2.pkl"

_tfidf = None
_model = None


def _load():
    """Model sirf pehli baar disk se load hota hai, phir memory mein rehta hai."""
    global _tfidf, _model
    if _model is None:
        _tfidf = joblib.load(MODEL_DIR / TFIDF_FILE)
        _model = joblib.load(MODEL_DIR / MODEL_FILE)
    return _tfidf, _model


def _predict(texts):
    """Raw texts ki list -> [(label, confidence), ...] (ek hi batch mein, tez)."""
    tfidf, model = _load()
    cleaned = [clean_text(t) for t in texts]
    out = [("Neutral", 0.0)] * len(texts)
    keep = [i for i, c in enumerate(cleaned) if c.strip()]
    if keep:
        probs = model.predict_proba(tfidf.transform([cleaned[i] for i in keep]))
        best = probs.argmax(axis=1)
        for row, i in enumerate(keep):
            out[i] = (str(model.classes_[best[row]]), float(probs[row, best[row]]))
    return out


def analyze_many(texts):
    """Hazaaron feedbacks ek saath analyze karne ke liye (CSV upload yahi use karega)."""
    texts = [str(t) for t in texts]
    overall = _predict(texts)

    seg_texts, owners = [], []
    for i, t in enumerate(texts):
        for seg in split_feedback(t):
            seg_texts.append(seg)
            owners.append(i)
    seg_pred = _predict(seg_texts) if seg_texts else []

    results = [
        {"text": t, "overall": o[0], "confidence": o[1], "segments": []}
        for t, o in zip(texts, overall)
    ]
    for seg, owner, (label, conf) in zip(seg_texts, owners, seg_pred):
        results[owner]["segments"].append({
            "text": seg,
            "sentiment": label,
            "confidence": conf,
            "aspects": detect_aspects(seg),
        })
    return results


def analyze_one(text):
    return analyze_many([text])[0]


if __name__ == "__main__":
    samples = [
        "Phone camera is amazing but battery is terrible",
        "Delivery was very late and the packaging was damaged. Support never replied.",
        "The room was dirty and the staff was rude, but the food was delicious",
        "Staff was helpful and polite",
        "Camera and battery are both terrible",
        "Great product",
    ]
    for r in analyze_many(samples):
        print(f"\n{r['text']}")
        print(f"  Overall: {r['overall']} ({r['confidence']:.0%})")
        for s in r["segments"]:
            print(f"   - [{', '.join(s['aspects'])}] {s['sentiment']} ({s['confidence']:.0%})  <- {s['text']}")