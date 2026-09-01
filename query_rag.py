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
LLM_MODEL = "granite4.2:8b"

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
# ======================================================================
# TAMBAHAN LANJUTAN: QUERY CACHING + SESSION HISTORY + RATE LIMITING
# ======================================================================

# ======================================================================
# 1. QUERY CACHING — Simpan jawapan untuk soalan sama
# ======================================================================
import hashlib
import json

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_key(query: str, top_k: int, temperature: float) -> str:
    """Buat key unik untuk cache berdasarkan parameter."""
    raw = f"{query}|{top_k}|{temperature}"
    return hashlib.md5(raw.encode()).hexdigest()

def load_from_cache(key: str) -> dict | None:
    """Baca cache jika wujud."""
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_to_cache(key: str, data: dict):
    """Simpan response ke cache."""
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================================================================
# 2. SESSION HISTORY — Ingat perbualan lepas
# ======================================================================
SESSION_HISTORY_FILE = Path(__file__).parent / "session_history.json"
session_history = []

def load_session_history():
    """Baca sejarah perbualan dari file."""
    global session_history
    if SESSION_HISTORY_FILE.exists():
        try:
            with open(SESSION_HISTORY_FILE, "r", encoding="utf-8") as f:
                session_history = json.load(f)
        except:
            session_history = []

def save_session_history():
    """Simpan sejarah perbualan ke file."""
    with open(SESSION_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(session_history, f, ensure_ascii=False, indent=2)

# Muat sejarah perbualan
load_session_history()

# ======================================================================
# 3. RATE LIMITING — Elak overload
# ======================================================================
from collections import deque
import time

RATE_LIMIT_WINDOW = 60  # 60 saat
RATE_LIMIT_MAX = 10     # Maksimum 10 query dalam 60 saat

request_history = deque()

def check_rate_limit():
    """Check jika melebihi had rate."""
    current_time = time.time()
    # Buang request lama
    while request_history and current_time - request_history[0] > RATE_LIMIT_WINDOW:
        request_history.popleft()
    
    if len(request_history) >= RATE_LIMIT_MAX:
        wait_time = RATE_LIMIT_WINDOW - (current_time - request_history[0])
        return False, f"Rate limit exceeded. Please wait {wait_time:.0f} seconds."
    
    request_history.append(current_time)
    return True, "OK"

# ======================================================================
# 4. INTEGRASI — Cek cache sebelum proses
# ======================================================================
cache_key = get_cache_key(args.query, args.top_k, args.temperature)
cached_response = load_from_cache(cache_key)

if cached_response:
    print("📦 Menggunakan cache...")
    print("\n📌 Jawapan:")
    print(cached_response['response'])
    print(f"\n🔎 Berdasarkan {cached_response['source_count']} dokumen sumber.")
    print(f"📊 Keyakinan: {cached_response['avg_confidence']:.2%}")
    print(f"⏱️  Dijana: {cached_response['timestamp']}")
    print(f"💾 Cached at: {cached_response['cached_at']}")
    sys.exit(0)

# ======================================================================
# 5. INTEGRASI — Rate limit check
# ======================================================================
rate_ok, rate_msg = check_rate_limit()
if not rate_ok:
    print(f"⚠️ {rate_msg}")
    logger.warning(f"Rate limit exceeded: {args.query}")
    sys.exit(1)

# ======================================================================
# 6. INTEGRASI — Tambah session history ke context
# ======================================================================
if session_history:
    history_context = "\n".join([
        f"User: {h['query']}\nAssistant: {h['response'][:200]}..."
        for h in session_history[-3:]  # 3 perbualan terakhir
    ])
    context = f"Perbualan sebelumnya:\n{history_context}\n\nData baru:\n{context}"
    logger.info(f"Session history used: {len(session_history)} conversations")

# ======================================================================
# 7. MODIFIED STREAMING — Simpan ke cache dan history
# ======================================================================
# (Ganti bahagian streaming sedia ada dengan yang ni)

response_text = ""
token_count = 0

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
# 8. SIMPAN KE CACHE & SESSION HISTORY
# ======================================================================

# Simpan ke cache
cache_data = {
    "query": args.query,
    "top_k": args.top_k,
    "temperature": args.temperature,
    "response": response_text,
    "source_count": len(results['documents'][0]),
    "avg_confidence": 1 - (sum(results['distances'][0]) / len(results['distances'][0])),
    "timestamp": datetime.now().isoformat(),
    "cached_at": datetime.now().isoformat()
}
save_to_cache(cache_key, cache_data)
logger.info(f"Cached response for: {args.query}")

# Simpan ke session history
session_history.append({
    "query": args.query,
    "response": response_text,
    "timestamp": datetime.now().isoformat()
})
save_session_history()
logger.info(f"Session history updated: {len(session_history)} conversations")
# ======================================================================
# TAMBAHAN LANJUTAN 2: HEALTH CHECK + CONFIG FILE + TELEMETRY
# ======================================================================

# ======================================================================
# 1. HEALTH CHECK — Pastikan semua sistem jalan
# ======================================================================
def health_check() -> dict:
    """Check status semua komponen sistem."""
    status = {
        "ollama": False,
        "chromadb": False,
        "config": False,
        "data": False,
        "errors": []
    }
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            status["ollama"] = True
            models = response.json().get("models", [])
            status["models"] = [m["name"] for m in models]
        else:
            status["errors"].append("Ollama API returned error")
    except Exception as e:
        status["errors"].append(f"Ollama not running: {e}")
    
    # Check ChromaDB
    try:
        test_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        test_client.heartbeat()
        status["chromadb"] = True
    except Exception as e:
        status["errors"].append(f"ChromaDB error: {e}")
    
    # Check config
    try:
        from config import CHROMA_DB_DIR, DATA_DIR
        status["config"] = True
        if DATA_DIR.exists():
            status["data"] = True
        else:
            status["errors"].append(f"Data directory not found: {DATA_DIR}")
    except Exception as e:
        status["errors"].append(f"Config error: {e}")
    
    return status

# ======================================================================
# 2. CONFIG FILE — Setting dari file (bukan hardcoded)
# ======================================================================
CONFIG_FILE = Path(__file__).parent / "query_config.json"

DEFAULT_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 500,
    "top_k": 3,
    "embed_model": "mxbai-embed-large",
    "llm_model": "qwen2.5:1.5b"
}

