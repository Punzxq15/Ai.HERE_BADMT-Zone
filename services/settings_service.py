"""
services/settings_service.py
อ่าน/แก้การตั้งค่าร้านและข้อมูลติดต่อร้าน (ตาราง settings) — อ่านได้ทุกคน (เป็นข้อมูลสาธารณะ)
แก้ได้เฉพาะเจ้าของร้าน (action settings.manage)
รองรับโลโก้ร้าน (store_logo_path / shop_logo_path), ชื่อร้าน, ที่ตั้งหน้าร้าน และข้อมูลร้านทั้งหมด
รวมถึงค่าปรับแต่งความยืดหยุ่นของร้านตาม T15 (ความเร็วเลื่อน Flash Sale, คูปองหน้าหลัก, สไลด์ Login ฯลฯ)
"""
import math
import re

from config import CONTACT_DEFAULT_SETTINGS, DEFAULT_SETTINGS
from core import permissions
from database import repo_settings
from services import audit_service
from utils import promptpay, validators

EDITABLE_KEYS = tuple(DEFAULT_SETTINGS.keys())
CONTACT_KEYS = tuple(CONTACT_DEFAULT_SETTINGS.keys())
ALL_KNOWN_KEYS = tuple(dict.fromkeys(EDITABLE_KEYS + CONTACT_KEYS))


def _resolve_shop_name(raw_val) -> str:
    if raw_val is not None and str(raw_val).strip() != "":
        return str(raw_val).strip()
    return DEFAULT_SETTINGS.get("shop_name", "AI.HERE BADᴍᴛ-Zone")


# ==========================================
# อ่านค่า
# ==========================================

def get(key: str, default=None):
    """ค่าของ key (ข้อความ) — ไม่มีใน DB ใช้ค่าตั้งต้นจาก config.DEFAULT_SETTINGS หรือ CONTACT_DEFAULT_SETTINGS"""
    if key == "shop_name":
        raw_val = repo_settings.get("shop_name", None)
        return _resolve_shop_name(raw_val)
    if key in ("store_logo_path", "shop_logo_path"):
        raw_all = repo_settings.get_all()
        v = raw_all.get("store_logo_path")
        if v is None or v == "":
            v = raw_all.get("shop_logo_path")
        if v is not None:
            return v
        return default if default is not None else ""
    val = repo_settings.get(key, default)
    if val is not None:
        return val
    return CONTACT_DEFAULT_SETTINGS.get(key, default)


def get_float(key: str, default: float = 0.0) -> float:
    """ค่าเป็นตัวเลขทศนิยม — แปลงไม่ได้ให้ใช้ค่าตั้งต้นของระบบ แล้วค่อย default"""
    for text in (repo_settings.get(key), DEFAULT_SETTINGS.get(key)):
        try:
            return float(text)
        except (TypeError, ValueError):
            continue
    return float(default)


def get_int(key: str, default: int = 0) -> int:
    """ค่าเป็นจำนวนเต็ม — แปลงไม่ได้ให้ใช้ค่าตั้งต้นของระบบ แล้วค่อย default"""
    return int(get_float(key, default))


def get_bool(key: str, default: bool = False) -> bool:
    """ค่าเป็นจริง/เท็จ ('1','true','yes','on' = จริง)"""
    text = repo_settings.get(key)
    if text is None:
        return default
    return str(text).strip().lower() in ("1", "true", "yes", "on")


def _resolve_logo_from_raw(raw_all: dict) -> str:
    store_logo = raw_all.get("store_logo_path")
    shop_logo = raw_all.get("shop_logo_path")
    if store_logo is not None and str(store_logo).strip() != "":
        return str(store_logo).strip()
    if shop_logo is not None and str(shop_logo).strip() != "":
        return str(shop_logo).strip()
    return ""


def get_all() -> dict:
    """ทุก key (ค่าเป็นข้อความตามที่เก็บใน DB) — ใช้เติมฟอร์มหน้าตั้งค่า"""
    data = dict(CONTACT_DEFAULT_SETTINGS)
    raw = repo_settings.get_all()
    data.update(raw)
    data["shop_name"] = _resolve_shop_name(raw.get("shop_name"))
    logo = _resolve_logo_from_raw(raw)
    data["store_logo_path"] = logo
    data["shop_logo_path"] = logo
    return data


