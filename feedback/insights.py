MIN_MENTIONS = 5     # aspect ko "reliable" maanne ke liye kam se kam itne feedbacks

ACTIONS = {
    "Delivery": "Review courier partners and the delivery-time promise you make to customers.",
    "Packaging": "Check how items are packed and sealed before they ship.",
    "Service & Support": "Look at response times and how complaints, refunds and replacements are handled.",
    "Staff": "Brief and train front-line staff; rude or unhelpful behaviour hurts reviews quickly.",
    "Price": "Compare your pricing with competitors, or make the value clearer to customers.",
    "Quality": "Inspect the products or batches that customers report as faulty or broken.",
    "Battery": "Investigate the battery-life and charging complaints with the product team.",
    "Camera": "Check the camera complaints for common conditions (low light, specific models).",
    "Performance": "Look into lag, hanging and heating reports, and which models they come from.",
    "Display": "Review screen complaints such as brightness, touch or resolution.",
    "Sound": "Check speaker and microphone complaints for a common cause.",
    "Food": "Review the dishes and ingredients that customers complain about.",
    "Room": "Inspect the rooms and facilities that guests complain about.",
    "Cleanliness": "Tighten cleaning checklists and inspection routines.",
    "Ambience": "Look at noise, crowding and seating problems at peak hours.",
    "Location": "Add clearer directions and parking information for customers.",
    "Teaching": "Share the teaching feedback with the faculty and review the course material.",
    "App/Website": "Fix the crashes and bugs users report in the app or website.",
    "Waiting Time": "Reduce queues and waiting time, for example by adding staff at peak hours.",
}
DEFAULT_ACTION = "Read the example comments below and look for the common cause."


def _join(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def build_insights(data):
    """analytics.build_dashboard() ke dict se plain-language insights. Koi API nahi, sirf rules."""
    if not data.get("total"):
        return None

    total = data["total"]
    pos, neu, neg = (s["pct"] for s in data["sentiment"])   # order: Positive, Neutral, Negative
    issues = data["issues"]
    points = []

    # 1) Overall tone
    if pos >= 60:
        tone = "mostly positive"
    elif neg >= 40:
        tone = "mostly negative"
    elif abs(pos - neg) < 10:
        tone = "mixed"
    elif pos > neg:
        tone = "leaning positive"
    else:
        tone = "leaning negative"
    headline = (f"Feedback is {tone}: {pos:.0f}% positive, {neu:.0f}% neutral and "
                f"{neg:.0f}% negative across {total} reviews.")

    # 2) Top issues
    if issues:
        text = f"Most negative feedback is about {issues[0]['aspect']} ({issues[0]['pct']:.0f}% of negative mentions)"
        others = [i["aspect"] for i in issues[1:3]]
        if others:
            text += f", followed by {_join(others)}"
        points.append({"kind": "bad", "text": text + "."})
    else:
        points.append({"kind": "good", "text": "No clear recurring issue stands out."})

    # 3) Strengths aur watch-list (sirf reliable aspects)
    reliable = [a for a in data["aspects"] if a["total"] >= MIN_MENTIONS]

    praised = sorted((a for a in reliable if a["Positive"] / a["total"] >= 0.6),
                     key=lambda a: -a["Positive"] / a["total"])[:2]
    if praised:
        parts = [f"{a['aspect']} ({a['Positive'] / a['total']:.0%} positive)" for a in praised]
        points.append({"kind": "good", "text": f"Customers are happiest with {_join(parts)}."})

    already = {i["aspect"] for i in issues[:3]}
    risky = sorted((a for a in reliable
                    if a["Negative"] / a["total"] >= 0.4 and a["aspect"] not in already),
                   key=lambda a: -a["Negative"] / a["total"])[:2]
    if risky:
        parts = [f"{a['aspect']} ({a['Negative'] / a['total']:.0%} of {a['total']} mentions negative)"
                 for a in risky]
        points.append({"kind": "bad", "text": f"Keep an eye on {_join(parts)}."})

    if not data["aspects"]:
        points.append({"kind": "info",
                       "text": "No specific aspects (delivery, price, staff...) were detected in this data."})

    # 4) Trend
    delta = data.get("trend_delta")
    if delta is not None:
        if delta > 2:
            points.append({"kind": "bad",
                           "text": f"Negative feedback is rising: up {delta:.1f} points in the later part of this period."})
        elif delta < -2:
            points.append({"kind": "good",
                           "text": f"Negative feedback is falling: down {abs(delta):.1f} points in the later part of this period."})
        else:
            points.append({"kind": "info", "text": "Sentiment has been stable over time."})

    # 5) Caveat
    if total < 30:
        points.append({"kind": "info",
                       "text": f"Only {total} feedbacks were analysed, so treat these numbers as indicative."})

    suggestions = [{"aspect": i["aspect"], "text": ACTIONS.get(i["aspect"], DEFAULT_ACTION)}
                   for i in issues[:2]]

    return {
        "headline": headline,
        "points": points,
        "suggestions": suggestions,
        "examples": data.get("issue_examples", []),
        "example_aspect": issues[0]["aspect"] if issues else "",
    }