from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json
import os

warranty_conditions_link = os.getenv('WARRANTY_CONDITIONS_URL')

try:
    instructions_data = json.load(open("resources/instructions.json", "r", encoding="utf-8"))
except Exception as e:
    instructions_data = [['❌Ошибка при получении инструкций','null'],['Пожалуйста обратитесь в поддержку','null']]

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📖 Инструкции", callback_data="instructions")],
        [InlineKeyboardButton("🎮 Вступить в группу GameHub", callback_data="join_group")],
        [InlineKeyboardButton("⭐️ Оставить отзыв", callback_data="reviews")],
        [InlineKeyboardButton("🛠 Техническая поддержка", callback_data="support")],
        [InlineKeyboardButton("🔒 Гарантии", callback_data="warranty")]
    ]
    return InlineKeyboardMarkup(keyboard)

def licence_accept():
    keyboard = [
        [InlineKeyboardButton("✅ Принять и продолжить", callback_data="licence_accepted")]
    ]
    return InlineKeyboardMarkup(keyboard)

def next_licence():
    keyboard = [
        [InlineKeyboardButton("✅ Далее", callback_data="next_licence")]
    ]
    return InlineKeyboardMarkup(keyboard)

def reviews():
    keyboard = [
        [InlineKeyboardButton("Wildberries", url="https://www.wildberries.ru/seller/4143228")],
        [InlineKeyboardButton("Яндекс Маркет", url="https://market.yandex.ru/business--gamehub/141327324")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def instructions():
    keyboard = [
        [InlineKeyboardButton(i[0], url=i[1])]
        for i in instructions_data
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def support():
    """Клавиатура для раздела поддержки"""
    keyboard = [
        [InlineKeyboardButton("📝 Создать новый тикет", callback_data="create_ticket")],
        [InlineKeyboardButton("📋 Мои тикеты", callback_data="my_tickets")],
        [InlineKeyboardButton("🔙 Вернуться в меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def supp_rating():
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

def warranty():
    """Клавиатура для меню гарантии"""
    keyboard = [
        [InlineKeyboardButton("✅ Проверить статус гарантии", callback_data="check_warranty")],
        [InlineKeyboardButton("📄 Условия гарантии", url=warranty_conditions_link)],
        [InlineKeyboardButton("🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main_menu():
    keyboard = [
        [InlineKeyboardButton("🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard) 