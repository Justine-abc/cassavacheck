"""Request log (FR-06) and the referral cases that grow out of it.

diagnosis_log and follow_up hold district, season, decision, confidence, timestamp and the farmer's answers to the
follow-up questions (fixed options only). No image bytes, no coordinates, no names.

referral is added after submission of the report: one row per case a farmer sends to the extension officer. It holds a
short check code so only the farmer can read the case status, the status the officer sets, and the officer's note.
A phone number is stored only if the farmer ticked consent, and it is deleted when the case is answered or after
CONTACT_RETENTION_DAYS, whichever comes first.

SQLite for a local run; PostgreSQL when DATABASE_URL is set, so the officer's list survives a restart on Render.
The SQL is written once and runs on both."""
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.calibration import Decision

CASE_STATUSES = ("received", "seen", "visit_planned", "answered")
CLOSED_STATUS = "answered"
CONTACT_RETENTION_DAYS = 30
# No 0/O, 1/I/L: a farmer reads the code off a phone screen and types it again later.
CHECK_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CHECK_CODE_LENGTH = 6


def new_check_code() -> str:
    return "".join(secrets.choice(CHECK_CODE_ALPHABET) for _ in range(CHECK_CODE_LENGTH))


class DiagnosisLog:
    def __init__(self, database_path: Path, database_url: str | None = None):
        self.database_path = database_path
        self.database_url = database_url
        self.postgres = bool(database_url)
        identity = "SERIAL PRIMARY KEY" if self.postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        # PostgreSQL REAL is 4 bytes and would round the logged confidence; SQLite REAL is already 8 bytes.
        decimal = "DOUBLE PRECISION" if self.postgres else "REAL"
        with self._cursor() as cursor:
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS diagnosis_log (
                id {identity}, created_at TEXT NOT NULL, district TEXT, season TEXT,
                decision TEXT NOT NULL, confidence {decimal} NOT NULL, model_version TEXT NOT NULL)""")
            # A separate table, so logs written before follow-up answers existed stay readable without a migration.
            cursor.execute("""CREATE TABLE IF NOT EXISTS follow_up (
                diagnosis_id INTEGER PRIMARY KEY REFERENCES diagnosis_log(id), created_at TEXT NOT NULL,
                answers TEXT NOT NULL, referral_requested INTEGER NOT NULL)""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS referral (
                diagnosis_id INTEGER PRIMARY KEY REFERENCES diagnosis_log(id), created_at TEXT NOT NULL,
                check_code TEXT NOT NULL, phone TEXT, contact_consent_at TEXT,
                status TEXT NOT NULL, officer_note TEXT, updated_at TEXT NOT NULL)""")

    @contextmanager
    def _cursor(self):
        """One connection per call, committed on success. Short-lived connections suit both a local file and a hosted
        database that closes idle connections."""
        if self.postgres:
            import psycopg  # only needed on the server that sets DATABASE_URL
            with psycopg.connect(self.database_url) as connection:
                with connection.cursor() as cursor:
                    yield _PostgresCursor(cursor)
        else:
            connection = sqlite3.connect(self.database_path)
            try:
                yield connection.cursor()
                connection.commit()
            finally:
                connection.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def record(self, district: str | None, season: str | None, decision: "Decision", model_version: str) -> int:
        with self._cursor() as cursor:
            cursor.execute("INSERT INTO diagnosis_log (created_at, district, season, decision, confidence, model_version) "
                           "VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
                           (self._now(), district, season, "abstain" if decision.abstained else decision.label, decision.confidence, model_version))
            return int(cursor.fetchone()[0])

    def exists(self, diagnosis_id: int) -> bool:
        with self._cursor() as cursor:
            cursor.execute("SELECT 1 FROM diagnosis_log WHERE id = ?", (diagnosis_id,))
            return cursor.fetchone() is not None

    def add_follow_up(self, diagnosis_id: int, answers: dict[str, str], referral_requested: bool) -> None:
        """Answering again replaces the earlier answers. Once a case is referred it stays referred."""
        with self._cursor() as cursor:
            cursor.execute("""INSERT INTO follow_up (diagnosis_id, created_at, answers, referral_requested) VALUES (?, ?, ?, ?)
                              ON CONFLICT (diagnosis_id) DO UPDATE SET created_at = excluded.created_at, answers = excluded.answers,
                              referral_requested = CASE WHEN follow_up.referral_requested = 1 THEN 1 ELSE excluded.referral_requested END""",
                           (diagnosis_id, self._now(), json.dumps(answers), int(referral_requested)))

    def open_referral(self, diagnosis_id: int, phone: str | None) -> str:
        """Creates the case, or returns the existing one's check code if the farmer presses the button twice.
        A phone number given later is added; one given earlier is never silently removed by a second press."""
        now = self._now()
        with self._cursor() as cursor:
            cursor.execute("SELECT check_code, status FROM referral WHERE diagnosis_id = ?", (diagnosis_id,))
            existing = cursor.fetchone()
            if existing:
                if phone and existing[1] != CLOSED_STATUS:
                    cursor.execute("UPDATE referral SET phone = ?, contact_consent_at = ?, updated_at = ? WHERE diagnosis_id = ?",
                                   (phone, now, now, diagnosis_id))
                return existing[0]
            check_code = new_check_code()
            cursor.execute("INSERT INTO referral (diagnosis_id, created_at, check_code, phone, contact_consent_at, status, updated_at) "
                           "VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (diagnosis_id, now, check_code, phone, now if phone else None, CASE_STATUSES[0], now))
            return check_code

    def case_status(self, diagnosis_id: int, check_code: str) -> dict | None:
        """What the farmer may see: status, the officer's note and dates. Never the phone number.
        A wrong code and an unknown case give the same answer, so case numbers cannot be probed."""
        with self._cursor() as cursor:
            cursor.execute("SELECT check_code, status, officer_note, created_at, updated_at FROM referral WHERE diagnosis_id = ?",
                           (diagnosis_id,))
            row = cursor.fetchone()
        if not row or not secrets.compare_digest(row[0].encode(), check_code.strip().upper().encode()):
            return None
        return {"case_number": diagnosis_id, "status": row[1], "officer_note": row[2], "created_at": row[3], "updated_at": row[4]}

    def update_case(self, diagnosis_id: int, status: str, officer_note: str | None) -> bool:
        """The officer moves a case along. Answering a case closes it and deletes the phone number."""
        if status not in CASE_STATUSES:
            raise ValueError(f"status must be one of {CASE_STATUSES}")
        clear_phone = ", phone = NULL" if status == CLOSED_STATUS else ""
        with self._cursor() as cursor:
            cursor.execute(f"UPDATE referral SET status = ?, officer_note = ?, updated_at = ?{clear_phone} WHERE diagnosis_id = ? RETURNING diagnosis_id",
                           (status, officer_note, self._now(), diagnosis_id))
            return cursor.fetchone() is not None

    def delete_expired_contacts(self) -> None:
        """Phone numbers older than the retention period are removed even if the case is still open."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=CONTACT_RETENTION_DAYS)).isoformat(timespec="seconds")
        with self._cursor() as cursor:
            cursor.execute("UPDATE referral SET phone = NULL WHERE phone IS NOT NULL AND contact_consent_at < ?", (cutoff,))

    def recent(self, limit: int = 50, district: str | None = None) -> list[dict]:
        self.delete_expired_contacts()
        query = """SELECT d.id, d.created_at, d.district, d.season, d.decision, d.confidence, f.answers, f.referral_requested,
                          r.status, r.phone, r.officer_note, r.updated_at
                   FROM diagnosis_log d LEFT JOIN follow_up f ON f.diagnosis_id = d.id LEFT JOIN referral r ON r.diagnosis_id = d.id"""
        parameters: tuple = ()
        if district:
            query += " WHERE d.district = ?"; parameters = (district,)
        query += " ORDER BY d.id DESC LIMIT ?"; parameters += (limit,)
        with self._cursor() as cursor:
            cursor.execute(query, parameters)
            rows = cursor.fetchall()
        return [{"id": r[0], "created_at": r[1], "district": r[2], "season": r[3], "decision": r[4], "confidence": r[5],
                 "answers": json.loads(r[6]) if r[6] else {}, "referral_requested": bool(r[7]) or r[8] is not None,
                 "case_status": r[8], "phone": r[9], "officer_note": r[10], "case_updated_at": r[11]} for r in rows]


class _PostgresCursor:
    """Lets the same SQL run on PostgreSQL: psycopg uses %s where sqlite3 uses ?. None of the queries contain a literal ?."""

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query: str, parameters: tuple = ()):
        return self.cursor.execute(query.replace("?", "%s"), parameters)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()
