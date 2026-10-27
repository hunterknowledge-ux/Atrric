import sqlite3
import csv
import random

conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()

# Buat table untuk CIDB
c.execute('''CREATE TABLE IF NOT EXISTS cidb_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    company TEXT,
    state TEXT,
    lat REAL,
    lon REAL
)''')

# Koordinat Ibu Negeri (Untuk letak titik atas peta)
STATE_COORDS = {
    'SELANGOR': (3.0738, 101.5183),
    'KUALA LUMPUR': (3.1390, 101.6869),
    'JOHOR': (1.4927, 103.7414),
    'PULAU PINANG': (5.4141, 100.3288),
    'PERAK': (4.5975, 101.0901),
    'SABAH': (5.9804, 116.0735),
    'SARAWAK': (1.5533, 110.3592),
    'PAHANG': (3.8077, 103.3260),
    'KEDAH': (6.1184, 100.3685),
    'KELANTAN': (6.1254, 102.2381),
    'TERENGGANU': (5.3302, 103.1408),
    'NEGERI SEMBILAN': (2.7258, 101.9424),
    'MELAKA': (2.1896, 102.2501),
    'PERLIS': (6.4449, 100.2048)
}

print("⏳ Membaca data CIDB...")

count = 0
with open('cidb_projects.csv', 'r', encoding='utf-8', errors='ignore') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Ambil nama projek (column name mungkin berbeza, kita try beberapa)
        name = row.get('Project Name') or row.get('project_name') or row.get('Nama Projek') or 'UNNAMED PROJECT'
        company = row.get('Company') or row.get('company') or row.get('Syarikat') or 'UNKNOWN'
        state = row.get('State') or row.get('state') or row.get('Negeri') or 'UNKNOWN'
        
        state_key = state.upper().strip()
        coords = STATE_COORDS.get(state_key)
        
        if coords:
            # Tambah sedikit random offset supaya titik tak bertindih sangat
            lat = coords[0] + (random.random() - 0.5) * 0.1
            lon = coords[1] + (random.random() - 0.5) * 0.1
            
            c.execute("INSERT INTO cidb_projects (project_name, company, state, lat, lon) VALUES (?, ?, ?, ?, ?)",
                      (name, company, state, lat, lon))
            count += 1

conn.commit()
conn.close()
print(f"✅ Siap! {count} projek CIDB berjaya dimasukkan ke SQLite.")