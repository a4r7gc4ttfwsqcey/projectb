import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import aiohttp
import bugzilla
from git import Commit, Repo
from jira import JIRA
from pydriller import Repository

from analyze_tools import get_refactoring_commits
from constants import *
from csv_tools import write_table_to_csv
from subprocess_tools import run_subprocess


def split_commit_history(repo: Repo, count: int) -> list[tuple[str, str]]:
    # Get the list of all commits
    commits = list(repo.iter_commits('HEAD', reverse=True))
    # Determine the size of each segment
    split_size = len(commits) // count
    ranges = []
    for i in range(count):
        start_idx = i * split_size
        end_idx = start_idx + split_size if i < count - 1 else len(commits)
        segment = commits[start_idx:end_idx]
        if segment:
            ranges.append((segment[0].hexsha, segment[-1].hexsha))
    return ranges


async def mine_repo_rf_activity_multipart(sem: asyncio.Semaphore, result_dir: Path, logs_dir: Path, project_repo: Repo) -> Path:
    async with sem:
        rf_cmd = [str(rf_miner_exec)]
        print(f"Mine project repository: {project_repo!s}")
        project_path = Path(project_repo.working_dir)
        log_path = logs_dir.joinpath(project_path.with_suffix(".txt").name)
        json_output_path = result_dir.joinpath(project_path.with_suffix(".json").name)
        if json_output_path.exists():
            if log_path.exists():
                if "Analyzed" in log_path.read_text():
                    print(f"Repository already mined: {json_output_path!s}")
                    return json_output_path
                log_path.unlink()
            print(f"Re-trying failed job: {project_repo!s}")
            json_output_path.unlink()
        # 8 part mining
        if "fineract" in str(project_repo.working_dir):
            # Predefined ranges to work around heap size issue with the commits
            range_count = 2
            commits = list(project_repo.iter_commits('HEAD', reverse=True))
            ranges = [
                (commits[0].hexsha, "22b10d933b4eedbdc6a0f99fa23451e4f7870f6d",),
                ("2a445a5862a432dcfb4e49559c3f717ad4d5f26a", commits[-1].hexsha,),
            ]
        if "plc4x" in str(project_repo.working_dir):
            # Predefined ranges to work around miner hang issue with the commits
            range_count = 2
            commits = list(project_repo.iter_commits('HEAD', reverse=True))
            ranges = [
                (commits[0].hexsha, "deb4a19433441de8a92dd8a223106e88996bce6a",),
                ("7ed0a80f6dbbf02d3de94751d27ae1068f6c611a", "673de2c62b5af77d13b72ffe9e4f3dc2ec7a34bd",),
                ("2663b5d08372039b33a58c15cebd5bc111f7732e", commits[-1].hexsha,),
            ]
        else:
            range_count = 8
            ranges = split_commit_history(project_repo, range_count)
        # CLI options:
        # -bc for analysing commit range
        # -json for output path
        count = 0
        parts = []

        for start, end in ranges:
            mine_args = rf_cmd + ["-bc", str(project_path), start, end, "-json", str(json_output_path.with_suffix(f".json.part{count}"))]
            await run_subprocess(mine_args, cwd=rf_miner_dir, log_path=log_path.with_suffix(f".txt.part{count}"))
            if "Analyzed" in log_path.with_suffix(f".txt.part{count}").read_text():
                print(f"Mining part{count} completed")
                parts.append(json_output_path.with_suffix(f".json.part{count}"))
            count += 1
        if len(parts) != range_count:
            print(f"Mining failed, check logs: {log_path.with_suffix(".txt.part*")!s}")
        final_json_obj = []
        for part in parts:
            for obj in json.loads(part.read_text())["commits"]:
                final_json_obj.append(obj)
        json_output_path.write_text(json.dumps({"commits": final_json_obj}, indent=4))
        log_path.write_text("Analyzed")
        print(f"Mining completed, results path: {json_output_path!s}")
        return json_output_path


