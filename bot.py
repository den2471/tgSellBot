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
import media_handler

class Main:
    def __init__(self):
        try:
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            logger.info(f"Загружен токен бота: ***{token[-10:]}")
            
            if not token:
                logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nТокен бота не найден в файле .env")
                return

            self.application = Application.builder().token(token).build()
            
            self.media_handler = media_handler.MediaManager(self.application.bot)

            managers.media_manager = self.media_handler
            
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
            
            self.application.add_handler(conv_handler)
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/id$') & filters.Chat(SUPPORT_GROUP_ID), 
                managers.Utility.get_thread_id))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/help$') & filters.Chat(SUPPORT_GROUP_ID), 
                managers.Utility.help))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^'+Format.console_code+r'$') & ~filters.COMMAND & filters.Chat(SUPPORT_GROUP_ID), 
                managers.ConsoleCodes.add_console_code))

            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/data '+Format.console_code+r'$') & filters.Chat(SUPPORT_GROUP_ID), 
                managers.ConsoleCodes.get_data))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/remove '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
                managers.ConsoleCodes.remove_console))
            
            self.application.add_handler(MessageHandler(
                (filters.Regex(r'(?i)^/sell '+Format.console_code+r'$') | filters.Regex(r'(?i)^/sell '+Format.console_code+r' '+Format.date_raw+r'$')) & filters.Chat(int(SUPPORT_GROUP_ID)), 
                managers.ConsoleCodes.sell_console))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/unsell '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
                managers.ConsoleCodes.unsell_console))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/bind '+Format.console_code+r' '+Format.tg_id+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
                managers.ConsoleCodes.bind_warranty))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/unbind '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
                managers.ConsoleCodes.unbind_warranty))
            
            self.application.add_handler(MessageHandler(
                (filters.Regex(r'(?i)^/approve '+Format.console_code+r'$') | filters.Regex(r'(?i)^/approve '+Format.console_code+r' '+Format.date_raw+r'$')) & filters.Chat(int(SUPPORT_GROUP_ID)), 
                managers.ConsoleCodes.approve))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/unapprove '+Format.console_code+r'$') & filters.Chat(int(SUPPORT_GROUP_ID)), 
                managers.ConsoleCodes.unapprove))

            self.application.add_handler(MessageHandler(
                (filters.Regex(r'(?i)^/newsletter\s+.+') | filters.CaptionRegex(r'(?i)^/newsletter\s+.+')) & filters.Chat(SUPPORT_GROUP_ID),
                managers.SupportManager.newsletter))
            
            self.application.add_handler(MessageHandler(
                filters.Regex(r'(?i)^/approve_warranty '+Format.console_code+r'$') & filters.Chat(SUPPORT_GROUP_ID),
                managers.SupportManager.manual_warranty_approval))

            self.application.add_handler(MessageHandler(
                (filters.Regex(r'(?is)^/reply '+Format.tg_id+r' \d+\s+.+') | filters.CaptionRegex(r'(?i)^/reply '+Format.tg_id+r' \d+\s+.+')) & filters.Chat(SUPPORT_GROUP_ID), 
                managers.SupportManager.ticket_response))
            
            self.application.add_handler(MessageHandler(
                (filters.Regex(r'(?is)^/direct_reply '+Format.tg_id+r'\s+.+') | filters.CaptionRegex(r'(?is)^/direct_reply '+Format.tg_id+r'\s+.+')) & filters.Chat(SUPPORT_GROUP_ID), 
                managers.SupportManager.direct_reply))
            
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except telegram.error.Conflict:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОбнаружен конфликт: возможно, запущено несколько экземпляров бота")
            sys.exit(1)
        
if __name__ == '__main__':
    Main()