# EFHW Auto Tuner 100W — 全自动谐振式 EFHW 调谐适配器

> 基于 AA5TB 并联 LC 耦合器理论 × N7DDC ATU-100 开源框架
> 硬件许可: CERN-OHL-S 2.0 | 固件许可: GPL-3.0
> 完整设计文档: `../references/auto_efhw_tuner_design_full.md`

## 项目简介

一台**室外架设、同轴 Bias-T 馈电、全自动调谐**的 100W EFHW 天线适配器。解决了 AA5TB 并联 LC 耦合器需要手动调谐的核心痛点——将手动可变电容替换为 7 位 128 档二进制高压电容阵列，由 PIC16F1938 微控制器自动扫描并锁定最佳谐振点。

## 核心技术指标

| 参数 | 值 |
|------|-----|
| 频率 | 40m–10m (7.0–29.7 MHz) |
| 功率 | 100W PEP SSB/CW |
| 磁芯 | T200-2 ×2 双叠 (羰基铁粉, μ=10) |
| 匝数比 | 2:13 → 42.25:1 阻抗比 |
| 调谐 | 7位128档纯电容扫描 (10–1,997 pF) |
| 调谐时间 | <0.2s (记忆重调) / <2s (全扫描) |
| 供电 | Bias-T 同轴馈电 12V DC |
| 防护 | IP66 铝壳 + GDT 避雷 + 静电泄放 |
| PCB | 140×90mm 双层, 物理开槽隔离 |
| 单套成本 | ~¥375 |

## 目录结构

```
auto-efhw-tuner/
├── README.md                    ← 本文件
├── firmware/                    ← 固件源码 (C, PIC16F1938/XC8)
│   ├── README.md
│   ├── config.h                 ← 用户可调参数 (含FDE/POST阈值)
│   ├── main.h                   ← 全局定义与函数原型 (含诊断模块)
│   ├── main.c                   ← 主程序入口 (含POST+BOR/WDT恢复)
│   ├── tuning.h / tuning.c       ← 自动调谐核心算法 (含GPIO回读+安全门控)
│   ├── swr_bridge.h / swr_bridge.c ← SWR 桥 (Tandem Match) 驱动
│   ├── eeprom.h / eeprom.c       ← EEPROM 频段记忆 + CRC-8
│   ├── display.h / display.c     ← 蜂鸣器/LED 状态指示
│   ├── diagnostics.h / diagnostics.c ← 🆕 运行时故障检测 + 健康状态机
│   ├── post.h / post.c           ← 🆕 4阶段上电自检 + 复位原因检测
│   └── Makefile                 ← 编译配置参考
├── hardware/                    ← 硬件设计文件
│   ├── EFHW_TUNER_BOM.csv       ← 完整BOM (带立创商城编号)
│   ├── KiCad_schematic_guide.md  ← KiCad 原理图/PCB 设计指南
│   └── simulation/              ← 🆕 SPICE 电路仿真 + PCB 传输线 + 热分析
│       ├── README.md            ← 仿真环境配置 + 验证清单
│       ├── swr_bridge_spice.cir ← Tandem Match 定向耦合器 (S参数)
│       ├── lc_resonant_tank.cir ← T200-2 并联LC谐振回路 (Q/V_peak/f_res)
│       ├── bias_tee_spice.cir   ← Bias-T 同轴馈电 (S21/隔离/SRF)
│       ├── relay_driver_spice.cir ← ULN2003A继电器驱动 (反峰/瞬态)
│       ├── pcb_transmission_lines.md ← PCB 传输线/过孔/寄生参数
│       └── thermal_analysis.md  ← 热仿真 (6热源温升/CFD边界条件)
├── docs/                        ← 工程文档
│   ├── SDD.md                   ← 🆕 软件设计文档 (架构/接口/状态机/时序)
│   ├── FDE.md                   ← 🆕 故障检测与消除 (FMEA/POST/降级/故障注入)
│   └── assembly_test_manual.md  ← 装配、测试、故障排查手册
└── bias-tee/                    ← 室内 Bias-T 注入盒
    └── bias_tee_design.md       ← 独立子设计 (原理图+BOM+测试)
```

## 快速开始

### 如果你是...

**固件开发者**：
1. 阅读 `docs/SDD.md` 了解架构和接口
2. 阅读 `docs/FDE.md` 了解故障检测策略
3. 安装 MPLAB X IDE + XC8 编译器
4. 打开 `firmware/` 源码 → 在 MPLAB X 中创建项目
5. 连接 PICkit 3/4 → ICSP 口 → 编译烧录

**PCB 设计者**：
1. 阅读 `hardware/KiCad_schematic_guide.md`
2. 在 KiCad 中创建项目 → 按指南绘制原理图和 PCB
3. 运行 DRC → 导出 Gerber → 发板厂

**DIY 爱好者**：
1. 从 `hardware/EFHW_TUNER_BOM.csv` 采购全部物料
2. 按 `docs/assembly_test_manual.md` 逐步焊接装配
3. 烧录预编译的 `efhw_tuner_100w.hex`
4. 按照测试章节完成校准和验收

## 关联项目文件

- `../references/auto_efhw_tuner_design_full.md` — 完整工程设计文档 (理论+全设计)
- `../references/aa5tb_efha_analysis.md` — AA5TB 原始理论深度解析
- `../references/efhw_ac_dual_mode.md` — A+C 双模匹配系统分析
- `../README.md` — EFHW 综合知识库

## 社区与贡献

本项目是 BG1SB EFHW 知识库的工程落地子项目。欢迎：
- 提交 Issue 报告 Bug/改进建议
- 分享你的建造经验/调试图
- 贡献不同频段 (80m/160m) 的扩展设计

---

> 🏗️ 状态：设计完成 | PCB 待制作 | 固件待实机验证
> 📅 最后更新：2026-06-08
