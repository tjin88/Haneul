from django.db import models

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
    manga_type = models.CharField(max_length=50)  # 'type' is a reserved keyword in Python
    followers = models.CharField(max_length=100)
    chapters = models.JSONField(default=dict)

    def __str__(self):
        return self.title
    
# Add more models below if needed
