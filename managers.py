import os
import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
import states
import keyboards
import inspect
from database import (
    TicketDb,
    WarrantyDb,
    PackedData
)
from datetime import datetime
from media_handler import MediaManager
from re_codes import Format

logger = logging.getLogger(__name__)
media_manager = MediaManager()
tickets_db = TicketDb()
warranty_db = WarrantyDb()

class BotCallbackData:
    NEXT_LICENCE = "next_licence"
    LICENCE_ACCEPTED = "licence_accepted"

class BotContextData:
    LICENCE_INDEX = "licence_index"

class Utility:

    support_thread_id = int(os.getenv('SUPPORT_THREAD_ID'))
    codes_thread_id = int(os.getenv('CODES_THREAD_ID'))
    
    async def get_thread_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            group_id = update.message.chat_id
            thread_id = update.message.message_thread_id
            await update.message.reply_text(f'ID группы {group_id}\nID топика {thread_id}')
        except:
            print('Error')
            pass
    
    async def is_valid_phone(phone):
        phone = re.sub(r'\D', '', phone)
        return len(phone) in [10, 11]
    
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        thread_id = update.message.message_thread_id
        if thread_id == Utility.support_thread_id:
            message = "" \
            "Список для чата топика поддержки\n" \
            "\n" \
            "<code>/id</code> - узнать id чата и топика\n" \
            "\n" \
            "<code>/newsletter [текст сообщения]</code> - Разослать сообщение всем пользователям принявшим лицензионное соглашение.\n" \
            "Пример:\n" \
            "<b>/newsletter текст сообщения</b>\n" \
            "\n" \
            "<code>/approve_warranty [код консоли]</code> - одобить гарантию для консоли и уведомить пользователя.\n" \
            "Пример:\n" \
            "<b>/approve_warranty ATJ10561484807</b>\n" \
            "\n" \
            "<code>/reply [tg_id пользователя] [номер тикета] [текст ответа]</code> - ответить на тикет пользователя. Можно прикрепить 1 медифайл.\n" \
            "Пример:\n" \
            "<b>/reply 123456789 1 текст ответа</b>\n" \
            "\n" \
            "<code>/direct_reply [tg_id пользователя]</code> - отправить сообщение пользователю напрямую. Можно прикрепить 1 медифайл.\n" \
            "Пример:\n" \
            "<b>/direct_reply 123456789 текст ответа</b>\n\n"
        elif thread_id == Utility.codes_thread_id:
            message = "" \
            "Список для чата топика кодов консолей. Пожалуйста обращайте внимание на формат даты\n" \
            "\n" \
            "<code>/id</code> - узнать id чата и топика\n" \
            "\n" \
            "<code>/data [код консоли]</code> - получить данные консоли\n" \
            "Пример:\n" \
            "<b>/data ATJ10561484807</b>\n" \
            "\n" \
            "<code>[код консоли]</code> - добавить консоль в базу данных\n" \
            "Пример:\n" \
            "<b>ATJ10561484807</b>\n" \
            "\n" \
            "<code>/remove [код консоли]</code> - удалить все данные консоли из базы\n" \
            "Пример:\n" \
            "<b>/remove ATJ10561484807</b>\n" \
            "\n" \
            "<code>/sell [код консоли] [дата]</code> - пометить консоль как проданную. Можно использовать комманду как с датой так и без. Если не указать дату, то будет выбрано сегодняшнее число\n" \
            "Пример:\n" \
            "<b>/sell ATJ10561484807 31-12-2025</b>\n" \
            "\n" \
            "<code>/unsell [код консоли]</code> - удалить данные о продаже. Так же будут удалены данные о привязке консоли и одобрении гарантии\n" \
            "Пример:\n" \
            "<b>/unsell ATJ10561484807</b>\n" \
            "\n" \
            "<code>/bind [код консоли] [tg_id пользователя]</code> - привязать консоль к пользователю\n" \
            "Пример:\n" \
            "<b>/bind ATJ10561484807 123456789</b>\n" \
            "\n" \
            "<code>/unbind [код консоли]</code> - удалить привязку консоли. Так же будут удалены данные о одобрении гарантии\n" \
            "Пример:\n" \
            "<b>/unbind ATJ10561484807</b>\n" \
            "\n" \
            "<code>/approve [код консоли] [дата]</code> - подтвердить гарантию без уведомления пользователя. Если не указать дату, будет выбрано сегодняшнее число. Исходя из даты будет расчитываться оставшийся срок действия гарантии\n" \
            "Пример:\n" \
            "<b>/approve ATJ10561484807 31-12-2025</b>\n" \
            "\n" \
            "<code>/unapprove [код консоли]</code> - аннулировать подтверждение гарантии\n" \
            "Пример:\n" \
            "<b>/unapprove ATJ10561484807</b>"
        
        await update.message.reply_text(message, parse_mode='HTML')


