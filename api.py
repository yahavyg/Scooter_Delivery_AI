from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import init_db
from models import (
    get_user_by_telegram_id,
    get_scooter_profile,
    get_daily_log,
    get_daily_logs_between,
    get_daily_events,
    get_daily_events_between,
    sum_daily_events_by_type,
    create_daily_event,
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


class EventCreateRequest(BaseModel):
    telegram_id: int
    event_date: str
    event_type: str
    amount: float
    liters: float = 0
    notes: str = ""


# =========================
# Helpers
# =========================
ALLOWED_EVENT_TYPES = {
    "income",
    "tip",
    "fuel",
    "service",
    "repair",
    "fine",
    "food",
}


def group_events_by_date(events):
    grouped = {}

    for event in events:
        event_date = event["event_date"]
        event_type = event["event_type"]
        amount = float(event["amount"] or 0)

        if event_date not in grouped:
            grouped[event_date] = {
                "income": 0.0,
                "tip": 0.0,
                "fuel": 0.0,
                "service": 0.0,
                "repair": 0.0,
                "fine": 0.0,
                "food": 0.0,
            }

        if event_type in grouped[event_date]:
            grouped[event_date][event_type] += amount

    return grouped


# =========================
# Routes
# =========================
@app.get("/")
def root():
    return {"message": "Delivery System API is running"}


# =========================
# Daily update
# =========================
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
    event_totals = sum_daily_events_by_type(user["id"], payload.log_date)

    calculation_result = calculate_daily_costs(updated_profile, daily_log, event_totals)
    maintenance_alerts = check_maintenance_alerts(updated_profile)
    summary = build_daily_summary(updated_profile, daily_log, event_totals)

    try:
        ai_summary = get_ai_daily_summary(daily_log, calculation_result)
    except Exception as e:
        ai_summary = f"AI summary failed: {str(e)}"

    return {
        "date": payload.log_date,
        "current_km": updated_profile["current_km"],
        "events": event_totals,
        "calculation": calculation_result,
        "maintenance_alerts": maintenance_alerts,
        "summary": summary,
        "ai_summary": ai_summary,
    }


# =========================
# Create event
# =========================
@app.post("/event")
def create_event(payload: EventCreateRequest):
    user = get_user_by_telegram_id(payload.telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = get_scooter_profile(user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Scooter profile not found")

    if payload.event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid event_type")

    if payload.amount < 0:
        raise HTTPException(status_code=400, detail="Amount cannot be negative")

    if payload.liters < 0:
        raise HTTPException(status_code=400, detail="Liters cannot be negative")

    event_id = create_daily_event(
        user_id=user["id"],
        event_date=payload.event_date,
        event_type=payload.event_type,
        amount=payload.amount,
        liters=payload.liters,
        km_at_event=float(profile["current_km"] or 0),
        notes=payload.notes or "",
    )

    updated_profile = get_scooter_profile(user["id"])
    event_totals = sum_daily_events_by_type(user["id"], payload.event_date)
    daily_log = get_daily_log(user["id"], payload.event_date)

    summary = None
    calculation = None
    maintenance_alerts = check_maintenance_alerts(updated_profile)

    if daily_log:
        calculation = calculate_daily_costs(updated_profile, daily_log, event_totals)
        summary = build_daily_summary(updated_profile, daily_log, event_totals)

    return {
        "message": "Event saved successfully",
        "event_id": event_id,
        "event_type": payload.event_type,
        "date": payload.event_date,
        "current_km": updated_profile["current_km"],
        "events": event_totals,
        "calculation": calculation,
        "summary": summary,
        "maintenance_alerts": maintenance_alerts,
    }


# =========================
# Daily events list
# =========================
@app.get("/events/{telegram_id}")
def daily_events(telegram_id: int, event_date: str):
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    events = get_daily_events(user["id"], event_date)
    totals = sum_daily_events_by_type(user["id"], event_date)

    return {
        "date": event_date,
        "totals": totals,
        "events": [dict(row) for row in events]
    }


# =========================
# Daily summary
# =========================
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

    event_totals = sum_daily_events_by_type(user["id"], log_date)
    summary = build_daily_summary(profile, daily_log, event_totals)
    calculation = calculate_daily_costs(profile, daily_log, event_totals)

    return {
        "date": log_date,
        "events": event_totals,
        "calculation": calculation,
        "summary": summary
    }


# =========================
# Weekly report
# =========================
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

    events = get_daily_events_between(
        user["id"],
        start_date.isoformat(),
        end_date.isoformat()
    )

    events_by_date = group_events_by_date(events)

    report = build_period_report(
        profile,
        logs,
        events_by_date=events_by_date,
        title=f"סיכום שבועי {start_date} עד {end_date}"
    )

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "report": report
    }


# =========================
# Monthly report
# =========================
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

    events = get_daily_events_between(
        user["id"],
        start_date.isoformat(),
        end_date.isoformat()
    )

    events_by_date = group_events_by_date(events)

    report = build_period_report(
        profile,
        logs,
        events_by_date=events_by_date,
        title=f"סיכום חודשי {start_date} עד {end_date}"
    )

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "report": report
    }


# =========================
# AI summary
# =========================
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

    event_totals = sum_daily_events_by_type(user["id"], log_date)
    calculation_result = calculate_daily_costs(profile, daily_log, event_totals)

    try:
        ai_summary_text = get_ai_daily_summary(daily_log, calculation_result)
    except Exception as e:
        ai_summary_text = f"AI summary failed: {str(e)}"

    return {
        "date": log_date,
        "events": event_totals,
        "ai_summary": ai_summary_text
    }
