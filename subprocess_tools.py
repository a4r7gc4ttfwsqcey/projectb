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


def run_subprocess(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=get_project_env(), check=True, text=True)
