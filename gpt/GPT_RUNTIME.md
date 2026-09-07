# GPT Runtime Contract

This repository is intended to be consumed by ChatGPT as a persistent model resource, not as a standalone web application.

## Trigger

When the user requests a football match analysis under the full SOP (including the usual Red Team instruction), the GPT workflow should:

1. Read `gpt/MANIFEST.json` and `config/quant_config.json` from this repository.
2. Read the current `gpt/quant_core.py` implementation identified by the manifest.
3. Parse the supplied Titan MD/XLSX snapshot into the Quant Packet input shape while preserving bookmaker names, odds timestamps, match id, MAIN/ALT line identity, and O/U line/price pairs.
4. Reject or label unsynchronised company comparisons instead of forcing a same-time comparison.
5. Execute the current Quant Engine in the Python calculation environment.
6. Freeze the returned Quant Packet before narrative interpretation.
7. Run the qualitative football SOP and independent Red Team review.
8. Treat `status=FAIL` as a hard block on Quant evidence; `PARTIAL` permits only validated components.

## Cross-chat continuity

This trigger and execution order apply across separate ChatGPT conversations. A new chat must not treat the Quant Layer as optional merely because the repository was initialized in another conversation. When the user supplies football match data and requests the full SOP with independent Red Team review, use this repository as the persistent source of truth and execute the same ordered workflow unless the user explicitly overrides it.

The fixed order is:

`Manifest/config -> Titan parse & QC -> Quant Engine -> freeze Quant Packet -> qualitative full SOP -> freeze H1 -> independent Red Team H2 -> CONFIRM/DOWNGRADE/OVERTURN -> final ticket.`

## User interaction

The user does not need to say “run penaltyblog” or “run quant engine”. The full-SOP request is sufficient. The Quant Layer is an internal step and should not delay the fast-ticket-first rule when kickoff is close.

## Version discipline

Every full analysis that uses this layer should identify the engine version in the internal analysis record. A later mathematical change requires a version bump and Changelog entry. Do not silently replace historical calculations with new formulas.

## Scope boundary

This runtime contract does not make GitHub, Penaltyblog, or the Quant Layer the final decision-maker. Market interpretation, lifecycle, attraction, fundamental/context layers and Red Team adjudication remain independent decision stages.
