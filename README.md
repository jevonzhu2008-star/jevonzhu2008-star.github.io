# Jevon Zhu · Power BI 站点入口

线上地址：<https://ipowerbi.icu/>

四个站点的统一首页：

- **人人都爱 Power BI** — <https://ipowerbi.mysxl.cn/>
- **Power BI 作品集** — <https://ipowerbi.icu/AIA-PowerBI-Portfolio/>
- **PBI 报表开发平台** — <https://ipowerbi.icu/L2-data-platform/>
- **智能问数** — <https://app.ipowerbi.icu/>（登录页公开，目前需要口令访问）

页面按「一屏一站」组织：首屏讲人，随后官网、作品集、平台、智能问数各占一屏，接着是「做报表的方法」、关于和联系。亮色底、Power BI 黄作签名色、黑色胶囊按钮。

## 本地打开

直接双击 `index.html`（图片、样式、脚本均为相对路径）。字体不依赖任何 CDN：拉丁字形用 `assets/fonts/` 里自托管的 Manrope（单个 24KB woff2，SIL Open Font License 1.1），中日韩文字走系统字体（PingFang SC / 微软雅黑）。

`404.html` 用的是站点根路径（`/assets/...`），双击打开会丢样式，需要本地起一个静态服务器预览。

## 文件

```
index.html            页面结构（文案、链接都在这里）
404.html              GitHub Pages 的 404 页，与首页同一套视觉
robots.txt            允许抓取，并指向 sitemap
sitemap.xml           站点地图（首页 + 作品集）
ca8fb82aa608eb6566678430c4a768a8.txt   IndexNow 密钥，Bing 主动推送验证用
scripts/indexnow.ps1  上线后把 URL 推给 Bing / Yandex
assets/site.css       全部样式
assets/site.js        入场动画、导航高亮、移动端菜单、宣传片播放
assets/fonts/         自托管 Manrope 可变字体
assets/og-cover.jpg   社交分享卡片（1200×630）
assets/wechat-qr.webp 微信二维码（从名片图裁切，联系区使用）
assets/portfolio-promo.mp4   作品集宣传片（960×540 / 50 秒 / 1.8MB，无音轨）
assets/shots/*.webp   截图（WebP 为主，jpg 仅作旧浏览器兜底）
assets/shots/promo-poster.webp  宣传片封面帧
```

三张大图（`ip-home`、`pf-overview`、`platform-login`）有 `-1600` / `-800` 两档，靠 `srcset` + `sizes` 按屏幕挑；小图（`ip-factory`、`ip-sales`、`report-*`）只有一档 WebP。截图是 2026-11-05 从线上站点按 1600px 宽重截的。

## 部署

放到任意静态站点即可，无需构建：

- GitHub Pages：把整个目录推到仓库根目录，或 `docs/` 并在仓库设置里指定。
- `404.html`、`robots.txt`、`sitemap.xml` 必须放在站点根目录才会生效。
- 仓库根目录的 `CNAME` 已绑定 `ipowerbi.icu`，GitHub Pages 会把旧地址 `jevonzhu2008-star.github.io` 301 到新域名。三个站点的绝对链接统一用 `https://ipowerbi.icu/`。

## 搜索引擎收录

页面本身已经做了：唯一 H1、canonical、OG / Twitter 卡片、`Person` / `WebSite` / `ProfilePage` / `Service` / `FAQPage` 结构化数据、含作品集的 sitemap、robots.txt、IndexNow 密钥，以及「服务」和「常见问题」两块正文内容。

剩下的是在各站长平台登记，都要用你自己的账号，做一次即可：

| 平台 | 入口 | 要做的 |
| --- | --- | --- |
| Google | Search Console | 添加「网址前缀」资源 → 用 HTML 标记验证（值填进 `index.html` 里 `google-site-verification` 的注释）→ 提交 `sitemap.xml` |
| 必应 | Bing Webmaster Tools | 可从 Search Console 直接导入；也可以添加站点后 HTML 验证 → 提交 sitemap |
| 百度 | 百度搜索资源平台 | 添加站点 → HTML 标签验证（`baidu-site-verification`）→ 提交 sitemap → 在「链接提交」里配主动推送 |

验证用的 `<meta>` 已经在 `index.html` 的 head 里留了注释位，拿到值后取消注释填进去。

每次改版推上线后，可以主动推一次 Bing：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\indexnow.ps1
```

百度同样有主动推送，配额每天 10 条左右：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\baidu-push.ps1
```

推送 token 属于敏感信息，不写进仓库：放在项目根目录的 `.baidu-token` 文件里（已加进 `.gitignore`），或者设置环境变量 `BAIDU_PUSH_TOKEN`。

### 关于百度

站点已绑定自有域名 `ipowerbi.icu`，百度不再受 `github.io` 主域站点数限制，按上面的清单添加站点、验证、提交 sitemap 即可。

百度对国内访问速度敏感；如果以后希望排名更稳，可以把站点迁到国内托管（域名备案 + 阿里云 OSS / 腾讯云 COS + CDN）。

必应和谷歌按上面的清单提交，通常几天到两周内收录。

## 域名与三站统一

`https://ipowerbi.icu/` 是三个站点的统一入口：

- 本站：`https://ipowerbi.icu/`
- 作品集：`https://ipowerbi.icu/AIA-PowerBI-Portfolio/`
- 平台：`https://ipowerbi.icu/L2-data-platform/`

根站绑定自定义域名后，同在 `jevonzhu2008-star.github.io` 下的项目站点会自动跟随到新域名，旧地址由 GitHub 301 过去。

仍待办：官网 `ipowerbi.mysxl.cn` 还在第三方平台，内容不在本仓库，视觉和加载方式由平台决定。把官网迁进本仓库的子路径（如 `/ipowerbi/`），复用 `assets/site.css`，三站才算真正同一套视觉。需要 mysxl 站点的导出或原稿。

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
