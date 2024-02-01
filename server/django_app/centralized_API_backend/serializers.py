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

class SimpleNovelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['title', 'image_url', 'newest_chapter']

    def to_representation(self, instance):
        if isinstance(instance, AsuraScans):
            self.Meta.model = AsuraScans
        elif isinstance(instance, LightNovelPub):
            self.Meta.model = LightNovelPub
        return super(SimpleNovelSerializer, self).to_representation(instance)
