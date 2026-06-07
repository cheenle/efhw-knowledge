# EFHW Auto Tuner 100W — 原理图描述文档 (Schematic Description)

> **Document ID**: SCH-EFHW-100W-V1.0
> **PCB Reference**: EFHW-100W-PCB-V1.0 (140×90mm, 2-layer FR4)
> **Design Tool**: KiCad V7+ / 立创 EDA
> **Status**: Design Complete

---

## 1. 原理图层次结构

```
Root Sheet: EFHW_Auto_Tuner_100W
│
├── Sheet 1/6: POWER (A区 — 电源管理)
│   Bias-T DC提取 → 1N4007防反 → LM7812(12V) → 78L05(5V)
│
├── Sheet 2/6: MCU (A区 — 微控制器)
│   PIC16F1938 + ICSP + 时钟 + 复位 + 去耦
│
├── Sheet 3/6: SWR_BRIDGE (A区 — SWR检测桥)
│   Tandem Match 定向耦合器 (FT37-43 ×2, BAT41 ×2)
│
├── Sheet 4/6: RELAY_DRIVE (A→B区 — 继电器驱动)
│   ULN2003A 达林顿阵列 + 7路继电器控制信号穿越开槽
│
├── Sheet 5/6: HV_TANK (B区 — 高压谐振回路)
│   T200-2×2 磁芯 2:13 + 7位电容阵列(10只1812 MLCC) + 7×G5Q-14
│
└── Sheet 6/6: PROTECTION (B区 — 保护电路)
    90V GDT + 2.2MΩ 静电泄放 + 天线/地网端子
```

---

## 2. Sheet 1/6: POWER — 电源管理

### 2.1 电路描述

同轴电缆芯线同时承载 RF 信号和 13.8V DC。Bias-T 提取电路通过 L_bias 扼流圈分离 DC，经 1N4007 防反接后送入 LM7812 稳压到 12V，再经 78L05 稳压到 5V 供 MCU。

### 2.2 完整 Netlist

| Net Name | 连接点 | 类型 | 预期电压 | 预期电流 |
|----------|--------|------|---------|---------|
| `COAX_CENTER` | J1(SO-239芯线) → C_block1,2(热端) → L_bias(热端) | RF+DC 叠加 | 0-100V RF + 13.8V DC | ≤ 2A RF + 0.2A DC |
| `RF_50OHM_IN` | C_block1,2(冷端) → SWR桥主线入口 | 纯 RF (隔直后) | 0-100V RF | ≤ 2A RF |
| `DC_RAW` | L_bias(冷端) → D_power(阳极) | 脉动 DC | 13.8V (±2V) | ≤ 250mA |
| `DC_12V_PRE` | D_power(阴极) → U3(LM7812, IN) → C7,C8(对地) | 整流后 DC | 13.3V (13.8-0.5Vf) | ≤ 250mA |
| `VCC_12V` | U3(OUT) → U4(78L05, IN) → 7×继电器线圈(+端) → ULN2003A COM(Pin9) | 稳压 12V | 12.0V ± 0.5V | ≤ 200mA |
| `VCC_5V` | U4(OUT) → U1(Pin20, VDD) → ICSP Pin2 | 稳压 5V | 5.0V ± 0.25V | ≤ 10mA |
| `GND_A_POWER` | U3(GND), U4(GND), D_power(阴极滤容对地), C7,C8(对地) | A区功率地 | 0V (参考) | — |
| `GND_CHASSIS` | J1(外壳) → 铝壳 → J3(地网端子) | 机箱地 | 0V (参考) | — |

### 2.3 元件清单

