"""
ui/pages/buyer/addresses.py
หน้าที่อยู่จัดส่ง: รายการ + เพิ่ม/แก้ไข (ฟอร์มในหน้า) + ลบ + ตั้งเป็นค่าเริ่มต้น
"""

import customtkinter as ctk

from services import account_service
from ui.components import dialogs
from ui.pages.buyer import common
from ui.theme import ThemeManager
from utils.formatters import format_phone

# (key, ป้ายกำกับ, ตำแหน่ง row, column, columnspan)
_FIELDS = (
    ("recipient", "ชื่อผู้รับ", 0, 0, 1),
    ("phone", "เบอร์โทรศัพท์", 0, 1, 1),
    ("address_line", "ที่อยู่ (บ้านเลขที่ ถนน ซอย)", 1, 0, 2),
    ("district", "แขวง/เขต หรือ ตำบล/อำเภอ", 2, 0, 1),
    ("province", "จังหวัด", 2, 1, 1),
    ("postcode", "รหัสไปรษณีย์", 3, 0, 1),
)


class AddressesPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._editing_id = None
        self.entries = {}

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        head = ctk.CTkFrame(body, fg_color="transparent")
        head.pack(fill="x")
        common.page_title(head, "📍 ที่อยู่จัดส่ง", "จัดการที่อยู่สำหรับรับสินค้า (เพิ่มได้หลายที่)").pack(side="left")
        self.add_btn = ctk.CTkButton(head, text="+ เพิ่มที่อยู่ใหม่", width=150, command=lambda: self._show_form(None),
                                     **ThemeManager.button_style("primary"))
        self.add_btn.pack(side="right")

        self.msg_label = common.error_label(body)
        self.msg_label.pack(fill="x", pady=(6, 0))

        self.form_card = ThemeManager.make_card(body)
        self._build_form()

        self.list_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.list_frame.pack(fill="x", pady=(8, 0))

    # ------------------------------------------------------------------ ฟอร์ม
    def _build_form(self):
        card = self.form_card
        card.grid_columnconfigure((0, 1), weight=1, uniform="f")
        self.form_title = ctk.CTkLabel(card, text="เพิ่มที่อยู่ใหม่", font=ThemeManager.get_font("h3"), anchor="w",
                                       text_color=ThemeManager.get_color_pair("text_main"))
        self.form_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(14, 4))

        for key, label, row, col, span in _FIELDS:
            cell = ctk.CTkFrame(card, fg_color="transparent")
            cell.grid(row=row + 1, column=col, columnspan=span, sticky="ew", padx=14, pady=4)
            ctk.CTkLabel(cell, text=label, font=ThemeManager.get_font("small"), anchor="w",
                         text_color=ThemeManager.get_color_pair("text_muted")).pack(fill="x")
            entry = ctk.CTkEntry(cell, **ThemeManager.entry_style(38))
            entry.pack(fill="x")
            entry.bind("<Return>", lambda _e: self._save())
            self.entries[key] = entry

        self.default_var = ctk.BooleanVar(value=False)
        self.default_check = ctk.CTkCheckBox(
            card, text="ตั้งเป็นที่อยู่เริ่มต้น", variable=self.default_var, font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_main"),
            fg_color=ThemeManager.get_color_pair("primary"),
            hover_color=ThemeManager.get_color_pair("primary_hover"), checkmark_color="#1A1A1A")
        self.default_check.grid(row=5, column=1, sticky="w", padx=14, pady=(18, 4))

        self.form_error = common.error_label(card, wraplength=640)
        self.form_error.grid(row=6, column=0, columnspan=2, sticky="w", padx=18)

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=7, column=0, columnspan=2, sticky="w", padx=14, pady=(6, 16))
        ctk.CTkButton(buttons, text="บันทึกที่อยู่", width=140, command=self._save,
                      **ThemeManager.button_style("primary")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="ยกเลิก", width=100, command=self._hide_form,
                      **ThemeManager.button_style("outline")).pack(side="left")

    def _show_form(self, address):
        """เปิดฟอร์ม — address=None คือเพิ่มใหม่, ส่ง dict ที่อยู่มาคือแก้ไข"""
        self.msg_label.configure(text="")
        self.form_error.configure(text="")
        self._editing_id = address["id"] if address else None
        self.form_title.configure(text="แก้ไขที่อยู่" if address else "เพิ่มที่อยู่ใหม่")
        for key, entry in self.entries.items():
            entry.delete(0, "end")
            if address and address.get(key) is not None:
                entry.insert(0, str(address[key]))
        self.default_var.set(bool(address and address.get("is_default")))
        self.form_card.pack(fill="x", pady=(8, 0), before=self.list_frame)
        self.entries["recipient"].focus_set()

    def _hide_form(self):
        self.form_card.pack_forget()
        self._editing_id = None

    def _save(self):
        values = {key: entry.get().strip() for key, entry in self.entries.items()}
        want_default = bool(self.default_var.get())
        uid = common.user_id()
        self.form_error.configure(text="")
        try:
            if self._editing_id is None:
                account_service.add_address(
                    uid, values["recipient"], values["phone"], values["address_line"], values["district"],
                    values["province"], values["postcode"], is_default=want_default)
                done = "เพิ่มที่อยู่เรียบร้อยแล้ว"
            else:
                account_service.update_address(
                    uid, self._editing_id, values["recipient"], values["phone"], values["address_line"],
                    values["district"], values["province"], values["postcode"])
                if want_default:
                    account_service.set_default_address(uid, self._editing_id)
                done = "บันทึกการแก้ไขเรียบร้อยแล้ว"
        except (ValueError, PermissionError) as exc:
            self.form_error.configure(text=str(exc))
            return
        self._hide_form()
        self._load()
        self.msg_label.configure(text=f"✓ {done}", text_color=ThemeManager.get_color_pair("success"))

    # ------------------------------------------------------------------ รายการ
    def on_show(self):
        self._hide_form()
        self.msg_label.configure(text="")
        self._load()

    def _load(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        try:
            addresses = account_service.list_addresses(common.user_id())
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))
            return
        if not addresses:
            ctk.CTkLabel(self.list_frame, text="📍\nยังไม่มีที่อยู่จัดส่ง กดปุ่ม \"เพิ่มที่อยู่ใหม่\" เพื่อเริ่มต้น",
                         font=ThemeManager.get_font("body"), text_color=ThemeManager.get_color_pair("text_muted"),
                         justify="center").pack(pady=50)
            return
        for address in addresses:
            self._address_card(address)

    def _address_card(self, address):
        card = ThemeManager.make_card(self.list_frame)
        card.pack(fill="x", pady=5)
        card.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=0, sticky="w", padx=16, pady=12)
        top = ctk.CTkFrame(info, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=address["recipient"], font=ThemeManager.get_font("body_bold"),
                     text_color=ThemeManager.get_color_pair("text_main")).pack(side="left")
        ctk.CTkLabel(top, text=format_phone(address["phone"]), font=ThemeManager.get_font("small"),
                     text_color=ThemeManager.get_color_pair("text_muted")).pack(side="left", padx=10)
        if address["is_default"]:
            ThemeManager.make_badge(top, "ค่าเริ่มต้น", "success").pack(side="left")
        ctk.CTkLabel(info, text=address["full_address"], font=ThemeManager.get_font("body"), anchor="w",
                     justify="left", wraplength=620, text_color=ThemeManager.get_color_pair("text_main")
                     ).pack(fill="x", pady=(4, 0))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e", padx=14, pady=12)
        ctk.CTkButton(actions, text="แก้ไข", width=70, command=lambda: self._show_form(address),
                      **ThemeManager.button_style("outline", "sm")).pack(side="left", padx=2)
        if not address["is_default"]:
            ctk.CTkButton(actions, text="ตั้งเป็นค่าเริ่มต้น", width=120,
                          command=lambda: self._set_default(address),
                          **ThemeManager.button_style("outline", "sm")).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="ลบ", width=60, command=lambda: self._delete(address),
                      **ThemeManager.button_style("danger", "sm")).pack(side="left", padx=2)

    def _set_default(self, address):
        try:
            account_service.set_default_address(common.user_id(), address["id"])
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))
            return
        self.msg_label.configure(text="✓ ตั้งเป็นที่อยู่เริ่มต้นแล้ว", text_color=ThemeManager.get_color_pair("success"))
        self._load()

    def _delete(self, address):
        if not dialogs.confirm(self, "ลบที่อยู่", f"ต้องการลบที่อยู่ของ \"{address['recipient']}\" ใช่ไหม?",
                               confirm_text="ลบ", danger=True):
            return
        try:
            account_service.delete_address(common.user_id(), address["id"])
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=str(exc), text_color=ThemeManager.get_color_pair("danger"))
            return
        if self._editing_id == address["id"]:
            self._hide_form()
        self.msg_label.configure(text="✓ ลบที่อยู่แล้ว", text_color=ThemeManager.get_color_pair("success"))
        self._load()
