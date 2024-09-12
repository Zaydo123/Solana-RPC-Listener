from dotenv import find_dotenv, load_dotenv
import psycopg2
import os

load_dotenv(find_dotenv(".env"))


""" 
    Connection string for PostgreSQL
"""

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
SSL_MODE = os.getenv("POSTGRES_SSL_MODE")

CONN_STRING = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if SSL_MODE:
    CONN_STRING += f"?sslmode={SSL_MODE}"


"""
Setup:
    create tables if they don't exist - timescale
"""

def check_table_exists(table_name: str) -> bool:
    with psycopg2.connect(CONN_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}');")
            fetched=cur.fetchone()
            if fetched and fetched[0]:
                return True
            else:
                return False

def create_tables():
    with open("sql/CREATE_TABLES.SQL", "r") as file:
        sql = file.read()

    with psycopg2.connect(CONN_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()

        
if __name__ == "__main__":
    if not check_table_exists("Token"):
        print("Creating tables...")
        create_tables()
