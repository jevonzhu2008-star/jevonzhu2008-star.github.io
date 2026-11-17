(() => {
  'use strict';

  const nav = document.querySelector('.blog-nav');

  /* ── 导航：滚动后加分隔线，同时更新阅读进度 ───────────── */
  const readBar = document.querySelector('.read-bar');
  let ticking = false;

  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(() => {
      ticking = false;
      if (nav) nav.classList.toggle('is-scrolled', window.scrollY > 8);

      if (readBar) {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        const pct = max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0;
        readBar.style.setProperty('--read', pct.toFixed(1) + '%');
      }
    });
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ── 移动端菜单 ───────────────────────────────────────── */
  const toggle = document.querySelector('.blog-nav-toggle');
  const drawer = document.querySelector('.blog-drawer');

  if (toggle && drawer) {
    const setOpen = (open) => {
      toggle.setAttribute('aria-expanded', String(open));
      drawer.hidden = !open;
      drawer.classList.toggle('is-open', open);
      document.documentElement.classList.toggle('nav-open', open);
      if (open) drawer.querySelector('a')?.focus({ preventScroll: true });
    };

    toggle.addEventListener('click', () => {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    drawer.addEventListener('click', (event) => {
      if (event.target.closest('a')) setOpen(false);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        toggle.focus();
        setOpen(false);
      }
    });

    window.matchMedia('(min-width: 861px)').addEventListener('change', (event) => {
      if (event.matches) setOpen(false);
    });
  }

  /* ── 索引页：按标签筛选 ───────────────────────────────── */
  const filters = Array.from(document.querySelectorAll('.filter-btn'));
  const cards = Array.from(document.querySelectorAll('.post-card'));

  if (filters.length && cards.length) {
    const empty = document.querySelector('.blog-empty');

    const apply = (tag) => {
      let shown = 0;
      cards.forEach((card) => {
        const tags = (card.dataset.tags || '').split('|');
        const hit = tag === '*' || tags.includes(tag);
        card.hidden = !hit;
        if (hit) shown += 1;
      });
      if (empty) empty.hidden = shown > 0;
      filters.forEach((btn) => btn.classList.toggle('is-on', btn.dataset.tag === tag));

      const url = new URL(window.location.href);
      if (tag === '*') url.searchParams.delete('tag');
      else url.searchParams.set('tag', tag);
      window.history.replaceState(null, '', url);
    };

    filters.forEach((btn) => {
      btn.addEventListener('click', () => apply(btn.dataset.tag));
    });

    const preset = new URLSearchParams(window.location.search).get('tag');
    if (preset && filters.some((btn) => btn.dataset.tag === preset)) apply(preset);
  }

  /* ── 文章页：目录跟随 ─────────────────────────────────── */
  const tocLinks = Array.from(document.querySelectorAll('.toc a'));

  // 浏览器的 hash 是 percent-encoded，标题 id 是原始中文，比较前先解码
  const anchorOf = (link) => {
    try {
      return decodeURIComponent(link.hash.slice(1));
    } catch (error) {
      return link.hash.slice(1);
    }
  };

  const headings = tocLinks.map((link) => document.getElementById(anchorOf(link))).filter(Boolean);

  if (tocLinks.length && headings.length) {
    let active = null;

    const mark = () => {
      const line = window.scrollY + 120;
      let current = headings[0];
      headings.forEach((heading) => {
        if (heading.getBoundingClientRect().top + window.scrollY <= line) current = heading;
      });

      if (current === active) return;
      active = current;

      tocLinks.forEach((link) => {
        const on = anchorOf(link) === current.id;
        link.classList.toggle('is-on', on);
        if (on) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    };

    window.addEventListener('scroll', mark, { passive: true });
    mark();
  }
})();
