/* ipowerbi 站点访问统计 · Cloudflare Worker
 *
 * 路由：
 *   POST /collect          前端 beacon 上报（跨域，来源白名单）
 *   GET  /admin            后台页面（数据需登录）
 *   POST /admin/login      口令登录，成功后下发签名 Cookie
 *   POST /admin/logout     退出
 *   GET  /admin/api/data   汇总 + 明细（需登录）
 *   GET  /admin/api/export 导出 CSV（需登录）
 *
 * 需要的密钥：
 *   ADMIN_PASSWORD   后台口令
 *   SESSION_SECRET   给登录 Cookie 签名的随机串
 * 需要的绑定：
 *   DB               D1 数据库（见 schema.sql）
 */
import ADMIN_HTML from "./admin.html";

const DAY_MS = 86400000;
const TZ_MS = 8 * 3600 * 1000; // 后台统一按北京时间分天
const MAX_BODY = 4096;

/* ── 小工具 ───────────────────────────────────────────── */

function dayKey(ts) {
  return new Date(ts + TZ_MS).toISOString().slice(0, 10);
}

function clean(v, max = 300) {
  if (v == null) return "";
  return String(v).replace(/[\u0000-\u001f\u007f]+/g, " ").trim().slice(0, max);
}

function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

function b64url(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function sign(env, msg) {
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(env.SESSION_SECRET || "dev-secret"),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const buf = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg));
  return b64url(new Uint8Array(buf));
}

function getCookie(request, name) {
  const h = request.headers.get("Cookie") || "";
  for (const part of h.split(";")) {
    const i = part.indexOf("=");
    if (i < 0) continue;
    if (part.slice(0, i).trim() === name) return decodeURIComponent(part.slice(i + 1).trim());
  }
  return "";
}

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extra,
    },
  });
}

/* ── CORS（/collect 专用） ─────────────────────────────── */

function allowList(env) {
  return (env.ALLOWED_ORIGINS || "https://ipowerbi.icu")
    .split(",").map((s) => s.trim()).filter(Boolean);
}

