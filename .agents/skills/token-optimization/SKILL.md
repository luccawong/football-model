---
name: token-optimization
description: Reduce Codex token usage, context growth, repeated file reads, verbose tool output, and unnecessary agent-loop iterations without sacrificing correctness or required analysis depth. Use for large-repository work, long sessions, context pressure, slow loops, or requests to reduce token/cost usage.
---

# Token Optimization

Optimize **tokens per completed task**, not tokens per individual request. A shorter call that causes extra retries, re-reading, or lower-quality analysis is a regression.

## Core workflow

1. **Find the dominant token source first.** Classify overhead into: always-loaded instructions, conversation/session history, file/tool results, repeated loop iterations, and final output. Optimize the largest one or two buckets.
2. **Use progressive disclosure.** Search/index before reading. Read only the files and line ranges required for the current decision. Do not recursively read the whole repository unless the task genuinely requires it.
3. **Do not re-read unchanged material.** Reuse the known current state of files already read or modified. Re-read only when the file may have changed, exact verification is required, or the prior read was incomplete.
4. **Batch independent work.** Combine independent searches, file reads, and checks into the same iteration when possible. Avoid one-file-per-turn or one-command-per-turn loops.
5. **Control verbose tool output.** For long logs, diffs, test output, database results, or generated data, keep the raw artifact addressable but inspect targeted sections using search, ranges, summaries, head/tail, or filtered queries. Do not repeatedly inject the full raw output into context.
6. **Use the filesystem as cold context.** For long tasks, store durable checkpoints, decisions, large intermediate results, or generated reports in files. Carry only the objective, relevant decisions, file paths, and unresolved issues in active context.
7. **Compact only at logical boundaries.** After a milestone, preserve: primary objective, non-negotiable constraints, decisions and reasons, active files and current state, unresolved risks/questions, and next actions. Drop stale intermediate chatter and superseded tool output.
8. **Keep stable instructions stable.** Avoid injecting timestamps, random IDs, or frequently changing material into reusable instruction prefixes. Put volatile information near the current task instead.
9. **Trim response overhead.** Skip filler and repeated restatements. Use concise progress updates and structured machine-facing output. Expand when the user explicitly asks for detail or when detail is necessary for correctness.
10. **Verify the result.** Judge optimization by the total work needed to finish the task: fewer unnecessary reads/calls and less duplicated context, with no loss of required evidence, tests, or output quality.

## Repository-specific execution rules

- Prefer existing indexes, manifests, database keys, match IDs, and targeted search over broad directory scans.
- For large football-model datasets, validation packets, odds timelines, SOP modules, and historical samples, load only the slices needed for the current match or research question.
- If the task requires a full SOP, Red Team review, statistical validation, or auditable evidence chain, **do not shorten the reasoning merely to save tokens**. Reduce transport/repetition overhead instead.
- When a generated command or script produces large output, write it to a file when practical and return a compact summary plus the path.
- Preserve exact source/version provenance when compacting research or model rules.

## Hard constraints

- Never remove or weaken user requirements, safety constraints, acceptance criteria, required tests, or evidence needed for correctness.
- Never claim token savings by silently doing less work.
- Never downgrade model/reasoning quality solely to save tokens unless the user explicitly asks for that tradeoff.
- Never discard raw evidence if it cannot be reproduced or re-read later.
- Prefer fewer high-information iterations over many tiny iterations.

## Completion check

Before finishing a substantial task, ask internally:

- Did I read or run anything twice without a reason?
- Could independent operations have been batched?
- Did large raw outputs remain in active context after their useful information was extracted?
- Did token optimization change the requested analytical depth or correctness standard?

If the last answer is yes, restore the required depth before finalizing.

## Provenance

Codex-focused lightweight adaptation of `bm629/agent-skills` → `token-optimization` v1.8.3. See `SOURCE.md` in this skill directory for provenance and compatibility notes.
