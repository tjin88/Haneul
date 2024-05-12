from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from .models import AllBooks, Profile
from .serializers import AsuraScansSerializer, LightNovelPubSerializer, HomeNovelSerializer, BrowseNovelSerializer
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
from django.db.models import Q

class HomeNovelGetView(views.APIView):
    def get(self, request):
        carousel_titles = {"Reaper of the Drifting Moon", "Solo Leveling", "The Strongest Player",
        "Swordmaster’s Youngest Son", "Damn Reincarnation", "My Daughter is the Final Boss",
        "Talent-Swallowing Magician", "Revenge of the Iron-Blooded Sword Hound", "Villain To Kill",
        "The Novel’s Extra (Remake)", "Chronicles Of The Martial God’s Return", "Academy’s Undercover Professor",
        "Everyone Else is A Returnee", "Heavenly Inquisition Sword", "Solo Bug Player",
        "Nano Machine", "Chronicles of the Demon Faction", "Academy’s Genius Swordmaster",
        "Shadow Slave", "Reverend Insanity", "Super Gene (Web Novel)", "Martial World (Web Novel)"}
        
        carousel_books = AllBooks.objects.filter(title__in=carousel_titles)
        recently_updated_books = AllBooks.objects.order_by('-updated_on')[:10]
        manga_books = AllBooks.objects.filter(novel_type="Manga").order_by('-rating')[:10]
        manhua_books = AllBooks.objects.filter(novel_type="Manhua").order_by('-rating')[:10]
        manhwa_books = AllBooks.objects.filter(novel_type="Manhwa").order_by('-rating')[:10]
        light_novel_books = AllBooks.objects.filter(novel_type="Light Novel").order_by('-rating')[:10]

        total_number_of_manga = AllBooks.objects.filter(novel_type="Manga").count()
        total_number_of_manhua = AllBooks.objects.filter(novel_type="Manhua").count()
        total_number_of_manhwa = AllBooks.objects.filter(novel_type="Manhwa").count()
        total_number_of_light_novels = AllBooks.objects.filter(novel_type="Light Novel").count()

        return Response({
            "carousel_books": HomeNovelSerializer(carousel_books, many=True).data,
            "recently_updated_books": HomeNovelSerializer(recently_updated_books, many=True).data,
            "manga_books": HomeNovelSerializer(manga_books, many=True).data,
            "manhua_books": HomeNovelSerializer(manhua_books, many=True).data,
            "manhwa_books": HomeNovelSerializer(manhwa_books, many=True).data,
            "light_novel_books": HomeNovelSerializer(light_novel_books, many=True).data,
            "numManga": total_number_of_manga,
            "numLightNovel": total_number_of_light_novels,
            "numManhwa": total_number_of_manhwa,
            "numManhua": total_number_of_manhua
        })

class AllNovelGetView(views.APIView):
    def get(self, request):
        allBooks = AllBooks.objects.all()
        allBookSerializer = AsuraScansSerializer(allBooks, many=True)

        return Response(allBookSerializer.data)

class AllNovelSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        genre = request.GET.get('genre', '')
        novel_source = request.GET.get('novel_source', 'All')

        conditions = Q()
        if title_query:
            conditions &= Q(title__icontains=title_query)
        if genre:
            conditions &= Q(genres__icontains=genre)
        
        serializer_data = []
        
        # TODO: Combine this into one. Atm frontend not even sending novel_source ... (from Browse)
        if novel_source in ['All', 'AsuraScans', 'Manga']:
            asura_results = AllBooks.objects.filter(conditions)
            asura_serializer = AsuraScansSerializer(asura_results, many=True)
            serializer_data += asura_serializer.data
        
        if novel_source in ['All', 'Light Novel Pub', 'Light Novel']:
            lightnovel_results = AllBooks.objects.filter(conditions)
            lightnovel_serializer = LightNovelPubSerializer(lightnovel_results, many=True)
            serializer_data += lightnovel_serializer.data

        return Response(serializer_data)
    
class AllNovelBrowseView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        genre = request.GET.get('genre', '')
        # sort_type = request.GET.get('sortType', '')
        novel_source = request.GET.get('novel_source', '')

        conditions = Q()
        if title_query:
            conditions &= Q(title__icontains=title_query)
        if genre:
            conditions &= Q(genres__icontains=genre)
        if novel_source:
            conditions &= Q(novel_source=novel_source)

        # browse_results = AllBooks.objects.filter(conditions).order_by(f'-{sort_type}')
        browse_results = AllBooks.objects.filter(conditions)
        browse_serializer = BrowseNovelSerializer(browse_results, many=True)

        return Response(browse_serializer.data)

