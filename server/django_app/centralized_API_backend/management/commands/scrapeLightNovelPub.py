import datetime
import time
import re
import os
import django
import logging
import traceback
import threading
import sys
from logging.handlers import RotatingFileHandler
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from centralized_API_backend.models import LightNovelPub
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app/django_app/settings')
django.setup()

def get_next_log_file_name(base_dir, base_filename):
    counter = 0
    while True:
        if counter == 0:
            log_file_name = f"{base_filename}.txt"
        else:
            log_file_name = f"{base_filename}_{counter}.txt"
        
        full_path = os.path.join(base_dir, log_file_name)
        if not os.path.exists(full_path):
            return full_path
        
        counter += 1

# Setting up the logging configuration
log_directory = "../out/LightNovelPub"
log_base_filename = "scrapeLightNovelPub"
log_file_path = get_next_log_file_name(log_directory, log_base_filename)

# Ensure the log directory exists
os.makedirs(log_directory, exist_ok=True)

# Setting up the logging config, storing as a file and outputting to console
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        RotatingFileHandler(log_file_path, maxBytes=10485760, backupCount=5),  # 10MB per file, max 5 files of size 10 MB
        logging.StreamHandler()
    ]
)

# Suppressing unnessary Selenium Web Driver Manager logs
logging.getLogger('WDM').setLevel(logging.WARNING)

# Set logger for all other log messages
logger = logging.getLogger("LightNovelPubScraper")

