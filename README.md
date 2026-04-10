# Real-Time Chat Application (Django PFSD Project)

A complete, practical, and modern Real-Time Chat Application built with Django and Django Channels.

## Features
- **User Authentication**: Secure registration, login, and password management.
- **Profiles**: Personalized profiles with images, bios, and online/offline status.
- **Real-Time Private Chat**: Instant messaging between users including typing indicators.
- **Group Chats**: Create and manage groups, invite members, and chat in real-time.
- **Friend System**: Send, accept, and manage friend requests.
- **Notifications**: Real-time alerts for new messages and friend requests.
- **Dashboards**: Dedicated dashboards for users and admins with visual analytics (Matplotlib).
- **Dark Mode**: Modern UI with a glassmorphism design and dark mode support.
- **Media Sharing**: Support for sharing images and documents in chats.

## Tech Stack
- **Backend**: Django 6+
- **Real-Time**: Django Channels (WebSockets)
- **Database**: SQLite (Development)
- **Frontend**: HTML5, Vanilla CSS, Bootstrap 5, JavaScript
- **Analytics**: Matplotlib, Pandas
- **Images**: Pillow

## Setup Instructions

1. **Activate Virtual Environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**:
   ```bash
   pip install Django channels daphne Pillow matplotlib pandas
   ```

3. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create Superuser (for Admin Dashboard)**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the Server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the App**:
   Open `http://localhost:8000` in your browser.

## Project Structure
- `accounts/`: Custom user model and authentication.
- `profiles/`: Profile management and friendships.
- `chat/`: One-to-one messaging logic and WebSockets.
- `groups/`: Group management and group chat logic.
- `notifications/`: User notification system.
- `dashboard/`: User and Admin analytics dashboards.
- `reports/`: Reporting tools.
- `static/`: Global CSS and JS files.
- `templates/`: HTML structures using Django Templates.

## Important Note
For real-time features to work properly, ensure that `daphne` is listed in your `INSTALLED_APPS` and that the server is run via `daphne chatapp.asgi:application` or simply using `runserver` in a modern Django setup which integrates with ASGI.
