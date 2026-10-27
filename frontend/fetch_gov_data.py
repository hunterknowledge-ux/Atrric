import urllib.request
import json
import sqlite3
import csv
import io

conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Termux; AtrricBot)'}

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

# Koordinat Ibu Negeri
STATE_COORDS = {
    'Johor': (1.4927, 103.7414), 'Kedah': (6.1184, 100.3685),
    'Kelantan': (6.1254, 102.2381), 'Melaka': (2.1896, 102.2501),
    'Negeri Sembilan': (2.7258, 101.9424), 'Pahang': (3.8077, 103.3260),
    'Perak': (4.5975, 101.0901), 'Perlis': (6.4449, 100.2048),
    'Pulau Pinang': (5.4141, 100.3288), 'Sabah': (5.9804, 116.0735),
    'Sarawak': (1.5533, 110.3592), 'Selangor': (3.0738, 101.5183),
    'Terengganu': (5.3302, 103.1408), 'Kuala Lumpur': (3.1390, 101.6869),
    'Labuan': (5.2833, 115.2333), 'Putrajaya': (2.9264, 101.6964),
}

print("⏳ Fetching MIDA Data (CKAN API)...")

try:
    # 1. Cari dataset ID melalui CKAN API
    ckan_url = "https://archive.data.gov.my/api/3/action/package_search?q=manufacturing+projects+approved+by+state"
    search_data = json.loads(fetch_url(ckan_url).decode('utf-8'))
    
    if not search_data['success'] or not search_data['result']['results']:
        raise Exception("Dataset tidak dijumpai dalam carian CKAN.")
        
    dataset = search_data['result']['results'][0]
    print(f"📌 Jumpa dataset: {dataset['title']}")
    
    # 2. Cari fail CSV dalam dataset tu
    csv_url = None
    for res in dataset['resources']:
        if res['format'].upper() == 'CSV':
            csv_url = res['url']
            break
            
    if not csv_url:
        raise Exception("Tiada fail CSV dalam dataset ni.")
        
    print(f"📥 Downloading CSV...")
    content = fetch_url(csv_url).decode('utf-8', errors='ignore')
    
    # 3. Baca dan masukkan ke SQLite
    reader = csv.DictReader(io.StringIO(content))
    print(f"📋 Kolum dijumpai: {reader.fieldnames}")
    
    count = 0
    for i, row in enumerate(reader):
        # Cari kolum negeri (nama mungkin berbeza)
        state = row.get('State') or row.get('state') or row.get('Negeri') or ''
        state_key = state.strip()
        
        # Padankan dengan koordinat (case-insensitive)
        for k in STATE_COORDS:
            if k.lower() in state_key.lower():
                lat, lon = STATE_COORDS[k]
                # Offset kecil supaya tak bertindih
                import random
                lat += (random.random() - 0.5) * 0.1
                lon += (random.random() - 0.5) * 0.1
                
                proj_name = f"MIDA Project - {state_key}"
                c.execute("INSERT OR REPLACE INTO real_projects (id, name, type, lat, lon) VALUES (?, ?, ?, ?, ?)",
                          (f"mida_{i}", proj_name, "Industrial Zone", lat, lon))
                count += 1
                break
                
    print(f" MIDA: {count} projek perkilangan dimasukkan.")
    
except Exception as e:
    print(f" MIDA Error: {e}")

conn.commit()
conn.close()
print(" Siap!")