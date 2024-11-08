from git_tools import clone_repositories
from subprocess_tools import run_subprocess
from constants import *


def build_refactoringminer() -> None:
    run_subprocess([str(gradle_exec), "jar"], cwd=rf_miner_dir)


def setup_tools() -> None:
    build_refactoringminer()


def main() -> None:
    setup_tools()
    # gather repositories from csv
    # clone_repositories()
    # mine refactoring activity
    # collect diffs into json
    # collect effort
    # mine bug fixes


if __name__ == "__main__":
    main()