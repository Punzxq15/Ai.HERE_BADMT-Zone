"""
ui/pages/admin/categories.py
จัดการหมวดหมู่ + แบรนด์ + ชุดตัวเลือกของหมวดหมู่ (เจ้าของร้านเท่านั้น — ปรับปรุงตามข้อ 10 และ T02):
- T02: เพิ่มแท็บและแผงจัดการ "ตัวเลือกของหมวดหมู่" ให้ Owner ตั้งค่าเพิ่ม/แก้ไข/เรียงลำดับ/ปิดใช้งานค่าต่างๆ ได้เอง:
  * หมวดหมู่ไม้แบดมินตัน: น้ำหนักไม้ (เพิ่ม 3U 4U 5U ... 10U ได้จาก Owner เท่านั้น), จุดสมดุล/ความหนักหัว (Balance),
    ความแข็งก้าน (Shaft Flexibility), ระดับผู้เล่น (Skill Level), สีไม้แบด, ขนาดด้าม, การปรับแต่งไม้
  * หมวดหมู่อื่นๆ: ความเร็วลูกแบด (74, 75, 76, 77), ขนาดไซซ์เสื้อ/กางเกง, ขนาดไซซ์รองเท้า, สี/สไตล์กระเป๋า ฯลฯ
- ฟังก์ชันเพิ่ม/แก้ไข/ปิด/ลบ/กู้คืนหมวดหมู่และแบรนด์ และการผูกแบรนด์กับหมวดหมู่ คงเดิมทั้งหมด
"""

import customtkinter as ctk

import config
from services import product_service
from ui.components import dialogs
from ui.components.image_picker import ImagePicker
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, empty_state, entry, font, label, option_menu, page_header, pill, segmented, thumb,
)
from ui.theme import ON_PRIMARY
from utils import image_utils

TAB_CATEGORY = "หมวดหมู่สินค้า"
TAB_BRAND = "แบรนด์สินค้า"
TAB_OPTIONS = "ตัวเลือกของหมวดหมู่ (3U-10U / สปีด / ไซซ์ / สี)"


