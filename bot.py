import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN
from models import (
    create_user,
    get_user_by_telegram_id,
    get_user_by_username,
    create_or_update_scooter_profile,
)

# =========================
# API
# =========================
API_BASE = "http://127.0.0.1:8000"

# =========================
# States
# =========================
(
    REG_NAME,
    REG_PHONE,
    REG_EMAIL,
    REG_USERNAME,
    REG_PASSWORD,

    SETUP_SCOOTER_TYPE,
    SETUP_ENGINE_CC,
    SETUP_YEAR,
    SETUP_PURCHASE_PRICE,
    SETUP_GARAGE_YEARLY,
    SETUP_TEST_YEARLY,
    SETUP_INSURANCE_YEARLY,
    SETUP_LOANS_YEARLY,
    SETUP_FINES_YEARLY,
    SETUP_FUEL_KM_PER_LITER,
    SETUP_FUEL_PRICE_PER_LITER,
    SETUP_AVG_KM_PER_DAY,
    SETUP_OIL_COST_PER_KM,
    SETUP_DEP_KM_COST_PER_KM,
    SETUP_CURRENT_KM,
    SETUP_LAST_OIL_CHECK_KM,
    SETUP_OIL_CHECK_INTERVAL_KM,
    SETUP_LAST_SERVICE_KM,
    SETUP_SERVICE_INTERVAL_KM,

    DAILY_HOURS,
    DAILY_KM,
    DAILY_INCOME,
) = range(27)

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


def safe_int(text: str):
    try:
        return int(text.strip())
    except:
        return None


# =========================
# Start / Registration
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = get_user_by_telegram_id(telegram_id)

    if user:
        await update.message.reply_text(
            "הבוט פעיל.\nבחר פעולה:",
            reply_markup=MAIN_KB
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "ברוך הבא.\nנתחיל ברישום.\nמה השם שלך?",
        reply_markup=ReplyKeyboardRemove()
    )
    return REG_NAME


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("מספר טלפון?")
    return REG_PHONE


async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_phone"] = update.message.text.strip()
    await update.message.reply_text("מייל?")
    return REG_EMAIL


async def reg_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reg_email"] = update.message.text.strip()
    await update.message.reply_text("שם משתמש למערכת?")
    return REG_USERNAME


async def reg_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()

    existing = get_user_by_username(username)
    if existing:
        await update.message.reply_text("שם המשתמש תפוס. תבחר אחר.")
        return REG_USERNAME

    context.user_data["reg_username"] = username
    await update.message.reply_text("סיסמה למערכת?")
    return REG_PASSWORD


async def reg_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    telegram_id = update.effective_user.id

    user_id = create_user(
        telegram_id=telegram_id,
        name=context.user_data["reg_name"],
        phone=context.user_data["reg_phone"],
        email=context.user_data["reg_email"],
        username=context.user_data["reg_username"],
        password=password,
    )

    context.user_data["user_id"] = user_id

    await update.message.reply_text(
        "החשבון נוצר.\nעכשיו נגדיר את הקטנוע.\nמה סוג הקטנוע?"
    )
    return SETUP_SCOOTER_TYPE


# =========================
# Scooter Setup
# =========================
async def setup_scooter_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["scooter_type"] = update.message.text.strip()
    await update.message.reply_text("נפח מנוע? למשל 125")
    return SETUP_ENGINE_CC


