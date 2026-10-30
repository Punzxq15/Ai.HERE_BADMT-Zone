"""
ui/pages/admin/common.py
ตัวช่วยร่วมของหน้าแอดมินทุกหน้า (ส่วน F) — คลาสฐาน AdminPage, สไตล์ปุ่ม/ช่องกรอก/ป้าย, ตารางแถว,
ตัวแบ่งหน้า, ดูรูปขยาย, เปิดไฟล์, ตัวแปลงตัวเลข
ปรับปรุงตาม T01 (ฟอนต์กลาง Kanit/Arimo) และ T14 (ลดช่องว่างเกินจำเป็นใน page_header เมื่อหน้าไม่มีปุ่ม actions)
"""

import os
import subprocess
import sys
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from core.constants import ROLE_OWNER
from core.session import Session
from ui.theme import FONT_FAMILY, ThemeManager
from utils import image_utils

# ค่าสำรอง ถ้า ThemeManager ไม่มีชื่อสีนั้น (light, dark)
_DEFAULT_COLORS = {
    "background": ("#F6F7F9", "#101216"),
    "surface": ("#FFFFFF", "#1A1D24"),
    "surface_alt": ("#ECEFF4", "#252A34"),
    "text": ("#111318", "#F8FAFC"),
    "text_main": ("#111318", "#F8FAFC"),
    "text_muted": ("#334155", "#CBD5E1"),
    "border": ("#CBD5E1", "#333A48"),
    "success": ("#16A34A", "#22C55E"),
    "warning": ("#D97706", "#F59E0B"),
    "danger": ("#E63946", "#EF4444"),
    "primary": ("#FFB703", "#FFB703"),
    "info": ("#0284C7", "#38BDF8"),
    "muted": ("#475569", "#64748B"),
}
_FONT_SIZES = {"h1": 28, "h2": 22, "h3": 18, "body": 14, "body_bold": 14, "small": 12,
               "small_bold": 12, "tiny": 10, "price": 15, "price_big": 22}


def color(name):
    """คืนคู่สี (light, dark) หรือสีเดี่ยว — ใช้ของ ThemeManager ก่อน ไม่มีค่อยใช้ค่าสำรอง"""
    if name in _DEFAULT_COLORS:
        try:
            value = ThemeManager.get_color_pair(name)
            if value:
                return value
        except Exception:  # noqa: BLE001
            pass
        return _DEFAULT_COLORS[name]
    try:
        return ThemeManager.get_color_pair(name)
    except Exception:  # noqa: BLE001
        return _DEFAULT_COLORS["text"]


def resolve_color(value):
    """แปลงคู่สีเป็นสีเดียวตามโหมดปัจจุบัน (สำหรับ tk.Canvas ที่ไม่รองรับคู่สี)"""
    if isinstance(value, (tuple, list)):
        return value[1] if ctk.get_appearance_mode() == "Dark" else value[0]
    return value


def font(name="body"):
    try:
        return ThemeManager.get_font(name)
    except Exception:  # noqa: BLE001
        weight = "bold" if name.startswith("h") or name.endswith("_bold") or name.startswith("price") else "normal"
        return (FONT_FAMILY, _FONT_SIZES.get(name, 14), weight)


def as_dict(row):
    """sqlite3.Row / dict / None → dict"""
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:  # noqa: BLE001
        return {}


def is_owner():
    return Session.get_role() == ROLE_OWNER


# ---------------------------------------------------------------------- วิดเจ็ตพื้นฐาน
def btn(parent, text, command, kind="primary", size="sm", **kw):
    """ปุ่มตามสไตล์ธีม (รวม kw ทับค่าเดิม ไม่ให้ส่งคีย์ซ้ำ)"""
    style = dict(ThemeManager.button_style(kind, size))
    style.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **style)


def segmented(parent, values, command=None, **kw):
    """CTkSegmentedButton ที่สีตัวอักษรตัดกับพื้นหลังชัดเจนทั้งแท็บที่เลือกและไม่ได้เลือก (ข้อ 16)"""
    style = dict(ThemeManager.segmented_style())
    style.update(kw)
    return ctk.CTkSegmentedButton(parent, values=list(values), command=command, **style)


def entry(parent, placeholder=None, height=36, **kw):
    style = dict(ThemeManager.entry_style(height))
    style.update(kw)
    if placeholder:
        style["placeholder_text"] = placeholder
    return ctk.CTkEntry(parent, **style)


def option_menu(parent, values, variable=None, command=None, width=160, height=36):
    return ctk.CTkOptionMenu(
        parent, values=list(values) or [""], variable=variable, command=command, width=width, height=height,
        font=font("body"), dropdown_font=font("body"), fg_color=color("surface_alt"),
        button_color=color("border"), text_color=color("text"), dropdown_text_color=color("text"),
        dropdown_fg_color=color("surface"),
    )


def card(parent, **kw):
    try:
        return ThemeManager.make_card(parent, **kw)
    except Exception:  # noqa: BLE001
        return ctk.CTkFrame(parent, corner_radius=12, fg_color=color("surface"), **kw)


