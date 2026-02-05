/**
 * Pa11y Configuration for Vraa Accessibility Testing
 *
 * This configuration file sets up automated accessibility testing
 * using WCAG 2.1 AA standards.
 *
 * Usage:
 *   npm install -g pa11y pa11y-ci
 *   pa11y-ci --config pa11y.config.js
 *
 * Note: Requires the development server to be running at localhost:8000
 */

module.exports = {
    defaults: {
        timeout: 30000,
        standard: 'WCAG2AA',
        runners: ['axe', 'htmlcs'],
        wait: 1000,
        chromeLaunchConfig: {
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        },
        // Hide certain known issues or false positives
        hideElements: '.fc-event, .fc-daygrid-event',
        // Viewport settings for testing
        viewport: {
            width: 1280,
            height: 1024
        }
    },

    // URLs to test (requires authentication for most pages)
    urls: [
        // Public pages (can be tested without login)
        {
            url: 'http://localhost:8000/login/',
            screenCapture: './accessibility-reports/login.png'
        },
        {
            url: 'http://localhost:8000/register/',
            screenCapture: './accessibility-reports/register.png'
        },

        // Pages requiring authentication - use actions to log in first
        {
            url: 'http://localhost:8000/',
            screenCapture: './accessibility-reports/frontpage.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for url to be http://localhost:8000/'
            ]
        },
        {
            url: 'http://localhost:8000/information/',
            screenCapture: './accessibility-reports/information.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for path to be /information/'
            ]
        },
        {
            url: 'http://localhost:8000/kalender/',
            screenCapture: './accessibility-reports/kalender.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for path to be /kalender/'
            ]
        },
        {
            url: 'http://localhost:8000/referater/',
            screenCapture: './accessibility-reports/referater.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for path to be /referater/'
            ]
        },
        {
            url: 'http://localhost:8000/vedtaegter/',
            screenCapture: './accessibility-reports/vedtaegter.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for path to be /vedtaegter/'
            ]
        },
        {
            url: 'http://localhost:8000/brugervejledning/',
            screenCapture: './accessibility-reports/brugervejledning.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for path to be /brugervejledning/'
            ]
        },
        {
            url: 'http://localhost:8000/notifikationer/',
            screenCapture: './accessibility-reports/notifikationer.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for path to be /notifikationer/'
            ]
        },
        {
            url: 'http://localhost:8000/profil/',
            screenCapture: './accessibility-reports/profil.png',
            actions: [
                'navigate to http://localhost:8000/login/',
                'set field #id_username to testuser',
                'set field #id_password to testpass123',
                'click element button[type="submit"]',
                'wait for path to be /profil/'
            ]
        }
    ]
};
