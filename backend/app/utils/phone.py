import re

def normalize_phone(raw: str) -> str | None:
    """
    Normalize a Kenyan phone number to E.164 format (+254XXXXXXXXX).
    Accepts: +254XXXXXXXXX, 0XXXXXXXXX, 254XXXXXXXXX
    Returns None if the number is invalid.
    """
    cleaned = re.sub(r'[\s\-().]', '', raw.strip())

    if re.match(r'^\+254\d{9}$', cleaned):
        return cleaned
    if re.match(r'^0\d{9}$', cleaned):
        return '+254' + cleaned[1:]
    if re.match(r'^254\d{9}$', cleaned):
        return '+' + cleaned

    return None  # Invalid
