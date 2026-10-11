import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
BOT_TOKEN    = os.getenv("BOT_TOKEN", "8714196040:AAF5W_X0CzbmLirEBs9ej8JTWk7FxT_ragI")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "8208198748"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@YourAdminUsername")  # update with your @username
WAIT_HOURS   = 12

GROUPS = ["አራዳ", "ሀገር ግዛት", "ሆጤ", "ሳላይሽ", "ሜጠሮ"]

PAYMENT_ACCOUNT = (
    "🏦 የደሴ መረዳጃ እድር\n"
    "🏛️ Commercial Bank of Ethiopia (CBE)\n"
    "💳 Account Number: 1000727096152"
)

# ─────────────────────────────────────────────
#  CONVERSATION STATES
# ─────────────────────────────────────────────
ASK_NAME, ASK_PAYEE, ASK_GROUP, ASK_MONTH_FROM, ASK_MONTH_TO, ASK_SCREENSHOT = range(6)

# Callback data prefixes
APPROVE_PREFIX = "approve_"
REJECT_PREFIX  = "reject_"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def help_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🆘 Help / እርዳታ", callback_data="help")]])


# ─────────────────────────────────────────────
#  CONVERSATION HANDLERS
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Welcome the user and start the conversation."""
    context.user_data.clear()

    welcome = (
        "👋 እንኳን ደህና መጡ!\n"
        "Welcome to *የደሴ መረዳጃ እድር* Payment Bot! 🙏\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{PAYMENT_ACCOUNT}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ክፍያዎን ለማረጋገጥ ቀጣዩን ደረጃዎች ይከተሉ።\n"
        "Follow the steps below to confirm your payment.\n\n"
        "✏️ *Step 1 of 5* — Please enter your *full name*:\n"
        "ሙሉ ስምዎን ይጻፉ:"
    )
    await update.message.reply_text(
        welcome, parse_mode="Markdown", reply_markup=help_keyboard()
    )
    return ASK_NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store name, ask payee."""
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("⚠️ Please enter a valid name. / ስም ያስፈልጋል።")
        return ASK_NAME

    context.user_data["name"] = name
    await update.message.reply_text(
        f"✅ ስም ተመዝግቧል: *{name}*\n\n"
        "✏️ *Step 2 of 5* — ለማን ይከፍላሉ?\n"
        "Who are you paying for? (write their full name)\n"
        "የሚከፈልለትን ሰው ስም ይጻፉ:",
        parse_mode="Markdown",
        reply_markup=help_keyboard(),
    )
    return ASK_PAYEE


async def got_payee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store payee, ask group."""
    payee = update.message.text.strip()
    if not payee:
        await update.message.reply_text("⚠️ Please enter a valid name. / ስም ያስፈልጋል።")
        return ASK_PAYEE

    context.user_data["payee"] = payee

    # Build group keyboard (2 per row, last one centered)
    rows = []
    for i in range(0, len(GROUPS) - 1, 2):
        rows.append([
            InlineKeyboardButton(GROUPS[i],     callback_data=f"group_{GROUPS[i]}"),
            InlineKeyboardButton(GROUPS[i + 1], callback_data=f"group_{GROUPS[i + 1]}"),
        ])
    if len(GROUPS) % 2 == 1:
        rows.append([InlineKeyboardButton(GROUPS[-1], callback_data=f"group_{GROUPS[-1]}")])

    reply_markup = InlineKeyboardMarkup(rows)
    await update.message.reply_text(
        f"✅ ተከፋዩ: *{payee}*\n\n"
        "✏️ *Step 3 of 5* — የትኛው ቡድን ነዎት?\n"
        "Which group are you in? Please select below:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return ASK_GROUP


async def got_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store group, ask month-from."""
    query = update.callback_query
    await query.answer()

    group = query.data.replace("group_", "")
    context.user_data["group"] = group

    await query.edit_message_text(
        f"✅ ቡድን: *{group}*\n\n"
        "✏️ *Step 4 of 5* — ክፍያው ከ ምን ጊዜ ጀምሮ ነው?\n"
        "Payment *from* which month/year?\n\n"
        "📝 Example: ጥቅምት 2017  or  October 2024",
        parse_mode="Markdown",
    )
    return ASK_MONTH_FROM


async def got_month_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store month-from, ask month-to."""
    month_from = update.message.text.strip()
    context.user_data["month_from"] = month_from

    await update.message.reply_text(
        f"✅ ከ: *{month_from}*\n\n"
        "✏️ *Step 5 of 5* — ክፍያው እስከ ምን ጊዜ ድረስ ነው?\n"
        "Payment *up to* which month/year?\n\n"
        "📝 Example: ህዳር 2017  or  November 2024",
        parse_mode="Markdown",
        reply_markup=help_keyboard(),
    )
    return ASK_MONTH_TO


async def got_month_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store month-to, ask for screenshot."""
    month_to = update.message.text.strip()
    context.user_data["month_to"] = month_to

    await update.message.reply_text(
        f"✅ እስከ: *{month_to}*\n\n"
        "📸 *Final Step* — እባክዎ የክፍያ ደረሰኝ ስክሪንሾት ይላኩ!\n"
        "Please send a *screenshot* of your bank transfer now.\n\n"
        "📲 Take a photo/screenshot of your transaction confirmation and send it here.",
        parse_mode="Markdown",
        reply_markup=help_keyboard(),
    )
    return ASK_SCREENSHOT


