"""Management advice and follow-up questions. Rules are data, not code paths, so RAB guidance can be edited without a deploy.
No entry ever names a pesticide, fungicide or dose; a test enforces that. Answers to the questions add guidance and are passed to
the extension officer; they never change the diagnosis."""
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
    {"id": "other_signs", "question": "Do you see any other signs on the plant?", "options": ["Tiny mites or insects", "Spots or cracks on the stem", "Wilting leaves", "None of these"]},
    {"id": "cuttings_source", "question": "Where did the cuttings come from?", "options": ["My own field", "A neighbour", "Certified seed"]},
]

# One note per answer that tells the farmer or officer something useful. Answers without a note add nothing.
GUIDANCE_BY_ANSWER: dict[tuple[str, str], str] = {
    ("whiteflies", "Yes"): "Whiteflies carry the mosaic and brown streak viruses. Tell the officer you saw them.",
    ("other_signs", "Tiny mites or insects"): "Mites on young leaves can cause green mite damage. Show the officer the undersides of the leaves.",
    ("other_signs", "Spots or cracks on the stem"): "Stem spots can come with bacterial blight. Keep cuttings from this plant out of the next planting.",
    ("other_signs", "Wilting leaves"): "Wilting can have several causes, including bacterial blight. The officer should see the plant.",
    ("cuttings_source", "My own field"): "Cuttings from your own field can carry viruses from last season. Certified cuttings are safer next season.",
    ("cuttings_source", "A neighbour"): "Cuttings from another field can bring viruses with them. Certified cuttings are safer next season.",
}

ABSTAIN_ADVICE: list[str] = [
    "Check two more leaves on the same plant and take another photo in daylight.",
    "Do not take cuttings from this plant until an officer has checked it.",
    "Ask your RAB extension officer and show them this result.",
]

FORBIDDEN_WORDS = ("pesticide", "fungicide", "insecticide", "spray", "dose", "ml per", "litre")


class AdvisoryService:
    """Turns a Decision into advice text. On abstention it returns the questions and referral advice, never a label."""

    def advice_for(self, decision: Decision) -> dict:
        if decision.abstained:
            return {"advice": ABSTAIN_ADVICE, "follow_up_questions": FOLLOW_UP_QUESTIONS, "referral": True}
        return {"advice": ADVICE_BY_LABEL[decision.label], "follow_up_questions": [], "referral": False}

    @staticmethod
    def valid_answers(answers: dict[str, str]) -> dict[str, str]:
        """Keep only answers to known questions with one of that question's options, so the log never stores free text."""
        options = {question["id"]: question["options"] for question in FOLLOW_UP_QUESTIONS}
        return {key: value for key, value in answers.items() if value in options.get(key, [])}

    @staticmethod
    def guidance_for_answers(answers: dict[str, str]) -> list[str]:
        return [GUIDANCE_BY_ANSWER[(key, value)] for key, value in answers.items() if (key, value) in GUIDANCE_BY_ANSWER]

    @staticmethod
    def contains_forbidden_words(text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in FORBIDDEN_WORDS)
