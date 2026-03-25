# Delivery System Bot

A smart Telegram bot for scooter delivery riders that calculates **daily profit or loss**, tracks **vehicle expenses**, and sends **maintenance alerts** based on real usage.

This project helps riders understand:

- How much money they **actually made today**
- How much their scooter **really costs per day**
- Whether they are operating at a **profit or a loss**
- When they need to **check oil** or do **maintenance**

---

# Features

## Daily profit / loss tracking
The bot asks the rider to update:

- Hours worked
- Kilometers driven
- Income for the day

Then it calculates:

- Fixed daily costs
- Fuel cost
- Oil cost
- Depreciation by time
- Depreciation by kilometers
- Total daily expenses
- Net profit / loss

---

## Expense model

The system separates expenses into:

### Fixed costs
- Historical garage / repair average
- Annual test
- Annual insurance
- Loans
- Fines
- Time-based depreciation

### Variable costs
- Fuel
- Oil usage
- Kilometer-based depreciation

---

## Maintenance alerts
The bot can warn the rider when it is time to:

- Check oil
- Do scheduled service

Based on:

- Current odometer
- Last oil check KM
- Oil check interval
- Last service KM
- Service interval

---

## Reports
The bot can generate:

- Daily summary
- Weekly report
- Monthly report

---

## AI summary
After each daily update, the system can generate a short AI summary explaining:

- Whether the day was profitable
- What stood out
- What costs were most significant

---

# Tech Stack

- **Python**
- **Telegram Bot API**
- **FastAPI**
- **SQLite**
- **OpenAI API**

---

# Project Structure

```bash
Delivery_system/
├── api.py
├── bot.py
├── config.py
├── database.py
├── models.py
├── services.py
├── ai_service.py
├── requirements.txt
├── .env
├── README.md
└── delivery_system.db
````

---

# Installation

## 1) Clone the project

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd Delivery_system
```

---

## 2) Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3) Install dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=your_model_here
APP_ENV=dev
```

Example:

```env
TELEGRAM_BOT_TOKEN=1234567890:AAExampleTelegramBotToken
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4.1-mini
APP_ENV=dev
```

---

# Run the System

## 1) Start the API

```bash
uvicorn api:app --reload
```

This will start the backend server on:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

---

## 2) Start the Telegram bot

Open a second terminal and run:

```bash
python bot.py
```

---

# First Use

When a new user starts the bot with:

```text
/start
```

The bot will begin the onboarding flow and ask for:

## Account details

* Name
* Phone number
* Email
* Username
* Password

## Scooter setup

* Scooter type
* Engine size (cc)
* Model year
* Purchase price
* Historical yearly garage cost
* Annual test cost
* Annual insurance cost
* Annual loans
* Annual fines
* Fuel economy (km per liter)
* Fuel price per liter
* Average km per day
* Oil cost per km
* Depreciation cost per km
* Current odometer
* Last oil check km
* Oil check interval
* Last service km
* Service interval

After setup is complete, the system becomes active.

---

# Bot Commands

## `/start`

Start the bot and onboarding

## `/update`

Start daily update flow

## `/today`

Show today's summary

## `/week`

Show weekly report

## `/month`

Show monthly report

## `/cancel`

Cancel current flow

---

# Telegram Menu Buttons

The bot also supports menu buttons:

* Daily Update
* Today Report
* Weekly Report
* Monthly Report

---

# How Daily Fuel Cost Is Calculated

Fuel cost is calculated using:

```text
Fuel Cost = (Daily KM / KM per Liter) × Fuel Price per Liter
```

Example:

* Daily KM = 70
* KM per Liter = 30
* Fuel Price = 7.50

```text
(70 / 30) × 7.50 = 17.50
```

---

# How Daily Profit Is Calculated

```text
Profit = Income - Total Daily Expenses
```

Where total daily expenses include:

* Fixed daily costs
* Fuel
* Oil
* Kilometer depreciation

---

# Notes

## This is currently an MVP

The current version is focused on:

* One scooter per user
* Manual fuel price input
* Telegram-first workflow
* Local SQLite storage

---

# Planned Improvements

* Automatic reminders (morning / afternoon / evening / end of day)
* Auto-close day at night if user does not answer
* One-day-back edit support
* Fuel price provider API
* Real user authentication / secure password hashing
* Multi-user deployment
* Paid version / SaaS model
* Admin dashboard
* Better analytics
* Maintenance history log
* Registration via API instead of direct model calls
* Docker deployment

---

# Security Notice

This project is currently an MVP and should **not** be treated as production-ready security architecture.

Before deploying publicly, you should improve:

* Password hashing
* User authentication
* Rate limiting
* API protection
* Secret management
* Database backup strategy

---

# License

MIT License

---

# Why This Exists

Most delivery riders only track **income**.

Very few track:

* hidden vehicle costs
* long-term wear
* maintenance timing
* real profit after expenses

This system exists to answer one question clearly:

# “Did I actually make money today?”


