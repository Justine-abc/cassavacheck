"""Management advice and follow-up questions. Rules are data, not code paths, so RAB guidance can be edited without a deploy.
No entry ever names a pesticide, fungicide or dose; a test enforces that."""
from api.calibration import Decision

ADVICE_BY_LABEL: dict[str, list[str]] = {
    "CBB": ["Remove badly affected plants and burn the debris.", "Use clean cuttings from a certified source next season.", "Ask the extension officer to confirm before replanting."],
    "CBSD": ["Do not take cuttings from this plant.", "Use certified, tolerant planting material.", "Ask the extension officer to confirm; brown streak is easy to confuse with other causes."],
    "CGM": ["Check the undersides of young leaves for mites.", "Keep the field weeded; mite damage usually eases with the rains.", "Prefer tolerant varieties next season."],
    "CMD": ["Do not take cuttings from this plant.", "Use certified, resistant varieties for the next planting.", "Remove heavily affected plants if they are few."],
    "healthy": ["No disease signs detected on this leaf.", "Check other leaves and plants in the field.", "Keep using clean planting material."],
}

FOLLOW_UP_QUESTIONS: list[dict] = [
    {"id": "leaf_age", "question": "How old is this leaf?", "options": ["Young (top of plant)", "Older (lower on plant)"]},
    {"id": "whiteflies", "question": "Do you see small white flies under the leaves?", "options": ["Yes", "No", "Not checked"]},
    {"id": "cuttings_source", "question": "Where did the cuttings come from?", "options": ["My own field", "A neighbour", "Certified seed"]},
]

ABSTAIN_ADVICE: list[str] = [
    "Check two more leaves on the same plant and take another photo in daylight.",
    "Do not take cuttings from this plant until an officer has checked it.",
    "Ask your RAB extension officer and show them this result.",
]

FORBIDDEN_WORDS = ("pesticide", "fungicide", "insecticide", "spray", "dose", "ml per", "litre")


class AdvisoryService:
    """Turns a Decision into advice text. On abstention it returns the three questions and referral advice, never a label."""

    def advice_for(self, decision: Decision) -> dict:
        if decision.abstained:
            return {"advice": ABSTAIN_ADVICE, "follow_up_questions": FOLLOW_UP_QUESTIONS, "referral": True}
        return {"advice": ADVICE_BY_LABEL[decision.label], "follow_up_questions": [], "referral": False}

    @staticmethod
    def contains_forbidden_words(text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in FORBIDDEN_WORDS)
