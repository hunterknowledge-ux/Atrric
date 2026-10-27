import urllib.request
import urllib.parse
import json
import csv
import sqlite3
import io
import time
import random

# Setup SQLite
conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS real_projects (
    id TEXT PRIMARY KEY, name TEXT, type TEXT, lat REAL, lon REAL
)''')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Termux; AtrricBot)'}

def fetch_url(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def ckan_package_show(pkg_id):
    url = f"https://archive.data.gov.my/api/3/action/package_show?id={pkg_id}"
    return json.loads(fetch_url(url).decode('utf-8')).get('result', {})

def download_csv(url):
    return fetch_url(url).decode('utf-8', errors='ignore')

# ==========================================
# 1. PEERINGDB: DATA CENTERS (LIVE API)
# ==========================================
print(" Fetching Data Centers from PeeringDB API...")
try:
    data = json.loads(fetch_url('https://peeringdb.com/api/fac?country=MY').decode('utf-8'))
    count_dc = 0
    for fac in data.get('data', []):
        name = fac.get('name', 'Unknown DC')
        lat = fac.get('latitude')
        lon = fac.get('longitude')
        if lat and lon:
            c.execute("INSERT OR REPLACE INTO real_projects (id, name, type, lat, lon) VALUES (?, ?, ?, ?, ?)",
                      (f"dc_{fac['id']}", name, "Data Center", lat, lon))
            count_dc += 1
    print(f" PeeringDB: {count_dc} Data Centers dimasukkan.")
except Exception as e:
    print(f" PeeringDB Error: {e}")

# ==========================================
# 2. MIDA: MANUFACTURING PROJECTS BY STATE
# ==========================================
print("\n Fetching MIDA Manufacturing Projects...")
try:
    pkg = ckan_package_show('manufacturing-projects-approved-by-state')
    for res in pkg.get('resources', []):
        if res.get('format', '').upper() == 'CSV':
            csv_url = res.get('url')
            print(f" Downloading: {csv_url}")
            content = download_csv(csv_url)
            reader = csv.DictReader(io.StringIO(content))
            print(f" Headers: {reader.fieldnames}")
            
            # Koordinat Ibu Negeri (untuk letak titik projek)
            STATE_COORDS = {
                'JOHOR': (1.4927, 103.7414), 'KEDAH': (6.1184, 100.3685),
                'KELANTAN': (6.1254, 102.2381), 'MELAKA': (2.1896, 102.2501),
                'NEGERI SEMBILAN': (2.7258, 101.9424), 'PAHANG': (3.8077, 103.3260),
                'PERAK': (4.5975, 101.0901), 'PERLIS': (6.4449, 100.2048),
                'PULAU PINANG': (5.4141, 100.3288), 'SABAH': (5.9804, 116.0735),
                'SARAWAK': (1.5533, 110.3592), 'SELANGOR': (3.0738, 101.5183),
                'TERENGGANU': (5.3302, 103.1408), 'KUALA LUMPUR': (3.1390, 101.6869),
                'LABUAN': (5.2833, 115.2333), 'PUTRAJAYA': (2.9264, 101.6964),
            }
            
            count_mida = 0
            for i, row in enumerate(reader):
                state = row.get('State') or row.get('state') or row.get('Negeri') or ''
                state_key = state.upper().strip()
                if state_key in STATE_COORDS:
                    lat, lon = STATE_COORDS[state_key]
                    # Random offset supaya titik tak bertindih
                    lat += (random.random() - 0.5) * 0.1
                    lon += (random.random() - 0.5) * 0.1
                    proj_name = f"MIDA Project - {state_key}"
                    c.execute("INSERT OR REPLACE INTO real_projects (id, name, type, lat, lon) VALUES (?, ?, ?, ?, ?)",
                              (f"mida_{i}", proj_name, "Industrial Zone", lat, lon))
                    count_mida += 1
            print(f" MIDA: {count_mida} projek perkilangan dimasukkan.")
            break
except Exception as e:
    print(f" MIDA Error: {e}")

# ==========================================
# 3. PERAK: SENARAI KILANG (FACTORY LIST)
# ==========================================
print("\n Fetching Perak Factory List...")
try:
    pkg = ckan_package_show('kawasan-kilang-di-negeri-perak')
    for res in pkg.get('resources', []):
        if res.get('format', '').upper() == 'CSV':
            csv_url = res.get('url')
            print(f" Downloading: {csv_url}")
            content = download_csv(csv_url)
            reader = csv.DictReader(io.StringIO(content))
            print(f" Headers: {reader.fieldnames}")
            
            base_lat, base_lon = 4.5975, 101.0901 # Perak centroid
            count_perak = 0
            for i, row in enumerate(reader):
                name = row.get('Nama Kilang') or row.get('Name') or row.get('nama_kilang') or f"Factory {i}"
                address = row.get('Alamat') or row.get('Address') or row.get('alamat') or ''
                
                lat, lon = base_lat, base_lon
                # Geocode guna Nominatim (slow, rate limit 1/sec)
                if address:
                    try:
                        geo_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(address + ', Perak, Malaysia')}&format=json&limit=1"
                        geo_data = json.loads(fetch_url(geo_url, timeout=10).decode('utf-8'))
                        if geo_data:
                            lat = float(geo_data[0]['lat'])
                            lon = float(geo_data[0]['lon'])
                        time.sleep(1) # Nominatim rate limit
                    except Exception:
                        pass
                
                c.execute("INSERT OR REPLACE INTO real_projects (id, name, type, lat, lon) VALUES (?, ?, ?, ?, ?)",
                          (f"perak_{i}", name, "Factory", lat, lon))
                count_perak += 1
            print(f" Perak: {count_perak} kilang dimasukkan.")
            break
except Exception as e:
    print(f" Perak Error: {e}")

conn.commit()
conn.close()
print("\n SEMUA DATA SIAP DIMASUKKAN KE SQLITE.")