import csv
from pathlib import Path

def parse_projects_from_csv(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8") as file:
        return {row["project"] for row in csv.DictReader(file)}
