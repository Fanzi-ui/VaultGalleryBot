async def send_text(bot, chat_id, text):
    await bot.send_message(chat_id=chat_id, text=text)
