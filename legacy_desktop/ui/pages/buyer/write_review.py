"""
ui/pages/buyer/write_review.py
หน้าเขียนรีวิวสินค้า (เฉพาะสินค้าในออเดอร์ที่ "สำเร็จ" และยังไม่เคยรีวิว): ให้ดาว 1–5 + ความเห็น
"""

import customtkinter as ctk

from services import order_service, review_service
from ui.components import dialogs
from ui.components.rating import RatingStars
from ui.pages.buyer import common
from ui.theme import ThemeManager
from utils.image_utils import load_ctk_image

RATING_TEXT = {0: "แตะดาวเพื่อให้คะแนน", 1: "แย่มาก", 2: "พอใช้", 3: "ปานกลาง", 4: "ดี", 5: "ดีมาก"}


class WriteReviewPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._product_id = None
        self._order_id = None
        self._image = None

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        common.page_title(body, "⭐ เขียนรีวิวสินค้า", "บอกเล่าประสบการณ์ให้ผู้ซื้อคนอื่นได้อ่าน").pack(anchor="w")

        self.card = ThemeManager.make_card(body)
        self.card.pack(fill="x", pady=12)
        self.card.grid_columnconfigure(1, weight=1)

        self.image_label = ctk.CTkLabel(self.card, text="")
        self.image_label.grid(row=0, column=0, rowspan=2, padx=18, pady=16, sticky="n")
        self.name_label = ctk.CTkLabel(self.card, text="", font=ThemeManager.get_font("h3"), anchor="w", justify="left",
                                       wraplength=560, text_color=ThemeManager.get_color_pair("text_main"))
        self.name_label.grid(row=0, column=1, sticky="w", padx=(0, 18), pady=(18, 0))
        self.option_label = ctk.CTkLabel(self.card, text="", font=ThemeManager.get_font("small"), anchor="w",
                                         text_color=ThemeManager.get_color_pair("text_muted"))
        self.option_label.grid(row=1, column=1, sticky="nw", padx=(0, 18))

        ctk.CTkLabel(self.card, text="ให้คะแนนสินค้า", font=ThemeManager.get_font("body_bold"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_main")
                     ).grid(row=2, column=0, columnspan=2, sticky="w", padx=18, pady=(4, 0))
        rating_row = ctk.CTkFrame(self.card, fg_color="transparent")
        rating_row.grid(row=3, column=0, columnspan=2, sticky="w", padx=14, pady=(2, 0))
        self.stars = RatingStars(rating_row, value=0, size=36, interactive=True, command=self._on_rate)
        self.stars.pack(side="left")
        self.rating_text = ctk.CTkLabel(rating_row, text=RATING_TEXT[0], font=ThemeManager.get_font("body"),
                                        text_color=ThemeManager.get_color_pair("text_muted"))
        self.rating_text.pack(side="left", padx=12)

        ctk.CTkLabel(self.card, text="ความเห็น (ไม่บังคับ)", font=ThemeManager.get_font("body_bold"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_main")
                     ).grid(row=4, column=0, columnspan=2, sticky="w", padx=18, pady=(14, 4))
        self.comment_box = ctk.CTkTextbox(self.card, **ThemeManager.entry_style(140))
        self.comment_box.grid(row=5, column=0, columnspan=2, sticky="ew", padx=18)
        self.comment_box.bind("<KeyRelease>", lambda _e: self._update_counter())
        self.counter_label = ctk.CTkLabel(self.card, text="", font=ThemeManager.get_font("tiny"), anchor="e",
                                          text_color=ThemeManager.get_color_pair("text_muted"))
        self.counter_label.grid(row=6, column=0, columnspan=2, sticky="e", padx=20)

        self.msg_label = common.error_label(self.card, wraplength=640)
        self.msg_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=18, pady=(4, 0))

        buttons = ctk.CTkFrame(self.card, fg_color="transparent")
        buttons.grid(row=8, column=0, columnspan=2, sticky="w", padx=14, pady=(6, 18))
        self.submit_btn = ctk.CTkButton(buttons, text="ส่งรีวิว", width=140, command=self._submit,
                                        **ThemeManager.button_style("primary", "lg"))
        self.submit_btn.pack(side="left", padx=(4, 8))
        ctk.CTkButton(buttons, text="ยกเลิก", width=100, command=self._back,
                      **ThemeManager.button_style("outline", "lg")).pack(side="left")

    # ------------------------------------------------------------------ โหลด/แสดง
    def on_show(self, product_id=None, order_id=None, **kwargs):
        self._product_id = product_id
        self._order_id = order_id
        self.stars.set(0)
        self._on_rate(0)
        self.comment_box.delete("1.0", "end")
        self._update_counter()
        self.msg_label.configure(text="")
        self.submit_btn.configure(state="disabled")
        self._load()

    def _load(self):
        uid = common.user_id()
        try:
            if self._product_id is None or self._order_id is None:
                raise ValueError("ไม่พบสินค้าที่ต้องการรีวิว")
            order = order_service.get_order_detail(self._order_id)
            item = next((i for i in order["items"] if i["product_id"] == self._product_id), None)
            if item is None:
                raise ValueError("ไม่พบสินค้านี้ในคำสั่งซื้อ")
            allowed = review_service.can_review(uid, self._product_id, self._order_id)
        except (ValueError, PermissionError) as exc:
            self.name_label.configure(text="-")
            self.option_label.configure(text="")
            self.image_label.configure(image=None)
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self._image = load_ctk_image(item.get("image_path"), (96, 96))
        self.image_label.configure(image=self._image)
        self.name_label.configure(text=item["product_name"])
        self.option_label.configure(text=item.get("option_label") or "")
        if allowed:
            self.submit_btn.configure(state="normal")
        else:
            self.msg_label.configure(text="⛔ ไม่สามารถรีวิวสินค้านี้ได้ — อาจรีวิวไปแล้ว หรือคำสั่งซื้อยังไม่สำเร็จ")

    def _on_rate(self, value):
        self.rating_text.configure(text=RATING_TEXT.get(int(value), ""))

    def _update_counter(self):
        length = len(self.comment_box.get("1.0", "end").strip())
        limit = review_service.MAX_COMMENT_LENGTH
        self.counter_label.configure(
            text=f"{length}/{limit}",
            text_color=ThemeManager.get_color_pair("danger" if length > limit else "text_muted"))

    # ------------------------------------------------------------------ การทำงาน
    def _submit(self):
        rating = self.stars.get()
        if rating < 1:
            self.msg_label.configure(text="⛔ กรุณาให้คะแนน 1-5 ดาว")
            return
        comment = self.comment_box.get("1.0", "end").strip()
        self.msg_label.configure(text="")
        self.submit_btn.configure(state="disabled")
        try:
            review_service.add_review(common.user_id(), self._product_id, self._order_id, rating, comment)
        except (ValueError, PermissionError) as exc:
            self.submit_btn.configure(state="normal")
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        dialogs.show_message(self, "ขอบคุณสำหรับรีวิว", "บันทึกรีวิวของคุณเรียบร้อยแล้ว", kind="success")
        self._back()

    def _back(self):
        if self._order_id is not None:
            self.controller.show("order_detail", order_id=self._order_id)
        else:
            self.controller.show("orders")
