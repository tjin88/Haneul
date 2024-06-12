# TODO: Look into optimizations. Took 1h 7m 12s to scrape 500 books (I did cap this at 500 manually).
# To be fair, my computer was overloaded at that time, so the CPU could have been overloaded.
import datetime
import json
import time
import re
import os
import django
import logging
import traceback
import threading
import sys
from logging.handlers import RotatingFileHandler
from requests.exceptions import ConnectionError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import IntegrityError, DatabaseError, connection
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.django_app.settings')
django.setup()

def get_next_log_file_name(base_dir, base_filename):
    counter = 0
    while True:
        log_file_name = f"{base_filename}_{counter}.txt" if counter else f"{base_filename}.txt"
        full_path = os.path.join(base_dir, log_file_name)
        if not os.path.exists(full_path):
            return full_path
        counter += 1

# Setting up the logging configuration
log_directory = "../out/BoxNovel"
log_base_filename = "scrapeBoxNovel"
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
logger = logging.getLogger("BoxNovelScraper")

class BoxNovelScraper:
    def __init__(self):
        '''
        TODO: Test to see if this is the optimal number of threads
        To be honest, ideally this script works on the burner computer. 
        If so, adjust the number of threads accordingly.

        3 > 2 > 5. Test 4 to see where it stands 
        Too many threads = server ban or system overload 
        Too little threads = slower scraping time

        3 threads, all skipped = 0h 9m 36s  --> See out/BoxNovel/scrapeBoxNovel_45.txt
        2 threads, all skipped = 0h 11m 35s --> See out/BoxNovel/scrapeBoxNovel_46.txt
        5 threads, all skipped = 1h 2m 34s  --> See out/BoxNovel/scrapeBoxNovel_44.txt
        '''
        # TODO: Test to see if this is the optimal number of threads
        # 3 > 2 > 5. Test 4 to see where it stands 
        # Too many threads = server ban or system overload 
        # Too little threads = slower scraping time
        self.MAX_THREADS = 3 # max thread count (or number of concurrent windows used for scraping)
        self.driver_pool = DriverPool(size=self.MAX_THREADS)
        self.continue_scraping = True
        self.skipped_threshold = 200

    def scrape_book_and_update_db(self, title_url_tuple, book_number, total_books):
        """
        Scrapes details for a single book and updates the database.

        Args:
            title_url_tuple (tuple): A tuple containing the title and URL of the book.
        """
        if not self.continue_scraping:
            # logger.info(f"{book_number}/{total_books} was 'cancelled': {title_url_tuple[0]}")
            return {'status': 'cancelled', 'title': title_url_tuple[0]}
    
        title, url = title_url_tuple
        normalized_title = title.replace('(WN)', '').replace('Web Novel', '').strip()
        try:
            driver = self.driver_pool.get_driver()
            driver.get(url)
            
            start_time = datetime.datetime.now()

            with connection.cursor() as cursor:
                cursor.execute("SELECT newest_chapter FROM all_books WHERE title = %s AND novel_source = %s", [normalized_title, 'Box Novel'])
                existing_book = cursor.fetchone()

            if existing_book:
                newest_chapter = self.scrape_newest_chapter(url, driver)
                if newest_chapter == existing_book[0]:
                    # duration = datetime.datetime.now() - start_time
                    # formatted_duration = self.format_duration(duration)
                    # logger.info(f"{book_number}/{total_books} took {formatted_duration} to 'skip': {title}")
                    return {'status': 'skipped', 'title': title}

            details = self.scrape_book_details(title, url, driver)

            # Attempt to update an existing book or create a new one
            # TODO: Come back to this --> May want to store then push at the end to avoid "concurrency issues" **
            # Look into batching --> bulk create or bulk update
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO all_books (title, synopsis, author, updated_on, newest_chapter, image_url, rating, status, novel_type, novel_source, followers, chapters)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (title, novel_source)
                    DO UPDATE SET
                        synopsis = EXCLUDED.synopsis,
                        author = EXCLUDED.author,
                        updated_on = EXCLUDED.updated_on,
                        newest_chapter = EXCLUDED.newest_chapter,
                        image_url = EXCLUDED.image_url,
                        rating = EXCLUDED.rating,
                        status = EXCLUDED.status,
                        novel_type = EXCLUDED.novel_type,
                        followers = EXCLUDED.followers,
                        chapters = EXCLUDED.chapters
                """, [
                    details['title'],
                    details['synopsis'],
                    details['author'],
                    details['updated_on'],
                    details['newest_chapter'],
                    details['image_url'],
                    details['rating'],
                    details['status'],
                    details['novel_type'],
                    details['novel_source'],
                    details['followers'],
                    json.dumps(details['chapters'])
                ])

                cursor.execute("DELETE FROM all_books_genres WHERE allbooks_title = %s AND allbooks_novel_source = %s", [details['title'], details['novel_source']])
                for genre_name in details['genres']:
                    genre_name = genre_name.strip().lower()
                    cursor.execute("SELECT id FROM genre WHERE name = %s", [genre_name])
                    genre_id = cursor.fetchone()
                    if not genre_id:
                        cursor.execute("INSERT INTO genre (name) VALUES (%s) RETURNING id", [genre_name])
                        genre_id = cursor.fetchone()[0]
                    else:
                        genre_id = genre_id[0]
                    cursor.execute("INSERT INTO all_books_genres (genre_id, allbooks_title, allbooks_novel_source) VALUES (%s, %s, %s)", [genre_id, details['title'], details['novel_source']])

            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)

            logger.info(f"{book_number}/{total_books} took {formatted_duration} to {'create' if not existing_book else 'update'} {title}, with {len(details['chapters'])} chapters")
            return {'status': 'processed', 'title': title}
        except DatabaseError as e:
            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)
            logger.error(f"{book_number}/{total_books} took {formatted_duration} to encounter a 'database error': {title}. Error: {e}")
            return {'status': 'database_error', 'title': title, 'message': str(e)}
        except Exception as e:
            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(f"{book_number}/{total_books} took {formatted_duration} to encounter an 'error': {title}. Error message: {e}")
            logger.error(f"Exception Type: {exc_type}")
            logger.error(f"Exception Value: {exc_value}")
            logger.error(f"Traceback: {''.join(traceback.format_tb(exc_traceback))}")
            return {'status': 'error', 'title': title, 'message': str(e)}
        finally:
            self.driver_pool.release_driver(driver)

    def scrape_box_novel(self):
        """
        Scrapes the Box Novel website for light novel details and updates the database.
        Uses multi-threading for faster scraping.
        """
        base_url = 'https://boxnovel.com/novel/'
        try:
            driver = self.driver_pool.get_driver()
            books = self.scrape_main_page(base_url, driver=driver)
        finally:
            self.driver_pool.release_driver(driver)

        logger.info(f"Found {len(books)} books. Starting to scrape details.")

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
                elif result['status'] == 'database_error':
                    consecutive_skipped += 1
                    if consecutive_skipped >= 5:
                        logger.info("5 books encountered a database error in a row. Exiting...")
                        self.continue_scraping = False
                        executor.shutdown(wait=False)
                        break
                elif results['processed'] > 0 or results['skipped'] > self.skipped_threshold:
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
        results['skipped'] += consecutive_skipped
        logger.info(f"Books Processed: {results['processed']}, Skipped: {results['skipped'] + results['cancelled']}, Errors: {results['error']}")
        logger.info(f"There should be {total_books} books!")

    def scrape_main_page(self, url, driver=None):
        """
        Scrapes the main listing page for book URLs using Selenium.
        This method scrapes the main page of Box Novel to find all the books listed. 
        It uses Selenium's WebDriverWait to ensure that the page is loaded before attempting to find elements. 

        Args:
            url (str): URL of the main listing page.
            driver (webdriver): The WebDriver instance for the thread.

        Returns:
            list: A list of tuples containing book titles and their URLs.
        """
        self.navigate_to_url(url, driver=driver)
        books = []
        page_count = 1

        while True:
            book_elements = self.wait_for_elements(By.CLASS_NAME, 'page-item-detail', driver=driver)
            for element in book_elements:
                title = self.get_element_text(By.CSS_SELECTOR, '.post-title a', default_text='Title not available', element=element, driver=driver)
                book_url = self.get_element_attribute(By.CSS_SELECTOR, '.post-title a', 'href', default_value=None, element=element, driver=driver)
                books.append((title, book_url))
            
            try:
                next_page_element = self.wait_for_element(By.CSS_SELECTOR, '.nav-previous a', timeout=10, driver=driver)
                if next_page_element and page_count < 50:
                    page_count += 1
                    print(f'Going to page {page_count}')
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_page_element)
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.nav-previous a')))
                    driver.execute_script("arguments[0].click();", next_page_element)
                    time.sleep(3) # TODO: Wait for the page to load. I don't love this hardcoded, but it works for now.
                else:
                    return books
            except TimeoutException:
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
            return self.get_element_text(By.CSS_SELECTOR, '.listing-chapters_wrap .wp-manga-chapter a', 'Chapter not available', driver=driver)
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
            self.navigate_to_url(book_url, driver=driver)
            
            # Extract details
            normalized_title = title.replace('(WN)', '').replace('Web Novel', '').strip()
            synopsis_str = self.wait_for_element(By.CSS_SELECTOR, '.description-summary .summary__content', driver=driver)
            synopsis = synopsis_str.get_attribute('textContent').replace('(adsbygoogle = window.adsbygoogle || []).push({});', '').replace('B0XNʘVEL.C0M', '').strip() if synopsis_str and synopsis_str.get_attribute('textContent') else 'Synopsis not available'
            authors = self.wait_for_elements(By.CSS_SELECTOR, '.summary-content .author-content a', driver=driver)
            author = ', '.join([author.text.strip() for author in authors]) if authors else 'Author not available'
            updated_on_text = self.get_element_text(By.CSS_SELECTOR, '.chapter-release-date i', driver=driver)
            newest_chapter = self.get_element_text(By.CSS_SELECTOR, '.listing-chapters_wrap .wp-manga-chapter a', driver=driver)
            genres = [genre.text.strip() for genre in self.wait_for_elements(By.CSS_SELECTOR, '.summary-content .genres-content a', driver=driver)]
            default_image_url = "https://via.placeholder.com/400x600/CCCCCC/FFFFFF?text=No+Image"
            image_url = self.get_element_attribute(By.CSS_SELECTOR, '.summary_image img', 'src', driver=driver) or default_image_url
            rating = self.get_element_text(By.CSS_SELECTOR, '.post-total-rating .score', driver=driver)
            status = self.get_value_based_on_heading("Status", driver)
            followers_str = self.get_value_based_on_heading("Rank", driver)
            followers = self.parse_followers(followers_str.split(' ')[-3]) if followers_str != 'N/A' else 'N/A'
            updated_on = self.parse_relative_date(updated_on_text).strftime('%Y-%m-%dT%H:%M:%S%z')

            try:
                next_page_element = self.wait_for_element(By.CLASS_NAME, 'chapter-readmore', timeout=5, driver=driver)
                if next_page_element:
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_page_element)
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'chapter-readmore')))
                    driver.execute_script("arguments[0].click();", next_page_element)
                    time.sleep(3) # TODO: Wait for the page to load. I don't love this hardcoded, but it works for now.
            except TimeoutException:
                # Yeah I guess keep going? It just means that there's less than 5 chapters ...
                pass

            chapters = {}
            try:
                chapter_elements = self.wait_for_elements(By.CSS_SELECTOR, 'ul.version-chap a', timeout=5, driver=driver)
                for chapter in chapter_elements:
                    chapter_title = chapter.text.strip()
                    chapter_url = chapter.get_attribute('href')
                    if chapter_title and chapter_url:
                        chapters[chapter_title] = chapter_url
            except TimeoutException:
                chapters = {}

            book_details = {
                'title': normalized_title,
                'synopsis': synopsis,
                'author': author,
                'updated_on': updated_on,
                'newest_chapter': newest_chapter,
                'genres': genres,
                'image_url': image_url,
                'rating': float(rating) * 2.0 if rating else 0.0,
                'status': status,
                'novel_type': 'Light Novel',
                'novel_source': 'Box Novel',
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
            if value in ["PagedList-skipToNext", ".nav-previous a", ".description-summary .summary__content"]:
                return None
            logger.error(f"Error waiting for element {value}: {e}")
            raise
    
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
    
    def get_value_based_on_heading(self, heading, driver):
        """
        Gets the value from the summary-content based on the given heading.

        Args:
            heading (str): The heading to look for (e.g., 'Status', 'Rank').
            driver (webdriver): The WebDriver instance.

        Returns:
            str: The corresponding value from the summary-content.
        """
        try:
            items = driver.find_elements(By.CSS_SELECTOR, '.post-content_item')
            for item in items:
                heading_text = item.find_element(By.CSS_SELECTOR, '.summary-heading h5').text.strip()
                if heading_text == heading:
                    return item.find_element(By.CSS_SELECTOR, '.summary-content').text.strip()
            return 'N/A'
        except NoSuchElementException:
            return 'N/A'

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
        
        if "day ago" in time_str:
            days = int(re.search(r'(\d+) day(?:s)? ago', time_str).group(1))
            return today - datetime.timedelta(days=days)
        elif "hour ago" in time_str:
            hours = int(re.search(r'(\d+) hour(?:s)? ago', time_str).group(1))
            return today - datetime.timedelta(hours=hours)
        elif "minute ago" in time_str:
            minutes = int(re.search(r'(\d+) minute(?:s)? ago', time_str).group(1))
            return today - datetime.timedelta(minutes=minutes)
        elif "year ago" in time_str:
            years = int(re.search(r'(\d+) year(?:s)? ago', time_str).group(1))
            return today - datetime.timedelta(days=years * 365)
        elif "month ago" in time_str:
            months = int(re.search(r'(\d+) month(?:s)? ago', time_str).group(1))
            return today - datetime.timedelta(days=months * 30)
        elif re.match(r'\b\d{1,2} \w+ \d{4}\b', time_str):
            # Parsing absolute dates like 'May 6, 2024'
            return datetime.datetime.strptime(time_str, '%B %d, %Y').replace(tzinfo=timezone.utc)
        else:
            # Default case returns current date and time
            return today
    
    @staticmethod
    def parse_followers(followers_str):
        """
        Parses the followers string into an integer value.
        The underscores are just for readability and do not affect the number.

        Args:
            followers_str (str): A string representing the number of followers (e.g., '1.2M', '3.4K', '500').

        Returns:
            int: The number of followers as an integer.
        """
        followers_str = followers_str.upper()
        if 'M' in followers_str:
            return int(float(followers_str.replace('M', '')) * 1_000_000)
        elif 'K' in followers_str:
            return int(float(followers_str.replace('K', '')) * 1_000)
        else:
            return int(followers_str)
    
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
        if hours == 0:
            return f"{minutes}m {seconds}s {milliseconds}ms"
        return f"{hours}h {minutes}m {seconds}s"

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

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def close_all_drivers(self):
        while not self.available_drivers.empty():
            driver = self.available_drivers.get()
            driver.quit()

class Command(BaseCommand):
    help = 'Scrapes light novels from Box Novel and updates the database.'

    def handle(self, *args, **kwargs):
        """
        Handles the command execution for scraping light novels.

        Executes the scraping process, calculates the duration of the operation, and logs the result.
        """
        logger.info("Starting to scrape Box Novel")
        start_time = datetime.datetime.now()
        scraper = BoxNovelScraper()
        try:
            scraper.scrape_box_novel()
            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)
            logger.info(f"Successfully executed scrapeBoxNovel in {formatted_duration} ")
            self.stdout.write(self.style.SUCCESS('Successfully executed scrapeBoxNovel'))
        except ConnectionError:
            logger.error("Looks like the computer was not connected to the internet. Abandoned this attempt to update server for Box Novel books.")
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
        if hours == 0:
            return f"{minutes}m {seconds}s"
        return f"{hours}h {minutes}m {seconds}s"

if __name__ == "__main__":
    Command().handle()