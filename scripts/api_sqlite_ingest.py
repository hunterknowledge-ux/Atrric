import json
import os
import sqlite3
import subprocess


def fetch_api_data_curl(url):
    print(f"Fetching data via curl: {url}")
    try:
        # Guna curl (ikut redirect -L) dan ambil output
        result = subprocess.run(
            ["curl", "-sL", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Curl error: {result.stderr}")
            return None
            
        if not result.stdout.strip():
            print("Curl return empty response.")
            return None

        data = json.loads(result.stdout)
        return data
    except json.JSONDecodeError:
        print("Response bukan JSON. Mungkin kena block atau rate limit.")
        print(f"Response preview: {result.stdout[:200]}")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def ingest_to_sqlite(data, db_file, table_name):
    if not data:
        print("Tiada data untuk dimasukkan.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        first_row = data[0]
        columns = list(first_row.keys())
        
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cols_def = ", ".join([f'"{col}" TEXT' for col in columns])
        cursor.execute(f"CREATE TABLE {table_name} ({cols_def})")

        placeholders = ", ".join(["?" for _ in columns])
        insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"

        count = 0
        for row in data:
            values = [str(row.get(col, "")) for col in columns]
            cursor.execute(insert_query, values)
            count += 1

        conn.commit()
        print(f"SUCCESS: {count} baris dimasukkan ke table '{table_name}'")

    except Exception as e:
        print(f"ERROR SQLite: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    API_URL = "https://api.data.gov.my/data-catalogue/?id=population_district&limit=5000"
    
    DB_PATH = "raw_data/spatial/atrric_macro.db"
    TABLE_NAME = "population_district"

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    print("=== ATRRIC SPATIAL INGEST (CURL MODE) ===")
    data = fetch_api_data_curl(API_URL)
    
    if data:
        print(f"Berjaya tarik {len(data)} baris dari API.")
        ingest_to_sqlite(data, DB_PATH, TABLE_NAME)
    else:
        print("Gagal tarik data. Sila semak sambungan internet atau URL API.")