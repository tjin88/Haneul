import re
from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connection
from django.views.decorators.http import require_http_methods

def fetch_books_as_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def fetch_count(query):
    cursor = connection.cursor()
    cursor.execute(query)
    count = cursor.fetchone()[0]
    return count

class HomeNovelGetView(views.APIView):
    def get(self, request):
        carousel_titles = ("Reaper of the Drifting Moon", "Solo Leveling", "The Strongest Player",
                           "Swordmaster’s Youngest Son", "Damn Reincarnation", "My Daughter is the Final Boss",
                           "Talent-Swallowing Magician", "Revenge of the Iron-Blooded Sword Hound", "Villain To Kill",
                           "The Novel’s Extra (Remake)", "Chronicles Of The Martial God’s Return", "Academy’s Undercover Professor",
                           "Everyone Else is A Returnee", "Heavenly Inquisition Sword", "Solo Bug Player",
                           "Nano Machine", "Chronicles of the Demon Faction", "Academy’s Genius Swordmaster",
                           "Shadow Slave", "Reverend Insanity", "Super Gene (Web Novel)", "Martial World (Web Novel)")
        
        carousel_books = fetch_books_as_dict(f"SELECT title, image_url, newest_chapter FROM all_books WHERE title IN {carousel_titles}")
        recently_updated_books = fetch_books_as_dict("SELECT title, image_url, newest_chapter, rating FROM all_books ORDER BY updated_on DESC LIMIT 10")
        manga_books = fetch_books_as_dict("SELECT title, image_url, newest_chapter, rating FROM all_books WHERE novel_type='Manga' ORDER BY rating DESC LIMIT 10")
        manhua_books = fetch_books_as_dict("SELECT title, image_url, newest_chapter, rating FROM all_books WHERE novel_type='Manhua' ORDER BY rating DESC LIMIT 10")
        manhwa_books = fetch_books_as_dict("SELECT title, image_url, newest_chapter, rating FROM all_books WHERE novel_type='Manhwa' ORDER BY rating DESC LIMIT 10")
        light_novel_books = fetch_books_as_dict("SELECT title, image_url, newest_chapter, rating FROM all_books WHERE novel_type='Light Novel' ORDER BY rating DESC LIMIT 10")

        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Manga'")
        total_number_of_manga = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Manhua'")
        total_number_of_manhua = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Manhwa'")
        total_number_of_manhwa = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM all_books WHERE novel_type='Light Novel'")
        total_number_of_light_novels = cursor.fetchone()[0]

        return Response({
            "carousel_books": carousel_books,
            "recently_updated_books": recently_updated_books,
            "manga_books": manga_books,
            "manhua_books": manhua_books,
            "manhwa_books": manhwa_books,
            "light_novel_books": light_novel_books,
            "numManga": total_number_of_manga,
            "numLightNovel": total_number_of_light_novels,
            "numManhwa": total_number_of_manhwa,
            "numManhua": total_number_of_manhua
        })

class AllNovelSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        genre = request.GET.get('genre', '')
        novel_source = request.GET.get('novel_source', 'All')

        conditions = []
        if title_query:
            conditions.append(f"title ILIKE '%{title_query}%'")
        if genre:
            conditions.append(f"genres ILIKE '%{genre}%'")

        condition_str = " AND ".join(conditions) if conditions else "1=1"

        results = []

        if novel_source in ['Light Novel Pub', 'AsuraScans']:
            results = fetch_books_as_dict(f"SELECT * FROM all_books WHERE {condition_str} AND novel_source='{novel_source}'")
        else:
            results = fetch_books_as_dict(f"SELECT * FROM all_books WHERE {condition_str}")

        return Response(results)

class AllNovelBrowseView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        genres = request.GET.get('genre', '').split(',')
        sort_types = request.GET.get('sortType', '').split(',')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))

        conditions = []
        if title_query:
            conditions.append(f"ab.title ILIKE '%{title_query}%'")
        
        genre_conditions = []
        if genres and any(genres):
            genre_conditions = [f"g.name = '{genre.strip().lower()}'" for genre in genres if genre.strip()]
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

        # Novel type conditions
        novel_type_conditions = []
        for sort_type in sort_types:
            if sort_type in ['manga', 'manhua', 'manhwa']:
                novel_type_conditions.append(f"ab.novel_type = '{sort_type.capitalize()}'")
            elif sort_type == 'light_novel':
                novel_type_conditions.append("ab.novel_type = 'Light Novel'")
    
        if novel_type_conditions:
            conditions.append(f"({' OR '.join(novel_type_conditions)})")

        condition_str = " AND ".join(conditions) if conditions else "1=1"

        # Sorting logic
        sort_mapping = {
            'rating': 'rating DESC',
            'updated': 'updated_on DESC',
            'followers': 'followers DESC',
        }

        order_by_clauses = []
        for sort_type in sort_types:
            if sort_type in sort_mapping:
                order_by_clauses.append(sort_mapping[sort_type])
    
        order_by = ', '.join(order_by_clauses) if order_by_clauses else ''

        # Calculate offset for pagination
        offset = (page - 1) * page_size

        # Query to get the paginated results
        base_columns = ["title", "image_url", "newest_chapter"]
        additional_columns = []
        if 'rating' in sort_types:
            additional_columns.append("rating")
        if 'updated' in sort_types:
            additional_columns.append("updated_on")
        if 'followers' in sort_types:
            additional_columns.append("followers")

        select_columns = base_columns + additional_columns

        query = f"""
            SELECT {', '.join(select_columns)}
            FROM (
                SELECT ab.title, ab.image_url, ab.newest_chapter
                       {', ' + ', '.join(additional_columns) if additional_columns else ''}, 
                       ROW_NUMBER() OVER (PARTITION BY ab.title ORDER BY {order_by if order_by else 'ab.title'}) as row_num
                FROM all_books ab
                LEFT JOIN all_books_genres abg ON ab.title = abg.allbooks_title AND ab.novel_source = abg.allbooks_novel_source
                LEFT JOIN genre g ON abg.genre_id = g.id
                WHERE {condition_str}
            ) subquery
            WHERE row_num = 1
            ORDER BY {order_by if order_by else 'title'}
            LIMIT {page_size} OFFSET {offset}
        """
        browse_results = fetch_books_as_dict(query)

        response_data = {
            'page': page,
            'page_size': page_size,
            'results': browse_results
        }

        return Response(response_data)

