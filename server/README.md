## How to run:

source myenv/bin/activate
python3 scraper.py

# Next steps:

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
    - 

## Long-term
- Add AWS or other cloud hosting to run every x minutes/hours