| 位号 | 元件 | 型号/值 | 封装 | 功能 |
|------|------|---------|------|------|
| J1 | 同轴输入座 | SO-239 (M座) 法兰安装 | Panel | RF+DC 输入, 外壳接地 |
| C_block1, C_block2 | 隔直电容 | 10nF / 1KV / C0G | 1206 | 隔 DC 通 RF, 两只并联降 ESR/ESL |
| L_bias | RF 扼流圈 | 22μH / 3A 工字电感 或 FT37-43 绕 15T | TH(CD75) 或 磁环 | 隔 RF 通 DC |
| D_power | 防反接二极管 | 1N4007 (1000V/1A) | DO-41 | 防止 DC 电源反接损坏电路 |
| U3 | 12V 稳压器 | LM7812ACT | TO-220 | 稳压 13.8V → 12V |
| U4 | 5V 稳压器 | 78L05 | TO-92 | 稳压 12V → 5V |
| C_in_12V | 输入滤波电解 | 47µF / 25V | 电解 D6.3mm | LM7812 输入旁路 |
| C_out_12V | 输出滤波电解 | 47µF / 25V | 电解 D6.3mm | LM7812 输出旁路 |
| C_byp_12V_1,2 | 高频旁路 | 100nF / 50V / X7R | 0805 | 12V 轨 RF 去耦 |
| C_in_5V | 输入滤波 | 10µF / 16V | 电解/钽 | 78L05 输入旁路 |
| C_out_5V | 输出滤波 | 10µF / 16V | 电解/钽 | 78L05 输出旁路 |
| C_byp_5V_1,2 | 高频旁路 | 100nF / 50V / X7R | 0805 | 5V 轨 RF 去耦 |

### 2.4 设计规则验证

| 规则 | 参数 | 状态 |
|------|------|:----:|
| LM7812 输入-输出压差 > 2.0V | 13.3V - 12V = 1.3V ⚠️ | **不足！需 >2V** |
| LM7812 替代方案 | 使用 LDO (LM2940-12, 压差 0.5V) 或提高 Bias-T 输入电压到 15V | 待修正 |
| 78L05 输入-输出压差 > 2.0V | 12V - 5V = 7.0V | ✓ |
| 1N4007 反向耐压 > 输入 | 1000V >> 13.8V | ✓ |
| C_block 耐压 > DC 偏置 | 1KV >> 13.8V | ✓ |
| L_bias DC 电流 > 负载 | 3A >> 200mA | ✓ |
| C0G 容值不随 DC 偏压变化 | 零压降特性 | ✓ |

> ⚠️ **重要设计修正**: LM7812 在 Bias-T 13.8V 供电时, 输入-输出压差仅 1.3V (考虑 1N4007 的 0.5V Vf 压降), 不满足 LM7812 的 2.0V 最小压差要求。
> **修正方案**: 
> - 替换 LM7812 为 **LM2940CT-12** (LDO, 压差 0.5V @ 1A), 或
> - 将 Bias-T 供电电压提高到 **15-16V**, 或
> - 在 L_bias 前增加倍压整流 (复杂)

---

## 3. Sheet 2/6: MCU — 微控制器

### 3.1 电路描述

PIC16F1938 是系统主控。7 个 GPIO (RB0-RB6) 控制电容阵列继电器。2 路 ADC (AN0, AN1) 读取 SWR 桥的正向/反向检波电压。ICSP 接口用于固件烧录和调试。

### 3.2 完整 Netlist

