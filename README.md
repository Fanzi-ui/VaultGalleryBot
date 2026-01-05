# VaultGalleryBot

VaultGalleryBot is a private Telegram bot + web admin that lets you upload, store, and view images and videos of models using simple chat commands and a dashboard.

It acts as a personal media vault with a clean backend architecture.

---

## ✨ What This App Does

- Upload images and videos via Telegram
- Organize media by model name
- Store media files on disk and metadata in SQLite
- Retrieve random media (all models or a specific model)
- Browse models and galleries in a web admin UI
- Delete media or entire models from the admin UI
- Restrict access to authorized users only

---

## 🧱 Architecture (MVC)

This project uses a clean MVC-style structure:

- **Controllers**
  - Handle Telegram commands
  - Parse user input
  - Enforce permissions

- **Services**
  - File storage logic
  - Database queries
  - Random selection logic

- **Models**
  - Database tables (SQLAlchemy)
  - Model and media relationships

- **Views**
  - Send messages
  - Send images and videos to Telegram

---

## 📁 Project Structure

VaultGalleryBot/
├── app.py
├── config.py
├── .env
├── controllers/
├── services/
├── models/
├── views/
├── media/
│ └── models/
├── requirements.txt
└── README.md

---

## 🔐 Web Admin Auth

The web admin requires a token and a login:

- `WEB_ADMIN_TOKEN` is used for cookie/session validation
- `WEB_ADMIN_USER` and `WEB_ADMIN_PASS` control the login credentials

Defaults are `admin` / `pass123` if you do not set them.

---

## ▶️ Running

Bot:

```
python app.py
```

Web admin:

```
uvicorn web.main:app --reload
```

---

## 🚀 Quick Start (New Users)

1) Create a Telegram bot
- Open Telegram → message `@BotFather` → `/newbot`
- Save the bot token

2) Get your Telegram user ID
- Message `@userinfobot` or `@getmyid_bot` and copy your ID

3) Create `.env` in the project root:
```
BOT_TOKEN=your_bot_token_here
AUTHORIZED_USERS=your_user_id_here
WEB_ADMIN_TOKEN=some_random_secret
WEB_ADMIN_USER=admin
WEB_ADMIN_PASS=pass123
```

4) Install dependencies:
```
pip install -r requirements.txt
```

5) Start the services:
```
python app.py
uvicorn web.main:app --reload
```

6) Use the app:
- Telegram: `/upload <model name>` with a photo/video
- Web: open `http://127.0.0.1:8000`, login, browse models and galleries




🛣️ Future Improvements

List models

Statistics

Bulk random media

Deletion and cleanup

Tags and search

Web UI
