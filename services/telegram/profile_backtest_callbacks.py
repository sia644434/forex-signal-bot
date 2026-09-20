from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config.symbols import normalize_timeframe
from profiles import build_execution_context, context_payload, list_profiles
from services.market_data.service import MarketDataService
from services.telegram.scanner import _configured_scan_symbols, get_scanner_provider_manager
from worker.contracts import JobRequest


_PERIODS = {
    "300": 300,
    "1000": 1000,
    "3000": 3000,
}
_TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")


def _selection(state) -> dict:
    raw = state.settings.get("profile_backtest_selection", {})
    return dict(raw) if isinstance(raw, dict) else {}


def _save_selection(state, **changes) -> dict:
    selection = _selection(state)
    selection.update(changes)
    state.settings["profile_backtest_selection"] = selection
    return selection


def _profile_or_none(state, profile_id: str):
    return next((p for p in list_profiles(state) if p.profile_id == profile_id), None)


def _symbols(profile, state) -> tuple[str, ...]:
    configured = tuple(profile.symbols) if profile.symbols else tuple(_configured_scan_symbols())
    return tuple(dict.fromkeys(configured))


def _menu_text(profile, selection, language: str) -> str:
    symbol = selection.get("symbol", "—")
    timeframe = selection.get("timeframe", "M15")
    bars = selection.get("bars", "1000")
    if language == "fa":
        return (
            f"🧪 <b>بک‌تست پروفایل</b>\n\n"
            f"پروفایل: <b>{profile.name}</b>\n"
            f"نماد: <b>{symbol}</b>\n"
            f"تایم‌فریم: <b>{timeframe}</b>\n"
            f"داده: <b>{bars} کندل اخیر</b>\n\n"
            "ابتدا نماد، تایم‌فریم و تعداد کندل را انتخاب کنید."
        )
    return (
        f"🧪 <b>Profile Backtest</b>\n\n"
        f"Profile: <b>{profile.name}</b>\n"
        f"Symbol: <b>{symbol}</b>\n"
        f"Timeframe: <b>{timeframe}</b>\n"
        f"Data: <b>last {bars} candles</b>\n\n"
        "Select the symbol, timeframe and candle range first."
    )


def _keyboard(profile, state, language: str):
    selection = _selection(state)
    rows = []
    for symbol in _symbols(profile, state)[:24]:
        mark = "✅ " if symbol == selection.get("symbol") else ""
        rows.append([InlineKeyboardButton(f"{mark}{symbol}", callback_data=f"bt_symbol:{profile.profile_id}:{symbol}")])
    tf_rows = []
    for timeframe in _TIMEFRAMES:
        mark = "✅ " if timeframe == selection.get("timeframe", "M15") else ""
        tf_rows.append(InlineKeyboardButton(f"{mark}{timeframe}", callback_data=f"bt_tf:{profile.profile_id}:{timeframe}"))
    rows.append(tf_rows)
    bars_rows = []
    for bars in _PERIODS:
        mark = "✅ " if bars == str(selection.get("bars", "1000")) else ""
        bars_rows.append(InlineKeyboardButton(f"{mark}{bars}", callback_data=f"bt_bars:{profile.profile_id}:{bars}"))
    rows.append(bars_rows)
    rows.append([InlineKeyboardButton(
        "▶️ شروع بک‌تست" if language == "fa" else "▶️ Start backtest",
        callback_data=f"bt_start:{profile.profile_id}",
    )])
    rows.append([InlineKeyboardButton(
        "📊 آخرین نتیجه" if language == "fa" else "📊 Last result",
        callback_data=f"bt_result:{profile.profile_id}",
    )])
    rows.append([InlineKeyboardButton(
        "🔙 بازگشت به پروفایل" if language == "fa" else "🔙 Back to profile",
        callback_data=f"profile_open:{profile.profile_id}",
    )])
    return InlineKeyboardMarkup(rows)


def _result_text(result: dict, profile, language: str) -> str:
    if language == "fa":
        return (
            f"🧪 <b>نتیجه بک‌تست</b>\n\n"
            f"پروفایل: <b>{profile.name}</b>\n"
            f"نسخه پروفایل: <b>{result.get('profile_version', profile.version)}</b>\n"
            f"کندل‌ها: <b>{result.get('bars', 0)}</b>\n"
            f"معاملات: <b>{result.get('trades', 0)}</b>\n"
            f"برد: <b>{result.get('wins', 0)}</b> | باخت: <b>{result.get('losses', 0)}</b>\n"
            f"نرخ برد: <b>{float(result.get('win_rate', 0.0)) * 100:.2f}%</b>\n"
            f"بازده: <b>{float(result.get('total_return', 0.0)) * 100:.2f}%</b>\n"
            f"سرمایه نهایی: <b>{float(result.get('final_equity', 1.0)):.4f}</b>"
        )
    return (
        f"🧪 <b>Backtest Result</b>\n\n"
        f"Profile: <b>{profile.name}</b>\n"
        f"Profile version: <b>{result.get('profile_version', profile.version)}</b>\n"
        f"Bars: <b>{result.get('bars', 0)}</b>\n"
        f"Trades: <b>{result.get('trades', 0)}</b>\n"
        f"Wins: <b>{result.get('wins', 0)}</b> | Losses: <b>{result.get('losses', 0)}</b>\n"
        f"Win rate: <b>{float(result.get('win_rate', 0.0)) * 100:.2f}%</b>\n"
        f"Return: <b>{float(result.get('total_return', 0.0)) * 100:.2f}%</b>\n"
        f"Final equity: <b>{float(result.get('final_equity', 1.0)):.4f}</b>"
    )


