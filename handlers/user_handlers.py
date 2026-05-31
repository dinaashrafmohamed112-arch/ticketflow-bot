"""
👤 User Handlers — Full Featured
==================================
✅ Multi-language (AR/EN)
✅ Rate Limiting
✅ Promo Codes
✅ Waitlist
✅ Paymob v2 Payment
✅ PDF Ticket
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_available_events, get_event,
    create_pending_booking, confirm_booking_payment,
    get_user_bookings, cancel_booking,
    validate_promo_code, use_promo_code,
    add_to_waitlist,
)
from ticket_generator import generate_ticket_pdf
from paymob import create_payment_url
from i18n import t, get_lang, toggle_lang
from rate_limiter import is_rate_limited

# ConversationHandler state for promo code
WAITING_PROMO = 50


# ════════════════════════════════════════
#   /start
# ════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user   = update.effective_user
    lang   = get_lang(user.id)
    toggle = "🌍 العربية" if lang == "en" else "🌍 English"

    keyboard = [
        [InlineKeyboardButton(t("btn_browse", lang),      callback_data="show_events")],
        [InlineKeyboardButton(t("btn_my_bookings", lang), callback_data="my_bookings")],
        [InlineKeyboardButton(t("btn_how", lang),         callback_data="how_it_works")],
        [InlineKeyboardButton(toggle,                     callback_data="toggle_lang")],
    ]
    text = t("welcome_title", lang) + "\n\n" + t("welcome_body", lang) + "\n\nWhat would you like to do? 👇" if lang == "en" else t("welcome_title", lang) + "\n\n" + t("welcome_body", lang) + "\n\nماذا تريد أن تفعل؟ 👇"

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown",
                                                       reply_markup=InlineKeyboardMarkup(keyboard))


async def toggle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    toggle_lang(query.from_user.id)
    await start(update, context)


async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = get_lang(query.from_user.id)

    text = (
        "ℹ️ *How It Works*\n\n"
        "1️⃣ *Browse* available events\n"
        "2️⃣ *Select* your event and tap Book\n"
        "3️⃣ *Apply* a promo code (optional)\n"
        "4️⃣ *Pay* securely via Paymob\n"
        "   (Credit Card • Vodafone Cash • InstaPay)\n"
        "5️⃣ *Receive* your PDF e-ticket instantly ✅\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔒 Payments processed by Paymob — Egypt's #1 gateway."
    ) if lang == "en" else (
        "ℹ️ *كيف يعمل؟*\n\n"
        "1️⃣ *تصفح* الفعاليات المتاحة\n"
        "2️⃣ *اختر* فعاليتك واضغط احجز\n"
        "3️⃣ *أضف* كود خصم (اختياري)\n"
        "4️⃣ *ادفع* بأمان عبر Paymob\n"
        "   (كارت • فودافون كاش • انستاباي)\n"
        "5️⃣ *استلم* تذكرتك PDF فوراً ✅\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔒 المدفوعات عبر Paymob — البوابة الأولى في مصر."
    )

    keyboard = [
        [InlineKeyboardButton(t("btn_browse", lang), callback_data="show_events")],
        [InlineKeyboardButton(t("back_menu", lang),  callback_data="start_menu")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Browse Events
# ════════════════════════════════════════

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user_id = query.from_user.id if query else update.message.from_user.id
    lang    = get_lang(user_id)

    if query:
        await query.answer()

    # Rate limit check
    if is_rate_limited(user_id):
        msg = t("rate_limited", lang)
        if query:
            await query.answer(msg, show_alert=True)
        return

    events = get_available_events()

    if not events:
        text     = t("no_events", lang)
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="show_events")]]
        if query:
            await query.edit_message_text(text, parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
        return

    keyboard = []
    for e in events:
        remaining   = e["capacity"] - e["booked"]
        price_label = t("free", lang) if e["price"] == 0 else f"EGP {e['price']:.0f}"
        seats_icon  = "🔴" if remaining <= 5 else "🟡" if remaining <= 20 else "🟢"
        keyboard.append([InlineKeyboardButton(
            f"🎪 {e['name']}   {price_label}   {seats_icon} {remaining}",
            callback_data=f"event_{e['id']}"
        )])

    keyboard.append([InlineKeyboardButton(t("btn_my_bookings", lang), callback_data="my_bookings")])
    keyboard.append([InlineKeyboardButton(t("back_menu", lang),       callback_data="start_menu")])

    title = t("events_title", lang)
    text  = (
        f"{title}\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*{len(events)}* event{'s' if len(events) != 1 else ''} available.\n\n"
        "🟢 = plenty   🟡 = filling up   🔴 = almost gone\n\n"
        "Tap an event to book:"
    ) if lang == "en" else (
        f"{title}\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*{len(events)}* فعالية متاحة.\n\n"
        "🟢 = مقاعد كثيرة   🟡 = تمتلئ   🔴 = آخر المقاعد\n\n"
        "اختر فعالية للحجز:"
    )

    if query:
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Event Details
# ════════════════════════════════════════

async def select_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    lang     = get_lang(query.from_user.id)
    event_id = int(query.data.split("_")[1])
    event    = get_event(event_id)

    if not event:
        await query.edit_message_text("❌ Event not found.")
        return

    remaining   = event["capacity"] - event["booked"]
    booked_pct  = int((event["booked"] / event["capacity"]) * 100) if event["capacity"] else 0
    price_text  = f"EGP {event['price']:.0f}" if event["price"] > 0 else ("🆓 FREE" if lang == "en" else "🆓 مجاني")
    filled      = min(10, int(booked_pct / 10))
    bar         = "🟥" * filled + "⬜" * (10 - filled)

    if remaining == 0:
        urgency = t("sold_out", lang)
    elif remaining <= 5:
        urgency = f"🔥 *Only {remaining} left!*" if lang == "en" else f"🔥 *{remaining} مقاعد فقط!*"
    elif remaining <= 20:
        urgency = f"⚡ *{remaining} seats left*" if lang == "en" else f"⚡ *{remaining} مقعد متبقي*"
    else:
        urgency = f"✅ *{remaining} seats available*" if lang == "en" else f"✅ *{remaining} مقعد متاح*"

    text = (
        f"🎪 *{event['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅  *Date:*    {event['date']}\n"
        f"📍  *Venue:*   {event['venue']}\n"
        f"💰  *Price:*   {price_text}\n\n"
        f"🪑  *Availability*\n"
        f"{bar}  {booked_pct}%\n"
        f"{urgency}\n"
    ) if lang == "en" else (
        f"🎪 *{event['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅  *التاريخ:*   {event['date']}\n"
        f"📍  *المكان:*    {event['venue']}\n"
        f"💰  *السعر:*    {price_text}\n\n"
        f"🪑  *المقاعد*\n"
        f"{bar}  {booked_pct}%\n"
        f"{urgency}\n"
    )

    keyboard = []
    if remaining > 0:
        book_btn = "🎟️ Book Now" if lang == "en" else "🎟️ احجز الآن"
        keyboard.append([InlineKeyboardButton(book_btn, callback_data=f"book_{event_id}")])
    else:
        # Sold out → Waitlist
        wait_btn = "📋 Join Waitlist" if lang == "en" else "📋 قائمة الانتظار"
        keyboard.append([InlineKeyboardButton(wait_btn, callback_data=f"waitlist_{event_id}")])

    keyboard.append([InlineKeyboardButton(t("back_events", lang), callback_data="show_events")])
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Waitlist
# ════════════════════════════════════════

async def join_waitlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    lang     = get_lang(query.from_user.id)
    event_id = int(query.data.split("_")[1])
    user     = query.from_user
    username = user.username or user.first_name

    added = add_to_waitlist(user.id, username, event_id)
    text  = t("added_to_waitlist", lang) if added else (
        "⚠️ You're already on the waitlist!" if lang == "en" else "⚠️ أنت بالفعل في قائمة الانتظار!"
    )
    keyboard = [[InlineKeyboardButton(t("back_events", lang), callback_data="show_events")]]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Book → Ask for Promo Code
# ════════════════════════════════════════

async def initiate_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    lang     = get_lang(query.from_user.id)
    event_id = int(query.data.split("_")[1])
    event    = get_event(event_id)

    if not event:
        await query.edit_message_text("❌ Event not found.")
        return

    # Store event_id for next step
    context.user_data["booking_event_id"] = event_id

    price_text = f"EGP {event['price']:.0f}" if event["price"] > 0 else ("FREE" if lang == "en" else "مجاني")

    text = (
        f"🎟️ *Booking: {event['name']}*\n"
        f"💰 Price: {price_text}\n\n"
        f"Do you have a promo code?"
    ) if lang == "en" else (
        f"🎟️ *حجز: {event['name']}*\n"
        f"💰 السعر: {price_text}\n\n"
        f"هل لديك كود خصم؟"
    )

    skip_btn  = "Skip → Pay Now" if lang == "en" else "تخطى ← ادفع الآن"
    promo_btn = "🏷️ Enter Promo Code" if lang == "en" else "🏷️ أدخل كود الخصم"

    keyboard = [
        [InlineKeyboardButton(promo_btn,                  callback_data=f"ask_promo_{event_id}")],
        [InlineKeyboardButton(skip_btn,                   callback_data=f"pay_{event_id}_0")],
        [InlineKeyboardButton(t("back_events", lang),     callback_data="show_events")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def ask_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    lang     = get_lang(query.from_user.id)
    event_id = int(query.data.split("_")[2])
    context.user_data["promo_event_id"] = event_id

    text = "🏷️ *Enter your promo code:*" if lang == "en" else "🏷️ *أدخل كود الخصم:*"
    keyboard = [[InlineKeyboardButton(
        "Skip" if lang == "en" else "تخطى",
        callback_data=f"pay_{event_id}_0"
    )]]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data["waiting_promo"] = True


async def handle_promo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle promo code text input"""
    if not context.user_data.get("waiting_promo"):
        return

    lang     = get_lang(update.message.from_user.id)
    code     = update.message.text.strip()
    event_id = context.user_data.get("promo_event_id")
    promo    = validate_promo_code(code)

    if not promo:
        text = t("promo_invalid", lang)
        keyboard = [[InlineKeyboardButton(
            "Try Again" if lang == "en" else "حاول مجدداً",
            callback_data=f"ask_promo_{event_id}"
        ), InlineKeyboardButton(
            "Skip" if lang == "en" else "تخطى",
            callback_data=f"pay_{event_id}_0"
        )]]
        await update.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
        return

    discount = promo["discount_pct"]
    context.user_data["promo_code"]    = code
    context.user_data["promo_discount"] = discount
    context.user_data["waiting_promo"]  = False

    text = t("promo_applied", lang, discount=discount)
    keyboard = [[InlineKeyboardButton(
        f"✅ Pay Now with {discount}% off" if lang == "en" else f"✅ ادفع الآن بخصم {discount}%",
        callback_data=f"pay_{event_id}_{discount}"
    )]]
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Process Payment
# ════════════════════════════════════════

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer("Processing... ⏳")
    lang     = get_lang(query.from_user.id)

    parts    = query.data.split("_")  # pay_{event_id}_{discount}
    event_id = int(parts[1])
    discount = int(parts[2])

    user     = query.from_user
    username = user.username or user.first_name
    event    = get_event(event_id)

    if not event:
        await query.edit_message_text("❌ Event not found.")
        return

    # Calculate final price
    final_price = event["price"] * (1 - discount / 100)
    promo_code  = context.user_data.pop("promo_code", None)

    # Create pending booking
    success, result = create_pending_booking(
        user.id, username, event_id,
        discount=discount, final_price=final_price
    )

    if not success:
        msg = t("already_booked", lang) if result == "already_booked" else t("no_seats", lang)
        await query.edit_message_text(msg, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup([[
                                          InlineKeyboardButton(t("btn_browse", lang),
                                                               callback_data="show_events")
                                      ]]))
        return

    booking_id = result

    # Use promo code
    if promo_code:
        use_promo_code(promo_code)

    # Free event → confirm immediately
    if final_price == 0:
        confirm_booking_payment(booking_id)
        await query.edit_message_text(
            t("booking_confirmed", lang), parse_mode="Markdown"
        )
        await _send_ticket(context, user, event, booking_id)
        return

    # Paid → generate Paymob link
    await query.edit_message_text(
        "⏳ *Preparing secure payment...*" if lang == "en" else "⏳ *جاري تجهيز الدفع...*",
        parse_mode="Markdown"
    )

    try:
        pay_url = await create_payment_url(
            amount=final_price, booking_id=booking_id,
            user_name=user.first_name
        )

        discount_line = f"\n🏷️ *Discount:* {discount}% applied!" if discount > 0 else ""
        text = (
            f"💳 *Complete Your Payment*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎪 {event['name']}\n"
            f"💰 *Amount:* EGP {final_price:.0f}{discount_line}\n"
            f"🔖 *Booking:* `#{booking_id:04d}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ Ticket sent automatically after payment."
        ) if lang == "en" else (
            f"💳 *أكمل الدفع*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎪 {event['name']}\n"
            f"💰 *المبلغ:* {final_price:.0f} جنيه{discount_line}\n"
            f"🔖 *الحجز:* `#{booking_id:04d}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ تُرسل التذكرة تلقائياً بعد الدفع."
        )

        keyboard = [
            [InlineKeyboardButton(
                f"💳 Pay EGP {final_price:.0f}" if lang == "en" else f"💳 ادفع {final_price:.0f} جنيه",
                url=pay_url
            )],
            [InlineKeyboardButton(
                "❌ Cancel" if lang == "en" else "❌ إلغاء",
                callback_data=f"cancel_{booking_id}"
            )],
        ]
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        import logging
        logging.error(f"[Paymob] {e}", exc_info=True)
        cancel_booking(booking_id, user.id)
        await query.edit_message_text(
            "❌ *Payment system unavailable. Try again.*" if lang == "en"
            else "❌ *نظام الدفع غير متاح. حاول مجدداً.*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Retry", callback_data=f"book_{event_id}")
            ]])
        )


