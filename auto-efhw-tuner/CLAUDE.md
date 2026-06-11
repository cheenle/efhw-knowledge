# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`auto-efhw-tuner/` is the engineering subproject of the BG1SB EFHW antenna knowledge base (parent repo at `../`). It is a **100W End-Fed Half-Wave antenna tuner (ATU)** — an outdoor, coax-fed (Bias-T), WiFi-remote auto-tuning matchbox. The current design is **V3.0 "Fuchs ATU"**: an ESP32-S3 drives an MG996R servo that continuously turns an air variable capacitor in a Fuchs parallel-LC coupler (T200-6 core, 2:14 turns → 49:1). SWR sensing is **not onboard** — it is delegated entirely to a remote MRRC ATR1000 over a WebSocket link. The ATU is a pure actuator.

Most of the repository is documentation and hardware design. The only buildable software is the ESP32 firmware and a few Python analysis scripts.

## Build & flash (V3.0 ESP32-S3 firmware — the live code)

Requires ESP-IDF v5.x. All commands run from `firmware-esp32/`:

```bash
idf.py set-target esp32s3   # one-time
idf.py build
idf.py flash monitor        # USB-C connected
```

- Project is a standard ESP-IDF CMake project (`firmware-esp32/CMakeLists.txt` → component in `main/CMakeLists.txt`).
- Custom 16MB flash layout in `partitions.csv`; SDK config in `sdkconfig.defaults` (dual OTA, 5s task WDT with panic, size-optimized build).
- `components/cJSON/` is vendored. There is no test harness — verification is bench testing (see `docs/V3_MIGRATION_CHECKLIST.md` and `docs/assembly_test_manual.md`).

## Other buildable artifacts

- **Hardware schematic** (`hardware/schemdraw_schematic.py`): `pip install 'schemdraw>=0.19' && python3 hardware/schemdraw_schematic.py`. The netlist/topology is defined directly in code.
- **Resonance analysis** (`hardware/simulation/lc_resonant_tank_analysis.py`): `python3 lc_resonant_tank_analysis.py`. ngspice is not installed; simulations are analytical (Python + Fourier).
- **Legacy firmware** (`firmware-legacy/`, archived, do not modify unless asked): V1.0 PIC16F1938 (XC8, see `firmware-legacy/pic/Makefile`) and V2.0 STM32F103 (Arduino/libmaple, adapted from profdc9/ModularTuner).

## Firmware architecture (`firmware-esp32/main/`)

`app_main()` in `atu_main.c` initializes hardware (servo, NVS, indicators), registers the task watchdog, then spawns **three FreeRTOS tasks** and runs an LED-heartbeat loop:

| Task | Pri | Module | Role |
|------|-----|--------|------|
| `ws_client` | 3 | `ws_client.c` | WiFi + WebSocket long connection to MRRC; parses incoming JSON commands and dispatches them |
| `tune_engine` | 2 | `tune_engine.c` | Tuning state machine; **event-driven**, not polling |
| `health_mon` | 1 | `health_mon.c` | Periodic Bias-V ADC + core-temp checks, health FSM |

Key data-flow detail: the tuner does not measure SWR locally. The flow is **MRRC → WebSocket → `ws_client` → `tune_engine_feed_swr()` → engine advances one step → emits a JSON event via the callback → `ws_client_send()` → MRRC**. Each servo move waits for the next SWR report before deciding the next position. `tune_engine_set_event_callback()` wires the engine's output back to the WebSocket sender (see `tune_event_handler` in `atu_main.c`).

Module responsibilities:
- `tune_engine.c` — state machine `ATU_IDLE → SWEEPING → FINE_TUNING → LOCKED` (`atu_state_t` in `atu_config.h`). Strategy: NVS cache lookup first, then coarse sweep (37 points @5°), then fine sweep (@1°). Early-exit at SWR ≤ 1.05.
- `servo_ctrl.c` — LEDC PWM at 50Hz (500–2500µs pulse). Powers the servo via a MOSFET enable pin and **cuts power after settling** to avoid jitter/heat.
- `nvs_cache.c` — frequency→servo-position cache in the dedicated `nvs_tune` partition; ±50kHz fuzzy lookup so a band-edge QSY reuses a nearby solution (<1s vs <10s full sweep).
- `protocol.c` — all MRRC↔ATU JSON (cJSON), 6 message types: parse `tune_start`/`swr_update`; build `tune_progress`/`tune_done`/`tune_error`/`status_report`/`health_alert`.
- `health_mon.c` — `SYS_HEALTHY/DEGRADED/SAFE` FSM from Bias voltage and core temperature.

All compile-time constants, GPIO pin map, and shared type/enum definitions live in **`atu_config.h`** — start there to understand parameters (servo timing, tune thresholds, ADC divider, WS URL default `ws://192.168.1.100:8877/atu`).

## Safety-critical behavior to preserve

- **Tuning only at low power.** `tune_engine` requires forward power within `TUNE_POWER_MIN_W`/`TUNE_POWER_MAX_W` (0.5–15W). Tuning the servo/capacitor under 100W RF would arc the air capacitor. Do not loosen these bounds without explicit instruction.
- The RF high-voltage resonant section is intentionally **off-PCB point-to-point wiring** (keeps stray capacitance ~4pF, which is what makes 10m coverage possible). Hardware docs reflect this deliberately.

## Documentation map (read before changing design)

- `docs/SDD.md` — 14-chapter software design spec (also online at ybr387rz.mule.page). Authoritative for architecture/interfaces/state machine/timing.
- `docs/FDE.md` — fault detection boundary, FMEA, what is and isn't detectable.
- `docs/V3_MIGRATION_CHECKLIST.md`, `docs/assembly_test_manual.md` — verification and assembly procedures (the substitute for an automated test suite).
- `hardware/` — `SCH_Description.md`, `PCB_Description.md`, `EFHW_TUNER_BOM_FUCHS.csv`, plus `simulation/`.
- `CHANGELOG.md` — V1.0 PIC → V2.0 STM32 → V3.0 ESP32-S3 evolution and the architectural decision records (AD-001…006).
- `../atu_fuchs_handler.py` — the MRRC-side WebSocket handler this firmware talks to.

## Conventions

- Documentation and design docs are written in Chinese (with English headers/tables); match the surrounding language when editing docs. Code, identifiers, and comments are in English.
- Firmware license GPL-3.0; hardware license CERN-OHL-S 2.0.
