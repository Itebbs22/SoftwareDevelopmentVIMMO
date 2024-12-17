import subprocess
import os

def run_scheduler():
    script_path = os.path.join(os.path.dirname(__file__), "setup_cron.sh")
    result = subprocess.run(["bash", script_path], check=True)
    print("Script executed successfully:", result)