/**
 * Vraa Components — Replaces Bootstrap JS
 * Handles: dialog modals, collapse toggles, alert dismiss, dropdowns
 */
(function () {
  'use strict';

  /* ─── DIALOG MODAL ─── */

  window.vraaModal = {
    open(dialogEl) {
      if (!dialogEl || !dialogEl.showModal) return;
      dialogEl.showModal();
      // Trap focus
      dialogEl.addEventListener('keydown', trapFocus);
    },

    close(dialogEl) {
      if (!dialogEl) return;
      dialogEl.close();
      dialogEl.removeEventListener('keydown', trapFocus);
    }
  };

  function trapFocus(e) {
    if (e.key !== 'Tab') return;
    const dialog = e.currentTarget;
    const focusable = dialog.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  // Close dialog on backdrop click
  document.addEventListener('click', function (e) {
    if (e.target.tagName === 'DIALOG' && e.target.open) {
      const rect = e.target.getBoundingClientRect();
      if (
        e.clientX < rect.left ||
        e.clientX > rect.right ||
        e.clientY < rect.top ||
        e.clientY > rect.bottom
      ) {
        e.target.close();
      }
    }
  });


  /* ─── COLLAPSE TOGGLE ─── */

  window.vraaToggle = function (targetId) {
    var el = document.getElementById(targetId);
    if (!el) return;
    var isOpen = el.classList.toggle('is-open');
    // Update aria-expanded on triggering button
    var triggers = document.querySelectorAll('[data-toggle-target="' + targetId + '"]');
    triggers.forEach(function (btn) {
      btn.setAttribute('aria-expanded', isOpen);
    });
  };


  /* ─── ALERT DISMISS ─── */

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.alert-dismiss');
    if (btn) {
      var alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        setTimeout(function () { alert.remove(); }, 250);
      }
    }
  });


  /* ─── DROPDOWN TOGGLE ─── */

  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('.nav-dropdown-toggle');
    if (toggle) {
      e.preventDefault();
      e.stopPropagation();
      var menu = toggle.nextElementSibling;
      if (menu && menu.classList.contains('nav-dropdown-menu')) {
        menu.classList.toggle('is-open');
      }
      // Close other dropdowns
      document.querySelectorAll('.nav-dropdown-menu.is-open').forEach(function (m) {
        if (m !== menu) m.classList.remove('is-open');
      });
      return;
    }
    // Close dropdowns on outside click
    document.querySelectorAll('.nav-dropdown-menu.is-open').forEach(function (m) {
      m.classList.remove('is-open');
    });
  });


  /* ─── MOBILE NAV TOGGLE ─── */

  document.addEventListener('click', function (e) {
    var hamburger = e.target.closest('.nav-hamburger');
    if (hamburger) {
      var navLinks = document.querySelector('.nav-links');
      if (navLinks) {
        navLinks.classList.toggle('is-open');
        hamburger.setAttribute('aria-expanded', navLinks.classList.contains('is-open'));
      }
    }
  });


  /* ─── ESCAPE KEY ─── */

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;

    // Close open dialogs
    var openDialog = document.querySelector('dialog[open]');
    if (openDialog) {
      openDialog.close();
      return;
    }

    // Close open dropdowns
    document.querySelectorAll('.nav-dropdown-menu.is-open').forEach(function (m) {
      m.classList.remove('is-open');
    });

    // Close mobile nav
    var navLinks = document.querySelector('.nav-links.is-open');
    if (navLinks) {
      navLinks.classList.remove('is-open');
      var hamburger = document.querySelector('.nav-hamburger');
      if (hamburger) hamburger.setAttribute('aria-expanded', 'false');
    }

    // Close open comment forms
    document.querySelectorAll('.comment-form-wrapper.is-open').forEach(function (el) {
      el.classList.remove('is-open');
    });
  });

})();
