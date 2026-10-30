"""
database/repo_addresses.py
ที่อยู่จัดส่ง (ตาราง addresses) — ผู้ใช้หนึ่งคนมี is_default ได้ไม่เกิน 1 ที่อยู่
"""
from database.repo_base import use_conn


def list(user_id: int, conn=None):  # noqa: A001 (ชื่อตามที่กำหนดในแผน)
    """ที่อยู่ทั้งหมดของผู้ใช้ — ที่อยู่หลักขึ้นก่อน"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id",
                         (user_id,)).fetchall()


def get(address_id: int, conn=None):
    """ที่อยู่ 1 รายการ (service ต้องตรวจเองว่าเป็นของผู้ใช้คนนั้น) หรือ None"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM addresses WHERE id = ?", (address_id,)).fetchone()


def get_default(user_id: int, conn=None):
    """ที่อยู่หลักของผู้ใช้ หรือ None"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM addresses WHERE user_id = ? AND is_default = 1 "
                         "ORDER BY id LIMIT 1", (user_id,)).fetchone()


def count(user_id: int, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute("SELECT COUNT(*) AS n FROM addresses WHERE user_id = ?",
                         (user_id,)).fetchone()["n"]


def create(user_id: int, recipient: str, phone: str, address_line: str, district: str,
           province: str, postcode: str, is_default: bool = False, conn=None) -> int:
    """เพิ่มที่อยู่ คืน id — ถ้า is_default=True จะยกเลิกที่อยู่หลักเดิมให้อัตโนมัติ"""
    with use_conn(conn) as c:
        if is_default:
            c.execute("UPDATE addresses SET is_default = 0 WHERE user_id = ?", (user_id,))
        return c.execute(
            "INSERT INTO addresses (user_id, recipient, phone, address_line, district, province, "
            "postcode, is_default) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, recipient, phone, address_line, district, province, postcode,
             1 if is_default else 0),
        ).lastrowid


def update(address_id: int, recipient: str, phone: str, address_line: str, district: str,
           province: str, postcode: str, conn=None) -> bool:
    """แก้ข้อมูลที่อยู่ (ไม่แตะ is_default — ใช้ set_default)"""
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE addresses SET recipient = ?, phone = ?, address_line = ?, district = ?, "
            "province = ?, postcode = ? WHERE id = ?",
            (recipient, phone, address_line, district, province, postcode, address_id),
        ).rowcount > 0


def delete(address_id: int, conn=None) -> bool:
    """ลบที่อยู่ (ออเดอร์เก่าเก็บสำเนาข้อความที่อยู่ไว้แล้ว จึงลบได้)"""
    with use_conn(conn) as c:
        return c.execute("DELETE FROM addresses WHERE id = ?", (address_id,)).rowcount > 0


def set_default(user_id: int, address_id: int, conn=None) -> bool:
    """ตั้งเป็นที่อยู่หลัก (ล้างของเดิมให้) — ไม่ใช่ที่อยู่ของ user นี้ -> False และไม่แก้อะไร"""
    with use_conn(conn) as c:
        owned = c.execute("SELECT 1 FROM addresses WHERE id = ? AND user_id = ?",
                          (address_id, user_id)).fetchone()
        if owned is None:
            return False
        c.execute("UPDATE addresses SET is_default = 0 WHERE user_id = ?", (user_id,))
        c.execute("UPDATE addresses SET is_default = 1 WHERE id = ?", (address_id,))
        return True

list_by_user = list