| Net Name | 连接点 | 类型 | 预期电压 | 备注 |
|----------|--------|------|---------|------|
| `VCC_5V` | U1(Pin20) + C_byp_mcu1,2 + ICSP(Pin2) | 电源 | 5.0V ± 0.25V | — |
| `DGND` | U1(Pin8,19) + C_byp_mcu 对地 + ICSP(Pin3) | 数字地 | 0V | A区数字地平面 |
| `MCLR` | U1(Pin1) → R_mclr(10kΩ) → VCC_5V; C_mclr(100nF) → DGND; ICSP(Pin1) | 复位 | 5.0V (运行) / 13V (编程) | 内部弱上拉 + 外部 10kΩ |
| `SWR_FWD` | U1(Pin2, RA0/AN0) → R_swr_fwd(10kΩ) → SWR_BRIDGE V_FWD_DC | 模拟输入 | 0-3V DC | 10-bit ADC |
| `SWR_REV` | U1(Pin3, RA1/AN1) → R_swr_rev(10kΩ) → SWR_BRIDGE V_REV_DC | 模拟输入 | 0-3V DC | 10-bit ADC |
| `C_RELAY_1` | U1(Pin21, RB0) → ULN2003A IN1 | 数字输出 | 0V/5V | bit0=10pF |
| `C_RELAY_2` | U1(Pin22, RB1) → ULN2003A IN2 | 数字输出 | 0V/5V | bit1=22pF |
| `C_RELAY_3` | U1(Pin23, RB2) → ULN2003A IN3 | 数字输出 | 0V/5V | bit2=47pF |
| `C_RELAY_4` | U1(Pin24, RB3) → ULN2003A IN4 | 数字输出 | 0V/5V | bit3=100pF |
| `C_RELAY_5` | U1(Pin25, RB4) → ULN2003A IN5 | 数字输出 | 0V/5V | bit4=220pF |
| `C_RELAY_6` | U1(Pin26, RB5) → ULN2003A IN6 | 数字输出 | 0V/5V | bit5=470pF |
| `C_RELAY_7` | U1(Pin27, RB6) → ULN2003A IN7 | 数字输出 | 0V/5V | bit6=1000pF |
| `PGC` | U1(Pin28, RB7/RB6-ICSP) → ICSP(Pin5) | ICSP 时钟 | — | RB6 复用 |
| `PGD` | U1(Pin27, RB7) → ICSP(Pin4) | ICSP 数据 | — | RB7 复用 |
| `BUZZER` | U1(Pin11, RC0) → Q1(Base) | 数字输出 | 0V/5V | 蜂鸣器驱动 (可选) |
| `LED` | U1(Pin12, RC1) → R_led(1kΩ) → LED(阳极) | 数字输出 | 0V/5V | 状态指示 |
| `NTC_AN2` | U1(Pin4, RA2/AN2) → NTC分压点 | 模拟输入 | 0-5V | 可选温度传感器 |
| `NC_RC2-6` | U1(Pin13-18, RC2-RC6) | — | 悬空 | 原电感控制引脚, 本设计不用 |

### 3.3 元件清单

| 位号 | 元件 | 型号/值 | 封装 | 功能 |
|------|------|---------|------|------|
| U1 | MCU | PIC16F1938-I/SO | SOIC-28W | 主控 |
| R_mclr | 上拉电阻 | 10kΩ / 1% | 0805 | MCLR 上拉到 5V |
| C_mclr | 滤波电容 | 100nF / 50V X7R | 0805 | MCLR 去抖 |
| C_byp_mcu1,2 | 去耦电容 | 100nF / 50V X7R | 0805 | VDD 高频去耦 (每 VSS 一只) |
| C_bulk_mcu | 储能电容 | 10µF / 16V | 钽/电解 | VDD 低频储能 |
| R_swr_fwd, R_swr_rev | 限流电阻 | 10kΩ / 1% | 0805 | ADC 输入保护 |
| Q1 | NPN 三极管 | 2N2222A | SOT-23 | 蜂鸣器驱动 |
| R_led | 限流电阻 | 1kΩ / 1% | 0805 | LED 限流 |
| LED1 | 指示灯 | 3mm 红/绿 LED | TH 3mm | 状态指示 |
| BZ1 | 蜂鸣器 | 5V 有源蜂鸣器 | TH 12mm | 音响反馈 |
| ICSP | 编程排针 | 1×5 Pin 2.54mm直针 | TH | 固件烧录/调试 |

### 3.4 OSC/时钟树

