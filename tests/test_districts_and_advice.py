"""Unit tests for the district repository and the advisory rules."""
from pathlib import Path

from api.advice import ADVICE_BY_LABEL, ABSTAIN_ADVICE, GUIDANCE_BY_ANSWER, AdvisoryService
from api.calibration import Decision
from api.districts import RWANDA_DISTRICTS, DistrictRepository


def write_table(path: Path) -> Path:
    path.write_text("district,survey_year,sampling_period,cbsd_incidence_pct,ci_low_pct,ci_high_pct,plants_examined,source\n"
                    "Nyanza,2019,May to September,62,56,67,300,\"Nyirakanani et al. (2021), Table 1\"\n"
                    "Bugesera,2019,May to September,60,54,65,300,\"Nyirakanani et al. (2021), Table 1\"\n", encoding="utf-8")
    return path


def test_lookup_known_and_unknown_district(tmp_path):
    repository = DistrictRepository(write_table(tmp_path / "districts.csv"))
    assert repository.lookup("Nyanza").cbsd_incidence_pct == 62
    assert repository.lookup("nyanza").district == "Nyanza"           # case does not matter
    assert repository.lookup("Kigali") is None                        # unknown district gives no panel, never a made-up value


def test_sentence_states_year_denominator_and_interval(tmp_path):
    repository = DistrictRepository(write_table(tmp_path / "districts.csv"))
    sentence = repository.lookup("Bugesera").sentence()
    assert "2019" in sentence and "300 cassava plants" in sentence and "60%" in sentence and "54 to 65" in sentence
    assert "not your leaf" in sentence


def test_published_table_covers_the_thirteen_surveyed_districts():
    from api import config
    repository = DistrictRepository(config.DISTRICT_TABLE_PATH)
    assert len(repository.rows) == 13
    assert all(row.district in sum(RWANDA_DISTRICTS.values(), []) for row in repository.rows)


def test_advice_never_names_a_pesticide():
    service = AdvisoryService()
    for lines in list(ADVICE_BY_LABEL.values()) + [ABSTAIN_ADVICE, list(GUIDANCE_BY_ANSWER.values())]:
        for line in lines:
            assert not service.contains_forbidden_words(line), line


def test_abstention_returns_questions_and_no_label():
    guidance = AdvisoryService().advice_for(Decision(label=None, confidence=0.4, probabilities={}, abstained=True))
    assert len(guidance["follow_up_questions"]) == 4 and guidance["referral"] is True


def test_only_known_answers_are_kept_and_turned_into_guidance():
    service = AdvisoryService()
    answers = service.valid_answers({"whiteflies": "Yes", "other_signs": "free text a farmer typed", "unknown_question": "Yes"})
    assert answers == {"whiteflies": "Yes"}                            # the log never stores free text
    assert any("Whiteflies" in note for note in service.guidance_for_answers(answers))


def test_district_choices_cover_all_thirty_and_flag_surveyed(tmp_path):
    choices = DistrictRepository(write_table(tmp_path / "districts.csv")).choices()
    assert len(choices) == 30 == sum(len(names) for names in RWANDA_DISTRICTS.values())
    assert {c["district"] for c in choices if c["has_survey"]} == {"Nyanza", "Bugesera"}
