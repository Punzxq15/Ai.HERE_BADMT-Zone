"""
server/routes/auth.py
API สำหรับการยืนยันตัวตน เซสชัน สมัครสมาชิก+OTP ลืมรหัสผ่าน เปลี่ยนรหัสผ่าน โหมดผู้เยี่ยมชม และการล็อกหน้าจอเมื่อไม่มีการใช้งาน
"""
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

import config
from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_OWNER
from core.session import Session
from server import deps
from server.serializers import to_jsonable
from services import (
    auth_service,
    banner_service,
    cart_service,
    chat_service,
    contact_service,
    notification_service,
    otp_service,
    payment_service,
    settings_service,
)

router = APIRouter(prefix="/api", tags=["auth"])


def _client_ip(request: Request) -> str:
    fwd = (request.headers.get("x-forwarded-for") or "").strip()
    if fwd:
        return fwd.split(",", 1)[0].strip() or "unknown"
    if request.client and request.client.host:
        return str(request.client.host)
    return "unknown"


def _set_session_cookie(response: Response, raw_token: str, role: str, remember: bool) -> None:
    days = 90 if (role in (ROLE_ADMIN, ROLE_OWNER) and remember) else 7
    max_age = days * 86400 if remember else 7 * 86400
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=bool(config.COOKIE_SECURE),
        path="/",
    )
    response.delete_cookie(key=config.GUEST_COOKIE_NAME, path="/")


@router.get("/bootstrap")
def get_bootstrap():
    """ดึงสถานะเริ่มต้นของแอป: ผู้ใช้ปัจจุบัน การตั้งค่าร้าน แบนเนอร์หน้า Login ข้อมูลติดต่อ และตัวเลขแจ้งเตือน"""
    user = Session.current_user
    role = Session.get_role()
    uid = Session.get_user_id()

    shop_info = settings_service.get_shop_info()
    login_banners = banner_service.list_login_banners()
    shop_info["login_banners"] = login_banners
    contact_info = contact_service.get_owner_contact_info()

    cart_count = 0
    unread_notis = 0
    unread_chat = 0
    pending_slips = 0

    if Session.is_authenticated() and not Session.is_locked:
        try:
            unread_notis = notification_service.unread_count()
        except Exception:
            unread_notis = 0
        try:
            unread_chat = chat_service.unread_count()
        except Exception:
            unread_chat = 0
        if role == ROLE_BUYER and uid:
            try:
                cart_count = cart_service.get_cart_count(uid)
            except Exception:
                cart_count = 0
        elif role in (ROLE_ADMIN, ROLE_OWNER):
            try:
                pending_slips = len(payment_service.list_pending_payments())
            except Exception:
                pending_slips = 0

    return to_jsonable({
        "user": user,
        "is_authenticated": Session.is_authenticated(),
        "is_guest": Session.is_guest(),
        "is_locked": Session.is_locked,
        "idle_seconds": round(Session.idle_seconds(), 1),
        "idle_timeout_minutes": config.STAFF_IDLE_TIMEOUT_MINUTES,
        "shop": shop_info,
        "login_banners": login_banners,
        "contact": contact_info,
        "badges": {
            "cart_count": cart_count,
            "unread_notifications": unread_notis,
            "unread_chat": unread_chat,
            "pending_slips": pending_slips,
        },
    })


@router.get("/auth/ui-config")
def get_auth_ui_config():
    """ดึงโลโก้ร้านและรายการแบนเนอร์รองเท้าสำหรับหน้า Login & Sign Up"""
    shop_info = settings_service.get_shop_info()
    banners = banner_service.list_login_banners()
    return to_jsonable({
        "store_logo_path": shop_info.get("store_logo_path") or "",
        "shop_logo_path": shop_info.get("shop_logo_path") or "",
        "login_banners": banners,
        "login_showcase_seconds": shop_info.get("login_showcase_seconds", 5),
    })


@router.get("/auth/me")
def get_me():
    return to_jsonable({
        "user": Session.current_user,
        "is_authenticated": Session.is_authenticated(),
        "is_guest": Session.is_guest(),
        "is_locked": Session.is_locked,
        "idle_seconds": round(Session.idle_seconds(), 1),
        "idle_timeout_minutes": config.STAFF_IDLE_TIMEOUT_MINUTES,
    })


@router.post("/auth/login")
def login(payload: dict, response: Response):
    identifier = payload.get("identifier") or payload.get("username") or payload.get("email") or ""
    password = payload.get("password") or ""
    remember = bool(payload.get("remember", False))
    user = auth_service.login(identifier, password, remember=remember)
    raw_token = Session.session_token
    if raw_token:
        _set_session_cookie(response, raw_token, user.get("role", ROLE_BUYER), remember)
    return to_jsonable({
        "user": user,
        "is_authenticated": True,
        "is_guest": False,
        "is_locked": False,
    })


