import os
from dotenv import load_dotenv
from xpoz import XpozClient

load_dotenv()
API_KEY = os.getenv("XPOZ_API_KEY")

print(f"🔑 Key: {API_KEY[:10]}...")

try:
    client = XpozClient(API_KEY)
    results = client.twitter.search_posts("Gen Z Malaysia", max_results=3)
    print(f"✅ Found {len(results.data)} tweets")
    for t in results.data:
        print(f"  - {t.text[:60]}...")
    client.close()
except Exception as e:
    print(f"❌ Error: {e}")
