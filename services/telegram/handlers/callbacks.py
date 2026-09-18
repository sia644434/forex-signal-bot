from dataclasses import replace
from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..state import update_menu, get_user_state
from ..scanner import scan_market, format_scan, get_scanner_provider_manager
from ..journal import format_journal, add_entry, JournalEntry
from ..coach import explain_report
from ..tracker import list_tracking, stop_tracking
from ..i18n import t
from analysis.market_aware_engine import MarketAwareAnalysisEngine
from services.market_data.service import get_market_data_service
from core.errors import ApplicationError
from config.symbols import get_all_symbols, get_symbols_by_market, is_supported_symbol, normalize_symbol


ALLOWED_CALLBACKS = {
    "home", "analysis", "signals", "scanner", "coach", "journal", "journal_add",
    "signal_track", "signal_untrack", "signal_new", "settings",
    "settings_language", "settings_analysis_mode", "settings_risk", "settings_market",
    "settings_timeframe", "settings_notifications", "analysis_quick", "analysis_full",
    "language_fa", "language_en", "mode_manual", "mode_smart", "mode_hybrid",
    "risk_low", "risk_medium", "risk_high", "notifications_on", "notifications_off",
    "market_EURUSD", "market_GBPUSD", "market_USDJPY", "market_EURJPY",
    "timeframe_M5", "timeframe_M15", "timeframe_H1", "timeframe_H4",
}

ALLOWED_CALLBACKS |= {f"market_{symbol}" for symbol in get_all_symbols()}


def main_menu_keyboard(language: str = "fa"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Smart Analysis" if language == "en" else "📊 تحلیل هوشمند", callback_data="analysis"), InlineKeyboardButton("📡 Live Signal" if language == "en" else "📡 سیگنال زنده", callback_data="signals")],
        [InlineKeyboardButton("🔎 Market Scanner" if language == "en" else "🔎 اسکن بازار", callback_data="scanner"), InlineKeyboardButton("🧠 AI Coach", callback_data="coach")],
        [InlineKeyboardButton("📒 Trading Journal" if language == "en" else "📒 ژورنال معاملات", callback_data="journal"), InlineKeyboardButton("⚙️ Settings" if language == "en" else "⚙️ تنظیمات", callback_data="settings")],
    ])


