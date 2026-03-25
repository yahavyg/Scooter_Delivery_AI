import requests
import json
import os
from datetime import date
from telegram import Update
from keyboards import main_keyboard, remove_keyboard
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
    create_or_update_scooter_profile,
)

API_BASE = "http://127.0.0.1:8000"

ALLOWED_USER_ID = 851468939

(
    REG_NAME,
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
    SETUP_CURRENT_KM,
    SETUP_LAST_OIL_CHECK_KM,
    SETUP_OIL_CHECK_INTERVAL_KM,
    SETUP_LAST_SERVICE_KM,
    SETUP_SERVICE_INTERVAL_KM,
    DAILY_HOURS,
    DAILY_KM,
    DAILY_INCOME,
    EVENT_AMOUNT,
    EVENT_LITERS,
    EVENT_NOTES,
) = range(23)


def get_today_str():
    return date.today().isoformat()


def safe_float(text: str):
    try:
        return float(text.replace(",", ".").strip())
    except Exception:
        return None


def safe_int(text: str):
    try:
        return int(text.strip())
    except Exception:
        return None


def fmt_money(value):
    try:
        return f"{float(value):,.2f} ₪"
    except Exception:
        return "0.00 ₪"


def fmt_num(value):
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return "0.00"


def pick_first_number(data: dict, keys: list[str], default=0.0):
    for key in keys:
        if key in data and isinstance(data[key], (int, float)):
            return float(data[key])
    return float(default)


def classify_day(net_profit: float, profit_per_hour: float) -> str:
    if net_profit < 0:
        return "יום הפסדי"
    if profit_per_hour < 20:
        return "יום חלש"
    if profit_per_hour < 35:
        return "יום בינוני"
    return "יום טוב"


def validate_engine_cc(value: int):
    if value < 50 or value > 1000:
        return 'נפח מנוע חייב להיות בין 50 ל־1000 סמ"ק.'
    return None


def validate_model_year(value: int):
    if value < 2000 or value > 2026:
        return "שנתון חייב להיות בין 2000 ל־2026."
    return None


def validate_positive_money(value: float, field_name: str):
    if value < 0:
        return f"{field_name} לא יכול להיות שלילי."
    if value > 500000:
        return f"{field_name} לא נראה הגיוני. תבדוק שוב."
    return None


def validate_fuel_km_per_liter(value: float):
    if value < 10 or value > 60:
        return 'ק"מ לליטר חייב להיות בין 10 ל־60.'
    return None


def validate_fuel_price(value: float):
    if value < 1 or value > 20:
        return "מחיר ליטר דלק חייב להיות בין 1 ל־20."
    return None


def validate_km(value: float, field_name: str):
    if value < 0:
        return f"{field_name} לא יכול להיות שלילי."
    if value > 999999:
        return f"{field_name} לא נראה הגיוני. תבדוק שוב."
    return None


def validate_interval(value: float, field_name: str, min_value: float, max_value: float):
    if value < min_value or value > max_value:
        return f'{field_name} חייב להיות בין {int(min_value)} ל־{int(max_value)} ק"מ.'
    return None


