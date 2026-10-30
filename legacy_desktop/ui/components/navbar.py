"""
ui/components/navbar.py
แถบด้านบนของฝั่งผู้ซื้อและผู้เยี่ยมชม (Guest Storefront):
- ชื่อร้านใน Header ปรับตามที่ Owner ตั้งค่าไว้ (ข้อ 15)
- โลโก้ร้าน 1:1 อยู่ฝั่งซ้ายของชื่อ ขนาดเล็กเท่ากับขนาดตัวหนังสือ แทนที่ไอคอนไม้แบดเดิม (ถ้ายังไม่ได้อัปโหลดใช้ไอคอนเวกเตอร์ไม้แบดเริ่มต้น)
- สีฟอนต์และขนาดตัวอักษรเดิม ช่องค้นหามีไอคอนแว่นขยาย
- ปุ่มดูที่ตั้งหน้าร้าน (ให้ลูกค้าดูที่อยู่หน้าร้านที่ Owner ตั้งค่าไว้ได้สะดวก)
"""

import tkinter as tk
import webbrowser

import customtkinter as ctk

from core.session import Session
from services import settings_service
from ui.components.search_bar import SearchBar
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.image_utils import load_ctk_image
from utils.validators import is_valid_https_url

POLL_MS = 15000
_WHITE = "#FFFFFF"


def _cart_count(user_id):
    from services import cart_service
    return cart_service.get_cart_count(user_id)


def _notification_count():
    from services import notification_service
    return notification_service.unread_count()


def _chat_count():
    from services import chat_service
    return chat_service.unread_count()


def _suggest_products(query: str):
    from services import product_service
    return product_service.suggest_products(query, limit=6)


def _safe(getter):
    try:
        return int(getter() or 0)
    except Exception:  # noqa: BLE001
        return 0