def submenu_keyboard(menu: str, language: str = "fa"):
    if menu == "analysis": buttons = [[InlineKeyboardButton(t(language, "quick"), callback_data="analysis_quick")], [InlineKeyboardButton(t(language, "full"), callback_data="analysis_full")]]
    elif menu == "signals": buttons = [[InlineKeyboardButton(t(language, "new_signal"), callback_data="signal_new")], [InlineKeyboardButton(t(language, "track"), callback_data="signal_track")]]
    elif menu == "settings": buttons = [[InlineKeyboardButton(t(language, "language"), callback_data="settings_language")], [InlineKeyboardButton(t(language, "analysis_mode"), callback_data="settings_analysis_mode")], [InlineKeyboardButton(t(language, "risk"), callback_data="settings_risk")], [InlineKeyboardButton(t(language, "market"), callback_data="settings_market")], [InlineKeyboardButton(t(language, "timeframe"), callback_data="settings_timeframe")], [InlineKeyboardButton(t(language, "notifications"), callback_data="settings_notifications")]]
    else: buttons = []
    buttons.append([InlineKeyboardButton(t(language, "back"), callback_data="home")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(setting: str, language: str = "fa"):
    options = {
        "settings_language": [(t(language, "persian"), "language_fa"), (t(language, "english"), "language_en")],
        "settings_analysis_mode": [("Manual", "mode_manual"), ("Smart", "mode_smart"), ("Hybrid", "mode_hybrid")],
        "settings_risk": [("Low", "risk_low"), ("Medium", "risk_medium"), ("High", "risk_high")],
        "settings_market": [("Forex", "market_forex"), ("Crypto", "market_crypto"), ("Stocks", "market_stock"), ("Indices", "market_index"), ("Commodities", "market_commodity")],
        "settings_timeframe": [("M5", "timeframe_M5"), ("M15", "timeframe_M15"), ("H1", "timeframe_H1"), ("H4", "timeframe_H4")],
        "settings_notifications": [("🔔 On" if language == "en" else "🔔 فعال", "notifications_on"), ("🔕 Off" if language == "en" else "🔕 خاموش", "notifications_off")],
    }
    buttons = [[InlineKeyboardButton(text, callback_data=data)] for text, data in options.get(setting, [])]
    buttons.append([InlineKeyboardButton(t(language, "settings_back"), callback_data="settings")])
    return InlineKeyboardMarkup(buttons)


def market_symbols_keyboard(market: str, language: str = "fa"):
    symbols = get_symbols_by_market(market)
    buttons = []
    for index in range(0, len(symbols), 2):
        row = []
        for symbol in symbols[index:index + 2]:
            label = f"{symbol[:3]}/{symbol[3:]}" if market == "forex" and len(symbol) == 6 else symbol
            row.append(InlineKeyboardButton(label, callback_data=f"market_{symbol}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(t(language, "settings_back"), callback_data="settings_market")])
    return InlineKeyboardMarkup(buttons)


def _apply_setting(state, data: str) -> str | None:
    """Apply only canonical settings callbacks emitted by repository keyboards."""
    allowed = {
        "language_fa": lambda: setattr(state, "language", "fa") or "زبان فارسی",
        "language_en": lambda: setattr(state, "language", "en") or "English",
        "timeframe_M5": lambda: state.settings.__setitem__("timeframe", "M5") or "Timeframe M5",
        "timeframe_M15": lambda: state.settings.__setitem__("timeframe", "M15") or "Timeframe M15",
        "timeframe_H1": lambda: state.settings.__setitem__("timeframe", "H1") or "Timeframe H1",
        "timeframe_H4": lambda: state.settings.__setitem__("timeframe", "H4") or "Timeframe H4",
        "mode_manual": lambda: state.settings.__setitem__("analysis_mode", "manual") or "Analysis mode manual",
        "mode_smart": lambda: state.settings.__setitem__("analysis_mode", "smart") or "Analysis mode smart",
        "mode_hybrid": lambda: state.settings.__setitem__("analysis_mode", "hybrid") or "Analysis mode hybrid",
        "risk_low": lambda: state.settings.__setitem__("risk_level", "low") or "Risk low",
        "risk_medium": lambda: state.settings.__setitem__("risk_level", "medium") or "Risk medium",
        "risk_high": lambda: state.settings.__setitem__("risk_level", "high") or "Risk high",
        "notifications_on": lambda: state.settings.__setitem__("notifications_enabled", True) or "Notifications enabled",
        "notifications_off": lambda: state.settings.__setitem__("notifications_enabled", False) or "Notifications disabled",
    }
    action = allowed.get(data)
    if action:
        return action()
    if data.startswith("market_"):
        symbol = normalize_symbol(data.removeprefix("market_"))
        if is_supported_symbol(symbol) and f"market_{symbol}" in ALLOWED_CALLBACKS:
            state.settings["market_symbol"] = symbol
            return f"Market {symbol}"
    return None


def _tracking_callback(symbol: str, timeframe: str) -> str:
    return f"signal_untrack:{symbol}:{timeframe}"


def _parse_tracking_callback(data: str) -> tuple[str, str] | None:
    if not data.startswith("signal_untrack:"):
        return None
    parts = data.split(":")
    if len(parts) != 3 or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


async def _run_signal_report(state, market_data):
    symbol = state.settings.get("market_symbol", "EURUSD"); timeframe = state.settings.get("timeframe", "M15")
    candles = await market_data.get_candles_list(symbol, timeframe, 300)
    if not candles: raise RuntimeError("empty market data")
    return await MarketAwareAnalysisEngine(market_data=market_data).analyze(candles, symbol=symbol, timeframe=timeframe)


def _scanner_failure_text(language: str, error: Exception) -> str:
    if isinstance(error, ApplicationError) and error.details.get("required_environment"):
        required = ", ".join(error.details["required_environment"])
        if language == "en":
            return "❌ No market-data provider is configured on the server.\n\nAdd at least one real provider key to Railway environment variables:\n" + required
        return "❌ هیچ Provider داده بازار روی سرور فعال نیست.\n\nحداقل یکی از کلیدهای واقعی Provider را در Environment Variables ریل‌وی قرار بده:\n" + required
    return t(language, "scan_failed")


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query: return
    await query.answer()
    data = query.data or "home"
    if data not in ALLOWED_CALLBACKS and not data.startswith("signal_untrack:"):
        await query.edit_message_text("❌ درخواست نامعتبر است." if update.effective_user and get_user_state(update.effective_user.id).language == "fa" else "❌ Invalid request.")
        return
    user = update.effective_user; state = get_user_state(user.id) if user else None
    language = state.language if state else "fa"
    if user: update_menu(user.id, data)
    if data == "home": await query.edit_message_text(t(language, "home"), reply_markup=main_menu_keyboard(language)); return
    if data in ("analysis", "signals", "settings"):
        await query.edit_message_text(t(language, data), reply_markup=submenu_keyboard(data, language)); return
    if data == "scanner":
        if not state: return
        await query.edit_message_text("⏳ Scanning major markets..." if language == "en" else "⏳ در حال اسکن بازارهای اصلی...")
        try:
            timeframe = state.settings.get("timeframe", "M15"); results = await scan_market(timeframe=timeframe, provider_manager=get_scanner_provider_manager(context.application))
            await query.edit_message_text(format_scan(results, timeframe, language), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "retry"), callback_data="scanner")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        except Exception as error:
            await query.edit_message_text(_scanner_failure_text(language, error), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "retry"), callback_data="scanner")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        return
    if data == "coach":
        if not state: return
        await query.edit_message_text("⏳ Building AI coach explanation..." if language == "en" else "⏳ در حال ساخت توضیح مربی...")
        try:
            report = await _run_signal_report(state, get_market_data_service(context.application)); await query.edit_message_text(explain_report(report), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "retry"), callback_data="coach")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        except Exception:
            await query.edit_message_text("❌ AI Coach could not obtain valid analysis." if language == "en" else "❌ مربی نتوانست تحلیل معتبر دریافت کند.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="home")]]))
        return
    if data == "journal":
        if not user: return
        add_label = "➕ Add latest signal" if language == "en" else "➕ ثبت آخرین سیگنال معتبر"
        await query.edit_message_text(format_journal(user.id), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(add_label, callback_data="journal_add")], [InlineKeyboardButton(t(language, "back"), callback_data="home")]])); return
    if data == "journal_add":
        if not user: return
        active = list_tracking(user.id)
        if not active:
            text = "ℹ️ No valid active signal is available to add to the journal." if language == "en" else "ℹ️ هیچ سیگنال معتبر و فعالی برای ثبت در ژورنال وجود ندارد."
        else:
            item = active[0]
            add_entry(user.id, JournalEntry(symbol=item.symbol, side=item.signal, entry=item.entry, stop_loss=item.stop_loss, take_profit=item.take_profit_1, notes="Added from active signal", status="OPEN"))
            text = "✅ Latest active signal added to the journal." if language == "en" else "✅ آخرین سیگنال معتبر در ژورنال ثبت شد."
        await query.edit_message_text(text + "\n\n" + format_journal(user.id), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="home")]])); return
    if data == "signal_track":
        if not user: return
        active = list_tracking(user.id)
        if not active:
            text = "📈 <b>Signal Tracking</b>\n\nNo active signal is being tracked." if language == "en" else "📈 <b>پیگیری سیگنال</b>\n\nسیگنال فعالی برای پیگیری ندارید."
            buttons = [[InlineKeyboardButton(t(language, "new_signal"), callback_data="signal_new")], [InlineKeyboardButton(t(language, "back"), callback_data="signals")]]
        else:
            lines = ["📈 <b>Tracked Signals</b>", ""]
            buttons = []
            for item in active:
                lines.append(f"• {escape(str(item.symbol), quote=False)}/{escape(str(item.timeframe), quote=False)} → <b>{escape(str(item.last_signal), quote=False)}</b> | {escape(str(item.status), quote=False)} | {escape(str(item.last_price) if item.last_price is not None else '—', quote=False)}")
                buttons.append([InlineKeyboardButton(("⛔ Stop " if language == "en" else "⛔ توقف ") + f"{item.symbol}/{item.timeframe}", callback_data=_tracking_callback(item.symbol, item.timeframe))])
            buttons.extend([[InlineKeyboardButton("🔄 Refresh" if language == "en" else "🔄 بروزرسانی", callback_data="signal_track")], [InlineKeyboardButton(t(language, "back"), callback_data="signals")]])
            text = "\n".join(lines)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons)); return
    if data == "signal_untrack":
        # Legacy callback: only stop the currently selected track if it actually exists.
        if user and state:
            symbol = state.settings.get("market_symbol", "EURUSD")
            timeframe = state.settings.get("timeframe", "M15")
            removed = stop_tracking(user.id, symbol, timeframe)
            text = ("⛔ Tracking stopped." if removed else "ℹ️ No active tracking found.") if language == "en" else ("⛔ پیگیری متوقف شد." if removed else "ℹ️ سیگنال فعالی پیدا نشد.")
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="signals")]]))
        return
    parsed_tracking = _parse_tracking_callback(data)
    if parsed_tracking is not None:
        if not user:
            return
        symbol, timeframe = parsed_tracking
        owned = {(item.symbol, item.timeframe) for item in list_tracking(user.id)}
        if (symbol, timeframe) not in owned:
            await query.edit_message_text("❌ درخواست پیگیری نامعتبر است." if language == "fa" else "❌ Invalid tracking request.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="signals")]]))
            return
        removed = stop_tracking(user.id, symbol, timeframe)
        text = ("⛔ Tracking stopped." if removed else "ℹ️ No active tracking found.") if language == "en" else ("⛔ پیگیری متوقف شد." if removed else "ℹ️ سیگنال فعالی پیدا نشد.")
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "back"), callback_data="signals")]]))
        return
    if data in {"market_forex", "market_crypto", "market_stock", "market_index", "market_commodity"}:
        market = data.removeprefix("market_")
        await query.edit_message_text("📊 Select market symbol" if language == "en" else "📊 نماد بازار را انتخاب کنید", reply_markup=market_symbols_keyboard(market, language))
        return
    if data.startswith("settings_"):
        await query.edit_message_text(t(language, "settings"), reply_markup=settings_keyboard(data, language)); return
    if data in {"analysis_quick", "analysis_full"}:
        if state: state.settings["analysis_mode"] = "smart" if data == "analysis_quick" else "full"
        await query.edit_message_text("📊 Analysis mode selected.\n\nUse New Signal to run live analysis." if language == "en" else "📊 حالت تحلیل انتخاب شد.\n\nبرای اجرای تحلیل زنده، روی سیگنال جدید بزنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "new_signal"), callback_data="signal_new")], [InlineKeyboardButton(t(language, "back"), callback_data="analysis")]])); return
    if data == "signal_new":
        from .signal import signal_handler
        await signal_handler(update, context); return
    message = _apply_setting(state, data) if state else None
    if message is None:
        await query.edit_message_text("❌ درخواست تنظیمات نامعتبر است." if language == "fa" else "❌ Invalid settings request.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "settings_back"), callback_data="settings")]]))
        return
    if data in {"language_fa", "language_en"}:
        language = state.language
        await query.edit_message_text(t(language, "home"), reply_markup=main_menu_keyboard(language)); return
    await query.edit_message_text(f"✅ {message}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(language, "settings_back"), callback_data="settings")]]))
