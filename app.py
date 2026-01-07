import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
from models.database import ensure_media_rating_columns, ensure_model_normalized_columns
from services.rating_service import backfill_missing_ratings

# --- Controllers (business logic) ---
from controllers.start_controller import start_command             # /start
from controllers.help_controller import help_command               # /help
from controllers.upload_controller import upload_command           # media uploads
from controllers.random_controller import random_command           # /random
from controllers.listmodels_controller import listmodels_command   # /listmodels
from controllers.deletemedia_controller import deletemedia_command # /deletemedia
from controllers.deleteallmedia_controller import deleteallmedia_command  # /deleteallmedia
from controllers.latest_controller import latest_command           # /latest
from controllers.stats_controller import stats_command             # /stats


def main():
    # --- Logging configuration ---
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    ensure_media_rating_columns()
    ensure_model_normalized_columns()
    backfill_missing_ratings()

    # --- Create Telegram application ---
    app = Application.builder().token(config.BOT_TOKEN).build()

    # --- Command handlers ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("random", random_command))
    app.add_handler(CommandHandler("listmodels", listmodels_command))
    app.add_handler(CommandHandler("deletemedia", deletemedia_command))
    app.add_handler(CommandHandler("deleteallmedia", deleteallmedia_command))
    app.add_handler(CommandHandler("latest", latest_command))
    app.add_handler(CommandHandler("stats", stats_command))

    # --- Media upload handler ---
    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO,
            upload_command
        )
    )

    # --- Startup info ---
    print("Bot is starting...")
    print("Authorized users:", config.AUTHORIZED_USERS)

    # --- Start polling Telegram for updates ---
    app.run_polling()


if __name__ == "__main__":
    main()
