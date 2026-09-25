# Implementation Phases

## Phase 0 — Repo & media probe
- repo;
- config;
- ffmpeg detection;
- ffprobe;
- sample CLI.
Gate: corrupted/valid files classified correctly.

## Phase 1 — ASR
- audio extraction;
- Faster-Whisper;
- word timestamps;
- transcript JSON.
Gate: 10 samples successful.

## Phase 2 — Highlight engine
- segmentation;
- heuristic scorer;
- LLM structured rerank;
- top-N CLI output.
Gate: manual review publishable_top5 baseline recorded.

## Phase 3 — Render engine
- static crop + blur fallback;
- ASS captions;
- NVENC;
- manifests.
Gate: 1080x1920 valid clips.

## Phase 4 — Smart reframe
- face detect;
- tracking;
- smoothing;
- active speaker approximation.
Gate: face_visible_ratio target on golden set.

## Phase 5 — Persistence
- PostgreSQL;
- artifacts;
- jobs;
- versioning.

## Phase 6 — Worker/API
- Redis;
- durable worker;
- FastAPI;
- SSE;
- cancel/retry/idempotency.

## Phase 7 — Web UI
- dashboard;
- upload;
- processing;
- results/editor;
- export.

## Phase 8 — Storage
- Drive archive adapter;
- R2 adapter;
- cleanup lifecycle.

## Phase 9 — Security/observability
- auth;
- quotas;
- audit;
- metrics/tracing;
- backups.

## Phase 10 — Beta
- 5–10 users;
- usage feedback;
- decide niche.
