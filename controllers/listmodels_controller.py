import config
from views.message_view import send_text
from services.model_service import get_models_with_counts


async def listmodels_command(update, context):
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

    models = get_models_with_counts()

    if not models:
        await send_text(
            context.bot,
            chat_id,
            "📭 No models found."
        )
        return

    lines = ["📂 Available Models:"]
    for name, count in models:
        lines.append(f"• {name} ({count})")

    await send_text(context.bot, chat_id, "\n".join(lines))
