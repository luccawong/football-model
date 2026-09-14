# Token Optimization Skill — Source and Compatibility

Upstream inspiration/source:

- Repository: `bm629/agent-skills`
- Skill: `skills/token-optimization`
- Upstream version reviewed for this installation: `1.8.3`
- Upstream license: MIT

This repository uses a **Codex-focused lightweight adaptation**, not a byte-for-byte copy of the upstream `SKILL.md`.

## Why it is adapted

The upstream skill is provider-agnostic and includes a large body plus several reference documents. For this repository, the objective is specifically to reduce active Codex context and repeated tool/file overhead while preserving analysis quality, so the installed version keeps the highest-value rules in a smaller instruction footprint.

The current OpenAI Codex skill discovery convention is repository-scoped `.agents/skills/<skill-name>/SKILL.md`. Older third-party installation documentation may refer to `.codex/agents/*.toml`; that location is for Codex custom subagents rather than the current repository Skill format.

## Upstream URL

https://github.com/bm629/agent-skills/tree/main/skills/token-optimization

No claim is made that the adapted file is the upstream author's exact distribution. See `LICENSE` for the upstream MIT notice retained with this adaptation.
