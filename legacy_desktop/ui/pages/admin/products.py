"""
ui/pages/admin/products.py
หน้ารายการสินค้า + รายการสินค้าที่ถูกลบ (แอดมิน/เจ้าของ — ปรับปรุงตามข้อ 2 และ ข้อ 3):
- ข้อ 3: เฉพาะ Owner เท่านั้น สามารถเพิ่ม/ลบสินค้าจาก Flash Sale ได้อย่างรวดเร็ว (ส่วนตั้งเวลา Flash Sale มีอยู่แล้วในฟอร์มสินค้า)
- ข้อ 2: รองรับปุ่มจัดการแบนเนอร์ (1-10 รูป + แก้ไขข้อความ) ให้ทั้ง Owner และ Admin ใช้งานได้
- แท็บสินค้าในระบบและแท็บสินค้าที่ถูกลบ (Soft Delete & Restore) คงเดิม
"""

from datetime import datetime, timedelta

import customtkinter as ctk

from services import banner_service, product_service, settings_service
from ui.components import dialogs
from ui.components.image_picker import ImagePicker
from ui.components.search_bar import SearchBar
from ui.pages.admin.common import (
    AdminPage, Pager, as_dict, btn, card, color, empty_state, entry, font, is_owner, label,
    option_menu, page_header, parse_money, pill, segmented, table_header, table_row, thumb,
)
from ui.theme import ThemeManager
from utils.formatters import format_datetime, format_price

PAGE_SIZE = 20
ALL_CATEGORIES = "ทุกหมวดหมู่"
ALL_BRANDS = "ทุกแบรนด์"
STATUS_ALL = "ทุกสถานะ"
STATUS_ACTIVE = "เฉพาะที่ขายอยู่"
STATUS_FLASH = "เฉพาะสินค้า Flash Sale"
SORTS = {
    "ใหม่ล่าสุด": "newest",
    "ราคา ต่ำ → สูง": "price_asc",
    "ราคา สูง → ต่ำ": "price_desc",
    "ชื่อ A → Z": "name",
    "ขายดี": "popular",
}
TAB_ACTIVE = "สินค้าในระบบ"
TAB_DELETED = "สินค้าที่ถูกลบ (ประวัติยอดขาย & กู้คืน)"

# รูป | ชื่อ | หมวด/แบรนด์ | ราคา | สต็อก | สถานะ | ปุ่ม
COLS = [(0, 56), (4, 175), (2, 120), (2, 105), (0, 64), (0, 82), (0, 285)]
DEL_COLS = [(0, 56), (4, 190), (2, 130), (2, 110), (2, 150), (2, 130), (0, 130)]


class AdminProductsPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._page = 1
        self._search = ""
        self._cat_ids = {}
        self._brand_ids = {}
        self._threshold = 5
        self._mode = TAB_ACTIVE

        _header, actions = page_header(
            self.content, "จัดการสินค้า · Flash Sale · แบนเนอร์หน้าร้าน",
            "จัดการสินค้า สต็อก แบนเนอร์ 1–10 รูป และจัดการสินค้า Flash Sale (เฉพาะ Owner)",
        )
        btn(actions, "＋ เพิ่มสินค้าใหม่", lambda: self.controller.show("admin_product_form"),
            kind="primary", size="md").pack(side="right")
        btn(actions, "จัดการแบนเนอร์ (1-10 รูป)", self._open_banner_manager_dialog,
            kind="info", size="md").pack(side="right", padx=6)

        self.mode_tabs = segmented(
            self.content, values=[TAB_ACTIVE, TAB_DELETED], command=self._switch_mode,
        )
        self.mode_tabs.set(TAB_ACTIVE)
        self.mode_tabs.pack(anchor="w", pady=(0, 8))

        # แถบค้นหา/ตัวกรอง
        self.filter_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        self.filter_bar.pack(fill="x", pady=(0, 8))
        SearchBar(self.filter_bar, command=self._on_search, placeholder="ค้นหาชื่อสินค้า/แบรนด์", width=250,
                  height=36).pack(side="left", padx=(0, 8))
        self.cat_var = ctk.StringVar(value=ALL_CATEGORIES)
        self.cat_menu = option_menu(self.filter_bar, [ALL_CATEGORIES], self.cat_var, self._on_filter, width=145)
        self.cat_menu.pack(side="left", padx=4)
        self.brand_var = ctk.StringVar(value=ALL_BRANDS)
        self.brand_menu = option_menu(self.filter_bar, [ALL_BRANDS], self.brand_var, self._on_filter, width=125)
        self.brand_menu.pack(side="left", padx=4)
        self.status_var = ctk.StringVar(value=STATUS_ALL)
        option_menu(
            self.filter_bar, [STATUS_ALL, STATUS_ACTIVE, STATUS_FLASH],
            self.status_var, self._on_filter, width=155,
        ).pack(side="left", padx=4)
        self.sort_var = ctk.StringVar(value="ใหม่ล่าสุด")
        option_menu(self.filter_bar, list(SORTS), self.sort_var, self._on_filter, width=135).pack(side="left", padx=4)

        self.table_head_holder = ctk.CTkFrame(self.content, fg_color="transparent")
        self.table_head_holder.pack(fill="x")
        self.list_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.list_frame.pack(fill="x")
        self.pager = Pager(self.content, self._goto)
        self.pager.pack(pady=12)

    def on_show(self, **kwargs):
        if not self.allowed():
            return
        self._threshold = settings_service.get_int("low_stock_threshold", 5)
        self._reload_filter_menus()
        self._load()

    def _switch_mode(self, mode):
        self._mode = mode
        self._page = 1
        self._load()

    def _reload_filter_menus(self):
        ok, cats = self.call(product_service.list_categories, include_inactive=True)
        ok2, brands = self.call(product_service.list_brands, include_inactive=True)
        self._cat_ids = {as_dict(c).get("name", ""): as_dict(c).get("id") for c in (cats if ok else [])}
        self._brand_ids = {as_dict(b).get("name", ""): as_dict(b).get("id") for b in (brands if ok2 else [])}
        self.cat_menu.configure(values=[ALL_CATEGORIES] + list(self._cat_ids))
        self.brand_menu.configure(values=[ALL_BRANDS] + list(self._brand_ids))
        if self.cat_var.get() not in self._cat_ids:
            self.cat_var.set(ALL_CATEGORIES)
        if self.brand_var.get() not in self._brand_ids:
            self.brand_var.set(ALL_BRANDS)

    def _on_search(self, text):
        self._search = (text or "").strip()
        self._page = 1
        self._load()

    def _on_filter(self, _value=None):
        self._page = 1
        self._load()

    def _goto(self, page):
        self._page = page
        self._load()

    def _filters(self):
        filters = {}
        if self.cat_var.get() in self._cat_ids:
            filters["category_id"] = self._cat_ids[self.cat_var.get()]
        if self.brand_var.get() in self._brand_ids:
            filters["brand_id"] = self._brand_ids[self.brand_var.get()]
        if self.status_var.get() == STATUS_FLASH:
            filters["on_sale"] = True
        return filters

    def _load(self):
        self.set_error("")
        for child in self.table_head_holder.winfo_children():
            child.destroy()
        for child in self.list_frame.winfo_children():
            child.destroy()

        if self._mode == TAB_DELETED:
            self.filter_bar.pack_forget()
            self.pager.pack_forget()
            table_header(
                self.table_head_holder, DEL_COLS,
                ["", "สินค้าที่ถูกลบ", "หมวด / แบรนด์", "ราคา", "ยอดขายสะสม", "ลบเมื่อ", "จัดการ"],
            )
            ok, rows = self.call(product_service.list_deleted_products, search=self._search or None)
            if not ok:
                empty_state(self.list_frame, "โหลดรายการสินค้าที่ถูกลบไม่สำเร็จ")
                return
            items = [as_dict(r) for r in (rows or [])]
            if not items:
                empty_state(self.list_frame, "ยังไม่มีสินค้าในถังขยะ")
                return
            for item in items:
                self._add_deleted_row(item)
            return

        if not self.filter_bar.winfo_ismapped():
            self.filter_bar.pack(fill="x", pady=(0, 8), before=self.table_head_holder)
        if not self.pager.winfo_ismapped():
            self.pager.pack(pady=12)

        table_header(self.table_head_holder, COLS, ["", "สินค้า", "หมวด / แบรนด์", "ราคา", "สต็อก", "สถานะ", "จัดการ"])
        ok, result = self.call(
            product_service.list_products_admin, search=self._search or None, filters=self._filters(),
            sort=SORTS.get(self.sort_var.get(), "newest"), page=self._page, page_size=PAGE_SIZE,
            show_inactive=self.status_var.get() != STATUS_ACTIVE,
        )
        if not ok:
            empty_state(self.list_frame, "โหลดรายการสินค้าไม่สำเร็จ")
            self.pager.set(1, 1)
            return
        result = as_dict(result)
        items = result.get("items") or []
        if not items:
            empty_state(self.list_frame, "ไม่พบสินค้าตามเงื่อนไขที่เลือก")
        for item in items:
            self._add_row(as_dict(item))
        self.pager.set(result.get("page", 1), result.get("pages", 1), result.get("total"))

    def _add_row(self, p):
        row = table_row(self.list_frame, COLS)
        thumb(row, p.get("image_path"), 44).grid(row=0, column=0, padx=8, pady=6)

        name_box = ctk.CTkFrame(row, fg_color="transparent")
        name_box.grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(name_box, text=p.get("name", "-"), font=font("body_bold"), anchor="w", wraplength=240,
                     justify="left").pack(anchor="w")
        label(name_box, f"รหัส #{p.get('id')}", "tiny", muted=True).pack(anchor="w")

        label(row, f"{p.get('category_name') or '-'}\n{p.get('brand_name') or '-'}", "small",
              muted=True, justify="left").grid(row=0, column=2, sticky="w", padx=8)

        price_box = ctk.CTkFrame(row, fg_color="transparent")
        price_box.grid(row=0, column=3, sticky="w", padx=8)
        eff = p.get("effective_price", p.get("price"))
        ctk.CTkLabel(price_box, text=format_price(eff), font=font("body_bold"), anchor="w").pack(anchor="w")
        if p.get("is_on_sale"):
            ctk.CTkLabel(price_box, text="FLASH SALE ลดราคา", font=font("tiny"), anchor="w",
                         text_color=color("danger")).pack(anchor="w")

        stock = int(p.get("stock") or 0)
        low = stock <= self._threshold
        ctk.CTkLabel(row, text="หมด" if stock == 0 else str(stock), font=font("body_bold"),
                     text_color=color("danger") if low else color("text")).grid(row=0, column=4, sticky="w", padx=8)

        active = bool(p.get("is_active", 1))
        pill(row, "ขายอยู่" if active else "ปิดขาย", "success" if active else "muted").grid(
            row=0, column=5, sticky="w", padx=8)

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=6, sticky="e", padx=8)
        btn(actions, "แก้ไข", lambda pid=p.get("id"): self.controller.show("admin_product_form", product_id=pid),
            kind="outline", width=54).pack(side="left", padx=2)
        if is_owner():
            # ข้อ 3: เฉพาะ Owner เท่านั้น สามารถเพิ่ม/ลบของใน Flash Sale ได้เลย
            on_sale = bool(p.get("is_on_sale"))
            btn(
                actions,
                "ลบ Flash" if on_sale else "+Flash Sale",
                lambda prod=p: self._manage_flash_sale(prod),
                kind="danger" if on_sale else "primary",
                width=78,
            ).pack(side="left", padx=2)
            btn(actions, "ปิดขาย" if active else "เปิดขาย",
                lambda prod=p: self._toggle_active(prod),
                kind="warning" if active else "success", width=60).pack(side="left", padx=2)
            btn(actions, "ลบ",
                lambda prod=p: self._soft_delete(prod),
                kind="danger", width=48).pack(side="left", padx=2)

    def _add_deleted_row(self, p):
        row = table_row(self.list_frame, DEL_COLS)
        thumb(row, p.get("image_path"), 44).grid(row=0, column=0, padx=8, pady=6)

        name_box = ctk.CTkFrame(row, fg_color="transparent")
        name_box.grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(name_box, text=p.get("name", "-"), font=font("body_bold"), anchor="w", wraplength=260,
                     justify="left").pack(anchor="w")
        label(name_box, f"รหัส #{p.get('id')}", "tiny", muted=True).pack(anchor="w")

        label(row, f"{p.get('category_name') or '-'}\n{p.get('brand_name') or '-'}", "small",
              muted=True, justify="left").grid(row=0, column=2, sticky="w", padx=8)

        ctk.CTkLabel(row, text=format_price(p.get("price")), font=font("body_bold"), anchor="w").grid(
            row=0, column=3, sticky="w", padx=8)

        sold_qty = int(p.get("total_sold_qty") or 0)
        sold_rev = float(p.get("total_sold_revenue") or 0.0)
        label(row, f"ขายแล้ว {sold_qty:,} ชิ้น\nรวม {format_price(sold_rev)}", "small",
              muted=False, justify="left").grid(row=0, column=4, sticky="w", padx=8)

        label(row, format_datetime(p.get("deleted_at")), "tiny", muted=True).grid(
            row=0, column=5, sticky="w", padx=8)

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=6, sticky="e", padx=8)
        if is_owner():
            btn(actions, "กู้คืนสินค้า", lambda prod=p: self._restore(prod),
                kind="success", width=110).pack(side="left", padx=2)

    # ------------------------------------------------------------------ ข้อ 3: เพิ่ม/ลบสินค้า Flash Sale (เฉพาะ Owner)
    def _manage_flash_sale(self, p: dict):
        if not is_owner():
            self.set_error("เฉพาะเจ้าของร้าน (Owner) เท่านั้นที่จัดการ Flash Sale ได้")
            return
        pid = p.get("id")
        ok, full = self.call(product_service.get_product_for_edit, pid)
        if not ok or not full:
            return
        full = as_dict(full)

        if p.get("is_on_sale"):
            if not dialogs.confirm(
                self, "นำออกจาก Flash Sale",
                f"ต้องการนำ “{p.get('name')}” ออกจากโปรโมชัน Flash Sale กลับไปใช้ราคาปกติ {format_price(full.get('price'))} ใช่หรือไม่?",
                confirm_text="นำออกจาก Flash Sale", danger=True,
            ):
                return
            fields = {
                "category_id": full["category_id"],
                "brand_id": full["brand_id"],
                "name": full["name"],
                "description": full.get("description") or "",
                "price": full["price"],
                "sale_price": None,
                "sale_ends_at": None,
                "stock": full.get("stock") or 0,
                "is_active": bool(full.get("is_active", 1)),
                "weight_class": full.get("weight_class"),
                "balance": full.get("balance"),
                "flex": full.get("flex"),
                "level": full.get("level"),
            }
            ok2, _ = self.call(product_service.save_product, fields, product_id=pid)
            if ok2:
                self._load()
            return

        # เปิดหน้าต่างตั้งราคาโปรและเวลาสิ้นสุด Flash Sale
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"เพิ่มสินค้าเข้า Flash Sale — {full.get('name')}")
        dlg.geometry("440x320")
        dlg.resizable(False, False)
        dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
        dlg.transient(self.winfo_toplevel())

        ctk.CTkLabel(dlg, text=f"เพิ่มเข้า Flash Sale: {full.get('name')}", font=font("h3")).pack(
            anchor="w", padx=20, pady=(16, 4))
        label(dlg, f"ราคาปกติ: {format_price(full.get('price'))}", "body_bold").pack(anchor="w", padx=20, pady=(0, 8))

        label(dlg, "ราคาลดพิเศษ Flash Sale (บาท) *", "small", muted=True).pack(anchor="w", padx=20)
        default_sale = round(float(full.get("price") or 100) * 0.85, 0)
        sp_entry = entry(dlg, f"เช่น {default_sale:g}")
        sp_entry.pack(fill="x", padx=20, pady=(2, 8))
        sp_entry.insert(0, f"{default_sale:g}")

        label(dlg, "วันเวลาสิ้นสุด Flash Sale (YYYY-MM-DD HH:MM) *", "small", muted=True).pack(anchor="w", padx=20)
        default_end = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d 23:59")
        end_entry = entry(dlg, default_end)
        end_entry.pack(fill="x", padx=20, pady=(2, 6))
        end_entry.insert(0, default_end)

        err_lbl = ctk.CTkLabel(dlg, text="", font=font("small"), text_color=color("danger"))
        err_lbl.pack(fill="x", padx=20)

        def save_flash():
            try:
                sp = parse_money(sp_entry.get(), "ราคาลดพิเศษ", required=True, minimum=1)
                fields = {
                    "category_id": full["category_id"],
                    "brand_id": full["brand_id"],
                    "name": full["name"],
                    "description": full.get("description") or "",
                    "price": full["price"],
                    "sale_price": sp,
                    "sale_ends_at": end_entry.get().strip(),
                    "stock": full.get("stock") or 0,
                    "is_active": bool(full.get("is_active", 1)),
                    "weight_class": full.get("weight_class"),
                    "balance": full.get("balance"),
                    "flex": full.get("flex"),
                    "level": full.get("level"),
                }
                product_service.save_product(fields, product_id=pid)
                dlg.destroy()
                self._load()
            except Exception as exc:  # noqa: BLE001
                err_lbl.configure(text=str(exc))

        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=12)
        btn(row, "บันทึกเข้า Flash Sale", save_flash, kind="primary", size="md").pack(side="right")
        btn(row, "ยกเลิก", dlg.destroy, kind="outline", size="md").pack(side="right", padx=8)
        dlg.after(120, lambda: (dlg.lift(), sp_entry.focus_set()))

    # ------------------------------------------------------------------ ข้อ 2: หน้าต่างจัดการแบนเนอร์ 1–10 รูป สำหรับ Owner และ Admin
    def _open_banner_manager_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("จัดการแบนเนอร์หน้าแรก (1–10 รูป พร้อมปรับแต่งข้อความ)")
        dlg.geometry("680x580")
        dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
        dlg.transient(self.winfo_toplevel())

        edit_state = {"id": None}

        top_box = card(dlg)
        top_box.pack(fill="x", padx=16, pady=(14, 8))
        form_lbl = label(top_box, "เพิ่ม/แก้ไขแบนเนอร์หน้าแรก (รองรับ 1 – 10 รูป)", "h3")
        form_lbl.pack(fill="x", padx=14, pady=(10, 4))

        frow = ctk.CTkFrame(top_box, fg_color="transparent")
        frow.pack(fill="x", padx=14, pady=4)
        b_picker = ImagePicker(frow, size=76, allow_clear=True)
        b_picker.pack(side="left", padx=(0, 12))
        rcol = ctk.CTkFrame(frow, fg_color="transparent")
        rcol.pack(side="left", fill="x", expand=True)
        b_title = entry(rcol, "หัวข้อแบนเนอร์ * เช่น ตัวช่วยเลือกไม้ & AI แนะนำไม้แบดคู่ใจ 3 รุ่น", height=34)
        b_title.pack(fill="x", pady=2)
        b_sub = entry(rcol, "คำอธิบายเพิ่มเติม เช่น วิเคราะห์ตามระดับฝีมือ สไตล์การเล่น และงบประมาณ", height=34)
        b_sub.pack(fill="x", pady=2)

        err_lbl = ctk.CTkLabel(top_box, text="", font=font("small"), text_color=color("danger"))
        err_lbl.pack(fill="x", padx=14)

        b_btns = ctk.CTkFrame(rcol, fg_color="transparent")
        b_btns.pack(fill="x", pady=(4, 6))

        list_scroll = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        list_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        def reset_form():
            edit_state["id"] = None
            form_lbl.configure(text="เพิ่ม/แก้ไขแบนเนอร์หน้าแรก (รองรับ 1 – 10 รูป)")
            b_title.delete(0, "end")
            b_sub.delete(0, "end")
            b_picker.set_initial(None)
            save_btn.configure(text="＋ เพิ่มแบนเนอร์")

        def save_banner():
            err_lbl.configure(text="")
            t = b_title.get().strip()
            s = b_sub.get().strip()
            if not t and not b_picker.get_selected_file():
                err_lbl.configure(text="กรุณากรอกหัวข้อแบนเนอร์ หรือเลือกรูปแบนเนอร์")
                return
            payload = {"title": t or "โปรโมชันพิเศษ", "subtitle": s, "is_active": True}
            if b_picker.has_change():
                payload["image_path"] = b_picker.get_selected_file() or ""
            try:
                banner_service.save_banner(payload, banner_id=edit_state["id"])
                reset_form()
                reload_list()
            except Exception as exc:  # noqa: BLE001
                err_lbl.configure(text=str(exc))

        save_btn = btn(b_btns, "＋ เพิ่มแบนเนอร์", save_banner, kind="primary", size="sm")
        save_btn.pack(side="left")
        btn(b_btns, "ล้างฟอร์ม", reset_form, kind="outline", size="sm").pack(side="left", padx=6)

        def edit_item(item):
            edit_state["id"] = item.get("id")
            form_lbl.configure(text=f"แก้ไขแบนเนอร์ #{item.get('id')}")
            b_title.delete(0, "end")
            b_title.insert(0, str(item.get("title") or ""))
            b_sub.delete(0, "end")
            b_sub.insert(0, str(item.get("subtitle") or ""))
            b_picker.set_initial(item.get("image_path") or None)
            save_btn.configure(text="บันทึกการแก้ไข")

        def toggle_item(item):
            try:
                banner_service.set_banner_active(item.get("id"), not bool(item.get("is_active", 1)))
                reload_list()
            except Exception as exc:  # noqa: BLE001
                err_lbl.configure(text=str(exc))

        def del_item(bid):
            try:
                banner_service.delete_banner(bid)
                reload_list()
            except Exception as exc:  # noqa: BLE001
                err_lbl.configure(text=str(exc))

        def reload_list():
            for child in list_scroll.winfo_children():
                child.destroy()
            try:
                rows = banner_service.list_all_banners()
            except Exception:  # noqa: BLE001
                rows = []
            if not rows:
                label(list_scroll, "ยังไม่มีแบนเนอร์ที่อัปโหลดเอง (ใส่ได้ตั้งแต่ 1 – 10 รูป)", "small", muted=True).pack(pady=12)
                return
            for idx, b in enumerate(rows, start=1):
                r = card(list_scroll)
                r.pack(fill="x", pady=2)
                thumb(r, b.get("image_path"), 42, cover=bool(b.get("image_path"))).pack(side="left", padx=8, pady=4)
                inf = ctk.CTkFrame(r, fg_color="transparent")
                inf.pack(side="left", fill="x", expand=True, padx=6)
                ctk.CTkLabel(inf, text=f"#{idx} {b.get('title') or '-'}", font=font("small_bold"), anchor="w").pack(fill="x")
                label(inf, b.get("subtitle") or "", "tiny", muted=True).pack(fill="x")
                act = bool(b.get("is_active", 1))
                pill(r, "แสดง" if act else "ซ่อน", "success" if act else "muted").pack(side="left", padx=4)
                btn(r, "แก้ไข", lambda it=b: edit_item(it), kind="info", width=54).pack(side="left", padx=2)
                btn(r, "ซ่อน" if act else "แสดง", lambda it=b: toggle_item(it), kind="outline", width=54).pack(side="left", padx=2)
                btn(r, "ลบ", lambda bid=b.get("id"): del_item(bid), kind="danger", width=48).pack(side="left", padx=(2, 8))

        reload_list()
        dlg.after(120, dlg.lift)

    def _toggle_active(self, p):
        active = bool(p.get("is_active", 1))
        name = p.get("name", "")
        if active:
            if not dialogs.confirm(
                self, "ปิดขายสินค้า",
                f"ปิดขาย “{name}” ใช่ไหม?\nผู้ซื้อจะมองไม่เห็นสินค้านี้ (ประวัติออเดอร์ยังอยู่ครบ)",
                confirm_text="ปิดขาย", danger=True,
            ):
                return
        ok, _ = self.call(product_service.set_product_active, p.get("id"), not active)
        if ok:
            self._load()

    def _soft_delete(self, p):
        name = p.get("name", "")
        if not dialogs.confirm(
            self, "ลบสินค้าแบบเก็บประวัติ (Soft Delete)",
            f"ย้ายสินค้า “{name}” ไปที่รายการสินค้าที่ถูกลบใช่ไหม?\n"
            "• สินค้าจะถูกซ่อนจากหน้าร้าน\n"
            "• ประวัติคำสั่งซื้อ รีวิว และรายงานยอดขายเดิมจะยังคงอยู่ครบถ้วน\n"
            "• สามารถกดกู้คืนได้ทุกเมื่อที่แท็บ 'สินค้าที่ถูกลบ'",
            confirm_text="ลบเก็บประวัติ", danger=True,
        ):
            return
        ok, _ = self.call(product_service.soft_delete_product, p.get("id"))
        if ok:
            self._load()

    def _restore(self, p):
        ok, _ = self.call(product_service.restore_product, p.get("id"), activate=True)
        if ok:
            dialogs.show_message(self, "กู้คืนสำเร็จ", f"กู้คืนสินค้า “{p.get('name')}” กลับมาเปิดขายเรียบร้อยแล้ว", kind="success")
            self._load()
