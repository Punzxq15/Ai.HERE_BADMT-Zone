"""
ui/components/product_filter.py
แผงตัวกรองสินค้า: แบรนด์ (+หมวด), ช่วงราคา, สเปกไม้ (น้ำหนัก/จุดสมดุล/ความแข็งก้าน/ระดับ),
เฉพาะลดราคา, เฉพาะที่มีสินค้า

ใช้งาน:
    f = ProductFilter(parent, on_apply=lambda filters: self.search(filters), show_category=False)
    f.pack(side="left", fill="y")
    f.get_filters()        # dict พร้อมส่งเป็น filters ของ product_service.search_products
                           # (คีย์: brand_id, category_id, weight_class, balance, flex, level,
                           #  min_price, max_price, on_sale, in_stock — ไม่เลือก = ไม่มีคีย์)
                           # ถ้าช่วงราคาไม่ถูกต้องจะโยน ValueError(ข้อความไทย)
    f.set_filters({...}); f.reset(); f.set_spec_visible(False)   # ซ่อนสเปกเมื่อไม่ใช่หมวดไม้แบด
    f.reload_options()     # โหลดตัวเลือกแบรนด์/หมวด/สเปกจาก DB ใหม่ (เรียกใน on_show ได้)

หมายเหตุ: ตัวเลือกแบรนด์/หมวดมาจาก product_service.list_filter_values() → ต้องเป็นรายการที่มี id และ name
(dict หรือ sqlite3.Row); ถ้าโหลดไม่ได้จะแสดงเมนูว่าง ไม่ทำให้หน้าพัง

ทดสอบเดี่ยว:  python -m ui.components.product_filter   (รันจาก root โปรเจกต์ — ใช้ข้อมูลจำลอง ไม่แตะ DB)
"""

import customtkinter as ctk

from ui.theme import ThemeManager

ALL = "ทั้งหมด"

_SPEC_LABELS = (
    ("weight_class", "น้ำหนักไม้ (U)"),
    ("balance", "จุดสมดุล"),
    ("flex", "ความแข็งก้าน"),
    ("level", "ระดับผู้เล่น"),
)


def _id_name(item):
    """แปลงรายการจาก list_filter_values เป็น (id, name) — รองรับ dict / sqlite3.Row"""
    try:
        return item["id"], str(item["name"])
    except (KeyError, IndexError, TypeError):
        return None, None


