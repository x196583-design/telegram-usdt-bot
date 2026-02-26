import os
import psycopg2
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from tronpy.keys import PrivateKey

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def create_tron_wallet():
    private_key = PrivateKey.random()
    address = private_key.public_key.to_base58check_address()
    return address, private_key.hex()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    conn = get_connection()
    cur = conn.cursor()

    # 檢查用戶是否已存在
    cur.execute("SELECT wallet_address FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cur.fetchone()

    if result:
        wallet_address = result[0]
    else:
        address, private_key = create_tron_wallet()
        cur.execute(
            "INSERT INTO users (telegram_id, wallet_address, private_key) VALUES (%s, %s, %s)",
            (telegram_id, address, private_key)
        )
        conn.commit()
        wallet_address = address

    cur.close()
    conn.close()

    await update.message.reply_text(
        f"你的專屬 USDT(TRC20) 收款地址：\n\n{wallet_address}"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == "__main__":
    main()
