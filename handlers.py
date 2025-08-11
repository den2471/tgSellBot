import os
import logging
import re
import cv2
import easyocr
import string
import numpy as np
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
import states
import keyboards
import inspect
from database import (
    TicketDb,
    WarrantyDb
)
from enum import Enum
from media_handler import media_manager

logger = logging.getLogger(__name__)
tickets_db = TicketDb()
warranty_db = WarrantyDb()

class CallbackData(Enum):
    NEXT_LICENCE = "next_licence"
    LICENCE_ACCEPTED = "licence_accepted"

class ContextData(Enum):
    LICENCE_INDEX = "licence_index"

licence_error_cap = 'Не получилось отправить пользовательское соглашение, перезапустите бота немного позже ↩️ либо ознакомьтесь с соглашением в соответствующем разделе'
internal_error_cap = '🛑 Произошла внутрення ошибка, пожалуйста перезапустите бота командой /start'

def is_valid_phone(phone):
    """Проверка валидности номера телефона"""
    phone = re.sub(r'\D', '', phone)
    return len(phone) in [10, 11]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ботом"""
    user = update.effective_user
    logger.info(f"Получена команда /start от пользователя {user.full_name} ({user.id})")
    context.user_data[ContextData.LICENCE_INDEX.value] = 1
    licence_photo, quantity = media_manager.get_licence_by_index(context.user_data[ContextData.LICENCE_INDEX.value])
    if not licence_photo:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno} - Файлы лицензионного соглашения не найдены")
            await context.bot.send_message(
                chat_id=context._chat_id, 
                text=licence_error_cap)
            await send_advert(update, context)
            return states.WAITING_FOR_ACTION
    else:
        logger.info(f"{quantity} лицензионных файлов ранее загружено")
        await update.message.reply_photo(
                photo=licence_photo,
                caption=f'{context.user_data[ContextData.LICENCE_INDEX.value]} из {quantity}',
                reply_markup=keyboards.next_licence_keyboard()
            )
        return states.WAITING_FOR_LICENCE_ACCEPT

async def licence_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        query = update.callback_query
        await query.answer()
        if query.data == CallbackData.NEXT_LICENCE.value:
            context.user_data[ContextData.LICENCE_INDEX.value] += 1
            licence_photo, quantity = media_manager.get_licence_by_index(context.user_data[ContextData.LICENCE_INDEX.value])
            if context.user_data[ContextData.LICENCE_INDEX.value] < quantity:
                markup = keyboards.next_licence_keyboard()
            elif context.user_data[ContextData.LICENCE_INDEX.value] == quantity:
                markup = keyboards.licence_accept_keyboard()
            else:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\Ошибка индекса лицензионного файла")
                context.bot.send_message(internal_error_cap)
                return states.WAITING_FOR_LICENCE_ACCEPT
            await query.message.reply_photo(
                photo=licence_photo,
                caption=f"{context.user_data[ContextData.LICENCE_INDEX.value]} из {quantity}",
                reply_markup=markup,
            )
            return states.WAITING_FOR_LICENCE_ACCEPT
        elif query.data == CallbackData.LICENCE_ACCEPTED.value:
            logger.info(f"Пользователь {user.full_name} ({user.id}) принял соглашение")
            await send_advert(update, context)
            return states.WAITING_FOR_ACTION
        else:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\Получен не верный CallBack от сервера")
            context.bot.send_message(internal_error_cap)
    except Exception as ex:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\Ошибка при отправке файла соглашения {ex}, пропуск шага")
        context.bot.send_message(licence_error_cap)

async def send_advert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cap = "🎮 Присоединяйтесь к нашему игровому комьюнити 🎮!\n\n" \
                        "Здесь вас ждет:\n" \
                        "✅ Эксклюзивные акции — розыгрыши игр, скидки и подарки только для участников.\n" \
                        "✅ Быстрая поддержка — ответы на вопросы в чате по техническим проблемам.\n" \
                        "✅ Полезные материалы — гайды, Инструкции.\n" \
                        "Стань частью сообщества — делитесь опытом, находите друзей и получайте крутые бонусы!"
    ad_media, extention = media_manager.get_random_ad()
    if ad_media:
        if extention == "pic":
            await context.bot.send_photo(
                chat_id=context._chat_id,
                photo=ad_media
            )
            await context.bot.send_message(
                chat_id=context._chat_id,
                text=cap,
                reply_markup=keyboards.get_main_menu_keyboard()
            )
        elif extention == 'vid':
            await context.bot.send_video(
                chat_id=context._chat_id,
                video=ad_media
            )
            await context.bot.send_message(
                chat_id=context._chat_id,
                text=cap,
                reply_markup=keyboards.get_main_menu_keyboard()
            )
        else:
            await context.bot.send_video(
                chat_id=context._chat_id,
                video=ad_media
            )
            await context.bot.send_message(
                chat_id=context._chat_id,
                text=cap,
                reply_markup=keyboards.get_main_menu_keyboard()
            )  
    else:
        logger.error("Не найдены рекламные файлы, пропуск")
        await context.bot.send_message(
            chat_id=context._chat_id,
            text=cap,
            reply_markup=keyboards.get_main_menu_keyboard()
        )

async def advert_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "advert_accepted":
        return states.WAITING_FOR_ACTION

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "instructions":
        await query.message.edit_text(
            "📖 Выберите инструкцию:",
            reply_markup=keyboards.get_instructions_keyboard()
        )
        return states.WAITING_FOR_ACTION
    
    elif query.data == "join_group":
        group_id = os.getenv('USER_GROUP_ID')
        user_group_global_link = os.getenv('USER_GROUP_GLOBAL_LINK')
        user_id = query.from_user.id
        
        # Проверяем, не было ли уже отправлено сообщение о вступлении
        if query.message.text and "Вы уже являетесь участником" in query.message.text:
            await query.answer("Вы уже в группе! 🎮")
            return states.WAITING_FOR_ACTION
            
        if query.message.text and "Вы успешно добавлены" in query.message.text:
            await query.answer("Вы уже добавлены в группу! 🎮")
            return states.WAITING_FOR_ACTION
            
        if query.message.text and "Присоединяйтесь к нашей группе" in query.message.text:
            await query.answer("Пожалуйста, используйте предоставленную ссылку для вступления")
            return states.WAITING_FOR_ACTION
            
        try:
            # Проверяем, является ли пользователь участником группы
            chat_member = await context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            
            if chat_member.status in ['member', 'administrator', 'creator']:
                # Если пользователь уже в группе, просто отправляем сообщение
                await query.message.edit_text(
                    "✅ Вы уже являетесь участником нашей группы!\n\n"
                    "🔗 Ссылка на группу: "+user_group_global_link+"\n\n"
                    "Рады видеть вас в нашем сообществе! 🎮",
                    reply_markup=keyboards.get_main_menu_keyboard()
                )
                return states.WAITING_FOR_ACTION
            
            # Если пользователь не в группе, пытаемся добавить
            try:
                # Сначала разбаним пользователя, если он был забанен
                await context.bot.unban_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    only_if_banned=True
                )
                
                # Пытаемся добавить пользователя
                await context.bot.approve_chat_join_request(
                    chat_id=group_id,
                    user_id=user_id
                )
                
                await query.message.edit_text(
                    "✅ Вы успешно добавлены в группу GameHub!\n\n"
                    "🎮 Добро пожаловать в наше сообщество!\n\n"
                    "🔗 Ссылка на группу: https://t.me/+1BmAG12rjZg2MmRi\n\n"
                    "В группе вас ждет:\n"
                    "• Эксклюзивные акции и розыгрыши\n"
                    "• Быстрая поддержка от администраторов\n"
                    "• Полезные гайды и инструкции\n"
                    "• Общение с единомышленниками",
                    reply_markup=keyboards.get_main_menu_keyboard()
                )
            except Exception as e:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при добавлении пользователя в группу: {e}")
                # Если не удалось добавить автоматически, отправляем ссылку
                invite_link = await context.bot.create_chat_invite_link(
                    chat_id=group_id,
                    expire_date=datetime.now() + timedelta(days=1),
                    member_limit=1
                )
                await query.message.edit_text(
                    "🔗 Присоединяйтесь к нашей группе: https://t.me/+1BmAG12rjZg2MmRi\n\n"
                    f"🔗 Прямая ссылка для входа: {invite_link.invite_link}\n\n"
                    "Если у вас возникли проблемы со вступлением, "
                    "пожалуйста, обратитесь в поддержку.",
                    reply_markup=keyboards.get_main_menu_keyboard()
                )
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при проверке статуса пользователя: {e}")
            await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    elif query.data == "reviews":
        await query.message.edit_text(
            "⭐️ Выберите площадку, где хотите оставить отзыв:",
            reply_markup=keyboards.get_reviews_keyboard()
        )
    
    elif query.data == "main_menu":
        await query.message.edit_text(
            "🎮 Выберите действие:",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        return states.WAITING_FOR_ACTION
    
    elif query.data == "website":
        link = os.getenv('WEBSITE_URL')
        if not link:
            await query.message.edit_text(
                "⚠️ Ссылка на сайт временно недоступна",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
            return states.WAITING_FOR_ACTION
            
        await query.message.edit_text(
            f"🌐 Наш сайт: {link}\n\n",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        return states.WAITING_FOR_ACTION
    
    elif query.data == "vk":
        link = os.getenv('VK_URL')
        if not link:
            await query.message.edit_text(
                "⚠️ Ссылка на группу ВКонтакте временно недоступна",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
            return states.WAITING_FOR_ACTION
            
        await query.message.edit_text(
            f"📱 Наша группа ВКонтакте: {link}\n\n",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        return states.WAITING_FOR_ACTION

    elif query.data == "support":
        # Получаем все активные тикеты пользователя
        active_tickets = tickets_db.get_all_tickets(query.from_user.id)
        active_tickets = [t for t in active_tickets if t[8] != 'answered']  # Фильтруем только неотвеченные
        
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
                reply_markup=keyboards.get_support_keyboard()
            )
        else:
            await query.message.edit_text(
                "🛠 Техническая поддержка\n\n"
                "Выберите действие:",
                reply_markup=keyboards.get_support_keyboard()
            )
        return states.WAITING_FOR_ACTION

    elif query.data == "create_ticket":
        # Если есть активные тикеты, закрываем их
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
            reply_markup=keyboards.get_back_to_main_keyboard()
        )
        return states.WAITING_FOR_TICKET_DESCRIPTION

    elif query.data == "my_tickets":
        await show_user_tickets(update, context)
        return states.WAITING_FOR_ACTION
    
    elif 'ticket_rating' in query.data:
        ticket_id = context.user_data.pop('closed_ticket_id', None)
        if not ticket_id:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при получении ID тикета: {e}")
            return states.WAITING_FOR_ACTION
        rating = int(query.data.split(' ')[1])
        tickets_db.rate_ticket(ticket_id, rating)
        await query.message.edit_text(
            "✅ Спасибо за вашу оценку!\n\nВыберите действие:",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        return states.WAITING_FOR_ACTION
    
    elif query.data == "warranty":
        try:
            link = os.getenv('WARRANTY_CONDITIONS_URL')
        except e as Exception:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при получении ссылки на условия гарантии: {e}")
            link = 'https://docs.google.com/document/u/0/'
        await query.message.edit_text(
            "🔒 Расширенная гарантия включает:\n\n"
            "✅ Организацию доставки в сервисный центр (если произошла поломка)\n"
            "✅ Бесплатный ремонт в течении всего срока гарантии\n"
            "✅ Быструю замену при невозможности починки\n"
            "✅ Скидки на обслуживание\n\n"
            "Для того чтобы закрепить гарантию:\n"
            "1️⃣ Выберите пункт "+"📝 Отправить отзыв на проверку"+" и введите код вашей консоли. Вы получите код вашей гарантии\n"
            "2️⃣ Оставьте отзыв на купленное устройство. В комментарии к озыву укажите ваш код гарантии.\n"
            "3️⃣ Отправьте боту скриншот отзыва.\n\n",
            reply_markup=keyboards.get_warranty_keyboard(),
            parse_mode = 'HTML',
            disable_web_page_preview=True
        )
        return states.WAITING_FOR_ACTION
    
    elif query.data == "submit_review":
        await query.message.edit_text(
            "⌨️ Пожалуйста, отправьте код вашей консоли.\n",
            reply_markup=keyboards.get_back_to_main_keyboard()
        )
        return states.WAITING_FOR_REVIEW_CHECK
    
    elif query.data == "check_warranty":
        await query.message.edit_text(
            "⌨️ Пожалуйста, отправьте код вашей консоли.\n",
            reply_markup=keyboards.get_back_to_main_keyboard()
        )
        return states.WAITING_FOR_WARRANTY_CHECK
    
    elif query.data == "back_to_main":
        await query.message.edit_text(
            "Выберите действие:",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        return states.WAITING_FOR_ACTION
    
    return states.WAITING_FOR_ACTION

async def handle_ticket_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик описания тикета"""
    user = update.effective_user
    
    # Проверяем наличие медиафайлов
    photo = update.message.photo[-1] if update.message.photo else None
    video = update.message.video if update.message.video else None
    document = update.message.document if update.message.document else None
    
    # Получаем текст описания
    description = update.message.caption if (photo or video or document) else update.message.text
    
    if not description:
        await update.message.reply_text(
            "❌ Пожалуйста, добавьте описание к вашему тикету."
        )
        return states.WAITING_FOR_TICKET_DESCRIPTION
    
    logger.info(f"Создание тикета для пользователя {user.full_name} ({user.id})")
    
    # Сохраняем тикет в базу данных
    ticket_id = len(tickets_db.get_all_tickets(user.id)) + 1
    tickets_db.add_ticket(
        user_id=user.id,
        ticket_id=ticket_id,
        description=description,
        photo_id=photo.file_id if photo else None,
        video_id=video.file_id if video else None,
        file_id=document.file_id if document else None
    )
    
    # Запрашиваем номер телефона с примером
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

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик номера телефона"""
    user = update.effective_user
    phone = update.message.text
    
    # Проверяем валидность номера
    if not is_valid_phone(phone):
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
        
        # Отправляем тикет в группу поддержки
        support_group_id = os.getenv('SUPPORT_GROUP_ID')
        if support_group_id:
            message = (
                f"🆕 Новый тикет #{ticket[2]}\n\n"
                f"👤 Пользователь: {user.first_name} (ID: {user.id})\n"
                f"📱 Телефон: {phone}\n"
                f"📅 Дата: {ticket[9]}\n\n"
                f"📝 Описание:\n{ticket[3]}\n\n"
                f"💬 Ответить: /reply_{user.id}_{ticket[2]}"
            )
            
            try:
                # Отправляем медиафайлы, если они есть
                if ticket[4]:  # photo_id
                    await context.bot.send_photo(
                        chat_id=support_group_id,
                        photo=ticket[4],
                        caption=message
                    )
                elif ticket[5]:  # video_id
                    await context.bot.send_video(
                        chat_id=support_group_id,
                        video=ticket[5],
                        caption=message
                    )
                elif ticket[6]:  # file_id
                    await context.bot.send_document(
                        chat_id=support_group_id,
                        document=ticket[6],
                        caption=message
                    )
                else:
                    await context.bot.send_message(chat_id=support_group_id, text=message, parse_mode='HTML')
            except Exception as e:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке тикета в группу поддержки: {e}")
                await update.message.reply_text(
                    "❌ Произошла ошибка при создании тикета. Пожалуйста, попробуйте позже.",
                    reply_markup=keyboards.get_main_menu_keyboard()
                )
                return states.WAITING_FOR_ACTION
    
    await update.message.reply_text(
        "✅ Спасибо! Ваш тикет создан. Мы свяжемся с вами в ближайшее время.\n\n"
        "Вы можете проверить статус тикета в разделе 'Мои тикеты'.",
        reply_markup=keyboards.get_main_menu_keyboard()
    )
    
    return states.WAITING_FOR_ACTION

async def handle_ticket_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ответов на тикеты"""
    # Проверяем, что сообщение от группы поддержки
    support_group_id = os.getenv('SUPPORT_GROUP_ID')
    if str(update.effective_chat.id) != support_group_id:
        return states.WAITING_FOR_TICKET_RESPONSE

    # Проверяем наличие команды /reply_
    if not update.message.text or not update.message.text.startswith('/reply_'):
        return states.WAITING_FOR_TICKET_RESPONSE

    try:
        # Разбираем команду
        parts = update.message.text.split('_', 2)
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Неверный формат команды. Используйте: /reply_USER_ID_TICKET_ID текст ответа"
            )
            return states.WAITING_FOR_TICKET_RESPONSE

        user_id = int(parts[1])
        ticket_id = int(parts[2].split()[0])
        response_text = update.message.text.split(' ', 1)[1] if ' ' in update.message.text else ""
        
        # Проверяем наличие медиафайлов
        photo = update.message.photo[-1] if update.message.photo else None
        video = update.message.video if update.message.video else None
        document = update.message.document if update.message.document else None
        
        # Если нет ни текста, ни медиафайлов
        if not response_text and not photo and not video and not document:
            await update.message.reply_text(
                "❌ Пожалуйста, добавьте текст ответа или прикрепите файл."
            )
            return states.WAITING_FOR_TICKET_RESPONSE
        
        # Сохраняем ответ в базу данных
        tickets_db.add_response(
            ticket_id=ticket_id,
            user_id=user_id,
            response_text=response_text,
            photo_id=photo.file_id if photo else None,
            video_id=video.file_id if video else None,
            file_id=document.file_id if document else None
        )

        # Обновляем статус тикета
        tickets_db.update_ticket_status(ticket_id, 'answered')

        # Отправляем ответ пользователю
        try:
            if photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=photo.file_id,
                    caption=f"📨 Ответ на тикет #{ticket_id}:\n\n{response_text}"
                )
            elif video:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video.file_id,
                    caption=f"📨 Ответ на тикет #{ticket_id}:\n\n{response_text}"
                )
            elif document:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=document.file_id,
                    caption=f"📨 Ответ на тикет #{ticket_id}:\n\n{response_text}"
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📨 Ответ на тикет #{ticket_id}:\n\n{response_text}"
                )
            
            # Отправляем сообщение о закрытии тикета
            context.user_data['closed_ticket_id'] = ticket_id
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Тикет был закрыт. Пожалуйста оцените работу службы поддержки.\nЕсли у вас остались вопросы, создайте новый тикет.",
                reply_markup=keyboards.get_supp_rating_keyboard()
            )
            
            # Подтверждение для поддержки
            await update.message.reply_text(
                f"✅ Ответ успешно отправлен пользователю {user_id} на тикет #{ticket_id}"
            )
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке ответа пользователю: {e}")
            await update.message.reply_text(
                "❌ Не удалось отправить ответ пользователю. Возможно, пользователь заблокировал бота."
            )

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обработке ответа: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке ответа. Пожалуйста, попробуйте еще раз."
        )

    return states.WAITING_FOR_TICKET_RESPONSE

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
        await query.message.edit_text(message, reply_markup=keyboards.get_main_menu_keyboard())
    else:
        await update.message.reply_text(message, reply_markup=keyboards.get_main_menu_keyboard())

