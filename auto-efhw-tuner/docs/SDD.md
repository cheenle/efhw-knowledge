# EFHW Auto Tuner 100W — Software Design Description (SDD)

> **Document ID**: SDD-EFHW-2026-001
> **Version**: V1.0
> **Date**: 2026-06-08
> **Status**: Released
> **Methodology**: IBM Team Solution Design (TeamSD) v2.3.2
> **Project**: EFHW Auto Tuner 100W — 全自动谐振式 EFHW 调谐适配器
> **License**: GPL-3.0 (Firmware) / CERN-OHL-S 2.0 (Hardware)

---

## Document Index

| # | Chapter | ART Code | Description |
|---|---------|----------|-------------|
| 1 | Executive Summary | - | 项目概览、设计目标、核心功能、架构层 |
| 2 | Business Direction | BUS 411 | 用户画像、痛点分析、价值主张 |
| 3 | Project Definition | ENG 343 | 项目属性、范围、成功标准、里程碑 |
| 4 | System Context | APP 011 | 系统上下文图、外部接口、数据流、边界 |
| 5 | Non-Functional Requirements | ART 0507 | 性能、可靠性、安全、环境约束 |
| 6 | Use Case Model | ART 0508 | 角色定义、核心用例 (UC-001 ~ UC-005) |
| 7 | Subject Area Model | APP 408 | 领域实体、状态模型、关系图 |
| 8 | Architecture Decisions | ART 0513 | AD-001 ~ AD-012 技术决策记录 |
| 9 | Architecture Overview | ART 0512 | 分层架构、模块分解、依赖图 |
| 10 | Service Model | ART 0582 | 服务/模块接口契约 (8 模块) |
| 11 | Component Model | ART 0515 | 组件清单、接口定义、UML 图 |
| 12 | Operational Model | ART 0522 | 部署拓扑、运行时行为、故障恢复 |
| 13 | Feasibility Assessment | ART 0530 | 技术风险、资源评估、替代方案 |
| 14 | Version History | - | 文档版本记录 |

---

# 1. Executive Summary

## 1.1 Project Overview

**EFHW Auto Tuner 100W** 是一台室外架设、同轴 Bias-T 远程馈电、全自动调谐的末端馈电半波天线适配器。它解决了 AA5TB 并联 LC 耦合器需要逐波段手动调谐的核心痛点——将手动可变电容替换为由 PIC16F1938 微控制器驱动的 7 位 128 档二进制高压电容阵列。

**Key Differentiator**: 纯电容调谐 + T200-2 羰基铁粉磁芯 + 自动扫描 = 保留 AA5TB 窄带高效率 (>90%) 的同时消除手动操作，单套成本 ~¥375。

## 1.2 Design Goals

| Goal | Metric | Target |
|------|--------|--------|
| 全自动调谐 | 无需人工干预 | 128档自动扫描, <2s 完成 |
| 高效率匹配 | 谐振点 SWR | < 1.2:1 |
| 室外自主运行 | 连续运行无维护 | ≥ 6 个月 (仅换干燥剂) |
| 射频安全 | 热切换保护 | 功率 >15W 自动中止调谐 |
| 故障自愈 | 降级运行能力 | 单点故障不停机 |
| 成本可控 | 单套 BOM | < ¥400 |

## 1.3 Core Features

| Feature | Description |
|---------|-------------|
| 自动调谐 | PIC16F1938 扫描 7位128档电容阵列, 锁定最低 SWR 点 |
| EEPROM 记忆 | 7 个业余频段各存最佳电容值, 快速召回 |
| Bias-T 供电 | 同轴电缆同时传输 100W RF + 12V DC, 无独立电源线 |
| 安全保护 | 功率检测 (禁止 >15W 调谐) + GPIO 回写验证 + 看门狗 |
| POST 自检 | 4 阶段上电自检 (DC/核心/外设/RF路径) |
| 降级运行 | HEALTHY → DEGRADED → SAFE 三级健康状态机 |
| 故障日志 | EEPROM 环形缓冲 16 条 × 8 字节 |

