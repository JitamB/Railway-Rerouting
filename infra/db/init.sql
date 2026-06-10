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
