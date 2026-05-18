from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ===== 상태 =====
BOT_MODE = "AUTO"  # AUTO / MANUAL

# ===== 시작 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💰 가격문의", callback_data="price")],
        [InlineKeyboardButton("🤝 제휴문의", callback_data="partner")],
        [InlineKeyboardButton("📞 관리자 연결", callback_data="admin")],
        [InlineKeyboardButton("❓ 기타문의", callback_data="etc")]
    ]

    await update.message.reply_text(
        "👋 안녕하세요\n24시간 자동 고객센터입니다\n원하시는 메뉴를 선택해주세요",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== 버튼 처리 =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "admin":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="📞 관리자 연결 요청 발생"
        )
        await query.message.reply_text("관리자에게 연결 요청을 전달했습니다 📞")
        return

    messages = {
        "price": "💰 가격 문의입니다. 내용을 입력해주세요",
        "partner": "🤝 제휴 문의입니다. 내용을 입력해주세요",
        "etc": "❓ 기타 문의입니다. 내용을 입력해주세요"
    }

    await query.message.reply_text(messages.get(query.data, "문의 내용을 입력해주세요"))

# ===== 메시지 처리 =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text

    # 관리자 알림
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 문의 도착\n\n내용:\n{user_message}"
    )

    # 수동 모드
    if BOT_MODE == "MANUAL":
        await update.message.reply_text("현재 상담원이 직접 확인 중입니다 🙏")
        return

    # AI 응답
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {"role": "system", "content": "너는 친절한 고객센터 상담원이다."},
                {"role": "user", "content": user_message}
            ]
        )

        reply = completion.choices[0].message.content

    except:
        reply = "현재 상담이 많아 잠시 후 다시 시도해주세요 🙏"

    await update.message.reply_text(reply)

# ===== 관리자 명령 =====
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global BOT_MODE

    if update.message.chat_id != ADMIN_ID:
        return

    if len(context.args) == 0:
        await update.message.reply_text("사용: /mode auto 또는 /mode manual")
        return

    mode = context.args[0]

    if mode == "auto":
        BOT_MODE = "AUTO"
        await update.message.reply_text("🤖 자동응답 모드 ON")

    elif mode == "manual":
        BOT_MODE = "MANUAL"
        await update.message.reply_text("👨‍💼 수동응답 모드 ON")

# ===== 실행 =====
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mode", admin))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("BOT STARTED")
app.run_polling()
