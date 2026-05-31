import argparse
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
import ollama

CHROMA_PATH = "/workspaces/attric-engine/chroma_db"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="Soalan anda")
    args = parser.parse_args()

    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    results = vectorstore.similarity_search(args.query, k=3)
    if not results:
        print("❌ Tiada dokumen relevan ditemui.")
        return

    context = "\n\n".join([doc.page_content for doc in results])
    response = ollama.chat(
        model="qwen2.5-coder:7b",
        messages=[{"role": "user", "content": f"Gunakan konteks berikut untuk menjawab soalan dengan ringkas:\n\n{context}\n\nSoalan: {args.query}"}]
    )
    print(f"\n📌 Jawapan:\n{response['message']['content']}")
    print(f"\n🔎 Berdasarkan {len(results)} dokumen sumber.")

if __name__ == "__main__":
    main()
