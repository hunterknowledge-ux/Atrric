import urllib.request
import json
import sqlite3

conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Termux; AtrricBot)'}

def fetch_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

# Koordinat Ibu Negeri (untuk letak projek MIDA)
STATE_COORDS = {
    'Johor': (1.4927, 103.7414), 'Kedah': (6.1184, 100.3685),
    'Kelantan': (6.1254, 102.2381), 'Melaka': (2.1896, 102.2501),
    'Negeri Sembilan': (2.7258, 101.9424), 'Pahang': (3.8077, 103.3260),
    'Perak': (4.5975, 101.0901), 'Perlis': (6.4449, 100.2048),
    'Pulau Pinang': (5.4141, 100.3288), 'Sabah': (5.9804, 116.0735),
    'Sarawak': (1.5533, 110.3592), 'Selangor': (3.0738, 101.5183),
    'Terengganu': (5.3302, 103.1408), 'W.P. Kuala Lumpur': (3.1390, 101.6869),
    'W.P. Labuan': (5.2833, 115.2333), 'W.P. Putrajaya': (2.9264, 101.6964),
}

# ==========================================
# 1. MIDA: MANUFACTURING PROJECTS (VIA API BARU)
# ==========================================
print("⏳ Fetching MIDA Data from api.data.gov.my...")
try:
    # API rasmi data.gov.my untuk projek pembuatan
    url = "https://api.data.gov.my/data-catalogue?id=manufacturing_projects"
    data = json.loads(fetch_url(url).decode('utf-8'))
    
    count_mida = 0
    # Data ni berbentuk list of dictionaries
    for row in data:
        state = row.get('state', '')
        if state in STATE_COORDS:
            lat, lon = STATE_COORDS[state]
            
            # Kita cipta nama projek dari data MIDA
            proj_name = f"MIDA Project ({state}) - {row.get('type', 'Manufacturing')}"
            
            c.execute("INSERT OR REPLACE INTO real_projects (id, name, type, lat, lon) VALUES (?, ?, ?, ?, ?)",
                      (f"mida_{count_mida}", proj_name, "Industrial Zone", lat, lon))
            count_mida += 1
            
    print(f" MIDA API: {count_mida} projek perkilangan dimasukkan.")
except Exception as e:
    print(f" MIDA Error: {e}")

conn.commit()
conn.close()
print(" Siap!")