# EFHW Fuchs ATU V3.0 — PCB 布局描述文档

> **Document ID**: PCB-EFHW-FUCHS-V3.0
> **Schematic Reference**: SCH-EFHW-FUCHS-V3.0
> **Board**: 140mm × 50mm × 1.6mm, 2-layer FR4
> **MCU**: ESP32-S3-WROOM-1 (SMD 模组)

---

## 1. 机械规格

### 1.1 板外形

```
        140.00 mm
   ┌──────────────────────────────────────────┐  ↑
   │  H1(5,5)                      H2(135,5)  │  │
   │  ┌────────────────────────────────────┐  │  │
   │  │  单区设计 — 无A/B分区, 统一地平面  │  │  │
   │  │                                    │  │  │
   │  │  [ESP32-S3]  X=70 Y=20 (中心)     │  │  │
   │  │  [LM2940]    X=15 Y=15            │  │  │
   │  │  [LM2596]    X=20 Y=35            │  │  │50.0mm
   │  │  [AMS1117]   X=115 Y=15           │  │  │
   │  │  [IRF9540]   X=115 Y=35           │  │  │
   │  │  [Servo HDR] X=70 Y=48 (板边)     │  │  │
   │  │  [GDT pads]  X=130 Y=20           │  │  │
   │  │  [LED BZR]   X=5 Y=25             │  │  │
   │  └────────────────────────────────────┘  │  │
   │  H3(5,45)                    H4(135,45)  │  │
   └──────────────────────────────────────────┘  ↓

   板固定孔: Ø3.2mm ×4 (四角)
```

**V2.0→V3.0 关键变化**:
- 板尺寸从 140×90mm 缩小为 140×**50mm** (节省 44% 面积)
- 无 B区/A区 分隔 — 无高压隔离槽 (RF 高压不在 PCB 上)
- 继电器、高压电容、SWR桥全部删除 → PCB 仅为控制+电源板
- T200-6、可变电容、伺服电机均为 **板上安装(chassis mount)**, PCB 仅提供 3-pin 伺服排针

### 1.2 板上元件 vs 板外元件

| 位置 | 器件 |
|------|------|
| **PCB 上** | ESP32-S3, LM2940, LM2596, AMS1117, IRF9540, 2N2222A, 阻容去耦, Bias-V分压, 伺服排针, GDT焊盘, LED, BZR |
| **底板上 (chassis)** | T200-6 磁环, 空气可变电容, MG996R 伺服, SO-239, M5 天线端子, 齿轮组 |

---

## 2. 叠层结构

```
Layer Stack (双面板):
  F.Silkscreen  → 顶层丝印
  F.Mask        → 阻焊 (绿色)
  F.Cu (35µm)   → 信号 + 电源
  FR-4 (1.6mm)  → Er≈4.5
  B.Cu (35µm)   → 完整地平面 (无分割)
  B.Mask        → 阻焊
```

单区统一地平面。无高压隔离需求。

---

## 3. 元件布局坐标

### 3.1 主要 IC

| 位号 | 封装 | X (mm) | Y (mm) | 旋转 | 备注 |
|------|------|:------:|:------:|:----:|------|
| U1 | ESP32-S3-WROOM-1 | 70 | 20 | 0 | 天线区域朝板边 |
| U2 | TO-220 (LM2940) | 15 | 15 | 0 | 12V LDO, 板边散热 |
| U3 | SOT-223 (AMS1117) | 115 | 15 | 0 | 3.3V LDO |
| U4 | LM2596 模块 | 20 | 35 | 0 | 12V→6V DC-DC |

### 3.2 MOSFET 与 BJT

| 位号 | 封装 | X (mm) | Y (mm) | 备注 |
|------|------|:------:|:------:|------|
| Q1 | TO-220 (IRF9540) | 115 | 35 | P-MOSFET, 伺服供电开关 |
| Q2 | TO-92 (2N2222A) | 105 | 38 | 栅极驱动 NPN |
| R_gate | 0805 | 110 | 35 | 10kΩ 栅极下拉 |

### 3.3 连接器与接口

| 位号 | 封装 | X (mm) | Y (mm) | 备注 |
|------|------|:------:|:------:|------|
| HDR_SERVO | 1×3 Pin 2.54mm | 70 | 48 | GND/VCC_SERVO/Signal, 板底边缘 |
| J1 | SO-239 PCB焊盘 | 135 | 10 | 法兰安装到铝壳面板 |
| GDT1 | 径向 | 130 | 20 | 90V GDT |

### 3.4 被动元件

