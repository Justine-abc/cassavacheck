"""Runs before any test module imports the API, so diagnoses made by tests go to a throwaway log, not the officer's real one.
The suite never touches a real hosted database: DATABASE_URL is cleared, unless CASSACHECK_TEST_DATABASE_URL points the
suite at a throwaway PostgreSQL on purpose."""
import os
import tempfile
from pathlib import Path

os.environ.setdefault("CASSACHECK_LOG_PATH", str(Path(tempfile.mkdtemp()) / "test_diagnosis_log.sqlite"))
os.environ.pop("DATABASE_URL", None)
if os.environ.get("CASSACHECK_TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["CASSACHECK_TEST_DATABASE_URL"]
