import re
from aspects import find_aspects
from text_cleaning import clean_text

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+|\n+")
_CONTRAST_SPLIT = re.compile(r"\b(?:but|however|although|though|whereas)\b", re.IGNORECASE)


def _refine(segment):
    """'and' / comma pe tabhi todo jab dono taraf alag aspect aur poora clause ho."""
    pieces = [p.strip() for p in re.split(r",|\band\b", segment, flags=re.IGNORECASE) if p.strip()]
    if len(pieces) < 2:
        return [segment]
    aspect_sets = [frozenset(find_aspects(p)) for p in pieces]
    enough_words = all(len(p.split()) >= 3 for p in pieces)
    all_have_aspect = all(aspect_sets)
    different = len(set(aspect_sets)) > 1
    if enough_words and all_have_aspect and different:
        return pieces
    return [segment]


def split_feedback(text):
    segments = []
    for sentence in _SENTENCE_SPLIT.split(str(text)):
        for clause in _CONTRAST_SPLIT.split(sentence):
            clause = clause.strip(" ,-:")
            if clause:
                segments.extend(_refine(clause))
    return [s for s in segments if clean_text(s).strip()]