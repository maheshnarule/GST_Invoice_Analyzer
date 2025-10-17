
import sqlite3
from pathlib import Path

# Define the path for database
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

# Create connection
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create the 'users' table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    aadhaar_number TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    user_type TEXT DEFAULT 'CA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    item_name TEXT NOT NULL,
    hsn_code TEXT NOT NULL,
    rate_of_gst REAL NOT NULL
)
""")


conn.commit()
conn.close()

print(f"✅ SQLite database created at: {DB_PATH}")
print("✅ Tables 'users' and 'items' created successfully.")
