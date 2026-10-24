"""
clean_youtube.py — Cuci data YouTube dari spam dan emoji.
Guna:
    python clean_youtube.py
"""

import re
import sys
from pathlib import Path
from typing import List

ROOT_DIR = Path(__file__).parent
RAW_YT_DIR = ROOT_DIR / "raw_data" / "youtube"

# Senarai stopword / parasocial spam
SPAM_WORDS = {"wkwk", "hahaha", "hahah", "kak", "bang", "abang", "kakak", "p", "wkwkwk"}

def is_high_quality(text: str) -> bool:
    """Tapis komen yang cuma emoji atau spam."""
    # 1. Buang emoji & simbol
    clean = re.sub(r'[^\w\s.,?!]', '', text)
    
    # 2. Kira perkataan sebenar
    words = clean.lower().split()
    if len(words) < 5:  # Kena ada sekurang-kurangnya 5 perkataan
        return False
        
    # 3. Kira nisbah spam (kalau lebih 50% perkataan adalah spam)
    spam_count = sum(1 for w in words if w in SPAM_WORDS)
    if (spam_count / len(words)) > 0.5:
        return False
        
    # 4. Elak ayat berulang (contoh: "Financial faiz! Financial faiz!")
    unique_words = set(words)
    if len(unique_words) < 3:
        return False
        
    return True

def clean_file(filepath: Path) -> int:
    """Baca fail, tapis komen, tulis balik."""
    print(f"Processing: {filepath.name}")
    
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n\n") # Andaikan setiap komen dipisahkan oleh baris kosong
    
    # Ambil metadata di atas (--- source... ---)
    header = ""
    comments = lines
    if lines and lines[0].startswith("---"):
        # Gabungkan header block
        end_header_idx = 1
        while end_header_idx < len(lines) and not lines[end_header_idx].strip().endswith("---"):
            end_header_idx += 1
        header = "\n\n".join(lines[:end_header_idx + 1])
        comments = lines[end_header_idx + 1:]

    valid_comments = []
    for c in comments:
        c = c.strip()
        if not c: continue
        
        # Buang prefix "R: " kalau ada
        if c.startswith("R: "):
            c = c[3:]
            
        if is_high_quality(c):
            valid_comments.append(c)
            
    # Tulis balik
    if valid_comments:
        new_content = header + "\n\n" + "\n\n".join(valid_comments)
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  -> Dulu: {len(comments)} komen, Sekarang: {len(valid_comments)} komen (Dibuang: {len(comments) - len(valid_comments)})")
        return len(valid_comments)
    else:
        print(f"  -> SEMUA KOMEN DIBUANG (Sampah). Memadam fail...")
        filepath.unlink()
        return 0

def main():
    print("=== YOUTUBE DATA CLEANER ===")
    if not RAW_YT_DIR.exists():
        print("Folder raw_data/youtube takde.")
        return

    total_kept = 0
    # Cari semua fail .txt dalam folder (termasuk subfolder tarikh)
    for filepath in RAW_YT_DIR.rglob("*.txt"):
        kept = clean_file(filepath)
        total_kept += kept
        
    print(f"\n=== SELESAI. Jumlah komen bersih: {total_kept} ===")

if __name__ == "__main__":
    main()