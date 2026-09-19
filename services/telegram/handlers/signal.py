from __future__ import annotations

import html
import logging

from telegram import Update
from telegram.ext import ContextTypes

from analysis.market_aware_engine import MarketAwareAnalysisEngine
from services.market_data.service import get_market_data_service
from services.telegram.state import get_user_state
from services.telegram.tracker import track_report
from services.telegram.market_session import OPEN, evaluate_market_status, is_market_weekend_closed

logger = logging.getLogger(__name__)
DEFAULT_SYMBOL = "EURUSD"
DEFAULT_TIMEFRAME = "M15"
DEFAULT_CANDLE_LIMIT = 300
_SIGNAL_LABELS = {
    "STRONG_BUY": "🟢 خرید قوی",
    "BUY": "🟢 خرید",
    "WAIT": "🟡 انتظار",
    "NO_TRADE": "⛔ عدم معامله",
    "SELL": "🔴 فروش",
    "STRONG_SELL": "🔴 فروش قوی",
}
_EXECUTABLE_SIGNALS = {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}


def _setting_value(state, key: str, default: str) -> str:
    value = state.settings.get(key, default)
    return value if isinstance(value, str) and value.strip() else default


def _escape(value: object) -> str:
    return html.escape(str(value), quote=False)


def _format_price(value: float | None) -> str:
    return "—" if value is None else f"{value:.5f}"


