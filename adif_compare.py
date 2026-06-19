#!/usr/bin/env python3
"""Fetch BG1SB reception reports via the PSK Reporter ADIF endpoint and split
them into Config A (49:1 transformer) vs Config B (LC tuner) around the
switch time, then print a comparison.

The ADIF feed returns the last `days` of reports with full timestamps, so we
can slice precisely by switch time without any rolling-window limitations.

Usage:
    python3 adif_compare.py                 # fetch live, compare
    python3 adif_compare.py --save raw.adi  # also save raw ADIF to file
    python3 adif_compare.py --file raw.adi  # parse from a saved file
"""
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta

CALLSIGN = "bg1sb"
CST = timezone(timedelta(hours=8))
UTC = timezone.utc

# Switch from Config A (49:1) to Config B (LC tuner)
SWITCH_CST = datetime(2026, 6, 19, 12, 26, 52, tzinfo=CST)

# Only compare the band under test (15m, 21.074 MHz) by default.
BAND_LO_MHZ = 21.0
BAND_HI_MHZ = 21.5

URL = (
    "https://www.pskreporter.info/cgi-bin/pskdata.pl"
    f"?adif=1&days=1&callsign={CALLSIGN}"
)

FIELD_RE = re.compile(r"<([A-Za-z0-9_]+):(\d+)(?::[A-Za-z])?>")


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "efhw-test/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def parse_adif(text):
    """Parse ADIF records into dicts. Records separated by <eor>."""
    # Drop header up to <eoh>
    idx = text.lower().find("<eoh>")
    if idx != -1:
        text = text[idx + 5:]
    records = []
    for chunk in re.split(r"<eor>", text, flags=re.IGNORECASE):
        chunk = chunk.strip()
        if not chunk:
            continue
        rec = {}
        pos = 0
        while True:
            m = FIELD_RE.search(chunk, pos)
            if not m:
                break
            name = m.group(1).upper()
            length = int(m.group(2))
            start = m.end()
            value = chunk[start:start + length]
            rec[name] = value
            pos = start + length
        if rec:
            records.append(rec)
    return records


def rec_dt(rec):
    """Build a UTC datetime from QSO_DATE + TIME_ON."""
    d = rec.get("QSO_DATE", "")
    t = rec.get("TIME_ON", "")
    if len(d) != 8 or len(t) < 6:
        return None
    try:
        return datetime(
            int(d[0:4]), int(d[4:6]), int(d[6:8]),
            int(t[0:2]), int(t[2:4]), int(t[4:6]),
            tzinfo=UTC,
        )
    except ValueError:
        return None


def to_rec(r):
    dt = rec_dt(r)
    try:
        freq = float(r.get("FREQ", "0"))
    except ValueError:
        freq = 0.0
    try:
        snr = int(r.get("APP_PSKREP_SNR", ""))
    except ValueError:
        snr = None
    try:
        dist = float(r.get("DISTANCE", ""))
    except ValueError:
        dist = None
    return {
        "dt": dt,
        "rx": r.get("CALL", ""),
        "grid": r.get("GRIDSQUARE", ""),
        "country": r.get("COUNTRY", ""),
        "freq": freq,
        "snr": snr,
        "dist": dist,
    }


def summarize(name, recs):
    print(f"\n=== {name} ===")
    if not recs:
        print("  (no reports)")
        return
    times = [r["dt"] for r in recs if r["dt"]]
    t0 = min(times).astimezone(CST).strftime("%H:%M:%S")
    t1 = max(times).astimezone(CST).strftime("%H:%M:%S")
    span_min = (max(times) - min(times)).total_seconds() / 60
    snrs = [r["snr"] for r in recs if r["snr"] is not None]
    dists = [r["dist"] for r in recs if r["dist"] is not None]
    countries = Counter(r["country"] for r in recs if r["country"])
    uniq_rx = len(set(r["rx"] for r in recs))

    print(f"  window (CST)      : {t0} -> {t1}  ({span_min:.1f} min)")
    print(f"  total reports     : {len(recs)}")
    print(f"  unique RX stations: {uniq_rx}")
    print(f"  rx per min        : {uniq_rx / span_min:.2f}" if span_min > 0 else "")
    print(f"  countries (DXCC)  : {len(countries)}")
    if snrs:
        print(f"  SNR avg/min/max   : {sum(snrs)/len(snrs):.1f} / {min(snrs)} / {max(snrs)} dB")
    if dists:
        print(f"  dist avg/max (km) : {sum(dists)/len(dists):.0f} / {max(dists):.0f}")
    print("  --- by country ---")
    for c, n in countries.most_common(12):
        print(f"    {c:<22}{n}")
    return {
        "reports": len(recs),
        "rx": uniq_rx,
        "countries": len(countries),
        "snr_avg": round(sum(snrs)/len(snrs), 1) if snrs else None,
        "snr_min": min(snrs) if snrs else None,
        "snr_max": max(snrs) if snrs else None,
        "dist_avg": round(sum(dists)/len(dists)) if dists else None,
        "dist_max": round(max(dists)) if dists else None,
        "span_min": round(span_min, 1),
    }


def main():
    raw = None
    if "--file" in sys.argv:
        path = sys.argv[sys.argv.index("--file") + 1]
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    else:
        raw = fetch()
        if "--save" in sys.argv:
            path = sys.argv[sys.argv.index("--save") + 1]
            with open(path, "w", encoding="utf-8") as f:
                f.write(raw)
            print(f"saved raw ADIF -> {path}")

    recs = [to_rec(r) for r in parse_adif(raw)]
    recs = [r for r in recs if r["dt"]]

    # Filter to the band under test
    band = [r for r in recs if BAND_LO_MHZ <= r["freq"] <= BAND_HI_MHZ]

    print(f"total parsed reports (all bands, 24h): {len(recs)}")
    print(f"15m band (21.0-21.5 MHz) reports     : {len(band)}")
    print(f"switch A->B at (CST)                 : {SWITCH_CST.strftime('%H:%M:%S')}")

    a = [r for r in band if r["dt"] < SWITCH_CST]
    b = [r for r in band if r["dt"] >= SWITCH_CST]

    sa = summarize("Config A: 49:1 transformer (3xFT-240-51)", a)
    sb = summarize("Config B: LC tuner (SWR 1.3)", b)

    if sa and sb:
        print("\n=== A vs B (15m) ===")
        def line(label, ka, fmt="{}"):
            va = sa.get(ka)
            vb = sb.get(ka)
            print(f"  {label:<20} A={fmt.format(va):<10} B={fmt.format(vb)}")
        line("reports", "reports")
        line("unique RX", "rx")
        line("countries", "countries")
        line("SNR avg (dB)", "snr_avg")
        line("SNR max (dB)", "snr_max")
        line("dist avg (km)", "dist_avg")
        line("dist max (km)", "dist_max")
        line("span (min)", "span_min")


if __name__ == "__main__":
    main()
