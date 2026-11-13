"""Referral cases added after the report was submitted: consent before a phone number, a check code before the farmer
sees the case, officer-only updates, and the phone number deleted when the case is answered or expires."""
import os
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from api import config
from api.calibration import Decision
from api.log_store import CHECK_CODE_ALPHABET, CHECK_CODE_LENGTH, DiagnosisLog
from api.main import app, log
from api.referral import normalise_rwanda_phone, officer_note_problem

client = TestClient(app)
OFFICER_CODE = "test-officer-code"
os.environ[config.OFFICER_CODE_VARIABLE] = OFFICER_CODE
OFFICER = {"X-Officer-Code": OFFICER_CODE}
NOT_SURE = Decision(label=None, confidence=0.43, probabilities={"CBB": 0.18, "CBSD": 0.05, "CGM": 0.27, "CMD": 0.07, "healthy": 0.43}, abstained=True)


def new_case() -> int:
    """A logged diagnosis, written straight to the log so these tests do not depend on the model weights."""
    return log.record("Nyanza", "A", NOT_SURE, "test")


def officer_row(case_number: int) -> dict:
    return next(row for row in client.get("/log", headers=OFFICER).json() if row["id"] == case_number)


def test_rwandan_mobile_numbers_are_normalised():
    for written in ("0788123456", "0788 123 456", "+250 788-123-456", "250788123456", "0722123456", "0731234567"):
        assert normalise_rwanda_phone(written).startswith("+2507")
    assert normalise_rwanda_phone("0788 123 456") == "+250788123456"


def test_non_rwandan_or_malformed_numbers_are_refused():
    for written in ("", "12345", "0700123456", "078812345", "07881234567", "+254712345678", "hello"):
        assert normalise_rwanda_phone(written) is None


def test_officer_note_follows_the_no_chemical_rule():
    assert officer_note_problem("Brown streak confirmed. Uproot the plant and use clean cuttings.") is None
    assert officer_note_problem("Spray a fungicide twice a week") is not None
    assert officer_note_problem("x" * 501) is not None


def test_referral_without_phone_gives_case_number_and_check_code():
    case_number = new_case()
    reply = client.post("/referral", json={"diagnosis_id": case_number, "answers": {"whiteflies": "Yes"}})
    assert reply.status_code == 200
    body = reply.json()
    assert body["case_number"] == case_number and not body["contact_saved"]
    assert len(body["check_code"]) == CHECK_CODE_LENGTH and set(body["check_code"]) <= set(CHECK_CODE_ALPHABET)
    row = officer_row(case_number)
    assert row["referral_requested"] and row["case_status"] == "received" and row["phone"] is None
    assert row["answers"] == {"whiteflies": "Yes"}


def test_phone_needs_consent_and_a_valid_number():
    case_number = new_case()
    assert client.post("/referral", json={"diagnosis_id": case_number, "phone": "0788123456"}).status_code == 422
    assert client.post("/referral", json={"diagnosis_id": case_number, "contact_consent": True, "phone": "12345"}).status_code == 422
    reply = client.post("/referral", json={"diagnosis_id": case_number, "contact_consent": True, "phone": "0788 123 456"})
    assert reply.status_code == 200 and reply.json()["contact_saved"]
    assert officer_row(case_number)["phone"] == "+250788123456"


def test_pressing_refer_twice_keeps_the_same_case_and_code():
    case_number = new_case()
    first = client.post("/referral", json={"diagnosis_id": case_number}).json()
    second = client.post("/referral", json={"diagnosis_id": case_number, "contact_consent": True, "phone": "0788123456"}).json()
    assert first["check_code"] == second["check_code"]
    assert officer_row(case_number)["phone"] == "+250788123456"


def test_referral_for_unknown_diagnosis_is_404():
    assert client.post("/referral", json={"diagnosis_id": 10**9}).status_code == 404


def test_farmer_reads_status_only_with_the_right_code():
    case_number = new_case()
    code = client.post("/referral", json={"diagnosis_id": case_number, "contact_consent": True, "phone": "0788123456"}).json()["check_code"]
    found = client.get(f"/case/{case_number}", params={"code": code.lower()})   # typed in lower case still works
    assert found.status_code == 200 and found.json()["status"] == "received"
    assert "phone" not in found.json()
    assert client.get(f"/case/{case_number}", params={"code": "WRONG2"}).status_code == 404
    assert client.get(f"/case/{10**9}", params={"code": code}).status_code == 404


def test_only_officers_update_a_case():
    case_number = new_case()
    client.post("/referral", json={"diagnosis_id": case_number})
    update = {"status": "seen", "officer_note": "I will call you this week."}
    assert client.put(f"/cases/{case_number}", json=update).status_code == 401
    assert client.put(f"/cases/{case_number}", json=update, headers={"X-Officer-Code": "wrong"}).status_code == 401
    assert client.put(f"/cases/{case_number}", json=update, headers=OFFICER).status_code == 200


def test_officer_update_is_validated():
    case_number = new_case()
    client.post("/referral", json={"diagnosis_id": case_number})
    assert client.put(f"/cases/{case_number}", json={"status": "done"}, headers=OFFICER).status_code == 422
    assert client.put(f"/cases/{case_number}", json={"status": "answered", "officer_note": "Use insecticide"}, headers=OFFICER).status_code == 422
    assert client.put(f"/cases/{new_case()}", json={"status": "seen"}, headers=OFFICER).status_code == 404   # never referred


def test_answering_a_case_shows_the_note_to_the_farmer_and_deletes_the_phone():
    case_number = new_case()
    code = client.post("/referral", json={"diagnosis_id": case_number, "contact_consent": True, "phone": "0788123456"}).json()["check_code"]
    note = "Brown streak confirmed on visit. Uproot the plant; take cuttings only from plants without symptoms."
    client.put(f"/cases/{case_number}", json={"status": "answered", "officer_note": note}, headers=OFFICER)
    farmer_view = client.get(f"/case/{case_number}", params={"code": code}).json()
    assert farmer_view["status"] == "answered" and farmer_view["officer_note"] == note
    assert officer_row(case_number)["phone"] is None
    # A closed case does not take a new phone number.
    client.post("/referral", json={"diagnosis_id": case_number, "contact_consent": True, "phone": "0788999999"})
    assert officer_row(case_number)["phone"] is None


def test_phone_numbers_expire_after_the_retention_period(tmp_path):
    store = DiagnosisLog(tmp_path / "log.sqlite")
    case_number = store.record("Huye", "B", NOT_SURE, "test")
    store.open_referral(case_number, "+250788123456")
    old = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat(timespec="seconds")
    with store._cursor() as cursor:
        cursor.execute("UPDATE referral SET contact_consent_at = ? WHERE diagnosis_id = ?", (old, case_number))
    row = next(r for r in store.recent() if r["id"] == case_number)
    assert row["phone"] is None and row["case_status"] == "received"


def test_my_case_page_is_served_and_does_not_link_to_the_officer_view():
    response = client.get("/my-case")
    assert response.status_code == 200 and 'href="/officer"' not in response.text
