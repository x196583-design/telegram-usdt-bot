import os
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("Bot is running ✅")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # 保持程式不退出
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
