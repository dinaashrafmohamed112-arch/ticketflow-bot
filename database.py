"""
🗄️ Database — PostgreSQL or SQLite
===================================
Tables: events, bookings, payments, promo_codes, waitlist
Set USE_SQLITE=1 in .env for local demo without PostgreSQL.
"""

import os
import sqlite3
from pathlib import Path

import psycopg2
import psycopg2.extras

from config import DATABASE_URL

USE_SQLITE = os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes")
SQLITE_PATH = Path(__file__).parent / "local.db"
PH = "?" if USE_SQLITE else "%s"


def get_connection():
    if USE_SQLITE:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    return psycopg2.connect(DATABASE_URL)


def _dict_cur(conn):
    if USE_SQLITE:
        return conn.cursor()
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def _row(row):
    if not row:
        return None
    if USE_SQLITE:
        return dict(row)
    return row


def _rows(rows):
    if USE_SQLITE:
        return [dict(r) for r in rows]
    return rows


def _now_expr():
    return "datetime('now')" if USE_SQLITE else "NOW()"


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    if USE_SQLITE:
        id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
        ts_default = "DEFAULT CURRENT_TIMESTAMP"
    else:
        id_type = "SERIAL PRIMARY KEY"
        ts_default = "DEFAULT NOW()"

    cur.execute(f"""CREATE TABLE IF NOT EXISTS events (
        id {id_type}, name TEXT NOT NULL, date TEXT NOT NULL,
        venue TEXT NOT NULL, capacity INTEGER NOT NULL, booked INTEGER DEFAULT 0,
        price REAL DEFAULT 0, created_at TIMESTAMP {ts_default})""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS bookings (
        id {id_type}, user_id BIGINT NOT NULL, username TEXT,
        event_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending', discount REAL DEFAULT 0,
        final_price REAL DEFAULT 0, booked_at TIMESTAMP {ts_default},
        FOREIGN KEY(event_id) REFERENCES events(id))""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS payments (
        id {id_type}, booking_id INTEGER NOT NULL, user_id BIGINT NOT NULL,
        username TEXT, event_id INTEGER NOT NULL,
        amount REAL, method TEXT, screenshot_id TEXT,
        status TEXT DEFAULT 'pending', created_at TIMESTAMP {ts_default},
        FOREIGN KEY(booking_id) REFERENCES bookings(id))""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS promo_codes (
        id {id_type}, code TEXT NOT NULL UNIQUE,
        discount_pct INTEGER NOT NULL, max_uses INTEGER DEFAULT 100,
        used_count INTEGER DEFAULT 0, active INTEGER DEFAULT 1,
        expires_at TIMESTAMP, created_at TIMESTAMP {ts_default})""")

    cur.execute(f"""CREATE TABLE IF NOT EXISTS waitlist (
        id {id_type}, user_id BIGINT NOT NULL, username TEXT,
        event_id INTEGER NOT NULL,
        joined_at TIMESTAMP {ts_default},
        FOREIGN KEY(event_id) REFERENCES events(id),
        UNIQUE(user_id, event_id))""")

    conn.commit()
    cur.close()
    conn.close()
    backend = "SQLite" if USE_SQLITE else "PostgreSQL"
    print(f"[OK] {backend} Database ready")


# ── Events ────────────────────────────────────────────────────

def get_all_events():
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute("SELECT * FROM events ORDER BY date")
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


def get_available_events():
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute("SELECT * FROM events WHERE capacity > booked ORDER BY date")
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


def get_event(event_id):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(f"SELECT * FROM events WHERE id={PH}", (event_id,))
    r = _row(cur.fetchone()); cur.close(); conn.close(); return r


def add_event(name, date, venue, capacity, price):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        f"INSERT INTO events (name,date,venue,capacity,price) VALUES({PH},{PH},{PH},{PH},{PH})",
        (name, date, venue, capacity, price),
    )
    conn.commit(); cur.close(); conn.close()


def delete_event(event_id):
    conn = get_connection(); cur = conn.cursor()
    for tbl in ("payments", "bookings", "waitlist"):
        cur.execute(f"DELETE FROM {tbl} WHERE event_id={PH}", (event_id,))
    cur.execute(f"DELETE FROM events WHERE id={PH}", (event_id,))
    conn.commit(); cur.close(); conn.close()


# ── Bookings ──────────────────────────────────────────────────

