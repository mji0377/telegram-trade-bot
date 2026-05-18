from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from openai import OpenAI
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💰 가격문의", callback_data="price")],
        [InlineKeyboardButton("🤝 제휴문의", callback_data="partner")],
        [InlineKeyboardButton("📞 관리자 연결", callback_data="admin")],
        [InlineKeyboardButton("❓ 기타문의", callback_data="etc")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "안녕하세요 👋\n실시간 고객센터입니다.\n원하시는 메뉴를 선택해주세요.",
        reply_markup=reply_markup,
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    messages = {
        "price": "가격 문의를 선택하셨습니다 😊",
        "partner": "제휴 문의를 선택하셨습니다 🤝",
        "admin": "관리자에게 연결 요청을 전달했습니다 📞",
        "etc": "문의 내용을 입력해주세요 😊",
    }

    await query.message.reply_text(messages[query.data])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 새 문의 도착\n\n{user_message}",
    )

    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {
                    "role": "system",
                    "content": "너는 친절한 텔레그램 고객센터 상담원이다.",
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        ai_reply = completion.choices[0].message.content

    except Exception:
        ai_reply = "현재 문의가 많아 잠시 후 다시 시도해주세요 🙏"

    await update.message.reply_text(ai_reply)

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("봇 실행중...")
app.run_polling()
