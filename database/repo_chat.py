"""
database/repo_chat.py
ข้อความแชท (ตาราง chat_messages) — หนึ่งห้องต่อลูกค้า (customer_id)
sender_type = user | admin | ai   ไม่มี business logic (ตัดสินว่า AI ตอบไหมอยู่ที่ chat_service)
รองรับการแนบรูปภาพ (image_path) ทั้งฝั่งลูกค้า พนักงาน และเจ้าของร้าน
"""
from core.constants import SENDER_TYPE_USER
from database.repo_base import use_conn

READER_STAFF = "staff"        # แอดมินอ่าน -> ข้อความของลูกค้าถูกทำเป็นอ่านแล้ว
READER_CUSTOMER = "customer"  # ลูกค้าอ่าน -> ข้อความจาก admin/ai ถูกทำเป็นอ่านแล้ว


def add_message(customer_id: int, sender_type: str, sender_id, message: str, image_path: str | None = None, conn=None) -> int:
    """เพิ่มข้อความพร้อมรูปภาพแนบ (ถ้ามี) (sender_id = None ได้เมื่อเป็น AI) คืน id"""
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO chat_messages (customer_id, sender_type, sender_id, message, image_path) VALUES (?, ?, ?, ?, ?)",
            (customer_id, sender_type, sender_id, message if message is not None else "", image_path),
        ).lastrowid


def list_messages(customer_id: int, after_id: int = 0, limit=None, conn=None):
    """ข้อความของห้อง เก่า -> ใหม่ เฉพาะที่ id > after_id (ใช้โพลเอาเฉพาะข้อความใหม่)"""
    sql = "SELECT * FROM chat_messages WHERE customer_id = ? AND id > ? ORDER BY id"
    params = [customer_id, int(after_id or 0)]
    if limit is not None:
        # เอา "ล่าสุด limit ข้อความ" แล้วเรียงกลับเก่า->ใหม่
        sql = ("SELECT * FROM (SELECT * FROM chat_messages WHERE customer_id = ? AND id > ? "
               "ORDER BY id DESC LIMIT ?) ORDER BY id")
        params.append(int(limit))
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def list_threads(conn=None):
    """
    ห้องแชททั้งหมด ล่าสุดก่อน: customer_id, full_name, username, avatar_path,
    last_message, last_image_path, last_sender_type, last_at, unread_count (ข้อความลูกค้าที่แอดมินยังไม่อ่าน)
    """
    with use_conn(conn) as c:
        return c.execute(
            "SELECT m.customer_id, u.full_name, u.username, u.avatar_path, "
            "CASE WHEN (m.message IS NULL OR m.message = '') AND m.image_path IS NOT NULL "
            "     THEN '📷 [ส่งรูปภาพ]' ELSE m.message END AS last_message, "
            "m.image_path AS last_image_path, "
            "m.sender_type AS last_sender_type, m.created_at AS last_at, "
            "(SELECT COUNT(*) FROM chat_messages x WHERE x.customer_id = m.customer_id "
            " AND x.sender_type = ? AND x.is_read = 0) AS unread_count "
            "FROM chat_messages m JOIN users u ON u.id = m.customer_id "
            "WHERE m.id = (SELECT MAX(id) FROM chat_messages WHERE customer_id = m.customer_id) "
            "ORDER BY m.id DESC",
            (SENDER_TYPE_USER,),
        ).fetchall()


def mark_read(customer_id: int, reader_side: str, conn=None) -> int:
    """
    ทำเครื่องหมายอ่านแล้ว คืนจำนวนข้อความที่เปลี่ยน
    reader_side = "staff"    -> ข้อความที่ลูกค้าส่ง (sender_type=user)
    reader_side = "customer" -> ข้อความที่ admin/ai ส่ง
    """
    if reader_side == READER_STAFF:
        cond, params = "sender_type = ?", [SENDER_TYPE_USER]
    elif reader_side == READER_CUSTOMER:
        cond, params = "sender_type != ?", [SENDER_TYPE_USER]
    else:
        raise ValueError(f"reader_side ไม่ถูกต้อง: {reader_side}")
    with use_conn(conn) as c:
        return c.execute(
            f"UPDATE chat_messages SET is_read = 1 WHERE customer_id = ? AND is_read = 0 AND {cond}",
            [customer_id, *params],
        ).rowcount


def count_unread_for_staff(conn=None) -> int:
    """จำนวนข้อความจากลูกค้าที่แอดมินยังไม่อ่าน (ทุกห้องรวมกัน) — ใช้จุดแดงที่ sidebar"""
    with use_conn(conn) as c:
        return c.execute("SELECT COUNT(*) AS n FROM chat_messages WHERE sender_type = ? AND is_read = 0",
                         (SENDER_TYPE_USER,)).fetchone()["n"]


def count_unread_for_customer(customer_id: int, conn=None) -> int:
    """จำนวนข้อความจาก admin/ai ที่ลูกค้าคนนี้ยังไม่อ่าน"""
    with use_conn(conn) as c:
        return c.execute("SELECT COUNT(*) AS n FROM chat_messages WHERE customer_id = ? "
                         "AND sender_type != ? AND is_read = 0",
                         (customer_id, SENDER_TYPE_USER)).fetchone()["n"]
