import keyboards
import states
from telegram import Update
from telegram.ext import ContextTypes
from managers import Utility
import logging
import inspect
from database import TicketDb
import os

tickets_db = TicketDb()

logger = logging.getLogger(__name__)

class _support:

    support_thread_id = int(os.getenv('SUPPORT_THREAD_ID'))
    support_group_id = int(os.getenv('SUPPORT_GROUP_ID'))

    async def _open_support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        active_tickets = tickets_db.get_all_tickets(query.from_user.id)
        active_tickets = [t for t in active_tickets if t[8] != 'answered']
        
        if active_tickets:
            message = "📋 Ваши активные тикеты:\n\n"
            for ticket in active_tickets:
                message += (
                    "--------------------\n"
                    f"🆔 Тикет #{ticket[2]}\n"
                    f"📝 Описание: {ticket[3]}\n"
                    f"📱 Телефон: {ticket[7]}\n"
                    f"📅 Дата: {ticket[9]}\n"
                    f"📊 Статус: ⏳ Ожидает ответа\n\n"
                )
            
            message += "Вы можете:\n"
            message += "1. Дождаться ответа на текущие тикеты\n"
            message += "2. Создать новый тикет (предыдущие тикеты будут закрыты)\n"

            await query.message.edit_text(
                message,
                reply_markup=keyboards.support()
            )
        else:
            await query.message.edit_text(
                "🛠 Техническая поддержка\n\n"
                "Выберите действие:",
                reply_markup=keyboards.support()
            )
        return states.WAITING_FOR_ACTION
    
    async def show_user_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает тикеты пользователя"""
        user = update.effective_user
        query = update.callback_query
        
        tickets = tickets_db.get_all_tickets(user.id)
        if not tickets:
            message = "У вас пока нет созданных тикетов."
        else:
            message = "📋 Ваши тикеты:\n\n"
            for ticket in tickets:
                status = "✅ Отвечено" if ticket[8] == 'answered' else "⏳ Ожидает ответа"
                message += (
                    "--------------------\n"
                    f"🆔 Тикет #{ticket[2]}\n"
                    f"📝 Описание: \n{ticket[3]}\n"
                    f"📱 Телефон: {ticket[7]}\n"
                    f"📅 Дата: {ticket[9]}\n"
                    f"📊 Статус: {status}\n"
                )
                
                # Получаем ответы на тикет
                responses = tickets_db.get_ticket_responses(ticket[0])
                if responses:
                    message += "\n💬 Ответы:\n"
                    for i, response in enumerate(responses, 1):
                        message += f"{i}. {response[3]}\n"
                        if response[4]:  # photo_id
                            message += "   📷 Прикреплено фото\n"
                        if response[5]:  # video_id
                            message += "   🎥 Прикреплено видео\n"
                        if response[6]:  # file_id
                            message += "   📎 Прикреплен файл\n"
                
                message += "\n"
        
        if query:
            await query.message.edit_text(message, reply_markup=keyboards.main_menu())
        else:
            await update.message.reply_text(message, reply_markup=keyboards.main_menu())
    
    async def _create_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        active_tickets = tickets_db.get_all_tickets(query.from_user.id)
        active_tickets = [t for t in active_tickets if t[8] != 'answered']
        for ticket in active_tickets:
            tickets_db.update_ticket_status(ticket[0], 'closed')

        await query.message.edit_text(
            "📝 Создание тикета\n\n"
            "Опишите вашу проблему или вопрос. "
            "Пожалуйста, укажите:\n"
            "1. Тип проблемы (техническая, консультация и т.д.)\n"
            "2. Подробное описание\n"
            "3. Номер заказа (если есть)\n"
            "4. Вы так же можете прикрепить фото, видео или документ\n\n"
            "Отправьте всю информацию одним сообщением.",
            reply_markup=keyboards.back_to_main_menu()
        )
        return states.WAITING_FOR_TICKET_DESCRIPTION
    
    async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработчик номера телефона"""
        user = update.effective_user
        phone = update.message.text

        group_id = _support.support_group_id
        thread_id = _support.support_thread_id
        
        # Проверяем валидность номера
        if not await Utility.is_valid_phone(phone):
            await update.message.reply_text(
                "❌ Неверный формат номера телефона.\n\n"
                "📱 Примеры правильных номеров:\n"
                "• 89123456789\n"
                "• 79001234567\n"
                "• 89991234567\n\n"
                "Пожалуйста, введите только цифры (10 или 11 цифр):"
            )
            return states.WAITING_FOR_PHONE
        
        logger.info(f"Добавление телефона для пользователя {user.full_name} ({user.id})")
        
        # Обновляем тикет в базе данных
        ticket = tickets_db.get_latest_ticket(user.id)
        if ticket:
            tickets_db.update_ticket_phone(ticket[0], phone)
            
            message = (
                f"🆕 Новый тикет #{ticket[2]}\n\n"
                f"👤 Пользователь: {user.first_name} (ID: {user.id})\n"
                f"📱 Телефон: {phone}\n"
                f"📅 Дата: {ticket[9]}\n\n"
                f"📝 Описание:\n{ticket[3]}\n\n"
                f"💬 Ответить: <code>/reply {user.id} {ticket[2]} </code>"
            )
            try:
                if ticket[4]:  # photo_id
                    await context.bot.send_photo(
                        chat_id=group_id,
                        message_thread_id=thread_id,
                        photo=ticket[4],
                        caption=message,
                        parse_mode='HTML'
                    )
                elif ticket[5]:  # video_id
                    await context.bot.send_video(
                        chat_id=group_id,
                        message_thread_id=thread_id,
                        video=ticket[5],
                        caption=message,
                        parse_mode='HTML'
                    )
                elif ticket[6]:  # file_id
                    await context.bot.send_document(
                        chat_id=group_id,
                        message_thread_id=thread_id,
                        document=ticket[6],
                        caption=message,
                        parse_mode='HTML'
                    )
                else:
                    await context.bot.send_message(chat_id=group_id, message_thread_id=thread_id, text=message, parse_mode='HTML')
            except Exception as e:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке тикета в группу поддержки: {e}")
                await update.message.reply_text(
                    "❌ Произошла ошибка при создании тикета. Пожалуйста, попробуйте позже.",
                    reply_markup=keyboards.main_menu()
                )
                return states.WAITING_FOR_ACTION
        
        await update.message.reply_text(
            "✅ Спасибо! Ваш тикет создан. Мы свяжемся с вами в ближайшее время.\n\n"
            "Вы можете проверить статус тикета в разделе 'Мои тикеты'.",
            reply_markup=keyboards.main_menu()
        )
        
        return states.WAITING_FOR_ACTION
    
    async def _rate_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        ticket_id = context.user_data.pop('closed_ticket_id', None)
        if not ticket_id:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при получении ID тикета")
            return states.WAITING_FOR_ACTION
        rating = int(query.data.split(' ')[1])
        tickets_db.rate_ticket(ticket_id, rating)
        await query.message.edit_text(
            "✅ Спасибо за вашу оценку!\n\nВыберите действие:",
            reply_markup=keyboards.main_menu()
        )
        return states.WAITING_FOR_ACTION
    
    async def handle_ticket_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        photo = update.message.photo[-1] if update.message.photo else None
        video = update.message.video if update.message.video else None
        document = update.message.document if update.message.document else None
        
        description = update.message.caption if (photo or video or document) else update.message.text
        
        if not description:
            await update.message.reply_text(
                "❌ Пожалуйста, добавьте описание к вашему тикету."
            )
            return states.WAITING_FOR_TICKET_DESCRIPTION
        
        ticket_id = len(tickets_db.get_all_tickets(user.id)) + 1
        tickets_db.add_ticket(
            user_id=user.id,
            ticket_id=ticket_id,
            description=description,
            photo_id=photo.file_id if photo else None,
            video_id=video.file_id if video else None,
            file_id=document.file_id if document else None
        )
        
        await update.message.reply_text(
            "Пожалуйста, укажите ваш номер телефона для связи.\n\n"
            "📱 Примеры правильных номеров:\n"
            "• 89123456789\n"
            "• 79001234567\n"
            "• 89991234567\n\n"
            "❌ Неправильные форматы:\n"
            "• +7 (123) 456-78-90\n"
            "• 8-123-456-78-90\n"
            "• 123456789\n\n"
            "Введите только цифры (10 или 11 цифр):"
        )
        return states.WAITING_FOR_PHONE