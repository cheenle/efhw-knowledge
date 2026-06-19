#!/usr/bin/env python3
"""Import EFHW A/B test data into the dedicated StarRocks table efhw_ab_reports.

Sources (produced earlier in this test session):
  * pskr_adif_store.jsonl  — BG1SB reception reports (role=dut)
  * probe_store.jsonl      — 5 ON80 probe stations' reports (role=probe)

Each record is tagged:
  role   : 'dut' (BG1SB, antenna changed) | 'probe' (ON80, antenna fixed)
  config : 'A' (before switch) | 'B' (after switch), by the 12:26:52 CST cut
  band   : derived from frequency (all bands imported; filter at query time)
  distance_km / bearing : computed at import time vs each monitored station's grid

Idempotent: TRUNCATE then full reload (dataset is ~1e4 rows).

Usage:
    python3 efhw_ab_import.py            # truncate + load + verify
    python3 efhw_ab_import.py --verify   # just print row-count summary
"""
import os
import re
import sys
import json
import math
from datetime import datetime, timezone, timedelta

import mysql.connector

HERE = os.path.dirname(os.path.abspath(__file__))
CST = timezone(timedelta(hours=8))
UTC = timezone.utc

DB_CONFIG = {
    "host": "ham.vlsc.net", "port": 9030, "user": "root",
    "password": "", "database": "pskreporter", "charset": "utf8mb4",
}

TEST_ID = "efhw_49un_vs_lc_20260619"
DUT_CALL = "BG1SB"
DUT_GRID = "ON80da"

DUT_STORE = os.path.join(HERE, "pskr_adif_store.jsonl")
PROBE_STORE = os.path.join(HERE, "probe_store.jsonl")

# Probe stations' home grids (all ON80 = Beijing). BI1MDW reports ON80DB.
PROBE_GRIDS = {
    "BD1AUJ": "ON80", "BH1UWJ": "ON80", "BI1KND": "ON80",
    "BI1MDW": "ON80db", "BI1WIA": "ON80",
}

BAND_RANGES = [
    (1_800_000, 2_000_000, '160m'), (3_500_000, 4_000_000, '80m'),
    (5_330_000, 5_405_000, '60m'), (7_000_000, 7_300_000, '40m'),
    (10_100_000, 10_150_000, '30m'), (14_000_000, 14_350_000, '20m'),
    (18_068_000, 18_168_000, '17m'), (21_000_000, 21_450_000, '15m'),
    (24_890_000, 24_990_000, '12m'), (28_000_000, 29_700_000, '10m'),
    (50_000_000, 54_000_000, '6m'), (144_000_000, 148_000_000, '2m'),
]


def band_of(freq_hz):
    for low, high, name in BAND_RANGES:
        if low <= freq_hz <= high:
            return name
    return ''


def grid_to_latlon(grid):
    if not grid:
        return None, None
    grid = grid.strip().upper()
    if len(grid) < 4:
        return None, None
    try:
        lon = (ord(grid[0]) - 65) * 20 - 180
        lat = (ord(grid[1]) - 65) * 10 - 90
        lon += int(grid[2]) * 2
        lat += int(grid[3]) * 1
        if len(grid) >= 6 and grid[4].isalpha() and grid[5].isalpha():
            lon += (ord(grid[4]) - 65) * (2 / 24) + (2 / 24) / 2
            lat += (ord(grid[5]) - 65) * (1 / 24) + (1 / 24) / 2
        else:
            lon += 1
            lat += 0.5
    except (ValueError, IndexError):
        return None, None
    return lat, lon


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def load_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


import re as _re

UTC = timezone.utc
_FIELD = _re.compile(r"<([A-Za-z0-9_]+)(?::\d+(?::[A-Za-z])?)?>([^<]*)")


def load_dut_adif(paths):
    """Parse BG1SB TX-direction reports from one or more raw ADIF files.

    Only keeps records where someone heard BG1SB (CALL=BG1SB). The actual
    receiver is OPERATOR; its grid is MY_GRIDSQUARE. Dedup across files by
    (receiver, time, freq). Returns store-shaped dicts (rx/loc/dxcc/mode/snr/freq/t).
    """
    seen = set()
    out = []
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if "<eoh>" in text.lower():
            text = text[text.lower().index("<eoh>") + len("<eoh>"):]
        for chunk in _re.split(r"<eor>", text, flags=_re.IGNORECASE):
            chunk = chunk.strip()
            if not chunk:
                continue
            d = {}
            for m in _FIELD.finditer(chunk):
                d[m.group(1).upper()] = m.group(2).strip()
            if not d:
                continue
            # TX direction only: BG1SB is the sender (CALL), receiver is OPERATOR
            if d.get("CALL", "").upper() != DUT_CALL.upper():
                continue
            rx = d.get("OPERATOR", "")
            if not rx or rx.upper() == DUT_CALL.upper():
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
            if not ts:
                continue
            try:
                freq_hz = int(round(float(d.get("FREQ", "0")) * 1_000_000))
            except ValueError:
                freq_hz = 0
            try:
                snr = int(d.get("APP_PSKREP_SNR"))
            except (TypeError, ValueError):
                snr = None
            k = f"{rx}|{ts}|{freq_hz}"
            if k in seen:
                continue
            seen.add(k)
            out.append({
                "rx": rx,
                "loc": d.get("MY_GRIDSQUARE", ""),   # receiver's grid
                "dxcc": d.get("COUNTRY", ""),
                "mode": d.get("MODE", ""),
                "snr": snr,
                "freq": freq_hz,
                "t": ts,
            })
    return out


