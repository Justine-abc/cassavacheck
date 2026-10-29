"""Anonymised request log (FR-06): district, season, decision, confidence, timestamp, and the farmer's answers to the follow-up
questions when given. No image bytes, no coordinates, no names, no free text.
SQLite for the local build; the same interface is kept so PostgreSQL can replace it on Render by swapping this class."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from api.calibration import Decision


class DiagnosisLog:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS diagnosis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, district TEXT, season TEXT,
                decision TEXT NOT NULL, confidence REAL NOT NULL, model_version TEXT NOT NULL)""")
            # A separate table, so logs written before follow-up answers existed stay readable without a migration.
            connection.execute("""CREATE TABLE IF NOT EXISTS follow_up (
                diagnosis_id INTEGER PRIMARY KEY REFERENCES diagnosis_log(id), created_at TEXT NOT NULL,
                answers TEXT NOT NULL, referral_requested INTEGER NOT NULL)""")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def record(self, district: str | None, season: str | None, decision: Decision, model_version: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute("INSERT INTO diagnosis_log (created_at, district, season, decision, confidence, model_version) VALUES (?, ?, ?, ?, ?, ?)",
                                        (self._now(), district, season, "abstain" if decision.abstained else decision.label, decision.confidence, model_version))
            return int(cursor.lastrowid)

    def exists(self, diagnosis_id: int) -> bool:
        with self._connect() as connection:
            return connection.execute("SELECT 1 FROM diagnosis_log WHERE id = ?", (diagnosis_id,)).fetchone() is not None

    def add_follow_up(self, diagnosis_id: int, answers: dict[str, str], referral_requested: bool) -> None:
        """Answering again replaces the earlier answers for the same diagnosis."""
        with self._connect() as connection:
            connection.execute("INSERT OR REPLACE INTO follow_up (diagnosis_id, created_at, answers, referral_requested) VALUES (?, ?, ?, ?)",
                               (diagnosis_id, self._now(), json.dumps(answers), int(referral_requested)))

    def recent(self, limit: int = 50, district: str | None = None) -> list[dict]:
        query = """SELECT d.id, d.created_at, d.district, d.season, d.decision, d.confidence, f.answers, f.referral_requested
                   FROM diagnosis_log d LEFT JOIN follow_up f ON f.diagnosis_id = d.id"""
        parameters: tuple = ()
        if district:
            query += " WHERE d.district = ?"; parameters = (district,)
        query += " ORDER BY d.id DESC LIMIT ?"; parameters += (limit,)
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [{"id": r[0], "created_at": r[1], "district": r[2], "season": r[3], "decision": r[4], "confidence": r[5],
                 "answers": json.loads(r[6]) if r[6] else {}, "referral_requested": bool(r[7])} for r in rows]
