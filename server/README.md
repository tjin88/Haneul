## How to run:
1. Run Django App
2. Run Scraper
3. Run Frontend

### AsuraScans scraper
cd server
python -m venv myenv --> only on first run
source myenv/bin/activate
python3 scraper.py

### Django App API Endpoints
cd server
source myenv/bin/activate
cd django_app
python manage.py runserver

### When making changes to the Django Models
cd server
source myenv/bin/activate
cd django_app
python manage.py makemigrations
python manage.py migrate

### To clear "GET /centralized_API_backend/api/manga/" directory
cd server
source myenv/bin/activate
cd django_app
python manage.py shell
from centralized_API_backend.models import Manga
Manga.objects.all().delete()

### Update the requirements.txt
cd server
source myenv/bin/activate
pip freeze > requirements.txt

# Next steps:

## Immediate:
1. Database Setup (MongoDB)
2. Scheduled Scraping (APScheduler)
    - Likely will scrape once every hour, 3 hours, or 6 hours (depends on the typical release schedule of publisher)
3. Backend API (Flask or Django)
    - This API layer will be used for security between the database and the frontend
4. Deployment and Running (AWS, Azure, GCP)
5. Frontend (React)

## Short-term
- Create a frontend that will display the image, title, and chapter information for each book
    - Bookmarking function
    - User's current chapter information
    - Tags function
    - Reading status
- Add a page for user settings, where you can change your profile image, password, and email
- Add a page for each book, where you can add the book to your tracker,
and you can see the book's details (Total chapters, synopsis, genres, book type, etc.) 
- Add tokenization to ensure proper CSRF protection. Currently I've bypassed this, which definitely needs to be fixed before deploying

## Long-term
- Add AWS or other cloud hosting to run every x minutes/hours
- Look into how to solve the problem where the book is both a light novel and manga. Planning to use a primary key of a combination of book_title and book_type
- Look at how to solve the problem where the novel has mutliple names
    - Look into finding/creating a database with all novel/manga, along with their alt names?