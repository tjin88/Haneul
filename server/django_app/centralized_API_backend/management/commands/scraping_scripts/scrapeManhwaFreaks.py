import datetime
import json
import time
import os
import re
import django
import logging
import requests
import urllib.parse
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout, TooManyRedirects
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, DatabaseError, connection
from django.core.exceptions import ValidationError
from bson import ObjectId, Decimal128
import traceback
import sys

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
log_directory = "../out/ManhwaFreaks"
log_base_filename = "scrapeManhwaFreaks"
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
logger = logging.getLogger("ManhwaFreaksScraper")

class ManhwaFreaksScraper:
    def scrape_manhwa_freaks(self):
        # Define URLs for scraping
        url = 'https://manhwafreaks.org/manga/list-mode/'

        # Initialize counters for book processing
        pushed_books, error_books = 0, 0

        # Scrape the titles and details
        books = self.scrape_book_titles(url)
        if books == 'Details not available':
            logger.error("Unsuccessful scraping. It is assumed to be a network issue - please try again in 3+ minutes.")
        else:
            total_books = len(books)
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_title = {executor.submit(self.scrape_book_and_update_db, title_url, idx + 1, total_books): title_url for idx, title_url in enumerate(books.items())}

                for future in as_completed(future_to_title):
                    title_url = future_to_title[future]
                    try:
                        result = future.result()
                        if result['status'] == 'processed':
                            pushed_books += 1
                        elif result['status'] == 'skipped':
                            continue
                        else:
                            error_books += 1
                    except Exception as e:
                        logger.error(f"Error processing {title_url}: {e}")
                        error_books += 1

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

            details = {
                'title': self.get_text_or_default(soup, ('h1', {'class': 'entry-title'})),
                'synopsis': 'Not Available',
                'author': 'Not Available',
                'updated_on': self.get_text_or_default(soup, ('time', {'itemprop': 'dateModified'}), attribute='datetime'),
                'newest_chapter': self.extract_chapter_number(self.get_text_or_default(soup, ('span', {'class': 'epcur epcurlast'}))),
                'genres': [a.get_text().strip() for a in soup.find('span', class_='mgen').find_all('a')] if soup.find('span', class_='mgen') else [],
                'image_url': self.get_text_or_default(soup, ('img', {'class': 'wp-post-image'}), attribute='src'),
                'rating': self.get_text_or_default(soup, ('div', {'itemprop': 'ratingValue'})),
                'status': 'Not Available',
                'novel_type': 'Manhwa',
                'novel_source': 'ManhwaFreaks',
                'followers': 'Not Available',
                'chapters': {},
            }

            imptdt_elements = soup.find_all('div', class_='imptdt')
            for element in imptdt_elements:
                text = element.get_text().strip()
                if 'Status' in text:
                    details['status'] = text.replace('Status', '').strip()
                elif 'Type' in text:
                    details['novel_type'] = text.replace('Type', '').strip()

            fmed_elements = soup.find_all('div', class_='fmed')
            for element in fmed_elements:
                b_element = element.find('b')
                span_element = element.find('span')
                if b_element and span_element:
                    category = b_element.get_text().strip()
                    value = span_element.get_text().strip()
                    if 'Author' in category and value != '-':
                        details['author'] = value

            followers_element = soup.find('div', class_='bmc')
            if followers_element:
                details['followers'] = followers_element.get_text().strip()

            synopsis = ' '.join(p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip())
            if synopsis:
                details['synopsis'] = synopsis

            chapter_elements = soup.select('#chapterlist li[data-num]')
            chapters = {}
            for chapter in chapter_elements:
                chapter_num = chapter['data-num']
                chapter_url = chapter.find('a')['href']
                if chapter_num and chapter_url:
                    chapters[chapter_num] = chapter_url

            details['chapters'] = chapters

            return details

        except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
            logger.error(f"Error occurred while fetching book details from {book_url}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

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
                if title and book_url:
                    normalized_title = self.normalize_title(title)
                    if normalized_title not in books:
                        books[normalized_title] = book_url
            return books
        except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
            logger.error(f"Error occurred while fetching the main page: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

        return {}

    def is_data_new(self, existing_book_data, new_data):
        """
        Determines if the new data for a book is different from the existing data.

        Args:
        existing_book_data (dict): The existing book data from the database.
        new_data (dict): The newly scraped book data.

        Returns:
        bool: True if the new data is different from the existing data, False otherwise.
        """
        # logger.info(f"Existing book data: {existing_book_data}")
        # logger.info(f"New book data: {new_data}")

        for key, value in new_data.items():
            if key in ['id', 'followers', 'genres']:
                continue

            if key in ['posted_on', 'updated_on']:
                existing_value = existing_book_data.get(key)
                if isinstance(existing_value, datetime.datetime):
                    existing_date = existing_value.replace(tzinfo=None)
                else:
                    try:
                        existing_date = parse(existing_value).replace(tzinfo=None) if existing_value else None
                    except ValueError:
                        # Handle the case where the date parsing fails
                        logger.info(f'is_data_new returned True for {key} due to ValueError')
                        return True

                if isinstance(value, str):
                    try:
                        new_date = parse(value).replace(tzinfo=None) if value else None
                    except ValueError:
                        # Handle the case where the date parsing fails
                        logger.info(f'is_data_new returned True for {key} due to ValueError')
                        return True
                else:
                    new_date = value.replace(tzinfo=None) if value else None

                if existing_date != new_date:
                    logger.info(f'is_data_new returned True for "existing_date" due to some difference. existing_date: {existing_date}, new_date: {new_date}')
                    return True
                continue

            # Handle rating field (some ratings can have 2 decimals, others only have 1)
            if key == 'rating':
                existing_rating = existing_book_data.get(key, 0) or 0
                if isinstance(existing_rating, Decimal128):
                    existing_rating = float(existing_rating.to_decimal())
                else:
                    existing_rating = float(existing_rating)

                new_rating = float(value or 0)
                if existing_rating != new_rating:
                    logger.info(f'is_data_new returned True for "rating" due to some difference')
                    return True
                continue

            # Handle chapters field by comparing sorted dictionaries
            if key == 'chapters':
                existing_chapters = existing_book_data.get(key, {})
                new_chapters = value or {}

                if isinstance(existing_chapters, str):
                    try:
                        existing_chapters = json.loads(existing_chapters)
                    except json.JSONDecodeError:
                        logger.info(f'is_data_new returned True for "chapters" due to JSONDecodeError on existing_chapters')
                        return True

                if isinstance(new_chapters, str):
                    try:
                        new_chapters = json.loads(new_chapters)
                    except json.JSONDecodeError:
                        logger.info(f'is_data_new returned True for "chapters" due to JSONDecodeError on new_chapters')
                        return True

                # Sort the chapters dictionaries by keys
                existing_chapters_sorted = dict(sorted(existing_chapters.items()))
                new_chapters_sorted = dict(sorted(new_chapters.items()))

                if existing_chapters_sorted != new_chapters_sorted:
                    logger.info(f'is_data_new returned True for "chapters" due to some difference')
                    logger.info(f'Existing value: {existing_chapters_sorted}, new_data value: {new_chapters_sorted}')
                    return True
                continue

            # Check for other field differences
            if existing_book_data.get(key) != value:
                logger.info(f'is_data_new returned True for {key} due to some difference')
                logger.info(f'Existing value: {existing_book_data.get(key)}, new_data value: {value}')
                return True

        return False

    def normalize_title(self, title):
        """
        Normalizes the title by replacing all occurrences of ' with ’.
        """
        return title.replace("'", "’")

    def scrape_book_and_update_db(self, title_url_tuple, book_number, total_books):
        title, url = title_url_tuple
        try:
            start_time = datetime.datetime.now()

            # Normalize the title. Needed to not break the database LOL
            normalized_title = self.normalize_title(title)

            with connection.cursor() as cursor:
                cursor.execute("SELECT newest_chapter FROM all_books WHERE title = %s AND novel_source = %s", [normalized_title.strip(), 'ManhwaFreaks'])
                existing_book = cursor.fetchone()

            newest_chapter = self.scrape_newest_chapter(url)
            if existing_book and newest_chapter == existing_book[0]:
                # duration = datetime.datetime.now() - start_time
                # formatted_duration = self.format_duration(duration)
                # logger.info(f"{book_number}/{total_books} took {formatted_duration} to 'skip': {normalized_title}")
                return {'status': 'skipped', 'title': normalized_title}

            details = self.scrape_book_details(url)

            if len(details['chapters']) == 0:
                logger.warning(f"No chapters found for {normalized_title}. Skipping.")
                return {'status': 'skipped', 'title': normalized_title}

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
                    details['title'].strip(),
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

                cursor.execute("DELETE FROM all_books_genres WHERE allbooks_title = %s AND allbooks_novel_source = %s", [details['title'].strip(), details['novel_source']])
                for genre_name in details['genres']:
                    genre_name = genre_name.strip().lower()
                    cursor.execute("SELECT id FROM genre WHERE name = %s", [genre_name])
                    genre_id = cursor.fetchone()
                    if not genre_id:
                        cursor.execute("INSERT INTO genre (name) VALUES (%s) RETURNING id", [genre_name])
                        genre_id = cursor.fetchone()[0]
                    else:
                        genre_id = genre_id[0]
                    cursor.execute("INSERT INTO all_books_genres (genre_id, allbooks_title, allbooks_novel_source) VALUES (%s, %s, %s)", [genre_id, details['title'].strip(), details['novel_source']])

            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)

            logger.info(f"{book_number}/{total_books} took {formatted_duration} to {'create' if not existing_book else 'update'} {normalized_title}, with {len(details['chapters'])} chapters")
            return {'status': 'processed', 'title': normalized_title}
        except DatabaseError as e:
            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)
            logger.error(f"{book_number}/{total_books} took {formatted_duration} to encounter a 'database error': {normalized_title}. Error: {e}")
            return {'status': 'database_error', 'title': normalized_title, 'message': str(e)}
        except Exception as e:
            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(f"{book_number}/{total_books} took {formatted_duration} to encounter an 'error': {normalized_title}. Error message: {e}")
            logger.error(f"Exception Type: {exc_type}")
            logger.error(f"Exception Value: {exc_value}")
            logger.error(f"Traceback: {''.join(traceback.format_tb(exc_traceback))}")
            return {'status': 'error', 'title': normalized_title, 'message': str(e)}

    def scrape_newest_chapter(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.extract_chapter_number(self.get_text_or_default(soup, ('span', {'class': 'epcur epcurlast'})))
        except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
            logger.error(f"Error occurred while fetching newest chapter from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    @staticmethod
    def format_duration(duration):
        total_duration = duration.total_seconds()
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        milliseconds = int((total_duration - int(total_duration)) * 1000)
        if hours == 0:
            return f"{minutes}m {seconds}s {milliseconds}ms"
        return f"{hours}h {minutes}m {seconds}s"

class Command(BaseCommand):
    help = 'Scrapes books from ManhwaFreaks and updates the database.'

    def handle(self, *args, **kwargs):
        """
        Handles the command execution for scraping books from ManhwaFreaks.

        Executes the scraping process, calculates the duration of the operation, and logs the result.
        """
        logger.info("Starting to scrape ManhwaFreaks")

        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM all_books")
                count = cursor.fetchone()[0]
                logger.info(f"Found {count} books in the database")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return

        start_time = datetime.datetime.now()
        scraper = ManhwaFreaksScraper()
        try:
            scraper.scrape_manhwa_freaks()

            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)

            logger.info(f"Successfully executed scrapeManhwaFreaks in {formatted_duration} ")
            self.stdout.write(self.style.SUCCESS('Successfully executed scrapeManhwaFreaks'))
        except ConnectionError:
            logger.error(f"Looks like the computer was not connected to the internet. \
                         Abandoned this attempt to update server for ManhwaFreaks books.")
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