```
时钟源: 内部 HFINTOSC 8 MHz
PLL:    4x → 32 MHz (F_osc)
F_cy:   32 MHz / 4 = 8 MIPS

ADC 时钟: F_osc / 32 = 1 MHz → T_AD = 1 µs → 满足 1.6 µs 最小值? ⚠️
  修正: 应使用 F_osc / 16 = 2 MHz → T_AD = 0.5 µs ❌ 低于最小值!
  修正: 使用 F_osc / 64 = 500 kHz → T_AD = 2 µs ✓ (满足 ≥ 1.6 µs)
  代码修正: ADCON1 = 0b11000000 (FOSC/64)
```

---

## 4. Sheet 3/6: SWR_BRIDGE — SWR检测桥

### 4.1 电路描述

基于 John Grebenkemper, KI6WX 的 Tandem Match 定向耦合器设计 (QST Jan 1987)。RF 主线穿过两个 FT37-43 磁环的中心。磁环次级各绕 10T 漆包线, 分别耦合正向和反向行波。BAT41 肖特基二极管检波后, 经 10nF 电容滤波, 产生的直流电压正比于 √P_fwd 和 √P_rev。

### 4.2 完整 Netlist

| Net Name | 连接点 | 预期信号 |
|----------|--------|---------|
| `RF_50OHM_IN` | C_block 冷端 → T2 磁环中心穿过 → T3 磁环中心穿过 → T200-2 初级热端 | 50Ω RF, ≤ 100W |
| `T2_SEC_A` | FT37-43(FWD) 次级一端 | 耦合 RF 信号, 比例于 √P_fwd |
| `T2_SEC_B` | FT37-43(FWD) 次级另一端 → R_fwd_term(50Ω) | 50Ω 终端 |
| `V_FWD_RF` | FT37-43(FWD) 次级热端 → BAT41(D2, 阳极) | RF 检波输入 |
| `V_FWD_DC` | BAT41(D2, 阴极) → R_fwd_load(1MΩ)→GND; C_fwd_filt(10nF)→GND → MCU AN0 | DC 0-3V, 比例于 √P_fwd |
| `T3_SEC_A` | FT37-43(REV) 次级一端 (反向连接) | 耦合 RF 信号, 比例于 √P_rev |
| `T3_SEC_B` | FT37-43(REV) 次级另一端 → R_rev_term(50Ω) | 50Ω 终端 |
| `V_REV_RF` | FT37-43(REV) 次级热端 → BAT41(D3, 阳极) | RF 检波输入 |
| `V_REV_DC` | BAT41(D3, 阴极) → R_rev_load(1MΩ)→GND; C_rev_filt(10nF)→GND → MCU AN1 | DC 0-3V, 比例于 √P_rev |
| `SWR_GND` | 所有检波器地对 A区数字地 (单点连接) | 0V |

### 4.3 元件清单

| 位号 | 元件 | 型号/值 | 封装 | 功能 |
|------|------|---------|------|------|
| T2 | 磁环 (FWD) | FT37-43, 主线穿心 + 10T 次级 | 磁环 | 正向耦合器 |
| T3 | 磁环 (REV) | FT37-43, 主线穿心 + 10T 次级 (反向) | 磁环 | 反向耦合器 |
| D2, D3 | 检波二极管 | BAT41 (Vf 配对 < 5mV) | SOD-123 | RF 检波 |
| R_fwd_term | 终端电阻 | 50Ω (4×200Ω 1% 并联) | 0805 ×4 | FWD 端口匹配 |
| R_rev_term | 终端电阻 | 50Ω (4×200Ω 1% 并联) | 0805 ×4 | REV 端口匹配 |
| R_fwd_load, R_rev_load | 检波负载 | 1MΩ / 1% | 0805 | 肖特基检波负载 (高阻) |
| C_fwd_filt, C_rev_filt | 滤波电容 | 10nF / 50V / NPO | 0805 | 检波输出滤波 |
| R_trim_fwd, R_trim_rev | 平衡校准 | 10kΩ / 3296W 多圈可调 | 3296W 顶调 | FWD/REV 增益平衡 |

