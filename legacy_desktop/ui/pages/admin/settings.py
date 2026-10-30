"""
ui/pages/admin/settings.py
หน้าตั้งค่าร้าน รายงานรายรับ/รายจ่าย (.xlsx) ข้อมูลติดต่อเจ้าของร้าน แบนเนอร์ บันทึกกิจกรรม และสำรองข้อมูล
(เจ้าของร้านเท่านั้น — ปรับปรุงตาม T08, T14, T15):
  1. ตั้งค่าร้าน & โลโก้ร้าน 1:1 & ที่อยู่หน้าร้าน & พร้อมเพย์ + ตั้งค่าความยืดหยุ่นของหน้าร้านทั้งหมด (T15):
     - ความเร็วเลื่อนแถบ Flash Sale
     - เวลาสลับชุดคูปองหน้าหลัก & จำนวนคูปองที่แสดงต่อชุด
     - เวลาสุ่มเปลี่ยนภาพสินค้าหน้าเข้าสู่ระบบ
     - หมวดหมู่คูปองเพิ่มเติม & ประเภทตัวเลือกสินค้าเพิ่มเติม
  2. ข้อมูลติดต่อเจ้าของร้าน & โซเชียล + ข้อความด่วนจากแอดมิน
  3. รายงานรายรับ/รายจ่าย (.xlsx) & บันทึกรายจ่ายร้าน (ใช้ตัวเลือกวันที่แบบปฏิทิน DatePickerField ตาม T08)
  4. จัดการแบนเนอร์ 1–10 รูป & บันทึกกิจกรรม Audit Log
  5. สำรอง / กู้คืนฐานข้อมูล SQLite
  6. แก้ระยะห่างระหว่างส่วนหัวข้อและแถบแท็บสีเหลืองให้กระชับพอดี ไม่เกิดช่องว่างโล่ง (T14)
"""

from datetime import date
from tkinter import filedialog

import customtkinter as ctk

import config
from services import (
    audit_service, banner_service, contact_service, expense_service, export_service, settings_service,
)
from ui.components import dialogs
from ui.components.date_picker import DatePickerField
from ui.components.image_picker import ImagePicker
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, entry, font, is_owner,
    label, open_file, page_header, parse_money, pill, segmented, table_header, table_row, thumb,
)
from utils import backup, image_utils
from utils.formatters import format_datetime, format_price

TAB_STORE = "ตั้งค่าร้าน & โลโก้ 1:1"
TAB_CONTACT = "ข้อมูลติดต่อ & โซเชียล"
TAB_EXPORT = "รายงาน .xlsx & รายจ่าย"
TAB_BANNER_AUDIT = "แบนเนอร์ (1-10 รูป) & Audit"
TAB_BACKUP = "สำรองฐานข้อมูล"

FIELDS = {
    "shop": [
        ("shop_name", "ชื่อร้าน *", "เช่น Badminton Pro Shop", "แสดงบนหัวเว็บ (Header) ใบเสร็จ และตอนลูกค้าชำระเงิน"),
        ("shop_address", "ที่อยู่หน้าร้าน (ตั้งอยู่ตรงไหน ให้ลูกค้าดูได้) *", "เช่น 99/9 ถนนสุขุมวิท แขวงคลองเตย กรุงเทพฯ 10110", "แสดงในปุ่มที่ตั้งร้านบน Header ท้ายหน้าแรก และใบเสร็จ PDF"),
        ("shop_hours", "เวลาเปิด-ปิดหน้าร้าน", "เช่น เปิดทุกวัน 10:00 - 20:00 น.", "แสดงให้ลูกค้าดูพร้อมที่อยู่หน้าร้าน"),
        ("shop_phone", "เบอร์โทรศัพท์หน้าร้าน", "0812345678", "แสดงให้ลูกค้าติดต่อและบนใบเสร็จ"),
        ("maps_url", "ลิงก์แผนที่หน้าร้าน Google Maps (https://...)", "https://maps.google.com/...", "ลูกค้าสามารถกดเปิดดูแผนที่หน้าร้านได้ทันที"),
    ],
    "promptpay": [
        ("promptpay_no", "เลขพร้อมเพย์ *", "เบอร์โทร 10 หลัก / เลขบัตร 13 หลัก", "ใช้สร้าง QR รับเงิน (ใส่เฉพาะตัวเลข)"),
        ("promptpay_name", "ชื่อบัญชีพร้อมเพย์ *", "ชื่อที่จะแสดงให้ลูกค้าตรวจก่อนโอน", "ควรตรงกับชื่อบัญชีจริงของร้าน"),
    ],
    "shipping": [
        ("shipping_fee", "ค่าจัดส่ง (บาท)", "เช่น 50", "คิดต่อออเดอร์"),
        ("free_shipping_min", "ฟรีค่าส่งเมื่อซื้อครบ (บาท)", "0 = ไม่เปิดใช้", "นับจากราคาสินค้าก่อนหักส่วนลด"),
    ],
    "stock": [
        ("low_stock_threshold", "เกณฑ์สต็อกใกล้หมด (ชิ้น)", "เช่น 5", "เหลือเท่านี้หรือน้อยกว่า → แจ้งเตือนและขึ้นในแดชบอร์ด"),
        ("unpaid_cancel_hours", "ยกเลิกออเดอร์ที่ไม่ชำระใน (ชั่วโมง)", "เช่น 24", "0 = ไม่ยกเลิกอัตโนมัติ"),
    ],
    "customization": [
        ("flash_sale_scroll_speed", "ความเร็วเลื่อนแถบ Flash Sale หน้าแรก (1-10)", "เช่น 2", "ค่าน้อย = เลื่อนช้าๆ นุ่มนวล, ค่ามาก = เลื่อนเร็วขึ้น"),
        ("home_coupons_per_view", "จำนวนคูปองที่แสดงต่อชุดในหน้าหลัก (1-6 ใบ)", "เช่น 3", "จำนวนคูปองที่โชว์พร้อมกันในแถบหน้าหลัก (ค่าเริ่มต้น 3 ใบ)"),
        ("coupon_rotate_seconds", "เวลาสลับชุดคูปองหน้าหลัก (วินาที)", "เช่น 9", "ระยะเวลาเปลี่ยนชุดคูปองในหน้าหลัก"),
        ("login_showcase_seconds", "เวลาสุ่มเปลี่ยนภาพสินค้าหน้าเข้าสู่ระบบ (วินาที)", "เช่น 5", "ระยะเวลาสไลด์สุ่มสินค้าฝั่งซ้ายหน้า Login"),
        ("custom_coupon_categories", "หมวดหมู่คูปองเพิ่มเติม (คั่นด้วยจุลภาค ,)", "เช่น คูปองสมาชิก VIP, คูปองวันเกิด", "เพิ่มหมวดหมู่คูปองนอกเหนือจาก ส่วนลดค่าส่ง / % / บาท / อื่นๆ"),
        ("custom_option_types", "ประเภทตัวเลือกสินค้าเพิ่มเติม (คั่นด้วยจุลภาค ,)", "เช่น ความตึงเอ็น, รุ่นซองไม้", "เพิ่มประเภทตัวเลือกสินค้าในฟอร์มจัดการสินค้า"),
    ],
}

