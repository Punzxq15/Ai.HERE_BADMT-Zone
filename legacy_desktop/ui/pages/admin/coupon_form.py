"""
ui/pages/admin/coupon_form.py
ฟอร์มเพิ่ม/แก้ไขคูปอง (เจ้าของร้านเท่านั้น — ปรับปรุงตามข้อ 11 + T06, T08) — route `admin_coupon_form` → AdminCouponFormPage
รองรับการกำหนด:
- โค้ดคูปอง
- หมวดหมู่คูปอง (T06: คูปองส่วนลดค่าส่ง / คูปองส่วนลดเป็น % / คูปองส่วนลดเป็น บาท / และอื่นๆ)
- ประเภทส่วนลด (% / จำนวนเงินคงที่ / โค้ดส่งฟรี ส่วนลดค่าจัดส่ง) + มูลค่าส่วนลด + เพดานส่วนลดสูงสุด
- ยอดสั่งซื้อขั้นต่ำเพื่อใช้คูปอง + จำนวนสิทธิ์ทั้งหมด
- วันเริ่มต้นใช้งาน (starts_at) และวันหมดอายุ (expires_at) เลือกจากปฏิทิน DatePickerField (T08)
- ตั้งช่วงเวลารับโค้ด (เช่น 10:00 - 12:00 ของวันนี้ หรือรับได้ทุกวันในช่วงเวลานั้น)
- ตั้งรีโค้ดอัตโนมัติทุกๆ เวลา 12:00 น. ของทุกวัน (ลบโค้ดเก่าที่ไม่ได้รับและแทนที่ด้วยโค้ดใหม่)
- ปุ่มลบคูปอง (ยืนยันก่อนลบ)
"""

from datetime import datetime

import customtkinter as ctk

from core.constants import DISCOUNT_FIXED, DISCOUNT_PERCENT
from services import coupon_service
from ui.components import dialogs
from ui.components.date_picker import DatePickerField
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, entry, font, label, option_menu, page_header,
    parse_int, parse_money,
)
from utils.formatters import format_date_thai

TYPE_FREE_SHIP = "free_shipping"
TYPE_LABELS = {
    DISCOUNT_PERCENT: "เปอร์เซ็นต์ (%)",
    DISCOUNT_FIXED: "จำนวนเงินคงที่ (บาท)",
    TYPE_FREE_SHIP: "ส่งฟรี (ส่วนลดค่าจัดส่ง)",
}
DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")


def parse_expiry(text):
    text = (text or "").strip()
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(text, fmt)
            return text
        except ValueError:
            continue
    raise ValueError("วันที่ต้องอยู่ในรูปแบบ ปี-เดือน-วัน เช่น 2026-12-31 (ปี ค.ศ.)")


def expiry_to_text(value):
    text = str(value or "").strip()
    if text.endswith(" 23:59:59"):
        text = text[:-9]
    if text.endswith(" 00:00:00"):
        text = text[:-9]
    return text


