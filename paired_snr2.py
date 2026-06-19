#!/usr/bin/env python3
"""Robust paired-ΔSNR analysis: BG1SB (DUT, antenna A->B) vs ON80 probes.

For each receiver callsign heard in BOTH the A and B windows, compute its
mean SNR in A, mean SNR in B, and ΔSNR = mean(B)-mean(A). This is a PAIRED
comparison: each receiver is its own control (path, distance, RX sensitivity
cancel). The ON80 probe stations (antenna fixed) give the propagation-drift
baseline. Antenna effect = DUT ΔSNR - probe ΔSNR.

This version adds robustness:
  * --min N : require >= N reports in BOTH windows (drop single-shot noise)
  * weighted mean (weight = min(nA,nB)), reducing the impact of thin stations
  * bootstrap 95% CI on the DUT median and mean
  * same filter applied identically to probes

Usage:
    python3 paired_snr2.py            # min=1 (all), plus min=2 and min=3 sweeps
"""
import os
import re
import math
import random
import statistics
from collections import defaultdict
from datetime import datetime, timezone, timedelta

UTC = timezone.utc
CST = timezone(timedelta(hours=8))
SWITCH = datetime(2026, 6, 19, 12, 26, 52, tzinfo=CST)
WINDOW_MIN = 51
A_START = SWITCH - timedelta(minutes=WINDOW_MIN)
A_END = SWITCH
B_START = SWITCH
B_END = SWITCH + timedelta(minutes=WINDOW_MIN)

DUT = "BG1SB"
PROBES = ["BH1UWJ", "BD1AUJ", "BI1WIA", "BI1MDW", "BI1KND"]
FILES = {
    "BG1SB": "pskr_24h_latest.adi",
    "BH1UWJ": "probe_BH1UWJ.adi",
    "BD1AUJ": "probe_BD1AUJ.adi",
    "BI1WIA": "probe_BI1WIA.adi",
    "BI1MDW": "probe_BI1MDW.adi",
    "BI1KND": "probe_BI1KND.adi",
}

FIELD = re.compile(r"<([A-Za-z0-9_]+)(?::\d+(?::[A-Za-z])?)?>([^<]*)")


