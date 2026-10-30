"""
services/otp_service.py
จัดการรหัสยืนยัน OTP 6 หลักทางอีเมล (สำหรับสมัครสมาชิก 'register', ลืมรหัสผ่าน 'reset', และเปลี่ยนอีเมล 'email_change'):
- สร้างรหัส 6 หลักด้วยโมดูล secrets
- เก็บเฉพาะค่าแฮชแบบ HMAC-SHA256 (ใช้ OTP_SECRET ผสมกับ email + purpose + user_context) ในฐานข้อมูล ไม่เก็บรหัสจริง
- อายุรหัส 10 นาที
- กรอกผิดได้สูงสุด 5 ครั้งต่อรหัส (เกิน 5 ครั้งรหัสนั้นถูกยกเลิก ต้องขอใหม่)
- จำกัดการขอส่งซ้ำ: ต้องเว้นอย่างน้อย 60 วินาที และไม่เกิน 5 ครั้งต่อชั่วโมงต่ออีเมล
- จำกัดอัตราการเรียก API ต่อ IP (ไม่เกิน 10 ครั้งต่อ 10 นาทีต่อ IP)
- สร้างอีเมล Multipart (Plain text + HTML ตาราง inline CSS ธีมสีเหลือง-ดำ-ขาว สองภาษา ไทย/อังกฤษ พร้อม html.escape)
"""
import hashlib
import hmac
import html
import secrets
import threading
import time
from datetime import datetime, timedelta

import config
from database import repo_otp
from services import email_service, settings_service
from utils import validators
from utils.formatters import parse_datetime

OTP_EXPIRE_MINUTES = 10
MAX_OTP_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
MAX_SENDS_PER_HOUR = 5
VALID_PURPOSES = ("register", "reset")
ALL_TEMPLATE_PURPOSES = ("register", "reset", "email_change")

# ---------- การจำกัดอัตราต่อ IP (In-memory Rate Limiter สำหรับ OTP endpoints) ----------
OTP_IP_RATE_LIMIT_MAX = 10
OTP_IP_RATE_LIMIT_WINDOW_SECONDS = 600  # 10 นาที
_IP_RATE_BUCKETS: dict[str, list[float]] = {}
_IP_RATE_LOCK = threading.Lock()


class OtpRateLimitError(ValueError):
    """โยนเมื่อ IP เดียวกันส่งคำขอเกี่ยวกับ OTP เกินอัตราที่กำหนด (แปลงเป็น HTTP 429 ที่ชั้นเซิร์ฟเวอร์)"""
    status_code = 429


def reset_ip_rate_limits() -> None:
    """ล้างข้อมูลจำกัดอัตราต่อ IP (ใช้ในชุดทดสอบ)"""
    with _IP_RATE_LOCK:
        _IP_RATE_BUCKETS.clear()


def check_ip_rate_limit(ip: str, limit: int = OTP_IP_RATE_LIMIT_MAX,
                        window_seconds: int = OTP_IP_RATE_LIMIT_WINDOW_SECONDS) -> None:
    """
    ตรวจสอบและบันทึกการเรียกใช้งาน endpoint ของ OTP ต่อ IP:
    หากเกิน `limit` ครั้งภายใน `window_seconds` วินาที จะโยน OtpRateLimitError (HTTP 429) พร้อมข้อความภาษาไทย
    """
    key = (ip or "unknown").strip() or "unknown"
    now = time.monotonic()
    cutoff = now - float(window_seconds)
    with _IP_RATE_LOCK:
        timestamps = [t for t in _IP_RATE_BUCKETS.get(key, []) if t > cutoff]
        if len(timestamps) >= int(limit):
            _IP_RATE_BUCKETS[key] = timestamps
            raise OtpRateLimitError(
                "มีการส่งคำขอรหัส OTP จากอุปกรณ์ของคุณบ่อยเกินไป (สูงสุด 10 ครั้งต่อ 10 นาที) กรุณารอสักครู่แล้วลองใหม่อีกครั้ง"
            )
        timestamps.append(now)
        _IP_RATE_BUCKETS[key] = timestamps