def get_shop_info() -> dict:
    """ค่าตั้งค่าที่แปลงชนิดแล้ว (ตัวเลข/bool) พร้อมใช้งานใน service และหน้าจอ"""
    raw_all = repo_settings.get_all()

    def _g(k: str, default=None):
        v = raw_all.get(k)
        if v is not None:
            return v
        return CONTACT_DEFAULT_SETTINGS.get(k, default)

    def _gf(k: str, default: float = 0.0) -> float:
        for text in (raw_all.get(k), DEFAULT_SETTINGS.get(k)):
            try:
                return float(text)
            except (TypeError, ValueError):
                continue
        return float(default)

    def _gi(k: str, default: int = 0) -> int:
        return int(_gf(k, default))

    def _gb(k: str, default: bool = False) -> bool:
        text = raw_all.get(k)
        if text is None:
            return default
        return str(text).strip().lower() in ("1", "true", "yes", "on")

    logo = _resolve_logo_from_raw(raw_all)

    return {
        "shop_name": _resolve_shop_name(raw_all.get("shop_name")),
        "shop_logo_path": logo,
        "store_logo_path": logo,
        "shop_address": _g("shop_address") or CONTACT_DEFAULT_SETTINGS.get("shop_address", ""),
        "shop_hours": _g("shop_hours") or CONTACT_DEFAULT_SETTINGS.get("shop_hours", ""),
        "shop_phone": _g("shop_phone") or CONTACT_DEFAULT_SETTINGS.get("shop_phone", ""),
        "maps_url": _g("maps_url") or CONTACT_DEFAULT_SETTINGS.get("maps_url", ""),
        "promptpay_no": _g("promptpay_no"),
        "promptpay_name": _g("promptpay_name"),
        "shipping_fee": _gf("shipping_fee"),
        "free_shipping_min": _gf("free_shipping_min"),
        "low_stock_threshold": _gi("low_stock_threshold"),
        "unpaid_cancel_hours": _gi("unpaid_cancel_hours"),
        "ai_enabled": _gb("ai_enabled"),
        "flash_sale_scroll_speed": _gi("flash_sale_scroll_speed", 2),
        "coupon_rotate_seconds": _gi("coupon_rotate_seconds", 9),
        "home_coupons_per_view": _gi("home_coupons_per_view", 3),
        "login_showcase_seconds": _gi("login_showcase_seconds", 5),
        "custom_coupon_categories": _g("custom_coupon_categories") or "",
        "custom_option_types": _g("custom_option_types") or "",
    }


def get_contact_info() -> dict:
    """
    ข้อมูลติดต่อเจ้าของร้าน ที่ตั้งหน้าร้าน โลโก้ร้าน และช่องทางโซเชียล (สาธารณะ — ผู้เยี่ยมชม ผู้ซื้อ และแอดมินดูได้)
    """
    raw_all = repo_settings.get_all()
    logo = _resolve_logo_from_raw(raw_all)
    data = {
        "shop_name": _resolve_shop_name(raw_all.get("shop_name")),
        "shop_logo_path": logo,
        "store_logo_path": logo,
    }
    for key, default_val in CONTACT_DEFAULT_SETTINGS.items():
        if key in ("shop_logo_path", "store_logo_path"):
            data[key] = logo
            continue
        raw = raw_all.get(key)
        data[key] = raw if raw is not None else default_val
    return data


def shipping_fee_for(subtotal: float) -> float:
    """ค่าส่งของยอดสินค้านี้"""
    free_min = get_float("free_shipping_min")
    if free_min > 0 and float(subtotal or 0) >= free_min:
        return 0.0
    return round(max(get_float("shipping_fee"), 0.0), 2)


# ==========================================
# แก้ค่า (เจ้าของร้านเท่านั้น)
# ==========================================

def _num_text(value: float) -> str:
    value = round(float(value), 2)
    return str(int(value)) if value == int(value) else str(value)


