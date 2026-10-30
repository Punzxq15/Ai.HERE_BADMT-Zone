"""
ui/components/sidebar.py
เมนูด้านข้างของฝั่งแอดมิน/เจ้าของ — เมนูต่างกันตาม role:
    admin + owner : แดชบอร์ด, ออเดอร์, ตรวจสลิป, สินค้า, แชทลูกค้า, การแจ้งเตือน + ปุ่ม "ติดต่อเจ้าของร้าน" (ADM-1, ADM-2)
    owner เท่านั้น : หมวดหมู่/แบรนด์, คูปอง/กฎคูปอง, ผู้ใช้/แอดมิน, ตั้งค่าร้าน/รายงาน/แบนเนอร์/Audit
"""

import webbrowser

import customtkinter as ctk

from core.constants import ROLE_LABELS, ROLE_OWNER
from core.session import Session
from services import settings_service
from ui.components import dialogs
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.image_utils import load_ctk_image
from utils.validators import is_valid_https_url

POLL_MS = 15000
_WHITE = "#FFFFFF"

_STAFF_MENU = (
    ("admin_dashboard", "chart", "แดชบอร์ด", None),
    ("admin_orders", "order", "ออเดอร์", None),
    ("admin_payments", "receipt", "ตรวจสลิป", "slips"),
    ("admin_products", "racket", "สินค้า / กู้คืนสินค้า", None),
    ("admin_chat", "chat", "แชทลูกค้า", "chat"),
    ("notifications", "bell", "การแจ้งเตือน", "notifications"),
)
_OWNER_MENU = (
    ("admin_categories", "category", "หมวดหมู่ / แบรนด์", None),
    ("admin_coupons", "coupon", "คูปอง / กฎคูปอง", None),
    ("admin_users", "users", "ผู้ใช้ / แอดมิน", None),
    ("admin_settings", "settings", "ตั้งค่า / รายงาน / ระบบ", None),
)
ROUTE_PARENT = {
    "admin_product_form": "admin_products",
    "admin_order_detail": "admin_orders",
    "admin_coupon_form": "admin_coupons",
}


def _slip_count():
    from services import payment_service
    return len(payment_service.list_pending_payments())


def _chat_count():
    from services import chat_service
    return chat_service.unread_count()


def _notification_count():
    from services import notification_service
    return notification_service.unread_count()


_COUNTERS = {"slips": _slip_count, "chat": _chat_count, "notifications": _notification_count}


def _safe(getter):
    try:
        return int(getter() or 0)
    except Exception:  # noqa: BLE001
        return 0


