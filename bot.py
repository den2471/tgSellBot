import os
import logging
import sys
import inspect
from dotenv import load_dotenv
from telegram import  Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
import warnings
from telegram.warnings import PTBUserWarning
from re_codes import Format

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# remove unnesessary logging
logging.getLogger("httpx").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*per_message=False.*")

logger = logging.getLogger(__name__)

load_dotenv('resources/.env')
load_dotenv('resources/tg_token.env')

SUPPORT_GROUP_ID = int(os.getenv('SUPPORT_GROUP_ID'))
CODES_THREAD_ID = int(os.getenv('CODES_THREAD_ID'))
SUPPORT_THREAD_ID = int(os.getenv('SUPPORT_THREAD_ID'))

logger.info("Переменные загружены из resources/")

import states
import telegram
import managers

def main():
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        logger.info(f"Загружен токен бота: ***{token[-10:]}")
        
        if not token:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nТокен бота не найден в файле .env")
            return

        application = Application.builder().token(token).build()
        logger.info("Приложение бота успешно создано")
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', managers.UserConversation.start, filters=filters.ChatType.PRIVATE), CallbackQueryHandler(managers.UserConversation.button_handler)],
            states={
                states.WAITING_FOR_LICENCE_ACCEPT: [
                    CallbackQueryHandler(managers.UserConversation.licence_accept_handler)
                ],
                states.WAITING_FOR_ACTION: [
                    CallbackQueryHandler(managers.UserConversation.button_handler)
                ],
                states.WAITING_FOR_TICKET_DESCRIPTION: [
                    MessageHandler(
                        filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND,
                        managers.UserConversation.Support.handle_ticket_description
                    ),
                    CallbackQueryHandler(managers.UserConversation.button_handler)
                ],
                states.WAITING_FOR_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, managers.UserConversation.Support.handle_phone)
                ],
                states.WAITING_FOR_WARRANTY_CHECK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, managers.UserConversation.Warranty.warranty_check
                    ),
                    CallbackQueryHandler(managers.UserConversation.button_handler)
                ],
                states.WAITING_FOR_PHOTO_CHECK: [
                    MessageHandler(
                        filters.PHOTO, managers.UserConversation.Warranty.check_review_photo
                    ),
                    CallbackQueryHandler(managers.UserConversation.button_handler)
                ]
            },
            fallbacks=[CommandHandler('start', managers.UserConversation.start)],
            per_message=False,
        )
        
        application.add_handler(conv_handler)
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/id$') & filters.Chat(SUPPORT_GROUP_ID), 
            managers.Utility.get_thread_id))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/help$') & filters.Chat(SUPPORT_GROUP_ID), 
            managers.Utility.help))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^'+Format.console_code+r'$') & ~filters.COMMAND & filters.Chat(SUPPORT_GROUP_ID), 
            managers.ConsoleCodes.add_console_code))

        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/data '+Format.console_code+r'$') & filters.Chat(SUPPORT_GROUP_ID), 
            managers.ConsoleCodes.get_data))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/remove '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
            managers.ConsoleCodes.remove_console))
        
        application.add_handler(MessageHandler(
            (filters.Regex(r'(?i)^/sell '+Format.console_code+r'$') | filters.Regex(r'(?i)^/sell '+Format.console_code+r' '+Format.date_raw+r'$')) & filters.Chat(int(SUPPORT_GROUP_ID)), 
            managers.ConsoleCodes.sell_console))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/unsell '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
            managers.ConsoleCodes.unsell_console))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/bind '+Format.console_code+r' '+Format.tg_id+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
            managers.ConsoleCodes.bind_warranty))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/unbind '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
            managers.ConsoleCodes.unbind_warranty))
        
        application.add_handler(MessageHandler(
            (filters.Regex(r'(?i)^/approve '+Format.console_code+r'$') | filters.Regex(r'(?i)^/approve '+Format.console_code+r' '+Format.date_raw+r'$')) & filters.Chat(int(SUPPORT_GROUP_ID)), 
            managers.ConsoleCodes.approve))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/unapprove '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
            managers.ConsoleCodes.unapprove))

        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/newsletter .+') & filters.Chat(SUPPORT_GROUP_ID),
            managers.SupportManager.newsletter))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'(?i)^/approve_warranty '+Format.console_code+r'$') & filters.Chat(SUPPORT_GROUP_ID),
            managers.SupportManager.manual_warranty_approval))

        application.add_handler(MessageHandler(
            (filters.Regex(r'(?i)^/reply '+Format.tg_id+r' \d+ .+') | filters.CaptionRegex(r'(?i)^/reply '+Format.tg_id+r' \d+ .+')) & filters.Chat(SUPPORT_GROUP_ID), 
            managers.SupportManager.ticket_response))
        
        application.add_handler(MessageHandler(
            (filters.Regex(r'(?i)^/direct_reply '+Format.tg_id+r' .+') | filters.CaptionRegex(r'(?i)^/direct_reply '+Format.tg_id+r' .+')) & filters.Chat(SUPPORT_GROUP_ID), 
            managers.SupportManager.direct_reply))

        logger.info("Обработчики добавлены")
        
        logger.info("Запуск бота...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except telegram.error.Conflict:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОбнаружен конфликт: возможно, запущено несколько экземпляров бота")
        sys.exit(1)

if __name__ == '__main__':
    main() 