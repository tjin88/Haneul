import datetime
import json
import time
import os
import re
import django
import logging
import requests
import threading
import urllib.parse
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout, TooManyRedirects
from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, DatabaseError, connection
from django.core.exceptions import ValidationError
from bson import ObjectId, Decimal128
import traceback
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

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
log_directory = "../out/HiveScans"
log_base_filename = "scrapeHiveScans"
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
logger = logging.getLogger("HiveScansScraper")

class HiveScansScraper:
    def __init__(self):
        self.MAX_THREADS = 3 # max thread count (or number of concurrent windows used for scraping)
        self.continue_scraping = True

    def scrape_hive_scans(self):
        base_url = 'https://hivescans.com/az-list/'
        books = self.scrape_main_page(base_url)

        logger.info(f"Found {len(books)} books. Starting to scrape details.")

        results = {'processed': 0, 'skipped': 0, 'error': 0, 'cancelled': 0}
        book_number = 0
        total_books = len(books)
        futures = []

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

        logger.info(f"Books Processed: {results['processed']}, Skipped: {results['skipped']}, Errors: {results['error']}")
        logger.info(f"There should be {total_books} books!")

    def scrape_book_and_update_db(self, title_url_tuple, book_number, total_books):
        if not self.continue_scraping:
            return {'status': 'cancelled', 'title': title_url_tuple[0]}
    
        title, url = title_url_tuple
        try:
            start_time = datetime.datetime.now()

            with connection.cursor() as cursor:
                cursor.execute("SELECT newest_chapter FROM all_books WHERE title = %s AND novel_source = %s", [title, 'HiveScans'])
                existing_book = cursor.fetchone()

            newest_chapter = self.scrape_newest_chapter(url)
            if not newest_chapter or newest_chapter == "Chapter not available" or newest_chapter.strip() == "Chapter  ?":
                # logger.warning(f"No chapters found for {title}. Skipping.")
                if existing_book:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM all_books WHERE title = %s AND novel_source = %s", [title, 'HiveScans'])
                        cursor.execute("DELETE FROM all_books_genres WHERE allbooks_title = %s AND allbooks_novel_source = %s", [title, 'HiveScans'])
                    logger.info(f"Deleted {title} from the database.")
                return {'status': 'skipped', 'title': title}

            if existing_book and newest_chapter == existing_book[0]:
                duration = datetime.datetime.now() - start_time
                formatted_duration = self.format_duration(duration)
                # logger.info(f"{book_number}/{total_books} took {formatted_duration} to 'skip': {title}")
                return {'status': 'skipped', 'title': title}

            details = self.scrape_book_details(url)
            details['newest_chapter'] = newest_chapter

            if len(json.dumps(details['chapters'])) == 0:
                logger.warning(f"No chapters found for {title}. Skipping.")
                return {'status': 'skipped', 'title': title}

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

    def scrape_main_page(self, url):
        books = []
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Get all the URLs from the "lista" section
            lista_links = [a['href'] for a in soup.find('div', class_='lista').find_all('a')]
            
            for list_url in lista_links:
                current_url = list_url
                while current_url:
                    response = requests.get(current_url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    book_elements = soup.find_all('div', class_='bsx')
                    for element in book_elements:
                        link = element.find('a')
                        title = link.get('title').strip()
                        book_url = link.get('href').strip()
                        books.append((title, book_url))

                    next_page_element = soup.find('a', class_='next page-numbers')
                    current_url = next_page_element['href'] if next_page_element else None

        except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
            logger.error(f"Error occurred while fetching main page: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

        return books

    def scrape_book_details(self, book_url):
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            details = {
                'title': self.get_text_or_default(soup, ('h1', {'class': 'entry-title'})),
                'synopsis': 'Not Available',  # Placeholder for synopsis,
                'author': 'Not Available',  # Placeholder for author
                'updated_on': self.get_text_or_default(soup, ('time', {'itemprop': 'dateModified'}), attribute='datetime'),
                'newest_chapter': None,
                'genres': [a.get_text().strip() for a in soup.find('span', class_='mgen').find_all('a')] if soup.find('span', class_='mgen') else [],
                'image_url': self.get_text_or_default(soup, ('img', {'class': 'wp-post-image'}), attribute='src'),
                'rating': self.get_text_or_default(soup, ('div', {'itemprop': 'ratingValue'})),
                'status': 'Not Available',  # Placeholder for status
                'novel_type': 'Manhwa',  # Placeholder for novel_type
                'novel_source': 'HiveScans',  # This is always true
                'followers': 'Not Available',  # Placeholder for followers
                'chapters': {},  # Placeholder for chapters
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

        return None

    def scrape_newest_chapter(self, book_url):
        try:
            response = requests.get(book_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.get_text_or_default(soup, ('span', {'class': 'epcur epcurlast'}), default='Chapter not available')
        except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
            logger.error(f"Error occurred while fetching newest chapter from {book_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    def get_text_or_default(self, soup, selector, attribute=None, default='Not Available'):
        element = soup.find(*selector)
        if element:
            return element[attribute].strip() if attribute and element.has_attr(attribute) else element.get_text().strip()
        return default

    @staticmethod
    def extract_chapter_number(chapter_str):
        match = re.search(r'\d+', chapter_str)
        return match.group(0) if match else None

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
    help = 'Scrapes books from HiveScans and updates the database.'

    def handle(self, *args, **kwargs):
        logger.info("Starting to scrape HiveScans")

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM all_books")
                count = cursor.fetchone()[0]
                logger.info(f"Found {count} books in the database")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return

        start_time = datetime.datetime.now()
        scraper = HiveScansScraper()
        try:
            scraper.scrape_hive_scans()

            duration = datetime.datetime.now() - start_time
            formatted_duration = self.format_duration(duration)

            logger.info(f"Successfully executed scrapeHiveScans in {formatted_duration} ")
            self.stdout.write(self.style.SUCCESS('Successfully executed scrapeHiveScans'))
        except ConnectionError:
            logger.error(f"Looks like the computer was not connected to the internet. Abandoned this attempt to update server for HiveScans books.")
        except Exception as e:
            logger.error(f"An error occurred during scraping: {e}")
            raise CommandError(f"Scraping failed due to an error: {e}")
    
    @staticmethod
    def format_duration(duration):
        seconds = duration.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        if hours == 0:
            return f"{minutes}m {seconds}s"
        return f"{hours}h {minutes}m {seconds}s"

if __name__ == "__main__":
    Command().handle()
