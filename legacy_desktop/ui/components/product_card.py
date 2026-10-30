"""
ui/components/product_card.py
การ์ดสินค้า (T07 + สไตล์สปอร์ต เหลือง-แดง-ขาว/ดำ):
- การ์ดสินค้าสัดส่วน 3:4 (กว้าง 216 x สูง 288) ไม่ลีบ
- ส่วนบนเป็นรูปสินค้าสัดส่วน 1:1 (จัตุรัส) ภายในการ์ด มุมมน ไม่เพี้ยนสัดส่วน
- ส่วนที่เหลือด้านล่างเป็นรายละเอียดตามเดิม (แบรนด์, ชื่อสินค้า, ราคา/ราคาเดิมขีดฆ่า, ป้าย Flash Sale/เวลานับถอยหลัง, รีวิว)
- คงป้ายส่วนลด % (มุมซ้ายบน) และปุ่มหัวใจวงกลม (มุมขวาบน) ตำแหน่งเดิม
"""

import time

import customtkinter as ctk

from ui.components.rating import RatingStars
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.formatters import format_price
from utils.image_utils import load_product_card_image

# การ์ดสินค้าสัดส่วน 3:4 (216 : 288 = 3 : 4) ตาม T07
CARD_WIDTH = 216
CARD_HEIGHT = 288


