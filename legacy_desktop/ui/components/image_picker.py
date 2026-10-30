"""
ui/components/image_picker.py
ตัวเลือกรูป (สินค้า/หมวด/แบรนด์/โปรไฟล์): แสดงตัวอย่าง + ปุ่มเลือกไฟล์ + ปุ่มลบรูป

คอมโพเนนต์นี้ "ไม่บันทึกไฟล์" — แค่เก็บ path ที่ผู้ใช้เลือก ให้หน้าเป็นคนบันทึกตอนกดบันทึกฟอร์ม:
    picker = ImagePicker(parent, size=(160, 160), initial_path=product["image_path"])
    ...
    new_file = picker.get_selected_file()   # path เต็มของไฟล์ที่เพิ่งเลือก หรือ None
    if new_file:   rel = image_utils.save_upload(new_file, config.PRODUCT_IMAGES_DIR, "product_5")
    elif picker.is_cleared():   # ผู้ใช้กด "ลบรูป" → ตั้ง image_path เป็น None
    else:          # ไม่เปลี่ยนรูปเดิม (picker.get_existing_path())

ตรวจเบื้องต้นตอนเลือก: นามสกุล (config.ALLOWED_IMAGE_EXTENSIONS), ขนาดไม่เกิน config.MAX_UPLOAD_BYTES,
เปิดเป็นรูปได้จริง — ผิดจะแสดงข้อความสีแดงใต้ตัวอย่าง (ไม่เปลี่ยนรูปที่เลือกไว้เดิม)

ทดสอบเดี่ยว:  python -m ui.components.image_picker   (รันจาก root โปรเจกต์)
"""

import os
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageOps

from ui.theme import ThemeManager
from utils.image_utils import load_ctk_image

try:
    import config
    _ALLOWED = tuple(e.lower() for e in config.ALLOWED_IMAGE_EXTENSIONS)
    _MAX_BYTES = int(config.MAX_UPLOAD_BYTES)
except Exception:  # noqa: BLE001 - รันเดี่ยวโดยไม่มี config ก็ยังใช้ได้
    _ALLOWED = (".jpg", ".jpeg", ".png")
    _MAX_BYTES = 5 * 1024 * 1024


