# Implementation Plan: Message Board with User Authentication

## Overview

Add a message board ("Beskedtavle") to the Vraa website where authenticated users can post messages. The system includes user registration with administrator approval control.

---

## Requirements Summary

1. **Message Board** on the frontpage for posting messages
2. **User Authentication** - login/logout functionality
3. **User Registration** with administrator approval
4. **Authorization** - only logged-in users can write messages

---

## Implementation Steps

### Phase 1: User Authentication System

#### Step 1.1: Create Custom User Model (Optional but Recommended)

Extend Django's user model to add an `is_approved` field for admin-controlled registration.

**File: `main/models.py`**
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model with approval workflow."""
    is_approved = models.BooleanField(
        default=False,
        help_text='Designates whether this user has been approved by an administrator.'
    )

    class Meta:
        db_table = 'auth_user'
```

**File: `Vraa/settings.py`** (add)
```python
AUTH_USER_MODEL = 'main.User'
```

> **Alternative (Simpler):** Use Django's built-in `is_active` field on the default User model. New users register with `is_active=False`, and admin sets it to `True` to approve. This avoids a custom user model.

#### Step 1.2: Create Authentication URLs

**File: `main/urls.py`** (additions)
```python
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ... existing patterns ...

    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='main/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='main:frontpage'
    ), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]
```

#### Step 1.3: Create Login Template

**File: `main/templates/main/login.html`**
```html
{% extends 'main/base.html' %}

{% block content %}
<div class="auth-container">
    <h2>Log ind</h2>

    {% if form.errors %}
    <div class="alert alert-danger">
        Ugyldigt brugernavn eller adgangskode.
    </div>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label for="username" class="form-label">Brugernavn</label>
            <input type="text" name="username" id="username" class="form-control" required>
        </div>
        <div class="mb-3">
            <label for="password" class="form-label">Adgangskode</label>
            <input type="password" name="password" id="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary">Log ind</button>
    </form>

    <p class="mt-3">
        Har du ikke en konto? <a href="{% url 'main:register' %}">Registrer dig her</a>
    </p>
</div>
{% endblock %}
```

#### Step 1.4: Create Registration View and Template

**File: `main/views.py`** (addition)
```python
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages

class RegisterView(CreateView):
    """User registration with admin approval workflow."""
    form_class = UserCreationForm
    template_name = 'main/register.html'
    success_url = reverse_lazy('main:login')
    extra_context = {'title': 'Registrer'}

    def form_valid(self, form):
        response = super().form_valid(form)
        # Set user as inactive until admin approves
        self.object.is_active = False
        self.object.save()
        messages.success(
            self.request,
            'Din konto er oprettet og afventer godkendelse af administrator.'
        )
        return response
```

**File: `main/templates/main/register.html`**
```html
{% extends 'main/base.html' %}

{% block content %}
<div class="auth-container">
    <h2>Opret konto</h2>

    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-primary">Opret konto</button>
    </form>

    <p class="mt-3">
        Har du allerede en konto? <a href="{% url 'main:login' %}">Log ind her</a>
    </p>

    <div class="alert alert-info mt-3">
        <strong>Bemærk:</strong> Nye konti skal godkendes af en administrator før du kan logge ind.
    </div>
</div>
{% endblock %}
```

#### Step 1.5: Configure Login Settings

**File: `Vraa/settings.py`** (additions)
```python
# Authentication settings
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
```

#### Step 1.6: Add User Status to Base Template

**File: `main/templates/main/base.html`** (add to sidebar, after navigation)
```html
<!-- User authentication status -->
<div class="user-status mt-4 pt-3 border-top">
    {% if user.is_authenticated %}
        <p class="mb-2">Logget ind som <strong>{{ user.username }}</strong></p>
        <a href="{% url 'main:logout' %}" class="btn btn-outline-secondary btn-sm">Log ud</a>
    {% else %}
        <a href="{% url 'main:login' %}" class="btn btn-primary btn-sm me-2">Log ind</a>
        <a href="{% url 'main:register' %}" class="btn btn-outline-secondary btn-sm">Registrer</a>
    {% endif %}
</div>
```

---

### Phase 2: Message Board Model

#### Step 2.1: Create Message Model

**File: `main/models.py`** (addition)
```python
from django.db import models
from django.conf import settings

class Message(models.Model):
    """A message on the message board."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField(
        verbose_name='Besked',
        max_length=2000
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Besked'
        verbose_name_plural = 'Beskeder'

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}...'
```

#### Step 2.2: Register Model in Admin

**File: `main/admin.py`**
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_preview', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at', 'updated_at']

    def content_preview(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_preview.short_description = 'Besked'
```

#### Step 2.3: Create and Run Migrations

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

---

### Phase 3: Message Board Views

#### Step 3.1: Create Message Board View