def _clean_shop_name(value) -> str:
    """คงตัวอักษรทุกตัวที่ Owner พิมพ์ไว้ตรงตามต้นฉบับ (รวมตัวยก จุด เว้นวรรคภายใน ไม่แปลงตัวพิมพ์ใหญ่-เล็ก)"""
    raw = str(value if value is not None else "").strip()
    if not raw:
        raise ValueError("กรุณากรอกชื่อร้าน")
    if len(raw) > 100:
        raise ValueError("ชื่อร้านยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    return raw


def _clean_text(label: str, max_len: int, allow_empty: bool = False):
    def check(value):
        text = str(value or "").strip()
        if not text:
            if allow_empty:
                return ""
            raise ValueError(f"กรุณากรอก{label}")
        if len(text) > max_len:
            raise ValueError(f"{label}ยาวเกินไป (ไม่เกิน {max_len} ตัวอักษร)")
        return text
    return check


def _clean_promptpay_no(value):
    digits = re.sub(r"\D", "", str(value or ""))
    try:
        promptpay.build_payload(digits)
    except ValueError:
        raise ValueError("เลขพร้อมเพย์ไม่ถูกต้อง (เบอร์โทร 10 หลัก เลขบัตร 13 หลัก หรือ e-Wallet 15 หลัก)") from None
    return digits


def _clean_money(label: str):
    def check(value):
        try:
            number = float(str(value).strip())
        except (TypeError, ValueError):
            raise ValueError(f"{label}ต้องเป็นตัวเลข") from None
        if not math.isfinite(number) or number < 0 or number > 1_000_000:
            raise ValueError(f"{label}ต้องไม่ติดลบและไม่เกิน 1,000,000")
        return _num_text(number)
    return check


def _clean_int(label: str, minimum: int, maximum: int):
    def check(value):
        try:
            number = float(str(value).strip())
        except (TypeError, ValueError):
            raise ValueError(f"{label}ต้องเป็นตัวเลข") from None
        if not math.isfinite(number) or number != int(number):
            raise ValueError(f"{label}ต้องเป็นจำนวนเต็ม")
        if not minimum <= number <= maximum:
            raise ValueError(f"{label}ต้องอยู่ระหว่าง {minimum} ถึง {maximum}")
        return str(int(number))
    return check


def _clean_flag(value):
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return "1"
    if text in ("0", "false", "no", "off"):
        return "0"
    raise ValueError("ค่าเปิด/ปิดไม่ถูกต้อง")


def _clean_contact_phone(value):
    text = re.sub(r"[\s-]", "", str(value or "").strip())
    if not text:
        return ""
    if not validators.is_valid_shop_phone(text):
        raise ValueError("เบอร์โทรร้านไม่ถูกต้อง (ต้องเป็นตัวเลข 9-10 หลัก ขึ้นต้นด้วย 0)")
    return text


def _clean_contact_email(value):
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if not validators.is_valid_email(text):
        raise ValueError("รูปแบบอีเมลติดต่อร้านไม่ถูกต้อง")
    return text


def _clean_https_url(label: str):
    def check(value):
        text = str(value or "").strip()
        if not text:
            return ""
        if not validators.is_valid_https_url(text):
            raise ValueError(f"ลิงก์ {label} ต้องขึ้นต้นด้วย https:// และเป็น URL ที่ถูกต้อง")
        if len(text) > 300:
            raise ValueError(f"ลิงก์ {label} ยาวเกินไป (ไม่เกิน 300 ตัวอักษร)")
        return text
    return check


_CLEANERS = {
    "shop_name": _clean_shop_name,
    "shop_logo_path": _clean_text("โลโก้ร้าน", 500, allow_empty=True),
    "store_logo_path": _clean_text("โลโก้ร้าน", 500, allow_empty=True),
    "promptpay_no": _clean_promptpay_no,
    "promptpay_name": _clean_text("ชื่อบัญชีพร้อมเพย์", 100),
    "shipping_fee": _clean_money("ค่าส่ง"),
    "free_shipping_min": _clean_money("ยอดส่งฟรีขั้นต่ำ"),
    "low_stock_threshold": _clean_int("เกณฑ์สต็อกใกล้หมด", 0, 10_000),
    "unpaid_cancel_hours": _clean_int("ชั่วโมงยกเลิกอัตโนมัติ", 1, 720),
    "ai_enabled": _clean_flag,
    "flash_sale_scroll_speed": _clean_int("ความเร็วเลื่อน Flash Sale", 1, 20),
    "coupon_rotate_seconds": _clean_int("เวลาสลับชุดคูปองหน้าหลัก (วินาที)", 3, 120),
    "home_coupons_per_view": _clean_int("จำนวนคูปองที่แสดงหน้าหลัก", 1, 6),
    "login_showcase_seconds": _clean_int("เวลาเปลี่ยนภาพสินค้าหน้าเข้าสู่ระบบ (วินาที)", 2, 60),
    "custom_coupon_categories": _clean_text("หมวดหมู่คูปองเพิ่มเติม", 300, allow_empty=True),
    "custom_option_types": _clean_text("ประเภทตัวเลือกสินค้าเพิ่มเติม", 300, allow_empty=True),
    "shop_phone": _clean_contact_phone,
    "shop_email": _clean_contact_email,
    "facebook_name": _clean_text("ชื่อ Facebook", 100, allow_empty=True),
    "facebook_url": _clean_https_url("Facebook"),
    "line_name": _clean_text("ชื่อ LINE", 100, allow_empty=True),
    "instagram_name": _clean_text("ชื่อ Instagram", 100, allow_empty=True),
    "instagram_url": _clean_https_url("Instagram"),
    "shop_address": _clean_text("ที่อยู่ร้าน", 300, allow_empty=True),
    "shop_hours": _clean_text("เวลาเปิด-ปิดร้าน", 300, allow_empty=True),
    "maps_url": _clean_https_url("Google Maps"),
    "line_oa_url": _clean_https_url("LINE Official"),
    "tiktok_name": _clean_text("ชื่อ TikTok", 100, allow_empty=True),
    "tiktok_url": _clean_https_url("TikTok"),
    "auto_export_dir": _clean_text("โฟลเดอร์ส่งออกอัตโนมัติ", 500, allow_empty=True),
    "last_auto_export": _clean_text("เดือนส่งออกล่าสุด", 20, allow_empty=True),
    "last_low_stock_email": _clean_text("วันที่ส่งสรุปสต็อกต่ำล่าสุด", 20, allow_empty=True),
}


def update_many(values: dict) -> dict:
    """
    แก้หลายค่าพร้อมกัน (หน้าตั้งค่าร้าน) — ตรวจครบทุกค่าก่อน ถ้ามีค่าผิดจะไม่บันทึกอะไรเลย
    คืน get_shop_info() ล่าสุด | PermissionError ถ้าไม่ใช่เจ้าของร้าน | ValueError ถ้าค่าผิด/key ไม่รู้จัก
    """
    permissions.require(permissions.SETTINGS_MANAGE)
    if not values:
        raise ValueError("ไม่มีค่าที่จะบันทึก")
    cleaned = {}
    for key, value in values.items():
        if key not in ALL_KNOWN_KEYS:
            raise ValueError(f"ไม่รู้จักการตั้งค่า: {key}")
        cleaned[key] = _CLEANERS[key](value)

    if "store_logo_path" in cleaned and "shop_logo_path" not in cleaned:
        cleaned["shop_logo_path"] = cleaned["store_logo_path"]
    elif "shop_logo_path" in cleaned and "store_logo_path" not in cleaned:
        cleaned["store_logo_path"] = cleaned["shop_logo_path"]

    repo_settings.set_many(cleaned)
    audit_service.log("settings.update", "settings", None, cleaned)
    return get_shop_info()


def update_contact_info(values: dict) -> dict:
    """แก้ไขข้อมูลโปรไฟล์ร้านและช่องทางติดต่อของเจ้าของร้าน"""
    permissions.require(permissions.SETTINGS_MANAGE)
    if not values:
        raise ValueError("ไม่มีข้อมูลที่จะบันทึก")
    cleaned = {}
    for key, value in values.items():
        if key not in ALL_KNOWN_KEYS:
            raise ValueError(f"ไม่รู้จักข้อมูลติดต่อ: {key}")
        cleaned[key] = _CLEANERS[key](value)
    if "store_logo_path" in cleaned and "shop_logo_path" not in cleaned:
        cleaned["shop_logo_path"] = cleaned["store_logo_path"]
    elif "shop_logo_path" in cleaned and "store_logo_path" not in cleaned:
        cleaned["store_logo_path"] = cleaned["shop_logo_path"]
    repo_settings.set_many(cleaned)
    audit_service.log("settings.update_contact", "settings", None, cleaned)
    return get_contact_info()


def update(key: str, value) -> dict:
    """แก้ค่าเดียว (เจ้าของร้านเท่านั้น) คืน get_shop_info() ล่าสุด"""
    return update_many({key: value})
