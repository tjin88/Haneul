## How to run:
1. Run Django App
2. Run Scraper
3. Run Frontend

### AsuraScans scraper
cd server
python -m venv myenv --> only on first run
source myenv/bin/activate
cd django_app
python manage.py scrapeAsuraScans

### AsuraScans scraper
cd server
python -m venv myenv --> only on first run
source myenv/bin/activate
cd django_app
python manage.py scrapeLightNovelPub

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

### To clear "GET /centralized_API_backend/api/asurascans/" directory
cd server
source myenv/bin/activate
cd django_app
python manage.py shell
from centralized_API_backend.models import AsuraScans
AsuraScans.objects.all().delete()

### Update the requirements.txt
cd server
source myenv/bin/activate
pip freeze > requirements.txt

# Notes:
- Currently scraping manga using standalone python scripts --> Port over to Django app!

# Next steps:

## Immediate (Done most, still need to host and add scheduled scraping**)
1. Scheduled Scraping (Cron*)
    - Likely will scrape once every hour, 3 hours, or 6 hours (depends on the typical release schedule of publisher)

## Short-term (Done all except tokenization!)
1. Update frontend to use tokenization, allowing user to stay logged in for x days
    - This will also make sure proper CSRF protection
2. Update frontend to have less API calls to it more efficient/fast
3. Add a page for user settings, where you can change your profile image, password, and email

## Long-term
- Look into opening multiple tabs with selenium to reduce the time to scrape all books
    - scrapeLightNovelPub: 
        - Currently it takes a minimum of ~17 minutes to scrape all books with NO changes
        - With changes is usually 45 - 75 minutes. Clearly this needs to be reduced or improved.
    - scrapeAsuraScans:
        - Currently it is around 50-60 seconds. No changes needed atm.
- Add AWS or other cloud hosting to run every x minutes/hours
    - Planning on using Cron at the moment
- Look at how to solve the problem where the novel has mutliple names
    - Look into finding/creating a database with all novel/manga, along with their alt names?