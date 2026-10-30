"""
services/account_service.py
งานบัญชีส่วนตัวของผู้ใช้:
    ที่อยู่จัดส่งของผู้ซื้อ (action address.manage)  — list/get/add/update/delete/set_default_address
    รายการโปรด wishlist ของผู้ซื้อ (action wishlist.use) — toggle_wishlist / list_wishlist / wishlist_ids
    โปรไฟล์ของตัวเอง (ทุก role)                      — get_profile / set_avatar (แก้ชื่อ/เบอร์ใช้ auth_service.update_profile)

repo_addresses ไม่ตรวจเจ้าของ จึงตรวจที่นี่ทุกครั้ง: ที่อยู่ของคนอื่นจะตอบว่า "ไม่พบที่อยู่" (ไม่บอกว่ามีอยู่จริง)
"""
import re
import config
from core import permissions
from core.constants import ROLE_LABELS
from database import repo_addresses, repo_orders, repo_products, repo_reviews, repo_users, repo_wishlist
from database.db import transaction
from services import auth_service, product_service
from utils import image_utils, validators

MAX_ADDRESSES = 10


# ==========================================
# ที่อยู่จัดส่ง (พร้อมข้อความแจ้งข้อผิดพลาดระบุสาเหตุชัดเจนรายช่อง)
# ==========================================

def validate_address_fields(recipient, phone, address_line, district, province, postcode) -> dict[str, str]:
    """
    ตรวจสอบข้อมูลที่อยู่จัดส่งแบบละเอียดรายช่อง คืน dict {field_name: error_message}
    ถ้าถูกต้องทุกช่องจะคืน {}
    """
    errors: dict[str, str] = {}

    rec_text = " ".join(str(recipient or "").split())
    if not rec_text:
        errors["recipient"] = "กรุณากรอกชื่อผู้รับสินค้า"
    elif len(rec_text) < 2:
        errors["recipient"] = "ชื่อผู้รับสั้นเกินไป (ต้องมีอย่างน้อย 2 ตัวอักษร)"
    elif len(rec_text) > 100:
        errors["recipient"] = f"ชื่อผู้รับยาวเกินไป ({len(rec_text)}/100 ตัวอักษร — ต้องไม่เกิน 100 ตัวอักษร)"

    raw_phone = str(phone or "").strip()
    clean_phone = raw_phone.replace("-", "").replace(" ", "")
    if not clean_phone:
        errors["phone"] = "กรุณากรอกเบอร์โทรศัพท์ผู้รับ (ตัวเลข 10 หลัก ขึ้นต้นด้วย 0)"
    elif not clean_phone.isdigit():
        errors["phone"] = "เบอร์โทรศัพท์ต้องเป็นตัวเลขเท่านั้น (ห้ามมีตัวอักษรหรือสัญลักษณ์พิเศษ)"
    elif not clean_phone.startswith("0"):
        errors["phone"] = "เบอร์โทรศัพท์ต้องขึ้นต้นด้วยเลข 0 (เช่น 0812345678)"
    elif len(clean_phone) < 10:
        errors["phone"] = f"เบอร์โทรศัพท์ยังไม่ครบ 10 หลัก (กรอกแล้ว {len(clean_phone)}/10 หลัก)"
    elif len(clean_phone) > 10:
        errors["phone"] = f"เบอร์โทรศัพท์เกิน 10 หลัก (กรอกแล้ว {len(clean_phone)}/10 หลัก — ต้องมี 10 หลักพอดี)"

    addr_text = " ".join(str(address_line or "").split())
    if not addr_text:
        errors["address_line"] = "กรุณากรอกที่อยู่ (บ้านเลขที่ หมู่บ้าน ซอย ถนน)"
    elif len(addr_text) < 4:
        errors["address_line"] = "ที่อยู่สั้นเกินไป กรุณาระบุบ้านเลขที่และซอย/ถนนให้ชัดเจน"
    elif len(addr_text) > 200:
        errors["address_line"] = f"ที่อยู่ยาวเกินไป ({len(addr_text)}/200 ตัวอักษร — ต้องไม่เกิน 200 ตัวอักษร)"

    dist_text = " ".join(str(district or "").split())
    if not dist_text:
        errors["district"] = "กรุณากรอกแขวง/เขต หรือ ตำบล/อำเภอ"
    elif len(dist_text) < 2:
        errors["district"] = "ชื่อแขวง/เขต หรือ ตำบล/อำเภอสั้นเกินไป"
    elif len(dist_text) > 80:
        errors["district"] = f"แขวง/เขต หรือ ตำบล/อำเภอยาวเกินไป ({len(dist_text)}/80 ตัวอักษร)"

    prov_text = " ".join(str(province or "").split())
    if not prov_text:
        errors["province"] = "กรุณากรอกจังหวัด"
    elif len(prov_text) < 2:
        errors["province"] = "ชื่อจังหวัดสั้นเกินไป"
    elif len(prov_text) > 80:
        errors["province"] = f"ชื่อจังหวัดยาวเกินไป ({len(prov_text)}/80 ตัวอักษร)"

    raw_post = str(postcode or "").strip()
    if not raw_post:
        errors["postcode"] = "กรุณากรอกรหัสไปรษณีย์ 5 หลัก"
    elif not raw_post.isdigit():
        errors["postcode"] = "รหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลักเท่านั้น (ห้ามมีตัวอักษรหรือขีด)"
    elif len(raw_post) < 5:
        errors["postcode"] = f"รหัสไปรษณีย์ยังไม่ครบ 5 หลัก (กรอกแล้ว {len(raw_post)}/5 หลัก)"
    elif len(raw_post) > 5:
        errors["postcode"] = f"รหัสไปรษณีย์เกิน 5 หลัก (กรอกแล้ว {len(raw_post)}/5 หลัก — ต้องเป็นตัวเลข 5 หลักพอดี)"

    return errors


