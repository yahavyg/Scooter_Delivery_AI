from database import init_db
from models import get_user_by_telegram_id, get_scooter_profile, get_daily_log
from services import calculate_daily_costs, build_daily_summary, check_maintenance_alerts

init_db()

user = get_user_by_telegram_id(123456789)
profile = get_scooter_profile(user["id"])
daily_log = get_daily_log(user["id"], "2026-03-25")

result = calculate_daily_costs(profile, daily_log)
print("Calculation result:")
print(result)

print("\nMaintenance alerts:\n")
alerts = check_maintenance_alerts(profile)
for alert in alerts:
    print("-", alert)

print("\nDaily summary:\n")
print(build_daily_summary(profile, daily_log))

