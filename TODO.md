# Vraa Project - Feature Roadmap & TODO

This document tracks potential features and improvements for the Vraa vacation home website.

---

## Priority Legend

- **P1** - High priority (critical for usability)
- **P2** - Medium priority (significant user value)
- **P3** - Low priority (nice to have)

---

## Security & Privacy

### P0: Security Headers for Corporate Network Access *(NEW)*
- [ ] Add Content Security Policy (CSP) headers via django-csp
- [ ] Add Subresource Integrity (SRI) hashes to CDN resources
- [ ] Add Permissions-Policy header
- [ ] Enable HSTS preload (`SECURE_HSTS_PRELOAD = True`)
- [ ] Add `SECURE_REFERRER_POLICY` setting
- [ ] Verify with SSL Labs and Security Headers scanners
- [ ] Test access from corporate network

**Why**: Users report being blocked from accessing the site on corporate networks due to "site not secure" warnings. Modern corporate proxies and firewalls require proper security headers.

**Implementation**: See `implementation_plan.md` Phase 1 for detailed steps.

### P1: Require Login for Entire Site *(COMPLETED)*
- [x] Add `LoginRequiredMixin` to all views (or use middleware)
- [x] Create custom login-required middleware for site-wide protection
- [x] Exempt only login and registration pages
- [x] Redirect unauthenticated users to login page
- [x] Update brugervejledning to reflect login requirement

**Status**: Implemented via `LoginRequiredMiddleware` in `main/middleware.py`

---

## High-Impact User Features

### P1: User Profile with Display Names *(NEW)*
- [ ] Create `UserProfile` model with `display_name` field
- [ ] Add signal to auto-create profile when user is created
- [ ] Update registration form to include display name field
- [ ] Restrict username to no whitespace (best practice)
- [ ] Allow display name to contain whitespace (e.g., "Rasmus Damgaard")
- [ ] Update all templates to show display name instead of username
- [ ] Create profile edit view for users to update their display name
- [ ] Create management command to create profiles for existing users

**Why**: Users want human-readable names displayed on messages and bookings, while keeping usernames simple for login.

**Implementation**: See `implementation_plan.md` Phase 2 for detailed steps.

### P1: Family Heritage Line System *(NEW)*
- [ ] Create `HeritageLine` model with name, color, and badge class
- [ ] Add `heritage_line` ForeignKey to UserProfile
- [ ] Add `family_role` field (member, elder, head)
- [ ] Create template tag to display heritage line badges
- [ ] Show badges on message board posts
- [ ] Show badges on user profiles
- [ ] Admin interface for managing heritage lines
- [ ] Create fixture with initial 4 family lines

**Why**: The family summerhouse consists of 4 heritage lines. Users should have visible tags showing which line they belong to.

**Implementation**: See `implementation_plan.md` Phase 3 for detailed steps.

### P1: Reserved Weeks Calendar System *(NEW)*
- [ ] Create `ReservedWeek` model linking to heritage lines
- [ ] Implement rolling week allocation algorithm
- [ ] Show reserved weeks as background events on calendar
- [ ] Color-code reserved weeks by heritage line
- [ ] Add calendar legend showing line colors
- [ ] Update booking validation to check for reserved week conflicts
- [ ] Management command to generate reserved weeks for a year
- [ ] Admin interface for managing reserved weeks

**Why**: Each heritage line has 2 reserved weeks per year, rotating annually. This should be visible on the calendar and enforced during booking.

**Rotation Example** (4 lines, 2 weeks each):
| Year | Line 1 | Line 2 | Line 3 | Line 4 |
|------|--------|--------|--------|--------|
| 2024 | 26-27 | 28-29 | 30-31 | 32-33 |
| 2025 | 28-29 | 30-31 | 32-33 | 26-27 |
| 2026 | 30-31 | 32-33 | 26-27 | 28-29 |

**Implementation**: See `implementation_plan.md` Phase 4 for detailed steps.

### P1: Password Reset Functionality *(COMPLETED)*
- [x] Add Django's built-in password reset views
- [x] Create email templates for password reset flow
- [x] Configure email backend for production
- [x] Add "Forgot password?" link on login page

**Status**: Implemented with Django built-in password reset flow.

### P1: Email Notifications for Booking Status
- [ ] Send email when booking is approved
- [ ] Send email when booking is rejected (with optional reason)
- [ ] Configure email settings for production (SendGrid/Mailgun)
- [ ] Add admin setting to customize notification templates

**Why**: Users must manually check the calendar to see if their booking was approved.

### P2: User Profile & "My Bookings" Page
- [ ] Create user profile view at `/profile/` or `/mine-bookinger/`
- [ ] Display upcoming and past bookings
- [ ] Show booking status (pending/confirmed/cancelled)
- [ ] Optionally show user's message history

