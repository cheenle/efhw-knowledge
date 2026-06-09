#!/usr/bin/env python3
"""EFHW Fuchs ATU V3.0 — schemdraw 自动化原理图 (schemdraw ≥0.19)

基于电路拓扑矩阵 (Netlist) 由代码严格定义引脚到引脚的连接。
模块化拓扑: [POWER → MCU → SERVO_SWITCH] + [HV_RF_RESONANT] (空间错位隔离) + [STAR_GROUND]

Usage:
    pip install 'schemdraw>=0.19'
    python3 schemdraw_schematic.py
"""

import schemdraw
import schemdraw.elements as elm

d = schemdraw.Drawing(unit=2.5, fontsize=10)

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 1: POWER & MCU & SERVO SWITCH (低压控制与数字供电)
# ═══════════════════════════════════════════════════════════════════════════════

# -- 1.1 Bias-T DC 输入 → 防反二极管 → LM2940-12V --
d.add(elm.Line(arrow='->').label('DC_RAW\n13.8V', 'left'))
d.add(elm.Diode().label('D1\n1N4007', 'top'))
d.add(elm.Line().length(0.5))

d.add(elm.IcDIP(pins=4, edgepadW=0.6).label('U2\nLM2940-12V', 'center'))
d.push()
d.add(elm.Line().down().length(0.5))
d.add(elm.Ground().label('GND_PCB', 'right'))
d.pop()

d.add(elm.Line().length(0.8))
SAVE_VCC12 = d.here           # ★ save VCC_12V branch point
d.add(elm.Dot().label('VCC_12V', 'top'))

# -- 1.2 ADC voltage divider (R1+R2 → GPIO5) --
d.add(elm.Line().down().length(0.6))
d.add(elm.Resistor().label('R1\n47kΩ', 'right'))
d.add(elm.Dot().label('ADC_BIAS_V\n→GPIO5', 'right'))
d.add(elm.Resistor().label('R2\n10kΩ', 'right'))
d.add(elm.Ground().label('GND_PCB', 'right'))

# -- Return to 12V rail and continue to LM2596 --
d.move_from(SAVE_VCC12, dx=1.8, dy=0)
d.add(elm.Line().length(1.0))
SAVE_12V_LM2596 = d.here

d.add(elm.IcDIP(pins=4, edgepadW=0.6).label('U4\nLM2596-6V\n(Buck)', 'center'))
d.add(elm.Line().length(0.5))
SAVE_6V = d.here
d.add(elm.Dot().label('VCC_6V', 'top'))

# -- 1.3 AMS1117 3.3V LDO branch (from 12V rail, offset upward) --
d.move_from(SAVE_12V_LM2596, dx=0, dy=1.5)
d.add(elm.Line().length(1.5))
d.add(elm.IcDIP(pins=4, edgepadW=0.6).label('U3\nAMS1117-3.3\n(LDO)', 'center'))
d.add(elm.Line().length(0.5))
SAVE_3V3 = d.here
d.add(elm.Dot().label('VCC_3V3', 'top'))

# -- 1.4 ESP32-S3 MCU --
d.move(dx=1.5, dy=-1.0)
d.add(elm.IcDIP(pins=8, edgepadW=0.8).label('U1\nESP32-S3\nWROOM-1', 'center'))
SAVE_MCU_CENTER = d.here

# -- 1.5 Servo Power Switch --
# Path: GPIO2 → R3 → Q2(NPN) → Q1(P-MOSFET) → VCC_SERVO → Servo Header
d.move(dx=2.0, dy=1.0)
d.add(elm.Resistor().label('R3\n1kΩ', 'top'))
d.add(elm.BjtNpn().label('Q2\n2N2222A', 'right'))
d.push()
d.add(elm.Line().down().length(0.3))
d.add(elm.Ground())
d.pop()

d.add(elm.Line().length(0.8))
Q1_START = d.here
d.add(elm.PFet().label('Q1\nIRF9540', 'left'))

# P-MOSFET gate pull-up resistor connection
d.push()
d.move_from(Q1_START, dx=0, dy=0.5)
d.add(elm.Dot())
d.add(elm.Resistor().label('R4\n10kΩ', 'left').length(1.0))
d.pop()

d.add(elm.Line().length(0.3))
d.add(elm.Dot().label('VCC_SERVO', 'top'))

# Servo header
d.add(elm.Line().length(0.5))
SAVE_SERVO_HDR = d.here
d.add(elm.RBox(w=1.2, h=1.8).label('SERVO\nHDR', 'center'))

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 2: HIGH-VOLTAGE RF RESONANT LAYER (高压谐振腔)
# 垂直空间大幅偏移 — 上下层物理完全隔离
# ═══════════════════════════════════════════════════════════════════════════════
d.move(dx=-35.0, dy=-8.0)

# -- 2.1 RF Input + DC-block capacitors --
d.add(elm.Line(arrow='->').label('RF_IN\n(50Ω)', 'left'))
d.add(elm.Capacitor().label('C_block\n10nF 1kV\n×2', 'top'))
d.add(elm.Line().length(0.5))
SAVE_RF_DOT = d.here
d.add(elm.Dot())

# -- 2.2 T200-6 Primary (2T) shunted to GND --
d.add(elm.Inductor2().label('Pri 2T', 'top'))
d.add(elm.Line().down().length(0.5))
d.add(elm.Ground())

# -- 2.3 T200-6 Secondary (14T) + parallel Air Variable Capacitor (Fuchs topology) --
d.move_from(SAVE_RF_DOT, dx=2.0, dy=0)
d.add(elm.Inductor2().label('Sec 14T', 'top'))
SAVE_SEC_BOTTOM = d.here
d.add(elm.Dot())
d.add(elm.Line().down().length(0.3))
d.add(elm.Ground())

# Variable capacitor in parallel with secondary
d.move_from(SAVE_SEC_BOTTOM, dx=1.8, dy=0)
d.add(elm.CapacitorVar().label('Air Var Cap\n10-500pF\n≥1kV', 'top'))
d.add(elm.Line().down().length(0.5))
d.add(elm.Ground())

# -- 2.4 Protection: 2.2MΩ bleeder resistor --
d.add(elm.Line().length(0.8))
d.add(elm.Dot())
d.push()
d.add(elm.Line().down().length(0.8))
d.add(elm.Resistor().label('R_bleed\n2.2MΩ 2W', 'right'))
d.add(elm.Ground().label('GND_CHASSIS', 'right'))
d.pop()

# -- 2.5 Antenna output --
d.add(elm.Line(arrow='->').length(0.8).label('ANTENNA\n~20m Wire', 'right'))

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 3: STAR GROUNDING SYSTEM (星形单点接地)
# ═══════════════════════════════════════════════════════════════════════════════
d.move(dx=-9.0, dy=-3.0)
d.add(elm.Dot(radius=0.2).label('★ STAR GROUND', 'top'))
d.push()
d.add(elm.Line().left().length(1.0).label('GND_PCB', 'left'))
d.pop()
d.push()
d.add(elm.Line().right().length(1.0).label('GND_ANT', 'right'))
d.pop()
d.add(elm.Line().down().length(0.5))
d.add(elm.Ground().label('GND_CHASSIS\n(Al Box)', 'right'))

# ═══════════════════════════════════════════════════════════════════════════════
d.draw()
out_path = '/Users/cheenle/UHRR/MRRC/efhw-knowledge/auto-efhw-tuner/hardware/EFHW_Fuchs_ATU_V3_Schematic.png'
d.save(out_path, dpi=300)
print(f"✅ Schematic saved: {out_path}")
