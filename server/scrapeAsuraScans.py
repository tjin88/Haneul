import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout, TooManyRedirects
import time
from dateutil.parser import parse
import urllib.parse
import re
import os
from dotenv import load_dotenv

def get_text_or_default(soup, selector, attribute=None, default='Not Available'):
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


def scrape_with_retries(book_url, max_retries=3, delay=10):
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
            return scrape_book_details(book_url)
        except (ConnectionError, Timeout) as e:
            print(f"Attempt {attempt + 1}: Network error ({e}). Retrying in {delay} seconds...")
            time.sleep(delay)
        except (HTTPError, TooManyRedirects) as e:
            print(f"Attempt {attempt + 1}: Non-recoverable error ({e}). Stopping retries.")
            return None

    print(f"Failed to scrape {book_url} after {max_retries} attempts.")
    return None


def extract_chapter_number(chapter_str):
    match = re.search(r'\d+', chapter_str)
    return match.group(0) if match else None


def scrape_book_details(book_url):
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
            'title': get_text_or_default(soup, ('h1', {'class': 'entry-title'})),
            'synopsis': 'Not Available',  # Placeholder for synopsis,
            'author': 'Not Available',  # Placeholder for author
            'artist': 'Not Available',  # Placeholder for artist
            'released_by': 'Not Available',  # Placeholder for released_by
            'serialization': 'Not Available',  # Placeholder for serialization
            'posted_by': get_text_or_default(soup, ('span', {'class': 'author'})),
            'posted_on': get_text_or_default(soup, ('time', {'itemprop': 'datePublished'}), attribute='datetime'),
            'updated_on': get_text_or_default(soup, ('time', {'itemprop': 'dateModified'}), attribute='datetime'),
            'newest_chapter': extract_chapter_number(get_text_or_default(soup, ('span', {'class': 'epcur epcurlast'}))),
            'genres': [a.get_text().strip() for a in soup.find('span', class_='mgen').find_all('a')] if soup.find('span', class_='mgen') else [],
            'image_url': get_text_or_default(soup, ('img', {'class': 'wp-post-image'}), attribute='src'),
            'rating': get_text_or_default(soup, ('div', {'itemprop': 'ratingValue'})),
            'status': 'Not Available',  # Placeholder for status
            'manga_type': 'Not Available',  # Placeholder for manga_type
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
                details['manga_type'] = text.replace('Type', '').strip()
        
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
        print(f"Error occurred while fetching book details from {book_url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Return some default value
    return None


def scrape_book_titles(url):
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
                books[title] = scrape_with_retries(book_url) or 'Details not available'

        return books

    except (HTTPError, ConnectionError, Timeout, TooManyRedirects, RequestException) as e:
        print(f"Error occurred while fetching the main page: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    # Return some default value
    return {}


def get_existing_data(api_url):
    """
    Retrieves existing data from the API endpoint.

    Parameters:
    api_url (str): The URL of the API endpoint.

    Returns:
    list: A list of existing data if the request is successful, otherwise an empty list.
    """
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to retrieve existing data. Status code: {response.status_code}")
            return []
    except RequestException as e:
        print(f"An error occurred while retrieving existing data: {e}")
        return []


def format_existing_data_to_dict(existing_data_list):
    """
    Converts a list of book dictionaries into a dictionary of dictionaries indexed by the book title.

    Parameters:
    existing_data_list (list): A list of dictionaries where each dictionary contains details of a book.

    Returns:
    dict: A dictionary of dictionaries, with each key being a book title and its value being the book's details.
    """
    formatted_data = {}
    for book in existing_data_list:
        title = book.get('title')
        if title:
            formatted_data[title] = book
    return formatted_data


def is_data_new(existing_data, new_data):
    """
    Determines if the new data for a book is different from the existing data.

    Args:
    existing_data (dict): The existing book data stored in the database (a dictionary of dictionaries).
    new_data (dict): The newly scraped book data.

    Returns:
    bool: True if the new data is different from the existing data, False otherwise.
    """
    # Retrieve the existing book data by title, if it exists
    existing_book_data = existing_data.get(new_data['title'])

    if not existing_book_data:
        return True  # New book, not in existing data

    for key, value in new_data.items():
        if key == 'id' or key == 'followers':
            continue  # Skip 'id' and 'followers' fields (No need to update followers every time)
        
        if key in ['posted_on', 'updated_on']:
            # Normalize and compare date format fields
            if parse(existing_book_data[key]) != parse(value):
                return True
            continue

        # Handle rating field (some ratings can have 2 decimals, others only have 1)
        if key == 'rating':
            if float(existing_book_data[key] or 0) != float(value or 0):
                return True
            continue

        # Check for other field differences
        if key not in existing_book_data or existing_book_data[key] != value:
            return True

    # If all fields match, the data is not new
    return False


# URL encode the title
def encode_title(title):
    return urllib.parse.quote(title)


def send_book_data(api_url, book_data, existing_data):
    """
    Sends book data to the API for adding new books or updating existing ones.

    Args:
    api_url (str): The URL of the API endpoint.
    book_data (dict): The data of the book to be sent.
    existing_data (dict): The existing books data for comparison.

    Returns:
    int: 1 for success, -1 for failure, 0 for no action needed.
    """
    if is_data_new(existing_data, book_data):
        try:
            headers = {'Content-Type': 'application/json'}
            book_title = book_data['title']
            request_url = f"{api_url}{encode_title(book_title)}/"  # URL encoding for the book title

            # Choose POST or PUT based on whether the book exists
            response = requests.post(api_url, json=book_data, headers=headers) if book_title not in existing_data \
                       else requests.put(request_url, json=book_data, headers=headers)

            if response.status_code in [200, 201]:
                print(f"Book '{book_title}' successfully pushed to the database.")
                return 1
            else:
                print(f"Error updating '{book_title}': Status code {response.status_code}.")
                return -1
        except RequestException as e:
            print(f"Error processing '{book_title}': {e}")
            return -1
    else:
        # print(f"Book '{book_data['title']}' is up-to-date. No update needed.")
        return 0


if __name__ == "__main__":
    # Define URLs for scraping and API endpoint
    url = 'https://asuratoon.com/manga/list-mode/'

    # Load environment variables from .env file
    load_dotenv()  
    api_url = os.getenv('BACKEND_URL')

    # Retrieve existing data from the API
    existing_data = format_existing_data_to_dict(get_existing_data(api_url))

    # Initialize counters for book processing
    pushed_books, error_books = 0, 0

    # Scrape the titles and details
    books = scrape_book_titles(url)
    if books == 'Details not available':
        print("Unsucessful scraping. It is assumed to be a network issue - please try again in 3+ minutes.")
    else:
        total_books = len(books)

        # Process each scraped book
        for title, details in books.items():
            book_data = {
                'title': details.get('title'),
                'synopsis': details.get('synopsis'),
                'author': details.get('author'),
                'artist': details.get('artist'),
                'released_by': details.get('released_by'),
                'serialization': details.get('serialization'),
                'posted_by': details.get('posted_by'),
                'posted_on': details.get('posted_on'),
                'updated_on': details.get('updated_on'),
                'newest_chapter': details.get('newest_chapter'),
                'genres': details.get('genres', []),
                'image_url': details.get('image_url'),
                'rating': details.get('rating'),
                'status': details.get('status'),
                'manga_type': details.get('manga_type'),
                'followers': details.get('followers'),
                'chapters': details.get('chapters')
            }
            
            # Update database (if needed) with new or modified book data
            result = send_book_data(api_url, book_data, existing_data)
            if result == 1:
                pushed_books += 1
            elif result == -1:
                error_books += 1

        # Log summary of scraping results
        print(f"{total_books} books scraped. {pushed_books} updated, {error_books} errors, {total_books - pushed_books - error_books} unchanged.")
