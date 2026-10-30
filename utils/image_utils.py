"""
utils/image_utils.py
โหลด/บันทึก/ย่อรูปภาพ และสร้างภาพ Gradient/Banner/Shadow พร้อม cache สำหรับ CustomTkinter
    img = load_ctk_image("assets/images/products/x.jpg", (200, 200))   # ไม่พบไฟล์ -> รูป placeholder (ไม่ crash)
    rel = save_upload(src_path, PRODUCT_IMAGES_DIR, "product_12")      # -> 'assets/images/products/product_12_....jpg'
"""
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, UnidentifiedImageError

from config import (
    ALLOWED_IMAGE_EXTENSIONS, BASE_DIR, FONTS_DIR, MAX_UPLOAD_BYTES, UPLOAD_MAX_SIDE,
)

_ctk_cache: dict = {}


def resolve_path(path) -> Path:
    """path แบบ relative ที่เก็บใน DB -> path เต็ม (อิง root โปรเจกต์) | path เต็มอยู่แล้วคืนตามเดิม"""
    p = Path(path)
    return p if p.is_absolute() else BASE_DIR / p


def _to_relative(path: Path) -> str:
    """path เต็ม -> relative (เครื่องหมาย /) ถ้าอยู่ใต้ root โปรเจกต์ ไม่งั้นคืน path เต็ม"""
    try:
        return path.resolve().relative_to(BASE_DIR).as_posix()
    except ValueError:
        return str(path)


def _get_font(size: int, thai: bool = False, bold: bool = True):
    if thai:
        candidates = ("Kanit-Bold.ttf", "Kanit-SemiBold.ttf", "Kanit-Regular.ttf") if bold else ("Kanit-Regular.ttf", "Kanit-Medium.ttf")
    else:
        candidates = ("Arimo-Bold.ttf", "Arimo-Regular.ttf", "Kanit-Bold.ttf") if bold else ("Arimo-Regular.ttf", "Kanit-Regular.ttf")
    for name in candidates:
        font_file = FONTS_DIR / name
        if font_file.exists():
            try:
                return ImageFont.truetype(str(font_file), size)
            except OSError:
                pass
    return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = (hex_color or "#141619").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return 20, 22, 25


def make_gradient_image(size: tuple[int, int], color_start: str = "#141619", color_end: str = "#E63946",
                        accent_stripe: str | None = "#FFB703") -> Image.Image:
    """สร้างภาพพื้นหลังไล่เฉดสีแนวนอนพร้อมแถบสีเหลืองสปอร์ตด้านล่าง"""
    w, h = max(int(size[0]), 1), max(int(size[1]), 1)
    r1, g1, b1 = _hex_to_rgb(color_start)
    r2, g2, b2 = _hex_to_rgb(color_end)
    img = Image.new("RGB", (w, h), (r1, g1, b1))
    draw = ImageDraw.Draw(img)
    steps = max(1, w - 1)
    for x in range(w):
        t = x / steps
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(x, 0), (x, h)], fill=(r, g, b))
    if accent_stripe:
        stripe_h = max(4, h // 18)
        draw.rectangle([0, h - stripe_h, w, h], fill=_hex_to_rgb(accent_stripe))
    return img


def make_gradient_ctk_image(size: tuple[int, int], color_start: str = "#141619",
                            color_end: str = "#E63946", accent_stripe: str | None = "#FFB703"):
    """คืน CTkImage ไล่เฉดสีที่ cache ไว้ตามขนาดและคู่สี เพื่อไม่ให้สร้างซ้ำทุกครั้งที่วาดหน้า"""
    import customtkinter as ctk

    size = (max(1, int(size[0])), max(1, int(size[1])))
    key = ("gradient", size, color_start, color_end, accent_stripe)
    if key in _ctk_cache:
        return _ctk_cache[key]
    pil_img = make_gradient_image(size, color_start, color_end, accent_stripe)
    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    _ctk_cache[key] = ctk_img
    return ctk_img


def make_welcome_shadow_ctk_image(text: str = "Welcome ", font_size: int = 36,
                                  text_color: str = "#FFB703",
                                  shadow_offset: tuple[int, int] = (3, 4),
                                  blur_radius: float = 2.4):
    """
    T10: สร้างภาพข้อความ 'Welcome' ตัวใหญ่พร้อมเงาสีดำเบลอๆ เฉียงลงด้านล่างนิดเดียว (ไร้กรอบสี่เหลี่ยมครอบ)
    คืนค่า CTkImage
    """
    import customtkinter as ctk

    ox, oy = int(shadow_offset[0]), int(shadow_offset[1])
    key = ("welcome_shadow", text, int(font_size), text_color, (ox, oy), float(blur_radius))
    if key in _ctk_cache:
        return _ctk_cache[key]

    font = _get_font(int(font_size), thai=False, bold=True)
    dummy = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    d_draw = ImageDraw.Draw(dummy)
    bbox = d_draw.textbbox((0, 0), text, font=font)
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])
    pad_x, pad_y = 10, 10
    w = tw + pad_x * 2 + abs(ox)
    h = th + pad_y * 2 + abs(oy)

    # วาดเงาสีดำเบลอเฉียงลงขวาล่าง
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    tx = pad_x - bbox[0]
    ty = pad_y - bbox[1]
    s_draw.text((tx + ox, ty + oy), text, font=font, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=float(blur_radius)))

    # วาดตัวหนังสือจริงทับด้านบน
    fg_draw = ImageDraw.Draw(shadow)
    r, g, b = _hex_to_rgb(text_color)
    fg_draw.text((tx, ty), text, font=font, fill=(r, g, b, 255))

    ctk_img = ctk.CTkImage(light_image=shadow, dark_image=shadow, size=(w, h))
    _ctk_cache[key] = ctk_img
    return ctk_img


