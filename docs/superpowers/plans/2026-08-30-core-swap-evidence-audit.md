# 磁芯换装证据裁决与知识库闭环 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (本计划为内联执行选定)。Steps use checkbox (`- [ ]`) syntax.

**Goal:** 按规格 `docs/superpowers/specs/2026-08-30-core-swap-evidence-audit-design.md`（范围C）产出两份新参考文档、修复 7 处存量错标、重写 README 选型表、追加测试手册章节、归档外部草稿、更新索引。

**Architecture:** 纯 Markdown 知识库变更；证据文档与协议文档为新增主干，存量修复只拆错误前提、保留成立论证。

**Tech Stack:** Markdown、grep 验证、git 逐任务提交。

## Global Constraints

- 中文正文；`references/xxx.md` 命名；`[[wikilink]]` 与相对路径链接并存（沿用各文件现状）。
- 每个新数字必须带来源 URL 或标 *未实测*；owenduffy.net 主站已下线 → 引用一律走 `web.archive.org` 快照或 squashpractice.com 同作者文章。
- 数据表值优先于库内旧值（43 料 μᵢ=800 替换 850）。
- 每任务一个 commit，message 前缀 `docs:`；作者 trailer `Co-Authored-By: Claude <noreply@anthropic.com>`。
- 规格 §5 划界：不改 V3.0 电路/固件描述；不动 deep-dive 的 43% 结论（仅加勘误链接行）。

---

### Task 1: 新增 `references/core-swap-evidence-2026-08.md`（裁决主文档）

**Files:** Create `references/core-swap-evidence-2026-08.md`

- [ ] Step 1: 写入以下全文：

````markdown
# 磁芯换装证据裁决 — 3×FT240-51 → Fair-Rite 2643251002

> 2026-08-30 ｜ 状态：文献裁决完成，本库台架实测待执行（见 [[transformer_ab_protocol]]）
> 裁决对象：两份外部生成报告（存档于 `references/external-drafts/`）+ 知识库既有相关主张
> 方法：四级裁决（证伪/平反/修正/待实测），每条带证据与置信度。规则：数字必须出自
> ①材料数据表原文 ②发表实测 ③本库自测，否则不采信。

## 0. 自我修正记录

1. **撤回 "DG0SNC 效率研究" 引用**：多轮独立检索（qrp-labs、dg0snc.de、德文关键词变体）
   零结果，该"研究"不存在于任何索引源。今后本库效率数据一律引用 Owen Duffy / MM0OPX / N1FD。
2. **降级前判**："谐振漂移 170kHz 不现实" → 可信（F4LEK 实测换抽头挪 143kHz；高阻节点 1pF
   杂散即可挪 100kHz 级）；"350kHz 平底驻波不可能" → 可信（损耗阻尼+测量遮蔽可造出假宽带，
   ON7EQ：3dB 线损把馈电点 9:1 掩成电台端 3.5:1）。
3. **修正前判**："51 料优势在高磁通饱和" → 错。51 与 43 的 B@10Oe 同为 3500 G，
   51 的优势是 tanδ/μᵢ 与电阻率，不含饱和裕度。

## 1. 材料事实表（数据表原文级）

