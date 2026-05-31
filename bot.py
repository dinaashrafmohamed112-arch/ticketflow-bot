"""
🤖 TicketFlow Bot — Main Entry Point
"""

import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from config import BOT_TOKEN
from handlers.user_handlers import (
    start, show_events, select_event, initiate_booking,
    my_bookings, cancel_booking_handler, how_it_works,
    toggle_language, ask_promo, handle_promo_input, process_payment,
    join_waitlist,
)
from handlers.admin_handlers import (
    admin_panel, add_event_start, add_event_name, add_event_date,
    add_event_venue, add_event_capacity, add_event_price, add_event_confirm,
    view_all_bookings, delete_event_handler, cancel_add_event,
    view_pending_payments, approve_payment, reject_payment,
    sales_report_menu, send_report,
    promo_menu, add_promo_start, add_promo_code_input, add_promo_discount, add_promo_uses,
    broadcast_start, broadcast_send,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Conversation states
(EVENT_NAME, EVENT_DATE, EVENT_VENUE, EVENT_CAPACITY, EVENT_PRICE, EVENT_CONFIRM) = range(6)
(PROMO_CODE, PROMO_DISCOUNT, PROMO_USES) = range(10, 13)
BROADCAST_MSG = 20


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # ── User commands ────────────────────────────────────────
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("events",     show_events))
    app.add_handler(CommandHandler("mybookings", my_bookings))

    # ── User buttons ─────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(start,                  pattern="^start_menu$"))
    app.add_handler(CallbackQueryHandler(toggle_language,        pattern="^toggle_lang$"))
    app.add_handler(CallbackQueryHandler(show_events,            pattern="^show_events$"))
    app.add_handler(CallbackQueryHandler(how_it_works,           pattern="^how_it_works$"))
    app.add_handler(CallbackQueryHandler(select_event,           pattern="^event_\\d+$"))
    app.add_handler(CallbackQueryHandler(initiate_booking,       pattern="^book_\\d+$"))
    app.add_handler(CallbackQueryHandler(process_payment,        pattern="^pay_\\d+_\\d+$"))
    app.add_handler(CallbackQueryHandler(my_bookings,            pattern="^my_bookings$"))
    app.add_handler(CallbackQueryHandler(cancel_booking_handler, pattern="^cancel_\\d+$"))
    app.add_handler(CallbackQueryHandler(join_waitlist,          pattern="^waitlist_\\d+$"))

    # ── Admin commands ───────────────────────────────────────
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_panel,            pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(view_all_bookings,      pattern="^admin_bookings$"))
    app.add_handler(CallbackQueryHandler(view_pending_payments,  pattern="^admin_pending$"))
    app.add_handler(CallbackQueryHandler(approve_payment,        pattern="^approve_\\d+$"))
    app.add_handler(CallbackQueryHandler(reject_payment,         pattern="^reject_\\d+$"))
    app.add_handler(CallbackQueryHandler(sales_report_menu,      pattern="^admin_report$"))
    app.add_handler(CallbackQueryHandler(send_report,            pattern="^report_(excel|pdf)$"))
    app.add_handler(CallbackQueryHandler(promo_menu,             pattern="^admin_promos$"))
    app.add_handler(CallbackQueryHandler(delete_event_handler,   pattern="^(admin_delete_menu|del_event_\\d+)$"))

    # ── Add Event conversation ───────────────────────────────
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_event_start, pattern="^admin_add_event$")],
        states={
            EVENT_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_name)],
            EVENT_DATE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_date)],
            EVENT_VENUE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_venue)],
            EVENT_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_capacity)],
            EVENT_PRICE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_price)],
            EVENT_CONFIRM:  [CallbackQueryHandler(add_event_confirm, pattern="^(confirm_add|cancel_add)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_event)],
        per_message=False,
    ))

    # ── Promo input conversation (user) ─────────────────────
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_promo, pattern=r"^ask_promo_\d+$")],
        states={
            50: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_promo_input)],
        },
        fallbacks=[CallbackQueryHandler(process_payment, pattern=r"^pay_\d+_\d+$")],
        per_message=False,
    ))

    # ── Add Promo Code conversation ──────────────────────────
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_promo_start, pattern="^admin_add_promo$")],
        states={
            PROMO_CODE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_promo_code_input)],
            PROMO_DISCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_promo_discount)],
            PROMO_USES:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_promo_uses)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_event)],
        per_message=False,
    ))

    # ── Broadcast conversation ───────────────────────────────
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="^admin_broadcast$")],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_event)],
        per_message=False,
    ))

    return app


if __name__ == "__main__":
    print("Starting TicketFlow Bot...")
    app = build_app()
    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=["message", "callback_query"])