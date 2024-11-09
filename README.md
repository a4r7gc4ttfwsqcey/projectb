# Set up requirements
1. Clone this repository (To avoid path length limitations, consider a directory near the root)
2. Download and extract the following into 'tools/' directory:
- GraalVM JDK 23 (binary archive from https://www.graalvm.org/)
- Gradle 8.10.2 (complete distribution archive from https://services.gradle.org/distributions/gradle-8.10.2-all.zip)
- RefactoringMiner 3.0.9 (source package from https://github.com/tsantalis/RefactoringMiner/archive/refs/tags/3.0.9.zip)
- SCC 3.4.0 (binary archive from https://github.com/boyter/scc/releases/tag/v3.4.0)
3. Set correct tool paths in 'constants.py'
4. Install Python 3.12.x (from https://python.org)
5. Install the Pipenv module with 'python3.12 -m pip install pipenv'
6. Create virtual env with 'python3.12 -m pipenv install --python 3.12'
# Run project
1. Run project with 'python3.12 -m pipenv run python main.py'
