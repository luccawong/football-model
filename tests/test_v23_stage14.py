from gpt.stage14_auto import automatic_top3
from src.parser.titan_md import read_markdown_tables_text


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


def test_automatic_top3_uses_quant_reconstruction():
    packet = {
        "reconstruction": {
            "Pinnacle": {"lambda_home": 1.6, "lambda_away": 1.0, "rho": -0.05}
        }
    }
    result = automatic_top3(packet, "Pinnacle")
    assert result["status"] == "MARKET_RECONSTRUCTION"
    assert len(result["top3"]) == 3
    assert result["top3"][0]["probability"] >= result["top3"][1]["probability"]
