import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()

# Function to establish and return a database connection
def get_connection():
    
    try:
        # Attempt to establish a connection to the database
        conn=psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        
        print("Database connection established")
        return conn
    
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