class ImagePicker(ctk.CTkFrame):
    def __init__(self, parent, size=(160, 160), initial_path=None, on_change=None,
                 button_text="เลือกรูป...", allow_clear=True):
        super().__init__(parent, fg_color="transparent")
        # รับได้ทั้ง (กว้าง, สูง) และตัวเลขเดียว (= สี่เหลี่ยมจัตุรัส)
        self._size = (int(size), int(size)) if isinstance(size, (int, float)) else tuple(size)
        self._existing = initial_path or None   # path เดิมใน DB (relative)
        self._selected = None                   # ไฟล์ใหม่ที่เลือก (path เต็ม)
        self._cleared = False
        self._on_change = on_change
        self._image = None                      # เก็บอ้างอิงรูป ไม่ให้ถูกเก็บขยะ

        self.preview = ctk.CTkLabel(
            self, text="", width=self._size[0], height=self._size[1], corner_radius=10,
            fg_color=ThemeManager.get_color_pair("surface_alt"),
        )
        self.preview.pack()

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=(8, 0))
        ctk.CTkButton(row, text=button_text, width=110, command=self.choose,
                      **ThemeManager.button_style("outline", "sm")).pack(side="left")
        self.clear_btn = None
        if allow_clear:
            self.clear_btn = ctk.CTkButton(row, text="ลบรูป", width=70, command=self.clear,
                                           **ThemeManager.button_style("ghost", "sm"))
            self.clear_btn.pack(side="left", padx=(6, 0))

        self.error_label = ctk.CTkLabel(
            self, text="", font=ThemeManager.get_font("small"), wraplength=max(self._size[0], 160),
            text_color=ThemeManager.get_color_pair("danger"),
        )
        self.error_label.pack(pady=(4, 0))
        self._refresh_preview()

    # ------------------------------------------------------------------ API
    def get_selected_file(self):
        """path เต็มของไฟล์ที่ผู้ใช้เพิ่งเลือก (None = ยังไม่ได้เลือกไฟล์ใหม่)"""
        return self._selected

    def get_existing_path(self):
        """path รูปเดิม (relative) ที่ยังใช้อยู่ — None ถ้าไม่มี/ถูกกดลบรูป"""
        return None if self._cleared else self._existing

    def is_cleared(self) -> bool:
        """True = ผู้ใช้กด 'ลบรูป' (ต้องการไม่มีรูป)"""
        return self._cleared and self._selected is None

    def has_change(self) -> bool:
        return self._selected is not None or self.is_cleared()

    def set_image(self, path):
        """ตั้งรูปเดิม (relative path) และล้างสิ่งที่เลือกค้าง — ใช้ตอนโหลดแบบฟอร์มสินค้าใหม่"""
        self._existing = path or None
        self._selected = None
        self._cleared = False
        self.error_label.configure(text="")
        self._refresh_preview()

    reset = set_image
    set_initial = set_image

    # ------------------------------------------------------------------ การทำงาน
    def choose(self):
        path = filedialog.askopenfilename(
            title="เลือกรูปภาพ",
            filetypes=[("รูปภาพ", " ".join(f"*{e}" for e in _ALLOWED)), ("ทุกไฟล์", "*.*")],
        )
        if not path:
            return
        try:
            self._validate(path)
        except ValueError as exc:
            self.error_label.configure(text=str(exc))
            return
        self._selected = path
        self._cleared = False
        self.error_label.configure(text="")
        self._refresh_preview()
        self._notify()

    def clear(self):
        self._selected = None
        self._cleared = True
        self.error_label.configure(text="")
        self._refresh_preview()
        self._notify()

    def _validate(self, path):
        if os.path.splitext(path)[1].lower() not in _ALLOWED:
            raise ValueError("รองรับเฉพาะไฟล์ " + ", ".join(_ALLOWED))
        try:
            if os.path.getsize(path) > _MAX_BYTES:
                raise ValueError(f"ไฟล์ใหญ่เกิน {_MAX_BYTES // (1024 * 1024)}MB")
            with Image.open(path) as img:
                img.verify()
        except ValueError:
            raise
        except Exception:  # noqa: BLE001
            raise ValueError("ไฟล์นี้ไม่ใช่รูปภาพที่เปิดได้") from None

    def _refresh_preview(self):
        w, h = self._size
        if self._selected:
            try:
                with Image.open(self._selected) as img:
                    img = ImageOps.exif_transpose(img).convert("RGB")
                    img = ImageOps.contain(img, (w * 2, h * 2))   # ย่อก่อนเพื่อประหยัดหน่วยความจำ
                self._image = ctk.CTkImage(light_image=img, dark_image=img, size=self._fit(img.size))
            except Exception:  # noqa: BLE001
                self._image = load_ctk_image(None, (w, h))
        elif self._cleared:
            self._image = load_ctk_image(None, (w, h))          # placeholder "No Image"
        else:
            self._image = load_ctk_image(self._existing, (w, h))
        self.preview.configure(image=self._image)

    def _fit(self, img_size):
        """ขนาดแสดงผลที่คงสัดส่วนและไม่เกินกรอบ"""
        w, h = self._size
        iw, ih = img_size
        scale = min(w / iw, h / ih)
        return max(1, int(iw * scale)), max(1, int(ih * scale))

    def _notify(self):
        if self._on_change:
            self._on_change(self)


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("320x320")
    info = ctk.CTkLabel(root, text="")
    picker = ImagePicker(root, on_change=lambda p: info.configure(
        text=f"ไฟล์ใหม่: {p.get_selected_file()}\nลบรูป: {p.is_cleared()}"))
    picker.pack(pady=20)
    info.pack()
    root.mainloop()
