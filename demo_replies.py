"""Scripted replies used by DEMO MODE (no API key needed).

The business below ("Nova Print") is fictional. These are NOT real model outputs:
they only let you try the interface and the streaming behaviour offline.
"""

RULES = [
    (("price", "cost", "how much", "quote", "prix", "tarif"),
     "Happy to help with pricing! At Nova Print, 100 full-color business cards start at "
     "$12, flyers (A5, 250 pcs) at $34, and large-format banners at $9 per sq. ft. "
     "Tell me the product, quantity and size and I'll prepare an exact quote."),
    (("hour", "open", "close", "horaire", "ouvert"),
     "We're open Sunday to Thursday, 8:30 to 17:30, and Saturday 9:00 to 13:00. "
     "We're closed on Fridays."),
    (("deliver", "shipping", "ship", "livraison"),
     "Yes, we deliver! Local orders arrive within 24-48 hours, and national shipping "
     "takes 3-5 business days. Delivery is free for orders above $80."),
    (("gold", "foil", "emboss", "dorure"),
     "Hot-foil stamping and embossing are available on cards, invitations and packaging. "
     "Gold, silver and colored foils are in stock. Production usually takes 3 working days."),
    (("hello", "hi", "hey", "bonjour", "salam", "salut"),
     "Hello! I'm the Nova Print assistant. I can help with prices, opening hours, "
     "delivery and special finishes. What do you need today?"),
]

FALLBACK = (
    "Thanks for your message! This is a demo assistant, so I only know a few topics: "
    "prices, opening hours, delivery and hot-foil finishes. In a real deployment I'd "
    "answer from your own business knowledge base."
)


def demo_reply(message: str) -> str:
    text = message.lower()
    for keywords, reply in RULES:
        if any(k in text for k in keywords):
            return reply
    return FALLBACK
