import argparse
import chromadb
import ollama


from config import CHROMA_DB_DIR


EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "qwen2.5:1.5b"
COLLECTION_NAME = "atrric_corpus"  


parser = argparse.ArgumentParser(description="Query Atrric RAG Engine")
parser.add_argument("query", type=str, help="Soalan/kata kunci carian")
parser.add_argument("--top_k", type=int, default=3, help="Bilangan dokumen untuk retrieve (default: 3)")
args = parser.parse_args()

print(f"🔍 Mencari: '{args.query}' (Top-{args.top_k})...")


try:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
except Exception as e:
    print(f"❌ Error: Tak dapat connect ke ChromaDB.\n{e}")
    exit()


try:
    embed = ollama.embeddings(model=EMBED_MODEL, prompt=args.query)["embedding"]
except Exception as e:
    print("❌ Error: Ollama embedding tak jalan. Pastikan 'ollama serve' running.")
    print("💡 Dan model 'mxbai-embed-large' dah pull.")
    exit()


results = collection.query(query_embeddings=[embed], n_results=args.top_k)

if not results.get("documents") or not results["documents"][0]:
    print("❌ Tiada dokumen relevan ditemui.")
    exit()


context = "\n\n".join(results["documents"][0])
print("\n🧠 Memproses dengan LLM...\n")

stream = ollama.chat(
    model=LLM_MODEL,
    messages=[{"role": "user", "content": f"Gunakan konteks berikut untuk menjawab soalan dengan ringkas dan profesional:\n\n{context}\n\nSoalan: {args.query}"}],
    stream=True
)

print("📌 Jawapan:")
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
print("\n")


print(f"🔎 Berdasarkan {len(results['documents'][0])} dokumen sumber.")
if results.get("metadatas") and results["metadatas"][0]:
    print("📁 Sumber metadata:")
    for meta in results["metadatas"][0]:
        print(f"   - {meta}")