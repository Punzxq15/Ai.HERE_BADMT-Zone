"""
core/permissions.py
ตารางสิทธิ์ของระบบ (ตามตาราง "สิทธิ์" ใน PROGRESS.md / D-01)
ใช้ได้ทั้งฝั่ง UI (ซ่อนปุ่ม) และ services (บังคับสิทธิ์จริงด้วย require)

    from core import permissions
    permissions.can("buyer", "cart.use")      # -> True
    permissions.require("product.delete")     # ใช้ role จาก Session; ไม่มีสิทธิ์ -> PermissionError
"""
from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_GUEST, ROLE_OWNER
from core.session import Session

# ---------- ชื่อ action ----------
# ผู้ซื้อ
SHOP_BROWSE = "shop.browse"            # ดู/ค้นหา/เปรียบเทียบสินค้า
CART_USE = "cart.use"                  # ตะกร้า + สั่งซื้อ
ORDER_OWN = "order.own"                # ออเดอร์ของตัวเอง (ดู/ยกเลิก pending/แนบสลิป/ยืนยันรับของ)
REVIEW_WRITE = "review.write"
WISHLIST_USE = "wishlist.use"
ADDRESS_MANAGE = "address.manage"
CHAT_CUSTOMER = "chat.customer"

# แอดมิน + เจ้าของ
PRODUCT_VIEW = "product.view"
PRODUCT_CREATE = "product.create"
PRODUCT_EDIT = "product.edit"          # แก้ข้อมูลพื้นฐาน (รวมตัวเลือกสินค้า)
STOCK_UPDATE = "stock.update"
CHAT_REPLY = "chat.reply"
SLIP_VERIFY = "slip.verify"
ORDER_VIEW = "order.view"
ORDER_CANCEL = "order.cancel"          # ยกเลิกออเดอร์ของลูกค้า (ก่อนจัดส่ง)
SHIPMENT_UPDATE = "shipment.update"
DASHBOARD_VIEW = "dashboard.view"
BANNER_MANAGE = "banner.manage"        # จัดการแบนเนอร์หน้าแรก (Owner หรือ Admin ตามข้อ 2)

# เจ้าของเท่านั้น
PRODUCT_DELETE = "product.delete"      # ลบ(ปิด)สินค้า + กู้คืนสินค้าที่ถูกลบ
CATEGORY_MANAGE = "category.manage"
BRAND_MANAGE = "brand.manage"
COUPON_MANAGE = "coupon.manage"        # รวม Flash Sale และกฎซื้อครบรับคูปอง
USER_MANAGE = "user.manage"            # สร้างแอดมิน/ระงับบัญชี
SETTINGS_MANAGE = "settings.manage"    # ตั้งค่าร้าน/PromptPay/ข้อมูลติดต่อ
BACKUP_MANAGE = "backup.manage"        # สำรองฐานข้อมูล + ส่งออกรายงาน .xlsx
DASHBOARD_REVENUE = "dashboard.revenue"
AUDIT_VIEW = "audit.view"              # ดูบันทึกกิจกรรม (Audit Log)

_STAFF = frozenset({
    PRODUCT_VIEW, PRODUCT_CREATE, PRODUCT_EDIT, STOCK_UPDATE, CHAT_REPLY,
    SLIP_VERIFY, ORDER_VIEW, ORDER_CANCEL, SHIPMENT_UPDATE, DASHBOARD_VIEW,
    BANNER_MANAGE,
})

_OWNER_ONLY = frozenset({
    PRODUCT_DELETE, CATEGORY_MANAGE, BRAND_MANAGE, COUPON_MANAGE, USER_MANAGE,
    SETTINGS_MANAGE, BACKUP_MANAGE, DASHBOARD_REVENUE, BANNER_MANAGE, AUDIT_VIEW,
})

_BUYER = frozenset({
    SHOP_BROWSE, CART_USE, ORDER_OWN, REVIEW_WRITE, WISHLIST_USE,
    ADDRESS_MANAGE, CHAT_CUSTOMER,
})

