# Acceptance Criteria

MVP accepted when:
- 20 golden videos process without manual pipeline repair;
- output 1080x1920 H.264/AAC;
- rerender caption preset does not rerun ASR;
- job retry resumes from valid stage/artifacts;
- failed job does not leak temp files;
- top-5 candidates are logged with score dimensions/reason;
- exact model/prompt/pipeline version reproducible;
- browser can leave processing page and return;
- no secret exposed to frontend;
- deletion removes persistent artifacts;
- README can bootstrap clean machine.

Product gate:
At least 3 users use it twice or quality metric gives a credible reason to continue.
