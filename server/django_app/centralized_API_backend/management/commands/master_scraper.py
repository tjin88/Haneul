import subprocess
import os
import logging
from logging.handlers import RotatingFileHandler

def get_next_log_file_name(base_dir, base_filename):
    counter = 0
    while True:
        log_file_name = f"{base_filename}_{counter}.txt" if counter else f"{base_filename}.txt"
        full_path = os.path.join(base_dir, log_file_name)
        if not os.path.exists(full_path):
            return full_path
        counter += 1

# Setting up the logging configuration
log_directory = "../out/Master"
log_base_filename = "masterScraper"
log_file_path = get_next_log_file_name(log_directory, log_base_filename)

# Ensure the log directory exists
os.makedirs(log_directory, exist_ok=True)

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler(log_file_path, maxBytes=10485760, backupCount=5),  # 10MB per file, max 5 files of size 10 MB
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define the child folder containing your scripts
scripts_folder = "scraping_scripts"

# List of scripts that should not be run
scripts_to_ignore = [
    "scrapeAryaScans.py",
    "scrapeYakshaScans.py"
]

# Get all Python scripts in the child folder
all_runnable_scripts = [f for f in os.listdir(scripts_folder) if f.endswith('.py') and f not in scripts_to_ignore]

# Iterate over each runnable script and call it
for script in all_runnable_scripts:
    script_path = os.path.join(scripts_folder, script)
    try:
        result = subprocess.run(["python", script_path], check=True, capture_output=True, text=True)
        logger.info(f"Output of {script}:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred while running {script}:\n{e.stderr}")

logger.info("All runnable scripts executed.")
