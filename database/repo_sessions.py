"""
database/repo_sessions.py
จัดการตาราง sessions สำหรับเซสชันการล็อกอิน (เช่น จำเครื่องในร้านสำหรับ Admin/Owner และการสั่งเตะออกจากระบบทุกเครื่อง)
เก็บเฉพาะค่า hash ของ token เพื่อความปลอดภัย
"""
from database.repo_base import use_conn


def create_session(token_hash: str, user_id: int, expires_at: str, remember: bool = False,
                   user_agent: str = "Desktop-CustomTkinter", ip: str = "127.0.0.1", conn=None) -> None:
    with use_conn(conn) as c:
        c.execute(
            '''INSERT OR REPLACE INTO sessions
               (token_hash, user_id, remember, user_agent, ip, created_at, last_seen_at, expires_at)
               VALUES (?, ?, ?, ?, ?, datetime('now','localtime'), datetime('now','localtime'), ?)''',
            (token_hash, user_id, 1 if remember else 0, user_agent, ip, expires_at),
        )


def get_valid_session(token_hash: str, conn=None):
    """ดึงเซสชันที่ยังไม่หมดอายุ พร้อมข้อมูลผู้ใช้"""
    with use_conn(conn) as c:
        return c.execute(
            '''SELECT s.*, u.username, u.email, u.full_name, u.role, u.is_active,
                      u.email_verified, u.must_change_password
               FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > datetime('now','localtime')''',
            (token_hash,),
        ).fetchone()


def touch_session(token_hash: str, new_expires_at: str = None, conn=None) -> bool:
    with use_conn(conn) as c:
        if new_expires_at:
            cur = c.execute(
                "UPDATE sessions SET last_seen_at = datetime('now','localtime'), expires_at = ? "
                "WHERE token_hash = ?",
                (new_expires_at, token_hash),
            )
        else:
            cur = c.execute(
                "UPDATE sessions SET last_seen_at = datetime('now','localtime') WHERE token_hash = ?",
                (token_hash,),
            )
        return cur.rowcount > 0


def delete_session(token_hash: str, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,)).rowcount > 0


def delete_user_sessions(user_id: int, conn=None) -> int:
    """ลบเซสชันทั้งหมดของผู้ใช้นี้ (สั่งออกจากระบบทุกเครื่อง / ตอนเปลี่ยนรหัสผ่าน)"""
    with use_conn(conn) as c:
        return c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,)).rowcount


def list_active_sessions(user_id: int = None, conn=None):
    sql = (
        "SELECT s.token_hash, s.user_id, s.remember, s.user_agent, s.ip, s.created_at, "
        "s.last_seen_at, s.expires_at, u.username, u.email, u.full_name, u.role "
        "FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.expires_at > datetime('now','localtime')"
    )
    params = []
    if user_id is not None:
        sql += " AND s.user_id = ?"
        params.append(user_id)
    sql += " ORDER BY s.last_seen_at DESC"
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def purge_expired(conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute("DELETE FROM sessions WHERE expires_at <= datetime('now','localtime')").rowcount
