"""extract_reddit.py - Extract Reddit Malaysia Data via Xpoz"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from xpoz import XpozClient

load_dotenv()
API_KEY = os.getenv("XPOZ_API_KEY")
if not API_KEY:
    print("❌ API Key not found!")
    exit(1)

RAW_DATA_DIR = Path("raw_data")
RAW_DATA_DIR.mkdir(exist_ok=True)

# ======================================================================
# QUERIES BAHASA MELAYU/MANGLISH
# ======================================================================
QUERIES = [
    {"query": '"anak muda" OR "remaja" AND "Malaysia"', "subreddit": "malaysia", "label": "remaja_malaysia"},
    {"query": '"harga" OR "gaji" OR "ekonomi"', "subreddit": "MalaysianPF", "label": "ekonomi"},
    {"query": '"AI" OR "teknologi" OR "gadget"', "subreddit": "malaysia", "label": "teknologi"},
    {"query": '"sekolah" OR "universiti" OR "pelajar"', "subreddit": "malaysia", "label": "pendidikan"},
    {"query": '"politik" OR "kerajaan" OR "undi"', "subreddit": "malaysia", "label": "politik"},
]

def extract_reddit(client, config, limit=20):
    print(f"\n🔍 r/{config['subreddit']}: {config['label']}")
    posts = []
    
    try:
        results = client.reddit.search_posts(
            config['query'],
            subreddit=config['subreddit'],
            max_results=limit,
            sort="relevance"
        )
        
        for post in getattr(results, 'data', []):
            title = getattr(post, 'title', '')
            text = getattr(post, 'selftext', '')[:500]
            score = getattr(post, 'score', 0)
            comments = getattr(post, 'num_comments', 0)
            
            if score < 2:
                continue
            
            posts.append({
                "title": title,
                "text": text,
                "score": score,
                "comments": comments,
                "subreddit": config['subreddit'],
                "label": config['label']
            })
            
    except Exception as e:
        print(f"    ⚠️ Error: {e}")
    
    print(f"    ✅ Got {len(posts)} posts")
    return posts

def main():
    print("=" * 60)
    print("📦 ATRRIC REDDIT EXTRACTOR")
    print("=" * 60)
    
    client = XpozClient(API_KEY)
    all_data = []
    
    for config in QUERIES:
        data = extract_reddit(client, config, limit=20)
        all_data.extend(data)
    
    # Save to text format
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RAW_DATA_DIR / f"reddit_data_{timestamp}.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        for item in all_data:
            f.write(f"[r/{item['subreddit']}] {item['label']}\n")
            f.write(f"📌 {item['title']}\n")
            if item['text']:
                f.write(f"   {item['text'][:300]}...\n")
            f.write(f"⬆️ {item['score']} | 💬 {item['comments']}\n")
            f.write("\n")
    
    print("\n" + "=" * 60)
    print(f"✅ DONE! Total: {len(all_data)} posts")
    print(f"📁 File: {output_file}")
    print("=" * 60)
    print("\n💡 Next: python data_pipeline.py")

if __name__ == "__main__":
    main()
