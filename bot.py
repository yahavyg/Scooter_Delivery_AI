import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN

# =========================
# API
# =========================
API_BASE = "http://127.0.0.1:8000"

# =========================
# States
# =========================
DAILY_HOURS, DAILY_KM, DAILY_INCOME = range(3)

# =========================
# Keyboard
# =========================
MAIN_KB = ReplyKeyboardMarkup(
    [
        ["עדכון יומי", "דוח היום"],
        ["דוח שבועי", "דוח חודשי"],
    ],
    resize_keyboard=True
)


# =========================
# Helpers
# =========================
def get_today_str():
    from datetime import date
    return date.today().isoformat()


def safe_float(text: str):
    try:
        return float(text.replace(",", ".").strip())
    except:
        return None


# =========================
# Commands
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "הבוט פעיל.\nבחר פעולה:",
        reply_markup=MAIN_KB
    )


async def today_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    log_date = get_today_str()

    try:
        response = requests.get(
            f"{API_BASE}/daily-summary/{telegram_id}",
            params={"log_date": log_date},
            timeout=20
        )

        if response.status_code != 200:
            await update.message.reply_text("לא נמצא דוח להיום.")
            return

        data = response.json()
        await update.message.reply_text(data["summary"])

    except Exception as e:
        await update.message.reply_text(f"שגיאה בשליפת דוח היום:\n{e}")


async def week_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    try:
        response = requests.get(
            f"{API_BASE}/weekly-report/{telegram_id}",
            timeout=20
        )

        if response.status_code != 200:
            await update.message.reply_text("לא נמצא דוח שבועי.")
            return

        data = response.json()
        await update.message.reply_text(data["report"])

    except Exception as e:
        await update.message.reply_text(f"שגיאה בשליפת דוח שבועי:\n{e}")


async def month_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    try:
        response = requests.get(
            f"{API_BASE}/monthly-report/{telegram_id}",
            timeout=20
        )

        if response.status_code != 200:
            await update.message.reply_text("לא נמצא דוח חודשי.")
            return

        data = response.json()
        await update.message.reply_text(data["report"])

    except Exception as e:
        await update.message.reply_text(f"שגיאה בשליפת דוח חודשי:\n{e}")


# =========================
# Daily Update Flow
# =========================
async def update_day_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("כמה שעות עבדת היום?")
    return DAILY_HOURS


async def update_day_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין.")
        return DAILY_HOURS

    context.user_data["hours_worked"] = val
    await update.message.reply_text('כמה ק"מ עשית היום?')
    return DAILY_KM


async def update_day_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין.")
        return DAILY_KM

    context.user_data["km_done"] = val
    await update.message.reply_text("כמה הרווחת היום?")
    return DAILY_INCOME


async def update_day_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין.")
        return DAILY_INCOME

    telegram_id = update.effective_user.id

    payload = {
        "telegram_id": telegram_id,
        "log_date": get_today_str(),
        "hours_worked": context.user_data["hours_worked"],
        "km_done": context.user_data["km_done"],
        "income": val,
        "status": "manual"
    }

    try:
        response = requests.post(
            f"{API_BASE}/daily-update",
            json=payload,
            timeout=40
        )

        if response.status_code != 200:
            await update.message.reply_text(f"שגיאה בשמירת היום:\n{response.text}")
            return ConversationHandler.END

        data = response.json()

        msg = (
            f"{data['summary']}\n\n"
            f"🤖 AI:\n{data['ai_summary']}\n\n"
            f"📍 ק\"מ נוכחי: {data['current_km']}"
        )

        if data["maintenance_alerts"]:
            msg += "\n\n⚠️ תחזוקה:\n" + "\n".join(data["maintenance_alerts"])

        await update.message.reply_text(msg, reply_markup=MAIN_KB)

    except Exception as e:
        await update.message.reply_text(f"שגיאה בחיבור ל־API:\n{e}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("בוטל.", reply_markup=MAIN_KB)
    return ConversationHandler.END


# =========================
# Text Router
# =========================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text == "עדכון יומי":
        return await update_day_start(update, context)

    if text == "דוח היום":
        return await today_report(update, context)

    if text == "דוח שבועי":
        return await week_report(update, context)

    if text == "דוח חודשי":
        return await month_report(update, context)


# =========================
# Main
# =========================
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("update", update_day_start),
        ],
        states={
            DAILY_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_hours)],
            DAILY_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_km)],
            DAILY_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_income)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today_report))
    app.add_handler(CommandHandler("week", week_report))
    app.add_handler(CommandHandler("month", month_report))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
