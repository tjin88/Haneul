## How to run:
1. Run Django App
2. Run Scraper
3. Run Frontend

### Run scrapers
cd server
python -m venv myenv --> only on first run --> Built on Python 3.8.2
source myenv/bin/activate
pip install -r requirements.txt  --> only on first run
cd django_app
python manage.py master_scraper  --> Test all scrapers
python manage.py test_individual_scraper scrapeMangaSushi.py --> Test only 1 scraper

### Django App API Endpoints
cd server
source myenv/bin/activate
pip install -r requirements.txt  --> only on first run
cd django_app
python manage.py runserver

### See all files in a tree format
tree -I "node_modules|.git|out|migrations|myenv|__pycache__|static" --prune --> I excludes directories, prune gets rid of empty directories

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

### Run Extension
- Ensure the server is up and running, and the extension is pointing to server (currently server = localhost)
- Update manifest.json file based on Firefox (v2) and Chrome/Edge (v3)
- Should be quite plug and play :)

# Notes:
- Long term goal: Recommendation algo for users. Likely a K-means model?
- Socket programming would work well with the extension

# Current Tech Stack
- Frontend: REACT
- Backend: Django
- Database: Supabase (free tier)
- Server: Render (free tier)
- Extension: Releasing soon on on Chrome, Firefox, and Edge
- Cron Jobs: Locally scraping 25 sources every 2 hours, and Light Novel Pub every 4 hours
- Future implementation: Redis

# Next steps:

## Immediate
1. Add original link (untranslated)
    - Navier and other sources 
    - https://comic.naver.com/index
- TODO: Protect against injection attacks **

## Short-term
1. Update frontend to use tokenization, allowing user to stay logged in for x days
    - This will also make sure proper CSRF protection
2. Add a page for user settings, where you can change your profile image, password, and email
3. Scrape not only title, but any alternative titles. Then, when searching, check alternative title too ...
    - This will greatly increase the scraping and fetching difficulty. I dread, but yes definitely worh 
    - Would make the browse really pretty. Peek Solo Leveling vs Alone I level Up (same book :/)

## Websites to scrape:
On Pause:
- https://rizzfables.com/series --> Similar to AsuraScans, but there are some security protections. Fair, but I want to help them ?

Easy Light Novels (Similar to AsuraScans):
- https://tanooki.team/series/list-mode/
- https://arcanetranslations.com/series/list-mode/ --> Change "Korean Novel" to "Light Novel"
- https://donghuastream.org/anime/list-mode/ --> Anime not LN or Manga

Easy Manga:
- GET https://api.mangadex.org/manga?limit=100&offset=100
    - 76742 books. Site where scanslators upload their work
    - Instead of getting all data from this API, then storing it myself,
      can I, on the frontend, test if the book is in mangadex?
        - Yes this is possible:
        - GET https://api.mangadex.org/manga?title=solo%20leveling&limit=100
        - Returns all books that match this with their title OR alt title
            - IF going this route, check exact match to the title or alt title
            - https://api.mangadex.org/manga?title=reincarnator returns 6 books ...

Medium Manga (Similar to MangaSushi)
https://novelmic.com/comic/ --> Same as BoxNovel
- https://yakshascans.com/manga/
- https://paragonscans.com/mangax/ --> Aggregator :(
- https://stonescape.xyz/manhwaseries/
    - Also https://stonescape.xyz/novels/ for LN
- https://kakuseiproject.com/manga/ --> Portugese ?
- https://aryascans.com/manga/
- https://ksgroupscans.com/?s=&post_type=wp-manga
- https://blazescans.com/manga/list-mode/ --> Likely to be an aggregator
- https://darkscans.com/mangas/ --> Likely to be an aggregator
- https://dragontea.ink/manga/ --> Good but protection
- https://kunmanga.com/page/8/ --> Likely to be an aggregator
- https://coffeemanga.io/page/20/ --> Likely to be an aggregator

Not the worst:
- https://lightnovelstranslations.com/read/page/14/

Medium but worth:
- https://manhuaplus.com/ --> Tales of Demons and Gods! Douluo Dalu! BTTH
- https://manhwa-freak.org/manga/ --> Lots of books (and good titles), but nothing similar

Hard but worth:
- https://tcbscans.me/projects --> One Piece, Demon Slayer, Attack on Titan, Bleach, Chainsaw Man, Hunter x Hunter, Haikyuu, Jujutsu Kaisen Spy x Family
- https://likemanga.io/?act=home&pageNum=2#pages
- https://www.tappytoon.com/en/comics/home
- https://tapas.io/menu/2/subtab/7

Hard:
- https://zetrotranslation.com/novel/i-hope-youre-still-alive-when-tomorrow-comes/
- https://vortexscans.org/series
- https://wickedscans.com/series/
- https://ezmanga.net/series/
- https://po2scans.com/series
- https://scyllacomics.xyz/manga/
- https://templescan.net/comics
- https://flixscans.org/webtoons/action/home
- https://reaperscans.com/comics