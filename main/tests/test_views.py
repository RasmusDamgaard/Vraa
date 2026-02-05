"""
Tests for the ``main`` application.

Comprehensive test suite covering models, views, forms, and integrations.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from main.forms import BookingForm
from main.models import Booking, Comment, Message


# =============================================================================
# Base Test Case
# =============================================================================


class BaseTestCase(TestCase):
    """Base test class with common setup."""

    @classmethod
    def setUpTestData(cls):
        """Create test users once for all tests in class."""
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_active=True,
        )
        cls.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123',
            is_active=True,
        )
        cls.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
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
    def future_date(days: int = 5) -> date:
        """Return a date in the future."""
        return date.today() + timedelta(days=days)


# =============================================================================
# Model Tests
# =============================================================================


class MessageModelTests(BaseTestCase):
    """Tests for the Message model."""

    def test_message_creation(self):
        """A message can be created with valid data."""
        message = Message.objects.create(
            author=self.user,
            content='Test message content',
        )
        self.assertEqual(message.author, self.user)
        self.assertEqual(message.content, 'Test message content')
        self.assertIsNotNone(message.created_at)
        self.assertIsNotNone(message.updated_at)

    def test_message_str_representation_short_content(self):
        """__str__ returns full content with author for short messages."""
        message = Message.objects.create(
            author=self.user,
            content='Short message',
        )
        str_repr = str(message)
        self.assertIn(self.user.username, str_repr)
        self.assertIn('Short message', str_repr)

    def test_message_str_representation_long_content(self):
        """__str__ truncates long content with ellipsis."""
        long_content = 'A' * 100
        message = Message.objects.create(
            author=self.user,
            content=long_content,
        )
        str_repr = str(message)
        self.assertIn(self.user.username, str_repr)
        self.assertIn('...', str_repr)
        # Content should be truncated at 50 chars
        self.assertIn('A' * 50, str_repr)

    def test_messages_ordered_by_created_at_descending(self):
        """Messages are ordered newest first."""
        msg1 = Message.objects.create(author=self.user, content='First')
        msg2 = Message.objects.create(author=self.user, content='Second')
        messages = list(Message.objects.all())
        self.assertEqual(messages[0], msg2)  # Newest first
        self.assertEqual(messages[1], msg1)

    def test_message_deleted_when_user_deleted(self):
        """Message is deleted when author is deleted (CASCADE)."""
        temp_user = User.objects.create_user('tempuser', password='temppass')
        message = Message.objects.create(author=temp_user, content='Test')
        message_id = message.id
        temp_user.delete()
        self.assertFalse(Message.objects.filter(id=message_id).exists())

    def test_user_messages_related_name(self):
        """Messages accessible via user.messages."""
        Message.objects.create(author=self.user, content='Message 1')
        Message.objects.create(author=self.user, content='Message 2')
        self.assertEqual(self.user.messages.count(), 2)


class CommentModelTests(BaseTestCase):
    """Tests for the Comment model."""

    def setUp(self):
        """Create a message for comments."""
        super().setUp()
        self.message = Message.objects.create(
            author=self.user,
            content='Test message',
        )

    def test_comment_creation(self):
        """A comment can be created with valid data."""
        comment = Comment.objects.create(
            message=self.message,
            author=self.user,
            content='Test comment',
        )
        self.assertEqual(comment.message, self.message)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, 'Test comment')
        self.assertIsNotNone(comment.created_at)

    def test_comment_str_representation_short_content(self):
        """__str__ returns full content with author for short comments."""
        comment = Comment.objects.create(
            message=self.message,
            author=self.user,
            content='Short comment',
        )
        str_repr = str(comment)
        self.assertIn(self.user.username, str_repr)
        self.assertIn('Short comment', str_repr)

    def test_comment_str_representation_long_content(self):
        """__str__ truncates long content at 30 chars with ellipsis."""
        long_content = 'B' * 50
        comment = Comment.objects.create(
            message=self.message,
            author=self.user,
            content=long_content,
        )
        str_repr = str(comment)
        self.assertIn(self.user.username, str_repr)
        self.assertIn('...', str_repr)
        self.assertIn('B' * 30, str_repr)

    def test_comments_ordered_by_created_at_ascending(self):
        """Comments are ordered oldest first (chronological)."""
        c1 = Comment.objects.create(
            message=self.message, author=self.user, content='First'
        )
        c2 = Comment.objects.create(
            message=self.message, author=self.user, content='Second'
        )
        comments = list(Comment.objects.all())
        self.assertEqual(comments[0], c1)  # Oldest first
        self.assertEqual(comments[1], c2)

    def test_comment_deleted_when_message_deleted(self):
        """Comment is deleted when parent message is deleted (CASCADE)."""
        comment = Comment.objects.create(
            message=self.message, author=self.user, content='Test'
        )
        comment_id = comment.id
        self.message.delete()
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_comment_deleted_when_user_deleted(self):
        """Comment is deleted when author is deleted (CASCADE)."""
        temp_user = User.objects.create_user('tempuser', password='temppass')
        comment = Comment.objects.create(
            message=self.message, author=temp_user, content='Test'
        )
        comment_id = comment.id
        temp_user.delete()
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_message_comments_related_name(self):
        """Comments accessible via message.comments."""
        Comment.objects.create(
            message=self.message, author=self.user, content='Comment 1'
        )
        Comment.objects.create(
            message=self.message, author=self.user, content='Comment 2'
        )
        self.assertEqual(self.message.comments.count(), 2)

    def test_user_comments_related_name(self):
        """Comments accessible via user.comments."""
        Comment.objects.create(
            message=self.message, author=self.user, content='Comment 1'
        )
        self.assertEqual(self.user.comments.count(), 1)


class BookingModelTests(BaseTestCase):
    """Tests for the Booking model."""

    def test_booking_creation(self):
        """A booking can be created with valid data."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',
        )
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.status, 'pending')
        self.assertIsNotNone(booking.created_at)
        self.assertIsNotNone(booking.updated_at)

    def test_booking_str_representation(self):
        """__str__ returns booking summary with username and dates."""
        start = self.future_date(5)
        end = self.future_date(10)
        booking = Booking.objects.create(
            user=self.user,
            start_date=start,
            end_date=end,
            status='pending',
        )
        str_repr = str(booking)
        self.assertIn(self.user.username, str_repr)
        self.assertIn(str(start), str_repr)
        self.assertIn(str(end), str_repr)

    def test_duration_days_property(self):
        """duration_days returns correct number of days."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(0),
            end_date=self.future_date(3),
            status='pending',
        )
        self.assertEqual(booking.duration_days, 3)

    def test_duration_days_one_day(self):
        """duration_days returns 1 for single day booking."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(0),
            end_date=self.future_date(1),
            status='pending',
        )
        self.assertEqual(booking.duration_days, 1)

    def test_end_date_must_be_after_start_date(self):
        """Validation error when end_date <= start_date."""
        booking = Booking(
            user=self.user,
            start_date=self.future_date(10),
            end_date=self.future_date(5),  # Before start
            status='pending',
        )
        with self.assertRaises(ValidationError) as ctx:
            booking.full_clean()
        self.assertIn('end_date', str(ctx.exception))

    def test_same_start_and_end_date_invalid(self):
        """Validation error when end_date equals start_date."""
        same_date = self.future_date(5)
        booking = Booking(
            user=self.user,
            start_date=same_date,
            end_date=same_date,
            status='pending',
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_overlapping_confirmed_booking_raises_error(self):
        """Cannot create booking that overlaps a confirmed booking."""
        # Create confirmed booking
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        # Try to create overlapping booking
        overlapping = Booking(
            user=self.user,
            start_date=self.future_date(7),  # Overlaps
            end_date=self.future_date(12),
            status='pending',
        )
        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_overlapping_pending_booking_allowed(self):
        """Can create booking that overlaps a pending booking."""
        # Create pending booking
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',  # Not confirmed
        )
        # Overlapping booking should be allowed
        overlapping = Booking(
            user=self.user,
            start_date=self.future_date(7),
            end_date=self.future_date(12),
            status='pending',
        )
        overlapping.full_clean()  # Should not raise

    def test_adjacent_bookings_allowed(self):
        """Bookings can be adjacent (one ends when another starts)."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        # Adjacent booking (starts when previous ends)
        adjacent = Booking(
            user=self.user,
            start_date=self.future_date(10),
            end_date=self.future_date(15),
            status='pending',
        )
        adjacent.full_clean()  # Should not raise

    def test_cancelled_booking_does_not_block_overlap(self):
        """Cancelled bookings don't block new bookings."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='cancelled',
        )
        # Overlapping booking should be allowed
        overlapping = Booking(
            user=self.user,
            start_date=self.future_date(7),
            end_date=self.future_date(12),
            status='pending',
        )
        overlapping.full_clean()  # Should not raise

    def test_bookings_ordered_by_start_date(self):
        """Bookings are ordered by start_date ascending."""
        b2 = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(10),
            end_date=self.future_date(12),
            status='pending',
        )
        b1 = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(7),
            status='pending',
        )
        bookings = list(Booking.objects.all())
        self.assertEqual(bookings[0], b1)  # Earlier first
        self.assertEqual(bookings[1], b2)

    def test_notes_optional(self):
        """Booking can be created without notes."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',
            # No notes
        )
        self.assertEqual(booking.notes, '')

    def test_booking_default_status_pending(self):
        """Booking default status is pending."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
        )
        self.assertEqual(booking.status, 'pending')

    def test_booking_deleted_when_user_deleted(self):
        """Booking is deleted when user is deleted (CASCADE)."""
        temp_user = User.objects.create_user('tempuser', password='temppass')
        booking = Booking.objects.create(
            user=temp_user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',
        )
        booking_id = booking.id
        temp_user.delete()
        self.assertFalse(Booking.objects.filter(id=booking_id).exists())

    def test_user_bookings_related_name(self):
        """Bookings accessible via user.bookings."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(7),
            status='pending',
        )
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(10),
            end_date=self.future_date(12),
            status='pending',
        )
        self.assertEqual(self.user.bookings.count(), 2)


# =============================================================================
# View Tests - Login Required Middleware
# =============================================================================


class LoginRequiredMiddlewareTests(BaseTestCase):
    """Tests for site-wide login requirement middleware."""

    def test_anonymous_redirect_frontpage(self):
        """Anonymous users are redirected to login from frontpage."""
        response = self.client.get(reverse('main:frontpage'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_anonymous_redirect_information(self):
        """Anonymous users are redirected to login from information page."""
        response = self.client.get(reverse('main:information'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_anonymous_redirect_referater(self):
        """Anonymous users are redirected to login from referater page."""
        response = self.client.get(reverse('main:referater'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_anonymous_redirect_vedtaegter(self):
        """Anonymous users are redirected to login from vedtaegter page."""
        response = self.client.get(reverse('main:vedtaegter'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_login_page_accessible_without_auth(self):
        """Login page is accessible without authentication."""
        response = self.client.get(reverse('main:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_accessible_without_auth(self):
        """Register page is accessible without authentication."""
        response = self.client.get(reverse('main:register'))
        self.assertEqual(response.status_code, 200)

    def test_brugervejledning_accessible_without_auth(self):
        """Brugervejledning page is accessible without authentication."""
        response = self.client.get(reverse('main:brugervejledning'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_accessible_without_auth(self):
        """Password reset page is accessible without authentication."""
        response = self.client.get(reverse('main:password_reset'))
        self.assertEqual(response.status_code, 200)

    def test_redirect_preserves_next_parameter(self):
        """Redirect includes ?next parameter with original path."""
        response = self.client.get(reverse('main:frontpage'))
        self.assertIn('?next=/', response.url)

    def test_authenticated_user_can_access_frontpage(self):
        """Authenticated users can access the frontpage."""
        self.login_as_user()
        response = self.client.get(reverse('main:frontpage'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_can_access_information(self):
        """Authenticated users can access the information page."""
        self.login_as_user()
        response = self.client.get(reverse('main:information'))
        self.assertEqual(response.status_code, 200)


# =============================================================================
# View Tests - Password Reset
# =============================================================================


class PasswordResetTests(TestCase):
    """Tests for password reset functionality."""

    def test_password_reset_page_accessible(self):
        """Password reset page is accessible."""
        response = self.client.get(reverse('main:password_reset'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_uses_correct_template(self):
        """Password reset page uses correct template."""
        response = self.client.get(reverse('main:password_reset'))
        self.assertTemplateUsed(response, 'main/password_reset.html')

    def test_password_reset_form_submission(self):
        """Password reset form submission works."""
        User.objects.create_user('testuser', 'test@example.com', 'testpass')
        response = self.client.post(
            reverse('main:password_reset'),
            {'email': 'test@example.com'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main:password_reset_done'))

    def test_password_reset_done_page(self):
        """Password reset done page is accessible."""
        response = self.client.get(reverse('main:password_reset_done'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_complete_page(self):
        """Password reset complete page is accessible."""
        response = self.client.get(reverse('main:password_reset_complete'))
        self.assertEqual(response.status_code, 200)


# =============================================================================
# View Tests - Authenticated Pages (formerly Public Pages)
# =============================================================================


class AuthenticatedPageTests(BaseTestCase):
    """Tests for pages that require authentication."""

    def test_frontpage_accessible_when_logged_in(self):
        """Frontpage is accessible when logged in."""
        self.login_as_user()
        response = self.client.get(reverse('main:frontpage'))
        self.assertEqual(response.status_code, 200)

    def test_frontpage_uses_correct_template(self):
        """Frontpage uses frontpage.html template."""
        self.login_as_user()
        response = self.client.get(reverse('main:frontpage'))
        self.assertTemplateUsed(response, 'main/frontpage.html')

    def test_frontpage_contains_messages(self):
        """Frontpage displays messages from database."""
        self.login_as_user()
        Message.objects.create(author=self.user, content='Hello World')
        response = self.client.get(reverse('main:frontpage'))
        self.assertContains(response, 'Hello World')

    def test_frontpage_pagination(self):
        """Frontpage paginates at 20 messages."""
        self.login_as_user()
        for i in range(25):
            Message.objects.create(author=self.user, content=f'Message {i}')
        response = self.client.get(reverse('main:frontpage'))
        self.assertEqual(len(response.context['message_list']), 20)
        self.assertTrue(response.context['is_paginated'])

    def test_frontpage_pagination_page_2(self):
        """Frontpage page 2 shows remaining messages."""
        self.login_as_user()
        for i in range(25):
            Message.objects.create(author=self.user, content=f'Message {i}')
        response = self.client.get(reverse('main:frontpage') + '?page=2')
        self.assertEqual(len(response.context['message_list']), 5)

    def test_information_page_accessible(self):
        """Information page is accessible when logged in."""
        self.login_as_user()
        response = self.client.get(reverse('main:information'))
        self.assertEqual(response.status_code, 200)

    def test_information_page_uses_correct_template(self):
        """Information page uses information.html template."""
        self.login_as_user()
        response = self.client.get(reverse('main:information'))
        self.assertTemplateUsed(response, 'main/information.html')

    def test_referater_page_accessible(self):
        """Referater page is accessible when logged in."""
        self.login_as_user()
        response = self.client.get(reverse('main:referater'))
        self.assertEqual(response.status_code, 200)

    def test_vedtaegter_page_accessible(self):
        """Vedtaegter page is accessible when logged in."""
        self.login_as_user()
        response = self.client.get(reverse('main:vedtaegter'))
        self.assertEqual(response.status_code, 200)

    def test_bootstrap_included_in_base_template(self):
        """Base template includes Bootstrap 5.3.3."""
        self.login_as_user()
        response = self.client.get(reverse('main:frontpage'))
        self.assertContains(response, 'bootstrap@5.3.3')


# =============================================================================
# View Tests - Authentication Required
# =============================================================================


class AuthenticationRequiredTests(BaseTestCase):
    """Tests for pages requiring authentication."""

    def test_kalender_redirects_anonymous_user(self):
        """Kalender page redirects to login for anonymous users."""
        response = self.client.get(reverse('main:kalender'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_kalender_accessible_when_logged_in(self):
        """Kalender page is accessible when logged in."""
        self.login_as_user()
        response = self.client.get(reverse('main:kalender'))
        self.assertEqual(response.status_code, 200)

    def test_kalender_uses_correct_template(self):
        """Kalender page uses kalender.html template."""
        self.login_as_user()
        response = self.client.get(reverse('main:kalender'))
        self.assertTemplateUsed(response, 'main/kalender.html')

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
        message = Message.objects.create(author=self.user, content='Test')
        response = self.client.get(
            reverse('main:comment_create', kwargs={'message_pk': message.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_booking_api_requires_login(self):
        """Booking API endpoint requires authentication."""
        response = self.client.get(reverse('main:booking_api'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


# =============================================================================
# View Tests - Message CRUD
# =============================================================================


class MessageViewTests(BaseTestCase):
    """Tests for message CRUD operations."""

    def setUp(self):
        """Create a test message."""
        super().setUp()
        self.message = Message.objects.create(
            author=self.user,
            content='Original content',
        )

    def test_create_message_when_logged_in(self):
        """Authenticated user can create a message."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:message_create'),
            {'content': 'New message content'},
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(
            Message.objects.filter(content='New message content').exists()
        )

    def test_message_author_set_automatically(self):
        """Message author is set to logged-in user."""
        self.login_as_user()
        self.client.post(
            reverse('main:message_create'),
            {'content': 'New message'},
        )
        message = Message.objects.get(content='New message')
        self.assertEqual(message.author, self.user)

    def test_create_message_redirects_to_frontpage(self):
        """Creating a message redirects to frontpage."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:message_create'),
            {'content': 'New message'},
        )
        self.assertRedirects(response, reverse('main:frontpage'))

    def test_owner_can_access_edit_form(self):
        """Message author can access edit form."""
        self.login_as_user()
        response = self.client.get(
            reverse('main:message_update', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_can_edit_message(self):
        """Message author can edit their message."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:message_update', kwargs={'pk': self.message.pk}),
            {'content': 'Updated content'},
        )
        self.assertEqual(response.status_code, 302)
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, 'Updated content')

    def test_non_owner_cannot_access_edit_form(self):
        """Non-author cannot access edit form."""
        self.login_as_other()
        response = self.client.get(
            reverse('main:message_update', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_non_owner_cannot_edit_message(self):
        """Non-author cannot edit a message."""
        self.login_as_other()
        response = self.client.post(
            reverse('main:message_update', kwargs={'pk': self.message.pk}),
            {'content': 'Hacked content'},
        )
        self.assertEqual(response.status_code, 403)
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, 'Original content')

    def test_owner_can_access_delete_confirmation(self):
        """Message author can access delete confirmation."""
        self.login_as_user()
        response = self.client.get(
            reverse('main:message_delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_can_delete_message(self):
        """Message author can delete their message."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:message_delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(pk=self.message.pk).exists())

    def test_non_owner_cannot_delete_message(self):
        """Non-author cannot delete a message."""
        self.login_as_other()
        response = self.client.post(
            reverse('main:message_delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Message.objects.filter(pk=self.message.pk).exists())


# =============================================================================
# View Tests - Comment CRUD
# =============================================================================


class CommentViewTests(BaseTestCase):
    """Tests for comment CRUD operations."""

    def setUp(self):
        """Create a message and comment for testing."""
        super().setUp()
        self.message = Message.objects.create(
            author=self.user, content='Test message'
        )
        self.comment = Comment.objects.create(
            message=self.message,
            author=self.user,
            content='Original comment',
        )

    def test_create_comment_when_logged_in(self):
        """Authenticated user can create a comment."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:comment_create', kwargs={'message_pk': self.message.pk}),
            {'content': 'New comment'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Comment.objects.filter(
                message=self.message, content='New comment'
            ).exists()
        )

    def test_comment_linked_to_correct_message(self):
        """Comment is associated with the correct message."""
        self.login_as_user()
        self.client.post(
            reverse('main:comment_create', kwargs={'message_pk': self.message.pk}),
            {'content': 'Linked comment'},
        )
        comment = Comment.objects.get(content='Linked comment')
        self.assertEqual(comment.message, self.message)

    def test_comment_author_set_automatically(self):
        """Comment author is set to logged-in user."""
        self.login_as_user()
        self.client.post(
            reverse('main:comment_create', kwargs={'message_pk': self.message.pk}),
            {'content': 'My comment'},
        )
        comment = Comment.objects.get(content='My comment')
        self.assertEqual(comment.author, self.user)

    def test_comment_form_shows_parent_message(self):
        """Comment form shows the parent message context."""
        self.login_as_user()
        response = self.client.get(
            reverse('main:comment_create', kwargs={'message_pk': self.message.pk})
        )
        self.assertEqual(response.context['message'], self.message)

    def test_owner_can_delete_comment(self):
        """Comment author can delete their comment."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:comment_delete', kwargs={'pk': self.comment.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_non_owner_cannot_delete_comment(self):
        """Non-author cannot delete a comment."""
        self.login_as_other()
        response = self.client.post(
            reverse('main:comment_delete', kwargs={'pk': self.comment.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())


# =============================================================================
# View Tests - Booking CRUD
# =============================================================================


class BookingViewTests(BaseTestCase):
    """Tests for booking CRUD operations."""

    def setUp(self):
        """Create a test booking."""
        super().setUp()
        self.booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(10),
            end_date=self.future_date(15),
            status='pending',
            notes='Original notes',
        )

    def test_create_booking_when_logged_in(self):
        """Authenticated user can create a booking."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:booking_create'),
            {
                'start_date': self.future_date(20).isoformat(),
                'end_date': self.future_date(25).isoformat(),
                'notes': 'Test booking',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(notes='Test booking').exists())

    def test_booking_user_set_automatically(self):
        """Booking user is set to logged-in user."""
        self.login_as_user()
        self.client.post(
            reverse('main:booking_create'),
            {
                'start_date': self.future_date(20).isoformat(),
                'end_date': self.future_date(25).isoformat(),
            },
        )
        booking = Booking.objects.exclude(pk=self.booking.pk).first()
        self.assertEqual(booking.user, self.user)

    def test_booking_status_defaults_to_pending(self):
        """New bookings have pending status."""
        self.login_as_user()
        self.client.post(
            reverse('main:booking_create'),
            {
                'start_date': self.future_date(20).isoformat(),
                'end_date': self.future_date(25).isoformat(),
            },
        )
        booking = Booking.objects.exclude(pk=self.booking.pk).first()
        self.assertEqual(booking.status, 'pending')

    def test_owner_can_access_edit_form_for_pending(self):
        """Owner can access edit form for pending booking."""
        self.login_as_user()
        response = self.client.get(
            reverse('main:booking_update', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_can_edit_pending_booking(self):
        """Owner can edit their pending booking."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:booking_update', kwargs={'pk': self.booking.pk}),
            {
                'start_date': self.future_date(11).isoformat(),
                'end_date': self.future_date(16).isoformat(),
                'notes': 'Updated notes',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.notes, 'Updated notes')

    def test_owner_cannot_edit_confirmed_booking(self):
        """Owner cannot edit a confirmed booking."""
        self.booking.status = 'confirmed'
        self.booking.save()
        self.login_as_user()
        response = self.client.get(
            reverse('main:booking_update', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_non_owner_cannot_edit_booking(self):
        """Non-owner cannot edit a booking."""
        self.login_as_other()
        response = self.client.get(
            reverse('main:booking_update', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_can_delete_booking(self):
        """Owner can cancel their booking."""
        self.login_as_user()
        response = self.client.post(
            reverse('main:booking_delete', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())

    def test_non_owner_cannot_delete_booking(self):
        """Non-owner cannot cancel a booking."""
        self.login_as_other()
        response = self.client.post(
            reverse('main:booking_delete', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Booking.objects.filter(pk=self.booking.pk).exists())


# =============================================================================
# View Tests - Booking API
# =============================================================================


class BookingAPIViewTests(BaseTestCase):
    """Tests for the BookingAPIView JSON endpoint."""

    def test_api_requires_authentication(self):
        """API endpoint requires login."""
        response = self.client.get(reverse('main:booking_api'))
        self.assertEqual(response.status_code, 302)

    def test_api_returns_json(self):
        """API returns JSON content type."""
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_returns_empty_list_when_no_bookings(self):
        """API returns empty list when no bookings exist."""
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        data = response.json()
        self.assertEqual(data, [])

    def test_api_returns_booking_list(self):
        """API returns list of bookings."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_api_event_format(self):
        """API returns events in FullCalendar format."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertEqual(event['id'], f'booking-{booking.pk}')  # ID format is 'booking-{pk}'
        self.assertEqual(event['title'], self.user.username)
        self.assertEqual(event['start'], self.future_date(5).isoformat())
        self.assertEqual(event['end'], self.future_date(10).isoformat())
        self.assertIn('color', event)
        self.assertIn('extendedProps', event)

    def test_confirmed_booking_green_color(self):
        """Confirmed bookings have green color."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertEqual(event['color'], '#28a745')

    def test_pending_booking_yellow_color(self):
        """Pending bookings have yellow color."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertEqual(event['color'], '#ffc107')

    def test_api_includes_ownership_flag(self):
        """API includes is_owner flag in extendedProps."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertTrue(event['extendedProps']['is_owner'])

    def test_api_ownership_flag_false_for_others(self):
        """API shows is_owner=false for other users' bookings."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',
        )
        self.login_as_other()
        response = self.client.get(reverse('main:booking_api'))
        event = response.json()[0]
        self.assertFalse(event['extendedProps']['is_owner'])

    def test_api_excludes_cancelled_bookings(self):
        """API excludes cancelled bookings."""
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='cancelled',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_api'))
        data = response.json()
        self.assertEqual(len(data), 0)


# =============================================================================
# View Tests - Registration
# =============================================================================


class RegistrationViewTests(TestCase):
    """Tests for user registration."""

    def test_registration_page_accessible(self):
        """Registration page is accessible."""
        response = self.client.get(reverse('main:register'))
        self.assertEqual(response.status_code, 200)

    def test_registration_uses_correct_template(self):
        """Registration page uses register.html template."""
        response = self.client.get(reverse('main:register'))
        self.assertTemplateUsed(response, 'main/register.html')

    def test_user_registration_creates_user(self):
        """Registration creates a new user."""
        response = self.client.post(
            reverse('main:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'VraaTest2026Secure!',
                'password2': 'VraaTest2026Secure!',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_registration_creates_inactive_user(self):
        """Registered users are created as inactive."""
        self.client.post(
            reverse('main:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'VraaTest2026Secure!',
                'password2': 'VraaTest2026Secure!',
            },
        )
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)

    def test_registration_redirects_to_login(self):
        """Registration redirects to login page on success."""
        response = self.client.post(
            reverse('main:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'VraaTest2026Secure!',
                'password2': 'VraaTest2026Secure!',
            },
        )
        self.assertRedirects(response, reverse('main:login'))

    def test_inactive_user_cannot_login(self):
        """Inactive users cannot log in."""
        # Create inactive user
        user = User.objects.create_user('newuser', password='testpass')
        user.is_active = False
        user.save()
        # Attempt login
        login_success = self.client.login(username='newuser', password='testpass')
        self.assertFalse(login_success)


# =============================================================================
# Booking Detail (Print Confirmation) Tests
# =============================================================================


class BookingDetailViewTests(BaseTestCase):
    """Tests for BookingDetailView (printable booking confirmation)."""

    def test_booking_detail_requires_login(self):
        """Booking detail page requires authentication."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        response = self.client.get(reverse('main:booking_detail', args=[booking.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_owner_can_view_own_booking(self):
        """User can view their own booking confirmation."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_detail', args=[booking.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bookingbekræftelse')

    def test_owner_cannot_view_other_booking(self):
        """User cannot view another user's booking."""
        booking = Booking.objects.create(
            user=self.other_user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_detail', args=[booking.pk]))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_view_any_booking(self):
        """Staff can view any user's booking."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_admin()
        response = self.client.get(reverse('main:booking_detail', args=[booking.pk]))
        self.assertEqual(response.status_code, 200)

    def test_booking_detail_uses_correct_template(self):
        """Booking detail page uses booking_confirmation_print.html template."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_detail', args=[booking.pk]))
        self.assertTemplateUsed(response, 'main/booking_confirmation_print.html')

    def test_booking_detail_shows_status(self):
        """Booking detail shows booking status."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_detail', args=[booking.pk]))
        self.assertContains(response, 'Bekræftet')

    def test_booking_detail_has_print_button(self):
        """Booking detail page includes print button."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        self.login_as_user()
        response = self.client.get(reverse('main:booking_detail', args=[booking.pk]))
        self.assertContains(response, 'Udskriv')


# =============================================================================
# Form Tests
# =============================================================================


class BookingFormTests(BaseTestCase):
    """Tests for BookingForm validation."""

    def test_valid_form(self):
        """Form is valid with correct data."""
        form = BookingForm(
            data={
                'start_date': self.future_date(5),
                'end_date': self.future_date(10),
                'notes': 'Test booking',
            }
        )
        self.assertTrue(form.is_valid())

    def test_valid_form_without_notes(self):
        """Form is valid without notes (optional field)."""
        form = BookingForm(
            data={
                'start_date': self.future_date(5),
                'end_date': self.future_date(10),
            }
        )
        self.assertTrue(form.is_valid())

    def test_end_date_before_start_date_invalid(self):
        """Form is invalid when end_date < start_date."""
        form = BookingForm(
            data={
                'start_date': self.future_date(10),
                'end_date': self.future_date(5),  # Before start
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_same_start_and_end_date_invalid(self):
        """Form is invalid when start and end date are the same."""
        same_date = self.future_date(5)
        form = BookingForm(
            data={
                'start_date': same_date,
                'end_date': same_date,
            }
        )
        self.assertFalse(form.is_valid())

    def test_overlapping_confirmed_booking_invalid(self):
        """Form is invalid when overlapping confirmed booking."""
        # Create confirmed booking
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        # Try overlapping booking
        form = BookingForm(
            data={
                'start_date': self.future_date(7),
                'end_date': self.future_date(12),
            }
        )
        self.assertFalse(form.is_valid())

    def test_overlapping_pending_booking_valid(self):
        """Form is valid when overlapping pending booking."""
        # Create pending booking
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='pending',
        )
        # Overlapping booking should be allowed
        form = BookingForm(
            data={
                'start_date': self.future_date(7),
                'end_date': self.future_date(12),
            }
        )
        self.assertTrue(form.is_valid())

    def test_edit_excludes_self_from_overlap_check(self):
        """When editing, form doesn't flag self as overlap."""
        booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )
        # Edit same booking (same dates) - should be valid
        form = BookingForm(
            instance=booking,
            data={
                'start_date': self.future_date(5),
                'end_date': self.future_date(10),
            },
        )
        self.assertTrue(form.is_valid())

    def test_date_widgets_render_correctly(self):
        """Date fields render with date input type."""
        form = BookingForm()
        self.assertIn('type="date"', str(form['start_date']))
        self.assertIn('type="date"', str(form['end_date']))

    def test_form_has_bootstrap_classes(self):
        """Form fields have Bootstrap form-control class."""
        form = BookingForm()
        self.assertIn('form-control', str(form['start_date']))
        self.assertIn('form-control', str(form['end_date']))
        self.assertIn('form-control', str(form['notes']))


# =============================================================================
# Integration Tests
# =============================================================================


class MessageCommentIntegrationTests(BaseTestCase):
    """Integration tests for message and comment relationships."""

    def test_deleting_message_cascades_to_comments(self):
        """Deleting a message deletes all its comments."""
        message = Message.objects.create(author=self.user, content='Test')
        Comment.objects.create(message=message, author=self.user, content='C1')
        Comment.objects.create(message=message, author=self.user, content='C2')

        self.assertEqual(Comment.objects.count(), 2)
        message.delete()
        self.assertEqual(Comment.objects.count(), 0)

    def test_frontpage_displays_messages_with_comments(self):
        """Frontpage shows messages with their comments."""
        self.login_as_user()
        message = Message.objects.create(
            author=self.user, content='Main message'
        )
        Comment.objects.create(
            message=message, author=self.user, content='A comment'
        )

        response = self.client.get(reverse('main:frontpage'))

        self.assertContains(response, 'Main message')
        self.assertContains(response, 'A comment')

    def test_message_with_multiple_comments_displays_all(self):
        """Message with multiple comments displays all of them."""
        self.login_as_user()
        message = Message.objects.create(author=self.user, content='Message')
        Comment.objects.create(message=message, author=self.user, content='Comment 1')
        Comment.objects.create(message=message, author=self.user, content='Comment 2')
        Comment.objects.create(message=message, author=self.user, content='Comment 3')

        response = self.client.get(reverse('main:frontpage'))

        self.assertContains(response, 'Comment 1')
        self.assertContains(response, 'Comment 2')
        self.assertContains(response, 'Comment 3')


class UserWorkflowTests(TestCase):
    """Integration tests for complete user workflows."""

    def test_new_user_registration_to_approval_workflow(self):
        """Complete workflow: register -> inactive -> admin approve -> login."""
        # Step 1: Register
        self.client.post(
            reverse('main:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'VraaTest2026Secure!',
                'password2': 'VraaTest2026Secure!',
            },
        )
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)

        # Step 2: Cannot login while inactive
        login_success = self.client.login(
            username='newuser', password='VraaTest2026Secure!'
        )
        self.assertFalse(login_success)

        # Step 3: Admin activates user
        user.is_active = True
        user.save()

        # Step 4: User can now login
        login_success = self.client.login(
            username='newuser', password='VraaTest2026Secure!'
        )
        self.assertTrue(login_success)

    def test_message_creation_and_commenting_workflow(self):
        """Complete workflow: create message -> add comment -> view on frontpage."""
        user = User.objects.create_user('testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

        # Step 1: Create message
        self.client.post(
            reverse('main:message_create'),
            {'content': 'New discussion topic'},
        )
        message = Message.objects.get(content='New discussion topic')

        # Step 2: Add comment
        self.client.post(
            reverse('main:comment_create', kwargs={'message_pk': message.pk}),
            {'content': 'Great topic!'},
        )

        # Step 3: Verify on frontpage
        response = self.client.get(reverse('main:frontpage'))
        self.assertContains(response, 'New discussion topic')
        self.assertContains(response, 'Great topic!')

    def test_booking_creation_workflow(self):
        """Complete workflow: create booking -> verify pending."""
        user = User.objects.create_user('testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        today = date.today()

        # Step 1: Create booking
        self.client.post(
            reverse('main:booking_create'),
            {
                'start_date': (today + timedelta(days=10)).isoformat(),
                'end_date': (today + timedelta(days=15)).isoformat(),
                'notes': 'Family vacation',
            },
        )
        booking = Booking.objects.get(notes='Family vacation')

        # Step 2: Verify pending status
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.user, user)

        # Step 3: Verify visible in calendar API
        response = self.client.get(reverse('main:booking_api'))
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['extendedProps']['status'], 'pending')


class KalenderViewIntegrationTests(BaseTestCase):
    """Integration tests for the kalender view."""

    def test_kalender_shows_only_future_bookings(self):
        """Kalender only shows bookings with end_date >= today."""
        self.login_as_user()
        today = date.today()

        # Past booking (should not appear)
        Booking.objects.create(
            user=self.user,
            start_date=today - timedelta(days=10),
            end_date=today - timedelta(days=5),
            status='confirmed',
        )
        # Future booking (should appear)
        future_booking = Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='confirmed',
        )

        response = self.client.get(reverse('main:kalender'))
        bookings = response.context['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0], future_booking)

    def test_kalender_excludes_cancelled_bookings(self):
        """Kalender excludes cancelled bookings."""
        self.login_as_user()

        # Cancelled booking (should not appear)
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(5),
            end_date=self.future_date(10),
            status='cancelled',
        )
        # Confirmed booking (should appear)
        Booking.objects.create(
            user=self.user,
            start_date=self.future_date(15),
            end_date=self.future_date(20),
            status='confirmed',
        )

        response = self.client.get(reverse('main:kalender'))
        bookings = response.context['bookings']
        self.assertEqual(len(bookings), 1)
        self.assertEqual(bookings[0].status, 'confirmed')
