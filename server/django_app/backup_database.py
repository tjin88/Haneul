import os
import subprocess
import datetime
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Environment variables for Supabase database
SUPABASE_DB_NAME = os.getenv('postgresql_supabase_name')
SUPABASE_DB_USER = os.getenv('postgresql_supabase_user')
SUPABASE_DB_PASSWORD = os.getenv('postgresql_supabase_password')
SUPABASE_DB_HOST = os.getenv('postgresql_supabase_host')
SUPABASE_DB_PORT = os.getenv('postgresql_supabase_port', '5432')

# Get the current timestamp
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# Backup directory and file path
backup_dir = 'backups'
log_file_path = 'out/backups/supabase_backup_log.txt'
backup_file_path = os.path.join(backup_dir, f"backup_{SUPABASE_DB_NAME}_{timestamp}.sql")

# Ensure the backup and log directories exist
os.makedirs(backup_dir, exist_ok=True)
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# Setting up the logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler(log_file_path, maxBytes=10485760, backupCount=5),  # 10MB per file, max 5 files
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("BackupLogger")

# Function to perform the backup
def backup_database():
    try:
        # Command to dump the database
        dump_command = f"pg_dump --dbname=postgresql://{SUPABASE_DB_USER}:{SUPABASE_DB_PASSWORD}@{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME} -f {backup_file_path}"
        
        # Execute the command
        subprocess.run(dump_command, shell=True, check=True)
        logger.info(f"Database backup successful: {backup_file_path}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during backup: {e}")

# Main function
if __name__ == "__main__":
    backup_database()
