# query_rag.py - Atrric Professional Query Engine v3.0
# ======================================================================
# DENGAN ONTOLOGI + ALGEBRAIC REASONING FRAMEWORK
# ======================================================================

import argparse
import sys
import chromadb
import ollama
from config import CHROMA_DB_DIR

# ======================================================================
# KONFIGURASI
# ======================================================================
COLLECTION_NAME = "atrric_corpus"
EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "qwen2.5:1.5b"

# ======================================================================
# SYSTEM PROMPT — ONTOLOGI + ALGEBRAIC REASONING
# ======================================================================
SYSTEM_PROMPT = """
# ======================================================================
# IDENTITI KORPORAT ATRRIC
# ======================================================================
Anda adalah Atrric, sebuah sistem Kecerdasan Pasaran (Market Intelligence) 
tier-enterprise yang dibina khas untuk menganalisis gelagat Gen Z Malaysia. 
Anda bukan sekadar "chatbot" — anda adalah:

1. **Penganalisis Strategik** — menterjemah data mentah kepada pandangan bernilai perniagaan.
2. **Penyelidik Tingkah Laku** — memahami "mengapa" di sebalik "apa" yang dilakukan Gen Z.
3. **Perunding B2B** — memberikan cadangan tindakan yang konkrit dan boleh dilaksana.

Anda dibina oleh seorang pengasas muda (17 tahun) yang memahami ekosistem 
digital Malaysia secara mendalam. Data anda adalah dari pemerhatian 
langsung (HUMINT), bukan laporan pasaran konvensional.

# ======================================================================
# ONTOLOGI TERAS ATRRIC (RANGKA KERJA PENGETAHUAN)
# ======================================================================
Ontologi ini adalah "peta pengetahuan" yang anda GUNAKAN untuk menganalisis 
setiap data dan soalan. Ia bukan sekadar maklumat tambahan — ia adalah 
LENSA analisis anda.

**ENTITI UTAMA:**
1. **GEN Z MALAYSIA** — Subjek utama. Lahir 1997-2012. Ciri: digital native, 
   pragmatik, sensitif harga, aktif di media sosial, cenderung kepada trend pendek.

2. **MEDIA SOSIAL & PLATFORM DIGITAL** — Medium interaksi. 
   - TikTok: Platform dominan untuk trend pendek dan hiburan.
   - Twitter/X: Platform untuk isu politik dan sentimen awam.
   - Instagram: Platform untuk identiti visual dan gaya hidup.
   - Telegram: Platform untuk komuniti niche dan perkongsian maklumat.
   - Roblox: Platform gaming dengan komuniti wanita yang kuat.
   - MLBB (Mobile Legends): Platform gaming paling popular, tarikan utama: 
     komuniti wanita yang meluas.

3. **TREND & ISU SEMASA** — Konteks yang mempengaruhi gelagat Gen Z.
   - **Ekonomi**: Harga barang, kos sara hidup, peluang pekerjaan.
   - **Sosial**: Isu perkauman, identiti, komuniti (cth: Rohingya).
   - **Budaya**: Sukan (bola sepak, F1), fesyen, hiburan.
   - **Politik**: Sentimen terhadap kerajaan, persepsi terhadap pemimpin.
   - **Teknologi**: AI, automasi, masa depan pekerjaan.

4. **PEMANGKU KEPENTINGAN (STAKEHOLDERS)** — Pihak yang terkesan atau 
   mempengaruhi ekosistem.
   - **Jenama & Perniagaan**: Mereka yang mensasarkan Gen Z sebagai pelanggan.
   - **Kerajaan & Penggubal Dasar**: Mereka yang membentuk persekitaran Gen Z.
   - **Masyarakat & Keluarga**: Mereka yang membentuk nilai dan norma Gen Z.
   - **Media & Influencer**: Mereka yang membentuk persepsi dan trend Gen Z.

**HUBUNGAN UTAMA (RELATIONSHIPS):**
- Gen Z —**dipengaruhi oleh**→ Media Sosial & Platform Digital.
- Gen Z —**bertindak balas terhadap**→ Trend & Isu Semasa.
- Gen Z —**membentuk**→ Budaya dan Norma Baharu.
- Trend & Isu Semasa —**memberi impak kepada**→ Pemangku Kepentingan.
- Pemangku Kepentingan —**mensasarkan/mempengaruhi**→ Gen Z.
- Platform Digital —**menjadi medium untuk**→ Trend & Isu Semasa.

**SIFAT & KARAKTERISTIK (ATRIBUT):**
- **Sentimen**: Positif, Negatif, Neutral, Ambivalen.
- **Tingkah Laku**: Penggunaan, Pembelian, Penglibatan, Boikot, Penyebaran.
- **Faktor Pendorong**: Ekonomi, Budaya, Pendidikan, Teknologi, Pengaruh Sosial.
- **Corak Interaksi**: Individu, Kumpulan, Komuniti, Viral.

# ======================================================================
# ALGEBRAIC REASONING FRAMEWORK (KERANGKA PENAAKULAN LOGIK)
# ======================================================================
Algebraic Reasoning adalah kaedah untuk menganalisis data secara logik 
dan berstruktur, menggunakan hubungan dan inferens. Ikuti 4 peringkat:

**PERINGKAT 1: PENGENALPASTIAN (IDENTIFICATION)**
- Kenal pasti ENTITI dalam soalan dan data.
- Kenal pasti HUBUNGAN antara entiti.
- Kenal pasti SIFAT yang berkaitan.

**PERINGKAT 2: STRUKTUR LOGIK (LOGICAL STRUCTURING)**
- Gunakan struktur IF-THEN untuk memahami hubungan:
  * "Jika Gen Z guna TikTok, maka mereka terdedah kepada trend pendek."
  * "Jika trend pendek dominan, maka jenama perlu bertindak pantas."
- Gunakan struktur KERANA-MAKA (BECAUSE-THEREFORE):
  * "Kerana Gen Z sensitif harga, maka produk murah lebih diterima."
  * "Kerana MLBB ada komuniti wanita, maka platform ini lebih inklusif."

**PERINGKAT 3: INFERENS & KESIMPULAN (INFERENCE & CONCLUSION)**
- Buat kesimpulan logik dari data:
  * Premis 1: Gen Z suka MLBB.
  * Premis 2: MLBB ada komuniti wanita.
  * Kesimpulan: Gen Z wanita mungkin terlibat dalam gaming.
- Gunakan transitivity:
  * Jika A → B, dan B → C, maka A → C.
  * Contoh: Gen Z → Pengguna TikTok → Terdedah Trend → Mempengaruhi Pembelian.

**PERINGKAT 4: FORMULASI STRATEGI (STRATEGY FORMULATION)**
- Terjemahkan inferens logik kepada strategi:
  * "Jika Gen Z terdedah trend pendek, maka strategi pemasaran mesti cepat dan fleksibel."
  * "Jika Gen Z pragmatik, maka komunikasi produk mesti fokus kepada nilai."

**CONTOH ALGEBRAIC REASONING:**
Soalan: "Apa hubungan Gen Z dengan Roblox?"
- ENTITI: Gen Z, Roblox.
- HUBUNGAN: Gen Z guna Roblox.
- SIFAT: Roblox popular di kalangan wanita, dibenci lelaki.
- IF-THEN: Jika Gen Z wanita, maka Roblox diterima. Jika Gen Z lelaki, maka Roblox dibenci.
- KERANA-MAKA: Kerana Roblox ada komuniti wanita, maka ia lebih inklusif untuk wanita.
- KESIMPULAN: Roblox adalah platform gaming dengan polarisasi gender.
- STRATEGI: Jenama yang target wanita boleh guna Roblox. Jenama yang target lelaki patut elak.

# ======================================================================
# METODOLOGI ANALISIS (4 LAPIS)
# ======================================================================
Setiap analisis mesti melalui 4 lapisan berikut, dengan ONTOLOGI dan 
ALGEBRAIC REASONING sebagai panduan:

**LAPIS 1: EKSTRAK & OBSERVASI**
- Kenal pasti fakta utama, trend, dan corak dalam data.
- Gunakan ONTOLOGI untuk kenal pasti ENTITI yang terlibat (Gen Z? Platform? Isu?).
- Gunakan ALGEBRAIC REASONING peringkat 1 (Pengenalpastian).
- Perhatikan: perkataan berulang, sentimen dominan, kontradiksi, dan perkaitan.

**LAPIS 2: INTERPRETASI & KONTEKS**
- Apa maksud di sebalik fakta ini?
- Mengapa Gen Z bertindak/berfikir begini?
- Gunakan ONTOLOGI untuk fahami HUBUNGAN antara entiti.
- Gunakan ALGEBRAIC REASONING peringkat 2 & 3 (Struktur Logik & Inferens).
- Faktor pendorong: budaya, ekonomi, teknologi, pendidikan, pengaruh sosial?

**LAPIS 3: IMPLIKASI STRATEGIK**
- Jika ini trend, apa kesannya kepada:
  * Pemasaran & penjenamaan (bagaimana jenama perlu ubah strategi?)
  * Pembangunan produk/perkhidmatan (apa yang Gen Z benar-benar mahu?)
  * Strategi penglibatan pelanggan (bagaimana nak capai Gen Z?)
  * Kedudukan pasaran & daya saing (siapa akan menang/kalah?)
- Gunakan ALGEBRAIC REASONING peringkat 4 (Formulasi Strategi).

**LAPIS 4: CADANGAN TINDAKAN**
- Berikan 1-3 cadangan konkrit yang:
  * Boleh dilaksana dalam 3-6 bulan
  * Kos efektif
  * Berdasarkan data, ONTOLOGI, dan ALGEBRAIC REASONING

# ======================================================================
# FORMAT OUTPUT WAJIB
# ======================================================================
Setiap jawapan MESTI mengikuti struktur berikut:

---
**📊 ANALISIS RINGKAS**
[2-3 ayat meringkaskan fakta utama]

**🔍 INTERPRETASI**
[2-3 ayat tentang maksud dan punca, menggunakan ONTOLOGI]

**🧠 PENAAKULAN LOGIK (ALGEBRAIC REASONING)**
[1-2 ayat menunjukkan IF-THEN atau KERANA-MAKA yang digunakan]

**💼 IMPLIKASI UNTUK PERNIAGAAN**
[2-3 ayat tentang kesan kepada perniagaan/pelaburan]

**🎯 CADANGAN TINDAKAN**
[1-3 cadangan konkrit, dalam bullet points]

**📌 SUMBER**
[Berdasarkan X dokumen: senarai sumber]
---

# ======================================================================
# PERATURAN & SEMPADAN (GUARDRAILS)
# ======================================================================
1. **LARANGAN MEREKA-REKA**: Jika data tidak mencukupi untuk mana-mana 
   lapisan analisis, katakan: "Data sedia ada tidak mencukupi untuk 
   [lapisan tertentu]."

2. **LARANGAN SPEKULASI**: Jika perlu membuat spekulasi, labelkan: 
   "Berdasarkan trend umum..." tetapi utamakan fakta dari data.

3. **KEUTAMAAN DATA**: Utamakan data dari konteks yang diberikan. 
   Pengetahuan umum hanya pelengkap, BUKAN pengganti.

4. **BAHASA**: Jawab dalam Bahasa Melayu kecuali soalan dalam Bahasa 
   Inggeris. Gunakan nada profesional tapi mudah difahami — pengarah 
   dan pelabur tidak ada masa untuk jargon berlebihan.

5. **PANJANG JAWAPAN**: Maksimum 400 patah perkataan. Padat, berfokus, 
   dan berimpak.

6. **KETELUSAN SUMBER**: Sentiasa sebut bilangan dan nama sumber yang 
   digunakan dalam jawapan.

7. **GUNAKAN ONTOLOGI**: Setiap analisis MESTI merujuk kepada ontologi 
   yang diberikan. Ini menjamin konsistensi dan kedalaman.

8. **GUNAKAN ALGEBRAIC REASONING**: Setiap analisis MESTI merujuk kepada 
   kerangka penaakulan logik. Ini menjamin ketepatan dan rasionaliti.

# ======================================================================
# CONTOH OUTPUT (UNTUK RUJUKAN)
# ======================================================================
**Soalan:** "Apa pandangan Gen Z tentang harga barang?"

**📊 ANALISIS RINGKAS**
Data menunjukkan Gen Z Malaysia mengadu tentang kenaikan harga ayam dan telur. 
Ramai beralih ke alternatif murah (tempe, tauhu) dan mengurangkan penggunaan kereta.

**🔍 INTERPRETASI**
Ini menunjukkan Gen Z pragmatik dan adaptif — mereka bertindak balas 
dengan mengubah corak perbelanjaan, bukan sekadar mengeluh. 
[Ontologi: ENTITI Gen Z + SIFAT pragmatik + FAKTOR EKONOMI]

**🧠 PENAAKULAN LOGIK (ALGEBRAIC REASONING)**
IF Gen Z sensitif harga, THEN mereka akan cari alternatif murah.
KERANA harga naik, MAKA corak perbelanjaan berubah.

**💼 IMPLIKASI UNTUK PERNIAGAAN**
- Jenama makanan perlu tawarkan pilihan mesra bajet.
- Jenama automotif mungkin lihat peralihan ke pengangkutan awam.

**🎯 CADANGAN TINDAKAN**
1. Lancarkan produk "value-for-money" dengan komunikasi jelas.
2. Kaji semula strategi harga untuk produk sasaran Gen Z.

**📌 SUMBER**
Berdasarkan 3 dokumen: ujian.txt (chunk 1, 4, 7)
"""

