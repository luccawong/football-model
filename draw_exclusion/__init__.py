"""Formal external draw-exclusion label layer.

Only a row explicitly present in a successful source snapshot can carry a
binary label.  Absence from that pool is represented as ``None``.
"""

LABEL_EXCLUDED = 1
LABEL_NOT_EXCLUDED = 0
LABEL_UNKNOWN = None

MATCHED_EXCLUDED = "MATCHED_EXCLUDED"
MATCHED_NOT_EXCLUDED = "MATCHED_NOT_EXCLUDED"
NOT_IN_SOURCE_POOL = "NOT_IN_SOURCE_POOL"
SOURCE_SNAPSHOT_MISSING = "SOURCE_SNAPSHOT_MISSING"
AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
MATCH_FAILED = "MATCH_FAILED"

