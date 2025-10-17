import sqlite3
import pandas as pd

# Path to your CSV
CSV_FILE = "data\items.csv"   # rename if needed

# Connect to SQLite
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Read CSV
df = pd.read_csv(CSV_FILE)

# Normalize column names
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

# Insert data
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO items (hsn_code, category, item_name, rate_of_gst)
        VALUES (?, ?, ?, ?)
    """, (row['hsn_code'], row['category'], row['item_name'], row['rate_of_gst']))

conn.commit()
conn.close()

print("✅ CSV data successfully inserted into database.db")
