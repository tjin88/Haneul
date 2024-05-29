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

def execute_sql_statements():
    with conn.cursor() as cursor:
        # Rename columns
        cursor.execute("ALTER TABLE reading_list RENAME COLUMN title TO book_title;")
        cursor.execute("ALTER TABLE reading_list RENAME COLUMN novel_source TO book_novel_source;")
        
        # Drop unnecessary columns
        cursor.execute("ALTER TABLE reading_list DROP COLUMN chapter_link;")
        cursor.execute("ALTER TABLE reading_list DROP COLUMN novel_type;")
        
        # Add unique constraint
        cursor.execute("""
            ALTER TABLE reading_list 
            ADD CONSTRAINT unique_book_profile UNIQUE (book_title, book_novel_source, profile_id);
        """)
        
        # Commit the changes
        conn.commit()

def fetch_table_data(table_name):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        print(f"\nTable: {table_name}")
        print(f"{' | '.join(columns)}")
        for row in rows:
            print(f"{' | '.join(str(cell) for cell in row)}")

# Execute the SQL statements to alter the table structure
execute_sql_statements()

# List of tables to fetch data from
tables = [
    'reading_list',
]

for table in tables:
    fetch_table_data(table)

# Close the connection
conn.close()
