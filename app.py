import os
import psycopg2
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from tronpy.keys import PrivateKey

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

USDT_CONTRACT = "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj"
PORT = int(os.environ.get("PORT", 10000))


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

    cur.execute(
        "SELECT wallet_address FROM users WHERE telegram_id = %s",
        (telegram_id,)
    )
    result = cur.fetchone()

    if result:
        wallet_address = result[0]
    else:
        address, private_key = create_tron_wallet()
        cur.execute(
            """
            INSERT INTO users (telegram_id, wallet_address, private_key)
            VALUES (%s, %s, %s)
            """,
            (telegram_id, address, private_key),
        )
        conn.commit()
        wallet_address = address

    cur.close()
    conn.close()

    await update.message.reply_text(
        f"你的專屬 USDT(TRC20) 收款地址：\n\n{wallet_address}"
    )


async def check_deposits(context: ContextTypes.DEFAULT_TYPE):
    print("Deposit job running...")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, telegram_id, wallet_address FROM users")
    users = cur.fetchall()

    for user_id, telegram_id, wallet_address in users:
        url = f"https://api.trongrid.io/v1/accounts/{wallet_address}/transactions/trc20"
        headers = {"TRON-PRO-API-KEY": TRONGRID_API_KEY}

        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            continue

        data = response.json()

        if "data" in data:
            for tx in data["data"]:
                if tx["token_info"]["address"] != USDT_CONTRACT:
                    continue

                tx_hash = tx["transaction_id"]
                amount = int(tx["value"]) / 1_000_000

                cur.execute(
                    "SELECT 1 FROM deposits WHERE tx_hash = %s",
                    (tx_hash,)
                )

                if not cur.fetchone():
                    cur.execute(
                        """
                        INSERT INTO deposits (user_id, tx_hash, amount, confirmed)
                        VALUES (%s, %s, %s, true)
                        """,
                        (user_id, tx_hash, amount),
                    )
                    conn.commit()

                    await context.bot.send_message(
                        chat_id=telegram_id,
                        text=f"💰 收到 {amount} USDT 入帳！"
                    )

    cur.close()
    conn.close()


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(check_deposits, interval=30, first=10)

    print("Starting webhook...")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )


if __name__ == "__main__":
    main()
