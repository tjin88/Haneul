from django.shortcuts import render
from rest_framework import status, views
from rest_framework.response import Response
from .models import Manga
from .serializers import MangaSerializer

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

# Add more views here.