class ProductFilter(ctk.CTkScrollableFrame):
    def __init__(self, parent, on_apply=None, show_category=False, show_spec=True, width=230):
        super().__init__(
            parent, width=width, corner_radius=12, border_width=1,
            fg_color=ThemeManager.get_color_pair("surface"),
            border_color=ThemeManager.get_color_pair("border"),
        )
        self._on_apply = on_apply
        self._show_category = show_category
        self._spec_visible = show_spec
        self._brands = {}       # ชื่อ -> id
        self._categories = {}   # ชื่อ -> id
        self._menus = {}        # key -> (CTkOptionMenu, StringVar)

        self._heading("ตัวกรอง", big=True).pack(fill="x", padx=14, pady=(14, 4))

        # --- แบรนด์ / หมวด ---
        self._section = ctk.CTkFrame(self, fg_color="transparent")
        self._section.pack(fill="x", padx=14)
        self._add_menu(self._section, "brand_id", "แบรนด์")
        if show_category:
            self._add_menu(self._section, "category_id", "หมวดหมู่")

        # --- ราคา ---
        price_box = ctk.CTkFrame(self, fg_color="transparent")
        price_box.pack(fill="x", padx=14, pady=(12, 0))
        self._heading("ช่วงราคา (บาท)", price_box).pack(fill="x")
        row = ctk.CTkFrame(price_box, fg_color="transparent")
        row.pack(fill="x", pady=(4, 0))
        self.min_entry = ctk.CTkEntry(row, placeholder_text="ต่ำสุด", width=88, **ThemeManager.entry_style(34))
        self.min_entry.pack(side="left")
        ctk.CTkLabel(row, text="–", width=20, text_color=ThemeManager.get_color_pair("text_muted")).pack(side="left")
        self.max_entry = ctk.CTkEntry(row, placeholder_text="สูงสุด", width=88, **ThemeManager.entry_style(34))
        self.max_entry.pack(side="left")
        for entry in (self.min_entry, self.max_entry):
            entry.bind("<Return>", lambda _e: self._apply())
        self._price_box = price_box

        # --- สเปกไม้ ---
        self._spec_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._heading("สเปกไม้แบด", self._spec_frame).pack(fill="x", pady=(0, 2))
        for key, label in _SPEC_LABELS:
            self._add_menu(self._spec_frame, key, label)

        # --- ตัวเลือกอื่น ---
        self._flags = ctk.CTkFrame(self, fg_color="transparent")
        self._flags.pack(fill="x", padx=14, pady=(12, 0))
        self.on_sale_var = ctk.BooleanVar(value=False)
        self.in_stock_var = ctk.BooleanVar(value=False)
        for text, var in (("เฉพาะสินค้าลดราคา", self.on_sale_var), ("เฉพาะที่มีสินค้า", self.in_stock_var)):
            ctk.CTkCheckBox(
                self._flags, text=text, variable=var, font=ThemeManager.get_font("small"),
                fg_color=ThemeManager.get_color_pair("primary"),
                hover_color=ThemeManager.get_color_pair("primary_hover"),
                checkmark_color="#1A1A1A", text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(anchor="w", pady=3)

        self.error_label = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("small"), anchor="w", justify="left",
            text_color=ThemeManager.get_color_pair("danger"), wraplength=width - 40,
        )
        self.error_label.pack(fill="x", padx=14, pady=(8, 0))

        ctk.CTkButton(self, text="ใช้ตัวกรอง", command=self._apply, **ThemeManager.button_style("primary")
                      ).pack(fill="x", padx=14, pady=(8, 6))
        ctk.CTkButton(self, text="ล้างตัวกรอง", command=self._reset_and_apply,
                      **ThemeManager.button_style("outline")).pack(fill="x", padx=14, pady=(0, 14))

        self.set_spec_visible(show_spec)
        self.reload_options()

    # ------------------------------------------------------------------ สร้างส่วนประกอบ
    def _heading(self, text, parent=None, big=False):
        return ctk.CTkLabel(
            parent if parent is not None else self, text=text,
            font=ThemeManager.get_font("h3" if big else "body_bold"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_main"),
        )

    def _add_menu(self, parent, key, label):
        ctk.CTkLabel(parent, text=label, font=ThemeManager.get_font("small"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_muted")).pack(fill="x", pady=(8, 0))
        var = ctk.StringVar(value=ALL)
        menu = ctk.CTkOptionMenu(
            parent, values=[ALL], variable=var, height=34, font=ThemeManager.get_font("small"),
            dropdown_font=ThemeManager.get_font("small"),
            fg_color=ThemeManager.get_color_pair("surface_alt"),
            button_color=ThemeManager.get_color_pair("border"),
            button_hover_color=ThemeManager.get_color_pair("primary"),
            text_color=ThemeManager.get_color_pair("text_main"),
            dropdown_fg_color=ThemeManager.get_color_pair("surface"),
            dropdown_text_color=ThemeManager.get_color_pair("text_main"),
            dropdown_hover_color=ThemeManager.get_color_pair("surface_alt"),
        )
        menu.pack(fill="x", pady=(2, 0))
        self._menus[key] = (menu, var)

    # ------------------------------------------------------------------ โหลดตัวเลือก
    def reload_options(self):
        """โหลดรายการแบรนด์/หมวด/ค่าสเปกจาก product_service.list_filter_values()"""
        try:
            from services import product_service
            values = product_service.list_filter_values()
        except Exception:  # noqa: BLE001 - โหลดไม่ได้ก็แสดงเมนูว่าง
            values = {}

        self._brands = self._pairs(values.get("brands", []))
        self._categories = self._pairs(values.get("categories", []))
        self._set_values("brand_id", list(self._brands))
        if "category_id" in self._menus:
            self._set_values("category_id", list(self._categories))
        for key, _label in _SPEC_LABELS:
            self._set_values(key, [str(v) for v in values.get(key, []) if v])

    @staticmethod
    def _pairs(items):
        out = {}
        for item in items or []:
            item_id, name = _id_name(item)
            if item_id is not None:
                out[name] = item_id
        return out

    def _set_values(self, key, names):
        menu, var = self._menus[key]
        current = var.get()
        menu.configure(values=[ALL] + names)
        var.set(current if current in names else ALL)

    # ------------------------------------------------------------------ อ่าน/ตั้งค่า
    def get_filters(self) -> dict:
        """คืน dict ตัวกรอง (ไม่เลือก = ไม่มีคีย์) — ช่วงราคาผิด → ValueError"""
        filters = {}
        brand = self._menus["brand_id"][1].get()
        if brand != ALL and brand in self._brands:
            filters["brand_id"] = self._brands[brand]
        if "category_id" in self._menus:
            category = self._menus["category_id"][1].get()
            if category != ALL and category in self._categories:
                filters["category_id"] = self._categories[category]

        if self._spec_visible:
            for key, _label in _SPEC_LABELS:
                value = self._menus[key][1].get()
                if value != ALL:
                    filters[key] = value

        low = self._parse_price(self.min_entry.get(), "ราคาต่ำสุด")
        high = self._parse_price(self.max_entry.get(), "ราคาสูงสุด")
        if low is not None and high is not None and low > high:
            raise ValueError("ราคาต่ำสุดต้องไม่มากกว่าราคาสูงสุด")
        if low is not None:
            filters["min_price"] = low
        if high is not None:
            filters["max_price"] = high

        if self.on_sale_var.get():
            filters["on_sale"] = True
        if self.in_stock_var.get():
            filters["in_stock"] = True
        return filters

    @staticmethod
    def _parse_price(text, label):
        text = (text or "").strip().replace(",", "")
        if not text:
            return None
        try:
            value = float(text)
        except ValueError:
            raise ValueError(f"{label}ต้องเป็นตัวเลข") from None
        if value < 0:
            raise ValueError(f"{label}ต้องไม่ติดลบ")
        return value

    def set_filters(self, filters: dict):
        """ตั้งค่าจาก dict (เช่น จำค่าที่เคยเลือกไว้) — คีย์ที่ไม่มี = ล้างเป็น 'ทั้งหมด'"""
        filters = filters or {}
        self._select_by_id("brand_id", self._brands, filters.get("brand_id"))
        if "category_id" in self._menus:
            self._select_by_id("category_id", self._categories, filters.get("category_id"))
        for key, _label in _SPEC_LABELS:
            value = filters.get(key)
            menu, var = self._menus[key]
            var.set(str(value) if value is not None and str(value) in (menu.cget("values") or []) else ALL)
        self._set_entry(self.min_entry, filters.get("min_price"))
        self._set_entry(self.max_entry, filters.get("max_price"))
        self.on_sale_var.set(bool(filters.get("on_sale")))
        self.in_stock_var.set(bool(filters.get("in_stock")))
        self.error_label.configure(text="")

    def _select_by_id(self, key, mapping, wanted):
        var = self._menus[key][1]
        for name, item_id in mapping.items():
            if item_id == wanted:
                var.set(name)
                return
        var.set(ALL)

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, "end")
        if value not in (None, ""):
            entry.insert(0, f"{value:g}" if isinstance(value, (int, float)) else str(value))

    def reset(self):
        """ล้างตัวกรองทั้งหมด (ยังไม่เรียก on_apply)"""
        self.set_filters({})

    def set_spec_visible(self, visible: bool):
        """แสดง/ซ่อนส่วนสเปกไม้ (ตัวกรองสเปกจะไม่ถูกนับเมื่อซ่อน)"""
        self._spec_visible = bool(visible)
        if visible:
            self._spec_frame.pack(fill="x", padx=14, pady=(12, 0), before=self._flags)
        else:
            self._spec_frame.pack_forget()

    # ------------------------------------------------------------------ ปุ่ม
    def _apply(self):
        try:
            filters = self.get_filters()
        except ValueError as exc:
            self.error_label.configure(text=str(exc))
            return
        self.error_label.configure(text="")
        if self._on_apply:
            self._on_apply(filters)

    def _reset_and_apply(self):
        self.reset()
        if self._on_apply:
            self._on_apply({})


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("560x640")
    flt = ProductFilter(root, on_apply=lambda f: print("filters =", f), show_category=True)
    flt.pack(side="left", fill="y", padx=12, pady=12)
    # ข้อมูลจำลอง (ไม่ต่อ DB)
    flt._brands = {"Yonex": 1, "Victor": 2}
    flt._categories = {"ไม้แบด": 1, "รองเท้า": 3}
    flt._set_values("brand_id", ["Yonex", "Victor"])
    flt._set_values("category_id", ["ไม้แบด", "รองเท้า"])
    for k, vals in (("weight_class", ["3U", "4U"]), ("balance", ["Heavy Head", "Even Balance", "Light Head"]),
                    ("flex", ["Stiff", "Medium", "Flexible"]), ("level", ["Beginner", "Intermediate", "Advanced"])):
        flt._set_values(k, vals)
    ctk.CTkButton(root, text="set_spec_visible(False)", command=lambda: flt.set_spec_visible(False)).pack(pady=20)
    root.mainloop()
