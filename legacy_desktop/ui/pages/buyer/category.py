"""
ui/pages/buyer/category.py
หน้ารายการสินค้า: กริด + ตัวกรอง (แบรนด์/หมวด/ราคา/สเปกไม้) + ค้นหา + เรียงลำดับ + แบ่งหน้า

on_show(category_id=None, brand_id=None, search=None, on_sale=None)
"""

import customtkinter as ctk

from services import product_service
from ui.components.product_filter import ProductFilter
from ui.components.product_grid import ProductGrid
from ui.components.search_bar import SearchBar
from ui.pages.buyer import common
from ui.theme import ThemeManager

PAGE_SIZE = 12

_SORTS = {
    "ใหม่ล่าสุด": "newest",
    "ยอดนิยม": "popular",
    "ราคา: ต่ำ → สูง": "price_asc",
    "ราคา: สูง → ต่ำ": "price_desc",
    "ชื่อ A–Z": "name",
}


class CategoryPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._filters = {}
        self._query = ""
        self._sort = "newest"
        self._category_names = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- ซ้าย: ตัวกรอง ---
        self.filter_panel = ProductFilter(self, on_apply=self._apply_filters, show_category=True)
        self.filter_panel.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        # --- ขวา: หัวข้อ + ค้นหา + เรียง + กริด ---
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(main, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(
            top, text="สินค้าทั้งหมด", font=ThemeManager.get_font("h2"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_main"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.sort_var = ctk.StringVar(value=next(iter(_SORTS)))
        ctk.CTkOptionMenu(
            top, values=list(_SORTS), variable=self.sort_var, command=self._on_sort, width=150, height=34,
            font=ThemeManager.get_font("small"), dropdown_font=ThemeManager.get_font("small"),
            fg_color=ThemeManager.get_color_pair("surface"),
            button_color=ThemeManager.get_color_pair("border"),
            button_hover_color=ThemeManager.get_color_pair("primary"),
            text_color=ThemeManager.get_color_pair("text_main"),
            dropdown_fg_color=ThemeManager.get_color_pair("surface"),
            dropdown_text_color=ThemeManager.get_color_pair("text_main"),
        ).grid(row=0, column=1, sticky="e")

        bar_row = ctk.CTkFrame(main, fg_color="transparent")
        bar_row.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        self.search_bar = SearchBar(bar_row, command=self._on_search, width=420)
        self.search_bar.pack(side="left")
        self.error_label = common.error_label(bar_row)
        self.error_label.pack(side="left", padx=12)

        self.product_grid = ProductGrid(main, self.controller, on_page_change=self._load)
        self.product_grid.grid(row=2, column=0, sticky="nsew")

    # ------------------------------------------------------------------ โหลดข้อมูล
    def on_show(self, category_id=None, brand_id=None, search=None, on_sale=None, **kwargs):
        """รับตัวกรองเริ่มต้นจากหน้าอื่น (หมวดจากหน้าแรก, คำค้นจาก navbar)"""
        self.filter_panel.reload_options()
        try:
            self._category_names = {c["id"]: c["name"] for c in product_service.list_categories()}
        except (ValueError, PermissionError):
            self._category_names = {}

        initial = {}
        if category_id:
            initial["category_id"] = category_id
        if brand_id:
            initial["brand_id"] = brand_id
        if on_sale:
            initial["on_sale"] = True
        self.filter_panel.set_filters(initial)
        self._filters = dict(initial)

        self._query = (search or "").strip()
        self.search_bar.set(self._query)
        self._sort = "newest"
        self.sort_var.set(next(iter(_SORTS)))
        self._sync_spec_visibility()
        self._load(1)

    def _load(self, page=1):
        self.error_label.configure(text="")
        try:
            result = product_service.search_products(
                query=self._query or None, filters=self._filters, sort=self._sort,
                page=page, page_size=PAGE_SIZE, user_id=common.user_id(),
            )
        except (ValueError, PermissionError) as exc:
            self.error_label.configure(text=str(exc))
            return
        self.product_grid.set_result(result)
        self._update_title(result["total"])

    def _update_title(self, total):
        cat_id = self._filters.get("category_id")
        name = self._category_names.get(cat_id) if cat_id else None
        if self._query:
            text = f"ผลการค้นหา \"{self._query}\""
        elif name:
            text = name
        elif self._filters.get("on_sale"):
            text = "สินค้าลดราคา"
        else:
            text = "สินค้าทั้งหมด"
        self.title_label.configure(text=f"{text}  ({total:,})")

    def _sync_spec_visibility(self):
        """ตัวกรองสเปกไม้แสดงเฉพาะเมื่อดูทุกหมวด หรือหมวดที่เป็นไม้แบด"""
        cat_id = self._filters.get("category_id")
        name = self._category_names.get(cat_id, "") if cat_id else ""
        self.filter_panel.set_spec_visible(not cat_id or "ไม้" in name)

    # ------------------------------------------------------------------ ปุ่ม/ช่อง
    def _apply_filters(self, filters):
        self._filters = dict(filters)
        self._sync_spec_visibility()
        self._load(1)

    def _on_search(self, text):
        self._query = (text or "").strip()
        self._load(1)

    def _on_sort(self, label):
        self._sort = _SORTS.get(label, "newest")
        self._load(1)
