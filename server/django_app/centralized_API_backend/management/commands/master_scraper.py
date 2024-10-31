# Took 1h 7m 12s to scrape BoxNovel
# Took 1h 32m 59s for the full master scraper to complete
# Thus, took 25m 47s to scrape everything except BoxNovel (31 sources)
# TODO: In this script, once we've run all scrapers, 
# TODO: we should run a script to ensure there are no invalid chapter links or books w 0 chapters.
# TODO: Also check the book images, and replace all invalid images with null for faster indexing.
import datetime
import subprocess
import os
import logging
from logging.handlers import RotatingFileHandler
from django.core.management.base import BaseCommand, CommandError
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Command(BaseCommand):
    help = 'Runs all scraping scripts and updates the database.'

    def handle(self, *args, **kwargs):
        """
        Handles the command execution for scraping light novels.

        Executes the scraping process, calculates the duration of the operation, and logs the result.
        """
        # Setting up the logging configuration
        log_directory = "../out/Master"
        log_base_filename = "masterScraper"
        log_file_path = self.get_next_log_file_name(log_directory, log_base_filename)

        # Ensure the log directory exists
        os.makedirs(log_directory, exist_ok=True)

        # Setup logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                RotatingFileHandler(log_file_path, maxBytes=10485760, backupCount=10),  # 10MB per file, max 10 files of size 10 MB
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)

        # Define the correct path to the scripts folder
        scripts_folder = os.path.join(os.path.dirname(__file__), 'scraping_scripts')

        # List of scripts that should not be run
        scripts_to_ignore = [
            # Current Errors:
            "scrapeAsuraScans.py",      # To fix! (Priority: High)
            "scrapeHelScans.py",        # To fix! (Priority: Low) --> Changed website layout to other style
            "scrapeMagusManga.py",      # To fix! (Priority: Low) --> Changed website layout to other style. Same as HelScans

            # Could Remove:
            "scrapeFreakScans.py",      # These guys might be out of business now
            "scrapeLuminousComics.py",  # Received a DMCA takedown notice
            "scrapeSuryaScans.py",      # Down
            "scrapeImmortalUpdates.py", # Down
            "scrapeMangaGalaxy.py",     # Merged with Vortex Scans

            # Found 0 books
            "scrapeResetScans.py",
            "scrapeAnimatedGlitchedScans2.py",
            "scrapeLeviathanScans.py",
            "scrapeAryaScans.py",

            # Still Developing
            "scrapeHiveScans.py",       # Looks like we're using both Selenium and Beautiful soup, but Selenium not used correctly
            "scrapeYakshaScans.py",     # Look at server/out/YakshaScans/scrapeYakshaScans_7.txt for full details
            "scrapeRizzFables.py",
            "scrapeRizzFablesSelenium.py",

            # Takes a long time to scrape
            "scrapeBoxNovel.py",
            "scrapeLightNovelPub.py",
        ]

        # Get all Python scripts in the child folder
        all_runnable_scripts = [f for f in os.listdir(scripts_folder) if f.endswith('.py') and f not in scripts_to_ignore]

        # For testing purposes, run the below to only invoke certain scripts
        # all_runnable_scripts = [
        #     # "scrapeLightNovelPub.py",
        #     "scrapeBoxNovel.py"
        # ]

        # all_runnable_scripts = [
        #                         # 'scrapeBoxNovel.py', 'scrapeSetsuScans.py', 'scrapeFlameComics.py', 'scrapeFreakScans.py', 
        #                         # 'scrapeResetScans.py', 'scrapeLuminousComics.py', 'scrapeManhwaFreaks.py', 'scrapeAnimatedGlitchedScans2.py', 
        #                         # 'scrapeTritiniaScans.py', 'scrapeLeviathanScans.py', 'scrapeSpiderScans.py', 'scrapeCulturedWorks.py', 
        #                         # 'scrapeMangaGalaxy.py', 'scrapeRavenScans.py', 'scrapeKalango.py', 'scrapeHelScans.py', 'scrapeNightScans.py', 
        #                         # 'scrapeDrakeScans.py', 'scrapeMangaSushi.py', 'scrapeMagusManga.py', 'scrapeGDScans.py', 'scrapeLightNovelPub.py', 
        #                         'scrapeHiveScans.py', 'scrapeSuryaScans.py', 'scrapeHiraethTranslation.py', 'scrapeArvenComics.py', 'scrapeAsuraScans.py', 
        #                         'scrapeAnimatedGlitchedScans.py', 'scrapeLHTranslation.py', 'scrapePlatinumCrown.py', 'scrapeImmortalUpdates.py'
        #                     ]

        logger.info(f"Order of runnable scripts: {all_runnable_scripts}")

        # Define the Django settings module and project root
        django_settings_module = "django_app.settings"
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))

        total_time = datetime.datetime.now()

        # Iterate over each runnable script and call it
        for script in all_runnable_scripts:
            script_path = os.path.join(scripts_folder, script)
            try:
                logger.info(f"Starting to scrape {script}")
                result = subprocess.run(
                    ["python", script_path],
                    check=True,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "DJANGO_SETTINGS_MODULE": django_settings_module, "PYTHONPATH": project_root}
                )
                logger.info(f"Output of {script}:\n{result.stderr.strip()}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error occurred while running {script}:\n{e.stderr.strip()}")

        logger.info(f"All runnable scripts executed in {self.format_duration(datetime.datetime.now() - total_time)}.")
    
    @staticmethod
    def format_duration(duration):
        """
        Formats a duration into a human-readable string.

        Args:
            duration (datetime.timedelta): The duration to format.

        Returns:
            str: A string representing the duration in hours, minutes, and seconds.
        """
        seconds = duration.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        if hours == 0:
            return f"{minutes}m {seconds}s"
        return f"{hours}h {minutes}m {seconds}s"

    def get_next_log_file_name(self, base_dir, base_filename):
        counter = 0
        while True:
            log_file_name = f"{base_filename}_{counter}.txt" if counter else f"{base_filename}.txt"
            full_path = os.path.join(base_dir, log_file_name)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

if __name__ == "__main__":
    Command().handle()
