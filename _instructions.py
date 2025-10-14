import keyboards
import states
from telegram import Update
from telegram.ext import ContextTypes

class _instructions:
    
    async def _open_instructions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.message.edit_text(
                "📖 Выберите инструкцию:",
                reply_markup=keyboards.instructions()
            )
        return states.WAITING_FOR_ACTION