## 1.4 Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│  Application Layer:  main.c · tuning.c · display.c          │
├──────────────────────────────────────────────────────────────┤
│  Service Layer:     swr_bridge.c · eeprom.c · post.c        │
├──────────────────────────────────────────────────────────────┤
│  HAL Layer:         ADC · GPIO · EEPROM · FVR · WDT        │
├──────────────────────────────────────────────────────────────┤
│  Diagnostics Layer: diagnostics.c (runtime fault detection) │
└──────────────────────────────────────────────────────────────┘
```

## 1.5 Project Status

V1.0 设计完成。全部 10 个固件编译单元 (~6.6 KB Flash, ~230 B RAM)、完整 BOM、KiCad 设计指南、装配测试手册已交付。PCB 待制作，固件待实机验证。

---

# 2. Business Direction (BUS 411)

## 2.1 Target Users

| Persona | Description | Key Pain Point |
|---------|-------------|----------------|
| **FT8 数字模式操作者** | 固定频段长时间自动操作, 40m-10m 多频段跳频 | 每次换频段需走到室外手动调电容 |
| **便携/野外操作者** | SOTA/POTA 激活, 快速架设, 轻量要求 | 49:1 宽带变压器效率低, 尤其是高频段 |
| **DX/Contest 爱好者** | 追求极致 TX 效率, 单频段专注 | 宽带方案牺牲效率换取便利性 |

## 2.2 Problem Statement

AA5TB 并联 LC 耦合器在理论上是 EFHW 匹配的最优解 (粉末铁芯高频损耗极低, >90% 效率)。但它有一个致命缺陷：**每次换频段必须手动调整可变电容**。这导致：

1. FT8 多波段跳频操作不可行 (每 15 秒切换一次频段)
2. 室外永久安装的场景无法调谐 (设备在杆顶/屋顶)
3. 可变电容的机械可靠性有限, 不适合户外长期工作

## 2.3 Value Proposition

将手动 AA5TB 耦合器**自动化**：
- 保留 T200-2 粉末铁芯的高效率优势
- 用 7 只继电器 + 10 只固定高压 MLCC 替代机械可变电容
- 128 档全自动扫描, < 2 秒锁定最佳谐振点
- 成本 ~¥375, 开源设计可 DIY

---

# 3. Project Definition (ENG 343)

## 3.1 Project Attributes

| Attribute | Value |
|-----------|-------|
| Project Name | EFHW Auto Tuner 100W |
| Project Type | Embedded hardware + firmware system |
| Target Users | Amateur radio operators (HAM) |
| Deployment Environment | Outdoor, IP66 sealed, -20°C ~ +60°C |
| Target Platform | PIC16F1938 (8-bit MCU, 32MHz, 28KB Flash) |
| Current Version | V1.0 (Design Complete) |
| License | GPL-3.0 (Firmware) / CERN-OHL-S 2.0 (Hardware) |
| Repository | `auto-efhw-tuner/` (within efhw-knowledge) |

## 3.2 Project Scope

### In Scope
- 7 位 128 档纯电容自动调谐 (40m-10m)
- Tandem Match SWR 检测桥
- Bias-T 同轴馈电 (12V DC)
- 4 阶段 POST 自检 + 运行时故障诊断
- EEPROM 7 频段记忆 + 故障日志
- HEALTHY / DEGRADED / SAFE 三级降级
- 室内 Bias-T 注入盒子设计
- 完整 BOM (¥375/套) + KiCad 设计指南

### Out of Scope
- 80m / 160m 低频段支持 (需更大磁芯)
- 电感调谐功能 (此为纯电容架构)
- 远程数传/蓝牙监控 (V2.0 扩展)
- 500W+ 高功率支持 (V2.0 扩展)
- 成品量产制造 (当前为开源 DIY 级别)

## 3.3 Success Criteria

| ID | Criterion | Measurement |
|----|-----------|-------------|
| SC1 | 调谐后 SWR < 1.2:1 @ 目标频率 | VNA 或电台内置 SWR 表 |
| SC2 | 全扫描调谐时间 < 2s | 示波器/逻辑分析仪计时 |
| SC3 | 100W CW 60s 无打火/异常发热 | 红外测温 + 目视 |
| SC4 | 单继电器失效时仍可调谐 (DEGRADED) | 故障注入测试 |
| SC5 | POST 全部通过时间 < 2s | 上电→就绪计时 |
| SC6 | WDT 复位后 3 秒内恢复安全状态 | 禁用 CLRWDT 测试 |

## 3.4 Major Milestones

| Milestone | Date | Deliverable |
|-----------|------|-------------|
| M1: 理论验证 | 2026-06-06 | AA5TB 理论深度解析, T200-2 B_peak 定量计算 |
| M2: 工程设计 | 2026-06-07 | 完整设计文档, Netlist, PCB 规范, BOM |
| M3: 固件开发 | 2026-06-08 | 10 编译单元, SDD + FDE 文档 |
| M4: PCB 打样 | TBD | 嘉立创 5 片打样 + 贴片 |
| M5: 台架测试 | TBD | 6 项测试全部通过 |
| M6: 现场验证 | TBD | 7×24h FT8 连续运行 |

---

# 4. System Context (APP 011)

## 4.1 Users and System Interaction

```
┌──────────────────────────────────────────────────────────────────────┐
│                            Users                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐          ┌──────────────────┐                 │
│  │  HAM Operator    │          │  System Builder  │                 │
│  │  (FT8/DX/Portable)│          │  (DIY/Kit)       │                 │
│  └────────┬─────────┘          └────────┬─────────┘                 │
│           │                             │                             │
│           │ 切换频段 → 5W 载波          │ 装配 → 校准 → 部署         │
│           │ 观察 SWR 表                 │ 阅读 BOM/PCB 指南          │
│           ▼                             ▼                             │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │                EFHW Auto Tuner System                       │      │
│  │  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │      │
│  │  │ 室内Bias-T │  │ 室外调谐适配器│  │ 天线系统          │   │      │
│  │  │ 注入盒     │──┤ (IP66铝壳)   │──┤ EFHW 导线 ~20m   │   │      │
│  │  │ 13.8V → RF │  │ PIC16F1938   │  │ Counterpoise 2m  │   │      │
│  │  └────────────┘  │ T200-2×2     │  └──────────────────┘   │      │
│  │                   │ 7位电容阵列   │                          │      │
│  │                   │ G5Q-14 ×7    │                          │      │
│  │                   └──────────────┘                          │      │
│  └────────────────────────────────────────────────────────────┘      │
│                              │                                        │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Radio TX    │    │  DC Power    │    │  Lightning   │
│  100W PEP    │    │  13.8V       │    │  Environment │
│  1.8-30 MHz  │    │  Bias-T 注入 │    │  90V GDT     │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 4.2 External System Interfaces

| Interface | Protocol | Physical | Description |
|-----------|----------|----------|-------------|
| RF 输入 | 50Ω 非平衡 | SO-239 (M 座) | 100W PEP, 1.8-30 MHz, Bias-T DC 叠加 |
| 天线输出 | 高压 RF | M5 304 不锈钢螺栓 + PTFE 绝缘 | ~2,112 Ω, 峰值电压 ≤ 3KV |
| 地网端子 | RF 地 | M5 304 不锈钢螺栓 | 2m Counterpoise 导线 |
| ICSP 编程 | Microchip ICSP | 5-pin 2.54mm 排针 | PICkit 3/4, 烧录/调试 |
| DC 供电 | Bias-T 同轴馈电 | 同轴电缆芯线 | 12V DC, ~150mA max |

## 4.3 Data Flow

| Flow | Direction | Description |
|------|-----------|-------------|
| SWR 检测 | Radio → MCU | Tandem Match 定向耦合器 → BAT41 检波 → ADC AN0/AN1 → read_swr_x100() |
| 电容控制 | MCU → 电容阵列 | RB0-RB6 → ULN2003A → G5Q-14 继电器线圈 → 1812 高压 MLCC 接入/断开 |
| EEPROM 记忆 | MCU ↔ EEPROM | Band Table 读写 + Fault Log 环形缓冲 |
| POST 自检 | MCU → 全部外设 | 上电时依次验证 DC/振荡器/ADC/EEPROM/继电器/SWR桥 |
| 故障日志 | diagnostics → EEPROM | 状态迁移时写入 8 字节故障记录 |

## 4.4 System Boundaries

| Boundary | Description |
|----------|-------------|
| 射频边界 | 调谐器输出端 (天线端子) — 之后的天线导线和 Counterpoise 不在设计范围内 |
| 供电边界 | Bias-T 注入盒的输出端 (同轴电缆向室外侧) |
| 控制边界 | PIC16F1938 固件 — 无外部数字通信接口 (V1.0) |
| 物理边界 | IP66 压铸铝盒 — 内部 PCB/元件 vs 外部环境 |
| 频率边界 | 7.0-29.7 MHz (40m-10m) — 80m/160m 超出当前设计范围 |

---

# 5. Non-Functional Requirements (ART 0507)

## 5.1 Performance

| ID | Requirement | Target | Verification |
|----|------------|--------|-------------|
| NFR-P01 | 调谐时间 (全扫描) | < 2.0s | 128 × 13ms = 1.66s (不含早期退出) |
| NFR-P02 | 调谐时间 (记忆重调) | < 0.5s | 14 步微调 × 13ms = 0.18s |
| NFR-P03 | SWR 测量延迟 | < 1ms | 8× 过采样, 双通道 |
| NFR-P04 | POST 完成时间 | < 2.0s | 4 阶段总计 ~850ms |
| NFR-P05 | 主循环周期 | 10ms (±2ms) | __delay_ms(10) 控制 |
| NFR-P06 | ADC 分辨率 | 10-bit (有效 ~11.5-bit 过采样) | N=8 噪声抑制 ~9dB |

## 5.2 Reliability & Availability

