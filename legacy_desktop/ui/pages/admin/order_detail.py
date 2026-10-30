"""
ui/pages/admin/order_detail.py
รายละเอียดออเดอร์ฝั่งแอดมิน/เจ้าของ — route `admin_order_detail` → AdminOrderDetailPage
รองรับการบันทึกเลขพัสดุพร้อมส่งอีเมลแจ้งลูกค้าอัตโนมัติ (ship_order_and_notify — E8)
และแสดงรายละเอียดภาษีมูลค่าเพิ่ม VAT 7% ในสรุปยอดและใบเสร็จ PDF
"""

import threading

import customtkinter as ctk

from core.constants import (
    CARRIERS, ORDER_STATUS_CANCELLED, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_COMPLETED,
    ORDER_STATUS_PAID, ORDER_STATUS_PENDING, ORDER_STATUS_SHIPPED, PAYMENT_STATUS_LABELS,
    PAYMENT_STATUS_REJECTED, PAYMENT_STATUS_VERIFIED,
)
from services import email_outbox_service, order_service, receipt_service, shipping_service
from ui.components import dialogs
from ui.components.order_timeline import OrderTimeline
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, entry, font, label, load_fit_image,
    open_file, option_menu, page_header, pill, show_image_window, thumb,
)
from ui.theme import ThemeManager
from utils.formatters import format_datetime, format_phone, format_price

CANCELLABLE = (ORDER_STATUS_PENDING, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_PAID)
RECEIPT_STATUSES = (ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, ORDER_STATUS_COMPLETED)


class AdminOrderDetailPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._order_id = None
        self._detail = {}
        self._receipt_btn = None

    def on_show(self, order_id=None, **kwargs):
        if not self.allowed():
            return
        self._order_id = order_id
        self._load()

    def _load(self, detail=None):
        self.set_error("")
        ok, data = (True, detail) if detail is not None else self.call(order_service.get_order_detail, self._order_id)
        self.clear_content()
        if not ok:
            _h, actions = page_header(self.content, "ออเดอร์")
            btn(actions, "← กลับ", self._back, kind="outline").pack(side="right")
            return
        self._detail = as_dict(data)
        self._render()

    def _back(self):
        self.controller.go_back(default="admin_orders")

    def _act(self, func, *args):
        self.set_error("")
        ok, result = self.call(func, *args)
        if ok:
            self._load(detail=result)
            self.refresh_shell()
        return ok

    def _render(self):
        d = self._detail
        status = d.get("status")
        _h, actions = page_header(self.content, f"ออเดอร์ #{d.get('id')}",
                                  f"สั่งเมื่อ {format_datetime(d.get('created_at'))}")
        btn(actions, "← กลับ", self._back, kind="outline").pack(side="right")
        ThemeManager.status_badge(actions, status).pack(side="right", padx=10)

        cols = ctk.CTkFrame(self.content, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=3, uniform="c")
        cols.grid_columnconfigure(1, weight=2, uniform="c")
        left = ctk.CTkFrame(cols, fg_color="transparent")
        left.grid(row=0, column=0, sticky="new", padx=(0, 6))
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.grid(row=0, column=1, sticky="new", padx=(6, 0))

        self._items_card(left)
        self._timeline_card(left)
        self._buyer_card(right)
        self._payment_card(right)
        self._shipment_card(right)
        self._actions_card(right)

    def _items_card(self, parent):
        d = self._detail
        box = card(parent)
        box.pack(fill="x", pady=(0, 10))
        label(box, "รายการสินค้า & สรุปภาษีมูลค่าเพิ่ม (VAT 7%)", "h3").pack(fill="x", padx=16, pady=(12, 6))
        for item in d.get("items") or []:
            it = as_dict(item)
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            thumb(row, it.get("image_path"), 44).pack(side="left")
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10)
            ctk.CTkLabel(info, text=it.get("product_name", "-"), font=font("body"), anchor="w", wraplength=300,
                         justify="left").pack(anchor="w")
            sub = f"{format_price(it.get('price_at_purchase'))} × {it.get('qty')}"
            if it.get("option_label"):
                sub = f"{it.get('option_label')} · {sub}"
            label(info, sub, "small", muted=True).pack(anchor="w")
            ctk.CTkLabel(row, text=format_price(it.get("line_total")), font=font("body_bold")).pack(side="right")

        ctk.CTkFrame(box, height=1, fg_color=color("border")).pack(fill="x", padx=16, pady=8)
        self._sum_line(box, "ราคาสินค้า", format_price(d.get("subtotal")))
        if d.get("discount"):
            code = f" ({d.get('coupon_code')})" if d.get("coupon_code") else ""
            self._sum_line(box, f"ส่วนลด{code}", "-" + format_price(d.get("discount")))
        self._sum_line(box, "ค่าจัดส่ง", format_price(d.get("shipping_fee")) if d.get("shipping_fee") else "ฟรี")
        pre_vat = d.get("pre_vat_amount", round(float(d.get("total") or 0) / 1.07, 2))
        vat_amt = d.get("vat_amount", round(float(d.get("total") or 0) - pre_vat, 2))
        self._sum_line(box, "มูลค่าก่อนภาษี", format_price(pre_vat))
        self._sum_line(box, "ภาษีมูลค่าเพิ่ม (VAT 7%)", format_price(vat_amt))
        self._sum_line(box, "ยอดรวมสุทธิ (รวม VAT 7%)", format_price(d.get("total")), bold=True)
        ctk.CTkFrame(box, height=8, fg_color="transparent").pack()

    @staticmethod
    def _sum_line(parent, left, right, bold=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=1)
        style = "body_bold" if bold else "body"
        ctk.CTkLabel(row, text=left, font=font(style), anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=right, font=font("price" if bold else style)).pack(side="right")

    def _timeline_card(self, parent):
        box = card(parent)
        box.pack(fill="x", pady=(0, 10))
        label(box, "ความคืบหน้า", "h3").pack(fill="x", padx=16, pady=(12, 4))
        timeline = OrderTimeline(box)
        timeline.pack(fill="x", padx=12, pady=(0, 12))
        timeline.set_order(self._detail)

    def _buyer_card(self, parent):
        d = self._detail
        box = card(parent)
        box.pack(fill="x", pady=(0, 10))
        label(box, "ผู้ซื้อ / ที่อยู่จัดส่ง", "h3").pack(fill="x", padx=16, pady=(12, 4))
        label(box, f"บัญชี: {d.get('buyer_name') or '-'} (@{d.get('buyer_username') or '-'})", "small",
              muted=True).pack(fill="x", padx=16)
        label(box, f"ผู้รับ: {d.get('recipient_name') or '-'}", "body_bold").pack(fill="x", padx=16, pady=(6, 0))
        label(box, f"โทร {format_phone(d.get('recipient_phone'))}", "body").pack(fill="x", padx=16)
        ctk.CTkLabel(box, text=d.get("shipping_address") or "-", font=font("body"), anchor="w", justify="left",
                     wraplength=300).pack(fill="x", padx=16, pady=(2, 12))

    def _payment_card(self, parent):
        d = self._detail
        payment = as_dict(d.get("payment"))
        box = card(parent)
        box.pack(fill="x", pady=(0, 10))
        label(box, "การชำระเงิน (รวม VAT 7%)", "h3").pack(fill="x", padx=16, pady=(12, 4))
        if not payment:
            label(box, "ยังไม่มีการแนบสลิป", "small", muted=True).pack(fill="x", padx=16, pady=(0, 12))
            return
        pay_status = payment.get("status")
        kind = {PAYMENT_STATUS_VERIFIED: "success", PAYMENT_STATUS_REJECTED: "danger"}.get(pay_status, "warning")
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=16)
        pill(row, PAYMENT_STATUS_LABELS.get(pay_status, pay_status or "-"), kind).pack(side="left")
        label(row, f"ยอด {format_price(payment.get('amount'))}", "body_bold").pack(side="right")
        if payment.get("reject_reason"):
            ctk.CTkLabel(box, text=f"เหตุผลที่ปฏิเสธ: {payment.get('reject_reason')}", font=font("small"),
                         text_color=color("danger"), anchor="w", justify="left", wraplength=300).pack(
                fill="x", padx=16, pady=(4, 0))
        slip = payment.get("slip_path")
        if slip:
            image = load_fit_image(slip, 220, 260)
            if image is not None:
                holder = ctk.CTkLabel(box, text="", image=image)
                holder.image = image
                try:
                    holder.configure(cursor="hand2")
                except Exception:  # noqa: BLE001
                    pass
                holder.pack(padx=16, pady=(8, 2))
                holder.bind("<Button-1>", lambda _e: show_image_window(self, slip, f"สลิปออเดอร์ #{d.get('id')}"))
            btn(box, "ดูสลิปขยาย", lambda: show_image_window(self, slip, f"สลิปออเดอร์ #{d.get('id')}"),
                kind="outline").pack(padx=16, pady=(4, 0))
        if d.get("status") == ORDER_STATUS_CHECKING_SLIP and pay_status != PAYMENT_STATUS_VERIFIED:
            btn(box, "ไปหน้าตรวจสลิป (ยืนยัน/ปฏิเสธ)", lambda: self.controller.show("admin_payments"),
                kind="primary").pack(padx=16, pady=(8, 0))
        ctk.CTkFrame(box, height=12, fg_color="transparent").pack()

    def _shipment_card(self, parent):
        d = self._detail
        status = d.get("status")
        if status not in (ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, ORDER_STATUS_COMPLETED):
            return
        shipment = as_dict(d.get("shipment"))
        box = card(parent)
        box.pack(fill="x", pady=(0, 10))
        label(box, "การจัดส่ง & แจ้งเลขพัสดุ", "h3").pack(fill="x", padx=16, pady=(12, 4))

        if status == ORDER_STATUS_COMPLETED:
            label(box, f"ขนส่ง: {shipment.get('carrier') or '-'}", "body").pack(fill="x", padx=16)
            label(box, f"เลขพัสดุ: {shipment.get('tracking_no') or '-'}", "body_bold").pack(fill="x", padx=16)
            label(box, "ส่งถึงผู้รับแล้ว", "small", muted=True).pack(fill="x", padx=16, pady=(2, 12))
            return

        carriers = list(CARRIERS)
        current = shipment.get("carrier") if shipment.get("carrier") in carriers else carriers[0]
        self.carrier_var = ctk.StringVar(value=current)
        label(box, "ขนส่ง", "small", muted=True).pack(fill="x", padx=16)
        option_menu(box, carriers, self.carrier_var, width=200).pack(fill="x", padx=16)
        label(box, "เลขพัสดุ (A-Z, 0-9, - ยาว 4-40 ตัว)", "small", muted=True).pack(fill="x", padx=16, pady=(6, 0))
        self.tracking_entry = entry(box)
        self.tracking_entry.pack(fill="x", padx=16)
        if shipment.get("tracking_no"):
            self.tracking_entry.insert(0, shipment.get("tracking_no"))

        if status == ORDER_STATUS_PAID:
            btn(box, "บันทึกการจัดส่ง + แจ้งเลขพัสดุทางอีเมล", self._ship, kind="primary", size="md").pack(
                fill="x", padx=16, pady=(10, 14))
        else:  # shipped
            btn(box, "อัปเดตเลขพัสดุ", self._update_tracking, kind="outline", size="md").pack(
                fill="x", padx=16, pady=(10, 4))
            btn(box, "ส่งเลขพัสดุทางอีเมลซ้ำ", self._resend_tracking_email, kind="info", size="md").pack(
                fill="x", padx=16, pady=(0, 4))
            btn(box, "ส่งถึงผู้รับแล้ว", self._delivered, kind="success", size="md").pack(
                fill="x", padx=16, pady=(0, 14))

    def _actions_card(self, parent):
        d = self._detail
        status = d.get("status")
        has_receipt = status in RECEIPT_STATUSES
        can_cancel = status in CANCELLABLE
        if status == ORDER_STATUS_CANCELLED:
            box = card(parent)
            box.pack(fill="x", pady=(0, 10))
            label(box, "ออเดอร์ถูกยกเลิก", "h3", text_color=color("danger")).pack(fill="x", padx=16, pady=(12, 2))
            ctk.CTkLabel(box, text=f"เหตุผล: {d.get('cancel_reason') or '-'}", font=font("body"), anchor="w",
                         justify="left", wraplength=300).pack(fill="x", padx=16, pady=(0, 12))
            return
        if not (has_receipt or can_cancel):
            return
        box = card(parent)
        box.pack(fill="x", pady=(0, 10))
        label(box, "ใบเสร็จ & การจัดการ", "h3").pack(fill="x", padx=16, pady=(12, 6))
        if has_receipt:
            self._receipt_btn = btn(box, "สร้าง/เปิดใบเสร็จ PDF (รวม VAT 7%)", self._make_receipt, kind="primary", size="md")
            self._receipt_btn.pack(fill="x", padx=16, pady=(0, 4))
            btn(box, "ส่งใบเสร็จ PDF เข้าอีเมลลูกค้า", self._resend_receipt_email, kind="outline", size="md").pack(
                fill="x", padx=16, pady=(0, 6))
        if can_cancel:
            if status == ORDER_STATUS_PAID:
                ctk.CTkLabel(box, text="ออเดอร์นี้ชำระเงินแล้ว — ถ้ายกเลิกต้องคืนเงินลูกค้าด้วยตนเอง",
                             font=font("small"), text_color=color("danger"), anchor="w", justify="left",
                             wraplength=300).pack(fill="x", padx=16, pady=(0, 4))
            btn(box, "ยกเลิกออเดอร์", self._cancel, kind="danger", size="md").pack(fill="x", padx=16, pady=(0, 14))
        else:
            ctk.CTkFrame(box, height=8, fg_color="transparent").pack()

    def _ship(self):
        self._act(
            shipping_service.ship_order_and_notify,
            self._order_id, self.carrier_var.get(), self.tracking_entry.get().strip(),
        )

    def _update_tracking(self):
        self._act(
            shipping_service.update_tracking,
            self._order_id, self.carrier_var.get(), self.tracking_entry.get().strip(),
        )

    def _resend_receipt_email(self):
        ok, res = self.call(email_outbox_service.send_receipt_email, self._order_id)
        if ok:
            res = as_dict(res)
            dialogs.show_message(self, "ส่งใบเสร็จทางอีเมล", res.get("message", "ดำเนินการส่งใบเสร็จทางอีเมลแล้ว"), kind="info")

    def _resend_tracking_email(self):
        shipment = as_dict(self._detail.get("shipment"))
        ok, res = self.call(
            email_outbox_service.send_tracking_email,
            self._order_id, shipment.get("carrier") or "", shipment.get("tracking_no") or "",
        )
        if ok:
            res = as_dict(res)
            dialogs.show_message(self, "ส่งเลขพัสดุทางอีเมล", res.get("message", "ดำเนินการส่งอีเมลเลขพัสดุแล้ว"), kind="info")

    def _delivered(self):
        if dialogs.confirm(self, "ส่งถึงผู้รับแล้ว", "ยืนยันว่าพัสดุถึงผู้รับแล้ว? ออเดอร์จะเปลี่ยนเป็น \"สำเร็จ\"",
                           confirm_text="ยืนยัน"):
            self._act(shipping_service.mark_delivered, self._order_id)

    def _cancel(self):
        reason = dialogs.ask_reason(self, "ยกเลิกออเดอร์", f"ระบุเหตุผลที่ยกเลิกออเดอร์ #{self._order_id}",
                                    required=True, confirm_text="ยกเลิกออเดอร์", danger=True)
        if reason:
            self._act(order_service.cancel_order, self._order_id, reason)

    def _make_receipt(self):
        self.set_error("")
        order_id = self._order_id
        box = {}

        def work():
            try:
                box["path"] = receipt_service.generate_receipt(order_id)
            except (ValueError, PermissionError) as exc:
                box["error"] = str(exc)
            except Exception as exc:  # noqa: BLE001
                box["error"] = f"สร้างใบเสร็จไม่สำเร็จ: {exc}"

        if self._receipt_btn is not None:
            self._receipt_btn.configure(state="disabled", text="กำลังสร้างใบเสร็จ...")
        threading.Thread(target=work, daemon=True).start()
        self._poll_receipt(box)

    def _poll_receipt(self, box):
        if not self.winfo_exists():
            return
        if not box:
            self.after(150, lambda: self._poll_receipt(box))
            return
        if self._receipt_btn is not None and self._receipt_btn.winfo_exists():
            self._receipt_btn.configure(state="normal", text="สร้าง/เปิดใบเสร็จ PDF (รวม VAT 7%)")
        if "error" in box:
            self.set_error(box["error"])
            return
        if not open_file(box["path"]):
            dialogs.show_message(self, "สร้างใบเสร็จแล้ว", f"เปิดไฟล์อัตโนมัติไม่ได้ — ไฟล์อยู่ที่\n{box['path']}",
                                 kind="info")
