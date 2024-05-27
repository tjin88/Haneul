import psycopg2
import os
from dotenv import load_dotenv

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

cursor = conn.cursor()

# Query to list all tables in the public schema
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public';
""")

tables = cursor.fetchall()

print("Tables in the public schema:")
for table in tables:
    print(table[0])

cursor.close()
conn.close()
