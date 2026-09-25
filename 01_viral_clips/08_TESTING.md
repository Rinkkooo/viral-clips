# Testing

## Golden dataset
Minimum 20 videos:
- single speaker;
- two speakers;
- podcast wide shot;
- scene cuts;
- low light;
- no faces;
- gaming;
- Russian;
- English;
- noisy audio.

## Tests
Unit:
- candidate windows;
- score formula;
- subtitle segmentation;
- crop smoothing.

Integration:
- ffprobe;
- short FFmpeg render;
- ASR fixture;
- DB jobs.

Golden:
- expected candidate intervals within tolerance;
- face visibility metrics;
- subtitle timing.

E2E:
upload 60s sample → process → result → rerender → download.

## Regression
Store metrics by pipeline version.
A new model/prompt cannot silently reduce quality.
