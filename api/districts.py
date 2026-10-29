"""District information: published survey values shown beside the result. This module never touches the model."""
import csv
from dataclasses import dataclass
from pathlib import Path


# All 30 districts, so a farmer can always pick theirs; only districts with a verified survey row get a panel.
RWANDA_DISTRICTS = {
    "Kigali": ["Gasabo", "Kicukiro", "Nyarugenge"],
    "Southern": ["Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango"],
    "Western": ["Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro"],
    "Northern": ["Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo"],
    "Eastern": ["Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana"],
}


@dataclass(frozen=True)
class DistrictPrevalence:
    district: str
    survey_year: int
    season: str
    cbsd_incidence_pct: float | None
    cmd_incidence_pct: float | None
    fields_surveyed: int
    source: str

    def sentence(self) -> str:
        parts = []
        if self.cbsd_incidence_pct is not None:
            parts.append(f"CBSD found in {self.cbsd_incidence_pct:g}% of fields")
        if self.cmd_incidence_pct is not None:
            parts.append(f"CMD in {self.cmd_incidence_pct:g}%")
        values = ", ".join(parts) if parts else "no incidence value recorded"
        return f"{self.district}, season {self.season}: {values} ({self.survey_year} survey, {self.fields_surveyed} fields; {self.source})."


class DistrictRepository:
    """Loads the CSV once and answers lookups. Kept separate so the data source can become PostgreSQL without touching the API."""

    def __init__(self, table_path: Path):
        self.rows: list[DistrictPrevalence] = []
        with open(table_path, newline="", encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                self.rows.append(DistrictPrevalence(
                    district=raw["district"].strip(),
                    survey_year=int(raw["survey_year"]),
                    season=raw["season"].strip(),
                    cbsd_incidence_pct=self._optional_float(raw.get("cbsd_incidence_pct")),
                    cmd_incidence_pct=self._optional_float(raw.get("cmd_incidence_pct")),
                    fields_surveyed=int(raw["fields_surveyed"]),
                    source=raw["source"].strip(),
                ))

    @staticmethod
    def _optional_float(value: str | None) -> float | None:
        return float(value) if value not in (None, "") else None

    def districts(self) -> list[str]:
        return sorted({row.district for row in self.rows})

    def lookup(self, district: str, season: str) -> DistrictPrevalence | None:
        """Exact district and season first; if that season was not surveyed, any row for the district, so the panel is never empty
        for a known district."""
        exact = [row for row in self.rows if row.district.lower() == district.lower() and row.season.upper() == season.upper()]
        if exact:
            return exact[0]
        any_season = [row for row in self.rows if row.district.lower() == district.lower()]
        return any_season[0] if any_season else None

    def all_rows(self) -> list[dict]:
        return [row.__dict__ for row in self.rows]

    def choices(self) -> list[dict]:
        """Every district for the picker, with whether a surveyed value exists for it."""
        surveyed = {row.district.lower() for row in self.rows}
        return [{"district": name, "province": province, "has_survey": name.lower() in surveyed}
                for province, names in RWANDA_DISTRICTS.items() for name in names]
