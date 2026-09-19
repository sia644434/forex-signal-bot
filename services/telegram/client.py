from __future__ import annotations

from telegram import BotCommand
from telegram.ext import Application
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MAX_INSTANCES,
    EVENT_JOB_MISSED,
)

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

_SCANNER_SCHEDULER_EVENTS = (
    EVENT_JOB_EXECUTED
    | EVENT_JOB_ERROR
    | EVENT_JOB_MISSED
    | EVENT_JOB_MAX_INSTANCES
)


def _log_scanner_scheduler_event(event) -> None:
    """Log scheduler-level outcomes for the continuous scanner job."""
    if getattr(event, "job_id", None) != AUTO_SCANNER_JOB_NAME:
        return

    code = getattr(event, "code", None)
    if code == EVENT_JOB_EXECUTED:
        logger.info(
            "Automatic scanner scheduler event: executed job=%s scheduled=%s",
            event.job_id,
            getattr(event, "scheduled_run_time", None),
        )
    elif code == EVENT_JOB_ERROR:
        logger.error(
            "Automatic scanner scheduler event: ERROR job=%s scheduled=%s exception=%r",
            event.job_id,
            getattr(event, "scheduled_run_time", None),
            getattr(event, "exception", None),
        )
    elif code == EVENT_JOB_MISSED:
        logger.error(
            "Automatic scanner scheduler event: MISSED job=%s scheduled=%s",
            event.job_id,
            getattr(event, "scheduled_run_time", None),
        )
    elif code == EVENT_JOB_MAX_INSTANCES:
        logger.error(
            "Automatic scanner scheduler event: MAX_INSTANCES job=%s scheduled=%s",
            event.job_id,
            getattr(event, "scheduled_run_times", None),
        )


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

    def _schedule_auto_scanner(self) -> None:
        """Start the continuous multi-timeframe opportunity scanner."""
        if not auto_scanner_enabled():
            logger.info("Continuous automatic scanner is disabled.")
            return
        job_queue = self.application.job_queue
        if job_queue is None:
            raise RuntimeError("Telegram JobQueue is unavailable; automatic market scanning cannot run.")
        interval = auto_scanner_interval_seconds()
        job_queue.scheduler.add_listener(
            _log_scanner_scheduler_event,
            _SCANNER_SCHEDULER_EVENTS,
        )
        job = job_queue.run_repeating(
            run_continuous_market_scan,
            interval=interval,
            first=5,
            name=AUTO_SCANNER_JOB_NAME,
            job_kwargs={
                "max_instances": 1,
                "coalesce": True,
                "misfire_grace_time": max(30, interval * 2),
            },
        )
        logger.info(
            "Continuous multi-timeframe scanner scheduled: job=%s interval=%ss first=5s next_run=%s",
            AUTO_SCANNER_JOB_NAME,
            interval,
            getattr(job, "next_t", getattr(job, "next_run_time", None)),
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
