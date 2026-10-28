import urllib.request
import urllib.parse
import json
import csv
import sqlite3
import io
import time

conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()

# --- SETUP TABLES ---
# 1. Spatial (Untuk Peta)
c.execute('''CREATE TABLE IF NOT EXISTS real_projects (
    id TEXT PRIMARY KEY, name TEXT, type TEXT, lat REAL, lon REAL
)''')
# 2. MIDA (Agregat)
c.execute('''CREATE TABLE IF NOT EXISTS mida_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT, state TEXT, projects INTEGER, investment REAL
)''')
# 3. IPI (Trend)
c.execute('''CREATE TABLE IF NOT EXISTS ipi_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, sector TEXT, ipi_index REAL
)''')

# Clear old data
c.execute("DELETE FROM real_projects")
c.execute("DELETE FROM mida_stats")
c.execute("DELETE FROM ipi_stats")

HEADERS = {'User-Agent': 'Mozilla/5.0 (Termux; AtrricBot)'}

def fetch_url(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

# ==========================================
# 1. PEERINGDB (DATA CENTERS - SPATIAL)
# ==========================================
print("⏳ Fetching Data Centers (PeeringDB)...")
try:
    data = json.loads(fetch_url('https://peeringdb.com/api/fac?country=MY').decode('utf-8'))
    count = 0
    for fac in data.get('data', []):
        if fac.get('latitude') and fac.get('longitude'):
            c.execute("INSERT OR REPLACE INTO real_projects (id, name, type, lat, lon) VALUES (?, ?, ?, ?, ?)",
                      (f"dc_{fac['id']}", fac['name'], "Data Center", fac['latitude'], fac['longitude']))
            count += 1
    print(f"✅ {count} Data Centers dimasukkan.")
except Exception as e:
    print(f"❌ PeeringDB Error: {e}")

# ==========================================
# 2. MIDA (AGREGAT - CSV)
# ==========================================
print("\n⏳ Fetching MIDA Data...")
try:
    # URL direct ke fail CSV yang kau jumpa semalam (2017-2019)
    # Nota: Kalau URL ni rosak, kau kena copy link CSV dari page archive tu
    csv_url = "https://storage.data.gov.my/datastore/mida/manufacturing-projects-approved-by-state.csv"
    content = fetch_url(csv_url).decode('utf-8', errors='ignore')
    
    reader = csv.DictReader(io.StringIO(content))
    count = 0
    for row in reader:
        # Cari nama negeri (biasanya column 'state' atau 'negeri')
        state = row.get('state') or row.get('State') or row.get('Negeri') or 'Unknown'
        # Cari bilangan projek (mungkin 'projects' atau 'bilangan')
        proj = row.get('projects') or row.get('Projects') or 0
        # Cari nilai pelaburan (mungkin 'investment' atau 'nilai')
        inv = row.get('investment') or row.get('Investment') or 0.0
        
        try:
            c.execute("INSERT INTO mida_stats (state, projects, investment) VALUES (?, ?, ?)",
                      (state, int(float(proj)), float(inv)))
            count += 1
        except:
            pass
    print(f"✅ {count} rekod MIDA dimasukkan.")
except Exception as e:
    print(f"❌ MIDA Error: {e}")

# ==========================================
# 3. OPENDOSM / IPI (TREND - JSON)
# ==========================================
print("\n⏳ Fetching OpenDOSM IPI Data...")
try:
    # API OpenDOSM untuk Industrial Production Index
    api_url = "https://api.data.gov.my/data-catalogue?id=ipi&limit=20"
    data = json.loads(fetch_url(api_url).decode('utf-8'))
    
    count = 0
    for row in data:
        # Data IPI ada date, sector, index
        date = row.get('date', '')
        sector = row.get('sector', 'Overall')
        idx = row.get('index', 0.0)
        
        if date and idx:
            c.execute("INSERT INTO ipi_stats (date, sector, ipi_index) VALUES (?, ?, ?)",
                      (date, sector, float(idx)))
            count += 1
    print(f"✅ {count} rekod IPI dimasukkan.")
except Exception as e:
    print(f"❌ OpenDOSM Error: {e}")

conn.commit()
conn.close()
print("\n🎯 SEMUA DATA SIAP.")