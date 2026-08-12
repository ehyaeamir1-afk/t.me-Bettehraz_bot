bot
import os
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(TOKEN)
dp = Dispatcher()

db = sqlite3.connect("bot.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    balance INTEGER DEFAULT 1000
)
""")
db.commit()


def get_user(user):
    cursor.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user.id,)
    )
    result = cursor.fetchone()

    if result is None:
        cursor.execute(
            "INSERT INTO users (user_id, name, balance) VALUES (?, ?, ?)",
            (user.id, user.full_name, 1000)
        )
        db.commit()
        return 1000

    return result[0]


def update_balance(user_id, balance):
    cursor.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?",
        (balance, user_id)
    )
    db.commit()


def get_bet(text):
    parts = text.split()

    if len(parts) != 2:
        return None

    try:
        amount = int(parts[1])

        if amount <= 0:
            return None

        return amount

    except ValueError:
        return None


async def play_game(message, emoji, game):

    user = message.from_user
    balance = get_user(user)

    bet = get_bet(message.text)

    if bet is None:
        await message.reply(
            "❌ فرمت اشتباه است.\n\n"
            "مثال:\n"
            "/basket 100\n"
            "/dice 100\n"
            "/dart 100"
        )
        return

    if bet > balance:
        await message.reply(
            "❌ موجودی کافی نیست.\n"
            f"💰 موجودی شما: {balance:,}"
        )
        return

    # کم کردن مبلغ شرط
    balance -= bet
    update_balance(user.id, balance)

    # ارسال بازی واقعی تلگرام
    result = await message.answer_dice(emoji=emoji)

    # کمی صبر برای نمایش نتیجه
    await asyncio.sleep(3)

    value = result.dice.value

    win = False
    multiplier = 0

    if game == "dice":
        if value == 6:
            win = True
            multiplier = 5

    elif game == "basket":
        if value in (4, 5):
            win = True
            multiplier = 2

    elif game == "dart":
        if value in (6, 7):
            win = True
            multiplier = 3

    if win:

        prize = bet * multiplier
        balance += prize

        update_balance(user.id, balance)

        await message.answer(
            f"🎉 تبریک {user.first_name}!\n\n"
            f"🏆 بردی!\n"
            f"💰 جایزه: {prize:,} سکه\n"
            f"💳 موجودی: {balance:,} سکه"
        )

    else:

        await message.answer(
            f"😅 باختی {user.first_name}!\n\n"
            f"💸 مبلغ باخت: {bet:,} سکه\n"
            f"💳 موجودی: {balance:,} سکه"
        )


@dp.message(Command("start"))
async def start(message: types.Message):

    get_user(message.from_user)

    await message.answer(
        "🎮 Bettehraz Bot\n\n"
        "بازی‌های موجود:\n\n"
        "🏀 /basket 100\n"
        "🎲 /dice 100\n"
        "🎯 /dart 100\n\n"
        "💰 /balance\n"
        "🏆 /top\n\n"
        "🇮🇷 نسخه فارسی و انگلیسی\n"
        "💰 این نسخه فقط سکه مجازی دارد."
    )


@dp.message(Command("balance"))
async def balance(message: types.Message):

    balance = get_user(message.from_user)

    await message.reply(
        f"💰 موجودی شما: {balance:,} سکه"
    )


@dp.message(Command("basket"))
async def basket(message: types.Message):

    await play_game(
        message,
        "🏀",
        "basket"
    )


@dp.message(Command("dice"))
async def dice(message: types.Message):

    await play_game(
        message,
        "🎲",
        "dice"
    )


@dp.message(Command("dart"))
async def dart(message: types.Message):

    await play_game(
        message,
        "🎯",
        "dart"
    )


@dp.message(Command("بسکتبال"))
async def persian_basket(message: types.Message):

    await play_game(
        message,
        "🏀",
        "basket"
    )


@dp.message(Command("تاس"))
async def persian_dice(message: types.Message):

    await play_game(
        message,
        "🎲",
        "dice"
    )


@dp.message(Command("دارت"))
async def persian_dart(message: types.Message):

    await play_game(
        message,
        "🎯",
        "dart"
    )


@dp.message(Command("موجودی"))
async def persian_balance(message: types.Message):

    balance = get_user(message.from_user)

    await message.reply(
        f"💰 موجودی شما: {balance:,} سکه"
    )


async def main():

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
