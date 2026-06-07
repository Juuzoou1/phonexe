"""Dark theme palette and Qt stylesheet, modeled on the approved mockups."""

from __future__ import annotations

# Core palette — design brief values, deepened for a darker look.
BG = "#02060B"          # window background (near-black)
PANEL = "#060D16"       # main panels
CARD = "#0A131E"        # cards / inner surfaces
PANEL_ALT = CARD        # alias used across the UI
BORDER = "#11233A"      # borders
TEXT = "#F4F8FC"        # text primary
TEXT_DIM = "#90A6BC"    # text secondary
ACCENT = "#4FE3E0"      # primary accent (cyan)
ACCENT2 = "#24A8FF"     # secondary accent (blue)
ACCENT_DIM = "#1f7e7c"  # darker accent
OK = "#21D07A"          # success / connected
WARN = "#F7B731"        # warning
DANGER = "#FF5B5B"      # danger / end exam / deleted

# Corner radii (px) from the brief.
RADIUS_CARD = 12
RADIUS_BTN = 10
RADIUS_INPUT = 8

# Soft cyan glow used on key panels.
GLOW = "rgba(79,227,224,0.08)"

# Preferred font stack — IBM Plex Sans Arabic primary, per the brief.
FONT_STACK = ("'IBM Plex Sans Arabic', 'Cairo', 'Segoe UI', "
              "'Tahoma', 'Arial'")

# Stat-card numbers are the teal accent in the design, with one warm accent.
STAT_COLORS = [ACCENT, ACCENT, ACCENT, "#7EA0B8", ACCENT, ACCENT]


def stylesheet() -> str:
    return f"""
* {{
    font-family: {FONT_STACK};
    color: {TEXT};
    outline: none;
}}
QMainWindow {{ background: {BG}; }}
/* #root is painted in code (dark base + ambient glow) */

/* ---- top bar ---- */
QWidget#topbar {{
    background: {PANEL_ALT};
    border-bottom: 1px solid {BORDER};
}}
QLabel#appTitle {{ font-size: 16px; font-weight: 700; color: {TEXT}; }}
QLabel#appSubtitle {{ font-size: 11px; color: {TEXT_DIM}; }}
QLabel#clock {{ font-size: 15px; font-weight: 600; color: {ACCENT}; }}
QLabel#clockDate {{ font-size: 11px; color: {TEXT_DIM}; }}

/* ---- top nav buttons ---- */
QPushButton#navBtn {{
    background: transparent; border: none; padding: 10px 16px;
    color: {TEXT_DIM}; font-size: 13px; border-radius: 8px;
}}
QPushButton#navBtn:hover {{ color: {TEXT}; background: {PANEL}; }}
QPushButton#navBtn:checked {{
    color: {ACCENT}; background: {PANEL};
    border-bottom: 2px solid {ACCENT};
}}

/* ---- panels / cards ---- */
QFrame#panel, QFrame#card {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
}}
QLabel#panelTitle {{ font-size: 13px; font-weight: 600; color: {TEXT}; }}
QLabel#sectionHeader {{ font-size: 12px; color: {TEXT_DIM}; font-weight: 600; }}

/* ---- sidebar section buttons ---- */
QPushButton#sectionBtn {{
    background: transparent; border: none; text-align: left;
    padding: 11px 14px; color: {TEXT_DIM}; font-size: 13px; border-radius: 8px;
}}
QPushButton#sectionBtn:hover {{ background: {PANEL_ALT}; color: {TEXT}; }}
QPushButton#sectionBtn:checked {{
    background: {PANEL_ALT}; color: {ACCENT};
    border-left: 3px solid {ACCENT};
}}

/* ---- buttons ---- */
QPushButton#primary {{
    background: {ACCENT_DIM}; color: {TEXT}; border: 1px solid {ACCENT};
    border-radius: 10px; padding: 9px 16px; font-weight: 600;
}}
QPushButton#primary:hover {{ background: {ACCENT}; color: {BG}; }}
QPushButton#ghost {{
    background: transparent; color: {TEXT_DIM}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 8px 14px;
}}
QPushButton#ghost:hover {{ color: {TEXT}; border-color: {ACCENT}; }}
QPushButton#danger {{
    background: transparent; color: {DANGER}; border: 1px solid {DANGER};
    border-radius: 8px; padding: 10px 14px; font-weight: 600;
}}
QPushButton#danger:hover {{ background: {DANGER}; color: {TEXT}; }}

/* ---- stat cards ---- */
QFrame#statCard {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
}}
QLabel#statValue {{ font-size: 26px; font-weight: 700; }}
QLabel#statLabel {{ font-size: 12px; color: {TEXT_DIM}; }}

/* ---- tables ---- */
QTableView, QTableWidget {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px;
    gridline-color: {BORDER}; selection-background-color: {ACCENT_DIM};
    selection-color: {TEXT};
}}
QHeaderView::section {{
    background: {PANEL_ALT}; color: {TEXT_DIM}; border: none;
    border-bottom: 1px solid {BORDER}; padding: 8px; font-weight: 600;
}}
QTableWidget::item {{ padding: 6px; }}

/* ---- inputs ---- */
QLineEdit {{
    background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 8px 12px; color: {TEXT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}

/* ---- device card ---- */
QFrame#deviceCard {{
    background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 10px;
}}
QLabel#deviceName {{ font-size: 14px; font-weight: 700; }}
QLabel#deviceMeta {{ font-size: 11px; color: {TEXT_DIM}; }}
QLabel#statusOk {{ color: {OK}; font-size: 11px; font-weight: 600; }}
QLabel#noteLabel {{ color: {TEXT_DIM}; font-size: 11px; }}

/* ---- scrollbars ---- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT_DIM}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 30px; }}
"""