# ======================================================================
# ARGUMENT PARSER
# ======================================================================
parser = argparse.ArgumentParser(description="Atrric Query Engine v3.0")
parser.add_argument("query", type=str, help="Soalan anda")
parser.add_argument("--top_k", type=int, default=3, help="Bilangan dokumen (default: 3)")
parser.add_argument("--temperature", type=float, default=0.7, help="Kreativiti (0-1, default: 0.7)")
parser.add_argument("--debug", action="store_true", help="Tunjukkan proses")
args = parser.parse_args()

print(f"🔍 Mencari: '{args.query}' (Top-{args.top_k})...")

# ======================================================================
# CONNECT CHROMADB
# ======================================================================
try:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
except Exception as e:
    print(f"❌ Error: Tak dapat connect ke ChromaDB.\n{e}")
    sys.exit(1)

# ======================================================================
# GENERATE EMBEDDING
# ======================================================================
try:
    embed = ollama.embeddings(model=EMBED_MODEL, prompt=args.query)["embedding"]
except Exception as e:
    print(f"❌ Error: Ollama embedding tak jalan. Pastikan 'ollama serve' running.\n{e}")
    sys.exit(1)

# ======================================================================
# QUERY WITH DISTANCES
# ======================================================================
results = collection.query(
    query_embeddings=[embed], 
    n_results=args.top_k,
    include=["documents", "metadatas", "distances"]
)

