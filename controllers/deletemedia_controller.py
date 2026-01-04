import config
from views.message_view import send_text
from services.media_cleanup_service import delete_random_media_for_model
from models.database import SessionLocal
from models.model_entity import Model


def _resolve_model_name(user_input: str) -> str | None:
    """
    Normalize user input to match stored model names.
    Strategy:
    - Trim
    - Lowercase
    - Match by last token (since models are stored by last name)
    """
    if not user_input:
        return None

    tokens = user_input.strip().split()
    last_name = tokens[-1].lower()

    session = SessionLocal()
    try:
        models = session.query(Model).all()
        for m in models:
            if m.name.lower() == last_name:
                return m.name
        return None
    finally:
        session.close()


async def deletemedia_command(update, context):
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

    if not context.args:
        await send_text(
            context.bot,
            chat_id,
            "Usage: /deletemedia <model> [count]"
        )
        return

    # Parse args
    *name_parts, maybe_count = context.args
    count = 1

    if maybe_count.isdigit():
        count = max(1, int(maybe_count))
        model_input = " ".join(name_parts)
    else:
        model_input = " ".join(context.args)

    model_name = _resolve_model_name(model_input)

    if not model_name:
        await send_text(
            context.bot,
            chat_id,
            f"❌ Model not found: {model_input}"
        )
        return

    deleted = delete_random_media_for_model(model_name, count)

    if deleted == 0:
        await send_text(
            context.bot,
            chat_id,
            f"ℹ️ No media found to delete for {model_name}."
        )
        return

    await send_text(
        context.bot,
        chat_id,
        f"🗑️ Deleted {deleted} media item(s) from {model_name}."
    )
