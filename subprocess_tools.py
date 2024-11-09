import asyncio
from asyncio.subprocess import PIPE, STDOUT
import os
import subprocess
from constants import *
import aiofiles

async def get_project_env() -> dict[str, str]:
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


async def run_subprocess(
    args: list[str], cwd: Path | None = None, log_path: Path | None = None, quiet: bool = False
) -> str:
    if not quiet:
        print(f"Run subprocess: '{" ".join(args)}' Cwd: '{cwd}' Log path: '{log_path}'")
    if log_path:
        async with aiofiles.open(log_path, "w", encoding="utf-8") as log_file:
            proc = await asyncio.create_subprocess_exec(
                *args, cwd=cwd, env=await get_project_env(),
                stdout=log_file, stderr=log_file
            )
            return await proc.communicate()
    proc = await asyncio.create_subprocess_exec(*args, cwd=cwd, env=await get_project_env(), stdout=PIPE, stderr=STDOUT)
    stdout, _ = await proc.communicate()
    if stdout:
        return stdout.decode("utf-8")
    return ""
