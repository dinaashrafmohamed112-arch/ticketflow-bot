"""
🎟️ Premium Ticket Generator
=============================
Generates a stunning, professional e-ticket PDF
with logo, QR placeholder, and premium layout.
"""

import os
import math
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER


# ── Brand Colors ─────────────────────────────────────────────
C_BG        = colors.HexColor("#0D0D0D")   # almost black
C_SURFACE   = colors.HexColor("#1A1A1A")   # card bg
C_ACCENT    = colors.HexColor("#C9A84C")   # gold
C_ACCENT2   = colors.HexColor("#E8C97A")   # light gold
C_TEXT      = colors.HexColor("#F5F5F5")   # white text
C_MUTED     = colors.HexColor("#888888")   # grey
C_SUCCESS   = colors.HexColor("#2ECC71")   # green
C_DIVIDER   = colors.HexColor("#2A2A2A")   # subtle divider
C_STAMP_BG  = colors.HexColor("#0A2E1A")   # dark green bg for stamp
C_WHITE     = colors.white


def _draw_logo(c, x, y, size=14):
    """Draw a custom vector logo — stylized T + F (TicketFlow)"""
    # Outer hexagon-like shape
    c.setFillColor(C_ACCENT)
    c.setStrokeColor(C_ACCENT)
    c.setLineWidth(0)
    # Draw diamond shape as logo bg
    pts = [
        (x, y + size),
        (x + size, y),
        (x, y - size),
        (x - size, y),
    ]
    path = c.beginPath()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    path.close()
    c.drawPath(path, fill=True, stroke=False)

    # Inner "T" letter
    c.setFillColor(C_BG)
    c.setFont("Helvetica-Bold", size * 0.9)
    c.drawCentredString(x, y - size * 0.32, "T")


def _draw_decorative_circles(c, width, height):
    """Subtle decorative circles in background"""
    c.saveState()
    c.setFillColor(colors.HexColor("#1F1F1F"))
    c.setStrokeColor(colors.HexColor("#222222"))
    c.setLineWidth(0.5)
    # Large circle top-right
    c.circle(width + 20*mm, height - 10*mm, 60*mm, fill=True, stroke=False)
    # Small circle bottom-left
    c.circle(-10*mm, 30*mm, 35*mm, fill=True, stroke=False)
    c.restoreState()


def _draw_perforation(c, y, width):
    """Draw a dotted perforation line"""
    c.saveState()
    c.setStrokeColor(C_DIVIDER)
    c.setLineWidth(0.8)
    c.setDash(3, 5)
    # Left notch
    c.circle(12*mm, y, 3*mm, fill=True, stroke=False)
    c.setFillColor(C_BG)
    c.circle(12*mm, y, 3*mm, fill=True, stroke=False)
    # Right notch
    c.circle(width - 12*mm, y, 3*mm, fill=True, stroke=False)
    c.setFillColor(C_BG)
    c.circle(width - 12*mm, y, 3*mm, fill=True, stroke=False)
    # Dashed line
    c.line(15*mm, y, width - 15*mm, y)
    c.restoreState()


def _draw_field(c, label, value, x, y, label_size=7, value_size=13, value_color=None):
    """Draw a label + value pair"""
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", label_size)
    c.drawString(x, y + 5*mm, label.upper())

    c.setFillColor(value_color or C_TEXT)
    c.setFont("Helvetica-Bold", value_size)
    c.drawString(x, y, value)


def _draw_booking_stamp(c, booking_id, x, y, size=22):
    """Draw a circular 'CONFIRMED' stamp"""
    # Outer ring
    c.setStrokeColor(C_SUCCESS)
    c.setFillColor(C_STAMP_BG)
    c.setLineWidth(1.5)
    c.circle(x, y, size*mm, fill=True, stroke=True)

    # Inner ring
    c.setStrokeColor(C_SUCCESS)
    c.setLineWidth(0.5)
    c.circle(x, y, (size - 2.5)*mm, fill=False, stroke=True)

    # Text
    c.setFillColor(C_SUCCESS)
    c.setFont("Helvetica-Bold", 6.5)
    c.drawCentredString(x, y + 4*mm, "CONFIRMED")
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x, y - 1*mm, f"#{booking_id:04d}")
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(x, y - 6*mm, "TICKETFLOW")