**Why**: Users need an easy way to see their booking history without navigating the calendar.

### P2: Calendar - Click Booking for Details
- [ ] Add click handler on calendar events
- [ ] Display modal/popover with booking details (who, dates, status)
- [ ] Show edit/cancel buttons for user's own bookings
- [ ] Different styling for own vs. others' bookings

**Why**: Currently no way to see who made a booking without hovering or checking admin.

### P2: Calendar Export (ICS)
- [ ] Add "Export to Calendar" button
- [ ] Generate ICS file for individual bookings
- [ ] Generate ICS feed URL for all confirmed bookings
- [ ] Allow subscription in Google Calendar/Outlook

**Why**: Users want to sync vacation home bookings with personal calendars.

### P3: Search Functionality
- [ ] Add search box to message board
- [ ] Full-text search on message content
- [ ] Filter by author or date range
- [ ] Search results page with pagination

**Why**: Hard to find old discussions as message board grows.

---

## Communication Enhancements

### P1: Enhanced Notification System *(NEW - Extends existing)*
- [x] Create Notification model (user, message, read status, timestamp)
- [x] Add notification bell icon in navigation
- [x] Show unread count badge
- [x] Dropdown list of recent notifications
- [x] Mark as read on click
- [x] Trigger notifications for comments on user's messages
- [x] Trigger notifications for booking approved/rejected
- [ ] **NEW**: Email notifications for new messages (opt-in)
- [ ] **NEW**: Email notifications for comments on your messages
- [ ] **NEW**: @mention system with notifications
- [ ] **NEW**: User notification preferences (all, mentions only, none)
- [ ] **NEW**: Notify users when new messages are posted to message board
- [ ] **NEW**: Create email notification templates
- [ ] **NEW**: Add SITE_URL environment variable for email links

**Why**: Users want to be notified when new messages or comments are written on the message board, especially via email.

**Current Status**: In-app notifications work for comments and booking status. Email notifications only for booking status changes.

**Implementation**: See `implementation_plan.md` Phase 5 for detailed steps.

### P2: Pin Important Messages
- [ ] Add `is_pinned` boolean field to Message model
- [ ] Admin-only ability to pin/unpin messages
- [ ] Display pinned messages at top of message board
- [ ] Visual indicator for pinned messages (pin icon)

**Why**: Important announcements get buried as new messages are posted.

### P3: Message Reactions (Emoji)
- [ ] Create Reaction model (message, user, emoji type)
- [ ] Add reaction buttons below messages (thumbs up, heart, etc.)
- [ ] Display reaction counts
- [ ] Prevent duplicate reactions from same user

**Why**: Quick acknowledgment without needing to write a comment.

### P3: @Mentions in Messages
- [ ] Parse @username in message content
- [ ] Link mentions to user profiles (if implemented)
- [ ] Send notification to mentioned user
- [ ] Autocomplete dropdown when typing @

**Why**: Direct way to get someone's attention in a message.

### P3: Photo Sharing
- [ ] Add optional image field to Message model
- [ ] Image upload form with preview
- [ ] Thumbnail display in message list
- [ ] Lightbox for full-size viewing
- [ ] Consider storage (local vs. S3/Cloudinary)

**Why**: Families want to share vacation photos easily.

---

## Administrative Improvements

### P2: Document Management System
- [ ] Create Document model (title, file, category, upload_date, uploaded_by)
- [ ] Admin interface for uploading new referater/vedtaegter
- [ ] Automatic organization by year/category
- [ ] Version history for updated documents
- [ ] Replace static PDF approach with dynamic listing

**Why**: Currently requires developer to add new PDFs manually.

### P2: User Management Dashboard
- [ ] Admin view showing pending user registrations
- [ ] Bulk approve/reject users
- [ ] Last login tracking
- [ ] User activity summary (messages, bookings)

**Why**: Easier than navigating Django admin for common tasks.

### P3: Audit/Activity Log
- [ ] Create AuditLog model (user, action, target, timestamp, details)
- [ ] Log booking approvals/rejections
- [ ] Log message/comment deletions
- [ ] Log user activations/deactivations
- [ ] Admin view to browse audit log

**Why**: No record of who did what and when.

### P3: Booking Data Export
- [ ] Export bookings to CSV
- [ ] Filter by date range, user, status
- [ ] Include in admin interface

**Why**: Useful for record-keeping and analysis.

---

## Quality of Life Features

### P3: Dark Mode
- [ ] Add CSS variables for dark theme colors
- [ ] Toggle button in navigation
- [ ] Respect system preference (`prefers-color-scheme`)
- [ ] Store preference in localStorage
- [ ] Smooth transition between themes

