"""
ui/pages/buyer/home.py
หน้าแรก (Storefront — ปรับปรุงตามข้อ 2, 3, 4, 5 + T05, T06):
- ข้อ 2: ปุ่ม "แบนเนอร์ก่อนหน้า / แบนเนอร์ถัดไป" ตัวหนังสือสีสว่างชัดเจน ซ่อนปุ่มเลื่อน/ตัวนับเมื่อมีรูปเดียว
- T05: หน้า FLASH SALE แสดงสินค้าทุกอย่างที่ลดราคา และเลื่อนอัตโนมัติจากขวาไปซ้ายแบบช้าๆ
  * เอาเมาส์ชี้ -> หยุดเลื่อน | เอาเมาส์ออก -> เลื่อนต่อเรื่อยๆ | เลื่อนจนครบแล้ววนกลับมาเริ่มใหม่ (loop)
  * ถ้าสินค้าลดราคามีน้อยจนไม่เต็มความกว้าง จะแสดงนิ่งไม่เลื่อน
- T06: ส่วนการเก็บคูปอง ผู้ซื้อ
  * หน้าหลักโชว์คูปองทีละ 3 ใบ (หรือตามที่ Owner ตั้งค่า) เปลี่ยนชุดไปเรื่อยๆ ช้าๆ ถ้ามีไม่ถึง 3 ใบจัดระยะให้พอดี
  * มีปุ่ม "คูปองของฉัน (ที่เก็บไว้ทั้งหมด)" และปุ่ม "ดูคูปองทั้งหมดที่มี"
  * แยกหมวดหมู่คูปอง: คูปองส่วนลดค่าส่ง, คูปองส่วนลดเป็น %, คูปองส่วนลดเป็น บาท, และอื่นๆ
"""

import random
import tkinter as tk
import webbrowser

import customtkinter as ctk

from core.session import Session
from services import banner_service, contact_service, coupon_service, product_service, settings_service
from ui.components.navbar import open_store_location_dialog
from ui.components.product_card import CARD_HEIGHT, CARD_WIDTH
from ui.pages.buyer import common
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.formatters import format_date_thai, format_price
from utils.image_utils import load_ctk_image
from utils.validators import is_valid_https_url

FLASH_LIMIT = 60
RECOMMEND_LIMIT = 24
BANNER_ROTATE_MS = 5000
COUPON_ROTATE_DEFAULT_SEC = 9
HOME_COUPONS_PER_VIEW_DEFAULT = 3
_FIRE_COLORS = ("#E63946", "#FF4500", "#DC2626", "#EA580C", "#FF2A2A")


