from datetime import datetime
from pathlib import Path
from git import Repo
from constants import *

def projects_to_git_urls(projects: set[str]) -> set[str]:
    """Transform apache project names to GitHub repository links."""
    project_urls: str[str] = set()
    for p in projects:
        if p.startswith("apache_"):
            p = p.split("_", maxsplit=1)[1]
        if p.startswith("apache-"):
            p = p.split("-", maxsplit=1)[1]
        if "log4cxx" in p:
            p = f"logging-{p}"
        if any(name in p for name in ("knox", "jspwiki", "ant-master", "nemo", "milagro", "pdfbox", "poi-parent", "roller-master")):
            p = p.split("-", maxsplit=1)[0]
            if ":" in p:
                p = "incubator-" + p.split(":", maxsplit=1)[1]
            if "milagro" in p:
                p = "incubator-" + p
        project_urls.add(f"https://github.com/apache/{p}.git")
    return project_urls


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


def get_commit_timestamp(repo_name: str, commit_sha1: str) -> datetime:
    repo_path = git_clones_dir / repo_name
    repository = Repo(repo_path)
    commit = repository.commit(commit_sha1)
    return commit.committed_datetime
