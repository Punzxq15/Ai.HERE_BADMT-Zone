"""
ui/pages/admin/payments.py
ตรวจสลิปโอนเงิน (แอดมิน/เจ้าของ) — route `admin_payments` → AdminPaymentsPage
เมื่อกดยืนยันสลิป จะเรียก payment_service.verify_payment_and_notify เพื่อออกใบเสร็จ PDF ส่งอีเมล และแจกคูปองตามกฎซื้อครบอัตโนมัติ
"""

import customtkinter as ctk

from services import payment_service
from ui.components import dialogs
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, empty_state, font, label, load_fit_image,
    page_header, pill, show_image_window,
)
from utils.formatters import format_datetime, format_price

SLIP_W, SLIP_H = 150, 200


class AdminPaymentsPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        _header, actions = page_header(self.content, "ตรวจสลิปโอนเงิน", "สลิปโอนเงินที่รอการตรวจสอบ (เก่าสุดก่อน)")
        btn(actions, "🔄 รีเฟรช", self._load, kind="outline").pack(side="right")

        self.notice = ctk.CTkLabel(self.content, text="", font=font("small_bold"), text_color=color("success"),
                                   anchor="w", justify="left", wraplength=760)
        self.list_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.list_frame.pack(fill="x")

    def on_show(self, **kwargs):
        if not self.allowed():
            return
        self._set_notice("")
        self._load()

    def _set_notice(self, text):
        if text:
            self.notice.configure(text=text)
            if not self.notice.winfo_ismapped():
                self.notice.pack(fill="x", pady=(0, 8), before=self.list_frame)
        else:
            self.notice.configure(text="")
            self.notice.pack_forget()

    def _load(self, keep_error=False):
        if not keep_error:
            self.set_error("")
        ok, rows = self.call(payment_service.list_pending_payments)
        for child in self.list_frame.winfo_children():
            child.destroy()
        if not ok:
            empty_state(self.list_frame, "โหลดรายการสลิปไม่สำเร็จ")
            return
        rows = [as_dict(r) for r in (rows or [])]
        if not rows:
            empty_state(self.list_frame, "🎉 ไม่มีสลิปที่รอตรวจ")
        else:
            label(self.list_frame, f"รอตรวจ {len(rows)} รายการ", "body_bold").pack(fill="x", pady=(0, 6))
        for payment in rows:
            self._add_card(payment)
        self.refresh_shell()

    def _add_card(self, p):
        payment_id = p.get("id")
        order_id = p.get("order_id")
        amount = p.get("amount")
        order_total = p.get("order_total")
        slip = p.get("slip_path")
        title = f"สลิปออเดอร์ #{order_id}"

        box = card(self.list_frame)
        box.pack(fill="x", pady=4)

        left = ctk.CTkFrame(box, fg_color="transparent")
        left.pack(side="left", padx=14, pady=12)
        image = load_fit_image(slip, SLIP_W, SLIP_H) if slip else None
        if image is not None:
            holder = ctk.CTkLabel(left, text="", image=image)
            holder.image = image
            try:
                holder.configure(cursor="hand2")
            except Exception:  # noqa: BLE001
                pass
            holder.pack()
            holder.bind("<Button-1>", lambda _e, s=slip, t=title: show_image_window(self, s, t))
            btn(left, "🔍 ดูขยาย", lambda s=slip, t=title: show_image_window(self, s, t),
                kind="outline", width=SLIP_W).pack(pady=(6, 0))
        else:
            ctk.CTkLabel(left, text="ไม่พบรูปสลิป", font=font("small"), text_color=color("danger"),
                         width=SLIP_W, height=SLIP_H).pack()

        mid = ctk.CTkFrame(box, fg_color="transparent")
        mid.pack(side="left", fill="both", expand=True, pady=12)
        top = ctk.CTkFrame(mid, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=f"ออเดอร์ #{order_id}", font=font("h3"), anchor="w").pack(side="left")
        pill(top, "รอตรวจสลิป", "warning").pack(side="left", padx=10)
        label(mid, f"ผู้ซื้อ: {p.get('buyer_name') or '-'} (@{p.get('buyer_username') or '-'})", "body").pack(
            fill="x", pady=(4, 0))
        label(mid, f"แนบเมื่อ {format_datetime(p.get('created_at'))}", "small", muted=True).pack(fill="x")
        ctk.CTkLabel(mid, text=f"ยอดที่โอน {format_price(amount)}", font=font("price_big"), anchor="w").pack(
            fill="x", pady=(8, 0))
        label(mid, f"ยอดออเดอร์ {format_price(order_total)}", "small", muted=True).pack(fill="x")
        if self._amount_mismatch(amount, order_total):
            ctk.CTkLabel(mid, text="⚠️ ยอดในระบบไม่ตรงกับยอดออเดอร์ — ตรวจสลิปให้ละเอียด", font=font("small"),
                         text_color=color("danger"), anchor="w").pack(fill="x", pady=(4, 0))
        label(mid, "ตรวจชื่อผู้รับ ยอดเงิน และวันเวลาในสลิปให้ตรงกับออเดอร์ก่อนกดยืนยัน", "tiny", muted=True).pack(
            fill="x", pady=(6, 0))

        right = ctk.CTkFrame(box, fg_color="transparent")
        right.pack(side="right", padx=14, pady=12)
        btn(right, "✅ ยืนยันสลิป", lambda pid=payment_id, oid=order_id, amt=amount: self._verify(pid, oid, amt),
            kind="success", size="md", width=150).pack(pady=(0, 6))
        btn(right, "❌ ปฏิเสธสลิป", lambda pid=payment_id, oid=order_id: self._reject(pid, oid),
            kind="danger", size="md", width=150).pack(pady=(0, 6))
        btn(right, "ดูออเดอร์", lambda oid=order_id: self.controller.show("admin_order_detail", order_id=oid),
            kind="outline", size="md", width=150).pack()

    @staticmethod
    def _amount_mismatch(amount, order_total):
        try:
            return abs(float(amount or 0) - float(order_total or 0)) > 0.005
        except (TypeError, ValueError):
            return False

    def _verify(self, payment_id, order_id, amount):
        if not dialogs.confirm(
            self, "ยืนยันสลิป",
            f"ยืนยันว่าได้รับเงิน {format_price(amount)} ของออเดอร์ #{order_id} แล้วใช่ไหม?\n"
            "ออเดอร์จะเปลี่ยนเป็น “ชำระแล้ว” พร้อมออกใบเสร็จ PDF และพร้อมให้บันทึกการจัดส่ง",
            confirm_text="ยืนยันสลิป",
        ):
            return
        self.set_error("")
        ok, _ = self.call(payment_service.verify_payment_and_notify, payment_id)
        if ok:
            self._set_notice(f"✅ ยืนยันสลิปออเดอร์ #{order_id} แล้ว — ออกใบเสร็จและแจ้งลูกค้าเรียบร้อย")
            self._load()
        else:
            self._load(keep_error=True)

    def _reject(self, payment_id, order_id):
        reason = dialogs.ask_reason(
            self, "ปฏิเสธสลิป", f"ระบุเหตุผลที่ปฏิเสธสลิปของออเดอร์ #{order_id} (ผู้ซื้อจะเห็นข้อความนี้)",
            required=True, confirm_text="ปฏิเสธสลิป",
            placeholder="เช่น ยอดเงินไม่ตรง / สลิปไม่ชัด / ไม่ใช่สลิปของร้านนี้", danger=True,
        )
        if not reason:
            return
        self.set_error("")
        ok, _ = self.call(payment_service.reject_payment, payment_id, reason)
        if ok:
            self._set_notice(f"ปฏิเสธสลิปออเดอร์ #{order_id} แล้ว — ผู้ซื้อจะได้รับแจ้งเตือนให้แนบสลิปใหม่")
            self._load()
        else:
            self._load(keep_error=True)
