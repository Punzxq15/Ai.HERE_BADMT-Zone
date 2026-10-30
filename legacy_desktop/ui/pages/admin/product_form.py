"""
ui/pages/admin/product_form.py
ฟอร์มเพิ่ม/แก้ไขสินค้า (แอดมิน/เจ้าของ) — route `admin_product_form` → AdminProductFormPage
ปรับปรุงตาม T02, T03, T04, T08:
- T02: ตัวเลือกสเปกไม้ (น้ำหนัก 3U–10U, จุดสมดุล, ความแข็งก้าน, Skill Level) และตัวเลือกหมวดหมู่อื่นๆ ดึงจากที่ Owner ตั้งค่าไว้
- T03: ฟอร์มกรอก Technical Specifications ของไม้แบดมินตันครบทั้ง 7 หัวข้อ:
  * Material (พิมพ์เอง)
  * Weight Class / Grip (พิมพ์เอง)
  * Balance Point (ตัวเลข mm พิมพ์เอง + ประเภท Head Heavy ฯลฯ เลือกจากที่ Owner ตั้งไว้)
  * Shaft Flexibility (เลือกจากที่ Owner ตั้งไว้)
  * Max String Tension (พิมพ์เอง)
  * Length (พิมพ์เอง)
  * Skill Level (เลือกจากที่ Owner ตั้งไว้)
- T04: รองรับการเพิ่มรูปภาพสินค้าได้มากกว่า 1 รูป (แกลเลอรีหลายรูป + เรียงลำดับ + ตั้งรูปหลัก + ผูกรูปกับสี/สไตล์)
- T08: ช่องตั้งวัน-เวลาสิ้นสุด Flash Sale ใช้ปฏิทิน DateTimePickerField
"""

from datetime import datetime

import customtkinter as ctk

import config
from core.constants import BALANCES, FLEXES, LEVELS, OPTION_TYPES, WEIGHT_CLASSES
from services import product_service
from ui.components import dialogs
from ui.components.date_picker import DateTimePickerField
from ui.components.image_picker import ImagePicker
from ui.components.search_bar import SearchBar
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, entry, font, is_owner, label, option_menu,
    page_header, parse_int, parse_money, pill, thumb,
)
from utils import image_utils
from utils.formatters import format_price

NONE_CHOICE = "- ไม่ระบุ -"
PICK_CHOICE = "- เลือก -"
SALE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")


def _parse_sale_end(text):
    text = (text or "").strip()
    if not text:
        return None
    for fmt in SALE_FORMATS:
        try:
            value = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt == "%Y-%m-%d":
            value = value.replace(hour=23, minute=59, second=59)
        return value.strftime("%Y-%m-%d %H:%M:%S")
    raise ValueError("วันสิ้นสุดโปรต้องเป็นรูปแบบ ปปปป-ดด-วว หรือ ปปปป-ดด-วว ชม:นน (เช่น 2026-10-20 18:00)")


class AdminProductFormPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._product_id = None
        self._data = {}
        self._option_edit_id = None
        self._cat_map = {}
        self._brand_map = {}
        self._spec_menus = {}
        self.picker = None
        self.gallery_picker = None

    def on_show(self, product_id=None, **kwargs):
        if not self.allowed():
            return
        self._product_id = product_id
        self._option_edit_id = None
        self.set_error("")
        self._data = {}
        if product_id is not None:
            ok, data = self.call(product_service.get_product_for_edit, product_id)
            if not ok:
                self.clear_content()
                self._header(None)
                return
            self._data = as_dict(data)
        self._build()

    def _header(self, title):
        _h, actions = page_header(self.content, title or "สินค้า")
        btn(actions, "← กลับ", lambda: self.controller.go_back(default="admin_products"), kind="outline").pack(
            side="right")
        return actions

    def _has_options(self):
        return bool(self._data.get("options"))

    def _build(self):
        self.clear_content()
        is_new = self._product_id is None
        actions = self._header("เพิ่มสินค้าใหม่" if is_new else f"แก้ไขสินค้า #{self._product_id}")
        if not is_new and is_owner():
            active = bool(self._data.get("is_active", 1))
            btn(actions, "ปิดขายสินค้า" if active else "เปิดขายสินค้า", self._toggle_active,
                kind="warning" if active else "success").pack(side="right", padx=6)
            if self._data.get("deleted_at"):
                btn(actions, "♻️ กู้คืนสินค้า", self._restore_product, kind="success").pack(side="right", padx=6)
            else:
                btn(actions, "🗑️ ลบเก็บประวัติ", self._soft_delete_product, kind="danger").pack(side="right", padx=6)

        if not is_owner():
            note = ("แอดมินตั้งได้เฉพาะ \"ราคาปกติ\" — ราคาลด/Flash Sale ให้เจ้าของร้านตั้งภายหลัง" if is_new else
                    "แอดมินแก้ราคา/โปรโมชันไม่ได้ (เจ้าของร้านเท่านั้น) — แก้ข้อมูลอื่นและสต็อกได้")
            label(self.content, "ℹ️ " + note, "small", muted=True, wraplength=760, justify="left").pack(
                fill="x", pady=(0, 8))

        self._build_info_card(is_new)
        if is_new:
            label(
                self.content,
                "💡 บันทึกสินค้าก่อน แล้วจะสามารถเพิ่มรูปภาพหลายรูป (แกลเลอรี), ตัวเลือก (สี/สไตล์/ด้าม/เอ็น/ไซซ์) และสินค้าเสริมขายคู่ได้",
                "small", muted=True,
            ).pack(fill="x", pady=10)
            return

        # T04: การ์ดจัดการรูปภาพหลายรูปของสินค้า (แกลเลอรี + ผูกรูปกับสี/สไตล์)
        self.gallery_card = card(self.content)
        self.gallery_card.pack(fill="x", pady=(12, 0))
        self._build_gallery_card()

        self.opt_card = card(self.content)
        self.opt_card.pack(fill="x", pady=(12, 0))
        self._build_options_card()

        self.addon_card = card(self.content)
        self.addon_card.pack(fill="x", pady=(12, 16))
        self._build_addons_card()

    def _field(self, parent, text, row, col, span=1):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=col, columnspan=span, sticky="ew", padx=6, pady=4)
        label(box, text, "small", muted=True).pack(fill="x")
        return box

    def _build_info_card(self, is_new):
        d = self._data
        owner = is_owner()
        box = card(self.content)
        box.pack(fill="x")
        label(box, "ข้อมูลสินค้าและ Technical Specifications", "h3").pack(fill="x", padx=16, pady=(14, 4))
        body = ctk.CTkFrame(box, fg_color="transparent")
        body.pack(fill="x", padx=10, pady=(0, 6))
        body.grid_columnconfigure(1, weight=1)

        pic_box = ctk.CTkFrame(body, fg_color="transparent")
        pic_box.grid(row=0, column=0, sticky="n", padx=(6, 12), pady=4)
        self.picker = ImagePicker(pic_box, size=170, initial_path=d.get("image_path"), allow_clear=True)
        self.picker.pack()
        label(pic_box, "รูปสินค้าหลัก 1:1 (jpg/png/webp)", "tiny", muted=True).pack(pady=(4, 0))

        form = ctk.CTkFrame(body, fg_color="transparent")
        form.grid(row=0, column=1, sticky="ew")
        for c in range(2):
            form.grid_columnconfigure(c, weight=1, uniform="f")

        self.e_name = entry(self._field(form, "ชื่อสินค้า *", 0, 0, 2))
        self.e_name.pack(fill="x")
        self.e_name.insert(0, d.get("name") or "")

        cats = self._load_pairs(product_service.list_categories)
        brands = self._load_pairs(product_service.list_brands)
        self._cat_map, self._brand_map = cats, brands
        cat_name = next((n for n, i in cats.items() if i == d.get("category_id")), PICK_CHOICE)
        brand_name = next((n for n, i in brands.items() if i == d.get("brand_id")), PICK_CHOICE)
        self.cat_var = ctk.StringVar(value=cat_name)
        self.brand_var = ctk.StringVar(value=brand_name)
        option_menu(self._field(form, "หมวดหมู่ *", 1, 0), [PICK_CHOICE] + list(cats), self.cat_var,
                    command=self._on_category_change, width=200).pack(fill="x")
        self.brand_menu = option_menu(self._field(form, "แบรนด์ *", 1, 1), [PICK_CHOICE] + list(brands),
                                      self.brand_var, width=200)
        self.brand_menu.pack(fill="x")

        can_price = owner or is_new
        self.e_price = entry(self._field(form, "ราคาปกติ (บาท) *", 2, 0), "เช่น 2990")
        self.e_price.pack(fill="x")
        self.e_price.insert(0, "" if d.get("price") is None else f"{d.get('price'):g}")
        self.e_stock = entry(self._field(form, "สต็อก (ชิ้น)", 2, 1), "0")
        self.e_stock.pack(fill="x")
        self.e_stock.insert(0, str(d.get("stock") if d.get("stock") is not None else 0))

        self.e_sale = entry(self._field(form, "ราคาลด (บาท) — เว้นว่าง = ไม่ลด", 3, 0))
        self.e_sale.pack(fill="x")
        self.e_sale.insert(0, "" if d.get("sale_price") is None else f"{d.get('sale_price'):g}")

        # T08: เลือกวัน-เวลาสิ้นสุด Flash Sale จากปฏิทิน DateTimePickerField
        sale_end_box = self._field(form, "โปรสิ้นสุด (Flash Sale) — เลือกวัน-เวลาจากปฏิทิน", 3, 1)
        self.e_sale_end = DateTimePickerField(
            sale_end_box, placeholder_text="เว้นว่าง = ลดตลอด", default_end_of_day=True, height=36,
        )
        self.e_sale_end.pack(fill="x")
        self.e_sale_end.set(str(d.get("sale_ends_at") or "")[:19])

        self.e_cost = entry(self._field(form, "ต้นทุนต่อชิ้น (บาท — สำหรับรายงานกำไร/ต้นทุน)", 4, 0), "0")
        self.e_cost.pack(fill="x")
        self.e_cost.insert(0, "" if d.get("cost_price") is None else f"{float(d.get('cost_price') or 0):g}")

        if not can_price:
            self.e_price.configure(state="disabled")
        if not owner:
            for widget in (self.e_sale, self.e_sale_end, self.e_cost):
                widget.configure(state="disabled")
        self._sync_stock_entry()

        # T02 & T03: สเปกไม้แบด + Technical Specifications 7 หัวข้อ
        allowed_specs = product_service.get_allowed_racket_spec_options(
            category_id=d.get("category_id"), current_product=d
        )
        spec_frame = ctk.CTkFrame(form, fg_color=color("surface_alt"), corner_radius=10)
        spec_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=6, pady=(8, 4))

        spec_hdr = ctk.CTkFrame(spec_frame, fg_color="transparent")
        spec_hdr.pack(fill="x", padx=12, pady=(8, 2))
        label(
            spec_hdr,
            "Technical Specifications สำหรับไม้แบดมินตัน (T02 & T03 — เว้นว่างได้สำหรับหมวดอื่น)",
            "body_bold",
        ).pack(side="left")
        if owner:
            btn(
                spec_hdr,
                "⚙️ เพิ่มค่า 3U–10U / ตั้งค่าตัวเลือกหมวดหมู่",
                lambda: self.controller.show("admin_categories"),
                kind="outline", size="sm",
            ).pack(side="right")

        # แถวเลือกตัวเลือกหลัก (Weight Class, Balance Type, Shaft Flexibility, Skill Level)
        row = ctk.CTkFrame(spec_frame, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(2, 4))
        self.spec_vars = {}
        self._spec_menus = {}
        spec_defs = (
            ("weight_class", "Weight Class (ตัวกรอง)", allowed_specs.get("weight_class") or WEIGHT_CLASSES),
            ("balance", "Balance Type (เช่น Head Heavy)", allowed_specs.get("balance") or BALANCES),
            ("flex", "Shaft Flexibility *", allowed_specs.get("flex") or FLEXES),
            ("level", "Skill Level *", allowed_specs.get("level") or LEVELS),
        )
        for key, title, values in spec_defs:
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.pack(side="left", fill="x", expand=True, padx=4)
            label(cell, title, "tiny", muted=True).pack(fill="x")
            init_val = d.get(key) or (d.get("spec_balance_type") if key == "balance" else None) or NONE_CHOICE
            var = ctk.StringVar(value=init_val)
            self.spec_vars[key] = var
            m = option_menu(cell, [NONE_CHOICE] + list(values), var, width=130)
            m.pack(fill="x")
            self._spec_menus[key] = m

        # แถวกรอกข้อความ Technical Specifications (Material, Weight Class / Grip, Balance Point mm, Max String Tension, Length)
        tech_grid = ctk.CTkFrame(spec_frame, fg_color="transparent")
        tech_grid.pack(fill="x", padx=8, pady=(2, 10))
        tech_grid.grid_columnconfigure((0, 1), weight=1, uniform="ts")

        self.e_spec_material = entry(
            self._field(tech_grid, "Material (เจ้าของพิมพ์เอง)", 0, 0),
            "เช่น 46T Mitsubishi Carbon Sheet + M40X Carbon", height=34,
        )
        self.e_spec_material.pack(fill="x")
        self.e_spec_material.insert(0, d.get("spec_material") or "")

        self.e_spec_weight_grip = entry(
            self._field(tech_grid, "Weight Class / Grip (เจ้าของพิมพ์เอง)", 0, 1),
            "เช่น 4U (82±2 grams) / G6 grip size", height=34,
        )
        self.e_spec_weight_grip.pack(fill="x")
        self.e_spec_weight_grip.insert(0, d.get("spec_weight_grip") or "")

        self.e_spec_balance_mm = entry(
            self._field(tech_grid, "Balance Point ตัวเลข (mm — จะรวมกับ Balance Type อัตโนมัติ)", 1, 0),
            "เช่น 305±3 mm", height=34,
        )
        self.e_spec_balance_mm.pack(fill="x")
        self.e_spec_balance_mm.insert(0, d.get("spec_balance_mm") or "")

        self.e_spec_max_tension = entry(
            self._field(tech_grid, "Max String Tension (เจ้าของพิมพ์เอง)", 1, 1),
            "เช่น Up to 35 lbs", height=34,
        )
        self.e_spec_max_tension.pack(fill="x")
        self.e_spec_max_tension.insert(0, d.get("spec_max_tension") or "")

        self.e_spec_length = entry(
            self._field(tech_grid, "Length (ความยาวไม้ — เจ้าของพิมพ์เอง)", 2, 0),
            "เช่น 675 mm", height=34,
        )
        self.e_spec_length.pack(fill="x")
        self.e_spec_length.insert(0, d.get("spec_length") or "")

        desc_box = self._field(form, "คำอธิบายสินค้า", 6, 0, 2)
        self.t_desc = ctk.CTkTextbox(desc_box, height=90, font=font("body"), wrap="word")
        self.t_desc.pack(fill="x")
        self.t_desc.insert("1.0", d.get("description") or "")

        foot = ctk.CTkFrame(box, fg_color="transparent")
        foot.pack(fill="x", padx=16, pady=(6, 14))
        btn(foot, "💾 บันทึกสินค้า", self._save, kind="primary", size="md").pack(side="right")
        btn(foot, "ยกเลิก", lambda: self.controller.go_back(default="admin_products"), kind="outline",
            size="md").pack(side="right", padx=8)

    def _on_category_change(self, _val=None):
        cid = self._cat_map.get(self.cat_var.get())
        ok, rows = self.call(product_service.list_brands, include_inactive=True, category_id=cid)
        if ok:
            pairs = {}
            for r in (rows or []):
                r = as_dict(r)
                name = r.get("name", "")
                pairs[name + ("" if r.get("is_active", 1) else " (ปิด)")] = r.get("id")
            if pairs:
                self._brand_map = pairs
                self.brand_menu.configure(values=[PICK_CHOICE] + list(pairs))
                if self.brand_var.get() not in pairs:
                    self.brand_var.set(PICK_CHOICE)

        # อัปเดตรายการตัวเลือกสเปกไม้จากชุดตัวเลือกของหมวดที่เลือก
        try:
            allowed_specs = product_service.get_allowed_racket_spec_options(category_id=cid, current_product=self._data)
            for key, menu in self._spec_menus.items():
                vals = allowed_specs.get(key) or []
                menu.configure(values=[NONE_CHOICE] + list(vals))
        except Exception:  # noqa: BLE001
            pass

    def _load_pairs(self, loader):
        ok, rows = self.call(loader, include_inactive=True)
        pairs = {}
        for r in (rows if ok else []):
            r = as_dict(r)
            name = r.get("name", "")
            pairs[name + ("" if r.get("is_active", 1) else " (ปิด)")] = r.get("id")
        return pairs

    def _sync_stock_entry(self):
        if not hasattr(self, "e_stock") or not self.e_stock.winfo_exists():
            return
        self.e_stock.configure(state="normal")
        self.e_stock.delete(0, "end")
        self.e_stock.insert(0, str(self._data.get("stock") if self._data.get("stock") is not None else 0))
        if self._has_options():
            self.e_stock.configure(state="disabled")

    def _collect(self):
        is_new = self._product_id is None
        owner = is_owner()
        name = self.e_name.get().strip()
        if not name:
            raise ValueError("กรุณากรอกชื่อสินค้า")
        category_id = self._cat_map.get(self.cat_var.get())
        brand_id = self._brand_map.get(self.brand_var.get())
        if category_id is None:
            raise ValueError("กรุณาเลือกหมวดหมู่")
        if brand_id is None:
            raise ValueError("กรุณาเลือกแบรนด์")
        fields = {
            "name": name,
            "category_id": category_id,
            "brand_id": brand_id,
            "description": self.t_desc.get("1.0", "end").strip(),
        }
        for key, var in self.spec_vars.items():
            fields[key] = None if var.get() == NONE_CHOICE else var.get()

        # T03: Technical Specifications
        fields["spec_material"] = self.e_spec_material.get().strip() or None
        fields["spec_weight_grip"] = self.e_spec_weight_grip.get().strip() or None
        fields["spec_balance_mm"] = self.e_spec_balance_mm.get().strip() or None
        fields["spec_balance_type"] = fields.get("balance")
        fields["spec_max_tension"] = self.e_spec_max_tension.get().strip() or None
        fields["spec_length"] = self.e_spec_length.get().strip() or None

        if owner or is_new:
            price = parse_money(self.e_price.get(), "ราคาปกติ", required=True)
            if price <= 0:
                raise ValueError("ราคาปกติต้องมากกว่า 0")
            fields["price"] = price
        if owner:
            sale = parse_money(self.e_sale.get(), "ราคาลด")
            sale_end = _parse_sale_end(self.e_sale_end.get())
            if sale is not None and sale >= fields["price"]:
                raise ValueError("ราคาลดต้องน้อยกว่าราคาปกติ")
            if sale is None and sale_end is not None:
                raise ValueError("ตั้งวันสิ้นสุดโปรแล้ว กรุณากรอกราคาลดด้วย")
            fields["sale_price"] = sale
            fields["sale_ends_at"] = sale_end if sale is not None else None
            cost = parse_money(self.e_cost.get(), "ต้นทุนต่อชิ้น", required=False, minimum=0)
            fields["cost_price"] = cost or 0.0
        if not self._has_options():
            fields["stock"] = parse_int(self.e_stock.get(), "สต็อก", required=False) or 0

        if self.picker.has_change():
            if self.picker.is_cleared():
                fields["image_path"] = None
            else:
                fields["image_path"] = image_utils.save_upload(
                    self.picker.get_selected_file(), config.PRODUCT_IMAGES_DIR, "product",
                )
        return fields

    def _save(self):
        self.set_error("")
        try:
            fields = self._collect()
        except ValueError as exc:
            self.set_error(str(exc))
            return
        ok, saved = self.call(product_service.save_product, fields, product_id=self._product_id)
        if not ok:
            return
        new_id = as_dict(saved).get("id", self._product_id)
        was_new = self._product_id is None
        dialogs.show_message(
            self, "บันทึกแล้ว",
            "เพิ่มสินค้าเรียบร้อย — เลื่อนลงเพื่อเพิ่มรูปภาพหลายรูป ตัวเลือกสี/สไตล์ และสินค้าเสริมได้" if was_new
            else "บันทึกการแก้ไขเรียบร้อย",
            kind="success",
        )
        self.refresh_shell()
        self.on_show(product_id=new_id)

    def _toggle_active(self):
        active = bool(self._data.get("is_active", 1))
        if active and not dialogs.confirm(
            self, "ปิดขายสินค้า",
            "ผู้ซื้อจะมองไม่เห็นสินค้านี้ (ประวัติออเดอร์ยังอยู่ครบ) ปิดขายใช่ไหม?",
            confirm_text="ปิดขาย", danger=True,
        ):
            return
        ok, _ = self.call(product_service.set_product_active, self._product_id, not active)
        if ok:
            self.on_show(product_id=self._product_id)

    def _soft_delete_product(self):
        if not dialogs.confirm(
            self, "ลบสินค้าแบบเก็บประวัติ",
            "ย้ายสินค้านี้ไปที่รายการสินค้าที่ถูกลบใช่ไหม? (ประวัติยอดขายและออเดอร์เดิมยังอยู่ครบ)",
            confirm_text="ลบเก็บประวัติ", danger=True,
        ):
            return
        ok, _ = self.call(product_service.soft_delete_product, self._product_id)
        if ok:
            self.controller.show("admin_products")

    def _restore_product(self):
        ok, _ = self.call(product_service.restore_product, self._product_id, activate=True)
        if ok:
            self.on_show(product_id=self._product_id)

    def _refresh_data(self):
        ok, data = self.call(product_service.get_product_for_edit, self._product_id)
        if ok:
            self._data = as_dict(data)
        return ok

    # ------------------ T04: การ์ดจัดการรูปภาพหลายรูปของสินค้า + ผูกรูปกับสี/สไตล์ ------------------
    def _build_gallery_card(self):
        for child in self.gallery_card.winfo_children():
            child.destroy()

        images = [as_dict(img) for img in (self._data.get("images") or [])]
        label(self.gallery_card, "รูปภาพภายในสินค้า (T04 — เพิ่มได้หลายรูป & ผูกรูปกับสี/สไตล์)", "h3").pack(
            fill="x", padx=16, pady=(14, 0)
        )
        label(
            self.gallery_card,
            "รูปแรกสุดจะเป็นรูปหลักของการ์ดสินค้าอัตโนมัติ · สามารถระบุสี/สไตล์ของแต่ละรูปเพื่อให้เปลี่ยนรูปตามสีที่ลูกค้าเลือกได้",
            "tiny", muted=True,
        ).pack(fill="x", padx=16, pady=(0, 8))

        for idx, img in enumerate(images):
            row = ctk.CTkFrame(self.gallery_card, fg_color=color("surface_alt"), corner_radius=8)
            row.pack(fill="x", padx=16, pady=3)
            thumb(row, img.get("path"), 50).pack(side="left", padx=8, pady=6)

            info_col = ctk.CTkFrame(row, fg_color="transparent")
            info_col.pack(side="left", fill="x", expand=True, padx=6)
            if idx == 0:
                pill(info_col, "★ รูปหลัก (การ์ดสินค้า)", "primary").pack(side="left", padx=(0, 8))
            else:
                pill(info_col, f"รูปที่ {idx + 1}", "muted").pack(side="left", padx=(0, 8))

            color_tag = img.get("color_value")
            if color_tag:
                pill(info_col, f"สี/สไตล์: {color_tag}", "info").pack(side="left", padx=4)
            else:
                label(info_col, "(ไม่ได้ผูกสีเฉพาะ)", "small", muted=True).pack(side="left", padx=4)

            img_id = img.get("id")
            if img_id and int(img_id) > 0:
                if idx > 0:
                    btn(
                        row, "ตั้งเป็นรูปหลัก",
                        lambda iid=img_id: self._set_primary_img(iid),
                        kind="primary", width=96,
                    ).pack(side="left", padx=2)
                btn(
                    row, "ลบ",
                    lambda iid=img_id: self._delete_gallery_img(iid),
                    kind="danger", width=54,
                ).pack(side="left", padx=(2, 8))

        add_box = ctk.CTkFrame(self.gallery_card, fg_color=color("surface_alt"), corner_radius=10)
        add_box.pack(fill="x", padx=16, pady=(8, 14))
        label(add_box, "เพิ่มรูปภาพใหม่ในแกลเลอรีสินค้า", "body_bold").pack(fill="x", padx=12, pady=(8, 4))

        add_row = ctk.CTkFrame(add_box, fg_color="transparent")
        add_row.pack(fill="x", padx=12, pady=(0, 10))
        self.gallery_picker = ImagePicker(add_row, size=68, allow_clear=True, button_text="เลือกรูปเพิ่ม...")
        self.gallery_picker.pack(side="left", padx=(0, 12))

        right_add = ctk.CTkFrame(add_row, fg_color="transparent")
        right_add.pack(side="left", fill="x", expand=True)
        label(right_add, "ผูกกับสี/สไตล์ (เว้นว่างได้ ถ้าเป็นรูปมุมอื่นทั่วไป):", "small", muted=True).pack(fill="x")
        self.gallery_color_entry = entry(right_add, "เช่น แดง / น้ำเงิน / ขาว-ทอง", width=260, height=34)
        self.gallery_color_entry.pack(side="left", pady=4)
        btn(right_add, "＋ อัปโหลดเพิ่มเข้าแกลเลอรี", self._add_gallery_img, kind="primary", size="sm").pack(
            side="left", padx=8
        )

    def _add_gallery_img(self):
        self.set_error("")
        src = self.gallery_picker.get_selected_file() if self.gallery_picker else None
        if not src:
            self.set_error("กรุณาเลือกไฟล์รูปภาพที่ต้องการเพิ่ม")
            return
        try:
            saved_path = image_utils.save_upload(src, config.PRODUCT_IMAGES_DIR, f"prod_{self._product_id}")
        except ValueError as exc:
            self.set_error(str(exc))
            return
        color_val = self.gallery_color_entry.get().strip() or None
        ok, _ = self.call(
            product_service.add_product_image,
            self._product_id, saved_path, color_value=color_val,
        )
        if ok and self._refresh_data():
            self.picker.set_image(self._data.get("image_path"))
            self._build_gallery_card()
            self.refresh_shell()

    def _set_primary_img(self, image_id: int):
        self.set_error("")
        ok, _ = self.call(product_service.set_primary_product_image, self._product_id, image_id)
        if ok and self._refresh_data():
            self.picker.set_image(self._data.get("image_path"))
            self._build_gallery_card()
            self.refresh_shell()

    def _delete_gallery_img(self, image_id: int):
        if not dialogs.confirm(self, "ลบรูปภาพ", "ต้องการลบรูปภาพนี้ออกจากสินค้าใช่หรือไม่?", danger=True):
            return
        ok, _ = self.call(product_service.delete_product_image, image_id)
        if ok and self._refresh_data():
            self.picker.set_image(self._data.get("image_path"))
            self._build_gallery_card()
            self.refresh_shell()

    # ------------------ T02 & T04: ตัวเลือกสินค้า (สี / สไตล์ / ด้าม / เอ็น / ไซซ์ / ความเร็วลูก) ------------------
    def _build_options_card(self):
        for child in self.opt_card.winfo_children():
            child.destroy()
        options = self._data.get("options") or []
        label(self.opt_card, "ตัวเลือกสินค้า (สี / สไตล์ / ด้าม / เอ็น / ไซซ์ / ความเร็วลูก)", "h3").pack(
            fill="x", padx=16, pady=(14, 0)
        )
        label(
            self.opt_card,
            "ถ้ามีตัวเลือก สต็อกสินค้ารวมจะคำนวณจากตัวเลือกให้อัตโนมัติ · สามารถเลือกค่าจากที่ตั้งไว้ในหมวดหมู่ หรือพิมพ์เองก็ได้",
            "tiny", muted=True, wraplength=720, justify="left",
        ).pack(fill="x", padx=16, pady=(0, 6))

        if not options:
            label(self.opt_card, "ยังไม่มีตัวเลือก (สินค้าชิ้นเดียวใช้สต็อกด้านบนได้เลย)", "small", muted=True).pack(
                fill="x", padx=16, pady=6)
        for opt in options:
            self._option_row(as_dict(opt))

        form = ctk.CTkFrame(self.opt_card, fg_color=color("surface_alt"), corner_radius=10)
        form.pack(fill="x", padx=16, pady=(8, 14))
        editing = self._option_edit_id is not None
        label(form, "แก้ไขตัวเลือก" if editing else "เพิ่มตัวเลือกใหม่", "body_bold").pack(fill="x", padx=12, pady=(8, 2))

        # แถวตัวช่วยดึงค่าตัวเลือกที่ Owner ตั้งไว้ในหมวดหมู่นี้ (เช่น สี, ไซซ์, ความเร็วลูก 74-77)
        cat_groups = []
        try:
            cat_groups = product_service.list_category_option_groups(
                category_id=self._data.get("category_id"), include_inactive=False
            )
        except Exception:  # noqa: BLE001
            cat_groups = []

        preset_values = []
        for g in cat_groups:
            if g.get("key") in ("weight_class", "balance", "flex", "level"):
                continue
            for v in g.get("values") or []:
                preset_values.append(f"{g.get('label')}: {v.get('value')}")

        if preset_values:
            preset_row = ctk.CTkFrame(form, fg_color="transparent")
            preset_row.pack(fill="x", padx=12, pady=(0, 4))
            label(preset_row, "เลือกเร็วจากค่าที่ตั้งไว้ในหมวดหมู่:", "tiny", muted=True).pack(side="left", padx=(0, 6))
            preset_var = ctk.StringVar(value="- เลือกค่าที่ตั้งไว้ -")

            def _apply_preset(choice: str):
                if ":" not in choice or choice.startswith("-"):
                    return
                grp_lbl, val_txt = choice.split(":", 1)
                val_txt = val_txt.strip()
                self.opt_value.delete(0, "end")
                self.opt_value.insert(0, val_txt)
                if "สี" in grp_lbl:
                    self.opt_type.set("สี")
                elif "ไซซ์" in grp_lbl or "ขนาด" in grp_lbl:
                    self.opt_type.set("ไซซ์")
                elif "ความเร็ว" in grp_lbl or "สปีด" in grp_lbl:
                    self.opt_type.set("ความเร็ว")

            option_menu(
                preset_row, ["- เลือกค่าที่ตั้งไว้ -"] + preset_values,
                preset_var, command=_apply_preset, width=260, height=30,
            ).pack(side="left")

        line = ctk.CTkFrame(form, fg_color="transparent")
        line.pack(fill="x", padx=8, pady=(0, 10))
        current = next((as_dict(o) for o in options if as_dict(o).get("id") == self._option_edit_id), {})
        allowed_opt_types = product_service.get_allowed_option_types()
        self.opt_type = ctk.StringVar(value=current.get("option_type") or allowed_opt_types[0])
        option_menu(line, allowed_opt_types, self.opt_type, width=115).pack(side="left", padx=4)
        self.opt_value = entry(line, "ชื่อตัวเลือก เช่น แดง / ขาว-ทอง / 42 / XL / สปีด 75", width=230)
        self.opt_value.pack(side="left", padx=4)
        self.opt_extra = entry(line, "ราคาเพิ่ม", width=90)
        self.opt_extra.pack(side="left", padx=4)
        self.opt_stock = entry(line, "สต็อก", width=70)
        self.opt_stock.pack(side="left", padx=4)
        if editing:
            self.opt_value.insert(0, current.get("option_value") or "")
            self.opt_extra.insert(0, f"{current.get('extra_price') or 0:g}")
            self.opt_stock.insert(0, str(current.get("stock") or 0))
        btn(line, "บันทึก" if editing else "➕ เพิ่ม", self._save_option, kind="primary", width=80).pack(side="left", padx=4)
        if editing:
            btn(line, "ยกเลิก", self._cancel_option_edit, kind="outline", width=70).pack(side="left")

    def _option_row(self, o):
        row = ctk.CTkFrame(self.opt_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=2)
        pill(row, o.get("option_type") or "-", "info").pack(side="left")
        ctk.CTkLabel(row, text=o.get("option_value") or "-", font=font("body"), anchor="w").pack(
            side="left", padx=10, fill="x", expand=True)
        extra = float(o.get("extra_price") or 0)
        if extra:
            label(row, f"+{format_price(extra)}", "small", muted=True).pack(side="left", padx=8)
        stock = int(o.get("stock") or 0)
        ctk.CTkLabel(row, text="หมด" if stock == 0 else f"สต็อก {stock}", font=font("small_bold"), width=80,
                     text_color=color("danger") if stock == 0 else color("text")).pack(side="left", padx=8)
        btn(row, "แก้ไข", lambda oid=o.get("id"): self._start_option_edit(oid), kind="outline", width=60).pack(
            side="left", padx=2)
        btn(row, "ลบ", lambda opt=o: self._delete_option(opt), kind="danger", width=50).pack(side="left", padx=2)

    def _start_option_edit(self, option_id):
        self._option_edit_id = option_id
        self._build_options_card()

    def _cancel_option_edit(self):
        self._option_edit_id = None
        self._build_options_card()

    def _save_option(self):
        self.set_error("")
        value = self.opt_value.get().strip()
        try:
            if not value:
                raise ValueError("กรุณากรอกชื่อตัวเลือก")
            extra = parse_money(self.opt_extra.get(), "ราคาเพิ่ม") or 0.0
            stock = parse_int(self.opt_stock.get(), "สต็อก", required=False) or 0
        except ValueError as exc:
            self.set_error(str(exc))
            return
        ok, _ = self.call(product_service.save_option, self._product_id, self.opt_type.get(), value, extra, stock,
                          option_id=self._option_edit_id)
        if ok:
            self._option_edit_id = None
            self._after_option_change()

    def _delete_option(self, o):
        if not dialogs.confirm(self, "ลบตัวเลือก", f"ลบตัวเลือก “{o.get('option_type')}: {o.get('option_value')}” ใช่ไหม?",
                               confirm_text="ลบ", danger=True):
            return
        self.set_error("")
        ok, _ = self.call(product_service.delete_option, o.get("id"))
        if ok:
            self._after_option_change()

    def _after_option_change(self):
        if self._refresh_data():
            self._build_options_card()
            self._sync_stock_entry()
            self._build_addons_card()
            self.refresh_shell()

    @staticmethod
    def _addon_id(a):
        return a.get("id") if a.get("id") is not None else a.get("addon_product_id")

    def _build_addons_card(self):
        for child in self.addon_card.winfo_children():
            child.destroy()
        addons = [as_dict(a) for a in (self._data.get("addons") or [])]
        label(self.addon_card, "สินค้าเสริมขายคู่ (แสดงเป็น \"ซื้อคู่กัน\" ในหน้าสินค้า)", "h3").pack(
            fill="x", padx=16, pady=(14, 4))
        if not addons:
            label(self.addon_card, "ยังไม่มีสินค้าเสริม", "small", muted=True).pack(fill="x", padx=16, pady=4)
        for a in addons:
            row = ctk.CTkFrame(self.addon_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(row, text=a.get("name") or a.get("addon_name") or "-", font=font("body"), anchor="w").pack(
                side="left", fill="x", expand=True)
            price = a.get("effective_price", a.get("price"))
            if price is not None:
                label(row, format_price(price), "small", muted=True).pack(side="left", padx=8)
            btn(row, "✕ เอาออก", lambda aid=self._addon_id(a): self._remove_addon(aid), kind="outline", width=80).pack(
                side="left")

        label(self.addon_card, "เพิ่มสินค้าเสริม: ค้นหาแล้วกด เพิ่ม", "small", muted=True).pack(
            fill="x", padx=16, pady=(10, 2))
        SearchBar(self.addon_card, command=self._search_addons, placeholder="ค้นหาชื่อสินค้า", width=300, height=36).pack(
            anchor="w", padx=16)
        self.addon_results = ctk.CTkFrame(self.addon_card, fg_color="transparent")
        self.addon_results.pack(fill="x", padx=16, pady=(4, 14))
        label(self.addon_results, "", "tiny").pack()

    def _addon_ids(self):
        return [self._addon_id(as_dict(a)) for a in (self._data.get("addons") or [])]

    def _search_addons(self, text):
        for child in self.addon_results.winfo_children():
            child.destroy()
        text = (text or "").strip()
        if not text:
            label(self.addon_results, "", "tiny").pack()
            return
        ok, result = self.call(product_service.list_products_admin, search=text, page=1, page_size=6,
                               show_inactive=False)
        items = as_dict(result).get("items") or [] if ok else []
        current = set(self._addon_ids())
        shown = 0
        for item in items:
            p = as_dict(item)
            if p.get("id") == self._product_id or p.get("id") in current:
                continue
            shown += 1
            row = ctk.CTkFrame(self.addon_results, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=p.get("name", "-"), font=font("body"), anchor="w").pack(
                side="left", fill="x", expand=True)
            label(row, format_price(p.get("effective_price", p.get("price"))), "small", muted=True).pack(
                side="left", padx=8)
            btn(row, "เพิ่ม", lambda pid=p.get("id"): self._add_addon(pid), kind="primary", width=60).pack(side="left")
        if not shown:
            label(self.addon_results, "ไม่พบสินค้าที่เพิ่มได้", "small", muted=True).pack(anchor="w")

    def _add_addon(self, addon_id):
        self._save_addons(self._addon_ids() + [addon_id])

    def _remove_addon(self, addon_id):
        self._save_addons([i for i in self._addon_ids() if i != addon_id])

    def _save_addons(self, ids):
        self.set_error("")
        ok, _ = self.call(product_service.set_addons, self._product_id, ids)
        if ok and self._refresh_data():
            self._build_addons_card()
