import csv
from pathlib import Path

def parse_projects_from_csv(path: Path) -> set[str]:
    """Get the unique projects from the project column rows in the input csv file."""
    with path.open("r", encoding="utf-8") as file:
        return {row["project"] for row in csv.DictReader(file)}


def write_table_to_csv(path: Path, table_dict: dict[str, str]):
    """Save table columns, rows from a dictionary into a csv file."""
    with path.open("w", encoding="utf-8") as file:
        csv.DictWriter(file, table_dict)
