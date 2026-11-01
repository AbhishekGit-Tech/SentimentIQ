import re
import nltk
from nltk.corpus import stopwords

try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")

# "not", "no" jaise words rakhne hain, kyunki inse sentiment badalta hai
_KEEP = {"not", "no", "nor", "never", "but", "very", "too"}
STOP_WORDS = set(stopwords.words("english")) - _KEEP

# "star/stars" hatao: log review mein khud "two stars" likh dete hain,
# model ko shortcut mil jata hai jo asli feedback mein nahi hoga
STOP_WORDS |= {"star", "stars"}


def clean_text(text):
    text = str(text).lower()
    text = text.replace("\\n", " ")            # Yelp ke literal \n
    text = re.sub(r"<.*?>", " ", text)         # HTML tags
    text = re.sub(r"won't", "will not", text)
    text = re.sub(r"can't", "can not", text)
    text = re.sub(r"n't\b", " not", text)      # don't -> do not
    text = re.sub(r"[^a-z\s]", " ", text)      # sirf letters
    words = [w for w in text.split() if w not in STOP_WORDS]
    return " ".join(words)