def parse_records(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if "<eoh>" in text.lower():
        text = text[text.lower().index("<eoh>") + len("<eoh>"):]
    for chunk in re.split(r"<eor>", text, flags=re.IGNORECASE):
        chunk = chunk.strip()
        if not chunk:
            continue
        rec = {}
        for m in FIELD.finditer(chunk):
            rec[m.group(1).upper()] = m.group(2).strip()
        if rec:
            yield rec


def to_dt(rec):
    d, t = rec.get("QSO_DATE", ""), rec.get("TIME_ON", "")
    if len(d) != 8 or len(t) < 6:
        return None
    try:
        # ADIF timestamps are UTC; convert to CST
        u = datetime(int(d[0:4]), int(d[4:6]), int(d[6:8]),
                     int(t[0:2]), int(t[2:4]), int(t[4:6]), tzinfo=UTC)
        return u.astimezone(CST)
    except ValueError:
        return None


def is_15m_ft8(rec):
    try:
        f = float(rec.get("FREQ", "0"))
    except ValueError:
        return False
    return 21.0 <= f <= 21.5 and rec.get("MODE", "").upper() == "FT8"


def collect_by_rx(path):
    """Return {rx: {'A':[snr...], 'B':[snr...]}} for 15m FT8."""
    d = defaultdict(lambda: {"A": [], "B": []})
    for rec in parse_records(path):
        if not is_15m_ft8(rec):
            continue
        dt = to_dt(rec)
        if dt is None:
            continue
        try:
            snr = int(rec.get("APP_PSKREP_SNR"))
        except (TypeError, ValueError):
            continue
        rx = rec.get("OPERATOR") or rec.get("CALL", "")
        if not rx:
            continue
        if A_START <= dt < A_END:
            d[rx]["A"].append(snr)
        elif B_START <= dt < B_END:
            d[rx]["B"].append(snr)
    return d


def paired_deltas(by_rx, min_n):
    """Return list of (rx, meanA, meanB, dSNR, nA, nB, w) for common receivers."""
    out = []
    for rx, w in by_rx.items():
        nA, nB = len(w["A"]), len(w["B"])
        if nA >= min_n and nB >= min_n:
            mA, mB = statistics.mean(w["A"]), statistics.mean(w["B"])
            out.append((rx, mA, mB, mB - mA, nA, nB, min(nA, nB)))
    return out


def boot_ci(vals, stat=statistics.mean, n=4000, seed=42):
    if len(vals) < 2:
        return (None, None)
    rng = random.Random(seed)
    k = len(vals)
    samples = []
    for _ in range(n):
        s = [vals[rng.randrange(k)] for _ in range(k)]
        samples.append(stat(s))
    samples.sort()
    return (samples[int(0.025 * n)], samples[int(0.975 * n)])


def summarize(deltas, label):
    ds = [d[3] for d in deltas]
    if not ds:
        print(f"  {label}: no common receivers")
        return None
    mean = statistics.mean(ds)
    med = statistics.median(ds)
    sd = statistics.pstdev(ds) if len(ds) > 1 else 0.0
    se = sd / math.sqrt(len(ds)) if ds else 0.0
    # weighted mean by min(nA,nB)
    wsum = sum(d[6] for d in deltas)
    wmean = sum(d[3] * d[6] for d in deltas) / wsum if wsum else mean
    ci = boot_ci(ds, statistics.mean)
    ci_str = f"[{ci[0]:+.2f},{ci[1]:+.2f}]" if ci[0] is not None else "[n/a]"
    print(f"  {label}: n={len(ds)}  mean={mean:+.2f}  wmean={wmean:+.2f}  "
          f"median={med:+.2f}  sd={sd:.2f}  se={se:.2f}  "
          f"95%CI[mean]={ci_str}")
    return {"n": len(ds), "mean": mean, "wmean": wmean, "median": med,
            "sd": sd, "se": se, "ci": ci, "deltas": ds}


def main():
    dut_rx = collect_by_rx(FILES[DUT])
    probe_rx = {p: collect_by_rx(FILES[p]) for p in PROBES}

    print(f"Switch A->B : {SWITCH:%Y-%m-%d %H:%M:%S} CST")
    print(f"A window    : {A_START:%H:%M:%S} -> {A_END:%H:%M:%S}  ({WINDOW_MIN} min)")
    print(f"B window    : {B_START:%H:%M:%S} -> {B_END:%H:%M:%S}  ({WINDOW_MIN} min)")
    print("Metric      : per common receiver ΔSNR = mean(B) - mean(A)")
    print("="*70)

    for min_n in (1, 2, 3):
        print(f"\n########## MIN REPORTS PER WINDOW >= {min_n} ##########")
        dut_d = paired_deltas(dut_rx, min_n)
        print(f"\n--- DUT BG1SB (antenna A->B) ---")
        dut_s = summarize(dut_d, "BG1SB")

        # pooled probe deltas (same filter)
        print(f"\n--- ON80 probes (antenna fixed = propagation baseline) ---")
        pooled = []
        for p in PROBES:
            pd = paired_deltas(probe_rx[p], min_n)
            if pd:
                summarize(pd, p)
                pooled.extend(pd)
        probe_s = summarize(pooled, "POOLED probes") if pooled else None

        if dut_s and probe_s:
            eff_mean = dut_s["mean"] - probe_s["mean"]
            eff_wmean = dut_s["wmean"] - probe_s["wmean"]
            eff_med = dut_s["median"] - probe_s["median"]
            # combined SE for the mean difference
            cse = math.sqrt(dut_s["se"]**2 + probe_s["se"]**2)
            print(f"\n  >>> PROPAGATION-CORRECTED ANTENNA EFFECT (DUT - probe) <<<")
            print(f"      by mean    : {eff_mean:+.2f} dB  (±{cse:.2f} SE, "
                  f"95%CI≈[{eff_mean-1.96*cse:+.2f},{eff_mean+1.96*cse:+.2f}])")
            print(f"      by wmean   : {eff_wmean:+.2f} dB")
            print(f"      by median  : {eff_med:+.2f} dB")
            print(f"      (positive => LC tuner improved SNR beyond propagation)")


if __name__ == "__main__":
    main()
