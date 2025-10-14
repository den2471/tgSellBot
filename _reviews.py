import keyboards
import states
from telegram import Update
from telegram.ext import ContextTypes

class _reviews:
    
    async def _open_reviews_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.message.edit_text(
                "⭐️ Выберите площадку, где хотите оставить отзыв:",
                reply_markup=keyboards.reviews()
            )
        return states.WAITING_FOR_ACTION