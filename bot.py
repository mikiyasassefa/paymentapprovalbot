import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes,
)
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
BOT_TOKEN     = os.getenv("BOT_TOKEN",     "8714196040:AAF5W_X0CzbmLirEBs9ej8JTWk7FxT_ragI")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "8208198748"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@Dessiemeredajaedr")
WAIT_HOURS    = 12

GROUPS = ["አራዳ", "ሀገር ግዛት", "ሆጤ", "ሳላይሽ", "ሜጠሮ"]

PAYMENT_ACCOUNT = (
    "🏦 የደሴ መረዳጃ እድር\n"
    "🏛 Commercial Bank of Ethiopia (CBE)\n"
    "💳 Account Number: 1000727096152"
)

DB_FILE = "payments.json"   # saved in the same folder as bot.py

# ─────────────────────────────────────────────
#  CONVERSATION STATES
# ─────────────────────────────────────────────
ASK_NAME, ASK_PAYEE, ASK_GROUP, ASK_MONTH_FROM, ASK_MONTH_TO, ASK_SCREENSHOT = range(6)

APPROVE_PREFIX = "approve_"
REJECT_PREFIX  = "reject_"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  DATABASE HELPERS  (simple JSON file)
# ─────────────────────────────────────────────

def load_db() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_db(db: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def save_payment(user_id: int, data: dict):
    db = load_db()
    db[str(user_id)] = {
        "user_id":    user_id,
        "name":       data.get("name", "N/A"),
        "payee":      data.get("payee", "N/A"),
        "group":      data.get("group", "N/A"),
        "month_from": data.get("month_from", "N/A"),
        "month_to":   data.get("month_to", "N/A"),
        "screenshot": data.get("screenshot_file_id", ""),
        "username":   data.get("username", "N/A"),
        "status":     "pending",
        "submitted":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    save_db(db)


def update_payment_status(user_id: int, status: str):
    db = load_db()
    key = str(user_id)
    if key in db:
        db[key]["status"] = status
        save_db(db)


def get_pending_payments() -> list:
    db = load_db()
    return [v for v in db.values() if v.get("status") == "pending"]


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def help_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🆘 Help / እርዳታ", callback_data="help")]])


def format_payment(p: dict) -> str:
    return (
        f"👤 Name: {p['name']}\n"
        f"💳 Paying for: {p['payee']}\n"
        f"🏘 Group: {p['group']}\n"
        f"📅 Period: {p['month_from']} to {p['month_to']}\n"
        f"📱 Username: {p['username']}\n"
        f"🆔 Telegram ID: {p['user_id']}\n"
        f"🕐 Submitted: {p['submitted']}"
    )


# ─────────────────────────────────────────────
#  CONVERSATION HANDLERS
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    welcome = (
        "👋 እንኳን ደህና መጡ!\n"
        "Welcome to *የደሴ መረዳጃ እድር* Payment Bot! 🙏\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{PAYMENT_ACCOUNT}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✏️ *Step 1 of 5* — Please enter your *full name*:\n"
        "ሙሉ ስምዎን ይጻፉ:"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=help_keyboard())
    return ASK_NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("⚠️ Please enter a valid name.")
        return ASK_NAME
    context.user_data["name"] = name
    await update.message.reply_text(
        f"✅ ስም: *{name}*\n\n"
        "✏️ *Step 2 of 5* — ለማን ይከፍላሉ?\n"
        "Who are you paying for? (write their full name)",
        parse_mode="Markdown", reply_markup=help_keyboard(),
    )
    return ASK_PAYEE


async def got_payee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    payee = update.message.text.strip()
    if not payee:
        await update.message.reply_text("⚠️ Please enter a valid name.")
        return ASK_PAYEE
    context.user_data["payee"] = payee

    rows = []
    for i in range(0, len(GROUPS) - 1, 2):
        rows.append([
            InlineKeyboardButton(GROUPS[i],     callback_data=f"group_{GROUPS[i]}"),
            InlineKeyboardButton(GROUPS[i + 1], callback_data=f"group_{GROUPS[i + 1]}"),
        ])
    if len(GROUPS) % 2 == 1:
        rows.append([InlineKeyboardButton(GROUPS[-1], callback_data=f"group_{GROUPS[-1]}")])

    await update.message.reply_text(
        f"✅ ተከፋዩ: *{payee}*\n\n"
        "✏️ *Step 3 of 5* — የትኛው ቡድን ነዎት?\n"
        "Which group are you in?",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(rows),
    )
    return ASK_GROUP


async def got_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    group = query.data.replace("group_", "")
    context.user_data["group"] = group
    await query.edit_message_text(
        f"✅ ቡድን: *{group}*\n\n"
        "✏️ *Step 4 of 5* — ክፍያው ከ ምን ጊዜ ጀምሮ ነው?\n"
        "Payment *from* which month/year?\n"
        "📝 Example: ጥቅምት 2017  or  October 2024",
        parse_mode="Markdown",
    )
    return ASK_MONTH_FROM


async def got_month_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["month_from"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ ከ: *{context.user_data['month_from']}*\n\n"
        "✏️ *Step 5 of 5* — ክፍያው እስከ ምን ጊዜ ድረስ ነው?\n"
        "Payment *up to* which month/year?\n"
        "📝 Example: ህዳር 2017  or  November 2024",
        parse_mode="Markdown", reply_markup=help_keyboard(),
    )
    return ASK_MONTH_TO


async def got_month_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["month_to"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ እስከ: *{context.user_data['month_to']}*\n\n"
        "📸 *Final Step* — እባክዎ የክፍያ ደረሰኝ ስክሪንሾት ይላኩ!\n"
        "Please send a *screenshot* of your bank transfer now.",
        parse_mode="Markdown", reply_markup=help_keyboard(),
    )
    return ASK_SCREENSHOT


async def got_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ Please send a *photo/screenshot* of your payment.\n"
            "እባክዎ ፎቶ ብቻ ይላኩ!",
            parse_mode="Markdown",
        )
        return ASK_SCREENSHOT

    photo = update.message.photo[-1]
    context.user_data["screenshot_file_id"] = photo.file_id

    user = update.effective_user
    context.user_data["username"] = f"@{user.username}" if user.username else f"ID:{user.id}"

    # ── Save to database ────────────────────────────────────────
    save_payment(user.id, context.user_data)
    logger.info(f"Payment saved to DB for user {user.id}")

    d = context.user_data

    # ── Thank the user ─────────────────────────────────────────
    await update.message.reply_text(
        "🎉 *ስክሪንሾቱ ደርሷል! Screenshot received!*\n\n"
        "📋 *Summary:*\n"
        f"   👤 Name: {d.get('name')}\n"
        f"   💳 Paying for: {d.get('payee')}\n"
        f"   🏘 Group: {d.get('group')}\n"
        f"   📅 Period: {d.get('month_from')} to {d.get('month_to')}\n\n"
        f"⏳ Your payment will be reviewed within *{WAIT_HOURS} hours*.\n"
        "📢 You will be notified once the admin approves or rejects.\n\n"
        "🙏 Thank you for your patience!",
        parse_mode="Markdown", reply_markup=help_keyboard(),
    )

    # ── Notify admin ────────────────────────────────────────────
    admin_caption = (
        "🔔 NEW PAYMENT SUBMISSION\n"
        "══════════════════════════\n"
        f"👤 Name: {d.get('name', 'N/A')}\n"
        f"💳 Paying for: {d.get('payee', 'N/A')}\n"
        f"🏘 Group: {d.get('group', 'N/A')}\n"
        f"📅 Period: {d.get('month_from', 'N/A')} to {d.get('month_to', 'N/A')}\n"
        f"🆔 Telegram ID: {user.id}\n"
        f"📱 Username: {context.user_data['username']}\n"
        "══════════════════════════\n"
        "👇 Approve or Reject below:"
    )
    admin_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"{APPROVE_PREFIX}{user.id}"),
        InlineKeyboardButton("❌ Reject",  callback_data=f"{REJECT_PREFIX}{user.id}"),
    ]])

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo.file_id,
            caption=admin_caption,
            reply_markup=admin_keyboard,
        )
        logger.info(f"Admin notified for user {user.id}")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

    return ConversationHandler.END


