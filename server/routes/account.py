"""
server/routes/account.py
API สำหรับโปรไฟล์ส่วนตัว การเปลี่ยนอีเมลด้วย OTP ที่อยู่จัดส่ง และรายการโปรด (Wishlist)
"""
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from core.session import Session
from server import deps
from server.serializers import to_jsonable
from services import account_service, auth_service, otp_service

router = APIRouter(prefix="/api", tags=["account"])


def _client_ip(request: Request) -> str:
    fwd = (request.headers.get("x-forwarded-for") or "").strip()
    if fwd:
        return fwd.split(",", 1)[0].strip() or "unknown"
    if request.client and request.client.host:
        return str(request.client.host)
    return "unknown"


@router.get("/account/profile")
def get_profile():
    uid = deps.require_user_id()
    profile = account_service.get_profile(uid)
    user = Session.current_user or {}
    profile["must_change_password"] = bool(user.get("must_change_password", False))
    return to_jsonable(profile)


@router.post("/account/profile/validate")
def validate_profile_before_save(payload: dict):
    """ตรวจสอบความถูกต้องของข้อมูลโปรไฟล์ก่อนเปิดกล่องยืนยันรหัสผ่านปัจจุบัน"""
    uid = deps.require_user_id()
    cleaned = auth_service.validate_profile_fields(
        user_id=uid,
        full_name=payload.get("full_name") or "",
        phone=payload.get("phone") or "",
        username=payload.get("username"),
    )
    return to_jsonable({"ok": True, "cleaned": cleaned})


@router.put("/account/profile")
def update_profile(payload: dict):
    uid = deps.require_user_id()
    current_password = (
        payload.get("current_password")
        if payload.get("current_password") is not None
        else payload.get("password")
    )
    updated = auth_service.update_profile(
        user_id=uid,
        full_name=payload.get("full_name") or "",
        phone=payload.get("phone") or "",
        avatar_path=payload.get("avatar_path"),
        username=payload.get("username"),
        current_password=current_password,
        require_password=True,
    )
    return to_jsonable({"user": updated, "profile": account_service.get_profile(uid)})


@router.post("/account/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_password: str | None = Form(None),
):
    uid = deps.require_user_id()
    suffix = Path(file.filename or "avatar.jpg").suffix.lower() or ".jpg"
    raw = file.file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)
    try:
        profile = account_service.set_avatar(
            uid,
            tmp_path,
            current_password=current_password,
            require_password=bool(current_password is not None),
        )
        return to_jsonable({"profile": profile, "user": Session.current_user})
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/account/email/request-otp")
def request_email_change_otp(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    uid = deps.require_user_id()
    res = auth_service.request_email_change_otp(
        user_id=uid,
        new_email=payload.get("new_email") or payload.get("email") or "",
        check_cooldown=bool(payload.get("check_cooldown", True)),
    )
    return to_jsonable(res)


@router.post("/account/email/confirm-otp")
def confirm_email_change_otp(payload: dict, request: Request):
    try:
        otp_service.check_ip_rate_limit(_client_ip(request))
    except otp_service.OtpRateLimitError as exc:
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    uid = deps.require_user_id()
    current_password = payload.get("current_password") or payload.get("password")
    updated = auth_service.confirm_email_change_with_otp(
        user_id=uid,
        new_email=payload.get("new_email") or payload.get("email") or "",
        otp_code=payload.get("otp_code") or payload.get("code") or "",
        current_password=current_password,
        require_password=bool(current_password is not None),
    )
    return to_jsonable({"user": updated, "profile": account_service.get_profile(uid)})


# ==========================================
# ที่อยู่จัดส่ง (Addresses)
# ==========================================

@router.get("/addresses")
def list_addresses():
    uid = deps.require_user_id()
    return to_jsonable(account_service.list_addresses(uid))


@router.get("/addresses/{address_id}")
def get_address(address_id: int):
    uid = deps.require_user_id()
    return to_jsonable(account_service.get_address(uid, address_id))


@router.post("/addresses/validate")
def validate_address_endpoint(payload: dict):
    uid = deps.require_user_id()
    errors = account_service.validate_address_fields(
        recipient=payload.get("recipient") or "",
        phone=payload.get("phone") or "",
        address_line=payload.get("address_line") or "",
        district=payload.get("district") or "",
        province=payload.get("province") or "",
        postcode=payload.get("postcode") or "",
    )
    return to_jsonable({"ok": len(errors) == 0, "valid": len(errors) == 0, "errors": errors})


@router.post("/addresses")
def add_address(payload: dict):
    uid = deps.require_user_id()
    addr = account_service.add_address(
        user_id=uid,
        recipient=payload.get("recipient") or "",
        phone=payload.get("phone") or "",
        address_line=payload.get("address_line") or "",
        district=payload.get("district") or "",
        province=payload.get("province") or "",
        postcode=payload.get("postcode") or "",
        is_default=bool(payload.get("is_default", False)),
    )
    return to_jsonable(addr)


@router.put("/addresses/{address_id}")
def update_address(address_id: int, payload: dict):
    uid = deps.require_user_id()
    addr = account_service.update_address(
        user_id=uid,
        address_id=address_id,
        recipient=payload.get("recipient") or "",
        phone=payload.get("phone") or "",
        address_line=payload.get("address_line") or "",
        district=payload.get("district") or "",
        province=payload.get("province") or "",
        postcode=payload.get("postcode") or "",
    )
    if payload.get("is_default"):
        addr = account_service.set_default_address(uid, address_id)
    return to_jsonable(addr)


@router.delete("/addresses/{address_id}")
def delete_address(address_id: int):
    uid = deps.require_user_id()
    ok = account_service.delete_address(uid, address_id)
    return {"ok": bool(ok)}


@router.post("/addresses/{address_id}/default")
def set_default_address(address_id: int):
    uid = deps.require_user_id()
    addr = account_service.set_default_address(uid, address_id)
    return to_jsonable(addr)


# ==========================================
# รายการโปรด (Wishlist)
# ==========================================

@router.get("/wishlist")
def list_wishlist():
    uid = deps.require_user_id()
    return to_jsonable(account_service.list_wishlist(uid))


@router.post("/wishlist/toggle")
def toggle_wishlist(payload: dict):
    uid = deps.require_user_id()
    product_id = int(payload.get("product_id"))
    return to_jsonable(account_service.toggle_wishlist(uid, product_id))
