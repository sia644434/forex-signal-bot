from telegram import Update
from telegram.ext import ContextTypes

from services.telegram.scanner import _provider_readiness


async def status_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.message:
        return
    readiness = _provider_readiness()
    configured = len(readiness.configured_providers)
    if configured:
        provider_status = f"Market data: Ready ({configured} provider(s) configured)"
        state = "🟢"
    else:
        provider_status = "Market data: Not configured"
        state = "🟠"
    await update.message.reply_text(
        f"{state} وضعیت سیستم\n\n"
        "Telegram: Online\n"
        "Application: Running\n"
        f"{provider_status}"
    )
