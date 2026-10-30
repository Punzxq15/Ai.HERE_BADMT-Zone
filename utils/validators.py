import re
from datetime import datetime
from urllib.parse import urlparse


def is_valid_email(email: str) -> bool:
    """
    ตรวจสอบรูปแบบอีเมลด้วย Regular Expression
    ต้องมี @ และ . และไม่มีอักขระพิเศษที่ไม่ได้รับอนุญาต
    """
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\Z"
    return bool(re.match(pattern, str(email).strip()))


def is_valid_phone(phone: str) -> bool:
    """
    ตรวจสอบเบอร์โทรศัพท์ประเทศไทย
    ต้องเป็นตัวเลขล้วน 9-10 หลัก และขึ้นต้นด้วย '0' (รองรับทั้งมือถือ 10 หลัก และเบอร์บ้าน/ร้าน 9-10 หลัก)
    หมายเหตุ: การตรวจสอบบัญชีผู้ใช้เดิมใช้ 10 หลัก ส่วนเบอร์ติดต่อร้านใช้ is_valid_shop_phone ได้
    """
    if not phone:
        return False
    pattern = r"^0\d{9}\Z"
    return bool(re.match(pattern, str(phone).strip()))


def is_valid_shop_phone(phone: str) -> bool:
    """ตรวจสอบเบอร์โทรติดต่อร้าน (ตัวเลข 9-10 หลัก ขึ้นต้นด้วย 0)"""
    if not phone:
        return False
    digits = re.sub(r"[\s-]", "", str(phone).strip())
    return bool(re.match(r"^0\d{8,9}\Z", digits))


def is_strong_password(password: str) -> bool:
    """
    ตรวจสอบความแข็งแกร่งของรหัสผ่าน
    กำหนดความยาวขั้นต่ำที่ 8 ตัวอักษร
    """
    if not password:
        return False
    return len(password) >= 8


def is_valid_username(username: str) -> bool:
    """
    ตรวจสอบชื่อผู้ใช้
    อนุญาตเฉพาะภาษาอังกฤษ ตัวเลข และ _ (Underscore) ห้ามมีช่องว่างหรืออักขระพิเศษอื่น
    """
    if not username:
        return False
    pattern = r"^[a-zA-Z0-9_]+\Z"
    return bool(re.match(pattern, str(username).strip()))


def is_valid_postcode(postcode: str) -> bool:
    """
    ตรวจสอบรหัสไปรษณีย์ไทย ต้องเป็นตัวเลข 5 หลักพอดี
    """
    if not postcode:
        return False
    return bool(re.match(r"^\d{5}\Z", str(postcode).strip()))


def is_valid_https_url(url: str) -> bool:
    """
    ตรวจสอบ URL ภายนอก (เช่น Facebook, Instagram, LINE OA, TikTok, Google Maps)
    อนุญาตเฉพาะ https:// ที่มี host จริง ป้องกัน javascript: หรือ file:
    """
    if not url:
        return False
    text = str(url).strip()
    if not text.startswith("https://"):
        return False
    try:
        parsed = urlparse(text)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc) and "." in parsed.netloc


# ---------- ฟังก์ชันตรวจสอบเพิ่มเติม (T03, T08 — additive) ----------

_BALANCE_MM_RE = re.compile(
    r"^\s*(\d{2,3}(?:\.\d+)?)\s*(?:(?:\+-|±|-|~)\s*(\d+(?:\.\d+)?))?\s*(?:mm\.?|มม\.?)?\s*$",
    re.IGNORECASE,
)


def is_valid_balance_point_mm(value: str) -> bool:
    """
    ตรวจสอบค่าตัวเลข Balance Point (mm) เช่น '305', '305±3', '305+-3', '295-305', '305±3 mm'
    ค่าหลักต้องอยู่ในช่วง 150 - 450 mm
    """
    if value is None or str(value).strip() == "":
        return True
    m = _BALANCE_MM_RE.match(str(value).strip())
    if not m:
        return False
    try:
        main_val = float(m.group(1))
    except ValueError:
        return False
    return 150.0 <= main_val <= 450.0


def normalize_balance_point_mm(value: str) -> str | None:
    """ทำความสะอาดค่าตัวเลข Balance Point ให้เป็นรูปแบบมาตรฐาน เช่น '305±3 mm'"""
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).strip()
    if not is_valid_balance_point_mm(raw):
        raise ValueError("ค่าตัวเลข Balance Point ไม่ถูกต้อง (กรอกตัวเลขหน่วย mm เช่น 305 หรือ 305±3)")
    m = _BALANCE_MM_RE.match(raw)
    base = m.group(1)
    tol = m.group(2)
    if tol:
        return f"{base}±{tol} mm"
    return f"{base} mm"


def format_balance_point_display(mm_text: str | None, balance_type: str | None) -> str:
    """รวมตัวเลข Balance Point กับประเภท เช่น '305±3 mm (Head Heavy)'"""
    mm_clean = (mm_text or "").strip()
    b_clean = (balance_type or "").strip()
    if mm_clean and not mm_clean.lower().endswith("mm"):
        mm_clean = f"{mm_clean} mm"
    if mm_clean and b_clean:
        return f"{mm_clean} ({b_clean})"
    if mm_clean:
        return mm_clean
    return b_clean


def is_valid_date_range(start_text: str | None, end_text: str | None) -> bool:
    """ตรวจสอบว่าวันสิ้นสุดไม่ก่อนวันเริ่มต้น (ถ้ากรอกทั้งคู่)"""
    s = (start_text or "").strip()
    e = (end_text or "").strip()
    if not s or not e:
        return True
    fmts = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
    dt_s = dt_e = None
    for f in fmts:
        if dt_s is None:
            try:
                dt_s = datetime.strptime(s, f)
            except ValueError:
                pass
        if dt_e is None:
            try:
                dt_e = datetime.strptime(e, f)
            except ValueError:
                pass
    if dt_s is None or dt_e is None:
        return False
    if len(e) <= 10 and len(s) <= 10:
        return dt_e.date() >= dt_s.date()
    if len(e) <= 10:
        dt_e = dt_e.replace(hour=23, minute=59, second=59)
    return dt_e >= dt_s