class LightNovelPubScraper:
    def __init__(self):
        '''
        TODO: Test to see if this is the optimal number of threads

        3 > 2 > 5. Test 4 to see where it stands 
        Too many threads = server ban or system overload 
        Too little threads = slower scraping time

        3 threads, all skipped = 0h 9m 36s  --> See out/LightNovelPub/scrapeLightNovelPub_45.txt
        2 threads, all skipped = 0h 11m 35s --> See out/LightNovelPub/scrapeLightNovelPub_46.txt
        5 threads, all skipped = 1h 2m 34s  --> See out/LightNovelPub/scrapeLightNovelPub_44.txt
        '''
        # TODO: Test to see if this is the optimal number of threads
        # 3 > 2 > 5. Test 4 to see where it stands 
        # Too many threads = server ban or system overload 
        # Too little threads = slower scraping time
        self.MAX_THREADS = 3 # max thread count (or number of concurrent windows used for scraping)

        self.continue_scraping = True # Used to skip extra scraping (reduces scraping time)
        self.driver_pool = DriverPool(size=self.MAX_THREADS)

    def scrape_book_and_update_db(self, title_url_tuple, book_number, total_books):
        """
        Scrapes details for a single book and updates the database.

        Args:
            title_url_tuple (tuple): A tuple containing the title and URL of the book.
        """
        if not self.continue_scraping:
            logger.info(f"Book {book_number}/{total_books} was 'cancelled': {title}")
            return {'status': 'cancelled', 'title': title}
    
        title, url = title_url_tuple
        try:
            # Get next available driver
            driver = self.driver_pool.get_driver()

            driver.get(url)
            
            start_time = datetime.datetime.now()

            # Check if the book exists in the database
            existing_book = LightNovelPub.objects.filter(title=title).first()

            if existing_book:
                newest_chapter = self.scrape_newest_chapter(url, driver)
                if newest_chapter == existing_book.newest_chapter:
                    duration = datetime.datetime.now() - start_time
                    formatted_duration = self.format_duration(duration)
                    logger.info(f"Book {book_number}/{total_books} took {formatted_duration} to be 'skipped': {title}")
                    return {'status': 'skipped', 'title': title}

            # Get all details for the book
            details = self.scrape_book_details(title, url, driver)

            # Attempt to update an existing book or create a new one
            # TODO: Come back to this --> May want to store then push at the end to avoid "concurrency issues" **
            # Look into batching --> bulk create or bulk update
            LightNovelPub.objects.update_or_create(
                title=details['title'],
                novel_source=details['novel_source'],
                defaults=details
            )

            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)

            logger.info(f"Book {book_number}/{total_books} took {formatted_duration} to be {'created' if not existing_book else 'updated'}: {title}")
            return {'status': 'processed', 'title': title}
        except Exception as e:
            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(f"Book {book_number}/{total_books} took {formatted_duration} to encounter an 'error': {title}. Error message: {e}")
            logger.error(f"Exception Type: {exc_type}")
            logger.error(f"Exception Value: {exc_value}")
            logger.error(f"Traceback: {''.join(traceback.format_tb(exc_traceback))}")
            return {'status': 'error', 'title': title, 'message': str(e)}
        finally:
            self.driver_pool.release_driver(driver)

    def scrape_light_novel_pub(self):
        """
        Scrapes the LightNovelPub website for light novel details and updates the database.
        Uses multi-threading for faster scraping.
        """
        base_url = 'https://lightnovelpub.vip'
        main_url = f'{base_url}/browse/genre-all-25060123/order-updated/status-all'

        try:
            # Initialize a new driver for scraping the main page
            driver = self.driver_pool.get_driver()

            books = self.scrape_main_page(main_url, driver=driver)
        finally:
            self.driver_pool.release_driver(driver)

        results = {'processed': 0, 'skipped': 0, 'error': 0, 'cancelled': 0}
        book_number = 0
        total_books = len(books)
        futures = []
        consecutive_skipped = 0

        with ThreadPoolExecutor(max_workers=self.MAX_THREADS) as executor:
            for book in books:
                if not self.continue_scraping:
                    break
                book_number += 1
                futures.append(executor.submit(self.scrape_book_and_update_db, book, book_number, total_books))
                       
            for future in as_completed(futures):
                result = future.result()
                results[result['status']] += 1

                if result['status'] == 'error':
                    logger.error(f"Error processing {result['title']}: {result['message']}")
                elif results['processed'] > 0:
                    if result['status'] == 'skipped':
                        consecutive_skipped += 1

                        ''' 
                        Break if there are more than 5 books that haven't been updated.
                        This is because we would assume that the rest of the books are up to date.
                        '''
                        if consecutive_skipped >= 5:
                            logger.info("5 books skipped in a row after processing. Exiting...")
                            self.continue_scraping = False
                            executor.shutdown(wait=False)
                            break
                    elif result['status'] == 'processed':
                        results['skipped'] += consecutive_skipped
                        consecutive_skipped = 0
        
        self.driver_pool.close_all_drivers()

        # Edge case where there are < 5 skipped books at the end of the books list
        # Really only useful for logging purposes lol
        results['skipped'] += consecutive_skipped
        logger.info(f"Books Processed: {results['processed']}, Skipped: {results['skipped']+results['cancelled']}, Errors: {results['error']}")
        logger.info(f"There should be {total_books} books!")

    def scrape_main_page(self, url, driver=None):
        """
        Scrapes the main listing page for book URLs using Selenium.
        This method scrapes the main page of light novel pub to find all the books listed. 
        It uses Selenium's WebDriverWait to ensure that the page is loaded before attempting to find elements. 

        Args:
            url (str): URL of the main listing page.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            list: A list of tuples containing book titles and their URLs.
        """
        self.navigate_to_url(url, driver=driver)
        books = []

        while True:
            # Scrape the current page
            book_elements = self.wait_for_elements(By.CLASS_NAME, 'novel-item', driver=driver)
            for element in book_elements:
                title = self.get_element_text(By.CLASS_NAME, 'novel-title', default_text='Title not available', element=element, driver=driver)
                book_url = self.get_element_attribute(By.TAG_NAME, 'a', 'href', default_value=None, element=self.wait_for_element(By.CLASS_NAME, 'novel-title', element=element, driver=driver),  driver=driver)
                books.append((title, book_url))
            
            # If there are more books to add, add them to the list. If not, return all books.
            next_page_element = self.wait_for_element(By.CLASS_NAME, 'PagedList-skipToNext', timeout=5, driver=driver)

            if next_page_element:
                next_page_url = self.get_element_attribute(By.TAG_NAME, 'a', 'href', default_value=None, element=next_page_element, driver=driver)
                self.navigate_to_url(next_page_url, driver=driver)
            else:
                return books
    
    def scrape_newest_chapter(self, book_url, driver):
        """
        Scrapes only the newest chapter of a book.

        Args:
            book_url (str): URL of the book's detail page.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            str: The newest chapter of the book.
        """
        try:
            return self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.latest', 'Chapter not available', driver=driver)
        except NoSuchElementException as e:
            logger.warning(f"Element not found in {book_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error scraping newest chapter from {book_url}: {e}")
            return None

    def scrape_book_details(self, title, book_url, driver):
        """
        Scrapes detailed information about a book from its individual page using Selenium.
        
        Args:
            title (str): Title of the book.
            book_url (str): URL of the book's detail page.
            driver (webdriver): The WebDriver instance for the thread.
        
        Returns:
            dict: A dictionary containing key details of the book.
        """
        try:
            synopsis = self.get_element_text(By.CSS_SELECTOR, '.summary .content', driver=driver)
            author = self.get_element_text(By.CSS_SELECTOR, '.author', 'Author not available', driver=driver).replace('Author:', '').strip()
            updated_on = self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.update', driver=driver)
            # the below line is throwing the issue***
            newest_chapter = self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.latest', driver=driver)
            genres = [genre.text.strip() for genre in self.wait_for_elements(By.CSS_SELECTOR, 'div.categories a', driver=driver)]
            image_url = self.get_element_attribute(By.CSS_SELECTOR, 'figure.cover img', 'src', driver=driver)
            rating = self.get_element_text(By.CSS_SELECTOR, 'div.rating-star strong', driver=driver)
            status = self.get_element_text(By.CSS_SELECTOR, 'div.header-stats span:nth-of-type(4) strong', driver=driver)
            followers = self.get_element_text(By.CSS_SELECTOR, 'div.header-stats span:nth-of-type(3) strong', driver=driver)

            timezone_aware_updated_on = self.parse_relative_date(updated_on)

            chapters = self.extract_chapters(f'{book_url}/chapters', book_title=title, driver=driver)

            book_details = {
                'title': title,
                'synopsis': synopsis,
                'author': author,
                # 'artist': "None",
                # 'released_by': "None",
                # 'serialization': "None",
                # 'posted_by': "None",
                # The following two fields need to be both "datetime" fields
                # 'posted_on': "placeholder to be found", # TODO: Find the original data posted
                'updated_on': timezone_aware_updated_on,
                'newest_chapter': newest_chapter,
                'genres': genres,
                'image_url': image_url,
                'rating': rating,
                'status': status,
                'novel_type': 'Light Novel',
                'novel_source': 'Light Novel Pub',
                'followers': followers,
                'chapters': chapters
            }

            return book_details
        except NoSuchElementException as e:
            logger.error(f"Element not found in {book_url}: {e}")
        except WebDriverException as e:
            logger.error(f"WebDriverException encountered for {title} at {book_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing {title}: {e}")
    
    def navigate_to_url(self, url, driver=None):
        """
        Navigates to a specified URL using the WebDriver.

        Args:
            url (str): The URL to navigate to.
            driver (webdriver): The WebDriver instance for the thread.
        """
        try:
            driver.get(url)
        except WebDriverException as e:
            logger.error(f"Error navigating to URL {url}: {e}")
            raise
    
    def wait_for_elements(self, by, value, timeout=10, driver=None):
        """
        Waits for multiple elements to be present on the page.

        Args:
            by (By): The Selenium By strategy.
            value (str): The value to locate the elements.
            timeout (int): Maximum time to wait for the elements. Default is 10 seconds.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            List[WebElement]: A list of found elements, or an empty list if none found within the timeout.
        """
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Error waiting for elements {value}: {e}")
            return []

    def wait_for_element(self, by, value, timeout=10, element=None, driver=None):
        """
        Waits for a specific element to be present on the page or within a parent element.

        Args:
            by (By): The Selenium By strategy.
            value (str): The value to locate the element.
            timeout (int): Maximum time to wait for the element. Default is 10 seconds.
            element (WebElement, optional): The parent element to search within. Default is None, which means search in the entire page.

        Returns:
            WebElement: The found element, or None if not found within the timeout.
        """
        try:
            target = element if element else driver
            return WebDriverWait(target, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except (TimeoutException, WebDriverException) as e:
            if value != "PagedList-skipToNext":
                logger.error(f"Error waiting for element {value}: {e}")
                raise
            else:
                # logger.info(f"Starting process to update books")
                # Time to update books!
                return None
    
    def get_element_text(self, by, value, default_text='Not Available', element=None, driver=None):
        """
        Waits for an element to be present on the page and retrieves its text.

        Args:
            by (By): The Selenium By strategy.
            value (str): The value to locate the element.
            default_text (str): Default text to return if the element is not found.
            element (WebElement, optional): The parent element to search within. Default is None, which means search in the entire page.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            str: The text of the found element or default text if not found.
        """
        try:
            target_element = element if element else driver
            element = self.wait_for_element(by, value, element=target_element, driver=driver)
            return element.text.strip() if element else default_text
        except (TimeoutException, WebDriverException):
            logger.warning(f"Element {value} not found, using default value.")
            return default_text

    def get_element_attribute(self, by, value, attribute, default_value=None, element=None, driver=None):
        """
        Waits for an element to be present on the page and retrieves a specified attribute.

        Args:
            by (By): The Selenium By strategy.
            value (str): The value to locate the element.
            attribute (str): The attribute to retrieve from the element.
            default_value (any): Default value to return if the element or attribute is not found.
            element (WebElement, optional): The parent element to search within. Default is None, which means search in the entire page.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            str: The value of the attribute or default value if not found.
        """
        try:
            target_element = element if element else driver
            element = self.wait_for_element(by, value, element=target_element, driver=driver)
            return element.get_attribute(attribute) if element and element.get_attribute(attribute) else default_value
        except (TimeoutException, WebDriverException):
            logger.warning(f"Element {value} not found, using default value.")
            return default_value

    def extract_chapters(self, chapters_url, book_title, driver):
        """
        Extracts chapter details from a given URL.

        Args:
            chapters_url (str): The URL to scrape chapters from.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            dict: A dictionary where each key is a chapter title and each value is the corresponding chapter link.
        """
        self.navigate_to_url(chapters_url, driver=driver)

        book_chapters = {}
        try:
            while True:
                chapter_elements = self.wait_for_elements(By.CSS_SELECTOR, 'ul.chapter-list a', driver=driver)

                for chapter in chapter_elements:                
                    chapter_title, chapter_link = self.process_chapter_element(chapter, driver=driver)
                    # logger.info(f"Extracted: {chapter_title} - {chapter_link}")
                    book_chapters[chapter_title] = chapter_link
                
                # If there are more books to add, add them to the list. If not, return all books.
                next_page_element = self.wait_for_element(By.CLASS_NAME, 'PagedList-skipToNext', timeout=5, driver=driver)
                
                if next_page_element:
                    next_page_url = self.get_element_attribute(By.TAG_NAME, 'a', 'href', default_value=None, element=next_page_element, driver=driver)
                    self.navigate_to_url(next_page_url, driver=driver)
                else:
                    # No more pages found. Push to database
                    break
        except Exception as e:
            logger.error(f"An error occurred: {e}")

        return book_chapters

    def process_chapter_element(self, chapter_element, driver):
        """
        Processes a single chapter element to extract its title and link.

        Args:
            chapter_element (WebElement): The web element representing a chapter.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            tuple: A tuple containing the chapter title and link.
        """
        try:
            number = self.get_element_text(By.CLASS_NAME, 'chapter-no', default_text='', element=chapter_element, driver=driver)
            title = self.get_element_text(By.CLASS_NAME, 'chapter-title', default_text='', element=chapter_element, driver=driver)
            chapter_title = f'{number} - {title}' if number else title
            
            chapter_link = chapter_element.get_attribute('href')
            return chapter_title, chapter_link
        except Exception as e:
            logger.error(f"Error processing chapter element: {e}")
            return None, None
    
    @staticmethod
    def parse_relative_date(time_str):
        """
        Parses a relative date string into a timezone-aware datetime object.

        Args:
            time_str (str): A string representing a relative date (e.g., 'x days ago').

        Returns:
            datetime: A timezone-aware datetime object representing the parsed date.
        """
        today = timezone.now()
        
        if time_str == "Updated yesterday":
            return today - datetime.timedelta(days=1)
        elif "days ago" in time_str:
            days = int(re.search(r'(\d+) days ago', time_str).group(1))
            return today - datetime.timedelta(days=days)
        elif "years ago" in time_str:
            years = int(re.search(r'(\d+) years ago', time_str).group(1))
            return today - datetime.timedelta(days=years * 365)  # Best approximation I could think of ...
        else:
            return today
    
    @staticmethod
    def format_duration(duration):
        """
        Formats a duration into a human-readable string.

        Args:
            duration (datetime.timedelta): The duration to format.

        Returns:
            str: A string representing the duration in hours, minutes, and seconds.
        """
        total_duration = duration.total_seconds()

        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        milliseconds = int((total_duration - int(total_duration)) * 1000)
        
        return f"{hours}h {minutes}m {seconds}s {milliseconds}ms"


class DriverPool:
    def __init__(self, size):
        self.available_drivers = Queue()
        self.lock = threading.Lock()
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
        # options.add_argument('--disable-gpu')  # According to the documentation, this is becessary for headless mode
        # options.add_argument('--no-sandbox')  # Used to bypass OS security model
        # options.add_argument('--disable-dev-shm-usage')  # Used to overcome limited resource problems
        options.add_argument("--headless")  # Make the scraping happen as a background process rather than an active window

        # options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppresses log messages in console

        # Initialize ChromeDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def close_all_drivers(self):
        while not self.available_drivers.empty():
            driver = self.available_drivers.get()
            driver.quit()


class Command(BaseCommand):
    help = 'Scrapes light novels from LightNovelPub and updates the database.'

    def handle(self, *args, **kwargs):
        """
        Handles the command execution for scraping light novels.

        Executes the scraping process, calculates the duration of the operation, and logs the result.
        """
        logger.info("Starting to scrape LightNovelPub")
        start_time = datetime.datetime.now()
        scraper = LightNovelPubScraper()
        try:
            scraper.scrape_light_novel_pub()

            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)

            logger.info(f"Successfully executed scrapeLightNovelPub in {formatted_duration} ")
            self.stdout.write(self.style.SUCCESS('Successfully executed scrapeLightNovelPub'))
        except Exception as e:
            logger.error(f"An error occurred during scraping: {e}")
            raise CommandError(f"Scraping failed due to an error: {e}")
    
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
        return f"{hours}h {minutes}m {seconds}s"

if __name__ == "__main__":
    Command().handle()