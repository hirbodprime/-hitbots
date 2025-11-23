# bot/management/commands/runbot.py
import asyncio
from django.core.management.base import BaseCommand
from bot.bot import build_application


class Command(BaseCommand):
    help = "Run Telegram game bot (polling)."

    def handle(self, *args, **options):
        app = build_application()
        asyncio.run(app.run_polling(allowed_updates=app.resolve_all_updates()))
