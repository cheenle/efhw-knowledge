# EFHW Auto Tuner 100W — PCB 布局描述文档 (PCB Layout Description)

> **Document ID**: PCB-EFHW-STM32-V2.0
> **Schematic Reference**: SCH-EFHW-STM32-V2.0
> **Board**: 140mm × 90mm × 1.6mm, 2-layer FR4
> **MCU Module**: STM32F103C8T6 Bluepill (DIP-40 排母)
> **Core**: T200-2B ×2 (Carbonyl E Iron Powder, μ=10)

---

## 1. 机械规格

### 1.1 板外形与分区

```
        140.00 mm
   ┌──────────────────────────────────────────────┐  ↑
   │  H1(5,5)                          H2(135,5)  │  │
   │   ┌──────────────────────────────┐           │  │
   │   │    B区: 高压谐振区 (Y:45-90) │           │  │
   │   │  [T200-2B×2] [K1-K7]       │           │  │
   │   │  [C1-C7c] [R_bleed]        │           │  │
   │   │  [HV_BUS 5mm铜轨]          │           │  │
   │   ├────────────────────────────┤ ← Slot    │  │
   │   │  2.5mm × 115mm 透空槽    │   Y=45.0   │90.0mm
   │   │  7根控制线穿越 (0.5mm宽)  │           │  │
   │   ├────────────────────────────┤           │  │
   │   │    A区: 低压控制区 (Y:0-45)│           │  │
   │   │  [Bluepill DIP-40 排母]   │           │  │
   │   │  [ULN2003A] [LM2940]     │           │  │
   │   │  [AMS1117] [SWR桥 FT37]  │           │  │
   │   │  [SWD排针] [BOOT0跳线]   │           │  │
   │   └──────────────────────────────┘           │  │
   │  H3(5,85)                        H4(135,85) │  │
   └──────────────────────────────────────────────┘  ↓

   磁环安装孔: Ø4.0mm ×2 (B区中央 X=55,85 Y=67.5)
   板固定孔:   Ø3.2mm ×4 (四角)
```

## 2. 叠层结构

```
Layer Stack (双面板, 与V1.0相同):
  F.Silkscreen  → 顶层丝印
  F.Mask        → 阻焊 (绿色)
  F.Cu (35µm)   → 信号 + 电源 + HV_BUS
  FR-4 (1.6mm)  → Er≈4.5
  B.Cu (35µm)   → A区完整地平面 + B区地铜排
  B.Mask        → 阻焊
```

## 3. 元件布局坐标 (V2.0 更新)

### 3.1 A区元件 (Y: 0-45mm)

| 位号 | 封装 | X (mm) | Y (mm) | 旋转 | 备注 |
|------|------|:------:|:------:|:----:|------|
| **U1** | **DIP-40 排母 (Bluepill)** | **55** | **25** | **0** | **STM32F103 模块** |
| U2 | SOIC-16 | 55 | 12 | 0 | ULN2003A |
| U3 | TO-220 (LM2940) | 115 | 30 | 0 | 12V LDO |
| U5 | SOT-223 (AMS1117) | 95 | 35 | 0 | 3.3V LDO |
| D_power | DO-41 | 118 | 22 | 90 | 1N4007 |
| T2, T3 | FT37-43 磁环 | 75, 90 | 28 | 0 | SWR 桥 |
| D2, D3 | SOD-123 | 73, 88 | 20 | 0 | BAT41 配对 |
| R_trim_fwd, R_trim_rev | 3296W | 65, 83 | 8 | 0 | 10kΩ 多圈 |
| R_fwd_div, R_rev_div | 0805 ×4 | 70-76, 85-91 | 16 | 0 | 10kΩ 分压 (3.3V) |
| HDR_SWD | 1×4 Pin 2.54mm | 10 | 40 | 90 | ST-Link 调试 |
| BOOT0 | 1×2 Pin 2.54mm | 10 | 35 | 0 | BOOT0 跳线 |
| L_bias | CD75/FT37-43 | 15 | 25 | 0 | 扼流圈 |
| C_block1,2 | 1206 | 25, 30 | 32 | 0 | 隔直电容 |

### 3.2 B区元件 (Y: 45-90mm) — 与 V1.0 相同

| 位号 | 封装 | X | Y | 备注 |
|------|------|:--:|:--:|------|
| T1 | T200-2B ×2 双叠 | 70 | 67.5 | 尼龙扎带固定 |
| K1-K7 | G5Q-14 继电器 | 15-105 | 60 | 7只, 间距15mm |
| C1-C7c | 1812 MLCC ×10 | 15-115 | 75 | 10只, C6/C7 并联 |
| R_bleed | 轴向 2.2MΩ/3KV | 125 | 80 | 静电泄放 |
| GDT1 | 90V 气体放电管 | 115 | 52 | 浪涌保护 |

---

## 4. 关键布线变更 (V2.0)

### 4.1 STM32 到 ULN2003A (7路控制)

