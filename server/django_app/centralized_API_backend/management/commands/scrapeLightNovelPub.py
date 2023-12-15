import datetime
import time
import re
import os
import django
import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from centralized_API_backend.models import LightNovel

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app/django_app/settings')
django.setup()

# TODO: Change all print statements to log statements
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightNovelScraper:
    def __init__(self):
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.TIME_TO_WAIT = 3

    def scrape_light_novel_pub(self):
        base_url = 'https://lightnovelpub.vip'
        main_url = f'{base_url}/browse/genre-all-25060123/order-updated/status-all'

        success = 0
        skipped = 0
        try:
            books = self.scrape_main_page(main_url)
            
            for title, url in books:
                try:
                    self.navigate_to_url(url)

                    existing_book = LightNovel.objects.filter(title=title).first()

                    # Skip updating if the book has not changed
                    if existing_book:
                        newest_chapter = self.scrape_newest_chapter(url)
                        if newest_chapter == existing_book.newest_chapter:
                            skipped += 1
                            logger.info(f"Book {success+skipped}/{len(books)} - {'Skipped'}: {title}")
                            continue  

                    details = self.scrape_book_details(title, url)
                    lightNovel, created = LightNovel.objects.update_or_create(
                        title=details['title'],
                        defaults=details
                    )

                    success += 1
                    logger.info(f"Book {success+skipped}/{len(books)} - {'Created' if created else 'Updated'}: {lightNovel.title}")
                except WebDriverException as e:
                    logger.error(f"WebDriverException encountered for {title} at {url}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error while processing book '{title}': {e}")
        finally:
            logger.info(f"Success: {success}/{len(books)}\nSkipped: {skipped}/{len(books)}\nErrors: {len(books)-success-skipped}/{len(books)}")
            self.driver.quit()
    
    def scrape_newest_chapter(self, book_url):
        """
        Scrapes only the newest chapter of a book.

        Args:
        book_url (str): URL of the book's detail page.

        Returns:
        str: The newest chapter of the book.
        """
        try:
            # self.navigate_to_url(book_url)
            return self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.latest', 'Chapter not available')
        except NoSuchElementException as e:
            logger.error(f"Element not found in {book_url}: {e}")
        except Exception as e:
            logger.error(f"Error scraping newest chapter from {book_url}: {e}")
            return None

    def scrape_main_page(self, url):
        """
        Scrapes the main listing page for book URLs using Selenium.

        Args:
        url (str): URL of the main listing page.

        Returns:
        list: A list of tuples containing book titles and their URLs.
        """
        self.navigate_to_url(url)
        books = []

        while True:
            # Scrape the current page
            book_elements = self.driver.find_elements(By.CLASS_NAME, 'novel-item')
            for element in book_elements:
                title_element = element.find_element(By.CLASS_NAME, 'novel-title')
                title = title_element.text.strip()
                book_url = title_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                books.append((title, book_url))
            
            # Testing purposes**
            # return books

            # TODO: Later, change this to only x pages --> x = how many pages of books were updated since last scraped
            # Maybe scrape the bottom of each book --> if = "2 days ago", stop scraping? 
            # This accounts for if errors with previous scrape?

            # If there are more books to add, add them to the list. If not, return all books.
            try:
                next_page_element = self.driver.find_element(By.CLASS_NAME, 'PagedList-skipToNext')
                next_page_url = next_page_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                self.navigate_to_url(next_page_url)
            except NoSuchElementException:
                return books

    def scrape_book_details(self, title, book_url):
        """
        Scrapes detailed information about a book from its individual page using Selenium.
        
        Args:
        title (str): Title of the book.
        book_url (str): URL of the book's detail page.
        
        Returns:
        dict: A dictionary containing key details of the book.
        """
        try:
            # self.navigate_to_url(book_url)

            synopsis = self.get_element_text(By.CSS_SELECTOR, '.summary .content')
            author = self.get_element_text(By.CSS_SELECTOR, '.author', 'Author not available').replace('Author:', '').strip()
            updated_on = self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.update')
            newest_chapter = self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.latest')
            genres = [genre.text.strip() for genre in self.driver.find_elements(By.CSS_SELECTOR, 'div.categories a')]
            image_url = self.get_element_attribute(By.CSS_SELECTOR, 'figure.cover img', 'src')
            rating = self.get_element_text(By.CSS_SELECTOR, 'div.rating-star strong')
            status = self.get_element_text(By.CSS_SELECTOR, 'div.header-stats span:nth-of-type(4) strong')
            followers = self.get_element_text(By.CSS_SELECTOR, 'div.header-stats span:nth-of-type(3) strong')

            timezone_aware_updated_on = self.parse_relative_date(updated_on)

            chapters = self.extract_chapters(f'{book_url}/chapters')

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
    
    def navigate_to_url(self, url):
        try:
            self.driver.get(url)
            time.sleep(self.TIME_TO_WAIT)  # Adjusted for page loading
        except WebDriverException as e:
            logger.error(f"Error navigating to URL {url}: {e}")
            raise

    def wait_for_element(self, by, value, timeout=10):
        """
        Waits for a specific element to be present on the page.

        Args:
        by (By): The Selenium By strategy.
        value (str): The value to locate the element.
        timeout (int): Maximum time to wait for the element. Default is 10 seconds.

        Returns:
        WebElement: The found element, or None if not found within the timeout.
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Error waiting for element {value}: {e}")
            raise
    
    def get_element_text(self, by, value, default_text='Not Available'):
        """
        Waits for an element to be present on the page and retrieves its text.

        Args:
        by (By): The Selenium By strategy.
        value (str): The value to locate the element.
        default_text (str): Default text to return if the element is not found.

        Returns:
        str: The text of the found element or default text if not found.
        """
        try:
            element = self.wait_for_element(by, value)
            return element.text.strip() if element else default_text
        except (TimeoutException, WebDriverException):
            logger.warning(f"Element {value} not found, using default value.")
            return default_text
    
    def get_element_attribute(self, by, value, attribute, default_value=None):
        """
        Waits for an element to be present on the page and retrieves a specified attribute.

        Args:
        by (By): The Selenium By strategy.
        value (str): The value to locate the element.
        attribute (str): The attribute to retrieve from the element.
        default_value (any): Default value to return if the element or attribute is not found.

        Returns:
        str: The value of the attribute or default value if not found.
        """
        try:
            element = self.wait_for_element(by, value)
            return element.get_attribute(attribute) if element and element.get_attribute(attribute) else default_value
        except (TimeoutException, WebDriverException):
            logger.warning(f"Element {value} not found, using default value.")
            return default_value        

    def extract_chapters(self, chapters_url):
        self.navigate_to_url(chapters_url)

        chapters = {}
        chapter_elements = self.driver.find_elements(By.CSS_SELECTOR, 'ul.chapter-list a')
        for chapter in chapter_elements:
            chapter_title, chapter_link = self.process_chapter_element(chapter)
            chapters[chapter_title] = chapter_link
        return chapters

    def process_chapter_element(self, chapter_element):
        parts = chapter_element.text.strip().split('\n')
        chapter_title = f'{parts[0]} - {parts[1]}'
        chapter_link = chapter_element.get_attribute('href')
        return chapter_title, chapter_link
    
    @staticmethod
    def parse_relative_date(time_str):
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

class Command(BaseCommand):
    help = 'Scrapes light novels from LightNovelPub and updates the database.'

    def handle(self, *args, **kwargs):
        start_time = datetime.datetime.now()
        scraper = LightNovelScraper()
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
        Formats a datetime.timedelta object into a readable string.

        Args:
        duration (datetime.timedelta): The duration to format.

        Returns:
        str: A string representing the duration in a readable format.
        """
        seconds = duration.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours}h {minutes}m {seconds}s"

if __name__ == "__main__":
    Command().handle()