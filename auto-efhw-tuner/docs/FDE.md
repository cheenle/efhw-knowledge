# EFHW Fuchs ATU V3.0 — Fault Detection & Engineering (FDE)

> **Document ID**: FDE-EFHW-FUCHS-V3.0
> **Version**: V3.0
> **Date**: 2026-06-08
> **Status**: Released
> **MCU**: ESP32-S3-WROOM-1

---

## 1. Fault Catalog

| F# | Component | Fault Mode | Detection | Response |
|----|-----------|-----------|-----------|----------|
| F01 | MG996R Servo | Stall (齿轮卡死/堵转) | Position unchanged 3× after set_angle() | Cut power, tune_error (stall), SYS_DEGRADED |
| F02 | MG996R Servo | Stripped gear (空转) | SWR不随位置变化(需MRRC检测) | tune_error (no_match) |
| F03 | IRF9540 P-MOSFET | Short (伺服VCC常通) | 伺服空闲时有动作噪音 | Log alert, 不影响功能 |
| F04 | IRF9540 P-MOSFET | Open (伺服永远断电) | tune_engine detects consecutive stall | tune_error (stall), SYS_DEGRADED |
| F05 | 2N2222A NPN | Open (栅极无法拉低) | MOSFET不导通 → 伺服无电 | tune_error (stall) |
| F06 | T200-6 Core | Saturation (大功率/低频) | 匹配失效, SWR突变 | B_peak校核已排除此风险(47×裕度) |
| F07 | Variable Capacitor | Arc-over (打火/极板短路) | SWR = ∞ (全反射) | GDT保护, 物理恢复后需重启 |
| F08 | LM2596 DC-DC | Overheat/失效 | 6V轨跌落, 伺服无力 | tune_error(stall) |
| F09 | AMS1117-3.3 LDO | 失效 | ESP32-S3 掉电 → WDT reset | Auto reboot |
| F10 | WiFi connection | Disconnect | WIFI_EVENT_STA_DISCONNECTED | Auto reconnect every 10s |
| F11 | WebSocket | Disconnect | WEBSOCKET_EVENT_DISCONNECTED | Auto reconnect every 3s |
| F12 | NVS Partition | Corruption | nvs_flash_init fails | Auto erase + reinit |
| F13 | NVS Write | Flash worn | nvs_set_u8 returns error | Log, continue with RAM cache |
| F14 | Bias-T Voltage | Under-voltage (<10V) | ADC1_CH4 | health_alert → SYS_DEGRADED |
| F15 | Bias-T Voltage | Over-voltage (>15V) | ADC1_CH4 | health_alert → SYS_DEGRADED |
| F16 | Core Temperature | >80°C | Internal temp sensor | health_alert → disable auto-tune |
| F17 | Task WDT | Task hung > 5s | ESP Task WDT panic | Auto reset |
| F18 | cJSON Parse | Malformed JSON | cJSON_Parse returns NULL | Silent discard, no crash |
| F19 | Send Queue | Full (16 pending) | xQueueSend timeout | Drop oldest message |

**V2.0→V3.0 变化**: 删除继电器相关故障(G5Q-14×7, ULN2003A), 删除SWR桥故障(BAT41, FT37-43), 删除ADC卡死故障。新增: 伺服故障(F01-F02), MOSFET故障(F03-F05), WiFi/WS故障(F10-F11), JSON解析故障(F18)。

## 2. Top 5 FMEA

### F01: MG996R Servo Stall (RPN=60)

| Item | Detail |
|------|--------|
| Failure Mode | 齿轮/轴承卡滞, 电机无法转动 |
| Effect | 调谐中断, 无法改变电容 |
| Cause | 低温润滑失效(-20°C), 异物进入, 齿轮磨损 |
| Detection | servo_detect_stall(): 3次 set_angle 后位置不变 |
| Severity/Occurrence/Detection | S:5 (无法调谐), O:3, D:4 |
| RPN | 5×3×4 = 60 |
| Mitigation | 伺服断电 → tune_error(stall) → 定期维护/润滑 |

### F04: IRF9540 Open (RPN=40)

| Item | Detail |
|------|--------|
| Failure Mode | MOSFET 漏极开路, 伺服6V轨断开 |
| Effect | 伺服不通电, 调谐失败 |
| Cause | EOS/ESD, 过流烧毁, 栅极氧化层击穿 |
| Detection | tune_engine 检测到连续stall |
| RPN | 5×2×4 = 40 |
| Mitigation | 选型裕度(IRF9540 -100V/-23A远大于6V/3A); 栅极10kΩ下拉保护 |

### F10: WiFi Disconnect (RPN=36)

| Item | Detail |
|------|--------|
| Failure Mode | WiFi信号丢失 (距离/干扰/路由器重启) |
| Effect | MRRC无法控制ATU; 本地缓存仍可用 |
| Detection | WIFI_EVENT_STA_DISCONNECTED |
| RPN | 4×3×3 = 36 |
| Mitigation | Auto reconnect 10s间隔; LED闪烁指示; 缓存不依赖WiFi |

### F12: NVS Corruption (RPN=28)

