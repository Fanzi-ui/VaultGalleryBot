import config
from views.message_view import send_text
from services.media_cleanup_service import delete_all_media


async def deleteallmedia_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Permission check
    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to use this command."
        )
        return

    # Require explicit confirmation
    if not context.args or context.args[0].lower() != "confirm":
        await send_text(
            context.bot,
            chat_id,
            "⚠️ This will delete ALL media.\n"
            "Run: /deleteallmedia confirm"
        )
        return

    deleted = delete_all_media()

    await send_text(
        context.bot,
        chat_id,
        f"🧹 Deleted {deleted} media item(s).\nModels preserved."
    )
