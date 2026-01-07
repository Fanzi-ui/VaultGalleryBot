import config
from views.message_view import send_text
from services.stats_service import get_overall_stats, get_model_stats
from services.model_service import resolve_model_name, find_model_matches


def _format_avg_rating(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}"


async def stats_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to use this command."
        )
        return

    raw_input = " ".join(context.args).strip() if context.args else ""
    model_name = resolve_model_name(raw_input) if raw_input else None

    if raw_input and not model_name:
        matches = find_model_matches(raw_input)
        if len(matches) > 1:
            await send_text(
                context.bot,
                chat_id,
                "❌ Multiple matches: " + ", ".join(matches[:8])
            )
            return

        await send_text(
            context.bot,
            chat_id,
            f"❌ Model not found: {raw_input}"
        )
        return

    if model_name:
        stats = get_model_stats(model_name)
        if not stats:
            await send_text(
                context.bot,
                chat_id,
                "❌ No stats available."
            )
            return

        lines = [
            f"📊 Stats for {stats['model_name']}:",
            f"• Media: {stats['total_media']}",
            f"• Images: {stats['total_images']}",
            f"• Videos: {stats['total_videos']}",
            f"• Rated images: {stats['rated_images']}",
            f"• Avg rating: {_format_avg_rating(stats['avg_rating'])}",
        ]
        if stats["last_upload"]:
            lines.append(f"• Last upload: {stats['last_upload']:%Y-%m-%d}")

        await send_text(context.bot, chat_id, "\n".join(lines))
        return

    stats = get_overall_stats()
    lines = [
        "📊 Vault stats:",
        f"• Models: {stats['total_models']}",
        f"• Media: {stats['total_media']}",
        f"• Images: {stats['total_images']}",
        f"• Videos: {stats['total_videos']}",
        f"• Rated images: {stats['rated_images']}",
        f"• Avg rating: {_format_avg_rating(stats['avg_rating'])}",
    ]
    await send_text(context.bot, chat_id, "\n".join(lines))
