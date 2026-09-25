# UX/UI

## Screens
### 1. Dashboard
Cards:
- New project.
- Recent projects.
- Processing jobs.
- Storage usage.

### 2. New Project
Step 1: upload.
Step 2: language.
Step 3: desired clips 3/5/10.
Step 4: duration range.
Step 5: framing preset.
Step 6: subtitle preset.
Advanced collapsed.

Primary CTA: `Generate clips`.

### 3. Processing
- source thumbnail;
- stage;
- percent;
- stage-specific text;
- cancel;
- background-safe: можно уйти со страницы.

### 4. Results
Left: candidate list.
Center: vertical player.
Right inspector:
- score breakdown;
- reason;
- trim start/end;
- framing mode;
- caption preset;
- rerender.

Candidate card:
- title;
- duration;
- score;
- hook excerpt;
- processing state.

### 5. Transcript
Searchable transcript с word/segment timestamps.
Click segment -> seek video.

## Editor scope
MVP не является CapCut.
Разрешено:
- trim;
- choose crop mode;
- move crop focus keyframe manually;
- caption preset;
- font size;
- export.

## Error UX
- unsupported codec -> explain conversion option;
- no audio -> block ASR but allow manual visual clip only later;
- GPU out of memory -> retry lower ASR model / CPU fallback;
- render failed -> preserve all upstream artifacts and retry only render.