def make_placeholder(size: tuple[int, int], text: str = "No Image") -> Image.Image:
    """
    สร้างรูปแทนเมื่อไม่มีรูปจริง (พื้นเทาอ่อน + กรอบ + แถบเหลืองแดง + ข้อความ)
    """
    w, h = max(int(size[0]), 1), max(int(size[1]), 1)
    img = Image.new("RGB", (w, h), "#F1F5F9")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline="#CBD5E1", width=2)
    draw.rectangle([0, h - 6, w // 2, h - 1], fill="#FFB703")
    draw.rectangle([w // 2, h - 6, w - 1, h - 1], fill="#E63946")
    if text:
        has_thai = any("\u0E00" <= ch <= "\u0E7F" for ch in str(text))
        font = _get_font(max(10, min(w, h) // 8), thai=has_thai)
        box = draw.textbbox((0, 0), text, font=font)
        tw, th = box[2] - box[0], box[3] - box[1]
        draw.text(((w - tw) / 2 - box[0], (h - th) / 2 - box[1]), text, fill="#475569", font=font)
    return img


def _apply_cover_and_radius(pil_img: Image.Image, size: tuple[int, int],
                            cover: bool = False, corner_radius: int = 0,
                            contain_bg: tuple[int, int, int, int] | None = None) -> Image.Image:
    """ปรับขนาดภาพแบบเต็มกรอบ (cover) หรือพอดีกรอบบนพื้นหลัง (contain_bg) และตัดมุมมนด้วย 4x supersampling"""
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    img = pil_img.convert("RGBA")
    if contain_bg is not None:
        bg = Image.new("RGBA", (w, h), contain_bg)
        fitted = ImageOps.contain(img, (w, h), method=Image.LANCZOS)
        ox = (w - fitted.width) // 2
        oy = (h - fitted.height) // 2
        bg.alpha_composite(fitted, (ox, oy))
        img = bg
    elif cover:
        img = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))
    elif img.size != (w, h):
        img = img.resize((w, h), Image.LANCZOS)

    if corner_radius and corner_radius > 0:
        scale = 4
        r = min(int(corner_radius), min(w, h) // 2)
        mask_hi = Image.new("L", (w * scale, h * scale), 0)
        m_draw = ImageDraw.Draw(mask_hi)
        m_draw.rounded_rectangle([0, 0, w * scale - 1, h * scale - 1], radius=r * scale, fill=255)
        mask = mask_hi.resize((w, h), Image.LANCZOS)
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        out.paste(img, (0, 0), mask)
        return out
    return img


def _load_pil_or_placeholder(path, size: tuple[int, int], placeholder_text: str = "No Image") -> tuple[Image.Image, tuple]:
    """โหลด PIL Image จาก path หรือคืน placeholder พร้อม cache key พื้นฐาน"""
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    pil_img = None
    base_key = ("placeholder", (w, h), placeholder_text)
    if path:
        file_path = resolve_path(path)
        try:
            mtime = file_path.stat().st_mtime_ns
            base_key = (str(file_path), mtime, (w, h))
            with Image.open(file_path) as src:
                pil_img = src.convert("RGBA").copy()
        except (OSError, UnidentifiedImageError):
            pil_img = None
            base_key = ("placeholder", (w, h), placeholder_text)
    if pil_img is None:
        pil_img = make_placeholder((w, h), text=placeholder_text).convert("RGBA")
    return pil_img, base_key


def load_ctk_image(path, size: tuple[int, int], cover: bool = False, corner_radius: int = 0,
                   placeholder_text: str = "No Image", contain_on_white: bool = False):
    """
    โหลดรูปเป็น CTkImage ขนาด size (กว้าง, สูง) พร้อม cache
    - cover=True: ขยาย/ครอปรูปให้เต็มกรอบ (object-fit: cover)
    - contain_on_white=True: จัดวางรูปให้คงสัดส่วนเดิมบนพื้นขาว ไม่บิดเบี้ยว
    - corner_radius > 0: ทำมุมรูปภาพมน (border-radius)
    - path เป็น None / ไม่พบไฟล์ / ไฟล์เสีย -> ใช้ placeholder แทน (ไม่ raise)
    """
    import customtkinter as ctk

    size = (max(1, int(size[0])), max(1, int(size[1])))
    pil_img, base_key = _load_pil_or_placeholder(path, size, placeholder_text=placeholder_text)
    key = (*base_key, bool(cover), int(corner_radius or 0), bool(contain_on_white))
    if key in _ctk_cache:
        return _ctk_cache[key]

    if contain_on_white:
        pil_img = _apply_cover_and_radius(
            pil_img, size, cover=False, corner_radius=corner_radius,
            contain_bg=(255, 255, 255, 255),
        )
    elif cover or corner_radius:
        pil_img = _apply_cover_and_radius(pil_img, size, cover=cover, corner_radius=corner_radius)

    image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    _ctk_cache[key] = image
    return image


def load_product_card_image(path, size: tuple[int, int], corner_radius: int = 10,
                            discount_pct: int = 0, in_stock: bool = True,
                            show_heart: bool = False, in_wishlist: bool = False):
    """
    T07: โหลดรูปการ์ดสินค้าสัดส่วน 1:1 (ส่วนบนของการ์ด 3:4) มุมมน โดยไม่ทำให้สัดส่วนสินค้าเพี้ยน
    พร้อมวาดป้ายส่วนลด (ซ้ายบน) และปุ่มหัวใจทรงกลม (ขวาบน) ลงบนภาพโดยตรง
    """
    import customtkinter as ctk
    from utils import icon_utils

    size = (max(1, int(size[0])), max(1, int(size[1])))
    pil_img, base_key = _load_pil_or_placeholder(path, size)
    key = ("card_img_1x1", *base_key, int(corner_radius), int(discount_pct or 0),
           bool(in_stock), bool(show_heart), bool(in_wishlist))
    if key in _ctk_cache:
        return _ctk_cache[key]

    iw, ih = pil_img.size
    aspect = iw / max(ih, 1)
    if 0.82 <= aspect <= 1.22:
        canvas = _apply_cover_and_radius(pil_img, size, cover=True, corner_radius=corner_radius)
    else:
        canvas = _apply_cover_and_radius(
            pil_img, size, cover=False, corner_radius=corner_radius,
            contain_bg=(255, 255, 255, 255),
        )
    w, h = size

    if not in_stock:
        badge_w, badge_h = 74, 24
        overlay = Image.new("RGBA", (badge_w * 2, badge_h * 2), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle([0, 0, badge_w * 2 - 1, badge_h * 2 - 1], radius=12, fill=(100, 116, 139, 235))
        overlay = overlay.resize((badge_w, badge_h), Image.LANCZOS)
        od_sm = ImageDraw.Draw(overlay)
        fnt = _get_font(11)
        od_sm.text((10, 5), "OUT OF STOCK", fill=(255, 255, 255, 255), font=fnt)
        canvas.alpha_composite(overlay, (8, 8))
    elif discount_pct and int(discount_pct) > 0:
        txt = f"-{int(discount_pct)}%"
        badge_w, badge_h = 54, 24
        overlay = Image.new("RGBA", (badge_w * 2, badge_h * 2), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle([0, 0, badge_w * 2 - 1, badge_h * 2 - 1], radius=12, fill=(230, 57, 70, 245))
        overlay = overlay.resize((badge_w, badge_h), Image.LANCZOS)
        od_sm = ImageDraw.Draw(overlay)
        fnt = _get_font(12)
        box = od_sm.textbbox((0, 0), txt, font=fnt)
        tw, th = box[2] - box[0], box[3] - box[1]
        od_sm.text(((badge_w - tw) / 2 - box[0], (badge_h - th) / 2 - box[1]), txt, fill=(255, 255, 255, 255), font=fnt)
        canvas.alpha_composite(overlay, (8, 8))

    if show_heart:
        diam = 32
        scale = 4
        D = diam * scale
        circle = Image.new("RGBA", (D, D), (0, 0, 0, 0))
        cd = ImageDraw.Draw(circle)
        bg_rgba = (255, 240, 242, 245) if in_wishlist else (255, 255, 255, 238)
        border_rgba = (230, 57, 70, 255) if in_wishlist else (203, 213, 225, 245)
        cd.ellipse([scale, scale, D - scale - 1, D - scale - 1],
                   fill=bg_rgba, outline=border_rgba, width=max(2, int(scale * 1.1)))
        heart_icon = icon_utils.draw_icon_canvas(
            "heart_filled" if in_wishlist else "heart",
            int(diam * 0.58) * scale,
            "#E63946" if in_wishlist else "#475569",
        )
        hoff = (D - heart_icon.width) // 2
        circle.alpha_composite(heart_icon, (hoff, hoff))
        circle_sm = circle.resize((diam, diam), Image.LANCZOS)
        canvas.alpha_composite(circle_sm, (w - diam - 8, 8))

    image = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=size)
    _ctk_cache[key] = image
    return image


def clear_cache() -> None:
    """ล้าง cache รูป (เรียกหลังเปลี่ยนรูปสินค้า)"""
    _ctk_cache.clear()


def save_upload(src, dest_dir, prefix: str, max_side: int = UPLOAD_MAX_SIDE) -> str:
    """
    บันทึกรูปที่ผู้ใช้เลือก (สลิป/รูปสินค้า/รูปโปรไฟล์/แบนเนอร์/โลโก้) ลง dest_dir
    - รับเฉพาะ .jpg/.jpeg/.png/.webp ขนาดไม่เกิน MAX_UPLOAD_BYTES และต้องเป็นรูปจริง
    - รักษาความโปร่งใส (Alpha channel) สำหรับไฟล์ PNG และ WEBP
    """
    src_path = Path(src)
    if not src_path.is_file():
        raise ValueError("ไม่พบไฟล์รูปภาพที่เลือก")

    ext = src_path.suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("รองรับเฉพาะไฟล์รูป .jpg, .png และ .webp เท่านั้น")

    if src_path.stat().st_size > MAX_UPLOAD_BYTES:
        raise ValueError(f"ไฟล์ใหญ่เกินไป (ไม่เกิน {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)")

    try:
        with Image.open(src_path) as opened:
            opened.load()
            img = opened.copy()
            fmt = (opened.format or "").upper()
    except (OSError, UnidentifiedImageError):
        raise ValueError("ไฟล์นี้ไม่ใช่รูปภาพที่ถูกต้อง") from None

    if fmt not in ("JPEG", "PNG", "WEBP"):
        raise ValueError("รองรับเฉพาะไฟล์รูป .jpg, .png และ .webp เท่านั้น")

    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)

    out_dir = Path(dest_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = "".join(ch for ch in str(prefix) if ch.isalnum() or ch in ("_", "-")) or "img"
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")

    has_alpha = img.mode in ("RGBA", "LA") or "transparency" in img.info
    keep_png = fmt == "PNG" or (fmt == "WEBP" and (has_alpha or safe_prefix in ("logo", "login_banner")))
    out_ext = ".png" if keep_png else ".jpg"
    dest = (out_dir / f"{safe_prefix}_{stamp}_{uuid.uuid4().hex[:6]}{out_ext}").resolve()
    if out_dir not in dest.parents:
        raise ValueError("ตำแหน่งจัดเก็บไฟล์ไม่ปลอดภัย")

    try:
        if keep_png:
            img.save(dest, "PNG", optimize=True)
        else:
            img.convert("RGB").save(dest, "JPEG", quality=88, optimize=True)
    except OSError:
        raise ValueError("บันทึกรูปภาพไม่สำเร็จ") from None

    return _to_relative(dest)


def delete_upload(rel_path) -> None:
    """ลบไฟล์รูปที่เคยอัปโหลด (ไม่มีไฟล์ = ข้าม ไม่ error) — ใช้เมื่อเปลี่ยน/ลบรูปสินค้าหรือสลิป"""
    if not rel_path:
        return
    try:
        resolve_path(rel_path).unlink(missing_ok=True)
    except OSError:
        pass
    clear_cache()
