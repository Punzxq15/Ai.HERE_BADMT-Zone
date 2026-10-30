"""
ui/router.py
ตัวกลางจัดการการสลับหน้าจอ (Router) พร้อมระบบตรวจสอบสิทธิ์ (Role) และโหมดผู้เยี่ยมชม (Guest Storefront)

ข้อตกลงสำหรับทุกหน้า (Page):
- constructor รับ (parent, controller) โดย controller คือ Router ตัวนี้
- สลับหน้าด้วย  self.controller.show("ชื่อ route", **params)   เช่น show("product_detail", product_id=5)
- ย้อนกลับด้วย  self.controller.go_back()
- ออกจากระบบด้วย self.controller.logout()
- โหมดผู้เยี่ยมชม (Guest): สามารถเปิดดูหน้า home, category, product_detail, compare, racket_finder ได้
  แต่เมื่อกดทำรายการที่ต้องใช้บัญชี (เช่น ตะกร้า, สั่งซื้อ, รายการโปรด, แชท, ออเดอร์) ระบบจะพาไปหน้า login พร้อมจำหน้าปลายทางไว้
"""

import importlib
import inspect
import traceback

import customtkinter as ctk

from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_GUEST, ROLE_OWNER
from core.session import Session
from services import auth_service
from ui.theme import ThemeManager

# ---------------------------------------------------------------------------
# ทะเบียนหน้า: route -> (โมดูล, ชื่อคลาส)
# ---------------------------------------------------------------------------
ROUTE_TABLE = {
    # --- ผู้ซื้อ (ui/pages/buyer/) ---
    "login": ("ui.pages.buyer.login", "LoginPage"),
    "register": ("ui.pages.buyer.register", "RegisterPage"),
    "home": ("ui.pages.buyer.home", "HomePage"),
    "category": ("ui.pages.buyer.category", "CategoryPage"),
    "product_detail": ("ui.pages.buyer.product_detail", "ProductDetailPage"),
    "compare": ("ui.pages.buyer.compare", "ComparePage"),
    "racket_finder": ("ui.pages.buyer.racket_finder", "RacketFinderPage"),
    "wishlist": ("ui.pages.buyer.wishlist", "WishlistPage"),
    "cart": ("ui.pages.buyer.cart", "CartPage"),
    "checkout": ("ui.pages.buyer.checkout", "CheckoutPage"),
    "addresses": ("ui.pages.buyer.addresses", "AddressesPage"),
    "payment": ("ui.pages.buyer.payment", "PaymentPage"),
    "orders": ("ui.pages.buyer.orders", "OrdersPage"),
    "order_detail": ("ui.pages.buyer.order_detail", "OrderDetailPage"),
    "write_review": ("ui.pages.buyer.write_review", "WriteReviewPage"),
    "profile": ("ui.pages.buyer.profile", "ProfilePage"),
    "notifications": ("ui.pages.buyer.notifications", "NotificationsPage"),
    "chat": ("ui.pages.buyer.chat", "ChatPage"),
    # --- แอดมิน/เจ้าของ (ui/pages/admin/) ---
    "admin_dashboard": ("ui.pages.admin.dashboard", "AdminDashboardPage"),
    "admin_products": ("ui.pages.admin.products", "AdminProductsPage"),
    "admin_product_form": ("ui.pages.admin.product_form", "AdminProductFormPage"),
    "admin_categories": ("ui.pages.admin.categories", "AdminCategoriesPage"),
    "admin_orders": ("ui.pages.admin.orders", "AdminOrdersPage"),
    "admin_order_detail": ("ui.pages.admin.order_detail", "AdminOrderDetailPage"),
    "admin_payments": ("ui.pages.admin.payments", "AdminPaymentsPage"),
    "admin_coupons": ("ui.pages.admin.coupons", "AdminCouponsPage"),
    "admin_coupon_form": ("ui.pages.admin.coupon_form", "AdminCouponFormPage"),
    "admin_chat": ("ui.pages.admin.chat", "AdminChatPage"),
    "admin_users": ("ui.pages.admin.users", "AdminUsersPage"),
    "admin_settings": ("ui.pages.admin.settings", "AdminSettingsPage"),
}

# หน้า auth ที่ไม่ต้องล้างตอน logout
PUBLIC_ROUTES = frozenset({"login", "register"})

# หน้าหน้าร้านที่ผู้เยี่ยมชม (Guest) เข้าชมได้โดยยังไม่ต้องล็อกอิน (AUTH-2)
GUEST_STOREFRONT_ROUTES = frozenset({
    "home", "category", "product_detail", "compare", "racket_finder",
})

