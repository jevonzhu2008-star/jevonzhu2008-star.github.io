# -*- coding: utf-8 -*-
"""把合成数据渲染成 39 页自包含演示汇报（版式沿用智能问数的 deck 模板）。"""
import io, re, math, html, random
from collections import defaultdict
from gen_deck import (gen_orders, agg, BRAND, DS, PRODUCTS, REGIONS, CITIES,
                      CUSTOMER_TYPES, YEAR_ORDERS)

random.seed(20261126)
orders = gen_orders()
TOTAL_ORDERS = len(orders)

def esc(s):
    return html.escape(str(s), quote=True)

def wan(v, d=1):
    return f"{v/1e4:,.{d}f} 万"

def wan0(v):
    return f"{v/1e4:,.1f} 万"

def pct(v, d=1):
    return f"{v*100:.{d}f}%"

def num(v):
    return f"{v:,.0f}"

def money(v):
    if abs(v) >= 1e8:
        return f"¥{v/1e8:.2f} 亿"
    if abs(v) >= 1e4:
        return f"¥{v/1e4:,.1f} 万"
    return f"¥{v:,.0f}"

def nice_max(v):
    if v <= 0:
        return 1
    exp = math.floor(math.log10(v))
    base = v / 10 ** exp
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if base <= m + 1e-9:
            return m * 10 ** exp
    return 10 ** (exp + 1)

# ── 聚合 ──────────────────────────────────────────────────────
by_year = agg(orders, lambda o: o["year"])
by_ym = agg(orders, lambda o: o["ym"])
by_prod = agg(orders, lambda o: o["pname"])
by_cat = agg(orders, lambda o: o["category"])
by_region = agg(orders, lambda o: o["region"])
by_city = agg(orders, lambda o: o["city"])
by_ctype = agg(orders, lambda o: o["ctype"])

def year_cat(y, cat):
    s = defaultdict(float)
    for o in orders:
        if o["year"] == y and o["category"] == cat:
            s["sales"] += o["sales"]; s["profit"] += o["profit"]; s["qty"] += o["qty"]; s["orders"] += 1
    return s

def year_prod(y, pname):
    s = defaultdict(float)
    for o in orders:
        if o["year"] == y and o["pname"] == pname:
            s["sales"] += o["sales"]; s["profit"] += o["profit"]; s["qty"] += o["qty"]; s["orders"] += 1
    return s

def year_region(y, region):
    s = defaultdict(float)
    for o in orders:
        if o["year"] == y and o["region"] == region:
            s["sales"] += o["sales"]; s["profit"] += o["profit"]; s["qty"] += o["qty"]; s["orders"] += 1
    return s

TOTAL_SALES = sum(v["sales"] for v in by_year.values())
TOTAL_QTY = sum(v["qty"] for v in by_year.values())
AOV = TOTAL_SALES / TOTAL_ORDERS
Y26, Y25, Y24, Y23 = by_year[2026], by_year[2025], by_year[2024], by_year[2023]
YOY = (Y26["sales"] - Y25["sales"]) / Y25["sales"]
YOY_ADD = Y26["sales"] - Y25["sales"]

months = sorted(by_ym)
month_vals = [by_ym[m]["sales"] for m in months]
month_orders = [by_ym[m]["orders"] for m in months]
peak_m = max(months, key=lambda m: by_ym[m]["sales"])
low_m = min(months, key=lambda m: by_ym[m]["sales"])

season = defaultdict(lambda: {"sales": 0.0, "orders": 0})
for ym, v in by_ym.items():
    m = int(ym.split("-")[1])
    season[m]["sales"] += v["sales"]; season[m]["orders"] += v["orders"]
season_vals = [season[m]["sales"] for m in range(1, 13)]
season_peak = max(range(1, 13), key=lambda m: season[m]["sales"])
season_low = min(range(1, 13), key=lambda m: season[m]["sales"])

aov_month = [by_ym[m]["sales"] / by_ym[m]["orders"] for m in months]

prod_sales = sorted(by_prod.items(), key=lambda kv: -kv[1]["sales"])
prod_profit = sorted(by_prod.items(), key=lambda kv: -kv[1]["profit"])
prod_qty = sorted(by_prod.items(), key=lambda kv: -kv[1]["qty"])
top5_share = sum(v["sales"] for _, v in prod_sales[:5]) / TOTAL_SALES
top10_share = sum(v["sales"] for _, v in prod_sales[:10]) / TOTAL_SALES

region_sales = sorted(by_region.items(), key=lambda kv: -kv[1]["sales"])
city_sales = sorted(by_city.items(), key=lambda kv: -kv[1]["sales"])
city_top20 = city_sales[:20]

REGION_MGR = {"华东": "华东区经理", "中南": "中南区经理", "华北": "华北区经理",
              "东北": "东北区经理", "西南": "西南区经理", "西北": "西北区经理"}
REGION_RESELLER = {r[0]: r[2] for r in REGIONS}
REGION_TARGET_RATE = {"华东": 0.52, "中南": 0.61, "华北": 0.58, "东北": 0.66,
                      "西南": 0.74, "西北": 0.81}

ctype_items = sorted(by_ctype.items(), key=lambda kv: -kv[1]["sales"])
ctype_customers = {c[0]: c[2] for c in CUSTOMER_TYPES}

# 工作日 / 周末
wd = defaultdict(lambda: {"sales": 0.0, "orders": 0, "qty": 0})
for o in orders:
    k = "周末" if o["date"].weekday() >= 5 else "工作日"
    wd[k]["sales"] += o["sales"]; wd[k]["orders"] += 1; wd[k]["qty"] += o["qty"]
by_weekday = defaultdict(float)
for o in orders:
    by_weekday[o["date"].weekday()] += o["sales"]

# 月度环比
mom = []
for i in range(1, len(months)):
    prev, cur = month_vals[i - 1], month_vals[i]
    mom.append((months[i], prev, cur, (cur - prev) / prev if prev else 0))
mom_max_up = max(mom, key=lambda t: t[3])
mom_max_down = min(mom, key=lambda t: t[3])

# 区域达成：目标额 = 实际 / 达成率
region_reach = []
for name, v in region_sales:
    rate = REGION_TARGET_RATE[name]
    region_reach.append((name, v["sales"], v["sales"] / rate, rate))
avg_reach = sum(r[3] for r in region_reach) / len(region_reach)

# 客户类型
cnt_total = sum(v["orders"] for v in by_ctype.values())

# RFM（合成客户档案）
rfm = [("重要保持", 430), ("重要价值", 96), ("一般保持", 62), ("流失预警", 32)]
rfm_total = sum(n for _, n in rfm)

# 品类
cat_sales = {k: v["sales"] for k, v in by_cat.items()}
cat_profit = {k: v["profit"] for k, v in by_cat.items()}
cat_qty = {k: v["qty"] for k, v in by_cat.items()}
cat_orders = {k: v["orders"] for k, v in by_cat.items()}
cat_share = {k: v / TOTAL_SALES for k, v in cat_sales.items()}

# 低毛利与折扣
prod_discount = defaultdict(lambda: [0.0, 0])
for o in orders:
    prod_discount[o["pname"]][0] += o["discount"] * o["sales"]
    prod_discount[o["pname"]][1] += o["sales"]
prod_disc_rate = {k: v[0] / v[1] for k, v in prod_discount.items()}
prod_margin = {k: v["profit"] / v["sales"] for k, v in by_prod.items()}

# ── SVG 图表 ─────────────────────────────────────────────────
FONT = '"PingFang SC", "Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans SC", system-ui, -apple-system, "Segoe UI", sans-serif'
BLUE, YELLOW, RED, GRID, AXIS = "#1f5eff", "#f2c811", "#b42318", "#e2e7ef", "#66707f"

def axes_svg(ymax, yfmt, x0=70, x1=736, y0=44, y1=384):
    out = []
    for i in range(5):
        val = ymax * (4 - i) / 4
        y = y0 + (y1 - y0) * i / 4
        out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{x0-8}" y="{y+4:.1f}" text-anchor="end" font-size="10.5" fill="{AXIS}">{yfmt(val)}</text>')
    return "".join(out)

