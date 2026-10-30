"""
server/deps.py
ตัวช่วยตรวจสอบเซสชัน สิทธิ์การเข้าถึงหน้า (ROUTE_TABLE / ROUTE_ROLES / GUEST_STOREFRONT_ROUTES)
และดึงข้อมูลผู้ใช้ปัจจุบันสำหรับชั้น API
"""
from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_GUEST, ROLE_OWNER
from core.session import Session

# ทะเบียนหน้าทั้ง 30 หน้า (ตรงกับ ui/router.py ทุกประการ)
ROUTE_TABLE = {
    # --- ผู้ซื้อ (18 หน้า) ---
    "login": ("web/js/pages/buyer/login.js", "LoginPage"),
    "register": ("web/js/pages/buyer/register.js", "RegisterPage"),
    "home": ("web/js/pages/buyer/home.js", "HomePage"),
    "category": ("web/js/pages/buyer/category.js", "CategoryPage"),
    "product_detail": ("web/js/pages/buyer/product_detail.js", "ProductDetailPage"),
    "compare": ("web/js/pages/buyer/compare.js", "ComparePage"),
    "racket_finder": ("web/js/pages/buyer/racket_finder.js", "RacketFinderPage"),
    "wishlist": ("web/js/pages/buyer/wishlist.js", "WishlistPage"),
    "cart": ("web/js/pages/buyer/cart.js", "CartPage"),
    "checkout": ("web/js/pages/buyer/checkout.js", "CheckoutPage"),
    "addresses": ("web/js/pages/buyer/addresses.js", "AddressesPage"),
    "payment": ("web/js/pages/buyer/payment.js", "PaymentPage"),
    "orders": ("web/js/pages/buyer/orders.js", "OrdersPage"),
    "order_detail": ("web/js/pages/buyer/order_detail.js", "OrderDetailPage"),
    "write_review": ("web/js/pages/buyer/write_review.js", "WriteReviewPage"),
    "profile": ("web/js/pages/buyer/profile.js", "ProfilePage"),
    "notifications": ("web/js/pages/buyer/notifications.js", "NotificationsPage"),
    "chat": ("web/js/pages/buyer/chat.js", "ChatPage"),
    # --- แอดมิน/เจ้าของ (12 หน้า) ---
    "admin_dashboard": ("web/js/pages/admin/dashboard.js", "AdminDashboardPage"),
    "admin_products": ("web/js/pages/admin/products.js", "AdminProductsPage"),
    "admin_product_form": ("web/js/pages/admin/product_form.js", "AdminProductFormPage"),
    "admin_categories": ("web/js/pages/admin/categories.js", "AdminCategoriesPage"),
    "admin_orders": ("web/js/pages/admin/orders.js", "AdminOrdersPage"),
    "admin_order_detail": ("web/js/pages/admin/order_detail.js", "AdminOrderDetailPage"),
    "admin_payments": ("web/js/pages/admin/payments.js", "AdminPaymentsPage"),
    "admin_coupons": ("web/js/pages/admin/coupons.js", "AdminCouponsPage"),
    "admin_coupon_form": ("web/js/pages/admin/coupon_form.js", "AdminCouponFormPage"),
    "admin_chat": ("web/js/pages/admin/chat.js", "AdminChatPage"),
    "admin_users": ("web/js/pages/admin/users.js", "AdminUsersPage"),
    "admin_settings": ("web/js/pages/admin/settings.js", "AdminSettingsPage"),
}

PUBLIC_ROUTES = frozenset({"login", "register"})

GUEST_STOREFRONT_ROUTES = frozenset({
    "home", "category", "product_detail", "compare", "racket_finder",
})

_STAFF = (ROLE_ADMIN, ROLE_OWNER)
_BUYER_ONLY = (ROLE_BUYER,)

ROUTE_ROLES = {
    # ผู้ซื้อ (และผู้เยี่ยมชมเฉพาะหน้า GUEST_STOREFRONT_ROUTES)
    **{r: _BUYER_ONLY for r in (
        "home", "category", "product_detail", "compare", "racket_finder", "wishlist",
        "cart", "checkout", "addresses", "payment", "orders", "order_detail",
        "write_review", "chat",
    )},
    # แอดมิน + เจ้าของ
    **{r: _STAFF for r in (
        "admin_dashboard", "admin_products", "admin_product_form", "admin_orders",
        "admin_order_detail", "admin_payments", "admin_chat",
    )},
    # เจ้าของเท่านั้น
    **{r: (ROLE_OWNER,) for r in (
        "admin_users", "admin_settings", "admin_categories", "admin_coupons", "admin_coupon_form",
    )},
}


def get_current_user() -> dict | None:
    """คืน dict ข้อมูลผู้ใช้ที่ล็อกอินอยู่ในคำขอปัจจุบัน หรือ None"""
    return Session.current_user


def require_user_id() -> int:
    """บังคับต้องล็อกอิน และคืน user_id"""
    uid = Session.get_user_id()
    if uid is None:
        raise PermissionError("กรุณาเข้าสู่ระบบก่อน")
    return int(uid)


def require_roles(*allowed_roles: str) -> dict:
    """บังคับต้องล็อกอินและมี role อยู่ใน allowed_roles"""
    if not Session.is_authenticated():
        raise PermissionError("กรุณาเข้าสู่ระบบก่อน")
    role = Session.get_role()
    if role not in allowed_roles:
        raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")
    return Session.current_user


def check_route_access(route_name: str) -> dict:
    """
    ตรวจสอบสิทธิ์การเข้าถึง route ตามสัญญาเดียวกับ ui/router.py
    คืน {"allowed": bool, "redirect": str | None, "reason": str | None}
    """
    if route_name not in ROUTE_TABLE:
        raise ValueError(f"ไม่พบหน้า '{route_name}' ในระบบ Router")

    if route_name in PUBLIC_ROUTES:
        return {"allowed": True, "redirect": None, "reason": None}

    if Session.is_authenticated():
        user = Session.current_user or {}
        if user.get("must_change_password") and route_name != "profile":
            return {
                "allowed": False,
                "redirect": "profile",
                "reason": "กรุณาเปลี่ยนรหัสผ่านชั่วคราวก่อนใช้งานระบบ",
            }
        allowed = ROUTE_ROLES.get(route_name)
        role = Session.get_role()
        if allowed and role not in allowed:
            fallback = "admin_dashboard" if role in (ROLE_ADMIN, ROLE_OWNER) else "home"
            return {
                "allowed": False,
                "redirect": fallback,
                "reason": "คุณไม่มีสิทธิ์เข้าถึงหน้านี้",
            }
        return {"allowed": True, "redirect": None, "reason": None}

    if route_name in GUEST_STOREFRONT_ROUTES and Session.is_guest():
        return {"allowed": True, "redirect": None, "reason": None}

    return {
        "allowed": False,
        "redirect": "login",
        "reason": "กรุณาเข้าสู่ระบบเพื่อใช้งานฟังก์ชันนี้",
    }


def require_route_access(route_name: str) -> None:
    """บังคับสิทธิ์ระดับ route: ถ้าเข้าไม่ได้ให้โยน PermissionError"""
    res = check_route_access(route_name)
    if not res["allowed"]:
        raise PermissionError(res["reason"] or "คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
