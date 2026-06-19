-- EFHW A/B 对比试验专用表（与 pskreporter 主 schema 完全隔离）
-- 长期、多次切换的天线对比试验。数据按"切换时间线表"驱动打 config/segment 标签。
-- 短期小数据集（万行级），不分区，BUCKETS 4 足够。
--
-- 数据来源：
--   pskr_adif_store.jsonl  -> role=dut   (BG1SB，谁收到它)
--   probe_store.jsonl      -> role=probe (5 个 ON80 探针台，谁收到它们)
--
-- 配置标签由 efhw_ab_switches 时间线驱动：每条收报按 qso_time 落到对应区间。
-- 未来每切换一次天线，只需往 efhw_ab_switches 加一行，再重跑导入即可。
--
-- 运行：mysql -h ham.vlsc.net -P 9030 -u root pskreporter < efhw_ab_schema.sql

-- ============================================================
-- 切换时间线表：记录每一次天线配置切换（长期维护）
-- ============================================================
-- 每行表示"从 switch_time 起，配置变为 config"。导入时按收报时间戳落到
-- 相邻两次切换之间的区间，打上该区间的 config / segment / swr 标签。
CREATE TABLE IF NOT EXISTS efhw_ab_switches (
    id           BIGINT       AUTO_INCREMENT COMMENT '主键',
    test_id      VARCHAR(40)  NOT NULL       COMMENT '试验标识',
    seq          INT          NOT NULL       COMMENT '切换序号（从 0 递增，按时间排序）',
    switch_time  DATETIME     NOT NULL       COMMENT '该配置开始生效的时间 CST',
    config       VARCHAR(2)   NOT NULL       COMMENT 'A=49:1变压器 / B=LC调谐器',
    segment      VARCHAR(8)   NOT NULL       COMMENT '分段标识（如 A1/B1/A2），区分同配置不同时段',
    swr          DECIMAL(4,2) DEFAULT NULL   COMMENT '该段实测 SWR',
    note         VARCHAR(200) DEFAULT NULL   COMMENT '备注'
) ENGINE=OLAP
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 1
PROPERTIES (
    "replication_num" = "1"
);

-- ============================================================
-- 收报明细表
-- ============================================================
CREATE TABLE IF NOT EXISTS efhw_ab_reports (
    id           BIGINT       AUTO_INCREMENT COMMENT '主键',
    test_id      VARCHAR(40)  NOT NULL       COMMENT '试验标识',
    monitored    VARCHAR(20)  NOT NULL       COMMENT '被监测台呼号（BG1SB 或探针）',
    role         VARCHAR(8)   NOT NULL       COMMENT 'dut=被测台 / probe=传播探针',
    config       VARCHAR(2)   NOT NULL       COMMENT 'A=49:1变压器 / B=LC调谐器（按切换时间线划分）',
    segment      VARCHAR(8)   DEFAULT NULL   COMMENT '分段标识（A1/B1/A2…），区分同配置不同时段',
    rx_callsign  VARCHAR(20)  NOT NULL       COMMENT '收到信号的接收台呼号',
    rx_locator   VARCHAR(12)  DEFAULT NULL   COMMENT '接收台网格',
    dxcc         VARCHAR(50)  DEFAULT NULL   COMMENT '接收台国家/地区',
    mode         VARCHAR(10)  DEFAULT NULL   COMMENT '模式（FT8）',
    snr          INT          DEFAULT NULL   COMMENT '信噪比 dB',
    frequency    BIGINT       DEFAULT NULL   COMMENT '频率 Hz',
    band         VARCHAR(8)   DEFAULT NULL   COMMENT '波段',
    distance_km  DECIMAL(10,1) DEFAULT NULL  COMMENT '被监测台到接收台距离 km',
    bearing      DECIMAL(5,1) DEFAULT NULL   COMMENT '从被监测台看接收台的方位角',
    qso_time     DATETIME     NOT NULL       COMMENT '报告时间 CST'
) ENGINE=OLAP
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 4
PROPERTIES (
    "replication_num" = "1"
);

-- 若 efhw_ab_reports 已存在（早期单切换点版本），补加 segment 列：
-- ALTER TABLE efhw_ab_reports ADD COLUMN segment VARCHAR(8) DEFAULT NULL COMMENT '分段标识' AFTER config;

-- ============================================================
-- 初始切换时间线（2026-06-19 第一天试验）
-- ============================================================
-- A1: 12:02–12:26 49:1 初始段（更早数据已滚出 PSKR 24h 窗口）
-- B : 12:26–16:10 LC 调谐器
-- A2: 16:10–      回切 49:1
INSERT INTO efhw_ab_switches (test_id, seq, switch_time, config, segment, swr, note) VALUES
  ('efhw_49un_vs_lc_20260619', 0, '2026-06-19 12:02:00', 'A', 'A1', 1.47, '初始 49:1 变压器 3xFT-240-51'),
  ('efhw_49un_vs_lc_20260619', 1, '2026-06-19 12:26:52', 'B', 'B1', 1.30, 'LC 调谐器'),
  ('efhw_49un_vs_lc_20260619', 2, '2026-06-19 16:10:00', 'A', 'A2', 1.47, '回切 49:1 变压器');
