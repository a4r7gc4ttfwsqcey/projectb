import asyncio
from datetime import datetime
import json
from typing import Any
from csv_tools import write_table_to_csv
from constants import *
from subprocess_tools import run_subprocess
from git_tools import get_commit_timestamp


async def calculate_inter_ref_period(timestamp: datetime, prev_timestamp: datetime) -> float:
    time_diff = (prev_timestamp - timestamp).total_seconds()
    return time_diff


async def calculate_metrics(repo_name: str, json_dict: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """Perform analysis on the json dictionary object."""
    ref_types: set[str] = set()
    inter_ref_times: dict[str, list[str]] = {}
    total_refs: dict[str, int] = {}
    ref_types_row: list[str] = []
    inter_ref_times_row: list[str] = []
    total_refs_row: list[str] = []
    prev_timestamp = None
    commit_timestamp = None
    for commit in json_dict.get("commits", []):
        for ref in commit.get("refactorings", []):
            ref_type = ref.get("type", "Unknown")
            ref_types.add(ref_type)
            if commit_timestamp:
                prev_timestamp = commit_timestamp
            commit_timestamp = await get_commit_timestamp(repo_name, commit.get("sha1"))
            if prev_timestamp:
                time_diff = await calculate_inter_ref_period(commit_timestamp, prev_timestamp)
            else:
                time_diff: float = 0.0
            if inter_ref_times.get(ref_type) is None:
                inter_ref_times[ref_type] = [time_diff]
            else:
                inter_ref_times[ref_type].append(time_diff)
            if total_refs.get(ref_type) is None:
                total_refs[ref_type] = 1
            else:
                total_refs[ref_type] += 1
    for key in ref_types:
        ref_types_row.append(key)
        if inter_ref_times.get(key):
            inter_ref_times_row.append(sum(inter_ref_times.get(key)) / len(inter_ref_times.get(key)))
        else:
            inter_ref_times_row.append("Unknown")
        total_refs_row.append(str(total_refs.get(key, 0)))
    return ref_types_row, inter_ref_times_row, total_refs_row


async def create_refactoring_results_table(tables_dir: Path, result: Path) -> bool:
    """Collect refactoringminer result into a table format."""
    print(f"Analyze: {result!s}")
    table_path = tables_dir.joinpath(result.with_suffix(".csv").name)
    if table_path.exists():
        print(f"Already analyzed, see table: {table_path!s}")
        return False
    refactorings = json.loads(result.read_text())
    ref_types, inter_ref_times, total_refs = await calculate_metrics(result.with_suffix("").name, refactorings)
    table_contents: dict[str, list[str]] = {
        "Refactoring Type": ref_types,
        "Average Time of the Inter-Refactoring period": inter_ref_times,
        "Total Number of Refactorings": total_refs,
    }
    await write_table_to_csv(table_path, table_contents)
    print(f"Analysis complete, saved resulting table: {table_path!s}")
    return True


async def create_refactoring_results_tables(result_paths: list[Path]) -> None:
    """Collect refactoringminer results into a table format."""
    tables_dir = results_dir.joinpath("refactoring-tables")
    tables_dir.mkdir(parents=True, exist_ok=True)
    tasks = [create_refactoring_results_table(tables_dir, result) for result in result_paths]
    await asyncio.gather(*tasks)


async def get_refactoring_commits(json_file: Path) -> list[str]:
    refactorings = json.loads(json_file.read_text())
    refactor_commit_shas: list[str] = []
    for commit in refactorings.get("commits", []):
        if commit.get("refactorings", []):
            refactor_commit_shas.append(commit.get("sha1"))
    return refactor_commit_shas
