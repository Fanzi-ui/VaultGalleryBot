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

Defaults are `some_random_secret`, `admin`, and `pass123` if you do not set them.

---

## ▶️ Running

Quick start (recommended):

```
./run.sh
```

This launches the GUI installer every time so you can enter your own
`BOT_TOKEN` and `AUTHORIZED_USERS`, then starts the bot + web UI.

Headless servers (no GUI):

```
SKIP_SETUP=1 ./run.sh
```

---

## 🚀 First-Time Install (New Users)

1) Clone the repo:
```
git clone https://github.com/Fanzi-ui/VaultGalleryBot.git
cd VaultGalleryBot
```

2) Run the setup/start script:
```
chmod +x run.sh
./run.sh
```

3) In the GUI installer, provide:
- `BOT_TOKEN`: from Telegram `@BotFather` (`/newbot`)
- `AUTHORIZED_USERS`: your numeric Telegram ID (get via `@userinfobot`)

Defaults used automatically:
- `WEB_ADMIN_TOKEN=some_random_secret`
- `WEB_ADMIN_USER=admin`
- `WEB_ADMIN_PASS=pass123`

After saving, the bot and web UI start automatically.

4) Use the app:
- Telegram: `/upload <model name>` with a photo/video
- Web: open `http://127.0.0.1:8000`, login, browse models and galleries

---

## ✅ Success Checklist

- `./run.sh` opens the setup GUI and saves `.env`
- Terminal shows:
  - `VaultGalleryBot is running.`
  - `Bot: READY`
  - `Web: READY (http://127.0.0.1:8000)`
- Telegram bot responds to `/start`
- Web UI loads at `http://127.0.0.1:8000`

---

## ⚙️ Environment Variables

- `BOT_TOKEN`: Telegram bot token (required)
- `AUTHORIZED_USERS`: comma-separated numeric IDs (required)
- `WEB_ADMIN_TOKEN`: token for session validation (default `some_random_secret`)
- `WEB_ADMIN_USER`: admin username (default `admin`)
- `WEB_ADMIN_PASS`: admin password (default `pass123`)
- `WEB_SECURE_COOKIES`: set `true` when using HTTPS (default `false`)
- `DATABASE_URL`: SQLAlchemy URL (default `sqlite:///gallery.db`)

---

## 🛠️ Troubleshooting

- Logs are saved in `logs/` (`bot.log`, `web.log`, `install.log`).
- If the bot says “Temporary failure in name resolution,” your DNS/network is down.
- If the web UI doesn’t load, confirm `uvicorn` is running and port `8000` is free.

---

## 📦 Deployment Options

Docker:

```
docker build -t vaultgallerybot .
docker run --env-file .env -p 8000:8000 -v "$PWD/media:/app/media" -v "$PWD/gallery.db:/app/gallery.db" vaultgallerybot
```

Docker Compose:

```
docker compose up --build
```

Systemd:

- Copy `deploy/vaultgallerybot.service` to `/etc/systemd/system/`
- Update the `User` and `WorkingDirectory` fields
- Enable/start:
```
sudo systemctl enable --now vaultgallerybot
```




🛣️ Future Improvements

List models

Statistics

Bulk random media

Deletion and cleanup

Tags and search

Web UI