CONTACT_FIELDS = (
    ("owner_phone", "เบอร์โทรเจ้าของร้าน / ร้าน *", "0812345678"),
    ("owner_email", "อีเมลเจ้าของร้าน (รับข้อความด่วนจากแอดมิน) *", "owner@badmintonpro.th"),
    ("shop_address", "ที่อยู่หน้าร้าน (แสดงให้ลูกค้าดูได้และในใบเสร็จ)", "เช่น 99/9 ถ.สุขุมวิท คลองเตย กรุงเทพฯ 10110"),
    ("shop_open_hours", "เวลาทำการหน้าร้าน", "เช่น เปิดทุกวัน 10:00 - 20:00 น."),
    ("line_id", "ชื่อ LINE Official / LINE ID", "@badmintonpro"),
    ("facebook_name", "ชื่อเพจ Facebook", "Badminton Pro Shop TH"),
    ("facebook_url", "ลิงก์ Facebook (https://...)", "https://www.facebook.com/badmintonproshop"),
    ("instagram_name", "ชื่อ Instagram", "@badmintonpro.th"),
    ("instagram_url", "ลิงก์ Instagram (https://...)", "https://www.instagram.com/badmintonpro.th"),
    ("tiktok_name", "ชื่อ TikTok", "@badmintonpro.th"),
    ("tiktok_url", "ลิงก์ TikTok (https://...)", "https://www.tiktok.com/@badmintonpro.th"),
)

BACKUP_COLS = [(3, 220), (1, 160), (1, 90), (0, 100)]


def fmt_number(value):
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def fmt_size(size):
    try:
        size = float(size)
    except (TypeError, ValueError):
        return "-"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return "-"


