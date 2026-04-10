# ChatApp — Real-Time Messaging Platform

A full-featured, production-style real-time chat application built with **Django** and **Django Channels**. ChatApp supports private messaging, group chats with access controls, live push notifications, user profiles with online/offline tracking, and a modern dark-mode UI — all over WebSockets with zero external dependencies like Redis.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [User Roles & Permissions](#user-roles--permissions)
- [Authentication System](#authentication-system)
- [Private Messaging](#private-messaging)
- [Group Chat System](#group-chat-system)
- [Notification System](#notification-system)
- [User Profiles & Discovery](#user-profiles--discovery)
- [WebSocket Architecture](#websocket-architecture)
- [Dark Mode & Theming](#dark-mode--theming)
- [Database Models & Relationships](#database-models--relationships)
- [URL Structure](#url-structure)
- [Template Structure](#template-structure)
- [Running the Project](#running-the-project)

---

## Project Overview

ChatApp is built around three core experiences:

1. **Private Chats** — One-on-one real-time messaging between any two users, with typing indicators, online status, and last-seen timestamps.
2. **Group Chats** — Multi-user chat rooms that are either open (public, anyone can join) or invite-only (private, requires an access code).
3. **Live Notifications** — A persistent WebSocket connection on every page delivers push toasts for incoming messages in real time.

Every feature is connected end-to-end: when a message is sent, it is saved to the database, broadcast to the recipient's chat window, and simultaneously pushed as a toast notification through a separate notification WebSocket — all within the same async request cycle.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Web Framework | Django 6.0.1 |
| Real-Time | Django Channels 4.x (ASGI + WebSockets) |
| ASGI Server | Daphne |
| Channel Layer | `InMemoryChannelLayer` (no Redis required) |
| Database | SQLite 3 |
| Frontend | Bootstrap 5.3, Bootstrap Icons 1.11, Vanilla JS |
| Fonts | Google Fonts — Inter |
| Image Handling | Pillow |
| Auth | Django built-in `AbstractUser` (extended) |

---

## Project Structure

```
ChatApp/
├── chatapp/                  # Django project config
│   ├── settings.py           # All app settings, channel layer, media config
│   ├── urls.py               # Root URL dispatcher
│   ├── asgi.py               # ASGI application with WebSocket routing
│   └── wsgi.py
│
├── accounts/                 # Custom user model & auth views
│   ├── models.py             # Extended AbstractUser (profile_image, bio, is_online, last_seen)
│   ├── views.py              # register, login, logout, change_password
│   ├── forms.py              # Registration and profile forms
│   └── urls.py
│
├── chat/                     # Private messaging
│   ├── models.py             # PrivateChat, PrivateMessage, BlockedUser
│   ├── views.py              # chat_list, private_chat, search_users, block/unblock
│   ├── consumers.py          # ChatConsumer, GroupChatConsumer, NotificationConsumer
│   ├── routing.py            # WebSocket URL patterns
│   └── urls.py
│
├── groups/                   # Group chat rooms
│   ├── models.py             # ChatGroup (name, image, is_private, access_code, admin, members)
│   ├── views.py              # group_list, create_group, group_chat, join_private_group, leave_group
│   └── urls.py
│
├── profiles/                 # User profiles
│   ├── models.py             # FriendRequest
│   ├── views.py              # profile_view, edit_profile, send_friend_request, search_users
│   └── urls.py
│
├── notifications/            # Notification model and views
│   ├── models.py             # Notification (recipient, sender, type, message, is_read)
│   ├── views.py              # notification_list, mark_read
│   └── urls.py
│
├── dashboard/                # Admin-only analytics dashboard
│   ├── views.py              # admin_dashboard (staff only)
│   └── urls.py
│
├── templates/
│   ├── base.html             # Global layout: navbar, dark mode toggle, push toast, notif WebSocket
│   ├── accounts/             # login.html, register.html, change_password.html
│   ├── chat/                 # chat_list.html, private_chat.html
│   ├── groups/               # group_list.html, group_chat.html, create_group.html
│   ├── profiles/             # profile_view.html, edit_profile.html, search_users.html
│   ├── notifications/        # notification_list.html
│   └── dashboard/            # admin_dashboard.html
│
├── static/
│   └── css/
│       └── style.css         # Full CSS design system with light & dark theme variables
│
├── media/                    # User-uploaded images (profile photos, group photos)
├── db.sqlite3
└── manage.py
```

---

## User Roles & Permissions

| Role | Access |
|---|---|
| Anonymous | Login page, Register page only |
| Authenticated User | Private chats, group chats, profile, notifications, discovery |
| Group Admin | Can view access code for private groups; cannot leave own group |
| Staff / Superuser | Admin Dashboard (`/dashboard/`) via dropdown |

All views are protected with `@login_required`. Unauthorized access to another user's private chat or a private group returns a 404 (not 403) to avoid information leakage.

---

## Authentication System

ChatApp extends Django's built-in `AbstractUser` with additional fields on the `User` model itself (no separate Profile model):

```
User
├── username, email, password     (Django built-in)
├── first_name, last_name         (Django built-in)
├── profile_image                 (ImageField → media/profiles/)
├── bio                           (TextField, blank)
├── status_message                (CharField 255, blank)
├── is_online                     (BooleanField, default=False)
└── last_seen                     (DateTimeField, auto-updated)
```

**Online tracking** is handled at the WebSocket layer, not the HTTP layer. Every `ChatConsumer`, `GroupChatConsumer`, and `NotificationConsumer` calls `set_user_online(True)` on `connect()` and `set_user_online(False)` on `disconnect()`. This means `is_online` accurately reflects active browser tabs, not just login state.

**Last seen** is written as `User.objects.filter(id=user_id).update(last_seen=timezone.now())` — using `.update()` rather than `.save()` to avoid race conditions across concurrent WebSocket connections.

---

## Private Messaging

### Models

```
PrivateChat
├── participants    ManyToManyField(User)
└── created_at

PrivateMessage
├── chat            ForeignKey(PrivateChat)
├── sender          ForeignKey(User)
├── message         TextField
└── created_at

BlockedUser
├── blocker         ForeignKey(User, related_name='blocking')
├── blocked         ForeignKey(User, related_name='blocked_by')
└── unique_together (blocker, blocked)
```

A `PrivateChat` is created on first message (via `get_or_create` on the sorted participant pair). The `chat_list` view annotates each conversation with the last message and unread count, sorted by most recent activity.

### WebSocket Message Flow

```
User A types → [ChatConsumer.receive()]
    │
    ├── save_message()              ← @database_sync_to_async
    ├── channel_layer.group_send()  ← broadcast to room: chat_{chat_id}
    │       └── [ChatConsumer.chat_message()] on User B's socket
    │               └── ws.send() → User B's browser appends bubble
    │
    └── save_notification_and_get_recipient()  ← @database_sync_to_async
            └── channel_layer.group_send()  ← to notify_{recipient_id}
                    └── [NotificationConsumer.send_notification()]
                            └── ws.send() → toast appears on User B's screen
```

### UI Design

- Full-height layout: `height: calc(100vh - navbarHeight - 16px)` computed in JS on load and resize
- Own messages: gradient blue pill, right-aligned
- Other messages: grey pill, left-aligned
- Header shows real-time status: green dot + "Online" or "Last seen X ago"
- Send button disabled until input is non-empty
- `escapeHtml()` used for all dynamically inserted message content (XSS prevention)

---

## Group Chat System

### Models

```
ChatGroup
├── name            CharField(255)
├── description     TextField(blank)
├── image           ImageField → media/groups/
├── admin           ForeignKey(User)
├── members         ManyToManyField(User, blank)
├── is_private      BooleanField(default=False)
├── access_code     CharField(8, unique)
└── created_at      DateTimeField(auto_now_add)
```

Every group — public or private — gets an 8-character alphanumeric access code auto-generated on `save()`:

```python
def generate_access_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def save(self, *args, **kwargs):
    if not self.access_code:
        code = generate_access_code()
        while ChatGroup.objects.filter(access_code=code).exists():
            code = generate_access_code()
        self.access_code = code
    super().save(*args, **kwargs)
```

### Group Types

| Type | Join Method | Discovery |
|---|---|---|
| Public | Click "Join" on the Discover list | Visible to all users who aren't members |
| Private | Enter 8-character access code | Hidden from Discover list |

- **Public groups**: Visiting `/groups/<id>/` auto-adds the user as a member.
- **Private groups**: Visiting `/groups/<id>/` without membership returns 404. Must use "Join with Code" modal.
- **Group admin** cannot leave their own group.
- **Admin sees access code** in the group info panel (offcanvas) and on the group list card as a copyable chip.

### WebSocket Message Flow (Group)

```
User sends message → [GroupChatConsumer.receive()]
    │
    ├── save_group_message()                    ← @database_sync_to_async
    ├── channel_layer.group_send()              ← broadcast to group_{group_id}
    │       └── all members' browsers append bubble
    │
    └── save_group_notifications()              ← @database_sync_to_async
            returns (member_id_list, group_name)
            └── for each member_id:
                    channel_layer.group_send(notify_{member_id})
                        └── toast appears on each member's screen
```

---

## Notification System

### Model

```
Notification
├── recipient   ForeignKey(User, related_name='notifications')
├── sender      ForeignKey(User, related_name='sent_notifications')
├── notif_type  CharField — 'message' | 'group_message' | 'friend_request'
├── message     TextField
├── url         CharField — deep link back to the conversation
├── is_read     BooleanField(default=False)
└── created_at
```

### How It Works

1. **DB write**: A `Notification` row is created synchronously inside a `@database_sync_to_async` method when a message is sent.
2. **WS push**: The consumer then calls `channel_layer.group_send(f"notify_{recipient_id}", {...})` in the async context (never inside the thread pool).
3. **NotificationConsumer**: Every authenticated browser page connects to `/ws/notifications/` and joins the group `notify_{user_id}`. When a `send_notification` event arrives, it forwards the data as JSON over the WebSocket.
4. **Frontend**: `base.html` listens on `notifWs.onmessage`, calls `bumpNotifBadge()` (increments the red badge count) and `showPushToast(data)` (renders a slide-in toast in the top-right corner with a 6-second auto-dismiss).

### Notification Badge

The bell icon in the navbar starts with the server-rendered `unread_notifications_count` (injected via a context processor). Each incoming WebSocket notification increments the badge count by 1 client-side, so the count stays accurate across the session without additional HTTP requests.

---

## User Profiles & Discovery

### Profile View

Each user has a public profile at `/profiles/<username>/` showing:
- Profile photo, display name, username
- Bio and status message
- Online indicator or last seen time
- Friend request button (if not already friends)
- Mutual friends count

### Edit Profile (Settings)

At `/profiles/edit/`, users can update:
- First name, last name
- Status message (255 chars)
- Bio (500 chars)
- Profile photo (with live preview via `FileReader` API before upload)

The settings page uses plain HTML form fields with `enctype="multipart/form-data"` — no crispy forms dependency.

### User Discovery

`/chat/search/` provides a search-as-you-type user finder. Results show profile images, usernames, online status, and a direct "Message" button that opens a private chat.

---

## WebSocket Architecture

### ASGI Configuration (`chatapp/asgi.py`)

```python
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(chat.routing.websocket_urlpatterns)
    ),
})
```

`AuthMiddlewareStack` reads the session cookie and populates `scope['user']` — consumers access the authenticated user as `self.scope['user']` without any HTTP request object.

### Channel Layer

```python
# settings.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
```

No Redis required. State is in-process — a server restart drops all connections and clears all groups. Suitable for development and single-process deployments.

### WebSocket Endpoints

| Endpoint | Consumer | Group Name |
|---|---|---|
| `ws/chat/<chat_id>/` | `ChatConsumer` | `chat_{chat_id}` |
| `ws/group/<group_id>/` | `GroupChatConsumer` | `group_{group_id}` |
| `ws/notifications/` | `NotificationConsumer` | `notify_{user_id}` |

### Message Types Handled

**ChatConsumer / GroupChatConsumer**

| `type` field | Action |
|---|---|
| `message` | Save to DB, broadcast to group, push notification |
| `typing` | Broadcast typing indicator (not saved) |
| `heartbeat` | Silently ignored (keeps connection alive) |

**NotificationConsumer**

| Event | Action |
|---|---|
| `send_notification` | Forwards data JSON to client WebSocket |

### Online Status Tracking

```python
async def connect(self):
    await self.set_user_online(self.scope['user'].id, True)

async def disconnect(self, close_code):
    await self.set_user_online(self.scope['user'].id, False)

@database_sync_to_async
def set_user_online(self, user_id, is_online):
    User.objects.filter(id=user_id).update(
        is_online=is_online,
        last_seen=timezone.now()
    )
```

All three consumer types track online status — so a user with any open tab (chat, group, or just browsing) is marked online.

---

## Dark Mode & Theming

The entire design system is built on CSS custom properties (variables). Light mode values are defined on `:root`; dark mode overrides them on `body.dark-mode`.

### CSS Variable Palette

| Variable | Light Mode | Dark Mode |
|---|---|---|
| `--bg-app` | `#eef4fb` | `#0d1117` |
| `--bg-sidebar` | `#f4f6fb` | `#161b22` |
| `--bg-chat` | `#ffffff` | `#0d1117` |
| `--bg-elevated` | `#ffffff` | `#1c2130` |
| `--bg-hover` | `#f0f4fa` | `#21283a` |
| `--accent` | `#4a6fa5` | `#5b87d4` |
| `--accent-light` | `#3a5a8a` | `#7aa3e8` |
| `--text1` | `#1a2233` | `#e6edf3` |
| `--text2` | `#4a5568` | `#8b949e` |
| `--text3` | `#8898aa` | `#484f58` |
| `--msg-own-start` | `#4a6fa5` | `#3a5f94` |
| `--msg-other` | `#f0f4fa` | `#21283a` |
| `--online` | `#22c55e` | `#3fb950` |

### Toggle Logic

Dark mode preference is persisted in `localStorage` under the key `dark-mode`. On every page load, `applyDarkMode(localStorage.getItem('dark-mode') === 'enabled')` runs before the first paint, preventing flash of wrong theme. The moon/sun icon in the navbar swaps automatically.

```javascript
function applyDarkMode(enabled) {
    document.body.classList.toggle('dark-mode', enabled);
    dmIcon.className = enabled ? 'bi bi-sun fs-5' : 'bi bi-moon-stars fs-5';
}
```

Bootstrap components (navbar, dropdowns, modals, offcanvas, form inputs, alerts) are all overridden in `style.css` so they respect the dark variables without any Bootstrap-specific dark mode plugin.

---

## Database Models & Relationships

```
User (accounts.User — extends AbstractUser)
 │
 ├──< PrivateChat (via ManyToMany: participants)
 │        └──< PrivateMessage (FK: chat, sender)
 │
 ├──< ChatGroup (FK: admin)
 │        └── members (ManyToMany: User)
 │        └──< GroupMessage (FK: group, sender)
 │
 ├──< Notification (FK: recipient, sender)
 │
 ├──< FriendRequest (FK: from_user, to_user)
 │
 └──< BlockedUser (FK: blocker, blocked)
```

| Relationship | Cardinality | Notes |
|---|---|---|
| User ↔ PrivateChat | M:N | Via `participants` ManyToManyField |
| PrivateChat → PrivateMessage | 1:N | FK on message |
| User → ChatGroup (admin) | 1:N | One admin per group |
| User ↔ ChatGroup (member) | M:N | Via `members` ManyToManyField |
| User → Notification | 1:N | Both recipient and sender FKs |
| User → FriendRequest | 1:N | As requester and receiver |
| User → BlockedUser | 1:N | `unique_together` prevents duplicates |

---

## URL Structure

### HTTP Endpoints

| URL | View | Name |
|---|---|---|
| `/` | `chat_list` | `chat_list` |
| `/accounts/login/` | `login_view` | `login` |
| `/accounts/register/` | `register_view` | `register` |
| `/accounts/logout/` | `logout_view` | `logout` |
| `/accounts/password/` | `change_password` | `change_password` |
| `/chat/<int:chat_id>/` | `private_chat` | `private_chat` |
| `/chat/search/` | `search_users` | `search_users` |
| `/groups/` | `group_list` | `group_list` |
| `/groups/create/` | `create_group` | `create_group` |
| `/groups/<int:id>/` | `group_chat` | `group_chat` |
| `/groups/join/` | `join_private_group` | `join_private_group` |
| `/groups/<int:id>/leave/` | `leave_group` | `leave_group` |
| `/profiles/<str:username>/` | `profile_view` | `profile_view` |
| `/profiles/edit/` | `edit_profile` | `edit_profile` |
| `/notifications/` | `notification_list` | `notification_list` |
| `/dashboard/` | `admin_dashboard` | `admin_dashboard` |

### WebSocket Endpoints

| URL | Consumer |
|---|---|
| `ws/chat/<int:chat_id>/` | `ChatConsumer` |
| `ws/group/<int:group_id>/` | `GroupChatConsumer` |
| `ws/notifications/` | `NotificationConsumer` |

---

## Template Structure

```
templates/
├── base.html                    ← Global layout (navbar, dark mode, toasts, notif WS)
│
├── accounts/
│   ├── login.html
│   ├── register.html
│   └── change_password.html
│
├── chat/
│   ├── chat_list.html           ← Conversation list with unread badges & online dots
│   └── private_chat.html        ← Full-height messenger with real-time WS
│
├── groups/
│   ├── group_list.html          ← My Groups + Discover Public + Join with Code modal
│   ├── group_chat.html          ← Full-height group messenger + info offcanvas
│   └── create_group.html        ← Create form with privacy toggle
│
├── profiles/
│   ├── profile_view.html
│   ├── edit_profile.html        ← Settings with live avatar preview
│   └── search_users.html
│
├── notifications/
│   └── notification_list.html
│
└── dashboard/
    └── admin_dashboard.html     ← Staff only
```

All templates extend `base.html`. Custom per-page CSS goes in `{% block extra_css %}`, JS in `{% block extra_js %}`.

---

## Running the Project

### 1. Clone and Set Up Environment

```bash
git clone <repo-url>
cd ChatApp
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install django channels daphne pillow
```

### 3. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (for Admin Dashboard)

```bash
python manage.py createsuperuser
```

### 5. Run the Development Server

```bash
python manage.py runserver
```

Daphne is listed in `INSTALLED_APPS` so `runserver` automatically uses the ASGI stack — WebSockets work out of the box without running a separate server.

### 6. Open in Browser

```
http://localhost:8000
```

### Key Settings

| Setting | Value | Notes |
|---|---|---|
| `DEBUG` | `True` | Static files served by Django |
| `CHANNEL_LAYERS` | `InMemoryChannelLayer` | No Redis needed |
| `MEDIA_URL` | `/media/` | User uploads |
| `MEDIA_ROOT` | `BASE_DIR / 'media'` | Local disk storage |
| `LOGIN_REDIRECT_URL` | `chat_list` | Lands on chat after login |
| `LOGIN_URL` | `/accounts/login/` | Redirect for `@login_required` |

---

## Key Validations Summary

| Feature | Validation |
|---|---|
| Private group access | 404 if non-member visits `/groups/<id>/` |
| Private group join | Code lookup is case-insensitive (uppercased before query) |
| Group admin leave | Blocked — admin cannot leave own group |
| Blocked users | `unique_together` on `(blocker, blocked)` prevents duplicates |
| Access codes | Collision-checked loop ensures uniqueness at generation time |
| Message rendering | `escapeHtml()` applied to all WS-delivered content (XSS prevention) |
| File uploads | `accept="image/*"` on all image inputs; Pillow validates on save |
