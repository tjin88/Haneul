import threading
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import subprocess

class DriverPool:
    def __init__(self, size):
        self.available_drivers = Queue()
        self.lock = threading.Lock()

        # Get Chrome version
        try:
            chrome_version = subprocess.check_output(
                ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version']
            )
            chrome_version = chrome_version.decode('utf-8').strip().split()[-1]
            print(f"Detected Chrome version: {chrome_version}")
        except Exception as e:
            print(f"Warning: Could not detect Chrome version: {str(e)}")

        for _ in range(size):
            driver = self.create_webdriver_instance()
            self.available_drivers.put(driver)

    def get_driver(self):
        driver = self.available_drivers.get(block=True)
        return driver

    def release_driver(self, driver):
        self.available_drivers.put(driver)

    def create_webdriver_instance(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            # Using the latest ChromeDriver without specifying version
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            return driver
        except Exception as e:
            print(f"Error creating WebDriver: {str(e)}")
            try:
                # Fallback for ARM Macs
                driver = webdriver.Chrome(
                    service=Service(
                        ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                    ),
                    options=options
                )
                return driver
            except Exception as e:
                print(f"Fallback also failed: {str(e)}")
                raise

    def close_all_drivers(self):
        while not self.available_drivers.empty():
            driver = self.available_drivers.get()
            try:
                driver.quit()
            except Exception as e:
                print(f"Error closing driver: {str(e)}")