async def setup_engine_cc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_int(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין.")
        return SETUP_ENGINE_CC
    context.user_data["engine_cc"] = val
    await update.message.reply_text("שנתון? למשל 2022")
    return SETUP_YEAR


async def setup_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_int(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס שנתון תקין.")
        return SETUP_YEAR
    context.user_data["model_year"] = val
    await update.message.reply_text("מחיר קנייה של הקטנוע?")
    return SETUP_PURCHASE_PRICE


async def setup_purchase_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין.")
        return SETUP_PURCHASE_PRICE
    context.user_data["purchase_price"] = val
    await update.message.reply_text("מוסך היסטורי שנתי ממוצע?")
    return SETUP_GARAGE_YEARLY


async def setup_garage_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין.")
        return SETUP_GARAGE_YEARLY
    context.user_data["historical_garage_yearly"] = val
    await update.message.reply_text("עלות טסט שנתית?")
    return SETUP_TEST_YEARLY


async def setup_test_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין.")
        return SETUP_TEST_YEARLY
    context.user_data["annual_test"] = val
    await update.message.reply_text("ביטוח שנתי?")
    return SETUP_INSURANCE_YEARLY


async def setup_insurance_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין.")
        return SETUP_INSURANCE_YEARLY
    context.user_data["annual_insurance"] = val
    await update.message.reply_text("הלוואות שנתיות? אם אין 0")
    return SETUP_LOANS_YEARLY


async def setup_loans_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין.")
        return SETUP_LOANS_YEARLY
    context.user_data["annual_loans"] = val
    await update.message.reply_text("קנסות שנתיים? אם אין 0")
    return SETUP_FINES_YEARLY


async def setup_fines_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין.")
        return SETUP_FINES_YEARLY
    context.user_data["annual_fines"] = val
    await update.message.reply_text('כמה ק"מ לליטר הקטנוע עושה? למשל 30')
    return SETUP_FUEL_KM_PER_LITER


async def setup_fuel_km_per_liter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val <= 0:
        await update.message.reply_text("תכניס מספר תקין.")
        return SETUP_FUEL_KM_PER_LITER
    context.user_data["fuel_km_per_liter"] = val
    await update.message.reply_text("מה מחיר ליטר דלק כרגע?")
    return SETUP_FUEL_PRICE_PER_LITER


async def setup_fuel_price_per_liter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val <= 0:
        await update.message.reply_text("תכניס מחיר תקין.")
        return SETUP_FUEL_PRICE_PER_LITER
    context.user_data["fuel_price_per_liter"] = val
    await update.message.reply_text('ק"מ ממוצע ליום?')
    return SETUP_AVG_KM_PER_DAY


async def setup_avg_km_per_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין.")
        return SETUP_AVG_KM_PER_DAY
    context.user_data["avg_km_per_day"] = val
    await update.message.reply_text('עלות שמן לכל ק"מ? אם אין לך עדיין תכניס 0')
    return SETUP_OIL_COST_PER_KM


async def setup_oil_cost_per_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין.")
        return SETUP_OIL_COST_PER_KM
    context.user_data["oil_cost_per_km"] = val
    await update.message.reply_text('ירידת ערך לפי ק"מ (עלות לכל ק"מ)? אם אין כרגע תכניס 0')
    return SETUP_DEP_KM_COST_PER_KM


async def setup_dep_km_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין.")
        return SETUP_DEP_KM_COST_PER_KM
    context.user_data["depreciation_km_cost_per_km"] = val
    await update.message.reply_text('מה הק"מ הנוכחי של הקטנוע?')
    return SETUP_CURRENT_KM


async def setup_current_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס ק\"מ תקין.")
        return SETUP_CURRENT_KM
    context.user_data["current_km"] = val
    await update.message.reply_text('באיזה ק"מ בדקת שמן לאחרונה?')
    return SETUP_LAST_OIL_CHECK_KM


async def setup_last_oil_check_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס ק\"מ תקין.")
        return SETUP_LAST_OIL_CHECK_KM
    context.user_data["last_oil_check_km"] = val
    await update.message.reply_text('כל כמה ק"מ אתה רוצה תזכורת לבדוק שמן? למשל 500')
    return SETUP_OIL_CHECK_INTERVAL_KM


async def setup_oil_check_interval_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val <= 0:
        await update.message.reply_text("תכניס מספר תקין.")
        return SETUP_OIL_CHECK_INTERVAL_KM
    context.user_data["oil_check_interval_km"] = val
    await update.message.reply_text('באיזה ק"מ עשית טיפול אחרון?')
    return SETUP_LAST_SERVICE_KM


