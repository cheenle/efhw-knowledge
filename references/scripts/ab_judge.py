#!/usr/bin/env python3
"""变换器 A/B 台架判据速算 — 配套 references/transformer_ab_protocol.md

用法:
  python3 ab_judge.py s21 <新盒dB> <旧盒dB>   # S21 幅度(负dB), 输出效率与"代差"判定
  python3 ab_judge.py thermal <盒壁稳态C> <SWR漂移>  # P2 通过门判定
  python3 ab_judge.py --selftest

判据来源: references/core-swap-evidence-2026-08.md §4 (红线) 与 P1 (<0.5dB 差→效率代差叙事作废)。
"""
import sys

AMBIENT_REF = 25.0  # 参考室温; 红线判据为绝对值 55°C, 此值仅用于报告温升


def eta(db: float) -> float:
    """S21 dB (负值) -> 传输效率 %"""
    return 100.0 * 10 ** (db / 10.0)


def s21(new_db: float, old_db: float) -> int:
    assert new_db <= 0 and old_db <= 0, "S21 应为负 dB 值"
    e_new, e_old = eta(new_db), eta(old_db)
    delta = abs(new_db - old_db)
    verdict = "相对差 <0.5dB → 外部报告'效率代差'叙事作废" if delta < 0.5 \
        else f"相对差 {delta:.2f}dB ≥0.5dB → 代差成立, 回填 evidence §2"
    print(f"新盒 {new_db:+.2f}dB = {e_new:.1f}% | 旧盒 {old_db:+.2f}dB = {e_old:.1f}% | Δ={delta:.2f}dB")
    print("判定:", verdict)
    return 0


def thermal(case_c: float, swr_drift: float) -> int:
    t_ok, d_ok = case_c <= 55.0, swr_drift < 0.2
    print(f"盒壁 {case_c:.1f}°C (≤55 {t_ok}) | SWR漂移 {swr_drift:.2f} (<0.2 {d_ok}) | 温升 ΔT={case_c-AMBIENT_REF:.0f}K@参考室温{AMBIENT_REF:.0f}°C")
    if t_ok and d_ok:
        print("P2 通过 → 可解除 core-swap-evidence §4 对应红线 (在表内加实测行)")
    else:
        print("P2 未通过 → 红线维持: FT8/CW ≤50W (SSB 100W 仍可用)")
    return 0


def selftest() -> int:
    assert abs(eta(-0.5) - 89.1) < 0.2
    assert abs(eta(-1.25) - 75.0) < 0.2      # MM0OPX FT240-43 单只 80m 值
    assert abs(eta(-0.44) - 90.3) < 0.3      # 2643 2:14 下沿
    thermal.__name__ == "thermal"
    print("selftest OK")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        sys.exit(selftest())
    elif len(a) == 3 and a[0] == "s21":
        sys.exit(s21(float(a[1]), float(a[2])))
    elif len(a) == 3 and a[0] == "thermal":
        sys.exit(thermal(float(a[1]), float(a[2])))
    print(__doc__)
    sys.exit(1)