function corsHeaders(origin, env) {
  const ok = origin && allowList(env).includes(origin);
  if (!ok) return { Vary: "Origin" };
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

/* ── UA 解析（够看，不引依赖） ─────────────────────────── */

function parseUA(ua) {
  const s = (ua || "").toLowerCase();
  const out = { device: "desktop", browser: "—", os: "—" };

  if (/(bot|crawl|spider|slurp|bingpreview|yandex|baiduspider|googlebot|curl\/|wget|python-requests|headlesschrome|scrapy|ahrefs|semrush|petalsearch|gptbot|claude|ccbot)/.test(s)) {
    out.device = "bot";
    out.browser = "爬虫";
    return out;
  }

  if (/ipad|tablet/.test(s) || (/android/.test(s) && !/mobile/.test(s))) out.device = "tablet";
  else if (/mobi|iphone|ipod|android|windows phone/.test(s)) out.device = "mobile";

  if (/windows nt 10|windows nt 11/.test(s)) out.os = "Windows 10/11";
  else if (/windows nt 6\.3/.test(s)) out.os = "Windows 8.1";
  else if (/windows/.test(s)) out.os = "Windows";
  else if (/iphone|ipad|ipod/.test(s)) out.os = "iOS";
  else if (/mac os x/.test(s)) out.os = "macOS";
  else if (/android/.test(s)) out.os = "Android";
  else if (/linux/.test(s)) out.os = "Linux";

  if (/micromessenger/.test(s)) out.browser = "微信";
  else if (/wxwork/.test(s)) out.browser = "企业微信";
  else if (/qqbrowser/.test(s)) out.browser = "QQ 浏览器";
  else if (/dingtalk/.test(s)) out.browser = "钉钉";
  else if (/edg\//.test(s)) out.browser = "Edge";
  else if (/opr\/|opera/.test(s)) out.browser = "Opera";
  else if (/firefox\//.test(s)) out.browser = "Firefox";
  else if (/chrome\/|crios\//.test(s)) out.browser = "Chrome";
  else if (/safari\//.test(s) && /version\//.test(s)) out.browser = "Safari";

  return out;
}

/* ── 上报 ─────────────────────────────────────────────── */

async function collect(request, env) {
  const origin = request.headers.get("Origin") || "";
  const cors = corsHeaders(origin, env);

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: cors });
  }
  if (request.method !== "POST") {
    return new Response(null, { status: 405, headers: cors });
  }
  if (!origin || !allowList(env).includes(origin)) {
    return new Response(null, { status: 403, headers: cors });
  }

  let body;
  try {
    const text = await request.text();
    if (text.length > MAX_BODY) return new Response(null, { status: 413, headers: cors });
    body = JSON.parse(text);
  } catch {
    return new Response(null, { status: 400, headers: cors });
  }

  const now = Date.now();
  const cf = request.cf || {};
  const ip = request.headers.get("CF-Connecting-IP") || "";
  if (!ip) return new Response(null, { status: 204, headers: cors });

  let path = clean(body.p, 512) || "/";
  if (/^https?:\/\//i.test(path)) {
    try { path = new URL(path).pathname || "/"; } catch { path = "/"; }
  }

  const ua = clean(request.headers.get("User-Agent"), 512);
  const parsed = parseUA(ua);

  // 轻量防刷：同一 IP 每分钟最多 40 条，同一 IP + 页面 60 秒内只记一次
  try {
    const flood = await env.DB.prepare(
      "SELECT COUNT(*) AS c FROM hits WHERE ip = ? AND ts > ?"
    ).bind(ip, now - 60000).first();
    if (flood && flood.c >= 40) return new Response(null, { status: 204, headers: cors });

    const dup = await env.DB.prepare(
      "SELECT 1 AS x FROM hits WHERE ip = ? AND path = ? AND ts > ? LIMIT 1"
    ).bind(ip, path, now - 60000).first();
    if (dup) return new Response(null, { status: 204, headers: cors });
  } catch {
    // 查询失败也继续写，不因防刷丢掉真实访问
  }

  await env.DB.prepare(
    `INSERT INTO hits
       (ts, day, path, title, ref, ip, country, region, city, asn, org,
        ua, device, browser, os, lang, screen, tz, colo)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    now, dayKey(now), path, clean(body.t, 200),
    clean(body.r || request.headers.get("Referer"), 500),
    ip, clean(cf.country, 8), clean(cf.region, 60), clean(cf.city, 60),
    cf.asn ? Number(cf.asn) : null, clean(cf.asOrganization, 120),
    ua, parsed.device, parsed.browser, parsed.os,
    clean(body.l, 30), clean(body.s, 20), clean(body.z, 60), clean(cf.colo, 8)
  ).run();

  return new Response(null, { status: 204, headers: cors });
}

/* ── 后台鉴权 ─────────────────────────────────────────── */

async function isAuthed(request, env) {
  const v = getCookie(request, "s");
  if (!v) return false;
  const dot = v.lastIndexOf(".");
  if (dot < 0) return false;
  const exp = Number(v.slice(0, dot));
  if (!Number.isFinite(exp) || exp < Date.now()) return false;
  const expect = await sign(env, String(exp));
  return safeEqual(expect, v.slice(dot + 1));
}

function sessionCookie(value, maxAge) {
  return `s=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}

async function login(request, env) {
  let pwd = "";
  try {
    const text = await request.text();
    pwd = new URLSearchParams(text).get("pwd") || "";
  } catch {}
  if (!env.ADMIN_PASSWORD || !safeEqual(pwd, env.ADMIN_PASSWORD)) {
    return json({ ok: false, error: "口令不对" }, 401);
  }
  const exp = Date.now() + 7 * DAY_MS;
  const sig = await sign(env, String(exp));
  return json({ ok: true }, 200, {
    "Set-Cookie": sessionCookie(`${exp}.${sig}`, 7 * 24 * 3600),
  });
}

/* ── 查询 ─────────────────────────────────────────────── */

function validDay(s) {
  return /^\d{4}-\d{2}-\d{2}$/.test(s || "") ? s : "";
}

async function data(request, env, url) {
  if (!(await isAuthed(request, env))) return json({ ok: false, error: "unauthorized" }, 401);

  const today = dayKey(Date.now());
  let from = validDay(url.searchParams.get("from")) || dayKey(Date.now() - 29 * DAY_MS);
  let to = validDay(url.searchParams.get("to")) || today;
  if (from > to) [from, to] = [to, from];

  const q = clean(url.searchParams.get("q"), 100);
  const nobot = url.searchParams.get("nobot") === "1";
  const page = Math.max(1, parseInt(url.searchParams.get("page") || "1", 10) || 1);
  const limit = 50;
  const offset = (page - 1) * limit;

  const baseWhere = `day >= ? AND day <= ?${nobot ? " AND device <> 'bot'" : ""}`;
  const baseParams = [from, to];

  let rowWhere = baseWhere;
  const rowParams = [...baseParams];
  if (q) {
    rowWhere += " AND (ip LIKE ? OR path LIKE ? OR org LIKE ? OR city LIKE ? OR ua LIKE ? OR ref LIKE ?)";
    const like = `%${q}%`;
    rowParams.push(like, like, like, like, like, like);
  }

  const stmts = [
    env.DB.prepare(`SELECT COUNT(*) AS pv, COUNT(DISTINCT ip) AS uv FROM hits WHERE ${baseWhere}`).bind(...baseParams),
    env.DB.prepare(`SELECT COUNT(*) AS pv, COUNT(DISTINCT ip) AS uv FROM hits WHERE day = ?`).bind(today),
    env.DB.prepare(
      `SELECT day AS d, COUNT(*) AS pv, COUNT(DISTINCT ip) AS uv FROM hits
       WHERE ${baseWhere} GROUP BY day ORDER BY day`
    ).bind(...baseParams),
    env.DB.prepare(
      `SELECT path, COUNT(*) AS pv, COUNT(DISTINCT ip) AS uv FROM hits
       WHERE ${baseWhere} GROUP BY path ORDER BY pv DESC LIMIT 20`
    ).bind(...baseParams),
    env.DB.prepare(
      `SELECT ref, COUNT(*) AS pv FROM hits
       WHERE ${baseWhere} AND ref <> '' GROUP BY ref ORDER BY pv DESC LIMIT 40`
    ).bind(...baseParams),
    env.DB.prepare(
      `SELECT country, region, city, COUNT(*) AS pv, COUNT(DISTINCT ip) AS uv FROM hits
       WHERE ${baseWhere} GROUP BY country, region, city ORDER BY pv DESC LIMIT 24`
    ).bind(...baseParams),
    env.DB.prepare(
      `SELECT ip, COUNT(*) AS pv, MAX(ts) AS last, MAX(city) AS city, MAX(region) AS region,
              MAX(org) AS org, MAX(country) AS country, MAX(device) AS device
       FROM hits WHERE ${baseWhere} GROUP BY ip ORDER BY pv DESC LIMIT 20`
    ).bind(...baseParams),
    env.DB.prepare(
      `SELECT ts, day, path, title, ref, ip, country, region, city, asn, org,
              ua, device, browser, os, lang, screen, tz
       FROM hits WHERE ${rowWhere} ORDER BY ts DESC LIMIT ? OFFSET ?`
    ).bind(...rowParams, limit, offset),
    env.DB.prepare(`SELECT COUNT(*) AS c FROM hits WHERE ${rowWhere}`).bind(...rowParams),
  ];

  const [summary, todayRow, daily, pages, refs, places, ips, rows, total] = await env.DB.batch(stmts);
  const pick = (r) => (r && r.results ? r.results : []);

  return json({
    ok: true,
    range: { from, to, today },
    summary: pick(summary)[0] || { pv: 0, uv: 0 },
    today: pick(todayRow)[0] || { pv: 0, uv: 0 },
    daily: pick(daily),
    pages: pick(pages),
    refs: pick(refs),
    places: pick(places),
    ips: pick(ips),
    rows: pick(rows),
    total: (pick(total)[0] || { c: 0 }).c,
    page,
    limit,
  });
}

async function exportCsv(request, env, url) {
  if (!(await isAuthed(request, env))) return json({ ok: false, error: "unauthorized" }, 401);

  let from = validDay(url.searchParams.get("from")) || dayKey(Date.now() - 29 * DAY_MS);
  let to = validDay(url.searchParams.get("to")) || dayKey(Date.now());
  if (from > to) [from, to] = [to, from];

  const res = await env.DB.prepare(
    `SELECT ts, day, path, title, ref, ip, country, region, city, asn, org,
            device, browser, os, ua
     FROM hits WHERE day >= ? AND day <= ? ORDER BY ts DESC LIMIT 5000`
  ).bind(from, to).all();

  const cols = ["ts", "day", "path", "title", "ref", "ip", "country", "region", "city",
                "asn", "org", "device", "browser", "os", "ua"];
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const lines = [cols.join(",")];
  for (const r of res.results || []) {
    const row = { ...r, ts: new Date(r.ts + TZ_MS).toISOString().replace("T", " ").slice(0, 19) };
    lines.push(cols.map((c) => esc(row[c])).join(","));
  }
  const body = "﻿" + lines.join("\r\n"); // BOM 让 Excel 正确识别中文

  return new Response(body, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="ipowerbi-stats-${from}-${to}.csv"`,
      "Cache-Control": "no-store",
    },
  });
}

/* ── 入口 ─────────────────────────────────────────────── */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname.replace(/\/+$/, "") || "/";

    if (p === "/collect") return collect(request, env);
    if (p === "/admin") {
      return new Response(ADMIN_HTML, {
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-store",
          "X-Frame-Options": "DENY",
          "Referrer-Policy": "no-referrer",
          "Content-Security-Policy":
            "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; " +
            "connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        },
      });
    }
    if (p === "/admin/login" && request.method === "POST") return login(request, env);
    if (p === "/admin/logout" && request.method === "POST") {
      return json({ ok: true }, 200, { "Set-Cookie": sessionCookie("", 0) });
    }
    if (p === "/admin/api/data") return data(request, env, url);
    if (p === "/admin/api/export") return exportCsv(request, env, url);
    if (p === "/health") return new Response("ok");
    return new Response("Not found", { status: 404 });
  },
};
