import psycopg2
from psycopg2.extras import Json
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()  # Load environment variables from .env file

# PostgreSQL connection using environment variables
postgresql_name = os.getenv('postgresql_name')
postgresql_user = os.getenv('postgresql_user')
postgresql_password = os.getenv('postgresql_password')
postgresql_host = os.getenv('postgresql_host')
postgresql_port = os.getenv('postgresql_port')

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=postgresql_name,
    user=postgresql_user,
    password=postgresql_password,
    host=postgresql_host,
    port=postgresql_port,
)

def fetch_table_schema(table_name):
    with conn.cursor() as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """)
        columns = cursor.fetchall()
        print(f"\nTable: {table_name}")
        for column in columns:
            column_name, data_type, char_max_length, is_nullable = column
            char_max_length_str = f"({char_max_length})" if char_max_length else ""
            print(f"{column_name}: {data_type}{char_max_length_str}, Nullable: {is_nullable}")

# List of tables to fetch schema from
tables = [
    # 'all_books',
    # 'auth_user',
    'genre',
    # 'profile',
    # 'reading_list',
    'all_books_genres'
    # 'centralized_API_backend_profile',
    # 'centralized_API_backend_lightnovelpub',
    # 'centralized_API_backend_lightnovelpub_new_genres',
    # 'centralized_API_backend_genre',
    # 'centralized_API_backend_asurascans',
    # 'centralized_API_backend_asurascans_new_genres',
    # 'centralized_API_backend_allbooks',
    # 'centralized_API_backend_allbooks_new_genres'
]

for table in tables:
    fetch_table_schema(table)

# Close the connection
conn.close()