# ─────────────────────────────────────────────
#  ADMIN: /pending — review saved payments
# ─────────────────────────────────────────────

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Admin only command.")
        return

    payments = get_pending_payments()
    if not payments:
        await update.message.reply_text("✅ No pending payments right now.")
        return

    await update.message.reply_text(f"📋 There are *{len(payments)} pending payment(s)*:", parse_mode="Markdown")

    for p in payments:
        caption = (
            "🔔 PENDING PAYMENT\n"
            "══════════════════════════\n"
            + format_payment(p) +
            "\n══════════════════════════"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"{APPROVE_PREFIX}{p['user_id']}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"{REJECT_PREFIX}{p['user_id']}"),
        ]])

        if p.get("screenshot"):
            try:
                await context.bot.send_photo(
                    chat_id=ADMIN_CHAT_ID,
                    photo=p["screenshot"],
                    caption=caption,
                    reply_markup=keyboard,
                )
                continue
            except Exception:
                pass
        # Fallback: no screenshot available
        await update.message.reply_text(caption, reply_markup=keyboard)


# ─────────────────────────────────────────────
#  ADMIN DECISION — Approve / Reject
# ─────────────────────────────────────────────

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    if query.from_user.id != ADMIN_CHAT_ID:
        await query.answer("⛔ You are not authorized.", show_alert=True)
        return

    data = query.data

    if data.startswith(APPROVE_PREFIX):
        user_id = int(data[len(APPROVE_PREFIX):])
        await query.answer("✅ Payment Approved!")
        update_payment_status(user_id, "approved")

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 *ክፍያዎ ጸድቋል! APPROVED!* ✅\n\n"
                    "የደሴ መረዳጃ እድር ክፍያዎን ተቀብሏል።\n"
                    "Your payment has been *approved* by the admin.\n\n"
                    "ለትዕግስትዎ እናመሰግናለን! 🙏"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Could not notify user {user_id}: {e}")

        try:
            old = query.message.caption or query.message.text or ""
            new_text = old + "\n\n✅ APPROVED by admin"
            if query.message.caption is not None:
                await query.edit_message_caption(caption=new_text)
            else:
                await query.edit_message_text(text=new_text)
        except Exception:
            pass

    elif data.startswith(REJECT_PREFIX):
        user_id = int(data[len(REJECT_PREFIX):])
        await query.answer("❌ Payment Rejected.")
        update_payment_status(user_id, "rejected")

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ *ክፍያዎ አልጸደቀም። REJECTED.*\n\n"
                    "ክፍያዎ አስተዳዳሪው አልጸደቀም።\n"
                    "Your payment was *rejected* by the admin.\n\n"
                    f"For more info contact admin: *{ADMIN_USERNAME}*\n\n"
                    "To try again press /start"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Could not notify user {user_id}: {e}")

        try:
            old = query.message.caption or query.message.text or ""
            new_text = old + "\n\n❌ REJECTED by admin"
            if query.message.caption is not None:
                await query.edit_message_caption(caption=new_text)
            else:
                await query.edit_message_text(text=new_text)
        except Exception:
            pass


