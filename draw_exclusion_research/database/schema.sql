PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS matches (
    research_match_id TEXT PRIMARY KEY,
    competition TEXT NOT NULL,
    competition_normalized TEXT NOT NULL,
    home_team TEXT NOT NULL,
    home_team_normalized TEXT NOT NULL,
    away_team TEXT NOT NULL,
    away_team_normalized TEXT NOT NULL,
    kickoff_time TEXT NOT NULL,
    first_source_market TEXT NOT NULL CHECK (first_source_market IN ('JC', 'BD')),
    titan_match_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS website_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    snapshot_time_utc TEXT NOT NULL,
    snapshot_time_beijing TEXT NOT NULL,
    source_url TEXT NOT NULL,
    http_date TEXT,
    page_update_time TEXT,
    http_last_modified TEXT,
    sha256 TEXT NOT NULL,
    html_size INTEGER NOT NULL CHECK (html_size > 0),
    html_path TEXT NOT NULL UNIQUE,
    content_version INTEGER NOT NULL CHECK (content_version >= 1),
    same_hash_as_previous INTEGER,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_website_snapshots_time ON website_snapshots(snapshot_time_utc);
CREATE INDEX IF NOT EXISTS ix_website_snapshots_hash ON website_snapshots(sha256);

CREATE TABLE IF NOT EXISTS snapshot_diffs (
    snapshot_id TEXT PRIMARY KEY REFERENCES website_snapshots(snapshot_id),
    previous_snapshot_id TEXT REFERENCES website_snapshots(snapshot_id),
    added_rows INTEGER NOT NULL DEFAULT 0,
    deleted_rows INTEGER NOT NULL DEFAULT 0,
    label_changed_rows INTEGER NOT NULL DEFAULT 0,
    odds_changed_rows INTEGER NOT NULL DEFAULT 0,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS website_labels (
    snapshot_id TEXT NOT NULL REFERENCES website_snapshots(snapshot_id),
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    source_market TEXT NOT NULL CHECK (source_market IN ('JC', 'BD')),
    website_draw_exclusion_label INTEGER NOT NULL CHECK (website_draw_exclusion_label IN (0, 1)),
    site_row_index INTEGER NOT NULL CHECK (site_row_index >= 0),
    site_data_key TEXT NOT NULL,
    match_number TEXT NOT NULL,
    is_single_game INTEGER NOT NULL CHECK (is_single_game IN (0, 1)),
    PRIMARY KEY (snapshot_id, research_match_id, source_market)
);

CREATE INDEX IF NOT EXISTS ix_website_labels_match ON website_labels(research_match_id);
CREATE INDEX IF NOT EXISTS ix_website_labels_market_label ON website_labels(source_market, website_draw_exclusion_label);

CREATE TABLE IF NOT EXISTS site_visible_odds (
    snapshot_id TEXT NOT NULL,
    research_match_id TEXT NOT NULL,
    source_market TEXT NOT NULL,
    home_1x2 REAL,
    draw_1x2 REAL,
    away_1x2 REAL,
    asian_line REAL,
    asian_line_raw TEXT,
    home_water REAL,
    away_water REAL,
    PRIMARY KEY (snapshot_id, research_match_id, source_market),
    FOREIGN KEY (snapshot_id, research_match_id, source_market)
        REFERENCES website_labels(snapshot_id, research_match_id, source_market)
);

CREATE TABLE IF NOT EXISTS match_resolutions (
    snapshot_id TEXT NOT NULL,
    research_match_id TEXT NOT NULL,
    source_market TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('resolved', 'ambiguous', 'not_found', 'unavailable')),
    titan_match_id TEXT,
    matched_by TEXT,
    candidate_count INTEGER NOT NULL DEFAULT 0,
    candidates_json TEXT NOT NULL DEFAULT '[]',
    source_batch TEXT,
    resolved_at TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, research_match_id, source_market),
    FOREIGN KEY (snapshot_id, research_match_id, source_market)
        REFERENCES website_labels(snapshot_id, research_match_id, source_market)
);

