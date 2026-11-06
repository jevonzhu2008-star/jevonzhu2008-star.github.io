# Jevon Zhu · Power BI 站点入口

线上地址：<https://jevonzhu2008-star.github.io/>

三个站点的统一首页：

- **人人都爱 Power BI** — <https://ipowerbi.mysxl.cn/>
- **Power BI 作品集** — <https://jevonzhu2008-star.github.io/AIA-PowerBI-Portfolio/>
- **PBI 报表开发平台** — <https://jevonzhu2008-star.github.io/L2-data-platform/>

页面按「一屏一站」组织：首屏讲人，随后官网、作品集、平台各占一屏，接着是「做报表的方法」、关于和联系。亮色底、Power BI 黄作签名色、黑色胶囊按钮。

## 本地打开

直接双击 `index.html`（图片、样式、脚本均为相对路径）。字体不依赖任何 CDN：拉丁字形用 `assets/fonts/` 里自托管的 Manrope（单个 24KB woff2，SIL Open Font License 1.1），中日韩文字走系统字体（PingFang SC / 微软雅黑）。

`404.html` 用的是站点根路径（`/assets/...`），双击打开会丢样式，需要本地起一个静态服务器预览。

## 文件

```
index.html            页面结构（文案、链接都在这里）
404.html              GitHub Pages 的 404 页，与首页同一套视觉
robots.txt            允许抓取，并指向 sitemap
sitemap.xml           单页站点地图
assets/site.css       全部样式
assets/site.js        入场动画、导航高亮、移动端菜单、宣传片播放
assets/fonts/         自托管 Manrope 可变字体
assets/og-cover.jpg   社交分享卡片（1200×630）
assets/portfolio-promo.mp4   作品集宣传片（720p / 50 秒 / 3.4MB，无音轨）
assets/shots/*.webp   截图（WebP 为主，jpg 仅作旧浏览器兜底）
assets/shots/promo-poster.webp  宣传片封面帧
```

三张大图（`ip-home`、`pf-overview`、`platform-login`）有 `-1600` / `-800` 两档，靠 `srcset` + `sizes` 按屏幕挑；小图（`ip-factory`、`ip-sales`、`report-*`）只有一档 WebP。截图是 2026-11-05 从线上站点按 1600px 宽重截的。

## 部署

放到任意静态站点即可，无需构建：

- GitHub Pages：把整个目录推到仓库根目录，或 `docs/` 并在仓库设置里指定。
- `404.html`、`robots.txt`、`sitemap.xml` 必须放在站点根目录才会生效。
- 如果本页作为根站 `jevonzhu2008-star.github.io`，三个站点链接保持现在的绝对地址即可。

## 域名与三站统一（待办）

三个站点现在分属两种托管，这是「看起来不像一个站」的根源：

- 官网 `ipowerbi.mysxl.cn`：第三方建站，内容不在本仓库，视觉和加载方式由平台决定；
- 作品集、平台和本站：GitHub Pages，同一个 origin，共用这套视觉。

**短期**：把官网内容迁进本仓库的子路径（如 `/ipowerbi/`），复用 `assets/site.css` 的字体与色板，三站归到同一个域名、同一套视觉。需要 mysxl 站点的导出或原稿。

**长期**：换自有域名。在 GitHub Pages 设置自定义域名后，GitHub 会把 `jevonzhu2008-star.github.io` 301 到新域名；本仓库里的绝对链接统一替换成新域名即可。官网页面源码里出现的 `ipowerbi.com.cn` 如果是自己持有的域名，可以直接用它。

## 修改

- **换截图**：重截 16:10 的 1600×1000 原图，导出 `-1600.webp`、`-800.webp` 两档（小图单档）；jpg 兜底保持同名同比例。`<img>` 上的 `width`/`height` 只是占位比例，跟着改成 1600×1000 即可。
- **改文案**：首屏在 `.hero`，三站在 `.panel`，工作方法在 `.steps`，关于在 `.about`。
- **换链接**：按钮和帧的 `<a href>` 指向对应页面；公开报表用的是 `app.powerbi.com/view` 的公开地址。
- **换分享卡片**：`assets/og-cover.jpg` 固定 1200×630，改文案后重出一张，并同步 `index.html` 里的 `og:image` / `twitter:image`。

## 已知取舍

- 截图是 2026 年 11 月抓取的真实页面，站点改版后需要重截。
- 平台登录页公开可见，工作台需要账号；首页只展示登录页并注明「账号授权后访问」。
- 作品集区块放的是宣传片：静音、循环、`preload="none"`，滚到附近才开始下载播放；开了减少动效或省流量模式时只显示封面帧。
- 原始素材 `promo.mp4`（47MB / 1080p）不进仓库，已写进 `.gitignore`；改片后重新压一版 `assets/portfolio-promo.mp4` 并重出 `promo-poster.webp` 即可。
