# bot/management/commands/runbot.py
import asyncio
from django.core.management.base import BaseCommand
from bot.bot import build_application
# Optional: if you want to specify allowed_updates explicitly:
# from telegram import Update


class Command(BaseCommand):
    help = "Run Telegram game bot (polling)."

    def handle(self, *args, **options):
        app = build_application()

        # Simple version – let PTB decide allowed_updates
        asyncio.run(app.run_polling())

        # If you prefer to be explicit, you can instead do:
        # asyncio.run(app.run_polling(allowed_updates=Update.ALL_TYPES))
