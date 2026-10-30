"""
ui/pages/buyer/login.py
หน้าเข้าสู่ระบบ (Login) แบบ 2 คอลัมน์ (AuthSplitLayout):
- รองรับล็อกอินด้วยชื่อผู้ใช้หรืออีเมล
- รองรับข้อความแจ้งเตือนหลังสมัครสมาชิกสำเร็จ (AUTH-3) หรือเมื่อผู้เยี่ยมชมกดฟีเจอร์ที่ต้องล็อกอิน (AUTH-2)
- มีปุ่ม "ลืมรหัสผ่าน (ลูกค้า — รับ OTP ทางอีเมล)" (AUTH-5)
- มีปุ่ม "ลืมรหัสผ่านแอดมิน / ติดต่อเจ้าของร้าน" (E9)
"""

import customtkinter as ctk

from services import auth_service
from ui.components.auth_layout import AuthSplitLayout
from ui.components.sidebar import open_owner_contact_dialog
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils


class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller

        self.layout = AuthSplitLayout(
            self, controller,
            form_title="เข้าสู่ระบบ",
            form_subtitle="เข้าสู่ระบบเพื่อสั่งซื้อสินค้า เก็บคูปองส่วนลด และติดตามสถานะพัสดุ",
            center_vertically=True,
        )
        self.layout.pack(fill="both", expand=True)
        body = self.layout.form_body

        # แถบข้อความแจ้งสถานะ (เช่น สมัครสมาชิกสำเร็จ หรือกรุณาเข้าสู่ระบบ)
        self.banner_frame = ctk.CTkFrame(
            body, fg_color=ThemeManager.get_color_pair("success"), corner_radius=8,
        )
        self.banner_label = ctk.CTkLabel(
            self.banner_frame, text="", font=ThemeManager.get_font("small_bold"),
            text_color="#FFFFFF", wraplength=360, justify="left",
        )
        self.banner_label.pack(padx=12, pady=8)

        # ช่องกรอกชื่อผู้ใช้หรืออีเมล
        ctk.CTkLabel(
            body, text="ชื่อผู้ใช้ หรือ อีเมล", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"), anchor="w",
        ).pack(fill="x", pady=(6, 2))
        self.username_entry = ctk.CTkEntry(
            body, placeholder_text="กรอกชื่อผู้ใช้หรืออีเมลของคุณ",
            **ThemeManager.entry_style(42),
        )
        self.username_entry.pack(fill="x", pady=(0, 10))
        self.username_entry.bind("<Return>", lambda _e: self.handle_login())

        # ช่องกรอกรหัสผ่าน
        ctk.CTkLabel(
            body, text="รหัสผ่าน", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"), anchor="w",
        ).pack(fill="x", pady=(2, 2))
        self.password_entry = ctk.CTkEntry(
            body, placeholder_text="กรอกรหัสผ่าน", show="•",
            **ThemeManager.entry_style(42),
        )
        self.password_entry.pack(fill="x", pady=(0, 6))
        self.password_entry.bind("<Return>", lambda _e: self.handle_login())

        # ปุ่มลืมรหัสผ่าน (ลูกค้า OTP / แอดมินติดต่อเจ้าของร้าน)
        forgot_row = ctk.CTkFrame(body, fg_color="transparent")
        forgot_row.pack(fill="x", pady=(0, 6))
        self._key_ic = icon_utils.get_icon("key", 15, "#111318", "#F8FAFC")
        self._shield_ic = icon_utils.get_icon("shield", 15, "#111318", "#F8FAFC")
        ctk.CTkButton(
            forgot_row, text=" ลืมรหัสผ่าน (รับรหัส OTP)", image=self._key_ic, compound="left", width=165,
            command=self._open_forgot_password_dialog,
            **ThemeManager.button_style("ghost", "sm"),
        ).pack(side="left")
        ctk.CTkButton(
            forgot_row, text=" แอดมินลืมรหัส / ติดต่อเจ้าของ", image=self._shield_ic, compound="left", width=185,
            command=lambda: open_owner_contact_dialog(self),
            **ThemeManager.button_style("ghost", "sm"),
        ).pack(side="right")

        # ข้อความแจ้งข้อผิดพลาด
        self.error_label = ctk.CTkLabel(
            body, text="", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("danger"), wraplength=380, justify="left",
        )
        self.error_label.pack(fill="x", pady=(2, 8))

        # ปุ่มเข้าสู่ระบบหลัก (สีเหลือง ตัวอักษรดำเข้ม)
        self.login_btn = ctk.CTkButton(
            body, text="เข้าสู่ระบบ", command=self.handle_login,
            **ThemeManager.button_style("primary", "lg"),
        )
        self.login_btn.pack(fill="x", pady=(0, 10))

        # ปุ่มสมัครสมาชิกใหม่ (สีแดงสปอร์ต ตัวอักษรขาว)
        self._reg_ic = icon_utils.get_icon("edit", 16, "#FFFFFF", "#FFFFFF")
        self.register_btn = ctk.CTkButton(
            body, text=" ยังไม่มีบัญชี? สมัครสมาชิกใหม่ (ยืนยันอีเมล OTP)",
            image=self._reg_ic, compound="left",
            command=lambda: self.controller.show("register"),
            **ThemeManager.button_style("danger", "md"),
        )
        self.register_btn.pack(fill="x", pady=(0, 8))

        # ปุ่มดูสินค้าโดยไม่ต้องล็อกอิน
        self._shop_ic = icon_utils.get_icon("store", 16, "#111318", "#F8FAFC")
        ctk.CTkButton(
            body, text=" เข้าชมสินค้าในร้านโดยไม่ล็อกอิน",
            image=self._shop_ic, compound="left",
            command=lambda: self.controller.enter_guest_storefront("home"),
            **ThemeManager.button_style("outline", "md"),
        ).pack(fill="x")

    def handle_login(self):
        identifier = self.username_entry.get().strip()
        password = self.password_entry.get()
        self.error_label.configure(text="")

        if not identifier or not password:
            self.error_label.configure(text="กรุณากรอกชื่อผู้ใช้และรหัสผ่านให้ครบถ้วน")
            return

        self.login_btn.configure(state="disabled")
        try:
            user = auth_service.login(identifier, password)
            self.controller.go_after_login(user)
        except ValueError as exc:
            self.error_label.configure(text=str(exc))
        except Exception as exc:  # noqa: BLE001
            self.error_label.configure(text=f"เกิดข้อผิดพลาด: {exc!s}")
        finally:
            self.login_btn.configure(state="normal")

    def _open_forgot_password_dialog(self):
        """หน้าต่างตั้งรหัสผ่านใหม่ด้วยรหัส OTP ทางอีเมลสำหรับผู้ซื้อ (AUTH-5)"""
        dlg = ctk.CTkToplevel(self)
        dlg.title("ลืมรหัสผ่าน — รับรหัส OTP ทางอีเมล")
        dlg.geometry("460x440")
        dlg.resizable(False, False)
        dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
        dlg.transient(self.winfo_toplevel())

        hdr = ctk.CTkFrame(dlg, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="ตั้งรหัสผ่านใหม่ด้วย OTP",
            font=ThemeManager.get_font("h3"), text_color=ThemeManager.get_color_pair("primary"),
        ).pack(anchor="w", padx=20, pady=(14, 2))
        ctk.CTkLabel(
            hdr, text="สำหรับผู้ซื้อ — กรอกอีเมลที่สมัครไว้เพื่อรับรหัส OTP 6 หลัก",
            font=ThemeManager.get_font("small"), text_color="#FFFFFF",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        box = ctk.CTkFrame(dlg, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=22, pady=14)

        ctk.CTkLabel(box, text="อีเมลบัญชีของคุณ", font=ThemeManager.get_font("small_bold"),
                     text_color=ThemeManager.get_color_pair("text_main")).pack(anchor="w")
        email_row = ctk.CTkFrame(box, fg_color="transparent")
        email_row.pack(fill="x", pady=(2, 8))
        email_entry = ctk.CTkEntry(email_row, placeholder_text="name@example.com", **ThemeManager.entry_style(38))
        email_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkLabel(box, text="รหัส OTP 6 หลัก", font=ThemeManager.get_font("small_bold"),
                     text_color=ThemeManager.get_color_pair("text_main")).pack(anchor="w")
        otp_entry = ctk.CTkEntry(box, placeholder_text="กรอกรหัส OTP 6 หลัก", **ThemeManager.entry_style(38))
        otp_entry.pack(fill="x", pady=(2, 8))

        ctk.CTkLabel(box, text="รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร)", font=ThemeManager.get_font("small_bold"),
                     text_color=ThemeManager.get_color_pair("text_main")).pack(anchor="w")
        pw_entry = ctk.CTkEntry(box, placeholder_text="รหัสผ่านใหม่", show="•", **ThemeManager.entry_style(38))
        pw_entry.pack(fill="x", pady=(2, 8))

        msg_lbl = ctk.CTkLabel(box, text="", font=ThemeManager.get_font("small_bold"),
                               text_color=ThemeManager.get_color_pair("info"), wraplength=400, justify="left")
        msg_lbl.pack(fill="x", pady=4)

        def send_otp():
            em = email_entry.get().strip()
            try:
                res = auth_service.request_password_reset_otp(em)
                txt = res.get("message", "ส่งรหัส OTP แล้ว")
                if res.get("dev_otp"):
                    txt += f" (โหมดทดสอบออฟไลน์ รหัส OTP: {res['dev_otp']})"
                msg_lbl.configure(text=txt, text_color=ThemeManager.get_color_pair("success"))
            except Exception as exc:  # noqa: BLE001
                msg_lbl.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))

        ctk.CTkButton(email_row, text="ส่ง OTP", width=96, command=send_otp,
                      **ThemeManager.button_style("primary", "sm")).pack(side="right")

        def do_reset():
            try:
                res = auth_service.reset_password_with_otp(
                    email_entry.get().strip(), otp_entry.get().strip(), pw_entry.get()
                )
                dlg.destroy()
                self._show_banner(res.get("message", "ตั้งรหัสผ่านใหม่สำเร็จ กรุณาเข้าสู่ระบบ"), kind="success")
            except Exception as exc:  # noqa: BLE001
                msg_lbl.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))

        btn_bar = ctk.CTkFrame(box, fg_color="transparent")
        btn_bar.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(btn_bar, text="ยืนยันเปลี่ยนรหัสผ่าน", command=do_reset,
                      **ThemeManager.button_style("danger", "md")).pack(side="right")
        ctk.CTkButton(btn_bar, text="ยกเลิก", width=90, command=dlg.destroy,
                      **ThemeManager.button_style("outline", "md")).pack(side="right", padx=(0, 8))
        dlg.after(120, lambda: (dlg.lift(), email_entry.focus_set()))

    def _show_banner(self, text: str, kind: str = "success"):
        if not text:
            self.banner_frame.pack_forget()
            return
        bg = ThemeManager.get_color_pair("success" if kind == "success" else "primary")
        fg = "#FFFFFF" if kind == "success" else ON_PRIMARY
        self.banner_frame.configure(fg_color=bg)
        self.banner_label.configure(text=text, text_color=fg)
        self.banner_frame.pack(fill="x", pady=(0, 10), before=self.username_entry.master.winfo_children()[1])

    def on_show(self, registered_message: str = None, info_message: str = None, **kwargs):
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.error_label.configure(text="")
        self.layout.refresh_showcase()

        if registered_message:
            self.layout.set_titles(
                "สมัครสมาชิกสำเร็จ!",
                "บัญชีและอีเมลของคุณได้รับการยืนยันเรียบร้อยแล้ว กรุณาเข้าสู่ระบบด้านล่าง",
            )
            self.banner_frame.configure(fg_color=ThemeManager.get_color_pair("success"))
            self.banner_label.configure(text=registered_message, text_color="#FFFFFF")
            self.banner_frame.pack(fill="x", pady=(0, 10))
        elif info_message:
            self.layout.set_titles(
                "กรุณาเข้าสู่ระบบ",
                "ฟังก์ชันนี้สำหรับสมาชิก กรุณาเข้าสู่ระบบหรือสมัครสมาชิกก่อนทำรายการ",
            )
            self.banner_frame.configure(fg_color=ThemeManager.get_color_pair("primary"))
            self.banner_label.configure(text=info_message, text_color=ON_PRIMARY)
            self.banner_frame.pack(fill="x", pady=(0, 10))
        else:
            self.layout.set_titles(
                "เข้าสู่ระบบ",
                "เข้าสู่ระบบเพื่อสั่งซื้อสินค้า เก็บคูปองส่วนลด และติดตามสถานะพัสดุ",
            )
            self.banner_frame.pack_forget()

        self.username_entry.focus_set()