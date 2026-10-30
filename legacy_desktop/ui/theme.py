"""
ui/theme.py
ธีมกลางของแอป: สีหลัก เหลือง-แดง-ขาว/ดำ และสีเสริมที่หลากหลาย (เขียว/ฟ้า/ม่วง/ส้ม/ชมพู)
ออกแบบให้พื้นหลังและตัวหนังสือสีตัดกันชัดเจน (High Contrast WCAG >= 4.5:1) ทั้งโหมดสว่างและมืด
ตั้งค่าฟอนต์จากจุดเดียว (T01):
  - ฟอนต์ภาษาไทย: Kanit
  - ฟอนต์ภาษาอังกฤษ/ตัวเลข: Arimo
"""

import json
import re
from pathlib import Path

import customtkinter as ctk

# ---------------------------------------------------------------------------
# สี (light, dark) — เน้นสีเหลือง แดง ขาว/ดำ และสีเสริมที่ตัดกันชัดเจน อ่านง่ายทุกหน้าจอ
# ---------------------------------------------------------------------------
COLORS = {
    "primary": {"light": "#FFB703", "dark": "#FFB703"},        # สีเหลืองสปอร์ตหลัก (คู่กับตัวหนังสือสีดำเข้มเสมอ)
    "primary_hover": {"light": "#E5A100", "dark": "#D99600"},  # สีเหลืองเข้มเมื่อ hover
    "secondary": {"light": "#141619", "dark": "#0F1115"},      # สีดำ/เทาเข้มเกือบดำ (Navbar, Sidebar, Header)
    "secondary_hover": {"light": "#252A34", "dark": "#252A34"},
    "background": {"light": "#F6F7F9", "dark": "#101216"},     # สีพื้นหลังหลัก (ขาวอมเทาอ่อน / ดำเข้ม)
    "surface": {"light": "#FFFFFF", "dark": "#1A1D24"},        # สีพื้นการ์ด/ตาราง (ขาวบริสุทธิ์ / เทาดำ)
    "surface_alt": {"light": "#ECEFF4", "dark": "#252A34"},    # สีพื้นรองบนการ์ด/แถวสลับ
    "text": {"light": "#111318", "dark": "#F8FAFC"},           # alias สำหรับ text_main
    "text_main": {"light": "#111318", "dark": "#F8FAFC"},      # สีตัวหนังสือหลัก (ดำเข้มบนพื้นขาว / ขาวสว่างบนพื้นดำ)
    "text_muted": {"light": "#334155", "dark": "#CBD5E1"},     # สีตัวหนังสือรอง (ความตัดกันสูง >= 7:1 ไม่จาง)
    "muted": {"light": "#475569", "dark": "#64748B"},          # สีเทาเข้มที่อ่านตัวหนังสือขาวได้ชัด
    "danger": {"light": "#E63946", "dark": "#EF4444"},         # สีแดงสปอร์ตหลัก (Flash Sale, ราคาโปร, ปุ่มสำคัญ/ลบ)
    "danger_hover": {"light": "#C1121F", "dark": "#DC2626"},   # สีแดงเข้มเมื่อ hover
    "success": {"light": "#16A34A", "dark": "#22C55E"},        # สีเขียว (สำเร็จ/พร้อมส่ง)
    "success_hover": {"light": "#15803D", "dark": "#16A34A"},  # สีเขียวเข้มเมื่อ hover
    "warning": {"light": "#D97706", "dark": "#F59E0B"},        # สีส้มอำพัน (รอดำเนินการ/เตือน)
    "warning_hover": {"light": "#B45309", "dark": "#D97706"},
    "info": {"light": "#0284C7", "dark": "#38BDF8"},           # สีฟ้าน้ำเงิน (ข้อมูล/AI/ตรวจสลิป)
    "info_hover": {"light": "#0369A1", "dark": "#0284C7"},
    "purple": {"light": "#7C3AED", "dark": "#A855F7"},         # สีม่วง (จัดส่งแล้ว/ฟีเจอร์พิเศษ)
    "purple_hover": {"light": "#6D28D9", "dark": "#9333EA"},
    "orange": {"light": "#EA580C", "dark": "#FB923C"},         # สีส้มสด (คูปอง/โปรโมชัน)
    "pink": {"light": "#DB2777", "dark": "#EC4899"},           # สีชมพูเข้ม/โรส (รายการโปรด/หน้าสินค้า T11, T12)
    "pink_hover": {"light": "#BE185D", "dark": "#DB2777"},
    "pink_soft": {"light": "#FCE7F3", "dark": "#3B122B"},      # พื้นชมพูอ่อนตัดกับตัวหนังสือเข้ม/สว่าง
    "blue_soft": {"light": "#E0F2FE", "dark": "#0C2D48"},      # พื้นฟ้าอ่อนตัดกับตัวหนังสือเข้ม/สว่าง
    "green_soft": {"light": "#DCFCE7", "dark": "#0F2E1E"},     # พื้นเขียวอ่อนตัดกับตัวหนังสือเข้ม/สว่าง
    "yellow_soft": {"light": "#FEF3C7", "dark": "#3B2A0A"},    # พื้นเหลืองอ่อนตัดกับตัวหนังสือเข้ม/สว่าง
    "red_soft": {"light": "#FFE4E6", "dark": "#3B1219"},       # พื้นแดงชมพูอ่อนสำหรับกล่องราคา
    "dark_tech": {"light": "#181B22", "dark": "#14171F"},      # พื้นสีเข้มสไตล์เทคนิคสำหรับ Technical Specs
    "border": {"light": "#CBD5E1", "dark": "#333A48"},         # สีขอบการ์ดและช่องกรอก
    "star": {"light": "#FFB703", "dark": "#FFB703"},           # สีดาวรีวิว
    "star_off": {"light": "#CBD5E1", "dark": "#475569"},       # ดาวที่ยังไม่เต็ม
}

