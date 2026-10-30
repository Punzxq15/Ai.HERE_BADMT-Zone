"""
utils/formatters.py
ฟังก์ชันจัดรูปแบบข้อความที่แสดงบนหน้าจอ (ราคา วันที่ เบอร์โทร)
ทุกหน้า/ใบเสร็จต้องแสดงเงินผ่านไฟล์นี้เท่านั้น — ห้ามใช้สัญลักษณ์ ฿ (ฟอนต์ไม่มีตัวนี้)
"""
from datetime import date, datetime

_THAI_MONTHS_SHORT = (
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
)


def format_price(amount) -> str:
    """1290 -> '1,290 บาท' | 1290.5 -> '1,290.50 บาท' | None -> '0 บาท'"""
    try:
        value = round(float(amount or 0), 2)
    except (TypeError, ValueError):
        value = 0.0
    if value == int(value):
        return f"{int(value):,} บาท"
    return f"{value:,.2f} บาท"


def parse_datetime(value) -> datetime | None:
    """แปลงค่าจาก SQLite ('YYYY-MM-DD HH:MM:SS' / 'YYYY-MM-DD') หรือ datetime/date เป็น datetime; แปลงไม่ได้ = None"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def format_date_thai(value) -> str:
    """'2026-10-11 07:12:00' -> '11 ต.ค. 2569' (ปี พ.ศ.) | ไม่มีค่า -> '-'"""
    if value is None or value == "":
        return "-"
    dt = parse_datetime(value)
    if dt is None:
        return str(value)
    return f"{dt.day} {_THAI_MONTHS_SHORT[dt.month - 1]} {dt.year + 543}"


def format_datetime(value) -> str:
    """'2026-10-11 07:12:00' -> '11 ต.ค. 2569 07:12' (ปี พ.ศ.) | ไม่มีค่า -> '-'"""
    if value is None or value == "":
        return "-"
    dt = parse_datetime(value)
    if dt is None:
        return str(value)
    return f"{dt.day} {_THAI_MONTHS_SHORT[dt.month - 1]} {dt.year + 543} {dt.hour:02d}:{dt.minute:02d}"


def format_phone(phone) -> str:
    """'0812345678' -> '081-234-5678' | รูปแบบอื่น คืนค่าเดิม | ไม่มีค่า -> '-'"""
    if not phone:
        return "-"
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return str(phone)

THAI_MONTHS_SHORT = _THAI_MONTHS_SHORT
