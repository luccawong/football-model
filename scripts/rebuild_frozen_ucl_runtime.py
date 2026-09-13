"""Rebuild the frozen ACTIVE UCL runtime state without recalibration.

The original full-store archive descriptor references chunks that were never
committed.  This recovery path fits only the final UCL state from the audited
historical results, using the already frozen hyperparameters and Train-only
process covariance in the manifest.  It never reads market data and never
changes activation or validation decisions.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from gpt.prior_engine import HyperParameters, fit_league_model, load_titan_matches


COMPETITION = "欧冠"


def rebuild(db_path: str, manifest_path: str, store_path: str, output_path: str) -> dict:
    manifest_file = Path(manifest_path)
    store_file = Path(store_path)
    output_file = Path(output_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    store = json.loads(store_file.read_text(encoding="utf-8"))

    expected_sha = str(manifest["dataset"]["dataset_sha256"])
    from gpt.prior_competition import file_sha256

    if file_sha256(db_path) != expected_sha:
        raise ValueError("Titan mother-source SHA256 mismatch")
    if manifest["competition_status"][COMPETITION]["activation"] != "ACTIVE":
        raise ValueError("Frozen UCL activation is not ACTIVE")
    frozen = manifest["hyperparameters"][COMPETITION]
    if frozen.get("calibration") != "INTERIOR":
        raise ValueError("Frozen UCL hyperparameters are not an approved interior solution")
    if store["competition_status"][COMPETITION]["activation"] != "ACTIVE":
        raise ValueError("Runtime store UCL activation differs from the frozen manifest")

    rows, audit = load_titan_matches(db_path)
    if int(audit["usable_completed_matches"]) != int(manifest["dataset"]["matches_count"]):
        raise ValueError("Usable Titan row count differs from the frozen manifest")
    ucl_rows = [row for row in rows if row["league"] == COMPETITION]
    if not ucl_rows:
        raise ValueError("No completed UCL history in Titan source")
    cutoff = str(store["as_of"])
    hyper = HyperParameters(
        float(frozen["half_life_days"]),
        float(frozen["team_sd"]),
        float(frozen["transition_sd"]),
    )
    model = fit_league_model(
        rows,
        league=COMPETITION,
        as_of=cutoff,
        hyperparameters=hyper,
        include_precision_csc=True,
    )
    model["competition"] = COMPETITION
    model["process_cov_log_lambda"] = manifest["process_covariance"][COMPETITION][
        "process_cov_log_lambda"
    ]
    # Compact runtime propagation needs the Hessian precision, not the dense
    # inverse retained by the fitting API for legacy callers.
    model.pop("covariance", None)
    payload = {
        "artifact_version": "MODEL_1-TITAN-UCL-RUNTIME-RECOVERY-1.0.0",
        "competition": COMPETITION,
        "model": model,
        "provenance": {
            "dataset_sha256": expected_sha,
            "dataset_rows": int(audit["usable_completed_matches"]),
            "competition_rows": len(ucl_rows),
            "state_as_of": cutoff,
            "hyperparameters_source": str(manifest_file.as_posix()),
            "hyperparameters_frozen_before_final_state_fit": True,
            "test_recalibration_performed": False,
            "process_covariance_source": "FROZEN_TRAIN_ONLY_MANIFEST",
            "market_inputs_used": False,
        },
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    output_file.write_bytes(raw)

    try:
        relative = output_file.resolve().relative_to(store_file.resolve().parent).as_posix()
    except ValueError as exc:
        raise ValueError("UCL runtime output must be inside the prior-store directory") from exc
    store.setdefault("model_files", {})[COMPETITION] = {
        "path": relative,
        "sha256": sha256(raw).hexdigest(),
        "format": "SPARSE_PRECISION_JSON",
        "purpose": "ACTIVE_UCL_RUNTIME_RECOVERY",
    }
    if isinstance(store.get("packed_store"), dict):
        store["packed_store"]["availability"] = "INCOMPLETE_LEGACY_ARCHIVE"
        store["packed_store"]["runtime_precedence"] = "MODEL_FILES_FIRST"
    store_file.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument(
        "--manifest", default="database/priors/model_1_titan_prior_manifest.json"
    )
    parser.add_argument("--store", default="database/priors/model_1_titan_prior_store.json")
    parser.add_argument("--output", default="database/priors/european_runtime/ucl.json")
    args = parser.parse_args()
    rebuilt = rebuild(args.db, args.manifest, args.store, args.output)
    print(
        json.dumps(
            {
                "competition": COMPETITION,
                "n_matches": rebuilt["model"]["n_matches"],
                "n_states": rebuilt["model"]["n_states"],
                "converged": rebuilt["model"]["converged"],
            },
            ensure_ascii=False,
        )
    )
