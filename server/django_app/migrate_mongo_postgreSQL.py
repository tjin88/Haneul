import pymongo
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import os
import json
from decimal import Decimal
from dotenv import load_dotenv
from urllib.parse import quote_plus

import logging
from psycopg2 import pool
from bson import ObjectId, Decimal128

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # Load environment variables from .env file

# MongoDB connection using environment variables
username = quote_plus(os.getenv('USERNAME'))
password = quote_plus(os.getenv('PASSWORD'))
cluster = os.getenv('CLUSTER')
mongo_client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority")
mongo_db = mongo_client['SCRAPED_MANGA_AND_LIGHTNOVEL_DATABASE']

# PostgreSQL connection using environment variables
postgresql_name = os.getenv('postgresql_name')
postgresql_user = os.getenv('postgresql_user')
postgresql_password = os.getenv('postgresql_password')
postgresql_host = os.getenv('postgresql_host')
postgresql_port = os.getenv('postgresql_port')

# Initialize PostgreSQL connection pool
pg_pool = psycopg2.pool.SimpleConnectionPool(1, 10, 
    dbname=postgresql_name,
    user=postgresql_user,
    password=postgresql_password,
    host=postgresql_host,
    port=postgresql_port
)

def get_pg_connection():
    return pg_pool.getconn()

def release_pg_connection(conn):
    pg_pool.putconn(conn)

# Function to create tables in PostgreSQL
def create_tables():
    conn = get_pg_connection()
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("""
    DROP TABLE IF EXISTS all_books_genres, all_books, reading_list, profile, genre CASCADE;
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genre (
        id SERIAL PRIMARY KEY,
        name VARCHAR(150) UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        id VARCHAR(24) PRIMARY KEY,
        user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
        reading_list JSONB DEFAULT '[]'::jsonb
    );
    """)

    # Old reading_list table structure
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reading_list (
        id SERIAL PRIMARY KEY,
        profile_id VARCHAR(24) REFERENCES profile(id) ON DELETE CASCADE,
        title VARCHAR(255),
        reading_status VARCHAR(50),
        user_tag VARCHAR(100),
        latest_read_chapter VARCHAR(255),
        chapter_link VARCHAR(500),
        novel_type VARCHAR(50),
        novel_source VARCHAR(100)
    );
    """)

    # Current reading_list table structure
    '''
    CREATE TABLE IF NOT EXISTS reading_list (
        id SERIAL PRIMARY KEY,
        profile_id VARCHAR(24) REFERENCES profile(id) ON DELETE CASCADE,
        reading_status VARCHAR(50),
        user_tag VARCHAR(100),
        latest_read_chapter VARCHAR(255),
        book_title VARCHAR(255),
        book_novel_source VARCHAR(100),
        FOREIGN KEY (book_title, book_novel_source) REFERENCES all_books (title, novel_source) ON DELETE CASCADE
    );
    '''

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS all_books (
        title VARCHAR(255) NOT NULL,
        novel_source VARCHAR(100) NOT NULL DEFAULT 'Unknown',
        synopsis TEXT NOT NULL,
        author VARCHAR(150),
        updated_on TIMESTAMP NOT NULL,
        newest_chapter VARCHAR(150) NOT NULL,
        image_url VARCHAR(500) NOT NULL,
        rating DECIMAL(4, 2) NOT NULL,
        status VARCHAR(100) NOT NULL,
        novel_type VARCHAR(100) NOT NULL,
        followers VARCHAR(100) NOT NULL,
        chapters JSONB DEFAULT '{}'::jsonb,
        PRIMARY KEY (title, novel_source)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS all_books_genres (
        id SERIAL PRIMARY KEY,
        allbooks_title VARCHAR(255),
        allbooks_novel_source VARCHAR(100),
        genre_id INTEGER REFERENCES genre(id) ON DELETE CASCADE,
        FOREIGN KEY (allbooks_title, allbooks_novel_source)
            REFERENCES all_books (title, novel_source) ON DELETE CASCADE
    );
    """)
    conn.commit()
    release_pg_connection(conn)

