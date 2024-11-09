import json
from pathlib import Path
from typing import Any

from git import Commit, Repo
from pydriller import Repository

from analyze_tools import get_refactoring_commits
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
                commit_data["previous_commit_hash"] = commit.parents[0]
            except Exception:
                print(f"No parent for {commit.hash}")
            commit_data["diff_stats"] = {
                "total_add_count": commit.insertions,
                "total_del_count": commit.deletions,
                "files": []
            }
            commit_data["diff_content"] = []
            for file in commit.modified_files:
                if file.added_lines != 0 or file.deleted_lines != 0:
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
        diff_result_json.write_text(json.dumps(commits, indent=4))
        print(f"Repo diff mining complete: {diff_result_json!s}")


def get_commit_loc(repo: Repo, commit: Commit) -> int:
    """Get loc for commit from scc"""
    current_branch = repo.active_branch.name
    repo.git.checkout(commit)
    proc = run_subprocess([str(scc_exec), "--no-complexity", "--no-cocomo"], quiet=True)
    output = proc.stdout or ""
    total_loc: int = 0
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            language = parts[0]
            if language in TIOBE_PROGRAMMING_LANGUAGES_FOR_SCC:
                loc = int(parts[2].replace(",", ""))
                total_loc += loc
    repo.git.checkout(current_branch)
    return total_loc


def mine_effort(project_repos: list[Repo]):
    """Mine effort with scc"""
    for repo in project_repos:
        developer_tloc: dict[str, int] = {}
        ref_commit_tloc: dict[str, int] = {}
        print(f"Mine effort TLOC: {repo!s}")
        tloc_result_dir = results_dir.joinpath("tloc-outputs")
        tloc_result_dir.mkdir(parents=True, exist_ok=True)
        json_fn = Path(repo.working_dir).with_suffix(".json").name
        tloc_result_json = tloc_result_dir.joinpath(json_fn)
        if tloc_result_json.exists():
            print(f"Repo diff already mined: {tloc_result_json!s}")
            continue
        refactoringminer_json = results_dir.joinpath("rminer-outputs", json_fn)
        for commit_sha in get_refactoring_commits(refactoringminer_json):
            developer = repo.commit(commit_sha).author
            if developer not in developer_tloc:
                developer_tloc[developer] = 0
            loc = get_commit_loc(repo, repo.commit(commit_sha))
            try:
                previous_commit = repo.commit(commit_sha).parents[0]
                prev_commit_loc = get_commit_loc(repo, previous_commit)
            except Exception:
                print(f"no previous commit for {commit_sha}")
                continue
            tloc = abs(loc - prev_commit_loc)
            developer_tloc[developer] += tloc
            ref_commit_tloc[commit_sha] = tloc
        tloc_result_json.write_text(json.dumps({"developers": developer_tloc, "refactor_commits": ref_commit_tloc}, indent=4))
        print(f"Effort TLOC mined: {tloc_result_json!s}")


def mine_bugfixes(git_urls: list[str]):
    """Mine bug fixes"""