async def mine_repo_rf_activity(sem: asyncio.Semaphore, result_dir: Path, logs_dir: Path, project_repo: Repo) -> Path:
    if "fineract" in str(project_repo.working_dir) or "plc4x" in str(project_repo.working_dir):
        print(f"Multipart mining: {project_repo}")
        return await mine_repo_rf_activity_multipart(sem, result_dir, logs_dir, project_repo)
    async with sem:
        rf_cmd = [str(rf_miner_exec)]
        print(f"Mine project repository: {project_repo!s}")
        project_path = Path(project_repo.working_dir)
        log_path = logs_dir.joinpath(project_path.with_suffix(".txt").name)
        json_output_path = result_dir.joinpath(project_path.with_suffix(".json").name)
        if json_output_path.exists():
            if log_path.exists():
                if "Analyzed" in log_path.read_text():
                    print(f"Repository already mined: {json_output_path!s}")
                    return json_output_path
                log_path.unlink()
            print(f"Re-trying failed job: {project_repo!s}")
            json_output_path.unlink()
        # CLI options:
        # -a for analysing all commits
        # -json for output path
        mine_args = rf_cmd + ["-a", str(project_path), "-json", str(json_output_path)]
        await run_subprocess(mine_args, cwd=rf_miner_dir, log_path=log_path)
        if "Analyzed" in log_path.read_text():
            print(f"Mining completed, results path: {json_output_path!s}")
            return json_output_path
        print(f"Mining failed, check log: {log_path!s}")