# ════════════════════════════════════════
#   My Bookings
# ════════════════════════════════════════

async def my_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    user_id = query.from_user.id if query else update.message.from_user.id
    lang    = get_lang(user_id)

    if query:
        await query.answer()

    bookings = get_user_bookings(user_id)
    title    = "🎟️ *My Bookings*" if lang == "en" else "🎟️ *حجوزاتي*"

    if not bookings:
        text = (
            "📭 *No Bookings Yet*\n\nBrowse events and grab your seat! 🎉"
        ) if lang == "en" else (
            "📭 *لا توجد حجوزات*\n\nتصفح الفعاليات واحجز مقعدك! 🎉"
        )
        keyboard = [[InlineKeyboardButton(t("btn_browse", lang), callback_data="show_events")]]
        if query:
            await query.edit_message_text(text, parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, parse_mode="Markdown",
                                            reply_markup=InlineKeyboardMarkup(keyboard))
        return

    text     = f"{title}\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    status_map = {
        "confirmed": ("✅", "Confirmed",  "مؤكد"),
        "pending":   ("⏳", "Pending",    "معلق"),
        "cancelled": ("❌", "Cancelled",  "ملغي"),
    }

    for b in bookings:
        icon, en_label, ar_label = status_map.get(b["status"], ("❓", b["status"], b["status"]))
        label      = en_label if lang == "en" else ar_label
        price_line = f"EGP {b['final_price']:.0f}" if b["final_price"] else ""
        if b["discount"] and b["discount"] > 0:
            price_line += f" (-{b['discount']:.0f}%)"

        text += (
            f"{icon} *{b['name']}*\n"
            f"   📅 {b['date']}\n"
            f"   📍 {b['venue']}\n"
            f"   🔖 `#{b['id']:04d}`  •  _{label}_"
            + (f"  •  {price_line}" if price_line else "") + "\n\n"
        )
        if b["status"] in ("confirmed", "pending"):
            cancel_label = f"❌ Cancel #{b['id']:04d}" if lang == "en" else f"❌ إلغاء #{b['id']:04d}"
            keyboard.append([InlineKeyboardButton(cancel_label,
                                                   callback_data=f"cancel_{b['id']}")])

    keyboard.append([InlineKeyboardButton(t("back_menu", lang), callback_data="start_menu")])

    if query:
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Cancel Booking
# ════════════════════════════════════════