def load_config() -> dict:
    """Load config dari file JSON."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG.copy()
    else:
        # Buat config file jika takde
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        return DEFAULT_CONFIG.copy()

config = load_config()
logger.info(f"Config loaded: temperature={config.get('temperature', 0.7)}")

# Override dengan config jika tiada argument
if not args.temperature and config.get("temperature"):
    args.temperature = config["temperature"]
if not args.top_k and config.get("top_k"):
    args.top_k = config["top_k"]

# ======================================================================
# 3. TELEMETRY — Track penggunaan sistem
# ======================================================================
TELEMETRY_FILE = Path(__file__).parent / "telemetry.json"

def load_telemetry() -> dict:
    """Load telemetry data."""
    if TELEMETRY_FILE.exists():
        try:
            with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"total_queries": 0, "queries": [], "first_use": None, "last_use": None}
    return {"total_queries": 0, "queries": [], "first_use": None, "last_use": None}

def save_telemetry(data: dict):
    """Save telemetry data."""
    with open(TELEMETRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

telemetry = load_telemetry()

# ======================================================================
# 4. HEALTH CHECK — Jalankan sebelum query
# ======================================================================
if args.debug or True:  # Selalu check
    health = health_check()
    if health["errors"]:
        print("⚠️ Health check warnings:")
        for err in health["errors"]:
            print(f"   - {err}")
        logger.warning(f"Health check issues: {health['errors']}")
    else:
        logger.info("✅ Health check passed")
        print("✅ Sistem sedia.")

# ======================================================================
# 5. INTEGRASI TELEMETRY — Track query
# ======================================================================
telemetry["total_queries"] += 1
telemetry["queries"].append({
    "query": args.query,
    "timestamp": datetime.now().isoformat(),
    "top_k": args.top_k,
    "temperature": args.temperature,
    "response_length": len(response_text),
    "elapsed_time": round(elapsed_time, 2) if 'elapsed_time' in locals() else 0,
    "avg_confidence": avg_confidence if 'avg_confidence' in locals() else 0,
    "source_count": len(results['documents'][0]) if results.get('documents') else 0,
    "cached": cached_response if 'cached_response' in locals() and cached_response else False
})

# Simpan hanya 100 query terakhir untuk elak file besar
if len(telemetry["queries"]) > 100:
    telemetry["queries"] = telemetry["queries"][-100:]

if not telemetry["first_use"]:
    telemetry["first_use"] = datetime.now().isoformat()
telemetry["last_use"] = datetime.now().isoformat()

save_telemetry(telemetry)
logger.info(f"Telemetry updated: {telemetry['total_queries']} total queries")

# ======================================================================
# 6. TUNJUKKAN TELEMETRY RINGKAS (jika --debug)
# ======================================================================
if args.debug:
    print("\n📊 Telemetry Summary:")
    print(f"   Total queries: {telemetry['total_queries']}")
    print(f"   First use: {telemetry['first_use']}")
    print(f"   Last use: {telemetry['last_use']}")
    print(f"   Config used: temperature={args.temperature}, top_k={args.top_k}")
    # ======================================================================
# TAMBAHAN LANJUTAN 3: QUERY VALIDATION + AUTO-RETRY + SUGGESTIVE + EXPORT
# ======================================================================

# ======================================================================
# 1. QUERY VALIDATION — Check soalan kosong / sampah
# ======================================================================
def validate_query(query: str) -> tuple[bool, str]:
    """Validate soalan sebelum proses."""
    # Check kosong
    if not query or query.strip() == "":
        return False, "Soalan kosong. Sila tanya sesuatu."
    
    # Check terlalu pendek (kurang dari 3 huruf)
    if len(query.strip()) < 3:
        return False, "Soalan terlalu pendek. Sila tanya dengan lebih spesifik."
    
    # Check soalan sampah (contoh: "aaa", "123", "???")
    import re
    if re.match(r'^[?.\s\d]+$', query.strip()):
        return False, "Soalan tidak sah. Sila tanya soalan yang bermakna."
    
    # Check soalan dalam bahasa asing yang tak dikenali (pilihan)
    # Jika perlu, tambah logic untuk detect language
    
    return True, "OK"

# Jalankan validation
is_valid, validation_msg = validate_query(args.query)
if not is_valid:
    print(f"⚠️ {validation_msg}")
    logger.warning(f"Invalid query: {args.query}")
    sys.exit(0)

# ======================================================================
# 2. AUTO-RETRY — Retry jika Ollama crash
# ======================================================================
MAX_RETRIES = 3
retry_count = 0

def execute_with_retry(func, *args, **kwargs):
    """Execute function dengan auto-retry."""
    global retry_count
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            retry_count += 1
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    raise Exception(f"Failed after {MAX_RETRIES} attempts")

# Wrap streaming dengan retry
try:
    stream = execute_with_retry(
        ollama.chat,
        model=LLM_MODEL,
        messages=messages,
        stream=True,
        options={
            "temperature": args.temperature,
            "top_p": 0.9,
            "max_tokens": 500
        }
    )
    if retry_count > 0:
        logger.info(f"Success after {retry_count} retries")
except Exception as e:
    print(f"❌ Error: Gagal selepas {MAX_RETRIES} percubaan.\n{e}")
    logger.error(f"Query failed after retries: {e}")
    sys.exit(1)

# ======================================================================
# 3. SUGGESTIVE QUESTIONS — Cadangan soalan seterusnya
# ======================================================================
def generate_suggestions(query: str, response: str, context: str) -> list[str]:
    """Hasilkan 3 soalan cadangan berdasarkan jawapan."""
    suggestion_prompt = f"""
    Berdasarkan soalan: "{query}"
    Dan jawapan: "{response[:500]}..."
    
    Berikan 3 soalan susulan yang logik dan mendalam untuk diterokai.
    Output dalam format:
    1. [Soalan 1]
    2. [Soalan 2]
    3. [Soalan 3]
    """
    
    try:
        sug_response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": suggestion_prompt}],
            options={"temperature": 0.8, "max_tokens": 150}
        )
        suggestions = sug_response['message']['content'].strip().split('\n')
        # Bersihkan dan format
        clean_suggestions = []
        for s in suggestions:
            if s.strip() and s[0].isdigit() and '.' in s[:3]:
                clean_suggestions.append(s.strip())
        return clean_suggestions[:3]
    except:
        return []

# Generate suggestions (hanya jika response cukup panjang)
if len(response_text) > 50:
    suggestions = generate_suggestions(args.query, response_text, context)
    if suggestions:
        print("\n💡 Soalan cadangan:")
        for s in suggestions:
            print(f"   {s}")
        logger.info(f"Suggestions generated: {len(suggestions)}")

# ======================================================================
# 4. EXPORT TO MARKDOWN — Save jawapan ke file
# ======================================================================
def export_to_markdown(query: str, response: str, sources: list, confidence: float):
    """Export response ke file markdown."""
    export_dir = Path(__file__).parent / "exports"
    export_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = export_dir / f"query_{timestamp}.md"
    
    content = f"""# Atrric Query Report
