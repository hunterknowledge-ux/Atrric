"""POC pipeline - chunk data, bina prompt untuk SmolLM2."""
from pathlib import Path

# Lokasi
BASE = Path(__file__).parent
DATA_FILE = BASE / "data" / "ujian.txt"
PROMPT_FILE = BASE / "poc_prompt.txt"

# Baca fail
text = DATA_FILE.read_text(encoding="utf-8")
print(f"Baca: {len(text)} chars")

# Chunk (simple - split by perenggan)
chunks = [c.strip() for c in text.split("\n") if c.strip()]
print(f"Chunks: {len(chunks)}")

# Ambil chunk (POC - ambil semua, gabung semula)
context = "\n".join(chunks)[:1500]  # had 1500 char untuk context

# Soalan test
question = "Apa itu Gen Z Malaysia?"

# Bina prompt
prompt = f"""Data:
{context}

Soalan: {question}
Jawapan:"""

# Simpan
PROMPT_FILE.write_text(prompt, encoding="utf-8")
print(f"Prompt disimpan: {PROMPT_FILE}")
print(f"Saiz prompt: {len(prompt)} chars")
