"""
🌍 Multi-Language Support (Arabic / English)
=============================================
Usage:
    from i18n import t, get_lang, set_lang
    text = t("welcome", lang)
"""

STRINGS = {
    # ── Welcome ──────────────────────────────────────────────
    "welcome_title": {
        "en": "🎟️ *Welcome to TicketFlow!*",
        "ar": "🎟️ *أهلاً بك في TicketFlow!*",
    },
    "welcome_body": {
        "en": (
            "The fastest way to book event tickets\n"
            "— secure payment, instant e-ticket. ✨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔸 Browse & book in seconds\n"
            "🔸 Pay via Card, Vodafone Cash or InstaPay\n"
            "🔸 Receive your PDF ticket instantly\n"
            "🔸 Manage & cancel anytime\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        "ar": (
            "أسرع طريقة لحجز تذاكر الفعاليات\n"
            "— دفع آمن، وتذكرة فورية. ✨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔸 تصفح واحجز في ثوانٍ\n"
            "🔸 ادفع بالكارت أو فودافون كاش أو انستاباي\n"
            "🔸 استلم تذكرة PDF فوراً\n"
            "🔸 أدر حجوزاتك في أي وقت\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
    },
    "btn_browse":       {"en": "🎪 Browse Events",    "ar": "🎪 الفعاليات المتاحة"},
    "btn_my_bookings":  {"en": "🎟️ My Bookings",      "ar": "🎟️ حجوزاتي"},
    "btn_how":          {"en": "ℹ️ How It Works",     "ar": "ℹ️ كيف يعمل؟"},
    "btn_language":     {"en": "🌍 العربية",           "ar": "🌍 English"},

    # ── Events ───────────────────────────────────────────────
    "no_events": {
        "en": "📭 *No Upcoming Events*\n\nCheck back soon — something exciting is coming! 🔔",
        "ar": "📭 *لا توجد فعاليات حالياً*\n\nتابعنا قريباً — هناك شيء مثير قادم! 🔔",
    },
    "events_title": {
        "en": "🎪 *Upcoming Events*",
        "ar": "🎪 *الفعاليات القادمة*",
    },
    "sold_out":     {"en": "⛔ Sold Out",         "ar": "⛔ نفدت التذاكر"},
    "seats_left":   {"en": "{n} seats left",     "ar": "{n} مقعد متاح"},
    "free":         {"en": "FREE",               "ar": "مجاني"},

    # ── Booking ──────────────────────────────────────────────
    "already_booked": {
        "en": "⚠️ *Already Booked!*\n\nYou already have an active booking for this event.",
        "ar": "⚠️ *محجوز مسبقاً!*\n\nلديك حجز نشط لهذه الفعالية بالفعل.",
    },
    "no_seats": {
        "en": "😔 *Sold Out!*\n\nThe last seat was just taken.",
        "ar": "😔 *نفدت المقاعد!*\n\nتم أخذ آخر مقعد للتو.",
    },
    "booking_confirmed": {
        "en": "✅ *Booking Confirmed!*\n\nGenerating your e-ticket...",
        "ar": "✅ *تم تأكيد الحجز!*\n\nجاري إنشاء تذكرتك...",
    },
    "added_to_waitlist": {
        "en": "📋 *Added to Waitlist!*\n\nYou'll be notified automatically if a seat becomes available.",
        "ar": "📋 *تمت إضافتك لقائمة الانتظار!*\n\nسيتم إشعارك تلقائياً عند توفر مقعد.",
    },

    # ── Payment ──────────────────────────────────────────────
    "pay_title":    {"en": "💳 *Complete Your Payment*", "ar": "💳 *أكمل الدفع*"},
    "pay_now":      {"en": "💳 Pay Now",                 "ar": "💳 ادفع الآن"},
    "promo_applied":{"en": "🎉 Promo code applied! -{discount}%", "ar": "🎉 تم تطبيق كود الخصم! -{discount}%"},
    "promo_invalid":{"en": "❌ Invalid or expired promo code.", "ar": "❌ كود الخصم غير صالح أو منتهي."},

    # ── Notifications ────────────────────────────────────────
    "notif_24h": {
        "en": "⏰ *Reminder!*\n\nYour event *{event}* is tomorrow!\n📅 {date}\n📍 {venue}\n\nSee you there! 🎉",
        "ar": "⏰ *تذكير!*\n\nفعاليتك *{event}* غداً!\n📅 {date}\n📍 {venue}\n\nنراك هناك! 🎉",
    },
    "notif_1h": {
        "en": "🔔 *Starting Soon!*\n\n*{event}* starts in 1 hour!\n📍 {venue}",
        "ar": "🔔 *تبدأ قريباً!*\n\n*{event}* تبدأ خلال ساعة!\n📍 {venue}",
    },

    # ── Misc ─────────────────────────────────────────────────
    "cancel_success": {
        "en": "✅ *Booking Cancelled*\n\nWe hope to see you at a future event! 👋",
        "ar": "✅ *تم إلغاء الحجز*\n\nنأمل رؤيتك في فعالية قادمة! 👋",
    },
    "back_menu":    {"en": "◀️ Back to Menu",    "ar": "◀️ القائمة الرئيسية"},
    "back_events":  {"en": "◀️ Back to Events",  "ar": "◀️ الفعاليات"},
    "rate_limited": {
        "en": "⚠️ Too many requests. Please wait a moment.",
        "ar": "⚠️ طلبات كثيرة جداً. الرجاء الانتظار لحظة.",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated string. Falls back to English if key not found in lang."""
    val = STRINGS.get(key, {}).get(lang) or STRINGS.get(key, {}).get("en", key)
    if kwargs:
        val = val.format(**kwargs)
    return val


# ── User language preference (in-memory cache) ────────────────
_user_langs: dict[int, str] = {}

def get_lang(user_id: int) -> str:
    return _user_langs.get(user_id, "en")

def set_lang(user_id: int, lang: str):
    _user_langs[user_id] = lang

def toggle_lang(user_id: int) -> str:
    lang = "ar" if get_lang(user_id) == "en" else "en"
    set_lang(user_id, lang)
    return lang