### 4.4 耦合器关键参数

```
耦合度 (Coupling):      ~25-30 dB @ 1.8-30 MHz
方向性 (Directivity):    >25 dB @ 1.8-30 MHz (50Ω load)
插入损耗 (Insertion):    <0.15 dB @ 30 MHz
主线阻抗:                50 Ω
频率响应平坦度:           ±2 dB (1.8-30 MHz)
```

---

## 5. Sheet 4/6: RELAY_DRIVE — 继电器驱动

### 5.1 电路描述

ULN2003A 7 路达林顿阵列将 MCU 5V GPIO 信号转换为 12V 继电器线圈驱动。COM 脚 (Pin9) 接 VCC_12V 以为内置续流二极管提供回路。7 路输出通过 PCB 物理开槽上的 7 根控制线进入 B 区高压域。

### 5.2 完整 Netlist

| Net Name | 连接点 | 驱动逻辑 |
|----------|--------|---------|
| `IN1` – `IN7` | MCU RB0-RB6 → ULN2003A Pin1-7 | Hi(5V)=继电器吸合, Lo(0V)=释放 |
| `OUT1` – `OUT7` | ULN2003A Pin10-16 → K1-K7 线圈(-端) | Lo(~0.9V)=吸合, Hi-Z=释放 |
| `VCC_12V` | ULN2003A Pin9(COM) + K1-K7 线圈(+端) | 12V 常供电 |
| `PGND` | ULN2003A Pin8 → A区功率地 | — |
| `COIL_1` – `COIL_7` | K1-K7 线圈(-端) → OUT1-OUT7 | 12V 继电器线圈 |

### 5.3 关键布线约束

```
穿越物理开槽的 7 根控制线:
  F.Cu 层, 线宽 0.5mm, 间距 1.5mm
  两侧有 GND 铜箔屏蔽 (共面波导)
  总穿越宽度: 12.5mm (远小于 115mm 槽长)
  穿越区域不设过孔, 保持槽的物理隔离
```

---

## 6. Sheet 5/6: HV_TANK — 高压谐振回路

### 6.1 电路描述

T200-2 ×2 双叠磁芯以 2:13 匝比将 50Ω 输入变换到 ~2,112Ω。次级与 7 位二进制电容阵列构成并联 LC 谐振回路。每只 1812 高压 MLCC 通过对应的 G5Q-14 继电器接入或断开。

### 6.2 T200-2 变压器 Netlist

| Net Name | 连接点 | 信号 |
|----------|--------|------|
| `RF_50OHM_IN` | SWR桥主线出口 → T200-2 初级热端 (2T 始端) | 50Ω RF |
| `PRI_COLD` | T200-2 初级冷端 (2T 末端) → GND_B_HV | 初级地 |
| `SEC_HOT` | T200-2 次级热端 (13T 始端) → HV_BUS (铜轨 5mm 宽) | 高压 RF, ≤ 3KV peak |
| `SEC_COLD` | T200-2 次级冷端 (13T 末端) → GND_B_HV | 次级地 |

### 6.3 电容阵列 Netlist (7位二进制, 128档)

```
电容阵列总拓扑:

  HV_BUS (SEC_HOT)
     │
     ├── K1(NO) ── C1(10pF) ──┐
     ├── K2(NO) ── C2(22pF) ──┤
     ├── K3(NO) ── C3(47pF) ──┤
     ├── K4(NO) ── C4(100pF) ─┼── GND_B_HV
     ├── K5(NO) ── C5(220pF) ─┤
     ├── K6(NO) ── C6a(220pF) ─┤
     │         └── C6b(250pF) ─┤  等效 470pF
     └── K7(NO) ── C7a(470pF) ─┤
               ├── C7b(470pF) ─┤  等效 996pF ≈ 1000pF
               └── C7c(56pF)  ─┘

  所有继电器 COM 脚 → GND_B_HV
  所有继电器 NO 脚 → 各自电容热端
  所有电容冷端 → GND_B_HV (经 ≥3 个过孔)
```

