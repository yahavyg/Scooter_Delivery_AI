from datetime import datetime


def days_in_year(year: int) -> int:
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        return 366
    return 365


def annual_depreciation_by_time(purchase_price: float, model_year: int, current_year: int) -> float:
    """
    חישוב פשוט:
    שנה ראשונה 20%
    כל שנה נוספת 10%
    """
    age = max(0, current_year - model_year)

    if age == 0:
        return purchase_price * 0.20

    current_value = purchase_price
    current_value -= purchase_price * 0.20

    for _ in range(age):
        current_value -= current_value * 0.10

    total_depreciation = purchase_price - max(current_value, 0)
    return max(total_depreciation, 0)


def calculate_daily_costs(profile, daily_log):
    log_date = datetime.fromisoformat(daily_log["log_date"]).date()
    year_days = days_in_year(log_date.year)

    annual_fixed_without_dep = (
        profile["historical_garage_yearly"]
        + profile["annual_test"]
        + profile["annual_insurance"]
        + profile["annual_loans"]
        + profile["annual_fines"]
    )

    depreciation_time_annual = annual_depreciation_by_time(
        purchase_price=profile["purchase_price"],
        model_year=profile["model_year"],
        current_year=log_date.year,
    )

    fixed_daily = (annual_fixed_without_dep + depreciation_time_annual) / year_days

    km_done = daily_log["km_done"]

    fuel_cost = 0
    if profile["fuel_km_per_liter"] > 0:
        fuel_cost = (km_done / profile["fuel_km_per_liter"]) * profile["fuel_price_per_liter"]

    oil_cost = km_done * profile["oil_cost_per_km"]
    depreciation_km_cost = km_done * profile["depreciation_km_cost_per_km"]

    variable_daily = fuel_cost + oil_cost + depreciation_km_cost
    total_daily = fixed_daily + variable_daily
    profit = daily_log["income"] - total_daily

    return {
        "fixed_daily": fixed_daily,
        "depreciation_time_daily": depreciation_time_annual / year_days,
        "fuel_cost": fuel_cost,
        "oil_cost": oil_cost,
        "depreciation_km_cost": depreciation_km_cost,
        "variable_daily": variable_daily,
        "total_daily": total_daily,
        "profit": profit,
    }


def check_maintenance_alerts(profile):
    alerts = []

    current_km = profile["current_km"]

    # שמן
    oil_km_since_check = current_km - profile["last_oil_check_km"]
    oil_interval = profile["oil_check_interval_km"]

    if oil_interval > 0:
        oil_remaining = oil_interval - oil_km_since_check

        if oil_remaining <= 0:
            alerts.append(
                f"🛢 צריך לבדוק שמן עכשיו. עברו {oil_km_since_check:.0f} ק\"מ מאז הבדיקה האחרונה."
            )
        elif oil_remaining <= 100:
            alerts.append(
                f"🛢 בדיקת שמן מתקרבת. נשארו בערך {oil_remaining:.0f} ק\"מ."
            )

    # טיפול
    service_km_since = current_km - profile["last_service_km"]
    service_interval = profile["service_interval_km"]

    if service_interval > 0:
        service_remaining = service_interval - service_km_since

        if service_remaining <= 0:
            alerts.append(
                f"🔧 צריך טיפול עכשיו. עברו {service_km_since:.0f} ק\"מ מאז הטיפול האחרון."
            )
        elif service_remaining <= 300:
            alerts.append(
                f"🔧 טיפול מתקרב. נשארו בערך {service_remaining:.0f} ק\"מ."
            )

    return alerts


def build_daily_summary(profile, daily_log):
    result = calculate_daily_costs(profile, daily_log)
    alerts = check_maintenance_alerts(profile)

    profit_emoji = "🟢" if result["profit"] >= 0 else "🔴"

    summary = (
        f"📅 סיכום ליום {daily_log['log_date']}\n\n"
        f"⏱ שעות עבודה: {daily_log['hours_worked']}\n"
        f"🛵 ק\"מ: {daily_log['km_done']}\n"
        f"💰 הכנסה: ₪{daily_log['income']:.2f}\n\n"
        f"📌 הוצאות קבועות יומיות: ₪{result['fixed_daily']:.2f}\n"
        f"   └ ירידת ערך לפי זמן: ₪{result['depreciation_time_daily']:.2f}\n\n"
        f"📌 הוצאות משתנות: ₪{result['variable_daily']:.2f}\n"
        f"   ├ דלק: ₪{result['fuel_cost']:.2f}\n"
        f"   ├ שמן: ₪{result['oil_cost']:.2f}\n"
        f"   └ ירידת ערך לפי ק\"מ: ₪{result['depreciation_km_cost']:.2f}\n\n"
        f"🧾 סה\"כ הוצאות: ₪{result['total_daily']:.2f}\n"
        f"{profit_emoji} רווח / הפסד: ₪{result['profit']:.2f}"
    )

    if alerts:
        summary += "\n\n⚠️ התראות תחזוקה:\n" + "\n".join(alerts)

    return summary


def build_period_report(profile, logs, title="דוח תקופתי"):
    total_income = 0
    total_expenses = 0
    worked_days = 0
    no_work_days = 0
    auto_closed_days = 0

    for log in logs:
        result = calculate_daily_costs(profile, log)
        total_income += log["income"]
        total_expenses += result["total_daily"]

        if log["hours_worked"] > 0 or log["km_done"] > 0 or log["income"] > 0:
            worked_days += 1
        else:
            no_work_days += 1

        if log["status"] == "auto_closed":
            auto_closed_days += 1

    days_count = len(logs) if logs else 1
    total_profit = total_income - total_expenses
    avg_expenses = total_expenses / days_count
    avg_profit = total_profit / days_count

    emoji = "🟢" if total_profit >= 0 else "🔴"

    report = (
        f"📊 {title}\n\n"
        f"💰 הכנסות: ₪{total_income:.2f}\n"
        f"🧾 הוצאות: ₪{total_expenses:.2f}\n"
        f"{emoji} רווח / הפסד: ₪{total_profit:.2f}\n\n"
        f"📉 ממוצע הוצאות יומי: ₪{avg_expenses:.2f}\n"
        f"📈 ממוצע רווח יומי: ₪{avg_profit:.2f}\n\n"
        f"🗓 ימי עבודה: {worked_days}\n"
        f"🛑 ימים בלי עבודה: {no_work_days}\n"
        f"🤖 ימים שנסגרו אוטומטית: {auto_closed_days}"
    )

    alerts = check_maintenance_alerts(profile)
    if alerts:
        report += "\n\n⚠️ התראות תחזוקה:\n" + "\n".join(alerts)

    return report
