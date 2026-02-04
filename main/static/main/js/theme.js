/**
 * Theme Toggle for Vraa
 * Handles dark/light mode switching with system preference detection
 * and localStorage persistence.
 */
(function() {
    'use strict';

    const THEME_KEY = 'vraa-theme';
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';

    /**
     * Get the preferred theme from localStorage or system preference.
     * @returns {string} 'dark' or 'light'
     */
    function getPreferredTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem(THEME_KEY);
        if (savedTheme) {
            return savedTheme;
        }

        // Fall back to system preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches
            ? THEME_DARK
            : THEME_LIGHT;
    }

    /**
     * Apply a theme to the document.
     * @param {string} theme - 'dark' or 'light'
     */
    function setTheme(theme) {
        // Set the data-theme attribute on the document element
        document.documentElement.setAttribute('data-theme', theme);

        // Save preference to localStorage
        localStorage.setItem(THEME_KEY, theme);

        // Update the toggle button appearance
        updateToggleButton(theme);
    }

    /**
     * Update the toggle button to reflect the current theme.
     * @param {string} theme - 'dark' or 'light'
     */
    function updateToggleButton(theme) {
        const button = document.getElementById('theme-toggle');
        if (!button) return;

        const icon = button.querySelector('.theme-icon');
        const label = button.getAttribute('aria-label');

        if (theme === THEME_DARK) {
            // Show sun icon (to switch to light)
            if (icon) {
                icon.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0 1a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM8 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 0zm0 13a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0v-2A.5.5 0 0 1 8 13zm8-5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2a.5.5 0 0 1 .5.5zM3 8a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1 0-1h2A.5.5 0 0 1 3 8zm10.657-5.657a.5.5 0 0 1 0 .707l-1.414 1.415a.5.5 0 1 1-.707-.708l1.414-1.414a.5.5 0 0 1 .707 0zm-9.193 9.193a.5.5 0 0 1 0 .707L3.05 13.657a.5.5 0 0 1-.707-.707l1.414-1.414a.5.5 0 0 1 .707 0zm9.193 2.121a.5.5 0 0 1-.707 0l-1.414-1.414a.5.5 0 0 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .707zM4.464 4.465a.5.5 0 0 1-.707 0L2.343 3.05a.5.5 0 1 1 .707-.707l1.414 1.414a.5.5 0 0 1 0 .708z"/>
                    </svg>
                `;
            }
            button.setAttribute('aria-label', 'Skift til lyst tema');
            button.setAttribute('title', 'Skift til lyst tema');
        } else {
            // Show moon icon (to switch to dark)
            if (icon) {
                icon.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M6 .278a.768.768 0 0 1 .08.858 7.208 7.208 0 0 0-.878 3.46c0 4.021 3.278 7.277 7.318 7.277.527 0 1.04-.055 1.533-.16a.787.787 0 0 1 .81.316.733.733 0 0 1-.031.893A8.349 8.349 0 0 1 8.344 16C3.734 16 0 12.286 0 7.71 0 4.266 2.114 1.312 5.124.06A.752.752 0 0 1 6 .278z"/>
                    </svg>
                `;
            }
            button.setAttribute('aria-label', 'Skift til m\u00f8rkt tema');
            button.setAttribute('title', 'Skift til m\u00f8rkt tema');
        }
    }

    /**
     * Toggle between dark and light themes.
     */
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;
        setTheme(newTheme);
    }

    /**
     * Initialize the theme system.
     */
    function init() {
        // Apply the preferred theme immediately
        const theme = getPreferredTheme();
        setTheme(theme);

        // Set up the toggle button
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', toggleTheme);
        }

        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            // Only auto-switch if user hasn't manually set a preference
            // We check by seeing if the current theme matches what we'd auto-select
            const savedTheme = localStorage.getItem(THEME_KEY);
            if (!savedTheme) {
                setTheme(e.matches ? THEME_DARK : THEME_LIGHT);
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Also apply theme immediately to prevent flash
    // This runs before DOMContentLoaded
    const initialTheme = getPreferredTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);

})();
