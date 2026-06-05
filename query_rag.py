import argparse
import chromadb
import ollama

CHROMA_DIR = "/workspaces/Atrric/chroma_db"
EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "qwen2.5:1.5b"

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection(name="attric_docs")

parser = argparse.ArgumentParser()
parser.add_argument("query", type=str)
args = parser.parse_args()

embed = ollama.embeddings(model=EMBED_MODEL, prompt=args.query)["embedding"]
results = collection.query(query_embeddings=[embed], n_results=3)

if not results.get("documents") or not results["documents"][0]:

    print("❌ Tiada dokumen relevan ditemui.")
    exit()
    
 
context = "\n\n".join(results["documents"][0])
response = ollama.chat(
    model=LLM_MODEL,
    messages=[{"role": "user", "content": f"Gunakan konteks berikut untuk menjawab soalan dengan ringkas dan profesional:\n\n{context}\n\nSoalan: {args.query}"}]
)
print(f"\n📌 Jawapan:\n{response['message']['content']}")
print(f"\n🔎 Berdasarkan {len(results['documents'][0])} dokumen sumber.")