| ID | Requirement | Target |
|----|------------|--------|
| NFR-R01 | 平均无故障时间 (MTBF) | > 8,760 小时 (1 年连续运行) |
| NFR-R02 | WDT 复位恢复时间 | < 3s (复位 + POST + 恢复安全状态) |
| NFR-R03 | 继电器电气寿命 | > 100,000 次操作 (G5Q-14 额定) |
| NFR-R04 | EEPROM 数据保持 | > 40 年 (PIC16F1938 额定) |

## 5.3 Safety

| ID | Requirement | Implementation |
|----|------------|---------------|
| NFR-S01 | 禁止热切换 (>15W) | `run_autotune_efhw()` 入口 + 每步循环内功率检测 |
| NFR-S02 | GPIO 写后回读验证 | `set_capacitor_bank()` 3 次重试 |
| NFR-S03 | 高压对地爬电路径阻断 | PCB 2.5mm×115mm 物理开槽 |
| NFR-S04 | 静电泄放 | 2.2MΩ/3KV 无感电阻 (天线端子对地) |
| NFR-S05 | 浪涌保护 | 90V GDT (M 座芯线对地) |

## 5.4 Environmental

| ID | Requirement | Target |
|----|------------|--------|
| NFR-E01 | 工作温度 | -20°C ~ +60°C |
| NFR-E02 | 防护等级 | IP66 (防尘 + 防强力喷水) |
| NFR-E03 | 冷凝处理 | 底部 1.5mm 呼吸孔 + 干燥剂包 |
| NFR-E04 | UV 耐受 | 铝壳 + 不锈钢螺丝 + UV 抗性尼龙扎带 |

## 5.5 Resource Constraints

| ID | Requirement | Budget | Used | Margin |
|----|------------|--------|------|--------|
| NFR-C01 | Flash | 28 KB | ~6.6 KB | 76% free |
| NFR-C02 | RAM | 1,024 B | ~230 B | 78% free |
| NFR-C03 | EEPROM | 256 B | ~56 B (含故障日志 128B) | 22% used |
| NFR-C04 | CPU | 32 MHz | — | Ample for 10ms loop |
| NFR-C05 | Power (调谐器) | — | ~150 mA @ 12V | < 2W total |

---

# 6. Use Case Model (ART 0508)

## 6.1 Actors

| Actor | Description |
|-------|-------------|
| HAM Operator | 业余无线电操作者, 通过电台切换频段并发射低功率载波触发调谐 |
| Power System | 13.8V DC 电源 → Bias-T 注入 → 同轴馈电 → 调谐器 |
| Environment | 温度/湿度/静电/雷电 — 被动影响系统 |

## 6.2 Core Use Cases

### UC-001: 自动调谐 (首次/换频段)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   UC-001: Auto-Tune (Full Scan)                       │
├──────────────────────────────────────────────────────────────────────┤
│ Actor: HAM Operator                                                    │
│ Goal: 在新频段获得最佳 SWR 匹配                                        │
│ Precondition: 同轴已连接, Bias-T 供电正常, 系统 HEALTHY                │
│ Postcondition: 电容阵列锁定在最佳值, SWR < 1.2:1                      │
│                                                                      │
│ Basic Flow:                                                           │
│ 1. 用户切换频段 → 电台设 5W CW 载波                                   │
│ 2. MCU 检测 RF 功率 > 500mW, < 15W                                    │
│ 3. MCU 等待 ~500ms 去抖 → 确认稳定载波                               │
│ 4. MCU 扫描 c_val 0→127: 设电容 → 等12ms → 读SWR → 记录最优          │
│ 5. 早期退出: SWR < 1.05:1 → 停止扫描                                  │
│ 6. 锁定最佳 c_val → EEPROM 存储 → 蜂鸣 1 声 (成功)                    │
│                                                                      │
│ Alternative Flows:                                                     │
│ 2a. 功率 > 15W: 中止 → 蜂鸣 3 声 → 提示降低功率                       │
│ 2b. 功率 < 0.5W: 中止 → 蜂鸣 2 声 → 提示无 RF                         │
│ 4a. 扫描中功率骤升: 立即释放所有继电器 → 蜂鸣 4 声                     │
│ 4b. 全部 128 步 SWR > 3:1: 返回 TUNE_ERROR_SWR_HIGH → 蜂鸣长鸣        │
│ 4c. 系统处于 SAFE 模式: 拒绝调谐 → 蜂鸣 5 声                           │
└──────────────────────────────────────────────────────────────────────┘
```

### UC-002: 快速重调谐 (EEPROM 记忆有效)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   UC-002: Quick Re-Tune                                │
├──────────────────────────────────────────────────────────────────────┤
│ Actor: HAM Operator                                                    │
│ Goal: 在之前调谐过的频段快速恢复匹配                                   │
│ Precondition: EEPROM 中有该频段的有效记忆 (SWR < 2.0)                  │
│ Postcondition: 电容阵列微调到最优, SWR < 1.2:1                         │
│                                                                      │
│ Basic Flow:                                                           │
│ 1. 用户回到之前操作过的频段                                            │
│ 2. MCU 从 EEPROM 加载该频段记忆的 c_val                               │
│ 3. MCU 设电容为记忆值 → 验证 SWR < 2.0                                │
│ 4. 微调 ±7 步 → 锁定最优值 → EEPROM 更新                              │
│                                                                      │
│ Alternative: EEPROM 记忆过期 (SWR > 2.0) → 回退到 UC-001 全扫描       │
└──────────────────────────────────────────────────────────────────────┘
```

