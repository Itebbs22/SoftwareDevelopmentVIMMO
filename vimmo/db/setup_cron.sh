#!/bin/bash

# set -e --> immediately exit if any command has non-zero exit code
# set -u --> reference to any previously undefined variables causes error
# set -o pipefail sets return code of a pipeline to that of the first command that fails, rather than the last executed
set -euo pipefail


# Get the absolute path to the current directory (where the script is being run)
current_dir=$(dirname "$(realpath "$0")")
echo $current_dir

# Find the absolute path to the root of the cloned repo (assuming .git exists at the root)
repo_dir=$(git -C "$current_dir" rev-parse --show-toplevel 2>/dev/null)

# If the repo directory cannot be determined, exit (-z checks if the variable string is empty
if [ -z "$repo_dir" ]; then
  echo "Error: Unable to determine the root directory of the repository."
  exit 1
fi

# Define the cron job schedule based on user input
while true; do
  echo "Choose a schedule:"
  echo "1) Every minute"
  echo "2) Every day at midnight"
  echo "3) Every week at midnight (Sunday)"
  echo "4) Every month at midnight (1st)"
  echo "5) Remove schedule"

  read -p "Enter your choice (1-5): " choice

  case $choice in
    1)
      cron_schedule="* * * * *"  # Every minute
      schedule_text="Every minute"
      break
      ;;
    2)
      cron_schedule="0 0 * * *"  # Every day at midnight
      schedule_text="Every day at midnight"
      break
      ;;
    3)
      cron_schedule="0 0 * * 0"  # Every week on Sunday at midnight
      schedule_text="Every week at midnight (Sunday)"
      break
      ;;
    4)
      cron_schedule="0 0 1 * *"  # Every month on the 1st at midnight
      schedule_text="Every month at midnight (1st)"
      break
      ;;
    5)
      echo "Removing all crontab entries..."
      crontab -r
      echo "All crontab entries removed."
      exit 0
      ;;
    *)
      echo -e "\nInvalid option. Please try again.\n"
      ;;
  esac
done

echo "You selected: $schedule_text"

# Define the script and log file paths relative to the repo root directory
script_path="$repo_dir/vimmo/db/run_updates.sh"   # Adjust to the actual path within the repo
log_file="$repo_dir/vimmo/db/logs/cron_panel_updates.log"  # Adjust the log file path

# Ensure the logs directory exists
mkdir -p "$(dirname "$log_file")"

# Remove the old cron job (if exists) - we assume it's already using the same script path
# crontab -l lists cron jobs, grep -v removes matches to the script path, crontab - overwrites the crontab
crontab -l | grep -v "$script_path" | crontab -

# Find the user's Conda installation path dynamically
# -n checks if the conda_exe var is non-zero, checks if the file path stored in CONDA_EXE points to an executable file.
if [ -n "$CONDA_EXE" ] && [ -x "$CONDA_EXE" ]; then
    conda_path=$(dirname "$CONDA_EXE")   # Get the directory of the Conda executable
else
    echo "Error: Conda is not installed or not configured properly."
    exit 1
fi

# Set up the new cron job, including the steps to source Conda, activate the environment, and execute the script
(crontab -l 2>/dev/null; echo "$cron_schedule cd $repo_dir && /bin/bash -c 'source $conda_path/../etc/profile.d/conda.sh && conda activate VIMMO && /bin/bash $script_path >> $log_file 2>&1'") | crontab -

# Output confirmation with human-readable schedule
echo "Cron job updated to run: $schedule_text"
echo "Log file will be saved to: $log_file"
