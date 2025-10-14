import keyboards
import states
import os
from datetime import datetime, timedelta
import inspect
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class _user_group:
    
    async def _open_group_join_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
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
                    reply_markup=keyboards.main_menu()
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
                    reply_markup=keyboards.main_menu()
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
                    reply_markup=keyboards.main_menu()
                )
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при проверке статуса пользователя: {e}")
            await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")