**File: `main/views.py`** (additions)
```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Message

class MessageBoardView(ListView):
    """Display all messages on the message board."""
    model = Message
    template_name = 'main/frontpage.html'
    context_object_name = 'messages'
    paginate_by = 20
    extra_context = {'title': 'Frontpage'}


class MessageCreateView(LoginRequiredMixin, CreateView):
    """Create a new message (authenticated users only)."""
    model = Message
    fields = ['content']
    template_name = 'main/message_form.html'
    success_url = reverse_lazy('main:frontpage')
    extra_context = {'title': 'Ny besked'}

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a message (author only)."""
    model = Message
    fields = ['content']
    template_name = 'main/message_form.html'
    success_url = reverse_lazy('main:frontpage')
    extra_context = {'title': 'Rediger besked'}

    def test_func(self):
        return self.get_object().author == self.request.user


class MessageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a message (author only)."""
    model = Message
    template_name = 'main/message_confirm_delete.html'
    success_url = reverse_lazy('main:frontpage')
    extra_context = {'title': 'Slet besked'}

    def test_func(self):
        return self.get_object().author == self.request.user
```

#### Step 3.2: Add URL Patterns

**File: `main/urls.py`** (final version)
```python
from __future__ import annotations
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'main'

urlpatterns = [
    # Pages
    path('', views.MessageBoardView.as_view(), name='frontpage'),
    path('information/', views.InformationView.as_view(), name='information'),
    path('referater/', views.ReferaterView.as_view(), name='referater'),
    path('vedtaegter/', views.VedtaegterView.as_view(), name='vedtaegter'),
    path('kalender/', views.KalenderView.as_view(), name='kalender'),

    # Message board
    path('besked/ny/', views.MessageCreateView.as_view(), name='message_create'),
    path('besked/<int:pk>/rediger/', views.MessageUpdateView.as_view(), name='message_update'),
    path('besked/<int:pk>/slet/', views.MessageDeleteView.as_view(), name='message_delete'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='main/login.html',
        extra_context={'title': 'Log ind'}
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='main:frontpage'
    ), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]
```

---

### Phase 4: Templates

#### Step 4.1: Update Frontpage Template

**File: `main/templates/main/frontpage.html`**
```html
{% extends 'main/base.html' %}
{% load static %}

{% block content %}
<img src="{% static 'main/img/House.JPEG' %}" alt="Vraa" class="img-fluid mb-4 rounded" />

<section class="message-board">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2>Beskedtavle</h2>
        {% if user.is_authenticated %}
            <a href="{% url 'main:message_create' %}" class="btn btn-primary">
                Skriv besked
            </a>
        {% else %}
            <a href="{% url 'main:login' %}" class="btn btn-outline-primary">
                Log ind for at skrive
            </a>
        {% endif %}
    </div>

    {% if messages %}
        <div class="messages-list">
            {% for message in messages %}
                <article class="message-card mb-3 p-3 border rounded">
                    <header class="d-flex justify-content-between align-items-start mb-2">
                        <strong>{{ message.author.username }}</strong>
                        <small class="text-muted">
                            {{ message.created_at|date:"d. M Y, H:i" }}
                        </small>
                    </header>
                    <p class="mb-2">{{ message.content|linebreaks }}</p>
                    {% if user == message.author %}
                        <footer class="message-actions">
                            <a href="{% url 'main:message_update' message.pk %}"
                               class="btn btn-sm btn-outline-secondary">Rediger</a>
                            <a href="{% url 'main:message_delete' message.pk %}"
                               class="btn btn-sm btn-outline-danger">Slet</a>
                        </footer>
                    {% endif %}
                </article>
            {% endfor %}
        </div>

        {% if page_obj.has_other_pages %}
            <nav aria-label="Sidenavigation">
                <ul class="pagination">
                    {% if page_obj.has_previous %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Forrige</a>
                        </li>
                    {% endif %}
                    <li class="page-item disabled">
                        <span class="page-link">Side {{ page_obj.number }} af {{ page_obj.paginator.num_pages }}</span>
                    </li>
                    {% if page_obj.has_next %}
                        <li class="page-item">
                            <a class="page-link" href="?page={{ page_obj.next_page_number }}">Næste</a>
                        </li>
                    {% endif %}
                </ul>
            </nav>
        {% endif %}
    {% else %}
        <p class="text-muted">Ingen beskeder endnu. Vær den første til at skrive!</p>
    {% endif %}
</section>
{% endblock %}
```

#### Step 4.2: Create Message Form Template

**File: `main/templates/main/message_form.html`**
```html
{% extends 'main/base.html' %}

{% block content %}
<div class="message-form-container">
    <h2>{% if object %}Rediger besked{% else %}Ny besked{% endif %}</h2>

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label for="id_content" class="form-label">Din besked</label>
            <textarea name="content" id="id_content" class="form-control"
                      rows="5" maxlength="2000" required>{{ form.content.value|default:'' }}</textarea>
            {% if form.content.errors %}
                <div class="text-danger">{{ form.content.errors }}</div>
            {% endif %}
        </div>
        <button type="submit" class="btn btn-primary">
            {% if object %}Gem ændringer{% else %}Send besked{% endif %}
        </button>
        <a href="{% url 'main:frontpage' %}" class="btn btn-outline-secondary">Annuller</a>
    </form>
</div>
{% endblock %}
```

