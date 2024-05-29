from django.db import models
import re
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'genre'
        managed = False

    def __str__(self):
        return self.name

class Profile(models.Model):
    id = models.CharField(max_length=24, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    reading_list = models.JSONField(default=list)

    class Meta:
        db_table = 'profile'
        managed = False

    def __str__(self):
        return self.user.username

class AllBooks(models.Model):
    # id = models.BigAutoField(primary_key=True)
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
    genres = models.ManyToManyField('Genre', through='AllBooksGenres', related_name='all_books')

    class Meta:
        db_table = 'all_books'
        constraints = [
            models.UniqueConstraint(fields=['title', 'novel_source'], name='unique_book')
        ]
        indexes = [
            models.Index(fields=['title', 'novel_source'])
        ]
        managed = False

    def __str__(self):
        return f"{self.title} ({self.novel_source})"

    '''
        For AsuraScans, the latest chapter is the first chapter in the chapters dict
        For LightNovelPub, the latest chapter is the last chapter in the chapters dict
        TODO: Make a class list determining if the novel_source is first or last chapter for latest chapter
    '''
    def get_latest_chapter(self):
        if self.novel_source == 'AsuraScans':
            return next(iter(self.chapters), None) if self.chapters else None

        # Must be Light Novel Pub
        if not self.chapters:
            return None
        def chapter_key(chapter_str):
            numbers = re.findall(r"\d+\.\d+|\d+", chapter_str)
            return [float(num) for num in numbers]
        latest_chapter = max(self.chapters.keys(), key=chapter_key)
        return latest_chapter

    def get_chapter_link(self, chapter):
        return self.chapters.get(chapter, None)

class AllBooksGenres(models.Model):
    # Django does not support composite primary keys, so we will manually manage the relationships.
    allbooks = models.ForeignKey(AllBooks, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        db_table = 'all_books_genres'
        constraints = [
            models.UniqueConstraint(fields=['allbooks', 'genre'], name='unique_book_genre')
        ]
        indexes = [
            models.Index(fields=['allbooks', 'genre'])
        ]
        managed = False

    def __str__(self):
        return f"{self.allbooks.title}/{self.allbooks.novel_source} - {self.genre.name}"

class ReadingList(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    reading_status = models.CharField(max_length=50)
    user_tag = models.CharField(max_length=100, blank=True, null=True)
    latest_read_chapter = models.CharField(max_length=255, blank=True, null=True)
    # book_title and book_novel_source are FKs used to identify a book in a user's reading list
    book_title = models.CharField(max_length=255)
    book_novel_source = models.CharField(max_length=100)

    class Meta:
        db_table = 'reading_list'
        constraints = [
            models.UniqueConstraint(fields=['book_title', 'book_novel_source', 'profile'], name='unique_book_profile')
        ]
        indexes = [
            models.Index(fields=['profile', 'book_title', 'book_novel_source'])
        ]
        managed = False

    def __str__(self):
        return f"{self.profile.user.username} - {self.book_title} ({self.book_novel_source})"
