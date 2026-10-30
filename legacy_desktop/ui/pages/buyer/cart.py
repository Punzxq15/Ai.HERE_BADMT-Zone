"""
ui/pages/buyer/cart.py
หน้าตะกร้าสินค้า (ปรับปรุงตามข้อ 7):
- Checkbox เลือกสินค้าในแต่ละรายการว่าจะซื้ออันไหนบ้างหรือยังไม่ซื้อ
- ปุ่ม "เลือกทั้งหมด" (และยกเลิกเลือกทั้งหมด) + ปุ่ม "ลบสินค้าที่เลือกจากตะกร้า" (ยืนยันก่อนลบ)
- สรุปคำสั่งซื้อคำนวณจากเฉพาะสินค้าที่ติ๊กเลือก และส่งต่อเฉพาะสินค้าที่เลือกไปหน้าชำระเงิน
- สินค้าที่ไม่ได้เลือกจะยังคงอยู่ในตะกร้าหลังชำระเงินเสร็จ
"""

import customtkinter as ctk

from services import cart_service, settings_service
from ui.components import dialogs
from ui.pages.buyer import common
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.formatters import format_price
from utils.image_utils import load_ctk_image


class CartPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._images = []
        self._cart = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        common.page_title(self, "ตะกร้าสินค้า").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 4)
        )

        # --- แถบเครื่องมือเลือกสินค้าทั้งหมด / ลบสินค้าที่เลือก (ข้อ 7) ---
        self.toolbar = ThemeManager.make_card(self)
        self.toolbar.grid(row=1, column=0, sticky="ew", padx=(20, 8), pady=(4, 6))
        tb_inner = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        tb_inner.pack(fill="x", padx=14, pady=8)

        self.select_all_var = ctk.BooleanVar(value=True)
        self.select_all_cb = ctk.CTkCheckBox(
            tb_inner,
            text="เลือกทั้งหมด",
            variable=self.select_all_var,
            command=self._toggle_select_all,
            font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
            fg_color=ThemeManager.get_color_pair("primary"),
            hover_color=ThemeManager.get_color_pair("primary_hover"),
            checkmark_color=ON_PRIMARY,
        )
        self.select_all_cb.pack(side="left")

        self.sel_info_lbl = ctk.CTkLabel(
            tb_inner, text="", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        )
        self.sel_info_lbl.pack(side="left", padx=14)

        self._trash_ic = icon_utils.get_icon("trash", 15, "#FFFFFF", "#FFFFFF")
        self.del_selected_btn = ctk.CTkButton(
            tb_inner,
            text=" ลบสินค้าที่เลือก",
            image=self._trash_ic,
            compound="left",
            width=145,
            command=self._remove_selected,
            **ThemeManager.button_style("danger", "sm"),
        )
        self.del_selected_btn.pack(side="right")

        self.items_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.items_scroll.grid(row=2, column=0, sticky="nsew", padx=(16, 8), pady=(0, 16))

        # --- สรุปยอด (คิดจากเฉพาะสินค้าที่ติ๊กเลือก) ---
        self.summary = ThemeManager.make_card(self, width=310)
        self.summary.grid(row=1, column=1, rowspan=2, sticky="n", padx=(8, 20), pady=(4, 16))
        self.summary.grid_propagate(False)
        self.summary.configure(height=445)
        self.summary.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.summary, text="สรุปคำสั่งซื้อ (เฉพาะที่เลือก)", font=ThemeManager.get_font("h3"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_main"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 8))
        self.count_value = self._summary_row(1, "จำนวนสินค้าที่เลือก")
        self.subtotal_value = self._summary_row(2, "ยอดสินค้า")
        self.shipping_value = self._summary_row(3, "ค่าจัดส่ง (โดยประมาณ)")
        self.total_value = self._summary_row(4, "รวมโดยประมาณ", big=True)
        ctk.CTkLabel(
            self.summary, text="ส่วนลดจากคูปองและโค้ดส่งฟรี เลือกใช้ได้ในขั้นตอนชำระเงิน",
            font=ThemeManager.get_font("tiny"), text_color=ThemeManager.get_color_pair("text_muted"),
            wraplength=270, justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=18, pady=(4, 0))

        self.msg_label = common.error_label(self.summary, wraplength=270)
        self.msg_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=18, pady=(6, 0))

        self.checkout_btn = ctk.CTkButton(
            self.summary, text="ไปชำระเงิน", command=self._go_checkout,
            **ThemeManager.button_style("primary", "lg"),
        )
        self.checkout_btn.grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 6))
        ctk.CTkButton(
            self.summary, text="เลือกซื้อสินค้าต่อ", command=lambda: self.controller.show("category"),
            **ThemeManager.button_style("outline"),
        ).grid(row=8, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 16))

    def _summary_row(self, row, label, big=False):
        ctk.CTkLabel(
            self.summary, text=label, font=ThemeManager.get_font("body_bold" if big else "body"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_main" if big else "text_muted"),
        ).grid(row=row, column=0, sticky="w", padx=(18, 4), pady=3)
        value = ctk.CTkLabel(
            self.summary, text="-", font=ThemeManager.get_font("price" if big else "body_bold"),
            anchor="e", text_color=ThemeManager.get_color_pair("text_main"),
        )
        value.grid(row=row, column=1, sticky="e", padx=(4, 18), pady=3)
        return value

    # ------------------------------------------------------------------ โหลด/แสดง
    def on_show(self):
        self.msg_label.configure(text="")
        self._load()

    def _load(self):
        try:
            cart = cart_service.get_cart(common.user_id())
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=str(exc))
            return
        self._render(cart)

    def _render(self, cart):
        self._cart = cart
        for child in self.items_scroll.winfo_children():
            child.destroy()
        self._images = []

        items = cart["items"]
        if not items:
            self.toolbar.grid_remove()
            ctk.CTkLabel(
                self.items_scroll, text="ตะกร้าของคุณยังว่างอยู่", font=ThemeManager.get_font("body_bold"),
                text_color=ThemeManager.get_color_pair("text_muted"), justify="center",
            ).pack(pady=(60, 10))
            ctk.CTkButton(
                self.items_scroll, text="เลือกซื้อสินค้า", width=160,
                command=lambda: self.controller.show("category"),
                **ThemeManager.button_style("primary"),
            ).pack()
        else:
            self.toolbar.grid()
            all_sel = bool(cart.get("all_selected", True))
            self.select_all_var.set(all_sel)
            self.select_all_cb.configure(text="ยกเลิกเลือกทั้งหมด" if all_sel else "เลือกทั้งหมด")
            sel_rows = len(cart.get("selected_items") or [])
            self.sel_info_lbl.configure(text=f"(เลือก {sel_rows} จาก {len(items)} รายการ)")
            self.del_selected_btn.configure(state="normal" if sel_rows > 0 else "disabled")

        for item in items:
            self._item_row(item)
        self._update_summary(cart)

    def _item_row(self, item):
        is_sel = bool(item.get("is_selected", True))
        row = ThemeManager.make_card(
            self.items_scroll,
            border_color=ThemeManager.get_color_pair("primary" if is_sel else "border"),
            border_width=2 if is_sel else 1,
        )
        row.pack(fill="x", pady=5)
        row.grid_columnconfigure(2, weight=1)

        # Checkbox เลือกสินค้าแต่ละรายการ
        cb_var = ctk.BooleanVar(value=is_sel)
        cb = ctk.CTkCheckBox(
            row, text="", variable=cb_var, width=28,
            command=lambda cid=item["cart_item_id"], v=cb_var: self._toggle_item(cid, v.get()),
            fg_color=ThemeManager.get_color_pair("primary"),
            hover_color=ThemeManager.get_color_pair("primary_hover"),
            checkmark_color=ON_PRIMARY,
        )
        cb.grid(row=0, column=0, rowspan=2, padx=(14, 4), pady=12)

        # รูปสินค้าอัตราส่วน 3:4 (72x96)
        image = load_ctk_image(item.get("image_path"), (72, 96), cover=bool(item.get("image_path")), corner_radius=8)
        self._images.append(image)
        ctk.CTkLabel(row, text="", image=image).grid(row=0, column=1, rowspan=2, padx=(4, 12), pady=10)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=2, sticky="nw", pady=(12, 0))
        name = ctk.CTkLabel(
            info, text=item["product_name"], font=ThemeManager.get_font("body_bold"), anchor="w",
            justify="left", wraplength=340, text_color=ThemeManager.get_color_pair("text_main"),
        )
        name.pack(fill="x")
        name.bind("<Button-1>", lambda _e, pid=item["product_id"]: self.controller.show("product_detail", product_id=pid))
        try:
            name.configure(cursor="hand2")
        except Exception:  # noqa: BLE001
            pass
        if item.get("option_label"):
            ctk.CTkLabel(
                info, text=item["option_label"], font=ThemeManager.get_font("small"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_muted"),
            ).pack(fill="x")
        ctk.CTkLabel(
            info, text=f"ราคาต่อชิ้น {format_price(item['unit_price'])}", font=ThemeManager.get_font("small"),
            anchor="w", text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(fill="x")

        if item.get("problem"):
            ctk.CTkLabel(
                row, text=f"แจ้งเตือน: {item['problem']}", font=ThemeManager.get_font("small_bold"), anchor="w",
                justify="left", wraplength=360, text_color=ThemeManager.get_color_pair("danger"),
            ).grid(row=1, column=2, sticky="nw", pady=(0, 12))

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.grid(row=0, column=3, rowspan=2, padx=14, pady=12)
        stepper = ctk.CTkFrame(controls, fg_color="transparent")
        stepper.pack()
        ctk.CTkButton(
            stepper, text="−", width=32, command=lambda: self._change_qty(item, -1),
            state="normal" if item["qty"] > 1 else "disabled",
            **ThemeManager.button_style("outline", "sm"),
        ).pack(side="left")
        ctk.CTkLabel(
            stepper, text=str(item["qty"]), width=40, font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(side="left")
        ctk.CTkButton(
            stepper, text="+", width=32, command=lambda: self._change_qty(item, 1),
            **ThemeManager.button_style("outline", "sm"),
        ).pack(side="left")
        ctk.CTkLabel(
            controls, text=format_price(item["line_total"]), font=ThemeManager.get_font("price"),
            text_color=ThemeManager.get_color_pair("danger" if is_sel else "text_muted"),
        ).pack(pady=(8, 0))
        del_ic = icon_utils.get_icon("trash", 14, "#E63946", "#EF4444")
        ctk.CTkButton(
            controls, text=" ลบ", image=del_ic, compound="left", width=74,
            command=lambda: self._remove(item),
            fg_color="transparent", hover_color=ThemeManager.get_color_pair("surface_alt"),
            text_color=ThemeManager.get_color_pair("danger"), font=ThemeManager.get_font("small_bold"),
            height=26,
        ).pack(pady=(2, 0))

    def _update_summary(self, cart):
        sel_items = cart.get("selected_items") if "selected_items" in cart else cart["items"]
        sel_count = int(cart.get("selected_item_count", cart["item_count"]) or 0)
        sel_subtotal = float(cart.get("selected_subtotal", cart["subtotal"]) or 0)
        sel_problem = bool(cart.get("selected_has_problem", cart["has_problem"]))

        self.count_value.configure(text=f"{sel_count:,} ชิ้น")
        self.subtotal_value.configure(text=format_price(sel_subtotal))
        try:
            shipping = float(settings_service.shipping_fee_for(sel_subtotal)) if sel_items else 0.0
            self.shipping_value.configure(text="ฟรี" if sel_items and shipping == 0 else format_price(shipping))
            self.total_value.configure(text=format_price(round(sel_subtotal + shipping, 2)))
        except Exception:  # noqa: BLE001
            self.shipping_value.configure(text="-")
            self.total_value.configure(text=format_price(sel_subtotal))

        blocked = not sel_items or sel_problem
        self.checkout_btn.configure(state="disabled" if blocked else "normal")
        if cart["items"] and not sel_items:
            self.msg_label.configure(text="กรุณาติ๊กเลือกสินค้าอย่างน้อย 1 รายการเพื่อชำระเงิน")
        elif sel_items and sel_problem:
            self.msg_label.configure(text="สินค้าที่เลือกมีปัญหาสต็อก กรุณาแก้ไขหรือเอาติ๊กออกก่อนชำระเงิน")
        elif not self.msg_label.cget("text").startswith("⛔"):
            self.msg_label.configure(text="")

    # ------------------------------------------------------------------ การทำงาน
    def _toggle_item(self, cart_item_id: int, selected: bool):
        self.msg_label.configure(text="")
        try:
            cart = cart_service.set_item_selected(common.user_id(), cart_item_id, selected)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self._render(cart)

    def _toggle_select_all(self):
        self.msg_label.configure(text="")
        target = bool(self.select_all_var.get())
        try:
            cart = cart_service.set_all_selected(common.user_id(), target)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self._render(cart)

    def _remove_selected(self):
        sel_items = (self._cart or {}).get("selected_items") or []
        if not sel_items:
            return
        if not dialogs.confirm(
            self,
            "ลบสินค้าที่เลือก",
            f"ต้องการลบสินค้าที่ติ๊กเลือกไว้ทั้ง {len(sel_items)} รายการออกจากตะกร้าใช่หรือไม่?",
            confirm_text="ลบที่เลือก",
            danger=True,
        ):
            return
        try:
            cart = cart_service.remove_selected_items(common.user_id())
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        self._render(cart)

    def _go_checkout(self):
        sel_items = (self._cart or {}).get("selected_items") or []
        if not sel_items:
            self.msg_label.configure(text="กรุณาติ๊กเลือกสินค้าอย่างน้อย 1 รายการเพื่อชำระเงิน")
            return
        self.controller.show("checkout")

    def _change_qty(self, item, delta):
        new_qty = item["qty"] + delta
        if new_qty < 1:
            return
        self.msg_label.configure(text="")
        try:
            cart = cart_service.update_qty(common.user_id(), item["cart_item_id"], new_qty)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        self._render(cart)

    def _remove(self, item):
        if not dialogs.confirm(self, "ลบสินค้า", f"ต้องการลบ \"{item['product_name']}\" ออกจากตะกร้าใช่ไหม?",
                               confirm_text="ลบ", danger=True):
            return
        try:
            cart_service.remove_item(common.user_id(), item["cart_item_id"])
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        self.msg_label.configure(text="")
        self._load()
