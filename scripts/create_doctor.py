import os
import sys
import psycopg2
import logging

# Add the project's root directory to the Python path
# This allows us to import from the 'src' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.auth.security import hash_password

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_doctor_account():
    """
    Connects to the database and inserts a new doctor with a hashed password.
    """
    # --- Define the new doctor's details ---
    username = "iyang.thomas"
    # In a real app, this would come from a secure input, not be hardcoded.
    plain_password = "password123" 
    full_name = "Dr. Iyang Thomas"
    role = "clinician"

    logging.info(f"Preparing to create account for {full_name} ({username})...")

    # --- Securely hash the password ---
    hashed_pass = hash_password(plain_password)
    logging.info("Password has been securely hashed.")

    # --- Connect to the database and insert the record ---
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER", "rag_user"),
            password=os.getenv("DB_PASSWORD", "password123"),
            dbname=os.getenv("DB_NAME", "rag_db")
        )
        with conn.cursor() as cur:
            # Use ON CONFLICT to prevent errors if you run the script more than once
            cur.execute(
                """
                INSERT INTO doctors (username, hashed_password, full_name, role)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING;
                """,
                (username, hashed_pass, full_name, role)
            )
        conn.commit()
        logging.info(f"Successfully created or verified account for {username}.")

    except Exception as e:
        logging.error(f"Failed to create doctor account: {e}")
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

if __name__ == "__main__":
    create_doctor_account()