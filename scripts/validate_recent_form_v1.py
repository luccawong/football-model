"""Validate the committed RECENT_FORM V1 research artifact set."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gpt.domestic_prior import DOMESTIC
from gpt.recent_form import ARTIFACT_VERSION, canonical_json_sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="database/research/recent_form_v1")
    args = parser.parse_args()
    root = Path(args.root)
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    if summary.get("ucl") != "NOT_CALIBRATED_V1":
        raise SystemExit("UCL must remain NOT_CALIBRATED_V1")
    if int(summary.get("frozen_gate", {}).get("bootstrap_resamples", 0)) < 5000:
        raise SystemExit("paired bootstrap must have >= 5000 resamples")
    for league in DOMESTIC:
        for phase in ("opening", "closing"):
            artifact = json.loads((root / f"{league}_{phase}.json").read_text(encoding="utf-8"))
            unsigned = dict(artifact); expected = unsigned.pop("artifact_sha256", None)
            if artifact.get("artifact_version") != ARTIFACT_VERSION or expected != canonical_json_sha256(unsigned):
                raise SystemExit(f"invalid artifact: {league}/{phase}")
            if artifact.get("source_group") != "RECENT_FORM" or artifact.get("effect_mode") != "QUANTIFIED_OBSERVATION":
                raise SystemExit(f"wrong artifact semantic: {league}/{phase}")
            cell = summary["leagues"][league][phase]
            for split in ("validation", "test"):
                if cell[split]["base"]["n"] != cell[split]["recent"]["n"]:
                    raise SystemExit(f"unpaired comparison: {league}/{phase}/{split}")
                if cell[split]["bootstrap"]["resamples"] < 5000:
                    raise SystemExit(f"bootstrap too small: {league}/{phase}/{split}")
    print("RECENT_FORM_V1_VALID")


if __name__ == "__main__":
    main()
