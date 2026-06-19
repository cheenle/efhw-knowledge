#!/usr/bin/env python3
"""Paired-SNR antenna comparison.

Method (per user's insight): report COUNT is contaminated by how many times
each station transmitted in A vs B. The clean metric is, for each receiving
callsign that heard the DUT in BOTH windows, the change in that receiver's
mean SNR from A to B (ΔSNR = meanSNR_B - meanSNR_A). Each receiver is its own
control, so path/distance/receiver-sensitivity cancel. Averaging the paired
deltas across common receivers gives the DUT's A->B SNR shift.

Same computation for each ON80 probe station (antenna unchanged) gives the
pure propagation/ionospheric drift over the same interval. Subtracting:

    antenna_effect = ΔSNR(DUT) - ΔSNR(probe baseline)

Usage:
    python3 paired_snr.py
"""
import os
import re
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
    "BG1SB": "pskr_bg1sb_full.adi",
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
    """ADIF QSO_DATE/TIME_ON are UTC -> return CST-aware datetime."""
    d = rec.get("QSO_DATE", "")
    t = rec.get("TIME_ON", "")
    if len(d) != 8 or len(t) < 6:
        return None
    try:
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


def collect_by_rx(path, target):
    """Return {rx_callsign: {'A':[snr,...], 'B':[snr,...]}} for 15m FT8.

    PSK Reporter ADIF puts the QUERIED station (the transmitter we asked about)
    in either OPERATOR or CALL depending on the file; the OTHER field is the
    receiver who heard it. So the receiver is whichever callsign != target.
    """
    target = target.upper()
    by = defaultdict(lambda: {"A": [], "B": []})
    for rec in parse_records(path):
        if not is_15m_ft8(rec):
            continue
        dt = to_dt(rec)
        if dt is None:
            continue
        op = rec.get("OPERATOR", "").upper()
        call = rec.get("CALL", "").upper()
        # receiver = the callsign that is NOT the queried/target station
        if op == target:
            rx = call
        elif call == target:
            rx = op
        else:
            # target not in this record (other-band stray etc.) — skip
            continue
        if not rx:
            continue
        try:
            snr = int(rec.get("APP_PSKREP_SNR"))
        except (TypeError, ValueError):
            continue
        if A_START <= dt < A_END:
            by[rx]["A"].append(snr)
        elif B_START <= dt < B_END:
            by[rx]["B"].append(snr)
    return by


def paired_deltas(by, exclude=None):
    """For receivers present in BOTH windows, ΔSNR = mean(B) - mean(A)."""
    rows = []
    for rx, d in by.items():
        if exclude and rx == exclude:
            continue
        if d["A"] and d["B"]:
            ma = statistics.mean(d["A"])
            mb = statistics.mean(d["B"])
            rows.append((rx, ma, mb, mb - ma, len(d["A"]), len(d["B"])))
    return rows


def summarize(rows):
    deltas = [r[3] for r in rows]
    if not deltas:
        return None
    return {
        "n": len(deltas),
        "mean": statistics.mean(deltas),
        "median": statistics.median(deltas),
        "stdev": statistics.stdev(deltas) if len(deltas) > 1 else 0.0,
    }


def main():
    print(f"Switch A->B : {SWITCH:%Y-%m-%d %H:%M:%S} CST")
    print(f"A window    : {A_START:%H:%M:%S} -> {A_END:%H:%M:%S}  ({WINDOW_MIN} min)")
    print(f"B window    : {B_START:%H:%M:%S} -> {B_END:%H:%M:%S}  ({WINDOW_MIN} min)")
    print("Metric      : per common receiver ΔSNR = mean(B) - mean(A)\n")

    # ---- DUT ----
    dut_by = collect_by_rx(FILES[DUT], DUT)
    dut_rows = paired_deltas(dut_by, exclude=DUT)
    dut_rows.sort(key=lambda r: r[3], reverse=True)
    dsum = summarize(dut_rows)

    print(f"=== {DUT} (DUT, antenna A->B) — common-receiver ΔSNR ===")
    print(f"{'RX':<10}{'meanA':>7}{'meanB':>7}{'dSNR':>7}{'nA':>4}{'nB':>4}")
    for rx, ma, mb, d, na, nb in dut_rows:
        print(f"{rx:<10}{ma:>7.1f}{mb:>7.1f}{d:>+7.1f}{na:>4}{nb:>4}")
    if dsum:
        print(f"\n  common receivers (in both A&B): n={dsum['n']}")
        print(f"  ΔSNR  mean={dsum['mean']:+.2f} dB  median={dsum['median']:+.2f} dB  sd={dsum['stdev']:.2f}")

    # ---- probes ----
    print("\n\n=== ON80 PROBES (antenna fixed = propagation baseline) ===")
    probe_summaries = []
    for call in PROBES:
        by = collect_by_rx(FILES[call], call)
        rows = paired_deltas(by, exclude=call)
        s = summarize(rows)
        if s and s["n"] >= 5:
            probe_summaries.append((call, s))
            print(f"\n{call}: common RX n={s['n']}  "
                  f"ΔSNR mean={s['mean']:+.2f}  median={s['median']:+.2f}  sd={s['stdev']:.2f}")
        elif s:
            print(f"\n{call}: only n={s['n']} common RX (too few, excluded)  "
                  f"ΔSNR mean={s['mean']:+.2f}")
        else:
            print(f"\n{call}: no common receivers in both windows")

    # ---- pooled probe baseline ----
    print("\n\n=== PROPAGATION-CORRECTED ANTENNA EFFECT ===")
    if probe_summaries and dsum:
        # pool all probe common-receiver deltas weighted by count
        all_probe_deltas = []
        for call, _ in probe_summaries:
            by = collect_by_rx(FILES[call], call)
            rows = paired_deltas(by, exclude=call)
            all_probe_deltas.extend(r[3] for r in rows)
        base_mean = statistics.mean(all_probe_deltas)
        base_median = statistics.median(all_probe_deltas)
        print(f"Probe baseline ΔSNR (pooled, n={len(all_probe_deltas)}): "
              f"mean={base_mean:+.2f}  median={base_median:+.2f} dB")
        print(f"DUT ΔSNR                                  : "
              f"mean={dsum['mean']:+.2f}  median={dsum['median']:+.2f} dB")
        print(f"\nAntenna effect (DUT - baseline):")
        print(f"  by mean   : {dsum['mean'] - base_mean:+.2f} dB")
        print(f"  by median : {dsum['median'] - base_median:+.2f} dB")
        print("\n(positive => LC tuner improved SNR beyond propagation drift)")
    else:
        print("insufficient probe data for correction")


if __name__ == "__main__":
    main()