| 位号 | 封装 | X (mm) | Y (mm) | 备注 |
|------|------|:------:|:------:|------|
| D1 | DO-41 (1N4007) | 10 | 18 | 防反 |
| C_block1,2 | 1206 | 125, 128 | 8 | 隔直 |
| R_bias_div1,2 | 0805 | 95, 98 | 15 | 47kΩ+10kΩ |
| C_bias_div | 0805 | 97 | 18 | 100nF |
| LED1 | 3mm TH | 5 | 22 | |
| BZ1 | 有源蜂鸣器 TH | 5 | 30 | |
| C 去耦 ×6 | 0805 | 分散在各 IC 旁 | | 100nF |
| C 电解 ×4 | D6.3-D8mm | 分散在 LDO 旁 | | 47µF/100µF |

---

## 4. 关键布线

### 4.1 伺服电源路径 (高电流)

```
VCC_6V (LM2596 OUT) ── 2.0mm宽走线 ──→ Q1(IRF9540) Source
Q1 Drain ── 2.0mm宽走线 ──→ HDR_SERVO Pin2 (VCC_SERVO)
HDR_SERVO Pin1 → GND (地平面)
Q1 Gate ←── Q2(2N2222A) Collector + R_gate(10kΩ) 到 GND
Q2 Base ←── 1kΩ ←── GPIO2 (SERVO_PWR_CUT)
```

伺服供电轨最大 3A (堵转)。走线宽度 ≥2.0mm (1oz铜 ≈ 3A 容量)。PCB 上 6V 轨加 100µF 电解 + 100nF 陶瓷旁路。

### 4.2 伺服信号

```
GPIO1 ── 0.3mm走线 ── HDR_SERVO Pin3
```

PWM 50Hz 信号，低电流。常规走线即可。

### 4.3 Bias-T 电压监测

```
VCC_12V ── 0.3mm走线 ── R_bias_div1(47kΩ) ──┬── GPIO5
                                              │
                                        R_bias_div2(10kΩ)
                                              │
                                             GND
```

高阻抗分压 (总 57kΩ)，走线远离伺服 PWM 和大电流区域，100nF 电容紧靠 GPIO5。

### 4.4 天线/TRX 接线 (板外飞线)

```
SO-239 芯线 → (飞线) → C_block1/2 PCB焊盘
C_block 冷端 → (飞线) → T200-6 初级2匝热端
T200-6 初级冷端 → (飞线) → SO-239 外壳 (GND)
T200-6 次级热端 → (飞线) → 可变电容定片 → (飞线) → ANT M5 端子
```

---

## 5. DRC 自定义规则 (KiCad)

```json
{
  "rules": {
    "min_track_width": 0.25,
    "min_clearance": 0.25,
    "custom_rules": [
      {
        "name": "servo_power_width",
        "net": "VCC_SERVO",
        "min_width": 2.0
      },
      {
        "name": "servo_power_clearance",
        "net": "VCC_SERVO",
        "against": "GND",
        "min_clearance": 0.5
      },
      {
        "name": "adc_signal_clearance",
        "net": "ADC_BIAS_V",
        "against": "VCC_12V",
        "min_clearance": 1.0
      }
    ]
  }
}
```

---

## 6. 制造说明

| 参数 | 规格 |
|------|------|
| 板材 | FR-4, Tg≥135°C, 1.6mm |
| 铜厚 | 1oz (35µm) |
| 表面处理 | ENIG (推荐) 或 HASL |
| 阻焊 | 绿色 |
| 最小钻孔 | 0.3mm |
| 测试 | 飞针 100% netlist |

### 装配顺序

```
1. 回流焊: ESP32-S3模组, SOT-223 AMS1117, 0805/1206 R/C
2. 手工焊: TO-220 LM2940, TO-220 IRF9540, TO-92 2N2222A ×2
3. 手工焊: DO-41 1N4007, LM2596模块, 电解电容
4. 手工焊: 伺服排针, 接线端子, LED, 蜂鸣器
5. 入壳: 尼龙柱支撑 PCB → M座拧紧
6. 安装板外件: T200-6 尼龙扎带固定 → 可变电容+伺服 螺丝固定 → 齿轮耦合
7. RF 飞线: 按 §4.4 点对点连接 (1.5mm² 铜线)
8. ESP32-S3 通过 USB 烧录初版固件 → WiFi 配置
9. 三防漆喷涂 (仅 PCB 面, 避开连接器和散热器)
```

---

> **关联文档**: [`SCH_Description.md`](SCH_Description.md) · [`EFHW_TUNER_BOM_FUCHS.csv`](EFHW_TUNER_BOM_FUCHS.csv)
> **上一版本**: PCB-EFHW-STM32-V2.0 (已存档为 legacy 参考)
