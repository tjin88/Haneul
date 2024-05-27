from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from .models import Profile
# from .serializers import AsuraScansSerializer, LightNovelPubSerializer, HomeNovelSerializer, BrowseNovelSerializer
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

def fetch_books_as_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results

class HomeNovelGetView(views.APIView):
    def get(self, request):
        carousel_titles = ("Reaper of the Drifting Moon", "Solo Leveling", "The Strongest Player",
                           "Swordmaster’s Youngest Son", "Damn Reincarnation", "My Daughter is the Final Boss",
                           "Talent-Swallowing Magician", "Revenge of the Iron-Blooded Sword Hound", "Villain To Kill",
                           "The Novel’s Extra (Remake)", "Chronicles Of The Martial God’s Return", "Academy’s Undercover Professor",
                           "Everyone Else is A Returnee", "Heavenly Inquisition Sword", "Solo Bug Player",
                           "Nano Machine", "Chronicles of the Demon Faction", "Academy’s Genius Swordmaster",
                           "Shadow Slave", "Reverend Insanity", "Super Gene (Web Novel)", "Martial World (Web Novel)")
        
        carousel_books = fetch_books_as_dict(f"SELECT * FROM all_books WHERE title IN {carousel_titles}")
        recently_updated_books = fetch_books_as_dict("SELECT * FROM all_books ORDER BY updated_on DESC LIMIT 10")
        manga_books = fetch_books_as_dict("SELECT * FROM all_books WHERE novel_type='Manga' ORDER BY rating DESC LIMIT 10")
        manhua_books = fetch_books_as_dict("SELECT * FROM all_books WHERE novel_type='Manhua' ORDER BY rating DESC LIMIT 10")
        manhwa_books = fetch_books_as_dict("SELECT * FROM all_books WHERE novel_type='Manhwa' ORDER BY rating DESC LIMIT 10")
        light_novel_books = fetch_books_as_dict("SELECT * FROM all_books WHERE novel_type='Light Novel' ORDER BY rating DESC LIMIT 10")

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

class AllNovelGetView(views.APIView):
    def get(self, request):
        all_books = fetch_books_as_dict("SELECT * FROM all_books")
        return Response(all_books)

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

        asura_results = []
        lightnovel_results = []
        
        if novel_source in ['All', 'AsuraScans', 'Manga']:
            asura_results = fetch_books_as_dict(f"SELECT * FROM all_books WHERE {condition_str}")
        
        if novel_source in ['All', 'Light Novel Pub', 'Light Novel']:
            lightnovel_results = fetch_books_as_dict(f"SELECT * FROM all_books WHERE {condition_str}")

        serializer_data = asura_results + lightnovel_results
        return Response(serializer_data)
    
class AllNovelBrowseView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        genre = request.GET.get('genre', '')
        novel_source = request.GET.get('novel_source', '')

        conditions = []
        if title_query:
            conditions.append(f"title ILIKE '%{title_query}%'")
        if genre:
            conditions.append(f"genres ILIKE '%{genre}%'")
        if novel_source:
            conditions.append(f"novel_source='{novel_source}'")

        condition_str = " AND ".join(conditions) if conditions else "1=1"
        browse_results = fetch_books_as_dict(f"SELECT * FROM all_books WHERE {condition_str}")
        return Response(browse_results)

