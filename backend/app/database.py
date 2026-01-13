import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def close_db_connection(conn):
    """Close database connection"""
    if conn:
        conn.close()