async def handle_direct_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик прямых ответов пользователям"""
    # Проверяем, что сообщение начинается с /reply_
    if not update.message.text.startswith('/reply_'):
        return

    # Разбираем команду
    try:
        # Формат команды: /reply_USER_ID текст сообщения
        parts = update.message.text.split(' ', 1)  # Разделяем по первому пробелу
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Пожалуйста, укажите текст сообщения"
            )
            return

        command_part = parts[0]  # /reply_USER_ID
        message_text = parts[1]  # текст сообщения

        # Извлекаем user_id из команды
        try:
            user_id = int(command_part.split('_')[1])
        except (IndexError, ValueError):
            await update.message.reply_text(
                "❌ Неверный формат команды. Используйте: /reply_USER_ID текст сообщения"
            )
            return

        # Отправляем сообщение пользователю
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f'Сообщение от тех. поддержки: \n\n{message_text}'
            )
            
            # Подтверждение для поддержки
            await update.message.reply_text(
                f"✅ Сообщение успешно отправлено пользователю {user_id}"
            )
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке сообщения пользователю: {e}")
            await update.message.reply_text(
                "❌ Не удалось отправить сообщение пользователю. Возможно, пользователь заблокировал бота."
            )

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обработке сообщения: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте еще раз."
        )

async def handle_newsletter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды рассылки"""
    # Проверяем, что команда отправилась из группы поддержки
    support_group_id = os.getenv('SUPPORT_GROUP_ID')
    if str(update.effective_chat.id) != support_group_id:
        return

    # Получаем текст рассылки
    message_text = update.message.text.replace('/newsletter', '').strip()
    
    # Получаем всех пользователей
    users = tickets_db.get_all_users()
    
    success_count = 0
    fail_count = 0
    
    # Отправляем сообщение каждому пользователю
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message_text
            )
            success_count += 1
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке рассылки пользователю {user_id}: {e}")
            fail_count += 1
    
    # Отправляем отчет о рассылке
    await update.message.reply_text(
        f"📊 Результаты рассылки:\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не удалось отправить: {fail_count}"
    )

