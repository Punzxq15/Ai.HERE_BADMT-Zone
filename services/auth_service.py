"""
services/auth_service.py
จัดการตรรกะหลักของระบบผู้ใช้ (Business Logic)
เป็นส่วนเดียวที่ชั้นหน้าจอควรเรียกใช้งานสำหรับการยืนยันตัวตน สมัครสมาชิก โปรไฟล์ และจัดการบัญชี

ฟังก์ชันเดิม (พฤติกรรมไม่เปลี่ยน): hash_password, verify_password, register, login, logout,
                                change_password, update_profile, create_staff, set_user_active,
                                list_users, clear_all_online
เพิ่มตามข้อกำหนด PDF:
- register_start / register_verify / resend_register_otp (สมัครด้วยอีเมลจริง + ที่อยู่เริ่มต้น + ยืนยัน OTP)
- reset_start / reset_verify / resend_reset_otp (ลืมรหัสผ่านผู้ซื้อด้วย OTP)
- unlock_session (ปลดล็อกหน้าจอเมื่อเครื่องร้านถูกล็อกหลังไม่มีการใช้งาน)
- save_remember_session / restore_remember_session (เซสชันค้างล็อกอินสำหรับเครื่องร้าน)
- T11: update_username, request_email_change_otp, confirm_email_change_with_otp
"""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import bcrypt

import config
from core import permissions
from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_OWNER
from core.session import Session
from database import repo_addresses, repo_otp, repo_sessions, repo_users
from database.db import transaction
from services import audit_service, email_service, otp_service, settings_service
from utils import validators
from utils.formatters import parse_datetime

MAX_PASSWORD_BYTES = 72

_dummy_hash = None


def _get_dummy_hash() -> str:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("dummy-password-for-timing")
    return _dummy_hash


def _password_too_long(password: str) -> bool:
    """เช็คว่ารหัสผ่านยาวเกินขีดจำกัดของ bcrypt หรือไม่ (นับเป็นไบต์)"""
    return len(password.encode("utf-8")) > MAX_PASSWORD_BYTES


def _col(row, key, default=None):
    try:
        val = row[key]
        return default if val is None else val
    except (KeyError, IndexError, TypeError):
        return default


def _public_user(row) -> dict:
    """แปลงแถวผู้ใช้จากฐานข้อมูลเป็น dict ที่ตัด password_hash ออก"""
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "full_name": row["full_name"],
        "phone": row["phone"],
        "role": row["role"],
        "avatar_path": row["avatar_path"],
        "is_active": row["is_active"],
        "email_verified": int(_col(row, "email_verified", 1)),
        "must_change_password": int(_col(row, "must_change_password", 0)),
        "last_login_at": _col(row, "last_login_at"),
        "created_at": row["created_at"],
    }


