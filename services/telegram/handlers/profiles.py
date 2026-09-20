from telegram import Update
from telegram.ext import ContextTypes

from services.telegram.state import get_user_state
from services.telegram.profile_callbacks import _profile_list_text, profile_list_keyboard


async def profiles_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    state = get_user_state(update.effective_user.id)
    language = state.language
    await update.message.reply_text(
        _profile_list_text(state, language),
        parse_mode="HTML",
        reply_markup=profile_list_keyboard(state, language),
    )
