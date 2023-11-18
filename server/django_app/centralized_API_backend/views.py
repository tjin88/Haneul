from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from .models import Manga
from .serializers import MangaSerializer
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator

class MangaCreateView(views.APIView):
    def post(self, request):
        serializer = MangaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        mangas = Manga.objects.all()  # Retrieve all manga records from the database
        serializer = MangaSerializer(mangas, many=True)  # Serialize the data
        return Response(serializer.data)  # Return the serialized data in the response

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

@method_decorator(csrf_exempt, name='dispatch')
@api_view(['POST'])
def register_view(request):
    data = request.data
    username = data.get('email')
    password = data.get('password')
    profileName = data.get('profileName')

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=status.HTTP_409_CONFLICT)

    user = User.objects.create_user(username=username, email=username, password=password, first_name=profileName)
    return Response({"message": "User created successfully", "user": {"username": user.username, "profileName": user.first_name}}, status=status.HTTP_201_CREATED)

@csrf_exempt
@api_view(['POST'])
def login_view(request):
    data = request.data
    username = data.get('email')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({"message": "Login successful", "user": {"username": user.username, "profileName": user.first_name}}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)