def _format_number(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def _format_provider_diagnostics(exc: Exception) -> str:
    """Expose safe provider failure reasons without secrets or raw payloads."""
    details = getattr(exc, "details", None)
    failures = details.get("failures") if isinstance(details, dict) else None
    if not isinstance(failures, list):
        return ""
    latest: dict[str, str] = {}
    for item in failures:
        if not isinstance(item, dict):
            continue
        provider = str(item.get("provider") or "").strip()
        if not provider:
            continue
        message = str(item.get("message") or "").strip()
        nested = item.get("details")
        if isinstance(nested, dict):
            reason = str(nested.get("reason") or nested.get("message") or "").strip()
            if reason and reason not in message:
                message = f"{message}: {reason}" if message else reason
        if not message:
            message = str(item.get("error_type") or "unknown failure").strip()
        latest[provider] = message[:180]
    if not latest:
        return ""
    lines = ["", "🔎 <b>وضعیت تأمین‌کننده‌ها</b>"]
    for provider, message in list(latest.items())[:4]:
        lines.append(f"• {_escape(provider)}: {_escape(message)}")
    return "\n".join(lines)


def _format_signal_failure(exc: Exception, symbol: str, timeframe: str) -> str:
    """Turn internal signal-generation failures into actionable user-facing messages."""
    detail = str(exc).lower()

    if is_market_weekend_closed(symbol=symbol):
        return (
            "🔴 <b>بازار بسته است</b>\n\n"
            f"💱 بازار: <b>{_escape(symbol)}</b>\n"
            f"⏱ تایم‌فریم: <b>{_escape(timeframe)}</b>\n\n"
            "🗓 بازار فارکس در تعطیلات آخر هفته قرار دارد و فعلاً داده زنده جدیدی "
            "برای تولید سیگنال معاملاتی وجود ندارد.\n\n"
            "⏳ با باز شدن بازار دوباره درخواست <b>/signal</b> را ارسال کنید.\n"
            "⛔ در زمان بسته بودن بازار هیچ سیگنال ساختگی یا مبتنی بر داده قدیمی صادر نمی‌شود."
        )

    if "not fresh enough" in detail or "status=reject" in detail or "status=stale" in detail:
        return (
            "🟠 <b>سیگنال فعلاً قابل تولید نیست</b>\n\n"
            f"💱 بازار: <b>{_escape(symbol)}</b>\n"
            f"⏱ تایم‌فریم: <b>{_escape(timeframe)}</b>\n\n"
            "📉 آخرین داده دریافتی به اندازه کافی تازه نیست و برای تحلیل اجرایی "
            "قابل اعتماد محسوب نمی‌شود.\n\n"
            "⛔ برای جلوگیری از سیگنال اشتباه، داده قدیمی استفاده نمی‌شود. "
            "لطفاً بعداً دوباره تلاش کنید."
        )

    if "all market data providers failed" in detail:
        return (
            "🟠 <b>داده بازار در دسترس نیست</b>\n\n"
            f"💱 بازار: <b>{_escape(symbol)}</b>\n"
            f"⏱ تایم‌فریم: <b>{_escape(timeframe)}</b>\n\n"
            "📡 سرویس‌های تأمین داده بازار در حال حاضر داده معتبر ارائه نکردند.\n\n"
            "⛔ هیچ سیگنالی بدون داده معتبر صادر نمی‌شود. لطفاً چند دقیقه بعد دوباره تلاش کنید."
            + _format_provider_diagnostics(exc)
        )

    if "unsupported market symbol" in detail:
        return (
            "⚠️ <b>نماد انتخاب‌شده پشتیبانی نمی‌شود</b>\n\n"
            f"نماد <b>{_escape(symbol)}</b> در پیکربندی فعلی پشتیبانی نشده است.\n"
            "لطفاً نماد بازار را از گزینه‌های پشتیبانی‌شده انتخاب کنید."
        )

    if "timeout" in detail or "timed out" in detail:
        return (
            "🟠 <b>دریافت داده بازار زمان‌بر شد</b>\n\n"
            f"برای <b>{_escape(symbol)}/{_escape(timeframe)}</b> پاسخ داده به‌موقع دریافت نشد.\n\n"
            "⏳ لطفاً چند لحظه بعد دوباره تلاش کنید."
        )

    return (
        "❌ <b>تولید سیگنال انجام نشد</b>\n\n"
        f"💱 بازار: <b>{_escape(symbol)}</b>\n"
        f"⏱ تایم‌فریم: <b>{_escape(timeframe)}</b>\n\n"
        "داده یا یکی از مراحل تحلیل نتیجه معتبر تولید نکرد. "
        "برای جلوگیری از نتیجه نادرست، سیگنال صادر نشد.\n\n"
        "🔄 لطفاً چند لحظه بعد دوباره تلاش کنید."
    )


def _format_signal(report, symbol: str, timeframe: str) -> str:
    signal = str(report.signal).upper()
    confidence = max(0.0, min(1.0, float(report.confidence))) * 100.0
    lines = [
        "📡 <b>سیگنال جدید</b>", "",
        f"💱 بازار: <b>{_escape(symbol)}</b>",
        f"⏱ تایم‌فریم: <b>{_escape(timeframe)}</b>",
        f"📌 تصمیم: <b>{_escape(_SIGNAL_LABELS.get(signal, signal))}</b>",
        f"📊 امتیاز: <b>{_format_number(report.score)}</b>",
        f"🎯 اطمینان: <b>{confidence:.1f}%</b>",
        f"🏆 کیفیت معامله: <b>{_escape(report.trade_grade)}</b> ({_format_number(report.trade_quality)}/100)",
        f"📈 روند: <b>{_escape(report.trend)}</b>",
        f"🧭 ساختار: <b>{_escape(report.structure)}</b>", "",
        "💰 <b>سطوح مدیریت معامله</b>",
        f"ورود: <b>{_format_price(report.entry_price)}</b>",
        f"حد ضرر: <b>{_format_price(report.stop_loss)}</b>",
        f"هدف ۱: <b>{_format_price(report.take_profit_1)}</b>",
        f"هدف ۲: <b>{_format_price(report.take_profit_2)}</b>",
        f"هدف ۳: <b>{_format_price(report.take_profit_3)}</b>",
        f"⚖️ نسبت ریسک/بازده: <b>{_format_number(report.risk_reward)}</b>",
    ]
    if getattr(report, "portfolio_risk_blocked", False):
        lines.extend(["", "⛔ <b>محدودیت پرتفوی</b>"])
        flags = getattr(report, "portfolio_risk_flags", []) or ["RISK_LIMIT"]
        lines.extend(f"• {_escape(flag)}" for flag in flags[:5])
    if report.warnings:
        lines.extend(["", "⚠️ <b>هشدارها</b>"])
        lines.extend(f"• {_escape(warning)}" for warning in report.warnings[:5])
    if report.reasons:
        lines.extend(["", "🧠 <b>دلایل اصلی</b>"])
        lines.extend(f"• {_escape(reason)}" for reason in report.reasons[:6])
    if signal in {"WAIT", "NO_TRADE"}:
        lines.extend(["", "ℹ️ شرایط فعلی برای ورود مطمئن کافی نیست؛ مدیریت سرمایه را رعایت کنید."])
    return "\n".join(lines)


async def signal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch real market candles and run market-aware risk analysis."""
    source_message = update.message or (update.callback_query.message if update.callback_query else None)
    if source_message is None:
        return
    if update.callback_query:
        await update.callback_query.answer()
    user_id = update.effective_user.id if update.effective_user else None
    state = get_user_state(user_id) if user_id is not None else None
    symbol = _setting_value(state, "market_symbol", DEFAULT_SYMBOL) if state else DEFAULT_SYMBOL
    timeframe = _setting_value(state, "timeframe", DEFAULT_TIMEFRAME) if state else DEFAULT_TIMEFRAME
    status_message = await source_message.reply_text(
        f"⏳ در حال دریافت داده زنده {symbol}/{timeframe} و اجرای تحلیل کامل..."
    )
    candles = []
    try:
        market_data = get_market_data_service(context.application)
        candles = await market_data.get_candles_list(symbol=symbol, timeframe=timeframe, limit=DEFAULT_CANDLE_LIMIT)
        if not candles:
            raise RuntimeError("empty market data")

        market_status = evaluate_market_status(candles, timeframe, symbol=symbol)
        if market_status.status != OPEN:
            status_label = {
                "CLOSED": "بازار بسته است",
                "STALE": "داده بازار قدیمی است",
                "NO_DATA": "داده معتبر بازار در دسترس نیست",
            }.get(market_status.status, "وضعیت بازار نامعتبر است")
            await status_message.edit_text(
                "⛔ <b>عدم معامله</b>\n\n"
                f"بازار {_escape(symbol)}/{_escape(timeframe)}: {html.escape(status_label, quote=False)}.\n"
                "تا زمانی که داده معتبر و بازار قابل معامله نباشد، تحلیل اجرایی و Tracking ایجاد نمی‌شود.",
                parse_mode="HTML",
            )
            return

        report = await MarketAwareAnalysisEngine(market_data=market_data).analyze(candles, symbol=symbol, timeframe=timeframe)
        if user_id is not None and str(report.signal).upper() in _EXECUTABLE_SIGNALS:
            track_report(user_id, symbol, timeframe, report)
        await status_message.edit_text(_format_signal(report, symbol, timeframe), parse_mode="HTML")
    except Exception as exc:
        logger.exception("Signal generation failed for %s/%s", symbol, timeframe, exc_info=exc)
        await status_message.edit_text(
            _format_signal_failure(exc, symbol, timeframe),
            parse_mode="HTML",
        )
