"""
auto_fetch_news.py — Auto-fetch news RSS untuk ATRRIC.

Tarik berita dari sumber RSS Malaysia, tapis guna Gatekeeper 
(Entity + Topic keywords), dan simpan ke raw_data/news/YYYY-MM-DD/ 
berdasarkan TARIKH TERBIT artikel.

Guna:
    python auto_fetch_news.py
"""

import re
import time
from datetime import datetime
from pathlib import Path

import feedparser

# ==========================================
# KONFIGURASI
# ==========================================

RSS_FEEDS: dict[str, str] = {
    "fmt_bm": "https://www.freemalaysiatoday.com/category/bahasa/feed/",
    "soyacincau": "https://soyacincau.com/feed/",
    "cilisos": "https://cilisos.my/feed/",
    "lobakmerah": "https://lobakmerah.com/feed/",
}

# Senarai sumber yang tak perlu strict pada Entity (sebab diorang memang untuk Gen Z)
LIFESTYLE_SOURCES: list[str] = ["soyacincau", "cilisos", "lobakmerah"]

ENTITY_KEYWORDS: list[str] = [
    "gen z", "belia", "pelajar", "graduan", "fresh grad", 
    "anak muda", "universiti", "sekolah", "remaja", "ipt",
    "gen-z", "mahasiswa", "lepasan spm"
]

TOPIC_KEYWORDS: list[str] = [
    # Isu Berat
    "pendidikan", "ekonomi", "kerja", "gaji", "sara hidup", 
    "harga barang", "mental health", "silibus", "ptptn", 
    "pengangguran", "gig", "part time", "kerjaya", "internship",
    # Isu Lifestyle & Tech
    "tech", "gadget", "smartphone", "internet", "media sosial", 
    "viral", "trend", "lifestyle", "gaya hidup", "hiburan", 
    "gaming", "aplikasi", "tiktok", "shopee", "iphone", 
    "android", "review", "makanan", "tempat makan"
]

ROOT_DIR = Path(__file__).parent
RAW_NEWS_DIR = ROOT_DIR / "raw_data" / "news"


# ==========================================
# FUNGSI TERAS
# ==========================================

def matches_gatekeeper(title: str, source: str) -> bool:
    """
    Tapis tajuk. 
    - Kalau sumber Lifestyle: Cukup ada Topic.
    - Kalau sumber Berita (FMT): Mesti ada Entity DAN Topic.
    """
    title_lower = title.lower()
    has_topic = any(kw in title_lower for kw in TOPIC_KEYWORDS)
    
    if source in LIFESTYLE_SOURCES:
        return has_topic
    
    has_entity = any(kw in title_lower for kw in ENTITY_KEYWORDS)
    return has_entity and has_topic


def sanitize_filename(title: str, max_length: int = 50) -> str:
    safe = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip().lower()
    safe = re.sub(r'\s+', '_', safe)
    return safe[:max_length]


def save_article(source: str, url: str, title: str, text: str, pub_date: str, scraped_at: str) -> None:
    daily_dir = RAW_NEWS_DIR / pub_date
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    filename = sanitize_filename(title) + ".txt"
    filepath = daily_dir / filename

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
    saved_count = 0
    print(f"  [{source.upper()}] Menarik data...")

    try:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        feed = feedparser.parse(url, agent=user_agent)
        
        if feed.bozo and not feed.entries:
            print(f"    [!] Gagal parse RSS: {feed.bozo_exception}")
            return 0

        total_entries = len(feed.entries)
        print(f"    Ditemui {total_entries} artikel.")

        now_date = datetime.now().strftime("%Y-%m-%d")
        scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            clean_text = re.sub(r'<[^>]+>', '', summary).strip()

            # Pass source ke gatekeeper
            if not matches_gatekeeper(title, source):
                continue

            if len(clean_text) < 150:
                continue

            pub_date_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            
            if pub_date_struct:
                pub_date = time.strftime("%Y-%m-%d", pub_date_struct)
            else:
                pub_date = now_date

            save_article(source, link, title, clean_text, pub_date, scraped_at)
            saved_count += 1
            print(f"    [+] [{pub_date}] {title[:45]}...")

    except Exception as e:
        print(f"    [X] Ralat rangkaian: {e}")
    
    return saved_count


def main() -> None:
    print("=" * 60)
    print("ATRRIC NEWS AUTO-FETCHER (v1.5 - Smart Source Logic)")
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