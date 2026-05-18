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
# 시작 화면 (이미지 제거 버전)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛠 봇 관리 문의", callback_data="bot")],
        [InlineKeyboardButton("🎰 파칭코 제휴문의", callback_data="pachinko")],
        [InlineKeyboardButton("💬 기타 문의", callback_data="etc")],
        [InlineKeyboardButton("📞 상담원 연결", callback_data="admin")]
    ]

    await update.message.reply_text(
        "👋 안녕하세요 고객님\n\n"
        "📞 24시간 자동 고객센터입니다\n"
        "원하시는 메뉴를 선택하시면 AI가 자동으로 상담해드립니다\n\n"
        "⚡ 상담원 연결도 가능합니다",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# 버튼 처리
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "bot":
        await query.message.reply_text("🛠 봇 관리 문의입니다. 내용을 입력해주세요")

    elif query.data == "pachinko":
        await query.message.reply_text("🎰 파칭코 제휴 문의입니다. 내용을 입력해주세요")

    elif query.data == "etc":
        await query.message.reply_text("💬 기타 문의입니다. 내용을 입력해주세요")

    elif query.data == "admin":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📞 상담원 연결 요청\n유저ID: {query.from_user.id}"
        )
        await query.message.reply_text("📞 상담원에게 연결 요청을 전달했습니다. 잠시만 기다려주세요")

# =========================
# 메시지 처리 (핵심)
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    user_message = update.message.text
    text = user_message.lower()

    # 관리자 알림
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 문의 도착\n\n👤 {user_id}\n💬 {user_message}"
    )

    # =========================
    # 상담원 호출만 예외 처리
    # =========================
    if "상담원" in text or "직원" in text or "사람" in text:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📞 상담원 요청\n유저ID: {user_id}\n내용: {user_message}"
        )

        await update.message.reply_text(
            "📞 상담원 연결 요청이 접수되었습니다.\n잠시만 기다려주세요."
        )
        return

    # =========================
    # 금액 질문 자동 응답
    # =========================
    price_keywords = ["얼마", "가격", "비용", "금액"]

    if any(word in text for word in price_keywords):

        await update.message.reply_text(
            "🛠 봇 관리 설정 비용은 20만원입니다.\n\n"
            "금액 조정이 필요한 경우 상담원 연결을 통해 안내드립니다."
        )
        return

    # =========================
    # 파칭코 자동 응답
    # =========================
    if "파칭코" in text:

        await update.message.reply_text(
            "🎰 파칭코 제휴 금액 안내\n\n"
            "1달 25만원\n"
            "3달 65만원\n"
            "평생 100만원\n\n"
            "금액 조정은 상담원 연결 부탁드립니다."
        )
        return

    # =========================
    # 🚀 핵심: 항상 AI가 응답 (절대 막지 않음)
    # =========================
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 친절한 24시간 고객센터 상담원이다. "
                        "사용자의 질문에 항상 자연스럽고 구체적으로 답변해라."
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
# 관리자 답장 기능
# =========================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("사용법: /reply user_id 내용")
        return

    user_id = int(context.args[0])
    text = " ".join(context.args[1:])

    await context.bot.send_message(
        chat_id=user_id,
        text=f"📞 상담원 답변\n\n{text}"
    )

    await update.message.reply_text("전송 완료")

# =========================
# 실행
# =========================
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("reply", reply))

print("BOT STARTED")
app.run_polling()