### UC-003: 上电自检 (POST)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   UC-003: Power-On Self Test                           │
├──────────────────────────────────────────────────────────────────────┤
│ Actor: Power System (上电/BOR恢复/WDT复位)                             │
│ Goal: 验证系统完整性后才能进入正常运行                                 │
│ Precondition: MCU 完成复位, 振荡器稳定                                  │
│ Postcondition: 系统运行在 HEALTHY / DEGRADED 状态                      │
│                                                                      │
│ Basic Flow:                                                           │
│ 1. PHASE 0 (50ms): 测 VDD 4.5-5.5V → 失败则停机                       │
│ 2. PHASE 1 (100ms): 验证振荡器、PLL 锁定                               │
│ 3. PHASE 2 (200ms): ADC 不卡死、FVR 参考正常、EEPROM Magic 有效        │
│ 4. PHASE 3 (500ms): 逐个继电器吸合-释放、SWR 噪声底非零                │
│ 5. 全部通过 → HEALTHY → 蜂鸣 1 声                                      │
│                                                                      │
│ Alternative: PHASE 3 发现 1-2 个继电器异常 → DEGRADED → 蜂鸣 2 短      │
│ Alternative: PHASE 3 发现 ≥3 异常 → SAFE → 蜂鸣 5 声                   │
│ Alternative: WDT 复位 → 跳过 PHASE 0 → 加载最后已知电容值               │
└──────────────────────────────────────────────────────────────────────┘
```

### UC-004: 故障降级运行

```
┌──────────────────────────────────────────────────────────────────────┐
│                   UC-004: Graceful Degradation                         │
├──────────────────────────────────────────────────────────────────────┤
│ Actor: diagnostics.c (每 10 秒自动巡检)                                │
│ Goal: 单点故障时继续提供部分调谐能力                                   │
│ Precondition: 运行时故障检测发现 1-2 个继电器失效                       │
│ Postcondition: 系统降级到 DEGRADED, 用剩余继电器调谐                   │
│                                                                      │
│ Basic Flow:                                                           │
│ 1. diag_check_all_relays() 发现 bitmask != 0                          │
│ 2. 失效继电器数 < 3 → 迁移 HEALTHY → DEGRADED                         │
│ 3. diag_log_fault() 写入 EEPROM                                        │
│ 4. 后续调谐时排除失效继电器位                                          │
│ 5. LED 慢闪指示 DEGRADED 状态                                         │
│                                                                      │
│ Alternative: ≥3 继电器失效 → 迁移到 SAFE → 所有继电器释放              │
│ Alternative: 连续 3 次调谐失败 → 迁移到 SAFE                            │
│ Alternative: WDT 复位 ≥3 次/小时 → 迁移到 SAFE                          │
└──────────────────────────────────────────────────────────────────────┘
```

### UC-005: 大功率发射 (正常操作)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   UC-005: High Power TX                                │
├──────────────────────────────────────────────────────────────────────┤
│ Actor: HAM Operator                                                    │
│ Goal: 在已调谐状态下以 100W 正常发射                                   │
│ Precondition: 调谐已完成, SWR < 1.2:1                                  │
│ Postcondition: RF 功率高效传输到天线                                   │
│                                                                      │
│ Basic Flow:                                                           │
│ 1. 调谐完成后 MCU 进入 IDLE, 继电器保持锁定状态                        │
│ 2. 用户提升功率到 100W → 发射                                          │
│ 3. MCU 检测到功率 > 15W → 不触发调谐 (保护继电器)                      │
│ 4. 每 10s 后台诊断巡检 (无 RF 时部分检测跳过)                          │
│                                                                      │
│ Safety Note: 正常发射期间不进行任何继电器切换                          │
│              → 完全杜绝大功率下的热切换风险                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

# 7. Subject Area Model (APP 408)

## 7.1 Domain Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **TuneSession** | 一次调谐操作 | c_value(0-127), best_swr_x100, state, frequency |
| **CapacitorBank** | 7 位电容阵列 | bitmask(0x00-0x7F), relay_health[7], total_pF |
| **SweepPoint** | 扫描中的一个电容值 | c_val, swr_x100, timestamp |
| **BandMemory** | EEPROM 中一个频段的记忆 | freq_mhz_x10, best_c_val, best_swr_x100 |
| **FaultRecord** | 一条故障日志 | code, severity, timestamp, data_0/1, checksum |
| **HealthState** | 系统健康状态 | HEALTHY/DEGRADED/SAFE, failed_relay_mask |
| **PostReport** | POST 执行结果 | result_code, failed_phase, degraded_flag |

## 7.2 State Model

```
TuneSession 生命周期:
  TUNE_IDLE ──RF触发──▶ TUNE_CHECK_POWER ──功率OK──▶ TUNE_SCANNING
       ▲                                              │
       │                              ┌────────────────┼────────────────┐
       │                              ▼                ▼                ▼
       │                         TUNE_LOCKED    TUNE_ERROR_OVERPWR  TUNE_ERROR_NORF
       │                              │                                 
       └──────────────────────────────┘  (自动回到 IDLE)

HealthState 迁移:
  HEALTHY ──1-2继电器失效──▶ DEGRADED ──≥3失效──▶ SAFE
      │                          │                    │
      │◀── POST 全部通过 ────────│────────────────────┘ (仅掉电再上电)
      └── CRITICAL 故障 ──────────────────────────▶ SAFE
```

## 7.3 Entity Relationship

```
┌──────────┐       1      * ┌──────────────┐
│TuneSession│──────────────▶│  SweepPoint  │
└────┬─────┘               └──────────────┘
     │ 1
     │ 操作
     ▼ 1
┌──────────────┐    1    7 ┌──────────────┐
│CapacitorBank │──────────▶│   G5Q-14     │
│  (7-bitmask) │           │   Relay ×7   │
└──────┬───────┘           └──────────────┘
       │ 1
       │ 持久化到
       ▼ *
┌──────────────┐         ┌──────────────┐
│ BandMemory   │         │ FaultRecord  │
│ (7 bands)    │         │ (ring 16)    │
└──────────────┘         └──────────────┘
       │                      │
       └──────────┬───────────┘
                  │ 存储在
                  ▼
          ┌──────────────┐
          │   EEPROM     │
          │  (256 bytes) │
          └──────────────┘
