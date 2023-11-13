## How to run:

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
- Add MongoDB configuration to save on a cloud database rather than a local database
- Create a frontend that will display the image, title, and chapter information for each book
    - Bookmarking function
    - User's current chapter information
    - Tags function
    - Reading status

## Long-term
- Add AWS or other cloud hosting to run every x minutes/hours
- Look at how to solve the problem where the novel has mutliple names
    - Look into finding/creating a database with all novel/manga, along with their alt names?