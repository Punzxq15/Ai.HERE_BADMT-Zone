"""
database/repo_base.py
ตัวช่วยกลางของชั้น repo: จัดการ connection ตามข้อตกลง conn=None
(ภายในชั้น database เท่านั้น ไม่มี business logic)
"""
from contextlib import contextmanager

from database.db import get_connection

# SQL คำนวณ "ราคาที่ใช้จริง" ของ products (alias p) — ใช้ sale_price เมื่อมี และยังไม่หมดเวลาโปร
EFFECTIVE_PRICE_SQL = (
    "(CASE WHEN p.sale_price IS NOT NULL "
    "AND (p.sale_ends_at IS NULL OR p.sale_ends_at > datetime('now','localtime')) "
    "THEN p.sale_price ELSE p.price END)"
)


@contextmanager
def use_conn(conn=None):
    """
    ถ้าได้ conn มา -> ใช้ต่อโดยไม่ commit/close (ให้ service ครอบ transaction)
    ถ้าไม่ได้ -> เปิดเอง commit เอง (rollback ถ้าพลาด) ปิดเอง
    """
    if conn is not None:
        yield conn
        return
    own = get_connection()
    try:
        yield own
        own.commit()
    except BaseException:
        own.rollback()
        raise
    finally:
        own.close()


def like_pattern(text: str) -> str:
    """แปลงคำค้นเป็นรูปแบบ LIKE '%คำ%' (escape % _ ด้วย \\ — ต้องใช้คู่กับ ESCAPE '\\')"""
    safe = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{safe}%"


def as_list(value):
    """ค่าเดี่ยว -> [ค่า], list/tuple/set -> list (ใช้กับตัวกรองหลายค่า)"""
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]
