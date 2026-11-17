[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/apkeygbagus/makefun-gta6-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/apkeygbagus/makefun-gta6-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

# GTA VI Twitch CCU Forecast — make.fun "Forecast GTA VI's launch-day Twitch viewers hour by hour"

Bounty: https://make.fun/bounty/gta6-twitch-ccu-forecast-01
Slug: `gta6-twitch-ccu-forecast-01` · Pool $250 USDC (1st $50, 20 places paid) ·
**Deadline: 2026-11-19 01:00 UTC = 08:00 WIB** · Entry fee: none
(`entry_fee: null` verified via the official requirements API).

## What it does

`main.py` (Python 3.13, standard library only) reads every `*.in` case in
`$MAKEFUN_INPUT_DIR` (schema `makefun/twitch-ccu-case/v1`) and writes one
`/output/<id>.out` per case: 23 rows for hours 2–24, each with five quantiles
(0.05 / 0.25 / 0.5 / 0.75 / 0.95) of that hour's Twitch concurrent viewers for
the "Grand Theft Auto VI" category on launch day, conditioned on hour 1's
print. Scoring is mean pinball loss on the log scale; lowest wins, and a
prize requires beating the best house entry.

## Method

Same functional family as the house baseline,
`q_τ(h) = p1 · exp(shape[h] + z_τ · σ[h])`, but the curve and the spread are
estimated from the training data each case ships (`comparables`: 38 past big
launches in practice, 42 in the final, with hourly counts from 14 days before
to 3 days after release):

1. Per comparable: log ratio `ln(viewers_h / viewers_hour1)` for release-day
   hours h = 2..24.
2. `shape[h]` = **median** log ratio across comparables × shrink 1.05.
3. `σ[h]` = **1.4826 × MAD** of the log ratios × 1.6, floored at 0.20,
   capped at 1.30 — spread follows the empirical dispersion across launches.
4. Quantiles rounded to 2 decimals (half-up, like the starter), clamped to
   (0, 1e9], guaranteed non-decreasing. Fully deterministic: no randomness,
   no network, no wall clock.
5. Fallback when fewer than 5 comparables cover an hour: exactly the house
   baseline behaviour (persistence, σ = 0.15·√(h−1)) — verified identical to
   the brief's worked example for p1 = 100,000 at hour 24:
   `[30624.45, 61578.43, 100000, 162394.53, 326536.46]`.

## Validation

Leave-one-out backtest over the 38 comparables in practice case `p00`
(each launch treated as a case, curve built from the other 37, scored with
the grader's exact log pinball loss):

| Model | Mean pinball loss |
|---|---|
| House baseline (persistence, σ=0.15√) | 0.9297 |
| This model (shrink 1.05, σ×1.6) | **0.7858** |

−15.5% vs baseline on the same data; the model wins the majority of cases.
Constants chosen from a grid (shrink 0.8–1.05 × σ 0.8–2.0); performance is
flat around the optimum, not a sharp peak.

Format & runtime tests (local Python 3.12; grader runs 3.13, stdlib code is
compatible both ways):

- All 4 practice cases from the official kit (`p00`–`p03`) produce valid
  output: exactly 23 rows for hours 2–24, keys exactly `{hour, q}`, 5
  monotone quantiles within (0, 1e9], ≈1.5 KB per file.
- Deterministic: two runs → byte-identical outputs on every case.
- Runtime: **0.185 s total for 4 cases** (≈46 ms/case; cap is 8 s/case).
- Sanity: hour-2 median ≈ 0.87× hour-1 print (early-morning UTC dip),
  hour-24 median ≈ 2.1–2.4× (release-day prime time).

## Run it

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=<dir with *.in cases> MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The grader runs `python3 -P -s /bot/main.py` (PYTHONHASHSEED=0), offline,
1 CPU, max 8 s and 1024 MB per case.

## Entry facts

- Public GitHub repository, created after the competition opened
  (2026-11-17), MIT license (see `LICENSE`).
- `.makefun/owner.json` names the entrant account's wallet, proving this
  repository belongs to the entering make.fun account.
- Submitted with the transcript bundle of the agent sessions that built
  this entry (kit CLI `node cli/makefun.mjs bundle`), as the bounty
  requires. Max 10 submits/day, 20 total; the last submit before the
  deadline is the final entry.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
