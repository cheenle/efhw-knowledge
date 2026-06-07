# Nano Banana PCB 可视化 Prompt 集
# ==================================
# 用于 Gemini 2.5/3 Image Generation 生成 EFHW Tuner PCB 示意图
# 建议参数: CFG 7.0–9.0, 30-40 steps

---

## Prompt 1: PCB 板级 Knolling 布局图 (推荐首先生成)

```
Knolling flat lay of a 2-layer amateur radio antenna tuner PCB, dimensions
140mm x 90mm, green solder mask, FR4 board, white silkscreen.

The board is divided into two zones by a 2.5mm wide routing slot across the
horizontal centerline (at Y=45mm).

UPPER HALF (Zone B, Y:45-90mm, HIGH VOLTAGE area):
- 7 identical small black rectangular relays (Omron G5Q-14) arranged in a
  horizontal row near Y=60mm, evenly spaced across 15mm to 105mm X
- Two large red/brown toroidal magnetic cores (T200-2, 50mm outer diameter)
  stacked and secured by white nylon zip ties at center (X=70, Y=67mm)
- 10 beige/brown 1812 SMD ceramic capacitors (C0G/NPO) arranged near Y=75mm,
  some in parallel pairs and triplets
- One thick copper trace (5mm wide) running from the toroid core to a
  stainless steel M5 bolt terminal on the right edge, labeled "HV_BUS"
- A large axial high-voltage resistor (2.2MΩ, blue/gray body) near right edge
- A small gas discharge tube (GDT, cylindrical, ceramic body) near left edge
- Red silkscreen warning text: "HV — DO NOT TOUCH DURING TX"

LOWER HALF (Zone A, Y:0-45mm, LOW VOLTAGE control area):
- One 28-pin SOIC microcontroller chip (PIC16F1938) at center (X=50, Y=25mm)
- One 16-pin SOIC driver chip (ULN2003A) below the MCU
- One TO-220 voltage regulator (LM7812) with small heatsink tab, upper right
- One small TO-92 regulator (78L05) near the TO-220
- Two small black ferrite toroids (FT37-43, 9.5mm diameter) side by side,
  each wound with 10 turns of thin enameled copper wire, near X=70-85mm
- Two blue multi-turn trimmer potentiometers (3296W) near the toroids
- One SO-239 UHF coaxial connector on the left edge
- A 5-pin programming header (ICSP) at bottom left
- All small SMD components (0805/1206 resistors and capacitors) neatly placed

7 thin control traces (0.5mm wide each, spaced 1.5mm apart) cross through
the central routing slot, connecting Zone A to Zone B.

Pure white background, studio lighting, no shadows, no perspective distortion,
evenly spaced layout, top-down orthogonal view, product documentation style,
clean technical presentation
```

---

## Prompt 2: 分层架构示意图 (爆炸视图)

```
Exploded view diagram of an amateur radio antenna tuner PCB showing its
2-layer structure, orthographic projection, pure white background.

Bottom to top layers, separated along Z-axis:

Layer 1 (Bottom, labeled "BOTTOM COPPER"):
- Solid green ground plane covering the entire lower half (Zone A)
- Heavy copper bus bar zone in the upper half (Zone B)
- Dense via stitching (small gold circles, 0.6mm diameter) under each
  capacitor footprint (3 vias per capacitor)

Layer 2 (FR4 Core, labeled "FR-4 1.6mm Er=4.5"):
- Translucent off-white/beige color, 1.6mm thick
- A 2.5mm wide slot cut through the center horizontally

Layer 3 (TOP COPPER, labeled "TOP COPPER 35µm"):
- All components placed as described in Prompt 1
- Thick copper trace (HV_BUS, 5mm wide) with rounded corners (no 90° angles)
  running in the upper zone
- 7 thin parallel traces crossing the center slot

Layer 4 (Top Silkscreen, labeled "TOP SILKSCREEN"):
- White component designators (U1, U2, C1-C7, K1-K7, T1, etc.)
- Red high-voltage warning text in the upper zone
- Board name "EFHW Auto Tuner 100W V1.0" at top edge
- Pin 1 polarity dots on ICs

Connected by vertical dashed gray lines between layers, each layer labeled
with bold black sans-serif text, technical drawing style, clean line art
```

---

## Prompt 3: 功能框图 / 信号流示意图

