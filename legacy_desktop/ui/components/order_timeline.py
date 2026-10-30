"""
ui/components/order_timeline.py
ไทม์ไลน์สถานะออเดอร์ (เก่า → ใหม่ บนลงล่าง) + ข้อมูลขนส่ง/เลขพัสดุ

ข้อมูลเข้า: order detail จาก order_service.get_order_detail() →
    timeline : list[dict]  (status, note, changed_by_name, created_at)   — เรียงเก่า→ใหม่
    shipment : dict | None (carrier, tracking_no, status, updated_at)

ใช้งาน:
    tl = OrderTimeline(parent)
    tl.set_data(order["timeline"], order.get("shipment"))      # หรือ tl.set_order(order)

รายการล่าสุดจะเน้นสี (สถานะปัจจุบัน); ออเดอร์ที่ยกเลิกใช้สีแดง

ทดสอบเดี่ยว:  python -m ui.components.order_timeline   (รันจาก root โปรเจกต์)
"""

import customtkinter as ctk

from ui.theme import ThemeManager
from utils.formatters import format_datetime

_FALLBACK_LABELS = {
    "pending": "รอชำระเงิน", "checking_slip": "รอตรวจสลิป", "paid": "ชำระเงินแล้ว",
    "shipped": "จัดส่งแล้ว", "completed": "สำเร็จ", "cancelled": "ยกเลิก",
}


def _label(status):
    try:
        from core.constants import ORDER_STATUS_LABELS
        return ORDER_STATUS_LABELS.get(status, status)
    except Exception:  # noqa: BLE001
        return _FALLBACK_LABELS.get(status, str(status))


def _get(row, key, default=None):
    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if value is None else value


class OrderTimeline(ctk.CTkFrame):
    def __init__(self, parent, timeline=None, shipment=None):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.set_data(timeline or [], shipment)

    # ------------------------------------------------------------------ API
    def set_order(self, order: dict):
        """รับ order detail ทั้งก้อน"""
        self.set_data(_get(order, "timeline", []), _get(order, "shipment"))

    def set_data(self, timeline, shipment=None):
        for child in self.winfo_children():
            child.destroy()

        row_index = 0
        if shipment and (_get(shipment, "carrier") or _get(shipment, "tracking_no")):
            box = ThemeManager.make_card(self, fg_color=ThemeManager.get_color_pair("surface_alt"), border_width=0,
                                         corner_radius=10)
            box.grid(row=row_index, column=0, sticky="ew", pady=(0, 10))
            ctk.CTkLabel(
                box, text="🚚 ข้อมูลการจัดส่ง", font=ThemeManager.get_font("body_bold"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x", padx=12, pady=(8, 0))
            ctk.CTkLabel(
                box, anchor="w", justify="left", font=ThemeManager.get_font("body"),
                text=f"ขนส่ง: {_get(shipment, 'carrier', '-')}\nเลขพัสดุ: {_get(shipment, 'tracking_no', '-')}",
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x", padx=12, pady=(2, 8))
            row_index += 1

        entries = list(timeline or [])
        if not entries:
            ctk.CTkLabel(
                self, text="ยังไม่มีความเคลื่อนไหว", font=ThemeManager.get_font("small"),
                text_color=ThemeManager.get_color_pair("text_muted"),
            ).grid(row=row_index, column=0, sticky="w")
            return

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            self._add_row(row_index + i, entry, is_last)

    # ------------------------------------------------------------------ ภายใน
    def _add_row(self, row, entry, is_last):
        status = _get(entry, "status", "")
        cancelled = status == "cancelled"
        dot_color = ThemeManager.get_color_pair("danger" if cancelled else ("primary" if is_last else "star_off"))

        line = ctk.CTkFrame(self, fg_color="transparent")
        line.grid(row=row, column=0, sticky="ew")
        line.grid_columnconfigure(1, weight=1)

        rail = ctk.CTkFrame(line, fg_color="transparent", width=22)
        rail.grid(row=0, column=0, sticky="ns")
        ctk.CTkLabel(rail, text="●", width=22, font=("Arimo", 16 if is_last else 12),
                     text_color=dot_color).pack()
        if not is_last:
            ctk.CTkFrame(rail, width=2, height=1, fg_color=ThemeManager.get_color_pair("border")).pack(
                fill="y", expand=True)

        text_box = ctk.CTkFrame(line, fg_color="transparent")
        text_box.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 10))
        title_color = "danger" if cancelled else "text_main"
        ctk.CTkLabel(
            text_box, text=_label(status),
            font=ThemeManager.get_font("body_bold" if is_last else "body"), anchor="w",
            text_color=ThemeManager.get_color_pair(title_color if is_last else "text_muted"),
        ).pack(fill="x")

        meta = format_datetime(_get(entry, "created_at"))
        who = _get(entry, "changed_by_name")
        if who:
            meta += f" · โดย {who}"
        ctk.CTkLabel(
            text_box, text=meta, font=ThemeManager.get_font("small"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(fill="x")

        note = _get(entry, "note")
        if note:
            ctk.CTkLabel(
                text_box, text=str(note), font=ThemeManager.get_font("small"), anchor="w", justify="left",
                wraplength=360, text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x", pady=(2, 0))


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("420x520")
    demo_timeline = [
        dict(status="pending", note="สร้างออเดอร์", changed_by_name="buyer1", created_at="2026-10-11 07:12:00"),
        dict(status="checking_slip", note="แนบสลิปแล้ว", changed_by_name="buyer1", created_at="2026-10-11 07:20:00"),
        dict(status="paid", note="ตรวจสลิปผ่าน", changed_by_name="admin1", created_at="2026-10-11 08:00:00"),
        dict(status="shipped", note="ส่งกับ Kerry", changed_by_name="admin1", created_at="2026-10-12 09:30:00"),
    ]
    tl = OrderTimeline(root)
    tl.pack(fill="x", padx=20, pady=20)
    tl.set_data(demo_timeline, dict(carrier="Kerry", tracking_no="KE123456789"))
    root.mainloop()