class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._banners = []
        self._banner_idx = 0
        self._banner_job = None
        self._fire_job = None
        self._fire_idx = 0
        self._banner_img = None
        self._cat_imgs = []
        self._brand_imgs = []

        # T05: สถานะการเลื่อนอัตโนมัติของ Flash Sale
        self._flash_items = []
        self._flash_scroll_job = None
        self._flash_paused = False
        self._flash_offset = 0.0
        self._flash_set_width = 0

        # T06: สถานะการสลับชุดคูปองหน้าหลักทีละ 3 ใบ
        self._public_coupons = []
        self._coupon_rules = []
        self._coupon_page_idx = 0
        self._coupon_rotate_job = None
        self._coupon_paused = False
        self._uid = None

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=20, pady=16)

        self._build_banner_carousel(self.body)

        self.error_label = common.error_label(self.body)
        self.error_label.pack(fill="x", pady=(6, 0))

        # --- T06: คูปองส่วนลด & โปรซื้อครบรับคูปอง (แสดงทีละ 3 ใบ สลับชุดช้าๆ + ปุ่มดูคูปองทั้งหมด/ของฉัน) ---
        self.coupon_section = ctk.CTkFrame(self.body, fg_color="transparent")
        self.coupon_section.pack(fill="x", pady=(10, 4))
        self.coupon_section.bind("<Enter>", lambda _e: self._set_coupon_pause(True), add="+")
        self.coupon_section.bind("<Leave>", self._on_coupon_leave, add="+")

        # --- T05: Flash Sale & สินค้าลดราคาทั้งหมด เลื่อนขวา -> ซ้ายแบบช้าๆ ---
        self.flash_box = ctk.CTkFrame(
            self.body,
            fg_color=("#FAD2D5", "#3B181C"),
            corner_radius=14,
            border_width=2,
            border_color=ThemeManager.get_color_pair("danger"),
        )
        flash_hdr = ctk.CTkFrame(self.flash_box, fg_color=ThemeManager.get_color_pair("danger"), corner_radius=12)
        flash_hdr.pack(fill="x", padx=2, pady=(2, 6))
        self._flash_ic = icon_utils.get_icon("flash", 20, "#FFB703", "#FFB703")
        ctk.CTkLabel(
            flash_hdr, text="  FLASH SALE — สินค้าลดราคาทั้งหมด (ชี้เมาส์เพื่อหยุดดู)",
            image=self._flash_ic, compound="left",
            font=ThemeManager.get_font("h3"), text_color="#FFFFFF",
        ).pack(side="left", padx=16, pady=10)
        ctk.CTkButton(
            flash_hdr, text="ดูสินค้าลดราคาทั้งหมด ›", width=165,
            command=lambda: self.controller.show("category", on_sale=True),
            **ThemeManager.button_style("primary", "sm"),
        ).pack(side="right", padx=12, pady=8)

        # Canvas สำหรับเลื่อนการ์ดสินค้า Flash Sale ขวา -> ซ้ายอย่างลื่นไหล
        self.flash_viewport = ctk.CTkFrame(self.flash_box, fg_color="transparent", height=CARD_HEIGHT + 18)
        self.flash_viewport.pack(fill="x", padx=12, pady=(2, 12))
        self.flash_viewport.pack_propagate(False)

        self.flash_canvas = tk.Canvas(
            self.flash_viewport,
            bg="#FAD2D5",
            highlightthickness=0,
            bd=0,
            height=CARD_HEIGHT + 14,
        )
        self.flash_canvas.pack(fill="both", expand=True)
        self.flash_track = ctk.CTkFrame(self.flash_canvas, fg_color="transparent")
        self._flash_win_id = self.flash_canvas.create_window((0, 4), window=self.flash_track, anchor="nw")

        self.flash_box.bind("<Enter>", self._on_flash_enter, add="+")
        self.flash_box.bind("<Leave>", self._on_flash_leave, add="+")
        self.flash_canvas.bind("<Enter>", self._on_flash_enter, add="+")
        self.flash_canvas.bind("<Leave>", self._on_flash_leave, add="+")
        self.flash_canvas.bind("<Configure>", lambda _e: self._sync_flash_canvas_bg())

        # --- ข้อ 4: หมวดหมู่สินค้า & แบรนด์ชั้นนำ ---
        self.category_header = self._build_icon_section_header(
            self.body, "category", "หมวดหมู่สินค้าและแบรนด์ชั้นนำ"
        )
        self.category_header.pack(fill="x", pady=(18, 6))
        self.category_grid = common.WrapGrid(self.body, item_width=195, gap=12)
        self.category_grid.pack(fill="x")

        self.brand_section = ctk.CTkFrame(self.body, fg_color="transparent")
        self.brand_section.pack(fill="x", pady=(10, 4))

        # --- ข้อ 5: สินค้าแนะนำยอดนิยม (ฟอนต์สีแดงเหมือนไฟ + แสดงแบบสุ่มเยอะๆ) ---
        self.recommend_hdr = ctk.CTkFrame(self.body, fg_color="transparent")
        self.recommend_hdr.pack(fill="x", pady=(18, 6))
        self._fire_ic = icon_utils.get_icon("fire", 24, "#E63946", "#FF4500")
        self.popular_title_lbl = ctk.CTkLabel(
            self.recommend_hdr,
            text="  สินค้าแนะนำยอดนิยม",
            image=self._fire_ic,
            compound="left",
            font=ThemeManager.get_font("h2"),
            text_color="#E63946",
            anchor="w",
        )
        self.popular_title_lbl.pack(side="left")

        right_rec = ctk.CTkFrame(self.recommend_hdr, fg_color="transparent")
        right_rec.pack(side="right")
        self._refresh_ic = icon_utils.get_icon("refresh", 15, "#111318", "#F8FAFC")
        ctk.CTkButton(
            right_rec, text=" สุ่มสินค้าใหม่", image=self._refresh_ic, compound="left", width=120,
            command=self._reshuffle_products,
            **ThemeManager.button_style("outline", "sm"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            right_rec, text="ดูสินค้าทั้งหมด ›", width=130,
            command=lambda: self.controller.show("category"),
            **ThemeManager.button_style("ghost", "sm"),
        ).pack(side="left")

        self.recommend_grid = common.WrapGrid(self.body)
        self.recommend_grid.pack(fill="x")

        # --- สินค้าที่เพิ่งดูล่าสุด (E5) ---
        self.recent_box = ctk.CTkFrame(self.body, fg_color="transparent")
        self._build_icon_section_header(self.recent_box, "eye", "สินค้าที่คุณเพิ่งดูล่าสุด").pack(fill="x", pady=(16, 4))
        self.recent_grid = common.WrapGrid(self.recent_box)
        self.recent_grid.pack(fill="x")

        # --- ส่วนท้าย: เกี่ยวกับร้าน ที่ตั้งหน้าร้าน และช่องทางติดต่อ ---
        self.footer_box = ctk.CTkFrame(
            self.body, fg_color=ThemeManager.get_color_pair("secondary"),
            corner_radius=14, border_width=2, border_color=ThemeManager.get_color_pair("primary"),
        )
        self.footer_box.pack(fill="x", pady=(22, 8))

        self._start_fire_anim()

    def _build_icon_section_header(self, parent, icon_name: str, title: str):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ic = icon_utils.get_icon(icon_name, 20, "#E63946", "#FFB703")
        lbl = ctk.CTkLabel(
            frame, text=f"  {title}", image=ic, compound="left",
            font=ThemeManager.get_font("h2"),
            text_color=ThemeManager.get_color_pair("text_main"), anchor="w",
        )
        lbl.image = ic
        lbl.pack(side="left")
        return frame

    # ------------------------------------------------------------------ แอนิเมชันสีไฟหัวข้อสินค้ายอดนิยม (ข้อ 5)
    def _start_fire_anim(self):
        self._stop_fire_anim()
        self._fire_job = self.after(550, self._tick_fire_anim)

    def _stop_fire_anim(self):
        if self._fire_job is not None:
            try:
                self.after_cancel(self._fire_job)
            except Exception:  # noqa: BLE001
                pass
            self._fire_job = None

    def _tick_fire_anim(self):
        self._fire_job = None
        if not self.winfo_exists():
            return
        try:
            self._fire_idx = (self._fire_idx + 1) % len(_FIRE_COLORS)
            col = _FIRE_COLORS[self._fire_idx]
            self.popular_title_lbl.configure(text_color=col)
        except Exception:  # noqa: BLE001
            pass
        if self.winfo_exists():
            self._fire_job = self.after(550, self._tick_fire_anim)

    # ------------------------------------------------------------------ T05: Flash Sale เลื่อนอัตโนมัติ ขวา -> ซ้าย
    def _sync_flash_canvas_bg(self):
        try:
            mode = ctk.get_appearance_mode().lower()
            bg = "#3B181C" if mode == "dark" else "#FAD2D5"
            self.flash_canvas.configure(bg=bg)
        except Exception:  # noqa: BLE001
            pass

    def _on_flash_enter(self, _event=None):
        self._flash_paused = True

    def _on_flash_leave(self, _event=None):
        try:
            x, y = self.winfo_pointerxy()
            under = self.winfo_containing(x, y)
            if under is not None and str(under).startswith(str(self.flash_box)):
                return
        except Exception:  # noqa: BLE001
            pass
        self._flash_paused = False

    def _stop_flash_scroll(self):
        if self._flash_scroll_job is not None:
            try:
                self.after_cancel(self._flash_scroll_job)
            except Exception:  # noqa: BLE001
                pass
            self._flash_scroll_job = None

    def _render_flash_sale(self, flash_products: list[dict]):
        self._stop_flash_scroll()
        for child in self.flash_track.winfo_children():
            child.destroy()

        self._flash_items = list(flash_products or [])
        if not self._flash_items:
            self.flash_box.pack_forget()
            return

        self.flash_box.pack(fill="x", pady=(10, 4), before=self.category_header)
        self._sync_flash_canvas_bg()

        card_gap = 12
        single_count = len(self._flash_items)
        self._flash_set_width = single_count * (CARD_WIDTH + card_gap)

        # ถ้ามีสินค้าลดราคามากพอที่จะเลื่อน ให้วางชุดการ์ดซ้ำ 2 ชุดต่อกันเพื่อให้เลื่อนวนรอบ (loop) แบบไร้รอยต่อ
        need_loop = single_count >= 4
        display_list = (self._flash_items + self._flash_items) if need_loop else self._flash_items

        cards = common.product_cards(self.flash_track, display_list, self.controller)
        for card in cards:
            card.pack(side="left", padx=(0, card_gap), pady=2)
            card.bind("<Enter>", self._on_flash_enter, add="+")
            card.bind("<Leave>", self._on_flash_leave, add="+")
            for sub in card.winfo_children():
                sub.bind("<Enter>", self._on_flash_enter, add="+")

        self._flash_offset = 0.0
        if hasattr(self.flash_canvas, "coords"):
            self.flash_canvas.coords(self._flash_win_id, 0, 4)
        if need_loop:
            self._flash_scroll_job = self.after(60, self._tick_flash_scroll)

    def _tick_flash_scroll(self):
        self._flash_scroll_job = None
        if not self.winfo_exists():
            return
        try:
            self._sync_flash_canvas_bg()
            viewport_w = max(1, self.flash_canvas.winfo_width())
            # ถ้าสินค้ามีน้อยจนไม่เต็มความกว้าง ไม่ต้องเลื่อน
            if self._flash_set_width <= viewport_w:
                if hasattr(self.flash_canvas, "coords"):
                    self.flash_canvas.coords(self._flash_win_id, 0, 4)
            elif not self._flash_paused and self.winfo_ismapped():
                speed = max(1, min(10, settings_service.get_int("flash_sale_scroll_speed", 2)))
                self._flash_offset += speed * 0.85
                if self._flash_offset >= self._flash_set_width:
                    self._flash_offset -= self._flash_set_width
                if hasattr(self.flash_canvas, "coords"):
                    self.flash_canvas.coords(self._flash_win_id, -int(self._flash_offset), 4)
        except Exception:  # noqa: BLE001
            return

        if self.winfo_exists() and self._flash_items:
            self._flash_scroll_job = self.after(35, self._tick_flash_scroll)

    # ------------------------------------------------------------------ แบนเนอร์สไลด์โชว์ 1–10 ภาพ (ข้อ 2)
    def _build_banner_carousel(self, parent):
        self.banner_card = ctk.CTkFrame(
            parent, fg_color=ThemeManager.get_color_pair("secondary"),
            corner_radius=16, border_width=2, border_color=ThemeManager.get_color_pair("primary"),
        )
        self.banner_card.pack(fill="x")
        self.banner_card.grid_columnconfigure(0, weight=3)
        self.banner_card.grid_columnconfigure(1, weight=2)

        left = ctk.CTkFrame(self.banner_card, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=26, pady=20)

        tag_row = ctk.CTkFrame(left, fg_color="transparent")
        tag_row.pack(fill="x", pady=(0, 6))
        self._racket_tag_ic = icon_utils.get_icon("racket", 14, ON_PRIMARY, ON_PRIMARY)
        self.banner_tag_lbl = ctk.CTkLabel(
            tag_row, text="  BADMINTON PRO OFFICIAL  ", image=self._racket_tag_ic, compound="left",
            font=ThemeManager.get_font("small_bold"),
            fg_color=ThemeManager.get_color_pair("primary"), text_color=ON_PRIMARY,
            corner_radius=6, height=24, padx=6,
        )
        self.banner_tag_lbl.pack(side="left")
        self.banner_counter = ctk.CTkLabel(
            tag_row, text="แบนเนอร์ 1/1", font=ThemeManager.get_font("small_bold"),
            text_color="#FDE68A",
        )
        self.banner_counter.pack(side="left", padx=10)

        self.banner_title = ctk.CTkLabel(
            left, text="Badminton Pro Shop", font=ThemeManager.get_font("h1"),
            text_color="#FFFFFF", anchor="w", justify="left", wraplength=540,
        )
        self.banner_title.pack(fill="x")

        self.banner_sub = ctk.CTkLabel(
            left, text="ไม้แบด ลูกแบด รองเท้า และอุปกรณ์ครบ จากแบรนด์ชั้นนำของแท้ 100%",
            font=ThemeManager.get_font("body"),
            text_color="#E2E8F0", anchor="w", justify="left", wraplength=540,
        )
        self.banner_sub.pack(fill="x", pady=(4, 14))

        buttons = ctk.CTkFrame(left, fg_color="transparent")
        buttons.pack(fill="x")
        self._cart_ic = icon_utils.get_icon("cart", 16, ON_PRIMARY, ON_PRIMARY)
        self._target_ic = icon_utils.get_icon("target", 16, "#FFFFFF", "#FFFFFF")
        self._compare_ic = icon_utils.get_icon("compare", 16, "#FFFFFF", "#FFFFFF")
        ctk.CTkButton(
            buttons, text=" เลือกซื้อสินค้า", image=self._cart_ic, compound="left", width=142,
            command=lambda: self.controller.show("category"),
            **ThemeManager.button_style("primary", "md"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons, text=" ตัวช่วยเลือกไม้", image=self._target_ic, compound="left", width=142,
            command=lambda: self.controller.show("racket_finder"),
            **ThemeManager.button_style("danger", "md"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            buttons, text=" เปรียบเทียบ 2–5 รุ่น", image=self._compare_ic, compound="left", width=162,
            command=lambda: self.controller.show("compare"),
            **ThemeManager.button_style("info", "md"),
        ).pack(side="left", padx=(0, 8))

        self.slide_ctrl = ctk.CTkFrame(left, fg_color="transparent")
        self.slide_ctrl.pack(fill="x", pady=(12, 0))
        self.prev_banner_btn = ctk.CTkButton(
            self.slide_ctrl,
            text="‹ แบนเนอร์ก่อนหน้า",
            width=136,
            height=32,
            corner_radius=8,
            font=ThemeManager.get_font("small_bold"),
            fg_color="#252A34",
            hover_color="#384152",
            text_color="#FFFFFF",
            border_width=1,
            border_color="#FFB703",
            command=lambda: self._step_banner(-1),
        )
        self.prev_banner_btn.pack(side="left", padx=(0, 8))
        self.next_banner_btn = ctk.CTkButton(
            self.slide_ctrl,
            text="แบนเนอร์ถัดไป ›",
            width=136,
            height=32,
            corner_radius=8,
            font=ThemeManager.get_font("small_bold"),
            fg_color="#252A34",
            hover_color="#384152",
            text_color="#FFFFFF",
            border_width=1,
            border_color="#FFB703",
            command=lambda: self._step_banner(1),
        )
        self.next_banner_btn.pack(side="left")

        right = ctk.CTkFrame(self.banner_card, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=24, pady=16)
        self.banner_img_lbl = ctk.CTkLabel(right, text="")
        self.banner_img_lbl.pack()

    def _step_banner(self, delta: int):
        if not self._banners:
            return
        self._banner_idx = (self._banner_idx + delta) % len(self._banners)
        self._paint_banner()

    def _auto_banner(self):
        self._banner_job = None
        if not self.winfo_exists():
            return
        if self.winfo_ismapped() and len(self._banners) > 1:
            self._step_banner(1)
        if self.winfo_exists() and len(self._banners) > 1:
            self._banner_job = self.after(BANNER_ROTATE_MS, self._auto_banner)

    def _stop_banner_job(self):
        if self._banner_job is not None:
            try:
                self.after_cancel(self._banner_job)
            except Exception:  # noqa: BLE001
                pass
            self._banner_job = None

    def _paint_banner(self):
        total = len(self._banners)
        if total <= 1:
            self.slide_ctrl.pack_forget()
            self.banner_counter.pack_forget()
        else:
            if not self.banner_counter.winfo_ismapped():
                self.banner_counter.pack(side="left", padx=10)
            if not self.slide_ctrl.winfo_ismapped():
                self.slide_ctrl.pack(fill="x", pady=(12, 0))

        if not self._banners:
            self.banner_title.configure(text="Badminton Pro Shop")
            self.banner_sub.configure(text="ไม้แบด ลูกแบด รองเท้า และอุปกรณ์ครบ จากแบรนด์ชั้นนำ")
            self._banner_img = load_ctk_image(None, (260, 150), cover=False, corner_radius=10)
            self.banner_img_lbl.configure(image=self._banner_img)
            return

        b = self._banners[self._banner_idx % total]
        self.banner_title.configure(text=b.get("title") or "Badminton Pro Shop")
        self.banner_sub.configure(text=b.get("subtitle") or "โปรโมชันพิเศษสำหรับคนรักแบดมินตัน")
        self.banner_counter.configure(text=f"แบนเนอร์ {self._banner_idx + 1}/{total}")
        has_img = bool(b.get("image_path"))
        self._banner_img = load_ctk_image(
            b.get("image_path"), (260, 150), cover=has_img, corner_radius=10
        )
        self.banner_img_lbl.configure(image=self._banner_img)

    # ------------------------------------------------------------------ T06: คูปองหน้าหลัก (ทีละ 3 ใบ สลับชุดช้าๆ + ปุ่มดูทั้งหมด)
    def _set_coupon_pause(self, paused: bool):
        self._coupon_paused = bool(paused)

    def _on_coupon_leave(self, _event=None):
        try:
            x, y = self.winfo_pointerxy()
            under = self.winfo_containing(x, y)
            if under is not None and str(under).startswith(str(self.coupon_section)):
                return
        except Exception:  # noqa: BLE001
            pass
        self._coupon_paused = False

    def _stop_coupon_rotate(self):
        if self._coupon_rotate_job is not None:
            try:
                self.after_cancel(self._coupon_rotate_job)
            except Exception:  # noqa: BLE001
                pass
            self._coupon_rotate_job = None

    def _get_coupon_rotate_ms(self) -> int:
        try:
            sec = settings_service.get_int("coupon_rotate_seconds", COUPON_ROTATE_DEFAULT_SEC)
            return max(3000, min(120000, int(sec) * 1000))
        except Exception:  # noqa: BLE001
            return COUPON_ROTATE_DEFAULT_SEC * 1000

    def _get_coupons_per_view(self) -> int:
        try:
            n = settings_service.get_int("home_coupons_per_view", HOME_COUPONS_PER_VIEW_DEFAULT)
            return max(1, min(6, int(n)))
        except Exception:  # noqa: BLE001
            return HOME_COUPONS_PER_VIEW_DEFAULT

    def _render_coupons(self, uid):
        self._stop_coupon_rotate()
        self._uid = uid
        for child in self.coupon_section.winfo_children():
            child.destroy()
        try:
            self._public_coupons = coupon_service.list_public_coupons(uid)
            self._coupon_rules = [r for r in coupon_service.list_coupon_rules() if r.get("is_active")]
        except Exception:  # noqa: BLE001
            self._public_coupons, self._coupon_rules = [], []

        card = ThemeManager.make_card(self.coupon_section)
        card.pack(fill="x", pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        cp_ic = icon_utils.get_icon("coupon", 20, "#E63946", "#EF4444")
        ctk.CTkLabel(
            top, text="  คูปองส่วนลด & โปรโมชันประจำร้าน", image=cp_ic, compound="left",
            font=ThemeManager.get_font("h3"),
            text_color=ThemeManager.get_color_pair("danger"),
        ).pack(side="left")

        # T06: ปุ่มดูคูปองที่ผู้ซื้อมีทั้งหมด และปุ่มดูคูปองทั้งหมดที่มีในร้าน (แยกหมวดหมู่คูปอง)
        btn_group = ctk.CTkFrame(top, fg_color="transparent")
        btn_group.pack(side="right")

        ctk.CTkButton(
            btn_group,
            text="ดูคูปองที่มีทั้งหมดของร้าน",
            width=175,
            command=lambda: self._open_coupons_dialog(initial_tab="all"),
            **ThemeManager.button_style("danger", "sm"),
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_group,
            text="คูปองของฉันที่เก็บไว้",
            width=155,
            command=lambda: self._open_coupons_dialog(initial_tab="my"),
            **ThemeManager.button_style("info", "sm"),
        ).pack(side="right")

        if self._coupon_rules:
            r0 = self._coupon_rules[0]
            disc_txt = f"{r0['discount_value']:g}%" if r0["discount_type"] == "percent" else format_price(r0["discount_value"])
            gift_ic = icon_utils.get_icon("gift", 15, ON_PRIMARY, ON_PRIMARY)
            rule_bar = ctk.CTkFrame(card, fg_color="transparent")
            rule_bar.pack(fill="x", padx=16, pady=(0, 4))
            ctk.CTkLabel(
                rule_bar,
                text=f"  {r0['name']}: ซื้อครบ {format_price(r0['min_order_trigger'])} รับคูปองลด {disc_txt} สำหรับออเดอร์ถัดไปอัตโนมัติ!  ",
                image=gift_ic, compound="left",
                font=ThemeManager.get_font("small_bold"),
                fg_color=ThemeManager.get_color_pair("primary"),
                text_color=ON_PRIMARY, corner_radius=8, height=26, padx=8,
            ).pack(side="left")
            self.coupon_page_lbl = ctk.CTkLabel(
                rule_bar, text="", font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("text_muted"),
            )
            self.coupon_page_lbl.pack(side="right")
        else:
            self.coupon_page_lbl = ctk.CTkLabel(
                top, text="", font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("text_muted"),
            )
            self.coupon_page_lbl.pack(side="right", padx=8)

        self.coupon_cards_holder = ctk.CTkFrame(card, fg_color="transparent")
        self.coupon_cards_holder.pack(fill="x", padx=12, pady=(4, 12))

        self._coupon_page_idx = 0
        self._paint_coupon_subset()
        per_view = self._get_coupons_per_view()
        if len(self._public_coupons) > per_view:
            self._coupon_rotate_job = self.after(self._get_coupon_rotate_ms(), self._tick_coupon_subset)

    def _paint_coupon_subset(self):
        if not hasattr(self, "coupon_cards_holder") or not self.coupon_cards_holder.winfo_exists():
            return
        for child in self.coupon_cards_holder.winfo_children():
            child.destroy()

        coupons = self._public_coupons
        if not coupons:
            ctk.CTkLabel(
                self.coupon_cards_holder,
                text="ขณะนี้ยังไม่มีคูปองสาธารณะที่เปิดให้กดรับ — สามารถกดปุ่ม 'คูปองของฉันที่เก็บไว้' เพื่อตรวจสอบคูปองในบัญชีของคุณได้",
                font=ThemeManager.get_font("small"),
                text_color=ThemeManager.get_color_pair("text_muted"),
            ).pack(pady=8)
            self.coupon_page_lbl.configure(text="")
            return

        per_view = self._get_coupons_per_view()
        total_pages = max(1, (len(coupons) + per_view - 1) // per_view)
        self._coupon_page_idx = self._coupon_page_idx % total_pages
        start = self._coupon_page_idx * per_view
        subset = coupons[start:start + per_view]

        if total_pages > 1:
            self.coupon_page_lbl.configure(text=f"ชุดคูปอง {self._coupon_page_idx + 1}/{total_pages}")
        else:
            self.coupon_page_lbl.configure(text=f"ทั้งหมด {len(coupons)} คูปอง")

        # T06: ถ้ามีไม่ถึง 3 ใบ ก็จัดระยะห่างให้พอดี (แบ่งคอลัมน์ตามจำนวนใบที่มีจริงในชุดนั้น)
        cols = max(1, len(subset))
        for c in range(cols):
            self.coupon_cards_holder.grid_columnconfigure(c, weight=1, uniform="home_cp")

        for col_idx, cp in enumerate(subset):
            box = ctk.CTkFrame(
                self.coupon_cards_holder,
                fg_color=ThemeManager.get_color_pair("surface_alt"),
                corner_radius=12,
                border_width=1,
                border_color=ThemeManager.get_color_pair("primary"),
            )
            box.grid(row=0, column=col_idx, padx=8, pady=4, sticky="nsew")

            head_row = ctk.CTkFrame(box, fg_color="transparent")
            head_row.pack(fill="x", padx=12, pady=(8, 2))

            cat_badge_kind = (
                "info" if cp.get("coupon_category") == "free_shipping"
                else ("danger" if cp.get("coupon_category") == "percent" else "warning")
            )
            ThemeManager.make_badge(
                head_row, cp.get("category_label") or "คูปองส่วนลด", cat_badge_kind
            ).pack(side="left")

            ctk.CTkLabel(
                head_row,
                text=cp.get("status_text") or "ใช้ได้",
                font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("success" if cp.get("is_claimed") else "text_muted"),
            ).pack(side="right")

            ctk.CTkLabel(
                box,
                text=f"{cp['code']} · {cp.get('description') or ''}",
                font=ThemeManager.get_font("body_bold"),
                text_color=ThemeManager.get_color_pair("danger"),
                anchor="w",
            ).pack(fill="x", padx=12, pady=(2, 0))

            extra_parts = [f"ขั้นต่ำ {format_price(cp.get('min_order') or 0)}"]
            if cp.get("expires_at"):
                extra_parts.append(f"ถึง {format_date_thai(cp['expires_at'])}")
            if cp.get("claim_start_time") and cp.get("claim_end_time"):
                extra_parts.append(f"รับได้ {cp['claim_start_time']}-{cp['claim_end_time']} น.")
            if cp.get("daily_reset_12"):
                extra_parts.append("รีโค้ดทุก 12:00 น.")
            ctk.CTkLabel(
                box,
                text=" · ".join(extra_parts),
                font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("text_muted"),
                anchor="w",
            ).pack(fill="x", padx=12, pady=(0, 6))

            claimed = bool(cp.get("is_claimed"))
            used = bool(cp.get("is_used"))
            can_claim_now = bool(cp.get("can_claim_now", True))
            if claimed and not used:
                btn_text, btn_state, btn_kind = "✓ เก็บโค้ดแล้ว", "disabled", "success"
            elif used and can_claim_now:
                btn_text, btn_state, btn_kind = "กดรับโค้ดใหม่", "normal", "primary"
            elif not can_claim_now:
                btn_text, btn_state, btn_kind = "นอกเวลารับโค้ด", "disabled", "outline"
            else:
                btn_text, btn_state, btn_kind = "เก็บคูปอง", "normal", "primary"

            ctk.CTkButton(
                box,
                text=btn_text,
                state=btn_state,
                width=116,
                command=lambda code=cp["code"]: self._claim_coupon(code),
                **ThemeManager.button_style(btn_kind, "sm"),
            ).pack(anchor="e", padx=12, pady=(0, 10))

    def _tick_coupon_subset(self):
        self._coupon_rotate_job = None
        if not self.winfo_exists():
            return
        per_view = self._get_coupons_per_view()
        if not self._coupon_paused and self.winfo_ismapped() and len(self._public_coupons) > per_view:
            self._coupon_page_idx += 1
            self._paint_coupon_subset()
        if self.winfo_exists() and len(self._public_coupons) > per_view:
            self._coupon_rotate_job = self.after(self._get_coupon_rotate_ms(), self._tick_coupon_subset)

    def _claim_coupon(self, code: str, on_done=None):
        if not Session.is_authenticated():
            self.controller.show("login", info_message=f"กรุณาเข้าสู่ระบบเพื่อเก็บคูปอง {code}")
            return
        try:
            coupon_service.claim_coupon(code, common.user_id())
            self._render_coupons(common.user_id())
            if callable(on_done):
                on_done()
        except Exception as exc:  # noqa: BLE001
            self.error_label.configure(text=str(exc))

    def _open_coupons_dialog(self, initial_tab: str = "all"):
        """
        T06: หน้าต่างดูคูปองทั้งหมดของร้าน และคูปองของฉันที่เก็บไว้
        พร้อมแยกหมวดหมู่คูปอง:
        - ทั้งหมด
        - คูปองส่วนลดค่าส่ง
        - คูปองส่วนลดเป็น %
        - คูปองส่วนลดเป็น บาท
        - และอื่นๆ
        """
        uid = common.user_id()
        if initial_tab == "my" and not Session.is_authenticated():
            self.controller.show("login", info_message="กรุณาเข้าสู่ระบบเพื่อดูคูปองของฉันที่เก็บไว้")
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("ศูนย์รวมคูปองส่วนลด — Badminton Pro Shop")
        dlg.geometry("760x580")
        dlg.configure(fg_color=ThemeManager.get_color_pair("background"))
        dlg.transient(self.winfo_toplevel())

        hdr = ctk.CTkFrame(dlg, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="ศูนย์คูปองส่วนลด & คูปองของฉัน",
            font=ThemeManager.get_font("h2"),
            text_color=ThemeManager.get_color_pair("primary"),
        ).pack(anchor="w", padx=22, pady=(14, 2))
        ctk.CTkLabel(
            hdr, text="เลือกดูคูปองทั้งหมดของร้าน หรือคูปองที่คุณเก็บไว้ พร้อมกรองตามหมวดหมู่คูปอง",
            font=ThemeManager.get_font("small"), text_color="#E2E8F0",
        ).pack(anchor="w", padx=22, pady=(0, 12))

        mode_var = ctk.StringVar(value=initial_tab)
        cat_var = ctk.StringVar(value="all")

        # แถบสลับโหมด: คูปองทั้งหมดของร้าน vs คูปองของฉัน
        top_bar = ctk.CTkFrame(dlg, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(12, 4))

        mode_btns = {}
        for m_key, m_label in (
            ("all", "คูปองทั้งหมดที่ร้านมี"),
            ("my", "คูปองของฉัน (ที่เก็บไว้ทั้งหมด)"),
        ):
            b = ctk.CTkButton(
                top_bar, text=m_label, width=210,
                command=lambda mk=m_key: _switch_mode(mk),
                **ThemeManager.button_style("primary" if m_key == initial_tab else "outline", "md"),
            )
            b.pack(side="left", padx=(0, 8))
            mode_btns[m_key] = b

        # แถบหมวดหมู่คูปอง
        cat_bar = ctk.CTkFrame(dlg, fg_color="transparent")
        cat_bar.pack(fill="x", padx=20, pady=(4, 8))

        categories = [("all", "ทั้งหมด")] + coupon_service.get_coupon_categories()
        cat_btns = {}
        for c_key, c_label in categories:
            cb = ctk.CTkButton(
                cat_bar, text=c_label,
                command=lambda ck=c_key: _switch_cat(ck),
                **ThemeManager.button_style("danger" if c_key == "all" else "outline", "sm"),
            )
            cb.pack(side="left", padx=(0, 6), pady=2)
            cat_btns[c_key] = cb

        msg_lbl = ctk.CTkLabel(
            dlg, text="", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("danger"),
        )
        msg_lbl.pack(fill="x", padx=22)

        list_scroll = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        list_scroll.pack(fill="both", expand=True, padx=20, pady=(4, 14))

        def _refresh_list():
            for child in list_scroll.winfo_children():
                child.destroy()
            cur_mode = mode_var.get()
            cur_cat = cat_var.get()

            for mk, mb in mode_btns.items():
                mb.configure(**ThemeManager.button_style("primary" if mk == cur_mode else "outline", "md"))
            for ck, cb in cat_btns.items():
                cb.configure(**ThemeManager.button_style("danger" if ck == cur_cat else "outline", "sm"))

            if cur_mode == "my" and not Session.is_authenticated():
                ctk.CTkLabel(
                    list_scroll,
                    text="กรุณาเข้าสู่ระบบเพื่อดูคูปองที่คุณเก็บไว้",
                    font=ThemeManager.get_font("body_bold"),
                    text_color=ThemeManager.get_color_pair("text_muted"),
                ).pack(pady=40)
                return

            try:
                if cur_mode == "my":
                    items = coupon_service.list_my_coupons(uid, category=cur_cat)
                else:
                    items = coupon_service.list_all_shop_coupons(uid, category=cur_cat, include_expired=True)
            except Exception as exc:  # noqa: BLE001
                msg_lbl.configure(text=str(exc))
                return

            if not items:
                ctk.CTkLabel(
                    list_scroll,
                    text="ไม่พบคูปองในหมวดหมู่นี้",
                    font=ThemeManager.get_font("body_bold"),
                    text_color=ThemeManager.get_color_pair("text_muted"),
                ).pack(pady=40)
                return

            for cp in items:
                c_row = ThemeManager.make_card(list_scroll)
                c_row.pack(fill="x", pady=5)
                inner = ctk.CTkFrame(c_row, fg_color="transparent")
                inner.pack(fill="x", padx=16, pady=12)

                left_col = ctk.CTkFrame(inner, fg_color="transparent")
                left_col.pack(side="left", fill="x", expand=True)

                b_row = ctk.CTkFrame(left_col, fg_color="transparent")
                b_row.pack(fill="x")
                cat_kind = (
                    "info" if cp.get("coupon_category") == "free_shipping"
                    else ("danger" if cp.get("coupon_category") == "percent" else "warning")
                )
                ThemeManager.make_badge(b_row, cp.get("category_label") or "คูปอง", cat_kind).pack(side="left")

                status_txt = cp.get("status_text") or "ใช้ได้"
                st_kind = "success" if "ใช้ได้" in status_txt else ("danger" if "หมด" in status_txt else "muted")
                ThemeManager.make_badge(b_row, status_txt, st_kind).pack(side="left", padx=6)

                ctk.CTkLabel(
                    left_col,
                    text=f"{cp['code']}  —  {cp.get('description') or ''}",
                    font=ThemeManager.get_font("h3"),
                    text_color=ThemeManager.get_color_pair("danger"),
                    anchor="w",
                ).pack(fill="x", pady=(4, 2))

                meta = [f"ยอดสั่งซื้อขั้นต่ำ {format_price(cp.get('min_order') or 0)}"]
                if cp.get("expires_at"):
                    meta.append(f"หมดอายุ {format_date_thai(cp['expires_at'])}")
                if cp.get("remaining") is not None:
                    meta.append(f"คงเหลือ {cp['remaining']} สิทธิ์")
                ctk.CTkLabel(
                    left_col,
                    text=" · ".join(meta),
                    font=ThemeManager.get_font("small"),
                    text_color=ThemeManager.get_color_pair("text_muted"),
                    anchor="w",
                ).pack(fill="x")

                claimed = bool(cp.get("is_claimed"))
                used = bool(cp.get("is_used"))
                expired = bool(cp.get("is_expired"))
                can_claim_now = bool(cp.get("can_claim_now", True))
                full = cp.get("remaining") is not None and cp["remaining"] <= 0

                if expired:
                    b_txt, b_state, b_kind = "หมดอายุแล้ว", "disabled", "outline"
                elif full:
                    b_txt, b_state, b_kind = "สิทธิ์เต็ม", "disabled", "outline"
                elif claimed and not used:
                    b_txt, b_state, b_kind = "✓ เก็บแล้ว", "disabled", "success"
                elif used and can_claim_now and not cp.get("is_personal_reward"):
                    b_txt, b_state, b_kind = "กดรับโค้ดใหม่", "normal", "primary"
                elif used:
                    b_txt, b_state, b_kind = "ใช้แล้ว", "disabled", "outline"
                elif not can_claim_now:
                    b_txt, b_state, b_kind = "นอกเวลารับโค้ด", "disabled", "outline"
                else:
                    b_txt, b_state, b_kind = "เก็บคูปอง", "normal", "primary"

                def _do_claim(code=cp["code"]):
                    msg_lbl.configure(text="")
                    if not Session.is_authenticated():
                        dlg.destroy()
                        self.controller.show("login", info_message=f"กรุณาเข้าสู่ระบบเพื่อเก็บคูปอง {code}")
                        return
                    try:
                        coupon_service.claim_coupon(code, common.user_id())
                        self._render_coupons(common.user_id())
                        _refresh_list()
                    except Exception as exc:  # noqa: BLE001
                        msg_lbl.configure(text=str(exc))

                ctk.CTkButton(
                    inner, text=b_txt, state=b_state, width=130,
                    command=_do_claim,
                    **ThemeManager.button_style(b_kind, "md"),
                ).pack(side="right", padx=(12, 0))

        def _switch_mode(new_mode: str):
            mode_var.set(new_mode)
            _refresh_list()

        def _switch_cat(new_cat: str):
            cat_var.set(new_cat)
            _refresh_list()

        _refresh_list()
        dlg.after(100, dlg.lift)

    # ------------------------------------------------------------------ หมวดหมู่ (กรอบอวบชัด) & แบรนด์ (กรอบแดง + โลโก้ 1:1)
    def _render_categories_and_brands(self, categories, brands):
        self._cat_imgs = []
        chips = []
        for cat in categories:
            card = ctk.CTkFrame(
                self.category_grid,
                width=195,
                height=58,
                corner_radius=14,
                border_width=3,
                border_color=("#141619", "#FDE68A"),
                fg_color=ThemeManager.get_color_pair("primary"),
            )
            card.pack_propagate(False)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=10, pady=6)

            if cat.get("image_path"):
                c_img = load_ctk_image(cat.get("image_path"), (36, 36), cover=True, corner_radius=6)
            else:
                c_img = icon_utils.get_icon("racket", 22, ON_PRIMARY, ON_PRIMARY)
            self._cat_imgs.append(c_img)

            ic_lbl = ctk.CTkLabel(inner, text="", image=c_img, width=36, height=36)
            ic_lbl.pack(side="left", padx=(2, 8))
            txt_lbl = ctk.CTkLabel(
                inner, text=cat["name"], font=ThemeManager.get_font("body_bold"),
                text_color=ON_PRIMARY, anchor="w",
            )
            txt_lbl.pack(side="left", fill="x", expand=True)

            def _go_cat(_e=None, cid=cat["id"]):
                self.controller.show("category", category_id=cid)

            for w in (card, inner, ic_lbl, txt_lbl):
                w.bind("<Button-1>", _go_cat)
                try:
                    w.configure(cursor="hand2")
                except Exception:  # noqa: BLE001
                    pass
            chips.append(card)
        self.category_grid.set_items(chips)

        for child in self.brand_section.winfo_children():
            child.destroy()
        self._brand_imgs = []
        if brands:
            lbl_row = ctk.CTkFrame(self.brand_section, fg_color="transparent")
            lbl_row.pack(fill="x", pady=(4, 4))
            br_ic = icon_utils.get_icon("brand", 16, "#E63946", "#EF4444")
            ctk.CTkLabel(
                lbl_row, text="  แบรนด์ชั้นนำ (คลิกเลือกดูสินค้าตามแบรนด์):", image=br_ic, compound="left",
                font=ThemeManager.get_font("body_bold"),
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(side="left")

            brand_wrap = ctk.CTkFrame(self.brand_section, fg_color="transparent")
            brand_wrap.pack(fill="x")
            for br in brands[:10]:
                bcard = ctk.CTkFrame(
                    brand_wrap,
                    fg_color=ThemeManager.get_color_pair("surface"),
                    corner_radius=12,
                    border_width=2,
                    border_color=ThemeManager.get_color_pair("danger"),
                )
                bcard.pack(side="left", padx=(0, 10), pady=4)
                b_inner = ctk.CTkFrame(bcard, fg_color="transparent")
                b_inner.pack(padx=10, pady=6)

                logo_img = load_ctk_image(
                    br.get("logo_path"), (44, 44), cover=bool(br.get("logo_path")), corner_radius=6,
                    placeholder_text=str(br.get("name") or "Brand")[:6].upper(),
                )
                self._brand_imgs.append(logo_img)
                logo_lbl = ctk.CTkLabel(b_inner, text="", image=logo_img, width=44, height=44)
                logo_lbl.pack(side="left", padx=(0, 8))

                bname_lbl = ctk.CTkLabel(
                    b_inner, text=br["name"], font=ThemeManager.get_font("body_bold"),
                    text_color=ThemeManager.get_color_pair("text_main"),
                )
                bname_lbl.pack(side="left", padx=(0, 4))

                def _go_brand(_e=None, bid=br["id"]):
                    self.controller.show("category", brand_id=bid)

                for w in (bcard, b_inner, logo_lbl, bname_lbl):
                    w.bind("<Button-1>", _go_brand)
                    try:
                        w.configure(cursor="hand2")
                    except Exception:  # noqa: BLE001
                        pass

    def _reshuffle_products(self):
        uid = common.user_id()
        try:
            all_prods = product_service.search_products(
                sort="popular", page_size=48, user_id=uid,
            )["items"]
            random.shuffle(all_prods)
            recommended = all_prods[:RECOMMEND_LIMIT]
            self.recommend_grid.set_items(common.product_cards(self.recommend_grid, recommended, self.controller))
        except Exception as exc:  # noqa: BLE001
            self.error_label.configure(text=str(exc))

    # ------------------------------------------------------------------ ส่วนท้ายเกี่ยวกับร้าน & ที่ตั้งหน้าร้าน
    def _render_footer(self):
        for child in self.footer_box.winfo_children():
            child.destroy()
        try:
            info = contact_service.get_owner_contact_info()
            shop = settings_service.get_shop_info()
        except Exception:  # noqa: BLE001
            info, shop = {}, {}

        inner = ctk.CTkFrame(self.footer_box, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=16)

        top_foot = ctk.CTkFrame(inner, fg_color="transparent")
        top_foot.pack(fill="x")
        st_ic = icon_utils.get_icon("store", 20, "#FFB703", "#FFB703")
        ctk.CTkLabel(
            top_foot, text=f"  เกี่ยวกับร้าน {shop.get('shop_name') or info.get('shop_name') or 'Badminton Pro Shop'}",
            image=st_ic, compound="left",
            font=ThemeManager.get_font("h3"),
            text_color=ThemeManager.get_color_pair("primary"), anchor="w",
        ).pack(side="left")

        pin_btn_ic = icon_utils.get_icon("map_pin", 15, ON_PRIMARY, ON_PRIMARY)
        ctk.CTkButton(
            top_foot, text=" ดูที่ตั้งหน้าร้าน & แผนที่", image=pin_btn_ic, compound="left",
            command=lambda: open_store_location_dialog(self),
            **ThemeManager.button_style("primary", "sm"),
        ).pack(side="right")

        address_txt = shop.get("shop_address") or info.get("address") or "-"
        hours_txt = shop.get("shop_hours") or info.get("open_hours") or "-"
        ctk.CTkLabel(
            inner,
            text=f"ที่ตั้งหน้าร้าน: {address_txt}   |   เวลาทำการ: {hours_txt}",
            font=ThemeManager.get_font("body_bold"), text_color="#FDE68A", anchor="w", wraplength=920,
        ).pack(fill="x", pady=(4, 4))
        ctk.CTkLabel(
            inner,
            text=f"โทร: {info.get('phone') or '-'}   |   อีเมล: {info.get('email') or '-'}   |   LINE: {info.get('line_id') or '-'}",
            font=ThemeManager.get_font("small_bold"), text_color="#FFFFFF", anchor="w",
        ).pack(fill="x", pady=(0, 8))

        social_row = ctk.CTkFrame(inner, fg_color="transparent")
        social_row.pack(fill="x")
        socials = [
            ("Facebook: " + (info.get("facebook_name") or "Badminton Pro Shop"), info.get("facebook_url") or "", "info"),
            ("Instagram: " + (info.get("instagram_name") or "@badmintonpro.th"), info.get("instagram_url") or "", "danger"),
            ("TikTok: " + (info.get("tiktok_name") or "@badmintonpro.th"), info.get("tiktok_url") or "", "purple"),
        ]
        for label, url, kind in socials:
            if url and is_valid_https_url(url):
                ctk.CTkButton(
                    social_row, text=f"{label} ↗", command=lambda u=url: webbrowser.open(u),
                    **ThemeManager.button_style(kind, "sm"),
                ).pack(side="left", padx=(0, 8))

    # ------------------------------------------------------------------ โหลดข้อมูลทั้งหมด
    def on_show(self, **kwargs):
        self.error_label.configure(text="")
        self._stop_banner_job()
        self._stop_flash_scroll()
        self._stop_coupon_rotate()
        uid = common.user_id()

        try:
            shop_info = settings_service.get_shop_info()
            sname = (shop_info.get("shop_name") or "BADMINTON PRO").upper()
            self.banner_tag_lbl.configure(text=f"  {sname} OFFICIAL  ")
        except Exception:  # noqa: BLE001
            pass

        try:
            self._banners = banner_service.list_active_banners()
        except Exception:  # noqa: BLE001
            self._banners = []
        self._banner_idx = 0
        self._paint_banner()
        if len(self._banners) > 1:
            self._banner_job = self.after(BANNER_ROTATE_MS, self._auto_banner)

        self._render_coupons(uid)

        try:
            # T05: แสดงทุกอย่างที่ลดราคาในหน้า FLASH SALE
            flash_all = product_service.search_products(
                filters={"on_sale": True}, sort="popular", page_size=FLASH_LIMIT, user_id=uid,
            )["items"]
            categories = product_service.list_categories()
            brands = product_service.list_brands()
            all_prods = product_service.search_products(
                sort="popular", page_size=48, user_id=uid,
            )["items"]
            random.shuffle(all_prods)
            recommended = all_prods[:RECOMMEND_LIMIT]
            recent = product_service.list_recently_viewed(uid, limit=5) if uid else []
        except (ValueError, PermissionError) as exc:
            self.error_label.configure(text=str(exc))
            return

        self._render_flash_sale(flash_all)
        self._render_categories_and_brands(categories, brands)
        self.recommend_grid.set_items(common.product_cards(self.recommend_grid, recommended, self.controller))

        if recent:
            self.recent_box.pack(fill="x", before=self.footer_box)
            self.recent_grid.set_items(common.product_cards(self.recent_grid, recent, self.controller))
        else:
            self.recent_box.pack_forget()

        self._render_footer()

    def destroy(self):
        self._stop_banner_job()
        self._stop_fire_anim()
        self._stop_flash_scroll()
        self._stop_coupon_rotate()
        super().destroy()