async def handle_review_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        console_id = update.message.text
        user_id = update.message.chat_id
        console_data = warranty_db.get_console_data(console_id)
        
        if not console_data:
            await update.message.reply_text(
                "❌ Ваша консоль не найдена в системе. Проверьте правильно ли указан код и попробуйте ещё раз.\n\n"
                "Если вы уверены что код правильный, обратитесь в поддерждку.",
                reply_markup=keyboards.get_back_to_main_keyboard()
            )
            return states.WAITING_FOR_REVIEW_CHECK
        
        if str(console_data[1]['warranty check']) == '':
            warranty_id = warranty_db.generate_warranty_id(console_id)
            if warranty_db.bind_console_to_user(console_id, console_data[0], user_id, warranty_id):
                pass
            else:
                await update.message.reply_text(
                    f"❌ Ошибка при привязке вашей консоли.\n"
                    "Пожалуйста попробуйте позже или обратитесь в поддержку",
                    reply_markup=keyboards.get_back_to_main_keyboard()
                )
                return states.WAITING_FOR_REVIEW_CHECK
            if warranty_id:
                context.user_data['console data'] = console_data
                await update.message.reply_text(
                    f"📸 Ваш код гарантии {warranty_id}.\n"
                    "Теперь отправьте скриншот вашего отзыва.",
                    reply_markup=keyboards.get_back_to_main_keyboard()
                )
                return states.WAITING_FOR_PHOTO_CHECK
            else:
                await update.message.reply_text(
                    f"❌ Ошибка при генерации кода гарантии.\n"
                    "Пожалуйста попробуйте позже или обратитесь в поддержку",
                    reply_markup=keyboards.get_back_to_main_keyboard()
                )
                return states.WAITING_FOR_REVIEW_CHECK
        elif str(console_data[1]['warranty check']) == '0':
            context.user_data['console data'] = console_data
            await update.message.reply_text(
                f"📸 Ваш код гарантии {console_data[1]['warranty id']}\n"
                "Теперь отправьте скриншот вашего отзыва.",
                reply_markup=keyboards.get_back_to_main_keyboard()
            )
            return states.WAITING_FOR_PHOTO_CHECK
        else:
            registration_date = datetime.strptime(console_data[1]['sell date'], '%d.%m.%Y')
            warranty_end = registration_date + timedelta(days=int(os.getenv('WARRANTY_DURATION')) + int(os.getenv('WARRANTY_COMPENSATION')))
            remaining_days = (warranty_end - datetime.now()).days
            await update.message.reply_text(
                f"✅ Ваша гарантия уже подтверждена. Осталось дней: {remaining_days}",
                reply_markup=keyboards.get_back_to_main_keyboard()
            )
            return states.WAITING_FOR_PHOTO_CHECK
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обработке сообщения: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте ещё раз."
        )
    