CREATE TABLE IF NOT EXISTS external_1x2 (
    event_id TEXT PRIMARY KEY,
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    titan_match_id TEXT,
    company TEXT NOT NULL,
    odds_time TEXT,
    home REAL NOT NULL,
    draw REAL NOT NULL,
    away REAL NOT NULL,
    quote_role TEXT,
    source TEXT NOT NULL,
    source_record_id TEXT,
    raw_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_external_1x2_match_time ON external_1x2(research_match_id, odds_time);
CREATE INDEX IF NOT EXISTS ix_external_1x2_company_time ON external_1x2(company, odds_time);

CREATE TABLE IF NOT EXISTS external_ah (
    event_id TEXT PRIMARY KEY,
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    titan_match_id TEXT,
    company TEXT NOT NULL,
    odds_time TEXT,
    line REAL NOT NULL,
    home_price REAL NOT NULL,
    away_price REAL NOT NULL,
    quote_role TEXT,
    source TEXT NOT NULL,
    source_record_id TEXT,
    raw_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_external_ah_match_time ON external_ah(research_match_id, odds_time);

CREATE TABLE IF NOT EXISTS external_ou (
    event_id TEXT PRIMARY KEY,
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    titan_match_id TEXT,
    company TEXT NOT NULL,
    odds_time TEXT,
    line REAL NOT NULL,
    over_price REAL NOT NULL,
    under_price REAL NOT NULL,
    quote_role TEXT,
    source TEXT NOT NULL,
    source_record_id TEXT,
    raw_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_external_ou_match_time ON external_ou(research_match_id, odds_time);

CREATE TABLE IF NOT EXISTS final_results (
    research_match_id TEXT PRIMARY KEY REFERENCES matches(research_match_id),
    home_score INTEGER NOT NULL CHECK (home_score >= 0),
    away_score INTEGER NOT NULL CHECK (away_score >= 0),
    is_draw INTEGER NOT NULL CHECK (is_draw IN (0, 1)),
    home_win INTEGER NOT NULL CHECK (home_win IN (0, 1)),
    away_win INTEGER NOT NULL CHECK (away_win IN (0, 1)),
    result_1x2 TEXT NOT NULL CHECK (result_1x2 IN ('HOME', 'DRAW', 'AWAY')),
    source TEXT NOT NULL,
    settled_at TEXT NOT NULL,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS feature_snapshots (
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    feature_time TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    minutes_to_kickoff REAL NOT NULL,
    opening_validity TEXT,
    feature_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (research_match_id, feature_time, feature_version)
);

CREATE TABLE IF NOT EXISTS model_outputs (
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    model_version TEXT NOT NULL,
    prediction_time TEXT NOT NULL,
    draw_exclusion_probability REAL CHECK (draw_exclusion_probability BETWEEN 0 AND 1),
    draw_probability REAL CHECK (draw_probability BETWEEN 0 AND 1),
    classification TEXT NOT NULL CHECK (classification IN ('KEEP_DRAW', 'WEAK_EXCLUDE', 'EXCLUDE', 'STRONG_EXCLUDE')),
    teacher_label INTEGER CHECK (teacher_label IN (0, 1)),
    teacher_agreement INTEGER CHECK (teacher_agreement IN (0, 1)),
    positive_evidence_json TEXT NOT NULL DEFAULT '[]',
    negative_evidence_json TEXT NOT NULL DEFAULT '[]',
    conflicts_json TEXT NOT NULL DEFAULT '[]',
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    PRIMARY KEY (research_match_id, model_version, prediction_time)
);

CREATE TABLE IF NOT EXISTS rule_candidates (
    rule_id TEXT PRIMARY KEY,
    rule_version TEXT NOT NULL,
    rule_json TEXT NOT NULL,
    sample_size INTEGER NOT NULL,
    teacher_precision REAL,
    actual_non_draw_rate REAL,
    league_distribution_json TEXT NOT NULL DEFAULT '{}',
    failure_conditions_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS teacher_evaluation AS
SELECT
    wl.snapshot_id,
    wl.research_match_id,
    wl.source_market,
    wl.website_draw_exclusion_label,
    fr.is_draw,
    CASE
        WHEN wl.website_draw_exclusion_label = 1 AND fr.is_draw = 0 THEN 1
        WHEN wl.website_draw_exclusion_label = 1 AND fr.is_draw = 1 THEN 0
        ELSE NULL
    END AS teacher_exclusion_success
FROM website_labels wl
LEFT JOIN final_results fr USING (research_match_id);
