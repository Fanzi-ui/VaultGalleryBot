import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

import config

# --- Controllers (business logic) ---
from controllers.start_controller import start_command          # /start
from controllers.help_controller import help_command            # /help
from controllers.upload_controller import upload_command        # media uploads
from controllers.random_controller import random_command        # /random
from controllers.listmodels_controller import listmodels_command # /listmodels


def main():
    # --- Logging configuration ---
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # --- Create Telegram application ---
    app = Application.builder().token(config.BOT_TOKEN).build()

    # --- Command handlers ---
    # /start → bot status
    app.add_handler(CommandHandler("start", start_command))

    # /help → list available commands
    app.add_handler(CommandHandler("help", help_command))

    # /random [model] → random gallery selection
    app.add_handler(CommandHandler("random", random_command))

    # /listmodels → list all models with media counts
    app.add_handler(CommandHandler("listmodels", listmodels_command))

    # --- Media upload handler ---
    # Handles photos or videos with caption: /upload <model name>
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