def open_owner_contact_dialog(parent):
    """หน้าต่างข้อมูลติดต่อเจ้าของร้าน ที่ตั้งหน้าร้าน + ส่งอีเมลด่วนถึงเจ้าของร้าน (ADM-1, ADM-2)"""
    from services import contact_service

    info = contact_service.get_owner_contact_info()
    contact_full = settings_service.get_contact_info()
    dlg = ctk.CTkToplevel(parent)
    dlg.title("ข้อมูลติดต่อเจ้าของร้าน & ที่ตั้งหน้าร้าน")
    dlg.geometry("540x630")
    dlg.resizable(False, False)
    dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
    top = parent.winfo_toplevel() if parent is not None else None
    if top is not None:
        dlg.transient(top)

    # Header สีดำ-เหลือง-แดง
    hdr = ctk.CTkFrame(dlg, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
    hdr.pack(fill="x")
    ctk.CTkLabel(
        hdr, text="ข้อมูลติดต่อเจ้าของร้าน & ที่ตั้งหน้าร้าน",
        font=ThemeManager.get_font("h3"), text_color=ThemeManager.get_color_pair("primary"),
    ).pack(anchor="w", padx=20, pady=(14, 2))
    ctk.CTkLabel(
        hdr, text=f"ร้าน: {info.get('shop_name') or 'Badminton Pro Shop'}",
        font=ThemeManager.get_font("small"), text_color=_WHITE,
    ).pack(anchor="w", padx=20, pady=(0, 12))

    body = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=18, pady=12)

    card = ThemeManager.make_card(body)
    card.pack(fill="x", pady=(0, 12))

    rows = [
        ("เบอร์โทรศัพท์", info.get("phone") or "-", None),
        ("อีเมลเจ้าของร้าน", info.get("email") or "-", None),
        ("ที่อยู่หน้าร้าน", contact_full.get("shop_address") or "-", contact_full.get("maps_url") or ""),
        ("เวลาทำการ", contact_full.get("shop_hours") or "-", None),
        ("LINE Official / ID", info.get("line_id") or "-", None),
        ("Facebook", info.get("facebook_name") or "-", info.get("facebook_url") or ""),
        ("Instagram", info.get("instagram_name") or "-", info.get("instagram_url") or ""),
    ]
    for label, val, url in rows:
        r = ctk.CTkFrame(card, fg_color="transparent")
        r.pack(fill="x", padx=14, pady=5)
        ctk.CTkLabel(
            r, text=label, width=145, anchor="w",
            font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(side="left")
        ctk.CTkLabel(
            r, text=str(val), anchor="w", justify="left", wraplength=250,
            font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(side="left", fill="x", expand=True)
        if url and is_valid_https_url(url):
            ctk.CTkButton(
                r, text="เปิดลิงก์ ↗", width=86,
                command=lambda u=url: webbrowser.open(u),
                **ThemeManager.button_style("info", "sm"),
            ).pack(side="right")

    # ฟอร์มส่งอีเมลด่วนถึงเจ้าของร้าน (เฉพาะ Admin/Owner ที่ล็อกอิน)
    if Session.is_authenticated():
        mail_card = ThemeManager.make_card(body)
        mail_card.pack(fill="x", pady=(4, 8))
        ctk.CTkLabel(
            mail_card, text="ส่งอีเมลด่วนถึงเจ้าของร้าน",
            font=ThemeManager.get_font("h3"), text_color=ThemeManager.get_color_pair("danger"),
        ).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(
            mail_card, text="หัวข้อเรื่อง", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(anchor="w", padx=14)
        subj_entry = ctk.CTkEntry(
            mail_card, placeholder_text="เช่น แจ้งปัญหาสลิปโอนเงิน / สินค้าสต็อกด่วน",
            **ThemeManager.entry_style(36),
        )
        subj_entry.pack(fill="x", padx=14, pady=(2, 8))

        ctk.CTkLabel(
            mail_card, text="รายละเอียดข้อความ", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(anchor="w", padx=14)
        msg_box = ctk.CTkTextbox(
            mail_card, height=95, wrap="word",
            **{k: v for k, v in ThemeManager.entry_style().items() if k != "height"},
        )
        msg_box.pack(fill="x", padx=14, pady=(2, 8))

        status_lbl = ctk.CTkLabel(
            mail_card, text="", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_muted"), wraplength=440,
        )
        status_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        def do_send():
            subj = subj_entry.get().strip()
            msg = msg_box.get("1.0", "end").strip()
            if not subj or not msg:
                status_lbl.configure(text="กรุณากรอกทั้งหัวข้อและรายละเอียดข้อความ", text_color=ThemeManager.get_color_pair("danger"))
                return
            if not dialogs.confirm(dlg, "ยืนยันการส่งอีเมลถึงเจ้าของร้าน", f"หัวข้อ: {subj}\n\nต้องการส่งข้อความนี้ถึงเจ้าของร้านใช่หรือไม่?"):
                return
            try:
                res = contact_service.send_urgent_email_to_owner(subj, msg)
                status_lbl.configure(text=res.get("message", "ส่งข้อความเรียบร้อยแล้ว"), text_color=ThemeManager.get_color_pair("success"))
                subj_entry.delete(0, "end")
                msg_box.delete("1.0", "end")
            except Exception as exc:  # noqa: BLE001
                status_lbl.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))

        btn_bar = ctk.CTkFrame(mail_card, fg_color="transparent")
        btn_bar.pack(fill="x", padx=14, pady=(2, 12))
        ctk.CTkButton(
            btn_bar, text="ส่งข้อความถึงเจ้าของร้าน", command=do_send,
            **ThemeManager.button_style("danger", "md"),
        ).pack(side="right")

    ctk.CTkButton(
        dlg, text="ปิดหน้าต่าง", width=130, command=dlg.destroy,
        **ThemeManager.button_style("outline", "sm"),
    ).pack(pady=(0, 12))
    dlg.after(120, lambda: (dlg.lift(), dlg.focus_force()))


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, controller, width=240):
        super().__init__(parent, width=width, corner_radius=0, fg_color=ThemeManager.get_color_pair("secondary"))
        self.controller = controller
        self._built_role = None
        self._active = None
        self._buttons = {}
        self._button_icons = {}
        self._badges = {}
        self._poll_id = None
        self._logo_img = None

        self.pack_propagate(False)

        self.brand_label = ctk.CTkLabel(
            self, text=" Badminton Pro", font=ThemeManager.get_font("h3"),
            text_color=ThemeManager.get_color_pair("primary"), anchor="w",
        )
        self.brand_label.pack(fill="x", padx=18, pady=(18, 2))
        self.role_label = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("small_bold"),
            text_color="#E2E8F0", anchor="w",
        )
        self.role_label.pack(fill="x", padx=18, pady=(0, 8))

        # แถบสีเหลือง-แดงคั่นหัวเมนู
        ctk.CTkFrame(self, height=3, fg_color=ThemeManager.get_color_pair("danger")).pack(fill="x", padx=14, pady=(0, 10))

        self.menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.menu_frame.pack(fill="both", expand=True, padx=10)

        # ส่วนล่าง: ติดต่อเจ้าของร้าน + ชื่อผู้ใช้ + ธีม + ออกจากระบบ
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=10, pady=(6, 14))

        self._phone_ic = icon_utils.get_icon("phone", 16, _WHITE, _WHITE)
        ctk.CTkButton(
            bottom, text="  ติดต่อเจ้าของร้าน", image=self._phone_ic, compound="left",
            anchor="w", height=34, corner_radius=8,
            font=ThemeManager.get_font("small_bold"),
            fg_color=ThemeManager.get_color_pair("danger"),
            hover_color=ThemeManager.get_color_pair("danger_hover"),
            text_color=_WHITE,
            command=lambda: open_owner_contact_dialog(self),
        ).pack(fill="x", pady=(0, 8))

        self._user_ic = icon_utils.get_icon("user", 16, "#FFB703", "#FFB703")
        self.user_label = ctk.CTkLabel(
            bottom, text="", image=self._user_ic, compound="left",
            font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("primary"), anchor="w",
        )
        self.user_label.pack(fill="x", padx=8, pady=(0, 6))

        self._theme_ic = icon_utils.get_icon("theme", 16, _WHITE, _WHITE)
        ctk.CTkButton(
            bottom, text="  สลับโหมดมืด/สว่าง", image=self._theme_ic, compound="left",
            anchor="w", height=32, corner_radius=8,
            font=ThemeManager.get_font("small"), fg_color="transparent",
            hover_color=ThemeManager.get_color_pair("secondary_hover"), text_color=_WHITE,
            command=ThemeManager.toggle_mode,
        ).pack(fill="x")

        self._logout_ic = icon_utils.get_icon("logout", 16, _WHITE, _WHITE)
        ctk.CTkButton(
            bottom, text="  ออกจากระบบ", image=self._logout_ic, compound="left",
            anchor="w", height=32, corner_radius=8,
            font=ThemeManager.get_font("small_bold"), fg_color="transparent",
            hover_color=ThemeManager.get_color_pair("danger"), text_color=_WHITE,
            command=lambda: self.controller.logout(),
        ).pack(fill="x", pady=(2, 0))

        self.refresh()
        self._poll_id = self.after(POLL_MS, self._poll)

    def _build_menu(self, role):
        for child in self.menu_frame.winfo_children():
            child.destroy()
        self._buttons.clear()
        self._button_icons.clear()
        self._badges.clear()

        for entry in _STAFF_MENU:
            self._add_item(*entry)
        if role == ROLE_OWNER:
            ctk.CTkLabel(
                self.menu_frame, text="เฉพาะเจ้าของร้าน (OWNER)", font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("primary"), anchor="w",
            ).pack(fill="x", padx=10, pady=(12, 2))
            for entry in _OWNER_MENU:
                self._add_item(*entry)
        self._built_role = role
        self._paint_active()

    def _add_item(self, route, icon_name, text, counter):
        row = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        row.pack(fill="x", pady=1)
        ic_white = icon_utils.get_icon(icon_name, 18, _WHITE, _WHITE)
        ic_dark = icon_utils.get_icon(icon_name, 18, ON_PRIMARY, ON_PRIMARY)
        self._button_icons[route] = (ic_white, ic_dark)
        btn = ctk.CTkButton(
            row, text=f"  {text}", image=ic_white, compound="left",
            anchor="w", height=38, corner_radius=8,
            font=ThemeManager.get_font("body_bold"), fg_color="transparent",
            hover_color=ThemeManager.get_color_pair("secondary_hover"), text_color=_WHITE,
            command=lambda r=route: self.controller.show(r),
        )
        btn.pack(fill="x")
        self._buttons[route] = btn
        if counter:
            badge = ctk.CTkLabel(
                row, text="", width=22, height=20, corner_radius=10,
                font=("Arimo", 10, "bold"),
                fg_color=ThemeManager.get_color_pair("danger"), text_color=_WHITE,
            )
            badge.bind("<Button-1>", lambda _e, r=route: self.controller.show(r))
            self._badges[route] = (counter, badge)

    def set_active(self, route):
        self._active = ROUTE_PARENT.get(route, route)
        self._paint_active()

    def _paint_active(self):
        for route, btn in self._buttons.items():
            ic_white, ic_dark = self._button_icons.get(route, (None, None))
            if route == self._active:
                btn.configure(fg_color=ThemeManager.get_color_pair("primary"), text_color=ON_PRIMARY, image=ic_dark)
            else:
                btn.configure(fg_color="transparent", text_color=_WHITE, image=ic_white)

    def refresh(self):
        try:
            shop = settings_service.get_shop_info()
            shop_name = (shop.get("shop_name") or "Badminton Pro").strip()
            logo_path = (shop.get("shop_logo_path") or "").strip()
        except Exception:  # noqa: BLE001
            shop_name = "Badminton Pro"
            logo_path = ""
        if logo_path:
            self._logo_img = load_ctk_image(logo_path, (24, 24), cover=True, corner_radius=5)
        else:
            self._logo_img = icon_utils.get_icon("racket", 22, "#FFB703", "#FFB703")
        self.brand_label.configure(text=f" {shop_name}", image=self._logo_img, compound="left")

        user = Session.current_user
        role = user.get("role") if user else None
        if user:
            self.user_label.configure(text=f"  {user.get('full_name') or user.get('username') or ''}")
            self.role_label.configure(text=f"สถานะ: {ROLE_LABELS.get(role, role or '')}")
        else:
            self.user_label.configure(text="")
            self.role_label.configure(text="")
        if role != self._built_role:
            self._build_menu(role)
        for route, (counter, badge) in self._badges.items():
            count = _safe(_COUNTERS[counter]) if user else 0
            if count > 0:
                badge.configure(text="99+" if count > 99 else str(count), width=22 if count < 10 else 32)
                badge.place(relx=1.0, rely=0.5, x=-10, anchor="e")
            else:
                badge.place_forget()

    def _poll(self):
        try:
            if self.winfo_exists():
                if self.winfo_ismapped() and Session.is_authenticated():
                    self.refresh()
                self._poll_id = self.after(POLL_MS, self._poll)
        except Exception:  # noqa: BLE001
            self._poll_id = None

    def destroy(self):
        if self._poll_id is not None:
            try:
                self.after_cancel(self._poll_id)
            except Exception:  # noqa: BLE001
                pass
            self._poll_id = None
        super().destroy()