async def mine_refactoring_activity(project_repos: list[Repo]) -> list[Path]:
    """Mine refactoring activity from the projects with RefactoringMiner."""
    print(f"RefactoringMiner executable: {rf_miner_exec!s}")
    result_dir = results_dir.joinpath("rminer-outputs")
    result_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = results_dir.joinpath("rminer-logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(16)
    tasks = [mine_repo_rf_activity(sem, result_dir, logs_dir, project_repo) for project_repo in project_repos]
    results: list[Path] = await asyncio.gather(*tasks)
    return results


async def get_commit_diff_data_from_repo(sem: asyncio.Semaphore, diff_result_dir: Path, repo: Repo) -> bool:
    """Mine diff for a repo."""
    async with sem:
        commits: list = []
        print(f"Mine diff: {repo!s}")
        diff_result_json = diff_result_dir.joinpath(Path(repo.working_dir).with_suffix(".json").name)
        if diff_result_json.exists():
            print(f"Repo diff already mined: {diff_result_json!s}")
            return False
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
        return True


async def mine_diffs(project_repos: list[Repo]) -> bool:
    """Mine diffs with pydriller."""
    diff_result_dir = results_dir.joinpath("diff-outputs")
    diff_result_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(100)
    tasks = [get_commit_diff_data_from_repo(sem, diff_result_dir, repo) for repo in project_repos]
    await asyncio.gather(*tasks)
    return True


async def get_commit_loc(repo: Repo, commit: Commit) -> int:
    """Get loc for commit from scc"""
    # try:
    #     current_branch = repo.active_branch.name
    # except:
    #     current_branch = "origin/HEAD"
    repo.git.reset("--hard")
    repo.git.clean("-fdx")
    repo.git.checkout("--force", commit)
    output = await run_subprocess([str(scc_exec), "--no-complexity", "--no-cocomo"], cwd=repo.working_dir, quiet=True)
    total_loc: int = 0
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            language = parts[0]
            if language in TIOBE_PROGRAMMING_LANGUAGES_FOR_SCC:
                loc = int(parts[2].replace(",", ""))
                total_loc += loc
    #repo.git.checkout(current_branch)
    return total_loc


async def mine_effort_for_repo(sem: asyncio.Semaphore, tloc_result_dir: Path, repo: Repo) -> bool:
    async with sem:
        developer_dict = {}
        print(f"Mine effort TLOC: {repo!s}")
        repo.git.checkout("origin/HEAD")
        json_fn = Path(repo.working_dir).with_suffix(".json").name
        tloc_result_dir = tloc_result_dir / Path(repo.working_dir).name
        tloc_result_dir_temp = tloc_result_dir.with_suffix(".UNFINISHED")
        if tloc_result_dir_temp.exists():
            print(f"Remove incomplete: {tloc_result_dir_temp!s}")
            shutil.rmtree(tloc_result_dir_temp)
        if tloc_result_dir.exists():
            print(f"Repo TLOC already mined: {tloc_result_dir!s}")
            return False
        tloc_result_dir_temp.mkdir(parents=True)
        refactoringminer_json = results_dir.joinpath("rminer-outputs", json_fn)
        refactoring_commits = await get_refactoring_commits(refactoringminer_json)
        if not refactoring_commits:
            print(f"Repo contains no refactoring commits: {tloc_result_dir.name}")
        for commit_sha in refactoring_commits:
            developer = repo.commit(commit_sha).author.name
            if not developer:
                print(f"Empty developer name")
                developer = "Unknown"
            if developer not in developer_dict:
                developer_dict[developer] = {
                    "refactoring_hash": [],
                    "previous_commit_hash": [],
                    "TLOC": [],
                }
            loc = await get_commit_loc(repo, repo.commit(commit_sha))
            try:
                previous_commit = repo.commit(commit_sha).parents[0]
                prev_commit_loc = await get_commit_loc(repo, previous_commit)
            except Exception:
                print(f"no previous commit for {commit_sha}")
                continue
            tloc = abs(loc - prev_commit_loc)
            developer_dict[developer]["refactoring_hash"].append(commit_sha)
            developer_dict[developer]["previous_commit_hash"].append(previous_commit.hexsha)
            developer_dict[developer]["TLOC"].append(tloc)
        for dev in developer_dict:
            tloc_result_csv = tloc_result_dir_temp.joinpath(dev.replace("/", "_")).with_suffix(".csv")
            await write_table_to_csv(tloc_result_csv, developer_dict[dev])
        tloc_result_dir_temp.rename(tloc_result_dir)
        print(f"Effort TLOC mined: {tloc_result_dir!s}")
        return True


async def mine_effort(project_repos: list[Repo]) -> bool:
    """Mine effort with scc"""
    tloc_result_dir = results_dir.joinpath("tloc-outputs")
    tloc_result_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(100)
    tasks = [mine_effort_for_repo(sem, tloc_result_dir, repo) for repo in project_repos]
    await asyncio.gather(*tasks)
    return True


async def uses_github_issue_tracker_system(session: aiohttp.ClientSession, git_url: str) -> bool:
    """Return whether a project at URL uses GitHub ITS."""
    git_url = git_url.rsplit(".git")[0]
    parts = git_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]
    repo_metadata_endpoint = f"https://api.github.com/repos/{owner}/{repo}"
    token = github_api_key
    headers = {"Authorization": f"token {token}"} if token else {}
    print(f"Request {repo_metadata_endpoint}")
    async with session.get(repo_metadata_endpoint, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("has_issues", False) in ("true", True)
        if response.status in (403, 429):
            await asyncio.sleep(3601)  # sleep 1 hour on rate limit
            return await uses_github_issue_tracker_system(session, git_url)
        raise Exception(f"unable to determine github repo issue system, http error {response.status}")
    return True


async def mine_from_github(session: aiohttp.ClientSession, result_dir: Path, git_url: str) -> bool:
    """Mine bug fixes from GitHub."""
    json_fn = Path(git_url).with_suffix(".json").name
    if result_dir.joinpath(json_fn).exists():
        print(f"Repo already mined: {json_fn.rsplit(".", maxsplit=1)[0]!s}")
        return False
    result_json = result_dir.joinpath(json_fn)
    git_url = git_url.rsplit(".git")[0]
    parts = git_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]
    issue_metadata_endpoint = f"https://api.github.com/repos/{owner}/{repo}/issues"
    token = github_api_key
    headers = {"Authorization": f"token {token}"} if token else {}
    print(f"Request {issue_metadata_endpoint}")
    page = 0
    json_data: list[dict[str, Any]] = []
    while True:
        params = {
            "per_page": "100",
            "page": page
        }
        
        async with session.get(issue_metadata_endpoint, headers=headers, params=params) as response:
            if response.status == 200:
                if page == 0:
                    json_data = await response.json()
                else:
                    json_data.extend(await response.json())
                if "Link" not in response.headers:
                    break
                links = response.headers['Link'].split(',')
                if any(['rel="next"' in link for link in links]):
                    page += 1
                else:
                    break
            elif response.status in (403, 429):
                await asyncio.sleep(3601)  # sleep 1 hour on rate limit
                return await mine_from_github(session, result_dir, git_url)
            else:
                raise Exception(f"unable to fetch issues from github, http error {response.status}")
    result_json.write_text(json.dumps(json_data, indent=4))
    return True


async def mine_from_jira(result_dir: Path, git_url: str, key: str) -> bool:
    """Mine bug fixes from Jira."""
    txt_fn = Path(git_url).with_suffix(".txt").name
    result_txt = result_dir.joinpath(txt_fn)
    if result_txt.exists():
        print(f"Repo already mined: {txt_fn.rsplit(".", maxsplit=1)[0]!s}")
        return False
    jira_result_json = result_dir.joinpath("jira_projects", f"{key}.json")
    if jira_result_json.exists():
        print(f"Jira project already mined: {key}")
        result_txt.write_text('"' + str(jira_result_json) + '"')
        return False
    # Mine Jira issues
    jira = JIRA("https://issues.apache.org/jira")
    json_data = []
    issues = jira.search_issues(f'project = {key}', maxResults=False)
    for issue in issues:
        json_data.append(issue.raw)
    jira_result_json.write_text(json.dumps(json_data, indent=4))
    result_txt.write_text('"' + str(jira_result_json) + '"')
    return True


