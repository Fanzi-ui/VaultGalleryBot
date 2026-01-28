# VaultGalleryBot

VaultGalleryBot is a private web admin + API that lets you upload, store, and view images and videos of models using a dashboard and authenticated endpoints.

It acts as a personal media vault with a clean backend architecture.

---

## ✨ What This App Does

- Upload images and videos via the web UI or API
- Organize media by model name
- Store media files on disk and metadata in SQLite
- Browse models and galleries in a web admin UI
- Delete media or entire models from the admin UI
- Restrict access to authorized users only

---

## 🧱 Architecture

This project uses a clean layered structure:

- **Web routes**
  - FastAPI endpoints for admin UI + API
  - Auth + request validation

- **Services**
  - File storage logic
  - Database queries

- **Models**
  - Database tables (SQLAlchemy)
  - Model and media relationships

- **Templates/Static**
  - Jinja templates + CSS/JS for the admin UI

---

## 📁 Project Structure

VaultGalleryBot/
├── config.py
├── .env
├── services/
├── models/
├── web/
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

## 📱 Mobile/API Auth

API clients can log in via `POST /api/login` with a JSON body:

```json
{"username": "admin", "password": "pass123"}
```

The response returns `{"token": "..."}`. Send it on API requests as:

`Authorization: Bearer <token>`

You can also use `WEB_ADMIN_TOKEN` directly if you do not want an API login step.

---


## ▶️ Running

Quick start (recommended):

```
./run.sh
```

This launches the GUI installer every time so you can enter your own
web admin credentials, then starts the web UI.

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
- `WEB_ADMIN_TOKEN`: token for API access
- `WEB_ADMIN_USER` / `WEB_ADMIN_PASS`: login credentials

Defaults used automatically:
- `WEB_ADMIN_TOKEN=some_random_secret`
- `WEB_ADMIN_USER=admin`
- `WEB_ADMIN_PASS=pass123`

After saving, the web UI starts automatically.

4) Use the app:
- Web: open `http://127.0.0.1:8000`, login, browse models and galleries

---

## ✅ Success Checklist

- `./run.sh` opens the setup GUI and saves `.env`
- Terminal shows:
  - `VaultGalleryBot is running.`
  - `Web: READY (http://127.0.0.1:8000)`
- Web UI loads at `http://127.0.0.1:8000`

---

## ⚙️ Environment Variables

- `WEB_ADMIN_TOKEN`: token for session validation (default `some_random_secret`)
- `WEB_ADMIN_USER`: admin username (default `admin`)
- `WEB_ADMIN_PASS`: admin password (default `pass123`)
- `WEB_SECURE_COOKIES`: set `true` when using HTTPS (default `false`)
- `DATABASE_URL`: SQLAlchemy URL (default `sqlite:///gallery.db`)

---

## 🛠️ Troubleshooting

- Logs are saved in `logs/` (`web.log`, `install.log`).
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