# สีตัวอักษรบนปุ่มสีเหลือง (ดำเข้ม อ่านชัดทั้งโหมดสว่างและมืด)
ON_PRIMARY = "#141619"

# ---------------------------------------------------------------------------
# ฟอนต์ (T01: อังกฤษ = Arimo, ไทย = Kanit — กำหนดที่จุดเดียวในไฟล์นี้)
# หมายเหตุ: Tkinter กำหนด font family ได้ 1 ชื่อต่อ widget จึงใช้ Kanit สำหรับข้อความที่มีภาษาไทย
# และมีตัวช่วย get_font(style, text=...) / get_latin_font(style) สำหรับข้อความภาษาอังกฤษล้วน (Arimo)
# ---------------------------------------------------------------------------
FONT_FAMILY_LATIN = "Arimo"
FONT_FAMILY_THAI = "Kanit"
FONT_FAMILY = FONT_FAMILY_THAI

_THAI_CHAR_RE = re.compile(r"[\u0E00-\u0E7F]")

_FONT_SPEC = {
    "h1": (26, "bold"),
    "h2": (20, "bold"),
    "h3": (17, "bold"),
    "body": (14, "normal"),
    "body_bold": (14, "bold"),
    "small": (12, "normal"),
    "small_bold": (12, "bold"),
    "tiny": (11, "normal"),
    "price": (16, "bold"),
    "price_big": (24, "bold"),
}

FONTS = {
    style: (FONT_FAMILY, size, weight)
    for style, (size, weight) in _FONT_SPEC.items()
}

LATIN_FONTS = {
    style: (FONT_FAMILY_LATIN, size, weight)
    for style, (size, weight) in _FONT_SPEC.items()
}

# ---------------------------------------------------------------------------
# สไตล์ปุ่ม: ใช้ ctk.CTkButton(parent, text=..., **ThemeManager.button_style("primary"))
# ---------------------------------------------------------------------------
_BUTTON_KINDS = {
    "primary": dict(fg="primary", hover="primary_hover", text=ON_PRIMARY, border=0),
    "secondary": dict(fg="secondary", hover="secondary_hover", text="#FFFFFF", border=0),
    "danger": dict(fg="danger", hover="danger_hover", text="#FFFFFF", border=0),
    "success": dict(fg="success", hover="success_hover", text="#FFFFFF", border=0),
    "info": dict(fg="info", hover="info_hover", text="#FFFFFF", border=0),
    "purple": dict(fg="purple", hover="purple_hover", text="#FFFFFF", border=0),
    "pink": dict(fg="pink", hover="pink_hover", text="#FFFFFF", border=0),
    "warning": dict(fg="warning", hover="warning_hover", text="#FFFFFF", border=0),
    "ghost": dict(fg="transparent", hover="surface_alt", text="text_main", border=0),
    "outline": dict(fg="surface", hover="surface_alt", text="text_main", border=1),
}
_BUTTON_SIZES = {
    "sm": dict(height=32, corner_radius=6, font="small_bold"),
    "md": dict(height=38, corner_radius=8, font="body_bold"),
    "lg": dict(height=44, corner_radius=10, font="body_bold"),
}

