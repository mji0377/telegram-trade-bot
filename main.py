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

# ===== 시작 메시지 =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛠 봇 관리 문의", callback_data="bot")],
        [InlineKeyboardButton("🎰 파칭코 제휴문의", callback_data="pachinko")],
        [InlineKeyboardButton("💬 기타 문의", callback_data="etc")],
        [InlineKeyboardButton("📞 상담원 연결", callback_data="admin")]
    ]

    await update.message.reply_text(
        "👋 안녕하세요\n24시간 자동 고객센터입니다\n아래 메뉴를 선택해주세요",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== 버튼 처리 =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "bot":
        await query.message.reply_text("🛠 봇 관리 문의입니다. 내용을 입력해주세요")
    elif query.data == "pachinko":
        await query.message.reply_text("🎰 파칭코 제휴 문의입니다. 내용을 입력해주세요")
    elif query.data == "admin":
        await context.bot.send_message(chat_id=ADMIN_ID, text="📞 상담원 연결 요청 발생")
        await query.message.reply_text("상담원에게 연결 요청을 전달했습니다 📞")
    else:
        await query.message.reply_text("💬 문의 내용을 입력해주세요")

# ===== 메시지 처리 =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text
    text_lower = user_message.lower()

    # 관리자 알림
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 문의 도착\n\n{user_message}"
    )

    # 💰 금액 질문 자동 처리
    price_keywords = ["얼마", "가격", "비용", "금액"]

    if any(word in text_lower for word in price_keywords):

        await update.message.reply_text(
            "봇 관리 설정 비용은 20만원 입니다.\n\n"
            "또한 금액 부분은 조정이 필요한 경우 상담사 연결 해주시면 보다 빠른 상담 드리겠습니다."
        )
        return

    # 🎰 파칭코 관련 자동 응답
    if "파칭코" in text_lower:

        await update.message.reply_text(
            "저희 파칭코방 제휴 금액 알려드리겠습니다.\n\n"
            "1달 25만원\n"
            "3달 65만원\n"
            "평생 100만원\n\n"
            "금액 조정이 필요하시면 상담사 연결 요청해 주세요."
        )
        return

    # 🤖 기타 AI 응답
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

# ===== 실행 =====
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("BOT STARTED")
app.run_polling()
