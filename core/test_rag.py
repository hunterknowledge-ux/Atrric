"""Test RAG wrapper — vector-only, no graph, no real LLM."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag import RAG


def main():
    print("1. init RAG...")
    rag = RAG()
    print("   ok")

    print("\n2. retrieve('TikTok Gen Z')...")
    hits = rag.retrieve("TikTok Gen Z", limit=3)
    print(f"   {len(hits)} hits")
    for h in hits[:3]:
        # h = (chunk, score)
        chunk, score = h[0], h[1]
        text = getattr(chunk, "text", str(chunk))[:60]
        print(f"   {score:.4f} | {text}")

    print("\n3. search('TikTok Gen Z', synthesize=False)...")
    result = rag.search("TikTok Gen Z", synthesize=False)
    print(f"   type: {type(result).__name__}")
    print(f"   attrs: {[a for a in dir(result) if not a.startswith('_')]}")

    rag.close()
    print("\ndone.")


if __name__ == "__main__":
    main()