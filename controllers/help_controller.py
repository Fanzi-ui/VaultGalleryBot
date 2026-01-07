from views.message_view import send_text
import config


async def help_command(update, context):
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

    help_text = (
        "📂 VaultGalleryBot Help\n\n"
        "/start – Check bot status\n"
        "/help – Show this help message\n"
        "/upload <model> – Upload image or video\n"
        "/random – Get random media\n"
        "/random <model> – Get random media for model\n"
        "/latest – Get latest media\n"
        "/latest <model> [count] – Latest media for model\n"
        "/stats – Show vault stats\n"
        "/stats <model> – Show model stats\n"
        "/listmodels – List models with counts\n"
        "/deletemedia <model> [count] – Delete random media\n"
        "/deleteallmedia confirm – Delete all media\n"
    )

    await send_text(context.bot, chat_id, help_text)
