/**
 * Accessibility Enhancements for Vraa
 *
 * This module provides keyboard navigation improvements and
 * accessibility features for better screen reader support.
 */
(function() {
    'use strict';

    /**
     * Announce a message to screen readers via the live region.
     * @param {string} message - The message to announce
     * @param {string} priority - 'polite' or 'assertive'
     */
    function announce(message, priority) {
        const liveRegion = document.getElementById('aria-live-region');
        if (!liveRegion) return;

        // Set the priority if needed
        if (priority === 'assertive') {
            liveRegion.setAttribute('aria-live', 'assertive');
        } else {
            liveRegion.setAttribute('aria-live', 'polite');
        }

        // Clear and set the message (this triggers the announcement)
        liveRegion.textContent = '';
        setTimeout(function() {
            liveRegion.textContent = message;
        }, 100);

        // Clear after announcement
        setTimeout(function() {
            liveRegion.textContent = '';
            liveRegion.setAttribute('aria-live', 'polite');
        }, 3000);
    }

    // Expose announce function globally
    window.vraaAnnounce = announce;

    /**
     * Handle Escape key to close open modals and dropdowns.
     */
    function handleEscapeKey(event) {
        if (event.key !== 'Escape') return;

        // Close Bootstrap modals
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(function(modal) {
            const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
            if (closeBtn) {
                closeBtn.click();
                announce('Dialog lukket', 'polite');
            }
        });

        // Close Bootstrap dropdowns
        const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
        openDropdowns.forEach(function(dropdown) {
            const toggle = dropdown.previousElementSibling;
            if (toggle && toggle.classList.contains('dropdown-toggle')) {
                toggle.click();
            }
        });

        // Close Bootstrap collapse elements (mobile menu)
        const openCollapses = document.querySelectorAll('.navbar-collapse.show');
        openCollapses.forEach(function(collapse) {
            const toggle = document.querySelector('[data-bs-target="#' + collapse.id + '"]');
            if (toggle) {
                toggle.click();
                announce('Menu lukket', 'polite');
            }
        });
    }

    /**
     * Trap focus within a modal when it's open.
     * @param {HTMLElement} modal - The modal element
     */
    function trapFocus(modal) {
        const focusableSelector = [
            'button:not([disabled])',
            'a[href]',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ].join(', ');

        const focusableElements = modal.querySelectorAll(focusableSelector);
        if (focusableElements.length === 0) return;

        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        modal.addEventListener('keydown', function(event) {
            if (event.key !== 'Tab') return;

            if (event.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstFocusable) {
                    event.preventDefault();
                    lastFocusable.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastFocusable) {
                    event.preventDefault();
                    firstFocusable.focus();
                }
            }
        });
    }

    /**
     * Set up focus trap for modals.
     */
    function setupModalFocusTrapping() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(function(modal) {
            modal.addEventListener('shown.bs.modal', function() {
                trapFocus(modal);

                // Focus the first focusable element or the close button
                const firstFocusable = modal.querySelector(
                    'input:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
                );
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            });
        });
    }

    /**
     * Update ARIA expanded state for collapsible elements.
     */
    function setupCollapseAriaStates() {
        const collapseToggles = document.querySelectorAll('[data-bs-toggle="collapse"]');
        collapseToggles.forEach(function(toggle) {
            const targetId = toggle.getAttribute('data-bs-target');
            const target = document.querySelector(targetId);
            if (!target) return;

            // Update aria-expanded when collapse state changes
            target.addEventListener('shown.bs.collapse', function() {
                toggle.setAttribute('aria-expanded', 'true');
                // Update label if it's the mobile menu
                if (toggle.classList.contains('navbar-toggler')) {
                    toggle.setAttribute('aria-label', 'Luk navigation');
                }
            });

            target.addEventListener('hidden.bs.collapse', function() {
                toggle.setAttribute('aria-expanded', 'false');
                // Update label if it's the mobile menu
                if (toggle.classList.contains('navbar-toggler')) {
                    toggle.setAttribute('aria-label', 'Åbn navigation');
                }
            });
        });
    }

    /**
     * Add visual indication when user is navigating with keyboard.
     */
    function setupKeyboardNavigationIndicator() {
        let usingKeyboard = false;

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Tab') {
                usingKeyboard = true;
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', function() {
            usingKeyboard = false;
            document.body.classList.remove('keyboard-navigation');
        });
    }

    /**
     * Announce page navigation for single-page app behavior.
     */
    function announcePageChange() {
        const pageTitle = document.querySelector('h1');
        if (pageTitle) {
            const title = pageTitle.textContent.trim();
            announce('Side indlæst: ' + title, 'polite');
        }
    }

    /**
     * Set up form validation accessibility.
     */
    function setupFormAccessibility() {
        const forms = document.querySelectorAll('form');
        forms.forEach(function(form) {
            // Add aria-describedby for error messages
            const errorMessages = form.querySelectorAll('.text-danger, .invalid-feedback');
            errorMessages.forEach(function(error) {
                const input = error.previousElementSibling;
                if (input && (input.tagName === 'INPUT' || input.tagName === 'TEXTAREA' || input.tagName === 'SELECT')) {
                    const errorId = 'error-' + (input.id || Math.random().toString(36).substr(2, 9));
                    error.id = errorId;
                    input.setAttribute('aria-describedby', errorId);
                    input.setAttribute('aria-invalid', 'true');
                }
            });

            // Announce form submission status
            form.addEventListener('submit', function() {
                announce('Formular sendes...', 'polite');
            });
        });
    }

    /**
     * Make sure required fields are properly marked.
     */
    function setupRequiredFieldIndicators() {
        const requiredInputs = document.querySelectorAll('input[required], select[required], textarea[required]');
        requiredInputs.forEach(function(input) {
            input.setAttribute('aria-required', 'true');

            // Find the associated label
            const label = document.querySelector('label[for="' + input.id + '"]');
            if (label && !label.querySelector('.required-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'required-indicator';
                indicator.setAttribute('aria-hidden', 'true');
                indicator.textContent = ' *';
                label.appendChild(indicator);

                // Add visually hidden text for screen readers
                const srText = document.createElement('span');
                srText.className = 'sr-only';
                srText.textContent = ' (påkrævet)';
                label.appendChild(srText);
            }
        });
    }

    /**
     * Initialize all accessibility enhancements.
     */
    function init() {
        // Set up keyboard event handlers
        document.addEventListener('keydown', handleEscapeKey);

        // Set up modal focus trapping
        setupModalFocusTrapping();

        // Set up collapse aria states
        setupCollapseAriaStates();

        // Set up keyboard navigation indicator
        setupKeyboardNavigationIndicator();

        // Set up form accessibility
        setupFormAccessibility();

        // Set up required field indicators
        setupRequiredFieldIndicators();

        // Announce initial page load after a short delay
        setTimeout(announcePageChange, 500);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