class AsuraScansCreateView(views.APIView):
    def post(self, request):
        serializer = AsuraScansSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        mangas = AllBooks.objects.filter(novel_source='AsuraScans').all()
        serializer = AsuraScansSerializer(mangas, many=True)
        return Response(serializer.data)

class AsuraScansUpdateView(views.APIView):
    def put(self, request, title):
        try:
            manga = AllBooks.objects.get(title=title, novel_source='AsuraScans')
            serializer = AsuraScansSerializer(manga, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AllBooks.DoesNotExist:
            return Response({'message': 'AsuraScans not found'}, status=status.HTTP_404_NOT_FOUND)

class AsuraScansSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        mangas = AllBooks.objects.filter(title__icontains=title_query, novel_source='AsuraScans')
        serializer = AsuraScansSerializer(mangas, many=True)
        return Response(serializer.data)

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
        # User does not exist, so we can create a new user
        user = User.objects.create_user(username=username, email=username, password=password, first_name=profileName)
        payload = {
            'username': user.username,
            'profileName': user.first_name,
            'exp': datetime.utcnow() + timedelta(days=2)  # Set token to expire in 2 days
        }
        
        jwt_token = jwt.encode(payload, settings.JWT_TOKEN, algorithm='HS256')

        return Response({
            "message": "User created successfully",
            "token": jwt_token
        }, status=status.HTTP_201_CREATED)
    
    # This line should never be reached
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
            'exp': datetime.utcnow() + timedelta(days=2)  # Set token to expire in 2 days
        }
        
        jwt_token = jwt.encode(payload, settings.JWT_TOKEN, algorithm='HS256')

        return Response({
            "message": "Login successful",
            "token": jwt_token
        }, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(['PUT'])
# @permission_classes([IsAuthenticated])
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
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)
            response = Response({'reading_list': profile.reading_list})
            # TODO: Handle CORS better. 
            # Currently I am allowing all origins, which must be changed before deploying
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept"
            return response
        except (User.DoesNotExist, Profile.DoesNotExist):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

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
        print("User not found")
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Profile.DoesNotExist:
        print("Profile not found")
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

        novel = AllBooks.objects.get(title=title, novel_source=novel_source)
        # if (novel_source == 'Light Novel Pub'):
        #     novel = AllBooks.objects.get(title=title, novel_source='Light Novel Pub')
        # elif (novel_source == 'AsuraScans'):
        #     novel = AllBooks.objects.get(title=title, novel_source='AsuraScans')

        latest_chapter = novel.get_latest_chapter()
        chapter_link = novel.get_chapter_link(latest_chapter)

        for book in profile.reading_list:
            if book['title'] == title and book['novel_source'] == novel_source:
                book['latest_read_chapter'] = latest_chapter
                book['chapter_link'] = chapter_link
                break

        profile.save()
        return Response({"message": "Updated to latest chapter successfully"}, status=status.HTTP_200_OK)
    except AllBooks.DoesNotExist:
        print("AllBooks not found")
        return Response({"error": "AllBooks not found"}, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        print("User not found")
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Profile.DoesNotExist:
        print("Profile not found")
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LightNovelPubCreateView(views.APIView):
    def post(self, request):
        serializer = LightNovelPubSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        lightNovels = AllBooks.objects.filter(novel_source='Light Novel Pub').all()
        serializer = LightNovelPubSerializer(lightNovels, many=True)
        return Response(serializer.data)

class LightNovelPubUpdateView(views.APIView):
    def put(self, request, title):
        try:
            lightNovel = AllBooks.objects.get(title=title, novel_source='Light Novel Pub')
            serializer = LightNovelPubSerializer(lightNovel, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AllBooks.DoesNotExist:
            return Response({'message': 'Light Novel not found'}, status=status.HTTP_404_NOT_FOUND)

class LightNovelPubSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        lightNovel = AllBooks.objects.filter(title__icontains=title_query, novel_source='Light Novel Pub')
        serializer = LightNovelPubSerializer(lightNovel, many=True)
        return Response(serializer.data)

# TODO: Might need to change this to include light novel vs Manga, or source? Not sure
class BookDetailsView(views.APIView):
    def get(self, request, title):
        book = AllBooks.objects.filter(title=title).first()
        if not book:
            return Response({'message': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if isinstance(book, AllBooks):
            serializer = AsuraScansSerializer(book)
        else:
            serializer = LightNovelPubSerializer(book)
        
        return Response(serializer.data)
