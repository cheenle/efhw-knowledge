#!/usr/bin/env python3
"""Full cross-analysis: BG1SB (DUT, antenna changed) vs ON80 probe stations
(antenna unchanged = pure propagation baseline).

For each station's ADIF (who-heard-them), filter to 15m (21.0-21.5 MHz) FT8,
split into equal A/B windows around the switch time, and compute reports /
unique RX / countries / SNR. Then express each station's B/A change, use the
probe geometric mean as the propagation baseline, and normalize the DUT.

Usage:
    python3 cross_full.py
"""
import os
import re
import math
import statistics
from collections import Counter
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
SWITCH = datetime(2026, 6, 19, 12, 26, 52, tzinfo=CST)

# Equal windows: B is SWITCH -> SWITCH+W ; A is SWITCH-W -> SWITCH
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
    """Yield dict per <eor> record."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    # strip header up to <eoh>
    if "<eoh>" in text.lower():
        idx = text.lower().index("<eoh>") + len("<eoh>")
        text = text[idx:]
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
    d = rec.get("QSO_DATE", "")
    t = rec.get("TIME_ON", "")
    if len(d) != 8 or len(t) < 6:
        return None
    try:
        # ADIF QSO_DATE/TIME_ON are UTC; parse as UTC then convert to CST.
        utc = datetime(int(d[0:4]), int(d[4:6]), int(d[6:8]),
                       int(t[0:2]), int(t[2:4]), int(t[4:6]),
                       tzinfo=timezone.utc)
        return utc.astimezone(CST)
    except ValueError:
        return None


def is_15m_ft8(rec):
    try:
        f = float(rec.get("FREQ", "0"))
    except ValueError:
        return False
    if not (21.0 <= f <= 21.5):
        return False
    return rec.get("MODE", "").upper() == "FT8"


def collect(path):
    """Return list of (dt, rx_callsign, snr, dxcc, dist) for 15m FT8."""
    out = []
    for rec in parse_records(path):
        if not is_15m_ft8(rec):
            continue
        dt = to_dt(rec)
        if dt is None:
            continue
        rx = rec.get("OPERATOR") or rec.get("CALL", "")
        try:
            snr = int(rec.get("APP_PSKREP_SNR"))
        except (TypeError, ValueError):
            snr = None
        try:
            dist = float(rec.get("DISTANCE"))
        except (TypeError, ValueError):
            dist = None
        out.append((dt, rx, snr, rec.get("DXCC", ""), dist))
    return out


def window_stats(recs, start, end):
    sel = [r for r in recs if start <= r[0] < end]
    snrs = [r[2] for r in sel if r[2] is not None]
    dists = [r[4] for r in sel if r[4] is not None]
    rxs = set(r[1] for r in sel if r[1])
    ctry = set(r[3] for r in sel if r[3])
    return {
        "reports": len(sel),
        "rx": len(rxs),
        "countries": len(ctry),
        "snr_avg": round(statistics.mean(snrs), 1) if snrs else None,
        "snr_max": max(snrs) if snrs else None,
        "dist_avg": round(statistics.mean(dists)) if dists else None,
        "dist_max": round(max(dists)) if dists else None,
        "rx_set": rxs,
    }


def main():
    print(f"Switch A->B : {SWITCH:%Y-%m-%d %H:%M:%S} CST")
    print(f"A window    : {A_START:%H:%M:%S} -> {A_END:%H:%M:%S}  ({WINDOW_MIN} min)")
    print(f"B window    : {B_START:%H:%M:%S} -> {B_END:%H:%M:%S}  ({WINDOW_MIN} min)")
    print()

    results = {}
    for call in [DUT] + PROBES:
        recs = collect(FILES[call])
        if not recs:
            results[call] = None
            continue
        a = window_stats(recs, A_START, A_END)
        b = window_stats(recs, B_START, B_END)
        results[call] = {"A": a, "B": b, "total15m": len(recs)}

    # raw table
    print("=== Per-station A/B (15m FT8, equal 51-min windows) ===")
    print(f"{'station':<9}{'win':<4}{'rep':>5}{'rx':>5}{'ctry':>5}{'snrAvg':>8}{'snrMax':>8}{'distAvg':>9}")
    for call in [DUT] + PROBES:
        r = results[call]
        if not r:
            print(f"{call:<9} no 15m FT8 data")
            continue
        tag = "DUT" if call == DUT else "probe"
        for win in ("A", "B"):
            s = r[win]
            print(f"{call:<9}{win:<4}{s['reports']:>5}{s['rx']:>5}{s['countries']:>5}"
                  f"{str(s['snr_avg']):>8}{str(s['snr_max']):>8}{str(s['dist_avg']):>9}")

    # B/A ratios
    print("\n=== B/A reports ratio (antenna-fixed probes = propagation baseline) ===")
    print(f"{'station':<9}{'A_rep':>7}{'B_rep':>7}{'B/A':>7}{'snr_d':>7}  role")
    probe_ratios = []
    dut_ratio = None
    for call in [DUT] + PROBES:
        r = results[call]
        if not r:
            print(f"{call:<9}  -- insufficient data --")
            continue
        a_rep, b_rep = r["A"]["reports"], r["B"]["reports"]
        ratio = (b_rep / a_rep) if a_rep > 0 else None
        snr_d = None
        if r["A"]["snr_avg"] is not None and r["B"]["snr_avg"] is not None:
            snr_d = round(r["B"]["snr_avg"] - r["A"]["snr_avg"], 1)
        role = "DUT (antenna changed)" if call == DUT else "probe (fixed)"
        rs = f"{ratio:.2f}" if ratio is not None else "n/a"
        ds = f"{snr_d:+.1f}" if snr_d is not None else "n/a"
        print(f"{call:<9}{a_rep:>7}{b_rep:>7}{rs:>7}{ds:>7}  {role}")
        if call == DUT:
            dut_ratio = ratio
        elif ratio is not None and a_rep >= 10 and b_rep >= 1:
            # only probes with meaningful activity in BOTH windows
            probe_ratios.append((call, ratio))

    print("\n=== Propagation-corrected antenna effect ===")
    print(f"Qualified probes (active both windows, A>=10 reports):")
    for c, r in probe_ratios:
        print(f"  {c}: B/A = {r:.2f}")
    if probe_ratios and dut_ratio:
        ratios = [r for _, r in probe_ratios]
        geo = math.exp(statistics.mean(math.log(r) for r in ratios))
        arith = statistics.mean(ratios)
        print(f"\nProbe baseline B/A : geo-mean={geo:.2f}  arith-mean={arith:.2f}  n={len(ratios)}")
        print(f"DUT (BG1SB)  B/A   : {dut_ratio:.2f}")
        norm_geo = dut_ratio / geo
        norm_ari = dut_ratio / arith
        print(f"\nNormalized antenna effect (DUT / baseline):")
        print(f"  vs geo-mean  : {norm_geo:.2f}x reception rate")
        print(f"  vs arith-mean: {norm_ari:.2f}x reception rate")
        # rough dB equivalent: in FT8 marginal-decode regime,
        # report-count roughly tracks 10*log10(rate) as a loose proxy
        if norm_geo > 0:
            db_geo = 10 * math.log10(norm_geo)
            print(f"  loose dB proxy (10log10): {db_geo:+.1f} dB  (interpret with caution)")

    # set overlap on DUT
    if results[DUT]:
        a_set = results[DUT]["A"]["rx_set"]
        b_set = results[DUT]["B"]["rx_set"]
        print(f"\n=== BG1SB unique RX overlap ===")
        print(f"  A only : {len(a_set - b_set)}")
        print(f"  B only : {len(b_set - a_set)}")
        print(f"  both   : {len(a_set & b_set)}")


if __name__ == "__main__":
    main()