async def handle_profile_backtest_callback(query, state, language: str, data: str, application) -> bool:
    if not data.startswith("bt_"):
        return False
    parts = data.split(":")
    if len(parts) < 2:
        return True
    profile_id = parts[1]
    profile = _profile_or_none(state, profile_id)
    if profile is None:
        await query.edit_message_text("❌ پروفایل پیدا نشد." if language == "fa" else "❌ Profile not found.")
        return True

    if data.startswith("bt_open:"):
        _save_selection(state, profile_id=profile_id, symbol=_symbols(profile, state)[0] if _symbols(profile, state) else "—", timeframe=profile.timeframes[0] if profile.timeframes else "M15", bars="1000")
        await query.edit_message_text(_menu_text(profile, _selection(state), language), parse_mode="HTML", reply_markup=_keyboard(profile, state, language))
        return True

    if data.startswith("bt_symbol:") and len(parts) >= 3:
        _save_selection(state, profile_id=profile_id, symbol=parts[2])
        await query.edit_message_reply_markup(reply_markup=_keyboard(profile, state, language))
        return True

    if data.startswith("bt_tf:") and len(parts) >= 3:
        timeframe = parts[2].upper()
        if timeframe not in _TIMEFRAMES:
            return True
        _save_selection(state, profile_id=profile_id, timeframe=timeframe)
        await query.edit_message_reply_markup(reply_markup=_keyboard(profile, state, language))
        return True

    if data.startswith("bt_bars:") and len(parts) >= 3:
        if parts[2] not in _PERIODS:
            return True
        _save_selection(state, profile_id=profile_id, bars=parts[2])
        await query.edit_message_reply_markup(reply_markup=_keyboard(profile, state, language))
        return True

    if data.startswith("bt_result:"):
        result = state.settings.get("profile_backtest_last_result")
        if not isinstance(result, dict) or result.get("profile_id") != profile_id:
            await query.edit_message_text(
                "ℹ️ هنوز نتیجه‌ای برای این پروفایل ثبت نشده است." if language == "fa" else "ℹ️ No backtest result is stored for this profile.",
                reply_markup=_keyboard(profile, state, language),
            )
            return True
        await query.edit_message_text(_result_text(result, profile, language), parse_mode="HTML", reply_markup=_keyboard(profile, state, language))
        return True

    if data.startswith("bt_start:"):
        selection = _selection(state)
        symbol = str(selection.get("symbol", "")).strip()
        timeframe = str(selection.get("timeframe", "M15")).upper()
        bars = int(selection.get("bars", "1000"))
        if not symbol:
            await query.edit_message_text("⚠️ ابتدا یک نماد انتخاب کنید." if language == "fa" else "⚠️ Select a symbol first.", reply_markup=_keyboard(profile, state, language))
            return True
        try:
            context = build_execution_context(
                profile,
                "BACKTEST",
                symbols=[symbol],
                timeframes=[timeframe],
                user_id=str(query.from_user.id),
                requested_capabilities=["profile_analysis"],
            )
            provider_manager = get_scanner_provider_manager(application)
            market_data = MarketDataService(provider_manager=provider_manager)
            candles = await market_data.get_candles_list(symbol=symbol, timeframe=normalize_timeframe(timeframe), limit=bars)
            if len(candles) < 60:
                raise ValueError(f"Only {len(candles)} candles are available; at least 60 are required.")
            raw = [
                {
                    "timestamp": candle.timestamp.isoformat(),
                    "open": float(candle.open),
                    "high": float(candle.high),
                    "low": float(candle.low),
                    "close": float(candle.close),
                    "volume": float(getattr(candle, "volume", 0.0) or 0.0),
                }
                for candle in candles
            ]
            request = JobRequest(
                job_id=f"profile-backtest-{uuid4().hex}",
                job_type="profile_backtest",
                payload={
                    "candles": raw,
                    **context_payload(context),
                    "requested_bars": bars,
                },
                priority=70,
                timeout_seconds=3600,
            )
            worker_service = application.services.services.get("worker_processing")
            if worker_service is None:
                raise RuntimeError("Worker processing service is unavailable.")
            await query.edit_message_text(
                "⏳ بک‌تست در حال ارسال به PC Worker است..." if language == "fa" else "⏳ Submitting backtest to the PC Worker...",
                parse_mode="HTML",
            )
            result = await worker_service.submit(request)
            if result.status != "COMPLETED":
                status_text = {
                    "WORKER_OFFLINE": "PC Worker هنوز متصل/آماده نیست.",
                    "RUNNING": "بک‌تست در حال اجراست.",
                    "PENDING": "بک‌تست در صف قرار گرفت.",
                }.get(result.status, f"وضعیت: {result.status}")
                if language == "en":
                    status_text = {
                        "WORKER_OFFLINE": "PC Worker is not connected/ready yet.",
                        "RUNNING": "Backtest is running.",
                        "PENDING": "Backtest is queued.",
                    }.get(result.status, f"Status: {result.status}")
                await query.edit_message_text(
                    f"ℹ️ {status_text}",
                    reply_markup=_keyboard(profile, state, language),
                )
                return True
            output = dict(result.output or {})
            state.settings["profile_backtest_last_result"] = {
                key: value for key, value in output.items()
                if key not in {"results"}
            }
            await query.edit_message_text(_result_text(output, profile, language), parse_mode="HTML", reply_markup=_keyboard(profile, state, language))
        except Exception as error:
            await query.edit_message_text(
                ("❌ بک‌تست اجرا نشد.\n\n" + str(error)) if language == "fa" else ("❌ Backtest could not be started.\n\n" + str(error)),
                reply_markup=_keyboard(profile, state, language),
            )
        return True

    return False
