# Atrric — Working Notes

> **Status:** Living document. Updated as the project evolves.
> **Not a specification.** Not a promise. Not a roadmap commitment.
> Content here reflects current thinking and may change.

---

## What This File Is

A running log of focus areas, progress, and open questions for Atrric.
It exists so that future contributors (and future me) can see what was
being worked on and why.

For setup and usage, see `README.md`. For architecture, see individual
files in `core/`.

---

## What Atrric Is Meant To Be

Atrric is a **market intelligence engine**. Its purpose is to turn
unstructured conversation data into structured, usable insight about
a target audience.

It is not a general-purpose chatbot, not a hosted product, and not a
social media dashboard. It is a tool that runs on the user's own
infrastructure. Users choose their own backend and keep their own data.

Atrric's value depends on four distinct layers:
[1] EXTRACT    Gather raw conversation data from a target source
[2] PROCESS    Clean, chunk, embed, index
[3] GENERATE   Retrieve context and answer queries
[4] REPORT     Package findings as structured insight



Each layer is independent and can be upgraded on its own.

## Layer Status

| Layer | Purpose | Status |
|---|---|---|
| 1. Extract | Acquire raw data | Not implemented (manual only) |
| 2. Process | Chunk + embed + index | Working |
| 3. Generate | Query + LLM answer | Working (limited by model) |
| 4. Report | Structured insight output | Not implemented |

**The current bottleneck is Layer 1.** Everything downstream depends
on having real data to work with. Right now, only manual collection
is in place.

## Why Extract Matters

Without a proper extract layer, Atrric is only as good as whatever
data is dropped into `data/`. The engine itself is ready. The data
supply is not.

An extract layer should:
- Pull from one or more sources (APIs where available, archives,
  or curated datasets)
- Normalise format across sources
- Preserve source attribution
- Respect platform terms and user privacy
- Run without human intervention

This is the first thing to build once the proof of concept is
verified end-to-end.

## Structured Knowledge (Ontology)

Atrric should not treat data as a flat bag of text chunks. To produce
useful insight, the engine needs a structured view of the domain.

This means representing:
- **Entities** — recurring things (audiences, platforms, topics, products)
- **Attributes** — properties of entities (sentiment, frequency, timing)
- **Relationships** — how entities connect

Example for the current domain:
- Audiences: Gen Z, students, young professionals
- Platforms: TikTok, Instagram, Threads, Twitter/X
- Topics: education, cost of living, career, technology
- Relationships: audience uses platform, audience concerned about topic

This structured layer is used to:
- Filter retrieval by entity or relationship
- Expand queries with related concepts
- Organise the final report

Two approaches are planned:
1. **Curated (lightweight)** — a hand-written JSON file mapping
   common entities and relationships for a narrow domain.
2. **Extracted (automated)** — using an LLM to identify entities and
   relationships from the data, stored as a graph.

The curated version is enough for the proof of concept. The automated
version is a later goal.

## What Works Today

- llama.cpp compiled from source for ARMv7 (Android armv8l)
- Three local models tested on-device: 135M, 360M, 1B parameters
- Chunking pipeline (`core/chunk.py`)
- Embedding pipeline (`core/embed.py`)
- Vector store integration with PocketVectorDB (`core/store.py`)
- Query pipeline end-to-end (`query_rag_phone.py`)
- Repository structure, README, requirements, and git hygiene in place

## What's Next (Short Term)

- Add API backend as a selectable LLM option
- Validate pipeline output on a small set of real data
- Document setup for phone and laptop modes
- Stabilise output capture on ARMv7

## Future Ideas (Not Committed)

- Extract pipeline with at least one real source
- Curated structured knowledge layer (entities + relationships)
- Report generation layer
- Larger local model support (3B+) on laptop hardware
- Deployment options for enterprise use

## Open Questions

- Which source is legally and practically the best first target
  for the extract layer?
- How structured should the knowledge layer be for a usable POC
  without over-engineering?
- What does the first useful report actually contain?
- How much of the pipeline can stay fully on-device without
  compromising output quality?

---

*Last updated: 7 October 2026*