## Soalan
{query}

## Jawapan
{response}

## Sumber
"""
    for i, source in enumerate(sources):
        content += f"{i+1}. {source}\n"
    
    content += f"\n## Keyakinan Keseluruhan\n{confidence:.2%}\n"
    content += f"\n## Tarikh\n{datetime.now().isoformat()}\n"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Exported to: {filename}")
    return filename

# Tambah argument untuk export
parser.add_argument("--export", action="store_true", help="Export jawapan ke markdown")
args = parser.parse_args()

# Export jika flag --export
if args.export:
    sources = [
        f"{meta.get('source_file', 'unknown')} (confidence: {1 - results['distances'][0][i]:.2%})"
        for i, meta in enumerate(results['metadatas'][0])
    ]
    exported_file = export_to_markdown(
        args.query,
        response_text,
        sources,
        1 - (sum(results['distances'][0]) / len(results['distances'][0]))
    )
    print(f"\n📄 Eksport disimpan: {exported_file}")
    # ======================================================================
# SNIPER FIX: OVERRIDE PARSER (PASTE KAT HUJUNG)
# ======================================================================

# Reset parser dan define semula semua argument
import argparse
import sys

# Hapus parser lama (override)
parser = argparse.ArgumentParser(description="Atrric Query Engine v3.0")
parser.add_argument("query", type=str, help="Soalan anda")
parser.add_argument("--top_k", type=int, default=3, help="Bilangan dokumen (default: 3)")
parser.add_argument("--temperature", type=float, default=0.7, help="Kreativiti (0-1, default: 0.7)")
parser.add_argument("--debug", action="store_true", help="Tunjukkan proses")
parser.add_argument("--json", action="store_true", help="Output dalam format JSON")
parser.add_argument("--export", action="store_true", help="Export jawapan ke markdown")

# Parse arguments (override yang lama)
args = parser.parse_args()

print(f"🔍 Mencari: '{args.query}' (Top-{args.top_k})...")