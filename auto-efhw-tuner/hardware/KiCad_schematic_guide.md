# KiCad 原理图与 PCB 设计指南 (📦 V2.0 Legacy — 已归档)

> ⚠️ **2026-06-09**: 本文档为 **V2.0 STM32F103 Bluepill** 时代的 KiCad 指南，已归档作为历史参考。V3.0 Fuchs ATU 的硬件设计见:
> - [`SCH_Description.md`](SCH_Description.md) — V3.0 原理图 (ESP32-S3 + T200-6 + MG996R)
> - [`PCB_Description.md`](PCB_Description.md) — V3.0 PCB 布局 (140×50mm, 单区地平面)
>
> V3.0 与 V2.0 的硬件根本差异: 无继电器、无 SWR 桥、无高压隔离槽; PCB 仅为控制+电源板; RF 高压路径全部点对点飞线。
>
> ---
>
> # KiCad 原理图与 PCB 设计指南
> # =================================
> # EFHW Auto Tuner 100W — STM32F103 Bluepill
> # 版本: V2.0 (ARCHIVED)
> # =================================

## 一、KiCad 项目设置

### 1.1 创建项目
```
File > New Project > "efhw_auto_tuner_100w"
目录: auto-efhw-tuner/hardware/kicad/
```

### 1.2 原理图设置
- File > Schematic Setup
  - Page size: A3 (420×297mm) — 容纳 A/B 区完整原理图
  - Title: "EFHW Auto Tuner 100W"
  - Rev: V1.0
  - Date: 2026-06-08

### 1.3 PCB 设置
- File > Board Setup
  - Board size: 140mm × 90mm
  - Layers: 2 (F.Cu, B.Cu)
  - Board thickness: 1.6mm
  - Copper thickness: 1oz (35μm), B区高压铺铜区升级到 2oz

## 二、元件符号库

### 2.1 需要自建或查找的元件

| 元件 | KiCad 自带库 | 推荐操作 |
|------|-------------|---------|
| STM32F103C8T6 Bluepill | 自建 (DIP-40 排母 ×2) | STM32模块插入排母, 两侧各20P 2.54mm |
| ULN2003A | Driver_Motor / Transistor_Array | 搜索"ULN2003" |
| T200-2 磁芯 | 无 | 使用电感符号+自定义封装 |
| FT37-43 磁芯 | 无 | 同上 |
| 1812 3KV电容 | Capacitor_SMD:C_1812 | 注意设置耐压属性 |
| G5Q-14 继电器 | Relay_THT | 搜索"G5Q"或自建 |
| 3296W 可调电阻 | Potentiometer_THT | 搜索"3296W" |

### 2.2 T200-2 磁芯符号 (自定义)

在原理图中，T200-2 耦合器作为自定义变压器符号：
- 初级: 一个电感符号，标注"2T"
- 次级: 一个电感符号，标注"13T"，并联电容符号
- 耦合系数 K: 在两电感之间放置"K"符号，值设为"K_T200_2"

### 2.3 FT37-43 SWR桥符号 (自定义)

Tandem Match 定向耦合器：
```
  主线穿过磁芯 (用同轴符号或传输线符号)
  次级: 电感符号，标注"10T"
  检波器: BAT41 + 负载电阻 + 滤波电容
```

## 三、原理图绘制规范

### 3.1 页面分页

```
Sheet 1: 系统总览 (Block Diagram)
Sheet 2: A区 — MCU控制与SWR检测
Sheet 3: A区 — 电源管理 (Bias-T提取 + 稳压)
Sheet 4: B区 — 高压电容阵列
Sheet 5: B区 — T200-2磁芯与天线端子
Sheet 6: 保护电路 (GDT, 静电泄放)
```

### 3.2 关键连接标注

以下连接必须在原理图中明确标注：

1. **ULN2003A COM 脚 (Pin 9) → +12V** — 红色粗线或突出标注"!!DO NOT FLOAT!!"
2. **MCU RC0-RC6 (原电感控制) → 悬空** — 标注"NC / RESERVED"
3. **HV_BUS → 天线端子 J2** — 网络标签"HV_BUS"
4. **B区主地平面 → J3 (地网端子)** — 网络标签"HV_GND"
5. **A区数字地 vs B区高压地** — 两个不同的地符号，通过单一星形接地点连接

### 3.3 地符号区分

```
  GND_A      = A区数字/模拟地 (MCU, SWR检波, 电源)
  GND_B_HV    = B区高压地 (电容冷端、继电器COM)
  GND_CHASSIS = 铝壳/同轴外皮 (通过M座外壳连接)
```

A区地 和 B区地 在 PCB 上通过 M 座同轴外皮做单点连接（星形接地），避免高压大电流回流污染 MCU 的地。