```

---

# 8. Architecture Decisions (ART 0513)

### AD-001: MCU Selection

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-001 |
| Topic | 主控 MCU 选型 |
| Decision | **PIC16F1938** (8-bit, 32MHz, 28KB Flash, 10-bit ADC) |

**Problem**: 需要一款与 ATU-100 生态兼容、有足够 I/O 和 ADC、支持 EEPROM、工业温度范围的 MCU。

**Alternatives**:
- A1: ATmega328P — Arduino 生态, 但缺少原生 EEPROM
- A2: STM32F103 — 32-bit ARM, 超出需求, 功耗高
- A3: PIC16F1938 — 与 N7DDC ATU-100 固件兼容, 11ch ADC, 25 GPIO

**Rationale**: PIC16F1938 是 ATU-100 社区的标准选择, 可以直接复用开源固件框架。28KB Flash 仅用 ~24%, 1KB RAM 仅用 ~22%。

**Impact**: 必须使用 XC8 编译器 + PICkit 编程器, 开发环境为 MPLAB X IDE。

---

### AD-002: 纯电容调谐 vs L-C 联合调谐

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-002 |
| Topic | 调谐拓扑选择 |
| Decision | **纯电容调谐** — 电感固定为 T200-2 次级感抗 |

**Problem**: ATU-100 原设计使用 7 个电感 + 7 个电容的 L-C 二维联合调谐。对于 EFHW 谐振匹配器, 是否需要电感调谐？

**Alternatives**:
- A1: 保留 L-C 联合 — 调谐范围更广, 但需要 14 个继电器, PCB 尺寸翻倍
- A2: 纯 C 调谐 — 7 个继电器, 128 档电容, PCB 仅 140×90mm

**Rationale**: T200-2 次级 (13T, 约 2μH) 在 7-30 MHz 范围内提供了足够的电感基底。并联电容阵列 (10-1997pF) 足以覆盖 40m-10m 所有频段的谐振点。额外的电感调谐对 EFHW 场景无显著收益, 且增加一倍硬件复杂度。

**Impact**: 固化电感 → 调谐仅有一个自由度 (电容) → 全扫描 128 步即可穷举所有可能配置 → 算法简单可靠。

---

### AD-003: 磁芯材料选择

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-003 |
| Topic | LC 谐振回路磁芯材料 |
| Decision | **T200-2** 羰基铁粉末铁芯 (μ=10, Carbonyl E) ×2 双叠 |

**Problem**: 100W 功率下，40m 频段最低，磁芯需要承受最高磁通密度。铁氧体 (μ=850) 在 HF 高频段损耗急剧增大。

**Alternatives**:
- A1: FT240-43 铁氧体 (μ=850) — 低频电感大，但 14MHz 以上 Q 值崩塌
- A2: DMEGC Ni-Zn (μ=1000) — 80m 性能好，但高频段不如粉末铁芯
- A3: T200-2 (μ=10) — HF 全段 Q>150, 100W 时 B_peak=5.6mT (距 B_sat 143×)

**Rationale**: 定量计算表明 T200-2 在 40m/100W 时 B_peak 仅 5.6 mT, 距饱和 800 mT 有 143 倍安全裕度。Mix-2 材料在 28 MHz 时 Q 仍 >160, 远超铁氧体。

**Impact**: 需要双叠 (×2) 增大截面积; 需要更多匝数 (13T 次级) 补偿低 μ。

---

### AD-004: 电容选型 — 固定 MLCC 阵列 vs 可变电容

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-004 |
| Topic | 谐振电容实现方式 |
| Decision | **1812/3KV/C0G 固定 MLCC ×10 + G5Q-14 继电器 ×7** |

**Problem**: AA5TB 原设计使用机械可变电容。这增加了自动化的难度, 也引入了户外可靠性的问题。

**Alternatives**:
- A1: 电机驱动真空可变电容 — 无极调谐, 但成本 ¥200-500, 体积大
- A2: 继电器 + 固定高压 MLCC — 二进制权值 128 档, 成本 ~¥37 (电容) + ¥42 (继电器)
- A3: PIN 二极管开关电容 — 无机械部件, 但需要偏置电路, 且 PIN 管在高压下容易击穿

**Rationale**: 7 位二进制电容阵列 (10-1997pF, 1pF 步进) 在 HF 频段提供足够的调谐分辨率 (~20-50 kHz/步)。C0G/NPO 介质零老化、零压电效应, 3KV 额定耐压在高 Q 谐振回路中有安全余量。

**Impact**: 必须使用 C0G/NPO (X7R 在高压下有 -50~-80% 容值衰减); C6/C7 大容量位需多只并联分担 2.6A RMS 谐振环流。

---

### AD-005: 继电器 vs MOSFET 开关

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-005 |
| Topic | 电容切换元件选择 |
| Decision | **欧姆龙 G5Q-14 12VDC** 电磁继电器 |

**Problem**: 谐振回路中切换元件承受高电压和高环流, 且断开时需隔离 3KV。

**Alternatives**:
- A1: MOSFET (如 IRF740) — 速度快, 但关断时寄生电容耦合 RF, 且需要隔离驱动
- A2: 电磁继电器 — 物理断开, 2KV 触点耐压, 成熟可靠
- A3: MEMS 开关 — 理想特性, 但价格极高, 难以采购

**Rationale**: G5Q-14 触点间耐压 2KV AC (1分钟), 线圈-触点耐压 4KV。物理断开提供完美的 RF 隔离。缺点是机械动作时间 ~10ms, 且**不适用于 RF 热切换**。固件中的功率检测 (>15W 中止) 是防止此失效的关键。

**Impact**: 每次切换后需等待 12ms 机械稳定; 调谐期间必须维持低功率 (<15W)。

---

### AD-006: SWR 检测方案

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-006 |
| Topic | SWR/功率检测方案 |
| Decision | **Tandem Match 定向耦合器** (FT37-43 + BAT41) |

**Problem**: 需要准确测量 SWR 来驱动调谐算法。直接性、宽频率范围、低成本之间需要平衡。

**Alternatives**:
- A1: Stockton Bridge — 电路简单, 但高频定向性较差
- A2: 成品双向耦合器 (如 Mini-Circuits) — 性能优秀但 ¥200+
- A3: Tandem Match (KI6WX) — 经典设计, >25dB 定向性, DIY 成本 ~¥10

**Rationale**: Tandem Match 是 ARRL 天线手册推荐的经典设计。FT37-43 磁芯 10T 次级在 1.8-30 MHz 提供足够耦合。BAT41 肖特基管配对选 Vf 差 <5mV 可保证测量精度。

**Impact**: 需要台架校准 (50Ω 假负载 + 多圈可调电阻); REV 检波器失效会导致 SWR 误读为 1.0。

---

### AD-007: 供电方案

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-007 |
| Topic | 室外调谐器供电方案 |
| Decision | **Bias-T 同轴馈电** (13.8V DC 叠加到同轴电缆芯线) |

**Problem**: 室外设备需要供电, 但不应拉独立的电源线 (增加布线复杂度、雷击风险)。

**Alternatives**:
- A1: 独立 DC 电源线 — 简单但需要额外布线, 增加进雷路径
- A2: 太阳能 + 电池 — 成本高, 体积大, 阴天不可靠
- A3: Bias-T 同轴馈电 — 一根同轴线同时传 RF + DC, 零额外布线

**Rationale**: 同轴馈电是业余无线电室外设备的标准方案。室内用 22μH 扼流圈隔离 RF, 室外用 10nF 隔直电容隔离 DC。12V DC 电流 ~150mA 在 RG-58 上的压降可忽略。

**Impact**: 室内必须安装 Bias-T 注入盒 (~¥43 物料); L_bias 扼流圈的 SRF 必须 ≥30MHz。

---

### AD-008: 故障检测策略

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-008 |
| Topic | 运行时故障检测策略 |
| Decision | **多层级防御**: POST(上电) + diagnostics(每10s) + WDT(硬件兜底) |

**Problem**: 室外自主运行, 无人工监控。必须自我检测故障并采取行动。

**Alternatives**:
- A1: 无检测 (被动) — 故障后用户发现 SWR 飙升才排查, 可能已损坏设备
- A2: 仅 WDT — 只能防止固件跑飞, 无法检测硬件故障
- A3: 4 阶段 POST + 运行时诊断 + WDT — 三层防御

**Rationale**: 三层防御覆盖了从硬件到软件的故障谱。POST 在上电时验证全系统; 运行时诊断每 10 秒巡检; WDT 作为最后的硬件兜底。

**Impact**: 增加 ~2.3 KB Flash 和 ~90 B RAM 用于 post.c + diagnostics.c。

---

### AD-009: 降级策略

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-009 |
| Topic | 故障后运行策略 |
| Decision | **三级健康状态机**: HEALTHY → DEGRADED → SAFE |

**Problem**: 如何在不牺牲安全性的前提下最大化可用性？

**Alternatives**:
- A1: 任何故障直接停机 — 过于保守, 单继电器失效就不可用
- A2: 忽略故障继续运行 — 风险不可接受
- A3: 三级降级 — 单点故障降低功能, 多点故障进入安全状态

**Rationale**: 继电器是最常见的失效点 (机械部件)。1-2 个继电器失效时, 剩余 5-6 个仍可提供 32-64 档电容范围, 调谐能力虽下降但并非完全不可用。≥3 个失效或 CRITICAL 故障时, 进入 SAFE 锁定最后已知电容值。

**Impact**: 增加系统复杂度 (健康状态机), 但显著提升可用性。

---

### AD-010: EEPROM 磨损均衡

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-010 |
| Topic | EEPROM 磨损管理 |
| Decision | **简单方案**: Band Table (低频写入) + Fault Log (环形缓冲, 定期写入) |

**Problem**: PIC16F1938 EEPROM 额定 1M 次擦写。Band Table 每次调谐写 3 字节, 如果每小时调谐 10 次, 擦写寿命约 11 年。故障日志写频率更低 (< 10 次/天)。

**Rationale**: 考虑到设备预期寿命 (~10 年), 当前写入频率在 EEPROM 额定寿命内。不需要复杂的磨损均衡算法。

**Impact**: 如果未来增加遥测 (每秒写入), 需升级到磨损均衡方案。

---

### AD-011: 固件更新策略

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-011 |
| Topic | 固件更新机制 |
| Decision | **V1.0: 仅 ICSP 物理烧录** (需打开铝盒连接 PICkit) |

**Problem**: 室外设备如何更新固件？

**Alternatives**:
- A1: Bootloader + 串口 — 需要 UART 物理连接, 仍需打开铝盒
- A2: Bootloader + 同轴调制 — 技术上可行但复杂
- A3: ICSP 物理烧录 — 最简单, 适合 V1.0

**Rationale**: V1.0 为 DIY 级别, 固件更新频率低。生产版本 (V2.0+) 可考虑 OTA 方案。

**Impact**: 固件更新需要物理接触设备 — 对永久安装的室外设备不友好, V2.0 需改进。

---

### AD-012: 编程语言

| Attribute | Value |
|-----------|-------|
| Decision ID | AD-012 |
| Topic | 固件编程语言 |
| Decision | **C99** (XC8 编译器) |

**Rationale**: PIC16F1938 是 8 位架构, C 是最接近硬件且广泛支持的选择。XC8 是 Microchip 官方编译器, 免费版本支持 -O2 优化。

---

# 9. Architecture Overview (ART 0512)

## 9.1 Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                              │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ main.c           │  │ tuning.c         │  │ display.c    │  │
│  │ 事件循环 (100Hz)  │  │ 调谐算法          │  │ LED/蜂鸣器   │  │
│  │ 自动触发          │  │ 全扫描/快速/微调  │  │ 状态指示     │  │
│  │ 健康门控          │  │ 128档电容扫描    │  │              │  │
│  │ BOR/WDT 恢复      │  │ GPIO回写验证     │  │              │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                     │                    │          │
├───────────┼─────────────────────┼────────────────────┼──────────┤
│           │              SERVICE LAYER                │          │
│  ┌────────┴────────┐  ┌────────┴────────┐  ┌───────┴───────┐  │
│  │ swr_bridge.c    │  │ eeprom.c        │  │ post.c        │  │
│  │ ADC 驱动        │  │ 频段记忆表      │  │ 4阶段上电自检 │  │
│  │ SWR 计算        │  │ CRC-8 校验      │  │ 复位原因检测  │  │
│  │ 功率估算        │  │ 磨损均衡        │  │ FVR 电压测量  │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘  │
│           │                    │                    │          │
├───────────┼────────────────────┼────────────────────┼──────────┤
│           │                HAL LAYER                │          │
│  ┌────────┴────────────────────┴────────────────────┴───────┐  │
│  │  直接寄存器访问: ADC · GPIO · EEPROM · FVR · WDT · OSC  │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                  DIAGNOSTICS LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ diagnostics.c                                             │   │
│  │ 继电器健康监测 · SWR桥校验 · ADC卡死检测 · 故障日志      │   │
│  │ 健康状态管理 · 复位原因追踪 · 温度检测(可选)             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 9.2 Module Dependency Graph

```
main.c ──┬── tuning.c ──┬── swr_bridge.c
         │              ├── eeprom.c
         │              ├── display.c
         │              └── diagnostics.c
         │
         ├── swr_bridge.c
         ├── eeprom.c
         ├── display.c
         ├── post.c ──────── swr_bridge.c, eeprom.c, display.c
         └── diagnostics.c ── swr_bridge.c, eeprom.c, display.c

