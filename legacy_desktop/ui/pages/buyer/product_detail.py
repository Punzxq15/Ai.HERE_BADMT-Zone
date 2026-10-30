"""
ui/pages/buyer/product_detail.py
หน้ารายละเอียดสินค้า (ปรับปรุงตาม T03, T04, T12):
- T03: แสดง Technical Specifications ของไม้แบดมินตัน 7 หัวข้อ (Material, Weight Class / Grip, Balance Point,
  Shaft Flexibility, Max String Tension, Length, Skill Level) โดยซ่อนแถวที่เว้นว่าง
- T04: รองรับรูปภาพหลายรูปต่อสินค้า (แกลเลอรีรูปหลัก + แถบรูปย่อ + ปุ่มเลื่อนรูป) และเมื่อเลือกสี/สไตล์จะเปลี่ยนไปยังรูปที่ผูกไว้
- T12: เพิ่มสีสันหลากหลาย (แดง, ชมพู, ฟ้า, เขียว, ดำ/โทนเข้มเทคนิค) ที่พื้นหลังและตัวอักษรตัดกันอ่านชัดทั้งโหมด Light และ Dark
  พร้อมปรับกรอบข้อความ (กล่องราคา/ป้ายสต็อก/ป้ายแบรนด์) ให้กะทัดรัดพอดีกับตัวอักษร
"""

import time

import customtkinter as ctk

from core.session import Session
from services import cart_service, product_service, review_service
from ui.components.product_card import discount_percent, format_countdown
from ui.components.rating import RatingStars
from ui.pages.buyer import common
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.formatters import format_datetime, format_price
from utils.image_utils import load_ctk_image

IMG_WIDTH = 360
IMG_HEIGHT = 380
THUMB_SIZE = 62
REVIEW_PAGE_SIZE = 5
MAX_QTY = cart_service.MAX_QTY_PER_ITEM


def _lbl(parent, text="", style="body", color="text_main", **kwargs):
    return ctk.CTkLabel(
        parent, text=text, font=ThemeManager.get_font(style), anchor="w",
        text_color=ThemeManager.get_color_pair(color), **kwargs,
    )


def _option_menu(parent, values, variable, command=None, width=280):
    return ctk.CTkOptionMenu(
        parent, values=values, variable=variable, command=command, width=width, height=38,
        font=ThemeManager.get_font("body_bold"), dropdown_font=ThemeManager.get_font("body"),
        fg_color=ThemeManager.get_color_pair("surface_alt"),
        button_color=ThemeManager.get_color_pair("primary"),
        button_hover_color=ThemeManager.get_color_pair("primary_hover"),
        text_color=ThemeManager.get_color_pair("text_main"),
        dropdown_fg_color=ThemeManager.get_color_pair("surface"),
        dropdown_text_color=ThemeManager.get_color_pair("text_main"),
        dropdown_hover_color=ThemeManager.get_color_pair("surface_alt"),
    )


class ProductDetailPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self.product = None
        self._body = None
        self._image = None
        self._thumb_imgs = []
        self._gallery_items = []
        self._gallery_idx = 0
        self._tick_job = None
        self._deadline = None
        self._option_map = {}
        self._chip_buttons = {}
        self._qty = 1
        self._in_wishlist = False
        self._addon_rows = []
        self._review_page = 0
        self._review_pages = 1

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def on_show(self, product_id=None, **kwargs):
        self._cancel_tick()
        if self._body is not None:
            self._body.destroy()
        self._body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=20, pady=16)
        self._option_map, self._chip_buttons, self._addon_rows = {}, {}, []
        self._thumb_imgs, self._gallery_items, self._gallery_idx = [], [], 0
        self._qty, self._review_page, self._review_pages = 1, 0, 1

        ctk.CTkButton(
            self._body, text="‹ ย้อนกลับ", width=110,
            command=lambda: self.controller.go_back(default="home"),
            **ThemeManager.button_style("outline", "sm"),
        ).pack(anchor="w")

        try:
            self.product = product_service.get_product_detail(product_id, user_id=common.user_id())
        except (ValueError, PermissionError) as exc:
            self.product = None
            _lbl(self._body, f"{exc}", color="danger").pack(pady=40)
            return

        self._in_wishlist = bool(self.product.get("in_wishlist"))
        self._prepare_gallery()
        self._build_main()
        self._build_tech_specs_section()
        self._build_addons()
        self._build_description()
        self._build_reviews()
        self._refresh_option()
        self._start_countdown()

    def _prepare_gallery(self):
        p = self.product
        imgs = list(p.get("images") or [])
        seen_paths = {img.get("path") for img in imgs if img.get("path")}
        # รวมรูปที่ผูกไว้กับตัวเลือกสินค้า (ถ้ามี) เข้าแกลเลอรีด้วย
        for opt in (p.get("options") or []):
            opath = opt.get("image_path")
            if opath and opath not in seen_paths:
                seen_paths.add(opath)
                imgs.append({
                    "id": -int(opt["id"]),
                    "product_id": p["id"],
                    "path": opath,
                    "sort_order": 999,
                    "color_value": opt.get("option_value"),
                })
        if not imgs:
            imgs = [{"id": 0, "product_id": p["id"], "path": p.get("image_path"), "sort_order": 1, "color_value": None}]
        self._gallery_items = imgs
        self._gallery_idx = 0

    def _build_main(self):
        p = self.product
        card = ThemeManager.make_card(self._body)
        card.pack(fill="x", pady=(8, 12))
        card.grid_columnconfigure(0, weight=0, minsize=IMG_WIDTH + 40)
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)

        # ================== ฝั่งซ้าย (T04): รูปหลัก + ปุ่มเลื่อนรูป + แถบรูปย่อ (หลายรูปต่อสินค้า) ==================
        left_col = ctk.CTkFrame(card, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=20, pady=20, sticky="n")

        img_box = ctk.CTkFrame(
            left_col, width=IMG_WIDTH, height=IMG_HEIGHT,
            fg_color=ThemeManager.get_color_pair("surface_alt"),
            corner_radius=16, border_width=2, border_color=ThemeManager.get_color_pair("border"),
        )
        img_box.pack()
        img_box.pack_propagate(False)

        self.main_img_label = ctk.CTkLabel(img_box, text="")
        self.main_img_label.pack(fill="both", expand=True)

        self.img_caption_lbl = ctk.CTkLabel(
            left_col, text="", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("info"),
        )
        self.img_caption_lbl.pack(pady=(6, 2))

        if len(self._gallery_items) > 1:
            nav_row = ctk.CTkFrame(left_col, fg_color="transparent")
            nav_row.pack(fill="x", pady=(2, 4))
            ctk.CTkButton(
                nav_row, text="‹ รูปก่อนหน้า", width=96,
                command=lambda: self._step_gallery(-1),
                **ThemeManager.button_style("outline", "sm"),
            ).pack(side="left")
            self.gallery_counter_lbl = ctk.CTkLabel(
                nav_row, text="", font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("text_main"),
            )
            self.gallery_counter_lbl.pack(side="left", expand=True)
            ctk.CTkButton(
                nav_row, text="รูปถัดไป ›", width=96,
                command=lambda: self._step_gallery(1),
                **ThemeManager.button_style("outline", "sm"),
            ).pack(side="right")

            self.thumb_bar = ctk.CTkFrame(left_col, fg_color="transparent")
            self.thumb_bar.pack(fill="x", pady=(2, 0))
            self._thumb_btns = []
            for idx, g_item in enumerate(self._gallery_items[:6]):
                t_img = load_ctk_image(g_item.get("path"), (THUMB_SIZE - 8, THUMB_SIZE - 8), cover=True, corner_radius=6)
                self._thumb_imgs.append(t_img)
                t_btn = ctk.CTkButton(
                    self.thumb_bar,
                    text="",
                    image=t_img,
                    width=THUMB_SIZE,
                    height=THUMB_SIZE,
                    corner_radius=8,
                    fg_color=ThemeManager.get_color_pair("surface_alt"),
                    hover_color=ThemeManager.get_color_pair("primary_hover"),
                    border_width=2,
                    border_color=ThemeManager.get_color_pair("primary" if idx == 0 else "border"),
                    command=lambda i=idx: self._select_gallery_index(i),
                )
                t_btn.pack(side="left", padx=3, pady=2)
                self._thumb_btns.append(t_btn)
        else:
            self.gallery_counter_lbl = None
            self._thumb_btns = []

        self._render_gallery_image()

        # ================== ฝั่งขวา (T12): ข้อมูลสินค้า สีสันสดใส กรอบข้อความพอดีตัวอักษร ==================
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="nsew", padx=(4, 24), pady=20)

        # ป้ายแบรนด์ (สีฟ้า) และป้ายหมวดหมู่ (สีดำเข้ม/เหลือง) ขนาดพอดีคำ
        badges_row = ctk.CTkFrame(info, fg_color="transparent")
        badges_row.pack(fill="x", pady=(0, 4))
        if p.get("brand_name"):
            ctk.CTkLabel(
                badges_row,
                text=f"  {str(p['brand_name']).upper()}  ",
                font=ThemeManager.get_font("small_bold"),
                fg_color=("#DBEAFE", "#1E3A8A"),
                text_color=("#1D4ED8", "#BFDBFE"),
                corner_radius=6,
                height=26,
            ).pack(side="left", padx=(0, 6))
        if p.get("category_name"):
            ctk.CTkLabel(
                badges_row,
                text=f"  {p['category_name']}  ",
                font=ThemeManager.get_font("small_bold"),
                fg_color=("#18181B", "#334155"),
                text_color=("#FFB703", "#FDE68A"),
                corner_radius=6,
                height=26,
            ).pack(side="left", padx=(0, 6))

        # ชื่อสินค้า
        ctk.CTkLabel(
            info, text=p["name"], font=ThemeManager.get_font("h1"),
            text_color=ThemeManager.get_color_pair("text_main"),
            anchor="w", justify="left", wraplength=560,
        ).pack(fill="x", pady=(4, 8))

        # T12: กล่องราคาให้กรอบพอดีกับตัวอักษร (ไม่ยืดล้นเต็มความกว้างโดยไม่มีข้อมูล) พื้นชมพู/แดงอ่อน ตัวหนังสือแดงเข้มตัดกันชัด
        price_outer = ctk.CTkFrame(info, fg_color="transparent")
        price_outer.pack(fill="x", pady=(2, 8))

        self.price_card = ctk.CTkFrame(
            price_outer,
            fg_color=("#FFE4E6", "#3F1118"),
            corner_radius=12,
            border_width=2,
            border_color=("#E11D48", "#FB7185"),
        )
        self.price_card.pack(anchor="w")

        self.countdown_label = ctk.CTkLabel(
            self.price_card, text="", font=ThemeManager.get_font("small_bold"),
            text_color=("#BE123C", "#FDA4AF"), anchor="w",
        )

        price_row = ctk.CTkFrame(self.price_card, fg_color="transparent")
        price_row.pack(padx=16, pady=10)
        self.price_label = ctk.CTkLabel(
            price_row, text="", font=ThemeManager.get_font("price_big"),
            text_color=("#BE123C", "#FF4D5A"), anchor="w",
        )
        self.price_label.pack(side="left")
        self.old_price_label = ctk.CTkLabel(
            price_row, text="", font=ThemeManager.get_font_obj("body", overstrike=True),
            text_color=("#64748B", "#CBD5E1"),
        )
        self.discount_label = ctk.CTkLabel(
            price_row, text="", font=ThemeManager.get_font("small_bold"), corner_radius=6, height=26,
            fg_color="#E11D48", text_color="#FFFFFF",
        )

        # คะแนนรีวิว
        meta_row = ctk.CTkFrame(info, fg_color="transparent")
        meta_row.pack(fill="x", pady=(2, 6))
        RatingStars(meta_row, value=p.get("review_avg") or 0, count=p.get("review_count") or 0, size=14).pack(side="left")

        # --- T04: ตัวเลือกสินค้า (สี / สไตล์ / ด้าม / เอ็น / ไซซ์) พร้อมปุ่มชิปเลือกสี/สไตล์ที่เปลี่ยนรูปทันที ---
        options = p.get("options") or []
        if options:
            multi_type = len({o["option_type"] for o in options}) > 1
            opt_title = f"เลือก{options[0]['option_type']}" if not multi_type else "เลือกสี / สไตล์ / ตัวเลือกสินค้า"
            _lbl(info, opt_title, "body_bold").pack(fill="x", pady=(8, 4))

            for o in options:
                text = f"{o['option_type']}: {o['option_value']}" if multi_type else o["option_value"]
                if o["extra_price"]:
                    text += f"  (+{format_price(o['extra_price'])})"
                if not o["in_stock"]:
                    text += "  — หมด"
                self._option_map[text] = o

            default = next((t for t, o in self._option_map.items() if o["in_stock"]), next(iter(self._option_map)))
            self.option_var = ctk.StringVar(value=default)

            # ปุ่มชิปให้กดเลือกสี/สไตล์/ไซซ์ได้สะดวก พร้อมเปลี่ยนรูปตามสีที่เลือก
            chips_wrap = ctk.CTkFrame(info, fg_color="transparent")
            chips_wrap.pack(fill="x", pady=(0, 6))
            for idx, (label_txt, opt_obj) in enumerate(self._option_map.items()):
                r_i, c_i = divmod(idx, 4)
                btn = ctk.CTkButton(
                    chips_wrap,
                    text=opt_obj["option_value"] + (f" (+{int(opt_obj['extra_price'])})" if opt_obj["extra_price"] else ""),
                    height=32,
                    corner_radius=8,
                    font=ThemeManager.get_font("small_bold"),
                    command=lambda k=label_txt: self._on_chip_selected(k),
                )
                btn.grid(row=r_i, column=c_i, padx=(0, 6), pady=3, sticky="w")
                self._chip_buttons[label_txt] = btn

            _option_menu(
                info, list(self._option_map), self.option_var,
                command=lambda _v: self._refresh_option(),
            ).pack(anchor="w")
            self.option_hint = _lbl(info, "", "small", "text_muted", wraplength=480, justify="left")
            self.option_hint.pack(fill="x", pady=(4, 0))
        else:
            self.option_hint = _lbl(info, "")

        # --- จำนวน + ป้ายสต็อกสีเขียวพอดีคำ (T12) ---
        qty_row = ctk.CTkFrame(info, fg_color="transparent")
        qty_row.pack(fill="x", pady=(10, 0))
        _lbl(qty_row, "จำนวน", "body_bold").pack(side="left", padx=(0, 10))
        ctk.CTkButton(qty_row, text="−", width=36, command=lambda: self._change_qty(-1),
                      **ThemeManager.button_style("outline", "md")).pack(side="left")
        self.qty_label = _lbl(qty_row, "1", "body_bold", width=44)
        self.qty_label.configure(anchor="center")
        self.qty_label.pack(side="left")
        ctk.CTkButton(qty_row, text="+", width=36, command=lambda: self._change_qty(1),
                      **ThemeManager.button_style("outline", "md")).pack(side="left")

        self.stock_badge = ctk.CTkLabel(
            qty_row,
            text="",
            font=ThemeManager.get_font("small_bold"),
            corner_radius=8,
            height=30,
            padx=12,
        )
        self.stock_badge.pack(side="left", padx=12)

        # --- ปุ่มสั่งซื้อ (T12: เพิ่มลงตะกร้า=เหลือง, ซื้อเลย=แดง, รายการโปรด=ชมพู, เปรียบเทียบ=ฟ้า) ---
        buttons = ctk.CTkFrame(info, fg_color="transparent")
        buttons.pack(fill="x", pady=(16, 0))
        self._cart_ic = icon_utils.get_icon("cart", 18, ON_PRIMARY, ON_PRIMARY)
        self._flash_ic = icon_utils.get_icon("flash", 18, "#FFFFFF", "#FFFFFF")
        self._heart_ic = icon_utils.get_icon("heart", 16, "#FFFFFF", "#FFFFFF")
        self._heart_fill_ic = icon_utils.get_icon("heart_filled", 16, "#FFFFFF", "#FFFFFF")
        self._comp_ic = icon_utils.get_icon("compare", 16, "#FFFFFF", "#FFFFFF")

        self.add_btn = ctk.CTkButton(
            buttons, text=" เพิ่มลงตะกร้า", image=self._cart_ic, compound="left", width=160,
            command=lambda: self._add_to_cart(False),
            **ThemeManager.button_style("primary", "lg"),
        )
        self.add_btn.pack(side="left", padx=(0, 8))
        self.buy_btn = ctk.CTkButton(
            buttons, text=" ซื้อเลย", image=self._flash_ic, compound="left", width=125,
            command=lambda: self._add_to_cart(True),
            **ThemeManager.button_style("danger", "lg"),
        )
        self.buy_btn.pack(side="left", padx=(0, 8))
        self.wish_btn = ctk.CTkButton(
            buttons, text="", width=165, command=self._toggle_wishlist,
            **ThemeManager.button_style("pink", "lg"),
        )
        self.wish_btn.pack(side="left", padx=(0, 8))
        self._update_wish_button()
        if p.get("is_racket"):
            ctk.CTkButton(
                buttons, text=" เปรียบเทียบ", image=self._comp_ic, compound="left", width=130,
                command=lambda: self.controller.show("compare", ids=[p["id"]]),
                **ThemeManager.button_style("info", "lg"),
            ).pack(side="left")

        self.msg_label = _lbl(info, "", "small_bold", wraplength=520, justify="left")
        self.msg_label.pack(fill="x", pady=(8, 0))

    # ------------------ T03 & T12: กล่อง Technical Specifications โทนสีมืด/ดำ ตัวอักษรเหลือง-ขาว คมชัด ------------------
    def _build_tech_specs_section(self):
        p = self.product
        tech_specs = p.get("technical_specs") or []
        if not tech_specs:
            return

        spec_card = ctk.CTkFrame(
            self._body,
            fg_color=("#18181B", "#0F172A"),
            corner_radius=14,
            border_width=2,
            border_color=("#FFB703", "#F59E0B"),
        )
        spec_card.pack(fill="x", pady=(0, 12))

        hdr = ctk.CTkFrame(spec_card, fg_color=("#27272A", "#1E293B"), corner_radius=10)
        hdr.pack(fill="x", padx=14, pady=(12, 8))
        racket_ic = icon_utils.get_icon("racket", 18, "#FFB703", "#FFB703")
        ctk.CTkLabel(
            hdr,
            text="  Technical Specifications (ข้อมูลจำเพาะทางเทคนิค)",
            image=racket_ic,
            compound="left",
            font=ThemeManager.get_font("h3"),
            text_color="#FFB703",
            anchor="w",
        ).pack(side="left", padx=12, pady=8)

        table = ctk.CTkFrame(spec_card, fg_color="transparent")
        table.pack(fill="x", padx=18, pady=(0, 14))
        table.grid_columnconfigure(0, minsize=210)
        table.grid_columnconfigure(1, weight=1)

        for idx, item in enumerate(tech_specs):
            row_bg = ("#232329", "#1E293B") if idx % 2 == 0 else "transparent"
            row_frame = ctk.CTkFrame(table, fg_color=row_bg, corner_radius=6)
            row_frame.grid(row=idx, column=0, columnspan=2, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, minsize=210)
            row_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row_frame,
                text=f"• {item['label']}:",
                font=ThemeManager.get_font("body_bold"),
                text_color="#FDE68A",
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=(12, 16), pady=6)

            ctk.CTkLabel(
                row_frame,
                text=str(item["value"]),
                font=ThemeManager.get_font("body_bold"),
                text_color="#FFFFFF",
                anchor="w",
                justify="left",
                wraplength=650,
            ).grid(row=0, column=1, sticky="w", padx=(0, 12), pady=6)

    # ------------------ T04: แกลเลอรีหลายรูป + ผูกรูปกับสี/สไตล์ ------------------
    def _select_gallery_index(self, idx: int):
        if not self._gallery_items:
            return
        self._gallery_idx = idx % len(self._gallery_items)
        self._render_gallery_image()

    def _step_gallery(self, delta: int):
        if not self._gallery_items:
            return
        self._gallery_idx = (self._gallery_idx + delta) % len(self._gallery_items)
        self._render_gallery_image()

    def _render_gallery_image(self):
        if not self._gallery_items:
            return
        g_item = self._gallery_items[self._gallery_idx % len(self._gallery_items)]
        path = g_item.get("path")
        self._image = load_ctk_image(
            path, (IMG_WIDTH - 8, IMG_HEIGHT - 8),
            cover=False, corner_radius=14,
        )
        self.main_img_label.configure(image=self._image)

        color_tag = g_item.get("color_value")
        if color_tag:
            self.img_caption_lbl.configure(text=f"สี/สไตล์ที่แสดง: {color_tag}")
        else:
            self.img_caption_lbl.configure(text="")

        if self.gallery_counter_lbl is not None:
            self.gallery_counter_lbl.configure(text=f"รูปที่ {self._gallery_idx + 1} / {len(self._gallery_items)}")

        for i, btn in enumerate(getattr(self, "_thumb_btns", [])):
            btn.configure(
                border_color=ThemeManager.get_color_pair("primary" if i == self._gallery_idx else "border"),
                border_width=3 if i == self._gallery_idx else 1,
            )

    def _on_chip_selected(self, option_key: str):
        if hasattr(self, "option_var"):
            self.option_var.set(option_key)
            self._refresh_option()

    def _sync_gallery_to_option(self, opt: dict | None):
        if not opt or not self._gallery_items:
            return
        opt_val = str(opt.get("option_value") or "").strip().lower()
        opt_img = str(opt.get("image_path") or "").strip()
        for idx, g_item in enumerate(self._gallery_items):
            g_col = str(g_item.get("color_value") or "").strip().lower()
            g_path = str(g_item.get("path") or "").strip()
            if (opt_img and g_path == opt_img) or (opt_val and g_col and (opt_val == g_col or opt_val in g_col)):
                self._select_gallery_index(idx)
                return

    def _current_option(self):
        return self._option_map.get(self.option_var.get()) if self._option_map else None

    def _unit_price(self):
        opt = self._current_option()
        return opt["final_price"] if opt else self.product["effective_price"]

    def _stock(self):
        opt = self._current_option()
        return int(opt["stock"] or 0) if opt else int(self.product.get("stock") or 0)

    def _refresh_option(self):
        p = self.product
        opt = self._current_option()
        unit = self._unit_price()
        self.price_label.configure(text=format_price(unit))

        # อัปเดตสีปุ่มชิปตัวเลือกที่กำลังเลือก
        selected_key = self.option_var.get() if hasattr(self, "option_var") else None
        for k, btn in self._chip_buttons.items():
            if k == selected_key:
                btn.configure(
                    fg_color=ThemeManager.get_color_pair("primary"),
                    text_color=ON_PRIMARY,
                    border_width=2,
                    border_color=("#111318", "#FFFFFF"),
                )
            else:
                btn.configure(
                    fg_color=ThemeManager.get_color_pair("surface_alt"),
                    text_color=ThemeManager.get_color_pair("text_main"),
                    border_width=1,
                    border_color=ThemeManager.get_color_pair("border"),
                )

        self._sync_gallery_to_option(opt)

        pct = 0
        if p.get("is_on_sale"):
            full = (p.get("price") or 0) + (opt["extra_price"] if opt else 0)
            pct = discount_percent(full, unit)
            if pct:
                self.old_price_label.configure(text=format_price(full))
        if pct:
            self.old_price_label.pack(side="left", padx=(10, 0))
            self.discount_label.configure(text=f" ลด {pct}% ")
            self.discount_label.pack(side="left", padx=(8, 0))
        else:
            self.old_price_label.pack_forget()
            self.discount_label.pack_forget()

        stock = self._stock()
        if stock > 0:
            self.stock_badge.configure(
                text=f"✓ มีสินค้าพร้อมส่ง {stock:,} ชิ้น",
                fg_color=("#DCFCE7", "#14532D"),
                text_color=("#15803D", "#86EFAC"),
            )
            self._qty = max(1, min(self._qty, stock, MAX_QTY))
            state, add_text = "normal", " เพิ่มลงตะกร้า"
        else:
            self.stock_badge.configure(
                text="⛔ สินค้าหมดชั่วคราว",
                fg_color=("#FEE2E2", "#450A0A"),
                text_color=("#B91C1C", "#FCA5A5"),
            )
            self._qty = 1
            state, add_text = "disabled", "สินค้าหมด"
        self.qty_label.configure(text=str(self._qty))
        self.add_btn.configure(state=state, text=add_text)
        self.buy_btn.configure(state=state)

        if opt and opt["option_type"] == "เอ็น" and "ขึ้นเอ็น" in str(opt["option_value"]):
            self.option_hint.configure(text="ต้องการระบุความตึงเอ็น (lbs)? แจ้งร้านทางแชทหลังสั่งซื้อได้เลย")
        else:
            self.option_hint.configure(text="")
        self._update_bundle_total()

    def _change_qty(self, delta):
        limit = min(self._stock(), MAX_QTY)
        new = self._qty + delta
        if new < 1 or new > limit:
            return
        self._qty = new
        self.qty_label.configure(text=str(new))
        self._update_bundle_total()

    def _start_countdown(self):
        left = self.product.get("sale_seconds_left")
        if self.product.get("is_on_sale") and left is not None:
            self._deadline = time.time() + int(left)
            self.countdown_label.pack(fill="x", padx=16, pady=(8, 0), before=self.price_label.master)
            self._tick()
        else:
            self._deadline = None
            self.countdown_label.pack_forget()

    def _tick(self):
        self._tick_job = None
        if self._deadline is None or not self.winfo_exists():
            return
        left = int(self._deadline - time.time())
        if left <= 0:
            self.countdown_label.configure(text="Flash Sale สิ้นสุดแล้ว")
            return
        self.countdown_label.configure(text=f"⚡ FLASH SALE เหลือเวลา {format_countdown(left)}")
        self._tick_job = self.after(1000, self._tick)

    def _cancel_tick(self):
        self._deadline = None
        if self._tick_job is not None:
            try:
                self.after_cancel(self._tick_job)
            except Exception:  # noqa: BLE001
                pass
            self._tick_job = None

    def _set_msg(self, text, ok=True):
        self.msg_label.configure(text=text, text_color=ThemeManager.get_color_pair("success" if ok else "danger"))

    def _add_to_cart(self, buy_now):
        if not Session.is_authenticated():
            self.controller.pending_after_login = ("product_detail", {"product_id": self.product["id"]})
            self.controller.show("login", info_message="กรุณาเข้าสู่ระบบก่อนเพิ่มสินค้าลงตะกร้าหรือสั่งซื้อ")
            return
        opt = self._current_option()
        try:
            result = cart_service.add_to_cart(
                common.user_id(), self.product["id"], opt["id"] if opt else None, self._qty,
            )
        except (ValueError, PermissionError) as exc:
            self._set_msg(str(exc), ok=False)
            return
        self.controller.refresh_shell()
        if buy_now:
            self.controller.show("cart")
            return
        self._set_msg(f"✓ เพิ่มลงตะกร้าแล้ว (ในตะกร้ามี {result['cart_count']:,} ชิ้น)")

    def _toggle_wishlist(self):
        if not Session.is_authenticated():
            self.controller.pending_after_login = ("product_detail", {"product_id": self.product["id"]})
            self.controller.show("login", info_message="กรุณาเข้าสู่ระบบก่อนเพิ่มรายการโปรด")
            return
        state = common.toggle_wishlist(self, self.product["id"])
        if state is not None:
            self._in_wishlist = state
            self._update_wish_button()

    def _update_wish_button(self):
        if self._in_wishlist:
            self.wish_btn.configure(text=" อยู่ในรายการโปรด", image=self._heart_fill_ic, compound="left")
        else:
            self.wish_btn.configure(text=" เพิ่มในรายการโปรด", image=self._heart_ic, compound="left")

    def _build_addons(self):
        addons = self.product.get("addons") or []
        if not addons:
            return
        card = ThemeManager.make_card(self._body)
        card.pack(fill="x", pady=(0, 12))
        hdr = ctk.CTkFrame(card, fg_color=("#DCFCE7", "#14532D"), corner_radius=8)
        hdr.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            hdr, text="  ซื้อคู่กันคุ้มกว่า (Bundle Deal)",
            font=ThemeManager.get_font("h3"),
            text_color=("#15803D", "#86EFAC"), anchor="w",
        ).pack(side="left", padx=12, pady=6)
        _lbl(card, "เลือกสินค้าเสริมแล้วเพิ่มลงตะกร้าพร้อมกันได้ในคลิกเดียว", "small", "text_muted"
             ).pack(fill="x", padx=20, pady=(0, 6))

        for addon in addons:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                row, text=addon["name"], variable=var, command=self._update_bundle_total,
                state="normal" if addon.get("in_stock", True) else "disabled",
                font=ThemeManager.get_font("body"), text_color=ThemeManager.get_color_pair("text_main"),
                fg_color=ThemeManager.get_color_pair("primary"),
                hover_color=ThemeManager.get_color_pair("primary_hover"), checkmark_color=ON_PRIMARY,
            ).pack(side="left")

            options, opt_var = {}, None
            try:
                detail = product_service.get_product_detail(addon["id"], user_id=common.user_id())
                for o in detail.get("options") or []:
                    text = o["option_value"] + ("" if o["in_stock"] else "  — หมด")
                    options[text] = o
            except (ValueError, PermissionError):
                options = {}
            if options:
                first = next((t for t, o in options.items() if o["in_stock"]), next(iter(options)))
                opt_var = ctk.StringVar(value=first)
                _option_menu(row, list(options), opt_var, command=lambda _v: self._update_bundle_total(),
                             width=170).pack(side="right")
            price_label = _lbl(row, "", "body_bold")
            price_label.pack(side="right", padx=12)
            self._addon_rows.append({"product": addon, "var": var, "options": options,
                                     "opt_var": opt_var, "price_label": price_label})

        foot = ctk.CTkFrame(card, fg_color="transparent")
        foot.pack(fill="x", padx=20, pady=(8, 16))
        self.bundle_total_label = _lbl(foot, "", "body_bold")
        self.bundle_total_label.pack(side="left")
        self.bundle_btn = ctk.CTkButton(foot, text="เพิ่มชุดนี้ลงตะกร้า", width=170, command=self._add_bundle,
                                        **ThemeManager.button_style("primary", "md"))
        self.bundle_btn.pack(side="right")
        self.bundle_msg = _lbl(card, "", "small", wraplength=700, justify="left")
        self.bundle_msg.pack(fill="x", padx=20, pady=(0, 12))

    def _addon_option(self, row):
        return row["options"].get(row["opt_var"].get()) if row["opt_var"] is not None else None

    def _addon_price(self, row):
        opt = self._addon_option(row)
        return opt["final_price"] if opt else row["product"]["effective_price"]

    def _update_bundle_total(self):
        if not self._addon_rows or not hasattr(self, "bundle_total_label"):
            return
        selected = [r for r in self._addon_rows if r["var"].get()]
        for row in self._addon_rows:
            row["price_label"].configure(text=format_price(self._addon_price(row)))
        total = self._unit_price() * self._qty + sum(self._addon_price(r) for r in selected)
        self.bundle_total_label.configure(text=f"รวมชุดที่เลือก: {format_price(round(total, 2))}")
        self.bundle_btn.configure(state="normal" if selected and self._stock() > 0 else "disabled")

    def _add_bundle(self):
        if not Session.is_authenticated():
            self.controller.show("login", info_message="กรุณาเข้าสู่ระบบก่อนเพิ่มชุดสินค้าลงตะกร้า")
            return
        selected = [r for r in self._addon_rows if r["var"].get()]
        if not selected:
            return
        opt = self._current_option()
        addon_ids = [r["product"]["id"] for r in selected]
        addon_options = {r["product"]["id"]: self._addon_option(r)["id"] for r in selected if r["options"]}
        try:
            result = cart_service.add_with_addons(
                common.user_id(), self.product["id"], addon_ids,
                option_id=opt["id"] if opt else None, qty=self._qty, addon_options=addon_options or None,
            )
        except (ValueError, PermissionError) as exc:
            self.bundle_msg.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))
            return
        self.controller.refresh_shell()
        self.bundle_msg.configure(
            text=f"✓ เพิ่มชุดนี้ลงตะกร้าแล้ว (ในตะกร้ามี {result['cart_count']:,} ชิ้น)",
            text_color=ThemeManager.get_color_pair("success"),
        )

    def _build_description(self):
        card = ThemeManager.make_card(self._body)
        card.pack(fill="x", pady=(0, 12))
        hdr = ctk.CTkFrame(card, fg_color=("#E0F2FE", "#0C4A6E"), corner_radius=8)
        hdr.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            hdr, text="  รายละเอียดสินค้า",
            font=ThemeManager.get_font("h3"),
            text_color=("#0369A1", "#BAE6FD"), anchor="w",
        ).pack(side="left", padx=12, pady=6)
        _lbl(card, self.product.get("description") or "ไม่มีรายละเอียดเพิ่มเติม", "body",
             wraplength=900, justify="left").pack(fill="x", padx=20, pady=(4, 16))

    def _build_reviews(self):
        p = self.product
        card = ThemeManager.make_card(self._body)
        card.pack(fill="x", pady=(0, 12))
        head = ctk.CTkFrame(card, fg_color=("#FCE7F3", "#500724"), corner_radius=8)
        head.pack(fill="x", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            head, text="  รีวิวจากลูกค้าจริง",
            font=ThemeManager.get_font("h3"),
            text_color=("#9D174D", "#FBCFE8"), anchor="w",
        ).pack(side="left", padx=12, pady=6)
        RatingStars(head, value=p.get("review_avg") or 0, count=p.get("review_count") or 0, size=16
                    ).pack(side="left", padx=12)

        self.review_list = ctk.CTkFrame(card, fg_color="transparent")
        self.review_list.pack(fill="x", padx=20)
        self.review_more_btn = ctk.CTkButton(card, text="ดูรีวิวเพิ่มเติม", width=150,
                                             command=self._load_reviews, **ThemeManager.button_style("outline", "sm"))
        self.review_error = common.error_label(card)
        self.review_error.pack(fill="x", padx=20)
        self._load_reviews()
        ctk.CTkFrame(card, fg_color="transparent", height=12).pack()

    def _load_reviews(self):
        page = self._review_page + 1
        try:
            result = review_service.list_reviews(self.product["id"], page=page, page_size=REVIEW_PAGE_SIZE)
        except (ValueError, PermissionError) as exc:
            self.review_error.configure(text=str(exc))
            return
        self.review_error.configure(text="")
        if result["total"] == 0:
            _lbl(self.review_list, "ยังไม่มีรีวิวสำหรับสินค้านี้", "body", "text_muted").pack(fill="x", pady=8)
        for item in result["items"]:
            self._add_review_row(item)
        self._review_page, self._review_pages = result["page"], result["pages"]
        if self._review_page < self._review_pages:
            self.review_more_btn.pack(pady=(4, 0), before=self.review_error)
        else:
            self.review_more_btn.pack_forget()

    def _add_review_row(self, item):
        row = ctk.CTkFrame(self.review_list, fg_color=ThemeManager.get_color_pair("surface_alt"), corner_radius=8)
        row.pack(fill="x", pady=4)
        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(8, 0))
        _lbl(top, item.get("reviewer_name") or "ผู้ใช้", "small_bold").pack(side="left")
        RatingStars(top, value=item["rating"], size=13, show_value=False).pack(side="left", padx=8)
        _lbl(top, format_datetime(item.get("created_at")), "tiny", "text_muted").pack(side="right")
        if item.get("comment"):
            _lbl(row, item["comment"], "body", wraplength=860, justify="left").pack(fill="x", padx=12, pady=(2, 8))
        else:
            ctk.CTkFrame(row, fg_color="transparent", height=6).pack()

    def destroy(self):
        self._cancel_tick()
        super().destroy()
