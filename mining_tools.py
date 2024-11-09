from pathlib import Path

from constants import *
from subprocess_tools import run_subprocess

def mine_refactoring_activity(project_repos: list[Path]) -> None:
    """Mine refactoring activity from the projects with RefactoringMiner."""
    rf_cmd = [str(rf_miner_exec)]
    for project_repo in project_repos:
        project_path = project_repo.working_dir
        # CLI option -a for analysing all commits
        mine_args = rf_cmd + ["-a", project_path]
        json_output = run_subprocess(mine_args, cwd=rf_miner_dir)
        result_dir = results_dir.joinpath("rminer-outputs")
        result_dir.mkdir(parents=True, exist_ok=True)
        result_dir.joinpath(project_path.with_suffix(".json").name).write_text(json_output)
