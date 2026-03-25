from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import init_db
from models import (
    get_user_by_telegram_id,
    get_scooter_profile,
    get_daily_log,
    get_daily_logs_between,
    create_or_update_daily_log_with_km_sync,
)
from services import (
    build_daily_summary,
    build_period_report,
    calculate_daily_costs,
    check_maintenance_alerts,
)
from ai_service import get_ai_daily_summary
from datetime import date, timedelta

app = FastAPI(title="Delivery System API")

init_db()


# =========================
# Schemas
# =========================
class DailyUpdateRequest(BaseModel):
    telegram_id: int
    log_date: str
    hours_worked: float
    km_done: float
    income: float
    status: str = "manual"


# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {"message": "Delivery System API is running"}


@app.post("/daily-update")
def daily_update(payload: DailyUpdateRequest):
    user = get_user_by_telegram_id(payload.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_scooter_profile(user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Scooter profile not found")

    create_or_update_daily_log_with_km_sync(
        user_id=user["id"],
        log_date=payload.log_date,
        hours_worked=payload.hours_worked,
        km_done=payload.km_done,
        income=payload.income,
        status=payload.status,
    )

    updated_profile = get_scooter_profile(user["id"])
    daily_log = get_daily_log(user["id"], payload.log_date)

    calculation_result = calculate_daily_costs(updated_profile, daily_log)
    maintenance_alerts = check_maintenance_alerts(updated_profile)
    summary = build_daily_summary(updated_profile, daily_log)

    try:
        ai_summary = get_ai_daily_summary(daily_log, calculation_result)
    except Exception as e:
        ai_summary = f"AI summary failed: {str(e)}"

    return {
        "date": payload.log_date,
        "current_km": updated_profile["current_km"],
        "calculation": calculation_result,
        "maintenance_alerts": maintenance_alerts,
        "summary": summary,
        "ai_summary": ai_summary,
    }


@app.get("/daily-summary/{telegram_id}")
def daily_summary(telegram_id: int, log_date: str):
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_scooter_profile(user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Scooter profile not found")

    daily_log = get_daily_log(user["id"], log_date)
    if not daily_log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    summary = build_daily_summary(profile, daily_log)

    return {
        "date": log_date,
        "summary": summary
    }


@app.get("/weekly-report/{telegram_id}")
def weekly_report(telegram_id: int):
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_scooter_profile(user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Scooter profile not found")

    end_date = date.today()
    start_date = end_date - timedelta(days=6)

    logs = get_daily_logs_between(
        user["id"],
        start_date.isoformat(),
        end_date.isoformat()
    )

    report = build_period_report(profile, logs, title=f"סיכום שבועי {start_date} עד {end_date}")

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "report": report
    }


@app.get("/monthly-report/{telegram_id}")
def monthly_report(telegram_id: int):
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_scooter_profile(user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Scooter profile not found")

    end_date = date.today()
    start_date = end_date.replace(day=1)

    logs = get_daily_logs_between(
        user["id"],
        start_date.isoformat(),
        end_date.isoformat()
    )

    report = build_period_report(profile, logs, title=f"סיכום חודשי {start_date} עד {end_date}")

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "report": report
    }


@app.get("/ai-summary/{telegram_id}")
def ai_summary(telegram_id: int, log_date: str):
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_scooter_profile(user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Scooter profile not found")

    daily_log = get_daily_log(user["id"], log_date)
    if not daily_log:
        raise HTTPException(status_code=404, detail="Daily log not found")

    calculation_result = calculate_daily_costs(profile, daily_log)
    ai_summary_text = get_ai_daily_summary(daily_log, calculation_result)

    return {
        "date": log_date,
        "ai_summary": ai_summary_text
    }
