"""
ui/components/rating.py
แสดง/เลือกดาวรีวิว (1–5)

ใช้งาน:
    RatingStars(parent, value=4.3, count=12)                       # แสดงอย่างเดียว  ★★★★☆ 4.3 (12)
    stars = RatingStars(parent, interactive=True, size=28)          # ให้ผู้ใช้เลือกดาว
    stars.get()  ->  int 0–5      stars.set(4)

ทดสอบเดี่ยว:  python -m ui.components.rating   (รันจาก root โปรเจกต์)
"""

import customtkinter as ctk

from ui.theme import ThemeManager

STAR = "★"


class RatingStars(ctk.CTkFrame):
    def __init__(self, parent, value=0.0, count=None, size=16, interactive=False,
                 command=None, show_value=True, **kwargs):
        """
        value        : คะแนนเฉลี่ย (ทศนิยมได้ ปัดเป็นดาวเต็มด้วยการปัดปกติ) หรือคะแนนที่เลือก (interactive)
        count        : จำนวนรีวิว (แสดงต่อท้ายเป็น "(12)") — None = ไม่แสดง
        size         : ขนาดตัวอักษรของดาว
        interactive  : True = คลิกเลือกดาวได้ (hover พรีวิว) ; ค่าที่เลือกเป็นจำนวนเต็ม 1–5
        command      : เรียก command(value:int) เมื่อผู้ใช้เลือกดาว
        show_value   : แสดงตัวเลขคะแนนต่อท้าย (เฉพาะโหมดแสดงผล)
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._interactive = interactive
        self._command = command
        self._show_value = show_value and not interactive
        self._count = count
        self._value = 0.0
        self._hover = 0

        self._on = ThemeManager.get_color_pair("star")
        self._off = ThemeManager.get_color_pair("star_off")
        self._stars = []
        for i in range(5):
            lbl = ctk.CTkLabel(self, text=STAR, font=("Arimo", size), text_color=self._off,
                               width=size + 6)
            lbl.pack(side="left")
            if interactive:
                try:
                    lbl.configure(cursor="hand2")
                except Exception:  # noqa: BLE001 - บางเวอร์ชันของ customtkinter ไม่รองรับ cursor ที่ label
                    pass
                lbl.bind("<Button-1>", lambda _e, n=i + 1: self._choose(n))
                lbl.bind("<Enter>", lambda _e, n=i + 1: self._set_hover(n))
                lbl.bind("<Leave>", lambda _e: self._set_hover(0))
            self._stars.append(lbl)

        self._text = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        )
        self._text.pack(side="left", padx=(6, 0))
        self.set(value, count)

    # ------------------------------------------------------------------ API
    def set(self, value, count=None):
        """ตั้งค่าคะแนน (และจำนวนรีวิวถ้าระบุ)"""
        try:
            self._value = max(0.0, min(5.0, float(value or 0)))
        except (TypeError, ValueError):
            self._value = 0.0
        if count is not None:
            self._count = count
        self._paint()

    def get(self) -> int:
        """คะแนนที่เลือก (จำนวนเต็ม 0–5)"""
        return int(round(self._value))

    # ------------------------------------------------------------------ ภายใน
    def _filled(self) -> int:
        return self._hover if self._hover else int(round(self._value))

    def _paint(self):
        filled = self._filled()
        for i, lbl in enumerate(self._stars):
            lbl.configure(text_color=self._on if i < filled else self._off)

        parts = []
        if self._show_value:
            parts.append(f"{self._value:.1f}" if self._value else "ยังไม่มีคะแนน")
        if self._count is not None and not self._interactive:
            parts.append(f"({self._count})")
        self._text.configure(text=" ".join(parts))

    def _set_hover(self, n):
        self._hover = n
        self._paint()

    def _choose(self, n):
        self._value = float(n)
        self._hover = 0
        self._paint()
        if self._command:
            self._command(n)


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("360x240")
    RatingStars(root, value=4.3, count=12).pack(pady=10)
    RatingStars(root, value=0).pack(pady=10)
    picked = ctk.CTkLabel(root, text="ยังไม่เลือก")
    RatingStars(root, interactive=True, size=30, command=lambda v: picked.configure(text=f"เลือก {v} ดาว")).pack(pady=10)
    picked.pack()
    root.mainloop()
