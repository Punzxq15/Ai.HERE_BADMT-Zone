"""
ui/components/dialogs.py
กล่องโต้ตอบมาตรฐาน (modal) ใช้แทน messagebox ของ tkinter เพื่อให้เข้ากับธีม

ใช้งาน (ทุกฟังก์ชันรอจนผู้ใช้ตอบ แล้วคืนค่า):
    if dialogs.confirm(self, "ยกเลิกออเดอร์", "ต้องการยกเลิกใช่ไหม?", danger=True): ...
    dialogs.show_message(self, "บันทึกแล้ว", "บันทึกข้อมูลเรียบร้อย", kind="success")   # info|success|error|warning
    reason = dialogs.ask_reason(self, "ปฏิเสธสลิป", "ระบุเหตุผล")     # str หรือ None ถ้ากดยกเลิก

ทดสอบเดี่ยว:  python -m ui.components.dialogs   (รันจาก root โปรเจกต์)
"""

import customtkinter as ctk

from ui.theme import ThemeManager

_ICONS = {"info": "ℹ️", "success": "✅", "error": "⛔", "warning": "⚠️", "question": "❓"}
_ICON_COLORS = {"info": "text_main", "success": "success", "error": "danger", "warning": "warning", "question": "text_main"}


class _BaseDialog(ctk.CTkToplevel):
    """หน้าต่างโมดัล: กึ่งกลางหน้าต่างแม่ บล็อกการกดหน้าต่างอื่นจนกว่าจะปิด"""

    def __init__(self, parent, title, width=420, height=200):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=ThemeManager.get_color_pair("surface"))

        top = parent.winfo_toplevel() if parent is not None else None
        if top is not None:
            self.transient(top)
        self._center(top, width, height)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda _e: self._cancel())
        # grab_set ต้องรอให้หน้าต่างแสดงก่อน ไม่งั้น Windows/Linux จะ error "window not viewable"
        self.after(120, self._activate)

    def _center(self, top, width, height):
        self.update_idletasks()
        if top is not None and top.winfo_exists():
            x = top.winfo_rootx() + (top.winfo_width() - width) // 2
            y = top.winfo_rooty() + (top.winfo_height() - height) // 2
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def _activate(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:  # noqa: BLE001 - หน้าต่างถูกปิดไปก่อน
            pass

    def _cancel(self):
        self.result = self._cancel_value()
        self._close()

    def _cancel_value(self):
        return None

    def _close(self):
        try:
            self.grab_release()
        except Exception:  # noqa: BLE001
            pass
        self.destroy()

    def run(self):
        """แสดงและรอจนปิด แล้วคืน self.result"""
        self.wait_window(self)
        return self.result


class _MessageDialog(_BaseDialog):
    def __init__(self, parent, title, message, kind="info", confirm_text="ตกลง",
                 cancel_text=None, danger=False):
        lines = max(1, len(message) // 38 + message.count("\n") + 1)
        super().__init__(parent, title, width=420, height=min(120 + lines * 22 + 56, 520))
        self._has_cancel = cancel_text is not None

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(22, 6))
        ctk.CTkLabel(
            body, text=_ICONS.get(kind, "ℹ️"), font=("Arimo", 30),
            text_color=ThemeManager.get_color_pair(_ICON_COLORS.get(kind, "text_main")),
        ).pack(side="left", anchor="n", padx=(0, 14))
        text_box = ctk.CTkFrame(body, fg_color="transparent")
        text_box.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            text_box, text=title, font=ThemeManager.get_font("h3"), anchor="w", justify="left",
            text_color=ThemeManager.get_color_pair("text_main"), wraplength=290,
        ).pack(fill="x")
        ctk.CTkLabel(
            text_box, text=message, font=ThemeManager.get_font("body"), anchor="w", justify="left",
            text_color=ThemeManager.get_color_pair("text_muted"), wraplength=290,
        ).pack(fill="x", pady=(6, 0))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(8, 20))
        ok_kind = "danger" if danger else "primary"
        ok_btn = ctk.CTkButton(buttons, text=confirm_text, width=110, command=self._ok,
                               **ThemeManager.button_style(ok_kind))
        ok_btn.pack(side="right")
        if self._has_cancel:
            ctk.CTkButton(buttons, text=cancel_text, width=110, command=self._cancel,
                          **ThemeManager.button_style("outline")).pack(side="right", padx=(0, 10))
        self.bind("<Return>", lambda _e: self._ok())

    def _cancel_value(self):
        return False

    def _ok(self):
        self.result = True
        self._close()