| 参数 | Mix 43 | Mix 51 | Mix 61 | 来源 |
|---|---|---|---|---|
| 类别 | **NiZn**（EMI 抑制，20–250MHz） | **NiZn**（低损电感，**≤5MHz**，特殊订料） | NiZn（电感 ≤25MHz；抑制 >200MHz） | [43](https://fair-rite.com/43-material-data-sheet/) / [51](https://fair-rite.com/51-material-data-sheet/) / [61](https://fair-rite.com/61-material-data-sheet/) |
| μᵢ | 800 | 350 | 125 | 同上 |
| tanδ/μᵢ | 100×10⁻⁶ @1MHz | 30×10⁻⁶ @1MHz | 90×10⁻⁶ @10MHz | 同上 |
| 电阻率 | 1×10⁵ Ω·cm | 1×10⁹ Ω·cm | 1×10⁸ Ω·cm | 同上 |
| B@10Oe | 3500 G | 3500 G | 2500 G@15Oe | 同上 |
| Curie | >130°C | >170°C | >300°C | 同上 |

- **"51/43 均属低损"证伪**：43 是刻意做"损"的抑制料（ludens.cl 实测 43 的 HF 芯损为 61 料的
  7–15 倍：https://ludens.cl/Electron/ferrites/ferriteloss.html ）。
- **"FT240-51" provenance**：Amidon 无该目录件（https://www.amidoncorp.com/ft-240-51/ 404），
  51 为 Fair-Rite 特殊订料 → 实物 51 印字磁环来源存疑，本库一律标"未经证实的料号"。
- **2643251002**：43 料实心圆缆抑制环，OD 39.10 × ID 16.75 × L 22.20 mm，104 g
  （https://fair-rite.com/product/round-cable-emi-suppression-cores-2643251002/ ）；
  单匝 111Ω@10MHz。内孔仅容 0.5–1.5mm 漆包线（2.0mm 需挤压，社区多报告"very tight"）。

## 2. 实测效率汇总（49:1/同族，低功率 VNA/量热，非 100W 直测）

| 构型 | 3.6MHz | 7MHz | 14MHz | 21MHz | 28MHz | 来源/置信度 |
|---|---|---|---|---|---|---|
| FT240-43 单只 2:14 | 75.1% | 78.3% | 81.5% | — | 78.7% | [MM0OPX 表](https://docs.google.com/spreadsheets/d/1OCBE5aVc_kkPXRaPDy-xGL7LLEAjUilN) + [Owen 2026](https://squashpractice.com/2026-07-13/the-best-efhw-antenna-and-491-transformer/) 两源一致 |
| FT240-43 ×3 叠 2:14 | 88.1% | 88.6% | 87.6% | 83.9% | **66.4%** | MM0OPX |
| FT240-52 ×3 叠 2:14 | 91.0% | 94.2% | 90.5% | 89.9% | 85.7% | MM0OPX（单源） |
| **2643251002 单只 2:14+100pF** | 89–91% | ~89–91% | ~90% | 平坦 | 平坦；30MHz 0.7dB | Owen [p=21901 存档](http://web.archive.org/web/20241005224148/https://owenduffy.net/blog/?p=21901) / CT2FZI / MM0OPX 三源 |
| 2643251002 单只 **3:21** | 94.8% | 94.6% | 93.1% | — | **23%（−6.3dB）** | MM0OPX — 绕法即命运 |
| FT140-43 单只 2:14 | — | 68–73% | — | — | 20%(4:28) | MM0OPX |
| FT240-51 任何构型 | **零公开发表数据** | | | | | 仅 Reddit 轶事"efficiency was bad"（无数字） |

关键实测结论（Owen Duffy 量热法，https://squashpractice.com/2021-07-20/engineering-the-efhw-491-transformer-and-antenna/ ）：
1. **损耗 ∝ 1/N_primary，与磁芯质量基本无关**（原话：250g 磁芯与 14g 磁芯发热功率几乎相同，
   唯一补救是提高初级电感）。叠芯有效只因叠芯买到 Xm。
2. 43 料 μ′=μ″ 交叉在 ~7MHz，>10MHz 后 μ″ 主导 → **2 匝 43 料的发热最恶区是 20–10m**，
   低频发热才与 Xm 不足相关。"换 43 后 10m 全赢"不成立。
3. 量热：2×FT114-43 盒内 50W FT8（21W 平均）ΔT 9.8–14.2°C，η 90.5–93.4%（±20% 不确定度）。
4. Owen 热测 2643/2:14：50W@3.5–3.6MHz 芯损 4.3W、开架 ΔT 31.5°C → **低频 100W 连续模式须降额**。
5. <7MHz 时 43 料损耗随温度**上升**（正反馈）；>7MHz 无温度依赖。

## 3. 物理判定（外部报告逐条）

| 主张 | 裁决 | 依据 |
|---|---|---|
| 端馈点=电流波节；20.1m/λ 模第一腹点 ~5m@14MHz、~2.6m@28MHz | ✅ 成立 | [practicalantennas](https://practicalantennas.com/designs/end-fed/)、[N6CC](https://www.n6cc.com/end-fed-half-wave-wire-antennas/)；**"1.85m 腹点说"证伪** |
| 1.85m 串 L → 四波段独立对齐免天调 | ❌ 证伪 | 串联元件承载全部馈点电流；[PA3HHO](https://pa3hho.wordpress.com/end-fed-antennes/multiany-band-end-fed-english/)、[ON7EQ](https://www.qsl.net/on7eq/projects/efhw_antenna.htm)（110µH 线圈 SWR<3 仅 20kHz）、[VK3IL](https://vk3il.net/projects-antenna/trapped-five-band-efhw-sota-antenna/)、[AI6XG](https://www.ai6xg.com/post/trapped-20-30-40-meter-efhw-antenna) 全部记录强波段耦合 |
| 铝盒寄生电容下拉谐振 | ✅ 实锤 | Owen：次级寄生电容裸装 2.7pF→入盒 6.0pF（工程篇）；[Orderwire](https://theorderwire.com/2023-08-15/linked-efhw-what-if-we-remove-the-conductive-eyebolt/)：导电吊环挪 26kHz、手靠近挪 248kHz。社区规范=塑料壳 |
| 换磁芯改变仰角/DX 方向性 | ❌ 证伪 | 损耗等比缩放方向图。Sloper 固有弱方向性（偏向下坡端，20m 低端 ~+1.5dBi@20°，高端 −11dBi，[KK4OBI 4NEC2](https://www.qsl.net/kk4obi/EFHW%20Sloping.html)）与磁芯无关 |
| "43 太高效 → 共模倾泻回机房" | ⚠️ 机理倒置 | EFHW 共模由尾线电长度与端阻抗决定；43 料自身是损耗性 CM 阻抗（[PA0NHC](https://www.pa0nhc.nl/CommonModeChokes/indexE.htm)：阻性为主的扼流才消 CM）。损耗大的旧盒"消 CM"实为连有用功率一起烧。结论不变：室外 CMC 该装，但理由换掉 |
| CMC 用 FT240-43 绕 15–17 匝 | ❌ 过度 | 本库既有规程 6–10 匝（`references/efhw_cmc.md`，W8JI 口径）；15 匝以上自谐振下移反损高频扼流。L_bias 用 15 匝是 FT37-43 偏置隔 RF，用途不同勿混淆 |
| 2:14+130pF 银云母补偿 | ✅ 有实测背书 | Owen 配方即 2:14+~100pF；无补偿 ">15MHz 变差"，有补偿 1–30MHz IVSWR<2；**但补偿电容掩 VSWR 且增大高频芯损**（Owen/PA3HHO 警告），130pF 与"500V 耐压不足须两 240–270pF 串联"建议保留为工程改进项 |
| 100W 下"磁饱和热漂移" | ❌ 红鲱鱼 | B(100W,2T)≈70–137 G vs 43 热饱和 ~2000 G（Owen 工程篇）；功率极限=发热，发热极限=初级匝数 |

## 4. 功率红线（正式，2643251002 / 2:14 / 铝盒，直至实测推翻）

| 工况 | 限制 | 解除条件 |
|---|---|---|
| FT8/CW 3.5–7.3MHz | **≤50W** | [[transformer_ab_protocol]] T2 热测通过（60s/100W 盒壁 ≤55°C） |
| FT8/CW 14MHz | ≤100W | T2 通过即背书 |
| FT8/CW 21/28MHz | **≤50W**（μ″主导损耗区） | T2 含 10m 科目通过 |
| SSB/PAT（低占空比） | 100W 可用 | — |
| 80m 100W 连续 | **禁用** | 不建议解除（Owen 开架数据已 +31.5°C@50W） |
| 铝盒 | 散热差于开架；密封盒散不出 ~6W 量级（[N1FD 模型](https://www.n1fd.org/2022-08-12/ferrite-loss-2/)） | 热测后评估换壳/加导热垫 |

## 5. 存量文档修正映射

| 位置 | 错 | 处置 |
|---|---|---|
| README.md:119–121 | FT240-43/31 标 "Mn-Zn"、μ=850 | 重写 §2 选型表（本计划 Task 3） |
| README.md:126 | "磁芯容易进入磁饱和" | 改为磁化电流分流+芯损机理 |
| README.md:166–174 | "Ni-Zn vs Mn-Zn 涡流"整节（FT240-43 本为 NiZn） | 重写为 tanδ/电阻率家族内对比（Task 4） |
| README.md:259–263 | "Mn-Zn 铁氧体 (Mix 43)" | 错标+机理词（Task 4） |
| dmegc_nizn_toroid.md:63,73,157–163 | Mix 43 标 Mn-Zn、ρ=1–10 Ω·cm、趋肤深度论证 | 类别/数值改数据表值；2.6 节改 tanδ 论证并标 *推导待验*（Task 5） |
| aa5tb_efha_analysis.md:164 | "Mn-Zn Type 43/31/61" | 类别改正，结论保留（Task 5） |
| efhw_ac_dual_mode.md:72,87–91,258 | "Mn-Zn Mix 43"、ρ 行 | 类别/数值改正（Task 5） |

存活不受影响的论证：DMEGC 文档 Steinmetz/B 减半→Pv∝B^2.5 链（与材料类别无关）、
N6CC 石蜡测试、AA5TB <0.5dB 实测、README §8 N6CC 方向图数据。

## 6. 待实测清单（回填本表即闭环）

见 [[transformer_ab_protocol]]：P1 新旧盒 S21 逐带效率｜P2 2643 铝盒 60s/100W 红外热像
（40m+10m 双科目）｜P3 合盖/开盖谐振位移｜P4 CMC 三点位 A/B｜P5 V3.0 伺服 basin 宽度。
````

- [ ] Step 2: `grep -c "fair-rite.com" references/core-swap-evidence-2026-08.md` ≥3；文件无 "TODO/TBD"。
- [ ] Step 3: commit `docs: 磁芯换装证据裁决文档 (3xFT240-51 vs 2643251002)`

### Task 2: 新增 `references/transformer_ab_protocol.md`

**Files:** Create `references/transformer_ab_protocol.md`

- [ ] Step 1: 写入全文（结构：目的→P0 安全→P1 S21→P2 热→P3 自谐振→P4 现场扫频/合盖→P5 CMC→P6 调谐 basin→记录表 6 张→判据回写规则）。核心内容：

````markdown
# 变换器 A/B 实测协议 — 3×FT240-51 vs 2643251002

> 2026-08-30 ｜ 配套裁决文档：[[core-swap-evidence-2026-08]] ｜ 执行人：BG1SB
> 原则：所有效率数字以本协议实测为准，替换前一律标 *未实测*。

## P0 安全与准备
- 两盒同轴口均先接 50Ω 假负载试发 10W/10s 确认无打火；铝盒必须搭铁。
- 记录环境温湿度（影响散热解读）。设备：天析/NanoVNA（需 S21）、红外枪、秒表、5W 电阻串并组 2.4kΩ。

## P1 S21 透射效率（台架，裁决"1.5–2dB"与"90%+"之争）
1. 校准 S11+S21 至两根测试线端口。
2. 被测盒 50Ω 口 → VNA S11 端口；线端（天线口）→ 2450Ω 无感负载（2×1.2kΩ 串联，实测其阻值并记入表）。
3. VNA S21 端口经另一 49:1 参考变换器反推至该负载（参考件固定为 2643 盒，A/B 交换被测件消除参考误差）。
4. 连续波点频 3.6/7.1/14.2/21.3/28.5 MHz，记 |S21|(dB)；损耗(dB)≈|S21|参考互易修正，两盒直接相减即相对差。
5. **判据**：差 <0.5dB 则外部报告"效率代差"叙事作废；结果回填裁决文档 §6-P1。

## P2 热实测（裁决 §4 红线解除条件）
- 构型：2643 盒装入 **实际铝盒**，输出接 2450Ω 负载。
- 电台 FT8 模式 100W（占空 ~50%）× 60s + 静默 30s，共 5 周期；红外枪每 30s 记盒壁/磁芯可视部位温度。
- 科目：40m 与 10m **各一轮**（10m 验证 μ″ 主导发热预测）。同轮跑旧 3×51 盒作对照。
- **通过门**：盒壁稳态 ≤55°C 且驻波漂移 <0.2 → 解除 §4 对应红线（在裁决文档 §4 表格加实测行）。

## P3 自谐振与裸盒扫频
- VNA S11：初级看进去 1–54MHz log 扫；记录第一自谐振点。参考量级：2643 上 2T 绕组 SRF≈16MHz（Owen）。
- 目的：解释 15m/10m 匹配结构差异；结果回填 §5 表。

## P4 现场挂测（原斜拉几何、同尾线）
1. 校准至电台端，S1L2S3；扫 3–30MHz，**存 log-mag Z 幅相**（不只 SWR）。
2. 记录 7.050/14.074/14.260/21.2/28.3 的深 V 底点频率、SWR 底值、SWR<1.5/<2 带宽(kHz)。
3. **合盖/开盖对比**（开盖以扎带悬吊同位）：位移量 = 铝盒电容实测量（预判 30–150kHz；参照手靠近 248kHz 的敏感度量级）。
4. 新旧盒各一轮，其余几何零改动——任一几何差异使该轮作废。

## P5 CMC A/B（裁决"共模倾泻"之争）
- 三点位：CMC（FT240-43，RG-58 **7 匝**）置于盒下 3m / 4.5m / 不接；14.074 与 7.050 各扫一遍 + 发射时触碰法/备用场强探头定性对比。
- 记录 SWR 与深 V 位置位移；判据：若三点位 SWR 差 <0.2，机房 RFI 风险按现状可接受（USB 事件另行排查地环路）。

## P6 电台/调谐器行为（V3.0 或手调）
- 14.074 与 14.260 各完成一次自动调谐，记录伺服目标步数、锁定耗时、重试次数（MRRC 日志导出）。
- 判据：重试 ≥2 次 = V 形 basin 窄于搜索步进 → 该带调谐表加密或降速（记录进 CHANGELOG 操作注记，勿剪线）。

## 数据表模板（复制填写）
P1：| MHz | 旧盒dB | 新盒dB | 负载实阻 |
P2：| t/s | 40m新盒°C | 40m旧盒°C | 10m新盒°C |
P4：| 频点 | 新盒底点kHz/带宽 | 旧盒 | 合盖-开盖Δ |
P5/P6：同栏自加。
````

- [ ] Step 2: 与裁决文档互链存在（grep `core-swap-evidence` 命中）。
- [ ] Step 3: commit `docs: 变换器 A/B 实测协议`

### Task 3: README §2 磁芯选型表重写（README.md:115–126）

- [ ] Step 1: 将 117–126 行（表头行至"核心注意"段）整段替换为（新表含实测效率列+2643 行+匝数原则框+"磁饱和"措辞修正）：

| 磁芯 | 材质（数据表） | μᵢ | Ae (mm²) | 实测效率 @49:1（低功率 VNA） | 薄弱点 | 适用场景 |
- 行：FT240-43 单只（Ni-Zn 43, 800, 161, ≈75–82%〔两源〕, 2T 低频 Xm 不足, 不推荐单只 QRO）；
- FT240-43 ×3（483, 86–89% 40–15m, **10m 66%**, 低频 QRO 可用）；
- FT240-52 ×3（483, 91–94% 平坦, 160m 65–67% 且难采购, QRO 旗舰）；
- **2643251002**（Ni-Zn 43 实心缆环, 800, ≈248〔OD39.1×ID16.8×L22.2, 104g〕, **≈89–91% 平坦**〔三源〕, 10m/30MHz 0.7dB、内孔限 0.5–1.5mm 线、铝盒散热, 🏆 单芯最佳几何，须热测解锁 100W）；
- FT140-43（~70, 68–88% 强烈依赖匝数, 高匝比下 10m 崩, QRP）；
- DMEGC Ni-Zn 50×25×28（功率料 *未实测*, 800/1000, 350, 理论 2.5–7.4W@80m, —, 待 [[transformer_ab_protocol]] P1 台架）；
- "FT240-51"（料号存疑：Amidon 无目录件、51 为 Fair-Rite 特殊订料；**零公开实测**；低 μᵢ 须更多匝, 本库旧 3 叠实物按待测件处理）。
- 设计原则框：**损耗 ∝ 1/N_primary（磁芯大小几乎无关，Owen Duffy 量热实测）**；叠芯=买 Xm；43 料 >10MHz μ″ 主导 → 发热最恶区在 20–10m。数字均链接至 [[core-swap-evidence-2026-08]] §2。
- "核心注意"段改写：80m 表现差根因 = 初级感抗不足 → 磁化电流分流 + μ″ 芯损上升（≤100W 下磁通密度距饱和两个数量级，非"磁饱和"）。
- [ ] Step 2: 表下追加 124 行 DMEGC 旧"新发现"引言中 "80m 磁芯损耗仅 43%" 保留但补 "(Steinmetz 推导，未实测)"。
- [ ] Step 3: commit `fix(readme): 磁芯选型表按实测证据重写，纠正 Mn-Zn 错标`

### Task 4: README 涡流论证重写（166–174 行）+ 259 行表

- [ ] Step 1: 166–174 小节（标题"Ni-Zn vs Mn-Zn：高频涡流的隐藏优势"至"远低于 FT240-43"）整块替换为：

```markdown
#### 抑制料 vs 功率料：tanδ 才是主轴（2026-08-30 勘误重写）

> 原文以 "FT240-43 属 Mn-Zn、涡流大" 为前提——**该前提不成立**：Mix 43 是 Ni-Zn（见 [[core-swap-evidence-2026-08]] §1）。

| 参数 @1MHz（数据表） | Ni-Zn 43（FT240-43） | Ni-Zn 51（功率） | Ni-Zn 61（高频） |
|---|---|---|---|
| tanδ/μᵢ | 100×10⁻⁶ | 30×10⁻⁶ | 90×10⁻⁶ @10MHz |
| 电阻率 (Ω·cm) | 1×10⁵ | 1×10⁹ | 1×10⁸ |

- 同为 Ni-Zn，家族内 tanδ 差 3 倍+、电阻率差 4 个数量级：功率/高频料对抑制料的优势真实存在，但轴心是**损耗角与配方**，不是"NiZn vs MnZn"。
- 若 DMEGC 功率料优于 FT240-43，预期来源 = 更低 tanδ + Ae 大 2.2× 使 B 减半（Pv∝B^2.5）。*推导，未实测*。
```

- [ ] Step 2: 259–263 表格：列头 "Mn-Zn 铁氧体 (Mix 43)"→"Ni-Zn 抑制型铁氧体 (Mix 43)"；μ 850→800；"磁芯损耗 @30MHz 显著"→"磁芯损耗 @30MHz 显著（μ″ 主导，非涡流）"。268 行结论保留。
- [ ] Step 3: commit `fix(readme): 涡流论证重写为 tanδ/电阻率家族内对比`

### Task 5: 存量三文档错标修复

- [ ] Step 1: `references/dmegc_nizn_toroid.md`
  - :63 `Fair-Rite Mix 43 (Mn-Zn, μ=850): Bs ≈ 320 mT` → `Fair-Rite Mix 43 (**Ni-Zn**, μ=800): B@10Oe = 3500 G`
  - :73 `| Mix 43 (Mn-Zn, μ=850) | >130°C | Mn-Zn Tc 通常低于 Ni-Zn |` → `| Mix 43 (Ni-Zn, μ=800) | >130°C | 数据表值 |`
  - :155–163（§2.6 标题至"核心优势"引言块）替换：`| Ni-Zn 抑制型 (Mix 43) | 1×10⁵ Ω·cm | — |`、`| Ni-Zn 功率型 (51) | 1×10⁹ Ω·cm | — |` 两行 + 结论改为"优势主轴是 tanδ 与配方；原'43=MnZn 涡流'论证前提不成立，见 [[core-swap-evidence-2026-08]]。整节 *推导待验*"。
  - 文档头部状态行追加：`> ⚠️ 2026-08-30 勘误：材料类别与 §2.6 论证已修正（[[core-swap-evidence-2026-08]]），Steinmetz/Ae 链仍成立。`
- [ ] Step 2: `references/aa5tb_efha_analysis.md:164` → `- **慎用铁氧体**：Ni-Zn 抑制型铁氧体 (Mix 43/31/61) 在 10–30 MHz 磁芯损耗（μ″ 主导）显著增加`
- [ ] Step 3: `references/efhw_ac_dual_mode.md` :72 `Mn-Zn Mix 43, μ=850`→`Ni-Zn Mix 43, μ=800（数据表）`；:87 列头改 `铁氧体 (Ni-Zn Type 43)`、μ 850→800；:90 `电阻率 1-10 Ω·m`→`≈1×10⁵ Ω·cm`；:91 行词改"磁芯损耗（μ″ 主导）随频率增大"；:258 改为 tanδ 轴表述（一句）。
- [ ] Step 4: grep 验收：`grep -rn "Mn-Zn" README.md references/*.md | grep -iE "43|31|61"` 零命中。
- [ ] Step 5: commit `fix(refs): 清除 Mix 43/31/61 的 Mn-Zn 错标及派生论证（3 文件）`

### Task 6: V3 测试手册 + CHANGELOG

- [ ] Step 1: `auto-efhw-tuner/docs/assembly_test_manual.md` 在 `> **关联文档**` 行之前插入 `## 10. 变换器台架验收（A/B 换装红线）`：P1/P2 步骤引用 `../../references/transformer_ab_protocol.md`；通过门表=裁决文档 §4 红线表原样（FT8/CW 3.5–7.3MHz ≤50W…）+ 复测周期（每年 §9 全频段扫描时复跑 P2 单科目）。
- [ ] Step 2: `auto-efhw-tuner/CHANGELOG.md` V3.0 节末追加：`### 2026-08-30 — Docs\n- 测试手册 §10 变换器 A/B 验收与功率红线；证据链 references/core-swap-evidence-2026-08.md（撤回 DG0SNC，改用 Owen Duffy/MM0OPX/N1FD）`
- [ ] Step 3: commit `docs(v3): 测试手册增设变换器验收红线章节`

### Task 7: 索引与勘误指针

- [ ] Step 1: README:4 更新行 → `> 最后更新: 2026-08-30 (🆕 磁芯换装证据裁决 + A/B 实测协议入库)`
- [ ] Step 2: README 知识图谱表（DMEGC 行附近）加两行：`**磁芯换装证据裁决 (3×51→2643251002)** 🆕 | BG1SB/Claude 研究组 | 2026-08-30 | references/core-swap-evidence-2026-08.md`、`**变换器 A/B 实测协议** 🆕 | BG1SB | 2026-08-30 | references/transformer_ab_protocol.md`
- [ ] Step 3: `references/deep-dive-2026-05-25.md` 文首加一行：`> ⚠️ 2026-08-30：文中 "Mn-Zn" 类材料表述有误、"DG0SNC" 式效率叙事不适用——以 [[core-swap-evidence-2026-08]] 为准；43%/截面积推导保留。`
- [ ] Step 4: commit `docs: 索引与勘误指针更新`

### Task 8: 外部草稿归档 `references/external-drafts/`

- [ ] Step 1: 建目录；两文件 `2026-08-swap-report-draft-1.md`、`2026-08-swap-report-draft-2.md`。头部批注块（固定文本）：

```markdown
> 📦 外部生成草稿存档 — 未证实文本，保留原样仅供审计。
> 逐条裁决见 [[core-swap-evidence-2026-08]]。本文件任何数字不得直接引用。
```

  正文 = 两份报告原文逐字（**内联执行：取本会话用户消息原文**；若交子代理执行：由主控在派发前把原文粘入任务说明，禁止让执行者凭记忆复写）。尾部附"主张→裁决"两列摘要表（从裁决文档 §3/§2 摘行）。
- [ ] Step 2: commit `docs: 归档两份外部报告草稿并挂批注`

### Task 9: 终验（verification-before-completion）

- [ ] Step 1: 跑规格 §7 三条：① grep Mn-Zn→43/31/61 零命中；② grep DG0SNC 仅出现在"撤回"上下文；③ 协议数据表列/单位/判据完整人工过目。
- [ ] Step 2: URL 抽样 `curl -sI`：fair-rite 两页、squashpractice 三篇、n1fd 一篇 → 200/301；groups.io/docs.google 允许 403/302（记录"需登录"）。
- [ ] Step 3: `git status` 干净、`git log --oneline -8` 核对 8 次提交；向用户汇报实测差异清单。
