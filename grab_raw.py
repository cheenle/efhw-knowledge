#!/usr/bin/env python3
"""Continuously accumulate BG1SB reception reports into a deduplicated store.

Each run fetches the last 900s window from the PSK Reporter query API and
appends any *new* reception reports to pskr_raw.jsonl, deduplicating by
(receiver, flowStartSeconds, frequency). Because windows overlap, running
this every few minutes guarantees complete, gap-free coverage.

Usage:
    python3 grab_raw.py          # one fetch, append new records
    python3 grab_raw.py --stats  # print summary of stored data so far
"""
import sys
import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone, timedelta

CALLSIGN = "bg1sb"
CST = timezone(timedelta(hours=8))
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pskr_raw.jsonl")

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


def key(r):
    return f"{r['rx']}|{r['t']}|{r['freq']}"


def load_keys():
    keys = set()
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    keys.add(key(json.loads(line)))
                except json.JSONDecodeError:
                    pass
    return keys


def append(records):
    existing = load_keys()
    new = [r for r in records if key(r) not in existing]
    if new:
        with open(RAW, "a") as f:
            for r in new:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(new)


def load_all():
    recs = []
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        recs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return recs


def stats():
    recs = load_all()
    if not recs:
        print("no stored records yet")
        return
    times = [r["t"] for r in recs if r["t"]]
    t0 = datetime.fromtimestamp(min(times), CST).strftime("%Y-%m-%d %H:%M:%S")
    t1 = datetime.fromtimestamp(max(times), CST).strftime("%Y-%m-%d %H:%M:%S")
    snrs = [r["snr"] for r in recs if r["snr"] is not None]
    countries = Counter(r["dxcc"] for r in recs if r["dxcc"])
    freqs = Counter(round(r["freq"] / 1000) for r in recs if r["freq"])
    print(f"stored records   : {len(recs)}")
    print(f"unique RX        : {len(set(r['rx'] for r in recs))}")
    print(f"countries        : {len(countries)}")
    print(f"time span (CST)  : {t0} -> {t1}")
    if snrs:
        print(f"SNR avg/min/max  : {round(sum(snrs)/len(snrs),1)} / {min(snrs)} / {max(snrs)} dB")
    print(f"freq centers(kHz): {dict(freqs)}")


def main():
    if "--stats" in sys.argv:
        stats()
        return
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")
    try:
        reps = parse(fetch())
    except Exception as e:
        print(f"{now}  fetch error: {e}")
        return
    n = append(reps)
    total = len(load_all())
    print(f"{now}  window={len(reps)}  new={n}  total_stored={total}")


if __name__ == "__main__":
    main()
