# API

## Projects
POST `/v1/projects`
GET `/v1/projects`
GET `/v1/projects/{id}`
DELETE `/v1/projects/{id}`

## Upload
POST `/v1/projects/{id}/uploads/init`
POST `/v1/projects/{id}/uploads/complete`

Local/Drive MVP may instead use server-assisted upload.
R2 production returns direct-upload session.

## Processing
POST `/v1/projects/{id}/process`
Body:
```json
{
  "clip_count": 5,
  "min_duration_s": 20,
  "max_duration_s": 75,
  "framing": "active_speaker",
  "subtitle_preset": "bold_karaoke"
}
```

Response `202`:
```json
{"job_id":"...","status":"queued"}
```

GET `/v1/jobs/{id}`
GET `/v1/jobs/{id}/events` SSE
POST `/v1/jobs/{id}/cancel`

## Results
GET `/v1/projects/{id}/candidates`
POST `/v1/candidates/{id}/accept`
POST `/v1/clips/{id}/render`
GET `/v1/clips/{id}`
GET `/v1/renders/{id}/download`

## Idempotency
Processing/render POST принимает `Idempotency-Key`.

## Errors
Problem Details style:
```json
{
  "code":"UNSUPPORTED_CODEC",
  "message":"...",
  "request_id":"..."
}
```
