"""
ui/pages/buyer/order_detail.py
หน้ารายละเอียดคำสั่งซื้อ: timeline สถานะ, เลขพัสดุ, รายการสินค้า (+ปุ่มเขียนรีวิว), สรุปราคา (+ VAT 7%),
ยกเลิก / ได้รับสินค้าแล้ว / ใบเสร็จ PDF + ส่งใบเสร็จเข้าอีเมล (E8)
"""

import os
import subprocess
import sys
import threading

import customtkinter as ctk

from core.constants import (
    ORDER_STATUS_CANCELLED, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_COMPLETED, ORDER_STATUS_PAID,
    ORDER_STATUS_PENDING, ORDER_STATUS_SHIPPED,
)
from services import email_outbox_service, order_service, receipt_service, review_service
from ui.components import dialogs
from ui.components.order_timeline import OrderTimeline
from ui.pages.buyer import common
from ui.theme import ThemeManager
from utils.formatters import format_datetime, format_phone, format_price
from utils.image_utils import load_ctk_image, resolve_path

RECEIPT_STATUSES = (ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, ORDER_STATUS_COMPLETED)


def open_file(path):
    """เปิดไฟล์ด้วยโปรแกรมเริ่มต้นของเครื่อง (PDF ใบเสร็จ)"""
    path = str(resolve_path(path))
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class OrderDetailPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._order_id = None
        self._order = None
        self._images = []
        self.receipt_btn = None

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=20, pady=16)

    def on_show(self, order_id=None, **kwargs):
        self._order_id = order_id
        self._load()

    def _load(self, message=None, ok=False):
        try:
            order = order_service.get_order_detail(self._order_id) if self._order_id is not None else None
            if order is None:
                raise ValueError("ไม่พบคำสั่งซื้อ")
        except (ValueError, PermissionError) as exc:
            self._render_error(str(exc))
            return
        self._render(order, message, ok)

    def _clear(self):
        for child in self.body.winfo_children():
            child.destroy()
        self._images = []
        self.receipt_btn = None

    def _render_error(self, text):
        self._clear()
        ctk.CTkLabel(self.body, text=f"⛔ {text}", font=ThemeManager.get_font("body"),
                     text_color=ThemeManager.get_color_pair("danger")).pack(pady=(40, 10))
        ctk.CTkButton(self.body, text="ไปหน้าออเดอร์ของฉัน", width=180, command=lambda: self.controller.show("orders"),
                      **ThemeManager.button_style("primary")).pack()

    def _card(self, parent, title):
        card = ThemeManager.make_card(parent)
        card.pack(fill="x", pady=6)
        ctk.CTkLabel(card, text=title, font=ThemeManager.get_font("h3"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_main")).pack(fill="x", padx=18, pady=(14, 6))
        return card

    def _line(self, parent, text, font="body", color="text_main", pady=(0, 0), wraplength=520):
        label = ctk.CTkLabel(parent, text=text, font=ThemeManager.get_font(font), anchor="w", justify="left",
                             wraplength=wraplength, text_color=ThemeManager.get_color_pair(color))
        label.pack(fill="x", padx=18, pady=pady)
        return label

    def _render(self, order, message=None, ok=False):
        self._order = order
        self._clear()
        status = order["status"]

        head = ctk.CTkFrame(self.body, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkButton(head, text="‹ ย้อนกลับ", width=90, command=lambda: self.controller.go_back(default="orders"),
                      **ThemeManager.button_style("outline", "sm")).pack(side="left")
        ctk.CTkLabel(head, text=f"คำสั่งซื้อ #{order['id']}", font=ThemeManager.get_font("h2"),
                     text_color=ThemeManager.get_color_pair("text_main")).pack(side="left", padx=(8, 12))
        ThemeManager.status_badge(head, status).pack(side="left")
        ctk.CTkLabel(head, text=f"สั่งซื้อเมื่อ {format_datetime(order['created_at'])}", font=ThemeManager.get_font("small"),
                     text_color=ThemeManager.get_color_pair("text_muted")).pack(side="right")

        self.msg_label = common.error_label(self.body, wraplength=800)
        self.msg_label.pack(fill="x", pady=(6, 0))
        if message:
            self.msg_label.configure(
                text=message, text_color=ThemeManager.get_color_pair("success" if ok else "danger"))

        if status == ORDER_STATUS_CANCELLED and order.get("cancel_reason"):
            ctk.CTkLabel(self.body, text=f"เหตุผลที่ยกเลิก: {order['cancel_reason']}", font=ThemeManager.get_font("body_bold"),
                         anchor="w", text_color=ThemeManager.get_color_pair("danger")).pack(fill="x", pady=(2, 0))

        columns = ctk.CTkFrame(self.body, fg_color="transparent")
        columns.pack(fill="both", expand=True, pady=(4, 0))
        columns.grid_columnconfigure(0, weight=1)
        columns.grid_columnconfigure(1, weight=0, minsize=350)
        left = ctk.CTkFrame(columns, fg_color="transparent")
        left.grid(row=0, column=0, sticky="new", padx=(0, 10))
        right = ctk.CTkFrame(columns, fg_color="transparent")
        right.grid(row=0, column=1, sticky="new")

        self._render_timeline(left, order)
        self._render_shipment(left, order)
        self._render_items(left, order)
        self._render_summary(right, order)
        self._render_address(right, order)
        self._render_actions(right, order)

    def _render_timeline(self, parent, order):
        card = self._card(parent, "สถานะคำสั่งซื้อ")
        timeline = OrderTimeline(card)
        timeline.pack(fill="x", padx=14, pady=(0, 12))
        timeline.set_order(order)

    def _render_shipment(self, parent, order):
        shipment = order.get("shipment")
        if not shipment or not (shipment.get("carrier") or shipment.get("tracking_no")):
            return
        card = self._card(parent, "ข้อมูลการจัดส่ง")
        self._line(card, f"บริษัทขนส่ง: {shipment.get('carrier') or '-'}", "body_bold")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(2, 14))
        tracking = shipment.get("tracking_no") or "-"
        ctk.CTkLabel(row, text=f"เลขพัสดุ: {tracking}", font=ThemeManager.get_font("body_bold"),
                     text_color=ThemeManager.get_color_pair("info")).pack(side="left")
        if shipment.get("tracking_no"):
            ctk.CTkButton(row, text="คัดลอก", width=70, command=lambda: self._copy(tracking),
                          **ThemeManager.button_style("outline", "sm")).pack(side="left", padx=10)
        ThemeManager.status_badge(row, shipment["status"]).pack(side="right")

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.msg_label.configure(text="✓ คัดลอกเลขพัสดุแล้ว", text_color=ThemeManager.get_color_pair("success"))

    def _render_items(self, parent, order):
        item_cnt = sum(int(i["qty"]) for i in order.get("items", []))
        card = self._card(parent, f"รายการสินค้า ({item_cnt:,} ชิ้น)")
        uid = common.user_id()
        for item in order["items"]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=6)
            row.grid_columnconfigure(1, weight=1)
            image = load_ctk_image(item.get("image_path"), (60, 80), cover=bool(item.get("image_path")), corner_radius=6)
            self._images.append(image)
            ctk.CTkLabel(row, text="", image=image).grid(row=0, column=0, rowspan=3, padx=(0, 12), sticky="n")
            name = ctk.CTkLabel(row, text=item["product_name"], font=ThemeManager.get_font("body_bold"), anchor="w",
                                justify="left", wraplength=360, text_color=ThemeManager.get_color_pair("text_main"))
            name.grid(row=0, column=1, sticky="w")
            if item.get("product_id"):
                name.bind("<Button-1>", lambda _e, pid=item["product_id"]: self.controller.show("product_detail",
                                                                                                  product_id=pid))
            if item.get("option_label"):
                ctk.CTkLabel(row, text=item["option_label"], font=ThemeManager.get_font("small"), anchor="w",
                             text_color=ThemeManager.get_color_pair("text_muted")).grid(row=1, column=1, sticky="w")
            ctk.CTkLabel(row, text=f"{format_price(item['price_at_purchase'])} × {item['qty']}",
                         font=ThemeManager.get_font("small"), anchor="w",
                         text_color=ThemeManager.get_color_pair("text_muted")).grid(row=2, column=1, sticky="w")
            ctk.CTkLabel(row, text=format_price(item["line_total"]), font=ThemeManager.get_font("body_bold"),
                         text_color=ThemeManager.get_color_pair("text_main")).grid(row=0, column=2, padx=(8, 0), sticky="e")
            if order["status"] == ORDER_STATUS_COMPLETED and self._can_review(uid, item):
                ctk.CTkButton(row, text="เขียนรีวิว", width=106,
                              command=lambda i=item: self.controller.show(
                                  "write_review", product_id=i["product_id"], order_id=order["id"]),
                              **ThemeManager.button_style("primary", "sm")).grid(row=2, column=2, padx=(8, 0), sticky="e")
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _can_review(self, uid, item):
        if not item.get("product_id"):
            return False
        try:
            return review_service.can_review(uid, item["product_id"], self._order["id"])
        except (ValueError, PermissionError):
            return False

    def _render_summary(self, parent, order):
        card = self._card(parent, "สรุปยอดชำระ & ใบเสร็จ (VAT 7%)")
        box = ctk.CTkFrame(card, fg_color="transparent")
        box.pack(fill="x", padx=18, pady=(0, 14))
        box.grid_columnconfigure(1, weight=1)
        discount_label = f"ส่วนลด ({order['coupon_code']})" if order.get("coupon_code") else "ส่วนลด"
        pre_vat = order.get("pre_vat_amount", round(float(order["total"]) / 1.07, 2))
        vat_amt = order.get("vat_amount", round(float(order["total"]) - pre_vat, 2))
        rows = (
            ("ยอดสินค้า", format_price(order["subtotal"]), False),
            (discount_label, f"-{format_price(order['discount'])}" if order["discount"] else "-", False),
            ("ค่าจัดส่ง", "ฟรี" if not order["shipping_fee"] else format_price(order["shipping_fee"]), False),
            ("มูลค่าก่อนภาษี", format_price(pre_vat), False),
            ("ภาษีมูลค่าเพิ่ม (VAT 7%)", format_price(vat_amt), False),
            ("ยอดรวมสุทธิ (รวม VAT 7%)", format_price(order["total"]), True),
        )
        for index, (label, value, big) in enumerate(rows):
            ctk.CTkLabel(box, text=label, font=ThemeManager.get_font("body_bold" if big else "small"), anchor="w",
                         text_color=ThemeManager.get_color_pair("text_main" if big else "text_muted")
                         ).grid(row=index, column=0, sticky="w", pady=2)
            ctk.CTkLabel(box, text=value, font=ThemeManager.get_font("price" if big else "small_bold"), anchor="e",
                         text_color=ThemeManager.get_color_pair("danger" if big else "text_main")
                         ).grid(row=index, column=1, sticky="e", pady=2)
        payment = order.get("payment")
        if payment:
            text = f"การชำระเงิน: {payment['status_label']}"
            if payment.get("status") == "rejected" and payment.get("reject_reason"):
                text += f" — {payment['reject_reason']}"
            self._line(card, text, "small_bold", "text_muted", pady=(0, 12), wraplength=290)

    def _render_address(self, parent, order):
        card = self._card(parent, "ที่อยู่จัดส่ง")
        self._line(card, order["recipient_name"], "body_bold", wraplength=290)
        self._line(card, format_phone(order["recipient_phone"]), "small", "text_muted", wraplength=290)
        self._line(card, order["shipping_address"], "body", pady=(4, 14), wraplength=290)

    def _render_actions(self, parent, order):
        status = order["status"]
        card = ThemeManager.make_card(parent)
        card.pack(fill="x", pady=6)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)
        has_action = False

        def add(text, command, kind):
            nonlocal has_action
            has_action = True
            btn = ctk.CTkButton(inner, text=text, command=command, **ThemeManager.button_style(kind))
            btn.pack(fill="x", pady=3)
            return btn

        if status == ORDER_STATUS_PENDING:
            add("ชำระเงิน / แนบสลิป", lambda: self.controller.show("payment", order_id=order["id"]), "primary")
            add("ยกเลิกคำสั่งซื้อ", self._cancel, "danger")
        elif status == ORDER_STATUS_CHECKING_SLIP:
            add("ดูสถานะการชำระเงิน / สลิป", lambda: self.controller.show("payment", order_id=order["id"]), "outline")
        elif status == ORDER_STATUS_SHIPPED:
            add("✓ ได้รับสินค้าแล้ว", self._received, "success")
        if status in RECEIPT_STATUSES:
            self.receipt_btn = add("เปิดใบเสร็จ PDF (รวม VAT 7%)", self._make_receipt, "primary")
            add("ส่งใบเสร็จเข้าอีเมล", self._email_receipt, "info")
        add("ไปหน้าออเดอร์ของฉัน", lambda: self.controller.show("orders"), "ghost")
        if not has_action:
            card.pack_forget()

    def _cancel(self):
        reason = dialogs.ask_reason(
            self, "ยกเลิกคำสั่งซื้อ", "ระบุเหตุผลที่ต้องการยกเลิก (สินค้าจะถูกคืนเข้าสต็อก)",
            required=True, confirm_text="ยกเลิกคำสั่งซื้อ", danger=True)
        if reason is None:
            return
        try:
            order_service.cancel_order(self._order_id, reason)
        except (ValueError, PermissionError) as exc:
            self._load(f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        self._load("✓ ยกเลิกคำสั่งซื้อแล้ว", ok=True)

    def _received(self):
        if not dialogs.confirm(self, "ยืนยันการรับสินค้า", "ยืนยันว่าได้รับสินค้าครบถ้วนแล้วใช่ไหม?",
                               confirm_text="ได้รับแล้ว"):
            return
        try:
            order_service.confirm_received(self._order_id)
        except (ValueError, PermissionError) as exc:
            self._load(f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        self._load("✓ ขอบคุณที่ใช้บริการ — คุณเขียนรีวิวสินค้าได้แล้ว", ok=True)

    def _email_receipt(self):
        try:
            res = email_outbox_service.send_receipt_email(self._order_id)
            self.msg_label.configure(
                text=f"✓ {res.get('message', 'ดำเนินการส่งใบเสร็จทางอีเมลแล้ว')} (สถานะ: {res.get('status')})",
                text_color=ThemeManager.get_color_pair("success"),
            )
        except Exception as exc:  # noqa: BLE001
            self.msg_label.configure(text=f"⛔ {exc}", text_color=ThemeManager.get_color_pair("danger"))

    def _make_receipt(self):
        if self.receipt_btn is None:
            return
        self.receipt_btn.configure(state="disabled", text="กำลังสร้างใบเสร็จ...")
        order_id = self._order_id
        box = {}

        def work():
            try:
                box["path"] = receipt_service.generate_receipt(order_id)
            except Exception as exc:  # noqa: BLE001
                box["error"] = exc

        threading.Thread(target=work, daemon=True).start()
        self._poll_receipt(box)

    def _poll_receipt(self, box):
        if "path" not in box and "error" not in box:
            try:
                self.after(150, lambda: self._poll_receipt(box))
            except Exception:  # noqa: BLE001
                pass
            return
        try:
            if not self.winfo_exists():
                return
            if self.receipt_btn is not None and self.receipt_btn.winfo_exists():
                self.receipt_btn.configure(state="normal", text="เปิดใบเสร็จ PDF (รวม VAT 7%)")
        except Exception:  # noqa: BLE001
            return
        error = box.get("error")
        if error is not None:
            text = str(error) if isinstance(error, (ValueError, PermissionError)) else f"สร้างใบเสร็จไม่สำเร็จ: {error}"
            self.msg_label.configure(text=f"⛔ {text}", text_color=ThemeManager.get_color_pair("danger"))
            return
        try:
            open_file(box["path"])
        except OSError:
            self.msg_label.configure(text=f"✓ สร้างใบเสร็จแล้ว แต่เปิดไฟล์อัตโนมัติไม่ได้ — ไฟล์อยู่ที่ {box['path']}",
                                     text_color=ThemeManager.get_color_pair("success"))
            return
        self.msg_label.configure(text=f"✓ สร้างใบเสร็จแล้ว ({box['path']})",
                                 text_color=ThemeManager.get_color_pair("success"))