async def mine_from_bugzilla(result_dir: Path, git_url: str) -> bool:
    """Mine bug fixes from Bugzilla."""
    json_fn = Path(git_url).with_suffix(".json").name
    result_json = result_dir.joinpath(json_fn)
    if result_json.exists():
        print(f"Repo already mined: {json_fn.rsplit(".", maxsplit=1)[0]!s}")
        return False
    bz = bugzilla.Bugzilla("https://bz.apache.org/bugzilla/rest.cgi/", force_rest=True)
    if "ant" in git_url:
        project_name = "Ant"
    else:
        project_name = Path(git_url).with_suffix("").name.upper()
    q = {'product': project_name}
    bugs = bz.query(q)
    json_data = []
    for bug in bugs:
        json_data.append(bug.get_raw_data())
    result_json.write_text(json.dumps(json_data, indent=4))
    print(f"Bugzilla bugs mined: {project_name} {result_json}")
    return True


async def get_jira_project_key(input: str) -> str:
    input = Path(input).with_suffix("").name
    try:
        # cached in function attribute value
        jprojects = get_jira_project_key.jprojects
    except Exception:
        # fetch only when required
        jira = JIRA("https://issues.apache.org/jira/")
        get_jira_project_key.jprojects = jira.projects()
        jprojects = get_jira_project_key.jprojects
    for jp in jprojects:
        input = input.replace("-", " ")
        input = input.replace("incubator ", "")
        input = input.replace("logging ", "")
        input = input.replace("hadoop ", "")
        input = input.replace(" extensions", "")
        input = input.replace(" sandbox", "")
        input = input.replace(" jbig2", "")
        if input == "isis":
            input = "causeway"
        if input.startswith("sling"):
            input = "sling"
        if input == jp.name.lower():
            return jp.key
        if input == jp.name.lower().replace("apache ", ""):
            return jp.key
        if input == jp.name.lower().replace(" 2", ""):
            return jp.key
        if input == jp.name.lower().replace("apache ", "").rsplit(" ", maxsplit=1)[0]:
            return jp.key
        if "fineract cn" in input and jp.name == "Fineract Cloud Native":
            return jp.key
        if "jackrabbit filevault" in input and jp.name == "Jackrabbit FileVault":
            return jp.key
        if "ofbiz " in input and jp.name == "OFBiz":
            return jp.key
        if input.split(" ", maxsplit=1)[0] == jp.name:
            return jp.key
    return "UNRESOLVED"


async def mine_bugfixes_for_repo(
    sem: asyncio.Semaphore, gh_result_dir: Path, bz_result_dir: Path, jira_result_dir: Path, git_url: str
) -> bool:
    """Mine bug fixes."""
    async with sem:
        json_fn = Path(git_url).with_suffix(".json").name
        if gh_result_dir.joinpath(json_fn).exists() or jira_result_dir.joinpath(json_fn).exists():
            print(f"Repo already mined: {json_fn.rsplit(".", maxsplit=1)[0]!s}")
            return False
        async with aiohttp.ClientSession() as session:
            if await uses_github_issue_tracker_system(session, git_url):
                print(f"Mine repo bugfixes (Github): {git_url!s}")
                await mine_from_github(session, gh_result_dir, git_url)
                return True
            jira_key = await get_jira_project_key(git_url)
            if jira_key == "UNRESOLVED":
                await mine_from_bugzilla(bz_result_dir, git_url)
            else:
                print(f"Mine repo bugfixes (Jira): {git_url!s}")
                await mine_from_jira(jira_result_dir, git_url, jira_key)
        return True


async def mine_bugfixes(git_urls: list[str]) -> bool:
    """Mine bug fixes."""
    gh_result_dir = results_dir.joinpath("bugfixes-github")
    jira_result_dir = results_dir.joinpath("bugfixes-jira")
    bz_result_dir = results_dir.joinpath("bugfixes-bugzilla")
    for directory in gh_result_dir, jira_result_dir, bz_result_dir, jira_result_dir / "jira_projects":
        directory.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(10)
    tasks = [
        mine_bugfixes_for_repo(sem, gh_result_dir, bz_result_dir, jira_result_dir, git_url)
        for git_url in git_urls
    ]
    await asyncio.gather(*tasks)
    return True