@router.post("/auth/logout")
def logout(response: Response):
    auth_service.logout()
    response.delete_cookie(key=config.SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key=config.GUEST_COOKIE_NAME, path="/")
    return {"ok": True}


@router.post("/auth/guest")
def enter_guest(response: Response):
    if Session.is_authenticated():
        auth_service.logout()
    Session.enter_guest()
    response.delete_cookie(key=config.SESSION_COOKIE_NAME, path="/")
    response.set_cookie(
        key=config.GUEST_COOKIE_NAME,
        value="1",
        max_age=7 * 86400,
        httponly=True,
        samesite="lax",
        secure=bool(config.COOKIE_SECURE),
        path="/",
    )
    return {"ok": True, "is_guest": True}


@router.post("/auth/register")
def register_direct(payload: dict):
    user = auth_service.register(
        username=payload.get("username") or "",
        email=payload.get("email") or "",
        password=payload.get("password") or "",
        full_name=payload.get("full_name") or "",
        phone=payload.get("phone") or "",
    )
    return to_jsonable({"user": user})


@router.post("/auth/register/start")
def register_start(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    addr = payload.get("address")
    if not isinstance(addr, dict):
        addr = {
            "recipient": payload.get("recipient") or payload.get("full_name") or "",
            "phone": payload.get("address_phone") or payload.get("phone") or "",
            "address_line": payload.get("address_line") or "",
            "district": payload.get("district") or "",
            "province": payload.get("province") or "",
            "postcode": payload.get("postcode") or "",
        }
    res = auth_service.register_start(
        email=payload.get("email") or "",
        password=payload.get("password") or "",
        full_name=payload.get("full_name") or "",
        phone=payload.get("phone") or "",
        address=addr,
        username=payload.get("username"),
    )
    return to_jsonable({
        **res,
        "otp_required": True,
    })


@router.post("/auth/register/resend")
def register_resend(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    res = auth_service.resend_register_otp(payload.get("email") or "")
    return to_jsonable(res)


@router.post("/auth/register/verify")
def register_verify(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    user = auth_service.register_verify(
        email=payload.get("email") or "",
        otp_code=payload.get("otp_code") or payload.get("code") or "",
    )
    return to_jsonable({"user": user})


@router.post("/auth/reset/start")
def reset_start(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    res = auth_service.reset_start(payload.get("email") or "")
    return to_jsonable(res)


@router.post("/auth/reset/resend")
def reset_resend(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    res = auth_service.resend_reset_otp(payload.get("email") or "")
    return to_jsonable(res)


@router.post("/auth/reset/verify")
def reset_verify(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    new_pw = payload.get("new_password") or ""
    confirm_pw = payload.get("confirm_password")
    if confirm_pw is None:
        confirm_pw = new_pw
    ok = auth_service.reset_verify(
        email=payload.get("email") or "",
        otp_code=payload.get("otp_code") or payload.get("code") or "",
        new_password=new_pw,
        confirm_password=confirm_pw,
    )
    return {"ok": bool(ok), "message": "ตั้งรหัสผ่านใหม่เรียบร้อยแล้ว กรุณาเข้าสู่ระบบ"}


@router.post("/auth/change-password")
def change_password(payload: dict):
    uid = deps.require_user_id()
    old_pw = payload.get("old_password") or ""
    new_pw = payload.get("new_password") or ""
    confirm_pw = payload.get("confirm_password")
    if confirm_pw is not None and new_pw != confirm_pw:
        raise ValueError("รหัสผ่านใหม่และการยืนยันรหัสผ่านไม่ตรงกัน")
    ok = auth_service.change_password(uid, old_pw, new_pw)
    return to_jsonable({"ok": bool(ok), "user": Session.current_user})


@router.post("/auth/lock")
def lock_session():
    deps.require_user_id()
    Session.lock()
    return {"ok": True, "is_locked": Session.is_locked}


@router.post("/auth/unlock")
def unlock_session(payload: dict):
    password = payload.get("password") or ""
    auth_service.unlock_session(password)
    return to_jsonable({"ok": True, "is_locked": False, "user": Session.current_user})


@router.post("/auth/heartbeat")
def heartbeat():
    if Session.is_authenticated() and not Session.is_locked:
        Session.touch()
    return {
        "ok": True,
        "is_authenticated": Session.is_authenticated(),
        "is_locked": Session.is_locked,
        "idle_seconds": round(Session.idle_seconds(), 1),
    }


@router.get("/auth/idle-status")
def idle_status():
    return {
        "is_authenticated": Session.is_authenticated(),
        "is_locked": Session.is_locked,
        "idle_seconds": round(Session.idle_seconds(), 1),
        "timeout_minutes": config.STAFF_IDLE_TIMEOUT_MINUTES,
    }


@router.get("/auth/check-route")
def check_route(route: str):
    return to_jsonable(deps.check_route_access(route))
