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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# remove unnesessary logging
logging.getLogger("httpx").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*per_message=False.*")

logger = logging.getLogger(__name__)

# .env loading
class ResourcesMissing(Exception):
    pass

env_path = "resources/.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    raise ResourcesMissing('.env missing')

tg_token_env = "resources/tg_token.env"
if os.path.exists(tg_token_env):
    load_dotenv(tg_token_env)
else:
    raise ResourcesMissing('tg_token.env missing')

logger.info("Переменные загружены из resources/")

import states
import telegram
import handlers

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
            entry_points=[CommandHandler('start', handlers.start), CallbackQueryHandler(handlers.button_handler)],
            states={
                states.WAITING_FOR_LICENCE_ACCEPT: [
                    CallbackQueryHandler(handlers.licence_accept_handler)
                ],
                states.WAITING_FOR_ACTION: [
                    CallbackQueryHandler(handlers.button_handler)
                ],
                states.WAITING_FOR_TICKET_DESCRIPTION: [
                    MessageHandler(
                        filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND,
                        handlers.handle_ticket_description
                    ),
                    CallbackQueryHandler(handlers.button_handler)
                ],
                states.WAITING_FOR_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_phone)
                ],
                states.WAITING_FOR_TICKET_RESPONSE: [
                    MessageHandler(
                        filters.TEXT & filters.Regex(r'^/reply_\d+_\d+.*'),
                        handlers.handle_ticket_response
                    )
                ],
                states.WAITING_FOR_REVIEW_CHECK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, handlers.handle_review_check
                    ),
                    CallbackQueryHandler(handlers.button_handler)
                ],
                states.WAITING_FOR_PHOTO_CHECK: [
                    MessageHandler(
                        filters.PHOTO, handlers.handle_review_photo
                    ),
                    CallbackQueryHandler(handlers.button_handler)
                ],
                states.WAITING_FOR_WARRANTY_CHECK: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, handlers.handle_warranty_check
                    )
                ]
            },
            fallbacks=[CommandHandler('start', handlers.start)],
            per_message=False,
        )
        
        application.add_handler(conv_handler)
        
        application.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^/reply_\d+_\d+.*'), 
            handlers.handle_ticket_response))
        
        application.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^/reply_\d+.*'), 
            handlers.handle_direct_reply))

        application.add_handler(CommandHandler('newsletter', handlers.handle_newsletter))
        
        application.add_handler(MessageHandler(
            filters.Regex(r'^/approve_warranty_\d+'),
            handlers.handle_manual_warranty_approval
        ))
        
        logger.info("Обработчики добавлены")
        
        logger.info("Запуск бота...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except telegram.error.Conflict:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОбнаружен конфликт: возможно, запущено несколько экземпляров бота")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nПроизошла ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 