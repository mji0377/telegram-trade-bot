from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# =========================
# 상태 저장
# =========================
queue_number = 0
sessions = {}  # user_id -> {no, status, last_time}

# =========================
# 시작
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🛠 봇 관리 문의", callback_data="bot")],
        [InlineKeyboardButton("🎰 파칭코 제휴문의", callback_data="pachinko")],
        [InlineKeyboardButton("💬 기타 문의", callback_data="etc")],
        [InlineKeyboardButton("📞 상담원 요청", callback_data="admin")]
    ]

    await update.message.reply_text(
        "👋 고객센터입니다\n\n문의 유형을 선택해주세요.",
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

    await query.message.reply_text("내용을 입력해주세요.")

# =========================
# 상담 추가
# =========================
def create_session(user_id):
    global queue_number

    queue_number += 1

    sessions[user_id] = {
        "no": queue_number,
        "status": "WAITING",
        "last_time": time.time()
    }

    return queue_number

# =========================
# 메시지 처리
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    text = update.message.text
    now = time.time()

    # =========================
    # 종료 요청 (유저)
    # =========================
    if text.lower() in ["종료", "끝", "/end", "상담종료"]:

        if user_id in sessions:
            sessions[user_id]["status"] = "END"

        await update.message.reply_text("✅ 상담이 종료되었습니다.")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ 상담 종료 요청\n유저ID: {user_id}"
        )
        return

    # =========================
    # 첫 문의 등록
    # =========================
    if user_id not in sessions:
        no = create_session(user_id)
    else:
        no = sessions[user_id]["no"]

    sessions[user_id]["status"] = "ACTIVE"
    sessions[user_id]["last_time"] = now

    # 관리자 전달
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"""📩 문의

🎫 대기번호: {no}
👤 유저ID: {user_id}
💬 내용: {text}"""
    )

    # 유저 응답
    await update.message.reply_text(
        f"⏳ 현재 상담 대기중입니다.\n"
        f"🎫 대기번호: {no}\n\n"
        f"잠시만 기다려 주세요."
    )

# =========================
# 자동 3분 종료
# =========================
async def auto_close(context: ContextTypes.DEFAULT_TYPE):

    now = time.time()
    to_remove = []

    for user_id, data in sessions.items():

        if data["status"] != "ACTIVE":
            continue

        if now - data["last_time"] > 180:

            await context.bot.send_message(
                chat_id=user_id,
                text="⛔ 3분 동안 응답이 없어 상담이 자동 종료되었습니다."
            )

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⛔ 자동 종료\n유저ID: {user_id}"
            )

            data["status"] = "END"
            to_remove.append(user_id)

    for uid in to_remove:
        sessions.pop(uid, None)

# =========================
# 관리자 답장
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

    if user_id in sessions:
        sessions[user_id]["last_time"] = time.time()

    await update.message.reply_text("전송 완료")

# =========================
# 상담 종료 (관리자)
# =========================
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    if len(context.args) < 1:
        await update.message.reply_text("사용법: /done user_id")
        return

    user_id = int(context.args[0])

    sessions.pop(user_id, None)

    await context.bot.send_message(
        chat_id=user_id,
        text="✅ 상담이 종료되었습니다."
    )

    await update.message.reply_text("상담 종료 완료")

# =========================
# 실행
# =========================
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("reply", reply))
app.add_handler(CommandHandler("done", done))

# 자동 종료 체크 (1분마다)
app.job_queue.run_repeating(auto_close, interval=60, first=10)

print("BOT STARTED")
app.run_polling()
