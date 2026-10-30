"""
utils/icon_utils.py
ไลบรารีวาดไอคอนเวกเตอร์ (Vector-style Crisp Icons) ด้วย Pillow 4x Supersampling
สำหรับใช้กับ CustomTkinter (CTkImage) แทนอิโมจิ เพื่อความคมชัดและเข้ากับโทนสปอร์ตของร้าน
"""

from __future__ import annotations

import math
from PIL import Image, ImageDraw

_icon_cache: dict[tuple, object] = {}
_pil_cache: dict[tuple, Image.Image] = {}


def _hex_to_rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    c = (color or "#111318").strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return (17, 19, 24, alpha)
    try:
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), alpha)
    except ValueError:
        return (17, 19, 24, alpha)


def draw_icon_canvas(name: str, px_size: int, color_hex: str) -> Image.Image:
    """
    วาดไอคอนลงบน PIL Image โหมด RGBA ขนาด (px_size, px_size)
    สามารถนำไปวางซ้อน (alpha_composite) บนภาพอื่นหรือแปลงเป็น CTkImage ได้ทันที
    """
    px_size = max(8, int(px_size))
    cache_key = (name, px_size, str(color_hex))
    if cache_key in _pil_cache:
        return _pil_cache[cache_key].copy()

    S = max(64, px_size * 2)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = _hex_to_rgba(color_hex, 255)
    sw = max(3, int(S * 0.085))

    def sc(v: float) -> float:
        return v * S / 24.0

    icon = (name or "racket").strip().lower()

    if icon == "search":
        d.ellipse([sc(3.5), sc(3.5), sc(15.5), sc(15.5)], outline=col, width=sw)
        d.line([sc(14.0), sc(14.0), sc(20.5), sc(20.5)], fill=col, width=int(sw * 1.15))

    elif icon in ("heart", "heart_filled"):
        filled = icon == "heart_filled"
        pts = []
        for deg in range(0, 360, 4):
            t = math.radians(deg)
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            px = sc(12 + x * 0.56)
            py = sc(11.2 + y * 0.56)
            pts.append((px, py))
        if filled:
            d.polygon(pts, fill=col, outline=col)
        else:
            d.line(pts + [pts[0]], fill=col, width=sw, joint="curve")

    elif icon == "cart":
        d.line([sc(2.5), sc(4.5), sc(5.5), sc(4.5), sc(8.2), sc(15.0), sc(18.8), sc(15.0), sc(21.0), sc(7.5), sc(6.5), sc(7.5)],
               fill=col, width=sw, joint="curve")
        d.ellipse([sc(7.5), sc(17.2), sc(10.8), sc(20.5)], fill=col)
        d.ellipse([sc(16.2), sc(17.2), sc(19.5), sc(20.5)], fill=col)

    elif icon == "bell":
        d.pieslice([sc(5.5), sc(3.5), sc(18.5), sc(17.0)], 180, 360, outline=col, width=sw)
        d.line([sc(5.5), sc(10.2), sc(5.5), sc(16.0), sc(3.8), sc(17.5), sc(20.2), sc(17.5), sc(18.5), sc(16.0), sc(18.5), sc(10.2)],
               fill=col, width=sw, joint="curve")
        d.pieslice([sc(9.8), sc(17.5), sc(14.2), sc(21.5)], 0, 180, fill=col)

    elif icon == "chat":
        d.rounded_rectangle([sc(3.0), sc(4.0), sc(21.0), sc(16.5)], radius=sc(3.5), outline=col, width=sw)
        d.polygon([(sc(7.0), sc(16.5)), (sc(5.5), sc(20.8)), (sc(11.5), sc(16.5))], fill=col)
        d.ellipse([sc(7.5), sc(9.2), sc(9.3), sc(11.0)], fill=col)
        d.ellipse([sc(11.1), sc(9.2), sc(12.9), sc(11.0)], fill=col)
        d.ellipse([sc(14.7), sc(9.2), sc(16.5), sc(11.0)], fill=col)

    elif icon in ("user", "users"):
        d.ellipse([sc(8.0), sc(3.5), sc(16.0), sc(11.5)], outline=col, width=sw)
        d.arc([sc(4.0), sc(13.0), sc(20.0), sc(24.0)], 180, 360, fill=col, width=sw)
        if icon == "users":
            d.ellipse([sc(15.2), sc(4.5), sc(20.5), sc(9.8)], outline=col, width=max(2, sw - 1))
            d.arc([sc(14.0), sc(13.5), sc(22.8), sc(22.5)], 200, 355, fill=col, width=max(2, sw - 1))

    elif icon == "key":
        d.ellipse([sc(3.5), sc(7.5), sc(12.5), sc(16.5)], outline=col, width=sw)
        d.line([sc(12.5), sc(12.0), sc(21.0), sc(12.0)], fill=col, width=sw)
        d.line([sc(17.5), sc(12.0), sc(17.5), sc(16.0)], fill=col, width=sw)
        d.line([sc(20.2), sc(12.0), sc(20.2), sc(15.2)], fill=col, width=sw)

    elif icon == "lock":
        d.rounded_rectangle([sc(5.0), sc(10.5), sc(19.0), sc(20.5)], radius=sc(2.5), outline=col, width=sw)
        d.arc([sc(7.5), sc(3.5), sc(16.5), sc(14.5)], 180, 360, fill=col, width=sw)
        d.ellipse([sc(10.8), sc(14.2), sc(13.2), sc(16.6)], fill=col)

    elif icon == "shield":
        pts = [(sc(12.0), sc(2.8)), (sc(19.8), sc(5.8)), (sc(19.0), sc(13.2)),
               (sc(12.0), sc(21.2)), (sc(5.0), sc(13.2)), (sc(4.2), sc(5.8))]
        d.polygon(pts, outline=col, width=sw)
        d.line([sc(8.8), sc(12.0), sc(11.2), sc(14.5), sc(15.8), sc(9.5)], fill=col, width=sw, joint="curve")

    elif icon == "store":
        d.polygon([(sc(3.0), sc(9.5)), (sc(5.2), sc(4.0)), (sc(18.8), sc(4.0)), (sc(21.0), sc(9.5))], outline=col, width=sw)
        d.rectangle([sc(4.8), sc(9.5), sc(19.2), sc(20.2)], outline=col, width=sw)
        d.rectangle([sc(9.8), sc(13.5), sc(14.2), sc(20.2)], outline=col, width=sw)

    elif icon == "map_pin":
        d.ellipse([sc(6.0), sc(3.0), sc(18.0), sc(15.0)], outline=col, width=sw)
        d.polygon([(sc(6.8), sc(12.2)), (sc(12.0), sc(21.2)), (sc(17.2), sc(12.2))], fill=col)
        d.ellipse([sc(9.6), sc(6.6), sc(14.4), sc(11.4)], fill=(0, 0, 0, 0), outline=col, width=max(2, sw - 1))

    elif icon == "phone":
        d.rounded_rectangle([sc(6.5), sc(2.8), sc(17.5), sc(21.2)], radius=sc(2.5), outline=col, width=sw)
        d.ellipse([sc(10.8), sc(17.0), sc(13.2), sc(19.4)], fill=col)

    elif icon == "mail":
        d.rounded_rectangle([sc(3.0), sc(5.5), sc(21.0), sc(18.5)], radius=sc(2.0), outline=col, width=sw)
        d.line([sc(3.5), sc(6.5), sc(12.0), sc(13.0), sc(20.5), sc(6.5)], fill=col, width=sw, joint="curve")

    elif icon == "flash":
        pts = [(sc(13.5), sc(2.2)), (sc(5.5), sc(13.2)), (sc(11.8), sc(13.2)),
               (sc(10.2), sc(21.8)), (sc(18.8), sc(10.5)), (sc(12.5), sc(10.5))]
        d.polygon(pts, fill=col)

    elif icon == "fire":
        pts = [
            (sc(12.2), sc(2.2)), (sc(16.8), sc(7.8)), (sc(19.2), sc(12.8)),
            (sc(17.5), sc(18.8)), (sc(12.0), sc(21.5)), (sc(6.5), sc(18.8)),
            (sc(5.0), sc(13.2)), (sc(8.2), sc(8.5)), (sc(10.2), sc(11.2)),
        ]
        d.polygon(pts, fill=col)

    elif icon == "star":
        pts = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            r = sc(9.5) if i % 2 == 0 else sc(4.2)
            pts.append((sc(12.0) + r * math.cos(angle), sc(12.2) + r * math.sin(angle)))
        d.polygon(pts, fill=col)

    elif icon in ("coupon", "gift"):
        d.rounded_rectangle([sc(2.8), sc(6.2), sc(21.2), sc(17.8)], radius=sc(2.2), outline=col, width=sw)
        d.line([sc(9.5), sc(6.5), sc(9.5), sc(17.5)], fill=col, width=max(2, sw - 1))
        d.ellipse([sc(13.2), sc(9.8), sc(16.8), sc(14.2)], fill=col)

    elif icon == "truck":
        d.rectangle([sc(2.5), sc(6.5), sc(14.5), sc(16.2)], outline=col, width=sw)
        d.polygon([(sc(14.5), sc(9.5)), (sc(18.8), sc(9.5)), (sc(21.2), sc(12.8)),
                   (sc(21.2), sc(16.2)), (sc(14.5), sc(16.2))], outline=col, width=sw)
        d.ellipse([sc(5.5), sc(16.0), sc(9.5), sc(20.0)], fill=col)
        d.ellipse([sc(15.8), sc(16.0), sc(19.8), sc(20.0)], fill=col)

    elif icon == "category":
        for rx, ry in ((3.5, 3.5), (13.0, 3.5), (3.5, 13.0), (13.0, 13.0)):
            d.rounded_rectangle([sc(rx), sc(ry), sc(rx + 7.5), sc(ry + 7.5)], radius=sc(1.8), outline=col, width=sw)

    elif icon == "brand":
        pts = [(sc(12.0), sc(2.8)), (sc(19.8), sc(8.5)), (sc(16.8), sc(19.8)),
               (sc(7.2), sc(19.8)), (sc(4.2), sc(8.5))]
        d.polygon(pts, outline=col, width=sw)
        d.ellipse([sc(9.8), sc(9.8), sc(14.2), sc(14.2)], fill=col)

    elif icon == "compare":
        d.line([sc(4.0), sc(8.0), sc(19.5), sc(8.0)], fill=col, width=sw)
        d.line([sc(15.5), sc(4.5), sc(19.8), sc(8.0), sc(15.5), sc(11.5)], fill=col, width=sw, joint="curve")
        d.line([sc(20.0), sc(16.0), sc(4.5), sc(16.0)], fill=col, width=sw)
        d.line([sc(8.5), sc(12.5), sc(4.2), sc(16.0), sc(8.5), sc(19.5)], fill=col, width=sw, joint="curve")

    elif icon == "target":
        d.ellipse([sc(3.0), sc(3.0), sc(21.0), sc(21.0)], outline=col, width=sw)
        d.ellipse([sc(7.2), sc(7.2), sc(16.8), sc(16.8)], outline=col, width=max(2, sw - 1))
        d.ellipse([sc(10.2), sc(10.2), sc(13.8), sc(13.8)], fill=col)

    elif icon == "refresh":
        d.arc([sc(4.0), sc(4.0), sc(20.0), sc(20.0)], 30, 315, fill=col, width=sw)
        d.polygon([(sc(16.2), sc(2.8)), (sc(21.2), sc(6.5)), (sc(15.5), sc(8.8))], fill=col)

    elif icon == "trash":
        d.line([sc(4.0), sc(6.5), sc(20.0), sc(6.5)], fill=col, width=sw)
        d.rectangle([sc(8.8), sc(3.5), sc(15.2), sc(6.5)], outline=col, width=max(2, sw - 1))
        d.rounded_rectangle([sc(6.2), sc(6.5), sc(17.8), sc(20.5)], radius=sc(1.8), outline=col, width=sw)
        d.line([sc(10.0), sc(10.2), sc(10.0), sc(17.2)], fill=col, width=max(2, sw - 1))
        d.line([sc(14.0), sc(10.2), sc(14.0), sc(17.2)], fill=col, width=max(2, sw - 1))

    elif icon == "edit":
        d.polygon([(sc(14.8), sc(4.2)), (sc(19.8), sc(9.2)), (sc(8.8), sc(20.2)),
                   (sc(3.8), sc(20.2)), (sc(3.8), sc(15.2))], outline=col, width=sw)

    elif icon == "check":
        d.line([sc(4.2), sc(12.5), sc(9.8), sc(18.0), sc(20.0), sc(6.5)], fill=col, width=int(sw * 1.2), joint="curve")

    elif icon == "eye":
        d.arc([sc(2.5), sc(5.5), sc(21.5), sc(19.5)], 190, 350, fill=col, width=sw)
        d.arc([sc(2.5), sc(4.5), sc(21.5), sc(18.5)], 10, 170, fill=col, width=sw)
        d.ellipse([sc(9.5), sc(9.5), sc(14.5), sc(14.5)], fill=col)

    elif icon == "theme":
        d.pieslice([sc(4.0), sc(4.0), sc(20.0), sc(20.0)], 45, 315, fill=col)

    elif icon == "logout":
        d.line([sc(10.5), sc(4.0), sc(4.5), sc(4.0), sc(4.5), sc(20.0), sc(10.5), sc(20.0)], fill=col, width=sw)
        d.line([sc(9.5), sc(12.0), sc(20.2), sc(12.0)], fill=col, width=sw)
        d.line([sc(16.0), sc(8.0), sc(20.5), sc(12.0), sc(16.0), sc(16.0)], fill=col, width=sw, joint="curve")

    elif icon == "chart":
        d.line([sc(3.5), sc(20.0), sc(20.5), sc(20.0)], fill=col, width=sw)
        d.rectangle([sc(5.2), sc(12.0), sc(8.5), sc(20.0)], fill=col)
        d.rectangle([sc(10.5), sc(7.5), sc(13.8), sc(20.0)], fill=col)
        d.rectangle([sc(15.8), sc(4.5), sc(19.1), sc(20.0)], fill=col)

    elif icon in ("order", "receipt"):
        d.rounded_rectangle([sc(5.0), sc(3.2), sc(19.0), sc(20.8)], radius=sc(2.0), outline=col, width=sw)
        d.line([sc(8.2), sc(8.2), sc(15.8), sc(8.2)], fill=col, width=max(2, sw - 1))
        d.line([sc(8.2), sc(12.2), sc(15.8), sc(12.2)], fill=col, width=max(2, sw - 1))
        d.line([sc(8.2), sc(16.2), sc(13.2), sc(16.2)], fill=col, width=max(2, sw - 1))

    elif icon == "settings":
        d.ellipse([sc(6.2), sc(6.2), sc(17.8), sc(17.8)], outline=col, width=sw)
        d.ellipse([sc(9.8), sc(9.8), sc(14.2), sc(14.2)], fill=col)
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            x1, y1 = sc(12.0) + sc(6.0) * math.cos(rad), sc(12.0) + sc(6.0) * math.sin(rad)
            x2, y2 = sc(12.0) + sc(9.2) * math.cos(rad), sc(12.0) + sc(9.2) * math.sin(rad)
            d.line([x1, y1, x2, y2], fill=col, width=sw)

    else:  # racket (default)
        d.ellipse([sc(7.5), sc(2.5), sc(21.2), sc(15.8)], outline=col, width=sw)
        d.line([sc(11.0), sc(6.0), sc(18.0), sc(12.5)], fill=col, width=max(2, sw // 2))
        d.line([sc(18.0), sc(6.0), sc(11.0), sc(12.5)], fill=col, width=max(2, sw // 2))
        d.line([sc(10.0), sc(13.8), sc(3.5), sc(20.5)], fill=col, width=int(sw * 1.25))

    out = img.resize((px_size, px_size), Image.LANCZOS)
    _pil_cache[cache_key] = out
    return out.copy()


def get_icon(name: str, size: int = 18, light_color: str | tuple = "#111318", dark_color: str | None = None):
    """
    คืนค่า ctk.CTkImage ของไอคอนเวกเตอร์ รองรับทั้ง Light/Dark mode
    """
    import customtkinter as ctk

    if isinstance(light_color, (tuple, list)):
        lc = str(light_color[0])
        dc = str(light_color[1]) if len(light_color) > 1 else lc
    else:
        lc = str(light_color or "#111318")
        dc = str(dark_color or lc)

    size_int = max(8, int(size))
    key = (name, size_int, lc, dc)
    if key in _icon_cache:
        return _icon_cache[key]

    render_px = size_int * 2
    light_img = draw_icon_canvas(name, render_px, lc)
    dark_img = draw_icon_canvas(name, render_px, dc) if dc != lc else light_img

    ctk_img = ctk.CTkImage(light_image=light_img, dark_image=dark_img, size=(size_int, size_int))
    _icon_cache[key] = ctk_img
    return ctk_img