def create_pending_booking(user_id, username, event_id, discount=0, final_price=None):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(
        f"SELECT id FROM bookings WHERE user_id={PH} AND event_id={PH} AND status IN ('pending','confirmed')",
        (user_id, event_id),
    )
    if cur.fetchone():
        cur.close(); conn.close(); return False, "already_booked"
    cur.execute(f"SELECT capacity,booked,price FROM events WHERE id={PH}", (event_id,))
    ev = _row(cur.fetchone())
    if not ev or ev["booked"] >= ev["capacity"]:
        cur.close(); conn.close(); return False, "no_seats"
    fp = final_price if final_price is not None else ev["price"]
    if USE_SQLITE:
        cur.execute(
            f"""INSERT INTO bookings (user_id,username,event_id,status,discount,final_price)
                VALUES({PH},{PH},{PH},'pending',{PH},{PH})""",
            (user_id, username, event_id, discount, fp),
        )
        bid = cur.lastrowid
    else:
        cur.execute(
            f"""INSERT INTO bookings (user_id,username,event_id,status,discount,final_price)
                VALUES({PH},{PH},{PH},'pending',{PH},{PH}) RETURNING id""",
            (user_id, username, event_id, discount, fp),
        )
        bid = cur.fetchone()["id"]
    cur.execute(f"UPDATE events SET booked=booked+1 WHERE id={PH}", (event_id,))
    conn.commit(); cur.close(); conn.close()
    return True, bid


def confirm_booking_payment(booking_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"UPDATE bookings SET status='confirmed' WHERE id={PH}", (booking_id,))
    cur.execute(f"UPDATE payments SET status='approved' WHERE booking_id={PH}", (booking_id,))
    conn.commit(); cur.close(); conn.close()


def reject_booking_payment(booking_id):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(f"SELECT event_id FROM bookings WHERE id={PH}", (booking_id,))
    b = _row(cur.fetchone())
    if b:
        cur.execute(f"UPDATE bookings SET status='cancelled' WHERE id={PH}", (booking_id,))
        cur.execute(f"UPDATE payments SET status='rejected' WHERE booking_id={PH}", (booking_id,))
        cur.execute(f"UPDATE events SET booked=booked-1 WHERE id={PH}", (b["event_id"],))
    conn.commit(); cur.close(); conn.close()


def get_user_bookings(user_id):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(
        f"""SELECT b.id,b.status,b.booked_at,b.discount,b.final_price,
                   e.name,e.date,e.venue,e.price
            FROM bookings b JOIN events e ON b.event_id=e.id
            WHERE b.user_id={PH} ORDER BY b.booked_at DESC""",
        (user_id,),
    )
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


def cancel_booking(booking_id, user_id):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(
        f"SELECT event_id FROM bookings WHERE id={PH} AND user_id={PH} AND status IN ('pending','confirmed')",
        (booking_id, user_id),
    )
    b = _row(cur.fetchone())
    if not b:
        cur.close(); conn.close(); return False
    cur.execute(f"UPDATE bookings SET status='cancelled' WHERE id={PH}", (booking_id,))
    cur.execute(f"UPDATE events SET booked=booked-1 WHERE id={PH}", (b["event_id"],))
    conn.commit(); cur.close(); conn.close(); return True


def get_all_bookings():
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(
        """SELECT b.id,b.user_id,b.username,b.status,b.booked_at,
                  b.discount,b.final_price,e.name as event_name,e.price
           FROM bookings b JOIN events e ON b.event_id=e.id
           ORDER BY b.booked_at DESC LIMIT 100"""
    )
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


def get_confirmed_bookings_for_event(event_id):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(
        f"SELECT user_id,username,id as booking_id FROM bookings WHERE event_id={PH} AND status='confirmed'",
        (event_id,),
    )
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


# ── Payments ──────────────────────────────────────────────────

def create_payment(booking_id, user_id, username, event_id, amount, method, screenshot_id=None):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        f"""INSERT INTO payments (booking_id,user_id,username,event_id,amount,method,screenshot_id)
            VALUES({PH},{PH},{PH},{PH},{PH},{PH},{PH})""",
        (booking_id, user_id, username, event_id, amount, method, screenshot_id),
    )
    conn.commit(); cur.close(); conn.close()


def get_pending_payments():
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(
        """SELECT p.*,e.name as event_name,e.price,b.status as booking_status
           FROM payments p JOIN events e ON p.event_id=e.id
           JOIN bookings b ON p.booking_id=b.id
           WHERE p.status='pending' ORDER BY p.created_at DESC"""
    )
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


def get_payment_by_booking(booking_id):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(f"SELECT * FROM payments WHERE booking_id={PH}", (booking_id,))
    r = _row(cur.fetchone()); cur.close(); conn.close(); return r


