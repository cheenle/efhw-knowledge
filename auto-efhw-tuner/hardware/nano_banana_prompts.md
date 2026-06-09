# Nano Banana PCB 可视化 — 精简 Prompt (📦 V1.0/V2.0 Legacy)

> ⚠️ **2026-06-09**: 本文档为 **V1.0 PIC16F1938 / V2.0 STM32F103** 时代的 AI 图像生成 Prompt (7继电器, 140×90mm, A/B 区隔离)。V3.0 Fuchs ATU PCB 尺寸为 140×**50mm** 单区, 无继电器, 无高压隔离槽。PCB 可视化 Prompt 待更新以反映 V3.0 硬件。

---

---

## PCB 布局图

```
Top-down view of a green 140x90mm 2-layer PCB. A 2.5mm slot cuts horizontally
across the middle at Y=45mm, dividing the board.

UPPER HALF (HV zone):
- Two stacked 50mm-diameter red-brown toroid cores at center, secured by white zip ties
- 7 small black relays (20x10mm each) in a horizontal row, 15mm pitch
- 10 beige 1812 SMD capacitors (4.5x3.2mm) in a row below the relays,
  with C6 and C7 positions having parallel pairs and triplets
- A 5mm-wide copper trace arcs from the toroid to an M5 bolt terminal on right edge
- A blue axial resistor (2.2MΩ, 15mm long) near right edge
- A small ceramic gas discharge tube (8mm diameter) near left edge
- Red silkscreen: "⚠ HV — DO NOT TOUCH"

LOWER HALF (control zone, Y:0-45mm):
- PIC16F1938 SOIC-28 IC at center (X=50, Y=25mm)
- ULN2003A SOIC-16 below it (X=50, Y=15mm)
- LM7812 TO-220 at upper right (X=110, Y=30mm)
- Two 9.5mm black ferrite toroids wound with copper wire at X=70-85, Y=25mm
- Two blue 3296W trim pots nearby
- SO-239 coax connector on left edge
- 5-pin ICSP header at bottom left

7 thin traces (0.5mm, 1.5mm spacing) cross the center slot.

Clean orthographic top-down, pure white background, studio lighting,
no perspective distortion, technical documentation style
```

---

## 功能框图

```
Signal flow diagram, left to right, clean black-on-white schematic style.

[50Ω Radio] → [2x10nF DC-Block] → [SWR Bridge: FT37-43×2 + BAT41] →
[MCU AN0/AN1 ← FWD/REV] → [T200-2×2 2T:13T = 42.25:1 Transformer] →
[7× Relay Binary Capacitor Array: 10pF|22pF|47pF|100pF|220pF|470pF|1000pF] →
[Antenna 2112Ω]

DC power path branches off at input: → [22µH Choke → 1N4007 → LM7812(12V) → 78L05(5V) → MCU]
MCU controls relays: [RB0-RB6] → [ULN2003A] → [7× Relay Coils]

Protection: [90V GDT] at input to ground, [2.2MΩ bleeder] at output to ground.
Bold component labels, single-line arrows, no decorative elements.
```

---

## 系统接线图

```
[Transceiver 100W] —coax— [Bias-T Box: 10nF + 22µH + 13.8V DC] —coax(20m)—
[EFHW Tuner IP66 Box 160x110x70mm] —wire(20m)— [EFHW Radiator]
                                     —wire(2m)— [Counterpoise dropped down]
Ground rod symbol near mast.

Clean minimal line art, bold labels, no shadows, technical manual style.
```
