# Crawler Archive

Temporary one-month archive for raw pre-match Titan V23 crawler packets used by MODEL_1.

## Coverage

- Formal archive start: **2026-09-05**.
- Current indexed coverage: 2026-09-05 through 2026-09-12.
- Pre-2026-09-05 packets are outside this archive window.

## Storage

- Raw V23 MD packets are immutable pre-match source artifacts.
- Raw bytes are grouped in ChatGPT Library under `/Football_Model/Crawler_Archive/YYYY-MM-DD/`.
- GitHub stores `index.json` plus one `manifest.json` per date.
- Each packet is fingerprinted by SHA-256.
- Duplicate `(1)` re-uploads with identical bytes are omitted.
- Post-match information must never rewrite the raw packet.

## Macau AH operation-change annotation

Starting 2026-09-05, archive diagnostics track Macau Asian Handicap changes. The cross-packet file is `crawler_archive/macau_ah_change_index.json`.

For the same `match_id`, the newest archived snapshot is compared with the previous archived snapshot:

- `LINE_SHIFT`: handicap line changed.
- `WATER_STRUCTURE_SHIFT`: same line, at least 0.06 HK-water movement on one side.
- `WATER_FINE_TUNE`: same line, water changed by more than 0.01 but less than 0.06.
- `NO_MATERIAL_CHANGE`: no material line/water change.
- `FIRST_ARCHIVED_OBSERVATION`: no earlier archived snapshot for that match.
- `MACAU_AH_MISSING`: Macau AH data unavailable.

Within each raw crawler packet, MODEL_1 can additionally inspect Macau opening/current line, full history, line-switch count, reversals/test-and-revert behavior, and the latest effective time slice versus the immediately preceding time slice.

These tags describe observable market structure only. They do not by themselves determine hidden bookmaker intent or the final betting direction.

## Source-of-truth rule

For MODEL_1 retrospective work, use the immutable raw packet first. The Macau change index is an audit/diagnostic layer, not a replacement for the full odds timeline.
