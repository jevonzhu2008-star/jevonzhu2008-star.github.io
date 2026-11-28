-- 站点访问统计 · D1 表结构
-- 执行：npx wrangler d1 execute ipowerbi_stats --remote --file=schema.sql

CREATE TABLE IF NOT EXISTS hits (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      INTEGER NOT NULL,              -- 访问时间（Unix 毫秒）
  day     TEXT    NOT NULL,              -- 北京时间日期 YYYY-MM-DD
  path    TEXT    NOT NULL DEFAULT '',   -- 页面路径
  title   TEXT             DEFAULT '',   -- 页面标题
  ref     TEXT             DEFAULT '',   -- 来源页（完整 URL）
  ip      TEXT    NOT NULL DEFAULT '',   -- 访客公网 IP（来自 CF-Connecting-IP）
  country TEXT             DEFAULT '',   -- 国家代码，如 CN
  region  TEXT             DEFAULT '',   -- 省/州
  city    TEXT             DEFAULT '',   -- 城市
  asn     INTEGER,                       -- 自治系统号
  org     TEXT             DEFAULT '',   -- 运营商 / 机构名
  ua      TEXT             DEFAULT '',   -- User-Agent 原文
  device  TEXT             DEFAULT '',   -- desktop / mobile / tablet / bot
  browser TEXT             DEFAULT '',   -- 浏览器
  os      TEXT             DEFAULT '',   -- 操作系统
  lang    TEXT             DEFAULT '',   -- 浏览器语言
  screen  TEXT             DEFAULT '',   -- 屏幕尺寸
  tz      TEXT             DEFAULT '',   -- 时区
  colo    TEXT             DEFAULT ''    -- Cloudflare 接入节点
);

CREATE INDEX IF NOT EXISTS idx_hits_day      ON hits(day);
CREATE INDEX IF NOT EXISTS idx_hits_day_ip   ON hits(day, ip);
CREATE INDEX IF NOT EXISTS idx_hits_day_path ON hits(day, path);
CREATE INDEX IF NOT EXISTS idx_hits_ip_ts    ON hits(ip, ts);
