from __future__ import annotations

from telegram import BotCommand
from telegram.ext import Application

from core.logger import setup_logger
from services.market_data.service import install_market_data_service
from services.telegram.router import register_routes
from services.telegram.tracker_job import refresh_all_tracked_signals, tracker_refresh_interval_seconds


logger = setup_logger()


class TelegramClient:
    """Telegram bot client with explicit startup diagnostics."""

    def __init__(self, token: str) -> None:
        self.application = (
            Application
            .builder()
            .token(token)
            .build()
        )

        self.market_data_service = install_market_data_service(self.application)
        register_routes(self.application)
        logger.info("Telegram client configured and routes registered.")

    def _schedule_tracker_refresh(self) -> None:
        """Start the durable active-signal refresh loop required by tracking."""
        job_queue = self.application.job_queue
        if job_queue is None:
            raise RuntimeError("Telegram JobQueue is unavailable; active signal tracking cannot run.")
        interval = tracker_refresh_interval_seconds()
        job_queue.run_repeating(
            refresh_all_tracked_signals,
            interval=interval,
            first=interval,
            name="telegram-tracker-refresh",
        )
        logger.info("Telegram tracker refresh scheduled every %s seconds.", interval)

    async def start(self) -> None:
        """Initialize the bot, validate startup dependencies, then start polling."""
        logger.info("Starting Telegram client...")

        await self.application.initialize()
        logger.info("Telegram application initialized.")

        bot = self.application.bot
        me = await bot.get_me()
        logger.info(
            "Telegram authentication successful: @%s (id=%s).",
            me.username,
            me.id,
        )

        await bot.set_my_commands([
            BotCommand("start", "شروع ربات"),
            BotCommand("help", "راهنما"),
            BotCommand("signal", "دریافت سیگنال"),
            BotCommand("status", "وضعیت سیستم"),
            BotCommand("settings", "تنظیمات"),
        ])
        logger.info("Telegram commands registered.")

        updater = self.application.updater
        if updater is None:
            raise RuntimeError("Telegram updater is unavailable; polling cannot start.")

        # Validate and schedule background tracking before the application is
        # marked running. A startup dependency failure must not leave a
        # partially-started Telegram runtime behind.
        self._schedule_tracker_refresh()

        await self.application.start()
        logger.info("Telegram application runtime started.")

        await updater.start_polling()
        logger.info("Telegram polling started successfully.")
        logger.info("Telegram bot is online.")

    async def stop(self) -> None:
        """Stop polling and shut down the Telegram application."""
        logger.info("Stopping Telegram client...")

        updater = self.application.updater
        if updater is not None and updater.running:
            await updater.stop()

        if self.application.running:
            await self.application.stop()

        await self.application.shutdown()
        logger.info("Telegram bot stopped.")
