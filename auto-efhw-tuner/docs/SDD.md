# EFHW Auto Tuner 100W — Software Design Description (SDD)

> **Document ID**: SDD-EFHW-STM32-V2.0
> **Version**: V2.0
> **Date**: 2026-06-08
> **Status**: Released
> **Methodology**: IBM Team Solution Design (TeamSD) v2.3.2
> **MCU**: STM32F103C8T6 (Bluepill, 72MHz Cortex-M3)
> **Firmware Base**: profdc9/ModularTuner (CC-BY-SA 4.0) + BG1SB 适配
> **License**: GPL-3.0 (Firmware) / CERN-OHL-S 2.0 (Hardware)

---

## Document Index

| # | Chapter | ART Code | Key Content |
|---|---------|----------|-------------|
| 1 | Executive Summary | — | 项目概览、性能指标、架构层 |
| 2 | Business Direction | BUS 411 | 用户画像、痛点、差异化 |
| 3 | Project Definition | ENG 343 | 属性、范围、里程碑 |
| 4 | System Context | APP 011 | 上下文图、外部接口、数据流 |
| 5 | Non-Functional Requirements | ART 0507 | 性能/可靠性/安全/环境约束 |
| 6 | Use Case Model | ART 0508 | UC-001 ~ UC-005 |
| 7 | Subject Area Model | APP 408 | 实体、状态机、关系图 |
| 8 | Architecture Decisions | ART 0513 | AD-001 ~ AD-012 |
| 9 | Architecture Overview | ART 0512 | 分层架构、模块分解、依赖图 |
| 10 | Service Model | ART 0582 | 7模块接口契约 |
| 11 | Component Model | ART 0515 | 组件清单、UML图、交互序列 |
| 12 | Operational Model | ART 0522 | 部署拓扑、运行时、故障恢复 |
| 13 | Feasibility Assessment | ART 0530 | 风险、资源、替代方案 |
| 14 | Version History | — | V1.0→V2.0 变更记录 |

---

# 1. Executive Summary

## 1.1 Project Overview

**EFHW Auto Tuner 100W** 是一台室外架设、Bias-T 同轴馈电、全自动调谐的末端馈电半波天线适配器。基于 AA5TB 并联 LC 耦合器理论，以 STM32F103 驱动 7 位 128 档高压电容阵列自动扫描调谐。固件复用 Daniel Marks (KW4TI) 的 ModularTuner 开源代码作为 SWR 检波与频率计数基础。

## 1.2 Key Performance Metrics

| Metric | Target | Achievement |
|--------|--------|-------------|
| 调谐时间 | < 2s (全扫描) | 128 × 12ms = 1.54s (早期退出后典型 0.3-0.8s) |
| SWR 精度 | < 1.2:1 | 128档电容分辨率 ≈ 10-15pF/步 |
| ADC 分辨率 | 12-bit | LSB = 0.81mV (3.3V/4096) |
| MCU 算力 | 72 MHz | ~60 MIPS (Cortex-M3) |
| Flash 用量 | 64KB total | ~20KB (含 ModularTuner 复用 + 本设计新增) |
| RAM 用量 | 20KB total | ~3KB |
| 调谐缓存 | 200 条目 | 全 Flash 持久化 |
| 成本 | — | ~¥390/套 |

## 1.3 Architecture Layers

```
┌──────────────────────────────────────────────────┐
│  Application: efhw_tuner_stm32.ino               │
│  setup()→POST→loop{采样→触发→调谐→诊断}          │
├──────────────────────────────────────────────────┤
│  Service: SWRMeter · FrequencyCounter · FlashStore│
│  (SWRMeter/FreqCounter 复用 ModularTuner)         │
├──────────────────────────────────────────────────┤
│  Domain: CapBank · TuneCache · Post · Diag       │
│  (cap_sweep_tune / 128-step scan / health FSM)   │
├──────────────────────────────────────────────────┤
│  HAL: GPIO · ADC · TIM · USART · Flash (STM32)   │
└──────────────────────────────────────────────────┘
```

## 1.4 Project Status

