# SPICE Simulation Suite — EFHW Auto Tuner 100W
# =============================================
# 用于 LTSpice / ngspice / QUCS 的电路仿真网表
# 覆盖: SWR桥 · LC谐振回路 · Bias-T · 继电器驱动 · PCB传输线
# =============================================

---

## 仿真文件索引

| # | 文件 | 仿真对象 | 引擎 |
|---|------|---------|------|
| 1 | `swr_bridge_spice.cir` | Tandem Match 定向耦合器 (FT37-43, BAT41) | LTSpice / ngspice |
| 2 | `lc_resonant_tank.cir` | T200-2 并联 LC 谐振回路 (含电容阵列) | LTSpice / ngspice |
| 3 | `bias_tee_spice.cir` | Bias-T 同轴馈电电路 (RF+DC 叠加) | LTSpice / ngspice |
| 4 | `relay_driver_spice.cir` | ULN2003A + G5Q-14 继电器线圈驱动 | LTSpice / ngspice |
| 5 | `pcb_transmission_lines.md` | PCB 传输线参数 (微带/共面波导/差分对/过孔) | TX-Line / KiCad Calculator |
| 6 | `thermal_analysis.md` | 热仿真参数 (T200-2, MLCC, 继电器, 稳压器) | 解析计算 + CFD 边界条件 |

## 仿真环境配置

### LTSpice (推荐, 免费)
```bash
# macOS
brew install --cask ltspice

# 打开任意 .cir 文件
open swr_bridge_spice.cir
```

### ngspice (开源, CLI)
```bash
# macOS
brew install ngspice

# 运行仿真
ngspice -b swr_bridge_spice.cir
```

### QUCS (开源, GUI)
```bash
brew install qucs
# 导入 .cir 或手动搭建原理图
```

---

## 关键仿真参数速查

### RF 信号源
```
频率范围: 1.8 – 30 MHz (HF 全段)
功率: 0.5W – 100W (+27 dBm – +50 dBm)
阻抗: 50Ω (非平衡)
波形: 正弦 (CW 模式) 或瞬态包络 (SSB)
```

### 天线终端模型 (EFHW)
```
等效阻抗: 1,500 – 3,500 Ω (取决于高度/环境/Counterpoise)
标称阻抗: 2,112 Ω (0.05λ counterpoise 条件下)
电抗: ±j500 Ω (取决于频率偏移谐振点)
模型: 电阻串联电感 (感性偏移) 或 电阻并联电容 (容性偏移)
```

### 磁芯 SPICE 模型参数
| 磁芯 | L_1T (nH) | R_parallel (kΩ) @ 7MHz | C_stray (pF) |
|------|-----------|----------------------|--------------|
| T200-2 (AL=12nH) | 12 | 45 | ~1 |
| FT37-43 (AL=420nH) | 420 | 2.5 | ~2 |
| FT50-43 (AL=520nH) | 520 | 3.0 | ~2.5 |

---

## 仿真验证清单

- [ ] SWR 桥定向性 > 25 dB @ 1.8-30 MHz
- [ ] LC 谐振回路 Q_loaded = 8-15 (取决于频段)
- [ ] LC 谐振电容峰值电压 < 3KV @ 100W
- [ ] Bias-T 插入损耗 (S21) < 0.2 dB @ 1.8-30 MHz
- [ ] Bias-T RF-DC 隔离 (S31) > 60 dB @ 1.8-30 MHz
- [ ] 继电器线圈反峰电压 < 50V (ULN2003A 额定)
- [ ] HV_BUS 传输线特性阻抗 = 50Ω ±5%
- [ ] T200-2 温升 < 25°C @ 100W FT8 连续
