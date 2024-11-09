import shutil
from git_tools import clone_repositories, projects_to_git_urls
from subprocess_tools import run_subprocess
from constants import *
from csv_tools import parse_projects_from_csv

def build_refactoringminer() -> None:
    """Build refactoringminer from source with Gradle."""
    print(f"Build RefactoringMiner (source: {rf_miner_dir!s}) with Gradle (path: {gradle_dir!s})")
    run_subprocess([str(gradle_exec), "jar"], cwd=rf_miner_dir)


def setup_tools() -> None:
    """Set up the required mining tools."""
    if not rf_miner_jar.exists():
        build_refactoringminer()
        return
    print(f"RefactoringMiner already built: {rf_miner_jar!s}")


def main() -> None:
    """Main function to orchestrate all the steps."""
    setup_tools()
    projects = parse_projects_from_csv(input_csv)
    git_urls = projects_to_git_urls(projects)
    clone_repositories(git_urls, git_clones_dir)
    # mine refactoring activity
    # collect diffs into json
    # collect effort
    # mine bug fixes


if __name__ == "__main__":
    main()