# ---------------------------------------------------------------------------
# ป้ายสถานะออเดอร์ / สลิป / จัดส่ง / ผู้ใช้: (พื้น light/dark, ตัวอักษร light/dark) — สีตัดกันชัดเจน
# ---------------------------------------------------------------------------
_BADGE_STYLES = {
    "warning": (("#FEF3C7", "#451A03"), ("#92400E", "#FDE68A")),
    "info": (("#E0F2FE", "#0C4A6E"), ("#075985", "#7DD3FC")),
    "success": (("#DCFCE7", "#052E16"), ("#166534", "#86EFAC")),
    "purple": (("#F3E8FF", "#2E1065"), ("#5B21B6", "#D8B4FE")),
    "pink": (("#FCE7F3", "#500724"), ("#9D174D", "#FBCFE8")),
    "done": (("#16A34A", "#15803D"), ("#FFFFFF", "#FFFFFF")),
    "danger": (("#FEE2E2", "#450A0A"), ("#991B1B", "#FCA5A5")),
    "primary": (("#FFB703", "#FFB703"), ("#141619", "#141619")),
    "red_solid": (("#E63946", "#E63946"), ("#FFFFFF", "#FFFFFF")),
    "muted": (("#E2E8F0", "#334155"), ("#1E293B", "#F1F5F9")),
    # สถานะผู้ใช้ T13: ออฟไลน์ = สีเทา, ออนไลน์ = สีเขียว, ถูกระงับ = สีแดง
    "offline": (("#E2E8F0", "#334155"), ("#1E293B", "#F1F5F9")),
    "online": (("#DCFCE7", "#14532D"), ("#166534", "#86EFAC")),
    "suspended": (("#FEE2E2", "#450A0A"), ("#991B1B", "#FCA5A5")),
}

# สถานะ → ชนิดป้าย (ใช้ค่า string เดียวกับ core.constants)
STATUS_BADGE_KIND = {
    # ออเดอร์
    "pending": "warning",
    "checking_slip": "info",
    "paid": "success",
    "shipped": "purple",
    "completed": "done",
    "cancelled": "danger",
    "awaiting_review": "primary",
    # สลิป
    "verified": "success",
    "rejected": "danger",
    # จัดส่ง
    "preparing": "warning",
    "delivered": "done",
    # ผู้ใช้ (T13)
    "offline": "offline",
    "online": "online",
    "suspended": "suspended",
}

_PREFS_FILE = "ui_prefs.json"


def _prefs_path() -> Path:
    """path ของไฟล์ค่ากำหนด UI (อยู่ใน data/ ของโปรเจกต์)"""
    try:
        import config
        return Path(config.DATA_DIR) / _PREFS_FILE
    except Exception:  # noqa: BLE001
        return Path(__file__).resolve().parent.parent / "data" / _PREFS_FILE


