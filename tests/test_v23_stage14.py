from gpt.stage14_auto import automatic_top3, market_reconstruction_top3
from src.parser.titan_md import read_markdown_tables_text


def _quant_packet():
    return {
        "match_id": "123",
        "reconstruction": {
            "Pinnacle": {
                "lambda_home": 1.60,
                "lambda_away": 1.00,
                "rho": -0.05,
                "max_abs_residual": 0.004,
            },
            "Bet365": {
                "lambda_home": 1.55,
                "lambda_away": 1.05,
                "rho": -0.04,
                "max_abs_residual": 0.006,
            },
            "Macau": {
                "lambda_home": 1.66,
                "lambda_away": 0.98,
                "rho": -0.06,
                "max_abs_residual": 0.005,
            },
        },
    }


def _prior():
    return {
        "status": "VALID",
        "mean_log_lambda": [0.42, 0.03],
        "cov_log_lambda": [[0.09, 0.01], [0.01, 0.09]],
        "source_groups": ["TEAM_DATA"],
        "calibration_ref": "test-prior",
    }


def test_markdown_parser_reads_named_jsonl_tables():
    text = '''# MATCH 123

### Europe 1X2 (`Europe_1x2`) — 1 rows

```jsonl
{"match_id":"123","company":"Pinnacle","current_home":3.0,"current_draw":3.4,"current_away":2.2}
```

### Over Under Current MAIN (`OverUnder_Current`) — 1 rows

```jsonl
{"match_id":"123","company":"Pinnacle","current_left":0.9,"current_line":"2.5","current_right":0.9}
```
'''
    tables = read_markdown_tables_text(text)
    assert tables["Europe_1x2"][0]["match_id"] == "123"
    assert tables["OverUnder_Current"][0]["current_line"] == "2.5"


def test_market_reconstruction_top3_is_research_only():
    result = market_reconstruction_top3(_quant_packet(), "Pinnacle")
    assert result["status"] == "MARKET_RECONSTRUCTION_RESEARCH_ONLY"
    assert result["formal_stage14"] is False
    assert len(result["top3"]) == 3


def test_formal_automatic_top3_requires_prior():
    result = automatic_top3(_quant_packet(), "Pinnacle")
    assert result["status"] == "MISSING"
    assert result["reason"] == "BAYESIAN_PRIOR_REQUIRED"
    assert result["no_market_only_fallback"] is True


def test_formal_automatic_top3_uses_bayesian_posterior():
    result = automatic_top3(
        _quant_packet(),
        prior_packet=_prior(),
        execution_path={"winner": "HOME", "ou": {"side": "OVER", "line": 2.5}},
        draws=500,
    )
    assert result["status"] == "BAYESIAN_POSTERIOR_TOP3"
    assert result["provenance"] == "BAYESIAN_POSTERIOR_POISSON_DIXON_COLES"
    assert result["posterior"]["status"] == "BAYESIAN_POSTERIOR"
    assert result["posterior_predictive"]["status"] == "BAYESIAN_POSTERIOR_PREDICTIVE"
    assert 1 <= len(result["top3"]) <= 3
    assert all(int(row["score"].split("-")[0]) > int(row["score"].split("-")[1]) for row in result["top3"])
