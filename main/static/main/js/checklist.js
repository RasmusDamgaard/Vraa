/**
 * Vraa Departure Checklist — localStorage persistence
 */
(function () {
  'use strict';
  var KEY = 'vraa-departure-checklist';

  function init() {
    var checkboxes = document.querySelectorAll('#checklist input[type="checkbox"]');
    if (!checkboxes.length) return;

    // Restore saved state
    var saved = [];
    try { saved = JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) {}
    checkboxes.forEach(function (cb, i) {
      if (saved[i]) {
        cb.checked = true;
        cb.closest('li').classList.add('checked-item');
      }
      cb.addEventListener('change', function () {
        cb.closest('li').classList.toggle('checked-item', cb.checked);
        save(checkboxes);
      });
    });

    // Reset button
    var resetBtn = document.getElementById('checklist-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        checkboxes.forEach(function (cb) {
          cb.checked = false;
          cb.closest('li').classList.remove('checked-item');
        });
        localStorage.removeItem(KEY);
      });
    }
  }

  function save(checkboxes) {
    var state = Array.from(checkboxes).map(function (cb) { return cb.checked; });
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
