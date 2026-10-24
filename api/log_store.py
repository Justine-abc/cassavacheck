"""Anonymised request log (FR-06): district, season, decision, confidence, timestamp. No image bytes, no coordinates, no names.
SQLite for the local build; the same interface is kept so PostgreSQL can replace it on Render by swapping this class."""
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

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def record(self, district: str | None, season: str | None, decision: Decision, model_version: str) -> None:
        with self._connect() as connection:
            connection.execute("INSERT INTO diagnosis_log (created_at, district, season, decision, confidence, model_version) VALUES (?, ?, ?, ?, ?, ?)",
                               (datetime.now(timezone.utc).isoformat(timespec="seconds"), district, season,
                                "abstain" if decision.abstained else decision.label, decision.confidence, model_version))

    def recent(self, limit: int = 50, district: str | None = None) -> list[dict]:
        query = "SELECT created_at, district, season, decision, confidence FROM diagnosis_log"
        parameters: tuple = ()
        if district:
            query += " WHERE district = ?"; parameters = (district,)
        query += " ORDER BY id DESC LIMIT ?"; parameters += (limit,)
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [{"created_at": r[0], "district": r[1], "season": r[2], "decision": r[3], "confidence": r[4]} for r in rows]
