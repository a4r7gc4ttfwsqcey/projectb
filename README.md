# Set up requirements
1. Clone this repository (Consider a directory near the root of the file system to avoid issues with long paths)
2. Save input sonar_measures.csv file to git repository root.
3. Set 'git config --global core.longpaths true' to avoid issues with long paths
4. Download and extract the following into 'tools/' directory:
- GraalVM JDK 23 (binary archive from https://www.graalvm.org/)
- Gradle 8.10.2 (complete distribution archive from https://services.gradle.org/distributions/gradle-8.10.2-all.zip)
- RefactoringMiner 3.0.9 (source package from https://github.com/tsantalis/RefactoringMiner/archive/refs/tags/3.0.9.zip)
- SCC 3.4.0 (binary archive from https://github.com/boyter/scc/releases/tag/v3.4.0)
5. Generate an API token for Github, save it as 'GITHUB_API_KEY' file in git repository root.
6. Set correct paths and other configuration values in 'constants.py'
7. Install Python 3.12.x (from https://python.org)
8. Install the Pipenv module with 'python3.12 -m pip install pipenv'
9. Create virtual env with 'python3.12 -m pipenv install --python 3.12'
# Run project
1. Run project with 'python3.12 -m pipenv run python main.py'
