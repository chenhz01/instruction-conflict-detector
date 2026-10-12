# Changelog

## v0.1.1 (2026-10-13)

Round-2 revision after full self-review of the v0.1.0 draft:

- Added 4 extreme-edge test cases (500 duplicate rules -> all 124,750 pair
  findings, numeric-only vague rules, 4-node override cycles,
  --min-shared=3 suppression); suite grew 60 -> 64 cases, all PASS.
- Fixed round-1 fixtures: the precedence-keyword case now asserts override
  graph integrity instead of absence of errors (a separate precedence line
  does not erase a direct conflict); priority-warning and heading fixtures
  made keyword-sufficient; 20,000-rule stress reduced to 2,000 after
  measuring O(n^2) cost.
- Measured and documented Performance numbers ([Measured] tags, repro
  commands, O(rules^2) boundary).
- Added ALIGNMENT.md (rules 85-100 audit, 16 items with evidence).

## v0.1.0 (2026-10-13)

Initial draft:

- Rule parsing: numbered and bulleted lines, explicit number preservation.
- Modality detection (negative-dominant) and Unicode-safe keyword extraction
  ([^\W\d_]{3,} tokens, stopword-filtered).
- Findings: DIRECT_CONFLICT (error), DUPLICATE_RULE (warn),
  UNDECLARED_PRIORITY (info, --min-shared threshold), VAGUE_RULE (info),
  NO_RULES (info), UNKNOWN_RULE_REF (info), CIRCULAR_OVERRIDE (error,
  includes self-loops and multi-node cycles).
- CLI (`analyze`, `--min-shared`, `--json`) with exit-code contract 0/1/2;
  zero network, zero model calls.
- Self-test suite: 60 cases across functional / exception / extreme-edge
  classes, `SUMMARY: PASS n/n` reporting, four-defence template.
- README, MIT LICENSE.