# Function to insert data into PostgreSQL
def insert_data():
    conn = get_pg_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN;")
        
        # Insert Users into auth_user table
        users = mongo_db['auth_user'].find()
        user_records = []
        for user in users:
            date_joined = user['date_joined']
            if isinstance(date_joined, dict) and '$date' in date_joined:
                date_joined = datetime.utcfromtimestamp(date_joined['$date'] / 1000)
            elif isinstance(date_joined, str):
                date_joined = datetime.strptime(date_joined, '%Y-%m-%dT%H:%M:%S')
            elif isinstance(date_joined, int):
                date_joined = datetime.utcfromtimestamp(date_joined / 1000)
            else:
                date_joined = datetime.utcnow()
            
            last_login = user.get('last_login')
            if last_login:
                if isinstance(last_login, dict) and '$date' in last_login:
                    last_login = datetime.utcfromtimestamp(last_login['$date'] / 1000)
                elif isinstance(last_login, str):
                    last_login = datetime.strptime(last_login, '%Y-%m-%dT%H:%M:%S')
                elif isinstance(last_login, int):
                    last_login = datetime.utcfromtimestamp(last_login / 1000)
                else:
                    last_login = None

            user_records.append((
                int(user['id']),
                user['username'],
                user['password'],
                user['email'],
                user.get('is_staff', False),
                user.get('is_active', True),
                date_joined,
                user.get('is_superuser', False),  # Adding default value for is_superuser
                last_login,
                user.get('first_name', ''),  # Adding default empty string for first_name
                user.get('last_name', '')  # Adding default empty string for last_name
            ))

        cursor.executemany("""
            INSERT INTO auth_user (id, username, password, email, is_staff, is_active, date_joined, is_superuser, last_login, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, user_records)
        logging.info(f'Inserted {len(user_records)} users.')

        # Insert Genres with normalization
        genre_mapping = {}
        genres = mongo_db['centralized_API_backend_genre'].find()
        normalized_genre_records = {}
        
        for genre in genres:
            normalized_name = genre['name'].strip().lower()
            if normalized_name not in normalized_genre_records:
                normalized_genre_records[normalized_name] = genre['name'].strip()

        genre_records = [(name,) for name in normalized_genre_records.keys()]
        
        cursor.executemany("""
            INSERT INTO genre (name) VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, genre_records)
        
        # Fetch genre IDs to create a mapping
        cursor.execute("SELECT id, name FROM genre")
        genre_results = cursor.fetchall()
        for result in genre_results:
            genre_mapping[result[1].lower()] = result[0]
        logging.info(f'Inserted {len(genre_records)} genres.')

        # Insert Profiles and Reading List
        profiles = mongo_db['centralized_API_backend_profile'].find()
        profile_records = []
        reading_list_records = []
        for profile in profiles:
            profile_records.append((
                str(profile['_id']),  # Convert ObjectId to string
                int(profile['user_id']),  # Ensure user_id is an integer
                Json(profile['reading_list'])
            ))
            reading_list = json.loads(profile['reading_list'])
            for item in reading_list:
                reading_list_records.append((
                    str(profile['_id']),  # Convert ObjectId to string
                    item['title'],
                    item.get('reading_status', ''),  # Provide default empty string if missing
                    item.get('user_tag', ''),  # Provide default empty string if missing
                    item.get('latest_read_chapter', ''),  # Provide default empty string if missing
                    item.get('chapter_link', ''),  # Provide default empty string if missing
                    item.get('novel_type', ''),  # Provide default empty string if missing
                    item.get('novel_source', '')  # Provide default empty string if missing
                ))
        cursor.executemany("""
            INSERT INTO profile (id, user_id, reading_list) VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, profile_records)
        cursor.executemany("""
            INSERT INTO reading_list (profile_id, title, reading_status, user_tag, latest_read_chapter, chapter_link, novel_type, novel_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, reading_list_records)
        logging.info(f'Inserted {len(profile_records)} profiles and {len(reading_list_records)} reading list items.')

        # Insert AllBooks and Genres
        all_books = mongo_db['centralized_API_backend_allbooks'].find()
        all_books_records = []
        genres_records = []
        for book in all_books:
            rating = book['rating']
            if isinstance(rating, Decimal128):
                rating = rating.to_decimal()

            all_books_records.append((
                book['title'],
                book['novel_source'],
                book['synopsis'],
                book.get('author'),
                datetime.strptime(book['updated_on'], '%Y-%m-%dT%H:%M:%S') if isinstance(book['updated_on'], str) else book['updated_on'],
                book['newest_chapter'],
                book['image_url'],
                rating,
                book['status'],
                book.get('novel_type', ''),  # Provide default empty string if missing
                book['followers'],
                Json(book['chapters'])
            ))
            if 'new_genres' in book:
                for genre_id in book['new_genres']:
                    normalized_genre_id = genre_mapping[normalized_genre_records[genre_id].lower()]
                    genres_records.append((
                        book['title'],
                        book['novel_source'],
                        normalized_genre_id
                    ))
        cursor.executemany("""
            INSERT INTO all_books (title, novel_source, synopsis, author, updated_on, newest_chapter, image_url, rating, status, novel_type, followers, chapters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (title, novel_source) DO NOTHING
        """, all_books_records)
        cursor.executemany("""
            INSERT INTO all_books_genres (allbooks_title, allbooks_novel_source, genre_id) VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, genres_records)
        logging.info(f'Inserted {len(all_books_records)} books and {len(genres_records)} genre relationships.')

        cursor.execute("COMMIT;")
    except Exception as e:
        cursor.execute("ROLLBACK;")
        logging.error(f'Error during data insertion: {e}')
    finally:
        release_pg_connection(conn)
        mongo_client.close()

# Create tables
create_tables()

# Insert data
insert_data()