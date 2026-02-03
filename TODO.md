# Vraa Project - Feature Roadmap & TODO

This document tracks potential features and improvements for the Vraa vacation home website.

---

## Priority Legend

- **P1** - High priority (critical for usability)
- **P2** - Medium priority (significant user value)
- **P3** - Low priority (nice to have)

---

## High-Impact User Features

### P1: Password Reset Functionality
- [ ] Add Django's built-in password reset views
- [ ] Create email templates for password reset flow
- [ ] Configure email backend for production
- [ ] Add "Forgot password?" link on login page

**Why**: Users currently have no way to recover forgotten passwords. Critical for self-service.

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

### P2: In-App Notification System
- [ ] Create Notification model (user, message, read status, timestamp)
- [ ] Add notification bell icon in navigation
- [ ] Show unread count badge
- [ ] Dropdown list of recent notifications
- [ ] Mark as read on click
- [ ] Trigger notifications for:
  - [ ] Comments on user's messages
  - [ ] Booking approved/rejected
  - [ ] New replies to comments user participated in

**Why**: Users miss important updates without active notifications.

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
- [ ] Add HTMX library
- [ ] Convert comment add/delete to HTMX (no page refresh)
- [ ] Inline message editing
- [ ] Dynamic booking form validation
- [ ] Loading indicators for async operations

**Why**: Better UX while maintaining Django simplicity (no JS framework needed).

### P3: Progressive Web App (PWA)
- [ ] Add web app manifest
- [ ] Create service worker for offline caching
- [ ] Add to home screen capability
- [ ] Cache static assets for offline access
- [ ] Future: Push notifications

**Why**: Better mobile experience, works offline for viewing cached content.

### P3: Accessibility Audit
- [ ] Run automated accessibility tests (axe, WAVE)
- [ ] Test with screen reader
- [ ] Ensure WCAG 2.1 AA compliance
- [ ] Improve keyboard navigation
- [ ] Add skip links
- [ ] Review color contrast ratios

**Why**: Ensure site is usable by all family members.

### P3: API Rate Limiting
- [ ] Add rate limiting to booking API endpoint
- [ ] Consider django-ratelimit or similar
- [ ] Protect against abuse

**Why**: API endpoint is currently unprotected.

---

## Quick Wins (Low Effort, Good Value)

| Feature | Priority | Effort | Files to Modify |
|---------|----------|--------|-----------------|
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

---

**Last Updated**: 2026-02-03