| 位 | 继电器 | MCU Pin | 电容值 (pF) | MLCC 数量 | 等效并联 |
|----|--------|---------|:-----------:|:--------:|---------|
| bit0 (1) | K1 | RB0 | 10 | 1 | — |
| bit1 (2) | K2 | RB1 | 22 | 1 | — |
| bit2 (4) | K3 | RB2 | 47 | 1 | — |
| bit3 (8) | K4 | RB3 | 100 | 1 | — |
| bit4 (16) | K5 | RB4 | 220 | 1 | — |
| bit5 (32) | K6 | RB5 | 470 | **2** | 220pF ‖ 250pF |
| bit6 (64) | K7 | RB6 | 1000 | **3** | 470pF×2 ‖ 56pF |

### 6.4 B区元件清单

| 位号 | 元件 | 型号/值 | 封装 | 功能 |
|------|------|---------|------|------|
| T1 | 磁芯 | T200-2 ×2 双叠, 2T:13T | T200 (OD=50.8mm) | 阻抗变换 + 谐振电感 |
| K1-K7 | 继电器 | G5Q-14 DC12 (或 HF32F-G-12-HS) | TH 20.3×10.3×15.8mm | 电容切换 |
| C1 | 高压电容 | 10pF / 3KV / C0G | 1812 | bit0 |
| C2 | 高压电容 | 22pF / 3KV / C0G | 1812 | bit1 |
| C3 | 高压电容 | 47pF / 3KV / C0G | 1812 | bit2 |
| C4 | 高压电容 | 100pF / 3KV / C0G | 1812 | bit3 |
| C5 | 高压电容 | 220pF / 3KV / C0G | 1812 | bit4 |
| C6a, C6b | 高压电容 | 220+250pF / 3KV / C0G | 1812 ×2 | bit5 (=470pF) |
| C7a, C7b, C7c | 高压电容 | 470+470+56pF / 3KV / C0G | 1812 ×3 | bit6 (=996pF) |

---

## 7. Sheet 6/6: PROTECTION — 保护电路

### 7.1 电路描述

三道防线: (1) 90V 气体放电管在 M 座芯线对地, 拦截同轴电缆感应到的雷电浪涌; (2) 2.2MΩ/3KV 无感电阻在天线端子对地, 泄放天线收集的静电; (3) B区物理开槽阻断 FR4 表面 3KV 高压爬电路径。

### 7.2 Netlist

| Net Name | 连接点 | 功能 |
|----------|--------|------|
| `GDT_ANODE` | J1 芯线 (M座) → GDT1(一端) | 浪涌拦截点 |
| `GDT_CATHODE` | GDT1(另一端) → 铝壳 (GND_CHASSIS) | 浪涌泄放入地 |
| `ANT_STATIC` | J2 (天线端子) → R_bleed(2.2MΩ) → 铝壳 (GND_CHASSIS) | 静电泄放路径 |
| `HV_BUS` | J2 内部引出端 | 天线 RF 输出 |
| `GND_CHASSIS` | J3(地网端子) + J1(外壳) + GDT1(对地) + R_bleed(对地) + 铝壳本身 | 统一机箱地 |

### 7.3 元件清单

| 位号 | 元件 | 型号/值 | 封装 | 功能 |
|------|------|---------|------|------|
| GDT1 | 气体放电管 | 90V DC 击穿, ≥5kA 8/20µs (如 Littelfuse GTCR37-900M-R10) | 径向/贴片 | 雷电浪涌保护 |
| R_bleed | 高压无感电阻 | 2.2MΩ / 2W / 3KV (金属釉膜) | 轴向 | 天线静电泄放 |
| J2 | 天线端子 | M5 × 25mm 304 不锈钢螺栓 + PTFE 绝缘垫片 + 不锈钢螺母/垫圈 | Panel | 天线振子连接 |
| J3 | 地网端子 | M5 × 25mm 304 不锈钢螺栓 + 不锈钢螺母/垫圈 (无需绝缘) | Panel | Counterpoise 连接 |

