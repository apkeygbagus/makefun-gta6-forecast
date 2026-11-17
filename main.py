"""gta6-twitch-ccu-forecast-01 entry (Python 3.13, standard library only).

Model: the case itself ships the training data — `comparables`, 38 (practice)
or 42 (final) past big launches with hourly Twitch counts from 14 days before
to 3 days after their release day. For each comparable we compute, for every
release-day hour h = 2..24, the log ratio log(viewers_h / viewers_hour1).
Across comparables:

  shape[h] = median of those log ratios   -> the typical launch-day curve
  sigma[h] = robust spread (1.4826 * MAD) of those log ratios, floored/capped

Forecast for the case, with p1 = hour 1's print:

  q_tau(h) = p1 * exp(shape[h] + z_tau * sigma[h])

This is exactly the functional family the house baseline uses
(p1 * exp(z * 0.15 * sqrt(h-1))), except the median curve and the spread are
estimated from real launch days instead of assuming persistence with a
hand-set sigma. Scoring is pinball loss on the log scale, so a median curve
plus an honest, empirically calibrated spread is the right target.

Deterministic (medians/MAD only, no randomness, no network), stdlib only,
runs in well under a second per case.

Run contract (from the kit's RULES.txt / starter):
  python3 -P -s /bot/main.py   (grader; reads /input, writes /output)
  MAKEFUN_INPUT_DIR / MAKEFUN_OUTPUT_DIR override those locally.
Reads every *.in in the input dir in name order, writes <id>.out per case:
  {"hours": [{"hour": h, "q": [q05, q25, q50, q75, q95]}, ... 23 rows ...]}
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first (as the starter does).
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]

# Calibration constants (validated by leave-one-out backtest over the
# comparables shipped in the practice cases; see README.md).
SHAPE_SHRINK = 1.05   # LOO-tuned: median curve, very slightly amplified
SIGMA_SCALE = 1.6     # LOO-tuned: empirical MAD spread, widened (launches vary a lot)
SIGMA_FLOOR = 0.20    # never claim more certainty than this (log units)
SIGMA_CAP = 1.30      # never claim less


def parse_ts(s):
    """ISO-8601 'Z' timestamp -> epoch seconds (float)."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    mid = n // 2
    if n % 2:
        return xs[mid]
    return 0.5 * (xs[mid - 1] + xs[mid])


def robust_sigma(xs, med):
    """1.4826 * MAD; falls back to a plain stdev when MAD degenerates to 0."""
    mad = median([abs(x - med) for x in xs])
    s = 1.4826 * mad
    if s <= 1e-9 and len(xs) > 1:
        mean = sum(xs) / len(xs)
        s = math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))
    return s


def comparable_curves(case):
    """Per-hour lists of log(viewers_h / viewers_hour1) over all comparables."""
    by_hour = {h: [] for h in range(2, 25)}
    for comp in case.get("comparables") or []:
        try:
            day0 = parse_ts(comp["day_start"])
        except Exception:
            continue
        per_hour = {}
        for pt in comp.get("hourly") or []:
            try:
                off = (parse_ts(pt["from"]) - day0) / 3600.0
                v = pt.get("viewers")
            except Exception:
                continue
            if v is None or v <= 0:
                continue
            idx = int(round(off))
            if abs(off - idx) < 1e-6 and 0 <= idx < 24:
                per_hour[idx + 1] = float(v)
        v1 = per_hour.get(1)
        if not v1:
            continue
        logv1 = math.log(v1)
        for h in range(2, 25):
            if h in per_hour:
                by_hour[h].append(math.log(per_hour[h]) - logv1)
    return by_hour


def round2(x):
    """Round to 2 decimals, half up (as the starter / JS Math.round does)."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if float(value).is_integer() else value


def forecast_case(case, name):
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    if first is None:
        raise ValueError(f"{name} has no hour-1 print")
    p1 = max(1.0, float(first["viewers"]))

    by_hour = comparable_curves(case)

    rows = []
    last_shape, last_sigma = 0.0, 0.35
    for row in case["forecast"]:
        h = row["hour"]
        xs = by_hour.get(h) or []
        if len(xs) >= 5:
            med = median(xs)
            shape = SHAPE_SHRINK * med
            sigma = min(SIGMA_CAP, max(SIGMA_FLOOR, SIGMA_SCALE * robust_sigma(xs, med)))
            last_shape, last_sigma = shape, sigma
        else:
            # No usable comparable data for this hour: fall back toward the
            # house-baseline behaviour (persistence, widening spread).
            shape = last_shape
            sigma = max(last_sigma, 0.15 * math.sqrt(h - 1))
        centre = math.log(p1) + shape
        q = []
        for z in Z:
            v = math.exp(centre + z * sigma)
            v = min(1_000_000_000.0, max(0.01, v))
            q.append(round2(v))
        # Guarantee non-decreasing after rounding/clamping.
        for i in range(1, len(q)):
            if q[i] < q[i - 1]:
                q[i] = q[i - 1]
        rows.append({"hour": h, "q": q})
    return {"hours": rows}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
