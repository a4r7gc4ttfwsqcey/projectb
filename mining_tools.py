from pathlib import Path

from constants import *
from subprocess_tools import run_subprocess

def mine_refactoring_activity(project_repos: list[Path]) -> None:
    """Mine refactoring activity from the projects with RefactoringMiner."""
    rf_cmd = [str(rf_miner_exec)]
    print(f"RefactoringMiner executable: {rf_miner_exec!s}")
    for project_repo in project_repos:
        print(f"Mine project repository: {project_repo!s}")
        project_path = Path(project_repo.working_dir)
        logs_dir = results_dir.joinpath("rminer-logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir.joinpath(project_path.with_suffix(".txt").name)
        result_dir = results_dir.joinpath("rminer-outputs")
        result_dir.mkdir(parents=True, exist_ok=True)
        json_output_path = result_dir.joinpath(project_path.with_suffix(".json").name)
        if not json_output_path.exists():
            # CLI options:
            # -a for analysing all commits
            # -json for output path
            mine_args = rf_cmd + ["-a", str(project_path), "-json", str(json_output_path)]
            run_subprocess(mine_args, cwd=rf_miner_dir, log_path=log_path)
            print(f"Mining completed, results path: {json_output_path!s}")
            continue
        print(f"Repository already mined: {json_output_path!s}")
