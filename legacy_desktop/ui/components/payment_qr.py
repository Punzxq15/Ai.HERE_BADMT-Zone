"""
ui/components/payment_qr.py
การ์ดแสดง PromptPay QR พร้อมยอดเงิน/ชื่อบัญชี/เลขพร้อมเพย์ + ปุ่มบันทึก QR เป็นรูป

ข้อมูลเข้า: dict จาก payment_service.get_payment_info(order_id)
    amount, promptpay_no, promptpay_name, shop_name, payload

ใช้งาน:
    qr = PaymentQR(parent, size=240)
    qr.set_info(payment_service.get_payment_info(order_id))
    qr.clear()

ถ้ายังไม่ได้ตั้งเลขพร้อมเพย์ (payload ว่าง) หรือสร้าง QR ไม่ได้ จะแสดงข้อความแทนรูป ไม่ทำให้หน้าพัง

ทดสอบเดี่ยว:  python -m ui.components.payment_qr   (รันจาก root โปรเจกต์ — ต้องติดตั้ง qrcode)
"""

from tkinter import filedialog

import customtkinter as ctk

from ui.theme import ThemeManager
from utils.formatters import format_price


class PaymentQR(ctk.CTkFrame):
    def __init__(self, parent, size=240):
        super().__init__(
            parent, corner_radius=14, border_width=1,
            fg_color=ThemeManager.get_color_pair("surface"),
            border_color=ThemeManager.get_color_pair("border"),
        )
        self._size = size
        self._pil_image = None
        self._ctk_image = None

        ctk.CTkLabel(
            self, text="สแกนเพื่อชำระเงิน (PromptPay)", font=ThemeManager.get_font("h3"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(padx=20, pady=(16, 8))

        # กรอบขาวรอบ QR (แอปธนาคารสแกนง่ายขึ้นในโหมดมืด)
        self._frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=10, width=size + 20, height=size + 20)
        self._frame.pack(padx=20)
        self._frame.pack_propagate(False)
        self.qr_label = ctk.CTkLabel(self._frame, text="", text_color="#555555", wraplength=size - 20)
        self.qr_label.pack(expand=True)

        self.amount_label = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("price_big"),
            text_color=ThemeManager.get_color_pair("text_main"),
        )
        self.amount_label.pack(pady=(12, 0))
        self.name_label = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        )
        self.name_label.pack()
        self.number_label = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        )
        self.number_label.pack()

        self.save_btn = ctk.CTkButton(
            self, text="บันทึกรูป QR", width=140, command=self.save_image,
            **ThemeManager.button_style("outline", "sm"),
        )
        self.save_btn.pack(pady=(10, 16))
        self.clear()

    # ------------------------------------------------------------------ API
    def set_info(self, info: dict):
        """แสดง QR จากข้อมูลชำระเงิน"""
        if not info:
            return self.clear("ไม่พบข้อมูลการชำระเงิน")
        self.amount_label.configure(text=format_price(info.get("amount")))
        self.name_label.configure(text=info.get("promptpay_name") or info.get("shop_name") or "")
        self.number_label.configure(text=f"พร้อมเพย์ {info['promptpay_no']}" if info.get("promptpay_no") else "")

        payload = info.get("payload")
        if not payload:
            return self._show_text("ร้านยังไม่ได้ตั้งค่าเลขพร้อมเพย์\nกรุณาติดต่อร้านค้า")
        try:
            from utils import promptpay
            self._pil_image = promptpay.make_qr_image(payload, self._size)
            self._ctk_image = ctk.CTkImage(light_image=self._pil_image, dark_image=self._pil_image,
                                           size=(self._size, self._size))
        except Exception as exc:  # noqa: BLE001 - เช่น ไม่ได้ติดตั้ง qrcode
            self._pil_image = None
            return self._show_text(f"สร้าง QR ไม่สำเร็จ\n{exc}")
        self.qr_label.configure(image=self._ctk_image, text="")
        self.save_btn.configure(state="normal")

    def clear(self, text="ยังไม่มีข้อมูลการชำระเงิน"):
        self.amount_label.configure(text="")
        self.name_label.configure(text="")
        self.number_label.configure(text="")
        self._show_text(text)

    def save_image(self):
        """บันทึก QR เป็นไฟล์ PNG (ผู้ใช้เลือกที่เก็บ)"""
        if self._pil_image is None:
            return
        path = filedialog.asksaveasfilename(
            title="บันทึกรูป QR", defaultextension=".png", filetypes=[("PNG", "*.png")],
            initialfile="promptpay_qr.png")
        if path:
            self._pil_image.save(path)

    # ------------------------------------------------------------------ ภายใน
    def _show_text(self, text):
        self._pil_image = None
        self._ctk_image = None
        self.qr_label.configure(image=None, text=text)
        self.save_btn.configure(state="disabled")


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("360x540")
    box = PaymentQR(root)
    box.pack(pady=20)
    try:
        from utils import promptpay
        demo = dict(amount=1290.5, promptpay_no="0812345678", promptpay_name="ร้านทดสอบ", shop_name="Badminton Pro Shop",
                    payload=promptpay.build_payload("0812345678", 1290.5))
    except Exception as e:  # noqa: BLE001
        print("สร้าง payload ตัวอย่างไม่ได้:", e)
        demo = dict(amount=1290.5, promptpay_no="0812345678", promptpay_name="ร้านทดสอบ", payload="")
    box.set_info(demo)
    root.mainloop()
