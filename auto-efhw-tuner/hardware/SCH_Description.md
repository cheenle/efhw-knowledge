# EFHW Auto Tuner 100W — 原理图描述文档 (Schematic Description)

> **Document ID**: SCH-EFHW-STM32-V2.0
> **MCU**: STM32F103C8T6 (Bluepill)
> **PCB**: EFHW-100W-PCB-V2.0 (140×90mm, 2-layer FR4)
> **Design Tool**: KiCad V7+
> **Status**: Design Complete

---

## 1. 原理图层次结构

```
Root Sheet: EFHW_Auto_Tuner_STM32

├── Sheet 1/6: POWER (A区 — 电源管理)
│   Bias-T DC提取 → 1N4007防反 → LM7812(12V) → AMS1117-3.3(3.3V)
│
├── Sheet 2/6: MCU (A区 — STM32F103 Bluepill)
│   STM32F103C8T6 + SWD调试口 + BOOT选择 + 去耦
│
├── Sheet 3/6: SWR_BRIDGE (A区 — SWR检测桥)
│   Tandem Match 定向耦合器 (FT37-43 ×2, BAT41 ×2)
│   分压网络适配 3.3V ADC
│
├── Sheet 4/6: RELAY_DRIVE (A→B区 — 继电器驱动)
│   ULN2003A 达林顿阵列 + 7路控制线穿越开槽
│
├── Sheet 5/6: HV_TANK (B区 — 高压谐振回路)
│   T200-2B ×2 磁芯 2:13 + 7位电容阵列(10只1812 3KV C0G) + 7×G5Q-14
│
└── Sheet 6/6: PROTECTION (B区 — 保护电路)
    90V GDT + 2.2MΩ 静电泄放 + 天线/地网端子
```

---

## 2. Sheet 1/6: POWER — 电源管理

### 2.1 电路描述

同轴电缆芯线同时承载 RF 和 13.8V DC。L_bias 扼流圈分离 DC，经 1N4007 防反接后送入 LM7812 稳压到 12V。12V 轨直接驱动 7 路继电器线圈和 ULN2003A。AMS1117-3.3 LDO 将 12V 降压为 3.3V 供 STM32。

### 2.2 完整 Netlist

| Net | 连接点 | 类型 | 预期电压 | 预期电流 |
|-----|--------|------|---------|---------|
| `COAX_CENTER` | J1(SO-239芯线) → C_block(热端) → L_bias(热端) | RF+DC叠加 | 0-100V RF + 13.8V DC | ≤ 2A RF + 0.2A DC |
| `RF_50OHM_IN` | C_block(冷端) → SWR桥主线入口 | 纯RF (隔直后) | 0-100V RF | ≤ 2A RF |
| `DC_RAW` | L_bias(冷端) → D_power(阳极) | 脉动DC | 13.8V (±2V) | ≤ 250mA |
| `DC_12V_PRE` | D_power(阴极) → U3(LM7812, IN) | 整流后DC | 13.3V | ≤ 250mA |
| **`VCC_12V`** | U3(OUT) → 7×继电器线圈(+端) → ULN2003A COM(Pin9) → U5(AMS1117, IN) | 稳压12V | 12.0V ± 0.5V | ≤ 200mA |
| **`VCC_3V3`** | U5(OUT) → STM32 VDD → SWD(Pin1) | 稳压3.3V | 3.30V ± 0.1V | ≤ 50mA |
| `GND_A_POWER` | U3(GND), U5(GND), 去耦电容对地 | A区功率地 | 0V | — |
| `GND_CHASSIS` | J1(外壳) → 铝壳 → J3(地网端子) | 机箱地 | 0V | — |

### 2.3 元件清单

| 位号 | 元件 | 值 | 封装 | 功能 |
|------|------|-----|------|------|
| J1 | SO-239 M座 | 法兰安装 | Panel | RF+DC 输入 |
| C_block1,2 | 隔直电容 | 10nF/1KV/C0G ×2 并联 | 1206 | 隔DC通RF |
| L_bias | RF 扼流圈 | FT37-43 绕 15T (~95µH) | 磁环 TH | 隔RF通DC |
| D_power | 防反二极管 | 1N4007 | DO-41 | 防反接 |
| U3 | 12V 稳压器 | **LM2940CT-12** (LDO, 压差0.5V) | TO-220 | 13.8V→12V |
| U5 | 3.3V 稳压器 | **AMS1117-3.3** (LDO, 压差1.1V) | SOT-223 | 12V→3.3V |
| C_in_12V, C_out_12V | 电解 | 47µF/25V ×2 | D6.3mm | 12V 滤波 |
| C_in_3V3, C_out_3V3 | 钽/陶瓷 | 10µF/16V + 100nF | 0805 | 3.3V 滤波 |
| C_byp_12V, C_byp_3V3 | 高频旁路 | 100nF/50V X7R ×各2 | 0805 | RF 去耦 |