def _clean_text(value, label: str, max_len: int) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise ValueError(f"กรุณากรอก{label}")
    if len(text) > max_len:
        raise ValueError(f"{label}ยาวเกินไป (ไม่เกิน {max_len} ตัวอักษร)")
    return text


def _clean_address(recipient, phone, address_line, district, province, postcode) -> dict:
    raw_phone = str(phone or "").replace("-", "").replace(" ", "")
    if not validators.is_valid_phone(raw_phone):
        if not raw_phone:
            raise ValueError("กรุณากรอกเบอร์โทรศัพท์ (ตัวเลข 10 หลักและขึ้นต้นด้วย 0)")
        if not raw_phone.isdigit():
            raise ValueError("เบอร์โทรศัพท์ต้องเป็นตัวเลข 10 หลักและขึ้นต้นด้วย 0 (ห้ามมีตัวอักษร)")
        if not raw_phone.startswith("0"):
            raise ValueError("เบอร์โทรศัพท์ต้องเป็นตัวเลข 10 หลักและขึ้นต้นด้วย 0")
        raise ValueError(f"เบอร์โทรศัพท์ต้องเป็นตัวเลข 10 หลักและขึ้นต้นด้วย 0 (ปัจจุบันกรอก {len(raw_phone)} หลัก)")

    raw_post = str(postcode or "").strip()
    if not validators.is_valid_postcode(raw_post):
        if not raw_post:
            raise ValueError("กรุณากรอกรหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลัก")
        if not raw_post.isdigit():
            raise ValueError("รหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลัก (ห้ามมีตัวอักษร)")
        raise ValueError(f"รหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลัก (ปัจจุบันกรอก {len(raw_post)} หลัก)")

    return {
        "recipient": _clean_text(recipient, "ชื่อผู้รับ", 100),
        "phone": raw_phone,
        "address_line": _clean_text(address_line, "ที่อยู่", 200),
        "district": _clean_text(district, "แขวง/เขต หรือ ตำบล/อำเภอ", 80),
        "province": _clean_text(province, "จังหวัด", 80),
        "postcode": raw_post,
    }


def _address_dict(row) -> dict:
    d = dict(row)
    d["is_default"] = bool(d["is_default"])
    d["full_address"] = " ".join(
        str(d[k]).strip() for k in ("address_line", "district", "province", "postcode") if d.get(k))
    return d


def _own_address(user_id: int, address_id: int, conn=None):
    """ที่อยู่ที่เป็นของ user นี้เท่านั้น (ของคนอื่น/ไม่มี -> ValueError เหมือนกัน)"""
    row = repo_addresses.get(address_id, conn=conn)
    if row is None or row["user_id"] != user_id:
        raise ValueError("ไม่พบที่อยู่จัดส่ง")
    return row


def list_addresses(user_id: int) -> list[dict]:
    """ที่อยู่ทั้งหมดของผู้ซื้อ (ที่อยู่หลักขึ้นก่อน) — dict: id, recipient, phone, address_line, district, province,
    postcode, is_default (bool), full_address (ที่อยู่ 1 บรรทัด)"""
    permissions.require_self(permissions.ADDRESS_MANAGE, user_id)
    return [_address_dict(r) for r in repo_addresses.list(user_id)]


def get_address(user_id: int, address_id: int) -> dict:
    """ที่อยู่ 1 รายการของตัวเอง (ไม่พบ/ของคนอื่น -> ValueError)"""
    permissions.require_self(permissions.ADDRESS_MANAGE, user_id)
    return _address_dict(_own_address(user_id, address_id))