async def cancel_booking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query      = update.callback_query
    await query.answer()
    lang       = get_lang(query.from_user.id)
    booking_id = int(query.data.split("_")[1])
    success    = cancel_booking(booking_id, query.from_user.id)

    # Notify waitlist
    if success:
        from notifications import notify_waitlist
        from database import get_payment_by_booking
        payment = get_payment_by_booking(booking_id)
        if payment:
            event = get_event(payment["event_id"])
            if event:
                await notify_waitlist(context.bot, payment["event_id"], event["name"])

    text = t("cancel_success", lang) if success else (
        "❌ Unable to cancel." if lang == "en" else "❌ تعذر الإلغاء."
    )
    keyboard = [
        [InlineKeyboardButton(t("btn_my_bookings", lang), callback_data="my_bookings")],
        [InlineKeyboardButton(t("btn_browse", lang),      callback_data="show_events")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


# ════════════════════════════════════════
#   Helper: Send PDF Ticket
# ════════════════════════════════════════

async def _send_ticket(context, user, event, booking_id: int):
    lang = get_lang(user.id)
    try:
        pdf_path = generate_ticket_pdf(booking_id, user.first_name, dict(event))
        caption  = (
            f"🎟️ *Your E-Ticket is Ready!*\n\n"
            f"🎪 {event['name']}\n"
            f"📅 {event['date']}\n"
            f"🔖 Booking ID: `#{booking_id:04d}`\n\n"
            f"_See you there! 🎉_"
        ) if lang == "en" else (
            f"🎟️ *تذكرتك جاهزة!*\n\n"
            f"🎪 {event['name']}\n"
            f"📅 {event['date']}\n"
            f"🔖 رقم الحجز: `#{booking_id:04d}`\n\n"
            f"_نراك هناك! 🎉_"
        )
        with open(pdf_path, "rb") as f:
            await context.bot.send_document(
                chat_id=user.id, document=f,
                filename=f"TicketFlow_{booking_id:04d}.pdf",
                caption=caption, parse_mode="Markdown"
            )
        os.remove(pdf_path)
    except Exception:
        price_text = f"EGP {event['price']:.0f}" if event["price"] > 0 else "FREE"
        await context.bot.send_message(
            chat_id=user.id, parse_mode="Markdown",
            text=(
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n🎟️  *E-TICKET*\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔖  `#{booking_id:04d}`\n👤  {user.first_name}\n"
                f"🎪  {event['name']}\n📅  {event['date']}\n"
                f"📍  {event['venue']}\n💰  {price_text}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n✅  *CONFIRMED*"
            )
        )
    keyboard = [
        [InlineKeyboardButton("📋 My Bookings" if lang == "en" else "📋 حجوزاتي",
                              callback_data="my_bookings")],
        [InlineKeyboardButton("🎪 More Events" if lang == "en" else "🎪 فعاليات أخرى",
                              callback_data="show_events")],
    ]
    await context.bot.send_message(
        chat_id=user.id,
        text="What would you like to do next?" if lang == "en" else "ماذا تريد أن تفعل؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