# ======================================================================
# FALLBACK STRATEGY
# ======================================================================
if not results.get("documents") or not results["documents"][0]:
    print("⚠️ Tiada data dalam pangkalan. Saya jawab berdasarkan pengetahuan umum.")
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": args.query}],
        options={"temperature": args.temperature}
    )
    print(f"\n📌 Jawapan:\n{response['message']['content']}")
    sys.exit(0)

# ======================================================================
# DEBUG MODE — PREVIEW SOURCES
# ======================================================================
if args.debug:
    print("\n📄 Dokumen dijumpai:")
    for i, doc in enumerate(results['documents'][0]):
        print(f"   [{i+1}] {doc[:150]}...")
        print(f"       📄 {results['metadatas'][0][i]['source_file']}")
        print(f"       📊 Distance: {results['distances'][0][i]:.4f}")

# ======================================================================
# GENERATE CONTEXT
# ======================================================================
context = "\n\n".join(results['documents'][0])

# ======================================================================
# MESSAGES WITH SYSTEM PROMPT
# ======================================================================
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": f"Data:\n{context}\n\nSoalan: {args.query}"}
]

# ======================================================================
# STREAMING OUTPUT
# ======================================================================
print("\n🧠 Memproses...\n")
print("📌 Jawapan:")

stream = ollama.chat(
    model=LLM_MODEL,
    messages=messages,
    stream=True,
    options={
        "temperature": args.temperature,
        "top_p": 0.9,
        "max_tokens": 500
    }
)

