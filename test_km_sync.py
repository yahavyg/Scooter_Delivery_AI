from database import init_db
from models import (
    get_user_by_telegram_id,
    get_scooter_profile,
    create_or_update_daily_log_with_km_sync,
)

init_db()

user = get_user_by_telegram_id(123456789)

print("לפני:")
profile_before = get_scooter_profile(user["id"])
print("current_km =", profile_before["current_km"])

# יום חדש
create_or_update_daily_log_with_km_sync(
    user_id=user["id"],
    log_date="2026-03-26",
    hours_worked=7,
    km_done=50,
    income=700,
    status="manual",
)

print("\nאחרי הוספת יום:")
profile_after = get_scooter_profile(user["id"])
print("current_km =", profile_after["current_km"])

# עדכון אותו יום - משנה 50 ל-80
create_or_update_daily_log_with_km_sync(
    user_id=user["id"],
    log_date="2026-03-26",
    hours_worked=7,
    km_done=80,
    income=700,
    status="edited",
)

print("\nאחרי עדכון אותו יום:")
profile_after_edit = get_scooter_profile(user["id"])
print("current_km =", profile_after_edit["current_km"])
