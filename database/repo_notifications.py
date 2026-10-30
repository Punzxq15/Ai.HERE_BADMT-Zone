"""
database/repo_notifications.py
การแจ้งเตือน (ตาราง notifications) — ไม่มี business logic
"""
from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_OWNER
from database.repo_base import use_conn

MAX_BUYER_NOTIFICATIONS = 10


def _prune_buyer_notifications(c, user_id: int, max_keep: int = MAX_BUYER_NOTIFICATIONS) -> None:
    """เก็บการแจ้งเตือนได้แค่ 10 ครั้งล่าสุดสำหรับบัญชี Buyer เท่านั้น (ข้อ 14)"""
    role_row = c.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if role_row and role_row["role"] == ROLE_BUYER:
        c.execute(
            """
            DELETE FROM notifications
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT ?
            )
            """,
            (user_id, user_id, int(max_keep)),
        )


def create(user_id: int, title: str, message: str, target_route: str = None,
           target_params: str = None, conn=None) -> int:
    """สร้างการแจ้งเตือนให้ผู้ใช้ 1 คน คืน id (พร้อมตัดให้เหลือ 10 รายการล่าสุดสำหรับ Buyer)"""
    with use_conn(conn) as c:
        nid = c.execute(
            "INSERT INTO notifications (user_id, title, message, target_route, target_params) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, message, target_route, target_params),
        ).lastrowid
        _prune_buyer_notifications(c, user_id, MAX_BUYER_NOTIFICATIONS)
        return nid


def create_for_staff(title: str, message: str, target_route: str = None,
                     target_params: str = None, conn=None) -> int:
    """แจ้งเตือน admin + owner ที่ยังไม่ถูกระงับทุกคน คืนจำนวนคนที่ได้รับ"""
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO notifications (user_id, title, message, target_route, target_params) "
            "SELECT id, ?, ?, ?, ? FROM users WHERE role IN (?, ?) AND is_active = 1",
            (title, message, target_route, target_params, ROLE_ADMIN, ROLE_OWNER),
        ).rowcount


def list(user_id: int, limit: int = 50, unread_only: bool = False, conn=None):  # noqa: A001
    """การแจ้งเตือนของผู้ใช้ ใหม่สุดก่อน (สำหรับ Buyer จำกัดไม่เกิน 10 รายการล่าสุด)"""
    with use_conn(conn) as c:
        _prune_buyer_notifications(c, user_id, MAX_BUYER_NOTIFICATIONS)
        role_row = c.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        effective_limit = int(limit)
        if role_row and role_row["role"] == ROLE_BUYER:
            effective_limit = min(effective_limit, MAX_BUYER_NOTIFICATIONS)
        sql = "SELECT * FROM notifications WHERE user_id = ?"
        if unread_only:
            sql += " AND is_read = 0"
        sql += " ORDER BY id DESC LIMIT ?"
        return c.execute(sql, (user_id, effective_limit)).fetchall()


def count_unread(user_id: int, conn=None) -> int:
    with use_conn(conn) as c:
        _prune_buyer_notifications(c, user_id, MAX_BUYER_NOTIFICATIONS)
        return c.execute("SELECT COUNT(*) AS n FROM notifications WHERE user_id = ? AND is_read = 0",
                         (user_id,)).fetchone()["n"]


def mark_read(notification_id: int, user_id=None, conn=None) -> bool:
    """อ่านแล้ว 1 รายการ — ถ้าส่ง user_id จะตรวจว่าเป็นของคนนั้นด้วย (กันแก้ของคนอื่น)"""
    sql, params = "UPDATE notifications SET is_read = 1 WHERE id = ?", [notification_id]
    if user_id is not None:
        sql += " AND user_id = ?"
        params.append(user_id)
    with use_conn(conn) as c:
        return c.execute(sql, params).rowcount > 0


def mark_all_read(user_id: int, conn=None) -> int:
    """อ่านทั้งหมดของผู้ใช้ คืนจำนวนที่เปลี่ยน"""
    with use_conn(conn) as c:
        return c.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                         (user_id,)).rowcount
