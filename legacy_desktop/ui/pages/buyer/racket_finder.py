"""
ui/pages/buyer/racket_finder.py
ตัวช่วยเลือกไม้: ถามระดับฝีมือ / สไตล์การเล่น / งบ → product_service.recommend_rackets (กติกาตายตัว ไม่ใช้ AI)
"""

import customtkinter as ctk

from core.constants import LEVELS
from services import product_service
from ui.components.product_card import ProductCard
from ui.pages.buyer import common
from ui.theme import ThemeManager

_LEVEL_LABELS = {
    "Beginner": "มือใหม่",
    "Intermediate": "ปานกลาง",
    "Advanced": "ฝีมือดี",
    "Professional": "มืออาชีพ",
}
_STYLE_ORDER = (product_service.STYLE_ATTACK, product_service.STYLE_CONTROL, product_service.STYLE_SPEED)
_STYLE_HINTS = {
    product_service.STYLE_ATTACK: "เน้นตบหนัก ทำแต้มเร็ว → ไม้หัวหนัก ก้านแข็ง",
    product_service.STYLE_CONTROL: "วางลูกแม่น คุมจังหวะเกม → ไม้สมดุล ก้านกลาง",
    product_service.STYLE_SPEED: "ตอบโต้ไว เปลี่ยนจังหวะเร็ว → ไม้หัวเบา ก้านยืดหยุ่น",
}
MAX_SCORE = 8  # ระดับตรง 3 + สมดุลตรง 3 + ก้านตรง 2


class _Choice(ctk.CTkFrame):
    """แถวปุ่มเลือกหนึ่งค่า (ปุ่มที่เลือกเป็นสีเหลือง)"""

    def __init__(self, parent, options, command=None):
        super().__init__(parent, fg_color="transparent")
        self._value = None
        self._command = command
        self._buttons = {}
        for key, label in options:
            btn = ctk.CTkButton(self, text=label, width=110, command=lambda k=key: self._pick(k),
                                **ThemeManager.button_style("outline", "md"))
            btn.pack(side="left", padx=(0, 8))
            self._buttons[key] = btn

    def _pick(self, key):
        self.set(key)
        if self._command:
            self._command(key)

    def set(self, key):
        self._value = key
        for k, btn in self._buttons.items():
            if k == key:
                style = ThemeManager.button_style("primary", "md")
                style["border_width"] = 0
            else:
                style = ThemeManager.button_style("outline", "md")
            btn.configure(**style)

    def get(self):
        return self._value


class RacketFinderPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        common.page_title(body, "🎯 ตัวช่วยเลือกไม้", "ตอบ 3 ข้อสั้น ๆ แล้วเราจะแนะนำไม้ที่เหมาะกับคุณ").pack(fill="x")

        card = ThemeManager.make_card(body)
        card.pack(fill="x", pady=12)
        self._question(card, "1. ระดับฝีมือของคุณ").pack(fill="x", padx=20, pady=(16, 4))
        self.level_choice = _Choice(card, [(lv, _LEVEL_LABELS.get(lv, lv)) for lv in LEVELS])
        self.level_choice.pack(anchor="w", padx=20)

        self._question(card, "2. สไตล์การเล่น").pack(fill="x", padx=20, pady=(16, 4))
        self.style_choice = _Choice(
            card, [(s, product_service.STYLE_LABELS[s]) for s in _STYLE_ORDER], command=self._on_style)
        self.style_choice.pack(anchor="w", padx=20)
        self.style_hint = ctk.CTkLabel(card, text="", font=ThemeManager.get_font("small"), anchor="w",
                                       text_color=ThemeManager.get_color_pair("text_muted"))
        self.style_hint.pack(fill="x", padx=20, pady=(4, 0))

        self._question(card, "3. งบประมาณต่อไม้ (บาท — เว้นว่างได้ถ้าไม่จำกัด)").pack(fill="x", padx=20, pady=(16, 4))
        self.budget_entry = ctk.CTkEntry(card, placeholder_text="เช่น 3000", width=200, **ThemeManager.entry_style(40))
        self.budget_entry.pack(anchor="w", padx=20)
        self.budget_entry.bind("<Return>", lambda _e: self._recommend())

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(18, 18))
        ctk.CTkButton(footer, text="ค้นหาไม้ที่เหมาะกับฉัน", width=200, command=self._recommend,
                      **ThemeManager.button_style("primary", "lg")).pack(side="left")
        ctk.CTkButton(footer, text="ล้างคำตอบ", width=110, command=self._reset,
                      **ThemeManager.button_style("outline", "lg")).pack(side="left", padx=8)
        self.error_label = common.error_label(footer)
        self.error_label.pack(side="left", padx=8)

        self.result_title = ctk.CTkLabel(body, text="", font=ThemeManager.get_font("h3"), anchor="w",
                                         text_color=ThemeManager.get_color_pair("text_main"))
        self.result_title.pack(fill="x", pady=(8, 0))
        self.result_grid = common.WrapGrid(body, item_width=224)
        self.result_grid.pack(fill="x")
        self.empty_label = ctk.CTkLabel(body, text="", font=ThemeManager.get_font("body"),
                                        text_color=ThemeManager.get_color_pair("text_muted"))
        self.empty_label.pack(pady=10)

    @staticmethod
    def _question(parent, text):
        return ctk.CTkLabel(parent, text=text, font=ThemeManager.get_font("body_bold"), anchor="w",
                            text_color=ThemeManager.get_color_pair("text_main"))

    # ------------------------------------------------------------------ การทำงาน
    def on_show(self):
        self.error_label.configure(text="")

    def _on_style(self, style):
        self.style_hint.configure(text=_STYLE_HINTS.get(style, ""))

    def _reset(self):
        self.level_choice.set(None)
        self.style_choice.set(None)
        self.style_hint.configure(text="")
        self.budget_entry.delete(0, "end")
        self.error_label.configure(text="")
        self.result_title.configure(text="")
        self.empty_label.configure(text="")
        self.result_grid.clear()

    def _recommend(self):
        self.error_label.configure(text="")
        budget = self.budget_entry.get().strip().replace(",", "") or None
        try:
            rackets = product_service.recommend_rackets(
                self.level_choice.get() or "", self.style_choice.get() or "", budget=budget)
        except (ValueError, PermissionError) as exc:
            self.error_label.configure(text=str(exc))
            return

        if not rackets:
            self.result_grid.clear()
            self.result_title.configure(text="")
            self.empty_label.configure(text="ไม่พบไม้ที่ตรงกับเงื่อนไข ลองเพิ่มงบหรือเปลี่ยนสไตล์การเล่นดูนะครับ")
            return

        self.empty_label.configure(text="")
        self.result_title.configure(text=f"ไม้ที่แนะนำสำหรับคุณ ({len(rackets)} รุ่น)")
        boxes = []
        for racket in rackets:
            box = ctk.CTkFrame(self.result_grid, fg_color="transparent")
            ProductCard(
                box, racket, width=200,
                on_open=lambda pid: self.controller.show("product_detail", product_id=pid),
                on_wishlist=lambda pid: common.toggle_wishlist(self, pid),
            ).pack()
            ThemeManager.make_badge(box, f"เหมาะสม {racket['match_score']}/{MAX_SCORE}", "success").pack(pady=(6, 2))
            for reason in racket.get("match_reasons") or []:
                ctk.CTkLabel(box, text=f"✓ {reason}", font=ThemeManager.get_font("small"), wraplength=196,
                             justify="left", anchor="w",
                             text_color=ThemeManager.get_color_pair("text_muted")).pack(fill="x", padx=4)
            boxes.append(box)
        self.result_grid.set_items(boxes)
