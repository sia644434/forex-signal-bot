from __future__ import annotations

import asyncio
from types import SimpleNamespace

from telegram import BotCommand
from telegram.ext import Application
from core.logger import setup_logger
from services.market_data.service import install_market_data_service
from services.telegram.router import register_routes
from services.telegram.tracker_job import refresh_all_tracked_signals, tracker_refresh_interval_seconds
from services.telegram.auto_scanner import (
    AUTO_SCANNER_JOB_NAME,
    auto_scanner_enabled,
    auto_scanner_interval_seconds,
    run_continuous_market_scan,
)


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

    async def _run_auto_scanner_loop(self, interval: int) -> None:
        """Own the continuous scanner lifecycle independently of APScheduler.

        The scanner is a critical long-running loop. Keeping it on the
        application's asyncio lifecycle avoids silently losing executions when
        a scheduler job is paused, missed, or otherwise unavailable.
        """
        logger.info(
            "Continuous scanner loop started: interval=%ss first_run=5s",
            interval,
        )
        try:
            await asyncio.sleep(5)
            while True:
                await run_continuous_market_scan(
                    SimpleNamespace(
                        bot=self.application.bot,
                        application=self.application,
                    )
                )
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Continuous scanner loop cancelled.")
            raise
        except Exception:
            logger.exception("Continuous scanner loop stopped unexpectedly.")
            raise

    def _schedule_auto_scanner(self) -> None:
        """Start the continuous multi-timeframe opportunity scanner."""
        if not auto_scanner_enabled():
            logger.info("Continuous automatic scanner is disabled.")
            return
        interval = auto_scanner_interval_seconds()
        logger.info(
            "Continuous multi-timeframe scanner configured: interval=%ss first_run=5s",
            interval,
        )

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
        self._schedule_auto_scanner()

        await self.application.start()
        logger.info("Telegram application runtime started.")

        if auto_scanner_enabled():
            interval = auto_scanner_interval_seconds()
            self.application.create_task(
                self._run_auto_scanner_loop(interval),
                name=AUTO_SCANNER_JOB_NAME,
            )
            logger.info(
                "Continuous scanner loop started after application startup: interval=%ss",
                interval,
            )

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
