from django.db import models
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'genre'

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    reading_list = models.JSONField(default=list)

    class Meta:
        db_table = 'profile'

    def __str__(self):
        return self.user.username

class AllBooks(models.Model):
    title = models.CharField(max_length=255)
    novel_source = models.CharField(max_length=100, default='Unknown')
    synopsis = models.TextField()
    author = models.CharField(max_length=150, blank=True, null=True)
    updated_on = models.DateTimeField()
    newest_chapter = models.CharField(max_length=150)
    image_url = models.URLField(max_length=500)
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=100)
    novel_type = models.CharField(max_length=100)   # 'type' is a reserved keyword in Python
    followers = models.CharField(max_length=100)
    chapters = models.JSONField(default=dict)
    genres = models.ManyToManyField('Genre', through='AllBooksGenres')

    class Meta:
        db_table = 'all_books'
        unique_together = (('title', 'novel_source'),)
        indexes = [
            models.Index(fields=['title', 'novel_source'])
        ]

    def __str__(self):
        return f"{self.title} ({self.novel_source})"

    # For AsuraScans, the latest chapter is the first chapter in the chapters dict
    # For LightNovelPub, the latest chapter is the last chapter in the chapters dict
    def get_latest_chapter(self):
        if self.novel_source == 'AsuraScans':
            return next(iter(self.chapters), None) if self.chapters else None

        # Must be Light Novel Pub
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

class AllBooksGenres(models.Model):
    allbooks = models.ForeignKey(AllBooks, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        db_table = 'all_books_genres'
        unique_together = (('allbooks', 'genre'),)
        indexes = [
            models.Index(fields=['allbooks', 'genre'])
        ]
