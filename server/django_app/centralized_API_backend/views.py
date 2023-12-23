from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from .models import Manga, Profile, LightNovel
from .serializers import MangaSerializer, LightNovelSerializer
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

# TODO: Change from 'Manga' and 'LightNovel' --> 'AsuraScans' and 'LightNovelPub'

# TODO: Implement the below function to get ALL books (from AsuraScans AND LightNovelPub)
class AllNovelGetView(views.APIView):
    def get(self, request):
        mangas = Manga.objects.all()
        mangaSerializer = MangaSerializer(mangas, many=True)

        lightNovels = LightNovel.objects.all()
        lightNovelSerializer = LightNovelSerializer(lightNovels, many=True)

        serializer = mangaSerializer.data + lightNovelSerializer.data
        return Response(serializer)

class AllNovelSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        novel_source = request.GET.get('novel_source', '')
        if novel_source == 'AsuraScans':
            mangas = Manga.objects.filter(title__icontains=title_query)
            mangaSerializer = MangaSerializer(mangas, many=True)
            serializer = mangaSerializer.data
        elif novel_source == 'Light Novel Pub':
            lightNovels = LightNovel.objects.filter(title__icontains=title_query)
            lightNovelSerializer = LightNovelSerializer(lightNovels, many=True)
            serializer = lightNovelSerializer.data
        else:
            mangas = Manga.objects.filter(title__icontains=title_query)
            mangaSerializer = MangaSerializer(mangas, many=True)
            lightNovels = LightNovel.objects.filter(title__icontains=title_query)
            lightNovelSerializer = LightNovelSerializer(lightNovels, many=True)
            serializer = mangaSerializer.data + lightNovelSerializer.data

        return Response(serializer)

class MangaCreateView(views.APIView):
    def post(self, request):
        serializer = MangaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        mangas = Manga.objects.all()
        serializer = MangaSerializer(mangas, many=True)
        return Response(serializer.data)

class MangaUpdateView(views.APIView):
    def put(self, request, title):
        try:
            manga = Manga.objects.get(title=title)
            serializer = MangaSerializer(manga, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Manga.DoesNotExist:
            return Response({'message': 'Manga not found'}, status=status.HTTP_404_NOT_FOUND)

class MangaSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        mangas = Manga.objects.filter(title__icontains=title_query)
        serializer = MangaSerializer(mangas, many=True)
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

        profile.reading_list = [book for book in profile.reading_list if book['title'] != title_to_delete and book['novel_source'] != source]
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

        if (novel_source == 'Light Novel Pub'):
            novel = LightNovel.objects.get(title=title)
        elif (novel_source == 'AsuraScans'):
            novel = Manga.objects.get(title=title)

        latest_chapter = novel.get_latest_chapter()
        chapter_link = novel.get_chapter_link(latest_chapter)

        for book in profile.reading_list:
            if book['title'] == title and book['novel_source'] == novel_source:
                book['latest_read_chapter'] = latest_chapter
                book['chapter_link'] = chapter_link
                break

        profile.save()
        return Response({"message": "Updated to latest chapter successfully"}, status=status.HTTP_200_OK)
    except Manga.DoesNotExist:
        print("Manga not found")
        return Response({"error": "Manga not found"}, status=status.HTTP_404_NOT_FOUND)
    except LightNovel.DoesNotExist:
        print("LightNovel not found")
        return Response({"error": "Light Novel not found"}, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        print("User not found")
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Profile.DoesNotExist:
        print("Profile not found")
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LightNovelCreateView(views.APIView):
    def post(self, request):
        serializer = LightNovelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        lightNovels = LightNovel.objects.all()
        serializer = LightNovelSerializer(lightNovels, many=True)
        return Response(serializer.data)

class LightNovelUpdateView(views.APIView):
    def put(self, request, title):
        try:
            manga = LightNovel.objects.get(title=title)
            serializer = LightNovelSerializer(manga, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except LightNovel.DoesNotExist:
            return Response({'message': 'Light Novel not found'}, status=status.HTTP_404_NOT_FOUND)

class LightNovelSearchView(views.APIView):
    def get(self, request):
        title_query = request.GET.get('title', '')
        lightNovel = LightNovel.objects.filter(title__icontains=title_query)
        serializer = LightNovelSerializer(lightNovel, many=True)
        return Response(serializer.data)