def _get_otp_secret_bytes() -> bytes:
    secret = (getattr(config, "OTP_SECRET", "") or "").strip()
    if not secret:
        secret = "fallback-ephemeral-otp-secret-key-badmt-zone"
    return secret.encode("utf-8")


def _hash_code(email: str, purpose: str, code: str, user_context: str = "") -> str:
    """
    คำนวณ HMAC-SHA256 ของรหัส OTP โดยใช้ OTP_SECRET ผสมกับ email + purpose + user_context
    ทำให้รหัสของ purpose หนึ่งไม่สามารถใช้ข้าม purpose หรือข้ามบัญชีผู้ใช้ได้
    """
    clean_email = (email or "").strip().lower()
    clean_purpose = (purpose or "").strip().lower()
    clean_ctx = str(user_context if user_context is not None else clean_email).strip().lower()
    clean_code = (code or "").strip()
    msg = f"v2:{clean_purpose}:{clean_email}:{clean_ctx}:{clean_code}".encode("utf-8")
    return hmac.new(_get_otp_secret_bytes(), msg, hashlib.sha256).hexdigest()


def hash_email_change_code(user_id: int, new_email: str, code: str) -> str:
    """คำนวณ HMAC-SHA256 สำหรับการยืนยันเปลี่ยนอีเมลในโปรไฟล์ ผูกกับ user_id และ new_email"""
    return _hash_code(
        email=new_email,
        purpose="email_change",
        code=code,
        user_context=f"uid:{int(user_id)}",
    )


def mask_email(email: str) -> str:
    """ซ่อนอีเมลบางส่วน เช่น 'buyer@shop.com' -> 'bu***@shop.com'"""
    email = (email or "").strip().lower()
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked = local[:1] + "***"
    else:
        masked = local[:2] + "***"
    return f"{masked}@{domain}"


# ---------- เทมเพลตอีเมล OTP แบบสองภาษา (Plain Text + HTML ตาราง inline CSS) ----------

_PURPOSE_META = {
    "register": {
        "th_action": "ยืนยันการสมัครสมาชิก",
        "en_action": "Account Registration Verification",
        "th_subject": "รหัส OTP ยืนยันการสมัครสมาชิก",
        "en_subject": "Your verification code",
        "th_desc": "กรุณาใช้รหัสยืนยัน (OTP) 6 หลักด้านล่างเพื่อยืนยันอีเมลสำหรับการสมัครสมาชิกของคุณ",
        "en_desc": "Please use the 6-digit verification code below to complete your account registration.",
    },
    "reset": {
        "th_action": "ตั้งรหัสผ่านใหม่",
        "en_action": "Password Reset Verification",
        "th_subject": "รหัส OTP สำหรับตั้งรหัสผ่านใหม่",
        "en_subject": "Password reset verification code",
        "th_desc": "กรุณาใช้รหัสยืนยัน (OTP) 6 หลักด้านล่างเพื่อดำเนินการตั้งรหัสผ่านใหม่สำหรับบัญชีของคุณ",
        "en_desc": "Please use the 6-digit verification code below to reset your account password.",
    },
    "email_change": {
        "th_action": "ยืนยันการเปลี่ยนอีเมล",
        "en_action": "Email Change Verification",
        "th_subject": "รหัส OTP ยืนยันการเปลี่ยนอีเมล",
        "en_subject": "Email change verification code",
        "th_desc": "กรุณาใช้รหัสยืนยัน (OTP) 6 หลักด้านล่างเพื่อยืนยันการเปลี่ยนอีเมลใหม่ของบัญชีคุณ",
        "en_desc": "Please use the 6-digit verification code below to confirm your new email address.",
    },
}


