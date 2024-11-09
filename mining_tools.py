import json
from pathlib import Path
from typing import Any

from git import Repo
from pydriller import Repository

from constants import *
from subprocess_tools import run_subprocess

def mine_refactoring_activity(project_repos: list[Repo]) -> list[Path]:
    """Mine refactoring activity from the projects with RefactoringMiner."""
    rf_cmd = [str(rf_miner_exec)]
    print(f"RefactoringMiner executable: {rf_miner_exec!s}")
    results: list[Path] = []
    result_dir = results_dir.joinpath("rminer-outputs")
    result_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = results_dir.joinpath("rminer-logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    for project_repo in project_repos:
        print(f"Mine project repository: {project_repo!s}")
        project_path = Path(project_repo.working_dir)
        log_path = logs_dir.joinpath(project_path.with_suffix(".txt").name)
        json_output_path = result_dir.joinpath(project_path.with_suffix(".json").name)
        results.append(json_output_path)
        if not json_output_path.exists():
            # CLI options:
            # -a for analysing all commits
            # -json for output path
            mine_args = rf_cmd + ["-a", str(project_path), "-json", str(json_output_path)]
            run_subprocess(mine_args, cwd=rf_miner_dir, log_path=log_path)
            print(f"Mining completed, results path: {json_output_path!s}")
            continue
        print(f"Repository already mined: {json_output_path!s}")
    return results


def mine_diffs(project_repos: list[Repo]):
    """Mine diffs with pydriller."""
    commits: list = []
    for repo in project_repos:
        print(f"Mine diff: {repo!s}")
        diff_result_dir = results_dir.joinpath("diff-outputs")
        diff_result_dir.mkdir(parents=True, exist_ok=True)
        diff_result_json = diff_result_dir.joinpath(Path(repo.working_dir).with_suffix(".json").name)
        if diff_result_json.exists():
            print(f"Repo diff already mined: {diff_result_json!s}")
            continue
        repository = Repository(repo.working_dir)
        for commit in repository.traverse_commits():
            commit_data: dict[str, str | list[Any], dict[str, int | list[dict[str, int | str]]]] = {}
            commit_data["commit_hash"] = commit.hash
            try:
                commit_data["previous_commit_hash"] = commit.parents.pop()
            except Exception:
                print(f"No parent for {commit.hash}")
            commit_data["diff_stats"] = {
                "total_add_count": commit.insertions,
                "total_del_count": commit.deletions,
                "files": []
            }
            commit_data["diff_content"] = []
            for file in commit.modified_files:
                commit_data["diff_stats"]["files"].append(
                    {
                    "file": file.filename,
                    "add_count": file.added_lines,
                    "del_count": file.deleted_lines,
                    },
                ),
                commit_data["diff_content"].append(
                    {
                        "file": file.filename,
                        "diff": file.diff,
                    }
                )
            commits.append(commit_data)
        diff_result_json.write_text(json.dumps(commits))
        print(f"Repo diff mining complete: {diff_result_json!s}")


def mine_effort(project_repos: list[Repo]):
    """Mine effort with scc"""
    for repo in project_repos:
        repository = Repository(repo.working_dir)
        for commit in repository.traverse_commits():
            pass


def mine_bugfixes(git_urls: list[str]):
    """Mine bug fixes"""
