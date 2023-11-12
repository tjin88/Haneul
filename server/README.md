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

# Next steps:

## Immediate:
1. Database Setup (MongoDB)
2. Scheduled Scraping (APScheduler)
3. Backend API (Flask or Django)
4. Deployment and Running (AWS, Azure, GCP)
5. Frontend (React)

## Short-term
- Add MongoDB configuration to save on a database
- Look into optimizing the python script to:
    - have an initial scraper (gets everything, run this once a day)
    - have an updating scraper that only looks for changes (especially with new chapters)
- Create a frontend that will display the image, title, and chapter information for each book
    - Bookmarking function
    - User's current chapter information
    - Tags function
    - Reading status

## Long-term
- Add AWS or other cloud hosting to run every x minutes/hours