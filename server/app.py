"""
server/app.py
สร้าง FastAPI application พร้อม:
- Lifespan (startup / shutdown background jobs และการสำรองฐานข้อมูลอัตโนมัติ)
- Middleware กู้คืน Session จากคุกกี้ลง ContextVar ต่อคำขอ และล้างท้ายคำขอเสมอ
- Middleware ตรวจ Origin/Referer ป้องกัน CSRF สำหรับคำขอที่แก้ไขข้อมูล
- ตัวจัดการ Exception กลาง (ValueError -> 400, PermissionError -> 401/403, อื่นๆ -> 500 โดยไม่รั่ว stack trace)
- เสิร์ฟไฟล์สาธารณะ (web/, assets/fonts, assets/images, assets/icons, assets/reviews) และบล็อกการเข้าถึงสลิป/ใบเสร็จแบบไม่มีสิทธิ์
"""
from contextlib import asynccontextmanager
import hashlib
import html
import re
import traceback
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import config
from core import permissions
from core.constants import ROLE_ADMIN, ROLE_OWNER
from core.session import Session
from database import repo_orders, repo_payments, repo_sessions, repo_users
from server import jobs
from server.routes import (
    account,
    admin_ops,
    auth,
    cart,
    coupons_settings,
    orders_payments,
    products,
    reviews_notifications_chat,
)
from services import settings_service

_LOCK_EXEMPT_PATHS = frozenset({
    "/api/auth/unlock",
    "/api/auth/logout",
    "/api/auth/me",
    "/api/auth/idle-status",
    "/api/auth/lock",
    "/api/bootstrap",
})

_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "0.0.0.0", "testserver"})


def _extract_host(url_or_host: str) -> str:
    val = (url_or_host or "").strip().lower()
    if not val:
        return ""
    if "://" in val:
        parsed = urlparse(val)
        return (parsed.hostname or "").lower()
    return val.split(":", 1)[0].strip().lower()


def _is_same_origin(request: Request) -> bool:
    """ตรวจ Origin/Referer สำหรับคำขอที่แก้ไขข้อมูล เพื่อป้องกัน CSRF"""
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    source = origin or referer
    if not source:
        return True
    if source.strip().lower() == "null":
        return False
    src_host = _extract_host(source)
    req_host = _extract_host(request.headers.get("host") or "")
    if not src_host:
        return False
    if src_host == req_host:
        return True
    if src_host in _LOCAL_HOSTS and (not req_host or req_host in _LOCAL_HOSTS):
        return True
    return False


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config.check_otp_and_smtp_startup_warnings()
    jobs.start_background_jobs()
    try:
        yield
    finally:
        jobs.stop_background_jobs()


