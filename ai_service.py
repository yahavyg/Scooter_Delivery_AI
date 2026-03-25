from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL


client = OpenAI(api_key=OPENAI_API_KEY)


def build_ai_summary_input(daily_log, calculation_result) -> str:
    return f"""
תסכם את היום בעברית פשוטה, קצרה וברורה.
עד 3 משפטים.
בלי נקודות מיותרות.
תסביר אם היום היה רווחי או הפסדי ומה הכי בלט.

נתונים:
שעות עבודה: {daily_log["hours_worked"]}
ק"מ: {daily_log["km_done"]}
הכנסה: {daily_log["income"]:.2f}
הוצאות קבועות: {calculation_result["fixed_daily"]:.2f}
הוצאות משתנות: {calculation_result["variable_daily"]:.2f}
סה"כ הוצאות: {calculation_result["total_daily"]:.2f}
רווח/הפסד: {calculation_result["profit"]:.2f}
"""


def get_ai_daily_summary(daily_log, calculation_result) -> str:
    prompt = build_ai_summary_input(daily_log, calculation_result)

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt,
    )

    return response.output_text.strip()
