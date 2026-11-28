/* 自建访问统计上报（Cloudflare Worker）
 *
 * 页面 load 后异步发一条 beacon 到 stats.ipowerbi.icu，记录路径、标题、
 * 来源、语言、屏幕与时区；IP / 地区 / 运营商 / UA 由 Worker 从请求头读取。
 *
 * 本地预览（localhost / file://）、开启 Do Not Track 的访问一律不上报。
 * 统计失败不影响页面任何功能。
 */
(function () {
  'use strict';

  var ENDPOINT = 'https://stats.ipowerbi.icu/collect';

  var host = location.hostname;
  if (!host ||
      host === 'localhost' ||
      host === '127.0.0.1' ||
      host === '::1' ||
      location.protocol === 'file:') return;

  if (navigator.doNotTrack === '1' ||
      window.doNotTrack === '1' ||
      navigator.msDoNotTrack === '1') return;

  var sent = false;

  function send() {
    if (sent) return;
    sent = true;

    var payload;
    try {
      payload = JSON.stringify({
        p: location.pathname + location.search,
        t: document.title || '',
        r: document.referrer || '',
        l: navigator.language || '',
        s: (window.screen ? screen.width + 'x' + screen.height : ''),
        z: (function () {
          try { return Intl.DateTimeFormat().resolvedOptions().timeZone || ''; }
          catch (e) { return ''; }
        })()
      });
    } catch (e) {
      return;
    }

    try {
      if (navigator.sendBeacon) {
        // Blob + text/plain 属于 CORS 简单请求，不触发预检，也不会被跨域拦截
        var blob = new Blob([payload], { type: 'text/plain;charset=UTF-8' });
        if (navigator.sendBeacon(ENDPOINT, blob)) return;
      }
    } catch (e) {}

    try {
      fetch(ENDPOINT, {
        method: 'POST',
        body: payload,
        headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        mode: 'cors',
        credentials: 'omit',
        keepalive: true
      }).catch(function () {});
    } catch (e) {}
  }

  function schedule() {
    if (document.readyState === 'complete') {
      send();
    } else {
      window.addEventListener('load', send, { once: true });
    }
  }

  // 从浏览器往返缓存恢复（返回本页）时补记一次，服务端会按 IP + 页面去重
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) { sent = false; send(); }
  });

  schedule();
})();