def create_app() -> FastAPI:
    config.ensure_dirs()
    app = FastAPI(
        title="AI.HERE BADᴍᴛ-Zone Web API",
        version="3.0.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def session_and_csrf_middleware(request: Request, call_next):
        Session.clear_context()
        try:
            path = request.url.path

            # 1. ตรวจ CSRF Origin บนคำขอที่แก้ไขข้อมูล
            if request.method in _MUTATING_METHODS and path.startswith("/api/"):
                if not _is_same_origin(request):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "ปฏิเสธคำขอข้ามโดเมน (Origin ไม่ถูกต้อง)"},
                    )

            # 2. กู้คืน Session จากคุกกี้เข้าสู่ ContextVar ของคำขอนี้
            raw_token = request.cookies.get(config.SESSION_COOKIE_NAME, "").strip()
            restored = False
            if raw_token:
                token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
                try:
                    sess_row = repo_sessions.get_valid_session(token_hash)
                except Exception:
                    sess_row = None
                if sess_row is not None and sess_row["is_active"]:
                    user_row = repo_users.get_by_id(sess_row["user_id"])
                    if user_row is not None and user_row["is_active"]:
                        Session.bind_request_session(user_row, session_token=raw_token, touch=False)
                        restored = True

                        # ตรวจ Idle Timeout สำหรับพนักงาน (admin / owner)
                        role = user_row["role"]
                        if role in (ROLE_ADMIN, ROLE_OWNER) and not Session.is_locked:
                            timeout_sec = max(60, int(config.STAFF_IDLE_TIMEOUT_MINUTES) * 60)
                            if Session.idle_seconds() >= timeout_sec:
                                Session.lock()

                        if Session.is_locked and path.startswith("/api/") and path not in _LOCK_EXEMPT_PATHS:
                            return JSONResponse(
                                status_code=423,
                                content={
                                    "detail": "หน้าจอถูกล็อกอัตโนมัติเนื่องจากไม่มีการใช้งาน กรุณากรอกรหัสผ่านเพื่อปลดล็อก",
                                    "locked": True,
                                },
                            )

                        if not Session.is_locked and path != "/api/auth/idle-status":
                            Session.touch()

            if not restored:
                # คำขอที่ไม่มีคุกกี้ล็อกอินถือเป็นโหมดผู้เยี่ยมชม (guest) ตาม PLAN.md หัวข้อ 5.1
                Session.enter_guest()

            response = await call_next(request)
            if path == "/" or path.startswith("/js/") or path.startswith("/css/"):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response
        finally:
            Session.clear_context()

    # ------------------------------------------------------------------ Exception Handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(PermissionError)
    async def permission_error_handler(_request: Request, exc: PermissionError):
        status = 403 if Session.is_authenticated() else 401
        return JSONResponse(status_code=status, content={"detail": str(exc)})

    @app.exception_handler(FileNotFoundError)
    async def not_found_error_handler(_request: Request, exc: FileNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc) or "ไม่พบไฟล์ที่ร้องขอ"})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"detail": "ข้อมูลคำขอไม่ถูกต้อง", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception):
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง"},
        )

    # ------------------------------------------------------------------ Protected Slips & Receipts Guard
    @app.get("/assets/slips/{filename:path}")
    def protected_slip_asset(filename: str):
        """ห้ามเข้าถึงสลิปโอนเงินแบบสาธารณะ — ต้องเป็นเจ้าของออเดอร์หรือพนักงานที่มีสิทธิ์ตรวจสลิป/ดูออเดอร์"""
        if not Session.is_authenticated():
            raise PermissionError("กรุณาเข้าสู่ระบบก่อน")
        clean_name = (config.SLIPS_DIR / filename).resolve()
        if config.SLIPS_DIR.resolve() not in clean_name.parents or not clean_name.is_file():
            raise FileNotFoundError("ไม่พบไฟล์สลิป")

        role = Session.get_role()
        if not (permissions.can(role, permissions.SLIP_VERIFY) or permissions.can(role, permissions.ORDER_VIEW)):
            uid = Session.get_user_id()
            m = re.match(r"^slip_(\d+)_", clean_name.name)
            if not m:
                raise PermissionError("คุณไม่มีสิทธิ์ดูสลิปนี้")
            order = repo_orders.get_order(int(m.group(1)))
            if order is None or order["user_id"] != uid:
                raise PermissionError("คุณไม่มีสิทธิ์ดูสลิปของคำสั่งซื้ออื่น")
        return FileResponse(path=str(clean_name))

    @app.get("/assets/receipts/{filename:path}")
    def protected_receipt_asset(filename: str):
        """ห้ามเข้าถึงใบเสร็จ PDF แบบสาธารณะ — ต้องเป็นเจ้าของออเดอร์หรือพนักงาน"""
        if not Session.is_authenticated():
            raise PermissionError("กรุณาเข้าสู่ระบบก่อน")
        clean_name = (config.RECEIPTS_DIR / filename).resolve()
        if config.RECEIPTS_DIR.resolve() not in clean_name.parents or not clean_name.is_file():
            raise FileNotFoundError("ไม่พบไฟล์ใบเสร็จ")

        role = Session.get_role()
        if not permissions.can(role, permissions.ORDER_VIEW):
            uid = Session.get_user_id()
            m = re.match(r"^receipt_(\d+)\.pdf$", clean_name.name)
            if not m:
                raise PermissionError("คุณไม่มีสิทธิ์ดูใบเสร็จนี้")
            order = repo_orders.get_order(int(m.group(1)))
            if order is None or order["user_id"] != uid:
                raise PermissionError("คุณไม่มีสิทธิ์ดูใบเสร็จของคำสั่งซื้ออื่น")
        return FileResponse(path=str(clean_name), media_type="application/pdf")

    # ------------------------------------------------------------------ Register API Routers
    app.include_router(auth.router)
    app.include_router(account.router)
    app.include_router(products.router)
    app.include_router(cart.router)
    app.include_router(coupons_settings.router)
    app.include_router(orders_payments.router)
    app.include_router(reviews_notifications_chat.router)
    app.include_router(admin_ops.router)

    # ------------------------------------------------------------------ Static Assets (เฉพาะโฟลเดอร์สาธารณะ)
    config.REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    config.CHAT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/assets/fonts", StaticFiles(directory=str(config.FONTS_DIR)), name="assets_fonts")
    app.mount("/assets/images", StaticFiles(directory=str(config.IMAGES_DIR)), name="assets_images")
    app.mount("/assets/icons", StaticFiles(directory=str(config.ICONS_DIR)), name="assets_icons")
    app.mount("/assets/reviews", StaticFiles(directory=str(config.REVIEWS_DIR)), name="assets_reviews")

    web_css = config.WEB_DIR / "css"
    web_js = config.WEB_DIR / "js"
    web_css.mkdir(parents=True, exist_ok=True)
    web_js.mkdir(parents=True, exist_ok=True)
    app.mount("/css", StaticFiles(directory=str(web_css)), name="web_css")
    app.mount("/js", StaticFiles(directory=str(web_js)), name="web_js")

    @app.get("/api/health")
    def api_health():
        return {"ok": True}

    @app.get("/favicon.ico")
    def serve_favicon():
        icon_file = config.ICONS_DIR / "no_image.svg"
        if icon_file.is_file():
            return FileResponse(path=str(icon_file), media_type="image/svg+xml")
        return HTMLResponse(content="", status_code=204)

    @app.get("/", response_class=HTMLResponse)
    def serve_spa_index():
        try:
            shop_name = settings_service.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
        except Exception:
            shop_name = "AI.HERE BADᴍᴛ-Zone"
        safe_title = html.escape(str(shop_name))
        index_file = config.WEB_DIR / "index.html"
        if index_file.is_file():
            raw_html = index_file.read_text(encoding="utf-8")
            raw_html = re.sub(r"<title>.*?</title>", f"<title>{safe_title}</title>", raw_html, count=1, flags=re.DOTALL)
            return HTMLResponse(content=raw_html)
        return HTMLResponse(content=f"<!doctype html><html lang='th'><head><meta charset='utf-8'><title>{safe_title}</title></head><body><div id='app'>{safe_title}</div></body></html>")

    return app


app = create_app()