## 四、PCB 布局规范

### 4.1 分层策略

| 层 | A区 (Y: 0-45mm) | B区 (Y: 45-90mm) |
|----|-----------------|-------------------|
| 顶层 (F.Cu) | MCU, ULN2003A, 电源, SWR桥, 信号走线 | 继电器焊盘, 电容阵列焊盘, HV_BUS大面积铺铜, 磁环安装孔 |
| 底层 (B.Cu) | **完整地平面** (GND_A) — 严禁分割 | 高压地铜排 (GND_B_HV), 密集过孔到顶层 |

### 4.2 DRC 规则 (设计规则检查)

在 KiCad PCB Editor 中, Board Setup > Design Rules > Constraints:

```
Net Class: HV_BUS
  Clearance to GND: 5.0mm (200 mil)
  Clearance to other nets: 3.0mm
  Minimum track width: 5.0mm

Net Class: HV_GND
  Clearance to GND_A: 5.0mm (200 mil)
  Minimum track width: 3.0mm

Net Class: Default
  Clearance: 0.25mm (10 mil)
  Minimum track width: 0.25mm

Edge Cuts:
  物理开槽 (Slot): 在 Edge.Cuts 层画矩形
    位置: X=3mm to 118mm, Y=45mm (中心线)
    尺寸: 115mm × 2.5mm
    使用: Place > Add Slot (KiCad V7+) 或在Edge.Cuts层画封闭矩形
```

### 4.3 铜箔填充 (Zone) 设置

1. **A区底层**：添加填充区域 (B.Cu)
   - 网络: GND_A
   - 优先级: 0
   - 热焊盘: 0.5mm spokes
   - 最小宽度: 0.25mm

2. **B区高压地**：添加填充区域
   - 层: F.Cu and B.Cu
   - 网络: GND_B_HV (= GND_CHASSIS)
   - 优先级: 1

3. **HV_BUS 铺铜**：手动使用"添加填充区域"工具
   - 从 T200-2 次级热端焊盘 → 天线端子 J2 焊盘
   - 宽度 ≥ 5.0mm
   - 使用圆弧走向（Place > Arc）

### 4.4 过孔布局

- B区电容冷端 -> 底层地铜排：每个电容至少 3 个过孔（直径 0.6mm/孔 0.3mm）
- HV_BUS 沿路 -> 底层：不需要过孔（保持 HV_BUS 完整性）
- A区 MCU 接地：每个 VSS 引脚至少 2 个过孔到地平面

### 4.5 磁环安装孔

Place > Footprint > MountingHole:MountingHole_4mm
- 位置: B区中央，X≈70mm, Y≈67mm (2个，间距≈30mm)
- 孔径: 4.0mm (尼龙扎带宽 4.8mm 可穿过)
- 周围铜箔清除 (Keepout): 半径 8mm 圆形

## 五、导出制造文件

### 5.1 Gerber 文件
```
File > Fabrication Outputs > Gerbers
  Layers: F.Cu, B.Cu, F.Paste, B.Paste, F.Silkscreen, B.Silkscreen, F.Mask, B.Mask, Edge.Cuts
  Format: 4.6, English, 2:4
  Include Netlist Attributes: Yes
```

### 5.2 钻孔文件
```
File > Fabrication Outputs > Drill Files
  Format: Excellon, PTH and NPTH merged
  Map: Gerber
  Units: Millimeters
```

### 5.3 BOM (CPL) 贴片坐标
```
File > Fabrication Outputs > Component Placement
  Format: ASCII
  Units: Millimeters
  Side: Both
```

### 5.4 发给板厂前的自检清单

- [ ] DRC 运行通过 (0 errors, 0 warnings)
- [ ] 物理开槽在 Edge.Cuts 层可见
- [ ] HV_BUS 对地间距 ≥ 5.0mm 已确认
- [ ] ULN2003A COM 脚网络标签 = +12V
- [ ] B区电容冷端有足够的过孔
- [ ] 所有继电器封装方向正确 (线圈+/NO/COM 与原理图一致)
- [ ] 磁环安装孔不在铜箔上(Keepout 区域足够)
- [ ] M座/天线端子/地网端子的THT焊盘孔径匹配实际螺丝
- [ ] SWD排针方向正确 (Pin1=VCC, Pin2=SWDIO, Pin3=SWCLK, Pin4=GND)
- [ ] Bluepill 排母 Pin1 标记与 PCB 丝印对齐

## 六、KiCad 版本要求

- KiCad V7.0 或更高版本 (支持 Slot 工具和更好的 DRC 规则)
- 推荐 KiCad V8.0+ (UI 改进和更强大的 DRC)
