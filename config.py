
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data"
CHROMA_DB_DIR = ROOT_DIR / "chroma_db"
UJIAN_TXT_PATH = DATA_DIR / "ujian.txt"



# ======================================================================
# PHONE MODE (llama.cpp + local models)
# ======================================================================
# Binaries and models live in Termux home, not in repo.
LLAMA_CLI = Path.home() / "llama.cpp" / "build" / "bin" / "llama-cli"
LLAMA_EMBED = Path.home() / "llama.cpp" / "build" / "bin" / "llama-embedding"
SMOLLM_MODEL = Path.home() / "smollm2.gguf"
EMBED_MODEL = Path.home() / "hourai2-embed.gguf"

# Vector store (JSON for phone, RAM-friendly)
VECTOR_STORE_FILE = ROOT_DIR / "vector_store.json"

# ======================================================================
# PIPELINE SETTINGS
# ======================================================================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3
CONTEXT_SIZE = 512
THREADS = 2
MAX_TOKENS = 60