class _ReasonDialog(_BaseDialog):
    def __init__(self, parent, title, message, required, confirm_text, placeholder, danger):
        super().__init__(parent, title, width=460, height=330)
        self._required = required

        ctk.CTkLabel(
            self, text=title, font=ThemeManager.get_font("h3"), anchor="w",
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(fill="x", padx=24, pady=(22, 0))
        if message:
            ctk.CTkLabel(
                self, text=message, font=ThemeManager.get_font("body"), anchor="w", justify="left",
                text_color=ThemeManager.get_color_pair("text_muted"), wraplength=410,
            ).pack(fill="x", padx=24, pady=(4, 0))

        self.textbox = ctk.CTkTextbox(
            self, height=100, wrap="word",
            **{k: v for k, v in ThemeManager.entry_style().items() if k != "height"},
        )
        self.textbox.pack(fill="x", padx=24, pady=(12, 0))
        self._placeholder = placeholder
        self.textbox.focus_set()

        self.error_label = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("danger"), anchor="w",
        )
        self.error_label.pack(fill="x", padx=24, pady=(4, 0))
        if placeholder:
            ctk.CTkLabel(
                self, text=placeholder, font=ThemeManager.get_font("small"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_muted"),
            ).pack(fill="x", padx=24)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=24, pady=(10, 20), side="bottom")
        ctk.CTkButton(buttons, text=confirm_text, width=110, command=self._ok,
                      **ThemeManager.button_style("danger" if danger else "primary")).pack(side="right")
        ctk.CTkButton(buttons, text="ยกเลิก", width=110, command=self._cancel,
                      **ThemeManager.button_style("outline")).pack(side="right", padx=(0, 10))

    def _ok(self):
        text = self.textbox.get("1.0", "end").strip()
        if self._required and not text:
            self.error_label.configure(text="กรุณาระบุเหตุผล")
            return
        self.result = text
        self._close()


# ---------------------------------------------------------------------------
# ฟังก์ชันสำหรับเรียกใช้
# ---------------------------------------------------------------------------
def confirm(parent, title, message, confirm_text="ยืนยัน", cancel_text="ยกเลิก", danger=False) -> bool:
    """กล่องยืนยัน — คืน True ถ้ากดยืนยัน, False ถ้ายกเลิก/ปิด"""
    return bool(_MessageDialog(parent, title, message, kind="question", confirm_text=confirm_text,
                               cancel_text=cancel_text, danger=danger).run())


def show_message(parent, title, message, kind="info", button_text="ตกลง") -> None:
    """กล่องข้อความ kind: info|success|error|warning"""
    _MessageDialog(parent, title, message, kind=kind, confirm_text=button_text).run()


def ask_reason(parent, title, message="", required=True, confirm_text="ยืนยัน",
               placeholder="", danger=False):
    """กล่องใส่เหตุผล — คืนข้อความ (strip แล้ว) หรือ None ถ้ากดยกเลิก/ปิด
    required=True (ค่าเริ่มต้น) จะไม่ยอมให้ส่งช่องว่าง"""
    return _ReasonDialog(parent, title, message, required, confirm_text, placeholder, danger).run()


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("420x300")
    out = ctk.CTkLabel(root, text="")
    out.pack(pady=10)

    def t_confirm():
        out.configure(text=f"confirm -> {confirm(root, 'ยกเลิกออเดอร์', 'ต้องการยกเลิกออเดอร์นี้ใช่ไหม?', danger=True)}")

    def t_msg():
        show_message(root, "บันทึกแล้ว", "บันทึกข้อมูลเรียบร้อย", kind="success")
        out.configure(text="show_message ปิดแล้ว")

    def t_reason():
        out.configure(text=f"ask_reason -> {ask_reason(root, 'ปฏิเสธสลิป', 'ระบุเหตุผลที่ปฏิเสธ', danger=True)!r}")

    for text, fn in (("confirm", t_confirm), ("message", t_msg), ("reason", t_reason)):
        ctk.CTkButton(root, text=text, command=fn).pack(pady=6)
    root.mainloop()