V2.0 设计完成。STM32F103 固件 10 源文件 (~1,500 行)。SCH/PCB 描述文档更新至 Bluepill 架构。全部文件已提交至 GitHub。

---

# 2. Business Direction (BUS 411)

## 2.1 Target Users & Pain Points

| Persona | Pain Point | Solution |
|---------|-----------|----------|
| FT8 多频段跳频操作者 | 每次换频段需走到室外手动调电容 | 自动扫描 < 1s 锁定 |
| SOTA/POTA 便携操作者 | 宽带 49:1 变压器高频段效率低 | T200-2B 粉末铁芯 HF 全段 Q>150 |
| DX/Contest 爱好者 | 追求极致 TX 效率 | AA5TB 并联谐振 > 90% 效率 |

## 2.2 Competitive Differentiation

| 维度 | 现有方案 | 本设计 |
|------|---------|--------|
| 磁芯 | 43号铁氧体 (μ=850, Q崩塌) | **T200-2B** 羰基铁粉 (μ=10, Q>150@30MHz) |
| 电容 | 低压贴片 (打火烧毁) | **1812/3KV/C0G ×10** (多并联, 无压降) |
| MCU | PIC16 8-bit / ATmega | **STM32F103 32-bit** (72MHz, 12-bit ADC) |
| 供电 | 独立电源线或电池 | **Bias-T 同轴馈电** (一根线搞定) |
| 代码 | 全自写 | **复用 ModularTuner** SWR/频率/Flash 模块 |

---

# 3. Project Definition (ENG 343)

## 3.1 Project Attributes

| Attribute | Value |
|-----------|-------|
| Project Name | EFHW Auto Tuner 100W |
| Project Type | Embedded hardware + firmware system |
| MCU | STM32F103C8T6 (Bluepill, Cortex-M3) |
| Firmware Base | profdc9/ModularTuner (CC-BY-SA 4.0) |
| Core | T200-2B ×2 (Carbonyl E Iron Powder, μ=10) |
| Frequency | 40m–10m (7.0–29.7 MHz) |
| Power | 100W PEP (SSB/CW) |
| License | GPL-3.0 (Firmware) / CERN-OHL-S 2.0 (Hardware) |

## 3.2 Milestones

| M# | Date | Deliverable |
|----|------|-------------|
| M1 | 2026-06-06 | AA5TB 理论验证 + A+C 双模分析 |
| M2 | 2026-06-07 | PIC16 工程设计 (Netlist/PCB/BOM) |
| M3 | 2026-06-08 | PIC16 固件 v1.0 + SDD/FDE v1.0 |
| M4 | 2026-06-08 | **STM32 架构迁移** (ModularTuner 复用 + 裁剪) |
| M5 | 2026-06-08 | **硬件文档 V2.0** (SCH/PCB/BOM 全面更新) |
| M6 | TBD | PCB 打样 + Bluepill 台架测试 |
| M7 | TBD | 现场 7×24h FT8 验证 |

---

# 4. System Context (APP 011)

## 4.1 System Diagram

```
[Radio 100W]──coax──[Bias-T Box: 10nF+22µH+13.8V]──coax(20m)──┐
                                                                 │
┌────────────────────────────────────────────────────────────────┼────┐
│  EFHW Auto Tuner (IP66 AL Enclosure)                          │    │
│                                                                │    │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌────────────┐  │    │
│  │ Bias-T   │  │ SWR Meter│  │ STM32F103  │  │ CapBank    │  │    │
│  │ Extract  │  │ Tandem   │  │ Bluepill   │  │ 7×Relay+   │──┼────┤→ Antenna
│  │ LM2940   │  │ Match    │  │ 72MHz      │  │ 10×1812MLCC│  │    │    ~20m
│  │ AMS1117  │  │ FT37-43  │  │ 12-bit ADC │  │ T200-2B×2  │  │    │
│  └──────────┘  └──────────┘  └────────────┘  └────────────┘  │    │
│                                                                │    │
│  Protection: 90V GDT + 2.2MΩ bleeder + 2.5mm slot            │    │
└────────────────────────────────────────────────────────────────┘    │
                                                                      │
                            Counterpoise 2m ──────────────────────────┘
```

