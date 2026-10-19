import urllib.request
import json
import sqlite3
import os

def fetch_api_data(url):
    print(f"Fetching data dari API: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"ERROR fetch API: {e}")
        return None

def ingest_to_sqlite(data, db_file, table_name):
    if not data:
        print("Tiada data untuk dimasukkan.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        # Ambil keys dari data pertama untuk buat kolum
        first_row = data[0]
        columns = list(first_row.keys())
        
        # Buat table (drop dulu kalau dah ada)
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cols_def = ", ".join([f'"{col}" TEXT' for col in columns])
        cursor.execute(f"CREATE TABLE {table_name} ({cols_def})")

        # Masukkan data
        placeholders = ", ".join(["?" for _ in columns])
        insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"

        count = 0
        for row in data:
            # Tukar semua value ke string (SQLite TEXT)
            values = [str(row.get(col, "")) for col in columns]
            cursor.execute(insert_query, values)
            count += 1

        conn.commit()
        print(f"SUCCESS: {count} baris dimasukkan ke table '{table_name}' dalam {db_file}")

    except Exception as e:
        print(f"ERROR SQLite: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # URL API OpenDOSM untuk data populasi daerah
    # Limit=5000 untuk ambil banyak data (boleh adjust ikut keperluan)
    API_URL = "https://api.data.gov.my/opendosm?id=population_district&limit=5000"
    
    DB_PATH = "raw_data/spatial/atrric_macro.db"
    TABLE_NAME = "population_district"

    # Pastikan folder wujud
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    print("=== ATRRIC SPATIAL INGEST (API MODE) ===")
    data = fetch_api_data(API_URL)
    
    if data:
        print(f"Berjaya tarik {len(data)} baris dari API.")
        ingest_to_sqlite(data, DB_PATH, TABLE_NAME)
    else:
        print("Gagal tarik data. Sila semak sambungan internet atau URL API.")