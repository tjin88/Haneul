from rest_framework import serializers
from .models import AsuraScans, LightNovelPub

class AsuraScansSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsuraScans
        fields = '__all__'  # Rather than individually adding all fields, use all fields from models.py

        # fields = [
        #     'title', 'synopsis', 'author', 'artist', 'released_by', 
        #     'serialization', 'posted_by', 'posted_on', 'updated_on', 
        #     'newest_chapter', 'genres', 'image_url', 'rating', 
        #     'status', 'novel_source', 'followers', 'chapters'
        # ]

class LightNovelPubSerializer(serializers.ModelSerializer):
    class Meta:
        model = LightNovelPub
        fields = '__all__'