config.h ←── ALL modules
main.h   ←── ALL modules (+ diagnostics.h + post.h)
```

## 9.3 Key Design Patterns

| Pattern | Implementation | Module |
|---------|---------------|--------|
| **State Machine** | `tune_state_t` (6 states) | tuning.c |
| **Health State Machine** | `sys_health_t` (4 states, 3 transitions) | diagnostics.c |
| **Observer** | `diag_run_all()` polling every 10s | diagnostics.c |
| **Write-Back Verification** | `set_capacitor_bank()` 3-retry | tuning.c |
| **Ring Buffer** | EEPROM fault log (16 × 8 bytes) | diagnostics.c |
| **Early Exit** | SWR < 1.05 break during scan | tuning.c |
| **Graceful Degradation** | HEALTHY → DEGRADED → SAFE | diagnostics.c + main.c |

---

# 10. Service Model (ART 0582)

## 10.1 Module Interface Contracts

### M1: System Control (main.c)

| Operation | Signature | Pre-condition | Post-condition |
|-----------|-----------|--------------|----------------|
| Init | `void system_init(void)` | — | Osc ready, GPIO init, ADC init, POST done, health set |
| Tick | `void system_tick(void)` | — | WDT pet, LED heartbeat |
| Command | `void process_tune_command(void)` | — | External trigger check (placeholder V1.0) |

### M2: Tuning Engine (tuning.c)

| Operation | Signature | Pre-condition | Post-condition |
|-----------|-----------|--------------|----------------|
| Set Bank | `void set_capacitor_bank(uint8_t c)` | c ∈ [0,127] | RB0-RB6 = c, 回读验证通过, RC0-RC6 = 0 |
| Full Scan | `tune_result_t run_autotune_efhw(void)` | RF ∈ [0.5W, 15W], health ≠ SAFE | best_c locked or error code |
| Quick Tune | `tune_result_t run_quick_retune_efhw(uint32_t f)` | EEPROM valid | fine-tuned or fallback to full scan |
| Fine Tune | `void tune_fine_around(uint8_t c)` | c ∈ [0,127], RF present | best_c ∈ [c-7, c+7] |
| Abort | `void abort_tune(void)` | — | all relays OFF |

**Invariants**:
- INV1: 每次继电器切换前 `fwd_power < TUNE_POWER_MAX_MW`
- INV2: RC0-RC6 永远为低
- INV3: `set_capacitor_bank()` 后 GPIO 回读验证

### M3: SWR Bridge (swr_bridge.c)

| Operation | Signature | Pre-condition | Post-condition | WCET |
|-----------|-----------|--------------|----------------|------|
| Init | `void swr_bridge_init(void)` | ADC configured | ADON=1 | 5 μs |
| Read SWR | `uint16_t read_swr_x100(void)` | — | 100 ≤ ret ≤ 999 | 500 μs |
| FWD Power | `uint16_t read_fwd_power_mw(void)` | — | 0-65535 mW | 250 μs |
| ADC raw | `uint16_t read_adc_channel(uint8_t ch)` | ch ∈ [0,31] | 0-1023 | 30 μs |

### M4: EEPROM Storage (eeprom.c)

| Operation | Pre-condition | Post-condition | WCET |
|-----------|--------------|----------------|------|
| `eeprom_save_tune(f, c, swr)` | f ∈ amateur bands | Band Table updated | 25 ms |
| `eeprom_load_tune(f, &c, &swr)` | — | c, swr filled if hit | 30 μs |
| `eeprom_is_valid()` | — | 1 if magic=0xA5 | 10 μs |

### M5: POST (post.c)

| Operation | WCET | Failure Action |
|-----------|------|---------------|
| `post_run_full()` | ~850ms | beep pattern + health state set |
| `post_check_dc_rails()` | 50ms | Continuous rapid beep → halt |
| `post_check_relay_bank()` | 500ms | Failed relay mask → degraded |

### M6: Diagnostics (diagnostics.c)

| Operation | Period | Failure Action |
|-----------|--------|---------------|
| `diag_run_all()` | Every 10s | Health state migration + fault log |
| `diag_check_adc_stuck()` | Every ADC read | ADC HW reset retry |
| `diag_log_fault()` | On state change | EEPROM ring buffer write |

---

# 11. Component Model (ART 0515)

## 11.1 Component Inventory

| Component | Type | File(s) | Responsibility |
|-----------|------|---------|----------------|
| SystemMain | Application | `main.c/h` | 初始化, 事件循环, 健康门控, BOR/WDT恢复 |
| TuningEngine | Application | `tuning.c/h` | 电容阵列控制, 全扫描/快速重调/微调 |
| DisplayDriver | Application | `display.c/h` | LED 开关, 蜂鸣器模式 |
| SwrBridge | Service | `swr_bridge.c/h` | ADC 驱动, SWR 计算, 功率估算 |
| EepromStore | Service | `eeprom.c/h` | EEPROM 读写, Band Table, CRC-8 |
| PostRunner | Service | `post.c/h` | 4阶段POST, 复位原因检测, 电压测量 |
| FaultDiagnostics | Diagnostics | `diagnostics.c/h` | 继电器/SWR/ADC 健康监测, 故障日志, 状态管理 |
| ConfigParams | Configuration | `config.h` | 全部可调参数 (#defines) |

## 11.2 Component Interfaces (UML Style)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SystemMain (main.c)                           │
├─────────────────────────────────────────────────────────────────────┤
│ +system_init(): void                                                 │
│ +system_tick(): void                                                 │
│ +process_tune_command(): void                                        │
│ -last_tune_freq_hz: uint32_t                                        │
│ -tune_cooldown: uint8_t                                             │
│ -consecutive_tune_fails: uint8_t                                    │
│ -reset_cause_flags: uint8_t                                         │
│ -wdt_reset_count: uint8_t                                           │
└──────────────┬──────────────────────────────────────────────────────┘
               │ uses
    ┌──────────┼──────────┬──────────────┬──────────────┐
    ▼          ▼          ▼              ▼              ▼
┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│Tuning   │ │SwrBridge│ │Eeprom    │ │PostRunner│ │FaultDiag     │
│Engine   │ │         │ │Store     │ │          │ │nostics       │
├─────────┤ ├─────────┤ ├──────────┤ ├──────────┤ ├──────────────┤
│+set()   │ │+read()  │ │+save()   │ │+run()    │ │+run_all()    │
│+scan()  │ │+fwd()   │ │+load()   │ │+checkDC()│ │+checkRelay() │
│+quick() │ │+rev()   │ │+valid()  │ │+checkADC │ │+checkADC()   │
│+fine()  │ │+adc()   │ │+clear()  │ │+checkRel │ │+log()        │
│+abort() │ │         │ │          │ │+checkSWR │ │+health()     │
└─────────┘ └─────────┘ └──────────┘ └──────────┘ └──────────────┘
     │           │            │             │              │
     └───────────┴────────────┴─────────────┴──────────────┘
                              │
                         all use
                              ▼
                    ┌──────────────────┐
                    │   config.h       │
                    │   main.h         │
                    │   (全局类型+常量) │
                    └──────────────────┘
```

