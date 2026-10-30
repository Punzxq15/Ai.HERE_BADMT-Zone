"""
services/contact_service.py
จัดการข้อมูลติดต่อเจ้าของร้านสำหรับแอดมิน (ADM-1):
- ดึงข้อมูลติดต่อเจ้าของร้าน (เบอร์โทร, อีเมล, Facebook ชื่อ/ลิงก์, LINE ชื่อ, Instagram ชื่อ/ลิงก์)
- ส่งอีเมลด่วนจากแอดมินถึงเจ้าของร้าน (จำกัดไม่เกิน 5 ครั้ง/ชั่วโมง, ตั้ง Reply-To เป็นอีเมลแอดมิน)
"""
import config
from core import permissions
from core.constants import ROLE_ADMIN, ROLE_OWNER
from core.session import Session
from database import repo_outbox, repo_users
from services import email_service, notification_service, settings_service
from utils import validators

MAX_URGENT_PER_HOUR = 5
MAX_SUBJECT_LEN = 150
MAX_MESSAGE_LEN = 2000


def get_owner_contact_info() -> dict:
    """
    ข้อมูลติดต่อเจ้าของร้าน (ใช้แสดงในหน้าติดต่อเจ้าของร้านของแอดมิน และหน้าพนักงานลืมรหัสผ่าน)
    """
    info = settings_service.get_contact_info()
    owner_row = repo_users.get_owner()
    owner_email = (
        info.get("shop_email")
        or config.OWNER_EMAIL
        or (owner_row["email"] if owner_row else "owner@shop.com")
    )
    owner_phone = info.get("shop_phone") or (owner_row["phone"] if owner_row else "0811111111")
    owner_name = owner_row["full_name"] if owner_row else "เจ้าของร้าน"
    return {
        **info,
        "owner_name": owner_name,
        "owner_email": owner_email,
        "owner_phone": owner_phone,
        "phone": owner_phone,
        "email": owner_email,
        "line_id": info.get("line_name") or "",
        "address": info.get("shop_address") or "",
        "open_hours": info.get("shop_hours") or "",
    }