_STAFF = (ROLE_ADMIN, ROLE_OWNER)
_BUYER_ONLY = (ROLE_BUYER,)
_ALL_ROLES = (ROLE_ADMIN, ROLE_OWNER, ROLE_BUYER)

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

HISTORY_LIMIT = 30


class _PageNotReady(Exception):
    """หน้านี้ยังไม่ถูกเขียน — ใช้หน้าแทนแบบเงียบ ๆ"""


class _PlaceholderPage(ctk.CTkFrame):
    """หน้าแทนที่ใช้เมื่อหน้าจริงยังไม่พร้อม — ให้แอปยังใช้งานส่วนอื่นต่อได้"""

    def __init__(self, parent, controller, route_name="", detail=""):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        box = ctk.CTkFrame(self, fg_color="transparent")
        box.grid(row=1, column=0)
        ctk.CTkLabel(box, text="🚧", font=("Arimo", 44)).pack(pady=(0, 8))
        ctk.CTkLabel(
            box, text="หน้านี้ยังไม่พร้อมใช้งาน", font=ThemeManager.get_font("h2"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack()
        ctk.CTkLabel(
            box, text=f"({route_name})", font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(pady=(2, 0))
        if detail:
            ctk.CTkLabel(
                box, text=detail, font=ThemeManager.get_font("small"),
                text_color=ThemeManager.get_color_pair("danger"), wraplength=520,
            ).pack(pady=(10, 0))
        ctk.CTkButton(
            box, text="ย้อนกลับ", width=140, command=lambda: controller.go_back(),
            **ThemeManager.button_style("outline"),
        ).pack(pady=(18, 0))

    def on_show(self, **kwargs):
        pass


class Router:
    def __init__(self, container):
        self.container = container
        self.frames = {}
        self.current_route = None
        self.current_params = {}
        self.history = []          # [(route, params), ...] สำหรับ go_back()
        self.listeners = []        # ฟังก์ชัน f(route, params) เรียกหลังเปลี่ยนหน้าทุกครั้ง
        self.navbar = None
        self.sidebar = None
        self.pending_after_login = None  # (route, params) เมื่อผู้เยี่ยมชมกดฟีเจอร์ที่ต้องล็อกอิน

        self.routes = dict(ROUTE_TABLE)

    # ------------------------------------------------------------------ registry
    def register_route(self, route_name: str, page):
        """เพิ่ม/แทนที่ route (page = คลาส หรือ (module, class_name))"""
        self.routes[route_name] = page
        old = self.frames.pop(route_name, None)
        if old is not None:
            old.destroy()

    def register_temp_routes(self, temp_routes: dict):
        """รับ dict ชื่อ route -> คลาสหน้าจอ"""
        for name, page in temp_routes.items():
            self.register_route(name, page)

    def add_listener(self, callback):
        """ลงทะเบียนฟังก์ชัน callback(route, params) ที่ถูกเรียกหลังเปลี่ยนหน้า"""
        self.listeners.append(callback)

    # ------------------------------------------------------------------ สิทธิ์
    def _can_access(self, route_name: str):
        """
        ตรวจสิทธิ์เข้าหน้า
        คืนค่า: None ถ้าเข้าได้, หรือชื่อ "login" / "redirect" บอกว่าต้องพาไปที่ไหนแทน
        """
        if route_name in PUBLIC_ROUTES:
            return None
        # ผู้เยี่ยมชม (Guest) สามารถดูหน้าร้านสาธารณะได้เมื่อเปิดโหมดผู้เยี่ยมชมไว้ (Session.is_guest())
        if route_name in GUEST_STOREFRONT_ROUTES and Session.is_guest():
            return None
        if not Session.is_authenticated():
            return "login"
        allowed = ROUTE_ROLES.get(route_name)
        if allowed and Session.get_role() not in allowed:
            return "redirect"
        return None

    # ------------------------------------------------------------------ สร้างหน้า
    def _resolve_page_class(self, route_name: str):
        entry = self.routes[route_name]
        if not isinstance(entry, tuple):
            return entry
        module_name, class_name = entry
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                raise _PageNotReady() from exc
            raise
        page_class = getattr(module, class_name, None)
        if page_class is None:
            raise _PageNotReady()
        return page_class

    def _build_frame(self, route_name: str):
        try:
            page_class = self._resolve_page_class(route_name)
        except _PageNotReady:
            return _PlaceholderPage(self.container, self, route_name)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            return _PlaceholderPage(self.container, self, route_name, f"โหลดหน้าไม่สำเร็จ: {exc}")
        try:
            return page_class(parent=self.container, controller=self)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            return _PlaceholderPage(self.container, self, route_name, f"สร้างหน้าไม่สำเร็จ: {exc}")

    # ------------------------------------------------------------------ สลับหน้า
    def show(self, route_name: str, **params):
        """สลับไปยังหน้าที่กำหนด พร้อมบันทึกกิจกรรมการใช้งานเพื่อรีเซ็ต idle timer"""
        Session.touch()
        self._navigate(route_name, params, push=True)

    def enter_guest_storefront(self, route_name: str = "home", **params):
        """เข้าชมหน้าร้านในฐานะผู้เยี่ยมชม (ไม่ต้องล็อกอิน แต่ดูสินค้า/คูปอง/เปรียบเทียบไม้ได้)"""
        Session.enter_guest()
        self.history.clear()
        self._navigate(route_name if route_name in GUEST_STOREFRONT_ROUTES else "home", params, push=False)

    @staticmethod
    def _call_on_show(on_show, params: dict):
        if not params:
            on_show()
            return
        try:
            sig = inspect.signature(on_show)
            has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if has_var_kw:
                on_show(**params)
            else:
                accepted = {k: v for k, v in params.items() if k in sig.parameters}
                on_show(**accepted)
        except (ValueError, TypeError):
            on_show(**params)

    def _navigate(self, route_name: str, params: dict, push: bool):
        if route_name not in self.routes:
            raise ValueError(f"ไม่พบหน้า '{route_name}' ในระบบ Router")

        denied = self._can_access(route_name)
        if denied == "login":
            if route_name not in PUBLIC_ROUTES:
                self.pending_after_login = (route_name, dict(params))
            login_params = {"info_message": "กรุณาเข้าสู่ระบบเพื่อใช้งานฟังก์ชันนี้"} if Session.is_guest() else {}
            return self._navigate("login", login_params, push=False)
        if denied == "redirect":
            return self.go_after_login(Session.current_user)

        if route_name not in self.frames:
            frame = self._build_frame(route_name)
            self.frames[route_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        if push and self.current_route and (self.current_route, self.current_params) != (route_name, params):
            if self.current_route not in PUBLIC_ROUTES:
                self.history.append((self.current_route, self.current_params))
                del self.history[:-HISTORY_LIMIT]

        frame = self.frames[route_name]
        frame.tkraise()
        self.current_route = route_name
        self.current_params = dict(params)

        on_show = getattr(frame, "on_show", None)
        if callable(on_show):
            self._call_on_show(on_show, params)

        for callback in list(self.listeners):
            try:
                callback(route_name, self.current_params)
            except Exception:  # noqa: BLE001
                traceback.print_exc()

    def go_back(self, default: str = None):
        while self.history:
            route, params = self.history.pop()
            if route in self.routes and self._can_access(route) is None:
                return self._navigate(route, params, push=False)
        if default and default in self.routes and self._can_access(default) is None:
            return self._navigate(default, {}, push=False)
        if Session.is_authenticated():
            return self.go_after_login(Session.current_user)
        if Session.is_guest():
            return self._navigate("home", {}, push=False)
        return self._navigate("login", {}, push=False)

    def refresh(self):
        if self.current_route:
            self._navigate(self.current_route, dict(self.current_params), push=False)

    def refresh_shell(self):
        for widget in (self.navbar, self.sidebar):
            if widget is not None:
                try:
                    widget.refresh()
                except Exception:  # noqa: BLE001
                    traceback.print_exc()

    def go_after_login(self, user):
        role = user["role"] if user else None
        self.history.clear()

        if role == ROLE_BUYER:
            pending = self.pending_after_login
            self.pending_after_login = None
            if pending and pending[0] in self.routes and self._can_access(pending[0]) is None:
                return self._navigate(pending[0], pending[1], push=False)
            self._navigate("home", {}, push=False)
        elif role in (ROLE_ADMIN, ROLE_OWNER):
            self.pending_after_login = None
            self._navigate("admin_dashboard", {}, push=False)
        else:
            Session.logout()
            self._navigate("login", {}, push=False)

    def logout(self):
        auth_service.logout()

        for name in list(self.frames):
            if name not in PUBLIC_ROUTES:
                self.frames.pop(name).destroy()

        self.history.clear()
        self.pending_after_login = None
        self.current_route = None
        self.current_params = {}
        self._navigate("login", {}, push=False)