#### Step 4.3: Create Delete Confirmation Template

**File: `main/templates/main/message_confirm_delete.html`**
```html
{% extends 'main/base.html' %}

{% block content %}
<div class="delete-confirm-container">
    <h2>Slet besked</h2>

    <div class="alert alert-warning">
        <p>Er du sikker på, at du vil slette denne besked?</p>
        <blockquote class="border-start ps-3 my-3">
            {{ object.content|truncatewords:50 }}
        </blockquote>
    </div>

    <form method="post">
        {% csrf_token %}
        <button type="submit" class="btn btn-danger">Ja, slet besked</button>
        <a href="{% url 'main:frontpage' %}" class="btn btn-outline-secondary">Annuller</a>
    </form>
</div>
{% endblock %}
```

---

### Phase 5: Styling

#### Step 5.1: Add Message Board Styles

**File: `main/static/main/css/style.css`** (additions)
```css
/* Message Board Styles */
.message-board {
    margin-top: var(--spacing-lg);
}

.message-card {
    background: var(--surface-white);
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s ease;
}

.message-card:hover {
    box-shadow: var(--shadow-md);
}

.message-actions {
    border-top: 1px solid var(--border-light);
    padding-top: var(--spacing-sm);
    margin-top: var(--spacing-sm);
}

/* Authentication Forms */
.auth-container,
.message-form-container,
.delete-confirm-container {
    max-width: 500px;
    margin: 0 auto;
    padding: var(--spacing-lg);
}

.user-status {
    font-size: var(--font-size-sm);
}
```

---

### Phase 6: Admin User Approval

#### Step 6.1: Configure User Admin

The Django admin already provides user management. To approve users:

1. Navigate to `/admin/`
2. Go to Users
3. Select the user awaiting approval
4. Check the "Active" checkbox
5. Save

For a better admin experience, customize the User admin:

**File: `main/admin.py`** (addition)
```python
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    actions = ['approve_users', 'deactivate_users']

    @admin.action(description='Approve selected users')
    def approve_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

# Unregister the default UserAdmin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
```

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `main/models.py` | Modify | Add `Message` model |
| `main/views.py` | Modify | Add message board views, RegisterView |
| `main/urls.py` | Modify | Add authentication and message URLs |
| `main/admin.py` | Modify | Register Message model, customize User admin |
| `main/templates/main/frontpage.html` | Modify | Add message board display |
| `main/templates/main/login.html` | Create | Login form |
| `main/templates/main/register.html` | Create | Registration form |
| `main/templates/main/message_form.html` | Create | Message create/edit form |
| `main/templates/main/message_confirm_delete.html` | Create | Delete confirmation |
| `main/templates/main/base.html` | Modify | Add user status in sidebar |
| `main/static/main/css/style.css` | Modify | Add message board styles |
| `Vraa/settings.py` | Modify | Add login redirect settings |

---

## Database Migrations Required

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser  # If not already done
```

---

## Testing Checklist

- [ ] User can register a new account
- [ ] New accounts are inactive by default
- [ ] Admin can see pending users in admin panel
- [ ] Admin can activate users via admin panel
- [ ] Active user can log in
- [ ] Inactive user cannot log in (gets error message)
- [ ] Logged-in user can create a message
- [ ] Messages appear on frontpage in reverse chronological order
- [ ] User can edit their own messages
- [ ] User can delete their own messages
- [ ] User cannot edit/delete other users' messages
- [ ] Anonymous user sees login prompt instead of create button
- [ ] Pagination works when >20 messages exist

---

## Security Considerations

1. **CSRF Protection**: All forms include `{% csrf_token %}`
2. **Authorization**: `LoginRequiredMixin` and `UserPassesTestMixin` protect views
3. **Content Sanitization**: Django's template system auto-escapes HTML
4. **Password Validation**: Django's built-in validators are configured
5. **Admin Approval**: Users cannot access site until admin approves

---

## Optional Enhancements (Future)

1. **Email Notifications**: Notify admin when new user registers
2. **Password Reset**: Add forgot password functionality
3. **Rich Text Editor**: Allow basic formatting in messages
4. **Message Replies**: Threaded conversations
5. **User Profiles**: Display user info and message history
6. **Moderation**: Allow admin to hide/delete inappropriate messages

---

## Decision Points for Implementation

1. **Custom User Model vs. Default User**:
   - Recommended: Use Django's default User with `is_active` for approval
   - Simpler, no migrations complexity, works with existing admin

2. **Message Location**:
   - Option A: On frontpage (as planned)
   - Option B: Separate `/beskedtavle/` page with link on frontpage

3. **Message Length Limit**:
   - Currently set to 2000 characters
   - Adjust in model if needed

---

*Plan created: 2026-01-17*
*Django version: 4.x*
*Status: Ready for implementation*