| Item | Detail |
|------|--------|
| Failure Mode | NVS partition 数据损坏 (掉电时写入) |
| Effect | 缓存丢失 → 冷启动需全扫描重建 |
| Detection | nvs_flash_init returns error |
| RPN | 4×2×4 = 28 |
| Mitigation | Auto erase + reinit |

### F14: Bias-T Under-voltage (RPN=18)

| Item | Detail |
|------|--------|
| Failure Mode | DC供电<10V (线路损耗/电源故障) |
| Effect | 伺服无力, ESP32可能欠压 |
| Cause | Bias-T电源故障, 同轴过长压降大 |
| RPN | 3×2×3 = 18 |
| Mitigation | health_alert → SYS_DEGRADED → 限制调谐 |

## 3. POST (3-Phase)

| Phase | Check | Method | Failure Action |
|-------|-------|--------|---------------|
| PHASE_0: DC | ESP32-S3 3.3V 供电正常 | 代码能执行 = 供电OK | — |
| PHASE_1: WiFi | WiFi STA initialized | esp_wifi_init check | Retry 3次 → LED fast blink |
| PHASE_2: Servo | 伺服范围测试 | set_angle(90°)→delay→set_angle(0°) | 失败=SYS_DEGRADED |

## 4. Health State Machine

```
  POST PASS ──▶ SYS_HEALTHY
                    │
     servo stall 3次 / bias voltage / core temp >80°C
                    ▼
               SYS_DEGRADED (仍可调谐, 仅告警)
                    │
     连续3次 tune fail / WDT触发
                    ▼
               SYS_SAFE (伺服归零, 禁止自动调谐)
                    │
     ONLY exit: power cycle + POST pass
```

## 5. Degradation Strategies

| Condition | Strategy |
|-----------|----------|
| 1-2次 tune fail | 允许重试, 清除 cooldown |
| 3次 consecutive tune fail | SYS_SAFE → 伺服归零 → 禁止自动调谐 |
| WiFi disconnect | 不影响本地缓存; 仅限制远程命令 |
| NVS cache miss | 全扫描建立新缓存 (~8s) |
| Bias-V out of range | DEGRADED: 仅告警, 不限制 (可能为暂时波动) |
| Core temp >80°C | 禁止自动调谐, wait cooldown, 每30s重检 |

## 6. Fault Injection Test Cases

| Test | Method | Expected |
|------|--------|----------|
| Servo stall | 物理卡住伺服臂, 触发 tune_start | tune_error(stall), MOSFET断电, SYS_DEGRADED |
| WiFi disconnect | 关闭路由器 | LED fast blink, auto reconnect |
| Bias under-voltage | 降低Bias-T电源到9V | health_alert, SYS_DEGRADED |
| NVS corruption | Erase nvs_tune partition mid-write | Auto reformat, cold sweep |
| Malformed JSON | Send invalid JSON to /atu WS | Silent discard, no crash |
| Overpower during tune | fwd_pwr_w=100 | tune_error(overpower), servo to zero |
| RF lost during tune | fwd_pwr_w=0.1 | tune_error(no_rf), servo to zero |
| Send queue full | Flood 32 messages | Queue oldest drop, system stable |

## 7. Diagnostic Data

`get_status` response: `{pos, cache_hits, health, uptime}`

UART0 debug (115200bps): servo position, NVS stats, WiFi RSSI, Bias-V, core temp via esp_log.

## 8. MTBF Estimation

| Component | λ (FIT) | Qty | Total FIT |
|-----------|:-------:|:---:|:---------:|
| ESP32-S3 module | 200 | 1 | 200 |
| MG996R servo | 500 | 1 | 500 |
| IRF9540 MOSFET | 50 | 1 | 50 |
| LM2596 DC-DC | 100 | 1 | 100 |
| LM2940CT LDO | 50 | 1 | 50 |
| AMS1117 LDO | 30 | 1 | 30 |
| 2N2222A NPN | 20 | 2 | 40 |
| T200-6 core | 5 | 1 | 5 |
| Variable capacitor | 300 | 1 | 300 |
| GDT | 10 | 1 | 10 |
| Passives (~25 R/C) | 2 | 25 | 50 |
| Solder joints (~100) | 1 | 100 | 100 |
| **Total** | | | **1,435 FIT** |

MTBF ≈ 1×10^9 / 1435 ≈ **697,000 hours ≈ 80 years** (不含极端环境加速因子)

## 9. Maintenance Schedule

| Interval | Action |
|----------|--------|
| Monthly | 检查 SWR 曲线(MRRC趋势), 确认齿轮无异响 |
| 6-month | 开壳检查: 齿轮磨损、接线松动、GDT 状态、干燥剂 |
| Annual | 抽检 NVS 缓存完整性, 检查防水密封 |
| On fault | MRRC health_alert → 按FMEA指示修复 |

---

> **关联文档**: [`SDD.md`](SDD.md) · [`../hardware/SCH_Description.md`](../hardware/SCH_Description.md)
> **上一版本**: FDE-EFHW-STM32-V2.0 (已存档)
