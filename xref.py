#!/usr/bin/env python3
"""Cross-reference analysis: use co-grid (ON80) reference stations as
propagation probes to separate antenna effect from ionospheric drift.

For BG1SB and each reference station, slice 15m reports into:
  A window: before switch (12:26:52)
  B window: after switch
Restricted to an EQUAL-LENGTH A-tail vs B (51 min each) for fairness.
Then compare each station's A->B ratio. Reference stations didn't change
antenna, so their A->B change == pure propagation drift baseline.
"""
import re, glob, os
from datetime import datetime, timezone, timedelta
from collections import Counter

CST = timezone(timedelta(hours=8))
SWITCH = datetime(2026,6,19,12,26,52,tzinfo=CST)
# equal window: B is 12:26:58 -> 13:17:59 (~51 min). A tail = 50.8 min before switch
B_END   = datetime(2026,6,19,13,17,59,tzinfo=CST)
WIN_MIN = 51.0
A_START = SWITCH - timedelta(minutes=WIN_MIN)

def parse_adif(path):
    with open(path, errors="ignore") as f:
        txt = f.read()
    recs = []
    for eor in re.split(r"<eor>", txt, flags=re.I):
        d = {}
        for m in re.finditer(r"<([^:>]+):(\d+)(?::[^>]*)?>", eor):
            field = m.group(1).upper(); ln = int(m.group(2))
            start = m.end(); val = eor[start:start+ln]
            d[field] = val
        if "FREQ" in d and "QSO_DATE" in d and "TIME_ON" in d:
            recs.append(d)
    return recs

def to_dt(d):
    try:
        s = d["QSO_DATE"] + d["TIME_ON"].ljust(6,"0")[:6]
        dt = datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return dt.astimezone(CST)
    except Exception:
        return None

def is15m(d):
    try:
        f = float(d["FREQ"]); return 21.0 <= f <= 21.5
    except Exception:
        return False

def slice_station(path):
    recs = parse_adif(path)
    A=[]; B=[]
    for d in recs:
        if not is15m(d): continue
        dt = to_dt(d)
        if dt is None: continue
        if A_START <= dt <= SWITCH: A.append((dt,d))
        elif SWITCH < dt <= B_END:  B.append((dt,d))
    return A,B

def stat(rows):
    rx = set(); ctry=Counter(); snrs=[]
    for dt,d in rows:
        rx.add(d.get("CALL",""))
        if d.get("COUNTRY"): ctry[d["COUNTRY"]]+=1
        try: snrs.append(int(d.get("APP_PSKREP_SNR","")))
        except: pass
    return {
        "reports": len(rows),
        "rx": len(rx),
        "countries": len(ctry),
        "snr_avg": round(sum(snrs)/len(snrs),1) if snrs else None,
    }

def ratio(b,a):
    return round(b/a,2) if a else None

print(f"Equal windows: A {A_START.strftime('%H:%M')}->{SWITCH.strftime('%H:%M')}  |  B {SWITCH.strftime('%H:%M')}->{B_END.strftime('%H:%M')}  ({WIN_MIN:.0f} min each)\n")

# BG1SB from latest full file
files = [("BG1SB","pskr_24h_latest.adi")]
for c in ["BH1UWJ","BD1AUJ","BI1WIA","BI1MDW","BI1KND"]:
    p=f"ref_{c}.adi"
    if os.path.exists(p): files.append((c,p))

hdr = f"{'station':<9}{'win':<4}{'rep':>5}{'rx':>5}{'ctry':>6}{'snr':>7}"
print(hdr); print("-"*len(hdr))
results={}
for call,path in files:
    A,B = slice_station(path)
    sa,sb = stat(A),stat(B)
    results[call]=(sa,sb)
    print(f"{call:<9}{'A':<4}{sa['reports']:>5}{sa['rx']:>5}{sa['countries']:>6}{str(sa['snr_avg']):>7}")
    print(f"{call:<9}{'B':<4}{sb['reports']:>5}{sb['rx']:>5}{sb['countries']:>6}{str(sb['snr_avg']):>7}")

print("\n=== A->B ratio (B/A), reference stations = propagation baseline ===")
print(f"{'station':<9}{'rep_x':>7}{'rx_x':>7}{'ctry_x':>8}{'snr_d':>8}")
print("-"*39)
for call,(sa,sb) in results.items():
    rep_x=ratio(sb['reports'],sa['reports'])
    rx_x=ratio(sb['rx'],sa['rx'])
    ct_x=ratio(sb['countries'],sa['countries'])
    snr_d = round(sb['snr_avg']-sa['snr_avg'],1) if (sa['snr_avg'] is not None and sb['snr_avg'] is not None) else None
    tag = "  <-- DUT (antenna changed)" if call=="BG1SB" else ""
    print(f"{call:<9}{str(rep_x):>7}{str(rx_x):>7}{str(ct_x):>8}{str(snr_d):>8}{tag}")
