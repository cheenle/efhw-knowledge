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
| 换芯后存在"代差级 DX 增益" | ❌ **本库实测直接证伪** | 2026-06-19 端到端 A/B（21.074 FT8/100W/同一天线，49:1 3×FT240-51 vs LC 调谐器）：ΔSNR 净差 −0.3～−0.75dB，落在 ±1dB 测量噪声内，**统计不可区分**——见仓库根 `EFHW_49to1_vs_LC_测试报告_20260619.md`（含脚本/ADIF/探针全链可复算） |
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
| SSB/PSK（低占空比） | 100W 可用 | — |
| 80m 100W 连续 | **禁用** | 不建议解除（Owen 开架数据已 +31.5°C@50W） |
| 铝盒 | 散热差于开架；密封盒散不出 ~6W 量级（[N1FD 模型](https://www.n1fd.org/2022-08-12/ferrite-loss-2/)） | 热测后评估换壳/加导热垫 |

## 5. 存量文档修正映射

| 位置 | 错 | 处置 |
|---|---|---|
| README.md:119–121 | FT240-43/31 标 "Mn-Zn"、μ=850 | 重写 §2 选型表 |
| README.md:126 | "磁芯容易进入磁饱和" | 改为磁化电流分流+芯损机理 |
| README.md:166–174 | "Ni-Zn vs Mn-Zn 涡流"整节（FT240-43 本为 NiZn） | 重写为 tanδ/电阻率家族内对比 |
| README.md:259–263 | "Mn-Zn 铁氧体 (Mix 43)" | 错标+机理词 |
| dmegc_nizn_toroid.md:63,73,157–163 | Mix 43 标 Mn-Zn、ρ=1–10 Ω·cm、趋肤深度论证 | 类别/数值改数据表值；2.6 节改 tanδ 论证并标 *推导待验* |
| aa5tb_efha_analysis.md:164 | "Mn-Zn Type 43/31/61" | 类别改正，结论保留 |
| efhw_ac_dual_mode.md:72,87–91,258 | "Mn-Zn Mix 43"、ρ 行 | 类别/数值改正 |

存活不受影响的论证：DMEGC 文档 Steinmetz/B 减半→Pv∝B^2.5 链（与材料类别无关）、
N6CC 石蜡测试、AA5TB <0.5dB 实测、README §8 N6CC 方向图数据。

## 6. 待实测清单（回填本表即闭环）

**已完成**：21MHz 端到端 A/B（49:1 变压器 vs LC 调谐器，2026-06-19，`EFHW_49to1_vs_LC_测试报告_20260619.md`）——天线级效率差统计不可区分。
**待执行**：见 [[transformer_ab_protocol]]：P1 新旧盒 S21 逐带效率｜P2 2643 铝盒 60s/100W 红外热像
（40m+10m 双科目）｜P3 合盖/开盖谐振位移｜P4 CMC 三点位 A/B｜P5 V3.0 伺服 basin 宽度。
现场记录：[[transformer_ab_log-2026-08]] ｜ 判据速算：`scripts/ab_judge.py`。
