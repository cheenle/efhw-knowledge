# SPICE Simulation Suite — EFHW Fuchs ATU V3.0

> **版本**: V3.0 (2026-06-09) — ESP32-S3 + T200-6
> **引擎**: ngspice (未安装) → 解析计算 (Python + Fourier)
> **V2.0 文件**: .cir 网表为 V2.0 格式, 已归档备用

---

## 仿真文件索引

| # | 文件 | 仿真对象 | V3.0 状态 |
|---|------|---------|:---------:|
| 1 | `lc_resonant_tank_analysis.md` | **T200-6 LC 解析分析** (频率覆盖/Q值/效率/电容耐压) | ✅ V3.0 |
| 2 | `lc_resonant_tank_analysis.py` | **Python 谐振计算脚本** (运行 `python3 lc_resonant_tank_analysis.py`) | ✅ V3.0 |
| 3 | `thermal_analysis.md` | **热分析** (T200-6, MOSFET, DC-DC, 伺服) | ✅ V3.0 |
| 4 | `bias_tee_spice.cir` | Bias-T 同轴馈电 (RF+DC) | ✅ 保持 (Bias-T 未变) |
| 5 | `pcb_transmission_lines.md` | PCB 传输线参数 | ⚠️ 需更新 (PCB 缩小) |
| 6 | `lc_resonant_tank.cir` | ~~T200-2 继电器阵列~~ (V2.0 已归档) | ❌ 不适用于 V3.0 |
| 7 | `swr_bridge_spice.cir` | ~~Tandem Match SWR 桥~~ (V3.0 无板载 SWR) | ❌ 不适用于 V3.0 |
| 8 | `relay_driver_spice.cir` | ~~ULN2003A 继电器驱动~~ (V3.0 无继电器) | ❌ 不适用于 V3.0 |

## 关键仿真发现 (V3.0 解析优化)

### 🔑 10m 覆盖的关键依赖: 低杂散电容

| 场景 | C_stray | f_max (C=10pF) | 10m 可调? |
|------|:------:|:--------------:|:---------:|
| V3.0 点对点飞线 | 4 pF | 29.65 MHz | ✅ |
| V2.0 PCB HV 走线 | 10 pF | 24.81 MHz | ❌ |

**结论**: V3.0 的点对点 HV 飞线不仅是简化, 更是 10m 覆盖的**必要条件**。

### 🔑 匝数比对效率无影响

```
Q_loaded = Z_out / XL ∝ n² / N2² = constant (n ∝ N2)
```

效率仅取决于耦合系数 k 和磁芯 Q_u, **不**取决于匝数比。当前 2:14 (49:1) 的阻抗比匹配 2,450Ω 是合理的工程选择。

### 🔑 全频段覆盖验证

| 频段 | f (MHz) | 最优 C (pF) | 是否在 10-500pF 范围内 |
|------|:-------:|:-----------:|:--------------------:|
| 40m | 7.100 | 240 | ✅ |
| 30m | 10.125 | 116 | ✅ |
| 20m | 14.200 | 57 | ✅ |
| 17m | 18.118 | 34 | ✅ |
| 15m | 21.200 | 23 | ✅ |
| 12m | 24.940 | 16 | ✅ |
| 10m | 28.500 | 11 | ✅ (仅 1pF 余量!) |

> ⚠️ 10m 对杂散电容极其敏感 — C_stray > 6pF 即失去 10m。确保接线最短, 避免不必要的金属靠近 HV 节点。

## 运行 Python 仿真

```bash
python3 auto-efhw-tuner/hardware/simulation/lc_resonant_tank_analysis.py
```

输出: V3.0 扫频表 + V2.0 对比 + 匝数比优化 + 最优电容反推表