async def send_today_summary(update: Update, telegram_id: int):
    try:
        response = requests.get(
            f"{API_BASE}/daily-summary/{telegram_id}",
            params={"log_date": get_today_str()},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            await update.message.reply_text(data["summary"], reply_markup=main_keyboard())
    except Exception:
        pass


# =========================
# START / REGISTRATION
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("הגישה נדחתה תשלח לי הודעה לעשות מנוי ב10 שקלים בחודש @Ygdevxxx ")
        return ConversationHandler.END

    telegram_id = update.effective_user.id
    user = get_user_by_telegram_id(telegram_id)

    if user:
        await update.message.reply_text(
            "המערכת פעילה.\nבחר פעולה:",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "ברוך הבא ל־Delivery System AI Bot.\n"
        "מערכת AI חכמה לרוכבי משלוחים על קטנוע.\n\n"
        "אני עוזר לך להבין כמה באמת נשאר לך ביד\n"
        "אחרי דלק, תחזוקה, הוצאות והפסדים.\n\n"
        "נתחיל קצר.\n"
        "מה השם שלך?",
        reply_markup=remove_keyboard()
    )
    return REG_NAME


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    if not name:
        await update.message.reply_text("תכתוב שם תקין.")
        return REG_NAME

    telegram_id = update.effective_user.id

    create_user(
        telegram_id=telegram_id,
        name=name,
        phone="",
        email="",
        username=f"tg_{telegram_id}",
        password="",
    )

    await update.message.reply_text(
        "מעולה.\n"
        "עכשיו נגדיר את הקטנוע כדי שאוכל לחשב לך רווח אמיתי.\n\n"
        "מה סוג הקטנוע?\n"
        "לדוגמה: סאן יאנג / הונדה / ימאהה"
    )
    return SETUP_SCOOTER_TYPE


async def setup_scooter_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = (update.message.text or "").strip()
    if not value:
        await update.message.reply_text("תכתוב סוג קטנוע תקין.")
        return SETUP_SCOOTER_TYPE

    context.user_data["scooter_type"] = value
    await update.message.reply_text('מה נפח המנוע?\nלדוגמה: 125 / 250 / 300')
    return SETUP_ENGINE_CC


async def setup_engine_cc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_int(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין לנפח מנוע.")
        return SETUP_ENGINE_CC

    error = validate_engine_cc(val)
    if error:
        await update.message.reply_text(error)
        return SETUP_ENGINE_CC

    context.user_data["engine_cc"] = val
    await update.message.reply_text("מה השנתון של הקטנוע?\nלדוגמה: 2022")
    return SETUP_YEAR


async def setup_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_int(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס שנתון תקין.")
        return SETUP_YEAR

    error = validate_model_year(val)
    if error:
        await update.message.reply_text(error)
        return SETUP_YEAR

    context.user_data["model_year"] = val
    await update.message.reply_text("מה היה מחיר הקנייה של הקטנוע?")
    return SETUP_PURCHASE_PRICE


async def setup_purchase_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין למחיר הקנייה.")
        return SETUP_PURCHASE_PRICE

    error = validate_positive_money(val, "מחיר קנייה")
    if error:
        await update.message.reply_text(error)
        return SETUP_PURCHASE_PRICE

    context.user_data["purchase_price"] = val
    await update.message.reply_text(
        "כמה בערך אתה מוציא בשנה על טיפולים ותיקונים?\n"
        "אם אתה לא בטוח, תכניס הערכה."
    )
    return SETUP_GARAGE_YEARLY


async def setup_garage_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין לעלות טיפולים ותיקונים שנתית.")
        return SETUP_GARAGE_YEARLY

    error = validate_positive_money(val, "עלות טיפולים ותיקונים שנתית")
    if error:
        await update.message.reply_text(error)
        return SETUP_GARAGE_YEARLY

    context.user_data["historical_garage_yearly"] = val
    await update.message.reply_text("מה עלות הטסט השנתית?")
    return SETUP_TEST_YEARLY


async def setup_test_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין לעלות טסט שנתית.")
        return SETUP_TEST_YEARLY

    error = validate_positive_money(val, "עלות טסט שנתית")
    if error:
        await update.message.reply_text(error)
        return SETUP_TEST_YEARLY

    context.user_data["annual_test"] = val
    await update.message.reply_text("מה עלות הביטוח השנתית?")
    return SETUP_INSURANCE_YEARLY


async def setup_insurance_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין לעלות ביטוח שנתית.")
        return SETUP_INSURANCE_YEARLY

    error = validate_positive_money(val, "עלות ביטוח שנתית")
    if error:
        await update.message.reply_text(error)
        return SETUP_INSURANCE_YEARLY

    context.user_data["annual_insurance"] = val
    await update.message.reply_text("כמה יש לך הלוואות שנתיות על הקטנוע?\nאם אין, תכניס 0")
    return SETUP_LOANS_YEARLY


async def setup_loans_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין להלוואות שנתיות.")
        return SETUP_LOANS_YEARLY

    error = validate_positive_money(val, "הלוואות שנתיות")
    if error:
        await update.message.reply_text(error)
        return SETUP_LOANS_YEARLY

    context.user_data["annual_loans"] = val
    await update.message.reply_text("כמה קנסות יש לך בשנה?\nאם אין, תכניס 0")
    return SETUP_FINES_YEARLY


async def setup_fines_yearly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס סכום תקין לקנסות שנתיים.")
        return SETUP_FINES_YEARLY

    error = validate_positive_money(val, "קנסות שנתיים")
    if error:
        await update.message.reply_text(error)
        return SETUP_FINES_YEARLY

    context.user_data["annual_fines"] = val
    await update.message.reply_text(
        'כמה ק"מ לליטר הקטנוע עושה בממוצע?\n'
        "אם אתה לא בטוח, תכניס הערכה סבירה.\n"
        "ברוב הקטנועים זה בדרך כלל בין 20 ל־40."
    )
    return SETUP_FUEL_KM_PER_LITER


async def setup_fuel_km_per_liter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text('תכניס מספר תקין לק"מ לליטר.')
        return SETUP_FUEL_KM_PER_LITER

    error = validate_fuel_km_per_liter(val)
    if error:
        await update.message.reply_text(error)
        return SETUP_FUEL_KM_PER_LITER

    context.user_data["fuel_km_per_liter"] = val
    await update.message.reply_text(
        "מה מחיר ליטר דלק כרגע?\n"
        "אם אתה לא בטוח, תכניס את המחיר האחרון ששילמת."
    )
    return SETUP_FUEL_PRICE_PER_LITER


async def setup_fuel_price_per_liter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מחיר תקין לליטר דלק.")
        return SETUP_FUEL_PRICE_PER_LITER

    error = validate_fuel_price(val)
    if error:
        await update.message.reply_text(error)
        return SETUP_FUEL_PRICE_PER_LITER

    context.user_data["fuel_price_per_liter"] = val
    await update.message.reply_text('מה הק"מ הנוכחי של הקטנוע?')
    return SETUP_CURRENT_KM


async def setup_current_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text('תכניס ק"מ נוכחי תקין.')
        return SETUP_CURRENT_KM

    error = validate_km(val, 'ק"מ נוכחי')
    if error:
        await update.message.reply_text(error)
        return SETUP_CURRENT_KM

    context.user_data["current_km"] = val

    await update.message.reply_text(
        "מעולה. עכשיו נגדיר גם תחזוקה כדי שאוכל להתריע לך בזמן.\n\n"
        'באיזה ק"מ בדקת שמן לאחרונה?'
    )
    return SETUP_LAST_OIL_CHECK_KM


async def setup_last_oil_check_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text('תכניס ק"מ תקין לבדיקה אחרונה של שמן.')
        return SETUP_LAST_OIL_CHECK_KM

    error = validate_km(val, 'ק"מ בדיקת שמן אחרונה')
    if error:
        await update.message.reply_text(error)
        return SETUP_LAST_OIL_CHECK_KM

    context.user_data["last_oil_check_km"] = val
    await update.message.reply_text(
        'כל כמה ק"מ אתה רוצה תזכורת לבדוק שמן?\n'
        "לרוב אפשר להתחיל עם 500 או 1000."
    )
    return SETUP_OIL_CHECK_INTERVAL_KM


async def setup_oil_check_interval_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין למרווח בדיקת שמן.")
        return SETUP_OIL_CHECK_INTERVAL_KM

    error = validate_interval(val, "מרווח בדיקת שמן", 100, 5000)
    if error:
        await update.message.reply_text(error)
        return SETUP_OIL_CHECK_INTERVAL_KM

    context.user_data["oil_check_interval_km"] = val
    await update.message.reply_text('באיזה ק"מ עשית טיפול אחרון?')
    return SETUP_LAST_SERVICE_KM


async def setup_last_service_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text('תכניס ק"מ תקין לטיפול אחרון.')
        return SETUP_LAST_SERVICE_KM

    error = validate_km(val, 'ק"מ טיפול אחרון')
    if error:
        await update.message.reply_text(error)
        return SETUP_LAST_SERVICE_KM

    context.user_data["last_service_km"] = val
    await update.message.reply_text(
        'כל כמה ק"מ אתה רוצה תזכורת לטיפול?\n'
        "לרוב זה באזור 3000 עד 5000."
    )
    return SETUP_SERVICE_INTERVAL_KM


async def setup_service_interval_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None:
        await update.message.reply_text("תכניס מספר תקין למרווח טיפול.")
        return SETUP_SERVICE_INTERVAL_KM

    error = validate_interval(val, "מרווח טיפול", 500, 10000)
    if error:
        await update.message.reply_text(error)
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
        avg_km_per_day=0,
        oil_cost_per_km=0,
        depreciation_km_cost_per_km=0,
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
        "ההגדרה הושלמה.\n"
        "המערכת מוכנה.\n\n"
        "מעכשיו אני אחשב לך:\n"
        "- רווח / הפסד אמיתי\n"
        "- דלק\n"
        "- תחזוקה\n"
        "- הוצאות קבועות\n"
        "- התראות שמן וטיפול\n\n"
        "בחר פעולה:",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


# =========================
# REPORTS
# =========================
async def today_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    log_date = get_today_str()

    try:
        response = requests.get(
            f"{API_BASE}/daily-summary/{telegram_id}",
            params={"log_date": log_date},
            timeout=10
        )

        if response.status_code != 200:
            await update.message.reply_text("לא נמצא דוח להיום.", reply_markup=main_keyboard())
            return

        data = response.json()
        await update.message.reply_text(data["summary"], reply_markup=main_keyboard())

    except Exception as e:
        await update.message.reply_text(f"שגיאה בשליפת דוח היום:\n{e}", reply_markup=main_keyboard())


async def week_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    try:
        response = requests.get(
            f"{API_BASE}/weekly-report/{telegram_id}",
            timeout=10
        )

        if response.status_code != 200:
            await update.message.reply_text("לא נמצא דוח שבועי.", reply_markup=main_keyboard())
            return

        data = response.json()
        await update.message.reply_text(data["report"], reply_markup=main_keyboard())

    except Exception as e:
        await update.message.reply_text(f"שגיאה בשליפת דוח שבועי:\n{e}", reply_markup=main_keyboard())


async def month_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    try:
        response = requests.get(
            f"{API_BASE}/monthly-report/{telegram_id}",
            timeout=10
        )

        if response.status_code != 200:
            await update.message.reply_text("לא נמצא דוח חודשי.", reply_markup=main_keyboard())
            return

        data = response.json()
        await update.message.reply_text(data["report"], reply_markup=main_keyboard())

    except Exception as e:
        await update.message.reply_text(f"שגיאה בשליפת דוח חודשי:\n{e}", reply_markup=main_keyboard())


# =========================
# DAILY UPDATE FLOW
# =========================
async def update_day_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("קודם תסיים הרשמה דרך /start")
        return ConversationHandler.END

    context.user_data["flow_type"] = "daily_update"
    await update.message.reply_text("כמה שעות עבדת היום?\nתכניס מספר. לדוגמה: 8")
    return DAILY_HOURS


async def update_day_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val < 0 or val > 24:
        await update.message.reply_text("שעות עבודה חייבות להיות בין 0 ל־24.")
        return DAILY_HOURS

    context.user_data["hours_worked"] = val
    await update.message.reply_text('כמה ק"מ עשית היום?')
    return DAILY_KM


async def update_day_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val < 0 or val > 1000:
        await update.message.reply_text('ק"מ יומי חייב להיות בין 0 ל־1000.')
        return DAILY_KM

    context.user_data["km_done"] = val
    await update.message.reply_text("כמה הרווחת היום?")
    return DAILY_INCOME


async def update_day_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val < 0 or val > 100000:
        await update.message.reply_text("הכנסה יומית חייבת להיות בין 0 ל־100000.")
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
            timeout=20
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"שגיאה בשמירת היום:\n{response.text}",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        data = response.json()
        calculation = data.get("calculation", {}) or {}

        income = pick_first_number(calculation, ["total_income", "income"], default=val)
        total_expenses = pick_first_number(
            calculation,
            ["total_daily", "total_cost", "total_costs", "total_expenses", "expenses"],
            default=0
        )
        fuel_cost = pick_first_number(
            calculation,
            ["fuel_cost", "fuel", "fuel_expense", "fuel_expenses"],
            default=0
        )
        fixed_cost = pick_first_number(
            calculation,
            ["fixed_daily", "fixed_daily_cost", "fixed_cost", "fixed_expenses", "daily_fixed_cost"],
            default=0
        )
        maintenance_cost = (
            pick_first_number(calculation, ["service_cost"], 0)
            + pick_first_number(calculation, ["repair_cost"], 0)
            + pick_first_number(calculation, ["fine_cost"], 0)
            + pick_first_number(calculation, ["food_cost"], 0)
            + pick_first_number(calculation, ["oil_cost"], 0)
            + pick_first_number(calculation, ["depreciation_km_cost"], 0)
        )
        net_profit = pick_first_number(
            calculation,
            ["profit", "net_profit", "daily_profit", "profit_loss"],
            default=income - total_expenses
        )

        hours_worked = context.user_data["hours_worked"]
        km_done = context.user_data["km_done"]

        cost_per_km = (total_expenses / km_done) if km_done > 0 else 0
        profit_per_hour = (net_profit / hours_worked) if hours_worked > 0 else 0
        day_rating = classify_day(net_profit, profit_per_hour)

        msg = (
            "סיכום היום שלך\n\n"
            f"- שעות עבודה: {fmt_num(hours_worked)}\n"
            f'- ק"מ היום: {fmt_num(km_done)}\n'
            f"- הכנסה: {fmt_money(income)}\n"
            f"- דלק: {fmt_money(fuel_cost)}\n"
            f"- הוצאות קבועות: {fmt_money(fixed_cost)}\n"
            f"- תחזוקה והוצאות נוספות: {fmt_money(maintenance_cost)}\n"
            f"- סך כל ההוצאות: {fmt_money(total_expenses)}\n"
            f"- נשאר לך היום נקי: {fmt_money(net_profit)}\n"
            f'- עלות ממוצעת לק"מ היום: {fmt_money(cost_per_km)}\n'
            f"- רווח נקי לשעת עבודה: {fmt_money(profit_per_hour)}\n"
            f"- דירוג היום: {day_rating}\n"
            f'- ק"מ נוכחי: {fmt_num(data.get("current_km", 0))}'
        )

        ai_summary = (data.get("ai_summary") or "").strip()
        if ai_summary:
            msg += f"\n\nAI:\n{ai_summary}"

        if data.get("maintenance_alerts"):
            msg += "\n\nתחזוקה:\n" + "\n".join(data["maintenance_alerts"])

        await update.message.reply_text(msg, reply_markup=main_keyboard())

    except Exception as e:
        await update.message.reply_text(f"שגיאה בחיבור ל־API:\n{e}", reply_markup=main_keyboard())

    return ConversationHandler.END


# =========================
# EVENT FLOW
# =========================
EVENT_CONFIG = {
    "income": {
        "label": "הכנסה נוספת",
        "ask_amount": "כמה קיבלת?",
        "needs_liters": False,
    },
    "tip": {
        "label": "טיפ",
        "ask_amount": "כמה טיפ קיבלת?",
        "needs_liters": False,
    },
    "fuel": {
        "label": "דלק",
        "ask_amount": "כמה שילמת על הדלק?",
        "needs_liters": True,
    },
    "service": {
        "label": "טיפול",
        "ask_amount": "כמה עלה הטיפול?",
        "needs_liters": False,
    },
    "repair": {
        "label": "תיקון",
        "ask_amount": "כמה עלה התיקון?",
        "needs_liters": False,
    },
    "fine": {
        "label": "דוח",
        "ask_amount": "כמה עלה הדוח?",
        "needs_liters": False,
    },
    "food": {
        "label": "אוכל/שתייה",
        "ask_amount": "כמה הוצאת על אוכל/שתייה?",
        "needs_liters": False,
    },
}


async def start_event_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, event_type: str):
    telegram_id = update.effective_user.id
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("קודם תסיים הרשמה דרך /start")
        return ConversationHandler.END

    context.user_data["flow_type"] = "event"
    context.user_data["event_type"] = event_type
    context.user_data["event_date"] = get_today_str()
    context.user_data["event_liters"] = 0
    context.user_data["event_notes"] = ""

    cfg = EVENT_CONFIG[event_type]
    await update.message.reply_text(cfg["ask_amount"])
    return EVENT_AMOUNT


async def event_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    event_type = context.user_data.get("event_type")
    if not event_type:
        await update.message.reply_text("שגיאה בזרימת האירוע.", reply_markup=main_keyboard())
        return ConversationHandler.END

    val = safe_float(update.message.text)
    if val is None or val < 0 or val > 100000:
        await update.message.reply_text("תכניס סכום תקין.")
        return EVENT_AMOUNT

    context.user_data["event_amount"] = val

    if EVENT_CONFIG[event_type]["needs_liters"]:
        await update.message.reply_text("כמה ליטר מילאת?")
        return EVENT_LITERS

    await update.message.reply_text("רוצה להוסיף הערה קצרה? אם לא, תכתוב: לא")
    return EVENT_NOTES


async def event_liters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = safe_float(update.message.text)
    if val is None or val < 0 or val > 100:
        await update.message.reply_text("תכניס כמות ליטרים תקינה.")
        return EVENT_LITERS

    context.user_data["event_liters"] = val
    await update.message.reply_text("רוצה להוסיף הערה קצרה? אם לא, תכתוב: לא")
    return EVENT_NOTES


async def event_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if text.lower() == "לא":
        text = ""

    context.user_data["event_notes"] = text

    telegram_id = update.effective_user.id
    event_type = context.user_data["event_type"]

    payload = {
        "telegram_id": telegram_id,
        "event_date": context.user_data["event_date"],
        "event_type": event_type,
        "amount": context.user_data["event_amount"],
        "liters": context.user_data.get("event_liters", 0),
        "notes": context.user_data.get("event_notes", ""),
    }

    try:
        await update.message.reply_text("שומר את האירוע...")

        response = requests.post(
            f"{API_BASE}/event",
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            await update.message.reply_text(
                f"שגיאה בשמירת האירוע:\n{response.text}",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        data = response.json()

        msg = (
            f"{EVENT_CONFIG[event_type]['label']} נשמר בהצלחה.\n"
            f"- סכום: {fmt_money(payload['amount'])}"
        )

        if event_type == "fuel":
            msg += f"\n- ליטרים: {fmt_num(payload['liters'])}"

        if payload["notes"]:
            msg += f"\n- הערה: {payload['notes']}"

        if data.get("maintenance_alerts"):
            msg += "\n\nתחזוקה:\n" + "\n".join(data["maintenance_alerts"])

        await update.message.reply_text(msg, reply_markup=main_keyboard())

        if data.get("summary"):
            await update.message.reply_text(data["summary"], reply_markup=main_keyboard())

    except Exception as e:
        await update.message.reply_text(f"שגיאה בחיבור ל־API:\n{e}", reply_markup=main_keyboard())

    return ConversationHandler.END


# =========================
# BUTTON ACTIONS
# =========================
async def action_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_event_flow(update, context, "income")


async def action_tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_event_flow(update, context, "tip")


async def action_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_event_flow(update, context, "fuel")


async def action_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_event_flow(update, context, "service")


async def action_repair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_event_flow(update, context, "repair")


async def action_fine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_event_flow(update, context, "fine")


async def action_food(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_event_flow(update, context, "food")


# =========================
# CANCEL
# =========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("בוטל.", reply_markup=main_keyboard())
    return ConversationHandler.END


# =========================
# TEXT ROUTER - REPORTS ONLY
# =========================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text == "דוח היום":
        return await today_report(update, context)

    if text == "דוח שבועי":
        return await week_report(update, context)

    if text == "דוח חודשי":
        return await month_report(update, context)

    return None

import json
import os

OWNER_ID = 851468939
ACCESS_FILE = "access_control.json"


def load_access():
    if not os.path.exists(ACCESS_FILE):
        data = {
            "public_mode": False,
            "allowed_users": [OWNER_ID],
        }
        save_access(data)
        return data

    with open(ACCESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_access(data):
    with open(ACCESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


def is_allowed(update: Update):
    data = load_access()
    user_id = update.effective_user.id

    if data.get("public_mode", False):
        return True

    return user_id in data.get("allowed_users", [])


def add_allowed_user(user_id: int):
    data = load_access()
    users = data.get("allowed_users", [])
    if user_id not in users:
        users.append(user_id)
    data["allowed_users"] = users
    save_access(data)


def remove_allowed_user(user_id: int):
    data = load_access()
    users = data.get("allowed_users", [])
    if user_id in users and user_id != OWNER_ID:
        users.remove(user_id)
    data["allowed_users"] = users
    save_access(data)


def set_public_mode(enabled: bool):
    data = load_access()
    data["public_mode"] = enabled
    save_access(data)


async def public_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    set_public_mode(True)
    await update.message.reply_text("הבוט פתוח לכולם.")


async def public_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    set_public_mode(False)
    await update.message.reply_text("הבוט סגור. רק משתמשים מורשים יכולים להיכנס.")


async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        await update.message.reply_text("שימוש: /allow 123456789")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("תכניס ID תקין.")
        return

    add_allowed_user(user_id)
    await update.message.reply_text(f"המשתמש {user_id} נוסף לרשימת המורשים.")


async def deny_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not context.args:
        await update.message.reply_text("שימוש: /deny 123456789")
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("תכניס ID תקין.")
        return

    remove_allowed_user(user_id)
    await update.message.reply_text(f"המשתמש {user_id} הוסר מרשימת המורשים.")


async def allowed_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    data = load_access()
    public_mode = data.get("public_mode", False)
    users = data.get("allowed_users", [])

    msg = (
        f"Public mode: {'ON' if public_mode else 'OFF'}\n"
        f"Allowed users:\n" + "\n".join(str(u) for u in users)
    )
    await update.message.reply_text(msg)

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("update", update_day_start),

            MessageHandler(filters.Regex("^עדכון יומי$"), update_day_start),
            MessageHandler(filters.Regex("^קיבלתי הכנסה$"), action_income),
            MessageHandler(filters.Regex("^קיבלתי טיפ$"), action_tip),
            MessageHandler(filters.Regex("^מילאתי דלק$"), action_fuel),
            MessageHandler(filters.Regex("^עשיתי טיפול$"), action_service),
            MessageHandler(filters.Regex("^היה תיקון$"), action_repair),
            MessageHandler(filters.Regex("^קיבלתי דוח$"), action_fine),
            MessageHandler(filters.Regex("^קניתי אוכל/שתייה$"), action_food),
        ],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
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
            SETUP_CURRENT_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_current_km)],
            SETUP_LAST_OIL_CHECK_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_last_oil_check_km)],
            SETUP_OIL_CHECK_INTERVAL_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_oil_check_interval_km)],
            SETUP_LAST_SERVICE_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_last_service_km)],
            SETUP_SERVICE_INTERVAL_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_service_interval_km)],
            DAILY_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_hours)],
            DAILY_KM: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_km)],
            DAILY_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_day_income)],
            EVENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_amount)],
            EVENT_LITERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_liters)],
            EVENT_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_notes)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)

    app.add_handler(CommandHandler("public_on", public_on))
    app.add_handler(CommandHandler("public_off", public_off))
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("deny", deny_user))
    app.add_handler(CommandHandler("allowed", allowed_list))

    app.add_handler(CommandHandler("today", today_report))
    app.add_handler(CommandHandler("week", week_report))
    app.add_handler(CommandHandler("month", month_report))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
