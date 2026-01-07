import config
from views.message_view import send_text
from services.storage_service import save_media, save_media_file
from services.model_service import resolve_model_name

ALBUM_FLUSH_SECONDS = 2
ALBUM_MAX_ITEMS = 100


async def _process_album(context, chat_id: int, media_group_id: str) -> None:
    chat_data = context.application.chat_data.get(chat_id)
    if not chat_data:
        return

    album_buffer = chat_data.get("album_buffer", {})
    album_models = chat_data.get("album_models", {})
    album_jobs = chat_data.get("album_jobs", {})

    items = album_buffer.pop(media_group_id, [])
    model_name = album_models.pop(media_group_id, None)
    album_jobs.pop(media_group_id, None)

    if not items or not model_name:
        return

    saved = 0
    failures = 0
    for item in items:
        try:
            await save_media_file(
                context,
                model_name,
                item["file_id"],
                item["unique_id"],
                item["media_type"],
            )
            saved += 1
        except Exception:
            failures += 1

    if failures:
        await send_text(
            context.bot,
            chat_id,
            f"⚠️ Bulk upload finished: {saved} saved, {failures} failed."
        )
        return

    await send_text(
        context.bot,
        chat_id,
        f"✅ Bulk upload finished: {saved} item(s) saved for {model_name}."
    )


async def _album_job_callback(context) -> None:
    data = context.job.data
    await _process_album(
        context,
        data["chat_id"],
        data["media_group_id"],
    )


async def upload_command(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message = update.message

    # Permission check
    if user_id not in config.AUTHORIZED_USERS:
        await send_text(
            context.bot,
            chat_id,
            "❌ You are not authorized to upload media."
        )
        return

    # Must be photo or video
    if not message.photo and not message.video:
        return

    media_group_id = message.media_group_id

    # --- Resolve model name ---
    model_name = None

    if message.video and message.video.duration and message.video.duration > 60:
        await send_text(
            context.bot,
            chat_id,
            "❌ Video too long. Max duration is 60 seconds."
        )
        return

    if message.caption:
        parts = message.caption.split(maxsplit=1)
        if len(parts) < 2:
            await send_text(
                context.bot,
                chat_id,
                "❌ Missing model name. Use: /upload <model name>"
            )
            return
        model_name = parts[1].strip()
    elif media_group_id:
        model_name = context.chat_data.get("album_models", {}).get(media_group_id)

    if model_name:
        resolved_name = resolve_model_name(model_name)
        if resolved_name:
            model_name = resolved_name

    if media_group_id:
        if not model_name:
            await send_text(
                context.bot,
                chat_id,
                "❌ Missing caption. Use: /upload <model name>"
            )
            return

        context.chat_data.setdefault("album_models", {})[media_group_id] = model_name

        if message.photo:
            media_obj = message.photo[-1]
            media_type = "image"
        elif message.video:
            media_obj = message.video
            media_type = "video"
        else:
            return

        job_queue = context.application.job_queue
        if job_queue is None:
            try:
                await save_media_file(
                    context,
                    model_name,
                    media_obj.file_id,
                    media_obj.file_unique_id,
                    media_type,
                )
            except Exception as e:
                await send_text(
                    context.bot,
                    chat_id,
                    f"❌ Failed to save media: {e}"
                )
                return

            if message.caption:
                await send_text(
                    context.bot,
                    chat_id,
                    f"✅ Bulk upload saved for {model_name}."
                )
            return

        context.chat_data.setdefault("album_buffer", {})
        context.chat_data.setdefault("album_jobs", {})

        if len(context.chat_data["album_buffer"].get(media_group_id, [])) >= ALBUM_MAX_ITEMS:
            await send_text(
                context.bot,
                chat_id,
                "⚠️ Bulk upload limit reached (100 items)."
            )
            return

        context.chat_data["album_buffer"].setdefault(media_group_id, []).append(
            {
                "file_id": media_obj.file_id,
                "unique_id": media_obj.file_unique_id,
                "media_type": media_type,
            }
        )

        existing_job = context.chat_data["album_jobs"].get(media_group_id)
        if existing_job:
            existing_job.schedule_removal()

        job = job_queue.run_once(
            _album_job_callback,
            when=ALBUM_FLUSH_SECONDS,
            data={
                "chat_id": chat_id,
                "media_group_id": media_group_id,
            },
        )
        context.chat_data["album_jobs"][media_group_id] = job

        if message.caption:
            await send_text(
                context.bot,
                chat_id,
                f"✅ Bulk upload queued for {model_name}."
            )
        return

    if not model_name:
        await send_text(
            context.bot,
            chat_id,
            "❌ Missing caption. Use: /upload <model name>"
        )
        return

    try:
        await save_media(update, context, model_name)
    except Exception as e:
        await send_text(
            context.bot,
            chat_id,
            f"❌ Failed to save media: {e}"
        )
        return

    await send_text(
        context.bot,
        chat_id,
        f"✅ Media saved successfully under {model_name}"
    )
