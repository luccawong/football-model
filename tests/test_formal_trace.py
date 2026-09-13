import pytest

from gpt.decision_engine import MODEL_1_STAGE_ORDER, TicketDecision
from gpt.formal_trace import FrozenH1, RedTeamRecord, StageRecord, build_formal_trace
from gpt.preflight_gate import PreflightGateError


def _required_fields():
    return {stage: () for stage in MODEL_1_STAGE_ORDER}


def _records(draw_label="NOT_EXCLUDED", favourite_handicap=-1.0, *, preflight_complete=True):
    rows = []
    for stage in MODEL_1_STAGE_ORDER:
        evidence = {"ok": True}
        if stage == "market_snapshot":
            evidence = {
                "match_identity_qc": True,
                "snapshot_time": "2026-09-13T12:00:00Z",
                "market_state": "PREMATCH",
                "source_freshness": "CURRENT",
                "missing_core_data": "NONE",
                "missing_core_data_disclosed": True,
            }
        elif stage == "opening_first_impression":
            evidence = {
                "opening_only_view": "done",
                "opening_structure_conclusion": "test",
            }
        elif stage == "opening_rationality_lifecycle":
            evidence = {
                "opening_validity": "VALID",
                "lifecycle_events": ["test"],
            }
        elif stage == "one_x_two_real_vs_camouflage_open":
            evidence = {
                "same_time_slice_comparison": True,
                "real_vs_camouflage_open_audited": True,
            }
        elif stage == "asian_handicap_europe_asia_conversion":
            evidence = {
                "ah_lifecycle": "done",
                "water_lifecycle": "done",
                "europe_asia_conversion_audited": True,
                "ah_all_main_lines_divergence_audited": preflight_complete,
            }
        elif stage == "totals":
            evidence = {
                "ou_reference_line": 2.5,
                "ou_direction": "OVER",
                "ou_independent_conclusion": True,
            }
        elif stage == "draw_exclusion_winner_audit":
            evidence = {
                "authoritative_draw_label": draw_label,
                "draw_branch": "test",
                "draw_audit_completed": True,
            }
            if draw_label == "EXCLUDED":
                evidence.update({
                    "winner_only_audit_completed": True,
                    "draw_removed_from_execution": True,
                })
            elif draw_label == "NOT_EXCLUDED":
                evidence.update({
                    "enhanced_draw_audit_completed": True,
                    "draw_retained_as_active_path": True,
                })
            else:
                evidence.update({
                    "unknown_disclosed": True,
                    "draw_removed_from_execution": False,
                })
        elif stage == "underdog_outright_audit":
            required = draw_label == "EXCLUDED" or favourite_handicap <= -0.75
            evidence = {
                "audit_required": required,
                "audit_completed": required,
                "u_grade": "U1" if required else "U0",
                "outright_vs_cover_separated": required,
            }
        elif stage == "correct_score_poisson_bayesian":
            evidence = {
                "direction_consistency_gate": True,
                "top3_scores": ["2-0", "3-1", "3-0"],
            }
        elif stage == "freeze_h1":
            evidence = {
                "h1_direction": "HOME -1",
                "h1_market": "AH",
                "h1_line": "-1",
                "h1_grade": "B+",
                "h1_frozen_at": "2026-09-09T10:00:00Z",
            }
        elif stage == "red_team_h2":
            evidence = {
                "h2_alternative": "AWAY +1",
                "red_team_verdict": "CONFIRM",
                "strongest_counterevidence": ["draw path"],
                "independent_h2_completed": True,
            }
        elif stage == "formal_main_exactly_one":
            evidence = {
                "ticket_market": "AH",
                "ticket_line": "-1",
                "ticket_direction": "HOME -1",
                "ticket_grade": "B+",
                "actionable_price": ">=1.80",
                "ticket_locked": True,
            }
        rows.append(StageRecord(stage=stage, status="COMPLETE", evidence=evidence))
    return rows


def _build(records, draw_label, favourite_handicap):
    return build_formal_trace(
        match_id="123",
        model_version="MODEL_1",
        policy_version="test",
        quant_engine_version="q",
        feature_engine_version="f",
        records=records,
        required_fields=_required_fields(),
        favourite_handicap=favourite_handicap,
        h1=FrozenH1("HOME -1", "AH", "-1", "B+", "2026-09-09T10:00:00Z"),
        red_team=RedTeamRecord("AWAY +1", "CONFIRM", ["draw path"]),
        ticket=TicketDecision("AH", "-1", "B+", ">=1.80", "HOME -1"),
        current_model_1_policy_loaded=True,
    )


def test_build_valid_not_excluded_trace():
    trace = _build(_records("NOT_EXCLUDED", -1.0), "NOT_EXCLUDED", -1.0)
    assert trace["model_id"] == "MODEL_1"
    assert trace["draw_branch"]["label"] == "NOT_EXCLUDED"
    assert trace["preflight"]["status"] == "PREFLIGHT_PASS"
    assert len(trace["stages"]) == 18
    assert trace["non_main_count"] == 0


def test_build_valid_excluded_trace_forces_winner_branch():
    trace = _build(_records("EXCLUDED", -0.25), "EXCLUDED", -0.25)
    assert trace["draw_branch"]["winner_only_audit"] is True
    assert trace["preflight"]["passed"] is True


def test_formal_trace_is_blocked_when_preflight_is_incomplete():
    with pytest.raises(PreflightGateError):
        _build(_records("NOT_EXCLUDED", -1.0, preflight_complete=False), "NOT_EXCLUDED", -1.0)
