import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

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
            'synopsis': ' '.join(p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()),
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
            'type': 'Not Available',  # Placeholder for type
        }

        # Extracting fields from 'imptdt' class elements
        imptdt_elements = soup.find_all('div', class_='imptdt')
        for element in imptdt_elements:
            text = element.get_text().strip()
            if 'Status' in text:
                details['status'] = text.replace('Status', '').strip()
            elif 'Type' in text:
                details['type'] = text.replace('Type', '').strip()
        
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

        return details

    except RequestException as e:
        print(f"Error fetching book details from {book_url}: {e}")
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
                books[title] = scrape_book_details(book_url) or 'Details not available'

        return books

    except RequestException as e:
        print(f"Error fetching the main page: {e}")
        return {}

# URL of the webpage to scrape
url = 'https://asuratoon.com/manga/list-mode/'

# Scrape the titles and details
books = scrape_book_titles(url)
for title, details in books.items():
    print(f"{title}:")
    for key, value in details.items():
        print(f"  {key}: {value}")

print(f"A total of {len(books)} books were scraped from AsuraScans")

