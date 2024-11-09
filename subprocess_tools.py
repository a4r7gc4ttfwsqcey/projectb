import os
import subprocess
from constants import *


def get_project_env():
    env: dict[str, str] = os.environ.copy()
    # Set JAVA_HOME
    env["JAVA_HOME"] = str(java_home_dir)
    # Set PATH
    env["PATH"] = os.pathsep.join(
        (
            str(java_home_dir / "bin"),
            str(gradle_dir / "bin"),
            env["PATH"]
        )
    )
    return env


def run_subprocess(
    args: list[str], cwd: Path | None = None, log_path: Path | None = None, quiet: bool = False
) -> subprocess.CompletedProcess[str]:
    if not quiet:
        print(f"Run subprocess: '{" ".join(args)}' Cwd: '{cwd}' Log path: '{log_path}'")
    if log_path:
        with log_path.open("w", encoding="utf-8") as log_file:
            return subprocess.run(
                args, cwd=cwd, env=get_project_env(), check=True, text=True,
                stdout=log_file, stderr=log_file
            )
    return subprocess.run(args, cwd=cwd, env=get_project_env(), check=True, text=True, capture_output=True)
