from django.core.management.base import BaseCommand
import os
import subprocess
import sys
import datetime

class Command(BaseCommand):
    help = 'Test a specific scraper with live output'

    def add_arguments(self, parser):
        parser.add_argument('scraper_name', type=str, help='Name of the scraper to test (e.g., scrapeMangaSushi.py)')

    def handle(self, *args, **kwargs):
        print("Start Time:", datetime.datetime.now())
        scraper_name = kwargs['scraper_name']
        scripts_folder = os.path.join(os.path.dirname(__file__), 'scraping_scripts')
        script_path = os.path.join(scripts_folder, scraper_name)

        if not os.path.exists(script_path):
            self.stdout.write(self.style.ERROR(f'Scraper {scraper_name} not found'))
            return

        try:
            # Use python -u for unbuffered output
            process = subprocess.Popen(
                ["python", "-u", script_path],  # Add -u here
                env={
                    **os.environ,
                    "DJANGO_SETTINGS_MODULE": "django_app.settings",
                    "PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')),
                    "PYTHONUNBUFFERED": "1"  # Force unbuffered output
                },
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0  # No buffering
            )

            # Print output in real-time
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip(), flush=True)  # Force flush
                
                error = process.stderr.readline()
                if error:
                    print(error.strip(), flush=True)  # Force flush
                
                # Check if process has finished
                if output == '' and error == '' and process.poll() is not None:
                    break

            if process.returncode != 0:
                self.stdout.write(self.style.ERROR(f'Scraper failed with return code {process.returncode}'))
            else:
                self.stdout.write(self.style.SUCCESS('Scraper completed successfully'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error running scraper: {str(e)}"))