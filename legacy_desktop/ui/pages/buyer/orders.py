"""
ui/pages/buyer/orders.py
หน้าออเดอร์ของฉัน (BUY-3):
แสดงแท็บสถานะตามลำดับที่กำหนดในเอกสาร:
การสั่งซื้อ → รอชำระเงิน → ชำระเงินแล้ว → รอตรวจสลิป → จัดส่งแล้ว → สำเร็จ → รอรีวิว | สินค้าที่คุณยกเลิก
"""

import customtkinter as ctk

from core.constants import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_DISPLAY_ORDER,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_SHIPPED,
    ORDER_TAB_AWAITING_REVIEW,
)
from services import order_service
from ui.components import dialogs
from ui.pages.buyer import common
from ui.theme import ON_PRIMARY, ThemeManager
from utils.formatters import format_datetime, format_price
from utils.image_utils import load_ctk_image

PAGE_SIZE = 6
MAX_LINES = 2

TABS = ORDER_STATUS_DISPLAY_ORDER


class OrdersPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._status = "all"
        self._page = 1
        self._pages = 1
        self._images = []
        self.tab_buttons = {}
        self._tab_labels = {}

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 4))
        common.page_title(
            head, "📦 ออเดอร์ของฉัน",
            "ติดตามสถานะคำสั่งซื้อ การชำระเงิน การจัดส่ง การรีวิว และรายการสินค้าที่ยกเลิก",
        ).pack(side="left")
        self.msg_label = common.error_label(head, wraplength=420)
        self.msg_label.pack(side="left", padx=16)

        # แถบแท็บสถานะทั้ง 8 แท็บตามลำดับในเอกสาร
        tabs = ctk.CTkFrame(self, fg_color="transparent")
        tabs.pack(fill="x", padx=16, pady=(6, 6))
        for item in TABS:
            status_key, label = item[0], item[1]
            self._tab_labels[status_key] = label
            btn = ctk.CTkButton(
                tabs, text=label, width=106,
                command=lambda s=status_key: self._select_tab(s),
                **self._tab_style(False, is_cancel=(status_key == ORDER_STATUS_CANCELLED)),
            )
            btn.pack(side="left", padx=2, pady=2)
            self.tab_buttons[status_key] = btn

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=(16, 8), pady=(0, 4))

        pager = ctk.CTkFrame(self, fg_color="transparent")
        pager.pack(fill="x", padx=20, pady=(0, 12))
        self.prev_btn = ctk.CTkButton(
            pager, text="‹ ก่อนหน้า", width=100, command=lambda: self._go_page(-1),
            **ThemeManager.button_style("outline", "sm"),
        )
        self.prev_btn.pack(side="left")
        self.page_label = ctk.CTkLabel(
            pager, text="", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        )
        self.page_label.pack(side="left", padx=12)
        self.next_btn = ctk.CTkButton(
            pager, text="ถัดไป ›", width=100, command=lambda: self._go_page(1),
            **ThemeManager.button_style("outline", "sm"),
        )
        self.next_btn.pack(side="left")

    @staticmethod
    def _tab_style(active: bool, is_cancel: bool = False):
        if active:
            kind = "danger" if is_cancel else "primary"
            style = ThemeManager.button_style(kind, "sm")
        else:
            style = ThemeManager.button_style("outline", "sm")
        style.setdefault("border_width", 1 if not active else 0)
        return style

    def on_show(self, status=None, **kwargs):
        try:
            order_service.auto_cancel_unpaid()
        except Exception:  # noqa: BLE001
            pass
        self._status = status if status in self.tab_buttons else "all"
        self._page = 1
        self.msg_label.configure(text="")
        self._load()

    def _select_tab(self, status):
        self._status = status
        self._page = 1
        self.msg_label.configure(text="")
        self._load()

    def _go_page(self, delta):
        self._page = max(1, min(self._pages, self._page + delta))
        self._load()

    def _load(self):
        uid = common.user_id()
        try:
            counts = order_service.count_my_orders_by_tab(uid)
        except Exception:  # noqa: BLE001
            counts = {}

        for status_key, btn in self.tab_buttons.items():
            base_label = self._tab_labels.get(status_key, "")
            cnt = counts.get(status_key, 0)
            txt = f"{base_label} ({cnt})" if cnt else base_label
            btn.configure(
                text=txt,
                **self._tab_style(status_key == self._status, is_cancel=(status_key == ORDER_STATUS_CANCELLED)),
            )

        try:
            result = order_service.list_my_orders(uid, status=self._status, page=self._page, page_size=PAGE_SIZE)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}", text_color=ThemeManager.get_color_pair("danger"))
            result = {"items": [], "total": 0, "page": 1, "pages": 1}
        self._page = result["page"]
        self._pages = result["pages"]
        self._render(result)

    def _render(self, result):
        for child in self.scroll.winfo_children():
            child.destroy()
        self._images = []
        if not result["items"]:
            empty_txt = "ยังไม่มีรายการสินค้าที่คุณยกเลิก" if self._status == ORDER_STATUS_CANCELLED else "ยังไม่มีคำสั่งซื้อในหมวดนี้"
            ctk.CTkLabel(
                self.scroll, text=f"📦\n{empty_txt}", font=ThemeManager.get_font("body_bold"),
                text_color=ThemeManager.get_color_pair("text_muted"), justify="center",
            ).pack(pady=(60, 10))
            ctk.CTkButton(
                self.scroll, text="🛒 เลือกซื้อสินค้า", width=160,
                command=lambda: self.controller.show("category"),
                **ThemeManager.button_style("primary"),
            ).pack()
        for order in result["items"]:
            self._order_card(order)
        self.page_label.configure(text=f"หน้า {self._page}/{self._pages} · ทั้งหมด {result['total']:,} รายการ")
        self.prev_btn.configure(state="normal" if self._page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self._page < self._pages else "disabled")

    def _order_card(self, order):
        card = ThemeManager.make_card(self.scroll)
        card.pack(fill="x", pady=6)
        card.grid_columnconfigure(1, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            header, text=f"คำสั่งซื้อ #{order['id']}", font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(side="left")
        ctk.CTkLabel(
            header, text=format_datetime(order["created_at"]), font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(side="left", padx=12)

        awaiting_rev = int(order.get("awaiting_review_count") or 0)
        if order["status"] == ORDER_STATUS_COMPLETED and awaiting_rev > 0:
            ThemeManager.make_badge(header, f"รอรีวิว ({awaiting_rev})", "primary").pack(side="right", padx=(6, 0))
        ThemeManager.status_badge(header, order["status"]).pack(side="right")

        items = order.get("items") or []
        image = load_ctk_image(items[0].get("image_path") if items else None, (64, 64))
        self._images.append(image)
        ctk.CTkLabel(card, text="", image=image).grid(row=1, column=0, padx=(16, 10), pady=6, sticky="n")

        lines = ctk.CTkFrame(card, fg_color="transparent")
        lines.grid(row=1, column=1, sticky="w", pady=6)
        for item in items[:MAX_LINES]:
            label = item["product_name"] + (f" ({item['option_label']})" if item.get("option_label") else "")
            ctk.CTkLabel(
                lines, text=f"{label} × {item['qty']}", font=ThemeManager.get_font("body_bold"), anchor="w",
                justify="left", wraplength=480, text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x")
        if len(items) > MAX_LINES:
            ctk.CTkLabel(
                lines, text=f"และอีก {len(items) - MAX_LINES} รายการ", font=ThemeManager.get_font("small"),
                anchor="w", text_color=ThemeManager.get_color_pair("text_muted"),
            ).pack(fill="x")
        if order["status"] == ORDER_STATUS_CANCELLED and order.get("cancel_reason"):
            ctk.CTkLabel(
                lines, text=f"เหตุผลที่ยกเลิก: {order['cancel_reason']}",
                font=ThemeManager.get_font("small_bold"), anchor="w",
                text_color=ThemeManager.get_color_pair("danger"),
            ).pack(fill="x", pady=(2, 0))

        total = ctk.CTkFrame(card, fg_color="transparent")
        total.grid(row=1, column=2, sticky="ne", padx=16, pady=6)
        ctk.CTkLabel(
            total, text=f"{order.get('item_count', len(items))} ชิ้น", font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(anchor="e")
        ctk.CTkLabel(
            total, text=format_price(order["total"]), font=ThemeManager.get_font("price"),
            text_color=ThemeManager.get_color_pair("danger"),
        ).pack(anchor="e")

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=2, column=0, columnspan=3, sticky="e", padx=16, pady=(2, 12))
        if order["status"] == ORDER_STATUS_PENDING:
            ctk.CTkButton(
                actions, text="💳 ชำระเงิน", width=110, command=lambda: self._pay(order),
                **ThemeManager.button_style("primary", "sm"),
            ).pack(side="right", padx=(6, 0))
        if order["status"] == ORDER_STATUS_SHIPPED:
            ctk.CTkButton(
                actions, text="✓ ได้รับสินค้าแล้ว", width=135, command=lambda: self._received(order),
                **ThemeManager.button_style("success", "sm"),
            ).pack(side="right", padx=(6, 0))
        if order["status"] == ORDER_STATUS_COMPLETED and awaiting_rev > 0:
            ctk.CTkButton(
                actions, text="⭐ เขียนรีวิวสินค้า", width=135, command=lambda: self._open(order),
                **ThemeManager.button_style("primary", "sm"),
            ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            actions, text="ดูรายละเอียด ›", width=115, command=lambda: self._open(order),
            **ThemeManager.button_style("outline", "sm"),
        ).pack(side="right")

    def _open(self, order):
        self.controller.show("order_detail", order_id=order["id"])

    def _pay(self, order):
        self.controller.show("payment", order_id=order["id"])

    def _received(self, order):
        if not dialogs.confirm(
            self, "ยืนยันการรับสินค้า",
            f"ยืนยันว่าได้รับสินค้าของคำสั่งซื้อ #{order['id']} เรียบร้อยแล้วใช่ไหม?",
            confirm_text="ได้รับแล้ว",
        ):
            return
        try:
            order_service.confirm_received(order["id"])
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}", text_color=ThemeManager.get_color_pair("danger"))
            self._load()
            return
        self.controller.refresh_shell()
        self._load()
        self.msg_label.configure(
            text=f"✓ ยืนยันรับสินค้าคำสั่งซื้อ #{order['id']} แล้ว — เขียนรีวิวได้ที่แท็บ 'รอรีวิว'",
            text_color=ThemeManager.get_color_pair("success"),
        )
