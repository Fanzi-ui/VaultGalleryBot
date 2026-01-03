from views.message_view import send_text
import config


async def start_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Permission check
    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to use this bot."
        )
        return

    # Authorized user
    await send_text(
        context.bot,
        chat_id,
        "✅ VaultGalleryBot is online.\nSend /help to see available commands."
    )
