"""
ui/app.py
หน้าต่างหลักของแอป: ประกอบ Router + Navbar (ผู้ซื้อ/ผู้เยี่ยมชม) + Sidebar (แอดมิน/เจ้าของ)
พร้อมระบบตรวจ Idle Timeout ล็อกหน้าจออัตโนมัติสำหรับเครื่องหน้าร้าน และการส่งออกรายเดือนอัตโนมัติ
"""

import sys
import traceback
from pathlib import Path
from tkinter import messagebox

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import customtkinter as ctk  # noqa: E402

import config  # noqa: E402
from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_OWNER  # noqa: E402
from core.session import Session  # noqa: E402
from ui.components.navbar import Navbar  # noqa: E402
from ui.components.sidebar import Sidebar  # noqa: E402
from ui.router import GUEST_STOREFRONT_ROUTES, PUBLIC_ROUTES, Router  # noqa: E402
from ui.theme import ThemeManager  # noqa: E402
from utils.font_installer import install_project_fonts  # noqa: E402
from utils.icon_utils import get_icon  # noqa: E402


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. ติดตั้งฟอนต์อัตโนมัติ
        try:
            install_project_fonts()
        except Exception:  # noqa: BLE001
            traceback.print_exc()

        # 2. เริ่มต้นระบบธีม
        ThemeManager.setup()

        # 3. ตั้งค่าพื้นฐานของหน้าต่างแอปพลิเคชัน
        self.title("Badminton Pro Shop — ระบบร้านแบดมินตันครบวงจร")
        w, h = getattr(config, "WINDOW_DEFAULT_SIZE", (1280, 800))
        min_w, min_h = getattr(config, "WINDOW_MIN_SIZE", (960, 620))
        self.geometry(f"{w}x{h}")
        self.minsize(min_w, min_h)
        self.configure(fg_color=ThemeManager.get_color_pair("background"))

        self._idle_check_id = None
        self._lock_dialog = None

        # 4. ฐานข้อมูล + งานตอนเริ่มระบบ
        self._start_backend()

        # 5. โครงหน้าต่าง: navbar (บน) / sidebar (ซ้าย) / container (กลาง)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.container = ctk.CTkFrame(self, fg_color=ThemeManager.get_color_pair("background"), corner_radius=0)
        self.container.grid(row=1, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.router = Router(self.container)
        self.navbar = Navbar(self, self.router)
        self.sidebar = Sidebar(self, self.router)
        self.router.navbar = self.navbar
        self.router.sidebar = self.sidebar
        self.router.add_listener(self._on_route_changed)

        # ดักจับการขยับเมาส์/กดคีย์บอร์ดเพื่ออัปเดตเวลาใช้งานล่าสุด (Idle Timeout)
        for seq in ("<ButtonPress>", "<KeyPress>"):
            self.bind_all(seq, self._on_user_activity, add="+")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.report_callback_exception = self._on_callback_error

        self.router.show("login")
        self._idle_check_id = self.after(15000, self._check_idle_timeout)

    # ------------------------------------------------------------------ เริ่ม/ปิดระบบ
    def _start_backend(self):
        try:
            if hasattr(config, "ensure_dirs"):
                config.ensure_dirs()
            from database import db
            db.init_db()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            messagebox.showerror("เริ่มระบบไม่สำเร็จ", f"เปิดฐานข้อมูลไม่สำเร็จ\n\n{exc}")
            self.destroy()
            raise SystemExit(1) from exc

        try:
            from services import auth_service, coupon_service, export_service, order_service, settings_service
            auth_service.clear_all_online()
            order_service.auto_cancel_unpaid()
            coupon_service.run_daily_noon_reset()
            export_service.auto_export_previous_month()
            shop_info = settings_service.get_shop_info()
            shop_name = shop_info.get("shop_name") or "Badminton Pro Shop"
            self.title(f"{shop_name} — ระบบร้านแบดมินตันครบวงจร")
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    def _on_user_activity(self, _event=None):
        if not Session.is_locked:
            Session.touch()

    def _check_idle_timeout(self):
        try:
            if not self.winfo_exists():
                return
            try:
                from services import coupon_service
                coupon_service.run_daily_noon_reset()
            except Exception:  # noqa: BLE001
                pass
            user = Session.current_user
            role = user.get("role") if user else None
            timeout_min = getattr(config, "ADMIN_IDLE_TIMEOUT_MINUTES", 30)
            if user and role in (ROLE_ADMIN, ROLE_OWNER) and not Session.is_locked:
                if Session.idle_seconds() >= max(60, int(timeout_min) * 60):
                    Session.lock()
                    self._show_lock_screen()
        except Exception:  # noqa: BLE001
            pass
        finally:
            if self.winfo_exists():
                self._idle_check_id = self.after(15000, self._check_idle_timeout)

    def _show_lock_screen(self):
        if self._lock_dialog is not None and self._lock_dialog.winfo_exists():
            return
        dlg = ctk.CTkToplevel(self)
        dlg.title("หน้าจอถูกล็อกอัตโนมัติ (ไม่มีการใช้งาน)")
        dlg.geometry("420x280")
        dlg.resizable(False, False)
        dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
        dlg.transient(self)
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)
        self._lock_dialog = dlg

        user = Session.current_user or {}
        ctk.CTkLabel(
            dlg,
            text="หน้าจอถูกล็อกเพื่อความปลอดภัย",
            image=get_icon("lock", 18, ("#0F172A", "#F8FAFC")),
            compound="left",
            font=ThemeManager.get_font("h2"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(pady=(22, 4))
        ctk.CTkLabel(dlg, text=f"บัญชี: {user.get('username') or user.get('email') or ''}\nกรุณากรอกรหัสผ่านเพื่อปลดล็อก หรือออกจากระบบ",
                     font=ThemeManager.get_font("small"), text_color=ThemeManager.get_color_pair("text_muted")).pack(pady=(0, 12))

        pw_entry = ctk.CTkEntry(dlg, placeholder_text="รหัสผ่านของคุณ", show="•", width=300,
                                **ThemeManager.entry_style())
        pw_entry.pack(pady=4)
        err_lbl = ctk.CTkLabel(dlg, text="", font=ThemeManager.get_font("small"),
                               text_color=ThemeManager.get_color_pair("danger"))
        err_lbl.pack()

        def do_unlock():
            from services import auth_service
            ok, msg = auth_service.verify_active_session_password(pw_entry.get())
            if ok:
                dlg.destroy()
                self._lock_dialog = None
            else:
                err_lbl.configure(text=msg)

        def do_logout():
            dlg.destroy()
            self._lock_dialog = None
            self.router.logout()

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=12)
        ctk.CTkButton(btn_row, text="ปลดล็อก", width=130, command=do_unlock,
                      **ThemeManager.button_style("primary")).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="ออกจากระบบ", width=130, command=do_logout,
                      **ThemeManager.button_style("danger")).pack(side="left", padx=6)
        pw_entry.bind("<Return>", lambda _e: do_unlock())
        dlg.after(150, lambda: (dlg.lift(), dlg.grab_set(), pw_entry.focus_set()))

    def _on_close(self):
        if self._idle_check_id is not None:
            try:
                self.after_cancel(self._idle_check_id)
            except Exception:  # noqa: BLE001
                pass
            self._idle_check_id = None
        try:
            from services import auth_service
            auth_service.clear_all_online()
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        try:
            from utils.backup import auto_backup_on_exit
            auto_backup_on_exit()
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        self.destroy()

    def _on_callback_error(self, exc_type, exc_value, exc_tb):
        traceback.print_exception(exc_type, exc_value, exc_tb)
        try:
            from ui.components import dialogs
            dialogs.show_message(self, "เกิดข้อผิดพลาด", f"{exc_value}", kind="error")
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ แสดง/ซ่อน navbar-sidebar
    def _on_route_changed(self, route, _params):
        try:
            from services import settings_service
            shop_info = settings_service.get_shop_info()
            shop_name = shop_info.get("shop_name") or "Badminton Pro Shop"
            self.title(f"{shop_name} — ระบบร้านแบดมินตันครบวงจร")
        except Exception:  # noqa: BLE001
            pass

        user = Session.current_user
        role = user.get("role") if user else None
        is_buyer_or_guest = (
            route not in PUBLIC_ROUTES
            and (role == ROLE_BUYER or (Session.is_guest() and route in GUEST_STOREFRONT_ROUTES))
        )
        is_staff = bool(user) and route not in PUBLIC_ROUTES and role in (ROLE_ADMIN, ROLE_OWNER)

        if is_buyer_or_guest:
            self.navbar.grid(row=0, column=0, columnspan=2, sticky="ew")
            self.navbar.refresh()
            if route != "category":
                self.navbar.clear_search()
        else:
            self.navbar.grid_remove()

        if is_staff:
            self.sidebar.grid(row=1, column=0, sticky="ns")
            self.sidebar.refresh()
            self.sidebar.set_active(route)
        else:
            self.sidebar.grid_remove()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
