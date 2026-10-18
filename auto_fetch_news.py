"""
auto_fetch_news.py — Auto-fetch news RSS untuk ATRRIC.

Tarik berita dari sumber RSS Malaysia, tapis guna Gatekeeper 
(Entity + Topic keywords), dan simpan ke raw_data/news/YYYY-MM-DD/ 
berdasarkan TARIKH TERBIT artikel.

Guna:
    python auto_fetch_news.py
"""

import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import feedparser

# ==========================================
# KONFIGURASI
# ==========================================

# Senarai RSS Sumber
RSS_FEEDS: Dict[str, str] = {
    "fmt": "https://www.freemalaysiatoday.com/feed/",
    "bernama": "https://www.bernama.com/rss/en/news.php",
    "sinarharian": "https://www.sinarharian.com.my/rss/national",
    "malaymail": "https://www.malaymail.com/feed",
}

# Gatekeeper Keywords
ENTITY_KEYWORDS: List[str] = [
    "gen z", "belia", "pelajar", "graduan", "fresh grad", 
    "anak muda", "universiti", "sekolah", "remaja", "ipt"
]

TOPIC_KEYWORDS: List[str] = [
    "pendidikan", "ekonomi", "kerja", "gaji", "sara hidup", 
    "harga barang", "mental health", "silibus", "ptptn", 
    "pengangguran", "gig", "part time"
]

# Path Setup
ROOT_DIR = Path(__file__).parent
RAW_NEWS_DIR = ROOT_DIR / "raw_data" / "news"


# ==========================================
# FUNGSI TERAS
# ==========================================

def matches_gatekeeper(title: str) -> bool:
    """
    Tapis tajuk. Mesti ada sekurang-kurangnya 1 Entity DAN 1 Topic.
    """
    title_lower = title.lower()
    has_entity = any(kw in title_lower for kw in ENTITY_KEYWORDS)
    has_topic = any(kw in title_lower for kw in TOPIC_KEYWORDS)
    return has_entity and has_topic


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Tukar tajuk berita jadi nama fail yang selamat (buang simbol pelik)."""
    safe = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip().lower()
    safe = re.sub(r'\s+', '_', safe)
    return safe[:max_length]


def save_article(source: str, url: str, title: str, text: str, pub_date: str, scraped_at: str) -> None:
    """Simpan artikel ke folder harian berdasarkan tarikh terbit."""
    # Folder ikut tarikh terbit (contoh: raw_data/news/2026-10-18/)
    daily_dir = RAW_NEWS_DIR / pub_date
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    filename = sanitize_filename(title) + ".txt"
    filepath = daily_dir / filename

    # Idempotent: Kalau dah wujud (same title & date), skip
    if filepath.exists():
        return

    content = f"""---
source: {source}
url: {url}
published_date: {pub_date}
scraped_at: {scraped_at}
---
[Title] {title}

[Text]
{text}
"""
    filepath.write_text(content, encoding="utf-8")


def fetch_feed(source: str, url: str) -> int:
    """
    Tarik satu RSS feed, tapis, dan simpan.
    Return: bilangan artikel yang berjaya disimpan.
    """
    saved_count = 0
    print(f"  [{source.upper()}] Menarik data...")

    try:
        feed = feedparser.parse(url)
        
        if feed.bozo and not feed.entries:
            print(f"    [!] Gagal parse RSS: {feed.bozo_exception}")
            return 0

        total_entries = len(feed.entries)
        print(f"    Ditemui {total_entries} artikel.")

        # Tarikh hari ni (fallback jika RSS tak bagi tarikh)
        now_date = datetime.now().strftime("%Y-%m-%d")
        scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            
            # Ambil summary/description, buang tag HTML
            summary = entry.get("summary", "")
            clean_text = re.sub(r'<[^>]+>', '', summary).strip()

            # 1. Tapis Tajuk (Gatekeeper)
            if not matches_gatekeeper(title):
                continue

            # 2. Tapis Teks (Elak artikel kosong/terlalu pendek)
            if len(clean_text) < 150:
                continue

            # 3. Dapatkan Tarikh Terbit (Published Date)
            # feedparser simpan tarikh dalam published_parsed atau updated_parsed
            pub_date_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            
            if pub_date_struct:
                # Tukar struct_time ke string YYYY-MM-DD
                pub_date = time.strftime("%Y-%m-%d", pub_date_struct)
            else:
                # Kalau RSS tak bagi tarikh, guna tarikh hari ni
                pub_date = now_date

            # 4. Simpan
            save_article(source, link, title, clean_text, pub_date, scraped_at)
            saved_count += 1
            print(f"    [+] [{pub_date}] {title[:45]}...")

    except Exception as e:
        print(f"    [X] Ralat rangkaian: {e}")
    
    return saved_count


# ==========================================
# MAIN PROGRAM
# ==========================================

def main() -> None:
    print("=" * 60)
    print("ATRRIC NEWS AUTO-FETCHER (v1.1 - Time-Series)")
    print("=" * 60)

    total_saved = 0

    for source, url in RSS_FEEDS.items():
        saved = fetch_feed(source, url)
        total_saved += saved
        print()

    print("=" * 60)
    print(f"SELESAI. Jumlah artikel baru disimpan: {total_saved}")
    print(f"Lokasi: {RAW_NEWS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()