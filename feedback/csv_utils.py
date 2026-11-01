import pandas as pd

MAX_FILE_MB = 25
MAX_ROWS = 5000
MAX_TEXT_CHARS = 2000

TEXT_HINTS = ["text", "review", "feedback", "comment", "comments", "content", "message", "description", "body"]
DATE_HINTS = ["date", "time", "created", "timestamp", "posted"]


def read_csv_safely(uploaded_file):
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding, low_memory=False)
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty.")
        except pd.errors.ParserError:
            raise ValueError("Could not read this CSV (the format looks broken).")
    else:
        raise ValueError("Could not work out the file encoding.")
    if df.empty:
        raise ValueError("The CSV has no rows.")
    return df


def pick_column(df, requested, hints):
    """User ne naam diya to wahi, warna hints se guess, warna None."""
    lowered = [(col, str(col).strip().lower()) for col in df.columns]
    if requested:
        for col, low in lowered:
            if low == requested.strip().lower():
                return col
        raise ValueError(f"Column '{requested}' not found. Available: {', '.join(str(c) for c in df.columns)}")
    for hint in hints:                      # pehle exact naam
        for col, low in lowered:
            if low == hint:
                return col
    for hint in hints:                      # phir 'contains'
        for col, low in lowered:
            if hint in low:
                return col
    return None


def fallback_text_column(df):
    """Naam se na mile to sabse lambe text wala column."""
    best, best_len = None, 0
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            avg = df[col].dropna().astype(str).str.len().mean()
            if avg > best_len:
                best, best_len = col, avg
    return best


def prepare_rows(df, text_col, date_col=None):
    """-> (rows, date_used). rows = [(text, datetime), ...]"""
    from django.utils import timezone

    df = df.dropna(subset=[text_col])
    texts = df[text_col].astype(str).str.strip().str.slice(0, MAX_TEXT_CHARS)

    date_used = False
    parsed = pd.Series(pd.NaT, index=df.index)
    if date_col:
        col = df[date_col]
        if pd.api.types.is_numeric_dtype(col):
            candidate = pd.to_datetime(col, unit="s", errors="coerce", utc=True)   # unix seconds
        else:
            candidate = pd.to_datetime(col, errors="coerce", utc=True, format="mixed")
        # sanity check: zyadatar valid hon aur saal 1995 ke baad ke hon
        if candidate.notna().mean() >= 0.5 and candidate.dropna().dt.year.median() >= 1995:
            parsed, date_used = candidate, True

    now = timezone.now()
    rows = []
    for text, ts in zip(texts, parsed):
        if text:
            rows.append((text, now if pd.isna(ts) else ts.to_pydatetime()))
    return rows, date_used