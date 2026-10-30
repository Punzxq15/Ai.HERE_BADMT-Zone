"""
ui/pages/buyer/common.py
ตัวช่วยร่วมของหน้าผู้ซื้อ (ส่วน E): สลับ wishlist, หัวข้อหน้า/หัวข้อส่วน, กริดการ์ดที่ขึ้นบรรทัดใหม่ตามความกว้าง
"""

import customtkinter as ctk

from core.session import Session
from services import account_service
from ui.components import dialogs
from ui.components.product_card import CARD_WIDTH, ProductCard
from ui.theme import ThemeManager


def user_id():
    """id ผู้ใช้ปัจจุบัน (None ถ้ายังไม่ล็อกอิน)"""
    return Session.get_user_id()


def toggle_wishlist(parent, product_id):
    """สลับ wishlist ของผู้ใช้ปัจจุบัน — คืนสถานะใหม่ (True = อยู่ในรายการโปรด) หรือ None ถ้าทำไม่ได้"""
    try:
        result = account_service.toggle_wishlist(user_id(), product_id)
    except (ValueError, PermissionError) as exc:
        dialogs.show_message(parent, "ทำรายการไม่ได้", str(exc), kind="error")
        return None
    return bool(result["in_wishlist"])


def page_title(parent, text, subtitle=None):
    """หัวข้อหน้า (ตัวใหญ่) + คำอธิบายสั้น ๆ (ไม่บังคับ)"""
    box = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        box, text=text, font=ThemeManager.get_font("h2"), anchor="w",
        text_color=ThemeManager.get_color_pair("text_main"),
    ).pack(fill="x")
    if subtitle:
        ctk.CTkLabel(
            box, text=subtitle, font=ThemeManager.get_font("small"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(fill="x")
    return box


def section_header(parent, text, action_text=None, action=None):
    """หัวข้อส่วน + ปุ่มลิงก์ด้านขวา (เช่น \"ดูทั้งหมด ›\")"""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        row, text=text, font=ThemeManager.get_font("h3"), anchor="w",
        text_color=ThemeManager.get_color_pair("text_main"),
    ).pack(side="left")
    if action_text and action:
        ctk.CTkButton(
            row, text=action_text, width=90, command=action, **ThemeManager.button_style("ghost", "sm"),
        ).pack(side="right")
    return row


def error_label(parent, **kwargs):
    """ข้อความผิดพลาดสีแดง (เริ่มต้นว่าง) — ตั้งข้อความด้วย .configure(text=...)"""
    return ctk.CTkLabel(
        parent, text="", font=ThemeManager.get_font("small"), anchor="w", justify="left",
        text_color=ThemeManager.get_color_pair("danger"), **kwargs,
    )


def product_cards(parent, items, controller, width=CARD_WIDTH):
    """สร้างการ์ดสินค้าจากรายการ (parent ต้องเป็น WrapGrid ที่จะรับไปจัดเรียง)"""
    def open_product(pid):
        controller.show("product_detail", product_id=pid)

    return [
        ProductCard(
            parent, item, on_open=open_product,
            on_wishlist=lambda pid: toggle_wishlist(parent, pid), width=width,
        )
        for item in items
    ]


class WrapGrid(ctk.CTkFrame):
    """กรอบที่จัดวิดเจ็ตเป็นแถว ๆ และขึ้นบรรทัดใหม่เองตามความกว้าง (ไม่มีแถบเลื่อนของตัวเอง)

    ใช้งาน: cards = [ProductCard(wrap, ...), ...]  แล้ว wrap.set_items(cards)
    (วิดเจ็ตต้องสร้างโดยมี wrap เป็น parent; ชุดเก่าที่ไม่อยู่ในชุดใหม่จะถูกทำลายให้)
    """

    def __init__(self, parent, item_width=CARD_WIDTH, gap=12):
        super().__init__(parent, fg_color="transparent")
        self._item_width = item_width
        self._gap = gap
        self._items = []
        self._cols = 0
        self._job = None
        self.bind("<Configure>", self._on_configure)

    def set_items(self, widgets):
        new = list(widgets)
        for old in self._items:
            if old not in new:
                old.destroy()
        self._items = new
        self._layout(force=True)

    def clear(self):
        self.set_items([])

    def _on_configure(self, _event=None):
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(100, self._layout)

    def _layout(self, force=False):
        self._job = None
        if not self._items:
            return
        width = self.winfo_width()
        cols = max(1, width // (self._item_width + self._gap)) if width > 1 else 4
        if cols == self._cols and not force:
            return
        for c in range(max(cols, self._cols)):
            self.grid_columnconfigure(c, weight=1 if c < cols else 0)
        for index, widget in enumerate(self._items):
            widget.grid(row=index // cols, column=index % cols,
                        padx=self._gap // 2, pady=self._gap // 2, sticky="n")
        self._cols = cols