class AdminSettingsPage(AdminPage):
    OWNER_ONLY = True

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._entries = {}
        self._contact_entries = {}
        self._restored = False
        self._tab = TAB_STORE
        self._edit_banner_id = None

        # T14: กระชับระยะห่างด้านบนระหว่างหัวข้อ/คำอธิบายกับแถบแท็บสีเหลือง (ประมาณ 6-10 px)
        page_header(
            self.content, "ตั้งค่าร้าน · รายงาน .xlsx · ข้อมูลติดต่อ · ระบบ",
            "ศูนย์ควบคุมการตั้งค่าทุกอย่างในร้าน โลโก้ร้าน 1:1 ที่ตั้งหน้าร้าน และรายงานรายรับ/รายจ่าย (Owner Only)",
        )

        self.notice = ctk.CTkLabel(self.content, text="", font=font("body_bold"), text_color=color("success"),
                                   anchor="w", justify="left", wraplength=760)

        self.tabs = segmented(
            self.content,
            values=[TAB_STORE, TAB_CONTACT, TAB_EXPORT, TAB_BANNER_AUDIT, TAB_BACKUP],
            command=self._switch_tab,
        )
        self.tabs.set(TAB_STORE)
        self.tabs.pack(anchor="w", pady=(2, 8))

        self.p_store = ctk.CTkFrame(self.content, fg_color="transparent")
        self.p_contact = ctk.CTkFrame(self.content, fg_color="transparent")
        self.p_export = ctk.CTkFrame(self.content, fg_color="transparent")
        self.p_banner = ctk.CTkFrame(self.content, fg_color="transparent")
        self.p_backup = ctk.CTkFrame(self.content, fg_color="transparent")

        self._build_settings_card()
        self._build_contact_panel()
        self._build_export_panel()
        self._build_banner_audit_panel()
        self._build_backup_card()

        self.p_store.pack(fill="x")

    def _switch_tab(self, tab):
        self.set_error("")
        if not self._restored:
            self._set_notice("")
        for p in (self.p_store, self.p_contact, self.p_export, self.p_banner, self.p_backup):
            p.pack_forget()
        self._tab = tab
        if tab == TAB_STORE:
            self.p_store.pack(fill="x")
            self._load_settings()
        elif tab == TAB_CONTACT:
            self.p_contact.pack(fill="x")
            self._load_contact()
        elif tab == TAB_EXPORT:
            self.p_export.pack(fill="x")
            self._load_export_panel()
        elif tab == TAB_BANNER_AUDIT:
            self.p_banner.pack(fill="x")
            self._load_banner_audit()
        elif tab == TAB_BACKUP:
            self.p_backup.pack(fill="x")
            self._load_backups()

    def on_show(self, **kwargs):
        if not self.allowed():
            return
        self._switch_tab(self._tab)

    def _set_notice(self, text, kind="success"):
        if text:
            self.notice.configure(text=text, text_color=color(kind))
            if not self.notice.winfo_ismapped():
                self.notice.pack(fill="x", pady=(0, 4), before=self.tabs)
        else:
            self.notice.configure(text="")
            self.notice.pack_forget()

    # ================================================================== แท็บ 1: ตั้งค่าร้าน (โลโก้ 1:1 + ชื่อร้าน + ที่อยู่หน้าร้าน + ปรับแต่งทุกอย่าง T15)
    def _section(self, parent, title):
        label(parent, title, "body_bold").pack(fill="x", padx=16, pady=(8, 2))
        ctk.CTkFrame(parent, height=1, fg_color=color("border")).pack(fill="x", padx=16, pady=(0, 4))

    def _field(self, parent, key, title, placeholder, hint):
        cell = ctk.CTkFrame(parent, fg_color="transparent")
        cell.pack(fill="x", padx=16, pady=2)
        label(cell, title, "small", muted=True).pack(fill="x")
        widget = entry(cell, placeholder, height=34)
        widget.pack(fill="x")
        if hint:
            label(cell, hint, "tiny", muted=True).pack(fill="x")
        self._entries[key] = widget

    def _build_settings_card(self):
        box = card(self.p_store)
        box.pack(fill="x", pady=(0, 8))
        label(box, "ตั้งค่าร้านค้า โลโก้ร้าน (1:1) ที่อยู่หน้าร้าน และการรับชำระเงิน", "h3").pack(
            fill="x", padx=16, pady=(10, 2))

        self._section(box, "โลโก้ร้าน (อัตราส่วน 1:1) · ชื่อร้าน · ที่ตั้งหน้าร้าน")
        logo_row = ctk.CTkFrame(box, fg_color="transparent")
        logo_row.pack(fill="x", padx=16, pady=4)
        self.logo_picker = ImagePicker(
            logo_row, size=(84, 84), button_text="เลือกโลโก้ 1:1...", allow_clear=True
        )
        self.logo_picker.pack(side="left", padx=(0, 14))
        logo_info = ctk.CTkFrame(logo_row, fg_color="transparent")
        logo_info.pack(side="left", fill="x", expand=True)
        label(logo_info, "โลโก้ร้านอัตราส่วน 1:1 (แสดงฝั่งซ้ายของชื่อร้านใน Header แทนไอคอนไม้แบด)", "body_bold").pack(anchor="w")
        label(logo_info, "หากไม่อัปโหลดรูปโลโก้ ระบบจะใช้ไอคอนไม้แบดมินตันเริ่มต้นอัตโนมัติ", "small", muted=True).pack(anchor="w", pady=(2, 0))

        for spec in FIELDS["shop"]:
            self._field(box, *spec)

        self._section(box, "พร้อมเพย์ (รับชำระเงิน)")
        for spec in FIELDS["promptpay"]:
            self._field(box, *spec)

        self._section(box, "การจัดส่ง")
        for spec in FIELDS["shipping"]:
            self._field(box, *spec)

        self._section(box, "สต็อกและออเดอร์")
        for spec in FIELDS["stock"]:
            self._field(box, *spec)

        # T15: ส่วนการปรับแต่งหน้าร้านและความยืดหยุ่นทั้งหมดโดย Owner
        self._section(box, "การปรับแต่งหน้าร้าน คูปอง สไลด์ และตัวเลือกสินค้า (Owner Customization)")
        for spec in FIELDS["customization"]:
            self._field(box, *spec)

        self._section(box, "AI ตอบแชท")
        self.ai_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(box, text="ให้ AI ตอบแชทแทนเมื่อไม่มีแอดมินออนไลน์", variable=self.ai_var, font=font("body"),
                      progress_color=color("success")).pack(anchor="w", padx=16, pady=(4, 2))

        btns = ctk.CTkFrame(box, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(10, 14))
        btn(btns, "บันทึกการตั้งค่าร้านทั้งหมด", self._save_settings, kind="primary", size="md").pack(side="left")
        btn(btns, "ยกเลิกการแก้ไข", self._load_settings, kind="outline", size="md").pack(side="left", padx=8)

    def _fill(self, info):
        info = as_dict(info)
        text_keys = {
            "shop_name", "shop_address", "shop_hours", "shop_phone", "maps_url",
            "promptpay_no", "promptpay_name", "custom_coupon_categories", "custom_option_types",
        }
        for key, widget in self._entries.items():
            value = info.get(key)
            if key in text_keys:
                text = "" if value is None else str(value)
            else:
                text = fmt_number(value)
            widget.delete(0, "end")
            widget.insert(0, text)
        self.logo_picker.set_image(info.get("shop_logo_path") or None)
        self.ai_var.set(bool(info.get("ai_enabled", True)))

    def _load_settings(self):
        self.set_error("")
        ok, info = self.call(settings_service.get_shop_info)
        if ok:
            self._fill(info)

    def _save_settings(self):
        self.set_error("")
        values = {key: widget.get().strip() for key, widget in self._entries.items()}
        values["ai_enabled"] = "1" if self.ai_var.get() else "0"

        if self.logo_picker.has_change():
            sel = self.logo_picker.get_selected_file()
            if sel:
                try:
                    values["shop_logo_path"] = image_utils.save_upload(sel, config.IMAGES_DIR, "shop_logo")
                except ValueError as exc:
                    self.set_error(str(exc))
                    return
            else:
                values["shop_logo_path"] = ""

        ok, info = self.call(settings_service.update_many, values)
        if ok:
            self._fill(info)
            self._set_notice("บันทึกการตั้งค่าร้าน โลโก้ร้าน และที่ตั้งหน้าร้านเรียบร้อยแล้ว (มีผลกับทั้งแอปทันที)")
            self.refresh_shell()

    # ================================================================== แท็บ 2: ข้อมูลติดต่อเจ้าของร้าน (OWN-6, ADM-2)
    def _build_contact_panel(self):
        box = card(self.p_contact)
        box.pack(fill="x", pady=(0, 10))
        label(box, "ข้อมูลติดต่อเจ้าของร้าน ที่อยู่หน้าร้าน & ช่องทางโซเชียล (Facebook / LINE / Instagram / TikTok)", "h3").pack(
            fill="x", padx=16, pady=(10, 2))
        label(box, "ข้อมูลนี้จะแสดงให้ลูกค้าดูที่ตั้งหน้าร้าน และให้แอดมินกดติดต่อในกรณีฉุกเฉิน", "small",
              muted=True).pack(fill="x", padx=16, pady=(0, 6))

        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=2)
        grid.grid_columnconfigure((0, 1), weight=1, uniform="cf")

        for idx, (key, title, ph) in enumerate(CONTACT_FIELDS):
            r, c = divmod(idx, 2)
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=r, column=c, sticky="ew", padx=4, pady=3)
            label(cell, title, "small", muted=True).pack(fill="x")
            e = entry(cell, ph, height=34)
            e.pack(fill="x")
            self._contact_entries[key] = e

        btns = ctk.CTkFrame(box, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(8, 12))
        btn(btns, "บันทึกข้อมูลติดต่อเจ้าของร้าน", self._save_contact, kind="primary", size="md").pack(side="left")

        msg_box = card(self.p_contact)
        msg_box.pack(fill="x", pady=(0, 10))
        label(msg_box, "ข้อความด่วนที่แอดมินส่งถึงเจ้าของร้าน", "h3").pack(fill="x", padx=16, pady=(10, 4))
        self.staff_msg_list = ctk.CTkFrame(msg_box, fg_color="transparent")
        self.staff_msg_list.pack(fill="x", padx=14, pady=(0, 12))

    def _load_contact(self):
        ok, all_settings = self.call(settings_service.get_all)
        data = as_dict(all_settings) if ok else {}
        mapping = {
            "owner_phone": data.get("shop_phone") or "",
            "owner_email": data.get("shop_email") or "",
            "shop_address": data.get("shop_address") or "",
            "shop_open_hours": data.get("shop_hours") or "",
            "line_id": data.get("line_name") or "",
            "facebook_name": data.get("facebook_name") or "",
            "facebook_url": data.get("facebook_url") or "",
            "instagram_name": data.get("instagram_name") or "",
            "instagram_url": data.get("instagram_url") or "",
            "tiktok_name": data.get("tiktok_name") or "",
            "tiktok_url": data.get("tiktok_url") or "",
        }
        for key, e in self._contact_entries.items():
            e.delete(0, "end")
            e.insert(0, str(mapping.get(key, data.get(key) or "")))

        for child in self.staff_msg_list.winfo_children():
            child.destroy()
        ok_m, msgs = self.call(contact_service.list_staff_messages_for_owner, 20)
        msgs = [as_dict(m) for m in (msgs if ok_m else [])]
        if not msgs:
            label(self.staff_msg_list, "ยังไม่มีข้อความด่วนจากแอดมิน", "small", muted=True).pack(anchor="w", pady=4)
            return
        for m in msgs:
            row = ctk.CTkFrame(self.staff_msg_list, fg_color=color("surface_alt"), corner_radius=8)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row,
                text=f"{m.get('subject')} — จาก {m.get('sender_name') or m.get('sender_email')} ({format_datetime(m.get('created_at'))})",
                font=font("small_bold"), anchor="w",
            ).pack(fill="x", padx=12, pady=(6, 2))
            ctk.CTkLabel(row, text=m.get("message") or "", font=font("small"), anchor="w", justify="left",
                         wraplength=700).pack(fill="x", padx=12, pady=(0, 6))

    def _save_contact(self):
        self.set_error("")
        payload = {k: e.get().strip() for k, e in self._contact_entries.items()}
        ok, _ = self.call(contact_service.update_owner_contact_info, payload)
        if ok:
            self._set_notice("บันทึกข้อมูลติดต่อเจ้าของร้าน ที่ตั้งหน้าร้าน และโซเชียลมีเดียเรียบร้อยแล้ว")
            self._load_contact()

    # ================================================================== แท็บ 3: รายงาน .xlsx & รายจ่าย (T08 ปฏิทินเลือกวันที่)
    def _build_export_panel(self):
        box = card(self.p_export)
        box.pack(fill="x", pady=(0, 8))
        label(box, "ส่งออกรายงานรายรับ/รายจ่าย/สินค้า/ลูกค้า เป็นไฟล์ Excel (.xlsx แยกสีรายรับเขียว/รายจ่ายแดง)", "h3").pack(
            fill="x", padx=16, pady=(10, 2))
        label(box, "เลือกช่วงวันที่จากปฏิทินได้สูงสุด 1 ปีเต็ม (รวมถึง 1 ม.ค. – 31 ธ.ค.) จัดหน้าสวยงามพร้อมแถวสรุปรวม", "small",
              muted=True).pack(fill="x", padx=16, pady=(0, 6))

        today = date.today()
        y_start = f"{today.year}-01-01"
        y_end = f"{today.year}-12-31"

        d_row = ctk.CTkFrame(box, fg_color="transparent")
        d_row.pack(fill="x", padx=16, pady=3)
        label(d_row, "ตั้งแต่วันที่:", "small_bold").pack(side="left", anchor="n", pady=6)
        self.exp_start = DatePickerField(d_row, placeholder_text=y_start, allow_empty=False, width=215, height=34)
        self.exp_start.pack(side="left", padx=(6, 12))
        self.exp_start.set(y_start)

        label(d_row, "ถึงวันที่:", "small_bold").pack(side="left", anchor="n", pady=6)
        self.exp_end = DatePickerField(d_row, placeholder_text=y_end, allow_empty=False, width=215, height=34)
        self.exp_end.pack(side="left", padx=(6, 12))
        self.exp_end.set(y_end)

        btn(d_row, f"ทั้งปี {today.year} (1 ม.ค.–31 ธ.ค.)", lambda: self._set_date_range(y_start, y_end),
            kind="outline", width=165).pack(side="left", padx=4, anchor="n")
        m_start = f"{today.year}-{today.month:02d}-01"
        btn(d_row, "เดือนปัจจุบัน", lambda: self._set_date_range(m_start, today.isoformat()),
            kind="outline", width=105).pack(side="left", padx=4, anchor="n")

        act_row = ctk.CTkFrame(box, fg_color="transparent")
        act_row.pack(fill="x", padx=16, pady=(6, 10))
        btn(act_row, "ส่งออกรายงาน Excel (.xlsx)...", self._export_xlsx_now, kind="primary", size="md").pack(side="left")
        self.export_summary_lbl = label(act_row, "", "small_bold")
        self.export_summary_lbl.pack(side="left", padx=14)

        auto_card = card(self.p_export)
        auto_card.pack(fill="x", pady=(0, 8))
        label(auto_card, "ตั้งค่าส่งออกรายงานและสำรองข้อมูลรายเดือนอัตโนมัติ", "h3").pack(
            fill="x", padx=16, pady=(10, 2))
        self.auto_exp_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            auto_card, text="ส่งออกรายงาน .xlsx ของเดือนก่อนหน้าอัตโนมัติเมื่อเปิดแอปในเดือนใหม่",
            variable=self.auto_exp_var, font=font("body"), progress_color=color("success"),
        ).pack(anchor="w", padx=16, pady=(2, 4))

        f_row = ctk.CTkFrame(auto_card, fg_color="transparent")
        f_row.pack(fill="x", padx=16, pady=(2, 10))
        label(f_row, "โฟลเดอร์ปลายทาง:", "small_bold").pack(side="left")
        self.auto_folder_entry = entry(f_row, str(config.EXPORTS_DIR), width=350, height=34)
        self.auto_folder_entry.pack(side="left", padx=8)
        btn(f_row, "เลือกโฟลเดอร์...", self._pick_export_folder, kind="outline", width=115).pack(side="left", padx=4)
        btn(f_row, "บันทึกตั้งค่าส่งออกอัตโนมัติ", self._save_auto_export_config, kind="primary", width=185).pack(
            side="left", padx=6)

        exp_card = card(self.p_export)
        exp_card.pack(fill="x", pady=(0, 8))
        label(exp_card, "บันทึกรายจ่ายร้านค้า (แสดงเป็นสีแดงอ่อนในรายงานรายรับ/รายจ่าย .xlsx)", "h3").pack(
            fill="x", padx=16, pady=(10, 4))
        e_row = ctk.CTkFrame(exp_card, fg_color="transparent")
        e_row.pack(fill="x", padx=16, pady=3)
        self.ex_title = entry(e_row, "รายการรายจ่าย เช่น ค่าเช่าร้าน / ค่ากล่องพัสดุ", width=220, height=34)
        self.ex_title.pack(side="left", padx=(0, 6), anchor="n")
        self.ex_cat = entry(e_row, "หมวดหมู่ เช่น ค่าเช่า/วัสดุ", width=130, height=34)
        self.ex_cat.pack(side="left", padx=4, anchor="n")
        self.ex_amt = entry(e_row, "จำนวนเงิน (บาท)", width=115, height=34)
        self.ex_amt.pack(side="left", padx=4, anchor="n")
        self.ex_date = DatePickerField(e_row, placeholder_text=today.isoformat(), allow_empty=False, width=205, height=34)
        self.ex_date.pack(side="left", padx=4)
        self.ex_date.set(today.isoformat())
        btn(e_row, "＋ เพิ่มรายจ่าย", self._add_expense, kind="danger", width=105).pack(side="left", padx=6, anchor="n")

        self.expense_list = ctk.CTkFrame(exp_card, fg_color="transparent")
        self.expense_list.pack(fill="x", padx=16, pady=(4, 10))

    def _set_date_range(self, s: str, e: str):
        self.exp_start.set(s)
        self.exp_end.set(e)

    def _pick_export_folder(self):
        folder = filedialog.askdirectory(title="เลือกโฟลเดอร์สำหรับบันทึกรายงานอัตโนมัติ")
        if folder:
            self.auto_folder_entry.delete(0, "end")
            self.auto_folder_entry.insert(0, folder)

    def _save_auto_export_config(self):
        ok, _ = self.call(
            export_service.configure_auto_monthly_export,
            bool(self.auto_exp_var.get()),
            self.auto_folder_entry.get().strip(),
        )
        if ok:
            self._set_notice("บันทึกการตั้งค่าส่งออกรายเดือนอัตโนมัติแล้ว")

    def _export_xlsx_now(self):
        s = self.exp_start.get().strip()
        e = self.exp_end.get().strip()
        default_name = f"badminton_report_{s}_to_{e}.xlsx"
        dest = filedialog.asksaveasfilename(
            title="บันทึกไฟล์รายงาน Excel (.xlsx)",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel Workbook", "*.xlsx")],
        )
        if not dest:
            return
        ok, res = self.call(export_service.export_report_xlsx, s, e, dest)
        if ok:
            res = as_dict(res)
            self._set_notice(f"ส่งออกไฟล์รายงานสำเร็จ: {res.get('path')}")
            self.export_summary_lbl.configure(
                text=f"รายรับรวม {format_price(res.get('gross_revenue'))} | กำไรสุทธิ {format_price(res.get('net_profit'))} | ลูกค้า {res.get('customer_count')} ราย"
            )
            open_file(res.get("path"))

    def _add_expense(self):
        self.set_error("")
        try:
            amt = parse_money(self.ex_amt.get(), "จำนวนเงินรายจ่าย", required=True, minimum=0)
        except ValueError as exc:
            self.set_error(str(exc))
            return
        ok, _ = self.call(
            expense_service.add_expense,
            self.ex_title.get().strip(), amt,
            self.ex_cat.get().strip() or "ทั่วไป",
            self.ex_date.get().strip(),
        )
        if ok:
            self.ex_title.delete(0, "end")
            self.ex_amt.delete(0, "end")
            self._load_export_panel()

    def _delete_expense(self, eid):
        ok, _ = self.call(expense_service.delete_expense, eid)
        if ok:
            self._load_export_panel()

    def _load_export_panel(self):
        ok_s, all_s = self.call(settings_service.get_all)
        sdata = as_dict(all_s) if ok_s else {}
        self.auto_exp_var.set(str(sdata.get("export_auto_monthly_enabled", "1")) in ("1", "true"))
        self.auto_folder_entry.delete(0, "end")
        self.auto_folder_entry.insert(0, str(sdata.get("export_auto_folder") or config.EXPORTS_DIR))

        for child in self.expense_list.winfo_children():
            child.destroy()
        ok, rows = self.call(expense_service.list_expenses)
        rows = [as_dict(r) for r in (rows if ok else [])]
        if not rows:
            label(self.expense_list, "ยังไม่มีรายการรายจ่ายที่บันทึกไว้", "small", muted=True).pack(anchor="w", pady=4)
            return
        for r in rows[:15]:
            line = ctk.CTkFrame(self.expense_list, fg_color=color("surface_alt"), corner_radius=6)
            line.pack(fill="x", pady=2)
            ctk.CTkLabel(
                line,
                text=f"{r.get('expense_date')} · [{r.get('category')}] {r.get('title')}",
                font=font("small_bold"), anchor="w",
            ).pack(side="left", padx=10, pady=5)
            btn(line, "ลบ", lambda eid=r.get("id"): self._delete_expense(eid), kind="danger", width=50).pack(
                side="right", padx=8, pady=3)
            ctk.CTkLabel(line, text=format_price(r.get("amount")), font=font("small_bold"),
                         text_color=color("danger")).pack(side="right", padx=10)

    # ================================================================== แท็บ 4: แบนเนอร์ 1–10 รูป & Audit Log
    def _build_banner_audit_panel(self):
        b_card = card(self.p_banner)
        b_card.pack(fill="x", pady=(0, 10))
        self.banner_form_lbl = label(
            b_card, "จัดการแบนเนอร์สไลด์โชว์หน้าแรก (ใส่ได้ตั้งแต่ 1 – 10 รูป พร้อมปรับแต่งหัวข้อและคำโปรย)", "h3"
        )
        self.banner_form_lbl.pack(fill="x", padx=16, pady=(10, 4))

        f_row = ctk.CTkFrame(b_card, fg_color="transparent")
        f_row.pack(fill="x", padx=16, pady=4)
        self.b_picker = ImagePicker(f_row, size=80, allow_clear=True)
        self.b_picker.pack(side="left", padx=(0, 12))
        right = ctk.CTkFrame(f_row, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True)
        self.b_title = entry(right, "หัวข้อแบนเนอร์ * เช่น ตัวช่วยเลือกไม้ & AI แนะนำไม้แบดคู่ใจ 3 รุ่น", height=34)
        self.b_title.pack(fill="x", pady=2)
        self.b_sub = entry(right, "คำอธิบายเพิ่มเติม เช่น วิเคราะห์ตามระดับฝีมือ สไตล์การเล่น และงบประมาณของคุณ", height=34)
        self.b_sub.pack(fill="x", pady=2)

        b_btns = ctk.CTkFrame(right, fg_color="transparent")
        b_btns.pack(fill="x", pady=(4, 0))
        self.b_save_btn = btn(b_btns, "＋ เพิ่มแบนเนอร์ใหม่", self._save_banner_form, kind="primary", size="sm")
        self.b_save_btn.pack(side="left")
        self.b_cancel_btn = btn(b_btns, "ยกเลิกแก้ไข", self._reset_banner_form, kind="outline", size="sm")

        self.banner_list = ctk.CTkFrame(b_card, fg_color="transparent")
        self.banner_list.pack(fill="x", padx=16, pady=(4, 12))

        a_card = card(self.p_banner)
        a_card.pack(fill="x", pady=(0, 10))
        label(a_card, "บันทึกกิจกรรมผู้ใช้งานและแอดมิน (Audit Log)", "h3").pack(
            fill="x", padx=16, pady=(10, 4))
        self.audit_list = ctk.CTkFrame(a_card, fg_color="transparent")
        self.audit_list.pack(fill="x", padx=16, pady=(0, 12))

    def _edit_banner_row(self, b: dict):
        self._edit_banner_id = b.get("id")
        self.banner_form_lbl.configure(text=f"แก้ไขแบนเนอร์ #{self._edit_banner_id}: {b.get('title') or ''}")
        self.b_title.delete(0, "end")
        self.b_title.insert(0, str(b.get("title") or ""))
        self.b_sub.delete(0, "end")
        self.b_sub.insert(0, str(b.get("subtitle") or ""))
        self.b_picker.set_initial(b.get("image_path") or None)
        self.b_save_btn.configure(text="บันทึกการแก้ไขแบนเนอร์")
        if not self.b_cancel_btn.winfo_ismapped():
            self.b_cancel_btn.pack(side="left", padx=8)

    def _reset_banner_form(self):
        self._edit_banner_id = None
        self.banner_form_lbl.configure(
            text="จัดการแบนเนอร์สไลด์โชว์หน้าแรก (ใส่ได้ตั้งแต่ 1 – 10 รูป พร้อมปรับแต่งหัวข้อและคำโปรย)"
        )
        self.b_title.delete(0, "end")
        self.b_sub.delete(0, "end")
        self.b_picker.set_initial(None)
        self.b_save_btn.configure(text="＋ เพิ่มแบนเนอร์ใหม่")
        self.b_cancel_btn.pack_forget()

    def _save_banner_form(self):
        self.set_error("")
        title = self.b_title.get().strip()
        sub = self.b_sub.get().strip()
        if not title and not self.b_picker.get_selected_file():
            self.set_error("กรุณากรอกหัวข้อแบนเนอร์ หรือเลือกรูปภาพแบนเนอร์")
            return

        payload = {"title": title or "โปรโมชันพิเศษ", "subtitle": sub, "is_active": True}
        if self.b_picker.has_change():
            payload["image_path"] = self.b_picker.get_selected_file() or ""

        ok, _ = self.call(banner_service.save_banner, payload, banner_id=self._edit_banner_id)
        if ok:
            self._reset_banner_form()
            self._load_banner_audit()

    def _toggle_banner(self, b):
        ok, _ = self.call(banner_service.set_banner_active, b.get("id"), not bool(b.get("is_active", 1)))
        if ok:
            self._load_banner_audit()

    def _delete_banner(self, bid):
        if not dialogs.confirm(self, "ลบแบนเนอร์", "ต้องการลบแบนเนอร์รายการนี้ใช่หรือไม่?", danger=True):
            return
        ok, _ = self.call(banner_service.delete_banner, bid)
        if ok:
            if self._edit_banner_id == bid:
                self._reset_banner_form()
            self._load_banner_audit()

    def _load_banner_audit(self):
        for child in self.banner_list.winfo_children():
            child.destroy()
        ok, banners = self.call(banner_service.list_all_banners)
        b_list = [as_dict(x) for x in (banners if ok else [])]
        if not b_list:
            label(
                self.banner_list,
                "ยังไม่ได้อัปโหลดแบนเนอร์ที่กำหนดเอง (หน้าแรกกำลังแสดงแบนเนอร์มาตรฐานของร้าน — สามารถเพิ่มได้ตั้งแต่ 1 ถึง 10 รูป)",
                "small", muted=True,
            ).pack(anchor="w", pady=4)
        for idx, b in enumerate(b_list, start=1):
            row = ctk.CTkFrame(self.banner_list, fg_color=color("surface_alt"), corner_radius=8)
            row.pack(fill="x", pady=2)
            thumb(row, b.get("image_path"), 42, cover=bool(b.get("image_path"))).pack(side="left", padx=8, pady=4)
            txt_col = ctk.CTkFrame(row, fg_color="transparent")
            txt_col.pack(side="left", fill="x", expand=True, padx=6, pady=4)
            ctk.CTkLabel(
                txt_col, text=f"#{idx} {b.get('title') or '-'}",
                font=font("small_bold"), anchor="w",
            ).pack(fill="x")
            label(txt_col, b.get("subtitle") or "(ไม่มีคำอธิบายรอง)", "tiny", muted=True).pack(fill="x")

            act = bool(b.get("is_active", 1))
            pill(row, "แสดงอยู่" if act else "ซ่อน", "success" if act else "muted").pack(side="left", padx=4)
            btn(row, "แก้ไข", lambda item=b: self._edit_banner_row(item),
                kind="info", width=56).pack(side="left", padx=2)
            btn(row, "ซ่อน" if act else "แสดง", lambda item=b: self._toggle_banner(item),
                kind="outline", width=54).pack(side="left", padx=2)
            btn(row, "ลบ", lambda bid=b.get("id"): self._delete_banner(bid),
                kind="danger", width=48).pack(side="left", padx=(2, 8))

        for child in self.audit_list.winfo_children():
            child.destroy()
        ok_a, logs = self.call(audit_service.list_logs, 40)
        logs = [as_dict(x) for x in (logs if ok_a else [])]
        if not logs:
            label(self.audit_list, "ยังไม่มีประวัติกิจกรรม", "small", muted=True).pack(anchor="w")
            return
        for lg in logs[:25]:
            line = ctk.CTkFrame(self.audit_list, fg_color=color("surface_alt"), corner_radius=6)
            line.pack(fill="x", pady=1)
            txt = (
                f"[{format_datetime(lg.get('created_at'))}] "
                f"{lg.get('username') or 'system'} ({lg.get('user_role') or '-'}) → "
                f"{lg.get('action')} ({lg.get('target_type') or ''}:{lg.get('target_id') or ''}) {lg.get('detail') or ''}"
            )
            ctk.CTkLabel(line, text=txt, font=font("tiny"), anchor="w", justify="left", wraplength=820).pack(
                fill="x", padx=10, pady=4)

    # ================================================================== แท็บ 5: สำรอง / กู้คืนฐานข้อมูล
    def _build_backup_card(self):
        box = card(self.p_backup)
        box.pack(fill="x", pady=(0, 10))
        head = ctk.CTkFrame(box, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(12, 0))
        label(head, "สำรอง / กู้คืนฐานข้อมูล SQLite", "h3").pack(side="left")
        btn(head, "สำรองข้อมูลตอนนี้", self._backup_now, kind="primary", size="md").pack(side="right")
        label(box, "ไฟล์สำรองเก็บในโฟลเดอร์ data/backups (แยกจากไฟล์รายงาน .xlsx) — "
                   "การกู้คืนจะสำรองข้อมูลปัจจุบันไว้ให้ก่อนเสมอ", "small", muted=True,
              wraplength=720, justify="left").pack(fill="x", padx=16, pady=(2, 8))

        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=(0, 12))
        table_header(inner, BACKUP_COLS, ["ไฟล์", "สร้างเมื่อ", "ขนาด", ""])
        self.backup_list = ctk.CTkFrame(inner, fg_color="transparent")
        self.backup_list.pack(fill="x")

    def _run(self, func, *args):
        if not is_owner():
            self.set_error("คุณไม่มีสิทธิ์ทำรายการนี้")
            return False, None
        try:
            return True, func(*args)
        except (ValueError, PermissionError) as exc:
            self.set_error(str(exc))
        except OSError as exc:
            self.set_error(f"จัดการไฟล์ไม่สำเร็จ: {exc}")
        return False, None

    def _load_backups(self):
        ok, rows = self._run(backup.list_backups)
        for child in self.backup_list.winfo_children():
            child.destroy()
        rows = [as_dict(r) for r in (rows if ok else [])]
        if not rows:
            ctk.CTkLabel(self.backup_list, text="ยังไม่มีไฟล์สำรอง", font=font("body"),
                         text_color=color("text_muted")).pack(pady=16)
            return
        for item in rows:
            row = table_row(self.backup_list, BACKUP_COLS)
            ctk.CTkLabel(row, text=item.get("name") or "-", font=font("small"), anchor="w").grid(
                row=0, column=0, sticky="w", padx=8, pady=8)
            label(row, format_datetime(item.get("created_at")), "small", muted=True).grid(
                row=0, column=1, sticky="w", padx=8)
            label(row, fmt_size(item.get("size")), "small", muted=True).grid(row=0, column=2, sticky="w", padx=8)
            btn(row, "กู้คืน", lambda it=item: self._restore(it), kind="danger", width=80).grid(
                row=0, column=3, sticky="e", padx=8)

    def _backup_now(self):
        self.set_error("")
        ok, path = self._run(backup.backup_db)
        if ok:
            self._set_notice(f"สำรองข้อมูลแล้ว: {getattr(path, 'name', path)}")
            self._load_backups()

    def _restore(self, item):
        name = item.get("name") or "-"
        if not dialogs.confirm(
            self, "กู้คืนข้อมูล",
            f"กู้คืนข้อมูลจากไฟล์\n{name}\nใช่ไหม?\n\n"
            "ข้อมูลปัจจุบันทั้งหมดจะถูกแทนที่ด้วยข้อมูลในไฟล์นี้ (ระบบสำรองข้อมูลปัจจุบันไว้ให้ก่อน)\n"
            "หลังกู้คืนต้องปิดแอปแล้วเปิดใหม่",
            confirm_text="กู้คืนข้อมูล", danger=True,
        ):
            return
        self.set_error("")
        ok, _ = self._run(backup.restore_backup, item.get("path"))
        if ok:
            self._restored = True
            self._set_notice("กู้คืนข้อมูลสำเร็จ — กรุณาปิดแอปแล้วเปิดใหม่ทันที", kind="danger")
            dialogs.show_message(self, "กู้คืนสำเร็จ",
                                 "กู้คืนข้อมูลเรียบร้อย\nกรุณาปิดแอปแล้วเปิดใหม่เพื่อใช้ข้อมูลที่กู้คืน", kind="warning")
            self._load_backups()
