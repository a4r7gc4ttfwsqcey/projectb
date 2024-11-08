"""This file contains configuration options for the scripts."""

from pathlib import Path

# Set directories
project_root_dir = Path(__file__).resolve().parent
tools_dir = project_root_dir / "tools"
git_clones_dir = project_root_dir / "git_clones"
results_dir = project_root_dir / "results"

# graalvm jdk 23
# https://www.graalvm.org/
# Set JAVA_HOME directory
java_home_dir = tools_dir / "jdk"
java_exec = java_home_dir / "bin" / "java.exe"

# refactoringminer 3.0.9 source
# https://github.com/tsantalis/RefactoringMiner/archive/refs/tags/3.0.9.zip
# Set RefactoringMiner source dir
rf_miner_dir = tools_dir / "rfm"
rf_miner_jar = rf_miner_dir / "build" / "libs" / "RefactoringMiner-3.0.9.jar"

# gradle 8.10.2
# https://services.gradle.org/distributions/gradle-8.10.2-all.zip
# Set gradle paths
gradle_dir = tools_dir / "gradle"
gradle_exec = gradle_dir / "bin" / "gradle.bat"

# scc 3.4.0
# https://github.com/boyter/scc/releases/tag/v3.4.0
# Set scc paths
scc_dir = tools_dir / "scc"
scc_exec = scc_dir / "scc.exe"