class _CategoryPanel(ctk.CTkFrame):
    def __init__(self, parent, page):
        super().__init__(parent, fg_color="transparent")
        self.page = page
        self._edit = None
        self._brand_vars = {}
        self._bind_all_var = ctk.BooleanVar(value=True)

        self.form = card(self)
        self.form.pack(fill="x")
        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="x", pady=(6, 0))
        self._build_form()

    def _build_form(self, item=None):
        self._edit = item
        self._brand_vars.clear()
        for child in self.form.winfo_children():
            child.destroy()

        label(self.form, f"แก้ไขหมวดหมู่: {item.get('name')}" if item else "เพิ่มหมวดหมู่ใหม่", "h3").pack(
            fill="x", padx=12, pady=(8, 2))

        row = ctk.CTkFrame(self.form, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 6))
        self.picker = ImagePicker(row, size=68, initial_path=item.get("image_path") if item else None, allow_clear=False)
        self.picker.pack(side="left", padx=(2, 10))

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True)
        label(right, "ชื่อหมวดหมู่ *", "small", muted=True).pack(fill="x")
        self.name_entry = entry(right, "เช่น ไม้แบดมินตัน / รองเท้าแบดมินตัน", height=34)
        self.name_entry.pack(fill="x")
        if item:
            self.name_entry.insert(0, item.get("name") or "")
        self.name_entry.bind("<Return>", lambda _e: self._save())

        bind_box = ctk.CTkFrame(right, fg_color=color("surface_alt"), corner_radius=8)
        bind_box.pack(fill="x", pady=(4, 2))
        bind_all_init = bool(item.get("bind_all_brands", 1)) if item else True
        self._bind_all_var.set(bind_all_init)

        ctk.CTkSwitch(
            bind_box, text="ผูกกับทุกแบรนด์ในร้าน (ค่าเริ่มต้น)",
            variable=self._bind_all_var, command=self._toggle_brand_checks,
            font=font("small_bold"), progress_color=color("primary"),
        ).pack(anchor="w", padx=10, pady=(4, 2))

        self.brands_holder = ctk.CTkFrame(bind_box, fg_color="transparent")
        self.brands_holder.pack(fill="x", padx=10, pady=(0, 4))

        ok_b, all_brands = self.page.call(product_service.list_brands, include_inactive=True)
        selected_ids = set(item.get("brand_ids") or []) if item else set()
        for idx, b in enumerate(all_brands if ok_b else []):
            bd = as_dict(b)
            bid = bd.get("id")
            var = ctk.BooleanVar(value=(bid in selected_ids))
            self._brand_vars[bid] = var
            cb = ctk.CTkCheckBox(
                self.brands_holder, text=bd.get("name") or "-", variable=var,
                font=font("small"), fg_color=color("primary"), checkmark_color=ON_PRIMARY,
                height=22,
            )
            cb.grid(row=idx // 5, column=idx % 5, sticky="w", padx=6, pady=1)
        self._toggle_brand_checks()

        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.pack(fill="x", pady=(4, 0))
        btn(btns, "บันทึกหมวดหมู่", self._save, kind="primary", size="sm").pack(side="left")
        if item:
            btn(btns, "ยกเลิกการแก้ไข", lambda: self._build_form(None), kind="outline", size="sm").pack(
                side="left", padx=6)
            btn(
                btns, "⚙️ ตั้งค่าตัวเลือกในหมวดหมู่นี้",
                lambda cid=item.get("id"): self.page.open_options_for_category(cid),
                kind="info", size="sm",
            ).pack(side="left", padx=6)

    def _toggle_brand_checks(self):
        state = "disabled" if self._bind_all_var.get() else "normal"
        for child in self.brands_holder.winfo_children():
            try:
                child.configure(state=state)
            except Exception:  # noqa: BLE001
                pass

    def _save(self):
        self.page.set_error("")
        name = self.name_entry.get().strip()
        if not name:
            self.page.set_error("กรุณากรอกชื่อหมวดหมู่")
            return
        bind_all = bool(self._bind_all_var.get())
        brand_ids = [bid for bid, var in self._brand_vars.items() if var.get()]
        if not bind_all and not brand_ids:
            self.page.set_error("กรุณาเลือกอย่างน้อย 1 แบรนด์ หรือเปิดสวิตช์ 'ผูกกับทุกแบรนด์ในร้าน'")
            return
        image_path = None
        if self.picker.has_change() and self.picker.get_selected_file():
            try:
                image_path = image_utils.save_upload(self.picker.get_selected_file(), config.CATEGORY_IMAGES_DIR, "category")
            except ValueError as exc:
                self.page.set_error(str(exc))
                return
        item_id = self._edit.get("id") if self._edit else None
        ok, _ = self.page.call(
            product_service.save_category, name, category_id=item_id, image_path=image_path,
            bind_all_brands=bind_all, brand_ids=brand_ids,
        )
        if ok:
            self._build_form(None)
            self.reload()

    def reload(self):
        ok, rows = self.page.call(product_service.list_categories, include_inactive=True, include_deleted=True)
        for child in self.list_frame.winfo_children():
            child.destroy()
        rows = [as_dict(r) for r in (rows if ok else [])]
        if not rows:
            empty_state(self.list_frame, "ยังไม่มีหมวดหมู่")
        for item in rows:
            self._row(item)

    def _row(self, item):
        row = card(self.list_frame)
        row.pack(fill="x", pady=1)
        thumb(row, item.get("image_path"), 38).pack(side="left", padx=8, pady=5)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=4, pady=3)
        ctk.CTkLabel(info, text=item.get("name", "-"), font=font("body_bold"), anchor="w").pack(anchor="w")
        bind_txt = "ผูกทุกแบรนด์" if item.get("bind_all_brands", 1) else f"ผูกเฉพาะ {len(item.get('brand_ids') or [])} แบรนด์"
        prod_cnt = int(item.get("product_count") or item.get("active_product_count") or 0)
        label(info, f"{bind_txt} · สินค้าในหมวด {prod_cnt} รายการ", "tiny", muted=True).pack(anchor="w")

        deleted = bool(item.get("deleted_at"))
        active = bool(item.get("is_active", 1)) and not deleted
        if deleted:
            pill(row, "ถูกลบ (เก็บประวัติ)", "danger").pack(side="left", padx=4)
            btn(row, "กู้คืน", lambda it=item: self._restore(it), kind="success", width=72).pack(side="left", padx=(2, 8))
            return

        pill(row, "เปิดใช้งาน" if active else "ปิดอยู่", "success" if active else "muted").pack(side="left", padx=4)
        btn(
            row, "ตั้งค่าตัวเลือก",
            lambda cid=item.get("id"): self.page.open_options_for_category(cid),
            kind="info", width=96,
        ).pack(side="left", padx=2)
        btn(row, "แก้ไข", lambda it=item: self._build_form(it), kind="outline", width=56).pack(side="left", padx=2)
        btn(row, "ปิด" if active else "เปิด", lambda it=item: self._toggle(it),
            kind="warning" if active else "success", width=54).pack(side="left", padx=2)
        btn(row, "ลบ", lambda it=item: self._delete(it), kind="danger", width=54).pack(side="left", padx=(2, 8))

    def _toggle(self, item):
        active = bool(item.get("is_active", 1))
        ok, _ = self.page.call(product_service.set_category_active, item.get("id"), not active)
        if ok:
            self.reload()

    def _delete(self, item):
        cnt = int(item.get("product_count") or item.get("active_product_count") or 0)
        msg = f"ต้องการลบหมวดหมู่ “{item.get('name')}” ใช่หรือไม่?"
        if cnt > 0:
            msg += f"\n\nมีสินค้าที่เปิดขายอยู่ในหมวดหมู่นี้ {cnt} รายการ หากยืนยัน ระบบจะปิดการแสดงผลสินค้าเหล่านั้นอย่างปลอดภัยโดยไม่ลบประวัติออเดอร์"
        if not dialogs.confirm(self, "ยืนยันการลบหมวดหมู่", msg, confirm_text="ยืนยันลบ", danger=True):
            return
        ok, _ = self.page.call(product_service.delete_category, item.get("id"), force_deactivate_products=True)
        if ok:
            self.reload()

    def _restore(self, item):
        ok, _ = self.page.call(product_service.restore_category, item.get("id"))
        if ok:
            self.reload()


