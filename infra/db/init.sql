-- CascadeGuard TimescaleDB init (skeleton).
-- Delay events as a time-series hypertable; predictions stored for drift/calibration analysis.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS delay_events (
    event_time     TIMESTAMPTZ NOT NULL,   -- event-time, not processing-time (audit-04 §9)
    received_time  TIMESTAMPTZ NOT NULL,
    train_no       TEXT NOT NULL,
    station        TEXT NOT NULL,
    delay_min      DOUBLE PRECISION NOT NULL,
    source         TEXT NOT NULL,
    regime         TEXT
);
-- SELECT create_hypertable('delay_events', 'event_time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS predictions (
    event_time         TIMESTAMPTZ NOT NULL,
    station            TEXT NOT NULL,
    cascade_risk       DOUBLE PRECISION NOT NULL,
    delay_lower_min    DOUBLE PRECISION,
    delay_upper_min    DOUBLE PRECISION,
    mode               TEXT NOT NULL,
    data_age_s         DOUBLE PRECISION NOT NULL
);
-- SELECT create_hypertable('predictions', 'event_time', if_not_exists => TRUE);
-- Continuous aggregates for dashboard rollups go here (audit-03 §6).

-- Helpline / grievance redressal. PII-bearing: store the minimum, scope to the owner,
-- and honour a retention policy (audit-04 bonus: privacy).
CREATE TABLE IF NOT EXISTS grievance_cases (
    case_id            TEXT PRIMARY KEY,
    passenger_id       TEXT NOT NULL,
    category           TEXT NOT NULL,
    department         TEXT NOT NULL,
    channel            TEXT NOT NULL,
    external_reference TEXT,
    summary            TEXT,
    language           TEXT,
    input_mode         TEXT,            -- 'text' | 'speech'
    transcript         TEXT,
    status             TEXT NOT NULL DEFAULT 'open',  -- open|in_progress|resolved|rejected
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_grievance_passenger ON grievance_cases (passenger_id, created_at DESC);

-- Per-case status changes / messages (the 'My Queries' history view).
CREATE TABLE IF NOT EXISTS grievance_events (
    id        BIGSERIAL PRIMARY KEY,
    case_id   TEXT NOT NULL REFERENCES grievance_cases (case_id),
    at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    status    TEXT NOT NULL,
    note      TEXT
);
