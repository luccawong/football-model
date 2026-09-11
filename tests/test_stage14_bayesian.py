from gpt.stage14_auto import automatic_top3
from gpt.stage14_bayesian import build_bayesian_posterior, posterior_score_summary


def _prior():
    return [
        {"lambda_home": 1.2, "lambda_away": 1.2, "rho": -0.03, "weight": 1.0},
        {"lambda_home": 1.8, "lambda_away": 1.0, "rho": -0.03, "weight": 1.0},
        {"lambda_home": 2.2, "lambda_away": 0.8, "rho": -0.03, "weight": 1.0},
    ]


def _evidence():
    return [
        {
            "evidence_id": "market-cutoff",
            "kind": "market_1x2_ou",
            "validated_for_update": True,
            "independent_update": True,
            "timestamp": "2026-09-11T15:00:00+00:00",
            "target_1x2": {"home": 0.55, "draw": 0.25, "away": 0.20},
            "ou_line": 2.5,
            "target_over_probability": 0.55,
            "sigma_home": 0.08,
            "sigma_draw": 0.08,
            "sigma_over": 0.08,
        }
    ]


def test_bayesian_posterior_drives_score_summary():
    posterior = build_bayesian_posterior(
        prior_particles=_prior(),
        evidence_records=_evidence(),
        prior_provenance={"source": "synthetic-test-prior"},
        cutoff_time="2026-09-11T16:00:00+00:00",
    )
    assert posterior["status"] == "POSTERIOR_VALIDATED"
    assert posterior["formal_stage14_usable"] is True
    assert abs(sum(x["weight"] for x in posterior["posterior_particles"]) - 1.0) < 1e-12

    summary = posterior_score_summary(posterior)
    assert summary["status"] == "BAYESIAN_POSTERIOR_POISSON_DC"
    assert len(summary["top3"]) == 3
    assert 0.0 < summary["posterior_1x2"]["home"] < 1.0


def test_stage14_refuses_market_only_fallback():
    quant_packet = {
        "reconstruction": {
            "Pinnacle": {"lambda_home": 1.8, "lambda_away": 1.1, "rho": -0.03}
        }
    }
    out = automatic_top3(quant_packet, "Pinnacle")
    assert out["status"] == "INSUFFICIENT_SOURCE_DATA"
    assert out["formal_stage14_usable"] is False
    assert out["top3"] == []
    assert out["market_preview"]["status"] == "MARKET_RECONSTRUCTION_PREVIEW_ONLY"


def test_stage14_accepts_validated_posterior():
    posterior = build_bayesian_posterior(
        prior_particles=_prior(),
        evidence_records=_evidence(),
        prior_provenance={"source": "synthetic-test-prior"},
    )
    quant_packet = {
        "reconstruction": {
            "Pinnacle": {"lambda_home": 1.8, "lambda_away": 1.1, "rho": -0.03}
        }
    }
    out = automatic_top3(quant_packet, "Pinnacle", posterior)
    assert out["status"] == "BAYESIAN_POSTERIOR_POISSON_DC"
    assert out["formal_stage14_usable"] is True
    assert out["source_label"] == "BAYESIAN_POSTERIOR_POISSON_DC"
    assert len(out["top3"]) == 3