def open_store_location_dialog(parent):
    """หน้าต่างแสดงที่ตั้งหน้าร้าน เวลาเปิด-ปิด และช่องทางติดต่อ ให้ลูกค้าดูได้ (ตามที่ Owner ตั้งค่าไว้)"""
    info = settings_service.get_contact_info()
    shop = settings_service.get_shop_info()
    shop_name = shop.get("shop_name") or "Badminton Pro Shop"
    logo_path = shop.get("shop_logo_path") or ""

    dlg = ctk.CTkToplevel(parent)
    dlg.title(f"ที่ตั้งหน้าร้าน & ข้อมูลร้าน — {shop_name}")
    dlg.geometry("540x460")
    dlg.resizable(False, False)
    dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
    top = parent.winfo_toplevel() if parent is not None else None
    if top is not None:
        dlg.transient(top)

    hdr = ctk.CTkFrame(dlg, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
    hdr.pack(fill="x")
    hdr_row = ctk.CTkFrame(hdr, fg_color="transparent")
    hdr_row.pack(fill="x", padx=20, pady=14)

    if logo_path:
        logo_img = load_ctk_image(logo_path, (44, 44), cover=True, corner_radius=8)
    else:
        logo_img = icon_utils.get_icon("store", 28, "#FFB703", "#FFB703")
    logo_lbl = ctk.CTkLabel(hdr_row, text="", image=logo_img)
    logo_lbl.image = logo_img
    logo_lbl.pack(side="left", padx=(0, 12))

    title_col = ctk.CTkFrame(hdr_row, fg_color="transparent")
    title_col.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(
        title_col, text=shop_name,
        font=ThemeManager.get_font("h2"), text_color=ThemeManager.get_color_pair("primary"), anchor="w",
    ).pack(fill="x")
    ctk.CTkLabel(
        title_col, text="ข้อมูลที่ตั้งหน้าร้าน เวลาทำการ และช่องทางติดต่อ",
        font=ThemeManager.get_font("small"), text_color=_WHITE, anchor="w",
    ).pack(fill="x")

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=20, pady=14)

    addr_card = ThemeManager.make_card(body)
    addr_card.pack(fill="x", pady=(0, 10))
    pin_ic = icon_utils.get_icon("map_pin", 18, "#E63946", "#EF4444")
    ctk.CTkLabel(
        addr_card, text="  ที่อยู่หน้าร้าน (Store Location)", image=pin_ic, compound="left",
        font=ThemeManager.get_font("body_bold"), text_color=ThemeManager.get_color_pair("danger"), anchor="w",
    ).pack(fill="x", padx=16, pady=(12, 4))
    ctk.CTkLabel(
        addr_card, text=info.get("shop_address") or "ยังไม่ได้ระบุที่อยู่หน้าร้าน",
        font=ThemeManager.get_font("body_bold"), text_color=ThemeManager.get_color_pair("text_main"),
        anchor="w", justify="left", wraplength=460,
    ).pack(fill="x", padx=16, pady=(0, 10))

    maps_url = (info.get("maps_url") or "").strip()
    if maps_url and is_valid_https_url(maps_url):
        ctk.CTkButton(
            addr_card, text="เปิดแผนที่หน้าร้าน (Google Maps) ↗",
            command=lambda u=maps_url: webbrowser.open(u),
            **ThemeManager.button_style("primary", "sm"),
        ).pack(anchor="w", padx=16, pady=(0, 12))

    detail_card = ThemeManager.make_card(body)
    detail_card.pack(fill="x")
    rows = [
        ("เวลาเปิด-ปิดทำการ", info.get("shop_hours") or "-"),
        ("เบอร์โทรศัพท์ร้าน", info.get("shop_phone") or "-"),
        ("อีเมลติดต่อ", info.get("shop_email") or "-"),
        ("LINE Official", info.get("line_name") or "-"),
        ("Facebook", info.get("facebook_name") or "-"),
    ]
    for k_txt, v_txt in rows:
        r = ctk.CTkFrame(detail_card, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(
            r, text=k_txt, width=140, anchor="w",
            font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(side="left")
        ctk.CTkLabel(
            r, text=str(v_txt), anchor="w",
            font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(side="left", fill="x", expand=True)

    ctk.CTkButton(
        dlg, text="ปิดหน้าต่าง", width=130, command=dlg.destroy,
        **ThemeManager.button_style("outline", "sm"),
    ).pack(pady=(6, 14))
    dlg.after(120, lambda: (dlg.lift(), dlg.focus_force()))


class Navbar(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, height=68, corner_radius=0, fg_color=ThemeManager.get_color_pair("secondary"))
        self.controller = controller
        self._poll_id = None
        self._badges = {}
        self._logo_img = None

        self.grid_propagate(False)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- โลโก้ + ชื่อร้านตามที่ Owner ตั้งค่าไว้ (ข้อ 15) ---
        self.logo = ctk.CTkButton(
            self, text=" Badminton Pro", font=ThemeManager.get_font("h3"), height=40,
            fg_color="transparent", hover_color=ThemeManager.get_color_pair("secondary_hover"),
            text_color=ThemeManager.get_color_pair("primary"), anchor="w",
            command=lambda: self.controller.show("home"),
        )
        self.logo.grid(row=0, column=0, padx=(14, 4), sticky="w")

        # --- ปุ่มลัดหน้าร้าน + ปุ่มดูที่ตั้งหน้าร้าน ---
        quick_nav = ctk.CTkFrame(self, fg_color="transparent")
        quick_nav.grid(row=0, column=1, padx=4, sticky="w")
        for label, route in (("สินค้าทั้งหมด", "category"), ("เปรียบเทียบไม้", "compare"), ("เลือกไม้ให้เหมาะ", "racket_finder")):
            ctk.CTkButton(
                quick_nav, text=label, height=32, width=92, corner_radius=6,
                font=ThemeManager.get_font("small_bold"),
                fg_color="transparent", hover_color=ThemeManager.get_color_pair("danger"),
                text_color=_WHITE, command=lambda r=route: self.controller.show(r),
            ).pack(side="left", padx=2)

        self._pin_ic = icon_utils.get_icon("map_pin", 15, "#FFB703", "#FFB703")
        ctk.CTkButton(
            quick_nav, text=" ที่ตั้งร้าน", image=self._pin_ic, compound="left",
            height=32, width=84, corner_radius=6,
            font=ThemeManager.get_font("small_bold"),
            fg_color="transparent", hover_color=ThemeManager.get_color_pair("danger"),
            text_color=ThemeManager.get_color_pair("primary"),
            command=lambda: open_store_location_dialog(self),
        ).pack(side="left", padx=2)

        # --- ค้นหาพร้อมไอคอนแว่นขยายและคำแนะนำอัตโนมัติ (ข้อ 15) ---
        self.search = SearchBar(
            self, command=self._search, width=320, height=38,
            suggest_fn=_suggest_products,
            on_select_suggestion=lambda pid, _item: self.controller.show("product_detail", product_id=pid),
        )
        self.search.grid(row=0, column=2, padx=6)

        # --- ไอคอนเวกเตอร์ด้านขวา (ไม่ใช้อิโมจิ — ข้อ 5) ---
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=3, padx=(4, 14), sticky="e")
        self._icon(right, "wishlist", "heart", lambda: self.controller.show("wishlist"))
        self._icon(right, "chat", "chat", lambda: self.controller.show("chat"))
        self._icon(right, "notifications", "bell", lambda: self.controller.show("notifications"))
        self._icon(right, "cart", "cart", lambda: self.controller.show("cart"))
        self._icon(right, "theme", "theme", self._toggle_theme)

        self._user_ic_dark = icon_utils.get_icon("user", 16, ON_PRIMARY, ON_PRIMARY)
        self._key_ic_light = icon_utils.get_icon("key", 16, _WHITE, _WHITE)
        self.user_btn = ctk.CTkButton(
            right, text=" ผู้ใช้", image=self._user_ic_dark, compound="left",
            font=ThemeManager.get_font("small_bold"), width=148, height=36, corner_radius=18,
            fg_color=ThemeManager.get_color_pair("primary"),
            hover_color=ThemeManager.get_color_pair("primary_hover"),
            text_color=ON_PRIMARY, command=self._open_user_menu,
        )
        self.user_btn.pack(side="left", padx=(8, 0))

        # แถบเส้นสีเหลือง-แดงด้านล่าง Navbar
        stripe = ctk.CTkFrame(self, height=3, corner_radius=0, fg_color=ThemeManager.get_color_pair("primary"))
        stripe.grid(row=1, column=0, columnspan=4, sticky="ew")

        self.refresh()
        self._poll_id = self.after(POLL_MS, self._poll)

    def _icon(self, parent, key, icon_name, command):
        holder = ctk.CTkFrame(parent, fg_color="transparent")
        holder.pack(side="left", padx=2)
        ic = icon_utils.get_icon(icon_name, 20, _WHITE, _WHITE)
        btn = ctk.CTkButton(
            holder, text="", image=ic, width=40, height=38, corner_radius=19,
            fg_color="transparent", hover_color=ThemeManager.get_color_pair("secondary_hover"),
            text_color=_WHITE, command=command,
        )
        btn.pack()
        if key != "theme":
            badge = ctk.CTkLabel(
                holder, text="", width=18, height=18, corner_radius=9, font=("Arimo", 10, "bold"),
                fg_color=ThemeManager.get_color_pair("danger"), text_color=_WHITE,
            )
            badge.bind("<Button-1>", lambda _e: command())
            self._badges[key] = badge

    def _set_badge(self, key, count):
        badge = self._badges.get(key)
        if badge is None:
            return
        if count and count > 0:
            badge.configure(text="99+" if count > 99 else str(count), width=18 if count < 10 else 26)
            badge.place(relx=1.0, rely=0.0, x=-2, y=2, anchor="ne")
        else:
            badge.place_forget()

    def _refresh_brand_header(self):
        """ดึงชื่อร้านและโลโก้ 1:1 ที่ Owner ตั้งค่าไว้มาแสดงใน Header (ข้อ 15)"""
        try:
            shop = settings_service.get_shop_info()
            shop_name = (shop.get("shop_name") or "Badminton Pro").strip()
            logo_path = (shop.get("shop_logo_path") or "").strip()
        except Exception:  # noqa: BLE001
            shop_name = "Badminton Pro"
            logo_path = ""

        if logo_path:
            # โลโก้ร้าน 1:1 ขนาดเล็กเท่ากับขนาดตัวหนังสือ แทนที่ไอคอนไม้แบดเดิม
            self._logo_img = load_ctk_image(logo_path, (24, 24), cover=True, corner_radius=5)
        else:
            self._logo_img = icon_utils.get_icon("racket", 22, "#FFB703", "#FFB703")

        self.logo.configure(text=f" {shop_name}", image=self._logo_img, compound="left")

    def refresh(self):
        self._refresh_brand_header()
        user = Session.current_user
        if user and Session.is_authenticated():
            name = (user.get("full_name") or user.get("username") or "").strip()
            short = name if len(name) <= 13 else name[:12] + "…"
            self.user_btn.configure(
                text=f" {short}",
                image=self._user_ic_dark,
                fg_color=ThemeManager.get_color_pair("primary"),
                text_color=ON_PRIMARY,
            )
            user_id = Session.get_user_id()
            self._set_badge("cart", _safe(lambda: _cart_count(user_id)))
            self._set_badge("notifications", _safe(_notification_count))
            self._set_badge("chat", _safe(_chat_count))
        else:
            self.user_btn.configure(
                text=" เข้าสู่ระบบ / สมัคร",
                image=self._key_ic_light,
                fg_color=ThemeManager.get_color_pair("danger"),
                text_color=_WHITE,
            )
            for key in self._badges:
                self._set_badge(key, 0)

    def _poll(self):
        try:
            if self.winfo_exists():
                if self.winfo_ismapped() and Session.is_authenticated():
                    self.refresh()
                self._poll_id = self.after(POLL_MS, self._poll)
        except Exception:  # noqa: BLE001
            self._poll_id = None

    def _search(self, text):
        text = (text or "").strip()
        if text:
            self.controller.show("category", search=text)
        else:
            self.controller.show("home")

    def clear_search(self):
        self.search.clear()

    @staticmethod
    def _toggle_theme():
        ThemeManager.toggle_mode()

    def _open_user_menu(self):
        menu = tk.Menu(self, tearoff=0, font=("Arimo", 11))
        if Session.is_authenticated():
            items = (
                ("โปรไฟล์ของฉัน", "profile"),
                ("ออเดอร์ของฉัน", "orders"),
                ("ที่อยู่จัดส่ง", "addresses"),
                ("รายการโปรด", "wishlist"),
                ("ตัวช่วยเลือกไม้", "racket_finder"),
                ("เปรียบเทียบไม้ (2-5 รุ่น)", "compare"),
                ("แชทกับร้าน / ถาม AI", "chat"),
            )
            for label, route in items:
                menu.add_command(label=label, command=lambda r=route: self.controller.show(r))
            menu.add_command(label="ดูที่ตั้งหน้าร้าน & เวลาทำการ", command=lambda: open_store_location_dialog(self))
            menu.add_separator()
            menu.add_command(label="ออกจากระบบ", command=self.controller.logout)
        else:
            menu.add_command(label="เข้าสู่ระบบ", command=lambda: self.controller.show("login"))
            menu.add_command(label="สมัครสมาชิกใหม่ (OTP)", command=lambda: self.controller.show("register"))
            menu.add_separator()
            menu.add_command(label="ดูที่ตั้งหน้าร้าน & เวลาทำการ", command=lambda: open_store_location_dialog(self))
            menu.add_command(label="ตัวช่วยเลือกไม้", command=lambda: self.controller.show("racket_finder"))
            menu.add_command(label="เปรียบเทียบไม้ (2-5 รุ่น)", command=lambda: self.controller.show("compare"))
        try:
            menu.tk_popup(self.user_btn.winfo_rootx(), self.user_btn.winfo_rooty() + self.user_btn.winfo_height() + 4)
        finally:
            menu.grab_release()

    def destroy(self):
        if self._poll_id is not None:
            try:
                self.after_cancel(self._poll_id)
            except Exception:  # noqa: BLE001
                pass
            self._poll_id = None
        super().destroy()
