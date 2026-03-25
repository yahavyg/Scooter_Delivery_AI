from database import init_db
from models import get_user_by_telegram_id, get_scooter_profile, get_daily_log
from services import calculate_daily_costs
from ai_service import get_ai_daily_summary

init_db()

user = get_user_by_telegram_id(123456789)
profile = get_scooter_profile(user["id"])
daily_log = get_daily_log(user["id"], "2026-03-25")

calculation_result = calculate_daily_costs(profile, daily_log)

summary = get_ai_daily_summary(daily_log, calculation_result)

print("AI Summary:\n")
print(summary)
