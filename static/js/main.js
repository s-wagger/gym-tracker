/* =========================================================================
   Gym Tracker — global interaction layer
   Scroll-reveal animations + real-time 3D tilt on cards.
   ========================================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ---- Dark / light theme toggle ---- */
  var themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    var root = document.documentElement;

    function isLight() { return root.getAttribute('data-theme') === 'light'; }

    function updateIcon() {
      themeBtn.textContent = isLight() ? '🌙' : '☀️';
      themeBtn.setAttribute('aria-label', isLight() ? 'Switch to dark mode' : 'Switch to light mode');
      themeBtn.title = isLight() ? 'Switch to dark mode' : 'Switch to light mode';
    }
    updateIcon();

    themeBtn.addEventListener('click', function () {
      if (isLight()) {
        root.removeAttribute('data-theme');
        try { localStorage.setItem('gt-theme', 'dark'); } catch (e) {}
      } else {
        root.setAttribute('data-theme', 'light');
        try { localStorage.setItem('gt-theme', 'light'); } catch (e) {}
      }
      updateIcon();
    });
  }

  /* ---- Scroll reveal ---- */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in-view'); });
  }

  /* ---- Real-time 3D tilt for .tilt-card elements ---- */
  var tiltCards = document.querySelectorAll('.tilt-card');
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!reduceMotion) {
    tiltCards.forEach(function (card) {
      var inner = card.querySelector('.tilt-inner') || card;

      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = (e.clientX - rect.left) / rect.width;
        var y = (e.clientY - rect.top) / rect.height;
        var rotateY = (x - 0.5) * 10;
        var rotateX = (0.5 - y) * 10;
        inner.style.transform = 'rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) translateY(-4px)';
      });

      card.addEventListener('mouseleave', function () {
        inner.style.transform = 'rotateX(0deg) rotateY(0deg) translateY(0)';
      });
    });
  }

  /* ---- Animated count-up for stat numbers with [data-count] ---- */
  var counters = document.querySelectorAll('[data-count]');
  counters.forEach(function (el) {
    var target = parseFloat(el.getAttribute('data-count')) || 0;
    var duration = 900;
    var startTime = null;

    function step(ts) {
      if (!startTime) startTime = ts;
      var progress = Math.min((ts - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var value = Math.round(target * eased);
      el.textContent = value;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });

});
