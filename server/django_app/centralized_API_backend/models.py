from django.db import models
import uuid
import re
from django.contrib.auth.models import User

class AsuraScans(models.Model):
    title = models.CharField(max_length=255, db_index=True, primary_key=True)
    synopsis = models.TextField()
    author = models.CharField(max_length=100, blank=True, null=True)
    # artist = models.CharField(max_length=100, blank=True, null=True)
    # released_by = models.CharField(max_length=100, blank=True, null=True)
    # serialization = models.CharField(max_length=100, blank=True, null=True)
    # posted_by = models.CharField(max_length=100, blank=True, null=True)
    # posted_on = models.DateTimeField()
    updated_on = models.DateTimeField()
    newest_chapter = models.CharField(max_length=100)
    genres = models.JSONField()
    image_url = models.URLField(max_length=500)
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=50)
    novel_type = models.CharField(max_length=50)  # 'type' is a reserved keyword in Python
    novel_source = models.CharField(max_length=50, default='AsuraScans')
    followers = models.CharField(max_length=100)
    chapters = models.JSONField(default=dict)

    def __str__(self):
        return self.title

    # For AsuraScans, the latest chapter is the first chapter in the chapters dict
    def get_latest_chapter(self):
        return next(iter(self.chapters), None) if self.chapters else None

    def get_chapter_link(self, chapter):
        return self.chapters.get(chapter, None)

class LightNovelPub(models.Model):
    title = models.CharField(max_length=255, db_index=True, primary_key=True)
    synopsis = models.TextField()
    author = models.CharField(max_length=100, blank=True, null=True)
    # artist = models.CharField(max_length=100, blank=True, null=True)
    # released_by = models.CharField(max_length=100, blank=True, null=True)
    # serialization = models.CharField(max_length=100, blank=True, null=True)
    # posted_by = models.CharField(max_length=100, blank=True, null=True)
    # posted_on = models.DateTimeField()
    updated_on = models.DateTimeField()
    newest_chapter = models.CharField(max_length=100)
    genres = models.JSONField()
    image_url = models.URLField(max_length=500)
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=50)
    novel_type = models.CharField(max_length=50)  # 'type' is a reserved keyword in Python
    novel_source = models.CharField(max_length=50, default='Light Novel Pub')
    followers = models.CharField(max_length=100)
    chapters = models.JSONField(default=dict)

    def __str__(self):
        return self.title

    # For LightNovelPub, the latest chapter is the last chapter in the chapters dict
    def get_latest_chapter(self):
        if not self.chapters:
            return None

        def chapter_key(chapter_str):
            # Extract numerical parts from the chapter string
            numbers = re.findall(r"\d+\.\d+|\d+", chapter_str)
            # Convert string numbers to floats for proper comparison
            return [float(num) for num in numbers]

        # Find the chapter with the maximum numerical value
        latest_chapter = max(self.chapters.keys(), key=chapter_key)
        return latest_chapter

    def get_chapter_link(self, chapter):
        return self.chapters.get(chapter, None)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    reading_list = models.JSONField(default=list)

    def __str__(self):
        return self.user.username

# Add more models below if needed