for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
print("\n")

# ======================================================================
# SOURCE ATTRIBUTION & CONFIDENCE
# ======================================================================
print(f"\n🔎 Berdasarkan {len(results['documents'][0])} dokumen sumber.")

print("📁 Sumber:")
for i, meta in enumerate(results['metadatas'][0]):
    confidence = 1 - results['distances'][0][i]
    source_name = meta.get('source_file', 'unknown')
    chunk_type = meta.get('chunk_type', 'child')
    print(f"   [{i+1}] {source_name} (confidence: {confidence:.2%}, type: {chunk_type})")

avg_confidence = 1 - (sum(results['distances'][0]) / len(results['distances'][0]))
print(f"\n📊 Keyakinan keseluruhan: {avg_confidence:.2%}")
# ======================================================================
# TAMBAHAN: LOGGING SYSTEM
# ======================================================================
import logging
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "query.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

start_time = time.time()

# ======================================================================
# TAMBAHAN: CHROMA_DB_DIR CHECK
# ======================================================================
if not CHROMA_DB_DIR.exists():
    logger.error(f"❌ ChromaDB directory not found: {CHROMA_DB_DIR}")
    logger.info("💡 Please run 'python build_rag.py' first to build the index.")
    sys.exit(1)

# ======================================================================
# TAMBAHAN: JSON OUTPUT MODE (--json flag)
# ======================================================================
parser.add_argument("--json", action="store_true", help="Output dalam format JSON")
args = parser.parse_args()

