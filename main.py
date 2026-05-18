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

# =========================
# 시작 화면 (버튼만)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛠 봇 관리 문의", callback_data="bot")],
        [InlineKeyboardButton("🎰 파칭코 제휴문의", callback_data="pachinko")],
        [InlineKeyboardButton("💬 기타 문의", callback_data="etc")],
        [InlineKeyboardButton("📞 상담원 요청", callback_data="admin")]
    ]

    await update.message.reply_text(
        "👋 안녕하세요 고객님\n\n"
        "24시간 자동 고객센터입니다.\n"
        "아래 버튼을 선택하면 AI가 즉시 상담을 시작합니다.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# 버튼 (중요: 절대 응답 제한 X)
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    # 👉 여기서 아무 "기다려주세요" 같은거 절대 금지
    if query.data == "admin":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📞 상담원 요청\n유저ID: {query.from_user.id}"
        )
        await query.message.reply_text("📞 상담원 요청이 전달되었습니다.")
        return

    # 👉 버튼은 그냥 “상담 시작 트리거”일 뿐
    await query.message.reply_text("이제 상담을 시작합니다. 내용을 입력해주세요.")

# =========================
# 핵심: 모든 메시지는 AI가 처리
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    user_message = update.message.text
    text = user_message.lower()

    # 관리자 알림 (항상)
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 문의\n👤 {user_id}\n💬 {user_message}"
    )

    # =========================
    # 상담원 요청만 예외 처리
    # =========================
    if "상담원" in text or "직원" in text:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📞 상담원 직접 요청\n유저ID: {user_id}\n내용: {user_message}"
        )

        await update.message.reply_text("📞 상담원 연결 요청이 접수되었습니다.")
        return

    # =========================
    # AI가 모든 상담 처리 (핵심)
    # =========================
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 실제 24시간 고객센터 상담원이다. "
                        "사용자의 질문에 절대 거절하지 말고, 항상 자연스럽고 상세하게 답변한다. "
                        "가격 문의, 제휴 문의, 일반 문의 모두 상담센터 직원처럼 처리한다."
                    )
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        reply = completion.choices[0].message.content

    except:
        reply = "현재 상담이 많아 잠시 후 다시 시도해주세요 🙏"

    await update.message.reply_text(reply)

# =========================
# 실행
# =========================
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("BOT STARTED")
app.run_polling()