class _BrandPanel(ctk.CTkFrame):
    def __init__(self, parent, page):
        super().__init__(parent, fg_color="transparent")
        self.page = page
        self._edit = None

        self.form = card(self)
        self.form.pack(fill="x")
        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="x", pady=(6, 0))
        self._build_form()

    def _build_form(self, item=None):
        self._edit = item
        for child in self.form.winfo_children():
            child.destroy()
        label(self.form, f"แก้ไขแบรนด์: {item.get('name')} (โลโก้ 1:1)" if item else "เพิ่มแบรนด์ใหม่ (โลโก้แบรนด์อัตราส่วน 1:1)", "h3").pack(
            fill="x", padx=12, pady=(8, 2))
        row = ctk.CTkFrame(self.form, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 8))
        self.picker = ImagePicker(row, size=68, initial_path=item.get("logo_path") if item else None, allow_clear=False)
        self.picker.pack(side="left", padx=(2, 10))
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True)
        label(right, "ชื่อแบรนด์ * (อัปโหลดรูปโลโก้แบรนด์อัตราส่วน 1:1 ด้านซ้าย)", "small", muted=True).pack(fill="x")
        self.name_entry = entry(right, "เช่น Yonex / Victor / Li-Ning", height=34)
        self.name_entry.pack(fill="x")
        if item:
            self.name_entry.insert(0, item.get("name") or "")
        self.name_entry.bind("<Return>", lambda _e: self._save())
        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.pack(fill="x", pady=(5, 0))
        btn(btns, "บันทึกแบรนด์", self._save, kind="primary", size="sm").pack(side="left")
        if item:
            btn(btns, "ยกเลิกการแก้ไข", lambda: self._build_form(None), kind="outline", size="sm").pack(
                side="left", padx=6)

    def _save(self):
        self.page.set_error("")
        name = self.name_entry.get().strip()
        if not name:
            self.page.set_error("กรุณากรอกชื่อแบรนด์")
            return
        logo_path = None
        if self.picker.has_change() and self.picker.get_selected_file():
            try:
                logo_path = image_utils.save_upload(self.picker.get_selected_file(), config.CATEGORY_IMAGES_DIR, "brand")
            except ValueError as exc:
                self.page.set_error(str(exc))
                return
        item_id = self._edit.get("id") if self._edit else None
        ok, _ = self.page.call(product_service.save_brand, name, brand_id=item_id, logo_path=logo_path)
        if ok:
            self._build_form(None)
            self.reload()

    def reload(self):
        ok, rows = self.page.call(product_service.list_brands, include_inactive=True, include_deleted=True)
        for child in self.list_frame.winfo_children():
            child.destroy()
        rows = [as_dict(r) for r in (rows if ok else [])]
        if not rows:
            empty_state(self.list_frame, "ยังไม่มีแบรนด์")
        for item in rows:
            self._row(item)

    def _row(self, item):
        row = card(self.list_frame)
        row.pack(fill="x", pady=1)
        thumb(row, item.get("logo_path"), 38).pack(side="left", padx=8, pady=5)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=4, pady=3)
        ctk.CTkLabel(info, text=item.get("name", "-"), font=font("body_bold"), anchor="w").pack(anchor="w")
        prod_cnt = int(item.get("product_count") or item.get("active_product_count") or 0)
        label(info, f"โลโก้ 1:1 · สินค้าในแบรนด์ {prod_cnt} รายการ", "tiny", muted=True).pack(anchor="w")

        deleted = bool(item.get("deleted_at"))
        active = bool(item.get("is_active", 1)) and not deleted
        if deleted:
            pill(row, "ถูกลบ (เก็บประวัติ)", "danger").pack(side="left", padx=4)
            btn(row, "กู้คืน", lambda it=item: self._restore(it), kind="success", width=72).pack(side="left", padx=(2, 8))
            return

        pill(row, "เปิดใช้งาน" if active else "ปิดอยู่", "success" if active else "muted").pack(side="left", padx=4)
        btn(row, "แก้ไข", lambda it=item: self._build_form(it), kind="outline", width=56).pack(side="left", padx=2)
        btn(row, "ปิด" if active else "เปิด", lambda it=item: self._toggle(it),
            kind="warning" if active else "success", width=54).pack(side="left", padx=2)
        btn(row, "ลบ", lambda it=item: self._delete(it), kind="danger", width=54).pack(side="left", padx=(2, 8))

    def _toggle(self, item):
        active = bool(item.get("is_active", 1))
        ok, _ = self.page.call(product_service.set_brand_active, item.get("id"), not active)
        if ok:
            self.reload()

    def _delete(self, item):
        cnt = int(item.get("product_count") or item.get("active_product_count") or 0)
        msg = f"ต้องการลบแบรนด์ “{item.get('name')}” ใช่หรือไม่?"
        if cnt > 0:
            msg += f"\n\nมีสินค้าที่เปิดขายอยู่ในแบรนด์นี้ {cnt} รายการ หากยืนยัน ระบบจะปิดการแสดงผลสินค้าเหล่านั้นอย่างปลอดภัยโดยไม่ลบประวัติออเดอร์"
        if not dialogs.confirm(self, "ยืนยันการลบแบรนด์", msg, confirm_text="ยืนยันลบ", danger=True):
            return
        ok, _ = self.page.call(product_service.delete_brand, item.get("id"), force_deactivate_products=True)
        if ok:
            self.reload()

    def _restore(self, item):
        ok, _ = self.page.call(product_service.restore_brand, item.get("id"))
        if ok:
            self.reload()


