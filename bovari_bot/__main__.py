"""Ishga tushirish: python -m bovari_bot"""

import logging

from telegram import Update

from .bot import BovariBot
from .config import load_settings


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = load_settings()
    if not settings.allowed_user_ids:
        logging.warning(
            "ALLOWED_USER_IDS bo'sh — botdan istalgan odam foydalana oladi va API xarajati "
            "sizning hisobingizdan ketadi. .env faylda jamoa ID larini kiriting."
        )
    app = BovariBot(settings).build_application()
    logging.info("%s boti ishga tushdi (model: %s)", settings.bot_name, settings.model)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