def send_urgent_to_owner(subject: str, message: str) -> dict:
    """
    แอดมิน (หรือเจ้าของร้าน) ส่งข้อความ/อีเมลด่วนถึงอีเมลเจ้าของร้าน:
    - ตรวจสอบสิทธิ์ต้องล็อกอินเป็น admin หรือ owner
    - จำกัดอัตราไม่เกิน 5 ครั้งต่อชั่วโมงต่อคน
    - ตั้งผู้ส่งเป็นระบบ SMTP ของร้าน และตั้ง Reply-To เป็นอีเมลของแอดมินผู้ส่ง (ไม่ปลอมแปลง sender)
    - บันทึกลงตาราง staff_messages และแจ้งเตือนเจ้าของร้านในแอปด้วย
    """
    staff_id = permissions.require_login()
    role = Session.get_role()
    if role not in (ROLE_ADMIN, ROLE_OWNER):
        raise PermissionError("เฉพาะแอดมินหรือเจ้าของร้านเท่านั้นที่ส่งข้อความถึงเจ้าของร้านได้")

    subject = (subject or "").strip() or "ข้อความด่วนจากแอดมินร้าน"
    message = (message or "").strip()
    if not message:
        raise ValueError("กรุณากรอกข้อความที่ต้องการส่งถึงเจ้าของร้าน")
    if len(subject) > MAX_SUBJECT_LEN:
        raise ValueError(f"หัวข้อเรื่องยาวเกินไป (ไม่เกิน {MAX_SUBJECT_LEN} ตัวอักษร)")
    if len(message) > MAX_MESSAGE_LEN:
        raise ValueError(f"ข้อความยาวเกินไป (ไม่เกิน {MAX_MESSAGE_LEN} ตัวอักษร)")

    recent = repo_outbox.count_recent_staff_messages(staff_id, within_seconds=3600)
    if recent >= MAX_URGENT_PER_HOUR:
        raise ValueError(f"ส่งข้อความด่วนเกินกำหนด (สูงสุด {MAX_URGENT_PER_HOUR} ครั้งต่อชั่วโมง)")

    admin_user = repo_users.get_by_id(staff_id)
    admin_name = (admin_user["full_name"] if admin_user else None) or Session.current_user.get("full_name") or "แอดมิน"
    admin_email = (admin_user["email"] if admin_user else None) or ""

    contact = get_owner_contact_info()
    target_email = (contact.get("owner_email") or config.OWNER_EMAIL or "").strip().lower()
    if not validators.is_valid_email(target_email):
        raise ValueError("ยังไม่ได้ตั้งค่าอีเมลเจ้าของร้านที่ถูกต้อง")

    full_subject = f"[ข้อความด่วนจากแอดมิน {admin_name}] {subject}"
    body_text = (
        f"เรียน เจ้าของร้าน {contact.get('shop_name', 'AI.HERE BADᴍᴛ-Zone')},\n\n"
        f"มีข้อความด่วนจากแอดมิน: {admin_name} ({admin_email or '-'})\n"
        f"หัวข้อ: {subject}\n\n"
        f"รายละเอียดข้อความ:\n{message}\n"
    )

    outbox_id = repo_outbox.create_outbox(
        kind="staff_urgent",
        to_email=target_email,
        subject=full_subject,
        body_text=body_text,
    )

    sent_ok = False
    mode = "queued"
    error_detail = None
    try:
        res = email_service.send_mail(
            to_email=target_email,
            subject=full_subject,
            text=body_text,
            reply_to=admin_email if validators.is_valid_email(admin_email) else None,
        )
        sent_ok = bool(res.get("sent"))
        mode = res.get("mode", "smtp")
        repo_outbox.mark_sent(outbox_id)
    except Exception as exc:
        error_detail = str(exc)
        repo_outbox.mark_failed(outbox_id, error_detail)

    msg_id = repo_outbox.create_staff_message(staff_id, subject, message, sent_ok=sent_ok)

    owner_row = repo_users.get_owner()
    if owner_row is not None:
        notification_service.notify(
            owner_row["id"],
            f"ข้อความด่วนจาก {admin_name}",
            f"{subject}: {message[:200]}",
        )

    if not sent_ok and email_service.is_smtp_configured() and error_detail:
        raise ValueError(error_detail)

    return {
        "id": msg_id,
        "to_email": target_email,
        "subject": subject,
        "sent_ok": sent_ok,
        "mode": mode,
    }


def list_staff_messages(limit: int = 50) -> list[dict]:
    """ดูประวัติข้อความด่วนที่ส่งถึงเจ้าของร้าน (แอดมินและเจ้าของร้านดูได้)"""
    permissions.require(permissions.DASHBOARD_VIEW)
    return [dict(r) for r in repo_outbox.list_staff_messages(limit=limit)]


def send_urgent_email_to_owner(subject: str, message: str) -> dict:
    res = send_urgent_to_owner(subject, message)
    return {
        **res,
        "status": "sent" if res.get("sent_ok") else "queued",
        "message": "ส่งข้อความด่วนถึงเจ้าของร้านเรียบร้อยแล้ว",
    }


def list_staff_messages_for_owner(limit: int = 50) -> list[dict]:
    return list_staff_messages(limit=limit)


def update_owner_contact_info(payload: dict) -> dict:
    permissions.require(permissions.SETTINGS_MANAGE)
    mapped = {}
    key_map = {
        "owner_phone": "shop_phone",
        "shop_phone": "shop_phone",
        "owner_email": "shop_email",
        "shop_email": "shop_email",
        "shop_address": "shop_address",
        "shop_open_hours": "shop_hours",
        "shop_hours": "shop_hours",
        "line_id": "line_name",
        "line_name": "line_name",
        "facebook_name": "facebook_name",
        "facebook_url": "facebook_url",
        "instagram_name": "instagram_name",
        "instagram_url": "instagram_url",
        "tiktok_name": "tiktok_name",
        "tiktok_url": "tiktok_url",
    }
    for k, target_k in key_map.items():
        if k in payload:
            mapped[target_k] = payload[k]
    settings_service.update_contact_info(mapped)
    return get_owner_contact_info()