def _get(product, key, default=None):
    try:
        value = product[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if value is None else value


def format_countdown(seconds: int) -> str:
    seconds = max(0, int(seconds))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    clock = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{days} วัน {clock}" if days else clock


def discount_percent(price, effective_price) -> int:
    try:
        price, effective_price = float(price), float(effective_price)
    except (TypeError, ValueError):
        return 0
    if price <= 0 or effective_price >= price:
        return 0
    return int(round((1 - effective_price / price) * 100))


class ProductCard(ctk.CTkFrame):
    def __init__(self, parent, product, on_open=None, on_wishlist=None, width=CARD_WIDTH):
        card_h = int(round(width * 4 / 3))
        super().__init__(
            parent, width=width, height=card_h, corner_radius=12, border_width=1,
            fg_color=ThemeManager.get_color_pair("surface"),
            border_color=ThemeManager.get_color_pair("border"),
        )
        self.product = product
        self.product_id = _get(product, "id")
        self._on_open = on_open
        self._on_wishlist = on_wishlist
        self._width = width
        self._height = card_h
        self._tick_id = None
        self._deadline = None
        self._image = None
        self._clickables = []
        self._in_wishlist = bool(_get(product, "in_wishlist", False))

        self._build()
        self._start_countdown()

    def _build(self):
        p = self.product
        pad = 10
        # T07: ส่วนบนเป็นรูปสินค้าอัตราส่วน 1:1 (จัตุรัส) ภายในการ์ด 3:4
        self._img_w = self._width - pad * 2
        self._img_h = self._img_w
        self._in_stock = bool(_get(p, "in_stock", True))
        price = _get(p, "price", 0)
        effective = _get(p, "effective_price", price)
        is_on_sale = bool(_get(p, "is_on_sale", False))
        self._pct = discount_percent(price, effective) if is_on_sale else 0
        self._show_heart = (self._on_wishlist is not None and self.product_id is not None)

        # --- รูปภาพสินค้า 1:1 มุมมน + ป้ายส่วนลด (ซ้ายบน) + ปุ่มหัวใจวงกลม (ขวาบน) ---
        holder = ctk.CTkFrame(
            self, width=self._img_w, height=self._img_h,
            fg_color="transparent", corner_radius=10,
        )
        holder.pack(padx=pad, pady=(pad, 4))
        holder.pack_propagate(False)

        self.img_label = ctk.CTkLabel(holder, text="", corner_radius=10)
        self.img_label.pack(fill="both", expand=True)
        self._render_card_image()

        # ดักคลิกบนรูปภาพ: ถ้าคลิกบริเวณปุ่มหัวใจมุมบนขวา -> สลับ Wishlist, คลิกส่วนอื่น -> เปิดหน้าสินค้า
        self.img_label.bind("<Button-1>", self._handle_image_click)
        self.img_label.bind("<Enter>", self._hover_on, add="+")
        self.img_label.bind("<Leave>", self._hover_off, add="+")
        try:
            self.img_label.configure(cursor="hand2")
        except Exception:  # noqa: BLE001
            pass

        # --- ส่วนล่าง: รายละเอียดสินค้าตามเดิม ---
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=pad, pady=(0, pad))

        brand = str(_get(p, "brand_name", "") or "").strip()
        if brand:
            brand_lbl = ctk.CTkLabel(
                body, text=brand.upper(), font=ThemeManager.get_font("tiny"), anchor="w",
                text_color=ThemeManager.get_color_pair("info"),
            )
            brand_lbl.pack(fill="x", pady=(0, 1))
            self._clickable(brand_lbl)

        name = str(_get(p, "name", ""))
        if len(name) > 42:
            name = name[:40].rstrip() + "…"
        name_lbl = ctk.CTkLabel(
            body, text=name, font=ThemeManager.get_font("body_bold"), anchor="nw", justify="left",
            height=38, wraplength=self._width - 24,
            text_color=ThemeManager.get_color_pair("text_main" if self._in_stock else "text_muted"),
        )
        name_lbl.pack(fill="x")
        self._clickable(name_lbl)

        # แถวราคา (เด่นชัด สีแดงเมื่อลดราคา)
        price_row = ctk.CTkFrame(body, fg_color="transparent")
        price_row.pack(fill="x", pady=(2, 1))
        self._clickable(price_row)
        price_lbl = ctk.CTkLabel(
            price_row, text=format_price(effective), font=ThemeManager.get_font("price"),
            text_color=ThemeManager.get_color_pair("danger" if is_on_sale else "text_main"),
        )
        price_lbl.pack(side="left")
        self._clickable(price_lbl)

        if is_on_sale and self._pct:
            old_lbl = ctk.CTkLabel(
                price_row, text=format_price(price),
                font=ThemeManager.get_font_obj("small", overstrike=True),
                text_color=ThemeManager.get_color_pair("text_muted"),
            )
            old_lbl.pack(side="left", padx=(6, 0), pady=(2, 0))
            self._clickable(old_lbl)

        # Flash Sale + นับถอยหลัง (ใช้ไอคอนเวกเตอร์สายฟ้า)
        self.countdown_label = None
        seconds_left = _get(p, "sale_seconds_left")
        if is_on_sale and seconds_left is not None and _get(p, "sale_ends_at"):
            self._deadline = time.time() + max(0, int(seconds_left))
            self._flash_ic = icon_utils.get_icon("flash", 13, ON_PRIMARY, ON_PRIMARY)
            self.countdown_label = ctk.CTkLabel(
                body, text="", image=self._flash_ic, compound="left",
                font=ThemeManager.get_font("tiny"), anchor="w",
                fg_color=ThemeManager.get_color_pair("primary"),
                text_color=ON_PRIMARY, corner_radius=6, height=20, padx=6,
            )
            self.countdown_label.pack(fill="x", pady=(1, 1))
            self._clickable(self.countdown_label)

        # ดาวรีวิว / สถานะสินค้า
        review_count = int(_get(p, "review_count", 0) or 0)
        if review_count:
            stars = RatingStars(body, value=_get(p, "avg_rating", 0), count=review_count, size=11)
            stars.pack(anchor="w", pady=(1, 0))
            self._clickable(stars, *stars.winfo_children())
        else:
            self._star_ic = icon_utils.get_icon("star", 12, "#FFB703", "#FFB703")
            no_rev = ctk.CTkLabel(
                body, text=" สินค้ามาใหม่", image=self._star_ic, compound="left",
                font=ThemeManager.get_font("tiny"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_muted"),
            )
            no_rev.pack(fill="x", pady=(1, 0))
            self._clickable(no_rev)

        self._clickable(body)
        self._clickable(self)

    def _render_card_image(self):
        self._image = load_product_card_image(
            _get(self.product, "image_path"),
            (self._img_w, self._img_h),
            corner_radius=10,
            discount_pct=self._pct,
            in_stock=self._in_stock,
            show_heart=self._show_heart,
            in_wishlist=self._in_wishlist,
        )
        self.img_label.configure(image=self._image)

    def _handle_image_click(self, event):
        if self._show_heart and event is not None:
            # พิกัดปุ่มหัวใจวงกลมมุมบนขวา (ขนาด 32x32 ระยะขอบ 8px)
            if event.x >= (self._img_w - 46) and event.y <= 46:
                self._toggle_wishlist()
                return "break"
        self._handle_click(event)

    def _clickable(self, *widgets):
        for w in widgets:
            w.bind("<Button-1>", self._handle_click, add="+")
            w.bind("<Enter>", self._hover_on, add="+")
            w.bind("<Leave>", self._hover_off, add="+")
            try:
                w.configure(cursor="hand2")
            except Exception:  # noqa: BLE001
                pass
            self._clickables.append(w)
        return widgets[0]

    def _handle_click(self, _event=None):
        if self._on_open and self.product_id is not None:
            self._on_open(self.product_id)

    def _hover_on(self, _event=None):
        self.configure(border_color=ThemeManager.get_color_pair("primary"), border_width=2)

    def _hover_off(self, _event=None):
        try:
            x, y = self.winfo_pointerxy()
            under = self.winfo_containing(x, y)
            if under is not None and str(under).startswith(str(self)):
                return
        except Exception:  # noqa: BLE001
            pass
        self.configure(border_color=ThemeManager.get_color_pair("border"), border_width=1)

    def _paint_heart(self):
        self._render_card_image()

    def _toggle_wishlist(self):
        if self._on_wishlist is None or self.product_id is None:
            return
        try:
            new_state = self._on_wishlist(self.product_id)
        except Exception:  # noqa: BLE001
            return
        if new_state is not None:
            self._in_wishlist = bool(new_state)
            self._paint_heart()

    def set_wishlist(self, value: bool):
        self._in_wishlist = bool(value)
        self._paint_heart()

    def _start_countdown(self):
        if self.countdown_label is not None:
            self._tick()

    def _tick(self):
        try:
            if not self.winfo_exists():
                return
            left = int(self._deadline - time.time())
            if left <= 0:
                self.countdown_label.configure(text=" หมดเวลาโปรโมชันแล้ว ")
                self._tick_id = None
                return
            self.countdown_label.configure(text=f" เหลือ {format_countdown(left)} ")
            self._tick_id = self.after(1000, self._tick)
        except Exception:  # noqa: BLE001
            self._tick_id = None

    def destroy(self):
        if self._tick_id is not None:
            try:
                self.after_cancel(self._tick_id)
            except Exception:  # noqa: BLE001
                pass
            self._tick_id = None
        super().destroy()

IMAGE_SIZE = (CARD_WIDTH - 20, CARD_WIDTH - 20)
