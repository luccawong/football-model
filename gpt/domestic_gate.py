"""Frozen domestic V2 release gate, shared by reporting and formal runtime."""
from math import isfinite


def activation_gate(validation, test, selected, trust):
    statuses = {}
    for phase in ("opening", "closing"):
        reasons = []
        insufficient = False
        if selected.get("boundary") or trust[phase].get("boundary"):
            reasons.append("UNRESOLVED_TRAIN_BOUNDARY")
        for period, report in (("validation", validation), ("test", test)):
            a, c = report[phase]["A"], report[phase]["C"]
            if min(a.get("n", 0), c.get("n", 0)) < 80:
                insufficient = True
                reasons.append(period + ":INSUFFICIENT_HISTORY")
            checks = (("correct_score_NLL", 0), ("1X2_Brier", 0), ("RPS", 0),
                      ("OU_over2_5_Brier", .005), ("AH_settlement_aware_Brier", .005))
            for key, tolerance in checks:
                if a.get(key) is None or c.get(key) is None or not all(isfinite(v) for v in (a[key], c[key])):
                    reasons.append(period + ":MISSING_" + key)
                elif c[key] > a[key] + tolerance:
                    reasons.append(period + ":" + ("SCORE_NLL_WORSE" if key == "correct_score_NLL" else key + "_HARM"))
            if a.get("Top3_coverage") is None or c.get("Top3_coverage") is None or not all(isfinite(v) for v in (a["Top3_coverage"], c["Top3_coverage"])):
                reasons.append(period + ":MISSING_TOP3")
            elif c["Top3_coverage"] < a["Top3_coverage"] - .01:
                reasons.append(period + ":TOP3_HARM")
        status = "INSUFFICIENT_HISTORY" if insufficient else "SHADOW" if reasons else "ACTIVE"
        statuses[phase] = {"status": status, "reasons": reasons or ["OOS_GATE_PASS"]}
    active = [p for p in statuses if statuses[p]["status"] == "ACTIVE"]
    statuses["activation"] = "ACTIVE" if active else "SHADOW"
    if all(statuses[p]["status"] == "INSUFFICIENT_HISTORY" for p in ("opening", "closing")):
        statuses["activation"] = "INSUFFICIENT_HISTORY"
    statuses["lifecycle"] = "BOTH_ACTIVE" if len(active) == 2 else active[0].upper() + "_ACTIVE" if active else "SHADOW"
    return statuses
