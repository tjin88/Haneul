# TODO: Protect against SQL Injection attacks
# TODO: Protect against Man-in-the-Middle attacks (Use HTTPS)
# TODO: Protect against Clickjacking attacks
# Using csrf_exempt as tokens are stored in localStorage and not in cookies
# Thus, at the moment, the program is not vulnerable to CSRF attacks
from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
import json
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.http import JsonResponse
from django.middleware.csrf import get_token
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection
from django.views.decorators.http import require_http_methods
from dotenv import load_dotenv
import os
import re
import cloudinary.uploader
from django.middleware.csrf import CsrfViewMiddleware
import requests
from urllib.parse import urlparse
import logging

load_dotenv()  # Load environment variables from .env file
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

###################### HELPER FUNCTIONS ######################
def fetch_books_as_dict(query, params=None, image_url_required=False, upper_limit=None, paginated=False, validate=True):
    """
    Fetches books from database with optional pagination and validation.
    
    Args:
        query (str): SQL query
        params (tuple): Query parameters
        image_url_required (bool): Whether to validate image URLs
        upper_limit (int): Maximum number of valid books to return
        paginated (bool): Whether the query already includes pagination
        
    Returns:
        list: List of valid book dictionaries
    """
    try:
        results = []
        
        if not paginated:
            # Only add pagination if not already included in query
            offset = 0
            page_size = 50
            
            while True:
                paginated_query = f"""
                    WITH base_query AS (
                        {query}
                    )
                    SELECT * FROM base_query
                    OFFSET {offset}
                    LIMIT {page_size}
                """
                
                cursor = connection.cursor()
                cursor.execute(paginated_query, params)
                columns = [col[0] for col in cursor.description]
                
                rows = cursor.fetchall()
                if not rows:  # No more results
                    break
                
                # Process each row in the current page
                for row in rows:
                    try:
                        book = dict(zip(columns, row))
                        if is_valid_book(book, image_url_required):
                            results.append(book)
                            if upper_limit and len(results) >= upper_limit:
                                return results
                    except Exception as e:
                        logger.error(f"Error processing row: {str(e)}")
                        continue
                
                offset += page_size
                
                if upper_limit and offset >= upper_limit * 3:
                    break
        else:
            # Execute the query as is (for already paginated queries)
            cursor = connection.cursor()
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            
            for row in cursor.fetchall():
                try:
                    book = dict(zip(columns, row))
                    if not validate or is_valid_book(book, image_url_required):
                        results.append(book)
                except Exception as e:
                    logger.error(f"Error processing row: {str(e)}")
                    continue
        
        return results
    except Exception as e:
        logger.error(f"Database error in fetch_books_as_dict: {str(e)}")
        return []

def build_paginated_query(base_query):
    """
    Helper function to ensure the base query can be properly paginated.
    Adds proper ORDER BY if not present.
    """
    if "ORDER BY" not in base_query.upper():
        base_query += " ORDER BY id"  # Assuming you have an id column
    return base_query

def fetch_count(query, params=None):
    cursor = connection.cursor()
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    return count

def get_newest_chapter_link(chapters):
    max_chapter = -1
    max_link = ""
    for chapter_key, link in chapters.items():
        try:
            chapter_num = float(re.findall(r"[-+]?\d*\.\d+|\d+", chapter_key)[0])
            if chapter_num > max_chapter:
                max_chapter = chapter_num
                max_link = link
        except (ValueError, IndexError):
            continue
    return max_link

def is_valid_book(book, image_url_required=False):
    """
    Validates all required fields of a book entry.
    
    Args:
        book (dict): Book dictionary containing required fields
        image_url_required (bool): Whether to validate image URL
        
    Returns:
        bool: True if all validations pass, False otherwise
    """
    try:
        # Check if book dict exists
        if not book:
            return False
        
        # Check required fields exist and are non-empty strings
        for field in ['title', 'novel_source', 'novel_type']:
            if not book.get(field) or not isinstance(book[field], str) or not book[field].strip():
                return False
            
        # Validate chapters - handle both string (JSON) and dict cases
        chapters = book.get('chapters')
        if chapters is None:
            return False
            
        # If chapters is a string, try to parse it as JSON
        if isinstance(chapters, str):
            try:
                chapters = json.loads(chapters)
            except json.JSONDecodeError:
                return False
                
        if not isinstance(chapters, dict) or not chapters:
            return False
            
        # Validate image_url if required
        if image_url_required:
            if not book.get('image_url'):
                return False
            if not is_valid_image_url(book['image_url']):
                return False
            
        return True
    except Exception as e:
        logger.error(f"Error validating book {book.get('title', 'Unknown')}: {str(e)}")
        return False

