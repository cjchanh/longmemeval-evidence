# Comparator source snapshots

The paper compares against numbers it did not produce. Until 2026-09-05 those
comparator figures were author-reported in the paper only; a reader could not
check them against the release. This directory pins the sources as fetched,
with SHA-256 digests, so the comparison rows in the paper can be re-derived
from bytes the release carries rather than from a live URL that may change.

Fetched 2026-09-05T03:12:08Z with `curl -L`. Hashes are of the files as stored
here (`shasum -a 256`).

| File | Source URL | SHA-256 | What the paper takes from it |
|---|---|---|---|
| `chronos-arxiv-2603.16862.pdf` | https://arxiv.org/pdf/2603.16862 | `a6a75d611a381ba8e244c77601c21ad4567e39e2e97426c85999a0cea21ae738` | Chronos High: 478/500 (95.60%) on LongMemEval-S, the published raw-score state of the art used as the headline comparator (paper §1, §5.1). Also the gold-defect note on question 6d550036 and the judge-variability example on 75f70248 (their §3.5). |
| `chronos-arxiv-2603.16862-abs.html` | https://arxiv.org/abs/2603.16862 | `8c9f8f80f70c4b66c657bb917a13b0428e3590cab3174d32d37da545052ddaa0` | Title, authors, version metadata for the citation. The abstract page carries the 95.60% figure. |
| `mastra-observational-memory.html` | https://mastra.ai/research/observational-memory | `cd0bf092daa9a2956bf8983c8425ea812290ef6c005b00eb6fa60ba7e0f2a073` | Mastra OM: 94.87% task-averaged, 468/500 raw, generator gpt-5-mini (paper §5.1 "not raw-comparable" discussion). The snapshot contains the 94.87% figure. |

## Not snapshotted

- **OMEGA "95.4%"** (paper §5.1). The paper cites this number without a source
  URL or reference entry, so there is nothing to pin. Either add the citation to
  the References section and snapshot it here, or drop the comparison. This is a
  release-integrity gap, recorded rather than papered over.

## How to re-verify

```
cd eval/dense_chain_v32_20260830/comparators
shasum -a 256 -c <<'EOF'
a6a75d611a381ba8e244c77601c21ad4567e39e2e97426c85999a0cea21ae738  chronos-arxiv-2603.16862.pdf
8c9f8f80f70c4b66c657bb917a13b0428e3590cab3174d32d37da545052ddaa0  chronos-arxiv-2603.16862-abs.html
cd0bf092daa9a2956bf8983c8425ea812290ef6c005b00eb6fa60ba7e0f2a073  mastra-observational-memory.html
EOF
```

A fresh fetch of the live URLs is expected to differ from these digests over
time (page templates change); the digests attest to what the paper's numbers
were checked against on the date above, not to the current state of the web.
