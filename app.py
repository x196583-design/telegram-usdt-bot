import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from tronpy.keys import PrivateKey

BOT_TOKEN = os.getenv("BOT_TOKEN")

def create_tron_wallet():
    private_key = PrivateKey.random()
    address = private_key.public_key.to_base58check_address()
    return address, private_key.hex()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address, private_key = create_tron_wallet()

    await update.message.reply_text(
        f"你的專屬 USDT(TRC20) 收款地址：\n\n{address}"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == "__main__":
    main()
