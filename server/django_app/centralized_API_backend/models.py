from django.db import models
from django.contrib.auth.models import User

class Manga(models.Model):
    title = models.CharField(max_length=255, primary_key=True)
    synopsis = models.TextField()
    author = models.CharField(max_length=100, blank=True, null=True)
    artist = models.CharField(max_length=100, blank=True, null=True)
    released_by = models.CharField(max_length=100, blank=True, null=True)
    serialization = models.CharField(max_length=100, blank=True, null=True)
    posted_by = models.CharField(max_length=100, blank=True, null=True)
    posted_on = models.DateTimeField()
    updated_on = models.DateTimeField()
    newest_chapter = models.CharField(max_length=100)
    genres = models.JSONField()
    image_url = models.URLField(max_length=500)
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=50)
    novel_type = models.CharField(max_length=50)  # 'type' is a reserved keyword in Python
    followers = models.CharField(max_length=100)
    chapters = models.JSONField(default=dict)

    def __str__(self):
        return self.title

    def get_latest_chapter(self):
        return next(iter(self.chapters), None) if self.chapters else None

    def get_chapter_link(self, chapter):
        return self.chapters.get(chapter, None)

class LightNovel(models.Model):
    title = models.CharField(max_length=255, primary_key=True)
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
    followers = models.CharField(max_length=100)
    chapters = models.JSONField(default=dict)

    def __str__(self):
        return self.title

    def get_latest_chapter(self):
        return next(iter(self.chapters), None) if self.chapters else None

    def get_chapter_link(self, chapter):
        return self.chapters.get(chapter, None)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    reading_list = models.JSONField(default=list)

    def __str__(self):
        return self.user.username

# Add more models below if needed