## 4.2 External Interfaces

| Interface | Physical | Signal |
|-----------|----------|--------|
| RF IN | SO-239 M座 | 50Ω, 1.8-30MHz, ≤100W + 13.8V DC Bias-T |
| Antenna OUT | M5 304 SS bolt + PTFE | ~2,112Ω, ≤3KV peak |
| Counterpoise | M5 304 SS bolt | GND reference, 2m wire |
| SWD Debug | 4-pin 2.54mm header | ST-Link (PA13/PA14) |

## 4.3 Data Flow

| Flow | Path |
|------|------|
| SWR 采样 | Tandem Match → BAT41 → 10k+10k divider → PA0/PA1 ADC (12-bit) |
| 频率计数 | RF sample → PB9 TIM4_CH4 hardware capture |
| 电容控制 | STM32 GPIO → ULN2003A → G5Q-14 relay coils |
| Bias-V 监测 | VCC_12V → 47k+10k divider → PA4 ADC |
| Flash 持久化 | TuneCache + params → STM32 internal Flash page 0x0801FC00 |

---

# 5. Non-Functional Requirements (ART 0507)

## 5.1 Performance

| ID | Requirement | Target | Implementation |
|----|------------|--------|----------------|
| P01 | 调谐全扫描 | < 2s | 128×12ms relay settle = 1.54s |
| P02 | 调谐重召 | < 0.5s | TuneCache.load() + fine tune ±7 steps |
| P03 | ADC 采样 | 12-bit @ 100Hz | analogRead() + oversampling |
| P04 | 频率测量 | ±1kHz @ HF | TIM4 硬件捕获 (reuse ModularTuner) |
| P05 | POST 完成 | < 2s | 4-phase: DC→ADC→Relay→SWR |

## 5.2 Reliability & Safety

| ID | Requirement | Implementation |
|----|------------|----------------|
| R01 | 禁止大功率调谐 | fwd_power > 15W → abort + bypass |
| R02 | GPIO 回写验证 | CapBank::setValue() 3-retry → mark failed bit |
| R03 | 降级运行 | SYS_DEGRADED: exclude failed relay, continue with N/7 bits |
| R04 | 安全失效 | SYS_SAFE: all relays OFF, lock last-known good C value |
| R05 | 看门狗 | STM32 IWDG (independent watchdog, 2s timeout) |

## 5.3 Environmental

| ID | Requirement | Target |
|----|------------|--------|
| E01 | 工作温度 | -20°C ~ +60°C |
| E02 | 防护 | IP66 (防尘+防强力喷水) |
| E03 | 冷凝处理 | 底部 1.5mm 呼吸孔 + 干燥剂 |

---

# 6. Use Case Model (ART 0508)

### UC-001: Auto-Tune (Full Scan)

```
Actor: HAM Operator (换频段 → 5W CW carrier)
Precondition: Bias-T powered, STM32 HEALTHY, fwd_power ∈ [0.5W, 15W]
Postcondition: CapBank locked at best_c, SWR < 1.2:1

Basic Flow:
1. User switches band → transmits 5W CW
2. loop() detects fwd_power > 0.5W → checks cooldown
3. cap_sweep_tune() called:
   for c = 0..127:
     capBank.setValue(c) → GPIO write + verify (3 retries)
     delay(12ms)         → G5Q-14 mechanical settle
     swrMeter.sampleSWR()
     if fwd_power > 15W → abort + bypass (protect relays)
     if swr < min_swr → update best_c
     if swr < 1.05  → break (early exit)
4. capBank.setValue(best_c) → TuneCache.save(freq, best_c)
5. signalBeep(1) → success
```

### UC-002: Quick Re-Tune

```
Actor: HAM Operator (回到之前调谐过的频段)
Flow:
1. TuneCache.load(freq) → returns saved cap_value
2. capBank.setValue(saved_c) → verify SWR < 2.0
3. If OK: fine-tune ±7 steps around saved_c
4. If stale: fallback to UC-001 full scan
```

