# v4 selector-mode operators — REPORT (landed by coordinator; worker blocked on report writes)

## Verdict first
**Do not swap selector mode in.** Candidate-coverage ceiling on selector-eligible rows is **59.6%**.
Every non-broken reader already scores **86.1%–92.4%** on those same rows under v3.4. No class
has a ceiling above a weak reader's existing accuracy. Selector mode would cost ~74 rows vs
grok-high on the 257-row facts slice.

## Class coverage (223/257 = 86.8% eligible)
| class | rows | code assembles |
|---|---:|---|
| count_enumeration | 96 | counts the item ids the reader selects |
| count_quantity | 50 | a stated amount, or a difference of two |
| date_interval | 48 | elapsed days/weeks/months between two anchors |
| recency_value | 26 | the selected newest user statement |
| date_anchor | 3 | canonical date form |
| passthrough | 34 | v3.4 facts_text byte-for-byte |

## Candidate coverage — the ceiling (abs golds excluded; NONE-escape handles them; 15 rows)
| class | scored | strict | any | mean cands | neg. control | verdict |
|---|---:|---:|---:|---:|---:|---|
| date_interval | 47 | 89.4% | 93.6% | 7.3 | 59.6% | real lift |
| count_quantity | 45 | 66.7% | 73.3% | 1.9 | 11.1% | <90%, biggest lift over control |
| count_enumeration | 89 | 29.2% | 37.1% | 9.8 | 60.0% | <90% AND loses to its own control |
| recency_value | 25 | 32.0% | 32.0% | 7.5 | n/a | <90% |
| date_anchor | 2 | 0.0% | 0.0% | 4.0 | n/a | n=2, not a measurement |
| overall | 208 | 51.0% | 56.7% | | | |

## Headroom test — the number that decides it (per-class, GPT-4o-judged existing runs)
| class | n | ceiling | grok-high | xhigh | sol | dsv4pro | nemotron |
|---|---:|---:|---:|---:|---:|---:|---:|
| date_interval | 48 | 93.8% | 97.9% | 97.9% | 93.8% | 95.8% | 43.8% |
| count_quantity | 50 | 76.0% | 98.0% | 92.0% | 92.0% | 90.0% | 62.0% |
| count_enumeration | 96 | 41.7% | 88.5% | 83.3% | 84.4% | 81.2% | 18.8% |
| date_anchor | 3 | 33.3% | 100% | 100% | 100% | 66.7% | 0% |
| recency_value | 26 | 34.6% | 84.6% | 80.8% | 80.8% | 80.8% | 3.8% |
| **all eligible** | **223** | **59.6%** | **92.4%** | **88.3%** | **87.9%** | **86.1%** | **31.8%** |

## Honest limits (L1–L9, from worker verbatim summary)
L1 ceiling below floor · L2 count_enumeration anti-informative (57/89 hit 20-item cap; gold subset-reachable
only 48.3%) · L3 recency cap unguarded, deliberately NOT raised (tuning-against-gold refusal) · L4 head-noun
misroute gates amount class (078150f1) · L5 date_anchor n=3 · L6 fractional units unrepresentable (3.5 weeks)
· L7 in-text year resolution heuristic · L8 runner needs --selector/suffix suppression for live use (out of
scope) · L9 no live selector pass — coverage bounds from above only.

## THE FINDING WORTH ACTING ON (out of worker scope)
**In-text date anchors are a defect in the v3.4 facts scaffold itself.** 19 of 23 elapsed-time rows the
session-header index cannot serve have exactly ONE session day in the entire packet — real dates sit
unparsed in prose. `dense_chain_reasoning_operators.py::_date_duration_lines` builds its date list from
`date:` headers only. Porting in-text anchors into v3.4 helps the FREE-GENERATION reader on those rows
with no selector involved. (Demonstrated on 08f4fc43: gold `30 days` only expressible via in-text
January 2nd / February 1st anchors; all 16 session headers carry one date.)

Worker discipline notes: two gold-blind code changes disclosed (in-text anchors — structural justification;
`need` trigger — module's own docstring); recency cap and enumeration ladder left untouched to avoid
tuning against the answer key. Tests 49/49. Determinism cmp-clean. Hashes: v4_selector.py 95313581b9…,
v4_selector_replay.py 59d8c8961b…, tests 76de39cfdb….

Full replay artifacts: replay_rows.jsonl, summary.json (this directory). Reproduce command in worker log.
