from database import init_db
from models import (
    create_user,
    get_user_by_telegram_id,
    create_or_update_scooter_profile,
    get_scooter_profile,
    create_or_update_daily_log,
    get_daily_log,
)

init_db()

user = get_user_by_telegram_id(123456789)

if not user:
    user_id = create_user(
        telegram_id=123456789,
        name="Yahav",
        phone="0500000000",
        email="test@test.com",
        username="yahav_test",
        password="123456",
    )
    print("User created:", user_id)
    user = get_user_by_telegram_id(123456789)
else:
    print("User already exists:", user["id"])

create_or_update_scooter_profile(
    user_id=user["id"],
    scooter_type="Joyride",
    engine_cc=125,
    model_year=2022,
    purchase_price=18000,
    historical_garage_yearly=2500,
    annual_test=500,
    annual_insurance=3500,
    annual_loans=2400,
    annual_fines=300,
    fuel_km_per_liter=30,
    fuel_price_per_liter=7.5,
    avg_km_per_day=80,
    oil_cost_per_km=0.05,
    depreciation_km_cost_per_km=0.10,
    fuel_price_mode="manual",
    fuel_type="95",
    country_code="IL",
    current_km=24000,
    last_oil_check_km=23600,
    oil_check_interval_km=500,
    last_service_km=21000,
    service_interval_km=3000,
)

profile = get_scooter_profile(user["id"])
print("Scooter profile:", dict(profile))

create_or_update_daily_log(
    user_id=user["id"],
    log_date="2026-03-25",
    hours_worked=8,
    km_done=70,
    income=900,
    status="manual",
)

log = get_daily_log(user["id"], "2026-03-25")
print("Daily log:", dict(log))
