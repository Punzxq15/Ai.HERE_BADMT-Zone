"""
ui/pages/buyer/checkout.py
หน้ายืนยันคำสั่งซื้อและการใส่โค้ดส่วนลด (ปรับปรุงตามข้อ 8):
- เช็คว่าลูกค้าคนนี้ไปรับโค้ดอะไรไว้บ้าง และแสดงรายการโค้ดพร้อมสถานะว่าใช้ได้ไหม (พร้อมเหตุผลสั้นๆ)
- ถ้าใช้ได้มีปุ่ม "ใช้โค้ด" กดใช้ได้เลยโดยไม่ต้องพิมพ์เอง (และยังคงช่องกรอกโค้ดด้วยมือไว้เหมือนเดิม)
- เพิ่มส่วนลดค่าจัดส่ง (โค้ดส่งฟรี / ลดค่าส่ง) ที่กดรับเองและกดใช้ได้เหมือนกัน
- กฎการใช้: 1 โค้ดใช้ได้ 1 ครั้ง จนกว่าจะกดรับใหม่
"""

import customtkinter as ctk

from services import account_service, cart_service, coupon_service, order_service, settings_service
from ui.pages.buyer import common
from ui.theme import ThemeManager
from utils import icon_utils
from utils.formatters import format_phone, format_price
from utils.image_utils import load_ctk_image


class CheckoutPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._images = []
        self._cart = None
        self._addresses = []
        self._coupon = None           # โค้ดส่วนลดสินค้า
        self._shipping_coupon = None  # โค้ดส่วนลดค่าจัดส่ง (ส่งฟรี)
        self._busy = False
        self.address_var = ctk.IntVar(value=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        common.page_title(self, "ยืนยันคำสั่งซื้อ", "ตรวจที่อยู่จัดส่ง เลือกใช้คูปอง และตรวจสอบยอดชำระก่อนสั่งซื้อ").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 4))

        # ---------------- ซ้าย: ที่อยู่ + รายการสินค้าที่เลือก
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=(0, 16))

        head = ctk.CTkFrame(self.scroll, fg_color="transparent")
        head.pack(fill="x", pady=(0, 2))
        common.section_header(head, "ที่อยู่จัดส่ง", "จัดการที่อยู่ ›",
                              lambda: self.controller.show("addresses")).pack(fill="x")
        self.addr_box = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.addr_box.pack(fill="x")

        common.section_header(self.scroll, "รายการสินค้าที่เลือกชำระเงิน").pack(fill="x", pady=(14, 2))
        self.items_box = ThemeManager.make_card(self.scroll)
        self.items_box.pack(fill="x", pady=4)

        # ---------------- ขวา: คูปองของฉัน + โค้ดส่วนลดค่าส่ง + สรุปยอด (เลื่อนได้)
        self.right_scroll = ctk.CTkScrollableFrame(self, width=385, fg_color="transparent")
        self.right_scroll.grid(row=1, column=1, sticky="nsew", padx=(8, 20), pady=(0, 16))

        self.summary = ThemeManager.make_card(self.right_scroll)
        self.summary.pack(fill="x", pady=(0, 8))
        self.summary.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.summary, text="โค้ดส่วนลด & โค้ดส่งฟรี", font=ThemeManager.get_font("h3"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_main")
                     ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 6))
        coupon_row = ctk.CTkFrame(self.summary, fg_color="transparent")
        coupon_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16)
        coupon_row.grid_columnconfigure(0, weight=1)
        self.coupon_entry = ctk.CTkEntry(coupon_row, placeholder_text="กรอกโค้ด เช่น WELCOME10",
                                         **ThemeManager.entry_style(36))
        self.coupon_entry.grid(row=0, column=0, sticky="ew")
        self.coupon_entry.bind("<Return>", lambda _e: self._toggle_coupon())
        self.coupon_btn = ctk.CTkButton(coupon_row, text="ใช้โค้ด", width=76, command=self._toggle_coupon,
                                        **ThemeManager.button_style("secondary", "sm"))
        self.coupon_btn.grid(row=0, column=1, padx=(6, 0))
        self.coupon_msg = common.error_label(self.summary, wraplength=330)
        self.coupon_msg.grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(4, 0))

        # รายการโค้ดของลูกค้าและโค้ดส่งฟรีที่กดรับ/กดใช้ได้ทันที (ข้อ 8)
        ctk.CTkLabel(
            self.summary, text="โค้ดของคุณ & โค้ดที่กดรับได้ (1 โค้ดใช้ได้ 1 ครั้ง จนกว่าจะกดรับใหม่)",
            font=ThemeManager.get_font("small_bold"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(10, 4))

        self.coupons_list_box = ctk.CTkFrame(self.summary, fg_color="transparent")
        self.coupons_list_box.grid(row=4, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(self.summary, text="สรุปคำสั่งซื้อ", font=ThemeManager.get_font("h3"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_main")
                     ).grid(row=5, column=0, columnspan=2, sticky="w", padx=16, pady=(10, 6))
        self.subtotal_value = self._summary_row(6, "ยอดสินค้า")
        self.discount_value = self._summary_row(7, "ส่วนลดสินค้า")
        self.ship_discount_value = self._summary_row(8, "ส่วนลดค่าจัดส่ง")
        self.shipping_value = self._summary_row(9, "ค่าจัดส่งสุทธิ")
        self.vat_value = self._summary_row(10, "รวม VAT 7% (ในยอดชำระ)")
        self.total_value = self._summary_row(11, "ยอดชำระสุทธิ", big=True)

        self.msg_label = common.error_label(self.summary, wraplength=330)
        self.msg_label.grid(row=12, column=0, columnspan=2, sticky="w", padx=16, pady=(8, 0))
        self.confirm_btn = ctk.CTkButton(self.summary, text="ยืนยันสั่งซื้อ", command=self._confirm,
                                         **ThemeManager.button_style("primary", "lg"))
        self.confirm_btn.grid(row=13, column=0, columnspan=2, sticky="ew", padx=16, pady=(10, 6))
        ctk.CTkButton(self.summary, text="‹ กลับไปตะกร้า", command=lambda: self.controller.show("cart"),
                      **ThemeManager.button_style("outline")
                      ).grid(row=14, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))

    def _summary_row(self, row, label, big=False):
        ctk.CTkLabel(self.summary, text=label, font=ThemeManager.get_font("body_bold" if big else "small"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_main" if big else "text_muted")
                     ).grid(row=row, column=0, sticky="w", padx=(16, 4), pady=2)
        value = ctk.CTkLabel(self.summary, text="-", font=ThemeManager.get_font("price" if big else "small_bold"),
                             anchor="e", text_color=ThemeManager.get_color_pair("danger" if big else "text_main"))
        value.grid(row=row, column=1, sticky="e", padx=(4, 16), pady=2)
        return value

    def _checkout_items(self):
        if not self._cart:
            return []
        return self._cart.get("selected_items") if "selected_items" in self._cart else self._cart.get("items", [])

    # ------------------------------------------------------------------ โหลด/แสดง
    def on_show(self):
        self._busy = False
        self._reset_coupon()
        self._shipping_coupon = None
        self.msg_label.configure(text="")
        self._load()

    def _load(self):
        uid = common.user_id()
        try:
            self._cart = cart_service.get_cart(uid)
            self._addresses = account_service.list_addresses(uid)
        except (ValueError, PermissionError) as exc:
            self._cart = {"items": [], "selected_items": [], "subtotal": 0, "selected_subtotal": 0,
                          "item_count": 0, "has_problem": False, "selected_has_problem": False}
            self._addresses = []
            self.msg_label.configure(text=f"⛔ {exc}")
        self._select_default_address()
        self._render_addresses()
        self._render_items()
        self._update_totals()
        self._render_user_coupons()

    def _select_default_address(self):
        ids = [a["id"] for a in self._addresses]
        if self.address_var.get() in ids:
            return
        default = next((a for a in self._addresses if a.get("is_default")), None)
        if default is None and self._addresses:
            default = self._addresses[0]
        self.address_var.set(default["id"] if default else 0)

    def _render_addresses(self):
        for child in self.addr_box.winfo_children():
            child.destroy()
        if not self._addresses:
            card = ThemeManager.make_card(self.addr_box)
            card.pack(fill="x", pady=4)
            ctk.CTkLabel(card, text="ยังไม่มีที่อยู่จัดส่ง กรุณาเพิ่มที่อยู่ก่อนสั่งซื้อ", font=ThemeManager.get_font("body"),
                         text_color=ThemeManager.get_color_pair("text_muted")).pack(padx=16, pady=(14, 6))
            ctk.CTkButton(card, text="+ เพิ่มที่อยู่จัดส่ง", width=160, command=lambda: self.controller.show("addresses"),
                          **ThemeManager.button_style("primary")).pack(pady=(0, 14))
            return
        for address in self._addresses:
            self._address_card(address)

    def _address_card(self, address):
        card = ThemeManager.make_card(self.addr_box)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)
        select = lambda _e=None, aid=address["id"]: self.address_var.set(aid)  # noqa: E731

        ctk.CTkRadioButton(card, text="", variable=self.address_var, value=address["id"], width=24,
                           fg_color=ThemeManager.get_color_pair("primary"),
                           hover_color=ThemeManager.get_color_pair("primary_hover")
                           ).grid(row=0, column=0, sticky="n", padx=(14, 4), pady=14)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", padx=(0, 14), pady=12)
        top = ctk.CTkFrame(info, fg_color="transparent")
        top.pack(fill="x")
        name = ctk.CTkLabel(top, text=address["recipient"], font=ThemeManager.get_font("body_bold"),
                            text_color=ThemeManager.get_color_pair("text_main"))
        name.pack(side="left")
        phone = ctk.CTkLabel(top, text=format_phone(address["phone"]), font=ThemeManager.get_font("small"),
                             text_color=ThemeManager.get_color_pair("text_muted"))
        phone.pack(side="left", padx=10)
        if address.get("is_default"):
            ThemeManager.make_badge(top, "ค่าเริ่มต้น", "success").pack(side="left")
        text = ctk.CTkLabel(info, text=address["full_address"], font=ThemeManager.get_font("body"), anchor="w",
                            justify="left", wraplength=480, text_color=ThemeManager.get_color_pair("text_main"))
        text.pack(fill="x", pady=(4, 0))
        for widget in (card, info, top, name, phone, text):
            widget.bind("<Button-1>", select)

    def _render_items(self):
        for child in self.items_box.winfo_children():
            child.destroy()
        self._images = []
        items = self._checkout_items()
        if not items:
            ctk.CTkLabel(self.items_box, text="ยังไม่มีสินค้าที่เลือกสำหรับชำระเงิน — กรุณาเลือกในตะกร้า",
                         font=ThemeManager.get_font("body"),
                         text_color=ThemeManager.get_color_pair("text_muted")).pack(padx=16, pady=(16, 6))
            ctk.CTkButton(self.items_box, text="กลับไปเลือกในตะกร้า", width=170, command=lambda: self.controller.show("cart"),
                          **ThemeManager.button_style("primary")).pack(pady=(0, 16))
            return
        for item in items:
            row = ctk.CTkFrame(self.items_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            row.grid_columnconfigure(1, weight=1)
            image = load_ctk_image(item.get("image_path"), (54, 72), cover=bool(item.get("image_path")), corner_radius=6)
            self._images.append(image)
            ctk.CTkLabel(row, text="", image=image).grid(row=0, column=0, rowspan=2, padx=(0, 10))
            ctk.CTkLabel(row, text=item["product_name"], font=ThemeManager.get_font("body_bold"), anchor="w",
                         justify="left", wraplength=420, text_color=ThemeManager.get_color_pair("text_main")
                         ).grid(row=0, column=1, sticky="w")
            detail = f"{item['option_label']} · " if item.get("option_label") else ""
            ctk.CTkLabel(row, text=f"{detail}{format_price(item['unit_price'])} × {item['qty']}",
                         font=ThemeManager.get_font("small"), anchor="w",
                         text_color=ThemeManager.get_color_pair("text_muted")).grid(row=1, column=1, sticky="w")
            ctk.CTkLabel(row, text=format_price(item["line_total"]), font=ThemeManager.get_font("body_bold"),
                         text_color=ThemeManager.get_color_pair("text_main")
                         ).grid(row=0, column=2, rowspan=2, padx=(8, 0))
            if item.get("problem"):
                ctk.CTkLabel(row, text=f"แจ้งเตือน: {item['problem']}", font=ThemeManager.get_font("small"), anchor="w",
                             text_color=ThemeManager.get_color_pair("danger")
                             ).grid(row=2, column=1, columnspan=2, sticky="w")

    # ------------------------------------------------------------------ แสดงรายการโค้ดของลูกค้า & โค้ดส่งฟรี (ข้อ 8)
    def _render_user_coupons(self):
        for child in self.coupons_list_box.winfo_children():
            child.destroy()

        items = self._checkout_items()
        subtotal = round(sum(float(i["line_total"]) for i in items), 2)
        try:
            base_ship = round(float(settings_service.shipping_fee_for(subtotal)), 2) if items else 0.0
        except Exception:  # noqa: BLE001
            base_ship = 0.0

        try:
            coupons = coupon_service.list_checkout_coupons(common.user_id(), subtotal, shipping_fee=base_ship)
        except Exception:  # noqa: BLE001
            coupons = []

        if not coupons:
            ctk.CTkLabel(
                self.coupons_list_box, text="ยังไม่มีคูปองในระบบ",
                font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("text_muted"),
            ).pack(pady=4)
            return

        active_code = (self._coupon or {}).get("code")
        active_ship_code = (self._shipping_coupon or {}).get("code")

        for cp in coupons:
            code = cp["code"]
            is_free_ship = bool(cp.get("is_free_shipping"))
            can_use = bool(cp.get("can_use"))
            can_claim = bool(cp.get("can_claim"))
            is_applied = (code == active_code) or (code == active_ship_code)

            row_card = ctk.CTkFrame(
                self.coupons_list_box,
                fg_color=ThemeManager.get_color_pair("surface_alt"),
                corner_radius=8,
                border_width=2 if is_applied else 1,
                border_color=ThemeManager.get_color_pair("success" if is_applied else ("primary" if can_use else "border")),
            )
            row_card.pack(fill="x", pady=3)

            top_r = ctk.CTkFrame(row_card, fg_color="transparent")
            top_r.pack(fill="x", padx=10, pady=(6, 2))

            ic = icon_utils.get_icon("truck" if is_free_ship else "coupon", 15, "#E63946", "#FFB703")
            ctk.CTkLabel(
                top_r, text=f" {code} · {cp.get('description') or ''}",
                image=ic, compound="left",
                font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("text_main"), anchor="w",
            ).pack(side="left")

            badge_kind = "success" if is_applied or can_use else ("warning" if can_claim else "muted")
            status_txt = "กำลังใช้งาน" if is_applied else (cp.get("status_text") or "")
            ThemeManager.make_badge(top_r, status_txt, badge_kind, font_style="tiny").pack(side="right")

            bot_r = ctk.CTkFrame(row_card, fg_color="transparent")
            bot_r.pack(fill="x", padx=10, pady=(0, 6))
            ctk.CTkLabel(
                bot_r, text=cp.get("reason") or "",
                font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("text_muted"),
                anchor="w", justify="left", wraplength=215,
            ).pack(side="left", fill="x", expand=True)

            if is_applied:
                ctk.CTkButton(
                    bot_r, text="ยกเลิก", width=72,
                    command=lambda fs=is_free_ship: self._clear_specific_coupon(fs),
                    **ThemeManager.button_style("outline", "sm"),
                ).pack(side="right")
            elif can_use:
                ctk.CTkButton(
                    bot_r, text="กดใช้โค้ด", width=80,
                    command=lambda c=code: self._apply_code_direct(c),
                    **ThemeManager.button_style("primary", "sm"),
                ).pack(side="right")
            elif can_claim:
                btn_lbl = "กดรับใหม่" if cp.get("is_used") else "กดรับโค้ด"
                ctk.CTkButton(
                    bot_r, text=btn_lbl, width=82,
                    command=lambda cid=cp["id"]: self._claim_and_refresh(cid),
                    **ThemeManager.button_style("danger", "sm"),
                ).pack(side="right")

    def _claim_and_refresh(self, coupon_id: int):
        self.coupon_msg.configure(text="")
        try:
            claimed = coupon_service.claim_coupon(common.user_id(), coupon_id)
            self.coupon_msg.configure(
                text=f"✓ รับโค้ด {claimed['code']} เรียบร้อยแล้ว กดใช้โค้ดได้ทันที!",
                text_color=ThemeManager.get_color_pair("success"),
            )
        except (ValueError, PermissionError) as exc:
            self.coupon_msg.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))
            return
        self._render_user_coupons()

    def _apply_code_direct(self, code: str):
        self.coupon_entry.configure(state="normal")
        self.coupon_entry.delete(0, "end")
        self.coupon_entry.insert(0, code)
        self._apply_coupon()

    def _clear_specific_coupon(self, is_free_shipping: bool):
        if is_free_shipping:
            self._shipping_coupon = None
        else:
            self._coupon = None
            self.coupon_entry.configure(state="normal")
            self.coupon_entry.delete(0, "end")
            self.coupon_btn.configure(text="ใช้โค้ด", **ThemeManager.button_style("secondary", "sm"))
        self._refresh_coupon_banner()
        self._update_totals()
        self._render_user_coupons()

    # ------------------------------------------------------------------ ยอดเงิน
    def _calc(self):
        """คืน (subtotal, prod_discount, ship_discount, net_shipping, total)"""
        items = self._checkout_items()
        subtotal = round(sum(float(i["line_total"]) for i in items), 2)
        base_shipping = 0.0
        if items:
            try:
                base_shipping = round(float(settings_service.shipping_fee_for(subtotal)), 2)
            except Exception:  # noqa: BLE001
                base_shipping = 0.0

        prod_discount = 0.0
        if self._coupon and not self._coupon.get("is_free_shipping"):
            prod_discount = round(min(float(self._coupon["discount"]), subtotal), 2)

        ship_discount = 0.0
        if self._coupon and self._coupon.get("is_free_shipping"):
            ship_discount = round(min(float(self._coupon["discount"]), base_shipping), 2)
        if self._shipping_coupon:
            rem_ship = max(0.0, base_shipping - ship_discount)
            ship_discount = round(ship_discount + min(float(self._shipping_coupon["discount"]), rem_ship), 2)

        net_shipping = round(max(0.0, base_shipping - ship_discount), 2)
        total = round(subtotal - prod_discount + net_shipping, 2)
        return subtotal, prod_discount, ship_discount, net_shipping, total

    def _update_totals(self):
        items = self._checkout_items()
        subtotal, prod_discount, ship_discount, net_shipping, total = self._calc()
        vat_info = order_service.compute_vat_breakdown(total)

        self.subtotal_value.configure(text=format_price(subtotal))
        self.discount_value.configure(text=f"-{format_price(prod_discount)}" if prod_discount else "-")
        self.ship_discount_value.configure(text=f"-{format_price(ship_discount)}" if ship_discount else "-")
        self.shipping_value.configure(text="ฟรี" if items and net_shipping == 0 else format_price(net_shipping))
        self.vat_value.configure(text=format_price(vat_info["vat_amount"]))
        self.total_value.configure(text=format_price(total))
        self._refresh_button()

    def _refresh_button(self):
        items = self._checkout_items()
        has_prob = any(i.get("problem") for i in items)
        ready = bool(items) and not has_prob and bool(self._addresses) and not self._busy
        self.confirm_btn.configure(state="normal" if ready else "disabled")
        if items and has_prob and not self.msg_label.cget("text"):
            self.msg_label.configure(text="มีสินค้าที่ซื้อไม่ได้ในรายการที่เลือก กรุณากลับไปแก้ไขในตะกร้าก่อน")

    # ------------------------------------------------------------------ คูปอง
    def _toggle_coupon(self):
        if self._coupon:
            self._reset_coupon()
            self._update_totals()
            self._render_user_coupons()
        else:
            self._apply_coupon()

    def _refresh_coupon_banner(self):
        parts = []
        if self._coupon:
            parts.append(f"{self._coupon['code']} ({self._coupon['description']})")
        if self._shipping_coupon:
            parts.append(f"{self._shipping_coupon['code']} ({self._shipping_coupon['description']})")
        if parts:
            self.coupon_msg.configure(
                text="✓ ใช้โค้ดแล้ว: " + " + ".join(parts),
                text_color=ThemeManager.get_color_pair("success"),
            )
        else:
            self.coupon_msg.configure(text="")

    def _apply_coupon(self):
        code = self.coupon_entry.get().strip()
        self.coupon_msg.configure(text="")
        items = self._checkout_items()
        subtotal = round(sum(float(i["line_total"]) for i in items), 2)
        try:
            base_ship = round(float(settings_service.shipping_fee_for(subtotal)), 2) if items else 0.0
        except Exception:  # noqa: BLE001
            base_ship = 0.0

        try:
            coupon = coupon_service.validate_coupon(
                code, common.user_id(), subtotal, shipping_fee=base_ship
            )
        except (ValueError, PermissionError) as exc:
            self.coupon_msg.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))
            return

        if coupon.get("is_free_shipping"):
            self._shipping_coupon = coupon
            self.coupon_entry.delete(0, "end")
        else:
            self._coupon = coupon
            self.coupon_entry.configure(state="disabled")
            self.coupon_btn.configure(text="ยกเลิก", **ThemeManager.button_style("outline", "sm"))

        self._refresh_coupon_banner()
        self._update_totals()
        self._render_user_coupons()

    def _reset_coupon(self):
        self._coupon = None
        self.coupon_entry.configure(state="normal")
        self.coupon_entry.delete(0, "end")
        self.coupon_btn.configure(text="ใช้โค้ด", **ThemeManager.button_style("secondary", "sm"))
        self.coupon_msg.configure(text="")

    # ------------------------------------------------------------------ สั่งซื้อ
    def _confirm(self):
        if self._busy:
            return
        address_id = self.address_var.get()
        if not address_id:
            self.msg_label.configure(text="⛔ กรุณาเลือกที่อยู่จัดส่ง")
            return
        items = self._checkout_items()
        if not items:
            self.msg_label.configure(text="⛔ กรุณาเลือกสินค้าในตะกร้าอย่างน้อย 1 รายการ")
            return

        code = self._coupon["code"] if self._coupon else None
        ship_code = self._shipping_coupon["code"] if self._shipping_coupon else None
        if code is None and ship_code is not None:
            code, ship_code = ship_code, None

        sel_ids = [i["cart_item_id"] for i in items]
        self._busy = True
        self.msg_label.configure(text="")
        self._refresh_button()
        try:
            order = order_service.checkout(
                common.user_id(),
                address_id,
                coupon_code=code,
                selected_item_ids=sel_ids,
                shipping_coupon_code=ship_code,
            )
        except (ValueError, PermissionError) as exc:
            self._busy = False
            message = str(exc)
            if (self._coupon or self._shipping_coupon) and any(word in message for word in ("โค้ด", "คูปอง", "ส่วนลด")):
                self._reset_coupon()
                self._shipping_coupon = None
            self._load()
            self.msg_label.configure(text=f"⛔ {message}")
            return
        self._busy = False
        self.controller.refresh_shell()
        self.controller.show("payment", order_id=order["id"])
