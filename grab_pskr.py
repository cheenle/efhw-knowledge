#!/usr/bin/env python3
"""Grab a live PSK Reporter reception window for BG1SB and print a summary.

Usage:
    python3 grab_pskr.py [label]

- Queries the PSK Reporter query API for the last 900s of reports where
  BG1SB is the SENDER (isSender=1), i.e. who heard us.
- Prints reports / rx stations / countries / SNR stats / by-country / top10.
- Appends one JSON line to efhw_test_log.json with an optional config label.
"""
import sys
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone, timedelta

CALLSIGN = "bg1sb"
CST = timezone(timedelta(hours=8))
LOG = "efhw_test_log.json"

URL = (
    "https://retrieve.pskreporter.info/query"
    f"?senderCallsign={CALLSIGN}"
    "&flowStartSeconds=-900"
    "&rronly=1"
)


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "efhw-test/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse(data):
    root = ET.fromstring(data)
    reps = []
    for rr in root.iter("receptionReport"):
        a = rr.attrib
        if a.get("senderCallsign", "").upper() != CALLSIGN.upper():
            continue
        try:
            snr = int(a["sNR"]) if "sNR" in a else None
        except (ValueError, KeyError):
            snr = None
        reps.append({
            "rx": a.get("receiverCallsign", ""),
            "loc": a.get("receiverLocator", ""),
            "dxcc": a.get("receiverDXCC", ""),
            "snr": snr,
            "freq": int(a.get("frequency", 0)),
            "t": int(a.get("flowStartSeconds", 0)),
        })
    return reps


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else ""
    data = fetch()
    reps = parse(data)
    if not reps:
        print("no reports in window")
        return

    times = [r["t"] for r in reps if r["t"]]
    snrs = [r["snr"] for r in reps if r["snr"] is not None]
    countries = Counter(r["dxcc"] for r in reps if r["dxcc"])
    freqs = Counter(round(r["freq"] / 1000) for r in reps if r["freq"])

    t0 = datetime.fromtimestamp(min(times), CST).strftime("%H:%M:%S")
    t1 = datetime.fromtimestamp(max(times), CST).strftime("%H:%M:%S")
    fetched = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")

    avg = round(sum(snrs) / len(snrs), 1) if snrs else None

    print(f"=== {label or 'window'} — PSKR live ===")
    print(f"fetched           : {fetched}")
    print(f"window (CST)      : {t0} -> {t1}")
    print(f"total reports     : {len(reps)}")
    print(f"unique RX stations: {len(set(r['rx'] for r in reps))}")
    print(f"countries (DXCC)  : {len(countries)}")
    print(f"SNR avg/min/max   : {avg} / {min(snrs) if snrs else None} / {max(snrs) if snrs else None} dB")
    print(f"freq centers (kHz): {dict(freqs)}")
    print("\n--- by country ---")
    for c, n in countries.most_common():
        print(f"  {c:<22}{n}")
    print("\n--- top 10 RX by SNR ---")
    top = sorted([r for r in reps if r["snr"] is not None],
                 key=lambda r: r["snr"], reverse=True)[:10]
    for r in top:
        print(f"  {r['rx']:<10} {r['loc']:<8} {r['dxcc']:<18} {r['snr']:+d} dB")

    entry = {
        "config": label,
        "fetched_at": fetched,
        "window_cst": f"{t0}-{t1}",
        "reports": len(reps),
        "rx_stations": len(set(r["rx"] for r in reps)),
        "countries": len(countries),
        "snr_avg": avg,
        "snr_min": min(snrs) if snrs else None,
        "snr_max": max(snrs) if snrs else None,
    }
    with open(LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\nsaved -> {LOG}")


if __name__ == "__main__":
    main()