## 11.3 Component Interaction Sequence: Auto-Tune

```
HAM Op.    main.c      tuning.c    swr_bridge.c   eeprom.c   diag.c
  │          │            │             │             │          │
  │ 5W CW    │            │             │             │          │
  ├─────────►│            │             │             │          │
  │          │ detect RF  │             │             │          │
  │          ├───────────►│             │             │          │
  │          │  health OK?│             │             │          │
  │          │◄───────────┤             │             │          │
  │          │ run_scan() │             │             │          │
  │          ├───────────►│             │             │          │
  │          │            │ set(C=0)    │             │          │
  │          │            │ delay(12ms) │             │          │
  │          │            ├────────────►│             │          │
  │          │            │ read_swr()  │             │          │
  │          │            │◄────────────┤             │          │
  │          │            │  ... (loop) │             │          │
  │          │            │ set(C=best) │             │          │
  │          │            ├────────────►│             │          │
  │          │            │◄────────────┤             │          │
  │          │  result    │             │             │          │
  │          │◄───────────┤             │             │          │
  │          ├──────────────────────────────────────►│             │
  │          │            │             │ save_tune() │          │
  │          │            │             │◄────────────┤          │
  │ beep OK  │            │             │             │          │
  │◄─────────┤            │             │             │          │
```

---

# 12. Operational Model (ART 0522)

## 12.1 Deployment Topology

```
┌──────────────────────────────────────────────────────────────────┐
│                        INDOOR (Shack)                             │
│  ┌──────────┐    ┌──────────────┐                                │
│  │ Radio TX │───▶│ Bias-T Box   │──▶ Coax ──▶ OUTDOOR           │
│  │ 100W PEP │    │ C_block+L_rfc│                                │
│  └──────────┘    └──────┬───────┘                                │
│                         │ 13.8V DC                                │
│                    ┌────▼─────┐                                   │
│                    │ DC Power │                                   │
│                    │ 13.8V/1A │                                   │
│                    └──────────┘                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       OUTDOOR (Mast/Roof)                         │
│                         Coax from indoor                          │
│                              │                                    │
│                    ┌─────────▼──────────┐                        │
│                    │ EFHW Auto Tuner    │                        │
│                    │ (IP66 AL Box)      │                        │
│                    │ ┌────────────────┐ │                        │
│                    │ │ PCB (140×90mm) │ │    EFHW Wire ~20m      │
│                    │ │ PIC16F1938     │ ├──────────────────────▶ │
│                    │ │ T200-2 ×2      │ │                        │
│                    │ │ 7×Relay+10×MLCC│ │    Counterpoise ~2m    │
│                    │ │ SWR Bridge     │ ├──────────────────────▶ │
│                    │ │ LM7812 + 78L05 │ │                        │
│                    │ └────────────────┘ │                        │
│                    │ 1.5mm Breath Hole │                         │
│                    │ 90V GDT           │                         │
│                    │ 2.2MΩ Bleeder     │                         │
│                    └───────────────────┘                        │
└──────────────────────────────────────────────────────────────────┘
```

