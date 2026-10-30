"""
ui/pages/admin/orders.py
รายการออเดอร์ทั้งหมด (แอดมิน/เจ้าของ) — route `admin_orders` → AdminOrdersPage
เรียงตัวเลือกกรองสถานะให้ตรงกับลำดับในเอกสาร (ORDER_STATUS_DISPLAY_ORDER)
"""

import customtkinter as ctk

from core.constants import ORDER_STATUS_DISPLAY_ORDER, ORDER_STATUS_LABELS, ORDER_STATUSES
from services import order_service
from ui.components.search_bar import SearchBar
from ui.pages.admin.common import (
    AdminPage, Pager, as_dict, btn, empty_state, font, label, option_menu,
    page_header, table_header, table_row,
)
from ui.theme import ThemeManager
from utils.formatters import format_datetime, format_price

PAGE_SIZE = 15
ALL_STATUS = "การสั่งซื้อ (ทั้งหมด)"
COLS = [(0, 90), (3, 170), (2, 140), (2, 110), (0, 130), (0, 110)]


class AdminOrdersPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._page = 1
        self._search = ""
        self._status_by_label = {
            item[1]: item[0] for item in ORDER_STATUS_DISPLAY_ORDER if item[0] not in (None, "all")
        }

        _header, actions = page_header(self.content, "จัดการคำสั่งซื้อ (Orders)", "รายการสั่งซื้อทั้งหมดตามลำดับสถานะ")
        btn(actions, "🔄 รีเฟรช", self._reload_from_start, kind="outline").pack(side="right")

        bar = ctk.CTkFrame(self.content, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))
        self.search_bar = SearchBar(bar, command=self._on_search, placeholder="ค้นหาเลขออเดอร์ / ชื่อผู้ซื้อ",
                                    width=280, height=36)
        self.search_bar.pack(side="left", padx=(0, 8))
        self.status_var = ctk.StringVar(value=ALL_STATUS)
        option_menu(bar, [ALL_STATUS] + list(self._status_by_label), self.status_var, self._on_filter,
                    width=190).pack(side="left")

        table_header(self.content, COLS, ["เลขที่", "ผู้ซื้อ", "วันที่สั่ง", "ยอดรวม", "สถานะ", ""])
        self.list_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.list_frame.pack(fill="x")
        self.pager = Pager(self.content, self._goto)
        self.pager.pack(pady=12)

    def on_show(self, status=None, **kwargs):
        if not self.allowed():
            return
        if status in ORDER_STATUSES:
            matched_lbl = next((item[1] for item in ORDER_STATUS_DISPLAY_ORDER if item[0] == status), None)
            self.status_var.set(matched_lbl or ORDER_STATUS_LABELS.get(status, status))
            self._page = 1
        try:
            order_service.auto_cancel_unpaid()
        except Exception:  # noqa: BLE001
            pass
        self._load()

    def _reload_from_start(self):
        self._page = 1
        self._load()

    def _on_search(self, text):
        self._search = (text or "").strip()
        self._page = 1
        self._load()

    def _on_filter(self, _value=None):
        self._page = 1
        self._load()

    def _goto(self, page):
        self._page = page
        self._load()

    def _load(self):
        self.set_error("")
        status = self._status_by_label.get(self.status_var.get())
        ok, result = self.call(order_service.list_orders_admin, status=status, search=self._search or None,
                               page=self._page, page_size=PAGE_SIZE)
        for child in self.list_frame.winfo_children():
            child.destroy()
        if not ok:
            empty_state(self.list_frame, "โหลดรายการออเดอร์ไม่สำเร็จ")
            self.pager.set(1, 1)
            return
        result = as_dict(result)
        items = result.get("items") or []
        if not items:
            empty_state(self.list_frame, "ไม่พบออเดอร์ตามเงื่อนไขที่เลือก")
        for item in items:
            self._add_row(as_dict(item))
        self.pager.set(result.get("page", 1), result.get("pages", 1), result.get("total"))

    def _add_row(self, o):
        row = table_row(self.list_frame, COLS)
        order_id = o.get("id")
        ctk.CTkLabel(row, text=f"#{order_id}", font=font("body_bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=8, pady=10)

        who = ctk.CTkFrame(row, fg_color="transparent")
        who.grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(who, text=o.get("buyer_name") or o.get("recipient_name") or "-", font=font("body"),
                     anchor="w").pack(anchor="w")
        label(who, f"{int(o.get('item_count') or 0)} ชิ้น · @{o.get('buyer_username') or '-'}", "tiny",
              muted=True).pack(anchor="w")

        label(row, format_datetime(o.get("created_at")), "small", muted=True).grid(
            row=0, column=2, sticky="w", padx=8)
        ctk.CTkLabel(row, text=format_price(o.get("total")), font=font("body_bold"), anchor="w").grid(
            row=0, column=3, sticky="w", padx=8)
        ThemeManager.status_badge(row, o.get("status")).grid(row=0, column=4, sticky="w", padx=8)
        btn(row, "ดูรายละเอียด", lambda oid=order_id: self.controller.show("admin_order_detail", order_id=oid),
            kind="outline", width=100).grid(row=0, column=5, sticky="e", padx=8)
