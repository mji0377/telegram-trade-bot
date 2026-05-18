from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# =========================
# 상태 저장 (간단 버전)
# =========================
queue_number = 0
active_sessions = {}  # user_id -> queue_number

# =========================
# 시작 화면
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
        "문의 유형을 선택해주세요.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# 버튼 처리
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "admin":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📞 상담원 요청\n유저ID: {query.from_user.id}"
        )
        await query.message.reply_text("📞 상담원 요청이 전달되었습니다.")
        return

    await query.message.reply_text("내용을 입력해 주세요.")

# =========================
# 문의 접수 (대기번호 시스템)
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global queue_number

    user_id = update.message.from_user.id
    user_message = update.message.text

    # =========================
    # 대기번호 생성
    # =========================
    queue_number += 1
    my_number = queue_number
    active_sessions[user_id] = my_number

    # 관리자 전달
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"""📩 새 문의

🎫 대기번호: {my_number}
👤 유저ID: {user_id}
💬 내용: {user_message}"""
    )

    # 유저 응답
    await update.message.reply_text(
        f"지금은 다른 상담중에 있어 조금만 기다려 주세요.\n\n"
        f"🎫 대기번호: {my_number}"
    )

# =========================
# 상담 종료 (/done)
# =========================
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    if len(context.args) < 1:
        await update.message.reply_text("사용법: /done user_id")
        return

    user_id = int(context.args[0])

    if user_id in active_sessions:
        del active_sessions[user_id]

    await context.bot.send_message(
        chat_id=user_id,
        text="✅ 상담이 종료되었습니다. 이용해주셔서 감사합니다."
    )

    await update.message.reply_text("상담 종료 처리 완료")

# =========================
# 관리자 답장 (/reply)
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
app.add_handler(CommandHandler("done", done))

print("BOT STARTED")
app.run_polling()
