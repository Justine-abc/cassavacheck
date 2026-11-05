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
    """One district row of the 2019 national survey (Nyirakanani et al., 2021, Table 1): the share of examined plants
    showing CBSD leaf symptoms, its 95% confidence interval, and how many plants were examined."""
    district: str
    survey_year: int
    sampling_period: str
    cbsd_incidence_pct: float
    ci_low_pct: float
    ci_high_pct: float
    plants_examined: int
    source: str

    def sentence(self) -> str:
        return (f"{self.district}: in the {self.survey_year} national survey ({self.sampling_period}), "
                f"{self.cbsd_incidence_pct:g}% of {self.plants_examined} cassava plants examined showed brown streak (CBSD) leaf symptoms "
                f"(95% interval {self.ci_low_pct:g} to {self.ci_high_pct:g}%). Source: {self.source}. "
                f"This describes the district, not your leaf.")


class DistrictRepository:
    """Loads the CSV once and answers lookups. Kept separate so the data source can become PostgreSQL without touching the API."""

    def __init__(self, table_path: Path):
        self.rows: list[DistrictPrevalence] = []
        with open(table_path, newline="", encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                self.rows.append(DistrictPrevalence(
                    district=raw["district"].strip(),
                    survey_year=int(raw["survey_year"]),
                    sampling_period=raw["sampling_period"].strip(),
                    cbsd_incidence_pct=float(raw["cbsd_incidence_pct"]),
                    ci_low_pct=float(raw["ci_low_pct"]),
                    ci_high_pct=float(raw["ci_high_pct"]),
                    plants_examined=int(raw["plants_examined"]),
                    source=raw["source"].strip(),
                ))

    def districts(self) -> list[str]:
        return sorted({row.district for row in self.rows})

    def lookup(self, district: str) -> DistrictPrevalence | None:
        """The surveyed row for a district, or None: a district outside the survey gets no panel, never a made-up value.
        The survey does not report values by season, so the season the farmer picks is logged but does not change the panel."""
        matches = [row for row in self.rows if row.district.lower() == district.lower()]
        return matches[0] if matches else None

    def all_rows(self) -> list[dict]:
        return [row.__dict__ for row in self.rows]

    def choices(self) -> list[dict]:
        """Every district for the picker, with whether a surveyed value exists for it."""
        surveyed = {row.district.lower() for row in self.rows}
        return [{"district": name, "province": province, "has_survey": name.lower() in surveyed}
                for province, names in RWANDA_DISTRICTS.items() for name in names]