### 7.4 安全间距验证

```
M座芯线 → GDT → 铝壳接地路径: 最短路径 < 2cm
天线端子 → R_bleed → 铝壳: 直接最短路径
天线端子对铝壳绝缘: PTFE 垫片 (介电强度 > 60 KV/mm)
  1.5mm PTFE 垫片 → 耐压 > 90 KV >> 3 KV ✓
```

---

## 8. 全局互联 (Sheet-to-Sheet)

### 8.1 跨 Sheet 信号

| 信号 | 源 Sheet | 目标 Sheet | 穿越介质 |
|------|---------|-----------|---------|
| `RF_50OHM_IN` | Sheet1 (POWER) | Sheet3 (SWR) → Sheet5 (HV_TANK) | 顶层走线 + 磁环穿心 |
| `VCC_12V` | Sheet1 (POWER) | Sheet4 (RELAY) → Sheet5 (RELAY线圈) | A区走线 + 穿越开槽 |
| `VCC_5V` | Sheet1 (POWER) | Sheet2 (MCU) | A区走线 |
| `DGND` / `PGND` | 全局 | A区全局 | 底层完整地平面 |
| `C_RELAY_1-7` | Sheet2 (MCU) | Sheet4 (RELAY) → Sheet5 (穿越开槽) | 7根 0.5mm 控制线 |
| `SWR_FWD / SWR_REV` | Sheet3 (SWR) | Sheet2 (MCU ADC) | A区顶层走线 |
| `GND_B_HV` | Sheet5 (HV_TANK) | Sheet1 (GND_CHASSIS 单点) | B区地铜排 |
| `HV_BUS` | Sheet5 (HV_TANK) | Sheet6 (PROTECTION) → J2 | B区 5mm 铺铜 |

### 8.2 星形接地方案

```
                     GND_CHASSIS (J1 外壳 / 铝壳)
                          │
               ┌──────────┼──────────┐
               │          │          │
           GND_A_POWER  GND_A_DIGITAL  GND_B_HV
          (电源地平面)  (MCU地平面)   (B区地铜排)
               │          │          │
               └──────────┴──────────┘
                          │
              在 M 座安装点单点连接
              避免 RF 大电流回流污染 MCU
```

---

## 9. 原理图设计规则检查 (ERC)

| # | 规则 | 状态 |
|---|------|:----:|
| 1 | 所有电源轨有去耦电容 | ✓ |
| 2 | IC 电源引脚无误接 | ✓ |
| 3 | 无未连接输入引脚 | ✓ (未用 GPIO 设输出低) |
| 4 | ADC 输入有串联保护电阻 | ✓ (10kΩ) |
| 5 | 继电器线圈有续流二极管 | ✓ (ULN2003A 内置, COM接+12V) |
| 6 | 高压与低压域电气隔离 | ✓ (物理开槽 + 星形接地) |
| 7 | GDT 与天线保护电阻不短路 RF | ✓ (GDT <1.5pF; R=2.2MΩ >> 2kΩ) |
| 8 | LM7812 输入-输出压差 > 2.0V | ⚠️ (见 §2.4, 待修正) |
| 9 | ADC T_AD > 1.6µs | ⚠️ (见 §3.4, FOSC/64) |

---

> **关联文档**: [`auto_efhw_tuner_design_full.md`](../../references/auto_efhw_tuner_design_full.md) §4 (完整 Netlist)
> **PCB 描述**: [`PCB_Description.md`](PCB_Description.md)
> **BOM**: [`EFHW_TUNER_BOM.csv`](EFHW_TUNER_BOM.csv)