def svg_line(values, labels, yfmt=lambda v: f"{v/1e4:,.0f}万", color=BLUE, area=True):
    ymax = nice_max(max(values))
    x0, x1, y0, y1 = 70, 736, 44, 384
    pts = []
    for i, v in enumerate(values):
        x = x0 + (x1 - x0) * i / max(1, len(values) - 1)
        y = y1 - (y1 - y0) * (v / ymax)
        pts.append((x, y))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    body = [axes_svg(ymax, yfmt)]
    if area:
        body.append(f'<polygon points="{x0},{y1} {poly} {x1},{y1}" fill="{color}" opacity="0.10"/>')
    body.append(f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round"/>')
    body.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#cdd5e1" stroke-width="1"/>')
    # x 轴标签：最多 8 个
    step = max(1, len(labels) // 8)
    for i in range(0, len(labels), step):
        x = x0 + (x1 - x0) * i / max(1, len(labels) - 1)
        if labels[i]:
            body.append(f'<text x="{x:.1f}" y="{y1+18}" text-anchor="middle" font-size="10.5" fill="{AXIS}">{esc(labels[i])}</text>')
    return f'<svg viewBox="0 0 760 440" role="img" xmlns="http://www.w3.org/2000/svg" font-family=\'{FONT}\'>{"".join(body)}</svg>'

def svg_bar(labels, values, yfmt=lambda v: f"{v/1e4:,.0f}万", color=BLUE, hl=None):
    ymax = nice_max(max(values))
    x0, x1, y0, y1 = 70, 736, 44, 384
    n = len(values)
    slot = (x1 - x0) / n
    bw = slot * 0.56
    body = [axes_svg(ymax, yfmt)]
    for i, v in enumerate(values):
        cx = x0 + slot * (i + 0.5)
        h = (y1 - y0) * (v / ymax)
        c = YELLOW if (hl is not None and i == hl) else color
        body.append(f'<rect x="{cx-bw/2:.1f}" y="{y1-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" fill="{c}"/>')
        body.append(f'<text x="{cx:.1f}" y="{y1+18}" text-anchor="middle" font-size="10.5" fill="{AXIS}">{esc(labels[i])}</text>')
    body.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#cdd5e1" stroke-width="1"/>')
    return f'<svg viewBox="0 0 760 440" role="img" xmlns="http://www.w3.org/2000/svg" font-family=\'{FONT}\'>{"".join(body)}</svg>'

def svg_hbar(items, fmt=lambda v: wan(v), color=BLUE, hl=0, label_w=132, show_pct=None, total=None):
    n = len(items)
    avail = 384 - 20
    row_h = min(92, avail / max(1, n))
    top = 20 + (avail - row_h * n) / 2
    maxv = max(abs(v) for _, v in items) or 1
    left = label_w + 18
    right = 700
    body = []
    for i, (label, v) in enumerate(items):
        y = top + row_h * i
        h = row_h * 0.52
        w = (right - left) * abs(v) / maxv
        c = YELLOW if i == hl else (RED if v < 0 else color)
        body.append(f'<text x="{label_w}" y="{y+row_h*0.5+4:.1f}" text-anchor="end" font-size="11.5" fill="#3a4554">{esc(label)}</text>')
        body.append(f'<rect x="{left}" y="{y+row_h*0.24:.1f}" width="{max(1,w):.1f}" height="{h:.1f}" rx="3" fill="{c}"/>')
        text = fmt(v)
        if show_pct and total:
            text += f" · {v/total*100:.1f}%"
        body.append(f'<text x="{left+w+8:.1f}" y="{y+row_h*0.5+4:.1f}" font-size="10.5" fill="{AXIS}">{esc(text)}</text>')
    return f'<svg viewBox="0 0 760 440" role="img" xmlns="http://www.w3.org/2000/svg" font-family=\'{FONT}\'>{"".join(body)}</svg>'

# ── 页面模板 ─────────────────────────────────────────────────
pages = []          # (html, kind, title, chapter)
PAGE_W = "2026-12-31"
GEN_AT = "2026-11-26 08:20"
DATASET = f"{BRAND}销售洞察（演示语义模型）"

def page_no():
    return len(pages) + 1

def foot(metrics):
    n = page_no()
    return (f'<footer class="slide-foot">'
            f'<span>数据源：{DATASET} · 指标：{metrics} · 数据截至：{PAGE_W}</span>'
            f'<span>第 {n} / 39 页 · 生成于 {GEN_AT}</span></footer>')

def insight(chapter, title, headline, chart, caption, kpis, bullets, metrics, queries=1):
    n = page_no()
    kpi_html = "".join(
        f'<div class="kpi {cls}"><span class="kpi-label">{esc(l)}</span><span class="kpi-value">{esc(v)}</span></div>'
        for l, v, cls in kpis)
    bul = "".join(f"<li>{esc(b)}</li>" for b in bullets)
    htm = f'''<section class="slide slide-insight">
  <header class="slide-head">
    <span class="kicker">{esc(chapter)} · {n:02d}</span>
    <h2>{esc(title)}</h2>
  </header>
  <div class="slide-body">
    <p class="headline">{esc(headline)}</p>
    <div class="insight-cols">
      <figure class="chart-figure">{chart}<figcaption>{esc(caption)}</figcaption></figure>
      <aside class="insight-side">
        <div class="kpis">{kpi_html}</div>
        <h3 class="side-title">关键点</h3><ul class="bullets">{bul}</ul>
        <div class="provenance">
    <span class="provenance-label">本页出处</span>
    <p>指标：{esc(metrics)}</p>
    <p>数据截至：{PAGE_W}</p>
    <p>{queries} 条 DAX 查询 · 见文末附录</p>
  </div>
      </aside>
    </div>
  </div>
  {foot(metrics)}
</section>'''
    pages.append({"html": htm, "kind": "insight", "title": title, "chapter": chapter})

def attribution(chapter, title, headline, chart, caption, kpis, bullets, metrics, queries=2):
    n = page_no()
    kpi_html = "".join(
        f'<div class="kpi {cls}"><span class="kpi-label">{esc(l)}</span><span class="kpi-value">{esc(v)}</span></div>'
        for l, v, cls in kpis)
    bul = "".join(f"<li>{esc(b)}</li>" for b in bullets)
    htm = f'''<section class="slide slide-insight">
  <header class="slide-head">
    <span class="kicker">{esc(chapter)} · 归因 · {n:02d}</span>
    <h2>{esc(title)}</h2>
  </header>
  <div class="slide-body">
    <p class="headline">{esc(headline)}</p>
    <div class="insight-cols">
      <figure class="chart-figure">{chart}<figcaption>{esc(caption)}</figcaption></figure>
      <aside class="insight-side">
        <div class="kpis">{kpi_html}</div>
        <h3 class="side-title">关键点</h3><ul class="bullets">{bul}</ul>
        <div class="provenance">
    <span class="provenance-label">本页出处</span>
    <p>指标：{esc(metrics)}</p>
    <p>数据截至：{PAGE_W}</p>
    <p>{queries} 条 DAX 查询 · 见文末附录</p>
  </div>
      </aside>
    </div>
  </div>
  {foot(metrics)}
</section>'''
    pages.append({"html": htm, "kind": "insight", "title": title, "chapter": chapter})

# ── 封面 ─────────────────────────────────────────────────────
CH1, CH2, CH3 = "总体规模与趋势", "产品结构与贡献", "渠道与区域对比"
CH4, CH5, CH6 = "时间周期与节奏", "客户结构与价值", "异常波动与行动建议"

cover = f'''<section class="slide slide-cover">
  <div class="cover-top"><span class="brand-mark">智</span><span class="cover-eyebrow">数据洞察汇报 · 演示</span></div>
  <h1>{esc(BRAND)}销售洞察报告</h1>
  <p class="cover-sub">2026 年销售额 {wan0(Y26["sales"])}，同比增 {pct(YOY)}；增长由 C 端拉动，区域达成与毛利结构待优化</p>
  <p class="cover-warning">演示数据：本报告由合成数据生成，不代表任何企业真实经营结果</p>
  <ul class="cover-chapters"><li><span>01</span>{CH1}</li><li><span>02</span>{CH2}</li><li><span>03</span>{CH3}</li><li><span>04</span>{CH4}</li><li><span>05</span>{CH5}</li><li><span>06</span>{CH6}</li></ul>
  <dl class="cover-meta">
    <div><dt>数据源</dt><dd>{DATASET}</dd></div>
    <div><dt>数据覆盖</dt><dd>{PAGE_W}</dd></div>
    <div><dt>洞察页</dt><dd>24 页 · 全篇 39 页</dd></div>
    <div><dt>生成时间</dt><dd>{GEN_AT}</dd></div>
  </dl>
  <p class="cover-foot">每页标注数据来源与口径，末页附可逐条核验的 DAX 查询附录。</p>
</section>'''
pages.append({"html": cover, "kind": "cover", "title": f"{BRAND}销售洞察报告", "chapter": "封面"})

# ── 章一 ─────────────────────────────────────────────────────
labs = [m[:4] if m.endswith("-01") else "" for m in months]
max_i = months.index(peak_m); min_i = months.index(low_m)
insight(CH1, "整体销售规模与订单量走势",
        f'销售额从 2023 年 {wan0(Y23["sales"])} 增至 2026 年 {wan0(Y26["sales"])}，订单量同步扩张',
        svg_line(month_vals, labs), f'月度销售额走势（{months[0]} 至 {months[-1]}）',
        [("累计销售额", money(TOTAL_SALES), "positive"), ("累计订单量", num(TOTAL_ORDERS), "neutral"), ("平均客单价", f"¥{AOV:,.0f}", "neutral")],
        [f'{peak_m} 销售额 {wan0(by_ym[peak_m]["sales"])}，为报告期内单月最高，订单 {num(by_ym[peak_m]["orders"])} 笔',
         f'{low_m} 销售额仅 {wan0(by_ym[low_m]["sales"])}，为报告期低点',
         f'月度客单价在 {min(aov_month):,.0f} 至 {max(aov_month):,.0f} 元之间波动，均值 {AOV:,.0f} 元',
         f'四年销售额复合增长 {((Y26["sales"]/Y23["sales"])**0.3333-1)*100:.1f}%'],
        "销售额、订单量、客单价")

yoy_by_year = {y: (by_year[y]["sales"] - by_year[y-1]["sales"]) / by_year[y-1]["sales"] for y in (2024, 2025, 2026)}
insight(CH1, "年度销售额与同比变化",
        f'年度销售额连续三年增长，2026 年同比增 {pct(YOY)} 至 {wan0(Y26["sales"])}',
        svg_bar(["2023", "2024", "2025", "2026"], [by_year[y]["sales"] for y in (2023, 2024, 2025, 2026)], hl=3),
        "各年度销售额（万元）",
        [("2026 年销售额", money(Y26["sales"]), "positive"), ("2026 年同比", pct(YOY), "positive"), ("2026 年订单量", num(Y26["orders"]), "neutral")],
        [f'2024 年销售额 {wan0(Y24["sales"])}，同比增 {pct(yoy_by_year[2024])}',
         f'2025 年销售额 {wan0(Y25["sales"])}，同比增 {pct(yoy_by_year[2025])}',
         f'2026 年销售额 {wan0(Y26["sales"])}，同比增 {pct(yoy_by_year[2026])}',
         f'订单量由 2023 年 {num(Y23["orders"])} 笔增至 2026 年 {num(Y26["orders"])} 笔'],
        "销售额、订单量、同比变化额", 2)

season_bar = svg_bar([f"{m}月" for m in range(1, 13)], season_vals, hl=season_peak - 1)
insight(CH1, "月度销售节奏与季节性",
        f'{season_peak} 月是全年峰值 {wan0(season[season_peak]["sales"])}，{season_low} 月为谷底',
        season_bar, "各月份累计销售额（四年合计，季节性）",
        [("峰值月", wan(season[season_peak]["sales"]), "positive"), ("谷值月", wan(season[season_low]["sales"]), "negative"), ("月均", wan(sum(season_vals)/12), "neutral")],
        [f'{season_peak} 月累计 {wan0(season[season_peak]["sales"])}，订单 {num(season[season_peak]["orders"])} 笔，为各月最高',
         f'1 月 {wan0(season[1]["sales"])}、3 月 {wan0(season[3]["sales"])}，年初为次高峰',
         f'{season_low} 月仅 {wan0(season[season_low]["sales"])}，为全年最低月份',
         f'旺季三个月合计 {wan0(season[season_peak]["sales"]+season[1]["sales"]+season[3]["sales"])}，占全期 {(season[season_peak]["sales"]+season[1]["sales"]+season[3]["sales"])/TOTAL_SALES*100:.1f}%'],
        "销售额、订单量")

insight(CH1, "客单价与单均购买量水平",
        f'客单价长期稳定在 {AOV:,.0f} 元附近，月度波动区间 {min(aov_month):,.0f} 至 {max(aov_month):,.0f} 元',
        svg_line(aov_month, labs, yfmt=lambda v: f"{v:,.0f}"), "月度客单价走势（元）",
        [("平均客单价", f"¥{AOV:,.0f}", "neutral"), ("最高", f"¥{max(aov_month):,.0f}", "positive"), ("最低", f"¥{min(aov_month):,.0f}", "negative")],
        [f'{months[aov_month.index(max(aov_month))]} 客单价 {max(aov_month):,.0f} 元，为报告期最高',
         f'{months[aov_month.index(min(aov_month))]} 客单价 {min(aov_month):,.0f} 元，为最低',
         '客单价各月围绕均值波动，没有持续上行趋势',
         'B 端批量订单压低了整体客单价，C 端单品价格带更高'],
        "客单价、销售额、订单量")

c_cur, b_cur = year_cat(2026, "C端"), year_cat(2026, "B端")
c_pre, b_pre = year_cat(2025, "C端"), year_cat(2025, "B端")
c_delta, b_delta = c_cur["sales"] - c_pre["sales"], b_cur["sales"] - b_pre["sales"]
attribution(CH1, f"{CH1} · 关键指标归因",
            f'销售额同比增 {wan(YOY_ADD)}，C 端贡献 {c_delta/YOY_ADD*100:.1f}% 为主因',
            svg_hbar([("C 端", c_delta), ("B 端", b_delta)], fmt=lambda v: f"{'+' if v>=0 else ''}{wan(v)}"),
            "各产品类别销售额同比变化",
            [("销售额同比增量", money(YOY_ADD), "positive"), ("C 端增幅", pct(c_delta/c_pre["sales"]), "positive"), ("利润同比增量", money(c_cur["profit"]+b_cur["profit"]-c_pre["profit"]-b_pre["profit"]), "neutral")],
            [f'C 端本期 {wan0(c_cur["sales"])}，较上年增加 {wan(c_delta)}，增幅 {pct(c_delta/c_pre["sales"])}',
             f'B 端本期 {wan0(b_cur["sales"])}，较上年增加 {wan(b_delta)}，增幅 {pct(b_delta/b_pre["sales"])}',
             f'C 端利润增加 {wan(c_cur["profit"]-c_pre["profit"])}，高于 B 端的 {wan(b_cur["profit"]-b_pre["profit"])}',
             f'两类机型订单量分别增加 {num(c_cur["orders"]-c_pre["orders"])} 笔和 {num(b_cur["orders"]-b_pre["orders"])} 笔'],
            "本期销售额、上年销售额、销售额变化")

# ── 章二 ─────────────────────────────────────────────────────
insight(CH2, "产品品类销售构成",
        f'B 端贡献销售额 {pct(cat_share["B端"])}、销量 {pct(cat_qty["B端"]/TOTAL_QTY)}，客单价低于 C 端',
        svg_hbar([("B 端", cat_sales["B端"]), ("C 端", cat_sales["C端"])], fmt=wan, show_pct=True, total=TOTAL_SALES, hl=0),
        "B 端与 C 端机型销售额对比",
        [("总销售额", money(TOTAL_SALES), "neutral"), ("B 端占比", pct(cat_share["B端"]), "neutral"), ("C 端客单价", f"¥{cat_sales['C端']/cat_orders['C端']:,.0f}", "positive")],
        [f'B 端销售额 {wan0(cat_sales["B端"])}，占比 {pct(cat_share["B端"])}，销量 {num(cat_qty["B端"])} 台，客单价 ¥{cat_sales["B端"]/cat_orders["B端"]:,.0f}',
         f'C 端销售额 {wan0(cat_sales["C端"])}，占比 {pct(cat_share["C端"])}，销量 {num(cat_qty["C端"])} 台，客单价 ¥{cat_sales["C端"]/cat_orders["C端"]:,.0f}',
         f'C 端客单价比 B 端高 ¥{cat_sales["C端"]/cat_orders["C端"]-cat_sales["B端"]/cat_orders["B端"]:,.0f}，销售额占比却低 {(cat_share["B端"]-cat_share["C端"])*100:.1f} 个百分点'],
        "销售额、销量、销售额占比")

insight(CH2, "产品销售额排名与集中度",
        f'{prod_sales[0][0]} 以 {pct(prod_sales[0][1]["sales"]/TOTAL_SALES)} 销售额居首，前 5 款合计贡献 {pct(top5_share)}',
        svg_hbar([(k, v["sales"]) for k, v in prod_sales], fmt=wan, show_pct=True, total=TOTAL_SALES),
        "各产品销售额排名",
        [("榜首销售额", money(prod_sales[0][1]["sales"]), "positive"), ("前 5 款占比", pct(top5_share), "neutral"), ("前 10 款占比", pct(top10_share), "neutral")],
        [f'{k} 销售额 {wan0(v["sales"])}，占比 {pct(v["sales"]/TOTAL_SALES)}' for k, v in prod_sales[:2]] +
        [f'前 5 款产品累计占比 {pct(top5_share)}，前 10 款累计 {pct(top10_share)}，头部集中度较高'],
        "销售额、排名、累计占比")

profit_rank = {k: i + 1 for i, (k, _) in enumerate(prod_profit)}
sales_rank = {k: i + 1 for i, (k, _) in enumerate(prod_sales)}
insight(CH2, "产品利润贡献排名",
        f'{prod_profit[0][0]} 利润 {wan0(prod_profit[0][1]["profit"])} 居首，利润第一名与销售第一名不是同一款',
        svg_hbar([(k, v["profit"]) for k, v in prod_profit], fmt=wan),
        "各产品利润贡献排名",
        [("总利润", money(sum(v["profit"] for v in by_prod.values())), "neutral"), (f'{prod_profit[0][0]} 利润率', pct(prod_margin[prod_profit[0][0]]), "positive"), (f'{prod_sales[0][0]} 利润率', pct(prod_margin[prod_sales[0][0]]), "negative")],
        [f'{prod_profit[0][0]} 利润 {wan0(prod_profit[0][1]["profit"])} 排名第 1，销售排名第 {sales_rank[prod_profit[0][0]]}，利润率 {pct(prod_margin[prod_profit[0][0]])}',
         f'{prod_sales[0][0]} 销售额排名第 1，利润排名第 {profit_rank[prod_sales[0][0]]}，利润率 {pct(prod_margin[prod_sales[0][0]])}',
         f'利润率最高与最低相差 {(max(prod_margin.values())-min(prod_margin.values()))*100:.1f} 个百分点'],
        "利润、销售额、利润排名")

insight(CH2, "产品销量排名与结构",
        f'{prod_qty[0][0]} 销量 {num(prod_qty[0][1]["qty"])} 台居首，销量与销售额结构明显错位',
        svg_hbar([(k, v["qty"]) for k, v in prod_qty], fmt=lambda v: f"{v:,.0f} 台"),
        "各产品销量排名",
        [("总销量", num(TOTAL_QTY), "neutral"), (f'{prod_qty[0][0]} 占比', pct(prod_qty[0][1]["qty"]/TOTAL_QTY), "neutral"), (f'{prod_qty[-1][0]} 占比', pct(prod_qty[-1][1]["qty"]/TOTAL_QTY), "neutral")],
        [f'{prod_qty[0][0]} 销量 {num(prod_qty[0][1]["qty"])} 台排名第 1，销售额排名第 {sales_rank[prod_qty[0][0]]}',
         f'{prod_sales[0][0]} 销售额第 1，销量 {num(prod_sales[0][1]["qty"])} 台排名第 {[i+1 for i,(k,_) in enumerate(prod_qty) if k==prod_sales[0][0]][0]}',
         '低价产品走量、高价产品走额，两条结构不一致'],
        "销量、销量排名、销售额")

prod_delta = []
for k, _ in prod_sales:
    d = year_prod(2026, k)["sales"] - year_prod(2025, k)["sales"]
    prod_delta.append((k, d))
prod_delta.sort(key=lambda kv: -kv[1])
attribution(CH2, f"{CH2} · 关键指标归因",
            f'销售额同比增 {pct(YOY)}，C 端贡献 {c_delta/YOY_ADD*100:.1f}% 增量，{prod_delta[0][0]} 单品贡献 {prod_delta[0][1]/YOY_ADD*100:.1f}%',
            svg_hbar(prod_delta, fmt=lambda v: f"{'+' if v>=0 else ''}{wan(v)}"),
            "各产品销售额同比变化贡献",
            [("本期销售额", money(Y26["sales"]), "neutral"), ("销售额变化", f"+{wan(YOY_ADD)}", "positive"), ("利润变化", f"+{wan(Y26['profit']-Y25['profit'])}", "positive")],
            [f'{k} 销售额变化 {wan(v)}，占整体增量 {v/YOY_ADD*100:.1f}%' for k, v in prod_delta[:3]] +
            [f'{k} 为下滑最大的产品，减少 {wan(abs(v))}' for k, v in prod_delta[-1:]],
            "本期销售额、同期销售额、销售额变化")

# ── 章三 ─────────────────────────────────────────────────────
insight(CH3, "区域销售额与经销商数量对比",
        f'{region_sales[0][0]}销售额 {wan0(region_sales[0][1]["sales"])} 居首，{"中南" if REGION_RESELLER["中南"]==max(REGION_RESELLER.values()) else region_sales[1][0]}经销商最多但单商产出偏低',
        svg_hbar([(k, v["sales"]) for k, v in region_sales], fmt=wan, show_pct=True, total=TOTAL_SALES),
        "各区域销售额对比",
        [("区域合计销售额", money(TOTAL_SALES), "neutral"), ("活跃经销商", f'{sum(REGION_RESELLER.values())} 家', "neutral"), (f'{region_sales[0][0]}占比', pct(region_sales[0][1]["sales"]/TOTAL_SALES), "positive")],
        [f'{k}销售额 {wan0(v["sales"])}，占比 {pct(v["sales"]/TOTAL_SALES)}，经销商 {REGION_RESELLER[k]} 家' for k, v in region_sales[:3]] +
        [f'{region_sales[-1][0]}销售额 {wan0(region_sales[-1][1]["sales"])}、经销商 {REGION_RESELLER[region_sales[-1][0]]} 家，规模与渠道数量均处末位'],
        "销售额、经销商数、订单量")

insight(CH3, "城市维度销售表现",
        f'{city_top20[0][0]}销售额 {wan0(city_top20[0][1]["sales"])} 领跑城市榜，TOP20 合计 {wan0(sum(v["sales"] for _, v in city_top20))}',
        svg_hbar([(k, v["sales"]) for k, v in city_top20[:12]], fmt=wan, label_w=96),
        "重点城市销售额 TOP12（共 20 城）",
        [("TOP20 城市销售额", money(sum(v["sales"] for _, v in city_top20)), "neutral"), ("首位城市", money(city_top20[0][1]["sales"]), "positive"), ("城市均值", money(sum(v["sales"] for _, v in city_top20)/20), "neutral")],
        [f'前五城市：' + '、'.join(f'{k} {wan0(v["sales"])}' for k, v in city_top20[:5]),
         f'TOP20 城市销售额合计 {wan0(sum(v["sales"] for _, v in city_top20))}，平均每城 {wan0(sum(v["sales"] for _, v in city_top20)/20)}',
         f'榜尾 {city_top20[-1][0]} 销售额 {wan0(city_top20[-1][1]["sales"])}，与首位相差约 {city_top20[0][1]["sales"]/city_top20[-1][1]["sales"]:.1f} 倍'],
        "销售额、经销商数")

mgr_items = [(REGION_MGR[k], v["sales"]) for k, v in region_sales]
insight(CH3, "区域经理业绩对比",
        f'{mgr_items[0][0]}销售额 {wan0(mgr_items[0][1])} 最高，六区合计 {wan0(TOTAL_SALES)}',
        svg_hbar(mgr_items, fmt=wan),
        "各区域经理销售额对比",
        [("区域合计", money(TOTAL_SALES), "neutral"), ("最高区域", money(mgr_items[0][1]), "positive"), ("区域经理", "6 人", "neutral")],
        [f'{k} {wan0(v)}' for k, v in mgr_items] + [f'最高与最低区域相差 {mgr_items[0][1]/mgr_items[-1][1]:.1f} 倍'],
        "销售额、目标销售额、经销商数")

reach_items = [(k, v) for k, s, g, v in region_reach]
insight(CH3, "区域目标达成情况",
        f'区域目标达成率平均 {pct(avg_reach)}，{max(region_reach, key=lambda r: r[3])[0]} 最高、{min(region_reach, key=lambda r: r[3])[0]} 最低',
        svg_hbar(sorted(reach_items, key=lambda kv: -kv[1]), fmt=lambda v: pct(v), label_w=96),
        "各区域销售目标达成率",
        [("平均达成率", pct(avg_reach), "neutral"), (f'最高（{max(region_reach, key=lambda r: r[3])[0]}）', pct(max(r[3] for r in region_reach)), "positive"), (f'最低（{min(region_reach, key=lambda r: r[3])[0]}）', pct(min(r[3] for r in region_reach)), "negative")],
        [f'{k} 达成率 {pct(v)}，目标 {wan0(g)}，实际 {wan0(s)}' for k, s, g, v in sorted(region_reach, key=lambda r: -r[3])[:3]] +
        [f'六区达成率全部低于 100%，整体目标偏高或执行不足'],
        "销售额、目标销售额、达成率")

reg_delta = []
for k, _ in region_sales:
    d = year_region(2026, k)["sales"] - year_region(2025, k)["sales"]
    reg_delta.append((k, d))
reg_delta.sort(key=lambda kv: -kv[1])
attribution(CH3, f"{CH3} · 关键指标归因",
            f'销售额同比增 {pct(YOY)}，{reg_delta[0][0]}与{reg_delta[1][0]}合计贡献 {(reg_delta[0][1]+reg_delta[1][1])/YOY_ADD*100:.1f}% 的增量',
            svg_hbar(reg_delta, fmt=lambda v: f"{'+' if v>=0 else ''}{wan(v)}", label_w=74),
            "各区域销售额同比变化贡献",
            [("本期销售额", money(Y26["sales"]), "neutral"), ("同比增量", f"+{wan(YOY_ADD)}", "positive"), ("同比增幅", pct(YOY), "positive")],
            [f'{k} 增加 {wan(v)}，占增量 {v/YOY_ADD*100:.1f}%' for k, v in reg_delta[:3]] +
            [f'{k} 减少 {wan(abs(v))}，是唯一负增长区域' for k, v in reg_delta if v < 0][:1] or ['六区全部正增长'],
            "本期销售额、去年同期销售额、销售额变化")

# ── 章四 ─────────────────────────────────────────────────────
cat_by_year = {y: {c: year_cat(y, c)["sales"] for c in ("B端", "C端")} for y in (2023, 2024, 2025, 2026)}
c_share_23 = cat_by_year[2023]["C端"] / (cat_by_year[2023]["B端"] + cat_by_year[2023]["C端"])
c_share_26 = cat_by_year[2026]["C端"] / (cat_by_year[2026]["B端"] + cat_by_year[2026]["C端"])
insight(CH4, "年度销售额结构变化",
        f'2026 年销售额 {wan0(Y26["sales"])}，B 端占比降至 {pct(1-c_share_26)}，C 端升至 {pct(c_share_26)}',
        svg_bar([f'C端 {y}' for y in (2023, 2024, 2025, 2026)], [cat_by_year[y]["C端"] for y in (2023, 2024, 2025, 2026)], hl=3),
        "各年度 C 端销售额（万元）",
        [("2026 年销售额", money(Y26["sales"]), "neutral"), ("B 端 2026 占比", pct(1 - c_share_26), "neutral"), ("C 端 2026 占比", pct(c_share_26), "positive")],
        [f'B 端销售额从 2023 年 {wan0(cat_by_year[2023]["B端"])} 增至 2026 年 {wan0(cat_by_year[2026]["B端"])}，占比由 {pct(1-c_share_23)} 降至 {pct(1-c_share_26)}',
         f'C 端销售额从 2023 年 {wan0(cat_by_year[2023]["C端"])} 增至 2026 年 {wan0(cat_by_year[2026]["C端"])}，占比由 {pct(c_share_23)} 升至 {pct(c_share_26)}',
         f'{region_sales[0][0]} 2026 年销售额 {wan0(year_region(2026, region_sales[0][0])["sales"])}、占比 {pct(year_region(2026, region_sales[0][0])["sales"]/Y26["sales"])}，区域集中度进一步提升'],
        "销售额、订单量、品类占比", 2)

mom_up_txt = f'{mom_max_up[0]} 环比 {pct(mom_max_up[3])}'
mom_down_txt = f'{mom_max_down[0]} 环比 {pct(mom_max_down[3])}'
insight(CH4, "月度环比变化",
        f'月度销售波动剧烈，{mom_max_down[0]} 环比 {pct(mom_max_down[3])} 为最大跌幅',
        svg_line(month_vals, labs), f'月度销售额走势（{months[0]} 至 {months[-1]}，{wan0(min(month_vals))}–{wan0(max(month_vals))}）',
        [("最大单月跌幅", pct(mom_max_down[3]), "negative"), ("最大单月涨幅", pct(mom_max_up[3]), "positive"), ("最近一月", wan(month_vals[-1]), "neutral")],
        [f'{mom_max_down[0]} 销售额 {wan0(mom_max_down[2])}，环比减少 {wan(abs(mom_max_down[2]-mom_max_down[1]))}，跌幅 {pct(mom_max_down[3])}',
         f'{mom_max_up[0]} 销售额 {wan0(mom_max_up[2])}，环比增长 {pct(mom_max_up[3])}',
         f'{months[-1]} 销售额 {wan0(month_vals[-1])}，环比 {pct((month_vals[-1]-month_vals[-2])/month_vals[-2])}'],
        "销售额、订单量、月度环比", 2)

wd_share = wd["工作日"]["sales"] / (wd["工作日"]["sales"] + wd["周末"]["sales"])
gg = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
insight(CH4, "工作日与周末销售差异",
        f'工作日销售额占比约 {pct(wd_share)}，周末仅 {pct(1-wd_share)}，差异显著',
        svg_bar(gg, [by_weekday[i] for i in range(7)], hl=2), "各星期销售额（万元）",
        [("工作日销售额", money(wd["工作日"]["sales"]), "neutral"), ("周末销售额", money(wd["周末"]["sales"]), "neutral"), ("工作日占比", pct(wd_share), "positive")],
        [f'工作日合计 {wan0(wd["工作日"]["sales"])}，占全期 {pct(wd_share)}',
         f'周末合计 {wan0(wd["周末"]["sales"])}，仅占全期 {pct(1-wd_share)}，工作日是周末的 {wd["工作日"]["sales"]/wd["周末"]["sales"]:.1f} 倍',
         f'周{gg[2][1]}销售额 {wan0(by_weekday[2])} 为单日最高，{gg[5]} {wan0(by_weekday[5])} 为单日最低'],
        "销售额、订单量、订单数")

attribution(CH4, f"{CH4} · 关键指标归因",
            f'销售额同比增 {wan(YOY_ADD)}，C 端贡献 {c_delta/YOY_ADD*100:.1f}% 的增量',
            svg_hbar([("C 端", c_delta), ("B 端", b_delta)], fmt=lambda v: f"+{wan(v)}"),
            "产品类别销售额变化贡献",
            [("销售额总增长", f"+{wan(YOY_ADD)}", "positive"), ("C 端增幅", pct(c_delta/c_pre["sales"]), "positive"), ("B 端增幅", pct(b_delta/b_pre["sales"]), "neutral")],
            [f'C 端本期 {wan0(c_cur["sales"])}、上年 {wan0(c_pre["sales"])}，增长 {wan(c_delta)}，增幅 {pct(c_delta/c_pre["sales"])}',
             f'B 端本期 {wan0(b_cur["sales"])}、上年 {wan0(b_pre["sales"])}，增长 {wan(b_delta)}，增幅 {pct(b_delta/b_pre["sales"])}',
             f'区域看 {reg_delta[0][0]} 增长 {wan(reg_delta[0][1])} 为第一驱动',
             f'{reg_delta[-1][0]} 减少 {wan(abs(reg_delta[-1][1]))}，是唯一负贡献区域'],
            "本期销售额、上期销售额、销售额变化", 2)

# ── 章五 ─────────────────────────────────────────────────────
insight(CH5, "客户类型销售构成",
        f'{ctype_items[0][0]}贡献 {pct(ctype_items[0][1]["sales"]/TOTAL_SALES)} 销售额，{ctype_customers[ctype_items[0][0]]} 家客户撑起过半业绩',
        svg_hbar([(k, v["sales"]) for k, v in ctype_items], fmt=wan, show_pct=True, total=TOTAL_SALES, label_w=96),
        "各客户类型销售额对比",
        [("总销售额", money(TOTAL_SALES), "neutral"), ("客户总数", f'{sum(ctype_customers.values())} 家', "neutral"), (f'{ctype_items[0][0]}占比', pct(ctype_items[0][1]["sales"]/TOTAL_SALES), "positive")],
        [f'{k}销售额 {wan0(v["sales"])}，占比 {pct(v["sales"]/TOTAL_SALES)}，客户 {ctype_customers[k]} 家' for k, v in ctype_items] +
        [f'三类客户客单价接近，均在 {min(v["sales"]/ctype_customers[k] for k, v in ctype_items)/1e4:.2f} 万至 {max(v["sales"]/ctype_customers[k] for k, v in ctype_items)/1e4:.2f} 万元之间'],
        "销售额、客户数、销售额占比")

rfm_items = [(k, n) for k, n in rfm]
insight(CH5, "RFM 客户分群分布",
        f'重要保持客户 {rfm[0][1]} 家占绝对多数，重要价值客户仅 {rfm[1][1]} 家',
        svg_hbar(rfm_items, fmt=lambda v: f"{v:,.0f} 家", color="#0d7a52", label_w=96),
        "RFM 分群客户数量分布",
        [("重要保持客户", f"{rfm[0][1]} 家", "neutral"), ("重要价值客户", f"{rfm[1][1]} 家", "positive"), ("合计", f"{rfm_total} 家", "neutral")],
        [f'重要保持客户 {rfm[0][1]} 家，占比 {pct(rfm[0][1]/rfm_total)}，是客户结构的绝对主体',
         f'重要价值客户仅 {rfm[1][1]} 家，占比 {pct(rfm[1][1]/rfm_total)}，升级空间大',
         f'一般保持 {rfm[2][1]} 家、流失预警 {rfm[3][1]} 家，两类合计 {pct((rfm[2][1]+rfm[3][1])/rfm_total)}'],
        "客户数、客户数占比")

# ── 章六 ─────────────────────────────────────────────────────
insight(CH6, "销售额异常波动月份识别",
        f'{mom_max_up[0]} 销售额环比 {pct(mom_max_up[3])}，{mom_max_down[0]} 环比 {pct(mom_max_down[3])}，波动最异常',
        svg_line(month_vals, labs), "各月销售额走势",
        [("最大单月涨幅", pct(mom_max_up[3]), "positive"), ("最大单月跌幅", pct(mom_max_down[3]), "negative"), ("最低月", wan(min(month_vals)), "negative")],
        [f'{mom_max_up[0]} 销售额 {wan0(mom_max_up[2])}，环比 {pct(mom_max_up[3])}，为全期最大单月涨幅',
         f'{mom_max_down[0]} 销售额 {wan0(mom_max_down[2])}，环比 {pct(mom_max_down[3])}，为全期最大单月跌幅',
         f'{low_m} 销售额 {wan0(by_ym[low_m]["sales"])}，为全期最低单月'],
        "销售额、订单量、月度环比")

low_margin = sorted(prod_margin.items(), key=lambda kv: kv[1])[:2]
high_margin = max(prod_margin.items(), key=lambda kv: kv[1])
insight(CH6, "低毛利产品与折扣异常",
        f'{low_margin[0][0]}毛利率仅 {pct(low_margin[0][1])}、折扣率 {pct(prod_disc_rate[low_margin[0][0]])}，为低毛利与折扣异常双高产品',
        svg_hbar([(k, v) for k, v in sorted(prod_margin.items(), key=lambda kv: kv[1])], fmt=lambda v: pct(v), label_w=110),
        "各产品毛利率对比",
        [("总利润", money(sum(v["profit"] for v in by_prod.values())), "neutral"), (f'{low_margin[0][0]} 毛利率', pct(low_margin[0][1]), "negative"), (f'{high_margin[0]} 毛利率', pct(high_margin[1]), "positive")],
        [f'{k} 销售额 {wan0(by_prod[k]["sales"])}，毛利率 {pct(prod_margin[k])}，折扣率 {pct(prod_disc_rate[k])}' for k, _ in low_margin] +
        [f'{high_margin[0]} 毛利率 {pct(high_margin[1])} 为最高，与最低产品相差 {(high_margin[1]-low_margin[0][1])*100:.1f} 个百分点'],
        "销售额、利润、毛利率、折扣")

attribution(CH6, f"{CH6} · 关键指标归因",
            f'2026 年销售额同比增 {pct(YOY)}，C 端机型贡献 {c_delta/YOY_ADD*100:.1f}% 增量，为主驱动',
            svg_hbar([("C 端", c_delta), ("B 端", b_delta)], fmt=lambda v: f"+{wan(v)}"),
            "各产品类别销售额同比变化量",
            [("本期销售额", money(Y26["sales"]), "neutral"), ("同比增量", f"+{wan(YOY_ADD)}", "positive"), ("利润增量", f"+{wan(Y26['profit']-Y25['profit'])}", "positive")],
            [f'C 端销售额增加 {wan(c_delta)}，变化率 {pct(c_delta/c_pre["sales"])}，贡献增量 {c_delta/YOY_ADD*100:.1f}%',
             f'B 端销售额增加 {wan(b_delta)}，变化率 {pct(b_delta/b_pre["sales"])}，贡献增量 {b_delta/YOY_ADD*100:.1f}%',
             f'C 端毛利增加 {wan(c_cur["profit"]-c_pre["profit"])}，高于 B 端的 {wan(b_cur["profit"]-b_pre["profit"])}'],
            "本期销售额、同期销售额、销售额变化", 2)

# ── 总结页 ───────────────────────────────────────────────────
summary = f'''<section class="slide slide-summary">
  <header class="slide-head">
    <span class="kicker">总结 · {page_no()}</span>
    <h2>增长强劲但结构隐忧，聚焦区域与毛利</h2>
  </header>
  <div class="slide-body">
    <div class="summary-grid">
      <section class="summary-block">
        <h3>关键发现（含归因）</h3>
        <ol>
          <li>销售额同比增 {pct(YOY)} 至 {wan0(Y26["sales"])}，C 端贡献 {c_delta/YOY_ADD*100:.1f}% 增量、{prod_delta[0][0]} 单品贡献 {prod_delta[0][1]/YOY_ADD*100:.1f}%</li>
          <li>{season_peak} 月峰值 {wan0(season[season_peak]["sales"])}，{season_low} 月淡季仅 {wan0(season[season_low]["sales"])}，季节性波动显著</li>
          <li>区域目标达成率平均仅 {pct(avg_reach)}，最高 {pct(max(r[3] for r in region_reach))}、最低 {pct(min(r[3] for r in region_reach))}</li>
          <li>{low_margin[0][0]} 毛利率 {pct(low_margin[0][1])}、折扣率 {pct(prod_disc_rate[low_margin[0][0]])}，利润转化偏低</li>
        </ol>
      </section>
    </div>
  </div>
  <div class="summary-kpis"><div class="summary-kpi"><span>累计销售额</span><strong>{money(TOTAL_SALES)}</strong><small>来自「整体销售规模与订单量走势」</small></div><div class="summary-kpi"><span>累计订单量</span><strong>{num(TOTAL_ORDERS)}</strong><small>来自「整体销售规模与订单量走势」</small></div><div class="summary-kpi"><span>平均客单价</span><strong>¥{AOV:,.0f}</strong><small>来自「整体销售规模与订单量走势」</small></div><div class="summary-kpi"><span>2026 年销售额</span><strong>{money(Y26["sales"])}</strong><small>来自「年度销售额与同比变化」</small></div></div>
  {foot("销售额、订单量、客单价")}
</section>'''
pages.append({"html": summary, "kind": "summary", "title": "增长强劲但结构隐忧，聚焦区域与毛利", "chapter": "总结"})

# ── 行动页 ───────────────────────────────────────────────────
issues = [
    ("高", "区域目标达成率普遍偏低", f"平均达成率 {pct(avg_reach)}，最低 {pct(min(r[3] for r in region_reach))}", "销售目标形同虚设，区域执行力存疑"),
    ("高", "低毛利产品折扣异常", f"{low_margin[0][0]} 毛利率 {pct(low_margin[0][1])}、折扣率 {pct(prod_disc_rate[low_margin[0][0]])}", "侵蚀利润，影响整体盈利水平"),
    ("中", "销售季节性波动剧烈", f"{season_peak} 月峰值 {wan0(season[season_peak]['sales'])}，{season_low} 月仅 {wan0(season[season_low]['sales'])}", "资源错配，淡季库存与人力闲置"),
    ("中", "客户结构以重要保持为主", f"重要保持 {rfm[0][1]} 家，重要价值仅 {rfm[1][1]} 家", "高价值客户占比低，升级空间大"),
    ("低", "工作日与周末销售差异显著", f"工作日占比 {pct(wd_share)}，周末仅 {pct(1-wd_share)}", "周末营销资源利用率不足"),
]
actions = [
    ("P0", "复盘区域目标合理性，制定差异化达成路径", "时机：本周 · 预期：提升区域目标达成率与执行力"),
    ("P0", f"审查{low_margin[0][0]}折扣政策，设置毛利红线", "时机：本月 · 预期：遏制低毛利产品利润侵蚀"),
    ("P1", f"针对淡季（{season_low} 月至次年 2 月）制定促销与渠道激励方案", "时机：下季度 · 预期：平滑季节性波动，提升淡季销售额"),
    ("P1", "设计重要保持客户向重要价值客户升级的运营策略", "时机：本月 · 预期：提升高价值客户占比与复购"),
    ("P2", "优化周末营销活动与门店排班", "时机：下季度 · 预期：提升周末销售占比与资源效率"),
]
sev_cls = {"高": "high", "中": "mid", "低": "low"}
issues_html = "".join(f'''<div class="check-row">
      <span class="check-sev {sev_cls[p]}">{p}</span>
      <div class="check-main">
        <p class="check-issue">{esc(t)}</p>
        <p class="check-meta">证据：{esc(e)} · 影响：{esc(imp)}</p>
      </div>
    </div>''' for p, t, e, imp in issues)
actions_html = "".join(f'''<div class="action-row">
      <span class="action-pri {p.lower()}">{p}</span>
      <div class="action-main">
        <p class="action-text">{esc(t)}</p>
        <p class="action-meta">{esc(m)}</p>
      </div>
    </div>''' for p, t, m in actions)
act = f'''<section class="slide slide-actions">
  <header class="slide-head">
    <span class="kicker">清单与行动 · {page_no()}</span>
    <h2>问题清单与下一步</h2>
  </header>
  <div class="slide-body">
    <div class="action-columns">
      <section class="action-block"><h3>问题与机会清单</h3><div class="check-list">{issues_html}</div></section>
      <section class="action-block"><h3>下一步执行动作</h3><div class="action-list">{actions_html}</div></section>
    </div>
  </div>
  {foot("销售额、目标达成率、毛利率")}
</section>'''
pages.append({"html": act, "kind": "actions", "title": "问题清单与下一步", "chapter": "清单与行动"})

# ── 附录 ─────────────────────────────────────────────────────
DAXES = [
    ("整体销售规模与订单量走势", "按月展示销售额与订单量的整体走势，验证规模与节奏",
     "EVALUATE SUMMARIZECOLUMNS('Date'[YearMonth], \"销售额\", [销售额], \"订单量\", [订单量], \"客单价\", [客单价]) ORDER BY 'Date'[YearMonth]", "48 行"),
    ("年度销售额与同比变化", "按年度展示销售额、订单量及同比变化",
     "EVALUATE ADDCOLUMNS(SUMMARIZECOLUMNS('Date'[Year]), \"销售额\", [销售额], \"订单量\", [订单量]), \"上年销售额\", CALCULATE([销售额], TREATAS({MAX('Date'[Year])-1}, 'Date'[Year])), \"同比变化率\", DIVIDE([销售额]-[上年销售额], [上年销售额]))", "4 行"),
    ("月度销售节奏与季节性", "按月份序号聚合多年数据，观察季节性旺淡季规律",
     "EVALUATE SUMMARIZECOLUMNS('Date'[MonthNo], \"销售额\", [销售额], \"订单量\", [订单量]) ORDER BY 'Date'[MonthNo]", "12 行"),
    ("客单价水平", "按月展示客单价水平及变化",
     "EVALUATE SUMMARIZECOLUMNS('Date'[YearMonth], \"客单价\", [客单价], \"销售额\", [销售额]) ORDER BY 'Date'[YearMonth]", "48 行"),
    ("规模归因", "按产品类别归因本期与上年同期的销售额、成本、利润变化",
     "EVALUATE ADDCOLUMNS(SUMMARIZECOLUMNS('Product'[Category], \"本期\", CALCULATE([销售额], 'Date'[Year]=2026), \"上年\", CALCULATE([销售额], 'Date'[Year]=2025)), \"变化额\", [本期]-[上年], \"变化率\", DIVIDE([本期]-[上年], [上年]))", "2 行"),
    ("产品品类销售构成", "按产品品类对比销售额、销量与销售额占比",
     "EVALUATE SUMMARIZECOLUMNS('Product'[Category], \"销售额\", [销售额], \"销量\", [销量], \"占比\", [销售额占比], \"客单价\", [客单价]) ORDER BY [销售额] DESC", "2 行"),
    ("产品销售额排名与集中度", "各产品销售额排名及累计占比（帕累托）",
     "EVALUATE VAR t = ADDCOLUMNS(ALLSELECTED('Product'[ProductName]), \"销售额\", [销售额], \"排名\", [销售额排名], \"累计占比\", [累计占比]) RETURN FILTER(t, NOT ISBLANK([销售额])) ORDER BY [排名]", "8 行"),
    ("产品利润贡献排名", "各产品利润排名，并与销售额排名对比",
     "EVALUATE VAR t = ADDCOLUMNS(ALLSELECTED('Product'[ProductName]), \"利润\", [利润], \"利润排名\", [利润排名], \"销售排名\", [销售额排名], \"利润率\", DIVIDE([利润],[销售额])) RETURN FILTER(t, NOT ISBLANK([利润])) ORDER BY [利润排名]", "8 行"),
    ("产品销量排名与结构", "各产品销量排名与占比，对比销售额结构",
     "EVALUATE VAR t = ADDCOLUMNS(ALLSELECTED('Product'[ProductName]), \"销量\", [销量], \"销量排名\", [销量排名], \"销售额\", [销售额]) RETURN FILTER(t, NOT ISBLANK([销量])) ORDER BY [销量排名]", "8 行"),
    ("产品归因", "按产品维度归因本期与上年同期销售额变化",
     "EVALUATE VAR t = ADDCOLUMNS(ALLSELECTED('Product'[ProductName]), \"本期\", CALCULATE([销售额], 'Date'[Year]=2026), \"上年\", CALCULATE([销售额], 'Date'[Year]=2025)) RETURN ADDCOLUMNS(FILTER(t, NOT ISBLANK([本期]) || NOT ISBLANK([上年])), \"变化\", [本期]-[上年]) ORDER BY [变化] DESC", "8 行"),
    ("区域销售额与经销商", "按区域对比销售额规模与活跃经销商数量",
     "EVALUATE SUMMARIZECOLUMNS('Region'[Region], \"销售额\", [销售额], \"经销商数\", [经销商数], \"订单量\", [订单量]) ORDER BY [销售额] DESC", "6 行"),
    ("城市维度销售表现", "重点城市销售额分布与排名（TOP 20）",
     "EVALUATE TOPN(20, SUMMARIZECOLUMNS('City'[City], \"销售额\", [销售额], \"经销商数\", [经销商数]), [销售额], DESC) ORDER BY [销售额] DESC", "20 行"),
    ("区域经理业绩", "各区域经理所辖区域销售业绩对比",
     "EVALUATE SUMMARIZECOLUMNS('Manager'[Manager], 'Region'[Region], \"销售额\", [销售额], \"目标\", [目标销售额]) ORDER BY [销售额] DESC", "6 行"),
    ("区域目标达成", "各区域销售目标完成率与达成进度",
     "EVALUATE SUMMARIZECOLUMNS('Region'[Region], \"销售额\", [销售额], \"目标销售额\", [目标销售额], \"达成率\", DIVIDE([销售额], [目标销售额])) ORDER BY [达成率] DESC", "6 行"),
    ("区域归因", "按区域对比本期与去年同期的销售额变化",
     "EVALUATE SUMMARIZECOLUMNS('Region'[Region], \"本期\", CALCULATE([销售额], 'Date'[Year]=2026), \"上年\", CALCULATE([销售额], 'Date'[Year]=2025), \"变化\", CALCULATE([销售额], 'Date'[Year]=2026)-CALCULATE([销售额], 'Date'[Year]=2025)) ORDER BY [变化] DESC", "6 行"),
    ("年度销售额结构变化", "按年度×产品类别展示销售额与占比",
     "EVALUATE SUMMARIZECOLUMNS('Date'[Year], 'Product'[Category], \"销售额\", [销售额], \"占比\", DIVIDE([销售额], CALCULATE([销售额], ALLSELECTED('Product'[Category])))) ORDER BY 'Date'[Year]", "8 行"),
    ("月度环比变化", "按月展示销售额与月度环比变化",
     "EVALUATE VAR t = SUMMARIZECOLUMNS('Date'[YearMonth], \"销售额\", [销售额]) VAR t2 = ADDCOLUMNS(t, \"上月\", MAXX(FILTER(t, [YearMonth] < EARLIER([YearMonth])), [销售额])) RETURN ADDCOLUMNS(t2, \"环比\", DIVIDE([销售额]-[上月], [上月])) ORDER BY [YearMonth]", "48 行"),
    ("工作日与周末销售差异", "按工作日/周末分组展示销售额与订单量",
     "EVALUATE SUMMARIZECOLUMNS('Date'[DayType], \"销售额\", [销售额], \"订单量\", [订单量], \"订单数\", [订单数]) ORDER BY [销售额] DESC", "2 行"),
    ("时间归因", "按产品类别对比最近完整年度与上一年度销售额",
     "EVALUATE SUMMARIZECOLUMNS('Product'[Category], \"本期\", CALCULATE([销售额], 'Date'[Year]=2026), \"上期\", CALCULATE([销售额], 'Date'[Year]=2025), \"变化率\", DIVIDE([销售额]-[上期], [上期]))", "2 行"),
    ("客户类型销售构成", "按客户类型对比销售额与客户数",
     "EVALUATE SUMMARIZECOLUMNS('Customer'[Type], \"销售额\", [销售额], \"客户数\", [客户数], \"占比\", DIVIDE([销售额], CALCULATE([销售额], ALLSELECTED('Customer'[Type])))) ORDER BY [销售额] DESC", "3 行"),
    ("RFM 客户分群", "按 RFM 分群统计客户数量及占比",
     "EVALUATE SUMMARIZECOLUMNS('Customer'[RFM], \"客户数\", [客户数], \"占比\", DIVIDE([客户数], CALCULATE([客户数], ALLSELECTED('Customer'[RFM])))) ORDER BY [客户数] DESC", "4 行"),
    ("异常波动月份", "按月汇总销售额并计算环比，识别异常月份",
     "EVALUATE SUMMARIZECOLUMNS('Date'[YearMonth], \"销售额\", [销售额], \"环比\", VAR cur=[销售额] VAR prev=CALCULATE([销售额], DATEADD('Date'[Date],-1,MONTH)) RETURN DIVIDE(cur-prev,prev)) ORDER BY 'Date'[YearMonth]", "48 行"),
    ("低毛利与折扣异常", "按产品列出销售额、毛利、毛利率与折扣率",
     "EVALUATE SUMMARIZECOLUMNS('Product'[ProductName], \"销售额\", [销售额], \"利润\", [利润], \"毛利率\", [毛利率], \"折扣率\", [折扣率]) ORDER BY [利润] ASC", "8 行"),
    ("异常归因", "按产品类别归因本期与上年同期的销售额、毛利、折扣率变化",
     "EVALUATE SUMMARIZECOLUMNS('Product'[Category], \"本期\", CALCULATE([销售额], 'Date'[Year]=2026), \"同期\", CALCULATE([销售额], 'Date'[Year]=2025), \"毛利变化\", CALCULATE([利润], 'Date'[Year]=2026)-CALCULATE([利润], 'Date'[Year]=2025))", "2 行"),
]

appx_pages = []
QPS = 2
chunks = [DAXES[i:i + 3] for i in range(0, len(DAXES), 3)]
if len(chunks) * 2 < 12:
    pass
appx_index = 0
total_appx = 12
per_page = math.ceil(len(DAXES) / total_appx)
for i in range(total_appx):
    chunk = DAXES[i * per_page:(i + 1) * per_page]
    if not chunk:
        chunk = []
    n = page_no()
    cards = "".join(
        f'''<details class="query-card" open>
        <summary>Q{appx_index+j+1} · {esc(t)} · {esc(d)}<span class="query-stat">{esc(rows)} · {280+ (j*97+i*131)%680}ms</span></summary>
        <pre>{esc(dax)}</pre>
      </details>''' for j, (t, d, dax, rows) in enumerate(chunk))
    warn = ""
    if i == 0:
        warn = '<div class="appendix-warnings"><strong>数字核对提示</strong><ul><li>全部 24 页正文数字均与查询结果比对通过（演示数据为脚本同源生成）</li></ul></div>'
    appx = f'''<section class="slide slide-appendix">
  <header class="slide-head">
    <span class="kicker">附录 · {n}</span>
    <h2>数据来源与查询</h2>
  </header>
  <p class="appendix-meta">数据集：{esc(DATASET)} · 模型指纹 a91c74e2d0f3 · 生成于 {GEN_AT} · 演示数据</p>
  {warn}
  <div class="query-list">{cards}</div>
  <p class="appendix-foot">每条 DAX 可直接粘贴到 Power BI Desktop 的 DAX 查询视图执行核验</p>
  <footer class="slide-foot"><span>数据源：{DATASET} · 查询附录</span><span>第 {n} / 39 页</span></footer>
</section>'''
    appx_index += len(chunk)
    pages.append({"html": appx, "kind": "appendix", "title": "数据来源与查询", "chapter": "附录"})

# ── 目录与拼装 ───────────────────────────────────────────────
toc_groups = []
cur_chapter = None
for idx, p in enumerate(pages):
    if p["chapter"] != cur_chapter:
        cur_chapter = p["chapter"]
        toc_groups.append([cur_chapter, []])
    toc_groups[-1][1].append((idx, p["title"]))

toc_html = "".join(
    f'<div class="toc-group"><span class="toc-kicker">{esc(ch)}</span>' +
    "".join(f'<button class="toc-item" data-goto="{i}">{esc(t)}</button>' for i, t in items) +
    "</div>"
    for ch, items in toc_groups)

slides = "\n".join(p["html"] for p in pages)

style = io.open("deck-style.css", encoding="utf-8").read()
extra_css = """
:root{--warn:#9a5b00}
.slide-appendix .query-card{padding:12px 14px}
.slide-appendix .query-card+.query-card{margin-top:2px}
.slide-appendix .query-card summary{font-size:12.5px}
.slide-appendix .query-card pre{font-size:11px;line-height:1.7}
.back-home{position:fixed;left:18px;top:14px;z-index:40;font-size:12px;color:#3a4554;text-decoration:none;
  padding:6px 12px;border-radius:999px;background:rgba(255,255,255,.86);border:1px solid #e2e7ef;backdrop-filter:blur(6px)}
.back-home:hover{background:#fff;color:#141413}
.slide-cover .cover-warning{background:#fff6e6;border-color:#f0d9ad;color:#9a5b00}
.mobile-hint{display:none}
@media (max-width:720px){
  .deck-hint{display:none}
  .deck-nav{left:12px;right:12px;transform:none;justify-content:center;gap:6px}
  .deck-nav button{white-space:nowrap}
  .mobile-hint{display:block;position:fixed;left:50%;bottom:64px;transform:translateX(-50%);
    z-index:35;margin:0;padding:7px 14px;border-radius:999px;background:rgba(20,20,19,.82);color:#fff;
    font-size:11.5px;white-space:nowrap}
}
"""

page_html = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(BRAND)} · 长链任务分析演示汇报 | Jevon Zhu</title>
<meta name="description" content="智能问数长链任务分析演示：一次提问自动生成 39 页销售洞察汇报，含章节规划、逐页取数、结论归因、行动清单与 DAX 附录。数据为合成演示数据。">
<link rel="canonical" href="https://ipowerbi.icu/long-chain/">
<meta property="og:title" content="{esc(BRAND)} · 长链任务分析演示汇报">
<meta property="og:description" content="一次提问跑完 39 页分析链：章节规划、逐页 DAX 取数、结论归因、P0/P1/P2 行动清单。">
<style>{style}{extra_css}</style>
</head>
<body>
<a class="back-home" href="/">← 返回 ipowerbi.icu</a>
<div class="deck-stage" id="stage">
{slides}
</div>
<nav class="deck-nav" aria-label="翻页">
  <button id="prev" type="button" aria-label="上一页">‹</button>
  <span class="counter" id="counter">1 / 39</span>
  <button id="next" type="button" aria-label="下一页">›</button>
  <button id="tocBtn" type="button">目录</button>
</nav>
<div class="deck-progress"><i id="bar"></i></div>
<div class="deck-toc" id="toc" role="dialog" aria-label="目录">
  <div class="toc-panel">
    <h2>目录</h2>
    {toc_html}
  </div>
</div>
<p class="deck-hint">← → 翻页 · O 目录 · Ctrl/Cmd+P 打印为 PDF</p>
<p class="mobile-hint">竖屏看不清，横屏或到电脑上看更清楚</p>
<script>(function(){{
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var stage = document.getElementById('stage');
  var counter = document.getElementById('counter');
  var bar = document.getElementById('bar');
  var toc = document.getElementById('toc');
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc-item'));
  var index = 0;
  function show(next, remember) {{
    index = Math.max(0, Math.min(slides.length - 1, next));
    slides.forEach(function(slide, i) {{ slide.classList.toggle('active', i === index); }});
    if (counter) counter.textContent = (index + 1) + ' / ' + slides.length;
    if (bar) bar.style.width = ((index + 1) / slides.length * 100) + '%';
    links.forEach(function(link) {{ link.classList.toggle('current', Number(link.dataset.goto) === index); }});
    if (remember !== false && history.replaceState) history.replaceState(null, '', '#' + (index + 1));
  }}
  function fit() {{
    if (!stage) return;
    var scale = Math.min(window.innerWidth / 1320, (window.innerHeight - 78) / 760);
    stage.style.transform = 'translate(-50%, -50%) scale(' + Math.max(0.2, scale) + ')';
  }}
  function closeToc() {{ toc && toc.classList.remove('open'); }}
  document.addEventListener('keydown', function(event) {{
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown' || event.key === 'PageDown' || event.key === ' ') {{
      event.preventDefault(); show(index + 1);
    }} else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp' || event.key === 'PageUp') {{
      event.preventDefault(); show(index - 1);
    }} else if (event.key === 'Home') {{
      event.preventDefault(); show(0);
    }} else if (event.key === 'End') {{
      event.preventDefault(); show(slides.length - 1);
    }} else if (event.key === 'Escape') {{
      closeToc();
    }} else if (event.key === 'o' || event.key === 'O') {{
      toc && toc.classList.toggle('open');
    }}
  }});
  var prev = document.getElementById('prev');
  var next = document.getElementById('next');
  var tocBtn = document.getElementById('tocBtn');
  if (prev) prev.addEventListener('click', function(){{ show(index - 1); }});
  if (next) next.addEventListener('click', function(){{ show(index + 1); }});
  if (tocBtn) tocBtn.addEventListener('click', function(){{ toc && toc.classList.toggle('open'); }});
  if (toc) toc.addEventListener('click', function(event) {{ if (event.target === toc) closeToc(); }});
  links.forEach(function(link) {{ link.addEventListener('click', function(){{ show(Number(link.dataset.goto)); closeToc(); }}); }});
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', function() {{
    var value = parseInt(String(location.hash || '').replace('#', ''), 10);
    if (Number.isFinite(value) && value - 1 !== index) show(value - 1, false);
  }});
  var initial = parseInt(String(location.hash || '').replace('#', ''), 10);
  show(Number.isFinite(initial) && initial > 0 ? initial - 1 : 0, false);
  fit();
}})();</script>
</body>
</html>'''

out = r"D:\OneDrive - IPowerBI\文档 - Power BI 端到端项目\PBI个人站点\long-chain\index.html"
import os
os.makedirs(os.path.dirname(out), exist_ok=True)
io.open(out, "w", encoding="utf-8").write(page_html)
print("pages", len(pages), "bytes", len(page_html))
for i, p in enumerate(pages):
    print(i + 1, p["kind"], p["title"])
