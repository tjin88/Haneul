from rest_framework import serializers
from .models import AllBooks

class AsuraScansSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllBooks
        fields = '__all__'  # Rather than individually adding all fields, use all fields from models.py

        # fields = [
        #     'title', 'synopsis', 'author', 'artist', 'released_by', 
        #     'serialization', 'posted_by', 'posted_on', 'updated_on', 
        #     'newest_chapter', 'genres', 'image_url', 'rating', 
        #     'status', 'novel_source', 'followers', 'chapters'
        # ]

class LightNovelPubSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllBooks
        fields = '__all__'

class HomeNovelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllBooks
        fields = ['title', 'image_url', 'newest_chapter', 'rating']

    # def to_representation(self, instance):
    #     if isinstance(instance, AllBooks):
    #         self.Meta.model = AllBooks
    #     elif isinstance(instance, AllBooks):
    #         self.Meta.model = AllBooks
    #     return super(HomeNovelSerializer, self).to_representation(instance)

class BrowseNovelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllBooks
        fields = ['title', 'image_url', 'genres', 'newest_chapter', 'status']

    # def to_representation(self, instance):
    #     if isinstance(instance, AllBooks):
    #         self.Meta.model = AllBooks
    #     elif isinstance(instance, AllBooks):
    #         self.Meta.model = AllBooks
    #     return super(BrowseNovelSerializer, self).to_representation(instance)

