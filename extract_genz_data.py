import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from xpoz import XpozClient

load_dotenv()
API_KEY = os.getenv("XPOZ_API_KEY")

RAW_DATA_DIR = Path("raw_data")
RAW_DATA_DIR.mkdir(exist_ok=True)

# Kata kunci am (Broad search)
QUERIES = [
    {"query": "Malaysia", "label": "malaysia_general"},
    {"query": "tech", "label": "tech_general"},
    {"query": "AI", "label": "ai_general"}
]

def main():
    print("🚀 Mencari data umum dari Xpoz...")
    client = XpozClient(API_KEY)
    all_tweets = []
    
    for q in QUERIES:
        print(f"🔎 Testing query: '{q['query']}'...")
        try:
            results = client.twitter.search_posts(q['query'], max_results=5)
            posts = getattr(results, 'data', []) or []
            print(f"   -> Dapat {len(posts)} ciapan")
            
            for tweet in posts:
                text = getattr(tweet, 'text', '')
                if text:
                    all_tweets.append({
                        "id": str(getattr(tweet, 'id', '')),
                        "text": text,
                        "created_at": str(getattr(tweet, 'created_at', '')),
                        "label": q['label']
                    })
        except Exception as e:
            print(f"⚠️ Ralat [{q['label']}]: {e}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RAW_DATA_DIR / f"genz_data_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_tweets, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ BERJAYA! Jumlah disimpan: {len(all_tweets)} ciapan ke '{output_file}'")

if __name__ == "__main__":
    main()