def add_address(user_id: int, recipient: str, phone: str, address_line: str, district: str,
                province: str, postcode: str, is_default: bool = False) -> dict:
    """
    เพิ่มที่อยู่ (สูงสุด MAX_ADDRESSES) — ที่อยู่แรกของผู้ใช้เป็นที่อยู่หลักเสมอ; is_default=True ล้างหลักเดิมให้
    เบอร์โทรเว้นวรรค/ขีดได้ (ระบบตัดให้) คืน dict ที่อยู่ใหม่ · ValueError: ข้อมูลไม่ครบ/รูปแบบผิด/ที่อยู่เต็ม
    """
    permissions.require_self(permissions.ADDRESS_MANAGE, user_id)
    fields = _clean_address(recipient, phone, address_line, district, province, postcode)
    with transaction() as conn:
        count = repo_addresses.count(user_id, conn=conn)
        if count >= MAX_ADDRESSES:
            raise ValueError(f"เพิ่มที่อยู่ได้สูงสุด {MAX_ADDRESSES} แห่ง กรุณาลบที่อยู่ที่ไม่ใช้ก่อน")
        address_id = repo_addresses.create(user_id, **fields, is_default=bool(is_default) or count == 0, conn=conn)
        return _address_dict(repo_addresses.get(address_id, conn=conn))


def update_address(user_id: int, address_id: int, recipient: str, phone: str, address_line: str,
                   district: str, province: str, postcode: str) -> dict:
    """แก้ที่อยู่ของตัวเอง (ไม่เปลี่ยนที่อยู่หลัก — ใช้ set_default_address) คืน dict ล่าสุด"""
    permissions.require_self(permissions.ADDRESS_MANAGE, user_id)
    fields = _clean_address(recipient, phone, address_line, district, province, postcode)
    with transaction() as conn:
        _own_address(user_id, address_id, conn)
        repo_addresses.update(address_id, **fields, conn=conn)
        return _address_dict(repo_addresses.get(address_id, conn=conn))


def delete_address(user_id: int, address_id: int) -> bool:
    """
    ลบที่อยู่ของตัวเอง (ออเดอร์เก่าเก็บสำเนาที่อยู่ไว้แล้ว จึงไม่กระทบ) — ถ้าลบที่อยู่หลัก
    จะตั้งที่อยู่ที่เหลืออันแรกเป็นหลักให้อัตโนมัติ
    """
    permissions.require_self(permissions.ADDRESS_MANAGE, user_id)
    with transaction() as conn:
        row = _own_address(user_id, address_id, conn)
        repo_addresses.delete(address_id, conn=conn)
        if row["is_default"]:
            remaining = repo_addresses.list(user_id, conn=conn)
            if remaining:
                repo_addresses.set_default(user_id, remaining[0]["id"], conn=conn)
        return True


def set_default_address(user_id: int, address_id: int) -> dict:
    """ตั้งเป็นที่อยู่หลัก (ล้างหลักเดิมให้) คืน dict ที่อยู่นั้น"""
    permissions.require_self(permissions.ADDRESS_MANAGE, user_id)
    with transaction() as conn:
        _own_address(user_id, address_id, conn)
        repo_addresses.set_default(user_id, address_id, conn=conn)
        return _address_dict(repo_addresses.get(address_id, conn=conn))


# ==========================================
# รายการโปรด (wishlist)
# ==========================================

def _is_sellable(product) -> bool:
    """สินค้า + หมวด + แบรนด์ต้องเปิดขายอยู่ (ตรงกับที่ผู้ซื้อมองเห็นในหน้าร้าน)"""
    if product is None or not product["is_active"]:
        return False
    category = repo_products.get_category(product["category_id"])
    brand = repo_products.get_brand(product["brand_id"])
    return bool(category and category["is_active"] and brand and brand["is_active"])


def toggle_wishlist(user_id: int, product_id: int) -> dict:
    """
    กดหัวใจ: ยังไม่มี = เพิ่ม, มีแล้ว = เอาออก คืน {"in_wishlist": bool} (สถานะหลังกด)
    เพิ่มได้เฉพาะสินค้าที่เปิดขาย (เอาออกได้เสมอ) · ValueError: ไม่พบสินค้า/ปิดขาย
    """
    permissions.require_self(permissions.WISHLIST_USE, user_id)
    if repo_wishlist.is_in(user_id, product_id):
        repo_wishlist.remove(user_id, product_id)
        return {"in_wishlist": False}
    if not _is_sellable(repo_products.get_product(product_id)):
        raise ValueError("ไม่พบสินค้า หรือสินค้าถูกปิดการขาย")
    repo_wishlist.add(user_id, product_id)
    return {"in_wishlist": True}