class _CategoryOptionsPanel(ctk.CTkFrame):
    """
    T02: แผงจัดการชุดตัวเลือกของหมวดหมู่สินค้า (Owner เท่านั้น):
    - เลือกหมวดหมู่ (เช่น ไม้แบดมินตัน, ลูกแบดมินตัน, รองเท้า, เสื้อผ้า, กระเป๋า ฯลฯ)
    - เพิ่มชุดตัวเลือกใหม่ในหมวดหมู่ (เช่น น้ำหนักไม้, ความหนักหัว, ความแข็งก้าน, Skill Level, ความเร็วลูก 74-77, ไซซ์, สี/สไตล์)
    - เพิ่ม / แก้ไข / เรียงลำดับ / เปิด-ปิดใช้งาน ค่าตัวเลือก (เช่น เพิ่ม 3U 4U 5U ... 10U)
    """

    def __init__(self, parent, page):
        super().__init__(parent, fg_color="transparent")
        self.page = page
        self._cat_map = {}
        self._id_to_cat_name = {}
        self._selected_cat_id = None

        # แถบเลือกหมวดหมู่ + ปุ่มลัดเพิ่ม 3U-10U
        top_card = card(self)
        top_card.pack(fill="x", pady=(0, 8))
        top_row = ctk.CTkFrame(top_card, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=10)

        label(top_row, "เลือกหมวดหมู่ที่ต้องการตั้งค่าตัวเลือก:", "body_bold").pack(side="left", padx=(0, 8))
        self.cat_var = ctk.StringVar(value="")
        self.cat_menu = option_menu(top_row, ["-"], self.cat_var, command=self._on_pick_category, width=220)
        self.cat_menu.pack(side="left", padx=(0, 10))

        self.quick_racket_btn = btn(
            top_row,
            "⚡ เพิ่มน้ำหนักไม้ 3U–10U ครบชุด",
            self._quick_add_3u_to_10u,
            kind="primary",
            size="sm",
        )
        self.quick_racket_btn.pack(side="left", padx=4)

        # ฟอร์มเพิ่มชุดตัวเลือกใหม่ให้หมวดหมู่ที่เลือก
        grp_form = ctk.CTkFrame(top_card, fg_color=color("surface_alt"), corner_radius=8)
        grp_form.pack(fill="x", padx=14, pady=(0, 10))
        gf_row = ctk.CTkFrame(grp_form, fg_color="transparent")
        gf_row.pack(fill="x", padx=10, pady=8)

        label(gf_row, "เพิ่มหัวข้อตัวเลือกใหม่ในหมวดนี้:", "small_bold").pack(side="left", padx=(0, 6))
        self.new_grp_key = entry(gf_row, "รหัส เช่น weight_class / size / color / speed", width=210, height=32)
        self.new_grp_key.pack(side="left", padx=4)
        self.new_grp_label = entry(gf_row, "ชื่อหัวข้อ เช่น น้ำหนักไม้ / ขนาดไซซ์ / สี", width=240, height=32)
        self.new_grp_label.pack(side="left", padx=4)
        btn(gf_row, "＋ เพิ่มชุดตัวเลือก", self._add_option_group, kind="info", size="sm").pack(side="left", padx=6)

        self.groups_holder = ctk.CTkFrame(self, fg_color="transparent")
        self.groups_holder.pack(fill="x")

    def select_category_id(self, category_id: int):
        self._selected_cat_id = int(category_id) if category_id is not None else None
        self.reload()

    def reload(self):
        ok, cats = self.page.call(product_service.list_categories, include_inactive=True)
        cats = [as_dict(c) for c in (cats if ok else []) if not as_dict(c).get("deleted_at")]
        self._cat_map = {c["name"]: c["id"] for c in cats}
        self._id_to_cat_name = {c["id"]: c["name"] for c in cats}
        names = list(self._cat_map.keys())
        if not names:
            self.cat_menu.configure(values=["-"])
            return

        if self._selected_cat_id in self._id_to_cat_name:
            target_name = self._id_to_cat_name[self._selected_cat_id]
        else:
            target_name = next((n for n in names if "ไม้แบด" in n), names[0])
            self._selected_cat_id = self._cat_map[target_name]

        self.cat_menu.configure(values=names)
        self.cat_var.set(target_name)
        self._render_groups()

    def _on_pick_category(self, cat_name: str):
        self._selected_cat_id = self._cat_map.get(cat_name)
        self._render_groups()

    def _quick_add_3u_to_10u(self):
        self.page.set_error("")
        ok, _ = self.page.call(product_service.quick_add_racket_weights, self._selected_cat_id)
        if ok:
            self._render_groups()
            dialogs.show_message(
                self, "เพิ่มน้ำหนักไม้สำเร็จ",
                "เพิ่มตัวเลือกน้ำหนักไม้ 3U, 4U, 5U, 6U, 7U, 8U, 9U, 10U เข้าหมวดหมู่เรียบร้อยแล้ว",
                kind="success",
            )

    def _add_option_group(self):
        self.page.set_error("")
        if not self._selected_cat_id:
            self.page.set_error("กรุณาเลือกหมวดหมู่ก่อน")
            return
        k = self.new_grp_key.get().strip()
        lbl = self.new_grp_label.get().strip()
        ok, _ = self.page.call(
            product_service.save_category_option_group,
            self._selected_cat_id, k, lbl,
        )
        if ok:
            self.new_grp_key.delete(0, "end")
            self.new_grp_label.delete(0, "end")
            self._render_groups()

    def _render_groups(self):
        for child in self.groups_holder.winfo_children():
            child.destroy()
        if not self._selected_cat_id:
            return

        cat_name = self._id_to_cat_name.get(self._selected_cat_id, "")
        if "ไม้แบด" in cat_name:
            self.quick_racket_btn.pack(side="left", padx=4)
        else:
            self.quick_racket_btn.pack_forget()

        ok, groups = self.page.call(
            product_service.list_category_option_groups,
            category_id=self._selected_cat_id,
            include_inactive=True,
        )
        groups = [as_dict(g) for g in (groups if ok else [])]
        if not groups:
            empty_state(self.groups_holder, "หมวดหมู่นี้ยังไม่มีชุดตัวเลือก — สามารถเพิ่มชุดตัวเลือกด้านบนได้เลย")
            return

        for g in groups:
            self._build_group_card(g)

    def _build_group_card(self, g: dict):
        g_card = card(self.groups_holder)
        g_card.pack(fill="x", pady=5)

        hdr = ctk.CTkFrame(g_card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 4))

        active = bool(g.get("is_active", 1))
        ctk.CTkLabel(
            hdr,
            text=f"{g.get('label')}  (key: {g.get('key')})",
            font=font("h3"),
            text_color=color("text_main"),
        ).pack(side="left")

        pill(hdr, "เปิดใช้งาน" if active else "ปิดใช้งาน", "success" if active else "muted").pack(side="left", padx=8)
        btn(
            hdr,
            "ปิดชุดนี้" if active else "เปิดชุดนี้",
            lambda gid=g["id"]: self._toggle_group(gid),
            kind="warning" if active else "success",
            width=82,
        ).pack(side="right")

        # รายการค่าตัวเลือกในชุดนี้
        vals = g.get("values") or []
        vals_wrap = ctk.CTkFrame(g_card, fg_color=color("surface_alt"), corner_radius=8)
        vals_wrap.pack(fill="x", padx=14, pady=4)

        if not vals:
            label(vals_wrap, "ยังไม่มีค่าตัวเลือกในหมวดนี้", "small", muted=True).pack(padx=12, pady=8, anchor="w")
        else:
            for idx, v in enumerate(vals):
                v_row = ctk.CTkFrame(vals_wrap, fg_color="transparent")
                v_row.pack(fill="x", padx=10, pady=2)
                v_active = bool(v.get("is_active", 1))
                pill(v_row, v.get("value") or "-", "primary" if v_active else "muted").pack(side="left", padx=(0, 8))
                ctk.CTkLabel(
                    v_row,
                    text=v.get("label") or v.get("value") or "-",
                    font=font("body_bold" if v_active else "body"),
                    text_color=color("text_main" if v_active else "text_muted"),
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

                if idx > 0:
                    btn(
                        v_row, "↑",
                        lambda gid=g["id"], v_list=vals, i=idx: self._move_value(gid, v_list, i, -1),
                        kind="outline", width=32,
                    ).pack(side="left", padx=2)
                if idx < len(vals) - 1:
                    btn(
                        v_row, "↓",
                        lambda gid=g["id"], v_list=vals, i=idx: self._move_value(gid, v_list, i, 1),
                        kind="outline", width=32,
                    ).pack(side="left", padx=2)

                btn(
                    v_row,
                    "ปิดใช้" if v_active else "เปิดใช้",
                    lambda vid=v["id"]: self._toggle_value(vid),
                    kind="danger" if v_active else "success",
                    width=64,
                ).pack(side="left", padx=2)

        # แถวเพิ่มค่าตัวเลือกใหม่ในชุดนี้
        add_row = ctk.CTkFrame(g_card, fg_color="transparent")
        add_row.pack(fill="x", padx=14, pady=(4, 10))
        v_entry = entry(add_row, "ค่าตัวเลือก เช่น 5U / 6U / Head Heavy / Medium-Stiff / 75 / XL", width=260, height=32)
        v_entry.pack(side="left", padx=(0, 6))
        l_entry = entry(add_row, "คำอธิบายแสดงผล (เว้นว่าง = ใช้ค่าเดียวกัน)", width=240, height=32)
        l_entry.pack(side="left", padx=(0, 6))

        def _do_add_val(gid=g["id"], ve=v_entry, le=l_entry):
            self.page.set_error("")
            ok, _ = self.page.call(
                product_service.save_category_option_value,
                gid, ve.get().strip(), label=le.get().strip() or None,
            )
            if ok:
                ve.delete(0, "end")
                le.delete(0, "end")
                self._render_groups()

        v_entry.bind("<Return>", lambda _e, fn=_do_add_val: fn())
        btn(add_row, "＋ เพิ่มค่าตัวเลือก", _do_add_val, kind="primary", size="sm").pack(side="left")

    def _toggle_group(self, group_id: int):
        ok, _ = self.page.call(product_service.toggle_category_option_group, group_id)
        if ok:
            self._render_groups()

    def _toggle_value(self, value_id: int):
        ok, _ = self.page.call(product_service.toggle_category_option_value, value_id)
        if ok:
            self._render_groups()

    def _move_value(self, group_id: int, vals: list[dict], index: int, delta: int):
        ids = [int(v["id"]) for v in vals]
        new_idx = index + delta
        if 0 <= new_idx < len(ids):
            ids[index], ids[new_idx] = ids[new_idx], ids[index]
            ok, _ = self.page.call(product_service.reorder_category_option_values, group_id, ids)
            if ok:
                self._render_groups()


class AdminCategoriesPage(AdminPage):
    OWNER_ONLY = True

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        page_header(
            self.content, "หมวดหมู่ / แบรนด์ / ตัวเลือกประจำหมวดหมู่",
            "จัดการหมวดหมู่ โลโก้แบรนด์ (1:1) และตั้งค่าตัวเลือกประจำหมวดหมู่ (เช่น 3U–10U, ความเร็วลูกแบด, ไซซ์, สี) — เฉพาะเจ้าของร้าน",
        )
        self.tabs = segmented(
            self.content,
            values=[TAB_CATEGORY, TAB_BRAND, TAB_OPTIONS],
            command=self._switch,
        )
        self.tabs.pack(anchor="w", pady=(2, 8))
        self.holder = ctk.CTkFrame(self.content, fg_color="transparent")
        self.holder.pack(fill="x")

        self.panels = {
            TAB_CATEGORY: _CategoryPanel(self.holder, self),
            TAB_BRAND: _BrandPanel(self.holder, self),
            TAB_OPTIONS: _CategoryOptionsPanel(self.holder, self),
        }
        self._current = TAB_CATEGORY
        self.tabs.set(TAB_CATEGORY)
        self.panels[TAB_CATEGORY].pack(fill="x")

    def open_options_for_category(self, category_id: int):
        self.tabs.set(TAB_OPTIONS)
        self.panels[TAB_OPTIONS].select_category_id(category_id)
        self._switch(TAB_OPTIONS)

    def _switch(self, tab):
        self.set_error("")
        self.panels[self._current].pack_forget()
        self._current = tab
        self.panels[tab].pack(fill="x")
        self.panels[tab].reload()

    def on_show(self, **kwargs):
        if not self.allowed():
            return
        self.set_error("")
        self.panels[self._current].reload()