def is_valid_image_url(url):
    """
    Validates if a URL points to an accessible image.
    Handles 400 and 404 errors explicitly.
    """
    try:
        if not url:
            return False
            
        # Basic URL format validation
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        
        # Try to get just the headers to check if image exists
        response = requests.head(url, timeout=2)
        
        # Check for specific error codes
        if response.status_code in [400, 404]:
            return False
            
        content_type = response.headers.get('content-type', '')
        return response.status_code == 200 and content_type.startswith('image/')
    except requests.exceptions.RequestException:
        return False
    except Exception as e:
        logger.error(f"Error checking image URL {url}: {str(e)}")
        return False

# TODO: Fix this!
def parse_and_sort_chapters(chapters):
    # Check if chapters is a JSON string and parse it
    if isinstance(chapters, str):
        try:
            chapters = chapters.replace('\\"', '"')
            chapters_dict = json.loads(chapters)
        except json.JSONDecodeError as e:
            print(f"Error parsing chapters: {e}")
            chapters_dict = {}
    else:
        chapters_dict = chapters

    # Sort chapters based on the first number found in the chapter key
    sorted_chapters = {k: v for k, v in sorted(chapters_dict.items(), key=lambda item: int(re.findall(r'\d+', item[0])[0]) if re.findall(r'\d+', item[0]) else float('inf'))}
    return sorted_chapters

@ensure_csrf_cookie
@api_view(['GET'])
def csrf_token_view(request):
    temp = get_token(request)
    print(f'CSRF token view: {temp}')
    return JsonResponse({'csrfToken': temp})

###################### MAIN FUNCTIONS ######################
class HomeNovelGetView(views.APIView):
    def get(self, request):
        num_carousel_books = 15
        carousel_titles = ("The Novel’s Extra (Remake)", "Nano Machine", "Reverend Insanity")
        # carousel_titles = ("Reaper of the Drifting Moon", "Solo Leveling", "The Strongest Player",
        #                    "Swordmaster’s Youngest Son", "Damn Reincarnation", "My Daughter is the Final Boss",
        #                    "Talent-Swallowing Magician", "Revenge of the Iron-Blooded Sword Hound", "Villain To Kill",
        #                    "The Novel’s Extra (Remake)", "Chronicles Of The Martial God’s Return", "Academy’s Undercover Professor",
        #                    "Everyone Else is A Returnee", "Heavenly Inquisition Sword", "Solo Bug Player",
        #                    "Nano Machine", "Chronicles of the Demon Faction", "Academy’s Genius Swordmaster",
        #                    "Shadow Slave", "Reverend Insanity", "Super Gene (Web Novel)", "Martial World (Web Novel)")
        issue_sites = ("HiveScans", "Animated Glitched Scans", "Arya Scans", "Hiraeth Translation", 
                       "FreakScans", "Manga Galaxy", "Magus Manga", "Immortal Updates",
                       "Reset Scans", "AsuraScans")
        issue_titles = ("The Greatest Sword Hero Returns After 69420 Years", "")

        base_query = """
            SELECT title, image_url, newest_chapter, novel_source, novel_type, chapters
            FROM all_books
            WHERE novel_source NOT IN %s
        """

        # Preferred titles for the carousel
        valid_carousel_books = fetch_books_as_dict(f"{base_query} AND title IN %s", [issue_sites, carousel_titles], image_url_required=True)
        logger.info(f"Valid carousel books: {[book['title'] for book in valid_carousel_books]}")

        # Supplemented books to ensure we have num_carousel_books books in the carousel
        if len(valid_carousel_books) < num_carousel_books:
            valid_additional_books = fetch_books_as_dict(f"{base_query} AND title NOT IN %s ORDER BY updated_on DESC",[issue_sites, carousel_titles], image_url_required=True, upper_limit=num_carousel_books - len(valid_carousel_books))
            # logger.info(f"Additional carousel books: {[book['title'] for book in additional_books]}")

            valid_carousel_books.extend(valid_additional_books[:num_carousel_books - len(valid_carousel_books)])

        recently_updated_books = fetch_books_as_dict(f"{base_query} ORDER BY updated_on DESC", [issue_sites], image_url_required=True, upper_limit=10)
        manga_books = fetch_books_as_dict(f"{base_query} AND novel_type='Manga' ORDER BY rating DESC", [issue_sites], image_url_required=True, upper_limit=10)
        manhua_books = fetch_books_as_dict(f"{base_query} AND novel_type='Manhua' AND title NOT IN %s ORDER BY rating DESC", [issue_sites, issue_titles], image_url_required=True, upper_limit=10)
        manhwa_books = fetch_books_as_dict(f"{base_query} AND novel_type='Manhwa' ORDER BY rating DESC", [issue_sites], image_url_required=True, upper_limit=10)
        light_novel_books = fetch_books_as_dict(f"{base_query} AND novel_type='Light Novel' ORDER BY rating DESC", [issue_sites], image_url_required=True, upper_limit=10)

        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Manga'")
        total_number_of_manga = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Manhua'")
        total_number_of_manhua = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Manhwa'")
        total_number_of_manhwa = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Light Novel'")
        total_number_of_light_novels = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT novel_source) FROM all_books")
        total_number_of_sources = cursor.fetchone()[0]

        return Response({
            "carousel_books": valid_carousel_books,
            "recently_updated_books": recently_updated_books,
            "manga_books": manga_books,
            "manhua_books": manhua_books,
            "manhwa_books": manhwa_books,
            "light_novel_books": light_novel_books,
            "numManga": total_number_of_manga,
            "numLightNovel": total_number_of_light_novels,
            "numManhwa": total_number_of_manhwa,
            "numManhua": total_number_of_manhua,
            "numSources": total_number_of_sources
        })

class AllNovelSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        genre = request.GET.get('genre', '')
        novel_source = request.GET.get('novel_source', 'All')

        conditions = []
        params = []

        if title_query:
            conditions.append("title ILIKE %s")
            params.append(f"%{title_query}%")
        if genre:
            conditions.append("genres ILIKE %s")
            params.append(f"%{genre}%")

        condition_str = " AND ".join(conditions) if conditions else "1=1"

        if novel_source in ['Light Novel Pub', 'AsuraScans']:
            condition_str += " AND novel_source = %s"
            params.append(novel_source)

        query = f"SELECT * FROM all_books WHERE {condition_str}"
        results = fetch_books_as_dict(query, params)

        return Response(results)

class AllNovelBrowseView(views.APIView):
    def get(self, request):
        try:
            # Replace all ' with ’
            title_query = request.GET.get('title', '').replace("'", "’")
            genres = request.GET.get('genre', '').split(',')
            sort_types = request.GET.get('sortType', '').split(',')
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))

            conditions = []
            params = []

            if title_query:
                conditions.append("ab.title ILIKE %s")
                params.append(f"%{title_query}%")
            
            genre_conditions = []
            if genres and any(genres):
                genre_conditions = [f"g.name = %s" for genre in genres if genre.strip()]
                if genre_conditions:
                    genre_subquery = f"""
                        SELECT abg.allbooks_title, abg.allbooks_novel_source
                        FROM all_books_genres abg
                        JOIN genre g ON abg.genre_id = g.id
                        WHERE {" OR ".join(genre_conditions)}
                        GROUP BY abg.allbooks_title, abg.allbooks_novel_source
                        HAVING COUNT(DISTINCT g.name) = {len(genre_conditions)}
                    """
                    conditions.append(f"(ab.title, ab.novel_source) IN ({genre_subquery})")
                    params.extend([genre.strip().lower() for genre in genres if genre.strip()])

            # Novel type conditions
            novel_type_conditions = []
            for sort_type in sort_types:
                if sort_type in ['manga', 'manhua', 'manhwa']:
                    novel_type_conditions.append("ab.novel_type = %s")
                    params.append(sort_type.capitalize())
                elif sort_type == 'light_novel':
                    novel_type_conditions.append("ab.novel_type = %s")
                    params.append("Light Novel")
        
            if novel_type_conditions:
                conditions.append(f"({' OR '.join(novel_type_conditions)})")

            condition_str = " AND ".join(conditions) if conditions else "1=1"

            # Sorting logic
            sort_mapping = {
                'rating': 'rating DESC NULLS LAST',  # Handle NULL values in sorting
                'updated': 'updated_on DESC NULLS LAST',
                'followers': 'followers DESC NULLS LAST',
            }

            order_by_clauses = []
            for sort_type in sort_types:
                if sort_type in sort_mapping:
                    order_by_clauses.append(sort_mapping[sort_type])
        
            order_by = ', '.join(order_by_clauses) if order_by_clauses else 'title'

            # Calculate offset for pagination
            offset = (page - 1) * page_size

            # Query to get the paginated results
            base_columns = ["ab.title", "ab.image_url", "ab.newest_chapter"]
            additional_columns = []
            if 'rating' in sort_types:
                additional_columns.append("ab.rating")
            if 'updated' in sort_types:
                additional_columns.append("ab.updated_on")
            if 'followers' in sort_types:
                additional_columns.append("ab.followers")

            select_columns = base_columns + additional_columns

            count_query = f"""
                SELECT COUNT(DISTINCT ab.title)
                FROM all_books ab
                LEFT JOIN all_books_genres abg ON ab.title = abg.allbooks_title AND ab.novel_source = abg.allbooks_novel_source
                LEFT JOIN genre g ON abg.genre_id = g.id
                WHERE {condition_str}
            """

            query = f"""
                WITH RankedBooks AS (
                    SELECT DISTINCT ON (ab.title) {', '.join(select_columns)}
                    FROM all_books ab
                    LEFT JOIN all_books_genres abg ON ab.title = abg.allbooks_title AND ab.novel_source = abg.allbooks_novel_source
                    LEFT JOIN genre g ON abg.genre_id = g.id
                    WHERE {condition_str}
                    ORDER BY ab.title, {order_by}
                )
                SELECT * FROM RankedBooks
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
            """
            
            params.extend([page_size, offset])

            total_count = fetch_count(count_query, params[:-2])
            browse_results = fetch_books_as_dict(query, params, paginated=True, validate=False)  # Note the paginated=True parameter

            response_data = {
                'page': page,
                'page_size': page_size,
                'results': browse_results,
                'total_count': total_count
            }

            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in AllNovelBrowseView: {str(e)}")
            return Response({
                "error": "An error occurred while fetching books",
                "detail": str(e)
            }, status=500)