class ThemeManager:
    FONT_FAMILY = FONT_FAMILY
    FONT_FAMILY_LATIN = FONT_FAMILY_LATIN
    FONT_FAMILY_THAI = FONT_FAMILY_THAI
    _current_mode = "light"  # ค่าเริ่มต้นโหมดสว่างเพื่อให้สีเหลือง-แดง-ขาว-ดำตัดกันชัดเจน

    # ------------------------------------------------------------------ โหมด
    @classmethod
    def setup(cls):
        """ตั้งค่าเริ่มต้นของ CustomTkinter (โหลดโหมดที่บันทึกไว้ครั้งก่อน)"""
        saved = cls._load_saved_mode()
        if saved:
            cls._current_mode = saved
        ctk.set_appearance_mode(cls._current_mode)
        ctk.set_default_color_theme("blue")

    @classmethod
    def set_mode(cls, mode: str, save: bool = True):
        """เปลี่ยน Light/Dark mode (และจำค่าไว้ใช้ครั้งหน้า)"""
        if mode in ("system", "light", "dark"):
            cls._current_mode = mode
            ctk.set_appearance_mode(mode)
            if save:
                cls._save_mode(mode)

    @classmethod
    def toggle_mode(cls):
        """สลับระหว่าง Light และ Dark mode"""
        actual = ctk.get_appearance_mode().lower()
        cls.set_mode("light" if actual == "dark" else "dark")

    @classmethod
    def is_dark(cls) -> bool:
        return ctk.get_appearance_mode().lower() == "dark"

    @classmethod
    def _load_saved_mode(cls):
        try:
            data = json.loads(_prefs_path().read_text(encoding="utf-8"))
            mode = data.get("appearance_mode")
            return mode if mode in ("system", "light", "dark") else None
        except Exception:  # noqa: BLE001
            return None

    @classmethod
    def _save_mode(cls, mode: str):
        try:
            path = _prefs_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"appearance_mode": mode}), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ สี
    @classmethod
    def get_color(cls, color_name: str) -> str:
        """ดึงค่าสี (string เดี่ยว) ตามโหมดปัจจุบัน"""
        mode = ctk.get_appearance_mode().lower()
        if mode not in ("light", "dark"):
            mode = "light"
        return COLORS.get(color_name, {}).get(mode, "#111318")

    @classmethod
    def get_color_pair(cls, color_name: str) -> tuple:
        """ดึงค่าสีเป็น (light, dark) tuple"""
        c = COLORS.get(color_name)
        return (c["light"], c["dark"]) if c else ("#111318", "#F8FAFC")

    # ------------------------------------------------------------------ สไตล์ & ฟอนต์ (T01)
    @staticmethod
    def apply_card_style(widget):
        """สำหรับตกแต่ง Widget ให้ดูเหมือน Card"""
        widget.configure(
            fg_color=ThemeManager.get_color_pair("surface"),
            corner_radius=12,
        )

    @staticmethod
    def get_font(style="body", text: str = None):
        """
        ดึงสไตล์ฟอนต์ (tuple):
        - หากระบุ text ที่เป็นภาษาอังกฤษ/ตัวเลขล้วน (ไม่มีอักษรไทย) จะใช้ Arimo
        - หากมีอักษรไทยหรือไม่ระบุ text จะใช้ Kanit เพื่อรองรับภาษาไทยครบถ้วน
        """
        if text is not None and str(text).strip() and not _THAI_CHAR_RE.search(str(text)):
            return LATIN_FONTS.get(style, LATIN_FONTS["body"])
        return FONTS.get(style, FONTS["body"])

    @staticmethod
    def get_latin_font(style="body", size: int = None, weight: str = None):
        """ดึงสไตล์ฟอนต์ภาษาอังกฤษ Arimo จากจุดเดียว (T01)"""
        base_family, base_size, base_weight = LATIN_FONTS.get(style, LATIN_FONTS["body"])
        return (base_family, int(size or base_size), weight or base_weight)

    @staticmethod
    def get_thai_font(style="body", size: int = None, weight: str = None):
        """ดึงสไตล์ฟอนต์ภาษาไทย Kanit จากจุดเดียว (T01)"""
        base_family, base_size, base_weight = FONTS.get(style, FONTS["body"])
        return (base_family, int(size or base_size), weight or base_weight)

    @staticmethod
    def get_font_obj(style="body", latin: bool = False, **kwargs):
        """ดึงฟอนต์เป็น CTkFont (ใช้เมื่อต้องการ overstrike/underline เช่น ราคาขีดฆ่า)"""
        src = LATIN_FONTS if latin else FONTS
        family, size, weight = src.get(style, src["body"])
        return ctk.CTkFont(family=family, size=size, weight=weight, **kwargs)

    @staticmethod
    def button_style(kind: str = "primary", size: str = "md") -> dict:
        """kwargs สำหรับ CTkButton  kind: primary|secondary|danger|success|info|purple|pink|warning|ghost|outline  size: sm|md|lg"""
        k = _BUTTON_KINDS.get(kind, _BUTTON_KINDS["primary"])
        s = _BUTTON_SIZES.get(size, _BUTTON_SIZES["md"])

        def pair(name):
            if name == "transparent":
                return "transparent"
            if name.startswith("#"):
                return name
            return ThemeManager.get_color_pair(name)

        style = dict(
            fg_color=pair(k["fg"]),
            hover_color=pair(k["hover"]),
            text_color=pair(k["text"]),
            font=FONTS[s["font"]],
            height=s["height"],
            corner_radius=s["corner_radius"],
        )
        if k["border"]:
            style["border_width"] = k["border"]
            style["border_color"] = ThemeManager.get_color_pair("border")
        return style

    @staticmethod
    def segmented_style() -> dict:
        """สไตล์สำหรับ CTkSegmentedButton ให้ตัวหนังสือสีขาวตัดกับพื้นเข้มทั้งแท็บที่เลือกและไม่ได้เลือก"""
        return dict(
            font=FONTS["small_bold"],
            fg_color=("#1E293B", "#0F1115"),
            unselected_color=("#334155", "#252A34"),
            unselected_hover_color=("#475569", "#334155"),
            selected_color=("#E63946", "#E63946"),
            selected_hover_color=("#C1121F", "#DC2626"),
            text_color=("#FFFFFF", "#FFFFFF"),
            text_color_disabled=("#94A3B8", "#64748B"),
        )

    @staticmethod
    def entry_style(height: int = 40) -> dict:
        """kwargs สำหรับ CTkEntry / CTkTextbox ให้หน้าตาเหมือนกันทุกหน้า และอ่านชัด"""
        return dict(
            font=FONTS["body"],
            height=height,
            corner_radius=8,
            border_width=1,
            border_color=ThemeManager.get_color_pair("border"),
            fg_color=ThemeManager.get_color_pair("surface"),
            text_color=ThemeManager.get_color_pair("text_main"),
        )

    @staticmethod
    def make_card(parent, **kwargs):
        """สร้าง CTkFrame หน้าตาการ์ด (พื้น surface + ขอบบาง + มุมมน)"""
        opts = dict(
            fg_color=ThemeManager.get_color_pair("surface"),
            corner_radius=12,
            border_width=1,
            border_color=ThemeManager.get_color_pair("border"),
        )
        opts.update(kwargs)
        return ctk.CTkFrame(parent, **opts)

    @staticmethod
    def badge_colors(kind: str) -> tuple:
        """คืน ((พื้น light, dark), (ตัวอักษร light, dark)) ของป้ายชนิดนั้น"""
        return _BADGE_STYLES.get(kind, _BADGE_STYLES["muted"])

    @staticmethod
    def make_badge(parent, text: str, kind: str = "muted", font_style: str = "small_bold"):
        """ป้ายเล็ก ๆ (CTkLabel มุมมน) kind: warning|info|success|purple|pink|done|danger|primary|red_solid|muted|offline|online|suspended"""
        bg, fg = ThemeManager.badge_colors(kind)
        return ctk.CTkLabel(
            parent, text=f"  {text}  ", font=FONTS[font_style],
            fg_color=bg, text_color=fg, corner_radius=10, height=24,
        )

    @staticmethod
    def status_badge(parent, status: str, label: str = None):
        """ป้ายสถานะ (ออเดอร์/สลิป/จัดส่ง) — label ไม่ใส่ = ใช้ชื่อไทยจาก core.constants"""
        if label is None:
            label = _status_label(status)
        return ThemeManager.make_badge(parent, label, STATUS_BADGE_KIND.get(status, "muted"))


def _status_label(status: str) -> str:
    """หาชื่อไทยของสถานะจาก core.constants (ไม่เจอก็คืนรหัสเดิม)"""
    try:
        from core import constants as c
        for table in (c.ORDER_STATUS_LABELS, c.PAYMENT_STATUS_LABELS, c.SHIPMENT_STATUS_LABELS):
            if status in table:
                return table[status]
    except Exception:  # noqa: BLE001
        pass
    return str(status)


# Module-level font helpers (T01)
get_font = ThemeManager.get_font
get_latin_font = ThemeManager.get_latin_font
get_thai_font = ThemeManager.get_thai_font
