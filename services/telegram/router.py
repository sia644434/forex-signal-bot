from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from services.telegram.access import authorized
from services.telegram.handlers.start import start_handler
from services.telegram.handlers.help import help_handler
from services.telegram.handlers.status import status_handler
from services.telegram.handlers.signal import signal_handler
from services.telegram.handlers.settings import settings_handler
from services.telegram.handlers.profiles import profiles_handler
from services.telegram.handlers.callbacks import menu_callback_handler


def register_routes(app: Application) -> None:
    """Register Telegram routes behind the centralized access-control boundary."""
    app.add_handler(CommandHandler("start", authorized(start_handler)))
    app.add_handler(CommandHandler("help", authorized(help_handler)))
    app.add_handler(CommandHandler("status", authorized(status_handler)))
    app.add_handler(CommandHandler("signal", authorized(signal_handler)))
    app.add_handler(CommandHandler("settings", authorized(settings_handler)))
    app.add_handler(CommandHandler("profiles", authorized(profiles_handler)))
    app.add_handler(CallbackQueryHandler(authorized(menu_callback_handler)))
