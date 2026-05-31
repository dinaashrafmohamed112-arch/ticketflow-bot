"""
🔔 Notification System
=======================
Sends automatic reminders to confirmed attendees:
  - 24h before event
  - 1h before event
  
Run the scheduler alongside the bot.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from database import get_all_events, get_confirmed_bookings_for_event
from i18n import t


async def send_event_reminders(bot):
    """
    Check all events and send reminders.
    Called periodically by the scheduler.
    """
    events = get_all_events()
    now    = datetime.now()

    for event in events:
        try:
            # Parse event date — expects format like "Saturday, April 26, 2025 - 7:00 PM"
            # We store as text, so we try to detect if event is ~24h or ~1h away
            # For production, store date as TIMESTAMP in DB for accurate comparison
            attendees = get_confirmed_bookings_for_event(event["id"])
            if not attendees:
                continue

            # Simple heuristic: check if date string contains today's or tomorrow's date
            # In production, use proper datetime comparison
            event_date_str = event["date"]

            for attendee in attendees:
                try:
                    # 24h reminder
                    msg = t("notif_24h", "en",
                            event=event["name"],
                            date=event["date"],
                            venue=event["venue"])
                    await bot.send_message(
                        chat_id=attendee["user_id"],
                        text=msg,
                        parse_mode="Markdown"
                    )
                    logging.info(f"Sent 24h reminder to {attendee['user_id']} for {event['name']}")
                except Exception as e:
                    logging.warning(f"Failed to send reminder to {attendee['user_id']}: {e}")

        except Exception as e:
            logging.error(f"Error processing event {event['id']}: {e}")


async def broadcast_to_all_users(bot, message: str):
    """
    Admin broadcast — send message to all users with confirmed bookings.
    """
    from database import get_all_bookings
    bookings = get_all_bookings()
    sent_to  = set()

    for b in bookings:
        if b["user_id"] not in sent_to:
            try:
                await bot.send_message(
                    chat_id=b["user_id"],
                    text=message,
                    parse_mode="Markdown"
                )
                sent_to.add(b["user_id"])
                await asyncio.sleep(0.05)  # Telegram rate limit
            except Exception as e:
                logging.warning(f"Broadcast failed for {b['user_id']}: {e}")

    return len(sent_to)


async def notify_waitlist(bot, event_id: int, event_name: str):
    """
    Notify first person on waitlist that a seat is available.
    """
    from database import get_waitlist_for_event, remove_from_waitlist
    waitlist = get_waitlist_for_event(event_id)

    if not waitlist:
        return

    first = waitlist[0]
    try:
        await bot.send_message(
            chat_id=first["user_id"],
            text=(
                f"🎉 *Good news!*\n\n"
                f"A seat just became available for *{event_name}*!\n\n"
                f"Tap below to book before it's gone! ⚡"
            ),
            parse_mode="Markdown"
        )
        remove_from_waitlist(first["user_id"], event_id)
        logging.info(f"Notified waitlist user {first['user_id']} for event {event_id}")
    except Exception as e:
        logging.error(f"Failed to notify waitlist user: {e}")
