"""
ui/pages/buyer/wishlist.py
หน้ารายการโปรด (Wishlist): กริดสินค้าที่กดหัวใจไว้ — กดหัวใจซ้ำเพื่อเอาออก (การ์ดหายไปทันที)
"""

import customtkinter as ctk

from services import account_service
from ui.components.product_grid import ProductGrid
from ui.pages.buyer import common
from ui.theme import ThemeManager


class WishlistPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 4))
        common.page_title(head, "♥ รายการโปรด", "สินค้าที่คุณกดหัวใจเก็บไว้").pack(side="left")
        self.error_label = common.error_label(head)
        self.error_label.pack(side="left", padx=16)

        self.product_grid = ProductGrid(
            self, controller, on_wishlist=self._toggle,
            empty_text="ยังไม่มีสินค้าในรายการโปรด\nกดหัวใจที่สินค้าเพื่อเก็บไว้ดูภายหลัง",
        )
        self.product_grid.pack(fill="both", expand=True, padx=16, pady=(4, 12))

    def on_show(self):
        self.error_label.configure(text="")
        try:
            items = account_service.list_wishlist(common.user_id())
        except (ValueError, PermissionError) as exc:
            self.error_label.configure(text=str(exc))
            self.product_grid.clear()
            return
        self.product_grid.set_products(items)

    def _toggle(self, product_id):
        """กดหัวใจในหน้านี้ = เอาออกจากรายการโปรด แล้วลบการ์ดทิ้ง"""
        state = common.toggle_wishlist(self, product_id)
        if state is False:
            self.after(150, lambda: self.product_grid.remove_product(product_id))
        return state
