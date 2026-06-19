#!/usr/bin/env python3
"""Ingest ON80 probe-station ADIF files into a persistent deduplicated store.

The 5 stations physically located in grid ON80 (the same grid as BG1SB) act as
propagation probes: their antennas did NOT change during the A/B test, so their
report counts / SNR over the same windows reflect pure ionospheric drift. By
differencing BG1SB's change against the probe baseline we isolate the antenna
effect from propagation.

This script parses each probe_<CALL>.adi file (who-heard-that-probe) and appends
new records to probe_store.jsonl, tagged with the probe callsign and keyed by
(probe, receiver, time_utc, freq_hz) so repeated ingests never duplicate.

Probe stations (auto-discovered from BG1SB's report set, grid=ON80*):
    BD1AUJ  BH1UWJ  BI1KND  BI1MDW(ON80DB)  BI1WIA

Usage:
    python3 ingest_probes.py            # ingest all probe_*.adi files
    python3 ingest_probes.py --stats    # per-probe summary (15m FT8)
"""
import os
import re
import sys
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

UTC = timezone.utc
CST = timezone(timedelta(hours=8))
HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "probe_store.jsonl")

PROBES = ["BD1AUJ", "BH1UWJ", "BI1KND", "BI1MDW", "BI1WIA"]

FIELD = re.compile(r"<([A-Za-z0-9_]+)(?::\d+(?::[A-Za-z])?)?>([^<]*)")


def parse(text, probe):
    """Yield one dict per <eor> record. rx = whoever heard the probe."""
    if "<eoh>" in text.lower():
        text = text[text.lower().index("<eoh>") + len("<eoh>"):]
    recs = []
    for chunk in re.split(r"<eor>", text, flags=re.IGNORECASE):
        chunk = chunk.strip()
        if not chunk:
            continue
        d = {}
        for m in FIELD.finditer(chunk):
            d[m.group(1).upper()] = m.group(2).strip()
        if not d:
            continue
        date, t = d.get("QSO_DATE", ""), d.get("TIME_ON", "")
        ts = None
        if len(date) == 8 and len(t) >= 6:
            try:
                dt = datetime(int(date[0:4]), int(date[4:6]), int(date[6:8]),
                              int(t[0:2]), int(t[2:4]), int(t[4:6]), tzinfo=UTC)
                ts = int(dt.timestamp())
            except ValueError:
                ts = None
        try:
            freq_hz = int(round(float(d.get("FREQ", "0")) * 1_000_000))
        except ValueError:
            freq_hz = 0
        try:
            snr = int(d.get("APP_PSKREP_SNR"))
        except (TypeError, ValueError):
            snr = None
        recs.append({
            "probe": probe,                   # the ON80 probe station
            "rx": d.get("OPERATOR", ""),      # who heard the probe (receiver)
            "loc": d.get("MY_GRIDSQUARE", ""),  # receiver's grid
            "dxcc": d.get("COUNTRY", ""),
            "mode": d.get("MODE", ""),
            "snr": snr,
            "freq": freq_hz,
            "t": ts,
        })
    return recs


def key(r):
    return f"{r['probe']}|{r['rx']}|{r['t']}|{r['freq']}"


def load_all():
    recs = []
    if os.path.exists(STORE):
        with open(STORE) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        recs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return recs


def load_keys():
    return {key(r) for r in load_all()}


def append(records):
    existing = load_keys()
    new = [r for r in records if r["t"] and key(r) not in existing]
    if new:
        with open(STORE, "a") as f:
            for r in new:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(new)


def ingest():
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")
    total_new = 0
    for probe in PROBES:
        path = os.path.join(HERE, f"probe_{probe}.adi")
        if not os.path.exists(path):
            print(f"  {probe}: file missing, skip")
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        recs = parse(text, probe)
        n = append(recs)
        total_new += n
        print(f"  {probe}: parsed={len(recs)}  new={n}")
    print(f"{now}  total_new={total_new}  store_total={len(load_all())}")


def stats():
    recs = load_all()
    if not recs:
        print("no probe records yet")
        return
    by_probe = defaultdict(list)
    for r in recs:
        by_probe[r["probe"]].append(r)
    print(f"probe_store.jsonl: {len(recs)} records, {len(by_probe)} probes\n")
    print(f"{'probe':<9}{'all':>7}{'15mFT8':>8}{'uniqRX':>8}{'ctry':>6}  span(CST)")
    for probe in PROBES:
        rs = by_probe.get(probe, [])
        if not rs:
            print(f"{probe:<9}{'(no data)':>7}")
            continue
        band = [r for r in rs if 21_000_000 <= r["freq"] <= 21_500_000
                and r.get("mode", "").upper() == "FT8"]
        times = [r["t"] for r in band if r["t"]]
        ctry = len(set(r["dxcc"] for r in band if r["dxcc"]))
        urx = len(set(r["rx"] for r in band if r["rx"]))
        if times:
            s0 = datetime.fromtimestamp(min(times), CST).strftime("%H:%M")
            s1 = datetime.fromtimestamp(max(times), CST).strftime("%H:%M")
            span = f"{s0}->{s1}"
        else:
            span = "-"
        print(f"{probe:<9}{len(rs):>7}{len(band):>8}{urx:>8}{ctry:>6}  {span}")


def main():
    if "--stats" in sys.argv:
        stats()
    else:
        ingest()


if __name__ == "__main__":
    main()
