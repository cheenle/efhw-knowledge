-- EFHW A/B 对比试验专用表（与 pskreporter 主 schema 完全隔离）
-- 一张表用 role(dut/probe) + config(A/B) 区分被测台/探针台、切换前后两段。
-- 短期小数据集（~1 万行），不分区，BUCKETS 4 足够。
--
-- 数据来源：
--   pskr_adif_store.jsonl  -> role=dut   (BG1SB，谁收到它)
--   probe_store.jsonl      -> role=probe (5 个 ON80 探针台，谁收到它们)
-- 切换点：2026-06-19 12:26:52 CST (epoch 1781843212)，A=切换前 / B=切换后
--
-- 运行：mysql -h ham.vlsc.net -P 9030 -u root pskreporter < efhw_ab_schema.sql

CREATE TABLE IF NOT EXISTS efhw_ab_reports (
    id           BIGINT       AUTO_INCREMENT COMMENT '主键',
    test_id      VARCHAR(40)  NOT NULL       COMMENT '试验标识',
    monitored    VARCHAR(20)  NOT NULL       COMMENT '被监测台呼号（BG1SB 或探针）',
    role         VARCHAR(8)   NOT NULL       COMMENT 'dut=被测台 / probe=传播探针',
    config       VARCHAR(2)   NOT NULL       COMMENT 'A=49:1变压器 / B=LC调谐器（按切换点划分）',
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
