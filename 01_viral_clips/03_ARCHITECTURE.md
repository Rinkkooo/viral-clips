# Architecture

```text
Browser
  │
  ├─ metadata/API ───────────────► FastAPI ─────► PostgreSQL
  │                                  │
  │                                  └────► Redis Queue
  │                                            │
  │                                            ▼
  │                                      GPU/Video Worker
  │                                     /   |   |    \
  │                                  ASR   LLM  CV   FFmpeg
  │
  └─ file upload ──► Storage Adapter ◄───────────────┘
                     Local/Drive/R2
```

## Core pipeline
```text
probe
→ extract audio
→ ASR
→ semantic candidate windows
→ cheap heuristic pre-rank
→ LLM re-rank
→ select clips
→ scene/face analysis
→ crop plan
→ subtitle plan
→ one-pass final render
→ validate output
```

## Important architecture rules
- ASR artifact reusable across rerenders.
- Highlight decisions reusable across caption changes.
- Crop plan separate from render command.
- Final render ideally one encode pass.
- Provider implementations behind interfaces.
- GPU concurrency configurable, default 1 on RTX 4060 8 GB.

## Intermediate artifacts
- `probe.json`
- `transcript.json`
- `candidates.json`
- `ranking.json`
- `crop_plan.json`
- `subtitle.ass`
- `render_manifest.json`

Каждый содержит schema_version.
