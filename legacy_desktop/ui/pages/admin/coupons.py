"""
ui/pages/admin/coupons.py
จัดการคูปองส่วนลด & กฎซื้อครบรับคูปองอัตโนมัติ (เจ้าของร้านเท่านั้น — ปรับปรุงตามข้อ 11):
- Owner กดลบคูปองได้ (ยืนยันก่อนลบ)
- รองรับคูปองส่งฟรี (ส่วนลดค่าจัดส่ง)
- รองรับรีโค้ดอัตโนมัติทุกๆ เวลา 12:00 น. ของทุกวัน (Asia/Bangkok)
- รองรับการตั้งช่วงเวลารับโค้ด (เช่น 10:00 - 12:00 ของวันนี้ หรือรับได้ทุกวันเวลานั้น)
- ตารางคูปองเดิม (OLD50, SAVE200, WELCOME10) คงเดิม
"""

import customtkinter as ctk

from core.constants import DISCOUNT_FIXED, DISCOUNT_PERCENT
from services import coupon_service
from ui.components import dialogs
from ui.components.search_bar import SearchBar
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, empty_state, entry, font, label, option_menu,
    page_header, parse_int, parse_money, pill, segmented, table_header, table_row,
)
from utils.formatters import format_date_thai, format_price

ST_ACTIVE, ST_INACTIVE, ST_EXPIRED, ST_FULL = "active", "inactive", "expired", "full"
STATUS_LABELS = {ST_ACTIVE: "ใช้งานได้", ST_INACTIVE: "ปิดอยู่", ST_EXPIRED: "หมดอายุ", ST_FULL: "ครบสิทธิ์"}
STATUS_KINDS = {ST_ACTIVE: "success", ST_INACTIVE: "muted", ST_EXPIRED: "danger", ST_FULL: "warning"}
ALL_STATUS = "ทุกสถานะ"
COLS = [(2, 115), (2, 130), (1, 95), (1, 95), (2, 155), (0, 95), (0, 195)]

TAB_COUPONS = "คูปองส่วนลดทั้งหมด"
TAB_RULES = "กฎซื้อครบรับคูปองอัตโนมัติ (ออเดอร์ถัดไป)"


def coupon_status(c):
    if not c.get("is_active"):
        return ST_INACTIVE
    if c.get("is_expired"):
        return ST_EXPIRED
    remaining = c.get("remaining")
    if remaining is not None and remaining <= 0:
        return ST_FULL
    return ST_ACTIVE


def discount_text(c):
    value = c.get("value") or 0
    if c.get("is_free_shipping"):
        return f"ส่งฟรี (สูงสุด {format_price(value)})"
    if c.get("discount_type") == DISCOUNT_PERCENT:
        return f"{value:g}%"
    return format_price(value)


def schedule_summary_text(c) -> str:
    parts = []
    if c.get("expires_at"):
        parts.append(format_date_thai(c.get("expires_at")))
    else:
        parts.append("ไม่มีวันหมดอายุ")
    if c.get("claim_start_time") and c.get("claim_end_time"):
        rep = "ทุกวัน" if c.get("repeat_daily") else "ตามวันที่"
        parts.append(f"รับได้ {c['claim_start_time']}-{c['claim_end_time']} ({rep})")
    if c.get("daily_reset_12"):
        parts.append("รีโค้ดทุก 12:00 น.")
    return "\n".join(parts)