def label(parent, text="", style="body", muted=False, **kw):
    if muted:
        kw.setdefault("text_color", color("text_muted"))
    else:
        kw.setdefault("text_color", color("text_main"))
    kw.setdefault("anchor", "w")
    return ctk.CTkLabel(parent, text=text, font=font(style), **kw)


def pill(parent, text, kind="muted"):
    """ป้ายสีเล็ก ๆ kind = success|warning|danger|info|muted|primary|offline|online|suspended"""
    bg, fg = ThemeManager.badge_colors(kind)
    return ctk.CTkLabel(parent, text=f"  {text}  ", height=24, corner_radius=11, font=font("small_bold"),
                        fg_color=bg, text_color=fg)


def error_label(parent, **kw):
    kw.setdefault("wraplength", 760)
    return ctk.CTkLabel(parent, text="", text_color=color("danger"), font=font("small"),
                        anchor="w", justify="left", **kw)


def page_header(parent, title, subtitle=None):
    """
    หัวหน้า: ชื่อ/คำอธิบายซ้าย, ปุ่มขวา → (header, actions_frame)
    T14: กำหนด width=1, height=1 ให้ actions เพื่อไม่ให้ CTkFrame ว่างมีขนาดเริ่มต้น 200px จนเกิดช่องว่างโล่งผิดปกติ
    """
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", pady=(0, 6))
    left = ctk.CTkFrame(header, fg_color="transparent")
    left.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(left, text=title, font=font("h2"), text_color=color("text_main"), anchor="w").pack(anchor="w")
    if subtitle:
        label(left, subtitle, "small", muted=True).pack(anchor="w", pady=(1, 0))
    actions = ctk.CTkFrame(header, fg_color="transparent", width=1, height=1)
    actions.pack(side="right", anchor="ne")
    return header, actions


def stat_card(parent, title, value, note=None, command=None, value_color=None):
    """การ์ดตัวเลขสรุป (คลิกได้ถ้ามี command)"""
    box = card(parent)
    label(box, title, "small", muted=True).pack(fill="x", padx=14, pady=(12, 0))
    value_label = ctk.CTkLabel(box, text=str(value), font=font("h2"), text_color=color("text_main"), anchor="w")
    if value_color:
        value_label.configure(text_color=value_color)
    value_label.pack(fill="x", padx=14, pady=(0, 2))
    note_label = None
    if note:
        note_label = label(box, note, "tiny", muted=True)
        note_label.pack(fill="x", padx=14, pady=(0, 10))
    else:
        ctk.CTkFrame(box, height=8, fg_color="transparent").pack()
    if command:
        for widget in (box, value_label, *box.winfo_children()):
            try:
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda _e: command())
            except Exception:  # noqa: BLE001
                pass
    return box


