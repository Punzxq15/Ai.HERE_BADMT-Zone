"""
ui/pages/admin/dashboard.py
หน้าแดชบอร์ดแอดมิน/เจ้าของ — route `admin_dashboard` → AdminDashboardPage
- แสดงสลิปรอตรวจ, รายได้ (เฉพาะ owner), จำนวนออเดอร์ตามสถานะ, กราฟแท่งรายวัน, สินค้าขายดี, สินค้าสต็อกต่ำ
- มีปุ่มลัด "📞 ติดต่อเจ้าของร้าน / ส่งข้อความด่วน" สำหรับแอดมิน (ADM-1, ADM-2) และปุ่มรายงาน .xlsx สำหรับเจ้าของร้าน
"""

import customtkinter as ctk

from core.constants import ORDER_STATUS_LABELS, ORDER_STATUSES
from services import order_service, product_service
from ui.components.sidebar import open_owner_contact_dialog
from ui.pages.admin.common import (
    AdminPage, as_dict, btn, card, color, font, is_owner, label, page_header,
    place_grid, resolve_color, stat_card, tk_canvas,
)
from utils.formatters import format_price

PERIODS = {"7 วัน": 7, "14 วัน": 14, "30 วัน": 30}
LIST_LIMIT = 8


class BarChart(ctk.CTkFrame):
    """กราฟแท่งบน Canvas — set_data([(ป้ายวัน, ค่า)], money) แล้ววาดใหม่เมื่อขนาดเปลี่ยน"""

    def __init__(self, parent, height=230):
        super().__init__(parent, fg_color="transparent", height=height)
        self._series = []
        self._money = False
        self.canvas = tk_canvas(self, height=height)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._draw_chart())

    def set_data(self, data, money=False):
        self._series = list(data)
        self._money = money
        self._draw_chart()

    def _draw_chart(self):
        cv = self.canvas
        cv.delete("all")
        bg = resolve_color(self._card_bg())
        cv.configure(bg=bg)
        width, height = cv.winfo_width(), cv.winfo_height()
        if width < 50 or height < 50:
            return
        if not self._series:
            cv.create_text(width / 2, height / 2, text="ยังไม่มีข้อมูล", fill=resolve_color(color("text_muted")),
                           font=font("small"))
            return
        pad_l, pad_r, pad_t, pad_b = 10, 10, 24, 28
        n = len(self._series)
        top = max((v for _, v in self._series), default=0) or 1
        slot = (width - pad_l - pad_r) / n
        bar_w = max(4, slot * 0.6)
        base_y = height - pad_b
        plot_h = base_y - pad_t
        muted = resolve_color(color("text_muted"))
        bar = resolve_color(color("primary"))
        cv.create_line(pad_l, base_y, width - pad_r, base_y, fill=resolve_color(color("border")))
        step = 1 if n <= 10 else (2 if n <= 20 else 5)
        for i, (day, value) in enumerate(self._series):
            cx = pad_l + slot * i + slot / 2
            bar_h = (value / top) * plot_h if value > 0 else 0
            if bar_h > 0:
                cv.create_rectangle(cx - bar_w / 2, base_y - bar_h, cx + bar_w / 2, base_y, fill=bar, width=0)
            if n <= 14 and value > 0:
                cv.create_text(cx, base_y - bar_h - 8, text=f"{value:,.0f}", fill=muted, font=("Arimo", 9))
            if i % step == 0:
                cv.create_text(cx, base_y + 13, text=str(day)[5:] or str(day), fill=muted, font=("Arimo", 9))

    def _card_bg(self):
        try:
            return self.master.cget("fg_color")
        except Exception:  # noqa: BLE001
            return color("surface")


class AdminDashboardPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._days = 7
        _header, actions = page_header(self.content, "แดชบอร์ดจัดการร้าน", "ภาพรวมออเดอร์ สต็อก และยอดขาย")
        self.period = ctk.CTkSegmentedButton(actions, values=list(PERIODS), command=self._on_period)
        self.period.set("7 วัน")
        self.period.pack(side="left", padx=(0, 8))
        btn(actions, "📞 ติดต่อเจ้าของร้าน", lambda: open_owner_contact_dialog(self), kind="danger").pack(
            side="left", padx=(0, 6),
        )
        btn(actions, "🔄 รีเฟรช", self.on_show, kind="outline").pack(side="left")
        self.dynamic = ctk.CTkFrame(self.content, fg_color="transparent")
        self.dynamic.pack(fill="both", expand=True)
        ctk.CTkLabel(self.dynamic, text="กำลังโหลด...", font=font("body")).pack(pady=30)

    def _on_period(self, value):
        self._days = PERIODS.get(value, 7)
        self.on_show()

    def on_show(self, **kwargs):
        if not self.allowed():
            return
        self.set_error("")
        ok, stats = self.call(order_service.get_dashboard_stats, self._days)
        ok_low, low = self.call(product_service.get_low_stock_products)
        for child in self.dynamic.winfo_children():
            child.destroy()
        if not ok:
            ctk.CTkLabel(self.dynamic, text="โหลดข้อมูลไม่สำเร็จ", font=font("body")).pack(pady=30)
            return
        self._render(as_dict(stats), as_dict(low) if ok_low else {})

    def _render(self, stats, low):
        owner = is_owner()
        parent = self.dynamic
        counts = as_dict(stats.get("counts"))
        pending = stats.get("pending_slips")
        pending_n = len(pending) if isinstance(pending, (list, tuple)) else int(pending or 0)

        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x")
        cards = [stat_card(top, "สลิปรอตรวจ", pending_n, "คลิกเพื่อไปตรวจสลิป",
                           command=lambda: self.controller.show("admin_payments"),
                           value_color=color("danger") if pending_n else None)]
        if owner:
            cards += [
                stat_card(top, "รายได้วันนี้", format_price(stats.get("revenue_today"))),
                stat_card(top, "รายได้เดือนนี้", format_price(stats.get("revenue_month"))),
                stat_card(top, "รายได้รวม (คลิกส่งออก .xlsx)", format_price(stats.get("revenue_total")),
                          command=lambda: self.controller.show("admin_settings")),
            ]
        else:
            cards.append(stat_card(top, "รายได้", "—", "แสดงเฉพาะเจ้าของร้าน"))
        place_grid(cards, 4 if owner else 2)

        label(parent, "ออเดอร์ตามสถานะ", "h3").pack(fill="x", pady=(14, 2))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")
        status_cards = []
        for status in ORDER_STATUSES:
            name = ORDER_STATUS_LABELS.get(status, status)
            status_cards.append(stat_card(row, name, int(counts.get(status, 0) or 0),
                                          command=lambda s=status: self.controller.show("admin_orders", status=s)))
        place_grid(status_cards, 3)

        daily = stats.get("daily_sales") or []
        title = f"ยอดขายรายวัน ({self._days} วันล่าสุด)" if owner else f"จำนวนออเดอร์รายวัน ({self._days} วันล่าสุด)"
        label(parent, title, "h3").pack(fill="x", pady=(14, 2))
        chart_card = card(parent)
        chart_card.pack(fill="x")
        chart = BarChart(chart_card)
        chart.pack(fill="x", padx=10, pady=10)
        data = []
        for item in daily:
            d = as_dict(item)
            value = d.get("revenue") if owner else d.get("orders")
            data.append((d.get("day", ""), float(value or 0)))
        chart.set_data(data, money=owner)

        cols = ctk.CTkFrame(parent, fg_color="transparent")
        cols.pack(fill="both", expand=True, pady=(14, 0))
        cols.grid_columnconfigure(0, weight=1, uniform="half")
        cols.grid_columnconfigure(1, weight=1, uniform="half")
        self._top_products(cols, stats.get("top_products") or [], owner).grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._low_stock(cols, low).grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    def _top_products(self, parent, rows, owner):
        box = card(parent)
        label(box, "🏆 สินค้าขายดี", "h3").pack(fill="x", padx=14, pady=(12, 6))
        if not rows:
            label(box, "ยังไม่มีข้อมูลการขาย", "small", muted=True).pack(fill="x", padx=14, pady=(0, 14))
            return box
        for rank, item in enumerate(rows[:LIST_LIMIT], start=1):
            d = as_dict(item)
            line = ctk.CTkFrame(box, fg_color="transparent")
            line.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(line, text=f"{rank}.", width=24, font=font("body_bold"), anchor="w").pack(side="left")
            ctk.CTkLabel(line, text=d.get("product_name", "-"), font=font("body"), anchor="w",
                         wraplength=220, justify="left").pack(side="left", fill="x", expand=True)
            extra = f"{int(d.get('total_qty') or 0):,} ชิ้น"
            if owner:
                extra += f"  ·  {format_price(d.get('total_sales'))}"
            label(line, extra, "small", muted=True).pack(side="right")
        ctk.CTkFrame(box, height=8, fg_color="transparent").pack()
        return box

    def _low_stock(self, parent, low):
        box = card(parent)
        threshold = low.get("threshold", "")
        head = "⚠️ สินค้าสต็อกต่ำ" + (f" (≤ {threshold})" if threshold != "" else "")
        label(box, head, "h3").pack(fill="x", padx=14, pady=(12, 6))
        entries = []
        for item in low.get("products") or []:
            d = as_dict(item)
            entries.append((d.get("name", "-"), d.get("stock", 0), d.get("id")))
        for item in low.get("options") or []:
            d = as_dict(item)
            name = d.get("product_name") or d.get("name") or "-"
            option = f"{d.get('option_type') or ''} {d.get('option_value') or ''}".strip()
            entries.append((f"{name} — {option}" if option else name, d.get("stock", 0), d.get("product_id")))
        if not entries:
            label(box, "ไม่มีสินค้าใกล้หมด 👍", "small", muted=True).pack(fill="x", padx=14, pady=(0, 14))
            return box
        for name, stock, product_id in entries[:LIST_LIMIT]:
            line = ctk.CTkFrame(box, fg_color="transparent")
            line.pack(fill="x", padx=14, pady=2)
            if product_id is not None:
                btn(line, "แก้ไข", lambda p=product_id: self.controller.show("admin_product_form", product_id=p),
                    kind="outline", width=60).pack(side="right")
            stock_text = "หมด" if not stock else f"เหลือ {stock}"
            ctk.CTkLabel(line, text=stock_text, font=font("small_bold"), width=70,
                         text_color=color("danger")).pack(side="right", padx=6)
            ctk.CTkLabel(line, text=name, font=font("body"), anchor="w", wraplength=200,
                         justify="left").pack(side="left", fill="x", expand=True)
        if len(entries) > LIST_LIMIT:
            label(box, f"และอีก {len(entries) - LIST_LIMIT} รายการ — ดูทั้งหมดที่หน้าสินค้า", "tiny",
                  muted=True).pack(fill="x", padx=14, pady=(2, 0))
        ctk.CTkFrame(box, height=8, fg_color="transparent").pack()
        return box
