from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json

try:
    instructions = json.load(open("resources/instructions.json", "r", encoding="utf-8"))
except Exception as e:
    instructions = [['❌Ошибка при получении инструкций','null'],['Пожалуйста обратитесь в поддержку','null']]

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 Инструкции", callback_data="instructions")],
        [InlineKeyboardButton("🎮 Вступить в группу GameHub", callback_data="join_group")],
        [InlineKeyboardButton("⭐️ Оставить отзыв", callback_data="reviews")],
        [InlineKeyboardButton("🛠 Техническая поддержка", callback_data="support")],
        [InlineKeyboardButton("🔒 Гарантии", callback_data="warranty")]
    ]
    return InlineKeyboardMarkup(keyboard)

def licence_accept_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Принять и продолжить", callback_data="licence_accepted")]
    ]
    return InlineKeyboardMarkup(keyboard)

def next_licence_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Далее", callback_data="next_licence")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reviews_keyboard():
    keyboard = [
        [InlineKeyboardButton("Wildberries", url="https://www.wildberries.ru/seller/4143228")],
        [InlineKeyboardButton("Яндекс Маркет", url="https://market.yandex.ru/business--gamehub/141327324")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_instructions_keyboard():
    keyboard = [
        [InlineKeyboardButton(i[0], url=i[1])]
        for i in instructions
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_support_keyboard():
    """Клавиатура для раздела поддержки"""
    keyboard = [
        [InlineKeyboardButton("📝 Создать новый тикет", callback_data="create_ticket")],
        [InlineKeyboardButton("📋 Мои тикеты", callback_data="my_tickets")],
        [InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_supp_rating_keyboard():
    """Клавиатура для оценки ответа поддержки"""
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="ticket_rating 1"),
            InlineKeyboardButton("2", callback_data="ticket_rating 2"),
            InlineKeyboardButton("3", callback_data="ticket_rating 3"),
            InlineKeyboardButton("4", callback_data="ticket_rating 4"),
            InlineKeyboardButton("5", callback_data="ticket_rating 5")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_warranty_keyboard():
    """Клавиатура для меню гарантии"""
    keyboard = [
        [InlineKeyboardButton("📝 Отправить отзыв на проверку", callback_data="submit_review")],
        [InlineKeyboardButton("✅ Проверить статус гарантии", callback_data="check_warranty")],
        [InlineKeyboardButton("📄 Условия гарантии", url="https://docs.google.com/document/d/1604j5itbp90y1f8vZTJ1Cj8yvIA3NKcb/edit?usp=sharing&ouid=113569597103807073493&rtpof=true&sd=true")],
        [InlineKeyboardButton("🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    """Клавиатура для отправки отзыва"""
    keyboard = [
        [InlineKeyboardButton("🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard) 