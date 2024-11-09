# Set up requirements
1. Clone this repository (Consider a directory near the root of the file system to avoid issues with long paths)
2. Set 'git config --global core.longpaths true' to avoid issues with long paths
3. Download and extract the following into 'tools/' directory:
- GraalVM JDK 23 (binary archive from https://www.graalvm.org/)
- Gradle 8.10.2 (complete distribution archive from https://services.gradle.org/distributions/gradle-8.10.2-all.zip)
- RefactoringMiner 3.0.9 (source package from https://github.com/tsantalis/RefactoringMiner/archive/refs/tags/3.0.9.zip)
- SCC 3.4.0 (binary archive from https://github.com/boyter/scc/releases/tag/v3.4.0)
4. Set correct tool paths in 'constants.py'
5. Install Python 3.12.x (from https://python.org)
6. Install the Pipenv module with 'python3.12 -m pip install pipenv'
7. Create virtual env with 'python3.12 -m pipenv install --python 3.12'
# Run project
1. Run project with 'python3.12 -m pipenv run python main.py'
