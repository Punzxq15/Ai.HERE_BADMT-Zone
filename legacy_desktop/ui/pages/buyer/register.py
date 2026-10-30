"""
ui/pages/buyer/register.py
หน้าสมัครสมาชิก (ผู้ซื้อ) แบบ 2 คอลัมน์ (AuthSplitLayout):
- รองรับการกรอกข้อมูลบัญชี + เบอร์โทร + ที่อยู่จัดส่งเริ่มต้น (BUY-1)
- รองรับการส่งรหัส OTP ไปยังอีเมลและยืนยัน OTP 6 หลักก่อนเปิดใช้งานบัญชี (AUTH-1)
- หลังสมัครและยืนยันสำเร็จ พากลับไปหน้า Login พร้อมแถบข้อความยืนยัน (AUTH-3)
"""

import customtkinter as ctk

from services import auth_service
from ui.components.auth_layout import AuthSplitLayout
from ui.theme import ThemeManager
from utils import icon_utils

_ACCOUNT_FIELDS = (
    ("username", "ชื่อผู้ใช้ (Username) *", "ภาษาอังกฤษ ตัวเลข และ _ เท่านั้น", False),
    ("email", "อีเมล (สำหรับรับรหัส OTP และใบเสร็จ) *", "name@example.com", False),
    ("full_name", "ชื่อ-นามสกุลผู้รับสินค้า *", "ชื่อจริง นามสกุล", False),
    ("phone", "เบอร์โทรศัพท์มือถือ (10 หลัก) *", "0812345678", False),
    ("password", "รหัสผ่าน (อย่างน้อย 8 ตัวอักษร) *", "อย่างน้อย 8 ตัวอักษร", True),
    ("confirm", "ยืนยันรหัสผ่านอีกครั้ง *", "กรอกรหัสผ่านอีกครั้ง", True),
)

_ADDRESS_FIELDS = (
    ("address_line", "บ้านเลขที่ / ซอย / ถนน (ที่อยู่เริ่มต้น)", "เช่น 99/9 ถ.สุขุมวิท แขวงคลองเตย"),
    ("district", "เขต / อำเภอ", "เช่น คลองเตย"),
    ("province", "จังหวัด", "เช่น กรุงเทพมหานคร"),
    ("postcode", "รหัสไปรษณีย์ (5 หลัก)", "10110"),
)


class RegisterPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self.entries = {}
        self._otp_pending_email = None

        self.layout = AuthSplitLayout(
            self, controller,
            form_title="สมัครสมาชิกใหม่",
            form_subtitle="กรอกข้อมูลบัญชี ที่อยู่เริ่มต้น และยืนยันรหัส OTP ทางอีเมลเพื่อเริ่มช้อปปิ้ง",
            center_vertically=False,
        )
        self.layout.pack(fill="both", expand=True)
        body = self.layout.form_body

        # ส่วนที่ 1: ข้อมูลบัญชี
        ctk.CTkLabel(
            body, text="1. ข้อมูลบัญชีผู้ใช้", font=ThemeManager.get_font("h3"),
            text_color=ThemeManager.get_color_pair("danger"), anchor="w",
        ).pack(fill="x", pady=(2, 4))

        for key, label, placeholder, secret in _ACCOUNT_FIELDS:
            ctk.CTkLabel(
                body, text=label, font=ThemeManager.get_font("small_bold"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x", pady=(4, 1))
            entry = ctk.CTkEntry(
                body, placeholder_text=placeholder, show="•" if secret else "",
                **ThemeManager.entry_style(38),
            )
            entry.pack(fill="x", pady=(0, 2))
            self.entries[key] = entry

        # ส่วนที่ 2: ที่อยู่จัดส่งเริ่มต้น (BUY-1)
        ctk.CTkLabel(
            body, text="2. ที่อยู่จัดส่งเริ่มต้น (แก้ไขหรือเพิ่มภายหลังได้)",
            font=ThemeManager.get_font("h3"),
            text_color=ThemeManager.get_color_pair("danger"), anchor="w",
        ).pack(fill="x", pady=(12, 4))

        for key, label, placeholder in _ADDRESS_FIELDS:
            ctk.CTkLabel(
                body, text=label, font=ThemeManager.get_font("small_bold"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x", pady=(4, 1))
            entry = ctk.CTkEntry(
                body, placeholder_text=placeholder,
                **ThemeManager.entry_style(36),
            )
            entry.pack(fill="x", pady=(0, 2))
            self.entries[key] = entry

        # ส่วนที่ 3: ส่งและยืนยันรหัส OTP (AUTH-1)
        otp_card = ctk.CTkFrame(
            body, fg_color=ThemeManager.get_color_pair("surface_alt"),
            corner_radius=10, border_width=1, border_color=ThemeManager.get_color_pair("primary"),
        )
        otp_card.pack(fill="x", pady=(12, 6))
        ctk.CTkLabel(
            otp_card, text="3. ยืนยันอีเมลด้วยรหัส OTP (6 หลัก)",
            font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_main"), anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        otp_row = ctk.CTkFrame(otp_card, fg_color="transparent")
        otp_row.pack(fill="x", padx=14, pady=(0, 8))
        self._mail_ic = icon_utils.get_icon("mail", 16, "#141619", "#141619")
        self.send_otp_btn = ctk.CTkButton(
            otp_row, text=" ส่งรหัส OTP ไปที่อีเมล", image=self._mail_ic, compound="left", width=185,
            command=self.handle_send_otp,
            **ThemeManager.button_style("primary", "md"),
        )
        self.send_otp_btn.pack(side="left", padx=(0, 8))

        self.otp_entry = ctk.CTkEntry(
            otp_row, placeholder_text="รหัส OTP 6 หลัก",
            **ThemeManager.entry_style(38),
        )
        self.otp_entry.pack(side="left", fill="x", expand=True)
        self.otp_entry.bind("<Return>", lambda _e: self.handle_verify_otp())

        self.otp_hint_label = ctk.CTkLabel(
            otp_card, text="กด 'ส่งรหัส OTP ไปที่อีเมล' จากนั้นนำรหัส 6 หลักมากรอกเพื่อยืนยันการสมัคร",
            font=ThemeManager.get_font("small"), text_color=ThemeManager.get_color_pair("text_muted"),
            anchor="w", justify="left", wraplength=370,
        )
        self.otp_hint_label.pack(fill="x", padx=14, pady=(0, 10))

        self.error_label = ctk.CTkLabel(
            body, text="", font=ThemeManager.get_font("small_bold"),
            wraplength=390, justify="left",
            text_color=ThemeManager.get_color_pair("danger"),
        )
        self.error_label.pack(fill="x", pady=(4, 6))

        self._chk_ic = icon_utils.get_icon("check", 16, "#FFFFFF", "#FFFFFF")
        self.register_btn = ctk.CTkButton(
            body, text=" ยืนยันรหัส OTP และสร้างบัญชีสมาชิก", image=self._chk_ic, compound="left",
            command=self.handle_verify_otp,
            **ThemeManager.button_style("danger", "lg"),
        )
        self.register_btn.pack(fill="x", pady=(4, 8))

        ctk.CTkButton(
            body, text="มีบัญชีอยู่แล้ว? กลับไปหน้าเข้าสู่ระบบ",
            command=lambda: self.controller.show("login"),
            **ThemeManager.button_style("outline", "md"),
        ).pack(fill="x")

    def _collect_values(self) -> dict[str, str]:
        return {key: entry.get() for key, entry in self.entries.items()}

    def handle_send_otp(self):
        """ตรวจสอบข้อมูลเบื้องต้นและส่งรหัส OTP ไปยังอีเมลของผู้สมัคร (AUTH-1)"""
        v = self._collect_values()
        self.error_label.configure(text="")
        if v["password"] != v["confirm"]:
            self.error_label.configure(text="รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน")
            return

        self.send_otp_btn.configure(state="disabled")
        try:
            res = auth_service.start_registration_with_otp(
                username=v["username"].strip(),
                email=v["email"].strip(),
                password=v["password"],
                full_name=v["full_name"].strip(),
                phone=v["phone"].strip(),
                address_line=v["address_line"].strip(),
                district=v["district"].strip(),
                province=v["province"].strip(),
                postcode=v["postcode"].strip(),
            )
            self._otp_pending_email = v["email"].strip().lower()
            hint = res.get("message", "ส่งรหัส OTP ไปยังอีเมลแล้ว")
            if res.get("dev_otp"):
                hint += f"\n(โหมดออฟไลน์/ทดสอบ รหัส OTP ของคุณคือ: {res['dev_otp']})"
                self.otp_entry.delete(0, "end")
                self.otp_entry.insert(0, str(res["dev_otp"]))
            self.otp_hint_label.configure(text=hint, text_color=ThemeManager.get_color_pair("success"))
            self.otp_entry.focus_set()
        except ValueError as exc:
            self.error_label.configure(text=str(exc))
        except Exception as exc:  # noqa: BLE001
            self.error_label.configure(text=f"เกิดข้อผิดพลาด: {exc!s}")
        finally:
            self.send_otp_btn.configure(state="normal")

    def handle_verify_otp(self):
        """ยืนยันรหัส OTP 6 หลักและสร้างบัญชีจริง จากนั้นพากลับหน้า Login (AUTH-1, AUTH-3)"""
        v = self._collect_values()
        self.error_label.configure(text="")
        if v["password"] != v["confirm"]:
            self.error_label.configure(text="รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน")
            return

        otp_code = self.otp_entry.get().strip()
        email = (self._otp_pending_email or v["email"]).strip()
        if not otp_code:
            self.error_label.configure(text="กรุณากด 'ส่งรหัส OTP ไปที่อีเมล' และกรอกรหัส OTP 6 หลักก่อนยืนยัน")
            return

        self.register_btn.configure(state="disabled")
        try:
            auth_service.complete_registration_with_otp(email, otp_code)
        except ValueError as exc:
            self.error_label.configure(text=str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            self.error_label.configure(text=f"เกิดข้อผิดพลาด: {exc!s}")
            return
        finally:
            self.register_btn.configure(state="normal")

        self.controller.show(
            "login",
            registered_message=f"สมัครสมาชิกและยืนยันอีเมล ({email}) สำเร็จแล้ว! กรุณาเข้าสู่ระบบ",
        )

    def handle_register(self):
        """เมธอดสำรองเพื่อความเข้ากันได้: ถ้ามี OTP แล้วให้ยืนยัน ถ้ายังไม่มีให้ส่ง OTP ก่อน"""
        if self.otp_entry.get().strip():
            self.handle_verify_otp()
        else:
            self.handle_send_otp()

    def on_show(self, **kwargs):
        self._otp_pending_email = None
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.otp_entry.delete(0, "end")
        self.error_label.configure(text="")
        self.otp_hint_label.configure(
            text="กด 'ส่งรหัส OTP ไปที่อีเมล' จากนั้นนำรหัส 6 หลักมากรอกเพื่อยืนยันการสมัคร",
            text_color=ThemeManager.get_color_pair("text_muted"),
        )
        self.layout.refresh_showcase()
        self.entries["username"].focus_set()
