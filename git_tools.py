from pathlib import Path
from pydriller import Repository
from git import Repo


def projects_to_git_urls(projects: set[str]) -> set[str]:
    """Transform apache project names to GitHub repository links."""
    return {
        f"https://github.com/apache/{p.split("_", maxsplit=1)[1]}.git"
        for p in projects
    }


def clone_repositories(repository_urls: list[str], directory: Path) -> list[Repo]:
    """Clone the list of repository links into subdirs in the chosen directory.

    If the project is already cloned, skip it.
    """
    repos: list[Repo] = []
    directory.mkdir(exist_ok=True, parents=True)
    for url in repository_urls:
        subdir = directory / Path(url).with_suffix("").name
        print(f"Clone repository from {url} to {subdir}")
        if not subdir.exists():
            repos.append(Repo.clone_from(url, subdir))
            continue
        print(f"Skipping, repository already cloned into {subdir}")
        repos.append(Repo(subdir))
    return repos
