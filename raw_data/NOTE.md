```markdown
# NOTE

The data in this directory is **raw** — as collected.

**This is NOT Gen Z data.**
**This is NOT filtered.**
**This is NOT representative.**

## Sources

### Threads (Meta)
- Method: manual copy
- Filter applied: education-related topics only
- Age filter: NONE (Threads does not expose age metadata)

### YouTube
- Method: automated (yt-dlp, comment extraction)
- Filter applied during conversion: promo/pinned/short comments removed
- Age filter: NONE (YouTube does not expose reliable age metadata)

## Scope Clarification
This dataset captures public discourse on education-related topics
from Threads and YouTube users. It does not claim to represent
Gen Z Malaysia, nor any specific demographic group.

Demographic filtering is deferred to the processing layer.
It is not applied here.

## Rules
- Copy as-is. Do not edit content.
- Only include comments that carry substance (conversation).
- Exclude: emoji-only comments, spam, advertisements.
- Strip usernames, full names, and photos before saving.
- Raw JSON from yt-dlp is gitignored (contains usernames/IDs).

## Folder Structure

```

raw_data/
├── NOTE.md
├── threads/           ← manual copy (Threads)
│   └── pendidikan.txt
├── youtube/           ← yt-dlp converted (YouTube)
│   └── pendidikan.txt
└── yt/                ← raw yt-dlp JSON (gitignored, local only)
└── <video_id>.info.json

```

## Raw Data Format

All `.txt` files under `raw_data/` follow this format.

### Structure

```

[Post n]
OP: <original post>

R: <reply to OP>
R:R: <reply to R:>
R:R:R: <reply to R:R:>
R: <new chain, reply to OP>

---

[Post n+1]
OP: ...

```

### Level rule
- `R:` = reply to OP
- `R:R:` = one level deeper (reply to reply)
- Each deeper level = one more `R:`

### Between posts
- Separate posts with `---`
- Number sequentially: `[Post 1]`, `[Post 2]`, ...

### Threads-specific note
Manual Threads data preserves nested reply depth (R:, R:R:, R:R:R:...)

### YouTube-specific note
YouTube data is flattened: all top-level comments → `R:`,
all replies → `R:R:` (source API does not expose full nesting depth)
```