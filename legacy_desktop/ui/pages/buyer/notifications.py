"""
ui/pages/buyer/notifications.py
หน้าการแจ้งเตือน (ปรับปรุงตามข้อ 14):
- สามารถกดเข้าไปดูแบบคร่าวๆ ได้ (พรีวิวรายละเอียด) และกดปุ่มไปยังหน้าที่เกี่ยวข้องได้ทันที
  (เช่น แจ้งเตือนจ่ายเงิน -> กดแล้วไปหน้าชำระเงินของออเดอร์นั้น)
- ใช้ได้ทุกคน และสำหรับบัญชี Buyer ระบบเก็บการแจ้งเตือนไว้เฉพาะ 10 ครั้งล่าสุดโดยอัตโนมัติ
- ปุ่ม "อ่านทั้งหมด" และตัวเลขแจ้งเตือนที่กระดิ่ง คงเดิม
"""

import customtkinter as ctk

from core.constants import ROLE_BUYER
from core.session import Session
from services import notification_service
from ui.pages.buyer import common
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.formatters import format_datetime

LIMIT = 100


class NotificationsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._expanded_id = None

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 4))
        self.title_box = common.page_title(
            head,
            "การแจ้งเตือน",
            "คลิกที่รายการเพื่อดูรายละเอียดคร่าวๆ หรือกดเปิดหน้าที่เกี่ยวข้อง (เก็บ 10 รายการล่าสุดสำหรับผู้ซื้อ)",
        )
        self.title_box.pack(side="left")
        self.read_all_btn = ctk.CTkButton(
            head, text="อ่านทั้งหมด", width=120, command=self._read_all,
            **ThemeManager.button_style("outline", "sm"),
        )
        self.read_all_btn.pack(side="right")
        self.msg_label = common.error_label(self, wraplength=700)
        self.msg_label.pack(fill="x", padx=20)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=(16, 8), pady=(0, 12))

    # ------------------------------------------------------------------ โหลด/แสดง
    def on_show(self):
        self.msg_label.configure(text="")
        self._load()

    def _load(self):
        for child in self.scroll.winfo_children():
            child.destroy()
        try:
            items = notification_service.list_my(limit=LIMIT)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            self.read_all_btn.configure(state="disabled")
            return
        unread = sum(1 for n in items if not n["is_read"])
        self.read_all_btn.configure(state="normal" if unread else "disabled")
        if not items:
            ctk.CTkLabel(
                self.scroll, text="ยังไม่มีการแจ้งเตือน", font=ThemeManager.get_font("body_bold"),
                text_color=ThemeManager.get_color_pair("text_muted"), justify="center",
            ).pack(pady=60)
            return

        if Session.get_role() == ROLE_BUYER:
            ctk.CTkLabel(
                self.scroll,
                text=f"แสดงการแจ้งเตือน {len(items)} รายการล่าสุด (ระบบเก็บสูงสุด 10 ครั้งล่าสุดสำหรับบัญชีผู้ซื้อ)",
                font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("text_muted"),
                anchor="w",
            ).pack(fill="x", padx=6, pady=(0, 4))

        for item in items:
            self._card(item)

    def _card(self, item):
        unread = not item["is_read"]
        nid = item["id"]
        is_expanded = (self._expanded_id == nid)
        card = ThemeManager.make_card(
            self.scroll,
            border_color=ThemeManager.get_color_pair("primary" if unread else ("info" if is_expanded else "border")),
            border_width=2 if (unread or is_expanded) else 1,
        )
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)

        bell_ic = icon_utils.get_icon("bell", 18, "#FFB703" if unread else "#64748B", "#FFB703" if unread else "#94A3B8")
        dot = ctk.CTkLabel(card, text="", image=bell_ic, width=24)
        dot.grid(row=0, column=0, rowspan=3, padx=(14, 4), pady=12, sticky="n")

        title_txt = item["title"] + ("  [ใหม่]" if unread else "")
        title = ctk.CTkLabel(
            card, text=title_txt, font=ThemeManager.get_font("body_bold" if unread else "body"),
            anchor="w", justify="left", wraplength=540,
            text_color=ThemeManager.get_color_pair("text_main"),
        )
        title.grid(row=0, column=1, sticky="w", padx=(4, 12), pady=(10, 0))
        widgets = [card, dot, title]

        if item.get("message"):
            message = ctk.CTkLabel(
                card, text=item["message"], font=ThemeManager.get_font("small"), anchor="w",
                justify="left", wraplength=540, text_color=ThemeManager.get_color_pair("text_muted"),
            )
            message.grid(row=1, column=1, sticky="w", padx=(4, 12), pady=(2, 0))
            widgets.append(message)

        when = ctk.CTkLabel(
            card, text=format_datetime(item["created_at"]) + "  ·  คลิกเพื่อดูแบบคร่าวๆ",
            font=ThemeManager.get_font("tiny"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_muted"),
        )
        when.grid(row=2, column=1, sticky="w", padx=(4, 12), pady=(2, 8))
        widgets.append(when)

        # ปุ่มลัดทางขวาเพื่อกดไปยังหน้าที่เกี่ยวข้องทันที
        btn_col = ctk.CTkFrame(card, fg_color="transparent")
        btn_col.grid(row=0, column=2, rowspan=3, padx=14, pady=10, sticky="e")
        ctk.CTkButton(
            btn_col,
            text=item.get("action_label") or "เปิดดู ›",
            width=165,
            command=lambda it=item: self._open_target(it),
            **ThemeManager.button_style("primary" if unread else "outline", "sm"),
        ).pack()

        # ส่วนพรีวิวแบบคร่าวๆ เมื่อผู้ใช้คลิกที่การ์ดการแจ้งเตือน (ข้อ 14)
        if is_expanded:
            preview = ctk.CTkFrame(
                card, fg_color=ThemeManager.get_color_pair("surface_alt"), corner_radius=8
            )
            preview.grid(row=3, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 10))
            ctk.CTkLabel(
                preview,
                text=f"พรีวิวรายละเอียด: {item['title']}\n{item.get('message') or '-'}\nเวลาแจ้งเตือน: {format_datetime(item['created_at'])}",
                font=ThemeManager.get_font("small"),
                text_color=ThemeManager.get_color_pair("text_main"),
                anchor="w", justify="left", wraplength=620,
            ).pack(side="left", padx=12, pady=8, fill="x", expand=True)
            ctk.CTkButton(
                preview,
                text=item.get("action_label") or "ไปยังหน้านี้ ›",
                width=175,
                command=lambda it=item: self._open_target(it),
                **ThemeManager.button_style("danger", "sm"),
            ).pack(side="right", padx=12, pady=8)

        for widget in widgets:
            widget.bind("<Button-1>", lambda _e, it=item: self._toggle_preview(it))
            try:
                widget.configure(cursor="hand2")
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------------------ การทำงาน
    def _toggle_preview(self, item: dict):
        nid = item["id"]
        if not item.get("is_read"):
            try:
                notification_service.mark_read(nid)
                self.controller.refresh_shell()
            except Exception:  # noqa: BLE001
                pass
        self._expanded_id = None if self._expanded_id == nid else nid
        self._load()

    def _open_target(self, item: dict):
        nid = item["id"]
        if not item.get("is_read"):
            try:
                notification_service.mark_read(nid)
                self.controller.refresh_shell()
            except Exception:  # noqa: BLE001
                pass
        route = item.get("target_route") or "orders"
        params = item.get("target_params") or {}
        if isinstance(params, dict):
            self.controller.show(route, **params)
        else:
            self.controller.show(route)

    def _mark_read(self, notification_id):
        try:
            notification_service.mark_read(notification_id)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        self._load()

    def _read_all(self):
        try:
            notification_service.mark_all_read()
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self.controller.refresh_shell()
        self._load()
