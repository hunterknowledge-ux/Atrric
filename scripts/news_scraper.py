import os
import sqlite3
import time
from datetime import datetime

import feedparser
import trafilatura

RSS_FEEDS = {
    "Global": [
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
    ],
    "National": [
        "https://www.freemalaysiatoday.com/category/nation/feed/",
        "https://www.malaymail.com/feed/rss/malaysia"
    ]
}

# EXPERT DICTIONARY
GLOBAL_ENTITIES = ["federal reserve", "fed rate", "us-china", "semiconductor", "ai", "tech layoff", "global inflation", "oil price", "recession", "interest rate"]
NATIONAL_ENTITIES = ["anwar ibrahim", "rafizi ramli", "subsidi", "opr", "ringgit", "belanjawan", "ptptn", "kwsp", "epf", "gaji", "sst", "gst", "harga", "pengangguran", "malaysia"]
GENZ_ENTITIES = ["gen z", "b40", "m40", "fresh grad", "pengangguran", "kos sara hidup", "rumah", "grab", "foodpanda", "belia", "mahasiswa"]

DB_PATH = "raw_data/news/atrric_news.db"

def setup_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            published_date TEXT,
            content TEXT,
            source TEXT,
            level TEXT,
            matched_tags TEXT
        )
    """)
    conn.commit()
    return conn

import re  # Pastikan import re ada di atas sekali


def analyze_relevance(text):
    text_lower = text.lower()
    tags = []
    
    # Guna regex \b untuk cari perkataan tepat (bukan sebahagian dari perkataan lain)
    for entity in GLOBAL_ENTITIES:
        if re.search(rf'\b{re.escape(entity)}\b', text_lower): tags.append(f"G:{entity}")
            
    for entity in NATIONAL_ENTITIES:
        if re.search(rf'\b{re.escape(entity)}\b', text_lower): tags.append(f"N:{entity}")
            
    for entity in GENZ_ENTITIES:
        if re.search(rf'\b{re.escape(entity)}\b', text_lower): tags.append(f"Z:{entity}")
            
    if len(tags) > 0:
        return ", ".join(tags)
    return None
def scrape_news():
    conn = setup_db()
    cursor = conn.cursor()
    
    for level, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            print(f"\n--- Scraping [{level}]: {feed_url} ---")
            feed = feedparser.parse(feed_url)
            source_name = feed_url.split('/')[2]
            
            # Ambil 15 berita terkini per portal
            for entry in feed.entries[:15]: 
                title = entry.title
                url = entry.link
                pub_date = entry.get('published', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                # Check duplicate
                cursor.execute("SELECT 1 FROM news WHERE url = ?", (url,))
                if cursor.fetchone():
                    continue
                    
                try:
                    # Tarik dan cuci teks berita
                    downloaded = trafilatura.fetch_url(url)
                    content = trafilatura.extract(downloaded)
                    
                    if not content:
                        content = entry.get('summary', '')
                        
                    # Tapis guna kamus
                    matched_tags = analyze_relevance(title + " " + content)
                    
                    if not matched_tags:
                        continue 
                        
                    print(f"  [MATCH!] {title[:50]}... | Tags: {matched_tags[:50]}")
                    
                    # Masukkan ke SQLite
                    cursor.execute("""
                        INSERT INTO news (title, url, published_date, content, source, level, matched_tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (title, url, pub_date, content, source_name, level, matched_tags))
                    conn.commit()
                    time.sleep(1) # Jeda 1 saat
                    
                except Exception:
                    pass
                
    conn.close()
    print("\nSelesai scrape berita (Expert Mode).")

if __name__ == "__main__":
    scrape_news()