### UC-003: POST Self-Test

```
Actor: Power System (上电/复位)
Flow:
1. PHASE 0: checkDC() — read STM32 internal Vrefint (CH17)
2. PHASE 1: Core — code executing = oscillator/Flash OK
3. PHASE 2: checkADC() — 8 consecutive reads, verify non-stuck
4. PHASE 3: checkRelays() — toggle each GPIO briefly
5. PHASE 4: checkSWRBridge() — FWD/REV noise floor > 0
```

### UC-004: Graceful Degradation

```
Actor: DiagMonitor (每 10s 巡检)
Flow:
1. diagMon.runChecks() → ADC stuck? SWR sensor plausible?
2. If 1-2 relays failed → SYS_DEGRADED (CapBank excludes them)
3. If ≥3 failures or consecutive_tune_fails ≥ 3 → SYS_SAFE
4. SAFE → all relays OFF → lock last-known C value → no auto-tune
```

### UC-005: Normal TX (High Power)

```
Actor: HAM Operator (100W SSB/CW after tune complete)
Flow:
1. Tune complete → tuner_state = IDLE, capBank locked
2. User increases power to 100W
3. loop() detects fwd_power > 15W → skips auto-tune trigger
4. Relays remain static (no hot-switching risk)
5. Diag monitoring continues in background
```

---

# 7. Subject Area Model (APP 408)

## 7.1 Domain Entities

| Entity | Attributes | Persistence |
|--------|-----------|-------------|
| **CapBank** | current_value(0-127), failed_mask(7bit) | RAM |
| **TuneCache** | entries[200]{freq_khz, cap_value} | STM32 Flash page |
| **SWRReading** | fwd_pwr, rev_pwr, swr, freq_hz | RAM (last reading) |
| **HealthState** | HEALTHY/DEGRADED/SAFE, fault_log[16] | RAM |
| **TuneResult** | success, best_cap, best_swr, error | Stack (transient) |

## 7.2 Health State Machine

```
  POWER-ON ──POST──▶ HEALTHY (7/7 relays OK)
                          │
          1-2 relays fail │  CRITICAL fault
                          ▼
                      DEGRADED (N/7 relays, still tunes)
                          │
         ≥3 relays fail   │
         or 3× tune fail  │
                          ▼
                      SAFE (all OFF, locked C, no auto-tune)
                          │
              ONLY exit: power cycle + full POST pass
```

---

# 8. Architecture Decisions (ART 0513)

### AD-001: MCU Platform

| Field | Value |
|-------|-------|
| **Decision** | **STM32F103C8T6** (Bluepill) + Arduino/STM32duino framework |
| **Problem** | PIC16F1938 10-bit ADC insufficient for fine SWR measurement; limited RAM (1KB) cannot hold 200-entry cache |
| **Alternatives** | ATmega328P (Arduino, 无12-bit ADC); ESP32 (WiFi功耗高) |
| **Rationale** | 12-bit ADC (4× PIC resolution), 20KB RAM (20×), 64KB Flash (2.3×), 硬件频率计数器, $1.5 Bluepill 极低成本 |
| **Impact** | 可复用 ModularTuner 的 SWRMeter/FrequencyCounter/FlashStore; 3.3V ADC 需分压适配; 放弃 PIC 生态 |

### AD-002: Firmware Reuse Strategy

| Field | Value |
|-------|-------|
| **Decision** | **复用 ModularTuner SWRMeter + FrequencyCounter + flashstruct** |
| **Rationale** | SWRMeter 已实现完整的 Tandem Match 采样/校准/复数阻抗计算; FrequencyCounter 提供硬件定时器捕获测频; Flash 存储提供掉电不丢失的调谐缓存 |
| **Impact** | ~2,000 行成熟代码直接复用; 裁剪 >3,000 行不需要的模块 (LCD/I2C/CAT/无线/多模块) |

### AD-003: CapBank — GPIO 直驱 vs I2C 扩展

