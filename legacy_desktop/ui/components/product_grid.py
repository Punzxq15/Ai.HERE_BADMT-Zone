"""
ui/components/product_grid.py
กริดการ์ดสินค้าแบบตอบสนองความกว้างหน้าต่าง (จำนวนคอลัมน์ปรับเองตามขนาด) + ตัวแบ่งหน้า

ใช้งาน:
    grid = ProductGrid(parent, controller, on_page_change=self.load_page)
    grid.pack(fill="both", expand=True)
    result = product_service.search_products(..., page=1)
    grid.set_result(result)              # result = {items, total, page, page_size, pages}
    grid.set_products(items)             # รายการล้วน ไม่มีแบ่งหน้า (เช่น wishlist)

    - คลิกการ์ด → controller.show("product_detail", product_id=...)  (หรือส่ง on_open(product_id) เอง)
    - หัวใจ wishlist ทำงานเองผ่าน account_service.toggle_wishlist (ส่ง on_wishlist=callable เพื่อทับ, None = ซ่อนหัวใจ)
    - on_page_change(page:int) ถูกเรียกเมื่อผู้ใช้กดเปลี่ยนหน้า → ผู้ใช้โหลดข้อมูลหน้านั้นแล้วเรียก set_result ใหม่

ทดสอบเดี่ยว:  python -m ui.components.product_grid   (รันจาก root โปรเจกต์ — ใช้ข้อมูลจำลอง ไม่แตะ DB)
"""

import customtkinter as ctk

from ui.components import dialogs
from ui.components.product_card import CARD_WIDTH, ProductCard
from ui.theme import ThemeManager

_AUTO = "auto"


def page_window(page: int, pages: int):
    """รายการปุ่มเลขหน้าที่จะแสดง: ตัวเลข หรือ None (= ...)  เช่น [1, None, 4, 5, 6, None, 20]"""
    if pages <= 7:
        return list(range(1, pages + 1))
    start = max(2, page - 1)
    end = min(pages - 1, page + 1)
    out = [1]
    if start > 2:
        out.append(None)
    out.extend(range(start, end + 1))
    if end < pages - 1:
        out.append(None)
    out.append(pages)
    return out