class SupportManager:

    support_thread_id = int(os.getenv('SUPPORT_THREAD_ID'))
    date_format = '%d-%m-%Y'

    async def _check_thread(update: Update):
        if update.message.message_thread_id == SupportManager.support_thread_id:
            return True
        
    async def _date_check(date):

        try:
            datetime.strptime(date, SupportManager.date_format)
            return True
        except:
            return False

    async def manual_warranty_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await SupportManager._check_thread(update):
            try:
                re_code = re.match(r'(?i)^/approve_warranty ('+Format.console_code+r')$', update.message.text)
                console_id = re_code.group(1)
                console: PackedData = warranty_db.get_packed(console_id)
                if not await console.exist():
                    await update.message.reply_text("➖ Консоль не найдена в базе данных")
                    return
                if not await console.sold():
                    await update.message.reply_text("❌ Консоль не продана")
                    return
                elif not await console.bound():
                    await update.message.reply_text("❌ Консоль не привязана к пользователю")
                    return
                elif await console.approved():
                    await update.message.reply_text("❌ Гарантия на эту консоль уже одобрена")
                    return
                
                if warranty_db.approve_warranty(console_id):
                    await update.message.reply_text("✅ Гарантия успешно одобрена!")
                    try:
                        await context.bot.send_message(
                            chat_id=console.tg_id,
                            text=f"🎉 Поздравляем! У вас теперь расширенная гарантия для консоли {console_id}!\n\n"
                                "Теперь вы можете пользоваться всеми преимуществами в течении 548 дней:\n"
                                "✅ Организация доставки в сервисный центр за наш счет\n"
                                "✅ Бесплатный ремонт\n"
                                "✅ Быстрая замена при необходимости\n\n"
                                "Проверить статус гарантии можно в меню гарантии.",
                            reply_markup=keyboards.warranty()
                        )
                    except Exception as e:
                        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке уведомления пользователю: {e}")
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')
                    
            except Exception as e:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при одобрении гарантии: {e}")
                await update.message.reply_text("❌ Произошла ошибка при обработке команды. Пожалуйста, проверьте формат.")

    async def direct_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await SupportManager._check_thread(update):
            try:
                try:
                    re_code = re.match(r'(?i)^/direct_reply ('+Format.tg_id+') (.+)', update.message.text)
                except:
                    re_code = re.match(r'(?i)^/direct_reply ('+Format.tg_id+') (.+)', update.message.caption)
                user_id = re_code.group(1)
                message_text = re_code.group(2)

                photo = update.message.photo[-1] if update.message.photo else None
                video = update.message.video if update.message.video else None
                document = update.message.document if update.message.document else None

                try:
                    if photo:
                        await context.bot.send_photo(
                            chat_id=user_id,
                            photo=photo.file_id,
                            caption=f"Сообщение от тех. поддержки: \n\n{message_text}",
                            reply_markup=keyboards.back_to_main_menu()
                        )
                    elif video:
                        await context.bot.send_video(
                            chat_id=user_id,
                            video=video.file_id,
                            caption=f"Сообщение от тех. поддержки: \n\n{message_text}",
                            reply_markup=keyboards.back_to_main_menu()
                        )
                    elif document:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=document.file_id,
                            caption=f"Сообщение от тех. поддержки: \n\n{message_text}",
                            reply_markup=keyboards.back_to_main_menu()
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Сообщение от тех. поддержки: \n\n{message_text}",
                            reply_markup=keyboards.back_to_main_menu()
                        )
                    
                    await update.message.reply_text(
                        f"✅ Сообщение успешно отправлено пользователю {user_id}"
                    )
                    
                except Exception as e:
                    logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при отправке ответа пользователю: {e}")
                    await update.message.reply_text(
                        "❌ Не удалось отправить ответ пользователю. Возможно, пользователь заблокировал бота."
                    )

            except Exception as e:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обработке сообщения: {e}")
                await update.message.reply_text(
                    "❌ Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте еще раз"
                )

    async def ticket_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if await SupportManager._check_thread(update):
            try:
                try:
                    re_code = re.match(r'(?i)^/reply ('+Format.tg_id+r') (\d+) (.+)', update.message.text)
                except:
                    re_code = re.match(r'(?i)^/reply ('+Format.tg_id+r') (\d+) (.+)', update.message.caption)
                user_id = int(re_code.group(1))
                ticket_id = int(re_code.group(2))
                response_text = re_code.group(2)
                
                photo = update.message.photo[-1] if update.message.photo else None
                video = update.message.video if update.message.video else None
                document = update.message.document if update.message.document else None
                
                # Сохраняем ответ в базу данных
                tickets_db.add_response(
                    ticket_id=ticket_id,
                    user_id=user_id,
                    response_text=response_text,
                    photo_id=photo.file_id if photo else None,
                    video_id=video.file_id if video else None,
                    file_id=document.file_id if document else None
                )

                tickets_db.update_ticket_status(ticket_id, 'answered')

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
                        text="✅ Тикет был закрыт.\nЕсли у вас остались вопросы, создайте новый тикет.\nПожалуйста оцените работу службы поддержки.",
                        reply_markup=keyboards.supp_rating()
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

    async def newsletter(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = re.match(r'(?i)^/newsletter (.+)', update.message.text).group(1)
        
        users = tickets_db.get_all_users()
        
        success_count = 0
        fail_count = 0
        
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

class ConsoleCodes:

    codes_thread_id = int(os.getenv('CODES_THREAD_ID'))

    async def _check_thread(update: Update):
        if update.message.message_thread_id == ConsoleCodes.codes_thread_id:
            return True
    
    async def _extract_user_id(command, string):
        extracted = re.search(r' \d+$', string)
        id = extracted.group(1)
        return id
    
    async def _form_data_string(data: PackedData):
        """
        Преобразует упакованные данные консоли в строку готовую к отправке
        """
        data_str = f'<code>{data.console_id}</code> - Код консоли\n<code>{data.sell_date}</code> - Дата продажи\n<code>{data.tg_id}</code> - TG_ID\n<code>{data.warranty_id}</code> - Код гарантии\n<code>{data.approval_date}</code> - Дата подтверждения гарантии'
        return data_str
        
    async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            console_id = re.match(r'(?i)^/data ('+Format.console_code+')$', update.message.text).group(1)
            console = warranty_db.get_packed(console_id)
            if await console.exist():
                await update.message.reply_text(f'✅ Данные консоли\n{await ConsoleCodes._form_data_string(console)}', parse_mode='HTML')
            else:
                await update.message.reply_text('➖ Консоли нет в базе')

    async def add_console_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            console_id = update.message.text
            console = warranty_db.get_packed(console_id)
            if await console.exist():
                await update.message.reply_text('➖ Консоль уже есть в базе')
            else:
                if warranty_db.add_console(console_id):
                    await update.message.reply_text('✅ Консоль успешно добавлена в базу')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')
    
    async def remove_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            console_id = re.match(r'(?i)^/remove ('+Format.console_code+')$', update.message.text).group(1)
            console = warranty_db.get_packed(console_id)
            if not await console.exist():
                await update.message.reply_text('➖ Консоли нет в базе')  
            else:
                if warranty_db.remove_console(console_id):
                    await update.message.reply_text(f'✅ Консоль успешно удалена из базы\nДанные до удаления:\n{await ConsoleCodes._form_data_string(console)}', parse_mode='HTML')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')
    
    async def sell_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            try:
                re_code = re.match(r'(?i)^/sell ('+Format.console_code+r') ('+Format.date_raw+r')$', update.message.text)
                console_id = re_code.group(1)
                date = re_code.group(2)
            except:
                re_code = re.match(r'(?i)^/sell ('+Format.console_code+r')$', update.message.text)
                console_id = re_code.group(1)
                date = None
            console = warranty_db.get_packed(console_id)
            if not await console.exist():
                await update.message.reply_text('➖ Консоли нет в базе')
            if await console.sold():
                await update.message.reply_text('➖ Консоль уже была продана')
            else:
                if warranty_db.sell_console(console_id, date):
                    await update.message.reply_text('✅ Консоль успешно помечена как проданная')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')
    
    async def unsell_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            console_id = re.match(r'(?i)^/unsell ('+Format.console_code+')$', update.message.text).group(1)
            console = warranty_db.get_packed(console_id)
            if not await console.exist():
                await update.message.reply_text('➖ Консоли нет в базе')
            elif not await console.sold():
                await update.message.reply_text('➖ Консоль не была помечена как проданная')
            else:
                if warranty_db.unsell_console(console_id):
                    await update.message.reply_text(f'✅ Консоль успешно помечена как не проданная\nДанные до удаления:\n{await ConsoleCodes._form_data_string(console)}', parse_mode='HTML')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')
    
    async def bind_warranty(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            re_code = re.match(r'(?i)^/bind ('+Format.console_code+') ('+Format.tg_id+')$', update.message.text)
            console_id = re_code.group(1) 
            tg_id = re_code.group(2)
            console = warranty_db.get_packed(console_id)
            if not await console.exist():
                await update.message.reply_text('➖ Консоли нет в базе')
            if not await console.sold():
                await update.message.reply_text('➖ Консоль не помечена как проданная. Сначала нужно пометить консоль как проданную. Используйте /sell')
            elif await console.bound():
                await update.message.reply_text('➖ Гарантия к консоли уже была привязана')
            else:
                if warranty_db.bind_warranty(console_id, tg_id):
                    await update.message.reply_text('✅ Гарантия успешно привязана')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')

    async def unbind_warranty(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            console_id = re.match(r'(?i)^/unbind ('+Format.console_code+')$', update.message.text).group(1)
            console = warranty_db.get_packed(console_id)
            if not await console.exist():
                await update.message.reply_text('➖ Консоли нет в базе')
            if not await console.bound():
                await update.message.reply_text('➖ Гарантия не была привязана к консоли')
            else:
                if warranty_db.unbind_warranty(console_id):
                    await update.message.reply_text(f'✅ Гарантия успешно отвязана от консоли\nДанные до удаления:\n{await ConsoleCodes._form_data_string(console)}', parse_mode='HTML')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')

    async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            try:
                re_code = re.match(r'(?i)^/approve ('+Format.console_code+r') ('+Format.date_raw+r')$', update.message.text)
                console_id = re_code.group(1)
                date = re_code.group(2)
            except:
                re_code = re.match(r'(?i)^/approve ('+Format.console_code+')$', update.message.text)
                console_id = re_code.group(1)
                date = None
            console = warranty_db.get_packed(console_id)
            if not await console.exist():
                await update.message.reply_text('➖ Консоли нет в базе')
            if not await console.sold():
                await update.message.reply_text('➖ Консоль не помечена как проданная. Сначала нужно пометить консоль как проданную. Используйте /sell')
            elif not await console.bound():
                await update.message.reply_text('➖ Гарантия не была привязана к консоли. Сначала нужно привязать гарантию. Используйте /bind')
            elif await console.approved():
                await update.message.reply_text('➖ Гарантия для консоли уже была одобрена')
            else:
                if warranty_db.approve_warranty(console_id, date):
                    await update.message.reply_text('✅ Гарантия одобрена')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')
    
    async def unapprove(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await ConsoleCodes._check_thread(update):
            console_id = re.match(r'(?i)^/unapprove ('+Format.console_code+')$', update.message.text).group(1)
            console = warranty_db.get_packed(console_id)
            if not await console.exist():
                await update.message.reply_text('➖ Консоли нет в базе')
            if not await console.approved():
                await update.message.reply_text('➖ Гарантия для консоли не была одобрена')
            else:
                if warranty_db.unapprove_warranty(console_id):
                    await update.message.reply_text(f'✅ Гарантия успешно отозвана\nДанные до удаления:\n{await ConsoleCodes._form_data_string(console)}', parse_mode='HTML')
                else:
                    await update.message.reply_text('❌ Произошла ошибка при внесении изменений в базу')

class UserConversation:

    from _support import _support as Support
    from _warranty import _warranty as Warranty

    licence_error_cap = 'Не получилось отправить пользовательское соглашение, перезапустите бота немного позже ↩️ либо ознакомьтесь с соглашением в соответствующем разделе'
    internal_error_cap = '🛑 Произошла внутрення ошибка, пожалуйста перезапустите бота командой /start'
    start_cap = "🎮 Присоединяйтесь к нашему игровому комьюнити 🎮!\n\n" \
                    "Здесь вас ждет:\n" \
                    "✅ Эксклюзивные акции — розыгрыши игр, скидки и подарки только для участников.\n" \
                    "✅ Быстрая поддержка — ответы на вопросы в чате по техническим проблемам.\n" \
                    "✅ Полезные материалы — гайды, Инструкции.\n" \
                    "Стань частью сообщества — делитесь опытом, находите друзей и получайте крутые бонусы!"
        
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        context.user_data[BotContextData.LICENCE_INDEX] = 1
        licence_photo, quantity = media_manager.get_licence_by_index(context.user_data[BotContextData.LICENCE_INDEX])
        if not licence_photo:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno} - Файлы лицензионного соглашения не найдены")
                await context.bot.send_message(
                    chat_id=context._chat_id, 
                    text=UserConversation.licence_error_cap)
                await UserConversation._send_advert(update, context)
                return states.WAITING_FOR_ACTION
        else:
            logger.info(f"{quantity} лицензионных файлов ранее загружено")
            await update.message.reply_photo(
                    photo=licence_photo,
                    caption=f'{context.user_data[BotContextData.LICENCE_INDEX]} из {quantity}',
                    reply_markup=keyboards.next_licence()
                )
            return states.WAITING_FOR_LICENCE_ACCEPT
    
    async def licence_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = update.effective_user
            query = update.callback_query
            await query.answer()
            if query.data == BotCallbackData.NEXT_LICENCE:
                context.user_data[BotContextData.LICENCE_INDEX] += 1
                licence_photo, quantity = media_manager.get_licence_by_index(context.user_data[BotContextData.LICENCE_INDEX])
                if context.user_data[BotContextData.LICENCE_INDEX] < quantity:
                    markup = keyboards.next_licence()
                elif context.user_data[BotContextData.LICENCE_INDEX] == quantity:
                    markup = keyboards.licence_accept()
                else:
                    logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\Ошибка индекса лицензионного файла")
                    context.bot.send_message(UserConversation.internal_error_cap)
                    return states.WAITING_FOR_LICENCE_ACCEPT
                await query.message.reply_photo(
                    photo=licence_photo,
                    caption=f"{context.user_data[BotContextData.LICENCE_INDEX]} из {quantity}",
                    reply_markup=markup,
                )
                return states.WAITING_FOR_LICENCE_ACCEPT
            elif query.data == BotCallbackData.LICENCE_ACCEPTED:
                logger.info(f"Пользователь {user.full_name} ({user.id}) принял соглашение")
                await UserConversation._send_advert(update, context)
                return states.WAITING_FOR_ACTION
            else:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\Получен не верный CallBack от сервера")
                context.bot.send_message(UserConversation.internal_error_cap)
                return states.WAITING_FOR_ACTION
        except Exception as ex:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\Ошибка при отправке файла соглашения {ex}, пропуск шага")
            context.bot.send_message(UserConversation.licence_error_cap)
            return states.WAITING_FOR_ACTION
    
    async def _send_advert(update: Update, context: ContextTypes.DEFAULT_TYPE):
        ad_media, extention = media_manager.get_random_ad()
        user_id = update.effective_user.id
        user_name = update.effective_user.name
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        tickets_db.add_user(user_id, user_name, first_name, last_name)
        if ad_media:
            if extention == "pic":
                await context.bot.send_photo(
                    chat_id=context._chat_id,
                    photo=ad_media
                )
                await context.bot.send_message(
                    chat_id=context._chat_id,
                    text=UserConversation.start_cap,
                    reply_markup=keyboards.main_menu()
                )
            else:
                await context.bot.send_video(
                    chat_id=context._chat_id,
                    video=ad_media
                )
                await context.bot.send_message(
                    chat_id=context._chat_id,
                    text=UserConversation.start_cap,
                    reply_markup=keyboards.main_menu()
                )  
        else:
            logger.error("Не найдены рекламные файлы, пропуск")
            await context.bot.send_message(
                chat_id=context._chat_id,
                text=UserConversation.start_cap,
                reply_markup=keyboards.main_menu()
            )
    
    async def _open_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.message.chat.send_message(
                text="🎮 Выберите действие:",
                reply_markup=keyboards.main_menu()
            )
        return states.WAITING_FOR_ACTION

    async def _send_site_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        link = os.getenv('WEBSITE_URL')
        if not link:
            await query.message.edit_text(
                "⚠️ Ссылка на сайт временно недоступна",
                reply_markup=keyboards.main_menu()
            )
            return states.WAITING_FOR_ACTION
            
        await query.message.edit_text(
            f"🌐 Наш сайт: {link}\n\n",
            reply_markup=keyboards.main_menu()
        )
        return states.WAITING_FOR_ACTION
    
    async def _send_vk_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        link = os.getenv('VK_URL')
        if not link:
            await query.message.edit_text(
                "⚠️ Ссылка на группу ВКонтакте временно недоступна",
                reply_markup=keyboards.main_menu()
            )
            return states.WAITING_FOR_ACTION
            
        await query.message.edit_text(
            f"📱 Наша группа ВКонтакте: {link}\n\n",
            reply_markup=keyboards.main_menu()
        )
        return states.WAITING_FOR_ACTION
    
    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "main_menu":
            return await UserConversation._open_main_menu(update, context)
        
        elif query.data == "instructions":
            return await _instructions._open_instructions_menu(update, context)
        
        elif query.data == "join_group":
            return await _user_group._open_group_join_menu(update, context)
        
        elif query.data == "reviews":
            return await _reviews._open_reviews_menu(update, context)
        
        elif query.data == "website":
            return await UserConversation._send_site_link(update, context)
        
        elif query.data == "vk":
            return await UserConversation._send_vk_link(update, context)
        
        elif query.data == "back_to_main":
            return await UserConversation._open_main_menu(update, context)


        
        elif query.data == "support":
            return await UserConversation.Support._open_support_menu(update, context)

        elif query.data == "create_ticket":
            return await UserConversation.Support._create_ticket(update, context)

        elif query.data == "my_tickets":
            return await UserConversation.Support.show_user_tickets(update, context)
        
        elif 'ticket_rating' in query.data:
            return await UserConversation.Support._rate_ticket(update, context)
        
                
        
        elif query.data == "warranty":
            return await UserConversation.Warranty._open_warranty_menu(update, context)
        
        elif query.data == "check_warranty":
            return await UserConversation.Warranty.console_id_request(update, context)
        
        
        
        return states.WAITING_FOR_ACTION
    
from _instructions import _instructions
from _user_group import _user_group
from _reviews import _reviews