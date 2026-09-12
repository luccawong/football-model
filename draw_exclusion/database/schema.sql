-- Extensions layered on top of draw_exclusion_research/database/schema.sql.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS match_crosswalk (
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    titan_match_id TEXT,
    source_match_id TEXT NOT NULL,
    source_market TEXT NOT NULL CHECK (source_market IN ('JC', 'BD')),
    competition TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    kickoff_time TEXT NOT NULL,
    resolution_status TEXT NOT NULL,
    matched_by TEXT,
    confidence REAL CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    source_snapshot_id TEXT NOT NULL REFERENCES website_snapshots(snapshot_id),
    provenance_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    PRIMARY KEY (research_match_id, source_market, source_snapshot_id)
);

CREATE INDEX IF NOT EXISTS ix_match_crosswalk_titan ON match_crosswalk(titan_match_id);

CREATE TABLE IF NOT EXISTS manual_teacher_labels (
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    label INTEGER NOT NULL CHECK (label IN (0, 1)),
    source_name TEXT NOT NULL,
    evidence_url TEXT,
    note TEXT,
    entered_by TEXT NOT NULL,
    entered_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    PRIMARY KEY (research_match_id, entered_at)
);

CREATE TABLE IF NOT EXISTS forensic_evidence (
    evidence_id TEXT PRIMARY KEY,
    snapshot_id TEXT REFERENCES website_snapshots(snapshot_id),
    research_match_id TEXT REFERENCES matches(research_match_id),
    evidence_type TEXT NOT NULL CHECK (evidence_type IN ('SCREENSHOT', 'HTML', 'NOTE')),
    path_or_url TEXT NOT NULL,
    sha256 TEXT,
    captured_at TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS formal_snapshot_diffs (
    snapshot_id TEXT PRIMARY KEY REFERENCES website_snapshots(snapshot_id),
    previous_snapshot_id TEXT,
    added_rows INTEGER NOT NULL,
    deleted_rows INTEGER NOT NULL,
    label_changed_rows INTEGER NOT NULL,
    odds_changed_rows INTEGER NOT NULL,
    time_changed_rows INTEGER NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_evaluation (
    research_match_id TEXT NOT NULL REFERENCES matches(research_match_id),
    titan_match_id TEXT,
    competition TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    kickoff_time TEXT NOT NULL,
    source_market TEXT NOT NULL CHECK (source_market IN ('JC', 'BD')),
    external_draw_exclusion_label INTEGER CHECK (external_draw_exclusion_label IN (0, 1)),
    external_label_snapshot_time TEXT,
    label_origin TEXT,
    our_draw_exclusion_class TEXT CHECK (
        our_draw_exclusion_class IS NULL OR our_draw_exclusion_class IN
        ('KEEP_DRAW', 'WEAK_EXCLUDE', 'EXCLUDE', 'STRONG_EXCLUDE')
    ),
    our_draw_probability REAL CHECK (our_draw_probability IS NULL OR our_draw_probability BETWEEN 0 AND 1),
    our_draw_exclusion_confidence REAL CHECK (
        our_draw_exclusion_confidence IS NULL OR our_draw_exclusion_confidence BETWEEN 0 AND 1
    ),
    winner_direction TEXT CHECK (winner_direction IS NULL OR winner_direction IN ('HOME', 'AWAY')),
    winner_model_pick TEXT CHECK (winner_model_pick IS NULL OR winner_model_pick IN ('HOME', 'AWAY')),
    final_home_score INTEGER CHECK (final_home_score IS NULL OR final_home_score >= 0),
    final_away_score INTEGER CHECK (final_away_score IS NULL OR final_away_score >= 0),
    final_is_draw INTEGER CHECK (final_is_draw IS NULL OR final_is_draw IN (0, 1)),
    teacher_correct INTEGER CHECK (teacher_correct IS NULL OR teacher_correct IN (0, 1)),
    student_correct INTEGER CHECK (student_correct IS NULL OR student_correct IN (0, 1)),
    teacher_student_agreement INTEGER CHECK (teacher_student_agreement IS NULL OR teacher_student_agreement IN (0, 1)),
    winner_pick_correct INTEGER CHECK (winner_pick_correct IS NULL OR winner_pick_correct IN (0, 1)),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (research_match_id, source_market, external_label_snapshot_time)
);

CREATE VIEW IF NOT EXISTS teacher_student_buckets AS
SELECT *,
    CASE
        WHEN external_draw_exclusion_label = 1 AND our_draw_exclusion_class IN ('EXCLUDE', 'STRONG_EXCLUDE') THEN 'A'
        WHEN external_draw_exclusion_label = 1 AND our_draw_exclusion_class = 'KEEP_DRAW' THEN 'B'
        WHEN external_draw_exclusion_label = 0 AND our_draw_exclusion_class IN ('EXCLUDE', 'STRONG_EXCLUDE') THEN 'C'
        WHEN external_draw_exclusion_label = 0 AND our_draw_exclusion_class = 'KEEP_DRAW' THEN 'D'
        ELSE NULL
    END AS research_bucket
FROM research_evaluation;

-- Existing compound primary keys remain intact. These views expose explicit
-- market fields while retaining every historical snapshot and Titan mapping.
CREATE VIEW IF NOT EXISTS jc_layer AS
SELECT e.research_match_id, e.research_match_id || '|JC' AS market_key,
       e.titan_match_id, e.external_draw_exclusion_label AS jc_draw_exclusion_label,
       CASE e.external_draw_exclusion_label WHEN 1 THEN 'MATCHED_EXCLUDED'
            WHEN 0 THEN 'MATCHED_NOT_EXCLUDED' ELSE 'UNKNOWN' END AS jc_status,
       s.snapshot_id AS jc_snapshot_id, e.external_label_snapshot_time AS jc_snapshot_time,
       s.source_url AS jc_source,
       json_object('label_origin', e.label_origin, 'snapshot_id', s.snapshot_id,
                   'sha256', s.sha256, 'source_url', s.source_url) AS jc_provenance
FROM research_evaluation e
LEFT JOIN website_snapshots s ON s.snapshot_time_beijing = e.external_label_snapshot_time
WHERE e.source_market = 'JC';

CREATE VIEW IF NOT EXISTS bd_layer AS
SELECT e.research_match_id, e.research_match_id || '|BD' AS market_key,
       e.titan_match_id, e.external_draw_exclusion_label AS bd_draw_exclusion_label,
       CASE e.external_draw_exclusion_label WHEN 1 THEN 'MATCHED_EXCLUDED'
            WHEN 0 THEN 'MATCHED_NOT_EXCLUDED' ELSE 'UNKNOWN' END AS bd_status,
       s.snapshot_id AS bd_snapshot_id, e.external_label_snapshot_time AS bd_snapshot_time,
       s.source_url AS bd_source,
       json_object('label_origin', e.label_origin, 'snapshot_id', s.snapshot_id,
                   'sha256', s.sha256, 'source_url', s.source_url) AS bd_provenance
FROM research_evaluation e
LEFT JOIN website_snapshots s ON s.snapshot_time_beijing = e.external_label_snapshot_time
WHERE e.source_market = 'BD';