@method_decorator(csrf_exempt, name='dispatch')
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
            'exp': datetime.utcnow() + timedelta(days=2)
        }
        jwt_token = jwt.encode(payload, settings.JWT_TOKEN, algorithm='HS256')
        return Response({
            "message": "User created successfully",
            "token": jwt_token
        }, status=status.HTTP_201_CREATED)
    return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def login_view(request):
    data = request.data
    username = data.get('email')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        payload = {
            'username': user.username,
            'profileName': user.first_name,
            'exp': datetime.utcnow() + timedelta(days=2)
        }
        jwt_token = jwt.encode(payload, settings.JWT_TOKEN, algorithm='HS256')
        return Response({
            "message": "Login successful",
            "token": jwt_token
        }, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['PUT'])
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

            # TODO: Get user authentication to work
            # if not user or user.is_anonymous:
            #     return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

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
    # TODO: Add tokens for user authentication
    # permission_classes = [IsAuthenticated]

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
                            chapters_json = chapters_json.replace('\\"', '"')  # Remove extra escape characters if necessary
                            chapters_dict = json.loads(chapters_json)
                        except json.JSONDecodeError:
                            chapters_dict = {}
                    else:
                        chapters_dict = chapters_json

                    newest_chapter_link = self.get_newest_chapter_link(chapters_dict)
                    
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

            print(response)
            return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_newest_chapter_link(self, chapters):
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

# class UserProfileReadingListView(views.APIView):
#     # TODO: Add tokens for user authentication
#     # permission_classes = [IsAuthenticated]

#     def get(self, request, email):
#         try:
#             with connection.cursor() as cursor:
#                 # Fetch user
#                 cursor.execute("SELECT id FROM auth_user WHERE email = %s", [email])
#                 user_result = cursor.fetchone()
                
#                 if not user_result:
#                     return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
                
#                 user_id = user_result[0]

#                 # Fetch reading list
#                 cursor.execute("""
#                     SELECT rl.id, rl.reading_status, rl.user_tag, rl.latest_read_chapter, 
#                            ab.title AS book_title, ab.novel_source, ab.novel_type, ab.newest_chapter, 
#                            ab.chapters->>rl.latest_read_chapter AS latest_read_chapter_link, 
#                            ab.chapters->>ab.newest_chapter AS newest_chapter_link
#                     FROM reading_list rl
#                     JOIN all_books ab ON rl.book_title = ab.title AND rl.book_novel_source = ab.novel_source
#                     WHERE rl.profile_id = (
#                         SELECT id FROM profile WHERE user_id = %s
#                     )
#                 """, [user_id])
#                 reading_list_results = cursor.fetchall()

#                 # Prepare the reading list response
#                 reading_list = []
#                 for row in reading_list_results:
#                     reading_list.append({
#                         'id': row[0],
#                         'reading_status': row[1],
#                         'user_tag': row[2],
#                         'latest_read_chapter': row[3],
#                         'title': row[4],
#                         'novel_source': row[5],
#                         'novel_type': row[6],
#                         'newest_chapter': row[7],
#                         'latest_read_chapter_link': row[8],
#                         'newest_chapter_link': row[9]
#                     })

#             response = Response({'reading_list': reading_list})
#             # TODO: Handle CORS better. 
#             # Currently I am allowing all origins, which must be cha
#             # \nged before deploying
#             response["Access-Control-Allow-Origin"] = "*"
#             response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
#             response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept"
#             return response

#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
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

@api_view(['PUT'])
def update_to_max_chapter(request):
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

            # Since we using SQL queries, I can't use my built-in get_latest_chapter function. 
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
                cursor.execute("SELECT * FROM all_books WHERE title = %s", [title])
                book = cursor.fetchone()
                if not book:
                    return Response({'message': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

                # Fetch column names to construct the dictionary
                columns = [col[0] for col in cursor.description]
                book_dict = dict(zip(columns, book))

            return Response(book_dict)
        except Exception as e:
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

@csrf_exempt
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
        print(f'user_email: {user_email}, token: {token}, book_title: {book_title}, chapter: {chapter}, novel_source: {novel_source}')

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

        print(f'Valid token for user: {user_email}')

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
                print(f'Existing book found. reading_list ID: {existing_book_result[0]}')
                print(f'Updating the latest read chapter for book id {existing_book_result[0]} to {chapter}')
                # Update the existing book
                cursor.execute("""
                    UPDATE reading_list
                    SET latest_read_chapter = %s
                    WHERE id = %s
                """, [chapter, existing_book_result[0]])
            else:
                print('New book. Adding to reading list')
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
