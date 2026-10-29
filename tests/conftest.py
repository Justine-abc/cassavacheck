"""Runs before any test module imports the API, so diagnoses made by tests go to a throwaway log, not the officer's real one."""
import os
import tempfile
from pathlib import Path

os.environ.setdefault("CASSACHECK_LOG_PATH", str(Path(tempfile.mkdtemp()) / "test_diagnosis_log.sqlite"))
