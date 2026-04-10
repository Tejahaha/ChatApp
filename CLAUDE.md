# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run development server (uses Daphne ASGI server via channels)
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Run tests
python manage.py test chat

# Run a specific test
python manage.py test chat.tests.TestClassName.test_method_name

# Open Django shell
python manage.py shell
```

All commands should be run from the project root (`C:\Users\TEJA\PycharmProjects\ChatApp`) with the `.venv` activated.

## Architecture

This is a **Django Channels** real-time chat application using ASGI with WebSockets and an in-memory channel layer (no Redis required for development).

### Request Flow

**HTTP requests** → Django views (`chat/views.py`) → templates (`templates/chat/`)
**WebSocket connections** → `ChatConsumer` (`chat/consumers.py`) → channel groups via `InMemoryChannelLayer`

### Key Design Patterns

**Room Access Control** — rooms use an 8-character alphanumeric access code (`Room.access_code`) for sharing. Access is tracked via `RoomMembership`. The creator always has access; others must use the code. Unauthorized access returns 404 (not 403) to avoid information leakage — this is intentional security behavior.

**WebSocket message protocol** — `ChatConsumer` handles four message types:
- `chat_message` — normal chat message, saved to DB
- `typing` — typing indicator, not saved
- `heartbeat` — silently ignored to keep connection alive
- `user_join` / `user_leave` — broadcast on connect/disconnect

**Channel groups** — each room has a group named `chat_{room_id}`. All consumers for that room join the group and receive broadcasts.

### App Structure

- `chatapp/` — Django project config (settings, urls, asgi, wsgi)
- `chat/` — the single Django app containing models, views, consumers, routing
- `templates/chat/` — all HTML templates; `base.html` is the layout base
- `static/css/style.css` — all custom styles

### Models

- `Room` — has `creator` (FK to User), `access_code` (unique 8-char), `description`, `created_at`
- `RoomMembership` — join table between `Room` and `User` for non-creator members
- `Message` — FK to both `Room` and `User`, with `content` and `timestamp`

`Room.has_access(user)` checks both creator and membership. `Room.grant_access(user)` calls `get_or_create` on `RoomMembership`.

### Settings Notes

- Uses `InMemoryChannelLayer` — WebSocket state is lost on server restart and doesn't scale across multiple processes
- `DEBUG = True` — static files served by Django directly
- SQLite database (`db.sqlite3`)
- CSRF trusted origins include an ngrok domain for external testing
