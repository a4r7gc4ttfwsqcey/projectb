from pathlib import Path
from pydriller import Repository
from git import Repo

def clone_repositories(repository_urls: list[str], directory: Path) -> list[Repo]:
    repos = list[Repo]
    for url in repository_urls:
        repos.append(Repo.clone_from(url, directory))
    return repos
