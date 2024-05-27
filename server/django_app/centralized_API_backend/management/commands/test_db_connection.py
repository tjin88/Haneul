import os
import django
from django.core.management.base import BaseCommand
from centralized_API_backend.models import AllBooks

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.django_app.settings')
django.setup()

class Command(BaseCommand):
    help = 'Test database connection'

    def handle(self, *args, **kwargs):
        try:
            # Check if we can fetch the first book
            first_book = AllBooks.objects.first()
            if first_book:
                self.stdout.write(self.style.SUCCESS(f"First book: {first_book.title}"))
            else:
                self.stdout.write(self.style.SUCCESS("No books found in the database."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error accessing the database: {e}"))

if __name__ == "__main__":
    Command().handle()
