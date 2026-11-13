(() => {
  'use strict';

  /* 隐藏态由脚本自己声明：脚本没加载时，页面内容保持可见 */
  document.documentElement.classList.add('js');

  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ── 数字滚动 ─────────────────────────────────────────── */
  const runCounter = (el) => {
    const target = Number.parseInt(el.dataset.count, 10);
    if (!Number.isFinite(target)) return;
    const start = performance.now();
    const duration = 1000;

    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = String(Math.round(target * eased));
      if (p < 1) window.requestAnimationFrame(tick);
    };

    window.requestAnimationFrame(tick);
  };

  /* ── 标题数字解码 ─────────────────────────────────────── */
  const GLYPHS = '0123456789';

  const splitChars = (el) => {
    const chars = [];

    [...el.childNodes].forEach((node) => {
      if (node.nodeType !== Node.TEXT_NODE) return;

      const frag = document.createDocumentFragment();
      [...node.textContent].forEach((ch) => {
        if (/\s/.test(ch)) {
          frag.append(ch);
          return;
        }
        const span = document.createElement('span');
        span.className = 'ch';
        span.textContent = ch;
        span.dataset.ch = ch;
        frag.append(span);
        chars.push(span);
      });
      node.replaceWith(frag);
    });

    return chars;
  };

  const runDecode = (el) => {
    el.setAttribute('aria-label', el.textContent.replace(/\s+/g, ' ').trim());
    const chars = splitChars(el);
    if (!chars.length) return;

    const start = performance.now();
    const wait = 220;      // 等遮罩揭开一段再开始
    const stagger = 58;    // 每字启动间隔
    const hold = 300;      // 每字乱跳时长

    const tick = (now) => {
      let pending = false;

      chars.forEach((node, i) => {
        const t = now - start - wait - i * stagger;

        if (t < 0) {
          pending = true;
          return;
        }

        if (t < hold) {
          pending = true;
          node.classList.add('is-scrambling');
          if (!node.dataset.next || now >= Number(node.dataset.next)) {
            node.textContent = GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
            node.dataset.next = String(now + 45 + Math.random() * 45);
          }
        } else if (node.textContent !== node.dataset.ch) {
          node.textContent = node.dataset.ch;
          node.classList.remove('is-scrambling');
        }
      });

      if (pending) window.requestAnimationFrame(tick);
    };

    window.requestAnimationFrame(tick);
  };

  /* ── 入场 ─────────────────────────────────────────────── */
  const items = Array.from(document.querySelectorAll('[data-reveal]'));

  const activate = (el) => {
    el.classList.add('is-in');
    if ('decode' in el.dataset && el.dataset.decoded !== '1') {
      el.dataset.decoded = '1';
      runDecode(el);
    }
    if (el.dataset.counted === '1') return;
    el.dataset.counted = '1';
    el.querySelectorAll('[data-count]').forEach(runCounter);
  };

  if (reduce) {
    items.forEach((el) => el.classList.add('is-in'));
  } else {
    const reveal = () => {
      items.forEach((el) => {
        if (el.classList.contains('is-in')) return;
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight * 0.92 && rect.bottom > 0) activate(el);
      });
    };

    let raf = 0;
    const schedule = () => {
      if (raf) return;
      raf = window.requestAnimationFrame(() => {
        raf = 0;
        reveal();
      });
    };

    window.requestAnimationFrame(() => window.requestAnimationFrame(reveal));
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
  }

  /* ── 当前站点 ─────────────────────────────────────────── */
  const spyLinks = Array.from(document.querySelectorAll('[data-spy], [data-spy-group]'));
  const spySections = spyLinks
    .map((link) => {
      const ids = String(link.dataset.spy || link.dataset.spyGroup || '')
        .split(/\s+/)
        .filter(Boolean);
      const el = ids.map((id) => document.getElementById(id)).find(Boolean) || null;
      return { link, el };
    })
    .filter((item) => item.el);

  const updateSpy = () => {
    const y = window.scrollY + window.innerHeight * 0.4;
    let active = null;

    spySections.forEach((item) => {
      const top = item.el.getBoundingClientRect().top + window.scrollY;
      if (top <= y) active = item;
    });

    spySections.forEach((item) => {
      const on = item === active;
      item.link.classList.toggle('is-active', on);
      if (item.link.tagName !== 'A') return;
      if (on) item.link.setAttribute('aria-current', 'location');
      else item.link.removeAttribute('aria-current');
    });
  };

  /* ── 「作品」下拉：四个站点收进一个入口 ───────────────── */
  const navMore = document.querySelector('.nav-more');

  if (navMore) {
    const moreToggle = navMore.querySelector('.nav-more-toggle');
    const moreMenu = navMore.querySelector('.nav-more-menu');
    const moreOpen = () => moreToggle.getAttribute('aria-expanded') === 'true';
    const setMore = (open) => {
      moreToggle.setAttribute('aria-expanded', String(open));
      moreMenu.hidden = !open;
      navMore.classList.toggle('is-open', open);
    };

    moreToggle.addEventListener('click', () => setMore(!moreOpen()));

    document.addEventListener('click', (event) => {
      if (moreOpen() && !navMore.contains(event.target)) setMore(false);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape' || !moreOpen()) return;
      setMore(false);
      moreToggle.focus();
    });

    moreMenu.addEventListener('click', (event) => {
      if (event.target.closest('a')) setMore(false);
    });

    // 指针设备悬停即开，触屏仍靠点击
    if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      let closeTimer = 0;
      navMore.addEventListener('mouseenter', () => {
        window.clearTimeout(closeTimer);
        setMore(true);
      });
      navMore.addEventListener('mouseleave', () => {
        closeTimer = window.setTimeout(() => setMore(false), 140);
      });
    }
  }

  /* ── 移动端菜单 ───────────────────────────────────────── */
  const navToggle = document.getElementById('nav-toggle');
  const navDrawer = document.getElementById('nav-drawer');

  if (navToggle && navDrawer) {
    const setMenu = (open) => {
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.setAttribute('aria-label', open ? '关闭菜单' : '打开菜单');
      navDrawer.classList.toggle('is-open', open);
      document.documentElement.classList.toggle('nav-open', open);
    };

    navToggle.addEventListener('click', () => {
      setMenu(navToggle.getAttribute('aria-expanded') !== 'true');
    });

    navDrawer.addEventListener('click', (event) => {
      if (event.target.closest('a')) setMenu(false);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && navToggle.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        navToggle.focus();
      }
    });

    window.matchMedia('(min-width: 721px)').addEventListener('change', (event) => {
      if (event.matches) setMenu(false);
    });
  }

  /* ── 滚动：导航阴影、进度条、卡组下坠 ─────────────────── */
  const nav = document.getElementById('nav');
  const progress = document.getElementById('nav-progress');
  const hero = document.querySelector('.hero');
  const heroText = document.querySelector('.hero-text');
  const deck = document.querySelector('.deck');
  const stages = Array.from(document.querySelectorAll('[data-stage]'));

  const onScroll = () => {
    if (nav) nav.classList.toggle('is-scrolled', window.scrollY > 8);

    if (progress) {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const pct = max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0;
      progress.style.setProperty('--progress', `${pct.toFixed(1)}%`);
    }

    if (hero && deck) {
      const p = Math.min(1, Math.max(0, window.scrollY / Math.max(1, hero.offsetHeight)));
      deck.style.setProperty('--sy', `${(p * 34).toFixed(1)}px`);
      if (heroText) heroText.style.setProperty('--ho', p.toFixed(3));
    }

    if (!reduce && stages.length) {
      const offsets = stages.map((stage) => {
        const rect = stage.getBoundingClientRect();
        const mid = rect.top + rect.height / 2;
        return Math.max(-1, Math.min(1, (window.innerHeight / 2 - mid) / (window.innerHeight * 0.75)));
      });

      stages.forEach((stage, i) => {
        stage.style.setProperty('--sp', offsets[i].toFixed(3));
      });
    }

    updateSpy();
  };

  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);

  /* ── 首屏卡组随指针倾斜 ───────────────────────────────── */
  const tilt = document.querySelector('[data-tilt]');

  if (tilt && finePointer && !reduce) {
    const deckEl = tilt.querySelector('.deck');
    let frame = 0;
    let targetX = 0;
    let targetY = 0;

    const render = () => {
      frame = 0;
      if (!deckEl) return;
      deckEl.style.setProperty('--ry', `${targetX.toFixed(2)}deg`);
      deckEl.style.setProperty('--rx', `${targetY.toFixed(2)}deg`);
    };

    tilt.addEventListener('pointermove', (event) => {
      const rect = tilt.getBoundingClientRect();
      targetX = ((event.clientX - rect.left) / rect.width - 0.5) * 11;
      targetY = -((event.clientY - rect.top) / rect.height - 0.5) * 9;
      if (!frame) frame = window.requestAnimationFrame(render);
    });

    tilt.addEventListener('pointerleave', () => {
      targetX = 0;
      targetY = 0;
      if (!frame) frame = window.requestAnimationFrame(render);
    });
  }

  /* ── 站点舞台：指针视差、跟随光标、聚光灯 ─────────────── */
  if (finePointer && !reduce) {
    stages.forEach((stage) => {
      const cursor = stage.querySelector('.stage-cursor');
      let targetX = 0;
      let targetY = 0;
      let curX = 0;
      let curY = 0;
      let frame = 0;

      const render = () => {
        frame = 0;
        curX += (targetX - curX) * 0.14;
        curY += (targetY - curY) * 0.14;
        stage.style.setProperty('--mx', curX.toFixed(4));
        stage.style.setProperty('--my', curY.toFixed(4));
        if (Math.abs(targetX - curX) > 0.002 || Math.abs(targetY - curY) > 0.002) schedule();
      };

      const schedule = () => {
        if (!frame) frame = window.requestAnimationFrame(render);
      };

      const track = (event) => {
        const rect = stage.getBoundingClientRect();
        const px = event.clientX - rect.left;
        const py = event.clientY - rect.top;

        targetX = Math.max(-1, Math.min(1, (px / rect.width - 0.5) * 2));
        targetY = Math.max(-1, Math.min(1, (py / rect.height - 0.5) * 2));

        if (cursor) {
          cursor.style.setProperty('--cx', `${px.toFixed(1)}px`);
          cursor.style.setProperty('--cy', `${py.toFixed(1)}px`);
        }

        stage.style.setProperty('--gx', `${px.toFixed(1)}px`);
        stage.style.setProperty('--gy', `${py.toFixed(1)}px`);

        schedule();
      };

      stage.addEventListener('pointermove', track);
      stage.addEventListener('pointerenter', track);

      stage.addEventListener('pointerleave', () => {
        targetX = 0;
        targetY = 0;
        schedule();
      });
    });
  }

  /* ── 作品集宣传片：进入视口才下载并播放 ───────────────── */
  const promos = Array.from(document.querySelectorAll('.stage-video'));

  if (promos.length && !reduce) {
    const connection = navigator.connection;
    const saveData = Boolean(connection && (connection.saveData || /(^|-)2g$/.test(connection.effectiveType || '')));

    const canPlay = (video) => {
      const started = video.play();
      if (started && typeof started.catch === 'function') started.catch(() => {});
    };

    if (saveData) {
      /* 省流量模式：停在封面帧，不下载视频 */
    } else if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          const video = entry.target;
          if (entry.isIntersecting) {
            if (video.preload !== 'auto') video.preload = 'auto';
            canPlay(video);
          } else if (!video.paused) {
            video.pause();
          }
        });
      }, { rootMargin: '240px 0px' });

      promos.forEach((video) => observer.observe(video));
    } else {
      promos.forEach(canPlay);
    }
  }

  /* ── 按钮磁吸 ─────────────────────────────────────────── */
  if (finePointer && !reduce) {
    document.querySelectorAll('.btn').forEach((btn) => {
      btn.addEventListener('pointermove', (event) => {
        const rect = btn.getBoundingClientRect();
        const x = (event.clientX - rect.left - rect.width / 2) * 0.14;
        const y = (event.clientY - rect.top - rect.height / 2) * 0.22;
        btn.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      });

      btn.addEventListener('pointerleave', () => {
        btn.style.transform = '';
      });
    });
  }
})();
