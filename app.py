import logging
from telegram.ext import Application

import config


def main():
    # Basic logging so we can see what's happening
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # Create the Telegram application
    app = Application.builder().token(config.BOT_TOKEN).build()

    print("Bot is starting...")
    print("Authorized users:", config.AUTHORIZED_USERS)

    # Start the bot (polling Telegram for updates)
    app.run_polling()


if __name__ == "__main__":
    main()
    