#!/bin/bash
set -euo pipefail
# Find the directory where this script is located --> $0 is script being run, realpath gets the absolute path
script_dir=$(dirname "$(realpath "$0")")

# Find the root of the Git repository by tracing up from the script's directory
# git -C "$script_dir" executes the git command as if it is in the script directory
# rev-parse --show-toplevel returns the absolute path to the root of the Git repository
# 2>dev/null redirects stderr to /dev/null, silencing errors
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null)

# If not in a git repo, exit with an error message
# $? gets exit code of last command run (i.e. the repo root command above where i have silenced stderr
if [ $? -ne 0 ]; then
    echo "Error: This script must be run from within a Git repository."
    exit 1
fi

# Run the Python script using the dynamic repo root path
python "$repo_root/vimmo/db/weekly_update.py"