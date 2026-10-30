"""
services/email_service.py
บริการส่งอีเมลผ่าน SMTP (ตั้งค่าผ่าน .env) สำหรับ:
- รหัสยืนยัน OTP ตอนสมัครสมาชิก ลืมรหัสผ่าน และเปลี่ยนอีเมลในโปรไฟล์
- ใบเสร็จอิเล็กทรอนิกส์ (ข้อความสรุป + แนบไฟล์ PDF)
- แจ้งสถานะจัดส่งพร้อมเลขพัสดุ
- สรุปสินค้าสต็อกต่ำรายวันถึงเจ้าของร้าน
- อีเมลด่วนจากแอดมินถึงเจ้าของร้าน (พร้อมตั้ง Reply-To เป็นอีเมลแอดมิน)

กติกาความปลอดภัย:
- ห้าม hardcode รหัสผ่าน SMTP ในโค้ด
- ห้ามบันทึกรหัส OTP หรือรหัสผ่านลงใน log หรือตาราง email_outbox
"""
import mimetypes
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

import config
from services import settings_service
from utils import validators


def _smtp_password() -> str:
    return (getattr(config, "SMTP_PASSWORD", "") or getattr(config, "SMTP_PASS", "") or "").strip()


def is_smtp_configured() -> bool:
    """ตรวจสอบว่าตั้งค่า SMTP_HOST, SMTP_USER และ SMTP_PASSWORD (หรือ SMTP_PASS) ใน .env พร้อมส่งจริงหรือไม่"""
    return bool(config.SMTP_HOST and config.SMTP_USER and _smtp_password())


def _build_from_header(shop_name: str) -> str:
    explicit_from = (getattr(config, "SMTP_FROM_EXPLICIT", "") or "").strip()
    from_name = (getattr(config, "SMTP_FROM_NAME", "") or "").strip() or shop_name
    sender_addr = (getattr(config, "SMTP_USER", "") or getattr(config, "OWNER_EMAIL", "") or "noreply@badmintonshop.local").strip()

    if explicit_from:
        if "<" in explicit_from and ">" in explicit_from:
            return explicit_from
        return f"{from_name} <{explicit_from}>"
    return f"{from_name} <{sender_addr}>"


def _send_via_smtp(msg: EmailMessage) -> None:
    host = str(config.SMTP_HOST).strip()
    port = int(getattr(config, "SMTP_PORT", 587) or 587)
    user = str(config.SMTP_USER).strip()
    password = _smtp_password()

    if port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, timeout=15, context=context) as server:
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)


def send_mail(to_email: str, subject: str, text: str, html: str = None,
              attachments=(), reply_to: str = None) -> dict:
    """
    ส่งอีเมลไปยังผู้รับผ่าน SMTP จริง
    คืน dict {"sent": True, "mode": "smtp"}
    โยน ValueError (ภาษาไทยที่เข้าใจง่าย ไม่เปิดเผยข้อมูลภายในหรือรหัสผ่าน SMTP) เมื่อส่งไม่สำเร็จหรือยังไม่ได้ตั้งค่า SMTP
    """
    to_email = (to_email or "").strip().lower()
    if not validators.is_valid_email(to_email):
        raise ValueError("รูปแบบอีเมลผู้รับไม่ถูกต้อง")

    try:
        shop_name = settings_service.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
    except Exception:
        shop_name = "AI.HERE BADᴍᴛ-Zone"

    subject = (subject or "").strip() or f"แจ้งเตือนจาก {shop_name}"
    text = str(text or "")

    from_header = _build_from_header(shop_name)

    msg = EmailMessage()
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Subject"] = subject
    if reply_to and validators.is_valid_email(reply_to.strip()):
        msg["Reply-To"] = reply_to.strip()

    msg.set_content(text)
    if html:
        msg.add_alternative(str(html), subtype="html")

    for att in attachments or ():
        if not att:
            continue
        p = Path(att)
        if not p.is_file():
            continue
        ctype, _ = mimetypes.guess_type(str(p))
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)

    if not is_smtp_configured():
        raise ValueError("ไม่สามารถส่งอีเมลได้ในขณะนี้ เนื่องจากระบบยังไม่ได้ตั้งค่าอีเมลผู้ส่ง (SMTP)")

    try:
        _send_via_smtp(msg)
        return {"sent": True, "mode": "smtp"}
    except Exception:
        raise ValueError("ส่งอีเมลไม่สำเร็จ กรุณาตรวจสอบอีเมลหรือลองใหม่อีกครั้งในภายหลัง") from None