_GUEST = frozenset({
    SHOP_BROWSE,
})

# role -> ชุด action ที่ทำได้ (owner ไม่ใช่ผู้ซื้อ จึงไม่มีสิทธิ์ฝั่งผู้ซื้อ ตามตาราง)
ROLE_PERMISSIONS = {
    ROLE_BUYER: _BUYER,
    ROLE_ADMIN: _STAFF,
    ROLE_OWNER: _STAFF | _OWNER_ONLY,
    ROLE_GUEST: _GUEST,
}

ALL_ACTIONS = frozenset().union(*ROLE_PERMISSIONS.values())


def can(role: str | None, action: str) -> bool:
    """role นี้ทำ action นี้ได้หรือไม่ (role ไม่รู้จัก/None = False)"""
    return action in ROLE_PERMISSIONS.get(role, frozenset())


def require(action: str, role: str | None = None) -> None:
    """
    บังคับสิทธิ์: ไม่มีสิทธิ์ -> PermissionError (ข้อความไทย)
    ไม่ส่ง role = ใช้ role ของผู้ใช้ที่ล็อกอินอยู่ใน Session (หรือ ROLE_GUEST ถ้าเปิดโหมดผู้เยี่ยมชม)
    """
    if action not in ALL_ACTIONS:
        # กันพิมพ์ชื่อ action ผิด ไม่ให้ผ่านแบบเงียบ ๆ
        raise ValueError(f"ไม่รู้จักสิทธิ์: {action}")
    if role is None:
        if Session.is_authenticated():
            role = Session.get_role()
        elif Session.is_guest():
            role = ROLE_GUEST
        else:
            raise PermissionError("กรุณาเข้าสู่ระบบก่อน")
    if not can(role, action):
        if Session.is_guest():
            raise PermissionError("กรุณาเข้าสู่ระบบก่อนทำรายการนี้")
        raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")


# ---------- ตัวช่วยตรวจสิทธิ์สำหรับ services (เพิ่มในส่วน C — ไม่เปลี่ยนฟังก์ชันเดิม) ----------

def require_login() -> int:
    """ต้องล็อกอินอยู่ — คืน id ของผู้ใช้ปัจจุบัน (ไม่ล็อกอิน -> PermissionError)"""
    user_id = Session.get_user_id()
    if user_id is None:
        raise PermissionError("กรุณาเข้าสู่ระบบก่อน")
    return user_id


def require_user(user_id: int) -> None:
    """ต้องล็อกอิน และ user_id ที่ส่งมาต้องเป็นของผู้ใช้ปัจจุบันเท่านั้น (ใช้กับเรื่องส่วนตัว เช่น โปรไฟล์)"""
    if require_login() != user_id:
        raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")


def require_self(action: str, user_id: int) -> None:
    """มีสิทธิ์ action นี้ และ user_id เป็นของผู้ใช้ปัจจุบัน (กันผู้ซื้อแตะตะกร้า/ออเดอร์ของคนอื่น)"""
    require(action)
    require_user(user_id)


def require_any(*actions: str) -> None:
    """ผ่านถ้ามีสิทธิ์อย่างน้อยหนึ่งใน actions (เช่น หน้าที่ทั้งผู้ซื้อและแอดมินดูได้)"""
    for action in actions:
        if action not in ALL_ACTIONS:
            raise ValueError(f"ไม่รู้จักสิทธิ์: {action}")
    if Session.is_authenticated():
        role = Session.get_role()
    elif Session.is_guest():
        role = ROLE_GUEST
    else:
        raise PermissionError("กรุณาเข้าสู่ระบบก่อน")
    if not any(can(role, a) for a in actions):
        if Session.is_guest():
            raise PermissionError("กรุณาเข้าสู่ระบบก่อนทำรายการนี้")
        raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")