> ⚠️ **LM2940CT-12 替代 LM7812**: 压差仅 0.5V (vs LM7812 的 2.0V), 保证 Bias-T 13.8V 供电时稳定输出 12V。

---

## 3. Sheet 2/6: MCU — STM32F103 Bluepill

### 3.1 电路描述

STM32F103C8T6 (Bluepill 开发板) 作为主控。72MHz Cortex-M3, 12-bit ADC, 20KB RAM, 64KB Flash。7 路 GPIO 控制电容阵列。SWD 接口用于调试/烧录。频率计数器使用 TIM4_CH4 (PB9) 硬件捕获。

### 3.2 引脚分配

| Pin | 功能 | 方向 | 连接 | 备注 |
|-----|------|:----:|------|------|
| PA0 | ADC_FWD | IN | SWR 桥 FWD 检波输出 (经分压) | 12-bit ADC CH0 |
| PA1 | ADC_REV | IN | SWR 桥 REV 检波输出 (经分压) | 12-bit ADC CH1 |
| PA4 | ADC_BIAS_V | IN | Bias-T 12V 分压监测 (5.7:1) | 12-bit ADC CH4 |
| **PA8** | **C_BIT0** | OUT | ULN2003A IN1 → K1 (10pF) | GPIO 推挽 |
| **PA9** | **C_BIT1** | OUT | ULN2003A IN2 → K2 (22pF) | GPIO 推挽 |
| **PA10** | **C_BIT2** | OUT | ULN2003A IN3 → K3 (47pF) | GPIO 推挽 |
| **PA11** | **C_BIT3** | OUT | ULN2003A IN4 → K4 (100pF) | GPIO 推挽 |
| **PA12** | **C_BIT4** | OUT | ULN2003A IN5 → K5 (220pF) | GPIO 推挽 |
| **PB3** | **C_BIT5** | OUT | ULN2003A IN6 → K6 (470pF) | 禁用JTAG后释放 |
| **PB4** | **C_BIT6** | OUT | ULN2003A IN7 → K7 (1000pF) | 禁用JTAG后释放 |
| PB9 | FREQ_IN | IN | 频率计数器输入 (TIM4_CH4) | 硬件捕获 |
| PB12 | BUZZER | OUT | 蜂鸣器 (经 NPN 驱动) | — |
| PB13 | LED | OUT | 状态 LED (经 1kΩ 限流) | — |
| PA13 | SWDIO | I/O | SWD 调试数据线 | 保留调试 |
| PA14 | SWCLK | IN | SWD 调试时钟线 | 保留调试 |
| PA15 | — | — | (JTAG TDI, 禁用后可作 GPIO) | 预留 |

> **关键**: `afio_cfg_debug_ports(AFIO_DEBUG_SW_ONLY)` 禁用 JTAG, 保留 SWD, 释放 PB3/PB4/PA15 为 GPIO。

### 3.3 3.3V ADC 校准参数

| 参数 | PIC16 (5V/10-bit) | STM32 (3.3V/12-bit) |
|------|:-----------------:|:-------------------:|
| 满量程 | 1023 | 4095 |
| LSB | 4.88 mV | 0.81 mV |
| FWD @ 5W (50Ω) 期望 ADC | 512 | ~2050 |
| FWD @ 100W (50Ω) 期望 ADC | ~900 | ~3600 |
| REV @ 完美匹配期望 ADC | <5 | <10 |
| SWR 桥分压比 | 直连 (5V tolerant) | **需分压: 10kΩ+10kΩ** (3.3V 保护) |

> ⚠️ **SWR 桥分压适配**: BAT41 检波输出在 100W 时可达 4-5V, 超出 STM32 3.3V ADC 耐受。需在检波输出端加 10kΩ+10kΩ 分压 (+ 100nF 滤波电容), 将最大电压限制在 <3.0V。

### 3.4 元件清单