| Field | Value |
|-------|-------|
| **Decision** | **STM32 GPIO 直驱** (PA8-PA14 + PB3-PB4), 保持 SWD |
| **Rationale** | ModularTuner 使用 MCP23017 I2C 扩展芯片。本设计仅需 7 路输出 (不是 16+ 路), 且 STM32 有足够 GPIO。删掉 I2C 减少故障点 |
| **Impact** | 需 `afio_cfg_debug_ports(SW_ONLY)` 释放 PB3/PB4; SWD (PA13/PA14) 保留用于调试 |

### AD-004: 3.3V ADC 适配

| Field | Value |
|-------|-------|
| **Decision** | **10kΩ+10kΩ 分压** + 100nF NPO 滤波, 将 SWR 检波输出适配到 STM32 3.3V ADC |
| **Rationale** | BAT41 检波输出在 100W 时可达 4-5V, 超过 STM32 3.3V 最大输入。0.5× 分压保护 ADC, 同时在固件中乘 2 恢复 |
| **Impact** | 4 只额外 0805 电阻; 校准系数需台架重新标定 |

### AD-005: 磁芯 — T200-2B (Type 2 羰基铁粉)

| Field | Value |
|-------|-------|
| **Decision** | **T200-2B ×2 双叠** (Carbonyl E, μ=10) |
| **Rationale** | Mix-2 在 HF 全段 Q>150 (28MHz 仍有 Q>160), 远超铁氧体; B_peak @ 100W/40m = 5.6mT (143× 裕度) |
| **Impact** | 需要 13T 次级 (补偿低 μ); 双叠增大功率容量 |

### AD-006 ~ AD-012

*(供电 Bias-T、电容 1812/3KV/C0G、继电器 G5Q-14、SWR Tandem Match、故障检测 3 级、降级 HEALTHY→SAFE — 与 V1.0 相同, 见原 SDD §8)*

---

# 9. Architecture Overview (ART 0512)

## 9.1 Module Decomposition

```
efhw_tuner_stm32.ino  ← 应用层 (setup/loop/tune/串口)
    │
    ├── tuner_config.h      ← 全部编译时常量
    │
    ├── lib/capbank/        ← 电容阵列域
    │   ├── CapBank         ← 7位 GPIO 直驱 + 回读验证
    │   └── TuneCache       ← 200条频率-电容映射 (RAM + Flash)
    │
    ├── lib/swrmeter/       ← 从 ModularTuner 复用
    │   ├── SWRMeter        ← Tandem Match 检波 (ADC采样/校准/SWR)
    │   ├── Complex         ← 复数运算
    │   └── FrequencyCounter← TIM4 硬件捕获测频
    │
    ├── lib/post/           ← 上电自检
    │   └── PostRunner      ← 4阶段 POST
    │
    └── lib/diag/           ← 运行时诊断
        └── DiagMonitor     ← 故障检测 + 健康状态机
```

## 9.2 Dependency Graph

```
efhw_tuner_stm32.ino
    ├── tuner_config.h  ← 所有模块 include
    ├── CapBank         ← (独立: GPIO only)
    ├── TuneCache       ← (独立: RAM + Flash)
    ├── SWRMeter        ← lib/swrmeter/ (复用 ModularTuner)
    ├── FrequencyCounter← lib/swrmeter/ (复用 ModularTuner)
    ├── PostRunner      ← (依赖: CapBank, SWRMeter)
    └── DiagMonitor     ← (依赖: CapBank)
```

## 9.3 Key Design Patterns

| Pattern | Implementation |
|---------|---------------|
| **State Machine** | tuner_state_t: IDLE → TUNING → LOCKED |
| **Health FSM** | SYS_HEALTHY → DEGRADED → SAFE |
| **Early Exit** | SWR < 1.05 → break during sweep |
| **Write-Verify** | CapBank::setValue(): write GPIO → read IDR → compare → retry×3 |
| **LRU Cache** | TuneCache: hit → move-to-top; miss → evict last |
| **Ring Buffer** | DiagMonitor::fault_log[16] |

---