def hash_password(password: str) -> str:
    """ฟังก์ชันเข้ารหัสรหัสผ่านด้วย bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """ตรวจสอบรหัสผ่านว่าตรงกับ hash ในระบบหรือไม่"""
    if _password_too_long(password):
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _check_new_password(password: str) -> None:
    """ตรวจรหัสผ่านใหม่ (ใช้ร่วมกันทั้งสมัคร/สร้างแอดมิน/เปลี่ยนรหัสผ่าน)"""
    if not validators.is_strong_password(password):
        raise ValueError("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
    if _password_too_long(password):
        raise ValueError("รหัสผ่านยาวเกินไป (ไม่เกิน 72 ไบต์ หรือประมาณ 24 ตัวอักษรไทย)")


def _generate_unique_username(email: str, preferred: str = None, conn=None) -> str:
    """สร้าง username ที่ไม่ซ้ำจากค่าที่ระบุหรือจากส่วนหน้า @ ของอีเมล"""
    if preferred and preferred.strip():
        cand = preferred.strip()
        if not validators.is_valid_username(cand):
            raise ValueError("รูปแบบชื่อผู้ใช้ไม่ถูกต้อง (อนุญาตเฉพาะภาษาอังกฤษ ตัวเลข และ _ เท่านั้น)")
        if repo_users.username_exists(cand, conn=conn):
            raise ValueError("ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว")
        return cand

    local = (email or "user").split("@", 1)[0]
    base = re.sub(r"[^a-zA-Z0-9_]", "_", local).strip("_") or "user"
    base = base[:18]
    candidate = base
    for _ in range(20):
        if not repo_users.username_exists(candidate, conn=conn):
            return candidate
        candidate = f"{base}_{secrets.randbelow(9000) + 1000}"
    return f"user_{secrets.token_hex(4)}"


def _clean_initial_address(address: dict, fallback_name: str, fallback_phone: str) -> dict:
    """
    ตรวจและทำความสะอาดที่อยู่จัดส่งเริ่มต้นตอนสมัครสมาชิก:
    - หากเว้นว่างทั้ง 4 ช่อง (บ้านเลขที่/เขต/จังหวัด/รหัสไปรษณีย์) ให้คืน {} (สามารถเพิ่มภายหลังได้ตามดีไซน์ใหม่)
    - หากกรอกข้อมูลที่อยู่ ให้ตรวจสอบความถูกต้องและบันทึกเป็น "ที่อยู่เริ่มต้น"
    """
    addr = dict(address or {})
    recipient = str(addr.get("recipient") or fallback_name or "").strip()
    phone = str(addr.get("phone") or fallback_phone or "").strip()
    address_line = str(addr.get("address_line") or "").strip()
    district = str(addr.get("district") or "").strip()
    province = str(addr.get("province") or "").strip()
    postcode = str(addr.get("postcode") or "").strip()

    if not any((address_line, district, province, postcode)):
        return {}

    if not recipient:
        raise ValueError("กรุณากรอกชื่อผู้รับสำหรับที่อยู่จัดส่ง")
    if phone and not validators.is_valid_phone(phone):
        raise ValueError("รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (ต้องเป็นตัวเลข 10 หลักและขึ้นต้นด้วย 0)")
    if not address_line:
        raise ValueError("กรุณากรอกบ้านเลขที่/ถนน/ซอย (ที่อยู่จัดส่งเริ่มต้น)")
    if not district:
        raise ValueError("กรุณากรอกเขต/อำเภอ")
    if not province:
        raise ValueError("กรุณากรอกจังหวัด")
    if not validators.is_valid_postcode(postcode):
        raise ValueError("รหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลัก")

    return {
        "recipient": recipient[:100],
        "phone": phone or "0000000000",
        "address_line": address_line[:250],
        "district": district[:100],
        "province": province[:100],
        "postcode": postcode,
    }


def _create_account(username, email, password, full_name, phone, role) -> dict:
    """ขั้นตอนสร้างบัญชีที่ใช้ร่วมกัน (register / create_staff)"""
    username = (username or "").strip()
    email = (email or "").strip().lower()
    full_name = (full_name or "").strip()
    phone = (phone or "").strip()
    password = password or ""

    if not validators.is_valid_username(username):
        raise ValueError("รูปแบบชื่อผู้ใช้ไม่ถูกต้อง (อนุญาตเฉพาะภาษาอังกฤษ ตัวเลข และ _ เท่านั้น)")

    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")

    _check_new_password(password)

    if not full_name:
        raise ValueError("กรุณากรอกชื่อ-นามสกุล")

    if phone and not validators.is_valid_phone(phone):
        raise ValueError("รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (ต้องเป็นตัวเลข 10 หลักและขึ้นต้นด้วย 0)")

    if repo_users.username_exists(username):
        raise ValueError("ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว")

    if repo_users.email_exists(email):
        raise ValueError("อีเมลนี้ถูกใช้งานแล้ว")

    pwd_hash = hash_password(password)

    try:
        user_id = repo_users.create_user(
            username=username,
            email=email,
            password_hash=pwd_hash,
            full_name=full_name,
            phone=phone or None,
            role=role,
            email_verified=1,
        )
    except sqlite3.IntegrityError:
        raise ValueError("ชื่อผู้ใช้หรืออีเมลนี้ถูกใช้งานแล้ว") from None

    return _public_user(repo_users.get_by_id(user_id))


def register(username: str, email: str, password: str, full_name: str, phone: str):
    """สมัครสมาชิกแบบเดิม (คงไว้เพื่อความเข้ากันได้กับชุดทดสอบเดิม) — บังคับ role เป็น 'buyer' เสมอ"""
    return _create_account(username, email, password, full_name, phone, ROLE_BUYER)


# ==========================================
# สมัครสมาชิกแบบยืนยันอีเมล OTP + ที่อยู่เริ่มต้น
# ==========================================

def register_start(email: str, password: str, full_name: str, phone: str = "",
                   address: dict = None, username: str = None) -> dict:
    """
    ขั้นที่ 1 ของการสมัครสมาชิก:
    ตรวจข้อมูลผู้ซื้อ + เบอร์โทร (ถ้ากรอก) + ที่อยู่เริ่มต้น (ถ้ากรอก) -> เก็บลง pending_registrations -> ส่ง OTP 6 หลักไปอีเมล
    """
    email = (email or "").strip().lower()
    full_name = (full_name or "").strip()
    phone = (phone or "").strip()
    password = password or ""

    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")
    _check_new_password(password)
    if not full_name:
        raise ValueError("กรุณากรอกชื่อ-นามสกุล")
    if len(full_name) > 100:
        raise ValueError("ชื่อ-นามสกุลยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    if phone and not validators.is_valid_phone(phone):
        raise ValueError("กรุณากรอกเบอร์โทรศัพท์ 10 หลักที่ขึ้นต้นด้วย 0")

    existing = repo_users.get_by_email(email)
    if existing is not None:
        raise ValueError("อีเมลนี้สมัครสมาชิกแล้ว กรุณาเข้าสู่ระบบ")

    clean_username = _generate_unique_username(email, preferred=username)
    clean_addr = _clean_initial_address(address, full_name, phone)
    pwd_hash = hash_password(password)

    repo_otp.save_pending_registration(
        email=email,
        username=clean_username,
        full_name=full_name,
        phone=phone or None,
        password_hash=pwd_hash,
        address_json=json.dumps(clean_addr, ensure_ascii=False),
    )
    return otp_service.generate_and_send_otp(
        email,
        purpose="register",
        check_cooldown=True,
        recipient_name=full_name,
    )


def resend_register_otp(email: str) -> dict:
    """ส่งรหัส OTP ซ้ำสำหรับการสมัครสมาชิกที่ค้างอยู่"""
    email = (email or "").strip().lower()
    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")
    pending = repo_otp.get_pending_registration(email)
    if pending is None:
        raise ValueError("ไม่พบข้อมูลการสมัครที่รอยืนยัน กรุณากรอกข้อมูลสมัครใหม่")
    return otp_service.generate_and_send_otp(
        email,
        purpose="register",
        check_cooldown=True,
        recipient_name=pending["full_name"],
    )


def register_verify(email: str, otp_code: str) -> dict:
    """
    ขั้นที่ 2 ของการสมัครสมาชิก:
    ตรวจรหัส OTP 6 หลัก -> สร้างบัญชี buyer (email_verified=1) + ที่อยู่เริ่มต้น (is_default=1 ถ้ากรอกไว้) ใน transaction เดียว
    """
    email = (email or "").strip().lower()
    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")
    pending = repo_otp.get_pending_registration(email)
    if pending is None:
        raise ValueError("ไม่พบข้อมูลการสมัครที่รอยืนยัน กรุณาเริ่มสมัครใหม่")

    if repo_users.email_exists(email):
        repo_otp.delete_pending_registration(email)
        raise ValueError("อีเมลนี้สมัครสมาชิกแล้ว กรุณาเข้าสู่ระบบ")

    otp_service.verify_otp(email, "register", otp_code)
    with transaction() as conn:
        uname = _generate_unique_username(email, preferred=pending["username"], conn=conn)
        user_id = repo_users.create_user(
            username=uname,
            email=email,
            password_hash=pending["password_hash"],
            full_name=pending["full_name"],
            phone=pending["phone"],
            role=ROLE_BUYER,
            email_verified=1,
            conn=conn,
        )
        addr = json.loads(pending["address_json"] or "{}")
        if addr and any(addr.get(k) for k in ("address_line", "district", "province", "postcode")):
            repo_addresses.create(
                user_id=user_id,
                recipient=addr.get("recipient") or pending["full_name"],
                phone=addr.get("phone") or pending["phone"] or "0000000000",
                address_line=addr.get("address_line") or "-",
                district=addr.get("district") or "-",
                province=addr.get("province") or "-",
                postcode=addr.get("postcode") or "10000",
                is_default=True,
                conn=conn,
            )
        repo_otp.delete_pending_registration(email, conn=conn)
        created = repo_users.get_by_id(user_id, conn=conn)
    return _public_user(created)


# ==========================================
# ลืมรหัสผ่านผู้ซื้อด้วย OTP (D13 / E9)
# ==========================================

RESET_GENERIC_NOTICE = "หากอีเมลนี้มีอยู่ในระบบ เราได้ส่งรหัสยืนยัน 6 หลักไปที่อีเมลของคุณแล้ว"


def reset_start(email: str) -> dict:
    """
    ขอรหัส OTP สำหรับตั้งรหัสผ่านใหม่ของผู้ซื้อ:
    - ข้อความและโครงสร้างข้อมูลตอบกลับเหมือนกันทุกประการไม่ว่าอีเมลนั้นมีอยู่ในระบบหรือไม่ (ป้องกันการเดาบัญชี)
    """
    email = (email or "").strip().lower()
    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")

    masked = otp_service.mask_email(email)
    user = repo_users.get_by_email(email)
    if user and user["role"] == ROLE_BUYER and user["is_active"] and int(_col(user, "email_verified", 1)):
        otp_service.generate_and_send_otp(
            email,
            purpose="reset",
            check_cooldown=True,
            recipient_name=user["full_name"],
        )

    return {
        "email": email,
        "masked_email": masked,
        "expires_in_minutes": otp_service.OTP_EXPIRE_MINUTES,
        "cooldown_seconds": otp_service.RESEND_COOLDOWN_SECONDS,
        "message": f"ส่งรหัสไปที่ {masked} แล้ว ({RESET_GENERIC_NOTICE})",
        "mode": "smtp",
    }


def resend_reset_otp(email: str) -> dict:
    return reset_start(email)


def reset_verify(email: str, otp_code: str, new_password: str, confirm_password: str = None) -> bool:
    """ตรวจสอบ OTP สำหรับลืมรหัสผ่าน ตั้งรหัสผ่านใหม่ และยกเลิกเซสชันเดิมทั้งหมดของผู้ใช้"""
    email = (email or "").strip().lower()
    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")
    new_password = new_password or ""
    if confirm_password is not None and new_password != confirm_password:
        raise ValueError("รหัสผ่านใหม่และการยืนยันรหัสผ่านไม่ตรงกัน")
    _check_new_password(new_password)

    user = repo_users.get_by_email(email)
    if user is None or user["role"] != ROLE_BUYER or not user["is_active"] or not int(_col(user, "email_verified", 1)):
        otp_service.verify_otp(email, "reset", otp_code)
        raise ValueError("ไม่พบรหัส OTP ที่ใช้งานได้ กรุณากดขอรหัสใหม่")

    otp_service.verify_otp(email, "reset", otp_code)
    with transaction() as conn:
        repo_users.update_password(user["id"], hash_password(new_password), must_change=False, conn=conn)
        repo_sessions.delete_user_sessions(user["id"], conn=conn)
    return True


# ==========================================
# เข้าสู่ระบบ / ออกจากระบบ / เซสชันเครื่องร้าน
# ==========================================

_SESSION_FILE = "session_token.json"


def _session_file_path() -> Path:
    return Path(config.DATA_DIR) / _SESSION_FILE


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def login(identifier: str, password: str, remember: bool = False):
    """เข้าสู่ระบบ รับ identifier เป็นได้ทั้ง username และ email"""
    identifier = (identifier or "").strip()
    password = password or ""
    generic_error = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"

    if not identifier or not password:
        raise ValueError(generic_error)

    if "@" in identifier:
        user = repo_users.get_by_email(identifier.lower())
    else:
        user = repo_users.get_by_username(identifier)

    if not user:
        verify_password(password, _get_dummy_hash())
        raise ValueError(generic_error)

    if not verify_password(password, user["password_hash"]):
        raise ValueError(generic_error)

    if not user["is_active"]:
        raise ValueError("บัญชีนี้ถูกระงับการใช้งาน")

    if not int(_col(user, "email_verified", 1)):
        raise ValueError("บัญชีนี้ยังไม่ได้ยืนยันอีเมล กรุณายืนยันรหัส OTP ก่อนเข้าสู่ระบบ")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    days = 90 if (user["role"] in (ROLE_ADMIN, ROLE_OWNER) and remember) else 7
    expires_at = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    try:
        repo_users.touch_last_login(user["id"])
        repo_sessions.create_session(token_hash, user["id"], expires_at, remember=remember)
        if remember:
            _save_local_token(raw_token)
    except sqlite3.Error:
        pass

    public = _public_user(repo_users.get_by_id(user["id"]) or user)
    Session.login(public, session_token=raw_token)
    try:
        repo_users.set_online(public["id"], True)
    except sqlite3.Error:
        pass
    return public


def _save_local_token(raw_token: str) -> None:
    try:
        path = _session_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"token": raw_token}), encoding="utf-8")
    except OSError:
        pass


def _clear_local_token() -> None:
    try:
        _session_file_path().unlink(missing_ok=True)
    except OSError:
        pass


def restore_remembered_session() -> dict | None:
    """กู้คืนเซสชันที่ติ๊ก 'จำเครื่องนี้' ไว้บนคอมร้าน"""
    try:
        path = _session_file_path()
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_token = str(data.get("token") or "").strip()
        if not raw_token:
            return None
        token_hash = _hash_token(raw_token)
        row = repo_sessions.get_valid_session(token_hash)
        if row is None or not row["is_active"]:
            _clear_local_token()
            return None
        if row["remember"] and row["role"] in (ROLE_ADMIN, ROLE_OWNER):
            new_exp = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
            repo_sessions.touch_session(token_hash, new_expires_at=new_exp)
        user_row = repo_users.get_by_id(row["user_id"])
        if user_row is None:
            return None
        public = _public_user(user_row)
        Session.login(public, session_token=raw_token)
        repo_users.set_online(public["id"], True)
        return public
    except Exception:
        return None


def is_current_session_valid() -> bool:
    """ตรวจว่าเซสชันปัจจุบันยังไม่ถูกเตะออกหรือระงับบัญชี"""
    if not Session.is_authenticated():
        return False
    uid = Session.get_user_id()
    user = repo_users.get_by_id(uid)
    if user is None or not user["is_active"]:
        return False
    if Session.session_token:
        row = repo_sessions.get_valid_session(_hash_token(Session.session_token))
        if row is None:
            return False
    return True


def unlock_session(password: str) -> bool:
    """ปลดล็อกหน้าจอที่ล็อกชั่วคราวด้วยรหัสผ่านของผู้ใช้ที่ล็อกอินอยู่"""
    uid = Session.get_user_id()
    if uid is None:
        raise PermissionError("กรุณาเข้าสู่ระบบใหม่")
    user = repo_users.get_by_id(uid)
    if user is None or not user["is_active"]:
        logout()
        raise PermissionError("บัญชีไม่สามารถใช้งานได้ กรุณาเข้าสู่ระบบใหม่")
    if not verify_password(password or "", user["password_hash"]):
        raise ValueError("รหัสผ่านไม่ถูกต้อง")
    Session.unlock()
    return True


def logout():
    """ออกจากระบบ ล้างสถานะออนไลน์ ลบเซสชันที่จำไว้ และล้าง Session เสมอ"""
    user_id = Session.get_user_id()
    token = Session.session_token
    try:
        if user_id is not None:
            repo_users.set_online(user_id, False)
        if token:
            repo_sessions.delete_session(_hash_token(token))
    except sqlite3.Error:
        pass
    _clear_local_token()
    Session.logout()


def clear_all_online() -> int:
    """ล้างสถานะออนไลน์ทุกคน"""
    return repo_users.clear_all_online()


# ==========================================
# โปรไฟล์ / รหัสผ่าน / เปลี่ยนชื่อผู้ใช้ / เปลี่ยนอีเมลด้วย OTP (T11)
# ==========================================

def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    permissions.require_user(user_id)
    old_password = old_password or ""
    new_password = new_password or ""

    row = repo_users.get_by_id(user_id)
    if row is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    if not verify_password(old_password, row["password_hash"]):
        raise ValueError("รหัสผ่านเดิมไม่ถูกต้อง")

    _check_new_password(new_password)
    if new_password == old_password:
        raise ValueError("รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านเดิม")

    repo_users.update_password(user_id, hash_password(new_password), must_change=False)
    if Session.current_user is not None and Session.current_user.get("id") == user_id:
        Session.current_user["must_change_password"] = False
    return True


_PROFILE_PW_ATTEMPTS: dict[int, list[float]] = {}
MAX_PROFILE_PW_ATTEMPTS = 5
PROFILE_PW_WINDOW_SECONDS = 300


def reset_profile_password_attempts(user_id: int = None) -> None:
    if user_id is None:
        _PROFILE_PW_ATTEMPTS.clear()
    else:
        _PROFILE_PW_ATTEMPTS.pop(int(user_id), None)


def verify_user_current_password(user_id: int, current_password: str | None) -> None:
    """ตรวจสอบรหัสผ่านปัจจุบันของ user_id พร้อมจำกัดจำนวนครั้งที่เดาผิด (ป้องกัน brute-force)"""
    import time
    uid = int(user_id)
    now = time.time()
    recent = [t for t in _PROFILE_PW_ATTEMPTS.get(uid, []) if now - t < PROFILE_PW_WINDOW_SECONDS]
    _PROFILE_PW_ATTEMPTS[uid] = recent
    if len(recent) >= MAX_PROFILE_PW_ATTEMPTS:
        raise ValueError("ยืนยันรหัสผ่านปัจจุบันผิดเกิน 5 ครั้ง กรุณารอสักครู่แล้วลองใหม่อีกครั้ง")

    pw = str(current_password or "")
    if not pw:
        raise ValueError("กรุณากรอกรหัสผ่านปัจจุบันเพื่อยืนยันการแก้ไขโปรไฟล์")

    row = repo_users.get_by_id(uid)
    if row is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    if not verify_password(pw, row["password_hash"]):
        recent.append(now)
        _PROFILE_PW_ATTEMPTS[uid] = recent
        left = max(0, MAX_PROFILE_PW_ATTEMPTS - len(recent))
        if left == 0:
            raise ValueError("รหัสผ่านปัจจุบันไม่ถูกต้อง (ผิดครบ 5 ครั้ง กรุณารอสักครู่ก่อนลองใหม่)")
        raise ValueError(f"รหัสผ่านปัจจุบันไม่ถูกต้อง (ลองได้อีก {left} ครั้ง)")

    _PROFILE_PW_ATTEMPTS.pop(uid, None)


def validate_profile_fields(user_id: int, full_name: str, phone: str, username: str = None) -> dict:
    """ตรวจสอบความถูกต้องของข้อมูลโปรไฟล์ก่อนเปิดกล่องถามรหัสผ่าน"""
    permissions.require_user(user_id)
    full_name_clean = (full_name or "").strip()
    phone_clean = str(phone or "").strip().replace("-", "").replace(" ", "")

    if not full_name_clean:
        raise ValueError("กรุณากรอกชื่อ-นามสกุล")
    if len(full_name_clean) > 100:
        raise ValueError("ชื่อ-นามสกุลยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    if phone_clean and not validators.is_valid_phone(phone_clean):
        raise ValueError("รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (ต้องเป็นตัวเลข 10 หลักและขึ้นต้นด้วย 0)")

    clean_username = None
    if username is not None:
        clean_username = str(username or "").strip()
        if not validators.is_valid_username(clean_username) or not (3 <= len(clean_username) <= 30):
            raise ValueError("รูปแบบชื่อผู้ใช้ไม่ถูกต้อง (อนุญาตเฉพาะภาษาอังกฤษ ตัวเลข และ _ ความยาว 3-30 ตัวอักษร)")
        if repo_users.username_exists_other(clean_username, user_id):
            raise ValueError("ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว")

    return {
        "full_name": full_name_clean,
        "phone": phone_clean,
        "username": clean_username,
    }


def update_profile(
    user_id: int,
    full_name: str,
    phone: str,
    avatar_path=None,
    username: str = None,
    current_password: str = None,
    require_password: bool = False,
) -> dict:
    permissions.require_user(user_id)
    checked = validate_profile_fields(user_id, full_name, phone, username=username)
    full_name_clean = checked["full_name"]
    phone_clean = checked["phone"]
    clean_username = checked["username"]

    if require_password or current_password is not None:
        verify_user_current_password(user_id, current_password)

    with transaction() as conn:
        if not repo_users.update_profile(user_id, full_name_clean, phone_clean or None, avatar_path, conn=conn):
            raise ValueError("ไม่พบบัญชีผู้ใช้")
        if clean_username is not None:
            try:
                repo_users.update_username(user_id, clean_username, conn=conn)
            except sqlite3.IntegrityError:
                raise ValueError("ชื่อผู้ใช้นี้มีผู้ใช้งานแล้ว") from None

    updated = _public_user(repo_users.get_by_id(user_id))
    if Session.current_user is not None and Session.current_user.get("id") == user_id:
        Session.current_user["full_name"] = updated["full_name"]
        Session.current_user["phone"] = updated["phone"]
        Session.current_user["username"] = updated["username"]
        if avatar_path:
            Session.current_user["avatar_path"] = updated["avatar_path"]
    return updated


def update_username(user_id: int, new_username: str) -> dict:
    permissions.require_user(user_id)
    user = repo_users.get_by_id(user_id)
    if user is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    return update_profile(user_id, user["full_name"], user["phone"] or "", username=new_username)


def _hash_email_change_otp(user_id: int, new_email: str, code: str) -> str:
    return otp_service.hash_email_change_code(user_id, new_email, code)


def request_email_change_otp(user_id: int, new_email: str, check_cooldown: bool = True) -> dict:
    permissions.require_user(user_id)
    user = repo_users.get_by_id(user_id)
    if user is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    clean_email = str(new_email or "").strip().lower()
    if not validators.is_valid_email(clean_email):
        raise ValueError("รูปแบบอีเมลใหม่ไม่ถูกต้อง")
    if clean_email == str(user["email"] or "").strip().lower():
        raise ValueError("อีเมลใหม่ตรงกับอีเมลปัจจุบันอยู่แล้ว")
    if repo_users.email_exists_other(clean_email, user_id):
        raise ValueError("อีเมลนี้ถูกใช้งานในบัญชีอื่นแล้ว")

    sent_hour = repo_otp.count_recent_email_change_otps(user_id, 3600, new_email=clean_email)
    if sent_hour >= otp_service.MAX_SENDS_PER_HOUR:
        raise ValueError("ขอรหัส OTP เกินจำนวนครั้งที่กำหนด (สูงสุด 5 ครั้งต่อชั่วโมง) กรุณารอสักครู่")

    if check_cooldown:
        latest = repo_otp.get_latest_email_change_otp_any(user_id)
        if latest is not None:
            created_dt = parse_datetime(latest["created_at"])
            if created_dt is not None:
                elapsed = (datetime.now() - created_dt).total_seconds()
                if elapsed < otp_service.RESEND_COOLDOWN_SECONDS:
                    wait_sec = max(1, int(otp_service.RESEND_COOLDOWN_SECONDS - elapsed))
                    raise ValueError(f"กรุณารออีก {wait_sec} วินาทีก่อนขอรหัส OTP ใหม่")

    code = f"{secrets.randbelow(1_000_000):06d}"
    code_hash = _hash_email_change_otp(user_id, clean_email, code)
    expires_at = (datetime.now() + timedelta(minutes=otp_service.OTP_EXPIRE_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    otp_id = repo_otp.create_email_change_otp(user_id, clean_email, code_hash, expires_at)

    try:
        shop_name = settings_service.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
    except Exception:
        shop_name = "AI.HERE BADᴍᴛ-Zone"

    subject, text_body, html_body = otp_service.build_otp_email_content(
        purpose="email_change",
        code=code,
        shop_name=shop_name,
        recipient_name=user["full_name"],
        expires_in_minutes=otp_service.OTP_EXPIRE_MINUTES,
        expires_at=expires_at,
        target_email=clean_email,
    )

    try:
        send_res = email_service.send_mail(clean_email, subject, text_body, html=html_body)
    except Exception:
        repo_otp.delete_email_change_otp(otp_id)
        raise

    masked = otp_service.mask_email(clean_email)
    return {
        "email": clean_email,
        "masked_email": masked,
        "expires_in_minutes": otp_service.OTP_EXPIRE_MINUTES,
        "cooldown_seconds": otp_service.RESEND_COOLDOWN_SECONDS,
        "mode": send_res.get("mode", "smtp"),
        "message": f"ส่งรหัสไปที่ {masked} แล้ว",
    }


def confirm_email_change_with_otp(user_id: int, new_email: str, otp_code: str,
                                  current_password: str = None, require_password: bool = False) -> dict:
    permissions.require_user(user_id)
    if require_password or current_password is not None:
        verify_user_current_password(user_id, current_password)
    clean_email = str(new_email or "").strip().lower()
    code = str(otp_code or "").strip()
    if not validators.is_valid_email(clean_email):
        raise ValueError("รูปแบบอีเมลใหม่ไม่ถูกต้อง")
    if not code or len(code) != 6 or not code.isdigit():
        raise ValueError("กรุณากรอกรหัส OTP ตัวเลข 6 หลัก")
    if repo_users.email_exists_other(clean_email, user_id):
        raise ValueError("อีเมลนี้ถูกใช้งานในบัญชีอื่นแล้ว")

    row = repo_otp.get_latest_active_email_change_otp(user_id, clean_email)
    if row is None:
        raise ValueError("ไม่พบรหัส OTP สำหรับอีเมลใหม่นี้ กรุณากดขอรหัส OTP ใหม่")

    if int(row["attempts"] or 0) >= otp_service.MAX_OTP_ATTEMPTS:
        repo_otp.mark_email_change_used(row["id"])
        raise ValueError("กรอกรหัสผิดเกิน 5 ครั้ง รหัสนี้ถูกยกเลิกแล้ว กรุณาขอรหัส OTP ใหม่")

    expires_dt = parse_datetime(row["expires_at"])
    if expires_dt is None or expires_dt < datetime.now():
        repo_otp.mark_email_change_used(row["id"])
        raise ValueError("รหัส OTP หมดอายุแล้ว กรุณากดขอรหัสใหม่")

    expected_hash = _hash_email_change_otp(user_id, clean_email, code)
    if not hmac.compare_digest(expected_hash, str(row["code_hash"])):
        attempts = repo_otp.increment_email_change_attempts(row["id"])
        if attempts >= otp_service.MAX_OTP_ATTEMPTS:
            repo_otp.mark_email_change_used(row["id"])
            raise ValueError("กรอกรหัสผิดครบ 5 ครั้ง รหัสนี้ถูกยกเลิกแล้ว กรุณาขอรหัส OTP ใหม่")
        left = otp_service.MAX_OTP_ATTEMPTS - attempts
        raise ValueError(f"รหัส OTP ไม่ถูกต้อง (ลองได้อีก {left} ครั้ง)")

    with transaction() as conn:
        if not repo_otp.mark_email_change_used(row["id"], conn=conn):
            raise ValueError("รหัส OTP นี้ถูกใช้งานไปแล้ว กรุณาขอรหัสใหม่")
        try:
            repo_users.update_email(user_id, clean_email, email_verified=1, conn=conn)
        except sqlite3.IntegrityError:
            raise ValueError("อีเมลนี้ถูกใช้งานในบัญชีอื่นแล้ว") from None

    updated = _public_user(repo_users.get_by_id(user_id))
    if Session.current_user is not None and Session.current_user.get("id") == user_id:
        Session.current_user["email"] = updated["email"]
    return updated


# ==========================================
# จัดการบัญชี (เจ้าของร้านเท่านั้น — action user.manage)
# ==========================================

def create_staff(username: str, email: str, password: str, full_name: str, phone: str,
                 role: str = ROLE_ADMIN) -> dict:
    permissions.require(permissions.USER_MANAGE)
    if role != ROLE_ADMIN:
        raise ValueError("สร้างได้เฉพาะบัญชีแอดมินเท่านั้น")
    created = _create_account(username, email, password, full_name, phone, ROLE_ADMIN)
    audit_service.log("staff.create", "user", created["id"], {"username": created["username"], "email": created["email"]})
    return created


def set_user_active(user_id: int, active: bool) -> dict:
    permissions.require(permissions.USER_MANAGE)
    target = repo_users.get_by_id(user_id)
    if target is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    if not active:
        if user_id == Session.get_user_id():
            raise ValueError("ไม่สามารถระงับบัญชีของตัวเองได้")
        if target["role"] == ROLE_OWNER:
            raise ValueError("ไม่สามารถระงับบัญชีเจ้าของร้านได้")
    repo_users.set_active(user_id, bool(active))
    if not active:
        repo_sessions.delete_user_sessions(user_id)
    audit_service.log("user.set_active", "user", user_id, {"is_active": bool(active)})
    return _public_user(repo_users.get_by_id(user_id))


def list_users(role=None, search=None) -> list[dict]:
    permissions.require(permissions.USER_MANAGE)
    return [dict(r) for r in repo_users.list_users(role=role, search=search)]


def start_registration_with_otp(
    username: str, email: str, password: str, full_name: str, phone: str = "",
    address_line: str = "", district: str = "", province: str = "", postcode: str = "",
) -> dict:
    addr = {
        "address_line": (address_line or "").strip() or "99/9 ถนนสุขุมวิท",
        "district": (district or "").strip() or "คลองเตย",
        "province": (province or "").strip() or "กรุงเทพมหานคร",
        "postcode": (postcode or "").strip() or "10110",
    }
    res = register_start(email=email, password=password, full_name=full_name, phone=phone, address=addr, username=username)
    return {
        **res,
        "otp_required": True,
        "message": res.get("message") or f"ส่งรหัสไปที่ {res.get('masked_email') or otp_service.mask_email(email)} แล้ว",
    }


def complete_registration_with_otp(email: str, otp_code: str) -> dict:
    return register_verify(email, otp_code)


def request_password_reset_otp(email: str) -> dict:
    return reset_start(email)


def reset_password_with_otp(email: str, otp_code: str, new_password: str) -> dict:
    reset_verify(email, otp_code, new_password, new_password)
    return {"reset": True, "message": "ตั้งรหัสผ่านใหม่เรียบร้อยแล้ว กรุณาเข้าสู่ระบบ"}


def verify_active_session_password(password: str) -> tuple[bool, str]:
    try:
        ok = unlock_session(password)
        return (True, "ปลดล็อกสำเร็จ") if ok else (False, "รหัสผ่านไม่ถูกต้อง")
    except Exception as exc:
        return False, str(exc)