```
Clean technical block diagram of an EFHW automatic antenna tuner, pure white
background, black and dark gray line art, bold sans-serif labels.

The diagram shows the signal flow from left to right:

LEFT: [Radio 50Ω Input] → coaxial connector symbol (SO-239 labeled "RF IN")

Signal splits into two paths:
  PATH A (RF): → "10nF×2 DC Block" capacitor symbol →
    → rectangular block labeled "SWR Bridge\nTandem Match\n(FT37-43 ×2)"
    → block with two output arrows: "FWD → MCU AN0" and "REV → MCU AN1"
    → "T200-2 ×2\n2T:13T\n42.25:1" transformer symbol (two coupled inductors)
    → thick line labeled "HV_BUS (5mm)" →
    → 7 parallel capacitor symbols arranged in binary weighted ladder
       labeled "10pF 22pF 47pF 100pF 220pF 470pF 1000pF"
    → "Stainless Steel M5\nAntenna Terminal" → RIGHT: [EFHW Wire ~20m]

  PATH B (DC): → "22µH RF Choke\n(Bias-T)" inductor symbol →
    → "1N4007" diode symbol →
    → "LM7812 → 12V" regulator block →
    → branches: "→ 7× Relay Coils" and "→ 78L05 → 5V → MCU"

BELOW the RF path, a control feedback loop:
  [PIC16F1938 MCU] → "RB0-RB6 (7 lines)" → [ULN2003A Driver] →
  → dashed lines up to each of the 7 relays

PROTECTION elements annotated around edges:
  - "90V GDT" gas discharge tube symbol at input
  - "2.2MΩ/3KV" resistor symbol at output to ground
  - Lightning bolt symbol and ground symbol

Thin solid black annotation lines with arrows, no overlap, evenly spaced
components, schematic diagram style, educational illustration quality
```

---

## Prompt 4: 3D 装配效果图

```
Isometric 3D rendering of an IP66 weatherproof aluminum enclosure for outdoor
antenna equipment, dimensions 160x110x70mm, silver/gray die-cast aluminum with
visible cooling fins on top surface.

The enclosure is partially open (lid shown separately above at 45 degree angle),
revealing the internal green PCB mounted on nylon standoffs inside.

Visible on exterior:
- One SO-239 UHF female coaxial connector on the left face, silver/chrome
- Two M5 stainless steel bolts protruding from the right face, one insulated
  with white PTFE washers (antenna terminal), one with plain metal washers
  (ground/counterpoise terminal)
- Three PG cable glands (black plastic, compression type) on the bottom face
- Four corner screws on the lid
- A tiny 1.5mm breather drain hole visible on the very bottom edge

Visible on the interior PCB (green board):
- Two large reddish-brown toroid cores stacked at center
- Seven small black relays in a row
- Multiple beige SMD capacitors
- Black microcontroller IC and driver IC

Studio lighting with soft shadows, 4K photorealistic render, product
documentation quality, clean presentation on light gray background
```

---

## Prompt 5: 电缆接线与系统集成示意图

```
System wiring diagram of an amateur radio station EFHW antenna setup,
pure white background, clean line art, technical illustration style.

LEFT SIDE (Indoor/Shack):
  Box labeled "Transceiver\n100W" with antenna output
  → short coax jumper → 
  Box labeled "Bias-T Injector\n(Indoor Box)" showing:
    - SO-239 input and output
    - Internal components visible: 10nF capacitor, 22µH choke coil
    - DC input jack "13.8V DC IN"
  → long horizontal coaxial cable line running left to right, labeled "RG-58 Coax\n(Carries RF + 12V DC)"

RIGHT SIDE (Outdoor/Mast):
  The coaxial cable enters the bottom of a rectangular box labeled
  "EFHW Auto Tuner 100W\n(IP66 AL Enclosure)"
  
  From the tuner box, two wires emerge on the right:
  - Upper wire: goes up diagonally, labeled "EFHW Wire ~20m\n(Radiator)"
  - Lower wire: hangs straight down, labeled "Counterpoise ~2m\n(0.05λ)"

  A ground symbol below the mast, with a ground rod symbol, labeled
  "Station Ground"

  Small annotations: "90V GDT Lightning Protection", "2.2MΩ Static Bleed"

Minimalist line art, dashed lines for connections, solid boxes for equipment,
bold black sans-serif labels, no decorative elements, pure schematic clarity
```

---

## 使用说明

1. **推荐顺序**: Prompt 1 (PCB布局) → Prompt 3 (功能框图) → Prompt 5 (系统接线)
2. **首次生成**: 先只用 Prompt 1 测试, 根据结果调整细节
3. **如果继电器位置不对**: 补充 "7 relays spaced 15mm apart, first relay at X=15mm"
4. **如果看不清分层**: 加 "each PCB layer differentiated by color: green copper, beige FR4, white silkscreen"
5. **Nano Banana Pro** (gemini-3-pro-image) 比标准版生成的电路图更准确

> **注意**: Nano Banana 是图像生成器，生成的电路图仅供文档/演示/概念验证使用。
> 实际 PCB 设计仍需在 KiCad / 立创 EDA 中完成。