# 10. Service Model (ART 0582)

### 10.1 CapBank — Capacitor Array Driver

| Operation | Signature | Pre-condition | Post-condition |
|-----------|-----------|--------------|----------------|
| setup | `void setup()` | — | 7 GPIOs configured as PP outputs, all LOW |
| setValue | `bool setValue(uint8_t v)` | v ∈ [0,127] | GPIOs = v & ~failed_mask, read-back verified |
| verifyWrite | `bool verifyWrite(uint8_t v)` | — | Returns true if IDR matches |
| getAvailableBits | `uint8_t getAvailableBits()` | — | Count of relays not in failed_mask |

**Invariant**: After every `setValue()`, `digitalRead(pin) == expected_state` for all non-failed bits.

### 10.2 SWRMeter — SWR Measurement (复用 ModularTuner)

| Operation | Returns | WCET |
|-----------|---------|------|
| `setup()` | — | 200ms |
| `sampleSWR()` | — | 1ms (ADC sampling) |
| `fwdPower()` | float (raw ADC) | <1µs |
| `revPower()` | float (raw ADC) | <1µs |
| `SWR()` | float | <10µs |
| `reflectionCoefficient()` | Complex | <10µs |
| `calculateImpedance()` | Complex | <10µs |

### 10.3 TuneCache — Frequency Memory

| Operation | Pre-condition | WCET |
|-----------|--------------|------|
| `find(freq_hz)` | — | O(n), n≤200 |
| `save(freq_hz, cap_value)` | — | O(n) + Flash write |
| `load(freq_hz, &cap_value)` | freq in cache | O(n) |

**Flash persistence**: TuneCache + params saved to STM32 Flash page 0x0801FC00 via `flashstruct` (复用 ModularTuner).

### 10.4 PostRunner — Power-On Self Test

| Phase | Check | Failure Action |
|-------|-------|---------------|
| DC | Internal Vrefint (CH17) ≈ 1.20V | Halt (critical) |
| ADC | 8× consecutive reads verify non-stuck | DEGRADED |
| Relays | Toggle each GPIO briefly | Mark failed bits |
| SWR Bridge | FWD/REV noise floor > 0 | DEGRADED |

### 10.5 DiagMonitor — Runtime Diagnostics

| Check | Period | Failure Action |
|-------|--------|---------------|
| SWR plausibility | 10s | REV > 2×FWD → DEGRADED |
| ADC stuck | Continuous | 8× same reading → ADC reset → DEGRADED |
| Consecutive tune fails | Per tune | ≥3 → SAFE |

---

# 11. Component Model (ART 0515)

## 11.1 Component Inventory

| Component | Type | Source | Responsibility |
|-----------|------|--------|----------------|
| efhw_tuner_stm32 | Application | BG1SB (ino) | Main loop, tune trigger, serial console |
| CapBank | Domain | BG1SB (cpp) | 7-bit GPIO direct drive, write-verify |
| TuneCache | Domain | BG1SB (cpp) | 200-entry LRU cache, Flash persist |
| SWRMeter | Service | ModularTuner | Tandem Match ADC sampling, SWR calc |
| FrequencyCounter | Service | ModularTuner | TIM4 hardware capture |
| flashstruct | Service | ModularTuner | STM32 internal Flash read/write |
| PostRunner | Service | BG1SB (cpp) | 4-phase POST with Vrefint self-check |
| DiagMonitor | Service | BG1SB (cpp) | Runtime fault detection, health FSM |

## 11.2 Interaction Sequence: Auto-Tune

```
loop()                 CapBank        SWRMeter       TuneCache
  │                       │               │              │
  │ fwd_pwr in [0.5,15]   │               │              │
  │ cap_sweep_tune()      │               │              │
  ├──────────────────────►│               │              │
  │  for c=0..127:        │               │              │
  │    setValue(c)        │               │              │
  │    delay(12ms)        │               │              │
  │    sampleSWR() ───────┼──────────────►│              │
  │    check fwd_pwr      │               │              │
  │    if swr < min → upd │               │              │
  │  setValue(best_c)     │               │              │
  │  save(freq, best_c) ──┼───────────────┼─────────────►│
  │◄──────────────────────┤               │              │
```

