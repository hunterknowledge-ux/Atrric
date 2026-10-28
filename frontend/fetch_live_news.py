import urllib.request
import urllib.parse
import json
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()

# 1. Table Berita Live (TTL 7 hari)
c.execute('''CREATE TABLE IF NOT EXISTS live_news (
    id TEXT PRIMARY KEY, title TEXT, link TEXT, source_country TEXT, lat REAL, lon REAL, date TEXT
)''')

print("⏳ Fetching Global News from GDELT...")

# 3. Query GDELT (Malaysia + Global Powers)
queries = [
    {"q": "(sourcecountry:MY) Malaysia", "lat": 3.1390, "lon": 101.6869, "country": "MY"},
    {"q": "(sourcecountry:CN) China", "lat": 35.8617, "lon": 104.1954, "country": "CN"},
    {"q": "(sourcecountry:RU) Russia", "lat": 61.5240, "lon": 105.3188, "country": "RU"},
    {"q": "(sourcecountry:US) United States", "lat": 37.0902, "lon": -95.7129, "country": "US"}
]

count = 0
for q_obj in queries:
    encoded_q = urllib.parse.quote(q_obj["q"])
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_q}&mode=artlist&maxrecords=15&format=json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AtrricBot'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            for article in data.get('articles', []):
                title = article.get('title')
                link = article.get('url')
                date_str = article.get('seendate', '')[:8] # YYYYMMDD
                
                c.execute("INSERT OR REPLACE INTO live_news (id, title, link, source_country, lat, lon, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (link, title, link, q_obj["country"], q_obj["lat"], q_obj["lon"], date_str))
                count += 1
    except Exception as e:
        print(f"❌ GDELT Error ({q_obj['country']}): {e}")

# 4. Buang berita > 7 hari
seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
c.execute("DELETE FROM live_news WHERE date < ?", (seven_days_ago,))

conn.commit()
conn.close()
print(f"✅ {count} berita global dimasukkan. Data lama dibuang.")