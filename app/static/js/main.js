/**
 * SecondSpark — Enhanced Main JavaScript v2
 * Features: Navbar scroll, flash toasts, scroll-reveal, counter animation,
 *           save/unsave projects, mobile menu, live search, filter chips
 */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Translucent Floating Dock Scroll Effect ── */
  const navbarWrapper = document.querySelector('.navbar-wrapper');
  if (navbarWrapper) {
    const onScroll = () => navbarWrapper.classList.toggle('scrolled', window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ── Flash Toast Auto-Dismiss ── */
  document.querySelectorAll('.flash-toast').forEach(toast => {
    const close = toast.querySelector('.flash-close');
    const dismiss = () => {
      toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 320);
    };
    if (close) close.addEventListener('click', dismiss);
    setTimeout(dismiss, 5000);
  });

  /* ── Animated Translucent Dock Capsule Indicator ── */
  const dockLinks = document.getElementById('nav-dock-links');
  const dockIndicator = document.getElementById('nav-dock-indicator');
  if (dockLinks && dockIndicator) {
    const links = dockLinks.querySelectorAll('.nav-link');
    const activeLink = dockLinks.querySelector('.nav-link.active');

    function positionIndicator(target) {
      if (!target) {
        dockIndicator.style.opacity = '0';
        return;
      }
      const parentRect = dockLinks.getBoundingClientRect();
      const targetRect = target.getBoundingClientRect();
      const left = targetRect.left - parentRect.left;
      const width = targetRect.width;

      dockIndicator.style.left = `${left}px`;
      dockIndicator.style.width = `${width}px`;
      dockIndicator.style.opacity = '1';
    }

    // Set initial position on active page
    if (activeLink) {
      setTimeout(() => positionIndicator(activeLink), 100);
    }

    links.forEach(link => {
      link.addEventListener('mouseenter', () => positionIndicator(link));
    });

    dockLinks.addEventListener('mouseleave', () => {
      positionIndicator(activeLink);
    });

    window.addEventListener('resize', () => {
      if (activeLink) positionIndicator(activeLink);
    });
  }

  /* ── Mobile Navigation Drawer ── */
  const mobileToggle = document.querySelector('.mobile-nav-toggle');
  const mobileDrawer = document.querySelector('.mobile-nav-drawer');
  const mobileOverlay = document.querySelector('.mobile-nav-overlay');
  const mobileClose = document.querySelector('.mobile-drawer-close');

  function openDrawer() {
    if (mobileDrawer) mobileDrawer.classList.add('active');
    if (mobileOverlay) mobileOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    if (mobileDrawer) mobileDrawer.classList.remove('active');
    if (mobileOverlay) mobileOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (mobileToggle) mobileToggle.addEventListener('click', openDrawer);
  if (mobileClose) mobileClose.addEventListener('click', closeDrawer);
  if (mobileOverlay) mobileOverlay.addEventListener('click', closeDrawer);

  /* ── User dropdown ── */
  const userBtn  = document.querySelector('.user-btn');
  const dropdown = document.querySelector('.dropdown-menu');
  if (userBtn && dropdown) {
    userBtn.addEventListener('click', e => {
      e.stopPropagation();
      dropdown.classList.toggle('active');
    });
    document.addEventListener('click', () => dropdown.classList.remove('active'));
  }

  /* ══════════════════════════════════════════════
     ANIMATED STAT COUNTER
     Counts from 0 → target value over 1.6 s
  ══════════════════════════════════════════════ */
  function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    if (isNaN(target)) return;
    const suffix = el.dataset.suffix || '';
    const duration = 1600;
    const start = performance.now();

    el.classList.add('counting');

    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(eased * target) + suffix;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target + suffix;
        el.classList.remove('counting');
      }
    }
    requestAnimationFrame(step);
  }

  /* ══════════════════════════════════════════════
     SCROLL-REVEAL  (IntersectionObserver)
     Also triggers counters when stats enter view
  ══════════════════════════════════════════════ */
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  // Counter observer — fires counters when stats section scrolls into view
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('[data-target]').forEach(animateCounter);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  const heroStats = document.querySelector('.hero-stats');
  if (heroStats) counterObserver.observe(heroStats);

  /* ══════════════════════════════════════════════
     SAVE / UNSAVE PROJECT (heart button)
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.save-project-btn').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.preventDefault();
      e.stopPropagation();
      const id = btn.dataset.projectId;
      try {
        const res = await fetch(`/projects/${id}/save`, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const data = await res.json();
        const icon = btn.querySelector('i');
        if (data.saved) {
          icon.className = 'fa-solid fa-heart';
          btn.style.color = '#EF4444';
        } else {
          icon.className = 'fa-regular fa-heart';
          btn.style.color = '';
        }
      } catch (_) {}
    });
  });

  /* ══════════════════════════════════════════════
     FILTER CHIPS (browse page)
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.filter-chip[data-filter]').forEach(chip => {
    chip.addEventListener('click', () => {
      const group = chip.dataset.group;
      if (group) {
        document.querySelectorAll(`.filter-chip[data-group="${group}"]`).forEach(c => c.classList.remove('active'));
      }
      chip.classList.toggle('active');
    });
  });

  /* ══════════════════════════════════════════════
     LIVE SEARCH INPUT DEBOUNCE
  ══════════════════════════════════════════════ */
  const searchInput = document.getElementById('live-search');
  const searchResults = document.getElementById('search-results-drop');
  if (searchInput && searchResults) {
    let timer;
    searchInput.addEventListener('input', () => {
      clearTimeout(timer);
      const q = searchInput.value.trim();
      if (!q) { searchResults.style.display = 'none'; return; }
      timer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=6`);
          const data = await res.json();
          if (!data.results || !data.results.length) { searchResults.style.display = 'none'; return; }
          searchResults.innerHTML = data.results.map(p => `
            <a href="/projects/${p.id}" class="search-result-item">
              <div class="search-result-title">${p.title}</div>
              <div class="search-result-meta">${p.category} · ${p.status}</div>
            </a>`).join('');
          searchResults.style.display = 'block';
        } catch (_) {}
      }, 280);
    });
    document.addEventListener('click', e => {
      if (!searchInput.contains(e.target)) searchResults.style.display = 'none';
    });
  }

  /* ══════════════════════════════════════════════
     ADD .reveal CLASS to key sections automatically
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.process-card, .category-card, .project-card, .review-card').forEach((el, i) => {
    el.classList.add('reveal');
    if (i % 4 === 1) el.classList.add('reveal-delay-1');
    if (i % 4 === 2) el.classList.add('reveal-delay-2');
    if (i % 4 === 3) el.classList.add('reveal-delay-3');
    revealObserver.observe(el);
  });

  /* ══════════════════════════════════════════════
     SECTION HEADERS REVEAL
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.section-header').forEach(el => {
    el.classList.add('reveal');
    revealObserver.observe(el);
  });

  /* ══════════════════════════════════════════════
     STAR RATING PICKER (review form)
  ══════════════════════════════════════════════ */
  const starPicker = document.getElementById('star-picker');
  if (starPicker) {
    const stars = starPicker.querySelectorAll('.star-btn');
    const input = document.getElementById('rating-value');
    stars.forEach((star, idx) => {
      star.addEventListener('mouseenter', () => {
        stars.forEach((s, i) => s.classList.toggle('hovered', i <= idx));
      });
      star.addEventListener('mouseleave', () => {
        stars.forEach(s => s.classList.remove('hovered'));
      });
      star.addEventListener('click', () => {
        const val = idx + 1;
        if (input) input.value = val;
        stars.forEach((s, i) => s.classList.toggle('selected', i <= idx));
      });
    });
    starPicker.addEventListener('mouseleave', () => {
      stars.forEach(s => s.classList.remove('hovered'));
    });
  }

  /* ══════════════════════════════════════════════
     SMOOTH SCROLL for anchor links
  ══════════════════════════════════════════════ */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const id = a.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ══════════════════════════════════════════════
     3D CARD TILT on project cards (mouse hover)
  ══════════════════════════════════════════════ */
  document.querySelectorAll('.project-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width  - 0.5) * 12;
      const y = ((e.clientY - rect.top)  / rect.height - 0.5) * -12;
      card.style.transform = `translateY(-6px) rotateX(${y}deg) rotateY(${x}deg) scale(1.01)`;
      card.style.transition = 'transform 0.08s linear';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
      card.style.transition = 'transform 0.4s cubic-bezier(0.16,1,0.3,1)';
    });
  });

});
