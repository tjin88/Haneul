from rest_framework import serializers
from .models import Manga, LightNovel

class MangaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manga
        fields = '__all__'  # Rather than individually adding all fields, use all fields from models.py

        # fields = [
        #     'title', 'synopsis', 'author', 'artist', 'released_by', 
        #     'serialization', 'posted_by', 'posted_on', 'updated_on', 
        #     'newest_chapter', 'genres', 'image_url', 'rating', 
        #     'status', 'novel_type', 'followers', 'chapters'
        # ]


class LightNovelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LightNovel
        fields = '__all__'