# ── Promo Codes ───────────────────────────────────────────────

def validate_promo_code(code):
    conn = get_connection(); cur = _dict_cur(conn)
    now = _now_expr()
    active = "active=1" if USE_SQLITE else "active=TRUE"
    cur.execute(
        f"""SELECT * FROM promo_codes WHERE UPPER(code)=UPPER({PH})
            AND {active} AND used_count<max_uses
            AND (expires_at IS NULL OR expires_at>{now})""",
        (code,),
    )
    r = _row(cur.fetchone()); cur.close(); conn.close(); return r


def use_promo_code(code):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"UPDATE promo_codes SET used_count=used_count+1 WHERE UPPER(code)=UPPER({PH})", (code,))
    conn.commit(); cur.close(); conn.close()


def add_promo_code(code, discount_pct, max_uses=100, expires_at=None):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        f"""INSERT INTO promo_codes (code,discount_pct,max_uses,expires_at)
            VALUES({PH},{PH},{PH},{PH}) ON CONFLICT(code) DO UPDATE
            SET discount_pct={PH},max_uses={PH},active={1 if USE_SQLITE else 'TRUE'}""",
        (code.upper(), discount_pct, max_uses, expires_at, discount_pct, max_uses),
    )
    conn.commit(); cur.close(); conn.close()


def get_all_promo_codes():
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute("SELECT * FROM promo_codes ORDER BY created_at DESC")
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


# ── Waitlist ──────────────────────────────────────────────────

def add_to_waitlist(user_id, username, event_id):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO waitlist (user_id,username,event_id) VALUES({PH},{PH},{PH})",
            (user_id, username, event_id),
        )
        conn.commit(); cur.close(); conn.close(); return True
    except (sqlite3.IntegrityError, psycopg2.errors.UniqueViolation):
        conn.rollback(); cur.close(); conn.close(); return False


def get_waitlist_for_event(event_id):
    conn = get_connection(); cur = _dict_cur(conn)
    cur.execute(f"SELECT * FROM waitlist WHERE event_id={PH} ORDER BY joined_at", (event_id,))
    r = _rows(cur.fetchall()); cur.close(); conn.close(); return r


def remove_from_waitlist(user_id, event_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"DELETE FROM waitlist WHERE user_id={PH} AND event_id={PH}", (user_id, event_id))
    conn.commit(); cur.close(); conn.close()


# ── Sales Report ──────────────────────────────────────────────

def get_sales_report():
    conn = get_connection(); cur = _dict_cur(conn)
    if USE_SQLITE:
        cur.execute(
            """SELECT e.name,e.date,e.venue,e.capacity,e.booked,e.price,
                      COUNT(CASE WHEN b.status='confirmed' THEN 1 END) as confirmed_count,
                      COALESCE(SUM(CASE WHEN b.status='confirmed' THEN b.final_price END),0) as total_revenue
               FROM events e LEFT JOIN bookings b ON e.id=b.event_id
               GROUP BY e.id ORDER BY e.date"""
        )
        cur.execute(
            """SELECT COUNT(CASE WHEN status='confirmed' THEN 1 END) as total_confirmed,
                      COUNT(CASE WHEN status='pending' THEN 1 END) as total_pending,
                      COUNT(CASE WHEN status='cancelled' THEN 1 END) as total_cancelled,
                      COALESCE(SUM(CASE WHEN status='confirmed' THEN final_price END),0) as total_revenue
               FROM bookings"""
        )
    else:
        cur.execute(
            """SELECT e.name,e.date,e.venue,e.capacity,e.booked,e.price,
                      COUNT(b.id) FILTER(WHERE b.status='confirmed') as confirmed_count,
                      COALESCE(SUM(b.final_price) FILTER(WHERE b.status='confirmed'),0) as total_revenue
               FROM events e LEFT JOIN bookings b ON e.id=b.event_id
               GROUP BY e.id ORDER BY e.date"""
        )
        cur.execute(
            """SELECT COUNT(*) FILTER(WHERE status='confirmed') as total_confirmed,
                      COUNT(*) FILTER(WHERE status='pending') as total_pending,
                      COUNT(*) FILTER(WHERE status='cancelled') as total_cancelled,
                      COALESCE(SUM(final_price) FILTER(WHERE status='confirmed'),0) as total_revenue
               FROM bookings"""
        )
    events = _rows(cur.fetchall())
    stats = _row(cur.fetchone())
    cur.close(); conn.close()
    return events, stats


init_db()
