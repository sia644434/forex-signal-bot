from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.telegram.state import get_user_state
from profiles import PRESET_PROFILES, list_profiles, get_profile


def _profile_label(profile, language: str) -> str:
    return profile.name if language == "fa" else profile.name


async def profiles_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    state = get_user_state(update.effective_user.id)
    language = state.language
    profiles = list_profiles(state)
    lines = ["⚙️ <b>پروفایل‌های تحلیل</b>"] if language == "fa" else ["⚙️ <b>Analysis Profiles</b>"]
    if profiles:
        for profile in profiles:
            marker = "🟢" if profile.profile_id == state.settings.get("active_profile_id") else "⚪"
            styles = ", ".join(item.style_id for item in profile.styles)
            lines.append(f"{marker} {profile.name} — {styles}")
    else:
        lines.append("هنوز پروفایلی ساخته نشده است." if language == "fa" else "No analysis profile has been created yet.")
    buttons = [[InlineKeyboardButton("➕ ساخت پروفایل" if language == "fa" else "➕ Create profile", callback_data="profile_create")]]
    buttons.append([InlineKeyboardButton("🏠 منوی اصلی" if language == "fa" else "🏠 Main menu", callback_data="home")])
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