async def handle_warranty_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Обработка запроса на проверку гарантий
    Проверка происходит в warranty_db.warranty_check
    Сообщение для пользователя и подходящую функцию для вызова клавиатуры так же возвращает warranty_db.warranty_check
    '''
    try:
        console_id = update.message.text
        logger.info(f"Проверка гарантии консоли {console_id}")
        result = warranty_db.warranty_check(console_id)
        if result:
            await update.message.reply_text(
                        result[0],
                        reply_markup=result[1]()
                    )
            return states.WAITING_FOR_ACTION
        else:
            await update.message.reply_text(
                "❌ Ваша консоль не найдена в системе. Проверьте правильно ли указан код и попробуйте ещё раз.\n"
                "Если вы уверены что код правильный, обратитесь в поддерждку.",
                reply_markup=keyboards.get_back_to_main_keyboard()
            )
            return states.WAITING_FOR_REVIEW_CHECK
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обработке сообщения: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте ещё раз.",
            reply_markup=keyboards.get_main_menu_keyboard()
        )
        return states.WAITING_FOR_ACTION

async def handle_review_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отправленного отзыва"""
    # Проверяем, является ли обновление callback_query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_main":
            await query.message.edit_text(
                "Выберите действие:",
                reply_markup=keyboards.get_main_menu_keyboard()
            )
            return states.WAITING_FOR_ACTION
    
    # Если это обычное сообщение
    message = update.message
    
    if not (message.photo or message.document):
        await message.reply_text(
            "Пожалуйста, отправьте скриншот отзыва в формате фото или документа.\n"
            "Или нажмите кнопку 'Вернуться в главное меню', чтобы отменить отправку отзыва.",
            reply_markup=keyboards.get_back_to_main_keyboard()
        )
        return states.WAITING_FOR_PHOTO_CHECK
    
    try:
        # Получаем и обрабатываем изображение
        file = await message.photo[-1].get_file() if message.photo else message.document
        photo_bytes = await file.download_as_bytearray()
        
        # Подготовка изображения для OCR
        image = cv2.imdecode(
            np.frombuffer(photo_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
        processed_image = cv2.threshold(
            cv2.GaussianBlur(
                cv2.cvtColor(image, cv2.COLOR_BGR2GRAY),
                (1, 1), 0
            ),
            100, 255, cv2.THRESH_BINARY
        )[1]

        # Распознавание текста
        reader = easyocr.Reader(['en'])
        recognized_text = " ".join(
            reader.readtext(
                processed_image,
                detail=0,
                allowlist=string.ascii_letters.upper()
            )
        )

        # Проверка гарантийного кода
        console_index, console_data = context.user_data.pop('console data', None)
        if not console_data:
            raise ValueError("Не найдена информация о консоли в контексте")

        warranty_code = console_data['warranty id']
        if not re.search(warranty_code, recognized_text):
            await message.reply_text(
                '❌ Не удалось распознать код. Попробуйте обрезать скриншот для лучшего распознования.',
                reply_markup=keyboards.get_warranty_keyboard()
            )
            return states.WAITING_FOR_ACTION

        # Успешная активация гарантии
        warranty_db.warranty_approval_write(console_data, console_index)
        await message.reply_text(
            "🎉 Поздравляем! У вас теперь расширенная гарантия!\n\n"
            "Теперь вы можете пользоваться всеми преимуществами в течение 548 дней:\n"
            "✅ Организация доставки в сервисный центр за наш счет\n"
            "✅ Бесплатный ремонт\n"
            "✅ Быстрая замена при необходимости\n\n"
            "Проверить статус гарантии можно в меню гарантии.",
            reply_markup=keyboards.get_warranty_keyboard()
        )

    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка обработки отзыва: {e}")
        await message.reply_text(
            "⚠️ Произошла ошибка при обработке. Пожалуйста, попробуйте позже.",
            reply_markup=keyboards.get_warranty_keyboard()
        )

    return states.WAITING_FOR_ACTION

async def handle_manual_warranty_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды одобрения гарантии"""
    try:
        # Проверяем, что команда отправлена в группе поддержки
        if str(update.effective_chat.id) != os.getenv('SUPPORT_GROUP_ID'):
            logger.warning(f"Попытка одобрения гарантии вне группы поддержки: {update.effective_chat.id}")
            return

        # Извлекаем ID консоли из команды
        command = update.message.text
        console_id = int(command.split('_')[-1])

        
        logger.info(f"Попытка одобрения гарантии для консоли {console_id}")
        
        # Проверяем, что консоль есть в базе данных
        index, console_data = warranty_db.get_console_data(console_id)
        if not console_data:
            await update.message.reply_text("❌ Консоль не найдена в базе данных.")
            return
        elif str(console_data['tg id']) == '':
            await update.message.reply_text("❌ Консоль не привязана к пользователю.")
            return
        elif str(console_data['warranty check']) == '1':
            await update.message.reply_text("❌ Гарантия на эту консоль уже одобрена.")
            return
        
        user_id = console_data['tg id']
        approve_warranty = warranty_db.warranty_approval_write(console_id, index)
        # Одобряем гарантию
        if approve_warranty:
            await update.message.reply_text("✅ Гарантия успешно одобрена!")
            
            # Отправляем уведомление пользователю
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 Поздравляем! У вас теперь расширенная гарантия для консоли {console_id}!\n\n"
                         "Теперь вы можете пользоваться всеми преимуществами в течении 548 дней:\n"
                         "✅ Организация доставки в сервисный центр за наш счет\n"
                         "✅ Бесплатный ремонт\n"
                         "✅ Быстрая замена при необходимости\n\n"
                         "Проверить статус гарантии можно в меню гарантии.",
                    reply_markup=keyboards.get_warranty_keyboard()
                )
            except Exception as e:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке уведомления пользователю: {e}")
        else:
            await update.message.reply_text("❌ Не удалось одобрить гарантию. Пожалуйста, попробуйте позже.")
            
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при одобрении гарантии: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке команды. Пожалуйста, проверьте формат.") 
    