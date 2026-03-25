from datetime import datetime
from database import get_connection


def now_str():
    return datetime.now().isoformat()


# =========================
# Users
# =========================
def create_user(telegram_id, name, phone, email, username, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (
            telegram_id, name, phone, email, username, password, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        telegram_id,
        name,
        phone,
        email,
        username,
        password,
        now_str(),
    ))

    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id


def get_user_by_telegram_id(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()

    conn.close()
    return row


def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()

    conn.close()
    return row


# =========================
# Scooter Profile
# =========================
def create_or_update_scooter_profile(
    user_id,
    scooter_type,
    engine_cc,
    model_year,
    purchase_price,
    historical_garage_yearly,
    annual_test,
    annual_insurance,
    annual_loans,
    annual_fines,
    fuel_km_per_liter,
    fuel_price_per_liter,
    avg_km_per_day,
    oil_cost_per_km,
    depreciation_km_cost_per_km,
    fuel_price_mode="manual",
    fuel_type="95",
    country_code="IL",
    current_km=0,
    last_oil_check_km=0,
    oil_check_interval_km=500,
    last_service_km=0,
    service_interval_km=3000,
):
    conn = get_connection()
    cur = conn.cursor()

    current_time = now_str()

    cur.execute("""
        INSERT INTO scooter_profiles (
            user_id,
            scooter_type,
            engine_cc,
            model_year,
            purchase_price,
            historical_garage_yearly,
            annual_test,
            annual_insurance,
            annual_loans,
            annual_fines,
            fuel_km_per_liter,
            fuel_price_per_liter,
            fuel_price_mode,
            fuel_type,
            country_code,
            avg_km_per_day,
            oil_cost_per_km,
            depreciation_km_cost_per_km,
            current_km,
            last_oil_check_km,
            oil_check_interval_km,
            last_service_km,
            service_interval_km,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            scooter_type = excluded.scooter_type,
            engine_cc = excluded.engine_cc,
            model_year = excluded.model_year,
            purchase_price = excluded.purchase_price,
            historical_garage_yearly = excluded.historical_garage_yearly,
            annual_test = excluded.annual_test,
            annual_insurance = excluded.annual_insurance,
            annual_loans = excluded.annual_loans,
            annual_fines = excluded.annual_fines,
            fuel_km_per_liter = excluded.fuel_km_per_liter,
            fuel_price_per_liter = excluded.fuel_price_per_liter,
            fuel_price_mode = excluded.fuel_price_mode,
            fuel_type = excluded.fuel_type,
            country_code = excluded.country_code,
            avg_km_per_day = excluded.avg_km_per_day,
            oil_cost_per_km = excluded.oil_cost_per_km,
            depreciation_km_cost_per_km = excluded.depreciation_km_cost_per_km,
            current_km = excluded.current_km,
            last_oil_check_km = excluded.last_oil_check_km,
            oil_check_interval_km = excluded.oil_check_interval_km,
            last_service_km = excluded.last_service_km,
            service_interval_km = excluded.service_interval_km,
            updated_at = excluded.updated_at
    """, (
        user_id,
        scooter_type,
        engine_cc,
        model_year,
        purchase_price,
        historical_garage_yearly,
        annual_test,
        annual_insurance,
        annual_loans,
        annual_fines,
        fuel_km_per_liter,
        fuel_price_per_liter,
        fuel_price_mode,
        fuel_type,
        country_code,
        avg_km_per_day,
        oil_cost_per_km,
        depreciation_km_cost_per_km,
        current_km,
        last_oil_check_km,
        oil_check_interval_km,
        last_service_km,
        service_interval_km,
        current_time,
        current_time,
    ))

    conn.commit()
    conn.close()


def get_scooter_profile(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM scooter_profiles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row


def update_current_km(user_id, new_current_km):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE scooter_profiles
        SET current_km = ?, updated_at = ?
        WHERE user_id = ?
    """, (new_current_km, now_str(), user_id))

    conn.commit()
    conn.close()


def mark_oil_checked(user_id, current_km):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE scooter_profiles
        SET last_oil_check_km = ?, updated_at = ?
        WHERE user_id = ?
    """, (current_km, now_str(), user_id))

    conn.commit()
    conn.close()


def mark_service_done(user_id, current_km):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE scooter_profiles
        SET last_service_km = ?, updated_at = ?
        WHERE user_id = ?
    """, (current_km, now_str(), user_id))

    conn.commit()
    conn.close()


# =========================
# Daily Logs
# =========================
def create_or_update_daily_log(user_id, log_date, hours_worked, km_done, income, status):
    conn = get_connection()
    cur = conn.cursor()

    current_time = now_str()

    cur.execute("""
        INSERT INTO daily_logs (
            user_id,
            log_date,
            hours_worked,
            km_done,
            income,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, log_date) DO UPDATE SET
            hours_worked = excluded.hours_worked,
            km_done = excluded.km_done,
            income = excluded.income,
            status = excluded.status,
            updated_at = excluded.updated_at
    """, (
        user_id,
        log_date,
        hours_worked,
        km_done,
        income,
        status,
        current_time,
        current_time,
    ))

    conn.commit()
    conn.close()


def get_daily_log(user_id, log_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM daily_logs
        WHERE user_id = ? AND log_date = ?
    """, (user_id, log_date))

    row = cur.fetchone()
    conn.close()
    return row


def get_daily_logs_between(user_id, start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM daily_logs
        WHERE user_id = ?
          AND log_date >= ?
          AND log_date <= ?
        ORDER BY log_date ASC
    """, (user_id, start_date, end_date))

    rows = cur.fetchall()
    conn.close()
    return rows
def create_or_update_daily_log_with_km_sync(user_id, log_date, hours_worked, km_done, income, status):
    """
    שומר לוג יומי ומסנכרן current_km בצורה חכמה:
    - אם זה יום חדש: מוסיף km_done ל-current_km
    - אם זה עדכון ליום קיים: מוסיף/מוריד רק את ההפרש
    """

    conn = get_connection()
    cur = conn.cursor()

    current_time = now_str()

    # לוג קיים?
    cur.execute("""
        SELECT * FROM daily_logs
        WHERE user_id = ? AND log_date = ?
    """, (user_id, log_date))
    existing_log = cur.fetchone()

    # פרופיל קיים
    cur.execute("""
        SELECT * FROM scooter_profiles
        WHERE user_id = ?
    """, (user_id,))
    profile = cur.fetchone()

    if not profile:
        conn.close()
        raise ValueError("Scooter profile not found")

    current_km = profile["current_km"]

    if existing_log:
        old_km = existing_log["km_done"]
        km_diff = km_done - old_km
    else:
        km_diff = km_done

    new_current_km = current_km + km_diff
    if new_current_km < 0:
        new_current_km = 0

    # שמירת הלוג
    cur.execute("""
        INSERT INTO daily_logs (
            user_id,
            log_date,
            hours_worked,
            km_done,
            income,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, log_date) DO UPDATE SET
            hours_worked = excluded.hours_worked,
            km_done = excluded.km_done,
            income = excluded.income,
            status = excluded.status,
            updated_at = excluded.updated_at
    """, (
        user_id,
        log_date,
        hours_worked,
        km_done,
        income,
        status,
        current_time,
        current_time,
    ))

    # עדכון current_km
    cur.execute("""
        UPDATE scooter_profiles
        SET current_km = ?, updated_at = ?
        WHERE user_id = ?
    """, (new_current_km, current_time, user_id))

    conn.commit()
    conn.close()
