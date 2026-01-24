# Testing Strategy for Vraa

This document outlines a comprehensive testing plan for the Vraa Django application, covering models, views, forms, admin functionality, and integration tests.

---

## Table of Contents

1. [Current State](#current-state)
2. [Testing Philosophy](#testing-philosophy)
3. [Test Categories](#test-categories)
4. [Model Tests](#model-tests)
5. [View Tests](#view-tests)
6. [Form Tests](#form-tests)
7. [Admin Tests](#admin-tests)
8. [Integration Tests](#integration-tests)
9. [Implementation Priority](#implementation-priority)
10. [Test Utilities](#test-utilities)
11. [Running Tests](#running-tests)

---

## Current State

### Existing Tests

The project has minimal test coverage in `main/tests.py`:

| Test | Status | Notes |
|------|--------|-------|
| `test_frontpage` | Passing | Basic 200 check |
| `test_bootstrap_included` | Passing | Checks Bootstrap CDN |
| `test_information_page` | Passing | Basic 200 check |
| `test_referater_page` | Passing | Basic 200 check |
| `test_vedtaegter_page` | Passing | Basic 200 check |
| `test_kalender_page` | **FAILING** | Bug: expects 200 but page requires login |

### Known Bug

`test_kalender_page` will fail because `KalenderView` uses `LoginRequiredMixin`. The test should either:
- Authenticate a user before making the request, OR
- Assert redirect to login page (302)

---

## Testing Philosophy

1. **Test behavior, not implementation** - Focus on what the code does, not how
2. **Test the happy path first** - Then edge cases and error conditions
3. **Use meaningful test names** - `test_booking_overlap_validation_raises_error`
4. **Keep tests independent** - Each test should be self-contained
5. **Use factories/fixtures** - Create reusable test data
6. **Test permissions explicitly** - Verify auth requirements

---

## Test Categories

### 1. Unit Tests
- Model methods and validation
- Form validation logic
- Utility functions

### 2. Integration Tests
- View request/response cycles
- Database relationships
- Admin actions

### 3. Permission Tests
- Authentication requirements
- Authorization (ownership) checks

---

## Model Tests

### Message Model

```python
class MessageModelTests(TestCase):
    """Tests for the Message model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    # Creation Tests
    def test_message_creation(self):
        """A message can be created with valid data."""
        message = Message.objects.create(
            author=self.user,
            content='Test message content'
        )
        self.assertEqual(message.author, self.user)
        self.assertEqual(message.content, 'Test message content')
        self.assertIsNotNone(message.created_at)
        self.assertIsNotNone(message.updated_at)

    def test_message_str_representation(self):
        """__str__ returns content preview with author."""
        message = Message.objects.create(
            author=self.user,
            content='A' * 100  # Long content
        )
        str_repr = str(message)
        self.assertIn(self.user.username, str_repr)
        self.assertLessEqual(len(str_repr), 80)  # Truncated

    # Ordering Tests
    def test_messages_ordered_by_created_at_descending(self):
        """Messages are ordered newest first."""
        msg1 = Message.objects.create(author=self.user, content='First')
        msg2 = Message.objects.create(author=self.user, content='Second')
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], msg2)  # Newest first
        self.assertEqual(messages[1], msg1)

    # Cascade Delete Tests
    def test_message_deleted_when_user_deleted(self):
        """Message is deleted when author is deleted."""
        message = Message.objects.create(author=self.user, content='Test')
        message_id = message.id
        self.user.delete()
        self.assertFalse(Message.objects.filter(id=message_id).exists())

    # Field Validation Tests
    def test_message_content_max_length(self):
        """Content respects max_length of 2000 characters."""
        message = Message(author=self.user, content='A' * 2001)
        with self.assertRaises(ValidationError):
            message.full_clean()
```

### Comment Model

```python
class CommentModelTests(TestCase):
    """Tests for the Comment model."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass123')
        self.message = Message.objects.create(
            author=self.user,
            content='Test message'
        )

    # Creation Tests
    def test_comment_creation(self):
        """A comment can be created with valid data."""
        comment = Comment.objects.create(
            message=self.message,
            author=self.user,
            content='Test comment'
        )
        self.assertEqual(comment.message, self.message)
        self.assertEqual(comment.author, self.user)

    def test_comment_str_representation(self):
        """__str__ returns content preview with author."""
        comment = Comment.objects.create(
            message=self.message,
            author=self.user,
            content='B' * 100
        )
        str_repr = str(comment)
        self.assertIn(self.user.username, str_repr)

    # Ordering Tests
    def test_comments_ordered_by_created_at_ascending(self):
        """Comments are ordered oldest first (chronological)."""
        c1 = Comment.objects.create(
            message=self.message, author=self.user, content='First'
        )
        c2 = Comment.objects.create(
            message=self.message, author=self.user, content='Second'
        )
        comments = list(self.message.comments.all())
        self.assertEqual(comments[0], c1)  # Oldest first
        self.assertEqual(comments[1], c2)

    # Cascade Delete Tests
    def test_comment_deleted_when_message_deleted(self):
        """Comment is deleted when parent message is deleted."""
        comment = Comment.objects.create(
            message=self.message, author=self.user, content='Test'
        )
        comment_id = comment.id
        self.message.delete()
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_comment_deleted_when_user_deleted(self):
        """Comment is deleted when author is deleted."""
        comment = Comment.objects.create(
            message=self.message, author=self.user, content='Test'
        )
        comment_id = comment.id
        self.user.delete()
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    # Related Name Tests
    def test_message_comments_related_name(self):
        """Comments accessible via message.comments."""
        Comment.objects.create(
            message=self.message, author=self.user, content='Comment 1'
        )
        Comment.objects.create(
            message=self.message, author=self.user, content='Comment 2'
        )
        self.assertEqual(self.message.comments.count(), 2)

    # Field Validation Tests
    def test_comment_content_max_length(self):
        """Content respects max_length of 1000 characters."""
        comment = Comment(
            message=self.message,
            author=self.user,
            content='A' * 1001
        )
        with self.assertRaises(ValidationError):
            comment.full_clean()
```

### Booking Model

```python
class BookingModelTests(TestCase):
    """Tests for the Booking model."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass123')
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)

    # Creation Tests
    def test_booking_creation(self):
        """A booking can be created with valid data."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.tomorrow,
            end_date=self.next_week,
            status='pending'
        )
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.status, 'pending')

    def test_booking_str_representation(self):
        """__str__ returns booking summary."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.tomorrow,
            end_date=self.next_week,
            status='pending'
        )
        str_repr = str(booking)
        self.assertIn(self.user.username, str_repr)
        self.assertIn(str(self.tomorrow), str_repr)

    # Duration Property Tests
    def test_duration_days_property(self):
        """duration_days returns correct number of days."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.today,
            end_date=self.today + timedelta(days=3),
            status='pending'
        )
        self.assertEqual(booking.duration_days, 3)

    # Validation Tests
    def test_end_date_must_be_after_start_date(self):
        """Validation error when end_date <= start_date."""
        booking = Booking(
            user=self.user,
            start_date=self.tomorrow,
            end_date=self.today,  # Before start
            status='pending'
        )
        with self.assertRaises(ValidationError) as ctx:
            booking.full_clean()
        self.assertIn('end_date', str(ctx.exception))

    def test_same_start_and_end_date_invalid(self):
        """Validation error when end_date equals start_date."""
        booking = Booking(
            user=self.user,
            start_date=self.tomorrow,
            end_date=self.tomorrow,  # Same as start
            status='pending'
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()

    # Overlap Detection Tests
    def test_overlapping_confirmed_booking_raises_error(self):
        """Cannot create booking that overlaps a confirmed booking."""
        # Create confirmed booking
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='confirmed'
        )
        # Try to create overlapping booking
        overlapping = Booking(
            user=self.user,
            start_date=self.today + timedelta(days=7),  # Overlaps
            end_date=self.today + timedelta(days=12),
            status='pending'
        )
        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_overlapping_pending_booking_allowed(self):
        """Can create booking that overlaps a pending booking."""
        # Create pending booking
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='pending'  # Not confirmed
        )
        # Overlapping booking should be allowed
        overlapping = Booking(
            user=self.user,
            start_date=self.today + timedelta(days=7),
            end_date=self.today + timedelta(days=12),
            status='pending'
        )
        overlapping.full_clean()  # Should not raise

    def test_adjacent_bookings_allowed(self):
        """Bookings can be adjacent (one ends when another starts)."""
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='confirmed'
        )
        # Adjacent booking (starts when previous ends)
        adjacent = Booking(
            user=self.user,
            start_date=self.today + timedelta(days=10),
            end_date=self.today + timedelta(days=15),
            status='pending'
        )
        adjacent.full_clean()  # Should not raise

    def test_cancelled_booking_does_not_block_overlap(self):
        """Cancelled bookings don't block new bookings."""
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='cancelled'
        )
        # Overlapping booking should be allowed
        overlapping = Booking(
            user=self.user,
            start_date=self.today + timedelta(days=7),
            end_date=self.today + timedelta(days=12),
            status='pending'
        )
        overlapping.full_clean()  # Should not raise

    # Status Choices Tests
    def test_valid_status_choices(self):
        """Only valid status choices are accepted."""
        booking = Booking(
            user=self.user,
            start_date=self.tomorrow,
            end_date=self.next_week,
            status='invalid_status'
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()

    # Ordering Tests
    def test_bookings_ordered_by_start_date(self):
        """Bookings are ordered by start_date ascending."""
        b2 = Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=10),
            end_date=self.today + timedelta(days=12),
            status='pending'
        )
        b1 = Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=7),
            status='pending'
        )
        bookings = list(Booking.objects.all())
        self.assertEqual(bookings[0], b1)  # Earlier first
        self.assertEqual(bookings[1], b2)

    # Notes Field Tests
    def test_notes_optional(self):
        """Booking can be created without notes."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.tomorrow,
            end_date=self.next_week,
            status='pending'
            # No notes
        )
        self.assertEqual(booking.notes, '')

    def test_notes_max_length(self):
        """Notes respects max_length of 500 characters."""
        booking = Booking(
            user=self.user,
            start_date=self.tomorrow,
            end_date=self.next_week,
            status='pending',
            notes='A' * 501
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()
```

---

## View Tests

### Public Pages (No Auth Required)

```python
class PublicPageTests(TestCase):
    """Tests for pages that don't require authentication."""

    def test_frontpage_accessible(self):
        """Frontpage is accessible without login."""
        response = self.client.get(reverse('main:frontpage'))
        self.assertEqual(response.status_code, 200)

    def test_frontpage_uses_correct_template(self):
        """Frontpage uses frontpage.html template."""
        response = self.client.get(reverse('main:frontpage'))
        self.assertTemplateUsed(response, 'main/frontpage.html')

    def test_frontpage_contains_messages(self):
        """Frontpage displays messages from database."""
        user = User.objects.create_user('testuser', password='pass')
        Message.objects.create(author=user, content='Hello World')
        response = self.client.get(reverse('main:frontpage'))
        self.assertContains(response, 'Hello World')

    def test_frontpage_pagination(self):
        """Frontpage paginates at 20 messages."""
        user = User.objects.create_user('testuser', password='pass')
        for i in range(25):
            Message.objects.create(author=user, content=f'Message {i}')
        response = self.client.get(reverse('main:frontpage'))
        self.assertEqual(len(response.context['message_list']), 20)
        self.assertTrue(response.context['is_paginated'])

    def test_information_page_accessible(self):
        """Information page is accessible without login."""
        response = self.client.get(reverse('main:information'))
        self.assertEqual(response.status_code, 200)

    def test_referater_page_accessible(self):
        """Referater page is accessible without login."""
        response = self.client.get(reverse('main:referater'))
        self.assertEqual(response.status_code, 200)

    def test_vedtaegter_page_accessible(self):
        """Vedtaegter page is accessible without login."""
        response = self.client.get(reverse('main:vedtaegter'))
        self.assertEqual(response.status_code, 200)

    def test_bootstrap_included_in_base_template(self):
        """Base template includes Bootstrap 5.3.3."""
        response = self.client.get(reverse('main:frontpage'))
        self.assertContains(response, 'bootstrap@5.3.3')
```

### Authentication Required Pages

```python
class AuthenticationRequiredTests(TestCase):
    """Tests for pages requiring authentication."""

    def test_kalender_redirects_anonymous_user(self):
        """Kalender page redirects to login for anonymous users."""
        response = self.client.get(reverse('main:kalender'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_kalender_accessible_when_logged_in(self):
        """Kalender page is accessible when logged in."""
        user = User.objects.create_user('testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('main:kalender'))
        self.assertEqual(response.status_code, 200)

    def test_message_create_requires_login(self):
        """Message creation requires authentication."""
        response = self.client.get(reverse('main:message_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_booking_create_requires_login(self):
        """Booking creation requires authentication."""
        response = self.client.get(reverse('main:booking_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_comment_create_requires_login(self):
        """Comment creation requires authentication."""
        user = User.objects.create_user('testuser', password='pass')
        message = Message.objects.create(author=user, content='Test')
        response = self.client.get(
            reverse('main:comment_create', kwargs={'message_id': message.id})
        )
        self.assertEqual(response.status_code, 302)
```

### Message CRUD Tests

```python
class MessageViewTests(TestCase):
    """Tests for message CRUD operations."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')
        self.other_user = User.objects.create_user('other', password='otherpass')
        self.message = Message.objects.create(
            author=self.user,
            content='Original content'
        )

    def test_create_message_when_logged_in(self):
        """Authenticated user can create a message."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:message_create'),
            {'content': 'New message content'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Message.objects.filter(content='New message content').exists())

    def test_message_author_set_automatically(self):
        """Message author is set to logged-in user."""
        self.client.login(username='testuser', password='testpass')
        self.client.post(
            reverse('main:message_create'),
            {'content': 'New message'}
        )
        message = Message.objects.get(content='New message')
        self.assertEqual(message.author, self.user)

    def test_owner_can_edit_message(self):
        """Message author can edit their message."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:message_update', kwargs={'pk': self.message.pk}),
            {'content': 'Updated content'}
        )
        self.assertEqual(response.status_code, 302)
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, 'Updated content')

    def test_non_owner_cannot_edit_message(self):
        """Non-author cannot edit a message."""
        self.client.login(username='other', password='otherpass')
        response = self.client.get(
            reverse('main:message_update', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_owner_can_delete_message(self):
        """Message author can delete their message."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:message_delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(pk=self.message.pk).exists())

    def test_non_owner_cannot_delete_message(self):
        """Non-author cannot delete a message."""
        self.client.login(username='other', password='otherpass')
        response = self.client.post(
            reverse('main:message_delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Message.objects.filter(pk=self.message.pk).exists())
```

### Comment View Tests

```python
class CommentViewTests(TestCase):
    """Tests for comment CRUD operations."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')
        self.other_user = User.objects.create_user('other', password='otherpass')
        self.message = Message.objects.create(author=self.user, content='Message')
        self.comment = Comment.objects.create(
            message=self.message,
            author=self.user,
            content='Original comment'
        )

    def test_create_comment_when_logged_in(self):
        """Authenticated user can create a comment."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:comment_create', kwargs={'message_id': self.message.id}),
            {'content': 'New comment'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(
                message=self.message,
                content='New comment'
            ).exists()
        )

    def test_comment_linked_to_correct_message(self):
        """Comment is associated with the correct message."""
        self.client.login(username='testuser', password='testpass')
        self.client.post(
            reverse('main:comment_create', kwargs={'message_id': self.message.id}),
            {'content': 'New comment'}
        )
        comment = Comment.objects.get(content='New comment')
        self.assertEqual(comment.message, self.message)

    def test_owner_can_delete_comment(self):
        """Comment author can delete their comment."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:comment_delete', kwargs={'pk': self.comment.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_non_owner_cannot_delete_comment(self):
        """Non-author cannot delete a comment."""
        self.client.login(username='other', password='otherpass')
        response = self.client.post(
            reverse('main:comment_delete', kwargs={'pk': self.comment.pk})
        )
        self.assertEqual(response.status_code, 403)
```

### Booking View Tests

```python
class BookingViewTests(TestCase):
    """Tests for booking CRUD operations."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')
        self.other_user = User.objects.create_user('other', password='otherpass')
        self.today = date.today()
        self.booking = Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=10),
            end_date=self.today + timedelta(days=15),
            status='pending'
        )

    def test_create_booking_when_logged_in(self):
        """Authenticated user can create a booking."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:booking_create'),
            {
                'start_date': (self.today + timedelta(days=20)).isoformat(),
                'end_date': (self.today + timedelta(days=25)).isoformat(),
                'notes': 'Test booking'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(notes='Test booking').exists())

    def test_booking_status_defaults_to_pending(self):
        """New bookings have pending status."""
        self.client.login(username='testuser', password='testpass')
        self.client.post(
            reverse('main:booking_create'),
            {
                'start_date': (self.today + timedelta(days=20)).isoformat(),
                'end_date': (self.today + timedelta(days=25)).isoformat(),
            }
        )
        booking = Booking.objects.exclude(pk=self.booking.pk).first()
        self.assertEqual(booking.status, 'pending')

    def test_owner_can_edit_pending_booking(self):
        """Owner can edit their pending booking."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:booking_update', kwargs={'pk': self.booking.pk}),
            {
                'start_date': (self.today + timedelta(days=11)).isoformat(),
                'end_date': (self.today + timedelta(days=16)).isoformat(),
                'notes': 'Updated notes'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.notes, 'Updated notes')

    def test_owner_cannot_edit_confirmed_booking(self):
        """Owner cannot edit a confirmed booking."""
        self.booking.status = 'confirmed'
        self.booking.save()
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('main:booking_update', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_non_owner_cannot_edit_booking(self):
        """Non-owner cannot edit a booking."""
        self.client.login(username='other', password='otherpass')
        response = self.client.get(
            reverse('main:booking_update', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_can_delete_booking(self):
        """Owner can cancel their booking."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('main:booking_delete', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())

    def test_non_owner_cannot_delete_booking(self):
        """Non-owner cannot cancel a booking."""
        self.client.login(username='other', password='otherpass')
        response = self.client.post(
            reverse('main:booking_delete', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)
```

### Booking API Tests

```python
class BookingAPIViewTests(TestCase):
    """Tests for the BookingAPIView JSON endpoint."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')
        self.today = date.today()

    def test_api_requires_authentication(self):
        """API endpoint requires login."""
        response = self.client.get(reverse('main:booking_api'))
        self.assertEqual(response.status_code, 302)

    def test_api_returns_json(self):
        """API returns JSON content type."""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('main:booking_api'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_returns_booking_list(self):
        """API returns list of bookings."""
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='confirmed'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('main:booking_api'))
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_api_event_format(self):
        """API returns events in FullCalendar format."""
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='confirmed'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertIn('id', event)
        self.assertIn('title', event)
        self.assertIn('start', event)
        self.assertIn('end', event)
        self.assertIn('color', event)
        self.assertIn('extendedProps', event)

    def test_confirmed_booking_green_color(self):
        """Confirmed bookings have green color."""
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='confirmed'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertEqual(event['color'], '#28a745')  # Green

    def test_pending_booking_yellow_color(self):
        """Pending bookings have yellow color."""
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='pending'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertEqual(event['color'], '#ffc107')  # Yellow

    def test_api_includes_ownership_flag(self):
        """API includes isOwner flag in extendedProps."""
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='pending'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertTrue(event['extendedProps']['isOwner'])
```

### Registration Tests

```python
class RegistrationViewTests(TestCase):
    """Tests for user registration."""

    def test_registration_page_accessible(self):
        """Registration page is accessible."""
        response = self.client.get(reverse('main:register'))
        self.assertEqual(response.status_code, 200)

    def test_user_registration_creates_inactive_user(self):
        """Registered users are created as inactive."""
        response = self.client.post(
            reverse('main:register'),
            {
                'username': 'newuser',
                'password1': 'complexpass123!',
                'password2': 'complexpass123!'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)

    def test_inactive_user_cannot_login(self):
        """Inactive users cannot log in."""
        # Create inactive user
        user = User.objects.create_user('newuser', password='testpass')
        user.is_active = False
        user.save()
        # Attempt login
        login_success = self.client.login(username='newuser', password='testpass')
        self.assertFalse(login_success)
```

---

## Form Tests

### BookingForm Tests

```python
class BookingFormTests(TestCase):
    """Tests for BookingForm validation."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')
        self.today = date.today()

    def test_valid_form(self):
        """Form is valid with correct data."""
        form = BookingForm(data={
            'start_date': self.today + timedelta(days=5),
            'end_date': self.today + timedelta(days=10),
            'notes': 'Test booking'
        })
        self.assertTrue(form.is_valid())

    def test_end_date_before_start_date_invalid(self):
        """Form is invalid when end_date < start_date."""
        form = BookingForm(data={
            'start_date': self.today + timedelta(days=10),
            'end_date': self.today + timedelta(days=5),  # Before start
        })
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_overlapping_booking_invalid(self):
        """Form is invalid when overlapping confirmed booking."""
        # Create confirmed booking
        Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='confirmed'
        )
        # Try overlapping booking
        form = BookingForm(data={
            'start_date': self.today + timedelta(days=7),
            'end_date': self.today + timedelta(days=12),
        })
        self.assertFalse(form.is_valid())

    def test_edit_excludes_self_from_overlap_check(self):
        """When editing, form doesn't flag self as overlap."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='confirmed'
        )
        # Edit same booking (same dates)
        form = BookingForm(
            instance=booking,
            data={
                'start_date': self.today + timedelta(days=5),
                'end_date': self.today + timedelta(days=10),
            }
        )
        self.assertTrue(form.is_valid())

    def test_notes_optional(self):
        """Notes field is optional."""
        form = BookingForm(data={
            'start_date': self.today + timedelta(days=5),
            'end_date': self.today + timedelta(days=10),
            # No notes
        })
        self.assertTrue(form.is_valid())

    def test_date_widgets_use_html5_date_input(self):
        """Date fields use HTML5 date input type."""
        form = BookingForm()
        self.assertEqual(
            form.fields['start_date'].widget.input_type,
            'date'
        )
        self.assertEqual(
            form.fields['end_date'].widget.input_type,
            'date'
        )
```

---

## Admin Tests

### BookingAdmin Tests

```python
class BookingAdminTests(TestCase):
    """Tests for BookingAdmin functionality."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'adminpass'
        )
        self.regular_user = User.objects.create_user('user', password='userpass')
        self.client.login(username='admin', password='adminpass')
        self.today = date.today()

    def test_approve_bookings_action(self):
        """Admin can approve pending bookings."""
        booking = Booking.objects.create(
            user=self.regular_user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='pending'
        )
        # Simulate admin action
        response = self.client.post(
            reverse('admin:main_booking_changelist'),
            {
                'action': 'approve_bookings',
                '_selected_action': [booking.pk]
            }
        )
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')

    def test_reject_bookings_action(self):
        """Admin can reject pending bookings."""
        booking = Booking.objects.create(
            user=self.regular_user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='pending'
        )
        response = self.client.post(
            reverse('admin:main_booking_changelist'),
            {
                'action': 'reject_bookings',
                '_selected_action': [booking.pk]
            }
        )
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')

    def test_booking_admin_list_display(self):
        """Booking admin shows expected columns."""
        Booking.objects.create(
            user=self.regular_user,
            start_date=self.today + timedelta(days=5),
            end_date=self.today + timedelta(days=10),
            status='pending'
        )
        response = self.client.get(reverse('admin:main_booking_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.regular_user.username)
```

### UserAdmin Tests

```python
class UserAdminTests(TestCase):
    """Tests for custom UserAdmin functionality."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'adminpass'
        )
        self.client.login(username='admin', password='adminpass')

    def test_approve_users_action(self):
        """Admin can approve inactive users."""
        user = User.objects.create_user('newuser', password='pass')
        user.is_active = False
        user.save()

        response = self.client.post(
            reverse('admin:auth_user_changelist'),
            {
                'action': 'approve_users',
                '_selected_action': [user.pk]
            }
        )
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_deactivate_users_action(self):
        """Admin can deactivate users."""
        user = User.objects.create_user('activeuser', password='pass')
        user.is_active = True
        user.save()

        response = self.client.post(
            reverse('admin:auth_user_changelist'),
            {
                'action': 'deactivate_users',
                '_selected_action': [user.pk]
            }
        )
        user.refresh_from_db()
        self.assertFalse(user.is_active)
```

---

## Integration Tests

### Message-Comment Integration

```python
class MessageCommentIntegrationTests(TestCase):
    """Integration tests for message and comment relationships."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')

    def test_deleting_message_cascades_to_comments(self):
        """Deleting a message deletes all its comments."""
        message = Message.objects.create(author=self.user, content='Test')
        Comment.objects.create(message=message, author=self.user, content='C1')
        Comment.objects.create(message=message, author=self.user, content='C2')

        initial_comment_count = Comment.objects.count()
        self.assertEqual(initial_comment_count, 2)

        message.delete()

        self.assertEqual(Comment.objects.count(), 0)

    def test_frontpage_displays_messages_with_comments(self):
        """Frontpage shows messages with their comments."""
        self.client.login(username='testuser', password='testpass')
        message = Message.objects.create(author=self.user, content='Main message')
        Comment.objects.create(message=message, author=self.user, content='A comment')

        response = self.client.get(reverse('main:frontpage'))

        self.assertContains(response, 'Main message')
        self.assertContains(response, 'A comment')
```

### User Workflow Integration

```python
class UserWorkflowTests(TestCase):
    """Integration tests for complete user workflows."""

    def test_new_user_registration_to_approval_workflow(self):
        """Complete workflow: register -> admin approve -> login."""
        # Step 1: Register
        self.client.post(
            reverse('main:register'),
            {
                'username': 'newuser',
                'password1': 'complexpass123!',
                'password2': 'complexpass123!'
            }
        )
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)

        # Step 2: Cannot login while inactive
        login_success = self.client.login(username='newuser', password='complexpass123!')
        self.assertFalse(login_success)

        # Step 3: Admin activates user
        user.is_active = True
        user.save()

        # Step 4: User can now login
        login_success = self.client.login(username='newuser', password='complexpass123!')
        self.assertTrue(login_success)

    def test_booking_creation_to_admin_approval_workflow(self):
        """Complete workflow: create booking -> admin approve."""
        user = User.objects.create_user('testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        today = date.today()

        # Step 1: Create booking
        self.client.post(
            reverse('main:booking_create'),
            {
                'start_date': (today + timedelta(days=10)).isoformat(),
                'end_date': (today + timedelta(days=15)).isoformat(),
            }
        )
        booking = Booking.objects.first()
        self.assertEqual(booking.status, 'pending')

        # Step 2: Admin approves
        booking.status = 'confirmed'
        booking.save()

        # Step 3: Verify booking is confirmed
        self.assertEqual(booking.status, 'confirmed')
```

---

## Implementation Priority

### Phase 1: Critical (Fix Existing + Core)

| Priority | Test Category | Est. Tests | Rationale |
|----------|---------------|------------|-----------|
| 1 | Fix `test_kalender_page` bug | 1 | Broken test |
| 2 | Model validation tests | 15 | Core business logic |
| 3 | Permission tests | 10 | Security critical |
| 4 | Booking overlap tests | 5 | Business logic |

### Phase 2: Important (CRUD Operations)

| Priority | Test Category | Est. Tests | Rationale |
|----------|---------------|------------|-----------|
| 5 | Message CRUD tests | 8 | Core feature |
| 6 | Comment CRUD tests | 6 | Core feature |
| 7 | Booking CRUD tests | 10 | Core feature |
| 8 | Form validation tests | 6 | Data integrity |

### Phase 3: Comprehensive (Admin + Integration)

| Priority | Test Category | Est. Tests | Rationale |
|----------|---------------|------------|-----------|
| 9 | Admin action tests | 6 | Admin workflow |
| 10 | Registration workflow tests | 4 | User onboarding |
| 11 | API endpoint tests | 6 | Calendar integration |
| 12 | Integration tests | 5 | End-to-end |

**Total estimated tests: ~80**

---

## Test Utilities

### Recommended Base Setup

```python
# main/tests.py or main/tests/base.py

from datetime import date, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse

from main.models import Message, Comment, Booking
from main.forms import BookingForm


class BaseTestCase(TestCase):
    """Base test class with common setup."""

    @classmethod
    def setUpTestData(cls):
        """Create test users once for all tests in class."""
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_active=True
        )
        cls.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
            is_active=True
        )
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )

    def login_as_user(self):
        """Log in as the standard test user."""
        self.client.login(username='testuser', password='testpass123')

    def login_as_other(self):
        """Log in as another user."""
        self.client.login(username='otheruser', password='otherpass123')

    def login_as_admin(self):
        """Log in as admin."""
        self.client.login(username='admin', password='adminpass123')

    @staticmethod
    def future_date(days=5):
        """Return a date in the future."""
        return date.today() + timedelta(days=days)
```

### Test Organization

Recommended file structure for comprehensive test suite:

```
main/
├── tests/
│   ├── __init__.py
│   ├── base.py          # BaseTestCase and utilities
│   ├── test_models.py   # Model tests
│   ├── test_views.py    # View tests
│   ├── test_forms.py    # Form tests
│   ├── test_admin.py    # Admin tests
│   └── test_integration.py  # Integration tests
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run python manage.py test

# Run with verbosity
uv run python manage.py test -v 2

# Run specific test module
uv run python manage.py test main.tests.test_models

# Run specific test class
uv run python manage.py test main.tests.test_models.BookingModelTests

# Run specific test method
uv run python manage.py test main.tests.test_models.BookingModelTests.test_end_date_must_be_after_start_date
```

### Coverage Reports

```bash
# Install coverage
uv add coverage

# Run tests with coverage
uv run coverage run --source='main' manage.py test

# Generate report
uv run coverage report

# Generate HTML report
uv run coverage html
# Open htmlcov/index.html in browser
```

### Recommended Coverage Targets

| Component | Target Coverage |
|-----------|-----------------|
| Models | 95% |
| Views | 85% |
| Forms | 90% |
| Admin | 75% |
| Overall | 80% |

---

## Summary

This testing strategy provides:

1. **Comprehensive model tests** - Validation, relationships, cascade deletes
2. **View tests with permission verification** - Auth requirements, ownership checks
3. **Form validation tests** - Date logic, overlap detection
4. **Admin action tests** - Approve/reject workflows
5. **Integration tests** - End-to-end user workflows

The plan prioritizes:
- Fixing the existing broken test first
- Testing security-critical permission checks
- Validating core business logic (booking overlaps)
- Comprehensive CRUD operation coverage

Estimated effort: ~80 tests covering all major functionality.