@api_view(['POST'])
def register_view(request):
    data = request.data
    username = data.get('email')
    password = data.get('password')
    profileName = data.get('profileName')

    try:
        if User.objects.get(username=username):
            return Response({"error": "User already exists"}, status=status.HTTP_409_CONFLICT)
    except User.DoesNotExist:
        user = User.objects.create_user(username=username, email=username, password=password, first_name=profileName)
        payload = {
            'username': user.username,
            'profileName': user.first_name,
            'exp': datetime.now() + timedelta(days=2)
        }
        jwt_token = jwt.encode(payload, settings.JWT_TOKEN, algorithm='HS256')
        return Response({
            "message": "User created successfully",
            "token": jwt_token
        }, status=status.HTTP_201_CREATED)
    return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login_view(request):
    data = request.data
    username = data.get('email')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)

    if not user:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        with connection.cursor() as cursor:
            # Fetch profile
            cursor.execute("SELECT profile_image, dark_mode, email_notifications FROM profile WHERE user_id = %s", [user.id])
            profile_result = cursor.fetchone()
            if not profile_result:
                return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
            profile_image, dark_mode, email_notifications = profile_result

            payload = {
                'username': user.username,
                'profileName': user.first_name,
                'profileImage': profile_image,
                # 'profileImage': 'https://via.placeholder.com/400x600/CCCCCC/FFFFFF?text=No+Image',
                'darkMode': dark_mode,
                'emailNotifications': email_notifications,
                'exp': datetime.now() + timedelta(days=2)
            }
            jwt_token = jwt.encode(payload, settings.JWT_TOKEN, algorithm='HS256')
            return Response({
                "message": "Login successful",
                "token": jwt_token,
                # TODO: PAUSE. This could be a huge security vulnerability!!
                "secret": os.getenv('EXTENSION_SECRET_KEY')
            }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@csrf_exempt
@api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([SessionAuthentication, TokenAuthentication])
def update_reading_list(request):
    data = request.data
    email = data.get('username')

    try:
        with connection.cursor() as cursor:
            # Fetch user
            cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
            user_result = cursor.fetchone()
            if not user_result:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            user_id = user_result[0]

            # Fetch profile
            cursor.execute("SELECT id FROM profile WHERE user_id = %s", [user_id])
            profile_result = cursor.fetchone()
            if not profile_result:
                return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
            profile_id = profile_result[0]

            # Fetch book details
            cursor.execute("""
                SELECT title, novel_source
                FROM all_books
                WHERE title = %s AND novel_source = %s
            """, [data.get('title'), data.get('novel_source')])
            book_result = cursor.fetchone()
            if not book_result:
                return Response({'error': 'Book not found in AllBooks'}, status=status.HTTP_404_NOT_FOUND)
            title, novel_source = book_result

            # Check if the book is already in the reading list
            cursor.execute("""
                SELECT id
                FROM reading_list
                WHERE profile_id = %s AND book_title = %s AND book_novel_source = %s
            """, [profile_id, title, novel_source])
            existing_book_result = cursor.fetchone()

            if existing_book_result:
                # Update the existing book
                reading_list_id = existing_book_result[0]
                cursor.execute("""
                    UPDATE reading_list
                    SET reading_status = %s, user_tag = %s, latest_read_chapter = %s
                    WHERE id = %s
                """, [data.get('reading_status'), data.get('user_tag'), data.get('latest_read_chapter'), reading_list_id])
                return Response({"message": "Book updated in reading list successfully"}, status=status.HTTP_200_OK)
            else:
                # Add the new book to the reading list
                cursor.execute("""
                    INSERT INTO reading_list (profile_id, reading_status, user_tag, latest_read_chapter, book_title, book_novel_source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [profile_id, data.get('reading_status'), data.get('user_tag'), data.get('latest_read_chapter'), title, novel_source])
                return Response({"message": "Book added to reading list successfully"}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileReadingListView(views.APIView):
    def get(self, request, email):
        try:
            with connection.cursor() as cursor:
                # Fetch user
                cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
                user_result = cursor.fetchone()
                
                if not user_result:
                    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
                
                user_id = user_result[0]

                # Fetch reading list
                cursor.execute("""
                    SELECT rl.id, rl.reading_status, rl.user_tag, rl.latest_read_chapter, 
                           ab.title AS book_title, ab.novel_source, ab.novel_type, ab.newest_chapter, 
                           ab.chapters->>rl.latest_read_chapter AS latest_read_chapter_link, 
                           ab.chapters AS chapters_json
                    FROM reading_list rl
                    JOIN all_books ab ON rl.book_title = ab.title AND rl.book_novel_source = ab.novel_source
                    WHERE rl.profile_id = (
                        SELECT id FROM profile WHERE user_id = %s
                    )
                """, [user_id])
                reading_list_results = cursor.fetchall()

                # Prepare the reading list response
                reading_list = []
                for row in reading_list_results:
                    chapters_json = row[9]

                    if isinstance(chapters_json, str):
                        try:
                            chapters_json = chapters_json.replace('\\"', '"')
                            chapters_dict = json.loads(chapters_json)
                        except json.JSONDecodeError:
                            chapters_dict = {}
                    else:
                        chapters_dict = chapters_json

                    newest_chapter_link = get_newest_chapter_link(chapters_dict)
                    
                    reading_list.append({
                        'id': row[0],
                        'reading_status': row[1],
                        'user_tag': row[2],
                        'latest_read_chapter': row[3],
                        'title': row[4],
                        'novel_source': row[5],
                        'novel_type': row[6],
                        'newest_chapter': row[7],
                        'latest_read_chapter_link': row[8],
                        'newest_chapter_link': newest_chapter_link
                    })

            response = Response({'reading_list': reading_list})
            # TODO: Handle CORS better. 
            # Currently I am allowing all origins, which must be changed before deploying
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept"

            return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['DELETE'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([SessionAuthentication, TokenAuthentication])
def delete_book_from_reading_list(request):
    data = request.data
    email = data.get('username')
    title_to_delete = data.get('title')
    source = data.get('novel_source')

    try:
        with connection.cursor() as cursor:
            # Fetch user
            cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
            user_result = cursor.fetchone()
            if not user_result:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            user_id = user_result[0]

            # Fetch profile
            cursor.execute("SELECT id FROM profile WHERE user_id = %s", [user_id])
            profile_result = cursor.fetchone()
            if not profile_result:
                return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
            profile_id = profile_result[0]

            # Delete the book from the reading list
            cursor.execute("""
                DELETE FROM reading_list
                WHERE profile_id = %s AND book_title = %s AND book_novel_source = %s
            """, [profile_id, title_to_delete, source])

            return Response({"message": "Book removed from reading list successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([SessionAuthentication, TokenAuthentication])
def update_to_max_chapter(request):
    print(f"CSRF Token from request: {request.META.get('HTTP_X_CSRFTOKEN')}")
    data = request.data
    email = data.get('username')
    title = data.get('title')
    novel_source = data.get('novel_source')

    try:
        with connection.cursor() as cursor:
            # Fetch user
            cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
            user_result = cursor.fetchone()
            if not user_result:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            user_id = user_result[0]

            # Fetch profile
            cursor.execute("SELECT id FROM profile WHERE user_id = %s", [user_id])
            profile_result = cursor.fetchone()
            if not profile_result:
                return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
            profile_id = profile_result[0]

            # Fetch book details
            cursor.execute("""
                SELECT chapters, novel_source
                FROM all_books
                WHERE title = %s AND novel_source = %s
            """, [title, novel_source])
            result = cursor.fetchone()
            if not result:
                return Response({'error': 'Book not found in AllBooks'}, status=status.HTTP_404_NOT_FOUND)
            chapters, novel_source = result
            chapters = json.loads(chapters)

            # Define chapter_key function to find latest chapter 
            # TODO: might switch to using something similar to get_newest_chapter_link
            def chapter_key(chapter_str):
                numbers = re.findall(r"\d+\.\d+|\d+", chapter_str)
                return [float(num) for num in numbers]
            
            latest_chapter = max(chapters.keys(), key=chapter_key) if chapters else None

            if latest_chapter:
                # Update the latest read chapter in the reading list
                cursor.execute("""
                    UPDATE reading_list
                    SET latest_read_chapter = %s
                    WHERE profile_id = %s AND book_title = %s AND book_novel_source = %s
                """, [latest_chapter, profile_id, title, novel_source])

                return Response({"message": "Updated to latest chapter successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No chapters found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BookDetailsView(views.APIView):
    def get(self, request, title):
        try:
            with connection.cursor() as cursor:
                # Fetch books with the given title
                cursor.execute("""
                    SELECT ab.*, 
                           ARRAY_AGG(g.name) AS genres
                    FROM all_books ab
                    LEFT JOIN all_books_genres abg ON ab.title = abg.allbooks_title AND ab.novel_source = abg.allbooks_novel_source
                    LEFT JOIN genre g ON abg.genre_id = g.id
                    WHERE ab.title = %s
                    GROUP BY ab.title, ab.novel_source, ab.synopsis, ab.author, ab.updated_on, ab.newest_chapter, ab.image_url, ab.rating, ab.status, ab.novel_type, ab.followers, ab.chapters
                    ORDER BY ab.novel_type
                """, [title])
                books = cursor.fetchall()
                if not books:
                    return Response({'message': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

                # Fetch column names to construct the dictionary
                columns = [col[0] for col in cursor.description]
                books_dict = {}
                for book in books:
                    book_dict = dict(zip(columns, book))
                    # print(f"Debug: book_dict['chapters']: {book_dict['chapters']}")  # Debug statement

                    # TODO: Send chapters as a sorted dictionary
                    # if book_dict['chapters']:
                    #     book_dict['chapters'] = parse_and_sort_chapters(book_dict['chapters'])

                    novel_type = book_dict['novel_type']
                    if novel_type not in books_dict:
                        books_dict[novel_type] = []
                    books_dict[novel_type].append(book_dict)

            return Response(books_dict)
        except Exception as e:
            print(f"Debug: Exception: {e}")  # Debug statement
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AllNovelGetGenres(views.APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM genre WHERE name IS NOT NULL AND name != ''")
                genres = [row[0] for row in cursor.fetchall()]
            return Response(genres)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@require_http_methods(["OPTIONS", "POST"])
@api_view(['POST'])
def update_reading(request):
    if request.method == 'OPTIONS':
        response = JsonResponse({'status': 'ok'})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-User-Email"
        return response

    try:
        data = json.loads(request.body)
        book_title = data.get('bookTitle')
        chapter = data.get('chapter')
        novel_source = data.get('novel_source')
        user_email = request.headers.get('X-User-Email')
        token = request.headers.get('Authorization').split()[1]  # Assuming Bearer token

        if not user_email or not token:
            return JsonResponse({'status': 'failure', 'error': 'User email or token not provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify token
        try:
            decoded = jwt.decode(token, settings.JWT_TOKEN, algorithms=['HS256'])
            if decoded['username'] != user_email:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return JsonResponse({'status': 'failure', 'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return JsonResponse({'status': 'failure', 'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        with connection.cursor() as cursor:
            # Fetch user by email
            cursor.execute("SELECT id FROM auth_user WHERE email = %s", [user_email])
            user_result = cursor.fetchone()
            if not user_result:
                return JsonResponse({'status': 'failure', 'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            user_id = user_result[0]

            # Fetch profile by user_id
            cursor.execute("SELECT id FROM profile WHERE user_id = %s", [user_id])
            profile_result = cursor.fetchone()
            if not profile_result:
                return JsonResponse({'status': 'failure', 'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
            profile_id = profile_result[0]

            # Check if the book is already in the reading list
            cursor.execute("""
                SELECT id FROM reading_list
                WHERE profile_id = %s AND book_title = %s AND book_novel_source = %s
            """, [profile_id, book_title, novel_source])
            existing_book_result = cursor.fetchone()

            if existing_book_result:
                print(f'Updating the latest read chapter for book id {existing_book_result[0]} for user {profile_id} to {chapter}')
                # Update the existing book
                cursor.execute("""
                    UPDATE reading_list
                    SET latest_read_chapter = %s
                    WHERE id = %s
                """, [chapter, existing_book_result[0]])
            else:
                print(f'Adding book {book_title} from {novel_source} at chapter {chapter} to reading list for user {user_email}')
                # Add the new book to the reading list
                cursor.execute("""
                    INSERT INTO reading_list (profile_id, book_title, book_novel_source, latest_read_chapter, reading_status, user_tag)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [profile_id, book_title, novel_source, chapter, "Reading", ""])

        response = JsonResponse({'status': 'success'})
        response["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        response = JsonResponse({'status': 'failure', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        response["Access-Control-Allow-Origin"] = "*"
        return response

@csrf_exempt
@api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([SessionAuthentication, TokenAuthentication])
def update_user_profile(request):
    print("Updating user profile")
    user = request.user
    data = request.data

    cursor = connection.cursor()

    # Fetch the current profile image
    profile_image_url = ""
    cursor.execute("SELECT profile_image FROM profile WHERE user_id = %s", [user.id])
    current_profile_image = cursor.fetchone()
    if current_profile_image:
        profile_image_url = current_profile_image[0]

    # Update email
    if 'email' in data:
        user.email = data['email']
        user.username = data['email']  # Assuming username is same as email
        user.save()

    # Update password
    if 'password' in data:
        user.set_password(data['password'])
        user.save()

    # Update profileName
    profile_name = data.get('profileName')
    if profile_name:
        cursor.execute("UPDATE profile SET profile_name = %s WHERE user_id = %s", [profile_name, user.id])

    # Update profileImage
    if 'profileImage' in request.FILES:
        profile_image_file = request.FILES['profileImage']
        upload_result = cloudinary.uploader.upload(profile_image_file)
        profile_image_url = upload_result.get('url')
        cursor.execute("UPDATE profile SET profile_image = %s WHERE user_id = %s", [profile_image_url, user.id])

    return Response({"message": "Profile updated successfully", "profileImage": profile_image_url}, status=status.HTTP_200_OK)

def csrf_failure(request, reason=""):
    print("Hello")
    return JsonResponse({'error': 'CSRF token missing or incorrect'}, status=403)