def list_wishlist(user_id: int) -> list[dict]:
    """
    สินค้าในรายการโปรด (เพิ่มล่าสุดก่อน เฉพาะที่ยังเปิดขาย) — dict แบบเดียวกับการ์ดสินค้าใน product_service.search_products:
    แถวสินค้า + effective_price, is_on_sale, sale_seconds_left, in_stock, avg_rating, review_count, in_wishlist (True)
    """
    permissions.require_self(permissions.WISHLIST_USE, user_id)
    active_categories = {c["id"] for c in repo_products.list_categories(active_only=True)}
    active_brands = {b["id"] for b in repo_products.list_brands(active_only=True)}
    rows = [r for r in repo_wishlist.list(user_id)
            if r["category_id"] in active_categories and r["brand_id"] in active_brands]
    ratings = repo_reviews.get_summaries([r["id"] for r in rows])
    items = []
    for row in rows:
        d = dict(row)
        d["effective_price"] = product_service.get_effective_price(row)
        d["is_on_sale"] = product_service.is_on_sale(row)
        d["sale_seconds_left"] = product_service.sale_seconds_left(row)
        d["in_stock"] = (d.get("stock") or 0) > 0
        d["avg_rating"], d["review_count"] = ratings.get(d["id"], (0.0, 0))
        d["in_wishlist"] = True
        items.append(d)
    return items


def wishlist_ids(user_id: int) -> set:
    """set ของ product_id ที่กดหัวใจไว้ (เช็คสถานะหัวใจทีละการ์ดได้เร็ว)"""
    permissions.require_self(permissions.WISHLIST_USE, user_id)
    return repo_wishlist.ids(user_id)


# ==========================================
# โปรไฟล์ของตัวเอง
# ==========================================

def get_profile(user_id: int) -> dict:
    """
    โปรไฟล์ของตัวเอง (ทุก role; ดูของคนอื่นไม่ได้ -> PermissionError) คืน dict:
    id, username, email, full_name, phone, role, role_label, avatar_path, created_at (ไม่มี password_hash)
    + address_count, default_address (dict หรือ None), wishlist_count, order_count (สามอย่างหลังเป็น 0/None สำหรับ admin/owner)
    """
    permissions.require_user(user_id)
    user = repo_users.get_by_id(user_id)
    if user is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    profile = {k: user[k] for k in ("id", "username", "email", "full_name", "phone", "role",
                                    "avatar_path", "created_at")}
    profile["role_label"] = ROLE_LABELS.get(profile["role"], profile["role"])
    is_buyer = permissions.can(profile["role"], permissions.ADDRESS_MANAGE)
    default = repo_addresses.get_default(user_id) if is_buyer else None
    profile["address_count"] = repo_addresses.count(user_id) if is_buyer else 0
    profile["default_address"] = _address_dict(default) if default else None
    profile["wishlist_count"] = len(repo_wishlist.ids(user_id)) if is_buyer else 0
    profile["order_count"] = repo_orders.count_orders(user_id=user_id) if is_buyer else 0
    return profile


def set_avatar(user_id: int, src_path, current_password: str = None, require_password: bool = False) -> dict:
    """
    เปลี่ยนรูปโปรไฟล์ของตัวเอง: ย่อ/บันทึกลง assets/images/users/ แล้วอัปเดตโปรไฟล์ และลบรูปเก่าของระบบทิ้ง
    คืน get_profile() · ValueError: ไฟล์ไม่พบ/ชนิดผิด/ใหญ่เกิน 5 MB/ไม่ใช่รูป/รหัสผ่านไม่ถูกต้อง
    """
    permissions.require_user(user_id)
    user = repo_users.get_by_id(user_id)
    if user is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    if require_password or current_password is not None:
        auth_service.verify_user_current_password(user_id, current_password)
    old_path = user["avatar_path"]
    new_path = image_utils.save_upload(src_path, config.USER_IMAGES_DIR, f"user_{user_id}")
    try:
        auth_service.update_profile(user_id, user["full_name"], user["phone"] or "", avatar_path=new_path)
    except BaseException:
        image_utils.delete_upload(new_path)
        raise
    if old_path and old_path != new_path and str(old_path).replace("\\", "/").startswith("assets/images/users/"):
        image_utils.delete_upload(old_path)  # ลบเฉพาะรูปที่ระบบอัปโหลดไว้เอง
    return get_profile(user_id)


# Convenience delegates to auth_service for profile & email OTP updates (T11)
update_profile = auth_service.update_profile
validate_profile_fields = auth_service.validate_profile_fields
update_username = auth_service.update_username
request_email_change_otp = auth_service.request_email_change_otp
confirm_email_change_with_otp = auth_service.confirm_email_change_with_otp
