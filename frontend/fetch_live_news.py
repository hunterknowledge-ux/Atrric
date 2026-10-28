import urllib.request
import sqlite3
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re
import html

conn = sqlite3.connect('spatial_cache.db')
c = conn.cursor()

# Drop table lama (sebab kita tambah column description)
c.execute('DROP TABLE IF EXISTS live_news')

# Buat table baru
c.execute('''CREATE TABLE live_news (
    id TEXT PRIMARY KEY, 
    title TEXT, 
    link TEXT, 
    source TEXT, 
    country TEXT,
    lat REAL, 
    lon REAL, 
    date TEXT,
    description TEXT
)''')

print("⏳ Fetching Global News from RSS Feeds...")

feeds = [
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "name": "BBC World", "country": "UK", "lat": 51.5074, "lon": -0.1278},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "name": "Al Jazeera", "country": "Qatar", "lat": 25.2854, "lon": 51.5310},
    {"url": "https://news.google.com/rss/search?q=China+geopolitics&hl=en-MY&gl=MY&ceid=MY:en", "name": "Google News", "country": "China", "lat": 39.9042, "lon": 116.4074},
    {"url": "https://news.google.com/rss/search?q=Russia+geopolitics&hl=en-MY&gl=MY&ceid=MY:en", "name": "Google News", "country": "Russia", "lat": 55.7558, "lon": 37.6173},
    {"url": "https://news.google.com/rss/search?q=USA+geopolitics&hl=en-MY&gl=MY&ceid=MY:en", "name": "Google News", "country": "USA", "lat": 38.9072, "lon": -77.0369},
    {"url": "https://www.malaymail.com/feed/rss/malaysia", "name": "Malay Mail", "country": "Malaysia", "lat": 3.1390, "lon": 101.6869},
    {"url": "https://news.google.com/rss/search?q=Malaysia+economy&hl=en-MY&gl=MY&ceid=MY:en", "name": "Google News", "country": "Malaysia", "lat": 3.1390, "lon": 101.6869}
]

def clean_html(raw_html):
    if not raw_html: return ""
    # Buang tag HTML
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    # Tukar karakter HTML entity (&amp; -> &)
    return html.unescape(cleantext).strip()

count = 0
for f in feeds:
    try:
        req = urllib.request.Request(f["url"], headers={'User-Agent': 'Mozilla/5.0 (Termux; AtrricBot)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text or "No Title"
                link = item.find('link').text or ""
                
                # Ambil description
                desc_tag = item.find('description')
                description = clean_html(desc_tag.text) if desc_tag is not None else "No description available."
                
                pub_date_str = item.find('pubDate').text
                try:
                    dt = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                    date = dt.strftime('%Y%m%d')
                except:
                    date = datetime.now().strftime('%Y%m%d')
                
                c.execute("INSERT OR REPLACE INTO live_news (id, title, link, source, country, lat, lon, date, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          (link, title, link, f["name"], f["country"], f["lat"], f["lon"], date, description))
                count += 1
    except Exception as e:
        print(f"❌ Error fetching {f['name']}: {e}")
    
    time.sleep(1)

seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
c.execute("DELETE FROM live_news WHERE date < ?", (seven_days_ago,))

conn.commit()
conn.close()
print(f"✅ {count} berita global dimasukkan (dengan description).")