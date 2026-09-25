# Database

## Entities

### users
- id uuid pk
- email citext unique
- created_at

### projects
- id
- owner_id fk
- name
- source_artifact_id
- status
- language
- desired_clip_count
- settings_json jsonb
- pipeline_version
- created_at
- updated_at
- deleted_at

Indexes:
- owner_id, created_at desc
- status

### artifacts
Общая таблица storage metadata.
- id
- project_id
- kind
- provider
- key
- sha256
- bytes
- mime_type
- duration_ms nullable
- width nullable
- height nullable
- created_at
- expires_at

Unique(provider,key).

### transcripts
- id
- project_id
- artifact_id
- model
- model_version
- language
- duration_ms
- words_json/artifact reference
- created_at

Для больших transcript лучше payload в JSON/Parquet artifact, DB хранит metadata + searchable segments отдельно.

### transcript_segments
- id bigint
- transcript_id
- ordinal
- start_ms
- end_ms
- text
Index transcript_id, ordinal.

### candidates
- id
- project_id
- start_ms
- end_ms
- title
- scores jsonb
- final_score numeric
- reason text
- rank
- scorer_version
- accepted bool nullable

### clips
- id
- project_id
- candidate_id nullable
- start_ms
- end_ms
- status
- current_render_id
- created_at

### renders
- id
- clip_id
- render_version
- crop_plan_artifact_id
- subtitle_artifact_id
- output_artifact_id
- preset_json
- encoder
- started_at
- completed_at
- error_code

### jobs
- id
- project_id
- type
- status
- stage
- progress smallint
- attempt
- idempotency_key
- error_code
- error_message
- created_at
- started_at
- finished_at

Unique(owner/project scope, idempotency_key) as appropriate.