def generate_ticket_pdf(booking_id: int, user_name: str, event: dict) -> str:
    """
    Generate a premium PDF ticket.
    Returns the file path.
    """
    os.makedirs("temp_tickets", exist_ok=True)
    filepath = os.path.join("temp_tickets", f"ticket_{booking_id:04d}.pdf")

    W, H = A4   # 210 × 297 mm
    c = canvas.Canvas(filepath, pagesize=A4)

    # ── Full page background ──────────────────────────────────
    c.setFillColor(C_BG)
    c.rect(0, 0, W, H, fill=True, stroke=False)

    _draw_decorative_circles(c, W, H)

    # ════════════════════════════════════════
    #   MAIN TICKET CARD
    # ════════════════════════════════════════
    card_x      = 12*mm
    card_w      = W - 24*mm
    card_top    = H - 20*mm
    card_bottom = 45*mm
    card_h      = card_top - card_bottom
    radius      = 6

    # Card shadow (offset rect)
    c.setFillColor(colors.HexColor("#050505"))
    c.roundRect(card_x + 1.5*mm, card_bottom - 1.5*mm, card_w, card_h,
                radius=radius, fill=True, stroke=False)

    # Card surface
    c.setFillColor(C_SURFACE)
    c.roundRect(card_x, card_bottom, card_w, card_h,
                radius=radius, fill=True, stroke=False)

    # ── Gold top border ───────────────────────────────────────
    c.setFillColor(C_ACCENT)
    c.roundRect(card_x, card_top - 3*mm, card_w, 3*mm,
                radius=radius, fill=True, stroke=False)

    # ════════════════════════════════════════
    #   HEADER SECTION (inside card)
    # ════════════════════════════════════════
    header_top = card_top - 3*mm
    header_h   = 55*mm

    # Header bg gradient-like (slightly lighter)
    c.setFillColor(colors.HexColor("#202020"))
    c.roundRect(card_x, header_top - header_h, card_w, header_h,
                radius=0, fill=True, stroke=False)
    # Fix corners at bottom
    c.rect(card_x, header_top - header_h, card_w, 6, fill=True, stroke=False)

    # Logo + Brand name
    logo_x = card_x + 12*mm
    logo_y = header_top - 14*mm
    _draw_logo(c, logo_x, logo_y, size=7*mm)

    c.setFillColor(C_ACCENT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(logo_x + 10*mm, logo_y + 1*mm, "TICKETFLOW")
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 6.5)
    c.drawString(logo_x + 10*mm, logo_y - 4.5*mm, "OFFICIAL E-TICKET")

    # "E-TICKET" badge (top right)
    badge_x = card_x + card_w - 35*mm
    badge_y = header_top - 18*mm
    c.setFillColor(C_ACCENT)
    c.roundRect(badge_x, badge_y, 23*mm, 8*mm, radius=3, fill=True, stroke=False)
    c.setFillColor(C_BG)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(badge_x + 11.5*mm, badge_y + 2.5*mm, "E-TICKET")

    # Event name (large)
    event_name = event.get("name", "Event")
    font_size  = 20 if len(event_name) <= 22 else 15 if len(event_name) <= 32 else 12
    c.setFillColor(C_TEXT)
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(card_x + 12*mm, header_top - 36*mm, event_name)

    # Date pill
    date_y = header_top - 47*mm
    c.setFillColor(colors.HexColor("#2A2A2A"))
    c.roundRect(card_x + 12*mm, date_y - 1.5*mm, 80*mm, 8*mm,
                radius=3, fill=True, stroke=False)
    c.setFillColor(C_ACCENT)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(card_x + 14.5*mm, date_y + 1*mm, f"📅  {event.get('date', '')}")

    # ════════════════════════════════════════
    #   PERFORATION LINE
    # ════════════════════════════════════════
    perf_y = header_top - header_h
    _draw_perforation(c, perf_y, W)

    # ════════════════════════════════════════
    #   DETAILS SECTION
    # ════════════════════════════════════════
    det_top = perf_y - 8*mm
    col1_x  = card_x + 12*mm
    col2_x  = card_x + card_w / 2

    price_text = f"EGP {event.get('price', 0):.0f}" if event.get("price", 0) > 0 else "FREE"

    _draw_field(c, "Attendee",    user_name,    col1_x, det_top)
    _draw_field(c, "Venue",       event.get("venue", ""), col1_x, det_top - 22*mm)
    _draw_field(c, "Booking ID",  f"#{booking_id:04d}", col2_x, det_top,
                value_color=C_ACCENT)
    _draw_field(c, "Price",       price_text,   col2_x, det_top - 22*mm,
                value_color=C_SUCCESS if event.get("price", 0) == 0 else C_TEXT)

    # Divider
    c.setStrokeColor(C_DIVIDER)
    c.setLineWidth(0.5)
    c.line(col1_x, det_top - 33*mm, card_x + card_w - 12*mm, det_top - 33*mm)

    # ════════════════════════════════════════
    #   STAMP + FOOTER INSIDE CARD
    # ════════════════════════════════════════
    stamp_x = card_x + card_w - 32*mm
    stamp_y = card_bottom + 28*mm
    _draw_booking_stamp(c, booking_id, stamp_x, stamp_y)

    # Notice text
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 6.5)
    notice_x = col1_x
    notice_y = card_bottom + 20*mm
    c.drawString(notice_x, notice_y,      "Valid for one person only  •  Non-transferable")
    c.drawString(notice_x, notice_y - 5*mm, "Please present this ticket (printed or digital) at the entrance")

    # ════════════════════════════════════════
    #   BOTTOM STRIP (outside card)
    # ════════════════════════════════════════
    strip_h = 12*mm
    c.setFillColor(C_ACCENT)
    c.rect(0, 0, W, strip_h, fill=True, stroke=False)

    c.setFillColor(C_BG)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(W / 2, strip_h / 2 - 1.5*mm,
                        f"TICKETFLOW  •  Powered by TicketFlow Bot  •  Non-refundable after 24h of booking")

    # ════════════════════════════════════════
    #   BOOKING ID watermark (subtle)
    # ════════════════════════════════════════
    c.saveState()
    c.setFillColor(colors.HexColor("#1C1C1C"))
    c.setFont("Helvetica-Bold", 60)
    c.rotate(35)
    c.drawCentredString(200*mm, 10*mm, f"#{booking_id:04d}")
    c.restoreState()

    c.save()
    return filepath
