import urllib.request
import json
import sqlite3
import csv
import io
import random

conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Termux; AtrricBot)'}

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

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

print("⏳ Mencari dataset MIDA di archive.data.gov.my...")

try:
    # LANGKAH 1: Cari dataset guna package_search (bukan package_show)
    search_url = "https://archive.data.gov.my/api/3/action/package_search?q=MANUFACTURING+PROJECTS+APPROVED+BY+STATE"
    search_data = json.loads(fetch_url(search_url).decode('utf-8'))
    
    if not search_data['success'] or not search_data['result']['results']:
        raise Exception("Dataset tak jumpa dalam carian.")
    
    # Ambil dataset pertama yang paling relevan
    dataset = search_data['result']['results'][0]
    dataset_id = dataset['id']
    print(f"📌 Jumpa dataset: {dataset['title']} (ID: {dataset_id})")
    
    # LANGKAH 2: Guna package_show dengan ID yang betul untuk dapatkan senarai fail
    show_url = f"https://archive.data.gov.my/api/3/action/package_show?id={dataset_id}"
    show_data = json.loads(fetch_url(show_url).decode('utf-8'))
    
    # Cari fail CSV dalam resources
    csv_url = None
    for res in show_data['result']['resources']:
        if res.get('format', '').upper() == 'CSV':
            csv_url = res.get('url')
            break
    
    if not csv_url:
        raise Exception("Dataset ni takde fail CSV.")
    
    print(f"📥 Downloading CSV dari: {csv_url}")
    content = fetch_url(csv_url).decode('utf-8', errors='ignore')
    
    # LANGKAH 3: Baca CSV dan masukkan ke SQLite
    reader = csv.DictReader(io.StringIO(content))
    print(f"📋 Kolum: {reader.fieldnames}")
    
    count = 0
    for i, row in enumerate(reader):
        # Cari kolum negeri (nama mungkin 'State', 'state', 'Negeri', dll)
        state_val = ''
        for key in row.keys():
            if key and ('state' in key.lower() or 'negeri' in key.lower()):
                state_val = row[key]
                break
        
        if not state_val:
            continue
        
        # Padankan dengan koordinat
        for k, (lat, lon) in STATE_COORDS.items():
            if k.lower() in state_val.lower():
                # Offset sikit supaya tak bertindih
                lat += (random.random() - 0.5) * 0.15
                lon += (random.random() - 0.5) * 0.15
                
                proj_name = f"MIDA Project - {state_val}"
                c.execute("INSERT OR REPLACE INTO real_projects (id, name, type, lat, lon) VALUES (?, ?, ?, ?, ?)",
                          (f"mida_{i}", proj_name, "Industrial Zone", lat, lon))
                count += 1
                break
    
    print(f"✅ MIDA: {count} projek dimasukkan.")
    
except Exception as e:
    print(f"❌ Error: {e}")

conn.commit()
conn.close()
print("🎯 Siap!")