def place_grid(widgets, columns):
    """วางวิดเจ็ตเป็นกริด n คอลัมน์ ความกว้างเท่ากัน (ทุกตัวต้องมี parent เดียวกัน)"""
    if not widgets:
        return
    parent = widgets[0].master
    for c in range(columns):
        parent.grid_columnconfigure(c, weight=1, uniform="cards")
    for i, widget in enumerate(widgets):
        widget.grid(row=i // columns, column=i % columns, sticky="nsew", padx=5, pady=5)


def configure_columns(frame, spec):
    """spec = [(weight, minsize), ...] สำหรับแถวตาราง"""
    for i, (weight, minsize) in enumerate(spec):
        frame.grid_columnconfigure(i, weight=weight, minsize=minsize)


def table_header(parent, spec, titles):
    row = ctk.CTkFrame(parent, fg_color=color("surface_alt"), corner_radius=8)
    row.pack(fill="x", pady=(0, 4))
    configure_columns(row, spec)
    for i, text in enumerate(titles):
        ctk.CTkLabel(row, text=text, font=font("small_bold"), anchor="w",
                     text_color=color("text_main")).grid(row=0, column=i, sticky="w", padx=8, pady=6)
    return row


def table_row(parent, spec):
    row = card(parent)
    row.pack(fill="x", pady=2)
    configure_columns(row, spec)
    return row


def empty_state(parent, text):
    return ctk.CTkLabel(parent, text=text, font=font("body"), text_color=color("text_muted")).pack(pady=30)


class Pager(ctk.CTkFrame):
    """ตัวแบ่งหน้า ‹ ก่อนหน้า | หน้า x / y | ถัดไป ›  — on_change(page) ถูกเรียกเมื่อกด"""

    def __init__(self, parent, on_change):
        super().__init__(parent, fg_color="transparent")
        self._on_change = on_change
        self._page = 1
        self._pages = 1
        self.prev_btn = btn(self, "‹ ก่อนหน้า", self._prev, kind="outline")
        self.prev_btn.pack(side="left")
        self.info = ctk.CTkLabel(self, text="", font=font("small"), text_color=color("text_muted"))
        self.info.pack(side="left", padx=14)
        self.next_btn = btn(self, "ถัดไป ›", self._next, kind="outline")
        self.next_btn.pack(side="left")

    def set(self, page, pages, total=None):
        self._page = max(1, int(page or 1))
        self._pages = max(1, int(pages or 1))
        extra = f"  ·  ทั้งหมด {total:,} รายการ" if total is not None else ""
        self.info.configure(text=f"หน้า {self._page} / {self._pages}{extra}")
        self.prev_btn.configure(state="normal" if self._page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self._page < self._pages else "disabled")

    def _prev(self):
        if self._page > 1:
            self._on_change(self._page - 1)

    def _next(self):
        if self._page < self._pages:
            self._on_change(self._page + 1)


class AdminPage(ctk.CTkFrame):
    """คลาสฐานของหน้าแอดมิน — ดูหัวไฟล์"""

    OWNER_ONLY = False

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=color("background"), corner_radius=0)
        self.controller = controller
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.body.pack(fill="both", expand=True, padx=14, pady=8)
        self.error = error_label(self.body)
        self.content = ctk.CTkFrame(self.body, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

    # ---- ข้อความผิดพลาด
    def set_error(self, message=""):
        if message:
            self.error.configure(text=message)
            if not self.error.winfo_ismapped():
                self.error.pack(fill="x", pady=(0, 8), before=self.content)
        else:
            self.error.configure(text="")
            self.error.pack_forget()

    def call(self, func, *args, **kwargs):
        """เรียก service; ValueError/PermissionError → แสดงข้อความแดง คืน (False, None)"""
        try:
            return True, func(*args, **kwargs)
        except (ValueError, PermissionError) as exc:
            self.set_error(str(exc))
            return False, None

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    def allowed(self):
        """หน้าของเจ้าของร้านเท่านั้น: แอดมินเข้ามา → เด้งกลับแดชบอร์ด (Router กันไว้แล้วอีกชั้น)"""
        if self.OWNER_ONLY and not is_owner():
            self.controller.show("admin_dashboard")
            return False
        return True

    def refresh_shell(self):
        try:
            self.controller.refresh_shell()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------- รูป/ไฟล์
def thumb(parent, path, size=48, cover=True, corner_radius=8):
    """รูปย่อสี่เหลี่ยมจัตุรัส 1:1 (ไม่มี/เสีย → placeholder)"""
    image = image_utils.load_ctk_image(path, (size, size), cover=cover, corner_radius=corner_radius)
    return ctk.CTkLabel(parent, text="", image=image, width=size, height=size)


def load_fit_image(path, max_w, max_h):
    """โหลดรูปแบบรักษาอัตราส่วนให้พอดีกรอบ → CTkImage | None"""
    try:
        if not path:
            return None
        img = Image.open(image_utils.resolve_path(path))
        img.load()
        img = img.convert("RGB")
        img.thumbnail((max_w, max_h))
        return ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
    except Exception:  # noqa: BLE001
        return None


def show_image_window(parent, path, title="ดูรูป"):
    """เปิดหน้าต่างแสดงรูปขยาย (เช่น สลิปโอนเงิน)"""
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry("700x780")
    image = load_fit_image(path, 660, 720)
    if image is None:
        ctk.CTkLabel(win, text="ไม่พบไฟล์รูป หรือเปิดไฟล์ไม่ได้", font=font("body"),
                     text_color=color("danger")).pack(expand=True)
    else:
        holder = ctk.CTkLabel(win, text="", image=image)
        holder.image = image  # กัน garbage collection
        holder.pack(expand=True, padx=10, pady=10)
    try:
        win.after(150, win.lift)
        win.focus_force()
    except Exception:  # noqa: BLE001
        pass
    return win


def open_file(path):
    """เปิดไฟล์ด้วยโปรแกรมเริ่มต้นของเครื่อง → True/False"""
    try:
        full = str(image_utils.resolve_path(path))
        if sys.platform.startswith("win"):
            os.startfile(full)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", full])
        else:
            subprocess.Popen(["xdg-open", full])
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------- แปลงค่าจากช่องกรอก
def parse_money(text, label_text, required=False, minimum=0.0):
    text = (text or "").strip().replace(",", "")
    if not text:
        if required:
            raise ValueError(f"กรุณากรอก{label_text}")
        return None
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"{label_text}ต้องเป็นตัวเลข") from None
    if value < minimum:
        raise ValueError(f"{label_text}ต้องไม่ต่ำกว่า {minimum:g}")
    return round(value, 2)


def parse_int(text, label_text, required=True, minimum=0):
    text = (text or "").strip().replace(",", "")
    if not text:
        if required:
            raise ValueError(f"กรุณากรอก{label_text}")
        return None
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"{label_text}ต้องเป็นจำนวนเต็ม") from None
    if value < minimum:
        raise ValueError(f"{label_text}ต้องไม่ต่ำกว่า {minimum}")
    return value


def tk_canvas(parent, **kw):
    """tk.Canvas ที่ไม่มีขอบ (ใช้วาดกราฟ)"""
    kw.setdefault("highlightthickness", 0)
    kw.setdefault("bd", 0)
    return tk.Canvas(parent, **kw)
