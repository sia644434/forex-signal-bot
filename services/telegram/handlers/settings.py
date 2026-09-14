from telegram import Update
from telegram.ext import ContextTypes

from services.telegram.state import get_user_state


async def settings_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show the user's actual current Telegram settings."""
    if not update.message or not update.effective_user:
        return
    state = get_user_state(update.effective_user.id)
    language = state.language
    symbol = state.settings.get("market_symbol", "EURUSD")
    timeframe = state.settings.get("timeframe", "M15")
    mode = state.settings.get("analysis_mode", "smart")
    risk = state.settings.get("risk_level", "medium")
    notifications = state.settings.get("notifications_enabled", True)

    if language == "en":
        mode_label = {"manual": "Manual", "smart": "Smart", "hybrid": "Hybrid", "full": "Full"}.get(mode, str(mode))
        risk_label = str(risk).title()
        notification_label = "On" if notifications else "Off"
        text = (
            "⚙️ <b>Current settings</b>\n\n"
            f"🌐 Language: English\n"
            f"📡 Market: {symbol}\n"
            f"⏱ Timeframe: {timeframe}\n"
            f"🧠 Analysis mode: {mode_label}\n"
            f"⚖️ Risk level: {risk_label}\n"
            f"🔔 Notifications: {notification_label}"
        )
    else:
        mode_label = {"manual": "دستی", "smart": "هوشمند", "hybrid": "ترکیبی", "full": "کامل"}.get(mode, str(mode))
        risk_label = {"low": "کم", "medium": "متوسط", "high": "زیاد"}.get(str(risk), str(risk))
        notification_label = "فعال" if notifications else "خاموش"
        text = (
            "⚙️ <b>تنظیمات فعلی</b>\n\n"
            f"🌐 زبان: فارسی\n"
            f"📡 بازار: {symbol}\n"
            f"⏱ تایم‌فریم: {timeframe}\n"
            f"🧠 حالت تحلیل: {mode_label}\n"
            f"⚖️ سطح ریسک: {risk_label}\n"
            f"🔔 اعلان‌ها: {notification_label}"
        )
    await update.message.reply_text(text, parse_mode="HTML")
