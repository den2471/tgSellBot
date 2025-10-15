import keyboards
import states
import cv2
import easyocr
import states
import keyboards
import inspect
import logging
import os
import re
import numpy as np
from database import WarrantyDb
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from database import PackedData as PacketData

logger = logging.getLogger(__name__)

warranty_db = WarrantyDb()

class ContextDataTypes:
    console_data = 'console_data'
    console_id = 'console_id'

class _OCR:
        
    async def recognize(file, console_id):

        photo_bytes = await file.download_as_bytearray()
                
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

        reader = easyocr.Reader(['ru'])
        recognized_text = " ".join(
            reader.readtext(
                processed_image,
                allowlist ='0123456789',
                detail=0,
            )
        )
        
        if not console_id:
            raise ValueError("Не найдена информация о консоли в контексте")

        warranty_id = warranty_db._get_warranty_id(console_id)

        if re.search(str(warranty_id.upper()), recognized_text):
            return True
        else:
            return False

class _warranty:

    warranty_duration = int(os.getenv('WARRANTY_DURATION'))
    delivery_compensation = int(os.getenv('WARRANTY_COMPENSATION'))
    warranty_bind_period = int(os.getenv('WARRANTY_BIND_PERIOD'))
    
    async def _open_warranty_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.message.edit_text(
            "🔒 Расширенная гарантия включает:\n\n"
            "✅ Организацию доставки в сервисный центр (если произошла поломка)\n"
            "✅ Бесплатный ремонт в течении всего срока гарантии\n"
            "✅ Быструю замену при невозможности починки\n"
            "✅ Скидки на обслуживание\n\n"
            "Для того чтобы закрепить гарантию:\n"
            "1️⃣ Выберите пункт <u>✅ Проверить статус гарантии</u> и введите код вашей консоли. Вы получите код вашей гарантии\n"
            "2️⃣ Оставьте отзыв на купленное устройство. В комментарии к озыву укажите ваш код гарантии.\n"
            "3️⃣ Отправьте боту скриншот отзыва.\n\n",
            reply_markup=keyboards.warranty(),
            parse_mode = 'HTML',
            disable_web_page_preview=True
        )
        return states.WAITING_FOR_ACTION

    async def _check_remainig(data: PacketData):
        registration_date = datetime.strptime(data.approval_date, '%d-%m-%Y')
        warranty_end = registration_date + timedelta(days=_warranty.warranty_duration + _warranty.delivery_compensation)
        remaining_days = (warranty_end - datetime.now()).days
        return remaining_days
        
    
    async def _check_bind_period(data: PacketData):
        sell_date = datetime.strptime(data.sell_date, '%d-%m-%Y')
        period_end = sell_date + timedelta(days=_warranty.warranty_bind_period)
        remaining_days = (period_end - datetime.now()).days
        if remaining_days <= 0:
            return False
        else:
            return True

    async def console_id_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.message.edit_text(
            "⌨️ Пожалуйста, отправьте код вашей консоли.\n",
            reply_markup=keyboards.back_to_main_menu()
        )
        return states.WAITING_FOR_WARRANTY_CHECK
        
    async def check_review_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            if query.data == "back_to_main":
                await query.message.edit_text(
                    "Выберите действие:",
                    reply_markup=keyboards.main_menu()
                )
                return states.WAITING_FOR_ACTION
        
        message = update.message
        
        if not (message.photo or message.document):
            await message.reply_text(
                "Пожалуйста, отправьте скриншот отзыва в формате фото или документа.\n"
                "Или нажмите кнопку 'Вернуться в главное меню', чтобы отменить отправку отзыва.",
                reply_markup=keyboards.back_to_main_menu()
            )
            return states.WAITING_FOR_PHOTO_CHECK
        
        try:
            file = await message.photo[-1].get_file() if message.photo else message.document
            console: PacketData = context.user_data.pop(ContextDataTypes.console_data, None)
            console_id = console.console_id
            if await _OCR.recognize(file, console_id):
                warranty_db.approve_warranty(console_id)
                await message.reply_text(
                    "🎉 Поздравляем! У вас теперь расширенная гарантия!\n\n"
                    "Теперь вы можете пользоваться всеми преимуществами в течение 548 дней:\n"
                    "✅ Организация доставки в сервисный центр за наш счет\n"
                    "✅ Бесплатный ремонт\n"
                    "✅ Быстрая замена при необходимости\n\n"
                    "Проверить статус гарантии можно в меню гарантии.",
                    reply_markup=keyboards.warranty()
                )
                return states.WAITING_FOR_ACTION
            else:
                await message.reply_text(
                    '❌ Не удалось распознать код. Попробуйте обрезать скриншот для лучшего распознования.',
                    reply_markup=keyboards.warranty()
                )
                return states.WAITING_FOR_ACTION
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка обработки отзыва: {e}")
            await message.reply_text(
                "⚠️ Произошла ошибка при обработке. Пожалуйста, попробуйте позже или обратитесь в поддержку.",
                reply_markup=keyboards.warranty()
            )
        return states.WAITING_FOR_ACTION
    
    async def warranty_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            if query.data == "back_to_main":
                await query.message.edit_text(
                    "Выберите действие:",
                    reply_markup=keyboards.main_menu()
                )
                return states.WAITING_FOR_ACTION
            
        try:
            console_id = update.message.text
            user_id = update.message.chat_id
            console = warranty_db.get_packed(console_id)
            
            if not await console.exist():
                await update.message.reply_text(
                    "❌ Ваша консоль не найдена в системе. Проверьте правильно ли указан код и попробуйте ещё раз.\n"
                    "Если вы уверены что код правильный, обратитесь в поддерждку.",
                    reply_markup=keyboards.back_to_main_menu()
                )
                return states.WAITING_FOR_ACTION

            if await console.approved():
                remaining_days = await _warranty._check_remainig(console)
                if remaining_days > 0:
                    await update.message.reply_text(
                        f"✅ Ваша гарантия подтверждена и активна. Осталось дней: {remaining_days}.",
                        reply_markup=keyboards.back_to_main_menu()
                    )
                    return states.WAITING_FOR_ACTION
                else:
                    await update.message.reply_text(
                        f"➖ Ваша гарантия истекла.",
                        reply_markup=keyboards.back_to_main_menu()
                    )
                    return states.WAITING_FOR_ACTION
            else:
                if await console.bound():
                    await update.message.reply_text(
                        "➖ Ваша гарантия не подтверждена.\n"
                        f"Ваш код гарантии {console.warranty_id}.\n"
                        "Для потверждения отправьте скриншот вашего отзыва.",
                        reply_markup=keyboards.back_to_main_menu()
                    )
                    context.user_data[ContextDataTypes.console_data] = console
                    return states.WAITING_FOR_PHOTO_CHECK
                else:
                    if await console.sold():
                        if await _warranty._check_bind_period(console):
                            pass
                        else:
                            await update.message.reply_text(
                                "➖ С момента покупки прошло больше 90 дней. Для регистрации гарантии пожалуйста обратитесь в поддержку.",
                                reply_markup=keyboards.back_to_main_menu()
                            )
                            return states.WAITING_FOR_ACTION
                        if warranty_db.bind_warranty(console_id, user_id):
                            console = warranty_db.get_packed(console_id)
                            await update.message.reply_text(
                                "➖ Ваша гарантия не подтверждена.\n"
                                f"Ваш код гарантии {console.warranty_id}.\n"
                                "Для потверждения отправьте скриншот вашего отзыва.",
                                reply_markup=keyboards.back_to_main_menu()
                            )
                            context.user_data[ContextDataTypes.console_data] = console
                            return states.WAITING_FOR_PHOTO_CHECK
                        else:
                            await update.message.reply_text(
                                f"❌ Произошла ошибка при привязке консоли. Пожалуйста попробуйте ещё раз или обратитесь в поддержку.",
                                reply_markup=keyboards.back_to_main_menu()
                            )
                            return states.WAITING_FOR_ACTION
                    else:
                        await update.message.reply_text(
                            f"❌ Произошла ошибка при привязке консоли. Пожалуйста обратитесь в поддержку.",
                            reply_markup=keyboards.back_to_main_menu()
                        )
                        return states.WAITING_FOR_ACTION
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} - {inspect.currentframe().f_lineno}\nОшибка при обработке сообщения: {e}")
            await update.message.reply_text(
                "⚠️ Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте ещё раз или обратитесь в поддержку."
            )