## 12.2 Runtime Behavior: Normal Operation

```
  State: HEALTHY (7/7 relays OK)
  
  Loop (every 10ms):
    1. read_fwd_power_mw()
    2. If 0.5W < P < 15W and cooldown expired and IDLE:
       → Trigger auto-tune (UC-001 or UC-002)
    3. If P > 15W:
       → No tune (safe – just pass RF through locked capacitor bank)
    4. If health == SAFE:
       → No tune, LED slow blink
    5. Every 10s: diag_run_all()
    6. system_tick() → CLRWDT()
```

## 12.3 Failure Recovery Sequence

```
  Event: WDT Reset (e.g., EMI glitch)
    1. MCU resets, RCON captured
    2. system_init() detects WDT flag
    3. Skip PHASE 0 POST (DC rails assumed OK)
    4. Run abbreviated POST (PHASE 1-2)
    5. Load last known C value from EEPROM
    6. If WDT count ≥ 3 in 1 hour → SAFE mode
    7. Otherwise → HEALTHY with locked C value (no auto-tune this cycle)
    8. Log FAULT_WDT_RESET to EEPROM
  
  Event: BOR Reset (e.g., supply dip)
    1. MCU resets, BOR flag set
    2. system_init() detects BOR flag
    3. If VDD now normal → run abbreviated POST
    4. Log FAULT_BOR_EVENT (INFO level)
    5. Resume normal operation

  Event: CRITICAL Fault (L0 – e.g., HV arc-over detected)
    1. set_capacitor_bank(0) – all relays OFF
    2. diag_set_health(SYS_SAFE)
    3. diag_log_fault(code, 0, ...) – CRITICAL
    4. Continuous rapid beep
    5. No auto-recovery – requires power cycle + full POST pass
```

## 12.4 Maintenance Windows

| Activity | Frequency | Downtime |
|----------|-----------|----------|
| 干燥剂更换 | 每 3 个月 | 0 min (操作时设备断电) |
| 铝盒开箱目视检查 | 每 6 个月 | ~10 min |
| SWR 桥校准 (50Ω假负载) | 每年 | ~5 min |
| 继电器寿命评估 | 每 2 年 | ~30 min (可能需要更换) |
| 固件更新 (ICSP烧录) | 按需 | ~5 min (需打开铝盒) |

---

# 13. Feasibility Assessment (ART 0530)

## 13.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| 高压打火 (PCB 爬电) | Medium | High | 2.5mm 开槽 + 三防漆 + 5mm 间距 |
| 继电器热切换烧毁 | Medium | High | 固件功率检测 + 操作培训 |
| 凝露导致 MLCC 表面放电 | Medium | Medium | IP66 + 底部呼吸孔 + 三防漆 + 干燥剂 |
| SWR 桥校准漂移 | Low | Medium | 年度校准 + BAT41 配对 <5mV |
| G5Q-14 触点氧化 | Low | Low | 密封型继电器 + 干燥环境 |
| EEPROM 写耗尽 | Very Low | Low | 写入频率分析 ≤ 10次/天 (寿命 > 30年) |

## 13.2 Resource Assessment

| Resource | Budget | Used | Assessment |
|----------|--------|------|------------|
| Flash | 28 KB | ~8 KB | Healthy margin for V2.0 features |
| RAM | 1 KB | ~230 B | Sufficient for current feature set |
| EEPROM | 256 B | ~184 B | 72% used — limited room for new persisted data |
| CPU | 32 MHz / 8 MIPS | Idle ~99% | Ample headroom |
| GPIO | 25 I/O | 9 used | 16 free for expansion |
| ADC | 11 channels | 3 used | 8 free for sensors (temp, 12V monitor, etc.) |
| Cost | ¥375 target | ¥375 actual | On budget |

## 13.3 Alternatives Considered But Rejected

| Alternative | Reason Rejected |
|-------------|-----------------|
| 真空可变电容 | 成本 ¥200-500 + 电机驱动复杂度 → 不适合 ¥375 DIY 目标 |
| PIN 二极管开关 | 3KV 高压下反向偏置可靠性不足 |
| 32-bit MCU (STM32) | 超出项目需求, 增加 BOM 成本, 不与 ATU-100 生态兼容 |
| 全 L-C 联合调谐 | 14 个继电器 → PCB 尺寸翻倍 → 铝盒更大 → 成本失控 |
| 80m 频段支持 | T200-2 在 3.5MHz 感抗不足 → 需要更大磁芯 → V2.0 扩展 |

## 13.4 Readiness Assessment

| Dimension | Status | Notes |
|-----------|--------|-------|
| 理论验证 | ✅ Complete | AA5TB 理论 + T200-2 B_peak 定量计算 |
| 工程设计 | ✅ Complete | Netlist, PCB 规范, BOM, Bias-T |
| 固件开发 | ✅ Complete | 10 编译单元, ~6.6KB Flash |
| SDD 文档 | ✅ Complete | 14 章 IBM TeamSD 规范 |
| FDE 文档 | ✅ Complete | Palantir FDE 方法论 |
| 装配手册 | ✅ Complete | 6 步骤装配 + 6 项台架测试 + 故障排查 |
| PCB 打样 | ⬜ Pending | 待发送 Gerber 到板厂 |
| 台架测试 | ⬜ Pending | 6 项测试, 需 100W 电台 + 假负载 |
| 现场验证 | ⬜ Pending | 7×24h FT8 连续运行 |

---

# 14. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| V0.1 | 2026-06-07 | BG1SB | Initial engineering design document |
| V0.2 | 2026-06-08 | BG1SB | Firmware source code (8 compile units) |
| V0.3 | 2026-06-08 | BG1SB | Simplified SDD + FDE (8-chapter format) |
| **V1.0** | **2026-06-08** | **BG1SB** | **Full IBM TeamSD 14-chapter SDD + Palantir FDE restructuring** |
| | | | Added: diagnostics.c/h, post.c/h firmware modules |
| | | | Upgraded: main.c (POST+BOR/WDT), tuning.c (GPIO verify) |
| | | | 24 files total, 10 compile units, 4,617 lines |

---

> **关联文档**: [`FDE.md`](FDE.md) (Palantir FDE 方法论)
> **工程设计**: [`../../references/auto_efhw_tuner_design_full.md`](../../references/auto_efhw_tuner_design_full.md)
> **固件源码**: [`../firmware/`](../firmware/)
> **装配测试**: [`assembly_test_manual.md`](assembly_test_manual.md)
