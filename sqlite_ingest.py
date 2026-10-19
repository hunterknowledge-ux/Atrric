import sqlite3
import csv
import os
import sys

# Naikkan had field CSV sebab fail DOSM ni besar
csv.field_size_limit(sys.maxsize)

def ingest_csv_to_sqlite(csv_file, db_file, table_name):
    if not os.path.exists(csv_file):
        print(f"ERROR: File {csv_file} tak wujud. Pastikan kau dah pindahkan fail tu.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # Bersihkan nama column (buang space, tukar ke lowercase)
            clean_headers = [h.replace(' ', '_').replace('-', '_').lower() for h in headers]
            
            # Cipta table
            cols_def = ", ".join([f'"{h}" TEXT' for h in clean_headers])
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(f"CREATE TABLE {table_name} ({cols_def})")

            # Masukkan data
            placeholders = ", ".join(["?" for _ in clean_headers])
            insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"

            count = 0
            for row in reader:
                cursor.execute(insert_query, row)
                count += 1

        conn.commit()
        print(f"SUCCESS: {count} baris data dimasukkan ke table '{table_name}' dalam {db_file}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    csv_path = "raw_data/spatial/population.csv"
    db_path = "raw_data/spatial/atrric_macro.db"
    table = "population_data"
    
    print("=== ATRRIC CSV INGEST ===")
    print(f"Memproses {csv_path}...")
    ingest_csv_to_sqlite(csv_path, db_path, table)