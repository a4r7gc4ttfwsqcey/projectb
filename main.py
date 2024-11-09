import platform
from git_tools import clone_repositories, projects_to_git_urls
from subprocess_tools import run_subprocess
from constants import *
from csv_tools import parse_projects_from_csv
from mining_tools import mine_diffs, mine_refactoring_activity, mine_effort, mine_bugfixes
from analyze_tools import create_refactoring_results_tables

def build_refactoringminer() -> None:
    """Build refactoringminer from source with Gradle."""
    print(f"Build RefactoringMiner (source: {rf_miner_dir!s}) with Gradle (path: {gradle_dir!s})")
    logs_dir = results_dir.joinpath("gradle-logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir.joinpath("gradle.txt")
    run_subprocess([str(gradle_exec), "distZip"], cwd=rf_miner_dir, log_path=log_path)


def unzip_refactoringminer_dist() -> None:
    """Unpack build refactoringminer zip archive."""
    logs_dir = results_dir.joinpath("unzip-logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir.joinpath("unzip.txt")
    if platform.system() == "Windows":
        run_subprocess(
            ["powershell.exe", "-Command", f'Expand-Archive -Path {rf_miner_dist_path} -DestinationPath {rf_miner_dist_path.parent}'],
            log_path=log_path)
    else:
        run_subprocess(
            ["unzip", str(rf_miner_dist_path), "-d", str(rf_miner_dist_path.parent)], log_path=log_path
        )


def setup_tools() -> None:
    """Set up the required mining tools."""
    if not rf_miner_dist_path.exists():
        build_refactoringminer()
        unzip_refactoringminer_dist()
        return
    print(f"RefactoringMiner already built: {rf_miner_dist_path!s}")


def main() -> None:
    """Main function to orchestrate all the steps."""
    setup_tools()
    projects = parse_projects_from_csv(input_csv)
    git_urls = projects_to_git_urls(projects)
    cloned_repos = clone_repositories(git_urls, git_clones_dir)
    mining_results = mine_refactoring_activity(cloned_repos)
    create_refactoring_results_tables(mining_results)
    mine_diffs(cloned_repos)
    mine_effort(cloned_repos)
    mine_bugfixes(git_urls)


if __name__ == "__main__":
    main()