import asyncio
import platform
from git_tools import clone_repositories, projects_to_git_urls
from subprocess_tools import run_subprocess
from constants import *
from csv_tools import parse_projects_from_csv
from mining_tools import mine_diffs, mine_refactoring_activity, mine_effort, mine_bugfixes
from analyze_tools import create_refactoring_results_tables

async def build_refactoringminer() -> bool:
    """Build refactoringminer from source with Gradle."""
    print(f"Build RefactoringMiner (source: {rf_miner_dir!s}) with Gradle (path: {gradle_dir!s})")
    logs_dir = results_dir.joinpath("gradle-logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir.joinpath("gradle.txt")
    await run_subprocess([str(gradle_exec), "distZip"], cwd=rf_miner_dir, log_path=log_path)
    return True


async def unzip_refactoringminer_dist() -> bool:
    """Unpack build refactoringminer zip archive."""
    logs_dir = results_dir.joinpath("unzip-logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir.joinpath("unzip.txt")
    if platform.system() == "Windows":
        await run_subprocess(
            ["powershell.exe", "-Command", f'Expand-Archive -Path {rf_miner_dist_path} -DestinationPath {rf_miner_dist_path.parent}'],
            log_path=log_path)
    else:
        await run_subprocess(
            ["unzip", str(rf_miner_dist_path), "-d", str(rf_miner_dist_path.parent)], log_path=log_path
        )
    return True


async def setup_tools() -> bool:
    """Set up the required mining tools."""
    if not rf_miner_dist_path.exists():
        await build_refactoringminer()
        await unzip_refactoringminer_dist()
        return
    print(f"RefactoringMiner already built: {rf_miner_dist_path!s}")
    return True


async def main() -> bool:
    """Main function to orchestrate all the steps."""
    await setup_tools()
    projects = await parse_projects_from_csv(input_csv)
    git_urls = await projects_to_git_urls(projects)
    cloned_repos = await clone_repositories(git_urls, git_clones_dir)
    mining_results = await mine_refactoring_activity(cloned_repos)
    await create_refactoring_results_tables(mining_results)
    await mine_diffs(cloned_repos)
    await mine_effort(cloned_repos)
    await mine_bugfixes(git_urls)
    return True


if __name__ == "__main__":
    asyncio.run(main())