class ProductGrid(ctk.CTkFrame):
    def __init__(self, parent, controller=None, card_width=CARD_WIDTH, gap=12, on_page_change=None,
                 on_open=None, on_wishlist=_AUTO, empty_text="ไม่พบสินค้าที่ตรงกับเงื่อนไข"):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self._card_width = card_width
        self._gap = gap
        self._on_page_change = on_page_change
        self._on_open = on_open
        self._on_wishlist = on_wishlist
        self._empty_text = empty_text

        self._cards = []
        self._empty_label = None
        self._cols = 0
        self._resize_job = None
        self._page = 1
        self._pages = 1
        self._total = 0

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, sticky="nsew")

        self.pager = ctk.CTkFrame(self, fg_color="transparent", height=44)
        self.pager.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self.bind("<Configure>", self._on_configure)

    # ------------------------------------------------------------------ ข้อมูลเข้า
    def set_result(self, result: dict):
        """รับผลจาก product_service.search_products (items, total, page, pages)"""
        self._page = int(result.get("page", 1) or 1)
        self._pages = int(result.get("pages", 1) or 1)
        self._total = int(result.get("total", len(result.get("items", []))) or 0)
        self._show_items(result.get("items", []))
        self._build_pager()

    def set_products(self, items, total=None):
        """รายการสินค้าล้วน (ไม่แบ่งหน้า)"""
        self._page, self._pages = 1, 1
        self._total = len(items) if total is None else total
        self._show_items(items)
        self._build_pager()

    def clear(self):
        self._show_items([])
        self._total, self._page, self._pages = 0, 1, 1
        self._build_pager()

    def remove_product(self, product_id):
        """เอาการ์ดออก (เช่น ลบออกจาก wishlist) แล้วจัดเรียงใหม่"""
        keep = []
        for card in self._cards:
            if card.product_id == product_id:
                card.destroy()
            else:
                keep.append(card)
        self._cards = keep
        self._total = max(0, self._total - 1)
        self._layout(force=True)
        if not self._cards:
            self._show_empty()
        self._build_pager()

    # ------------------------------------------------------------------ แสดงการ์ด
    def _show_items(self, items):
        for card in self._cards:
            card.destroy()
        self._cards = []
        if self._empty_label is not None:
            self._empty_label.destroy()
            self._empty_label = None

        if not items:
            self._show_empty()
            return

        wishlist_cb = self._wishlist_callback()
        for product in items:
            card = ProductCard(self.scroll, product, on_open=self._open, on_wishlist=wishlist_cb,
                               width=self._card_width)
            self._cards.append(card)
        self._layout(force=True)
        try:
            self.scroll._parent_canvas.yview_moveto(0)  # กลับไปบนสุดทุกครั้งที่เปลี่ยนชุดสินค้า/หน้า
        except Exception:  # noqa: BLE001 - โครงสร้างภายในต่างเวอร์ชัน
            pass

    def _show_empty(self):
        self._empty_label = ctk.CTkLabel(
            self.scroll, text=f"🔍\n{self._empty_text}", font=ThemeManager.get_font("body"),
            text_color=ThemeManager.get_color_pair("text_muted"), justify="center",
        )
        self._empty_label.pack(pady=60)

    def _wishlist_callback(self):
        if self._on_wishlist == _AUTO:
            return self._default_wishlist
        return self._on_wishlist  # callable หรือ None (ซ่อนหัวใจ)

    def _open(self, product_id):
        if self._on_open:
            self._on_open(product_id)
        elif self.controller is not None:
            self.controller.show("product_detail", product_id=product_id)

    def _default_wishlist(self, product_id):
        """สลับ wishlist ของผู้ใช้ปัจจุบัน — คืนสถานะใหม่ หรือ None ถ้าทำไม่ได้"""
        from core.session import Session
        from services import account_service
        try:
            result = account_service.toggle_wishlist(Session.get_user_id(), product_id)
        except (ValueError, PermissionError) as exc:
            dialogs.show_message(self, "ทำรายการไม่ได้", str(exc), kind="error")
            return None
        return bool(result["in_wishlist"])

    # ------------------------------------------------------------------ จัดเรียงตามความกว้าง
    def _calc_cols(self) -> int:
        avail = self.scroll.winfo_width()
        if avail <= 1:
            avail = self.winfo_width()
        avail -= 28  # แถบเลื่อน + ขอบ
        return max(1, avail // (self._card_width + self._gap))

    def _on_configure(self, _event=None):
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._layout)

    def _layout(self, force=False):
        self._resize_job = None
        if not self._cards:
            return
        cols = self._calc_cols()
        if cols == self._cols and not force:
            return
        for c in range(max(cols, self._cols)):
            self.scroll.grid_columnconfigure(c, weight=1 if c < cols else 0)
        for index, card in enumerate(self._cards):
            card.grid(row=index // cols, column=index % cols, padx=self._gap // 2, pady=self._gap // 2,
                      sticky="n")
        self._cols = cols

    # ------------------------------------------------------------------ ตัวแบ่งหน้า
    def _build_pager(self):
        for child in self.pager.winfo_children():
            child.destroy()
        if self._total <= 0:
            return

        ctk.CTkLabel(
            self.pager, text=f"ทั้งหมด {self._total:,} รายการ", font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(side="left", padx=(4, 0))
        if self._pages <= 1:
            return

        def nav(text, target, enabled):
            btn = ctk.CTkButton(
                self.pager, text=text, width=34, command=lambda: self._go(target),
                state="normal" if enabled else "disabled", **ThemeManager.button_style("outline", "sm"))
            btn.pack(side="right", padx=2)

        nav("▶", self._page + 1, self._page < self._pages)
        for number in reversed(page_window(self._page, self._pages)):
            if number is None:
                ctk.CTkLabel(self.pager, text="…", width=20,
                             text_color=ThemeManager.get_color_pair("text_muted")).pack(side="right")
                continue
            kind = "primary" if number == self._page else "outline"
            ctk.CTkButton(
                self.pager, text=str(number), width=34, command=lambda n=number: self._go(n),
                **ThemeManager.button_style(kind, "sm")).pack(side="right", padx=2)
        nav("◀", self._page - 1, self._page > 1)

    def _go(self, page):
        if page < 1 or page > self._pages or page == self._page:
            return
        if self._on_page_change:
            self._on_page_change(page)


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("980x640")

    def fake(n):
        return [dict(id=i, name=f"สินค้าตัวอย่าง {i}", brand_name="Yonex", price=1000 + i * 50,
                     effective_price=1000 + i * 50, is_on_sale=False, in_stock=i % 5 != 0,
                     review_count=i % 3, avg_rating=4.0) for i in range(n)]

    def make(page):
        return dict(items=fake(12), total=95, page=page, page_size=12, pages=8)

    grid = ProductGrid(root, on_open=lambda pid: print("เปิด", pid), on_wishlist=lambda pid: True,
                       on_page_change=lambda p: grid.set_result(make(p)))
    grid.pack(fill="both", expand=True, padx=12, pady=12)
    grid.set_result(make(1))
    root.mainloop()
