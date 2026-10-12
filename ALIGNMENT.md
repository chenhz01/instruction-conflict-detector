# Alignment Audit (Rules 85-100 / 16 items) — instruction-conflict-detector

Audited: 2026-10-13 (round 2, v0.1.1).

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | 85 Safety/Ethics section | PASS | Defensive prompt-hygiene tool: reads local text, zero network, zero model calls. README "How it works" + FAQ state the defensive positioning; "Limits" covers evasion-by-synonym misuse. |
| 2 | 86 Privacy de-identification | PASS | Zero secrets/tokens/real names; fixture prompts are generic policies. Grep for `(sk-\|ghp_\|api_key=)` returns 0 hits. |
| 3 | 87 Copyright boundary | PASS | All content authored fresh; frameworks referenced structurally, no excerpts. LICENSE (MIT, "zhengming contributors") present. |
| 4 | 88 Fact-check labeling | PASS | Performance numbers tagged [Measured] with repro command (timeit over analyze_rules), including the O(n^2) stress note. |
| 5 | 89 Confidence grading | PASS | README closing block: High (parsing/duplicates/cycles) / Medium (conflict recall) with justification. |
| 6 | 90 PLAN B built-in | PASS | README "Minimal Fallback": three grep pipelines for positive/negative/override rules. |
| 7 | 91 Timeout presets | PASS | Quickstart marks ~2 min total, per-command ~0.5s, self-test ~3.4s with the stress-case explanation. |
| 8 | 92 Rule-conflict arbitration | PASS | README "Design Trade-offs": conflict errors > override integrity > priority hygiene > convenience; negative-dominant modality rule. |
| 9 | 93 Version changelog | PASS | CHANGELOG.md has v0.1.0 and v0.1.1 with explicit iteration improvements. |
| 10 | 94 Exemption instruction | N/A | Session-governance rule; static repo content cannot carry exemptions. |
| 11 | 95 External-knowledge cutoff | PASS | README marks environment and "as of 2026-10-13" for landscape claims and measurements. |
| 12 | 96 Explicit assumptions | PASS | README `[Core Assumptions]` lists 4 premises. |
| 13 | 97 Logic-verification trio | PASS | self_test.py: 64 cases = functional A + CLI/exception B + extreme edges C (empty/huge/unicode/CRLF prompts, 500-duplicate stress). SUMMARY: PASS 64/64. |
| 14 | 98 Socratic question | PASS | FAQ "When NOT to use this tool?" (single-author short prompts; clean report != semantic consistency). |
| 15 | 99 Pareto iteration | PASS | Two rounds traceable: v0.1.0 -> review -> v0.1.1 (+4 edge cases incl. 4-node cycle and pair-count stress, fixture corrections). CHANGELOG + TestR2 class. |
| 16 | 100 Ultimate minimal entry | PASS | README opening paragraph is 60 words with a need-judgment ("otherwise skip it"). |

Repro for status column: `python self_test.py` -> `SUMMARY: PASS 64/64`.