# ─────────────────────────────────────────────
#  HELP / MYID / CANCEL
# ─────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🆘 *Help / እርዳታ*\n\n"
        "For questions or assistance, contact the admin:\n"
        f"👤 *Admin:* {ADMIN_USERNAME}\n\n"
        "To restart the payment process, press /start"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 Your Telegram ID is: {user.id}\n"
        f"👤 Username: @{user.username or 'N/A'}\n\n"
        f"ℹ️ Current Admin ID in bot: {ADMIN_CHAT_ID}"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "❌ ተሰርዟል / Cancelled.\nTo start again press /start"
    )
    return ConversationHandler.END


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ለመጀመር /start ይጫኑ። 👇\nPress /start to begin.",
        reply_markup=help_keyboard(),
    )


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME:       [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            ASK_PAYEE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_payee)],
            ASK_GROUP:      [CallbackQueryHandler(got_group, pattern=r"^group_")],
            ASK_MONTH_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_month_from)],
            ASK_MONTH_TO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, got_month_to)],
            ASK_SCREENSHOT: [MessageHandler(filters.PHOTO, got_screenshot)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("help",   help_command),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(help_command,   pattern="^help$"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern=r"^(approve_|reject_)\d+$"))
    app.add_handler(CommandHandler("help",    help_command))
    app.add_handler(CommandHandler("myid",    myid))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(MessageHandler(filters.ALL, unknown_message))

    logger.info("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
