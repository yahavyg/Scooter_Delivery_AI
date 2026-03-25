from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["עדכון יומי", "קיבלתי הכנסה"],
            ["קיבלתי טיפ", "מילאתי דלק"],
            ["עשיתי טיפול", "היה תיקון"],
            ["קיבלתי דוח", "קניתי אוכל/שתייה"],
            ["דוח היום", "דוח שבועי"],
            ["דוח חודשי"],
        ],
        resize_keyboard=True
    )


def remove_keyboard():
    return ReplyKeyboardRemove()
