"""
ui/pages/buyer/payment.py
หน้าชำระเงิน (ปรับปรุงตามข้อ 9 + แสดง VAT 7%):
- ขยับทุกส่วนไปตรงกลางหน้า ไม่ให้ฝั่งขวาโล่ง
- ฝั่งซ้าย = QR Code (PromptPay) พร้อมยอดเงิน/ชื่อบัญชี/ปุ่มบันทึกรูป QR
- ฝั่งขวา = รายการสินค้าที่สั่งซื้อแบบคร่าวๆ (ชื่อ / สเปก / ราคา) + แสดง VAT 7% + ส่วนแนบสลิปและปุ่มส่งสลิป
- ข้อความวิธีชำระเงินและเงื่อนไขภายใน 24 ชั่วโมง คงเดิม
"""

import customtkinter as ctk

from core.constants import (
    ORDER_STATUS_CANCELLED, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_PENDING, PAYMENT_STATUS_REJECTED,
)
from services import order_service, payment_service, settings_service
from ui.components import dialogs
from ui.components.image_picker import ImagePicker
from ui.components.payment_qr import PaymentQR
from ui.pages.buyer import common
from ui.theme import ThemeManager
from utils.formatters import format_price
from utils.image_utils import load_ctk_image


class PaymentPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._order_id = None
        self._info = None
        self._slip_image = None
        self.slip_picker = None
        self.submit_btn = None

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # จัดทุกส่วนให้อยู่ตรงกลางหน้าอย่างสมดุล (ข้อ 9)
        outer = ctk.CTkFrame(self.scroll, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=20, pady=18)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=0)
        outer.grid_columnconfigure(2, weight=1)

        self.center_wrap = ctk.CTkFrame(outer, fg_color="transparent")
        self.center_wrap.grid(row=0, column=1, sticky="n")
        self.center_wrap.grid_columnconfigure(0, weight=0)
        self.center_wrap.grid_columnconfigure(1, weight=1, minsize=480)

        self.title_box = ctk.CTkFrame(self.center_wrap, fg_color="transparent")
        self.title_box.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.title_label = ctk.CTkLabel(
            self.title_box, text="ชำระเงิน", font=ThemeManager.get_font("h2"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_main"),
        )
        self.title_label.pack(side="left")
        self.status_holder = ctk.CTkFrame(self.title_box, fg_color="transparent")
        self.status_holder.pack(side="left", padx=12)

        # ฝั่งซ้าย: QR Code (PromptPay)
        self.qr = PaymentQR(self.center_wrap, size=250)
        self.qr.grid(row=1, column=0, sticky="n", pady=(4, 0), padx=(0, 18))

        # ฝั่งขวา: รายการสินค้าคร่าวๆ (ชื่อ / สเปก / ราคา + VAT 7%) + แนบสลิปและส่งสลิป
        self.right = ThemeManager.make_card(self.center_wrap, width=520)
        self.right.grid(row=1, column=1, sticky="new", pady=(4, 0))
        self.state_frame = ctk.CTkFrame(self.right, fg_color="transparent")
        self.state_frame.pack(fill="x", padx=22, pady=18)

    # ------------------------------------------------------------------ โหลด/แสดง
    def on_show(self, order_id=None, **kwargs):
        self._order_id = order_id
        self._load()

    def _clear_state(self):
        for child in self.state_frame.winfo_children():
            child.destroy()
        for child in self.status_holder.winfo_children():
            child.destroy()
        self.slip_picker = None
        self.submit_btn = None
        self._slip_image = None

    def _load(self):
        self._clear_state()
        if self._order_id is None:
            self.title_label.configure(text="ชำระเงิน")
            self.qr.clear("ไม่พบคำสั่งซื้อ")
            self._show_error("ไม่พบคำสั่งซื้อที่ต้องการชำระเงิน")
            return
        self.title_label.configure(text=f"ชำระเงิน · คำสั่งซื้อ #{self._order_id}")
        try:
            info = payment_service.get_payment_info(self._order_id)
        except (ValueError, PermissionError) as exc:
            self.qr.clear("ไม่สามารถแสดง QR ได้")
            self._show_error(str(exc))
            return
        self._info = info
        ThemeManager.status_badge(self.status_holder, info["order_status"]).pack()

        status = info["order_status"]
        if status in (ORDER_STATUS_PENDING, ORDER_STATUS_CHECKING_SLIP):
            self.qr.set_info(info)
        elif status == ORDER_STATUS_CANCELLED:
            self.qr.clear("คำสั่งซื้อนี้ถูกยกเลิกแล้ว")
        else:
            self.qr.clear("ชำระเงินเรียบร้อยแล้ว")

        self._label("ยอดที่ต้องชำระ (รวม VAT 7%)", "small_bold", "text_muted")
        self._label(format_price(info["amount"]), "price_big", "danger")

        # แสดงรายการสินค้าที่สั่งซื้อแบบคร่าวๆ (ชื่อ / สเปก / ราคา) และ VAT 7% (ข้อ 9)
        self._render_order_items_summary(info)

        if status == ORDER_STATUS_PENDING:
            self._render_pending(info)
        elif status == ORDER_STATUS_CHECKING_SLIP:
            self._render_checking(info)
        elif status == ORDER_STATUS_CANCELLED:
            self._label("คำสั่งซื้อนี้ถูกยกเลิกแล้ว ไม่ต้องชำระเงิน", "body", "danger", pady=(12, 0))
        else:
            self._label(f"✓ ชำระเงินเรียบร้อยแล้ว (สถานะ: {info['order_status_label']})", "body_bold", "success",
                        pady=(12, 0))
        self._render_buttons(status)

    # ------------------------------------------------------------------ ส่วนประกอบ
    def _label(self, text, font="body", color="text_main", pady=(2, 0), wraplength=470):
        label = ctk.CTkLabel(
            self.state_frame, text=text, font=ThemeManager.get_font(font), anchor="w", justify="left",
            wraplength=wraplength, text_color=ThemeManager.get_color_pair(color),
        )
        label.pack(fill="x", pady=pady)
        return label

    def _render_order_items_summary(self, info: dict):
        items = info.get("items") or []
        box = ctk.CTkFrame(
            self.state_frame, fg_color=ThemeManager.get_color_pair("surface_alt"),
            corner_radius=10, border_width=1, border_color=ThemeManager.get_color_pair("border"),
        )
        box.pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(
            box, text=f"รายการสินค้าที่สั่งซื้อ ({len(items)} รายการ)",
            font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"), anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 4))

        for it in items:
            r = ctk.CTkFrame(box, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=2)
            r.grid_columnconfigure(0, weight=1)
            spec = it.get("spec_summary") or it.get("option_label") or "-"
            name_txt = f"• {it['product_name']} × {it['qty']}"
            ctk.CTkLabel(
                r, text=name_txt, font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("text_main"), anchor="w",
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                r, text=format_price(it["line_total"]), font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("danger"), anchor="e",
            ).grid(row=0, column=1, sticky="e")
            ctk.CTkLabel(
                r, text=f"   สเปก/ตัวเลือก: {spec}", font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("text_muted"), anchor="w",
            ).grid(row=1, column=0, columnspan=2, sticky="w")

        # แสดงรายละเอียด VAT 7% ในสลิป/หน้าชำระเงิน
        vat_row = ctk.CTkFrame(box, fg_color="transparent")
        vat_row.pack(fill="x", padx=12, pady=(6, 8))
        pre_vat = info.get("pre_vat_amount", round(float(info["amount"]) / 1.07, 2))
        vat_amt = info.get("vat_amount", round(float(info["amount"]) - pre_vat, 2))
        ctk.CTkLabel(
            vat_row,
            text=f"มูลค่าก่อนภาษี: {format_price(pre_vat)}   |   ภาษีมูลค่าเพิ่ม (VAT 7%): {format_price(vat_amt)}",
            font=ThemeManager.get_font("tiny"),
            text_color=ThemeManager.get_color_pair("text_muted"), anchor="w",
        ).pack(fill="x")

    def _show_error(self, text):
        self._label(f"⛔ {text}", "body", "danger", pady=(0, 10))
        self._render_buttons(None)

    def _render_pending(self, info):
        payment = info.get("payment")
        if payment and payment.get("status") == PAYMENT_STATUS_REJECTED:
            reason = payment.get("reject_reason") or "ไม่ระบุเหตุผล"
            self._label(f"⚠ สลิปครั้งก่อนถูกปฏิเสธ: {reason}\nกรุณาตรวจสอบแล้วแนบสลิปใหม่อีกครั้ง", "body", "danger",
                        pady=(10, 0))
        self._label("วิธีชำระเงิน & แนบสลิปโอนเงิน", "body_bold", pady=(10, 0))
        steps = (
            "1) สแกน QR ด้วยแอปธนาคาร และโอนตามยอดข้างต้น\n"
            "2) บันทึกสลิปการโอนเป็นรูป (jpg / png ไม่เกิน 5 MB)\n"
            "3) แนบสลิปด้านล่าง แล้วกด \"ส่งสลิป\""
        )
        self._label(steps, "small", "text_muted")
        try:
            hours = settings_service.get_int("unpaid_cancel_hours", 24)
        except Exception:  # noqa: BLE001
            hours = 0
        if hours > 0:
            self._label(f"* กรุณาชำระภายใน {hours} ชั่วโมง มิฉะนั้นระบบจะยกเลิกคำสั่งซื้ออัตโนมัติ", "small", "text_muted")

        picker_wrap = ctk.CTkFrame(self.state_frame, fg_color="transparent")
        picker_wrap.pack(fill="x", pady=(10, 0))
        self.slip_picker = ImagePicker(picker_wrap, size=(220, 240), button_text="เลือกสลิป...", allow_clear=False)
        self.slip_picker.pack(anchor="center")

        self.msg_label = common.error_label(self.state_frame, wraplength=470)
        self.msg_label.pack(fill="x", pady=(6, 0))
        self.submit_btn = ctk.CTkButton(
            self.state_frame, text="ส่งสลิปชำระเงิน", width=220, command=self._submit,
            **ThemeManager.button_style("primary", "lg"),
        )
        self.submit_btn.pack(anchor="center", pady=(8, 0))

    def _render_checking(self, info):
        self._label("ส่งสลิปแล้ว — รอแอดมินตรวจสอบ", "body_bold", "text_main", pady=(12, 0))
        self._label("เมื่อตรวจสลิปเรียบร้อย ระบบจะแจ้งเตือนคุณ และสถานะคำสั่งซื้อจะเปลี่ยนเป็น \"ชำระเงินแล้ว\" พร้อมออกใบเสร็จ (รวม VAT 7%)", "small",
                    "text_muted")
        payment = info.get("payment")
        if payment and payment.get("slip_path"):
            self._slip_image = load_ctk_image(payment["slip_path"], (180, 240))
            ctk.CTkLabel(self.state_frame, text="", image=self._slip_image).pack(anchor="center", pady=(12, 0))
            self._label("สลิปที่ส่ง", "tiny", "text_muted")
        self.msg_label = common.error_label(self.state_frame, wraplength=470)
        self.msg_label.pack(fill="x")

    def _render_buttons(self, status):
        row = ctk.CTkFrame(self.state_frame, fg_color="transparent")
        row.pack(fill="x", pady=(16, 0))
        if self._order_id is not None and status is not None:
            ctk.CTkButton(row, text="ดูรายละเอียดคำสั่งซื้อ", width=170,
                          command=lambda: self.controller.show("order_detail", order_id=self._order_id),
                          **ThemeManager.button_style("outline")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="ออเดอร์ของฉัน", width=130, command=lambda: self.controller.show("orders"),
                      **ThemeManager.button_style("outline")).pack(side="left", padx=(0, 8))
        if status == ORDER_STATUS_PENDING:
            ctk.CTkButton(row, text="ยกเลิกคำสั่งซื้อ", width=140, command=self._cancel,
                          **ThemeManager.button_style("danger")).pack(side="left")

    # ------------------------------------------------------------------ การทำงาน
    def _submit(self):
        path = self.slip_picker.get_selected_file() if self.slip_picker else None
        if not path:
            self.msg_label.configure(text="⛔ กรุณาเลือกไฟล์สลิปก่อนกดส่ง")
            return
        self.msg_label.configure(text="")
        self.submit_btn.configure(state="disabled")
        try:
            payment_service.submit_slip(self._order_id, path)
        except (ValueError, PermissionError) as exc:
            self.submit_btn.configure(state="normal")
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        dialogs.show_message(self, "ส่งสลิปเรียบร้อย", "ระบบแจ้งแอดมินให้ตรวจสอบสลิปของคุณแล้ว", kind="success")
        self._load()

    def _cancel(self):
        reason = dialogs.ask_reason(
            self, "ยกเลิกคำสั่งซื้อ", "ระบุเหตุผลที่ต้องการยกเลิก (สินค้าจะถูกคืนเข้าสต็อก)",
            required=True, confirm_text="ยกเลิกคำสั่งซื้อ", danger=True)
        if reason is None:
            return
        try:
            order_service.cancel_order(self._order_id, reason)
        except (ValueError, PermissionError) as exc:
            dialogs.show_message(self, "ยกเลิกไม่ได้", str(exc), kind="error")
            self._load()
            return
        self.controller.refresh_shell()
        self._load()