def build_otp_email_content(
    purpose: str,
    code: str,
    shop_name: str = None,
    recipient_name: str = None,
    expires_in_minutes: int = OTP_EXPIRE_MINUTES,
    expires_at: str = None,
    target_email: str = None,
) -> tuple[str, str, str]:
    """
    สร้างเนื้อหาอีเมล OTP แบบสองภาษา (ไทยเป็นหลักด้านบน + อังกฤษเป็นรองด้านล่าง)
    คืนค่า (subject, plain_text, html_body)
    - ใช้โครงสร้างตาราง (<table>) พร้อม inline CSS ล้วน ไม่ใช้รูปภาพภายนอกหรือ JavaScript
    - ธีมสี เหลือง (#FFD600) ดำ (#141619) ขาว (#FFFFFF)
    - ข้อมูลทุกส่วนที่แทรกลง HTML ผ่าน html.escape() ทุกครั้งเพื่อป้องกัน HTML/XSS injection
    """
    if purpose not in _PURPOSE_META:
        raise ValueError("ประเภทของเทมเพลตอีเมล OTP ไม่ถูกต้อง")

    meta = _PURPOSE_META[purpose]
    raw_shop_name = (shop_name or "").strip()
    if not raw_shop_name:
        try:
            raw_shop_name = settings_service.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
        except Exception:
            raw_shop_name = "AI.HERE BADᴍᴛ-Zone"

    clean_code = str(code or "").strip()
    exp_mins = int(expires_in_minutes or OTP_EXPIRE_MINUTES)
    raw_recipient = (recipient_name or "").strip()
    raw_target_email = (target_email or "").strip().lower()
    raw_expires_at = (expires_at or "").strip()

    # หัวเรื่องสองภาษา (ตัดขึ้นบรรทัดใหม่ป้องกัน header injection)
    safe_subject_shop = raw_shop_name.replace("\r", " ").replace("\n", " ").strip()
    subject = f"[{safe_subject_shop}] {meta['th_subject']} | {meta['en_subject']}"

    greeting_th = f"สวัสดีคุณ {raw_recipient}," if raw_recipient else "สวัสดีครับ / ค่ะ,"
    greeting_en = f"Hello {raw_recipient}," if raw_recipient else "Hello,"
    target_line_th = f"สำหรับอีเมล: {raw_target_email}\n" if raw_target_email else ""
    target_line_en = f"Target email: {raw_target_email}\n" if raw_target_email else ""
    exp_detail_th = f" (หมดอายุเวลา {raw_expires_at})" if raw_expires_at else ""
    exp_detail_en = f" (expires at {raw_expires_at})" if raw_expires_at else ""

    plain_text = (
        f"{greeting_th}\n\n"
        f"รายการ: {meta['th_action']} ({raw_shop_name})\n"
        f"{target_line_th}"
        f"{meta['th_desc']}\n\n"
        f"รหัส OTP ของคุณคือ: {clean_code}\n\n"
        f"อายุรหัส: รหัสนี้มีอายุการใช้งาน {exp_mins} นาที{exp_detail_th}\n"
        f"คำเตือนความปลอดภัย: อย่าบอกรหัสนี้กับใคร ทางร้านจะไม่ขอรหัสจากคุณทางโทรศัพท์หรือแชท\n"
        f"หากคุณไม่ได้ทำรายการนี้ กรุณาเพิกเฉยต่ออีเมลฉบับนี้\n\n"
        f"------------------------------------------------------------\n\n"
        f"{greeting_en}\n\n"
        f"Action: {meta['en_action']} ({raw_shop_name})\n"
        f"{target_line_en}"
        f"{meta['en_desc']}\n\n"
        f"Your verification code (OTP) is: {clean_code}\n\n"
        f"Validity: This code is valid for {exp_mins} minutes{exp_detail_en}.\n"
        f"Security notice: Never share this code with anyone. Our staff will never ask for your OTP via phone or chat.\n"
        f"If you did not request this code, please ignore this email.\n"
    )

    # Escape ข้อมูลไดนามิกทุกตัวก่อนแทรกลง HTML
    esc_shop = html.escape(raw_shop_name, quote=True)
    esc_code = html.escape(clean_code, quote=True)
    esc_greeting_th = html.escape(greeting_th, quote=True)
    esc_greeting_en = html.escape(greeting_en, quote=True)
    esc_action_th = html.escape(meta["th_action"], quote=True)
    esc_action_en = html.escape(meta["en_action"], quote=True)
    esc_desc_th = html.escape(meta["th_desc"], quote=True)
    esc_desc_en = html.escape(meta["en_desc"], quote=True)
    esc_exp_mins = html.escape(str(exp_mins), quote=True)
    esc_exp_at = html.escape(raw_expires_at, quote=True)
    esc_target_email = html.escape(raw_target_email, quote=True)

    target_html_th = (
        f'<div style="font-size:13px;color:#4B5563;margin-top:4px;">อีเมลที่ทำรายการ: <strong style="color:#141619;">{esc_target_email}</strong></div>'
        if esc_target_email else ""
    )
    target_html_en = (
        f'<div style="font-size:12px;color:#6B7280;margin-top:2px;">Email: <strong style="color:#374151;">{esc_target_email}</strong></div>'
        if esc_target_email else ""
    )
    exp_at_html_th = f" (หมดอายุเวลา {esc_exp_at})" if esc_exp_at else ""
    exp_at_html_en = f" (expires at {esc_exp_at})" if esc_exp_at else ""

    html_body = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc_shop} - {esc_action_th}</title>
