# Jevon Zhu · Power BI 站点入口

三个站点的统一首页：

- **人人都爱 Power BI** — <https://ipowerbi.mysxl.cn/>
- **Power BI 作品集** — <https://jevonzhu2008-star.github.io/AIA-PowerBI-Portfolio/>
- **L2 报表开发平台** — <https://jevonzhu2008-star.github.io/L2-data-platform/>

页面按「一屏一站」组织：首屏讲人，随后官网、作品集、平台各占一屏，接着是「做报表的方法」、关于和联系。亮色底、Power BI 黄作签名色、黑色胶囊按钮。

## 本地打开

直接双击 `index.html`（图片、样式、脚本均为相对路径）。字体通过 jsDelivr 加载，离线时回退到系统无衬线字体。

## 文件

```
index.html            页面结构（文案、链接都在这里）
assets/site.css       全部样式
assets/site.js        入场动画、导航高亮
assets/shots/*.jpg    截图（当前页面用 8 张，另有 5 张备用）
```

## 部署

放到任意静态站点即可，无需构建：

- GitHub Pages：把整个目录推到仓库根目录，或 `docs/` 并在仓库设置里指定。
- 如果本页作为根站 `jevonzhu2008-star.github.io`，三个站点链接保持现在的绝对地址即可。

## 修改

- **换截图**：替换 `assets/shots/` 下同名的 jpg，宽高写在 `<img>` 的 `width`/`height` 里，保持比例即可。
- **改文案**：首屏在 `.hero`，三站在 `.panel`，工作方法在 `.steps`，关于在 `.about`。
- **换链接**：按钮和帧的 `<a href>` 指向对应页面；公开报表用的是 `app.powerbi.com/view` 的公开地址。

## 已知取舍

- 截图是 2026 年 11 月抓取的真实页面，站点改版后需要重截。
- 平台登录页公开可见，工作台需要账号；首页只展示登录页并注明「账号授权后访问」。
- 页面没有视频：三个站点没有可直接使用的自有素材，画面全部用真实截图。
