# -*- coding: utf-8 -*-
"""把智能问数导出的原始汇报 HTML 脱敏，输出为 long-chain/index.html。

用法：
    python redact_deck.py <原始汇报.html> [-o ..\\..\\long-chain\\index.html]

脱敏范围：
- 品牌名、数据集名、数据集 ID 与模型指纹
- 11 家真实经销商公司名 -> 「城市 + 字母代号」
- 品牌型号 U*/UMIX* -> 通用代号 A*/B*
- 导出环境自带的统计脚本

金额、页数、口径、DAX 查询一律原样保留，页与页之间的数字关系不变。
脚本会做一次残留检查，发现敏感词直接报错，避免漏脱敏后上线。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE.parent.parent / "long-chain" / "index.html"

# 顺序敏感：长的先替换，避免短词先吃掉长词。
REPLACEMENTS: list[tuple[str, str]] = [
    # ── 标题与数据集名 ────────────────────────────────
    ("<title>优学派销售数据分析NEW · 洞察报告</title>",
     "<title>某教育硬件品牌 · 长链任务分析演示汇报 | Jevon Zhu</title>"),
    ("优学派销售数据分析NEW · 洞察报告", "某教育硬件品牌销售洞察报告"),
    ("优学派销售数据分析NEW（语义模型）", "某教育硬件品牌销售分析（演示语义模型）"),
    ("优学派销售数据分析NEW", "某教育硬件品牌销售分析（演示语义模型）"),
    ("优学派", "某教育硬件品牌"),

    # ── 数据集 ID 与模型指纹 ──────────────────────────
    (" · ID bd9b7b41-4f85-4793-9ea7-810bf4027a65 · 模型指纹 fd74933a45410808", ""),

    # ── 经销商公司名（全称 -> 截图里的截断形式 -> 正文简称）──
    ("天津市康星计算机技术发展有限公司", "天津经销商 A"),
    ("天津市康星计算机技术发展有限", "天津经销商 A"),
    ("天津市康星计算机", "天津经销商 A"),
    ("天津市康星", "天津经销商 A"),
    ("济南深度科技有限公司", "济南经销商 B"),
    ("济南深度科技", "济南经销商 B"),
    ("上海博胜佳欣科技有限公司", "上海经销商 C"),
    ("上海博胜佳欣", "上海经销商 C"),
    ("长春博锐通达信息技术有限公司", "长春经销商 D"),
    ("长春博锐通达", "长春经销商 D"),
    ("哈尔滨鼎鑫数据科技有限公司", "哈尔滨经销商 E"),
    ("哈尔滨鼎鑫", "哈尔滨经销商 E"),
    ("广东新耐特电子有限公司", "广东经销商 F"),
    ("广东新耐特", "广东经销商 F"),
    ("重庆安东电子科技有限公司", "重庆经销商 G"),
    ("重庆安东", "重庆经销商 G"),
    ("河北思成电子科技有限公司", "河北经销商 H"),
    ("河北思成", "河北经销商 H"),
    ("北京传奇天地科技有限公司", "北京经销商 I"),
    ("北京传奇天地", "北京经销商 I"),
    ("昆明佳谛科技有限公司", "昆明经销商 J"),
    ("昆明佳谛", "昆明经销商 J"),
    ("湖南蓝星电脑有限责任公司", "湖南经销商 K"),
    ("湖南蓝星", "湖南经销商 K"),

    # ── 品牌型号 -> 通用代号 ──────────────────────────
    ("UMIX6", "B6"),
    ("UMIX2", "B2"),
    ("U90", "A90"),
    ("U80", "A80"),
    ("U60", "A60"),
    ("U39", "A39"),
    ("U36+", "A36+"),
    ("U17", "A17"),
    ("S18PRO", "S18 Pro"),

    # 封面的数据源一栏改成 5 列后放不下，缩短标签
    ("<dd>某教育硬件品牌销售分析（演示语义模型）</dd>", "<dd>某教育硬件品牌销售分析</dd>"),

    # ── 导出环境的痕迹 ────────────────────────────────
    ('<span class="cover-eyebrow">数据洞察汇报</span>',
     '<span class="cover-eyebrow">数据洞察汇报 · 脱敏演示</span>'),
]

META = """<meta name="description" content="智能问数长链任务分析实测：一次点击生成 54 页销售洞察汇报，含 5 个章节、23 页洞察、逐页 DAX 取数、结论归因与 24 页查询附录。品牌与经销商已脱敏。">
<link rel="canonical" href="https://ipowerbi.icu/long-chain/">
<meta property="og:title" content="某教育硬件品牌 · 长链任务分析演示汇报">
<meta property="og:description" content="一次点击跑完 54 页分析链：5 个章节、23 页洞察、34 条 DAX 取数、逐页核对提示、24 页查询附录。">
<meta property="og:type" content="article">
"""

EXTRA_CSS = """
.cover-meta{grid-template-columns:repeat(5,minmax(0,1fr))}
.back-home{position:fixed;left:18px;top:14px;z-index:40;font-size:12px;color:#3a4554;text-decoration:none;
  padding:6px 12px;border-radius:999px;background:rgba(255,255,255,.86);border:1px solid #e2e7ef;backdrop-filter:blur(6px)}
.back-home:hover{background:#fff;color:#141413}
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

BACK_HOME = '<a class="back-home" href="/">← 返回 ipowerbi.icu</a>'
MOBILE_HINT = '<p class="mobile-hint">竖屏看不清，横屏或到电脑上看更清楚</p>'

# 脱敏后不允许再出现的字样（残留检查）
FORBIDDEN = ["优学派", "康星", "博胜佳欣", "博锐通达", "鼎鑫", "新耐特", "安东", "思成",
             "传奇天地", "佳谛", "蓝星", "bd9b7b41", "fd74933a", "cloudflareinsights"]


def redact(source: str) -> str:
    html = source
    for old, new in REPLACEMENTS:
        html = html.replace(old, new)

    # 去掉导出环境自带的统计脚本
    html = re.sub(
        r'<script type="module" src="https://static\.cloudflareinsights\.com/[^"]*"[^>]*></script>\s*',
        "",
        html,
    )

    # SEO / 社交卡片元信息
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1">'
    if viewport not in html:
        raise SystemExit("找不到 viewport 标签，导出格式可能变了")
    html = html.replace(viewport, viewport + "\n" + META, 1)

    # 站点导航与移动端提示
    html = html.replace("<body>", "<body>\n" + BACK_HOME, 1)
    hint = '<p class="deck-hint">← → 翻页 · O 目录 · Ctrl/Cmd+P 打印为 PDF</p>'
    if hint in html:
        html = html.replace(hint, hint + "\n" + MOBILE_HINT, 1)

    # 站点补充样式
    html = html.replace("</style>", EXTRA_CSS + "</style>", 1)

    # 自建访问统计（与站点其余页面同一份脚本）
    html = html.replace("</body>", '<script src="../assets/stats.js" defer></script>\n</body>', 1)

    # 替换后修顺语序：「头部经销商天津经销商 A」-> 「头部经销商：天津经销商 A」；
    # 「经销商 A销售额」-> 「经销商 A 销售额」
    html = html.replace("头部经销商天津经销商", "头部经销商：天津经销商")
    html = re.sub(r"(经销商 [A-K])(?=[一-龥])", r"\1 ", html)

    leftover = [word for word in FORBIDDEN if word in html]
    if leftover:
        raise SystemExit("脱敏不完整，仍含：" + "、".join(leftover))

    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="脱敏智能问数导出的汇报 HTML")
    parser.add_argument("source", help="智能问数导出的原始 HTML 路径")
    parser.add_argument("-o", "--out", default=str(DEFAULT_OUT), help="输出路径")
    args = parser.parse_args()

    source_path = Path(args.source)
    html = source_path.read_text(encoding="utf-8")
    result = redact(html)

    slides = result.count('<section class="slide')
    out_path = Path(args.out)
    out_path.write_text(result, encoding="utf-8", newline="\n")
    print(f"已写入 {out_path}（{slides} 页，{len(result):,} 字节）")


if __name__ == "__main__":
    main()
