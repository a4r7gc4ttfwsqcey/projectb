import platform
from git_tools import clone_repositories, projects_to_git_urls
from subprocess_tools import run_subprocess
from constants import *
from csv_tools import parse_projects_from_csv
from mining_tools import mine_refactoring_activity

def build_refactoringminer() -> None:
    """Build refactoringminer from source with Gradle."""
    print(f"Build RefactoringMiner (source: {rf_miner_dir!s}) with Gradle (path: {gradle_dir!s})")
    run_subprocess([str(gradle_exec), "distZip"], cwd=rf_miner_dir)


def unzip_refactoringminer_dist() -> None:
    """Unpack build refactoringminer zip archive."""
    if platform.system() == "Windows":
        run_subprocess(["powershell.exe", "-Command", f'Expand-Archive -Path {rf_miner_dist_path} -DestinationPath {rf_miner_dist_path.parent}'])
    else:
        run_subprocess(["unzip", str(rf_miner_dist_path), "-d", str(rf_miner_dist_path.parent)])


def setup_tools() -> None:
    """Set up the required mining tools."""
    if not rf_miner_dist_path.exists():
        build_refactoringminer()
        unzip_refactoringminer_dist()
        return
    print(f"RefactoringMiner already built: {rf_miner_dir!s}")


def main() -> None:
    """Main function to orchestrate all the steps."""
    setup_tools()
    projects = parse_projects_from_csv(input_csv)
    git_urls = projects_to_git_urls(projects)
    cloned_repos = clone_repositories(git_urls, git_clones_dir)
    mine_refactoring_activity(cloned_repos)
    # collect diffs into json
    # collect effort
    # mine bug fixes


if __name__ == "__main__":
    main()