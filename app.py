import logging
import time

from telegram import error as telegram_error
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
from models.database import (
    ensure_media_rating_columns,
    ensure_model_normalized_columns,
    init_db,
)
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


def build_application() -> Application:
    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("random", random_command))
    app.add_handler(CommandHandler("listmodels", listmodels_command))
    app.add_handler(CommandHandler("deletemedia", deletemedia_command))
    app.add_handler(CommandHandler("deleteallmedia", deleteallmedia_command))
    app.add_handler(CommandHandler("latest", latest_command))
    app.add_handler(CommandHandler("stats", stats_command))

    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.VIDEO,
            upload_command
        )
    )

    return app


def main():
    # --- Logging configuration ---
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    init_db()
    ensure_media_rating_columns()
    ensure_model_normalized_columns()
    backfill_missing_ratings()

    # --- Startup info ---
    print("Bot is starting...")
    print("Authorized users:", config.AUTHORIZED_USERS)

    # --- Start polling Telegram for updates (retry on transient network errors) ---
    backoff = 5
    while True:
        app = build_application()
        try:
            app.run_polling()
            backoff = 5
        except (telegram_error.NetworkError, OSError) as exc:
            logging.warning("Network error: %s. Retrying in %s seconds.", exc, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
        except Exception:
            logging.exception("Unexpected bot error. Retrying in %s seconds.", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)


if __name__ == "__main__":
    main()
