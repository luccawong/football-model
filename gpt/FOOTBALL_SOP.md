# GPT Football Analysis SOP — Quant Integration

## Required ordering for full pre-match analysis

1. Market snapshot and data-quality/QC.
2. Opening-line first impression using opening structure only.
3. Opening validity / lifecycle: true opening, material-event re-openings, normal movement.
4. Off-field scan.
5. Fundamentals.
6. **Quant Packet freeze** (`GPT-QUANT`).
7. 1X2 company-pricing analysis using same-time slices.
8. Asian handicap analysis.
9. Independent totals analysis.
10. Cross-market coherence: 1X2 ↔ AH ↔ OU.
11. Draw Exclusion Layer; default KEEP unless hard evidence supports exclusion.
12. Market-attraction / favourite-failure analysis.
13. Schedule & Priority Audit including next 7–10 days.
14. Club Relationship & Reciprocity Layer: separate verified facts, incentive inference and unverified speculation.
15. Correct-score layer derived from joint score distribution and reconciled with final direction.
16. Freeze initial hypothesis H1.
17. Independent Red Team H2; it may CONFIRM, DOWNGRADE or OVERTURN H1.
18. Final ticket decision.

## Quant Layer rules

- Quant output is evidence, never an automatic ticket.
- Market-implied lambda is not objective team strength.
- Power de-vig is the primary comparison method in v0.1.0; multiplicative and Shin are robustness checks.
- Company probability differences are percentage points.
- Missing detailed timelines are named and disclosed.
- WH/Ladbrokes fixed Base-2.5 display does not define dynamic O/U structure.
- `Quant Packet.status == FAIL`: exclude quantitative evidence and state why.
- `PARTIAL`: use only components that passed validation.

## Ticket discipline

Once a formal actionable ticket is issued, it is locked. Any later change must be labelled a correction; never silently rewrite the prior ticket.
