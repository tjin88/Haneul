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

def fetch_table_data(table_name):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        print(f"\nTable: {table_name}")
        print(f"{' | '.join(columns)}")
        for row in rows:
            print(f"{' | '.join(str(cell) for cell in row)}")

# List of tables to fetch data from
tables = [
    # 'auth_user',
    # 'genre',
    # 'profile',
    # 'reading_list',
    # 'all_books',
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
    fetch_table_data(table)

# Close the connection
conn.close()