| 位号 | 元件 | 值 | 封装 | 功能 |
|------|------|-----|------|------|
| U1 | MCU 模块 | STM32F103C8T6 Bluepill | DIP-40 排母 | 主控 |
| HDR_SWD | SWD 排针 | 1×4 Pin 2.54mm | TH | ST-Link 调试 |
| BOOT0 | 跳线 | 2-pin 2.54mm | TH | BOOT0 选择 |
| C_byp_mcu | 去耦 | 100nF ×2 | 0805 | VDD 去耦 |
| R_fwd_div, R_rev_div | 分压电阻 | 10kΩ ×4 (2+2) | 0805 | 3.3V ADC 保护 |
| C_fwd_div, C_rev_div | 滤波电容 | 100nF NPO | 0805 | 分压点滤波 |
| R_bias_div1, R_bias_div2 | Bias-V 分压 | 47kΩ + 10kΩ | 0805 | 12V→2.1V (5.7:1) |

---

## 4. Sheet 3/6: SWR_BRIDGE — SWR检测桥

*(电路拓扑与 V1.0 相同 — Tandem Match 定向耦合器)*

### 3.3V ADC 适配变更

```
V1.0 (PIC16/5V):                       V2.0 (STM32/3.3V):
                                        
BAT41 阴极 ──────── MCU AN0             BAT41 阴极 ─┬─ 10kΩ ─┬─ MCU PA0
                  (直连)                           │         │
                 │                                  └─ 10kΩ ─┴─ GND
                 │                                           │
              100nF                                        100nF
                 │                                           │
                GND                                         GND
```

分压比: 10kΩ/(10kΩ+10kΩ) = 0.5 → 5V 输入 → 2.5V 输出 (安全在 3.3V 以内)

---

## 5. Sheet 5/6: HV_TANK — 高压谐振回路

### 5.1 磁芯: T200-2B ×2 双叠

| 参数 | 值 |
|------|-----|
| 型号 | T200-2B (Amidon/Micrometals Type 2, 羰基铁粉) |
| 材质 | Carbonyl E Iron Powder, μ=10 |
| 尺寸 | OD=50.8mm, ID=31.8mm, HT=14.0mm |
| AL | 12 nH/N² (单只), ~20 nH/N² (双叠有效) |
| 匝数比 | **2T 初级 : 13T 次级** |
| 阻抗比 | (13/2)² = **42.25:1** |
| 输入 | 50Ω |
| 输出匹配 | 50 × 42.25 ≈ **2,112Ω** |
| B_peak @ 100W/7.1MHz | **5.6 mT** (vs B_sat 800 mT → 143× 裕度) |

### 5.2 电容阵列

*(7位二进制, 128档, 与 V1.0 完全相同)*

| 位 | 权值 | 电容 (pF) | MLCC | 继电器 | STM32 Pin |
|----|:----:|:---------:|:----:|:------:|-----------|
| bit0 | 1 | 10 | 1812 3KV C0G ×1 | K1 | **PA8** |
| bit1 | 2 | 22 | 1812 3KV C0G ×1 | K2 | **PA9** |
| bit2 | 4 | 47 | 1812 3KV C0G ×1 | K3 | **PA10** |
| bit3 | 8 | 100 | 1812 3KV C0G ×1 | K4 | **PA11** |
| bit4 | 16 | 220 | 1812 3KV C0G ×1 | K5 | **PA12** |
| bit5 | 32 | 470 | 1812 3KV C0G ×2 (并联) | K6 | **PB3** |
| bit6 | 64 | 1000 | 1812 3KV C0G ×3 (并联) | K7 | **PB4** |

---

## 6. 全局互联

### 星形接地 (V2.0 更新)

```
          GND_CHASSIS (J1 外壳 / 铝壳)
               │
    ┌──────────┼──────────┐
    │          │          │
GND_A_POWER  GND_A_DIGITAL  GND_B_HV
(12V/3.3V地) (STM32地)     (B区地铜排)
    │          │          │
    └──────────┴──────────┘
               │
    在 M座安装点单点连接 (星形接地)
```

---

> **关联文档**: [`PCB_Description.md`](PCB_Description.md) · [`EFHW_TUNER_BOM_STM32.csv`](EFHW_TUNER_BOM_STM32.csv) · [`../../references/auto_efhw_tuner_design_full.md`](../../references/auto_efhw_tuner_design_full.md)
