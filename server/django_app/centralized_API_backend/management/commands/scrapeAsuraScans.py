import datetime
import time
import os
import re
import django
import logging
import requests
import urllib.parse
from bson.decimal128 import Decimal128
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout, TooManyRedirects
from dateutil.parser import parse
from centralized_API_backend.models import AsuraScans
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.core.exceptions import ValidationError

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
log_directory = "../out/AsuraScans"
log_base_filename = "scrapeAsuraScans"
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
logger = logging.getLogger("LightNovelPubScraper")

class AsuraScansScraper:
    def scrape_asura_scans(self):
        # Define URLs for scraping and API endpoint
        url = 'https://asuratoon.com/manga/list-mode/'

        # Retrieve existing data from the API
        # existing_data = format_existing_data_to_dict(get_existing_data(api_url))

        # Initialize counters for book processing
        pushed_books, error_books = 0, 0

        # Scrape the titles and details
        books = self.scrape_book_titles(url)
        if books == 'Details not available':
            logger.error("Unsucessful scraping. It is assumed to be a network issue - please try again in 3+ minutes.")
        else:
            total_books = len(books)

            # Process each scraped book
            # TODO: Removed artist, released_by, serialization, posted_by, and posted_on fields
            #       to match novels from light novel pub
            for title, details in books.items():
                book_data = {
                    'title': details.get('title'),
                    'synopsis': details.get('synopsis'),
                    'author': details.get('author'),
                    # 'artist': details.get('artist'),
                    # 'released_by': details.get('released_by'),
                    # 'serialization': details.get('serialization'),
                    # 'posted_by': details.get('posted_by'),
                    # 'posted_on': details.get('posted_on'),
                    'updated_on': details.get('updated_on'),
                    'newest_chapter': details.get('newest_chapter'),
                    'genres': details.get('genres', []),
                    'image_url': details.get('image_url'),
                    'rating': details.get('rating'),
                    'status': details.get('status'),
                    'novel_type': details.get('novel_type'),
                    'novel_source': details.get('novel_source'),
                    'followers': details.get('followers'),
                    'chapters': details.get('chapters')
                }
                
                # Update database (if needed) with new or modified book data
                result = self.send_book_data(book_data)
                if result == 1:
                    pushed_books += 1
                elif result == -1:
                    error_books += 1

            # Log summary of scraping results
            logger.info(f"{total_books} books scraped. {pushed_books} updated, {error_books} errors, {total_books - pushed_books - error_books} unchanged.")


    def get_text_or_default(self, soup, selector, attribute=None, default='Not Available'):
        """
        Extracts text or a specified attribute from an element selected from a BeautifulSoup object.
        
        Parameters:
        soup (BeautifulSoup): The BeautifulSoup object to search within.
        selector (tuple): A tuple containing selector information for BeautifulSoup's find method.
        attribute (str, optional): The attribute to extract from the element. If None, extracts text. Default is None.
        default (str): The default value to return if the element or attribute is not found. Default is 'Not Available'.
        
        Returns:
        str: The extracted text or attribute value, or the default value if not found.
        """
        element = soup.find(*selector)
        if element:
            return element[attribute].strip() if attribute and element.has_attr(attribute) else element.get_text().strip()
        return default


    def scrape_with_retries(self, book_url, max_retries=3, delay=10):
        """
        Scrapes a webpage for book details, with a specified number of retries in case of failure.

        Parameters:
        book_url (str): The URL of the book page to scrape.
        max_retries (int): Maximum number of retry attempts. Default is 3.
        delay (int): Delay in seconds between retries. Default is 10.

        Returns:
        dict or None: The scraped book data as a dictionary if successful, None if all retries fail.
        """
        for attempt in range(max_retries):
            try:
                return self.scrape_book_details(book_url)
            except (ConnectionError, Timeout) as e:
                logger.warning(f"Attempt {attempt + 1}: Network error ({e}). Retrying in {delay} seconds...")
                time.sleep(delay)
            except (HTTPError, TooManyRedirects) as e:
                logger.error(f"Attempt {attempt + 1}: Non-recoverable error ({e}). Stopping retries.")
                return None

        logger.error(f"Failed to scrape {book_url} after {max_retries} attempts.")
        return None


    def extract_chapter_number(self, chapter_str):
        match = re.search(r'\d+', chapter_str)
        return match.group(0) if match else None


    def scrape_book_details(self, book_url):
        """
        Scrapes detailed information about a book from its individual page.
        
        Args:
        book_url (str): URL of the book's detail page.
        
        Returns:
        dict: A dictionary containing key details of the book. Returns None if scraping fails.
        """
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Simplifying extraction process
            details = {
                'title': self.get_text_or_default(soup, ('h1', {'class': 'entry-title'})),
                'synopsis': 'Not Available',  # Placeholder for synopsis,
                'author': 'Not Available',  # Placeholder for author
                'artist': 'Not Available',  # Placeholder for artist
                'released_by': 'Not Available',  # Placeholder for released_by
                'serialization': 'Not Available',  # Placeholder for serialization
                'posted_by': self.get_text_or_default(soup, ('span', {'class': 'author'})),
                'posted_on': self.get_text_or_default(soup, ('time', {'itemprop': 'datePublished'}), attribute='datetime'),
                'updated_on': self.get_text_or_default(soup, ('time', {'itemprop': 'dateModified'}), attribute='datetime'),
                'newest_chapter': self.extract_chapter_number(self.get_text_or_default(soup, ('span', {'class': 'epcur epcurlast'}))),
                'genres': [a.get_text().strip() for a in soup.find('span', class_='mgen').find_all('a')] if soup.find('span', class_='mgen') else [],
                'image_url': self.get_text_or_default(soup, ('img', {'class': 'wp-post-image'}), attribute='src'),
                'rating': self.get_text_or_default(soup, ('div', {'itemprop': 'ratingValue'})),
                'status': 'Not Available',  # Placeholder for status
                'novel_type': 'Manhwa',  # Placeholder for novel_type
                'novel_source': 'AsuraScans',  # This is always true
                'followers': 'Not Available',  # Placeholder for followers
                'chapters': {},  # Placeholder for chapters
            }

            # Extracting fields from 'imptdt' class elements
            imptdt_elements = soup.find_all('div', class_='imptdt')
            for element in imptdt_elements:
                text = element.get_text().strip()
                if 'Status' in text:
                    details['status'] = text.replace('Status', '').strip()
                elif 'Type' in text:
                    details['novel_type'] = text.replace('Type', '').strip()
            
            # Extracting released_by, serialization, and posted_by
            fmed_elements = soup.find_all('div', class_='fmed')
            for element in fmed_elements:
                b_element = element.find('b')
                span_element = element.find('span')
                if b_element and span_element:
                    category = b_element.get_text().strip()
                    value = span_element.get_text().strip()
                    if 'Released' in category and value != '-':
                        details['released_by'] = value
                    elif 'Serialization' in category and value != '-':
                        details['serialization'] = value
                    elif 'Artist' in category and value != '-':
                        details['artist'] = value
                    elif 'Author' in category and value != '-':
                        details['author'] = value

            # Extracting followers count
            followers_element = soup.find('div', class_='bmc')
            if followers_element:
                details['followers'] = followers_element.get_text().strip()

            # Extracting the synopsis
            synopsis = ' '.join(p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip())
            if synopsis:
                details['synopsis'] = synopsis

            # Extracting the book's chapters
            chapter_elements = soup.find_all('li', {'data-num': True})
            chapters = {}
            for chapter in chapter_elements:
                chapter_num = chapter['data-num']
                chapter_url = chapter.find('a')['href']
                chapters[chapter_num] = chapter_url

            details['chapters'] = chapters

            return details

        except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
            logger.error(f"Error occurred while fetching book details from {book_url}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

        # Return some default value
        return None


    def scrape_book_titles(self, url):
        """
        Scrapes book titles and their URLs from the manga list and fetches their details.
        
        Args:
        url (str): URL of the manga list to scrape.
        
        Returns:
        dict: Dictionary containing book titles and their details.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            book_elements = soup.find_all('a', class_='series')

            books = {}
            for element in book_elements:
                title = element.get_text().strip()
                book_url = element['href']
                if title and book_url and title not in books:
                    # Retry scraping in case of network-related errors
                    books[title] = self.scrape_with_retries(book_url) or 'Details not available'

            return books

        except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
            logger.error(f"Error occurred while fetching the main page: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        
        # Return some default value
        return {}

    def is_data_new(self, new_data):
        """
        Determines if the new data for a book is different from the existing data.

        Args:
        new_data (dict): The newly scraped book data.

        Returns:
        bool: True if the new data is different from the existing data, False otherwise.
        """
        # Retrieve the existing book data by title, if it exists
        try:
            existing_book_data = AsuraScans.objects.get(title=new_data['title'])
        except AsuraScans.DoesNotExist:
            return True  # New book, not in existing data

        for key, value in new_data.items():
            if key in ['id', 'followers']:
                continue  # Skip 'id' and 'followers' fields
            
            # Normalize and compare date format fields
            if key in ['posted_on', 'updated_on']:
                existing_value = getattr(existing_book_data, key, None)
                
                if isinstance(existing_value, datetime.datetime):
                    existing_date = existing_value
                else:
                    try:
                        existing_date = parse(existing_value) if existing_value else None
                    except ValueError:
                        # Handle the case where the date parsing fails
                        return True

                # Parse the new date only if it's a string
                if isinstance(value, str):
                    try:
                        new_date = parse(value) if value else None
                    except ValueError:
                        # Handle the case where the date parsing fails
                        return True
                else:
                    new_date = value  # Assuming the passed value is a datetime object

                if existing_date != new_date:
                    return True
                continue

            # Handle rating field (some ratings can have 2 decimals, others only have 1)
            if key == 'rating':
                existing_rating = getattr(existing_book_data, key, 0) or 0
                if isinstance(existing_rating, Decimal128):
                    existing_rating = float(existing_rating.to_decimal())
                else:
                    existing_rating = float(existing_rating)

                new_rating = float(value or 0)
                if existing_rating != new_rating:
                    return True
                continue

            # Check for other field differences
            if getattr(existing_book_data, key, None) != value:
                return True

        # If all fields match, the data is not new
        return False


    # URL encode the title
    def encode_title(self, title):
        return urllib.parse.quote(title)


    def send_book_data(self, book_data):
        """
        Sends book data to the API for adding new books or updating existing ones.

        Args:
        book_data (dict): The data of the book to be sent.

        Returns:
        int: 1 for success, -1 for failure, 0 for no action needed.
        """
        if self.is_data_new(book_data):
            try:
                # headers = {'Content-Type': 'application/json'}
                book_title = book_data['title']
                if book_data['novel_source'] != 'AsuraScans':
                    logger.error(f'[ERROR] NOVEL SOURCE IS INVALID')
                    # TODO: Throw some error here*

                AsuraScans.objects.update_or_create(
                    title=book_data['title'],
                    novel_source=book_data['novel_source'],
                    defaults=book_data
                )

                logger.info(f"Book '{book_title}' successfully pushed to the database.")
                return 1
            except RequestException as e:
                logger.error(f"Error processing '{book_title}': {e}")
                return -1
            except IntegrityError as e:
                logger.error(f"Database integrity error for {book_title}: {e}")
                return -1
            except ValidationError as e:
                logger.error(f"Validation error for {book_title}: {e}")
                return -1
            except Exception as e:
                logger.error(f"Unexpected error while processing book '{book_title}': {e}")
                return -1
        else:
            # print(f"Book '{book_data['title']}' is up-to-date. No update needed.")
            return 0


class Command(BaseCommand):
    help = 'Scrapes light novels from LightNovelPub and updates the database.'

    def handle(self, *args, **kwargs):
        """
        Handles the command execution for scraping light novels.

        Executes the scraping process, calculates the duration of the operation, and logs the result.
        """
        start_time = datetime.datetime.now()
        scraper = AsuraScansScraper()
        try:
            scraper.scrape_asura_scans()

            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)

            logger.info(f"Successfully executed scrapeAsuraScans in {formatted_duration} ")
            self.stdout.write(self.style.SUCCESS('Successfully executed scrapeAsuraScans'))
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