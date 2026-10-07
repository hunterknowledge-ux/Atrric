"""
config.py - Single source of truth for Atrric.
All paths and application constants live here.
"""

from pathlib import Path

# ======================================================================
# PATHS
# ======================================================================
ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data"
CHROMA_DB_DIR = ROOT_DIR / "chroma_db"
UJIAN_TXT_PATH = DATA_DIR / "ujian.txt"

# ======================================================================
# PHONE MODE — llama.cpp binaries and models
# ======================================================================
LLAMA_CLI = Path.home() / "llama.cpp" / "build" / "bin" / "llama-cli"
LLAMA_EMBED = Path.home() / "llama.cpp" / "build" / "bin" / "llama-embedding"

# Models available on phone
# Primary model (used by core/llm.py)
SMOLLM_MODEL = Path.home() / "smollm2-360m.gguf"
# Alternatives (swap if needed)
SMOLLM_135M = Path.home() / "smollm2.gguf"
MINICPM_1B = Path.home() / "minicpm5-1b-q2k.gguf"

# Embedding model
EMBED_MODEL = Path.home() / "hourai2-embed.gguf"

# ======================================================================
# VECTOR STORE
# ======================================================================
# Legacy JSON store (still supported)
VECTOR_STORE_FILE = ROOT_DIR / "vector_store.json"
# PocketVectorDB (preferred for phone)
POCKET_VECTOR_DIR = ROOT_DIR / "pocket_vectordb"
EMBED_DIM = 128

# ======================================================================
# PIPELINE SETTINGS
# ======================================================================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3
CONTEXT_SIZE = 512
THREADS = 2
MAX_TOKENS = 40  # reduced for 360M at ~1 tok/s