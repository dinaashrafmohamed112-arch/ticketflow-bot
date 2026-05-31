# 🎟️ TicketFlow Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Paymob](https://img.shields.io/badge/Paymob-v2_API-FF6B35?style=for-the-badge)
![Railway](https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)

**A production-ready Telegram bot for event ticket booking with integrated payment processing, PDF ticket generation, and a full admin dashboard.**

[Features](#-features) • [Tech Stack](#-tech-stack) • [Architecture](#-architecture) • [Setup](#-quick-start) • [Schema](#-database-schema)

</div>

---

## ✨ Features

### 👤 User Features
| Feature | Description |
|---------|-------------|
| 🎪 **Event Browsing** | Real-time seat availability with visual progress bars |
| 🎟️ **Instant Booking** | Reserve seats with one tap |
| 💳 **Secure Payments** | Credit Card, Vodafone Cash & InstaPay via Paymob v2 |
| 📄 **PDF E-Tickets** | Professional tickets auto-generated and delivered instantly |
| 📋 **Waitlist System** | Auto-notified when seats become available |
| 🏷️ **Promo Codes** | Discount codes with expiry dates and usage limits |
| 🌍 **Multi-Language** | Full Arabic and English support |
| ❌ **Easy Cancellation** | Cancel bookings with automatic seat release & waitlist notification |

### 👑 Admin Features
| Feature | Description |
|---------|-------------|
| 📊 **Live Dashboard** | Real-time stats: confirmed, pending, cancelled bookings |
| ➕ **Event Management** | Add/delete events via conversational UI |
| 📈 **Sales Reports** | Export to Excel (.xlsx) and PDF with full revenue breakdown |
| 🔔 **Broadcast** | Send announcements to all confirmed attendees |
| ⏳ **Payment Review** | Manual payment approval with instant user notification |

### 🛡️ Security & Reliability
- **Rate Limiting** — Prevents spam (configurable, default: 10 req/60s per user)
- **HMAC Webhook Verification** — Validates all Paymob payment callbacks
- **Environment-based Secrets** — Zero credentials in codebase
- **PostgreSQL** — Production-grade persistent storage (no data loss on redeploy)
- **Graceful Error Handling** — Fallback text tickets if PDF generation fails

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────┐
│                      Telegram                          │
│                  User  /  Admin                        │
└────────────────────────┬──────────────────────────────┘
                         │ Messages & Callbacks
                         ▼
┌───────────────────────────────────────────────────────┐
│                  TicketFlow Bot                        │
│  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Handlers   │ │  i18n    │ │  Rate Limiter    │   │
│  │ user/admin  │ │  AR/EN   │ │  anti-spam       │   │
│  └──────┬──────┘ └──────────┘ └──────────────────┘   │
│         │                                             │
│  ┌──────▼──────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  database   │ │  paymob  │ │  ticket/report   │   │
│  │ PostgreSQL  │ │  v2 API  │ │  generators      │   │
│  └─────────────┘ └──────────┘ └──────────────────┘   │
└───────────────────────────────────────────────────────┘
                         │ Webhook (HMAC verified)
                         ▼
┌───────────────────────────────────────────────────────┐
│                     Paymob                             │
│         Card / Vodafone Cash / InstaPay                │
└───────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12 |
| **Bot Framework** | python-telegram-bot 21.5 |
| **Database** | PostgreSQL + psycopg2 |
| **Payments** | Paymob v2 API |
| **PDF Generation** | ReportLab |
| **Excel Reports** | openpyxl |
| **HTTP Client** | httpx (async) |
| **Deployment** | Railway (24/7) |

---

## 📁 Project Structure

```
ticket_bot/
├── bot.py                  # Entry point & handler registration
├── config.py               # Environment configuration
├── database.py             # Full PostgreSQL data layer
├── paymob.py               # Paymob v2 payment integration
├── ticket_generator.py     # PDF e-ticket generation (ReportLab)
├── report_generator.py     # Excel & PDF sales reports
├── notifications.py        # Automated event reminders & broadcast
├── rate_limiter.py         # Anti-spam protection
├── i18n.py                 # Multi-language strings (AR / EN)
├── requirements.txt
└── handlers/
    ├── user_handlers.py    # User commands & booking flow
    └── admin_handlers.py   # Admin dashboard & management
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Telegram Bot Token — [@BotFather](https://t.me/BotFather)
- Paymob merchant account — [paymob.com](https://paymob.com)

### Installation

```bash
git clone https://github.com/dinaashrafmohamed112-arch/ticket-bot.git
cd ticket-bot
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789

DATABASE_URL=postgresql://user:pass@host:5432/dbname

PAYMOB_API_KEY=egy_sk_...
PAYMOB_PUBLIC_KEY=egy_pk_...
PAYMOB_INTEGRATION_ID=5578640
PAYMOB_IFRAME_ID=1015498
PAYMOB_HMAC_SECRET=your_hmac_secret
```

### Run

```bash
python bot.py
```

---

## 💳 Payment Flow

```
User taps "Book Now"
    ↓
Seat reserved (status: pending)
    ↓
Paymob payment link generated → sent to user
    ↓
User pays on Paymob (Card / Vodafone Cash / InstaPay)
    ↓
Paymob sends webhook → HMAC verified
    ↓
Booking confirmed → PDF ticket sent instantly ✅
```

---

## 📊 Database Schema

```sql
events      (id, name, date, venue, capacity, booked, price)
bookings    (id, user_id, event_id, status, discount, final_price)
payments    (id, booking_id, amount, method, status)
promo_codes (id, code, discount_pct, max_uses, used_count, expires_at)
waitlist    (id, user_id, event_id, joined_at)
```

---

## 🚀 Deployment (Railway)

```bash
# Auto-deploys on push to master
git push origin master
```

**Required services on Railway:**
1. Python service (this bot)
2. PostgreSQL plugin (persistent database)

---

## 📄 License

MIT License — feel free to use and modify.

---

<div align="center">
  TicketFlow — Telegram Ticket Booking Bot
</div>
