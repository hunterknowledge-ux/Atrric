import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

DATA_PATH = "/workspaces/attric-engine/data"
CHROMA_PATH = "/workspaces/attric-engine/chroma_db"

def main():
    documents = []
    if not os.path.exists(DATA_PATH):
        print("❌ Folder data/ tidak wujud.")
        return
    for filename in os.listdir(DATA_PATH):
        if filename.endswith(".txt"):
            filepath = os.path.join(DATA_PATH, filename)
            loader = TextLoader(filepath, encoding="utf-8")
            documents.extend(loader.load())
    
    if not documents:
        print("❌ Tiada fail .txt dalam folder data/")
        return

    print(f"📄 Berjaya memuatkan {len(documents)} dokumen.")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ".", " ", ""])
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 Jumlah chunks: {len(chunks)}")
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_PATH)
    vectorstore.persist()
    print("✅ Pangkalan data vektor siap disimpan!")

if __name__ == "__main__":
    main()
