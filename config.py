"""
⚙️ Configuration
=================
All settings loaded from .env
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ── Admin IDs (get yours from @userinfobot) ───────────────────
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

# ── Paymob ────────────────────────────────────────────────────
PAYMOB_API_KEY        = os.getenv("PAYMOB_API_KEY", "")
PAYMOB_INTEGRATION_ID = int(os.getenv("PAYMOB_INTEGRATION_ID", "0"))
PAYMOB_IFRAME_ID      = os.getenv("PAYMOB_IFRAME_ID", "")
PAYMOB_HMAC_SECRET    = os.getenv("PAYMOB_HMAC_SECRET", "")
PAYMOB_PUBLIC_KEY     = os.getenv("PAYMOB_PUBLIC_KEY", "")

# ── Database ──────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── Bot Branding ──────────────────────────────────────────────
BOT_NAME     = "TicketFlow"
BOT_USERNAME = "@ticketflow_demo_bot"
CURRENCY     = "EGP"