"""
👑 Admin Handlers — Full Featured
===================================
✅ Dashboard with live stats
✅ Add / Delete events
✅ View all bookings
✅ Sales Reports (Excel + PDF)
✅ Promo Code management
✅ Broadcast messages
✅ Pending payments
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS
from database import (
    add_event, get_all_events, get_event, delete_event,
    get_all_bookings, confirm_booking_payment, reject_booking_payment,
    add_promo_code, get_all_promo_codes, get_sales_report,
)

(EVENT_NAME, EVENT_DATE, EVENT_VENUE, EVENT_CAPACITY, EVENT_PRICE, EVENT_CONFIRM) = range(6)
(PROMO_CODE, PROMO_DISCOUNT, PROMO_USES) = range(10, 13)
BROADCAST_MSG = 20


def is_admin(user_id): return user_id in ADMIN_IDS
def _blocked(): return "⛔ *Access Denied.*"


# ════════════════════════════════════════
#   Dashboard
# ════════════════════════════════════════

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            await update.message.reply_text(_blocked(), parse_mode="Markdown")
        return

    bookings  = get_all_bookings()
    events    = get_all_events()
    confirmed = sum(1 for b in bookings if b["status"] == "confirmed")
    pending   = sum(1 for b in bookings if b["status"] == "pending")
    _, stats  = get_sales_report()
    revenue   = stats["total_revenue"] if stats else 0

    keyboard = [
        [InlineKeyboardButton("➕ Add Event",          callback_data="admin_add_event"),
         InlineKeyboardButton("🗑️ Delete Event",       callback_data="admin_delete_menu")],
        [InlineKeyboardButton("📊 All Bookings",       callback_data="admin_bookings"),
         InlineKeyboardButton("⏳ Pending Payments",   callback_data="admin_pending")],
        [InlineKeyboardButton("📈 Sales Report",       callback_data="admin_report"),
         InlineKeyboardButton("🏷️ Promo Codes",        callback_data="admin_promos")],
        [InlineKeyboardButton("📢 Broadcast",          callback_data="admin_broadcast")],
    ]
    text = (
        "👑 *Admin Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 *Active Events:*    {len(events)}\n"
        f"✅ *Confirmed:*         {confirmed}\n"
        f"⏳ *Pending:*            {pending}\n"
        f"💰 *Total Revenue:*   EGP {revenue:,.0f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Select an action:"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Add Event
# ════════════════════════════════════════

async def add_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.edit_message_text(_blocked(), parse_mode="Markdown")
        return ConversationHandler.END
    context.user_data["new_event"] = {}
    await query.edit_message_text(
        "➕ *Add New Event*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Step *1/5* — Enter the *event name*:",
        parse_mode="Markdown"
    )
    return EVENT_NAME


async def add_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_event"]["name"] = update.message.text.strip()
    await update.message.reply_text("Step *2/5* — Enter *date & time*:\n_e.g. Saturday, April 26, 2025 — 7:00 PM_",
                                    parse_mode="Markdown")
    return EVENT_DATE


async def add_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_event"]["date"] = update.message.text.strip()
    await update.message.reply_text("Step *3/5* — Enter *venue / location*:", parse_mode="Markdown")
    return EVENT_VENUE


async def add_event_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_event"]["venue"] = update.message.text.strip()
    await update.message.reply_text("Step *4/5* — Enter *total capacity* (number only):", parse_mode="Markdown")
    return EVENT_CAPACITY


async def add_event_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        capacity = int(update.message.text.strip())
        if capacity <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number:")
        return EVENT_CAPACITY
    context.user_data["new_event"]["capacity"] = capacity
    await update.message.reply_text("Step *5/5* — Enter *ticket price* in EGP.\n_Enter `0` for free._",
                                    parse_mode="Markdown")
    return EVENT_PRICE


async def add_event_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.strip())
        if price < 0: raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Enter a valid price (e.g. `150` or `0`):")
        return EVENT_PRICE
    context.user_data["new_event"]["price"] = price
    e          = context.user_data["new_event"]
    price_text = f"EGP {price:.0f}" if price > 0 else "FREE"
    summary = (
        "📋 *Review New Event*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎪 *Name:*      {e['name']}\n"
        f"📅 *Date:*      {e['date']}\n"
        f"📍 *Venue:*     {e['venue']}\n"
        f"🪑 *Capacity:*  {e['capacity']}\n"
        f"💰 *Price:*     {price_text}\n\n"
        "Confirm to publish?"
    )
    keyboard = [[
        InlineKeyboardButton("✅ Publish", callback_data="confirm_add"),
        InlineKeyboardButton("❌ Cancel",  callback_data="cancel_add"),
    ]]
    await update.message.reply_text(summary, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return EVENT_CONFIRM


async def add_event_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_add":
        e = context.user_data["new_event"]
        add_event(e["name"], e["date"], e["venue"], e["capacity"], e["price"])
        text = f"✅ *{e['name']}* is now live!"
    else:
        text = "❌ Event creation cancelled."
    context.user_data.pop("new_event", None)
    keyboard = [[InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")]]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


async def cancel_add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("new_event", None)
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# ════════════════════════════════════════
#   View Bookings
# ════════════════════════════════════════

async def view_all_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return
    bookings = get_all_bookings()
    icons    = {"confirmed": "✅", "pending": "⏳", "cancelled": "❌"}
    text     = f"📊 *All Bookings* ({len(bookings)})\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for b in bookings:
        icon  = icons.get(b["status"], "❓")
        uname = f"@{b['username']}" if b["username"] else f"ID:{b['user_id']}"
        text += f"{icon} `#{b['id']:04d}` {uname} ← {b['event_name']}\n"
        if len(text) > 3500:
            text += "\n_...truncated_"
            break
    keyboard = [[InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")]]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Sales Report
# ════════════════════════════════════════

async def sales_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return
    keyboard = [
        [InlineKeyboardButton("📊 Excel Report (.xlsx)", callback_data="report_excel")],
        [InlineKeyboardButton("📄 PDF Report",           callback_data="report_pdf")],
        [InlineKeyboardButton("◀️ Dashboard",            callback_data="admin_panel")],
    ]
    await query.edit_message_text(
        "📈 *Sales Report*\n\nChoose format:",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer("Generating report... ⏳")
    if not is_admin(query.from_user.id): return

    fmt             = query.data.split("_")[1]  # excel or pdf
    events_data, stats = get_sales_report()

    try:
        from report_generator import generate_excel_report, generate_pdf_report

        if fmt == "excel":
            data     = generate_excel_report(events_data, stats)
            filename = "TicketFlow_Sales_Report.xlsx"
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=data,
                filename=filename,
                caption="📊 *Sales Report — Excel*",
                parse_mode="Markdown"
            )
        else:
            filepath = generate_pdf_report(events_data, stats)
            with open(filepath, "rb") as f:
                await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=f,
                    filename="TicketFlow_Sales_Report.pdf",
                    caption="📄 *Sales Report — PDF*",
                    parse_mode="Markdown"
                )
            os.remove(filepath)

        await query.edit_message_text("✅ Report sent!", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")
        ]]))

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")
        ]]))


# ════════════════════════════════════════
#   Promo Codes
# ════════════════════════════════════════

async def promo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return

    promos = get_all_promo_codes()
    text   = "🏷️ *Promo Codes*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    if promos:
        for p in promos:
            status = "✅" if p["active"] else "❌"
            text  += f"{status} `{p['code']}` — {p['discount_pct']}% off  ({p['used_count']}/{p['max_uses']} used)\n"
    else:
        text += "_No promo codes yet._"

    keyboard = [
        [InlineKeyboardButton("➕ Add Promo Code", callback_data="admin_add_promo")],
        [InlineKeyboardButton("◀️ Dashboard",      callback_data="admin_panel")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def add_promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏷️ *Add Promo Code*\n\nStep *1/3* — Enter the *promo code*:\n_e.g. SUMMER20_",
        parse_mode="Markdown"
    )
    return PROMO_CODE


async def add_promo_code_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["promo"] = {"code": update.message.text.strip().upper()}
    await update.message.reply_text("Step *2/3* — Enter *discount percentage*:\n_e.g. 20 for 20% off_",
                                    parse_mode="Markdown")
    return PROMO_DISCOUNT


async def add_promo_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        disc = int(update.message.text.strip())
        if not 1 <= disc <= 100: raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Enter a number between 1 and 100:")
        return PROMO_DISCOUNT
    context.user_data["promo"]["discount"] = disc
    await update.message.reply_text("Step *3/3* — Enter *max uses*:\n_e.g. 50_",
                                    parse_mode="Markdown")
    return PROMO_USES


async def add_promo_uses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uses = int(update.message.text.strip())
        if uses <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Enter a valid number:")
        return PROMO_USES
    p = context.user_data["promo"]
    add_promo_code(p["code"], p["discount"], uses)
    context.user_data.pop("promo", None)
    keyboard = [[InlineKeyboardButton("◀️ Promo Codes", callback_data="admin_promos")]]
    await update.message.reply_text(
        f"✅ Promo code *{p['code']}* created!\n{p['discount']}% off — max {uses} uses.",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# ════════════════════════════════════════
#   Pending Payments
# ════════════════════════════════════════

async def view_pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return
    from database import get_pending_payments
    payments = get_pending_payments()
    if not payments:
        text     = "⏳ *No pending payments.* All clear! ✅"
        keyboard = [[InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")]]
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return
    text     = f"⏳ *Pending Payments* ({len(payments)})\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    for p in payments:
        uname = f"@{p['username']}" if p["username"] else f"ID:{p['user_id']}"
        text += f"🔖 `#{p['booking_id']:04d}` {uname}\n   🎪 {p['event_name']}  💰 EGP {p['amount']:.0f}\n\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ Approve #{p['booking_id']:04d}",
                                 callback_data=f"approve_{p['booking_id']}"),
            InlineKeyboardButton("❌ Reject",
                                 callback_data=f"reject_{p['booking_id']}"),
        ])
    keyboard.append([InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")])
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query      = update.callback_query
    await query.answer()
    booking_id = int(query.data.split("_")[1])
    from database import get_payment_by_booking
    payment    = get_payment_by_booking(booking_id)
    confirm_booking_payment(booking_id)
    if payment:
        event = get_event(payment["event_id"])
        if event:
            from handlers.user_handlers import _send_ticket
            class _User:
                id = payment["user_id"]; first_name = payment["username"] or "Attendee"; username = payment["username"]
            await _send_ticket(context, _User(), event, booking_id)
    await query.edit_message_text(f"✅ Booking #{booking_id:04d} approved. Ticket sent.",
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")
                                  ]]))


async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query      = update.callback_query
    await query.answer()
    booking_id = int(query.data.split("_")[1])
    from database import get_payment_by_booking
    payment    = get_payment_by_booking(booking_id)
    reject_booking_payment(booking_id)
    if payment:
        await context.bot.send_message(
            chat_id=payment["user_id"],
            text=f"❌ *Payment Rejected — Booking #{booking_id:04d}*\n\nYour seat has been released.",
            parse_mode="Markdown"
        )
    await query.edit_message_text(f"❌ Booking #{booking_id:04d} rejected.",
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")
                                  ]]))


# ════════════════════════════════════════
#   Broadcast
# ════════════════════════════════════════

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return
    await query.edit_message_text(
        "📢 *Broadcast Message*\n\nType your message — it will be sent to all confirmed attendees:",
        parse_mode="Markdown"
    )
    return BROADCAST_MSG


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    from notifications import broadcast_to_all_users
    count = await broadcast_to_all_users(context.bot, message)
    keyboard = [[InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")]]
    await update.message.reply_text(
        f"✅ *Broadcast sent to {count} users.*",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


# ════════════════════════════════════════
#   Delete Event
# ════════════════════════════════════════

async def delete_event_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id): return
    if query.data == "admin_delete_menu":
        events   = get_all_events()
        if not events:
            await query.edit_message_text("No events to delete.",
                                          reply_markup=InlineKeyboardMarkup([[
                                              InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")
                                          ]]))
            return
        keyboard = [[InlineKeyboardButton(f"🗑️ {e['name']} ({e['booked']}/{e['capacity']})",
                                          callback_data=f"del_event_{e['id']}")]
                    for e in events]
        keyboard.append([InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")])
        await query.edit_message_text("🗑️ *Select event to delete:*\n_⚠️ This removes all bookings too._",
                                      parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return
    event_id = int(query.data.split("_")[2])
    event    = get_event(event_id)
    name     = event["name"] if event else "Unknown"
    delete_event(event_id)
    await query.edit_message_text(f"✅ *{name}* deleted.",
                                  parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton("◀️ Dashboard", callback_data="admin_panel")
                                  ]]))
