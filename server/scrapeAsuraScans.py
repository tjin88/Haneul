import requests
import json
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout, TooManyRedirects
import time
from dateutil.parser import parse
import urllib.parse

def get_text_or_default(soup, selector, attribute=None, default='Not Available'):
    """
    Extracts text or attribute from a BeautifulSoup element. Returns a default value if not found.
    :param soup: BeautifulSoup object
    :param selector: Tuple for selecting the element
    :param attribute: Attribute to extract (optional)
    :param default: Default value if element or attribute not found
    :return: Extracted text or attribute value
    """
    element = soup.find(*selector)
    if element:
        if attribute:
            return element[attribute] if element.has_attr(attribute) else default
        return element.get_text().strip()
    return default


def scrape_with_retries(book_url, max_retries=3, delay=10):
    """
    Attempts to scrape the book details, retrying on failure up to a maximum number of retries.
    :param book_url: URL to scrape
    :param max_retries: Maximum number of retries
    :param delay: Delay between retries in seconds
    :return: Scraped data or None
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return scrape_book_details(book_url)
        except (ConnectionError, Timeout) as e:
            last_exception = e
            print(f"Network-related error on attempt {attempt + 1}: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
        except (HTTPError, TooManyRedirects) as e:
            # For these errors, retrying might not be helpful
            print(f"Persistent error on attempt {attempt + 1}: {e}. Aborting retries.")
            return None

    print(f"Failed to scrape {book_url} after {max_retries} attempts due to: {last_exception}")
    return None


def scrape_book_details(book_url):
    """
    Scrapes detailed information about a book from its individual page.
    :param book_url: URL of the book's detail page
    :return: Dictionary containing book details
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
            'newest_chapter': get_text_or_default(soup, ('span', {'class': 'epcur epcurlast'})),
            'genres': [a.get_text().strip() for a in soup.find('span', class_='mgen').find_all('a')] if soup.find('span', class_='mgen') else [],
            'image_url': get_text_or_default(soup, ('img', {'class': 'wp-post-image'}), attribute='src'),
            'rating': get_text_or_default(soup, ('div', {'itemprop': 'ratingValue'})),
            'status': 'Not Available',  # Placeholder for status
            'manga_type': 'Not Available',  # Placeholder for manga_type
        }

        # Extracting fields from 'imptdt' class elements
        imptdt_elements = soup.find_all('div', class_='imptdt')
        for element in imptdt_elements:
            text = element.get_text().strip()
            if 'Status' in text:
                details['status'] = text.replace('Status', '').strip()
            elif 'Type' in text:
                details['tymanga_typepe'] = text.replace('Type', '').strip()
        
        # Extracting released_by, serialization, and posted_by
        fmed_elements = soup.find_all('div', class_='fmed')
        for element in fmed_elements:
            b_element = element.find('b')
            span_element = element.find('span')
            if b_element and span_element:
                category = b_element.get_text().strip()
                value = span_element.get_text().strip()
                if 'Released' in category:
                    details['released_by'] = value
                elif 'Serialization' in category:
                    details['serialization'] = value
                elif 'Artist' in category:
                    details['artist'] = value
                elif 'Author' in category:
                    details['author'] = value

        # Extracting followers count
        followers_element = soup.find('div', class_='bmc')
        if followers_element:
            details['followers'] = followers_element.get_text().strip()

        # Extracting the synopsis
        synopsis = ' '.join(p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip())
        if synopsis:
            details['synopsis'] = synopsis

        return details

    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except TooManyRedirects as redirects_err:
        print(f"Too many redirects: {redirects_err}")
    except RequestException as e:
        print(f"Error fetching book details from {book_url}: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    # Return some default value
    return None


def scrape_book_titles(url):
    """
    Scrapes titles and corresponding URLs from the main page and fetches their details.
    :param url: URL of the main page to scrape
    :return: Dictionary containing titles and their details
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        book_elements = soup.find_all('a', class_='series')

        books = {}
        for element in book_elements:
            title = element.get_text().strip()
            if title and title not in books:
                book_url = element['href']
                # Retry scraping in case of network-related errors
                books[title] = scrape_with_retries(book_url) or 'Details not available'

        return books

    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except TooManyRedirects as redirects_err:
        print(f"Too many redirects: {redirects_err}")
    except RequestException as e:
        print(f"Error fetching the main page: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # Return some default value
    return {}


def get_existing_data(api_url):
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to retrieve existing data. Status code: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while retrieving existing data: {e}")
        return []


def format_existing_data_to_dict(existing_data_list):
    formatted_data = {}
    for book in existing_data_list:
        title = book.get('title')
        if title:
            formatted_data[title] = book
    return formatted_data


def is_data_new(existing_data, new_data):
    # Retrieve the existing book data by title, if it exists
    existing_book_data = existing_data.get(new_data['title'])

    # If existing_data is empty, it's new data
    if not existing_book_data:
        return True

    # If the book exists, check all fields for any differences
    for key, value in new_data.items():
        # If a key in new_data is not in existing_book_data or values are different, return True
        if key == 'id':
            continue

        # Normalize the date formats before comparing them
        if key in ['posted_on', 'updated_on']:
            existing_date = parse(existing_book_data[key])
            new_date = parse(value)
            if existing_date != new_date:
                return True
            continue

        # Handle rating field (some ratings can have 2 decimals, others only have 1)
        if key in ['rating']:
            existing_value = float(existing_book_data[key]) if existing_book_data[key] else None
            new_value = float(value) if value else None
            if existing_value != new_value:
                return True
            continue

        # Handle followers (No need to update followers every time)
        if key in ['followers']:
            continue

        if key not in existing_book_data or existing_book_data[key] != value:
            print(f"Book: {new_data['title']}, existing_book_data[{key}]: {existing_book_data[key]}, value: {value}")
            return True

    # If all fields match, the data is not new
    return False


# URL encode the title
def encode_title(title):
    return urllib.parse.quote(title)


def send_book_data(api_url, book_data, existing_data):
    # Only update the data if the existing data (stored in the database) is different from the new data
    if is_data_new(existing_data, book_data):
        try:
            headers = {'Content-Type': 'application/json'}
            book_title = book_data['title']

            # Check if the book exists
            if book_title not in existing_data:
                # POST request to add new book
                print(f"Adding new book to Django")
                response = requests.post(api_url, data=json.dumps(book_data), headers=headers)
            else:
                # URL encode the book title
                encoded_title = encode_title(book_title)

                # PUT request to update existing book
                response = requests.put(f"{api_url}{encoded_title}/", data=json.dumps(book_data), headers=headers)

            if response.status_code in [201, 200]:
                # print(f"response.json(): {response.json()}")
                return 1
            else:
                print(f"Failed to process data for {book_data['title']}. Status code: {response.status_code}")
                # print(f"response.text: {response.text}")
                return -1
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while processing data for {book_data['title']}: {e}")
            return -1
    else:
        # print(f"Data for {book_data['title']} is up-to-date. Skipping.")
        return 0


# Main function:
if __name__ == "__main__":
    # URL of the webpage to scrape
    url = 'https://asuratoon.com/manga/list-mode/'
    api_url = 'http://127.0.0.1:8000/centralized_API_backend/api/manga/'

    # Get existing data from the database
    existing_data_list = get_existing_data(api_url)
    existing_data = format_existing_data_to_dict(existing_data_list)

    books_updated = 0

    # Scrape the titles and details
    books = scrape_book_titles(url)
    if books == 'Details not available':
        print("Unsucessful scraping. It is assumed to be a network issue - please try again in 3+ minutes.")

    else:
        pushed_books = 0
        error_books = 0
        total_books = len(books)

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
                'followers': details.get('followers')
            }
            
            # Send scraped data to MongoDB through Django app
            send_book_data_response = send_book_data(api_url, book_data, existing_data)
            if send_book_data_response == 1:
                pushed_books += 1
            elif send_book_data_response == -1:
                error_books += 1

        # Scraping completed successfully
        print(f"A total of {total_books} books were scraped from AsuraScans")
        print(f"A total of {total_books - pushed_books - error_books} books were already up-to-date in the database")
        print(f"A total of {pushed_books} books were updated in the database")
        print(f"A total of {error_books} books encountered an issue when updating the database")

