# -*- coding: utf-8 -*-
"""生成「长链任务分析」演示汇报：合成数据 -> 自洽指标 -> 39 页自包含 HTML。"""
import random, json, math
from collections import defaultdict
from datetime import date, timedelta

random.seed(20261126)

BRAND = "某教育硬件品牌"
DS = "演示销售模型"

PRODUCTS = [
    # code, name, category, price, margin, share_weight
    ("A90", "学习机 A90", "C端", 4599, 0.223, 0.170),
    ("A80", "学习机 A80", "C端", 3799, 0.184, 0.155),
    ("A60", "学习机 A60", "C端", 2699, 0.151, 0.145),
    ("S20", "学生平板 S20", "C端", 2199, 0.082, 0.130),
    ("S10", "学生平板 S10", "C端", 1599, 0.061, 0.125),
    ("B9",  "教师平板 B9",  "B端", 4299, 0.201, 0.090),
    ("B8",  "教师平板 B8",  "B端", 3299, 0.118, 0.110),
    ("B6",  "教师平板 B6",  "B端", 2399, 0.052, 0.075),
]

REGIONS = [
    ("华东", 0.285, 42), ("中南", 0.245, 51), ("华北", 0.200, 22),
    ("东北", 0.150, 22), ("西南", 0.070, 19), ("西北", 0.050, 13),
]

CITIES = {
    "华东": ["上海", "苏州", "杭州", "南京"],
    "中南": ["武汉", "长沙", "郑州", "广州"],
    "华北": ["北京", "石家庄", "青岛", "济南"],
    "东北": ["沈阳", "哈尔滨", "大连", "长春"],
    "西南": ["成都", "重庆", "昆明"],
    "西北": ["西安", "兰州"],
}

CUSTOMER_TYPES = [("终端柜台", 0.50, 389), ("普教", 0.298, 225), ("职校", 0.202, 133)]

MONTH_SEASON = [1.35, 0.95, 1.20, 0.85, 1.55, 0.95, 0.55, 0.85, 1.00, 0.70, 0.75, 0.45]
YEAR_TARGET = {2023: 1860.0, 2024: 2240.0, 2025: 2910.0, 2026: 3420.0}  # 万元
YEAR_ORDERS = {2023: 4000, 2024: 4500, 2025: 5200, 2026: 6300}

MONTHS = [(y, m) for y in range(2023, 2027) for m in range(1, 13)]


def weighted_pick(items, weight_of):
    total = sum(weight_of(i) for i in items)
    r = random.random() * total
    acc = 0.0
    for it in items:
        acc += weight_of(it)
        if r <= acc:
            return it
    return items[-1]


def month_weight(y, m):
    base = MONTH_SEASON[m - 1]
    drift = 1 + 0.012 * ((y - 2023) * 12 + m) / 12.0
    return base * drift


def gen_orders():
    orders = []
    for y in sorted(YEAR_ORDERS):
        ws = [(m, month_weight(y, m)) for m in range(1, 13)]
        tot_w = sum(w for _, w in ws)
        year_growth_shift = {2023: 0.0, 2024: 0.03, 2025: 0.08, 2026: 0.13}[y]
        for m, w in ws:
            n = max(1, round(YEAR_ORDERS[y] * w / tot_w * random.uniform(0.92, 1.08)))
            for _ in range(n):
                # 日期：工作日占 82%
                while True:
                    day = random.randint(1, 28)
                    d = date(y, m, day)
                    weekday = d.weekday()  # 0=周一
                    if weekday >= 5:
                        if random.random() < 0.48:
                            continue
                    else:
                        if random.random() > 0.95:
                            continue
                    break
                prod = weighted_pick(PRODUCTS, lambda p: p[5])
                cat_shift = year_growth_shift if prod[2] == "C端" else -year_growth_shift * 0.5
                if random.random() < 0.35 + cat_shift:  # C 端略快
                    c_prods = [p for p in PRODUCTS if p[2] == "C端"]
                    prod = weighted_pick(c_prods, lambda p: p[5])
                region = weighted_pick(REGIONS, lambda r: r[1])
                city = random.choice(CITIES[region[0]])
                ctype = weighted_pick(CUSTOMER_TYPES, lambda c: c[1])
                qty = 1
                if prod[2] == "B端":
                    qty = random.choice([1, 2, 3, 4, 5, 8, 10, 12, 15]) if random.random() < 0.55 else 1
                else:
                    qty = 1 if random.random() < 0.9 else 2
                discount = max(0.0, min(0.30, random.gauss(0.18 if prod[2] == "B端" else 0.10, 0.06)))
                price = prod[3] * (1 - discount)
                gross = price * qty
                profit = gross * prod[4] * random.uniform(0.88, 1.12)
                orders.append({
                    "date": d, "year": y, "month": m, "ym": f"{y}-{m:02d}",
                    "product": prod[0], "pname": prod[1], "category": prod[2],
                    "region": region[0], "city": city, "ctype": ctype[0],
                    "qty": qty, "sales": gross, "profit": profit, "discount": discount,
                })
    return orders


def agg(orders, keyfn):
    out = defaultdict(lambda: {"sales": 0.0, "profit": 0.0, "qty": 0, "orders": 0})
    for o in orders:
        k = keyfn(o)
        out[k]["sales"] += o["sales"]
        out[k]["profit"] += o["profit"]
        out[k]["qty"] += o["qty"]
        out[k]["orders"] += 1
    return dict(out)


if __name__ == "__main__":
    orders = gen_orders()
    by_year = agg(orders, lambda o: o["year"])
    by_month = agg(orders, lambda o: o["ym"])
    by_prod = agg(orders, lambda o: o["pname"])
    by_region = agg(orders, lambda o: o["region"])
    total = sum(v["sales"] for v in by_year.values())
    print("订单数", len(orders), "总销售额（万）", round(total / 1e4, 1))
    for y in sorted(by_year):
        v = by_year[y]
        print(y, "销售额万", round(v["sales"] / 1e4, 1), "订单", v["orders"], "销量", v["qty"])
    print("--- 产品")
    for k, v in sorted(by_prod.items(), key=lambda kv: -kv[1]["sales"]):
        print(k, round(v["sales"] / 1e4, 1), "毛利率", round(v["profit"] / v["sales"] * 100, 1))
    print("--- 区域")
    for k, v in sorted(by_region.items(), key=lambda kv: -kv[1]["sales"]):
        print(k, round(v["sales"] / 1e4, 1))
    months = sorted(by_month)
    print("max month", max(by_month.items(), key=lambda kv: kv[1]["sales"])[0])
    print("min month", min(by_month.items(), key=lambda kv: kv[1]["sales"])[0])