async def got_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive screenshot, thank user, and notify admin."""
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ Please send a *photo/screenshot* of your payment.\n"
            "እባክዎ ፎቶ ብቻ ይላኩ (screenshot)!",
            parse_mode="Markdown",
        )
        return ASK_SCREENSHOT

    photo = update.message.photo[-1]  # highest resolution
    context.user_data["screenshot_file_id"] = photo.file_id

    user = update.effective_user
    d = context.user_data

    # ── Thank the user ──────────────────────────────────────────
    await update.message.reply_text(
        "🎉 *ስክሪንሾቱ ደርሷል! Screenshot received!*\n\n"
        "📋 *Summary of your submission:*\n"
        f"   👤 Name: {d.get('name')}\n"
        f"   💳 Paying for: {d.get('payee')}\n"
        f"   🏘️ Group: {d.get('group')}\n"
        f"   📅 Period: {d.get('month_from')} → {d.get('month_to')}\n\n"
        f"⏳ ክፍያዎ በ *{WAIT_HOURS} ሰዓታት* ውስጥ ይጸድቃል።\n"
        f"Your payment will be reviewed within *{WAIT_HOURS} hours*.\n\n"
        "📢 አስተዳዳሪው ሲያጸድቅ ወይም ሲቃወም ወዲያውኑ ይነገርዎታል።\n"
        "You will be notified here once the admin approves or rejects.\n\n"
        "🙏 ለትዕግስትዎ እናመሰግናለን! Thank you for your patience!",
        parse_mode="Markdown",
        reply_markup=help_keyboard(),
    )

    # ── Notify admin ─────────────────────────────────────────────
    username_display = f"@{user.username}" if user.username else f"(ID: {user.id})"
    admin_caption = (
        "🔔 *NEW PAYMENT SUBMISSION*\n"
        "══════════════════════════\n"
        f"👤 *Name:* {d.get('name', 'N/A')}\n"
        f"💳 *Paying for:* {d.get('payee', 'N/A')}\n"
        f"🏘️ *Group:* {d.get('group', 'N/A')}\n"
        f"📅 *Period:* {d.get('month_from', 'N/A')} → {d.get('month_to', 'N/A')}\n"
        f"🆔 *Telegram ID:* `{user.id}`\n"
        f"📱 *Username:* {username_display}\n"
        "══════════════════════════\n"
        "👇 Please review the screenshot and approve or reject:"
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
            parse_mode="Markdown",
            reply_markup=admin_keyboard,
        )
        logger.info(f"Admin notified about payment from user {user.id}")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

    return ConversationHandler.END


# ─────────────────────────────────────────────
#  ADMIN DECISION
# ─────────────────────────────────────────────

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin approve/reject button press."""
    query = update.callback_query

    # Verify it's the admin
    if query.from_user.id != ADMIN_CHAT_ID:
        await query.answer("⛔ You are not authorized.", show_alert=True)
        return

    data = query.data
    if data.startswith(APPROVE_PREFIX):
        user_id = int(data[len(APPROVE_PREFIX):])
        await query.answer("✅ Payment Approved!")

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 *ክፍያዎ ጸድቋል! APPROVED!* ✅\n\n"
                    "የደሴ መረዳጃ እድር ክፍያዎን ተቀብሏል።\n"
                    "Your payment has been *approved* by the admin.\n\n"
                    "ለትዕግስትዎ እናመሰግናለን! 🙏\n"
                    "Thank you for being part of our edir!"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Could not notify user {user_id}: {e}")

        # Update admin message
        new_caption = (query.message.caption or "") + "\n\n✅ *APPROVED* by admin ✅"
        try:
            await query.edit_message_caption(caption=new_caption, parse_mode="Markdown")
        except Exception:
            pass

    elif data.startswith(REJECT_PREFIX):
        user_id = int(data[len(REJECT_PREFIX):])
        await query.answer("❌ Payment Rejected.")

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ *ክፍያዎ አልጸደቀም። REJECTED.*\n\n"
                    "ክፍያዎ አስተዳዳሪው ተቀብሎ አልጸደቀም።\n"
                    "Your payment was *rejected* by the admin.\n\n"
                    "ለበለጠ መረጃ አስተዳዳሪውን ያነጋግሩ:\n"
                    f"Contact admin: *{ADMIN_USERNAME}*\n\n"
                    "ለሌላ ሙከራ /start ይጫኑ።\n"
                    "To try again, press /start"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Could not notify user {user_id}: {e}")

        # Update admin message
        new_caption = (query.message.caption or "") + "\n\n❌ *REJECTED* by admin ❌"
        try:
            await query.edit_message_caption(caption=new_caption, parse_mode="Markdown")
        except Exception:
            pass


# ─────────────────────────────────────────────
#  HELP & CANCEL
# ─────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message with admin contact."""
    text = (
        "🆘 *Help / እርዳታ*\n\n"
        "ለጥያቄዎች ወይም ለእርዳታ አስተዳዳሪውን ያነጋግሩ:\n"
        "For questions or assistance, contact the admin:\n\n"
        f"👤 *Admin:* {ADMIN_USERNAME}\n\n"
        "ወደ ክፍያ ሂደቱ ለመመለስ /start ይጫኑ።\n"
        "To restart the payment process, press /start"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ ተሰርዟል / Cancelled.\n"
        "ለመጀመር /start ይጫኑ። To start again, press /start"
    )
    return ConversationHandler.END


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unexpected messages outside the conversation."""
    await update.message.reply_text(
        "ለመጀመር /start ይጫኑ። 👇\n"
        "Press /start to begin.",
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
    app.add_handler(CallbackQueryHandler(help_command,    pattern="^help$"))
    app.add_handler(CallbackQueryHandler(admin_decision,  pattern=r"^(approve_|reject_)\d+$"))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.ALL, unknown_message))

    logger.info("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
