import config
from views.message_view import send_text, send_media
from services.random_service import get_random_media
from models.database import SessionLocal
from models.model_entity import Model


def _resolve_model_name(user_input: str | None) -> str | None:
    if not user_input:
        return None

    tokens = user_input.strip().split()
    last_name = tokens[-1].lower()

    session = SessionLocal()
    try:
        for model in session.query(Model).all():
            if model.name.lower() == last_name:
                return model.name
        return None
    finally:
        session.close()


async def random_command(update, context):
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

    raw_input = " ".join(context.args) if context.args else None
    model_name = _resolve_model_name(raw_input)

    if raw_input and not model_name:
        await send_text(
            context.bot,
            chat_id,
            f"❌ Model not found: {raw_input}"
        )
        return

    media = get_random_media(model_name)

    if not media:
        await send_text(
            context.bot,
            chat_id,
            "❌ No media found."
        )
        return

    await send_media(
        context.bot,
        chat_id,
        media["file_path"],
        media["media_type"]
    )
