"""The Kinyarwanda interface: every string the farmer pages translate has an entry, so nothing silently stays in English,
and translation never touches what is sent to the API."""
import json
import re

from api import config
from api.advice import ABSTAIN_ADVICE, ADVICE_BY_LABEL, FOLLOW_UP_QUESTIONS, GUIDANCE_BY_ANSWER, AdvisoryService

STATIC = config.STATIC_DIRECTORY
FARMER_PAGES = ("index.html", "result.html", "my_case.html", "how_it_works.html", "diseases.html")


def kinyarwanda_keys() -> set[str]:
    source = (STATIC / "i18n.js").read_text(encoding="utf-8")
    block = source[source.index("const RW = {"):]
    return {json.loads(f'"{key}"') for key in re.findall(r'^\s*"((?:[^"\\]|\\.)*)":', block, flags=re.MULTILINE)}


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().replace("<br/>", "<br>")


def test_every_literal_the_pages_translate_has_kinyarwanda():
    keys = kinyarwanda_keys()
    missing = []
    for page in FARMER_PAGES + ("app.js",):
        source = (STATIC / page).read_text(encoding="utf-8")
        missing += [literal for literal in (normalise(json.loads(f'"{m}"')) for m in re.findall(r'\bT\("((?:[^"\\]|\\.)*)"\)', source))
                    if literal not in keys]
        missing += [normalise(inner) for _, inner in re.findall(r"<(\w+)(?:\s[^>]*)?\sdata-t(?:\s[^>]*)?>([\s\S]*?)</\1>", source)
                    if normalise(inner) not in keys]
    assert not missing, missing


def test_all_advice_and_questions_have_kinyarwanda():
    keys = kinyarwanda_keys()
    texts = [line for lines in ADVICE_BY_LABEL.values() for line in lines] + ABSTAIN_ADVICE + list(GUIDANCE_BY_ANSWER.values())
    texts += [question["question"] for question in FOLLOW_UP_QUESTIONS] + [option for question in FOLLOW_UP_QUESTIONS for option in question["options"]]
    assert not [text for text in texts if text not in keys]


def test_kinyarwanda_text_names_no_chemical_product():
    # Only the Kinyarwanda side is checked: some English keys state the rule itself ("never ... a dose").
    # The English rule words still catch product names, which are written the same way in both languages.
    source = (STATIC / "i18n.js").read_text(encoding="utf-8")
    block = source[source.index("const RW = {"):]
    values = re.sub(r'^\s*"(?:[^"\\]|\\.)*":', "", block, flags=re.MULTILINE)
    assert not AdvisoryService.contains_forbidden_words(values)


def test_answers_are_sent_in_english_whatever_the_language():
    # The answer buttons carry the English option as their value; only the label is translated.
    source = (STATIC / "result.html").read_text(encoding="utf-8")
    assert 'data-option="${escapeHtml(option)}"' in source
    assert "<span>${escapeHtml(T(option))}</span>" in source
