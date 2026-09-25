# Pipeline & Jobs

## Stage weights
- probing 2%
- extracting_audio 5%
- transcribing 28%
- segmenting 5%
- ranking 10%
- visual_analysis 15%
- rendering 30%
- validating/uploading 5%

Percent — UX estimate, не promise ETA.

## Candidate generation
1. Sentence boundaries.
2. Topic shift / semantic windows.
3. Windows 20–90 sec.
4. Penalize:
   - context dependent openings;
   - unfinished endings;
   - low speech density;
   - long silence.
5. Keep top ~30 cheap candidates.
6. LLM rerank.
7. diversification: не выбирать 5 соседних моментов одной темы.

## Active speaker/crop
- sample/detect faces;
- track identities;
- optional speaker diarization;
- choose target subject;
- dead-zone;
- smoothing;
- scene-cut resets;
- keyframed crop path.

Fallback:
- no face -> center/saliency;
- two faces -> split/padded layout;
- uncertainty -> blur background preset.

## Subtitles
- phrase segmentation 2–6 words;
- ASS;
- word highlight from timestamps;
- safe area;
- no caption over face when avoidable.

## Render
One FFmpeg filtergraph:
trim → scale/background/crop → subtitles → audio normalize optional → h264_nvenc.

Output validation:
- exact dimensions;
- duration tolerance;
- audio stream exists;
- file decodes;
- no zero-byte output.