---

# 12. Operational Model (ART 0522)

## 12.1 Deployment Topology

```
INDOOR:  [Radio]──[Bias-T Box: C+choke+13.8V]──coax 20m──┐
OUTDOOR:                                                  │
  ┌─ IP66 AL Box 160×110×70mm ───────────────────────────┐│
  │  Bluepill → ULN2003A → 7×G5Q-14 → 10×1812 MLCC      ││
  │  SWRMeter (FT37-43) → 10k+10k divider → STM32 ADC    ││
  │  T200-2B×2 2T:13T → HV_BUS(5mm) → M5 Ant Terminal ──┘│
  │  GDT + 2.2MΩ bleeder + 1.5mm breather hole           │
  └──────────────────────────────────────────────────────┘
                      │
          Counterpoise 2m → free-hanging
```

## 12.2 Runtime Loop

```
loop() @ ~100Hz:
  1. sampleSWR() → read fwd_pwr, rev_pwr, swr
  2. adjustPower(fwd_raw) → if in [0.5, 15]W:
       if cooldown expired & freq_changed > 50kHz:
         cap_sweep_tune() OR TuneCache.load()→fine_tune
  3. Every 10s: diagMon.runChecks()
  4. Serial commands: "status", "tune", "bypass"
```

## 12.3 Failure Recovery

| Event | Recovery |
|-------|----------|
| WDT reset | Boot → POST → load last-known C from Flash |
| Brown-out | BOR reset → same as WDT |
| 1-2 relays stuck | DEGRADED: exclude failed bits, continue tuning |
| ≥3 relays failed | SAFE: all OFF, lock last C, no auto-tune |
| CRITICAL fault | SAFE: immediate all-relays-OFF |

---

# 13. Feasibility Assessment (ART 0530)

## 13.1 Technical Risks

| Risk | Mitigation |
|------|------------|
| 3.3V ADC overvoltage from SWR bridge | 10k+10k divider limits max to 1.65V |
| ModularTuner code compilation on STM32duino | Widely tested; Bluepill is ModularTuner's target platform |
| T200-2B core saturation | B_peak=5.6mT vs B_sat=800mT (143× margin) |
| G5Q-14 hot-switch | Firmware power gate: >15W → bypass, no relay switching |

## 13.2 Resource Budget

| Resource | Budget | Used | Free |
|----------|--------|------|------|
| Flash | 64KB | ~20KB | 69% |
| RAM | 20KB | ~3KB | 85% |
| GPIO | 37 | 16 | 21 |
| ADC channels | 10 | 3 | 7 |
| Cost | ¥400 | ~¥390 | On budget |

---

# 14. Version History

| Version | Date | Changes |
|---------|------|---------|
| V0.1 | 2026-06-07 | Initial engineering design (PIC16F1938) |
| V0.2 | 2026-06-08 | PIC16 firmware v1.0 (8 compile units) |
| V1.0 | 2026-06-08 | IBM TeamSD 14-chapter SDD + Palantir FDE (PIC16) |
| **V2.0** | **2026-06-08** | **Full STM32F103 migration** |
| | | MCU: STM32F103C8T6 Bluepill |
| | | Firmware: ModularTuner reuse (SWR/Freq/Flash) |
| | | New: CapBank GPIO direct-drive |
| | | ADC: 12-bit 3.3V with divider network |
| | | Power: LM2940 LDO + AMS1117-3.3 |
| | | Core: T200-2B ×2 (Carbonyl E, μ=10) |
| | | Memory: 20KB RAM / 64KB Flash / 200-entry cache |
| | | Cost: ~¥390 |

---

> **关联文档**: [`FDE.md`](FDE.md) · [`../hardware/SCH_Description.md`](../hardware/SCH_Description.md) · [`../hardware/PCB_Description.md`](../hardware/PCB_Description.md)
> **固件源码**: [`../firmware-stm32/`](../firmware-stm32/)