class AsuraScansCreateView(views.APIView):
    def post(self, request):
        data = request.data
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO all_books (title, novel_source, synopsis, author, updated_on, newest_chapter, image_url, rating, status, novel_type, followers, chapters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            'AsuraScans',
            data['synopsis'],
            data.get('author'),
            datetime.now(),
            data['newest_chapter'],
            data['image_url'],
            data['rating'],
            data['status'],
            data['novel_type'],
            data['followers'],
            json.dumps(data['chapters'])
        ))
        connection.commit()
        return Response(data, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        mangas = fetch_books_as_dict("SELECT * FROM all_books WHERE novel_source='AsuraScans'")
        return Response(mangas)

class AsuraScansUpdateView(views.APIView):
    def put(self, request, title):
        data = request.data
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE all_books SET
            synopsis = %s,
            author = %s,
            updated_on = %s,
            newest_chapter = %s,
            image_url = %s,
            rating = %s,
            status = %s,
            novel_type = %s,
            followers = %s,
            chapters = %s
            WHERE title = %s AND novel_source = 'AsuraScans'
        """, (
            data['synopsis'],
            data.get('author'),
            datetime.now(),
            data['newest_chapter'],
            data['image_url'],
            data['rating'],
            data['status'],
            data['novel_type'],
            data['followers'],
            json.dumps(data['chapters']),
            title
        ))
        connection.commit()
        return Response(data)

class AsuraScansSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        mangas = fetch_books_as_dict(f"SELECT * FROM all_books WHERE title ILIKE '%{title_query}%' AND novel_source='AsuraScans'")
        return Response(mangas)

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

    # TODO: Get user authentication to work
    # if not user or user.is_anonymous:
    #     return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    # TODO: Make 'latest_read_chapter' hold the chapter (key), and have the VALUE be the URL to that chapter.
    # This way, when there are any issues re: website URL changes, the dashboard won't forward you to a faulty link,
    # Since the URLs will be updated in the database from each scrape.
    try:
        user = User.objects.get(email=email)
        profile = Profile.objects.get(user=user)

        curr_book = {
            'title': data.get('title'),
            'reading_status': data.get('reading_status'),
            'user_tag': data.get('user_tag'),
            'latest_read_chapter': data.get('latest_read_chapter'),
            'chapter_link': data.get('chapter_link'),
            'novel_type': data.get('novel_type'),
            'novel_source': data.get('novel_source'),
        }

        # If the book is already in the reading list, update it
        for book in profile.reading_list:
            if book['title'] == curr_book['title'] and book['novel_source'] == curr_book['novel_source']:
                book.update(curr_book)
                profile.save()
                return Response({"message": "Book updated in reading list successfully"}, status=status.HTTP_200_OK)

        # As the book is not already in the reading list, add it
        profile.reading_list.append(curr_book)
        profile.save()

        return Response({"message": "Book added to reading list successfully"})
    except Profile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


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

                # Fetch profile
                cursor.execute("SELECT reading_list FROM profile WHERE user_id = %s", [user_id])
                profile_result = cursor.fetchone()

                if not profile_result:
                    return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

                # Parse the reading_list JSON string
                reading_list = json.loads(profile_result[0])

            response = Response({'reading_list': reading_list})
            # TODO: Handle CORS better. 
            # Currently I am allowing all origins, which must be changed before deploying
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept"
            return response

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_book_from_reading_list(request):
    data = request.data
    email = data.get('username')
    title_to_delete = data.get('title')
    source = data.get('novel_source')

    try:
        user = User.objects.get(email=email)
        profile = Profile.objects.get(user=user)

        profile.reading_list = [book for book in profile.reading_list if book['title'] != title_to_delete or (book['title'] == title_to_delete and book['novel_source'] != source)]
        profile.save()

        return Response({"message": "Book removed from reading list successfully"}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Profile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
def update_to_max_chapter(request):
    data = request.data
    email = data.get('username')
    title = data.get('title')
    novel_source = data.get('novel_source')

    try:
        user = User.objects.get(email=email)
        profile = Profile.objects.get(user=user)

        cursor = connection.cursor()
        cursor.execute("""
            SELECT chapters
            FROM all_books
            WHERE title = %s AND novel_source = %s
        """, [title, novel_source])
        result = cursor.fetchone()

        if result:
            chapters = json.loads(result[0])
            if novel_source == 'AsuraScans':
                latest_chapter = next(iter(chapters), None) if chapters else None
            else:
                def chapter_key(chapter_str):
                    numbers = re.findall(r"\d+\.\d+|\d+", chapter_str)
                    return [float(num) for num in numbers]

                latest_chapter = max(chapters.keys(), key=chapter_key) if chapters else None
                chapter_link = chapters.get(latest_chapter, None)

            for book in profile.reading_list:
                if book['title'] == title and book['novel_source'] == novel_source:
                    book['latest_read_chapter'] = latest_chapter
                    book['chapter_link'] = chapter_link
                    break

            profile.save()
            return Response({"message": "Updated to latest chapter successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "AllBooks not found"}, status=status.HTTP_404_NOT_FOUND)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Profile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LightNovelPubCreateView(views.APIView):
    def post(self, request):
        data = request.data
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO all_books (title, novel_source, synopsis, author, updated_on, newest_chapter, image_url, rating, status, novel_type, followers, chapters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['title'],
            'Light Novel Pub',
            data['synopsis'],
            data.get('author'),
            datetime.now(),
            data['newest_chapter'],
            data['image_url'],
            data['rating'],
            data['status'],
            data['novel_type'],
            data['followers'],
            json.dumps(data['chapters'])
        ))
        connection.commit()
        return Response(data, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        lightNovels = fetch_books_as_dict("SELECT * FROM all_books WHERE novel_source='Light Novel Pub'")
        return Response(lightNovels)

class LightNovelPubUpdateView(views.APIView):
    def put(self, request, title):
        data = request.data
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE all_books SET
            synopsis = %s,
            author = %s,
            updated_on = %s,
            newest_chapter = %s,
            image_url = %s,
            rating = %s,
            status = %s,
            novel_type = %s,
            followers = %s,
            chapters = %s
            WHERE title = %s AND novel_source = 'Light Novel Pub'
        """, (
            data['synopsis'],
            data.get('author'),
            datetime.now(),
            data['newest_chapter'],
            data['image_url'],
            data['rating'],
            data['status'],
            data['novel_type'],
            data['followers'],
            json.dumps(data['chapters']),
            title
        ))
        connection.commit()
        return Response(data)

class LightNovelPubSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        lightNovels = fetch_books_as_dict(f"SELECT * FROM all_books WHERE title ILIKE '%{title_query}%' AND novel_source='Light Novel Pub'")
        return Response(lightNovels)

class BookDetailsView(views.APIView):
    def get(self, request, title):
        book = fetch_books_as_dict(f"SELECT * FROM all_books WHERE title = '{title}'")
        if not book:
            return Response({'message': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(book[0])
