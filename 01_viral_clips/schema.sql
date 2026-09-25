CREATE TABLE projects (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL,
  name text NOT NULL,
  status text NOT NULL,
  language text,
  desired_clip_count integer NOT NULL DEFAULT 5,
  settings_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  pipeline_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);

CREATE INDEX idx_projects_owner_created
ON projects(owner_id, created_at DESC)
WHERE deleted_at IS NULL;

CREATE TABLE artifacts (
  id uuid PRIMARY KEY,
  project_id uuid NOT NULL REFERENCES projects(id),
  kind text NOT NULL,
  provider text NOT NULL,
  storage_key text NOT NULL,
  sha256 char(64),
  bytes bigint,
  mime_type text,
  duration_ms bigint,
  width integer,
  height integer,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz,
  UNIQUE(provider, storage_key)
);

CREATE TABLE candidates (
  id uuid PRIMARY KEY,
  project_id uuid NOT NULL REFERENCES projects(id),
  start_ms bigint NOT NULL,
  end_ms bigint NOT NULL,
  title text,
  scores jsonb NOT NULL,
  final_score numeric(6,3) NOT NULL,
  reason text,
  rank integer,
  scorer_version text NOT NULL,
  accepted boolean,
  CHECK (end_ms > start_ms)
);

CREATE TABLE jobs (
  id uuid PRIMARY KEY,
  project_id uuid NOT NULL REFERENCES projects(id),
  type text NOT NULL,
  status text NOT NULL,
  stage text,
  progress smallint NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  attempt integer NOT NULL DEFAULT 0,
  idempotency_key text NOT NULL,
  error_code text,
  error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz,
  UNIQUE(project_id, idempotency_key)
);
