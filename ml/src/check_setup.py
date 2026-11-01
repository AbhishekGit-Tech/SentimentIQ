"""Project health check. Project root se chalao:  python ml/src/check_setup.py"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "ml" / "src"))


def tag(ok):
    return "OK     " if ok else "MISSING"


print("Python :", sys.version.split()[0])
print("Root   :", ROOT)
print()

for pkg in ["django", "pandas", "numpy", "sklearn", "joblib", "nltk", "datasets"]:
    try:
        mod = __import__(pkg)
        print(tag(True), "package", pkg, getattr(mod, "__version__", ""))
    except Exception as e:
        print(tag(False), "package", pkg, f"({e})")

print()
for rel in ["ml/data/Reviews.csv", "ml/data/yelp/yelp_150k.csv", "ml/data/electronics",
            "ml/src/text_cleaning.py", "ml/models/tfidf_v2.pkl", "ml/models/sentiment_lr_v2.pkl"]:
    print(tag((ROOT / rel).exists()), rel)

reviews = ROOT / "ml/data/Reviews.csv"
if reviews.exists():
    print("\nReviews.csv zip hai?", zipfile.is_zipfile(reviews))

print("\nElectronics CSVs:")
for p in sorted((ROOT / "ml/data/electronics").glob("*.csv")):
    print("  ", p.name, f"{p.stat().st_size / 1e6:.1f} MB")

print()
try:
    from text_cleaning import clean_text
    print(tag(True), "text_cleaning ->", clean_text("I can't recommend this, NOT good!<br />"))
except Exception as e:
    print("PROBLEM text_cleaning:", e)

try:
    import joblib
    joblib.load(ROOT / "ml/models/sentiment_lr_v2.pkl")
    print(tag(True), "model load")
except Exception as e:
    print("PROBLEM model load:", e)