```
STM32 PA8  ──────────── ULN2003A IN1 ── K1 (10pF)
STM32 PA9  ──────────── ULN2003A IN2 ── K2 (22pF)
STM32 PA10 ──────────── ULN2003A IN3 ── K3 (47pF)
STM32 PA11 ──────────── ULN2003A IN4 ── K4 (100pF)
STM32 PA12 ──────────── ULN2003A IN5 ── K5 (220pF)
STM32 PB3  ──────────── ULN2003A IN6 ── K6 (470pF)   ← 禁用JTAG后释放
STM32 PB4  ──────────── ULN2003A IN7 ── K7 (1000pF)  ← 禁用JTAG后释放

ULN2003A COM (Pin9) → VCC_12V ← ⚠️ 必须连接!
```

### 4.2 3.3V ADC 分压网络 (新增)

```
BAT41(FWD) 阴极 ──┬── R_fwd_div1(10kΩ) ──┬── STM32 PA0
                   │                      │
                   └── R_fwd_div2(10kΩ) ──┴── GND
                                      │
                                   100nF → GND  (滤波)

BAT41(REV) 阴极 ──┬── R_rev_div1(10kΩ) ──┬── STM32 PA1
                   │                      │
                   └── R_rev_div2(10kΩ) ──┴── GND
                                      │
                                   100nF → GND
```

### 4.3 Bias-T 电压监测分压

```
VCC_12V ──── R_bias_div1(47kΩ) ──┬── STM32 PA4
                                  │
                            R_bias_div2(10kΩ)
                                  │
                                 GND

分压比: 10kΩ / (47kΩ+10kΩ) = 0.175
12V × 0.175 = 2.1V → 安全在 3.3V ADC 范围内
```

### 4.4 Bluepill 模块供电

```
VCC_3V3 ──→ Bluepill 5V pin (经板上 3.3V regulator 反向供电, 或)
         ──→ Bluepill 3.3V pin (直接供电 3.3V, 推荐)
GND    ──→ Bluepill GND pin

推荐: 使用 Bluepill 的 3.3V pin 直接供电 (AMS1117 输出),
      板上 USB 口不接 (不需要 USB 供电).
```

---

## 5. 高压隔离验证 (与 V1.0 相同)

| 检查点 | 要求间距 | 设计间距 | 裕度 |
|--------|:------:|:------:|:---:|
| HV_BUS ↔ GND_B_HV (同层) | ≥ 5.0mm | 5.0mm | 1.0× |
| HV_BUS ↔ GND_A (跨层 FR4) | ≥ 0.4mm | 1.6mm | 4.0× |
| 控制线 ↔ B区地 (穿越槽) | ≥ 1.5mm | 1.5mm | 1.0× |
| STM32 ↔ B区 (跨开槽 + 1.6mm FR4 + ULN2003A 隔离) | — | 物理开槽 + 达林顿隔离 | 双重 |

---

## 6. DRC 自定义规则 (KiCad)

```json
{
  "rules": {
    "min_track_width": 0.25,
    "min_clearance": 0.25,
    "custom_rules": [
      {
        "name": "HV_BUS_clearance",
        "net": "HV_BUS",
        "against": "GND_B_HV",
        "min_clearance": 5.0
      },
      {
        "name": "HV_BUS_width",
        "net": "HV_BUS",
        "min_width": 5.0
      },
      {
        "name": "Slot_edge_clearance",
        "edge_cuts_to_copper": 1.25
      },
      {
        "name": "ADC_signal_clearance",
        "nets": ["ADC_FWD", "ADC_REV"],
        "against": "VCC_12V",
        "min_clearance": 1.0
      }
    ]
  }
}
```

---

## 7. 制造说明

| 参数 | 规格 |
|------|------|
| 板材 | FR-4, Tg≥135°C, 1.6mm |
| 铜厚 | 1oz (35µm) |
| 表面处理 | ENIG (推荐, 平坦度好) 或 HASL |
| 阻焊 | 绿色 |
| 最小钻孔 | 0.3mm |
| 槽孔 | 2.5×115mm 铣槽 |
| 测试 | 飞针 100% netlist |

### 装配顺序 (V2.0)

```
1. 回流焊: 0805/1206 R/C, SOD-123, SOIC-16, SOT-223
2. 手工焊: TO-220 LM2940, DO-41 1N4007
3. 手工焊: G5Q-14 ×7, 3296W ×2
4. 手工焊: Bluepill DIP-40 排母 (注意方向!)
5. 手工焊: SWD 排针, BOOT0 跳线
6. 绕制 FT37-43 → 安装; T200-2B 绕线 → 扎带固定
7. Bluepill 插入排母 → ST-Link 连接 → 烧录
8. 三防漆喷涂 B区
9. 入壳: 尼龙柱支撑 → M座拧紧 → 防水接头
```

---

> **关联文档**: [`SCH_Description.md`](SCH_Description.md) · [`EFHW_TUNER_BOM_STM32.csv`](EFHW_TUNER_BOM_STM32.csv) · [`nano_banana_prompts.md`](nano_banana_prompts.md)