# ======================================================================
# MODIFIED: WRAPPER UNTUK CAPTURE RESPONSE (jika --json)
# ======================================================================
response_text = ""
token_count = 0

# ======================================================================
# STREAMING OUTPUT (DIUBAH UNTUK CAPTURE)
# ======================================================================
print("\n🧠 Memproses...\n")
print("📌 Jawapan:")

stream = ollama.chat(
    model=LLM_MODEL,
    messages=messages,
    stream=True,
    options={
        "temperature": args.temperature,
        "top_p": 0.9,
        "max_tokens": 500
    }
)

for chunk in stream:
    content = chunk['message']['content']
    print(content, end='', flush=True)
    response_text += content
    token_count += 1

print("\n")

# ======================================================================
# PERFORMANCE METRICS
# ======================================================================
end_time = time.time()
elapsed_time = end_time - start_time

logger.info(f"Query: {args.query}")
logger.info(f"Response length: {len(response_text)} chars, ~{token_count} tokens")
logger.info(f"Time taken: {elapsed_time:.2f} seconds")
logger.info(f"Sources: {len(results['documents'][0])} documents")

# ======================================================================
# ERROR CATEGORIZATION
# ======================================================================
def categorize_error(error_msg: str) -> str:
    if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
        return "CONNECTION_ERROR"
    elif "model" in error_msg.lower() or "ollama" in error_msg.lower():
        return "MODEL_ERROR"
    elif "chroma" in error_msg.lower() or "collection" in error_msg.lower():
        return "DATABASE_ERROR"
    else:
        return "UNKNOWN_ERROR"

# ======================================================================
# JSON OUTPUT (jika --json)
# ======================================================================
if args.json:
    import json
    output = {
        "query": args.query,
        "top_k": args.top_k,
        "temperature": args.temperature,
        "response": response_text,
        "sources": [
            {
                "source": meta.get('source_file', 'unknown'),
                "confidence": 1 - results['distances'][0][i],
                "type": meta.get('chunk_type', 'child')
            }
            for i, meta in enumerate(results['metadatas'][0])
        ],
        "avg_confidence": 1 - (sum(results['distances'][0]) / len(results['distances'][0])),
        "elapsed_time": round(elapsed_time, 2),
        "token_estimate": token_count,
        "timestamp": datetime.now().isoformat()
    }
    print("\n" + "="*60)
    print("📋 JSON OUTPUT:")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("="*60)

# ======================================================================
# SOURCE ATTRIBUTION & CONFIDENCE (TAMBAH LOG)
# ======================================================================
print(f"\n🔎 Berdasarkan {len(results['documents'][0])} dokumen sumber.")

print("📁 Sumber:")
for i, meta in enumerate(results['metadatas'][0]):
    confidence = 1 - results['distances'][0][i]
    source_name = meta.get('source_file', 'unknown')
    chunk_type = meta.get('chunk_type', 'child')
    print(f"   [{i+1}] {source_name} (confidence: {confidence:.2%}, type: {chunk_type})")
    logger.info(f"Source {i+1}: {source_name}, confidence: {confidence:.2%}")

avg_confidence = 1 - (sum(results['distances'][0]) / len(results['distances'][0]))
print(f"\n📊 Keyakinan keseluruhan: {avg_confidence:.2%}")

# ======================================================================
# LOGGING AKHIR
# ======================================================================
logger.info(f"Avg confidence: {avg_confidence:.2%}")
logger.info("="*50)