class AdminCouponFormPage(AdminPage):
    OWNER_ONLY = True

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._coupon_id = None
        self._coupon = {}
        self._cat_label_to_key = {}
        self._cat_key_to_label = {}

    def on_show(self, coupon_id=None, **kwargs):
        if not self.allowed():
            return
        self._coupon_id = coupon_id
        self._coupon = {}
        self.set_error("")
        if coupon_id is not None:
            ok, data = self.call(coupon_service.get_coupon, coupon_id)
            if not ok:
                self.clear_content()
                _h, actions = page_header(self.content, "แก้ไขคูปอง")
                btn(actions, "← กลับ", self._back, kind="outline").pack(side="right")
                return
            self._coupon = as_dict(data)
        self._render()

    def _back(self):
        self.controller.go_back(default="admin_coupons")

    def _render(self):
        self.clear_content()
        c = self._coupon
        editing = self._coupon_id is not None
        _h, actions = page_header(
            self.content,
            f"แก้ไขคูปอง {c.get('code') or ''}".strip() if editing else "เพิ่มคูปองใหม่",
            "ตั้งค่าเงื่อนไขส่วนลด หมวดหมู่คูปอง ปฏิทินวันเริ่ม/หมดอายุ และรีโค้ดอัตโนมัติเวลา 12:00 น.",
        )
        btn(actions, "← กลับ", self._back, kind="outline").pack(side="right")
        if editing:
            btn(actions, "ลบคูปองนี้", self._delete_current, kind="danger").pack(side="right", padx=8)

        box = card(self.content)
        box.pack(fill="x")
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        # แถวที่ 0: โค้ดคูปอง + หมวดหมู่คูปอง (T06)
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")
        code_col = ctk.CTkFrame(top_row, fg_color="transparent")
        code_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        label(code_col, "โค้ดคูปอง *", "small", muted=True).pack(fill="x")
        self.code_entry = entry(code_col, "เช่น NEWYEAR50 หรือ FREESHIP (ภาษาอังกฤษ/ตัวเลข 3-20 ตัว)")
        self.code_entry.pack(fill="x")
        if editing:
            self.code_entry.insert(0, c.get("code") or "")

        cat_col = ctk.CTkFrame(top_row, fg_color="transparent")
        cat_col.pack(side="left", fill="x", expand=True, padx=(8, 0))
        label(cat_col, "หมวดหมู่คูปอง (T06) *", "small", muted=True).pack(fill="x")
        cat_pairs = coupon_service.get_coupon_categories()
        self._cat_key_to_label = {k: lbl for k, lbl in cat_pairs}
        self._cat_label_to_key = {lbl: k for k, lbl in cat_pairs}
        init_cat_key = c.get("coupon_category") if editing else "percent"
        init_cat_lbl = self._cat_key_to_label.get(init_cat_key, cat_pairs[0][1])
        self.cat_var = ctk.StringVar(value=init_cat_lbl)
        option_menu(cat_col, list(self._cat_label_to_key.keys()), self.cat_var, width=240).pack(anchor="w")

        # ประเภท + มูลค่า + เพดานส่วนลดสูงสุด
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(10, 0))
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=(0, 6))
        label(left, "ประเภทส่วนลด *", "small", muted=True).pack(fill="x")
        if editing and c.get("is_free_shipping"):
            current_type = TYPE_FREE_SHIP
        elif c.get("discount_type") in TYPE_LABELS:
            current_type = c.get("discount_type")
        else:
            current_type = DISCOUNT_PERCENT
        self.type_var = ctk.StringVar(value=TYPE_LABELS[current_type])
        option_menu(left, list(TYPE_LABELS.values()), self.type_var, self._on_type_change, width=220).pack(anchor="w")

        mid = ctk.CTkFrame(row, fg_color="transparent")
        mid.pack(side="left", fill="x", expand=True, padx=6)
        self.value_label = label(mid, "", "small", muted=True)
        self.value_label.pack(fill="x")
        self.value_entry = entry(mid)
        self.value_entry.pack(fill="x")
        if editing and c.get("value") is not None:
            self.value_entry.insert(0, f"{float(c.get('value')):g}")

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(6, 0))
        label(right, "เพดานส่วนลดสูงสุด (บาท)", "small", muted=True).pack(fill="x")
        self.max_disc_entry = entry(right, "ว่าง = ไม่จำกัดเพดาน")
        self.max_disc_entry.pack(fill="x")
        if editing and c.get("max_discount"):
            self.max_disc_entry.insert(0, f"{float(c.get('max_discount')):g}")
        self._on_type_change()

        # ขั้นต่ำ + จำนวนสิทธิ์
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(10, 0))
        l2 = ctk.CTkFrame(row2, fg_color="transparent")
        l2.pack(side="left", fill="x", expand=True, padx=(0, 8))
        label(l2, "ยอดสั่งซื้อขั้นต่ำเพื่อใช้คูปอง (บาท)", "small", muted=True).pack(fill="x")
        self.min_entry = entry(l2, "ว่าง = ไม่มีขั้นต่ำ")
        self.min_entry.pack(fill="x")
        if editing and c.get("min_order"):
            self.min_entry.insert(0, f"{float(c.get('min_order')):g}")
        r2 = ctk.CTkFrame(row2, fg_color="transparent")
        r2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        label(r2, "จำนวนสิทธิ์ทั้งหมด (ครั้ง)", "small", muted=True).pack(fill="x")
        self.uses_entry = entry(r2, "ว่าง = ไม่จำกัด")
        self.uses_entry.pack(fill="x")
        if editing and c.get("max_uses"):
            self.uses_entry.insert(0, str(int(c.get("max_uses"))))
        if editing:
            label(r2, f"ใช้ไปแล้ว {int(c.get('used_count') or 0)} ครั้ง", "tiny", muted=True).pack(fill="x")

        # T08: วันเริ่มต้น + วันหมดอายุ เลือกจากปฏิทิน DatePickerField
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(10, 0))
        l3 = ctk.CTkFrame(row3, fg_color="transparent")
        l3.pack(side="left", fill="x", expand=True, padx=(0, 8))
        label(l3, "วันเริ่มต้นรับ/ใช้งาน (เลือกจากปฏิทิน)", "small", muted=True).pack(fill="x")
        self.starts_entry = DatePickerField(l3, placeholder_text="ว่าง = เริ่มได้ทันที", allow_empty=True, height=36)
        self.starts_entry.pack(fill="x")
        if editing and c.get("starts_at"):
            self.starts_entry.set(expiry_to_text(c.get("starts_at")))

        r3 = ctk.CTkFrame(row3, fg_color="transparent")
        r3.pack(side="left", fill="x", expand=True, padx=(8, 0))
        label(r3, "วันหมดอายุ (เลือกจากปฏิทิน)", "small", muted=True).pack(fill="x")
        self.expiry_entry = DatePickerField(r3, placeholder_text="ว่าง = ไม่หมดอายุ", allow_empty=True, height=36)
        self.expiry_entry.pack(fill="x")
        if editing and c.get("expires_at"):
            self.expiry_entry.set(expiry_to_text(c.get("expires_at")))
            label(r3, f"ปัจจุบัน: หมดอายุ {format_date_thai(c.get('expires_at'))}", "tiny", muted=True).pack(fill="x")

        # ตั้งช่วงเวลารับโค้ด + รีโค้ดอัตโนมัติเวลา 12:00 น.
        sched_box = ctk.CTkFrame(inner, fg_color=color("surface_alt"), corner_radius=10)
        sched_box.pack(fill="x", pady=(12, 0))
        label(sched_box, "ตั้งช่วงเวลารับโค้ด & รีเซ็ตโค้ดอัตโนมัติเวลา 12:00 น. (Asia/Bangkok)", "body_bold").pack(
            fill="x", padx=14, pady=(10, 4))

        time_row = ctk.CTkFrame(sched_box, fg_color="transparent")
        time_row.pack(fill="x", padx=14, pady=4)
        label(time_row, "เวลารับได้ตั้งแต่ (HH:MM):", "small").pack(side="left")
        self.claim_start_entry = entry(time_row, "เช่น 10:00", width=100)
        self.claim_start_entry.pack(side="left", padx=(6, 14))
        if editing and c.get("claim_start_time"):
            self.claim_start_entry.insert(0, str(c.get("claim_start_time")))

        label(time_row, "ถึงเวลา (HH:MM):", "small").pack(side="left")
        self.claim_end_entry = entry(time_row, "เช่น 12:00", width=100)
        self.claim_end_entry.pack(side="left", padx=(6, 12))
        if editing and c.get("claim_end_time"):
            self.claim_end_entry.insert(0, str(c.get("claim_end_time")))

        btn(time_row, "ตั้ง 10:00 - 12:00", lambda: self._set_claim_time("10:00", "12:00"),
            kind="outline", size="sm").pack(side="left", padx=3)
        btn(time_row, "ตั้ง 12:00 - 14:00", lambda: self._set_claim_time("12:00", "14:00"),
            kind="outline", size="sm").pack(side="left", padx=3)
        btn(time_row, "รับได้ทั้งวัน", lambda: self._set_claim_time("", ""),
            kind="ghost", size="sm").pack(side="left", padx=3)

        self.repeat_daily_var = ctk.BooleanVar(value=bool(c.get("repeat_daily", 0)) if editing else True)
        ctk.CTkSwitch(
            sched_box, text="เปิดให้รับได้ทุกวันในช่วงเวลานั้น (ถ้าปิด จะอ้างอิงตามช่วงวันเริ่มต้น - วันหมดอายุ)",
            variable=self.repeat_daily_var, font=font("small_bold"), progress_color=color("info"),
        ).pack(anchor="w", padx=14, pady=(4, 4))

        reset_row = ctk.CTkFrame(sched_box, fg_color="transparent")
        reset_row.pack(fill="x", padx=14, pady=(2, 10))
        self.daily_reset_var = ctk.BooleanVar(value=bool(c.get("daily_reset_12", 0)) if editing else False)
        ctk.CTkSwitch(
            reset_row,
            text="รีโค้ดให้กดรับได้ใหม่ทุกๆ เวลา 12:00 น. ของทุกวัน (ลบโค้ดเก่าที่ไม่ได้รับและแทนด้วยโค้ดใหม่)",
            variable=self.daily_reset_var, font=font("small_bold"), progress_color=color("primary"),
        ).pack(side="left")

        label(reset_row, "คำนำหน้าโค้ดใหม่:", "small", muted=True).pack(side="left", padx=(16, 4))
        self.prefix_entry = entry(reset_row, "เช่น NOON50", width=120)
        self.prefix_entry.pack(side="left")
        if editing and c.get("code_prefix"):
            self.prefix_entry.insert(0, str(c.get("code_prefix")))

        sw_row = ctk.CTkFrame(inner, fg_color="transparent")
        sw_row.pack(fill="x", pady=(12, 0))
        self.active_var = ctk.BooleanVar(value=bool(c.get("is_active", 1)) if editing else True)
        ctk.CTkSwitch(sw_row, text="เปิดใช้งานคูปองนี้", variable=self.active_var, font=font("body"),
                      progress_color=color("success")).pack(side="left", padx=(0, 24))
        self.claimable_var = ctk.BooleanVar(value=bool(c.get("claimable", 1)) if editing else True)
        ctk.CTkSwitch(sw_row, text="แสดงให้ลูกค้ากดเก็บที่หน้าแรกและหน้าชำระเงิน", variable=self.claimable_var,
                      font=font("body"), progress_color=color("primary")).pack(side="left")

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x", pady=(14, 0))
        btn(btns, "บันทึกคูปอง", self._save, kind="primary", size="md").pack(side="left")
        btn(btns, "ยกเลิก", self._back, kind="outline", size="md").pack(side="left", padx=8)

    def _set_claim_time(self, st: str, et: str):
        self.claim_start_entry.delete(0, "end")
        if st:
            self.claim_start_entry.insert(0, st)
        self.claim_end_entry.delete(0, "end")
        if et:
            self.claim_end_entry.insert(0, et)

    def _type_key(self):
        for key, text in TYPE_LABELS.items():
            if text == self.type_var.get():
                return key
        return DISCOUNT_PERCENT

    def _on_type_change(self, _value=None):
        tkey = self._type_key()
        if tkey == TYPE_FREE_SHIP:
            self.value_label.configure(text="วงเงินลดค่าจัดส่งสูงสุด (บาท) *")
            self.value_entry.configure(placeholder_text="เช่น 50")
            if not self.value_entry.get().strip():
                self.value_entry.insert(0, "50")
            if hasattr(self, "cat_var") and "free_shipping" in self._cat_key_to_label:
                self.cat_var.set(self._cat_key_to_label["free_shipping"])
        elif tkey == DISCOUNT_PERCENT:
            self.value_label.configure(text="ส่วนลด (1–100 %) *")
            self.value_entry.configure(placeholder_text="เช่น 10 หรือ 50")
            if hasattr(self, "cat_var") and "percent" in self._cat_key_to_label:
                self.cat_var.set(self._cat_key_to_label["percent"])
        else:
            self.value_label.configure(text="ส่วนลด (บาท) *")
            self.value_entry.configure(placeholder_text="เช่น 200")
            if hasattr(self, "cat_var") and "fixed" in self._cat_key_to_label:
                self.cat_var.set(self._cat_key_to_label["fixed"])

    def _collect(self):
        code = (self.code_entry.get() or "").strip().upper()
        if not code:
            raise ValueError("กรุณากรอกโค้ดคูปอง")
        if any(ch.isspace() for ch in code):
            raise ValueError("โค้ดคูปองต้องไม่มีช่องว่าง")

        tkey = self._type_key()
        is_free_shipping = (tkey == TYPE_FREE_SHIP)
        discount_type = DISCOUNT_FIXED if is_free_shipping else tkey
        coupon_category = self._cat_label_to_key.get(self.cat_var.get(), "other")

        raw_val = self.value_entry.get().strip()
        if is_free_shipping and not raw_val:
            value = 50.0
        else:
            value = parse_money(raw_val, "ส่วนลด", required=True, minimum=0)
        if value <= 0:
            raise ValueError("ส่วนลดต้องมากกว่า 0")
        if discount_type == DISCOUNT_PERCENT and value > 100:
            raise ValueError("ส่วนลดแบบเปอร์เซ็นต์ต้องไม่เกิน 100")

        min_order = parse_money(self.min_entry.get(), "ยอดสั่งซื้อขั้นต่ำ", required=False, minimum=0) or 0
        max_discount = parse_money(self.max_disc_entry.get(), "เพดานส่วนลดสูงสุด", required=False, minimum=0)
        max_uses = parse_int(self.uses_entry.get(), "จำนวนสิทธิ์", required=False, minimum=1)
        editing = self._coupon_id is not None
        if editing and max_uses is not None and max_uses < int(self._coupon.get("used_count") or 0):
            raise ValueError(f"จำนวนสิทธิ์ต้องไม่น้อยกว่าจำนวนที่ใช้ไปแล้ว ({int(self._coupon.get('used_count') or 0)} ครั้ง)")
        starts_at = parse_expiry(self.starts_entry.get())
        expires_at = parse_expiry(self.expiry_entry.get())

        claim_st = self.claim_start_entry.get().strip() or None
        claim_et = self.claim_end_entry.get().strip() or None
        if bool(claim_st) != bool(claim_et):
            raise ValueError("กรุณาระบุทั้งเวลาเริ่มและเวลาสิ้นสุดการรับโค้ด (เช่น 10:00 ถึง 12:00)")

        return {
            "code": code,
            "discount_type": discount_type,
            "is_free_shipping": is_free_shipping,
            "coupon_category": coupon_category,
            "value": value,
            "min_order": min_order,
            "max_discount": max_discount,
            "max_uses": max_uses,
            "starts_at": starts_at,
            "expires_at": expires_at,
            "claim_start_time": claim_st,
            "claim_end_time": claim_et,
            "repeat_daily": bool(self.repeat_daily_var.get()),
            "daily_reset_12": bool(self.daily_reset_var.get()),
            "code_prefix": self.prefix_entry.get().strip().upper() or None,
            "claimable": bool(self.claimable_var.get()),
            "is_active": bool(self.active_var.get()),
        }

    def _delete_current(self):
        if self._coupon_id is None:
            return
        code = self._coupon.get("code") or "-"
        if not dialogs.confirm(
            self, "ยืนยันการลบคูปอง", f"ต้องการลบคูปอง “{code}” ใช่หรือไม่?",
            confirm_text="ลบคูปอง", danger=True,
        ):
            return
        ok, _ = self.call(coupon_service.delete_coupon, self._coupon_id)
        if ok:
            self._back()

    def _save(self):
        self.set_error("")
        try:
            data = self._collect()
        except ValueError as exc:
            self.set_error(str(exc))
            return
        if self._coupon_id is None:
            ok, _ = self.call(
                coupon_service.create_coupon,
                data["code"], data["discount_type"], data["value"],
                min_order=data["min_order"], max_uses=data["max_uses"], expires_at=data["expires_at"],
                is_active=data["is_active"], max_discount=data["max_discount"],
                starts_at=data["starts_at"], claimable=data["claimable"],
                is_free_shipping=data["is_free_shipping"],
                daily_reset_12=data["daily_reset_12"],
                code_prefix=data["code_prefix"],
                claim_start_time=data["claim_start_time"],
                claim_end_time=data["claim_end_time"],
                repeat_daily=data["repeat_daily"],
                coupon_category=data["coupon_category"],
            )
        else:
            fields = {
                k: data[k] for k in (
                    "code", "discount_type", "is_free_shipping", "coupon_category",
                    "value", "min_order", "max_discount",
                    "max_uses", "starts_at", "expires_at", "claimable",
                    "daily_reset_12", "code_prefix", "claim_start_time", "claim_end_time", "repeat_daily",
                )
            }
            fields["is_active"] = 1 if data["is_active"] else 0
            ok, _ = self.call(coupon_service.update_coupon, self._coupon_id, fields)
        if ok:
            dialogs.show_message(self, "บันทึกแล้ว", "บันทึกคูปองเรียบร้อย", kind="success")
            self._back()