</head>
<body style="margin:0;padding:0;background-color:#F3F4F6;font-family:'Kanit','Segoe UI',Tahoma,Arial,sans-serif;color:#141619;-webkit-text-size-adjust:100%;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F3F4F6;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;background-color:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
          <!-- Header พื้นดำ ตัวอักษรชื่อร้านสีเหลืองแบดมินตัน #FFD600 -->
          <tr>
            <td align="center" style="background-color:#141619;padding:22px 24px;border-bottom:4px solid #FFD600;">
              <div style="font-size:22px;font-weight:800;color:#FFD600;letter-spacing:0.5px;line-height:1.3;">{esc_shop}</div>
              <div style="font-size:13px;color:#FFFFFF;margin-top:4px;font-weight:500;">{esc_action_th} | {esc_action_en}</div>
            </td>
          </tr>
          <!-- เนื้อหาหลักภาษาไทย (ด้านบน) -->
          <tr>
            <td style="padding:28px 28px 16px 28px;background-color:#FFFFFF;">
              <div style="font-size:16px;font-weight:700;color:#141619;margin-bottom:8px;">{esc_greeting_th}</div>
              <div style="display:inline-block;background-color:#141619;color:#FFD600;font-size:12px;font-weight:700;padding:4px 10px;border-radius:4px;margin-bottom:10px;">รายการ: {esc_action_th}</div>
              {target_html_th}
              <p style="font-size:14px;line-height:1.6;color:#1F2937;margin:10px 0 18px 0;">{esc_desc_th}</p>

              <!-- กล่องแสดงรหัส OTP พื้นเหลือง ตัวเลขดำขนาดใหญ่ตัวหนา เว้นระยะตัวอักษรชัด -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 18px 0;">
                <tr>
                  <td align="center" style="background-color:#FFD600;border:2px solid #141619;border-radius:10px;padding:18px 16px;">
                    <div style="font-size:12px;font-weight:700;color:#141619;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">รหัสยืนยันของคุณ / VERIFICATION CODE</div>
                    <div style="font-family:'Arimo','Courier New',monospace;font-size:34px;font-weight:800;color:#141619;letter-spacing:10px;line-height:1.2;">{esc_code}</div>
                  </td>
                </tr>
              </table>

              <p style="font-size:13px;line-height:1.6;color:#141619;margin:0 0 10px 0;">
                <strong>อายุรหัส:</strong> รหัสนี้มีอายุการใช้งาน <strong>{esc_exp_mins} นาที</strong>{exp_at_html_th}
              </p>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#FFFBEB;border-left:4px solid #FFD600;padding:10px 12px;margin:12px 0;">
                <tr>
                  <td style="font-size:13px;line-height:1.5;color:#141619;">
                    <strong>คำเตือนความปลอดภัย:</strong> อย่าบอกรหัสนี้กับใคร ทางร้านจะไม่ขอรหัสจากคุณทางโทรศัพท์หรือแชท<br>
                    <span style="color:#4B5563;">หากคุณไม่ได้ทำรายการนี้ กรุณาเพิกเฉยต่ออีเมลฉบับนี้</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- เส้นคั่นระหว่างภาษาไทยและภาษาอังกฤษ -->
          <tr>
            <td style="padding:0 28px;background-color:#FFFFFF;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr><td style="border-top:1px solid #E5E7EB;font-size:1px;line-height:1px;">&nbsp;</td></tr>
              </table>
            </td>
          </tr>
          <!-- เนื้อหารองภาษาอังกฤษ (ด้านล่าง ตัวเล็กกว่า) -->
          <tr>
            <td style="padding:16px 28px 24px 28px;background-color:#FFFFFF;color:#4B5563;font-size:12px;line-height:1.55;">
              <div style="font-weight:700;color:#1F2937;margin-bottom:4px;">{esc_greeting_en} ({esc_action_en})</div>
              {target_html_en}
              <p style="margin:6px 0;">{esc_desc_en}</p>
              <p style="margin:6px 0;"><strong>Validity:</strong> This OTP code is valid for <strong>{esc_exp_mins} minutes</strong>{exp_at_html_en}.</p>
              <p style="margin:6px 0;color:#374151;"><strong>Security Warning:</strong> Never share this code with anyone. Our store will never ask for your OTP via phone or chat. If you did not request this action, please ignore this email.</p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td align="center" style="background-color:#141619;padding:12px 20px;color:#FFFFFF;font-size:11px;">
              &copy; {esc_shop} — ระบบส่งรหัสยืนยันอัตโนมัติ กรุณาอย่าตอบกลับอีเมลนี้
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return subject, plain_text, html_body


