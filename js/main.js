(function () {
  'use strict';

  var root = document.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- theme toggle ----------
  var toggle = document.querySelector('.theme-toggle');
  var systemDark = window.matchMedia('(prefers-color-scheme: dark)');

  function currentTheme() {
    return root.dataset.theme || (systemDark.matches ? 'dark' : 'light');
  }

  function syncToggleLabel() {
    var dark = currentTheme() === 'dark';
    toggle.setAttribute('aria-pressed', String(dark));
    toggle.setAttribute('aria-label', dark ? 'ライトモードに切り替え' : 'ダークモードに切り替え');
  }

  toggle.addEventListener('click', function () {
    var next = currentTheme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
    syncToggleLabel();
  });
  systemDark.addEventListener('change', syncToggleLabel);
  syncToggleLabel();

  // ---------- header border on scroll ----------
  var header = document.querySelector('.site-header');
  function onScroll() {
    header.classList.toggle('is-scrolled', window.scrollY > 8);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---------- works filter ----------
  var filters = document.querySelector('.filters');
  var works = Array.prototype.slice.call(document.querySelectorAll('.work'));
  var chips = Array.prototype.slice.call(filters.querySelectorAll('.chip'));

  function matches(work, cat) {
    return cat === 'all' || work.dataset.cat.split(' ').indexOf(cat) !== -1;
  }

  chips.forEach(function (chip) {
    var cat = chip.dataset.filter;
    chip.querySelector('.chip__n').textContent = works.filter(function (w) { return matches(w, cat); }).length;

    chip.addEventListener('click', function () {
      chips.forEach(function (c) {
        var active = c === chip;
        c.classList.toggle('is-active', active);
        c.setAttribute('aria-pressed', String(active));
      });
      works.forEach(function (w) {
        var show = matches(w, cat);
        w.hidden = !show;
        if (show) w.classList.add('is-visible');
      });
    });
  });
  filters.hidden = false;

  // ---------- reveal on scroll ----------
  var reveals = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window) || reduceMotion) {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  }

  // ---------- current section in nav ----------
  var navLinks = document.querySelectorAll('.nav a');
  if ('IntersectionObserver' in window) {
    var navIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        navLinks.forEach(function (a) {
          a.classList.toggle('is-current', a.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    navLinks.forEach(function (a) {
      var target = document.querySelector(a.getAttribute('href'));
      if (target) navIo.observe(target);
    });
  }

  // ---------- scoreboard count-up ----------
  if (!reduceMotion) {
    document.querySelectorAll('.panel__digits').forEach(function (el) {
      var target = Number(el.dataset.count);
      var start = performance.now();
      var duration = 900;
      function tick(now) {
        var t = Math.min(1, (now - start) / duration);
        var value = Math.round(target * (1 - Math.pow(1 - t, 3)));
        el.textContent = String(value).padStart(2, '0');
        if (t < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  // ---------- footer year ----------
  document.getElementById('year').textContent = new Date().getFullYear();
})();
