import re

# Aspect -> keywords. Ye dictionary tumhari hai, naye domain ke liye words yahan add karte jao.
ASPECTS = {
    "Delivery": ["delivery", "delivered", "deliver", "shipping", "shipped", "shipment", "courier",
                 "arrived", "arrive", "late", "delay", "delayed", "dispatch", "dispatched",
                 "tracking", "parcel"],
    "Packaging": ["packaging", "packaged", "packed", "packing", "sealed", "wrapped", "box"],
    "Service & Support": ["service", "support", "helpline", "refund", "refunded", "replacement",
                          "replaced", "warranty", "complaint", "representative", "agent", "resolved"],
    "Staff": ["staff", "waiter", "waitress", "receptionist", "host", "manager", "employee",
              "employees", "behaviour", "behavior", "rude", "polite", "courteous"],
    "Price": ["price", "prices", "pricing", "cost", "costly", "expensive", "cheap", "overpriced",
              "affordable", "pricey", "value", "money", "worth", "bill", "budget"],
    "Quality": ["quality", "durable", "durability", "build", "material", "broke", "broken",
                "defective", "flimsy", "sturdy", "damaged", "faulty"],
    "Battery": ["battery", "batteries", "charge", "charging", "charged", "backup", "drain",
                "drains", "drained"],
    "Camera": ["camera", "cameras", "photo", "picture", "selfie", "lens", "zoom"],
    "Performance": ["performance", "lag", "laggy", "lagging", "hang", "hangs", "hanging",
                    "processor", "heating", "overheating", "heats", "speed", "smooth"],
    "Display": ["screen", "display", "brightness", "resolution", "touch", "amoled"],
    "Sound": ["sound", "speaker", "speakers", "audio", "volume", "bass", "microphone", "mic"],
    "Food": ["food", "taste", "tasty", "flavor", "flavour", "delicious", "dish", "dishes", "meal",
             "menu", "portion", "fresh", "bland", "cooked", "dinner", "lunch", "breakfast"],
    "Room": ["room", "rooms", "bed", "bathroom", "bedding", "suite", "view", "pool"],
    "Cleanliness": ["clean", "cleanliness", "dirty", "hygiene", "hygienic", "smell", "smelly",
                    "dust", "dusty", "stain", "stains", "filthy", "spotless"],
    "Ambience": ["ambience", "ambiance", "atmosphere", "music", "decor", "vibe", "noisy", "noise",
                 "crowded", "seating", "cozy"],
    "Location": ["location", "nearby", "parking", "distance", "walkable"],
    "Teaching": ["teacher", "teachers", "professor", "faculty", "lecture", "lectures", "teaching",
                 "curriculum", "syllabus"],
    "App/Website": ["app", "website", "login", "interface", "crash", "crashes", "bug", "bugs"],
    "Waiting Time": ["wait", "waiting", "waited", "queue", "queues"],
}

_KEYWORD_MAP = {}
for _aspect, _words in ASPECTS.items():
    for _w in _words:
        _KEYWORD_MAP.setdefault(_w, []).append(_aspect)


def _tokens(text):
    words = re.findall(r"[a-z]+", text.lower())
    tokens = set(words)
    for w in words:
        if len(w) > 3 and w.endswith("s"):
            tokens.add(w[:-1])          # photos -> photo
    return tokens


def find_aspects(text):
    """Jo aspects mile unki list (kuch na mile to khaali list)."""
    found = set()
    for tok in _tokens(text):
        found.update(_KEYWORD_MAP.get(tok, []))
    return sorted(found)


def detect_aspects(text):
    """Kuch na mile to 'General'."""
    return find_aspects(text) or ["General"]