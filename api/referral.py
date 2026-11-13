"""Checks for what a farmer or an officer types into a referral case. Kept apart from the log so the rules are tested
without a database."""
import re

from api.advice import AdvisoryService

# Rwandan mobile numbers: 07 then 2 or 3 (Airtel) or 8 or 9 (MTN), then seven digits.
_LOCAL_MOBILE = re.compile(r"07[2389]\d{7}")
OFFICER_NOTE_MAX_LENGTH = 500


def normalise_rwanda_phone(raw: str) -> str | None:
    """Returns the number as +2507XXXXXXXX, or None if it is not a Rwandan mobile number.
    Accepts the ways people write it: 0788 123 456, +250 788-123-456, 250788123456."""
    digits = re.sub(r"[\s\-().]", "", raw or "")
    if digits.startswith("+250"):
        digits = "0" + digits[4:]
    elif digits.startswith("250") and len(digits) == 12:
        digits = "0" + digits[3:]
    return "+250" + digits[1:] if _LOCAL_MOBILE.fullmatch(digits) else None


def officer_note_problem(note: str | None) -> str | None:
    """The officer's note reaches the farmer through the app, so it follows the same rule as the app's own advice:
    no chemical and no dose. Returns why a note is refused, or None if it is fine."""
    if note is None:
        return None
    if len(note) > OFFICER_NOTE_MAX_LENGTH:
        return f"Keep the note under {OFFICER_NOTE_MAX_LENGTH} characters."
    if AdvisoryService.contains_forbidden_words(note):
        return "The note reaches the farmer through the app, which never names a chemical or a dose. Give management steps, and advise in person if needed."
    return None
