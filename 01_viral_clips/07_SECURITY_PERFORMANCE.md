# Security & Performance

## Media validation
ffprobe sandboxed.
Limits:
- max duration configurable;
- max pixels/frame;
- max fps;
- max streams;
- max bytes.

Filename ignored as path.

## Cost guard
Per project:
- source minutes quota;
- clips per run;
- max concurrent jobs;
- LLM token budget;
- cloud ASR fallback cap.

## Performance
RTX 4060 local:
- GPU worker concurrency default 1;
- do not run ASR + heavy NVENC + CV concurrently until benchmark;
- reuse decode where feasible;
- proxy video for browser previews;
- cache transcript/crop/subtitle artifacts.

## Storage
Working video local SSD.
Drive/R2 is persistent source/sink, not frame-by-frame I/O.

## Retry
Safe retry:
- uploads;
- LLM;
- storage.
Render retry only from preserved manifest.
No retry loops without attempt cap.
