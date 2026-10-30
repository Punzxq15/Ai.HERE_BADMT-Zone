"""
ui/pages/buyer/profile.py
หน้าโปรไฟล์ของผู้ใช้งาน (ปรับปรุงตาม T11):
- ส่วนการ์ดสถิติ 3 ใบ มีสีสันชัดเจนเพื่อให้รู้ว่ากดได้:
  * คำสั่งซื้อ = สีเหลือง
  * ที่อยู่จัดส่ง = สีฟ้า
  * รายการโปรด = สีแดง/ชมพู
  พร้อม hover effect และกดไปยังหน้านั้นๆ ได้จริง
- มีปุ่ม "แก้ไขข้อมูลของฉัน" อยู่ในหน้าโปรไฟล์:
  * ชื่อผู้ใช้ (username) แก้ไขได้เลยและบันทึกได้เลย
  * ชื่อ-นามสกุล และเบอร์โทร แก้ไขได้เลยและบันทึกได้เลย
  * อีเมล ต้องแก้ไขอีกขั้นโดยการยืนยัน OTP ใหม่กับอีเมลใหม่อีกครั้ง จึงจะกดบันทึกและแก้ไขได้
  * รหัสผ่าน แก้ได้โดยการยืนยันรหัสผ่านเดิมตามเดิม
"""

import customtkinter as ctk

from core.constants import ROLE_BUYER
from services import account_service, auth_service
from ui.components.image_picker import ImagePicker
from ui.pages.buyer import common
from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.formatters import format_date_thai


class ProfilePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._profile = None
        self.entries = {}
        self._otp_verified_for_email = None

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)
        body.grid_columnconfigure(0, weight=1)

        hdr_row = ctk.CTkFrame(body, fg_color="transparent")
        hdr_row.grid(row=0, column=0, sticky="ew")
        common.page_title(hdr_row, "👤 โปรไฟล์ของฉัน", "จัดการข้อมูลบัญชี อีเมล และรหัสผ่านของคุณ").pack(side="left")

        self._edit_ic = icon_utils.get_icon("edit", 16, ON_PRIMARY, ON_PRIMARY)
        self.edit_my_info_btn = ctk.CTkButton(
            hdr_row,
            text=" แก้ไขข้อมูลของฉัน",
            image=self._edit_ic,
            compound="left",
            width=175,
            command=self._focus_edit_profile,
            **ThemeManager.button_style("primary", "md"),
        )
        self.edit_my_info_btn.pack(side="right", pady=4)

        # ---------------- ข้อมูลบัญชี
        self.info_card = ThemeManager.make_card(body)
        self.info_card.grid(row=1, column=0, sticky="ew", pady=(10, 6))
        self.info_card.grid_columnconfigure(1, minsize=120)
        self.info_card.grid_columnconfigure(2, weight=1)

        self.avatar = ImagePicker(self.info_card, size=(130, 130), allow_clear=False, button_text="เปลี่ยนรูป...")
        self.avatar.grid(row=0, column=0, rowspan=8, padx=20, pady=18, sticky="n")

        # T11: ชื่อผู้ใช้ แก้ไขได้เลยและบันทึกได้เลย
        self._entry_row(0, "username", "ชื่อผู้ใช้ (Username)")
        # T11: อีเมล ต้องยืนยัน OTP กับอีเมลใหม่ก่อนบันทึก
        self._build_email_row(1)
        self.role_label = self._static_row(3, "ประเภทบัญชี")
        self.since_label = self._static_row(4, "สมัครเมื่อ")
        self._entry_row(5, "full_name", "ชื่อ-นามสกุล")
        self._entry_row(6, "phone", "เบอร์โทรศัพท์")

        self.profile_msg = common.error_label(self.info_card, wraplength=600)
        self.profile_msg.grid(row=7, column=0, columnspan=3, sticky="w", padx=20, pady=(4, 0))

        btn_bar = ctk.CTkFrame(self.info_card, fg_color="transparent")
        btn_bar.grid(row=8, column=0, columnspan=3, sticky="w", padx=20, pady=(8, 18))
        self.save_btn = ctk.CTkButton(
            btn_bar, text="บันทึกโปรไฟล์", width=165, command=self._save_profile,
            **ThemeManager.button_style("primary", "md"),
        )
        self.save_btn.pack(side="left")

        # ---------------- T11: สถิติ/ทางลัด มีสีสันชัดเจน (คำสั่งซื้อ=เหลือง, ที่อยู่จัดส่ง=ฟ้า, รายการโปรด=แดง/ชมพู)
        self.stats_row = ctk.CTkFrame(body, fg_color="transparent")
        self.stats_row.grid(row=2, column=0, sticky="ew", pady=8)
        self.stats_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat")

        # ---------------- เปลี่ยนรหัสผ่าน (แบบเดิม ยืนยันรหัสผ่านเดิม)
        pw_card = ThemeManager.make_card(body)
        pw_card.grid(row=3, column=0, sticky="ew", pady=6)
        pw_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(pw_card, text="เปลี่ยนรหัสผ่าน (ยืนยันด้วยรหัสผ่านเดิม)", font=ThemeManager.get_font("h3"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_main")).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))
        self.pw_entries = {}
        for index, (key, label) in enumerate((("old", "รหัสผ่านเดิม"), ("new", "รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร)"),
                                              ("confirm", "ยืนยันรหัสผ่านใหม่"))):
            cell = ctk.CTkFrame(pw_card, fg_color="transparent")
            cell.grid(row=index + 1, column=0, sticky="ew", padx=20, pady=3)
            ctk.CTkLabel(cell, text=label, font=ThemeManager.get_font("small"), anchor="w",
                         text_color=ThemeManager.get_color_pair("text_muted")).pack(fill="x")
            entry = ctk.CTkEntry(cell, show="•", width=360, **ThemeManager.entry_style(38))
            entry.pack(anchor="w")
            entry.bind("<Return>", lambda _e: self._change_password())
            self.pw_entries[key] = entry
        self.pw_msg = common.error_label(pw_card, wraplength=520)
        self.pw_msg.grid(row=4, column=0, sticky="w", padx=20, pady=(4, 0))
        ctk.CTkButton(pw_card, text="เปลี่ยนรหัสผ่าน", width=160, command=self._change_password,
                      **ThemeManager.button_style("secondary")).grid(row=5, column=0, sticky="w", padx=20, pady=(6, 18))

        ctk.CTkButton(body, text="🚪 ออกจากระบบ", width=160, command=self.controller.logout,
                      **ThemeManager.button_style("outline")).grid(row=4, column=0, sticky="w", pady=(6, 0))

    def _static_row(self, row, label):
        ctk.CTkLabel(self.info_card, text=label, font=ThemeManager.get_font("small"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_muted")).grid(row=row, column=1, sticky="w", pady=(6, 0))
        value = ctk.CTkLabel(self.info_card, text="-", font=ThemeManager.get_font("body_bold"), anchor="w",
                             text_color=ThemeManager.get_color_pair("text_main"))
        value.grid(row=row, column=2, sticky="w", padx=(10, 20), pady=(6, 0))
        return value

    def _entry_row(self, row, key, label):
        ctk.CTkLabel(self.info_card, text=label, font=ThemeManager.get_font("small"), anchor="w",
                     text_color=ThemeManager.get_color_pair("text_muted")).grid(row=row, column=1, sticky="w", pady=(6, 0))
        entry = ctk.CTkEntry(self.info_card, width=320, **ThemeManager.entry_style(36))
        entry.grid(row=row, column=2, sticky="w", padx=(10, 20), pady=(6, 0))
        entry.bind("<Return>", lambda _e: self._save_profile())
        self.entries[key] = entry

    def _build_email_row(self, row: int):
        ctk.CTkLabel(
            self.info_card, text="อีเมล (ต้องยืนยัน OTP)", font=ThemeManager.get_font("small"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).grid(row=row, column=1, sticky="w", pady=(6, 0))

        email_wrap = ctk.CTkFrame(self.info_card, fg_color="transparent")
        email_wrap.grid(row=row, column=2, sticky="w", padx=(10, 20), pady=(6, 0))

        self.email_entry = ctk.CTkEntry(email_wrap, width=250, **ThemeManager.entry_style(36))
        self.email_entry.pack(side="left")
        self.entries["email"] = self.email_entry

        self.send_email_otp_btn = ctk.CTkButton(
            email_wrap,
            text="ส่ง OTP ยืนยันอีเมลใหม่",
            width=165,
            command=self._request_email_otp,
            **ThemeManager.button_style("info", "sm"),
        )
        self.send_email_otp_btn.pack(side="left", padx=(8, 0))

        # แถวกรอก OTP สำหรับอีเมลใหม่ (แสดงเมื่อกดส่ง OTP หรือเมื่อแก้ไขอีเมล)
        self.otp_row_frame = ctk.CTkFrame(
            self.info_card,
            fg_color=ThemeManager.get_color_pair("blue_soft"),
            corner_radius=8,
            border_width=1,
            border_color=ThemeManager.get_color_pair("info"),
        )
        self.otp_row_frame.grid(row=row + 1, column=1, columnspan=2, sticky="w", padx=(0, 20), pady=(4, 2))
        otp_inner = ctk.CTkFrame(self.otp_row_frame, fg_color="transparent")
        otp_inner.pack(padx=10, pady=6)

        ctk.CTkLabel(
            otp_inner, text="รหัส OTP 6 หลัก (จากอีเมลใหม่):",
            font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("info"),
        ).pack(side="left", padx=(0, 6))

        self.email_otp_entry = ctk.CTkEntry(
            otp_inner, width=130, placeholder_text="กรอก OTP 6 หลัก",
            **ThemeManager.entry_style(32),
        )
        self.email_otp_entry.pack(side="left", padx=(0, 6))

        self.verify_email_otp_btn = ctk.CTkButton(
            otp_inner,
            text="ยืนยัน OTP & เปลี่ยนอีเมล",
            width=165,
            command=self._confirm_email_otp,
            **ThemeManager.button_style("success", "sm"),
        )
        self.verify_email_otp_btn.pack(side="left")
        self.otp_row_frame.grid_remove()

    def _focus_edit_profile(self):
        try:
            self.entries["username"].focus_set()
            self.profile_msg.configure(
                text="สามารถแก้ไข ชื่อผู้ใช้ / ชื่อ-นามสกุล / เบอร์โทร แล้วกด 'บันทึกโปรไฟล์' ได้เลย (ส่วนอีเมลต้องกดส่งและยืนยัน OTP กับอีเมลใหม่ก่อน)",
                text_color=ThemeManager.get_color_pair("info"),
            )
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ โหลด/แสดง
    def on_show(self):
        self.profile_msg.configure(text="")
        self.pw_msg.configure(text="")
        self._otp_verified_for_email = None
        self.email_otp_entry.delete(0, "end")
        self.otp_row_frame.grid_remove()
        for entry in self.pw_entries.values():
            entry.delete(0, "end")
        self._load()

    def _load(self):
        try:
            profile = account_service.get_profile(common.user_id())
        except (ValueError, PermissionError) as exc:
            self.profile_msg.configure(text=f"⛔ {exc}", text_color=ThemeManager.get_color_pair("danger"))
            return
        self._profile = profile
        self.avatar.set_image(profile.get("avatar_path"))
        self.role_label.configure(text=profile["role_label"])
        self.since_label.configure(text=format_date_thai(profile["created_at"]))
        for key, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, profile.get(key) or "")
        self._render_stats(profile)

    def _render_stats(self, profile):
        for child in self.stats_row.winfo_children():
            child.destroy()
        if profile["role"] != ROLE_BUYER:
            self.stats_row.grid_remove()
            return
        self.stats_row.grid()

        # T11: คำสั่งซื้อ = สีเหลือง, ที่อยู่จัดส่ง = สีฟ้า, รายการโปรด = สีแดง/ชมพู
        stats = (
            (
                "📦 คำสั่งซื้อ",
                profile["order_count"],
                "orders",
                ("#FEF3C7", "#451A03"),
                ("#FDE68A", "#78350F"),
                ("#F59E0B", "#FBBF24"),
                ("#92400E", "#FEF3C7"),
            ),
            (
                "📍 ที่อยู่จัดส่ง",
                profile["address_count"],
                "addresses",
                ("#E0F2FE", "#0C4A6E"),
                ("#BAE6FD", "#075985"),
                ("#0284C7", "#38BDF8"),
                ("#075985", "#E0F2FE"),
            ),
            (
                "♥ รายการโปรด",
                profile["wishlist_count"],
                "wishlist",
                ("#FCE7F3", "#500724"),
                ("#FBCFE8", "#831843"),
                ("#E11D48", "#F472B6"),
                ("#9D174D", "#FCE7F3"),
            ),
        )
        for col, (label, count, route, bg_pair, hover_pair, border_pair, text_pair) in enumerate(stats):
            card = ctk.CTkFrame(
                self.stats_row,
                fg_color=bg_pair,
                corner_radius=14,
                border_width=2,
                border_color=border_pair,
            )
            card.grid(row=0, column=col, sticky="ew", padx=6, pady=2)
            number = ctk.CTkLabel(
                card, text=f"{count:,}", font=ThemeManager.get_font("price_big"),
                text_color=text_pair,
            )
            number.pack(pady=(12, 0))
            text = ctk.CTkLabel(
                card, text=label, font=ThemeManager.get_font("body_bold"),
                text_color=text_pair,
            )
            text.pack(pady=(2, 2))
            hint = ctk.CTkLabel(
                card, text="คลิกเพื่อเปิดดู ›", font=ThemeManager.get_font("tiny"),
                text_color=text_pair,
            )
            hint.pack(pady=(0, 10))

            def _bind_stat(c_widget, bg_p=bg_pair, hv_p=hover_pair, r_target=route, widgets=(card, number, text, hint)):
                def _on_enter(_e=None):
                    c_widget.configure(fg_color=hv_p)

                def _on_leave(_e=None):
                    c_widget.configure(fg_color=bg_p)

                def _on_click(_e=None):
                    self.controller.show(r_target)

                for w in widgets:
                    w.bind("<Button-1>", _on_click)
                    w.bind("<Enter>", _on_enter, add="+")
                    w.bind("<Leave>", _on_leave, add="+")
                    try:
                        w.configure(cursor="hand2")
                    except Exception:  # noqa: BLE001
                        pass

            _bind_stat(card)

    # ------------------------------------------------------------------ การเปลี่ยนอีเมลด้วย OTP (T11)
    def _request_email_otp(self):
        uid = common.user_id()
        new_email = self.email_entry.get().strip().lower()
        self.profile_msg.configure(text="")
        self.send_email_otp_btn.configure(state="disabled")
        try:
            res = auth_service.request_email_change_otp(uid, new_email)
            self.otp_row_frame.grid()
            self.email_otp_entry.focus_set()
            msg = f"ส่งรหัส OTP 6 หลักไปยังอีเมลใหม่ {res['email']} แล้ว กรุณากรอกรหัส OTP เพื่อยืนยัน"
            if res.get("dev_otp"):
                msg += f" (โหมดทดสอบออฟไลน์ รหัส OTP: {res['dev_otp']})"
            self.profile_msg.configure(text=msg, text_color=ThemeManager.get_color_pair("info"))
        except (ValueError, PermissionError) as exc:
            self.profile_msg.configure(text=f"⛔ {exc}", text_color=ThemeManager.get_color_pair("danger"))
        finally:
            self.send_email_otp_btn.configure(state="normal")

    def _confirm_email_otp(self):
        uid = common.user_id()
        new_email = self.email_entry.get().strip().lower()
        otp_code = self.email_otp_entry.get().strip()
        self.verify_email_otp_btn.configure(state="disabled")
        try:
            auth_service.confirm_email_change_with_otp(uid, new_email, otp_code)
            self._otp_verified_for_email = new_email
            self.otp_row_frame.grid_remove()
            self.email_otp_entry.delete(0, "end")
            self.controller.refresh_shell()
            self._load()
            self.profile_msg.configure(
                text=f"✓ ยืนยัน OTP และเปลี่ยนอีเมลเป็น {new_email} เรียบร้อยแล้ว",
                text_color=ThemeManager.get_color_pair("success"),
            )
        except (ValueError, PermissionError) as exc:
            self.profile_msg.configure(text=f"⛔ {exc}", text_color=ThemeManager.get_color_pair("danger"))
        finally:
            self.verify_email_otp_btn.configure(state="normal")

    # ------------------------------------------------------------------ บันทึกข้อมูลโปรไฟล์ (username, ชื่อ-นามสกุล, เบอร์โทร)
    def _save_profile(self):
        uid = common.user_id()
        self.profile_msg.configure(text="")
        username = self.entries["username"].get().strip()
        full_name = self.entries["full_name"].get().strip()
        phone = self.entries["phone"].get().strip()
        entered_email = self.entries["email"].get().strip().lower()
        current_email = (self._profile.get("email") or "").strip().lower() if self._profile else ""
        new_avatar = self.avatar.get_selected_file()

        # T11: ถ้าแก้ช่องอีเมลแต่ยังไม่ได้ยืนยัน OTP กับอีเมลใหม่ ให้แจ้งเตือนและเปิดแถว OTP
        if entered_email and entered_email != current_email and entered_email != self._otp_verified_for_email:
            self.otp_row_frame.grid()
            self.profile_msg.configure(
                text="⛔ การเปลี่ยนอีเมลต้องกด 'ส่ง OTP ยืนยันอีเมลใหม่' และกรอกรหัส OTP ให้ผ่านก่อนบันทึก",
                text_color=ThemeManager.get_color_pair("danger"),
            )
            return

        self.save_btn.configure(state="disabled")
        try:
            auth_service.update_profile(uid, full_name, phone, username=username)
            if new_avatar:
                account_service.set_avatar(uid, new_avatar)
        except (ValueError, PermissionError) as exc:
            self.profile_msg.configure(text=f"⛔ {exc}", text_color=ThemeManager.get_color_pair("danger"))
            return
        finally:
            self.save_btn.configure(state="normal")

        self.controller.refresh_shell()
        self._load()
        self.profile_msg.configure(
            text="✓ บันทึกข้อมูลโปรไฟล์ (ชื่อผู้ใช้ ชื่อ-นามสกุล และเบอร์โทรศัพท์) เรียบร้อยแล้ว",
            text_color=ThemeManager.get_color_pair("success"),
        )

    def _change_password(self):
        old, new, confirm = (self.pw_entries[k].get() for k in ("old", "new", "confirm"))
        danger = ThemeManager.get_color_pair("danger")
        if not old or not new:
            self.pw_msg.configure(text="⛔ กรุณากรอกรหัสผ่านเดิมและรหัสผ่านใหม่", text_color=danger)
            return
        if new != confirm:
            self.pw_msg.configure(text="⛔ รหัสผ่านใหม่และการยืนยันไม่ตรงกัน", text_color=danger)
            return
        try:
            auth_service.change_password(common.user_id(), old, new)
        except (ValueError, PermissionError) as exc:
            self.pw_msg.configure(text=f"⛔ {exc}", text_color=danger)
            return
        for entry in self.pw_entries.values():
            entry.delete(0, "end")
        self.pw_msg.configure(text="✓ เปลี่ยนรหัสผ่านเรียบร้อยแล้ว", text_color=ThemeManager.get_color_pair("success"))
