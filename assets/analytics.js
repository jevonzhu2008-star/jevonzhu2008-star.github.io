/* 站点统计加载器：Google Analytics 4 / 百度统计 / Microsoft Clarity
 *
 * 三个 ID 都写在 index.html 底部的 window.SITE_ANALYTICS 里，留空表示不启用。
 * 等页面 load 之后、浏览器空闲时才注入脚本，不占首屏带宽，也不影响 LCP。
 * 本地预览（localhost / file://）和开启了 Do Not Track 的访问一律跳过。
 * 同一份文件四个站点都能用，改 index.html 里的 ID 即可。
 */
(function () {
  'use strict';

  var cfg = window.SITE_ANALYTICS || {};
  var host = location.hostname;
  var isLocal = !host ||
    host === 'localhost' ||
    host === '127.0.0.1' ||
    host === '::1' ||
    location.protocol === 'file:';
  var dnt = navigator.doNotTrack === '1' ||
    window.doNotTrack === '1' ||
    navigator.msDoNotTrack === '1';

  if (isLocal || dnt) return;

  var started = false;

  function appendScript(src) {
    var s = document.createElement('script');
    s.async = true;
    s.src = src;
    document.head.appendChild(s);
  }

  function initGA4(id) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', id, { anonymize_ip: true });
    appendScript('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id));
  }

  function initBaidu(id) {
    window._hmt = window._hmt || [];
    appendScript('https://hm.baidu.com/hm.js?' + encodeURIComponent(id));
  }

  function initClarity(id) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r);
      t.async = 1;
      t.src = 'https://www.clarity.ms/tag/' + i;
      y = l.getElementsByTagName(r)[0];
      y.parentNode.insertBefore(t, y);
    })(window, document, 'clarity', 'script', id);
  }

  function start() {
    if (started) return;
    started = true;

    var ga4 = (cfg.ga4 || '').trim();
    var baidu = (cfg.baidu || '').trim();
    var clarity = (cfg.clarity || '').trim();

    try { if (ga4) initGA4(ga4); } catch (e) {}
    try { if (baidu) initBaidu(baidu); } catch (e) {}
    try { if (clarity) initClarity(clarity); } catch (e) {}
  }

  function schedule() {
    var run = function () {
      if ('requestIdleCallback' in window) {
        window.requestIdleCallback(start, { timeout: 3000 });
      } else {
        setTimeout(start, 1);
      }
    };
    if (document.readyState === 'complete') run();
    else window.addEventListener('load', run, { once: true });
  }

  /* 转化事件：复制微信、打开二维码、点去外部站点。
   * 脚本没加载成功时这些调用自动失效，不会报错。 */
  function track(name, label) {
    if (window.gtag) window.gtag('event', name, { event_label: label || '' });
    if (window._hmt) window._hmt.push(['_trackEvent', '转化', name, label || '']);
    if (window.clarity) window.clarity('event', name);
  }

  document.addEventListener('click', function (e) {
    var el = e.target;
    if (!el || !el.closest) return;

    var copy = el.closest('[data-copy]');
    if (copy) {
      track('wechat_copy', copy.getAttribute('data-copy') || '');
      return;
    }

    var link = el.closest('a[href]');
    if (!link) return;

    var href = link.getAttribute('href') || '';
    var label = link.getAttribute('data-track') || link.getAttribute('aria-label') || link.textContent.trim();

    if (href.indexOf('wechat-qr') !== -1) {
      track('wechat_qr_open', 'wechat_qr');
      return;
    }

    if (href.indexOf('http') === 0) {
      try {
        var target = new URL(href, location.href);
        if (target.hostname !== location.hostname) {
          track('outbound_click', target.hostname);
        }
      } catch (err) {}
    }
  }, false);

  schedule();
})();