**Why**: Many users prefer dark mode, especially at night.

### P3: Weather Widget
- [ ] Integrate weather API (OpenWeatherMap, yr.no)
- [ ] Display current weather at Vraa location
- [ ] 7-day forecast on information or calendar page
- [ ] Cache API responses to reduce calls

**Why**: Helpful for planning trips to the vacation home.

### P3: Equipment/Inventory Checklist
- [ ] Create static page or model for house inventory
- [ ] List items available at the house
- [ ] "What to bring" vs. "What's provided" sections
- [ ] Admin-editable content

**Why**: New visitors don't know what's available at the house.

### P3: Maintenance Request System
- [ ] Create MaintenanceRequest model (user, description, status, created_at)
- [ ] Form for users to report issues
- [ ] Admin can update status (pending/in-progress/resolved)
- [ ] History of past maintenance

**Why**: No formal way to report broken appliances or needed repairs.

---

## Technical Improvements

### P2: HTMX for Dynamic Interactions
- [x] Add HTMX library
- [x] Convert comment add/delete to HTMX (no page refresh)
- [ ] Inline message editing
- [ ] Dynamic booking form validation
- [ ] Loading indicators for async operations

**Why**: Better UX while maintaining Django simplicity (no JS framework needed).

**Status**: Partially implemented - HTMX added to base template, comment create/delete now work without page refresh.

### P3: Progressive Web App (PWA)
- [x] Add web app manifest
- [x] Create service worker for offline caching
- [x] Add to home screen capability
- [x] Cache static assets for offline access
- [ ] Future: Push notifications

**Why**: Better mobile experience, works offline for viewing cached content.

**Status**: Implemented - manifest.json, service worker (sw.js), and PWA meta tags added.

### P3: Accessibility Audit
- [ ] Run automated accessibility tests (axe, WAVE)
- [ ] Test with screen reader
- [ ] Ensure WCAG 2.1 AA compliance
- [ ] Improve keyboard navigation
- [ ] Add skip links
- [ ] Review color contrast ratios

**Why**: Ensure site is usable by all family members.

### P3: API Rate Limiting
- [x] Add rate limiting to booking API endpoint
- [x] Consider django-ratelimit or similar
- [x] Protect against abuse

**Why**: API endpoint is currently unprotected.

**Status**: Implemented - django-ratelimit added with 60 requests/hour limit on BookingAPIView.

---

## Quick Wins (Low Effort, Good Value)

| Feature | Priority | Effort | Files to Modify |
|---------|----------|--------|-----------------|
| Login required sitewide | P1 | Low | middleware.py (new), settings.py |
| Password reset | P1 | Low | urls.py, templates, settings.py |
| My Bookings page | P2 | Low | views.py, urls.py, new template |
| Pin messages | P2 | Low | models.py, views.py, frontpage.html |
| ICS export | P2 | Low | views.py, urls.py |
| Click booking details | P2 | Low | kalender.html (JS only) |
| Dark mode | P3 | Medium | style.css, base.html |

---

## Implementation Notes

### Email Configuration
For booking notifications and password reset, configure email in `settings.py`:
```python
# Production (example with SendGrid)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@vraa.dk'
```

### HTMX Integration
Add to base.html:
```html
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
```

### Weather API
Consider using yr.no (Norwegian Meteorological Institute) - free, no API key required, good for Scandinavian locations.

---

## Completed Features

See CLAUDE.md for list of completed features including:
- Message board with comments
- Booking system with admin approval
- User registration with admin activation
- On-site documentation (user guide, admin guide)
- Performance optimizations
- HTTPS security
- Dark mode toggle
- Weather widget
- Notification system
- Pin important messages
- User profile page
- Calendar click booking details
- ICS calendar export
- Document management system
- User management dashboard
- Audit/Activity log
- Maintenance request system
- **Phase 6: Technical Improvements**
  - HTMX integration for dynamic comment interactions
  - Progressive Web App (PWA) support
  - API rate limiting

---

**Last Updated**: 2026-02-04

---

## New Features Summary (Implementation Plan)

The following new features have been requested and documented in `implementation_plan.md`:

| Phase | Feature | Priority | Status |
|-------|---------|----------|--------|
| 1 | Security Headers (Corporate Access) | P0 | Planned |
| 2 | User Profile & Display Names | P1 | Planned |
| 3 | Family Heritage Line System | P1 | Planned |
| 4 | Reserved Weeks Calendar | P1 | Planned |
| 5 | Enhanced Email Notifications | P1 | Planned |

For full implementation details, see **[implementation_plan.md](implementation_plan.md)**.
