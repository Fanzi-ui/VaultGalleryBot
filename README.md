# VaultGalleryBot

VaultGalleryBot is a private Telegram bot that lets you upload, store, and randomly retrieve images and videos of models using simple chat commands.

It acts as a personal media vault with a clean backend architecture.

---

## ✨ What This App Does

- Upload images and videos via Telegram
- Organize media by model name
- Store media files on disk
- Store metadata in a database
- Retrieve random media from:
  - All models
  - A specific model
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





🛣️ Future Improvements

List models

Statistics

Bulk random media

Deletion and cleanup

Tags and search

Web UI