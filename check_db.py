import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
dsn = os.getenv("DATABASE_URL")
print("DSN:", dsn)

with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database();")
        print("DB:", cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM word;")
        print("Words:", cur.fetchone()[0])