async def setup_last_service_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס ק\"מ תקין.")
        return SETUP_LAST_SERVICE_KM
    context.user_data["last_service_km"] = val
    await update.message.reply_text('כל כמה ק"מ אתה רוצה תזכורת לטיפול? למשל 3000')
    return SETUP_SERVICE_INTERVAL_KM


async def setup_service_interval_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val <= 0:
        await update.message.reply_text("תכניס מספר תקין.")
        return SETUP_SERVICE_INTERVAL_KM

    context.user_data["service_interval_km"] = val

    telegram_id = update.effective_user.id
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("שגיאה ביצירת משתמש.")
        return ConversationHandler.END

    create_or_update_scooter_profile(
        user_id=user["id"],
        scooter_type=context.user_data["scooter_type"],
        engine_cc=context.user_data["engine_cc"],
        model_year=context.user_data["model_year"],
        purchase_price=context.user_data["purchase_price"],
        historical_garage_yearly=context.user_data["historical_garage_yearly"],
        annual_test=context.user_data["annual_test"],
        annual_insurance=context.user_data["annual_insurance"],
        annual_loans=context.user_data["annual_loans"],
        annual_fines=context.user_data["annual_fines"],
        fuel_km_per_liter=context.user_data["fuel_km_per_liter"],
        fuel_price_per_liter=context.user_data["fuel_price_per_liter"],
        avg_km_per_day=context.user_data["avg_km_per_day"],
        oil_cost_per_km=context.user_data["oil_cost_per_km"],
        depreciation_km_cost_per_km=context.user_data["depreciation_km_cost_per_km"],
        fuel_price_mode="manual",
        fuel_type="95",
        country_code="IL",
        current_km=context.user_data["current_km"],
        last_oil_check_km=context.user_data["last_oil_check_km"],
        oil_check_interval_km=context.user_data["oil_check_interval_km"],
        last_service_km=context.user_data["last_service_km"],
        service_interval_km=context.user_data["service_interval_km"],
    )

    await update.message.reply_text(
        "ההגדרה הושלמה.\nהמערכת פעילה.",
        reply_markup=MAIN_KB
    )
    return ConversationHandler.END


# =========================
# Reports
# =========================
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
    telegram_id = update.effective_user.id
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("קודם תסיים הרשמה דרך /start")
        return ConversationHandler.END

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
            CommandHandler("start", start),
            CommandHandler("update", update_day_start),
        ],
        states={
            # Registration
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_phone)],
            REG_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_email)],
            REG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_username)],
            REG_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_password)],

            # Setup
            SETUP_SCOOTER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_scooter_type)],
            SETUP_ENGINE_CC: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_engine_cc)],
            SETUP_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_year)],
            SETUP_PURCHASE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_purchase_price)],
            SETUP_GARAGE_YEARLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_garage_yearly)],
            SETUP_TEST_YEARLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_test_yearly)],
            SETUP_INSURANCE_YEARLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_insurance_yearly)],
            SETUP_LOANS_YEARLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_loans_yearly)],
            SETUP_FINES_YEARLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_fines_yearly)],
            SETUP_FUEL_KM_PER_LITER: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_fuel_km_per_liter)],
            SETUP_FUEL_PRICE_PER_LITER: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_fuel_price_per_liter)],
            SETUP_AVG_KM_PER_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_avg_km_per_day)],
            SETUP_OIL_COST_PER_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_oil_cost_per_km)],
            SETUP_DEP_KM_COST_PER_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_dep_km_cost)],
            SETUP_CURRENT_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_current_km)],
            SETUP_LAST_OIL_CHECK_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_last_oil_check_km)],
            SETUP_OIL_CHECK_INTERVAL_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_oil_check_interval_km)],
            SETUP_LAST_SERVICE_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_last_service_km)],
            SETUP_SERVICE_INTERVAL_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_service_interval_km)],

            # Daily update
            DAILY_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_hours)],
            DAILY_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_km)],
            DAILY_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_income)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("today", today_report))
    app.add_handler(CommandHandler("week", week_report))
    app.add_handler(CommandHandler("month", month_report))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