# Raw ADIF sources for DUT, in priority order (merged + deduped).
# pskr_bg1sb_full.adi covers the earliest A tail; pskr_ab_fresh.adi covers full B.
DUT_ADIF_SOURCES = [
    os.path.join(HERE, "pskr_bg1sb_full.adi"),
    os.path.join(HERE, "pskr_ab_fresh.adi"),
    os.path.join(HERE, "pskr_a2_fresh.adi"),
]


def load_timeline(cursor):
    """Load the switch timeline from efhw_ab_switches, ordered by time.

    Returns a list of (start_ts, config, segment) sorted ascending. Each
    record is assigned to the last segment whose switch_time <= its qso_time.
    Records before the first switch are dropped (no known config).
    """
    cursor.execute(
        """SELECT switch_time, config, segment FROM efhw_ab_switches
           WHERE test_id=%s ORDER BY switch_time ASC""",
        (TEST_ID,),
    )
    timeline = []
    for switch_time, config, segment in cursor.fetchall():
        ts = int(switch_time.replace(tzinfo=CST).timestamp())
        timeline.append((ts, config, segment))
    return timeline


def resolve_segment(t, timeline):
    """Return (config, segment) for timestamp t, or (None, None) if before all."""
    found = None
    for ts, config, segment in timeline:
        if t >= ts:
            found = (config, segment)
        else:
            break
    return found if found else (None, None)


def build_rows(timeline):
    """Yield tuples ready for INSERT. All bands and modes retained."""
    rows = []

    def make_row(monitored, role, home_grid, r):
        freq = int(r.get("freq", 0))
        band = band_of(freq)
        if not band:
            return None   # unknown/out-of-plan frequency
        t = r.get("t")
        if not t:
            return None
        config, segment = resolve_segment(t, timeline)
        if config is None:
            return None   # before the first known switch — unknown config
        qso_time = datetime.fromtimestamp(t, CST).strftime("%Y-%m-%d %H:%M:%S")
        # distance/bearing from monitored station's home grid to receiver
        hlat, hlon = grid_to_latlon(home_grid)
        rlat, rlon = grid_to_latlon(r.get("loc", ""))
        dist = bear = None
        if None not in (hlat, hlon, rlat, rlon):
            dist = round(haversine(hlat, hlon, rlat, rlon), 1)
            bear = round(bearing(hlat, hlon, rlat, rlon), 1)
        snr = r.get("snr")
        return (
            TEST_ID, monitored, role, config, segment,
            r.get("rx", ""), r.get("loc", ""), r.get("dxcc", ""),
            r.get("mode", ""), snr, freq, band, dist, bear, qso_time,
        )

    for r in load_dut_adif(DUT_ADIF_SOURCES):
        row = make_row(DUT_CALL, 'dut', DUT_GRID, r)
        if row:
            rows.append(row)

    for r in load_jsonl(PROBE_STORE):
        probe = r.get("probe", "")
        home = PROBE_GRIDS.get(probe, "ON80")
        row = make_row(probe, 'probe', home, r)
        if row:
            rows.append(row)

    return rows


INSERT_SQL = """
INSERT INTO efhw_ab_reports
(test_id, monitored, role, config, segment, rx_callsign, rx_locator, dxcc,
 mode, snr, frequency, band, distance_km, bearing, qso_time)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""


def verify(cursor):
    cursor.execute("""
        SELECT role, segment, config, COUNT(*) n, COUNT(DISTINCT rx_callsign) rx,
               COUNT(DISTINCT monitored) mon, ROUND(AVG(snr),2) avg_snr,
               MIN(qso_time) t0, MAX(qso_time) t1
        FROM efhw_ab_reports WHERE test_id=%s
        GROUP BY role, segment, config ORDER BY role, segment
    """, (TEST_ID,))
    print(f"{'role':<7}{'seg':<5}{'cfg':<4}{'rows':>7}{'uniqRX':>8}{'mon':>5}{'avgSNR':>8}  window")
    for r in cursor.fetchall():
        print(f"{r[0]:<7}{str(r[1]):<5}{r[2]:<4}{r[3]:>7}{r[4]:>8}{r[5]:>5}{str(r[6]):>8}  {r[7]}->{r[8]}")


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    if "--verify" in sys.argv:
        verify(cursor)
        cursor.close(); conn.close()
        return

    timeline = load_timeline(cursor)
    print("timeline:", [(s, c) for _, c, s in timeline])
    rows = build_rows(timeline)
    print(f"built {len(rows)} rows")
    cursor.execute("TRUNCATE TABLE efhw_ab_reports")
    # batch insert
    B = 500
    for i in range(0, len(rows), B):
        cursor.executemany(INSERT_SQL, rows[i:i + B])
        conn.commit()
    print(f"inserted {len(rows)} rows")
    verify(cursor)
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
