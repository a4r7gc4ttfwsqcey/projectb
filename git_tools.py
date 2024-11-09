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
    """Clone the list of repository links into the chosen directory."""
    repos = list[Repo]
    for url in repository_urls:
        repos.append(Repo.clone_from(url, directory))
    return repos
