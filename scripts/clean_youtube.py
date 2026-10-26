"""
clean_youtube.py — Cuci data YouTube dari spam dan emoji.
v2: Baca baris demi baris (splitlines), bukan perenggan.
"""

import re
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).parent
RAW_YT_DIR = ROOT_DIR / "raw_data" / "youtube"

# Senarai stopword / parasocial spam
SPAM_WORDS = {"wkwk", "hahaha", "hahah", "kak", "bang", "abang", "kakak", "wkwkwk", "hahahaha"}

def is_high_quality(text: str) -> bool:
    """Tapis komen yang cuma emoji atau spam."""
    # 1. Buang emoji & simbol pelik
    clean = re.sub(r'[^\w\s.,?!]', '', text)
    
    # 2. Kira perkataan sebenar
    words = clean.lower().split()
    if len(words) < 5:  # Kena ada sekurang-kurangnya 5 perkataan
        return False
        
    # 3. Kira nisbah spam (kalau lebih 50% perkataan adalah spam)
    spam_count = sum(1 for w in words if w in SPAM_WORDS)
    if len(words) > 0 and (spam_count / len(words)) > 0.5:
        return False
        
    # 4. Elak ayat berulang (contoh: "Financial faiz! Financial faiz!")
    unique_words = set(words)
    if len(unique_words) < 3:
        return False
        
    return True

def clean_file(filepath: Path) -> int:
    """Baca fail, tapis baris demi baris, tulis balik."""
    print(f"Processing: {filepath.name}")
    
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines() # <--- GUNA SPLITLINES (Baca setiap baris)
    
    header_lines = []
    valid_comments = []
    total_original = 0
    
    in_header = True
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Simpan header metadata (--- source: ... ---)
        if in_header:
            header_lines.append(line)
            if line == "---" and len(header_lines) > 1:
                in_header = False
            continue
            
        total_original += 1
        
        # Buang prefix "R: " atau "R:R: " kalau ada
        if line.startswith("R:"):
            # Buang semua "R:" atau "R:R:"
            line = re.sub(r'^(R:)+', '', line).strip()
            
        if is_high_quality(line):
            valid_comments.append(line)
            
    # Tulis balik
    if valid_comments:
        new_content = "\n".join(header_lines) + "\n\n" + "\n".join(valid_comments)
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  -> Dulu: {total_original} baris, Sekarang: {len(valid_comments)} komen (Dibuang: {total_original - len(valid_comments)})")
        return len(valid_comments)
    else:
        print(f"  -> SEMUA BARIS DIBUANG (Sampah). Memadam fail...")
        filepath.unlink()
        return 0

def main():
    print("=== YOUTUBE DATA CLEANER v2 ===")
    if not RAW_YT_DIR.exists():
        print("Folder raw_data/youtube takde.")
        return

    total_kept = 0
    # Cari semua fail .txt dalam folder
    for filepath in RAW_YT_DIR.rglob("*.txt"):
        kept = clean_file(filepath)
        total_kept += kept
        
    print(f"\n=== SELESAI. Jumlah komen bersih: {total_kept} ===")

if __name__ == "__main__":
    main()