class AdminCouponsPage(AdminPage):
    OWNER_ONLY = True

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._coupons = []
        self._rules = []
        self._search = ""
        self._mode = TAB_COUPONS
        self._edit_rule_id = None
        self._status_by_label = {label_text: key for key, label_text in STATUS_LABELS.items()}

        _header, actions = page_header(
            self.content, "คูปองส่วนลด & กฎแจกคูปองอัตโนมัติ",
            "กำหนดเงื่อนไขคูปอง โค้ดส่งฟรี ตั้งเวลารับโค้ด และรีโค้ดอัตโนมัติเวลา 12:00 น. — เฉพาะเจ้าของร้าน",
        )
        btn(actions, "＋ เพิ่มคูปองใหม่", lambda: self.controller.show("admin_coupon_form"), kind="primary",
            size="md").pack(side="right")
        btn(actions, "＋ สร้างโค้ดส่งฟรีด่วน", self._quick_create_free_shipping, kind="info",
            size="md").pack(side="right", padx=6)
        btn(actions, "รีเฟรช", self._load, kind="outline", size="md").pack(side="right", padx=6)

        self.mode_tabs = segmented(
            self.content, values=[TAB_COUPONS, TAB_RULES], command=self._switch_mode,
        )
        self.mode_tabs.set(TAB_COUPONS)
        self.mode_tabs.pack(anchor="w", pady=(0, 8))

        self.coupons_wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        self.coupons_wrap.pack(fill="x")

        bar = ctk.CTkFrame(self.coupons_wrap, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))
        self.search_bar = SearchBar(bar, command=self._on_search, placeholder="ค้นหาโค้ดคูปอง", width=240, height=36)
        self.search_bar.pack(side="left", padx=(0, 8))
        self.status_var = ctk.StringVar(value=ALL_STATUS)
        option_menu(bar, [ALL_STATUS] + list(self._status_by_label), self.status_var, lambda _v=None: self._render(),
                    width=160).pack(side="left")

        table_header(
            self.coupons_wrap, COLS,
            ["โค้ด", "ส่วนลด / เงื่อนไข", "ขั้นต่ำที่ใช้", "ใช้แล้ว", "วันหมดอายุ / ช่วงเวลารับ", "สถานะ", "จัดการ"],
        )
        self.list_frame = ctk.CTkFrame(self.coupons_wrap, fg_color="transparent")
        self.list_frame.pack(fill="x")

        # แผงจัดการกฎซื้อครบรับคูปอง (OWN-1)
        self.rules_wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        self._build_rules_panel()

    def _switch_mode(self, mode):
        self._mode = mode
        if mode == TAB_RULES:
            self.coupons_wrap.pack_forget()
            self.rules_wrap.pack(fill="x")
            self._load_rules()
        else:
            self.rules_wrap.pack_forget()
            self.coupons_wrap.pack(fill="x")
            self._load()

    def on_show(self, **kwargs):
        if not self.allowed():
            return
        if self._mode == TAB_RULES:
            self._load_rules()
        else:
            self._load()

    def _on_search(self, text):
        self._search = (text or "").strip().upper()
        self._render()

    def _load(self):
        self.set_error("")
        ok, rows = self.call(coupon_service.list_coupons)
        self._coupons = [as_dict(r) for r in (rows if ok else [])]
        self._render(failed=not ok)

    def _render(self, failed=False):
        for child in self.list_frame.winfo_children():
            child.destroy()
        if failed:
            empty_state(self.list_frame, "โหลดรายการคูปองไม่สำเร็จ")
            return
        wanted = self._status_by_label.get(self.status_var.get())
        shown = [c for c in self._coupons
                 if (not self._search or self._search in str(c.get("code") or "").upper())
                 and (wanted is None or coupon_status(c) == wanted)]
        if not shown:
            empty_state(self.list_frame, "ยังไม่มีคูปอง" if not self._coupons else "ไม่พบคูปองตามเงื่อนไขที่เลือก")
            return
        for coupon in shown:
            self._add_row(coupon)

    def _add_row(self, c):
        row = table_row(self.list_frame, COLS)
        coupon_id = c.get("id")
        status = coupon_status(c)

        ctk.CTkLabel(row, text=c.get("code") or "-", font=font("body_bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=8, pady=8)
        ctk.CTkLabel(row, text=discount_text(c), font=font("body"), anchor="w").grid(
            row=0, column=1, sticky="w", padx=8)
        min_order = c.get("min_order") or 0
        label(row, format_price(min_order) if min_order else "ไม่มี", "small", muted=True).grid(
            row=0, column=2, sticky="w", padx=8)
        max_uses = c.get("max_uses")
        used = int(c.get("used_count") or 0)
        label(row, f"{used} / {max_uses}" if max_uses else f"{used} / ไม่จำกัด", "small", muted=True).grid(
            row=0, column=3, sticky="w", padx=8)
        label(row, schedule_summary_text(c), "tiny", muted=True, justify="left").grid(
            row=0, column=4, sticky="w", padx=8, pady=4)
        pill(row, STATUS_LABELS[status], STATUS_KINDS[status]).grid(row=0, column=5, sticky="w", padx=8)

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=6, sticky="e", padx=8)
        btn(actions, "แก้ไข", lambda cid=coupon_id: self.controller.show("admin_coupon_form", coupon_id=cid),
            kind="outline", width=56).pack(side="left", padx=2)
        is_active = bool(c.get("is_active"))
        btn(actions, "ปิด" if is_active else "เปิด", lambda cid=coupon_id, act=is_active: self._toggle(cid, act),
            kind="warning" if is_active else "success", width=52).pack(side="left", padx=2)
        btn(actions, "ลบ", lambda item=c: self._delete_coupon(item),
            kind="danger", width=52).pack(side="left", padx=2)

    def _toggle(self, coupon_id, is_active):
        self.set_error("")
        ok, _ = self.call(coupon_service.toggle_coupon, coupon_id, active=not is_active)
        if ok:
            self._load()

    def _delete_coupon(self, coupon: dict):
        code = coupon.get("code") or "-"
        if not dialogs.confirm(
            self,
            "ยืนยันการลบคูปอง",
            f"ต้องการลบคูปอง “{code}” ออกจากระบบใช่หรือไม่?\n(ประวัติออเดอร์เดิมที่เคยใช้คูปองนี้จะยังคงอยู่ครบถ้วน)",
            confirm_text="ลบคูปอง",
            danger=True,
        ):
            return
        self.set_error("")
        ok, _ = self.call(coupon_service.delete_coupon, coupon.get("id"))
        if ok:
            self._load()

    def _quick_create_free_shipping(self):
        """สร้างโค้ดส่งฟรี + รีโค้ดทุก 12:00 น. อย่างรวดเร็ว หรือเปิดฟอร์มที่กรอกค่าส่งฟรีไว้ให้"""
        self.set_error("")
        code = "FREESHIP"
        existing = [c for c in self._coupons if str(c.get("code") or "").upper().startswith("FREESHIP")]
        if existing:
            code = f"FREESHIP{len(existing) + 1}"
        ok, created = self.call(
            coupon_service.create_coupon,
            code=code,
            discount_type="free_shipping",
            value=50,
            min_order=0,
            is_free_shipping=True,
            daily_reset_12=True,
            code_prefix="FREESHIP",
            claimable=True,
            is_active=True,
        )
        if ok:
            dialogs.show_message(
                self,
                "สร้างโค้ดส่งฟรีแล้ว",
                f"สร้างโค้ดส่งฟรี “{created.get('code')}” (ลดค่าจัดส่งสูงสุด 50 บาท · รีเซ็ตให้กดรับใหม่ทุก 12:00 น.) เรียบร้อยแล้ว",
                kind="success",
            )
            self._load()

    # ------------------------------------------------------------------ กฎซื้อครบรับคูปองอัตโนมัติ (OWN-1)
    def _build_rules_panel(self):
        form = card(self.rules_wrap)
        form.pack(fill="x", pady=(0, 10))
        self.rule_form_title = label(form, "เพิ่มกฎซื้อครบรับคูปองอัตโนมัติ (สำหรับใช้ออเดอร์ถัดไป)", "h3")
        self.rule_form_title.pack(fill="x", padx=16, pady=(12, 4))

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=4)
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="rf")

        def fcell(r, c, title, ph):
            box = ctk.CTkFrame(grid, fg_color="transparent")
            box.grid(row=r, column=c, sticky="ew", padx=4, pady=4)
            label(box, title, "small", muted=True).pack(fill="x")
            e = entry(box, ph)
            e.pack(fill="x")
            return e

        self.r_name = fcell(0, 0, "ชื่อแคมเปญ *", "เช่น ซื้อครบ 3,000 รับส่วนลด 10%")
        self.r_trigger = fcell(0, 1, "ยอดซื้อขั้นต่ำเพื่อรับคูปอง (บาท) *", "3000")
        self.r_prefix = fcell(0, 2, "คำนำหน้าโค้ดคูปอง *", "NEXT")

        type_box = ctk.CTkFrame(grid, fg_color="transparent")
        type_box.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        label(type_box, "ประเภทส่วนลด *", "small", muted=True).pack(fill="x")
        self.r_type_var = ctk.StringVar(value=DISCOUNT_PERCENT)
        option_menu(type_box, [DISCOUNT_PERCENT, DISCOUNT_FIXED], self.r_type_var, width=160).pack(fill="x")

        self.r_val = fcell(1, 1, "มูลค่าส่วนลด (% หรือ บาท) *", "10")
        self.r_next_min = fcell(1, 2, "ยอดขั้นต่ำเพื่อใช้ในออเดอร์ถัดไป (บาท)", "1000")
        self.r_days = fcell(2, 0, "อายุคูปอง (วัน)", "30")

        self.r_active_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(grid, text="เปิดใช้งานกฎนี้", variable=self.r_active_var, font=font("body"),
                      progress_color=color("success")).grid(row=2, column=1, sticky="w", padx=8, pady=8)

        b_row = ctk.CTkFrame(form, fg_color="transparent")
        b_row.pack(fill="x", padx=16, pady=(6, 12))
        btn(b_row, "บันทึกกฎแจกคูปอง", self._save_rule, kind="primary", size="md").pack(side="left")
        btn(b_row, "ล้างฟอร์ม", self._reset_rule_form, kind="outline", size="md").pack(side="left", padx=8)

        self.rules_list_frame = ctk.CTkFrame(self.rules_wrap, fg_color="transparent")
        self.rules_list_frame.pack(fill="x")

    def _reset_rule_form(self):
        self._edit_rule_id = None
        self.rule_form_title.configure(text="เพิ่มกฎซื้อครบรับคูปองอัตโนมัติ (สำหรับใช้ออเดอร์ถัดไป)")
        for e, default in ((self.r_name, ""), (self.r_trigger, ""), (self.r_prefix, "NEXT"),
                           (self.r_val, ""), (self.r_next_min, "0"), (self.r_days, "30")):
            e.delete(0, "end")
            if default:
                e.insert(0, default)
        self.r_type_var.set(DISCOUNT_PERCENT)
        self.r_active_var.set(True)

    def _edit_rule(self, r):
        self._edit_rule_id = r.get("id")
        self.rule_form_title.configure(text=f"แก้ไขกฎแจกคูปอง #{self._edit_rule_id}: {r.get('name')}")
        for e, val in (
            (self.r_name, r.get("name") or ""),
            (self.r_trigger, f"{float(r.get('min_order_trigger') or 0):g}"),
            (self.r_prefix, r.get("code_prefix") or "NEXT"),
            (self.r_val, f"{float(r.get('discount_value') or 0):g}"),
            (self.r_next_min, f"{float(r.get('min_order_next') or 0):g}"),
            (self.r_days, str(int(r.get("valid_days") or 30))),
        ):
            e.delete(0, "end")
            e.insert(0, val)
        self.r_type_var.set(r.get("discount_type") or DISCOUNT_PERCENT)
        self.r_active_var.set(bool(r.get("is_active", 1)))

    def _save_rule(self):
        self.set_error("")
        try:
            fields = {
                "name": self.r_name.get().strip(),
                "min_order_trigger": parse_money(self.r_trigger.get(), "ยอดซื้อขั้นต่ำเพื่อรับคูปอง", required=True, minimum=0),
                "code_prefix": self.r_prefix.get().strip().upper() or "NEXT",
                "discount_type": self.r_type_var.get(),
                "discount_value": parse_money(self.r_val.get(), "มูลค่าส่วนลด", required=True, minimum=0),
                "min_order_next": parse_money(self.r_next_min.get(), "ยอดขั้นต่ำออเดอร์ถัดไป", required=False, minimum=0) or 0.0,
                "valid_days": parse_int(self.r_days.get(), "อายุคูปอง", required=False, minimum=1) or 30,
                "is_active": bool(self.r_active_var.get()),
            }
        except ValueError as exc:
            self.set_error(str(exc))
            return
        ok, _ = self.call(coupon_service.save_coupon_rule, fields, rule_id=self._edit_rule_id)
        if ok:
            self._reset_rule_form()
            self._load_rules()

    def _delete_rule(self, rule_id):
        if not dialogs.confirm(self, "ลบกฎแจกคูปอง", "ต้องการลบกฎแจกคูปองอัตโนมัตินี้ใช่หรือไม่?", danger=True):
            return
        ok, _ = self.call(coupon_service.delete_coupon_rule, rule_id)
        if ok:
            self._load_rules()

    def _load_rules(self):
        self.set_error("")
        ok, rows = self.call(coupon_service.list_coupon_rules)
        for child in self.rules_list_frame.winfo_children():
            child.destroy()
        rows = [as_dict(r) for r in (rows if ok else [])]
        if not rows:
            empty_state(self.rules_list_frame, "ยังไม่มีกฎซื้อครบรับคูปองอัตโนมัติ")
            return
        for r in rows:
            row = card(self.rules_list_frame)
            row.pack(fill="x", pady=3)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=14, pady=10)
            ctk.CTkLabel(info, text=r.get("name") or "-", font=font("body_bold"), anchor="w").pack(anchor="w")
            disc = f"{r['discount_value']:g}%" if r.get("discount_type") == DISCOUNT_PERCENT else format_price(r.get("discount_value"))
            sub = (
                f"เมื่อซื้อครบ {format_price(r.get('min_order_trigger'))} → แจกโค้ด {r.get('code_prefix')}-XXXX ลด {disc} "
                f"(ขั้นต่ำครั้งถัดไป {format_price(r.get('min_order_next'))}, อายุ {r.get('valid_days')} วัน)"
            )
            label(info, sub, "small", muted=True).pack(anchor="w")
            active = bool(r.get("is_active", 1))
            pill(row, "เปิดใช้งาน" if active else "ปิดอยู่", "success" if active else "muted").pack(side="left", padx=8)
            btn(row, "แก้ไข", lambda item=r: self._edit_rule(item), kind="outline", width=64).pack(side="left", padx=2)
            btn(row, "ลบ", lambda rid=r.get("id"): self._delete_rule(rid), kind="danger", width=56).pack(side="left", padx=(2, 12))
