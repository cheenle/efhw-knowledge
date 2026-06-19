#!/usr/bin/env python3
"""Accumulate BG1SB reception reports via the PSK Reporter ADIF bulk endpoint.

Unlike the realtime query API (retrieve.pskreporter.info/query, -900s window),
which is heavily rate-limited (HTTP 503 below ~10-min intervals), the ADIF bulk
endpoint returns the FULL last-24h report set every call. So:

  * a single successful fetch already covers everything in the last 24h;
  * long poll intervals never create gaps (data persists ~24h);
  * we still dedup into a growing store so records are preserved even after
    they age out of the 24h window during a long test.

Each record is keyed by (receiver, time_utc, freq_hz) and appended to
pskr_adif_store.jsonl if new. Times are parsed as UTC and converted to CST.

Usage:
    python3 accum_adif.py            # one fetch, append new records
    python3 accum_adif.py --stats    # summarize stored data
    python3 accum_adif.py --stats --since "2026-06-19 12:26:52"  # window stats
"""
import os
import re
import sys
import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta

CALLSIGN = "bg1sb"
UTC = timezone.utc
CST = timezone(timedelta(hours=8))
HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "pskr_adif_store.jsonl")

URL = (
    "https://www.pskreporter.info/cgi-bin/pskdata.pl"
    f"?adif=1&days=1&callsign={CALLSIGN}"
)

FIELD = re.compile(r"<([A-Za-z0-9_]+)(?::\d+(?::[A-Za-z])?)?>([^<]*)")


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "efhw-test/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def parse(text):
    """Yield one dict per <eor> record from the ADIF body."""
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
        # date/time are UTC
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
        try:
            dist = float(d.get("DISTANCE"))
        except (TypeError, ValueError):
            dist = None
        # pskdata.pl returns BOTH directions:
        #   CALL=BG1SB  -> others heard BG1SB (TX direction) ; receiver=OPERATOR, rx grid=MY_GRIDSQUARE
        #   OPERATOR=BG1SB -> BG1SB heard others (RX direction)
        # For antenna TX comparison we only want the TX direction, and the
        # real receiver lives in OPERATOR (not CALL, which is BG1SB itself).
        call = d.get("CALL", "").upper()
        op = d.get("OPERATOR", "").upper()
        if call != CALLSIGN.upper():
            continue  # skip RX-direction (and any unrelated) records
        rx = op or call                       # receiver = OPERATOR
        rx_loc = d.get("MY_GRIDSQUARE", "")    # receiver's grid
        recs.append({
            "rx": rx,                          # who heard BG1SB
            "loc": rx_loc,
            "dxcc": d.get("COUNTRY", ""),
            "mode": d.get("MODE", ""),
            "snr": snr,
            "freq": freq_hz,
            "t": ts,
            "dist": dist,                      # DISTANCE from PSKR (km), receiver<->BG1SB
        })
    return recs


def key(r):
    return f"{r['rx']}|{r['t']}|{r['freq']}"


def load_keys():
    keys = set()
    if os.path.exists(STORE):
        with open(STORE) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        keys.add(key(json.loads(line)))
                    except json.JSONDecodeError:
                        pass
    return keys


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


def append(records):
    existing = load_keys()
    new = [r for r in records if r["t"] and key(r) not in existing]
    if new:
        with open(STORE, "a") as f:
            for r in new:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(new)


def stats(since=None):
    recs = load_all()
    if since:
        cut = int(datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
                  .replace(tzinfo=CST).timestamp())
        recs = [r for r in recs if r["t"] and r["t"] >= cut]
    # focus on 15m FT8 for the test
    band = [r for r in recs if 21_000_000 <= r["freq"] <= 21_500_000
            and r.get("mode", "").upper() == "FT8"]
    if not recs:
        print("no stored records yet")
        return
    times = [r["t"] for r in recs if r["t"]]
    t0 = datetime.fromtimestamp(min(times), CST).strftime("%Y-%m-%d %H:%M:%S")
    t1 = datetime.fromtimestamp(max(times), CST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== ALL bands ===")
    print(f"stored records   : {len(recs)}")
    print(f"unique RX        : {len(set(r['rx'] for r in recs))}")
    print(f"time span (CST)  : {t0} -> {t1}")
    if band:
        bt = [r["t"] for r in band if r["t"]]
        snrs = [r["snr"] for r in band if r["snr"] is not None]
        ctry = Counter(r["dxcc"] for r in band if r["dxcc"])
        bt0 = datetime.fromtimestamp(min(bt), CST).strftime("%H:%M:%S")
        bt1 = datetime.fromtimestamp(max(bt), CST).strftime("%H:%M:%S")
        print(f"\n=== 15m FT8 (21.0-21.5 MHz){' since '+since if since else ''} ===")
        print(f"reports          : {len(band)}")
        print(f"unique RX        : {len(set(r['rx'] for r in band))}")
        print(f"countries        : {len(ctry)}")
        print(f"window (CST)     : {bt0} -> {bt1}")
        if snrs:
            print(f"SNR avg/min/max  : {round(sum(snrs)/len(snrs),1)} / {min(snrs)} / {max(snrs)} dB")
        print("top countries    : " + ", ".join(f"{c}={n}" for c, n in ctry.most_common(8)))


def main():
    if "--stats" in sys.argv:
        since = None
        if "--since" in sys.argv:
            since = sys.argv[sys.argv.index("--since") + 1]
        stats(since)
        return
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")
    try:
        recs = parse(fetch())
    except Exception as e:
        print(f"{now}  fetch error: {e}")
        return
    n = append(recs)
    total = len(load_all())
    print(f"{now}  fetched={len(recs)}  new={n}  total_stored={total}")


if __name__ == "__main__":
    main()
