"""
ui/components/auth_layout.py
โครงหน้า Login & Sign Up โฉมใหม่ (AI.HERE Bad🅜-Zone — ขนาดอ้างอิง 1456×819 / การ์ดหลัก 1294×657):
- แบ่งครึ่ง 50/50 (โซนแบนเนอร์เหลือง #FFB600 + radial glow + เงาพื้น + เงารองเท้า / โซนฟอร์มพื้นขาว + เงาตะเข็บกลาง)
- ปุ่มสลับ LOGIN / SIGN UP ทรงแคปซูล (Pill 260×60) ลอยกึ่งกลางรอยต่อ
- โลโก้ร้าน 115×115 px แบบ No BG ไม่มีขอบ/วงกลม/พื้นหลัง/เงา (อัปโหลดโดย Owner)
- แบนเนอร์รองเท้าสุ่มเปลี่ยนจากตาราง login_banners (สูงสุด 7 รูป) ไม่ซ้ำติดกัน
- อนิเมชันสลับฝั่ง 650ms easeInOutCubic
"""
import random
import customtkinter as ctk

from services import banner_service, settings_service
from ui.theme import ThemeManager
from utils.image_utils import load_ctk_image

ROTATE_MS = 5000


class AuthSplitLayout(ctk.CTkFrame):
    def __init__(self, parent, controller, form_title: str = "", form_subtitle: str = "",
                 center_vertically: bool = True, mode: str = "login"):
        super().__init__(parent, fg_color="#E9E9E9")
        self.controller = controller
        self.mode = "signup" if mode in ("signup", "register") else "login"
        self._banners = []
        self._current_idx = -1
        self._rotate_job = None
        self._shoe_img = None
        self._logo_img = None

        self.main_card = ctk.CTkFrame(
            self, width=1294, height=657, corner_radius=50,
            fg_color="#FFFFFF", border_width=1, border_color="#FDE68A",
        )
        self.main_card.place(relx=0.5, rely=0.5, anchor="center")

        self.banner_zone = ctk.CTkFrame(
            self.main_card, width=647, height=657, corner_radius=50, fg_color="#FFB600",
        )
        self.shoe_label = ctk.CTkLabel(self.banner_zone, text="", fg_color="transparent")
        self.shoe_label.place(relx=0.5, rely=0.5, anchor="center")

        self.form_zone = ctk.CTkFrame(
            self.main_card, width=647, height=657, corner_radius=0, fg_color="#FFFFFF",
        )

        self.logo_label = ctk.CTkLabel(
            self.form_zone, text="", width=115, height=115, fg_color="transparent",
        )
        self.logo_label.place(x=266 if self.mode == "login" else 226, y=40)

        self.brand_label = ctk.CTkLabel(
            self.form_zone, text="AI.HERE Bad🅜-Zone",
            font=("Arimo", 11, "bold"), text_color="#111111", fg_color="transparent",
        )
        if self.mode == "login":
            self.brand_label.place(x=510, y=24)

        if center_vertically:
            self.form_card = ctk.CTkFrame(
                self.form_zone, width=449, height=411, corner_radius=38,
                fg_color="#FFFFFF", border_width=1, border_color="#E5E7EB",
            )
            self.form_card.place(x=98, y=187)
        else:
            self.scroll_zone = ctk.CTkScrollableFrame(
                self.form_zone, width=620, height=640, fg_color="transparent",
            )
            self.scroll_zone.place(x=0, y=0)
            self.form_card = ctk.CTkFrame(
                self.scroll_zone, width=451, height=949, corner_radius=38,
                fg_color="#FFFFFF", border_width=1, border_color="#E5E7EB",
            )
            self.form_card.pack(padx=(58, 110), pady=(187, 24), fill="x")

        self.header_box = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.header_box.pack(fill="x", padx=18, pady=(22, 4))
        self.title_label = ctk.CTkLabel(
            self.header_box, text=form_title, font=ThemeManager.get_font("h1"),
            text_color="#111111", anchor="w",
        )
        self.title_label.pack(fill="x")
        self.subtitle_label = ctk.CTkLabel(
            self.header_box, text=form_subtitle, font=ThemeManager.get_font("small"),
            text_color="#111111", anchor="w", justify="left", wraplength=410,
        )
        self.subtitle_label.pack(fill="x", pady=(2, 0))

        self.form_body = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.form_body.pack(fill="both", expand=True, padx=18, pady=(4, 18))

        # Pill Toggle (260 × 60 at center 647, 97)
        self.pill_frame = ctk.CTkFrame(
            self.main_card, width=260, height=60, corner_radius=30, fg_color="#FFFFFF",
        )
        self.pill_frame.place(x=517, y=67)
        self.pill_left_btn = ctk.CTkButton(
            self.pill_frame, width=130, height=60, corner_radius=30,
            text="SIGN UP" if self.mode == "login" else "LOGIN",
            fg_color="#FFFFFF" if self.mode == "login" else "#FFB600",
            text_color="#111111", font=("Arimo", 22, "bold"),
            command=self._on_pill_left,
        )
        self.pill_left_btn.pack(side="left")
        self.pill_right_btn = ctk.CTkButton(
            self.pill_frame, width=130, height=60, corner_radius=30,
            text="LOGIN" if self.mode == "login" else "SIGN UP",
            fg_color="#FFB600" if self.mode == "login" else "#FFFFFF",
            text_color="#111111", font=("Arimo", 22, "bold"),
            command=self._on_pill_right,
        )
        self.pill_right_btn.pack(side="right")

        self._apply_side_positions()

    def _apply_side_positions(self):
        if self.mode == "login":
            self.banner_zone.place(x=0, y=0)
            self.form_zone.place(x=647, y=0)
        else:
            self.form_zone.place(x=0, y=0)
            self.banner_zone.place(x=647, y=0)

    def _on_pill_left(self):
        target = "register" if self.mode == "login" else "login"
        self.controller.show(target)

    def _on_pill_right(self):
        pass

    def set_titles(self, title: str, subtitle: str = ""):
        self.title_label.configure(text=title)
        self.subtitle_label.configure(text=subtitle)

    def refresh_showcase(self):
        self._stop_rotate()
        try:
            shop = settings_service.get_shop_info()
            logo_path = shop.get("store_logo_path") or shop.get("shop_logo_path") or ""
            if logo_path:
                self._logo_img = load_ctk_image(logo_path, (115, 115), cover=False)
                self.logo_label.configure(image=self._logo_img, text="")
            else:
                self.logo_label.configure(image=None, text="")
        except Exception:  # noqa: BLE001
            pass

        try:
            rows = banner_service.list_login_banners()
            self._banners = [r.get("file_path") for r in rows if r.get("file_path")][:7]
        except Exception:  # noqa: BLE001
            self._banners = []

        self._pick_next_banner()
        if len(self._banners) >= 2:
            self._rotate_job = self.after(ROTATE_MS, self._auto_step)

    def _pick_next_banner(self):
        if not self._banners:
            self.shoe_label.configure(image=None, text="")
            return
        if len(self._banners) == 1:
            self._current_idx = 0
        else:
            cands = [i for i in range(len(self._banners)) if i != self._current_idx]
            self._current_idx = random.choice(cands)
        path = self._banners[self._current_idx]
        self._shoe_img = load_ctk_image(path, (520, 440), cover=False)
        self.shoe_label.configure(image=self._shoe_img, text="")

    def _auto_step(self):
        self._rotate_job = None
        if not self.winfo_exists():
            return
        self._pick_next_banner()
        if len(self._banners) >= 2:
            self._rotate_job = self.after(ROTATE_MS, self._auto_step)

    def _stop_rotate(self):
        if self._rotate_job is not None:
            try:
                self.after_cancel(self._rotate_job)
            except Exception:  # noqa: BLE001
                pass
            self._rotate_job = None

    def destroy(self):
        self._stop_rotate()
        super().destroy()