def generate_and_send_otp(email: str, purpose: str = "register", check_cooldown: bool = True,
                          recipient_name: str = None) -> dict:
    """
    สร้างรหัส OTP 6 หลัก บันทึกเฉพาะค่าแฮช (HMAC-SHA256) ลงฐานข้อมูล และส่งไปทางอีเมลจริง
    - ยกเลิกรหัสเก่าที่ยังไม่ใช้ของ (email, purpose) เดียวกันทันที
    - หากส่งอีเมลไม่สำเร็จหรือ SMTP ยังไม่ตั้งค่า จะลบแถว OTP ที่เพิ่งสร้างออกทันทีเพื่อไม่ให้มีรหัสค้างในฐานข้อมูล
    - คืน dict {"email", "masked_email", "expires_in_minutes", "mode"} (ไม่มีการคืนรหัส OTP ใน response เด็ดขาด)
    """
    email = (email or "").strip().lower()
    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")
    if purpose not in VALID_PURPOSES:
        raise ValueError("ประเภทการขอรหัส OTP ไม่ถูกต้อง")

    # ตรวจอัตราการส่งใน 1 ชั่วโมง
    sent_hour = repo_otp.count_recent_otps(email, purpose, 3600)
    if sent_hour >= MAX_SENDS_PER_HOUR:
        raise ValueError("ขอรหัส OTP เกินจำนวนครั้งที่กำหนด (สูงสุด 5 ครั้งต่อชั่วโมง) กรุณารอสักครู่")

    # ตรวจระยะเวลาส่งซ้ำ 60 วินาที
    if check_cooldown:
        latest = repo_otp.get_latest_otp_any(email, purpose)
        if latest is not None:
            created_dt = parse_datetime(latest["created_at"])
            if created_dt is not None:
                elapsed = (datetime.now() - created_dt).total_seconds()
                if elapsed < RESEND_COOLDOWN_SECONDS:
                    wait_sec = max(1, int(RESEND_COOLDOWN_SECONDS - elapsed))
                    raise ValueError(f"กรุณารออีก {wait_sec} วินาทีก่อนขอรหัส OTP ใหม่")

    code = f"{secrets.randbelow(1_000_000):06d}"
    code_hash = _hash_code(email, purpose, code, user_context=email)
    expires_at = (datetime.now() + timedelta(minutes=OTP_EXPIRE_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    otp_id = repo_otp.create_otp(email, purpose, code_hash, expires_at)

    try:
        shop_name = settings_service.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
    except Exception:
        shop_name = "AI.HERE BADᴍᴛ-Zone"

    subject, text_body, html_body = build_otp_email_content(
        purpose=purpose,
        code=code,
        shop_name=shop_name,
        recipient_name=recipient_name,
        expires_in_minutes=OTP_EXPIRE_MINUTES,
        expires_at=expires_at,
        target_email=email,
    )

    try:
        send_res = email_service.send_mail(email, subject, text_body, html=html_body)
    except Exception:
        repo_otp.delete_otp(otp_id)
        raise

    masked = mask_email(email)
    return {
        "email": email,
        "masked_email": masked,
        "expires_in_minutes": OTP_EXPIRE_MINUTES,
        "cooldown_seconds": RESEND_COOLDOWN_SECONDS,
        "mode": send_res.get("mode", "smtp"),
        "message": f"ส่งรหัสไปที่ {masked} แล้ว",
    }


def verify_otp(email: str, purpose: str, code: str, conn=None) -> bool:
    """
    ตรวจสอบรหัส OTP 6 หลัก:
    - รหัสไม่ถูกต้อง -> บวก attempts + 1 (บันทึกแยกเพื่อกัน brute-force) แล้วโยน ValueError
    - เกิน 5 ครั้ง หรือหมดอายุ -> ยกเลิกรหัสทันทีและโยน ValueError
    - ถูกต้อง -> ทำเครื่องหมาย used_at แบบอะตอมมิก (ป้องกัน race condition ยืนยันซ้ำพร้อมกัน) และคืน True
    """
    email = (email or "").strip().lower()
    code = (code or "").strip()
    if purpose not in VALID_PURPOSES:
        raise ValueError("ประเภทการยืนยัน OTP ไม่ถูกต้อง")
    if not code or len(code) != 6 or not code.isdigit():
        raise ValueError("กรุณากรอกรหัส OTP ตัวเลข 6 หลัก")

    # อ่านแถวล่าสุดจาก connection แยกเพื่อให้เห็นสถานะ attempts/used_at ล่าสุดเสมอ
    row = repo_otp.get_latest_active_otp(email, purpose, conn=conn)
    if row is None:
        raise ValueError("ไม่พบรหัส OTP ที่ใช้งานได้ กรุณากดขอรหัสใหม่")

    if int(row["attempts"] or 0) >= MAX_OTP_ATTEMPTS:
        repo_otp.mark_used(row["id"], conn=conn)
        raise ValueError("กรอกรหัสผิดเกิน 5 ครั้ง รหัสนี้ถูกยกเลิกแล้ว กรุณาขอรหัส OTP ใหม่")

    expires_dt = parse_datetime(row["expires_at"])
    if expires_dt is None or expires_dt < datetime.now():
        repo_otp.mark_used(row["id"], conn=conn)
        raise ValueError("รหัส OTP หมดอายุแล้ว กรุณากดขอรหัสใหม่")

    expected_hash = _hash_code(email, purpose, code, user_context=email)
    if not hmac.compare_digest(expected_hash, str(row["code_hash"])):
        # นับครั้งที่ผิดใน connection แยกเสมอ เพื่อไม่ให้ rollback ตอนเกิด error ล้างจำนวนครั้งที่เดาผิด
        attempts = repo_otp.increment_attempts(row["id"], conn=conn)
        if attempts >= MAX_OTP_ATTEMPTS:
            repo_otp.mark_used(row["id"], conn=conn)
            raise ValueError("กรอกรหัสผิดครบ 5 ครั้ง รหัสนี้ถูกยกเลิกแล้ว กรุณาขอรหัส OTP ใหม่")
        left = MAX_OTP_ATTEMPTS - attempts
        raise ValueError(f"รหัส OTP ไม่ถูกต้อง (ลองได้อีก {left} ครั้ง)")

    # Atomic conditional update: WHERE id = ? AND used_at IS NULL
    if not repo_otp.mark_used(row["id"], conn=conn):
        raise ValueError("รหัส OTP นี้ถูกใช้งานไปแล้ว กรุณาขอรหัสใหม่")
    return True
