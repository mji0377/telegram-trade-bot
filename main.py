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
sessions = {}  # user_id -> session data
vip_users = set()

# =========================
# 시작 상태 체크 (재문의 제한용)
# =========================
def can_chat(user_id):
    return user_id in sessions and sessions[user_id]["status"] != "END"

# =========================
# start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    sessions.setdefault(user_id, {
        "no": None,
        "status": "NEW",
        "last_time": time.time()
    })

    keyboard = [
        [InlineKeyboardButton("🛠 봇 관리 문의", callback_data="bot")],
        [InlineKeyboardButton("🎰 파칭코 제휴문의", callback_data="pachinko")],
        [InlineKeyboardButton("💬 기타 문의", callback_data="etc")],
        [InlineKeyboardButton("📞 상담원 요청", callback_data="admin")]
    ]

    await update.message.reply_text(
        "👋 고객센터입니다\n문의 유형을 선택해주세요.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# 상담 생성
# =========================
def create_session(user_id):
    global queue_number

    queue_number += 1

    sessions[user_id] = {
        "no": queue_number,
        "status": "ACTIVE",
        "last_time": time.time()
    }

    return queue_number

# =========================
# 버튼
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "admin":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📞 상담 요청\n유저ID: {query.from_user.id}"
        )
        await query.message.reply_text("📞 상담 요청이 전달되었습니다.")
        return

    await query.message.reply_text("내용을 입력해주세요.")

# =========================
# 메시지
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    text = update.message.text
    now = time.time()

    # ❌ 상담 종료 상태면 재시작 필요
    if user_id in sessions and sessions[user_id]["status"] == "END":
        await update.message.reply_text("상담이 종료되었습니다. /start 를 다시 눌러주세요.")
        return

    # 종료 요청
    if text.lower() in ["종료", "끝", "/end", "상담종료"]:

        if user_id in sessions:
            sessions[user_id]["status"] = "END"

        await update.message.reply_text("✅ 상담이 종료되었습니다.\n다시 시작하려면 /start")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ 상담 종료\n유저ID: {user_id}"
        )
        return

    # 신규 상담
    if user_id not in sessions or sessions[user_id]["no"] is None:
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
💬 내용: {text}
⭐ VIP: {"YES" if user_id in vip_users else "NO"}"""
    )

    # 유저 응답
    msg = f"⏳ 상담 접수 완료\n🎫 대기번호: {no}"

    if user_id in vip_users:
        msg = "⭐ VIP 고객 우선 처리 중\n" + msg

    await update.message.reply_text(msg)

# =========================
# /reply
# =========================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("사용법: /reply user_id 내용")
        return

    user_id = int(context.args[0])
    text = " ".join(context.args[1:])

    await context.bot.send_message(chat_id=user_id, text=f"📞 답변\n\n{text}")

    if user_id in sessions:
        sessions[user_id]["last_time"] = time.time()

    await update.message.reply_text("전송 완료")

# =========================
# /done
# =========================
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    user_id = int(context.args[0])

    if user_id in sessions:
        sessions[user_id]["status"] = "END"

    await context.bot.send_message(chat_id=user_id, text="✅ 상담 종료 (재시작 필요 /start)")
    await update.message.reply_text("종료 완료")

# =========================
# /list
# =========================
async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    msg = "📋 상담 리스트\n\n"

    for uid, data in sessions.items():
        msg += f"👤 {uid} | {data['status']} | #{data['no']}\n"

    await update.message.reply_text(msg or "없음")

# =========================
# /waiting
# =========================
async def waiting(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    count = sum(1 for s in sessions.values() if s["status"] == "ACTIVE")

    await update.message.reply_text(f"⏳ 대기중: {count}명")

# =========================
# /vip
# =========================
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    user_id = int(context.args[0])
    vip_users.add(user_id)

    await update.message.reply_text("VIP 등록 완료")

# =========================
# /broadcast
# =========================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    text = " ".join(context.args)

    for uid in sessions:
        await context.bot.send_message(chat_id=uid, text=f"📢 공지\n\n{text}")

    await update.message.reply_text("공지 완료")

# =========================
# /transfer
# =========================
async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id != ADMIN_ID:
        return

    from_id = int(context.args[0])
    to_id = int(context.args[1])

    if from_id in sessions:
        sessions[to_id] = sessions.pop(from_id)

    await update.message.reply_text("이관 완료")

# =========================
# 실행
# =========================
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.add_handler(CommandHandler("reply", reply))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("list", list_cmd))
app.add_handler(CommandHandler("waiting", waiting))
app.add_handler(CommandHandler("vip", vip))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("transfer", transfer))

print("BOT STARTED")
app.run_polling()
