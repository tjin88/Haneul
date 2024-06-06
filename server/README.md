## How to run:
1. Run Django App
2. Run Scraper
3. Run Frontend

### AsuraScans scraper
cd server
python -m venv myenv --> only on first run
source myenv/bin/activate
pip install -r requirements.txt  --> only on first run
cd django_app
python manage.py scrapeAsuraScans

### LightNovelPub scraper
cd server
python -m venv myenv --> only on first run
source myenv/bin/activate
pip install -r requirements.txt  --> only on first run
cd django_app
python manage.py scrapeLightNovelPub

### Django App API Endpoints
cd server
source myenv/bin/activate
pip install -r requirements.txt  --> only on first run
cd django_app
python manage.py runserver

### When making changes to the Django Models
cd server
source myenv/bin/activate
cd django_app
python manage.py makemigrations
python manage.py migrate

### Update the requirements.txt
cd server
source myenv/bin/activate
pip freeze > requirements.txt

# Notes:
- Long term goal: Recommendation algo for users. Likely a K-means model?
- Socket programming would work well with the extension
- Extension has two different manifest.json files
    - V2 if Firefox (not Chromium)

# Current Tech Stack
- Frontend: REACT
- Backend: Django
- Database: PostgreSQL (hosted locally, will host on same platform as server later)
- Server: Local. Planning on using either AWS or Render (Render is nice since free tier)
- Extension: Available on Chrome, Firefox, and Edge
- Cron Jobs: Locally scraping AsuraScans every 2 hours, and Light Novel Pub every 4 hours

# Next steps:

## Immediate
1. Add original link (untranslated)
    - Navier and other sources 
    - https://comic.naver.com/index
- TODO: Protect against injection attacks **

## Short-term (Done all except tokenization!)
1. Update frontend to use tokenization, allowing user to stay logged in for x days
    - This will also make sure proper CSRF protection
2. Add a page for user settings, where you can change your profile image, password, and email

## Websites to scrape:
On Pause:
- https://rizzfables.com/series --> Similar to AsuraScans, but there are some security protections. Fair, but I want to help them ?

Easy Light Novels (Similar to AsuraScans):
- https://arcanetranslations.com/series/list-mode/ --> Change "Korean Novel" to "Light Novel"

Medium Manga (These are all similar format):
- https://boxnovel.com/novel/
- https://tritinia.org/manga/
- https://lhtranslation.net/manga/
- https://setsuscans.com/
- https://mortalsgroove.com/mangas/

Medium Manga (These are similar to the above, but likely most protection or slightly different format)
- https://gdscans.com/page/2/
- https://reset-scans.xyz/mangas/
- https://hiraethtranslation.com/novel-genre/web-novel-cn/

Not the worst:
- https://lightnovelstranslations.com/read/page/14/

Hard:
- https://zetrotranslation.com/novel/i-hope-youre-still-alive-when-tomorrow-comes/