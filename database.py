import sqlite3
from pathlib import Path

DB_PATH = Path("delivery_system.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # =========================
    # users
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # =========================
    # scooter_profiles
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scooter_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        scooter_type TEXT NOT NULL,
        engine_cc INTEGER NOT NULL,
        model_year INTEGER NOT NULL,
        purchase_price REAL NOT NULL,

        historical_garage_yearly REAL NOT NULL,
        annual_test REAL NOT NULL,
        annual_insurance REAL NOT NULL,
        annual_loans REAL NOT NULL,
        annual_fines REAL NOT NULL,

        fuel_km_per_liter REAL NOT NULL,
        fuel_price_per_liter REAL NOT NULL,
        fuel_price_mode TEXT NOT NULL DEFAULT 'manual',
        fuel_type TEXT NOT NULL DEFAULT '95',
        country_code TEXT NOT NULL DEFAULT 'IL',

        avg_km_per_day REAL NOT NULL,
        oil_cost_per_km REAL NOT NULL,
        depreciation_km_cost_per_km REAL NOT NULL,

        current_km REAL NOT NULL DEFAULT 0,
        last_oil_check_km REAL NOT NULL DEFAULT 0,
        oil_check_interval_km REAL NOT NULL DEFAULT 500,
        last_service_km REAL NOT NULL DEFAULT 0,
        service_interval_km REAL NOT NULL DEFAULT 3000,

        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # =========================
    # daily_logs
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        log_date TEXT NOT NULL,
        hours_worked REAL NOT NULL DEFAULT 0,
        km_done REAL NOT NULL DEFAULT 0,
        income REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, log_date),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # =========================
    # daily_events
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_date TEXT NOT NULL,
        event_type TEXT NOT NULL,
        amount REAL NOT NULL DEFAULT 0,
        liters REAL NOT NULL DEFAULT 0,
        km_at_event REAL NOT NULL DEFAULT 0,
        notes TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # =========================
    # indexes
    # =========================
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date
    ON daily_logs(user_id, log_date)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_events_user_date
    ON daily_events(user_id, event_date)
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_daily_events_type
    ON daily_events(event_type)
    """)

    conn.commit()
    conn.close()
