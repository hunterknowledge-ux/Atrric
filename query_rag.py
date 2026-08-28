import argparse
import chromadb
import ollama

from config import CHROMA_DB_DIR  
client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "qwen2.5:1.5b"

client = chromadb.PersistentClient(path=CHROMA_DIR)
COLLECTION_NAME = "atrric_corpus"  
collection = client.get_collection(name=COLLECTION_NAME)

parser = argparse.ArgumentParser()
parser.add_argument("query", type=str)
args = parser.parse_args()

try:
    embed = ollama.embeddings(model=EMBED_MODEL, prompt=args.query)["embedding"]
except Exception as e:
    print("❌ Error: Ollama tak jalan atau model embedding takde.")
    print("💡 Pastikan 'ollama serve' dah start dan model dah pull.")
    exit()
parser.add_argument("--top_k", type=int, default=3, help="Bilangan dokumen untuk retrieve")
args = parser.parse_args()
results = collection.query(query_embeddings=[embed], n_results=args.top_k)

if not results.get("documents") or not results["documents"][0]:

    print("❌ Tiada dokumen relevan ditemui.")
    exit()
    
 
context = "\n\n".join(results["documents"][0])
stream = ollama.chat(model=LLM_MODEL, messages=[...], stream=True)
print("📌 Jawapan:")
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
print("\n")
print(f"\n🔎 Sumber dokumen: {results['metadatas'][0]}")  
