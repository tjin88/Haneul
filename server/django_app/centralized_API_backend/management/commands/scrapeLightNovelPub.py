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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrapes light novels from LightNovelPub and updates the database.'

    def handle(self, *args, **kwargs):
        scraper = LightNovelScraper()
        scraper.scrape_light_novel_pub()
        self.stdout.write(self.style.SUCCESS('Successfully executed scrapeLightNovelPub'))

class LightNovelScraper:
    def __init__(self):
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.time_to_wait = 5

    def scrape_light_novel_pub(self):
        base_url = 'https://lightnovelpub.vip'
        main_url = f'{base_url}/browse/genre-all-25060123/order-updated/status-all'
        try:
            books = self.scrape_main_page(main_url)
            success = 0
            for title, url in books:
                try:
                    details = self.scrape_book_details(title, url)
                    lightNovel, created = LightNovel.objects.update_or_create(
                        title=details['title'],
                        defaults=details
                    )
                    print(f"{'Created' if created else 'Updated'}: {lightNovel.title}")
                    success += 1
                except Exception as e:
                    print(f"Error processing book '{title}': {e}")
        finally:
            print(f"{success}/{len(books)} books were successfully updated in the database")
            self.driver.quit()

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
            self.navigate_to_url(book_url)

            synopsis = self.get_element_text(By.CSS_SELECTOR, '.summary .content')
            author = self.get_element_text(By.CSS_SELECTOR, '.author', 'Author not available').replace('Author:', '').strip()
            updated_on = self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.update')
            newest_chapter = self.get_element_text(By.CSS_SELECTOR, 'nav.content-nav p.latest')
            genres = [genre.text.strip() for genre in self.driver.find_elements(By.CSS_SELECTOR, 'div.categories a')]
            image_url = self.get_element_attribute(By.CSS_SELECTOR, 'figure.cover img', 'src')
            rating = self.get_element_text(By.CSS_SELECTOR, 'div.rating-star strong')
            status = self.get_element_text(By.CSS_SELECTOR, 'div.header-stats strong.ongoing')
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
            print(f"Element not found in {book_url}: {e}")
        except WebDriverException as e:
            print(f"WebDriverException encountered for {title} at {book_url}: {e}")
        except Exception as e:
            print(f"Unexpected error while processing {title}: {e}")
    
    def navigate_to_url(self, url):
        try:
            self.driver.get(url)
            time.sleep(self.time_to_wait)  # Adjusted for page loading
        except WebDriverException as e:
            logger.error(f"Error navigating to URL {url}: {e}")

    
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
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timeout waiting for element: {value}")
        except WebDriverException as e:
            print(f"WebDriverException encountered: {e}")
        return None
    
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
        element = self.wait_for_element(by, value)
        return element.text.strip() if element else default_text
    
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
        element = self.wait_for_element(by, value)
        return element.get_attribute(attribute) if element and element.get_attribute(attribute) else default_value

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
