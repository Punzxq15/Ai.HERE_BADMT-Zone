"""
database/repo_users.py
จัดการการดึงและบันทึกข้อมูลสำหรับตาราง users เท่านั้น
(ทำหน้าที่คุยกับ Database อย่างเดียว ไม่มี Business Logic)
"""
from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_OWNER
from database.repo_base import like_pattern, use_conn

# คอลัมน์ที่ปลอดภัยสำหรับรายการ (ไม่มี password_hash)
_SAFE_COLUMNS = ("id, username, email, full_name, phone, role, avatar_path, "
                 "is_online, is_active, email_verified, must_change_password, last_login_at, created_at")


# ---------- ฟังก์ชันเดิม (พฤติกรรมเดิมทุกอย่าง) ----------

def get_by_username(username: str, conn=None):
    """ค้นหาผู้ใช้จากชื่อผู้ใช้ (username)"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_by_email(email: str, conn=None):
    """ค้นหาผู้ใช้จากอีเมล (email)"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_by_id(user_id: int, conn=None):
    """ค้นหาผู้ใช้จากไอดี (id)"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def username_exists(username: str, conn=None) -> bool:
    """ตรวจสอบว่ามี username นี้ในระบบหรือยัง"""
    with use_conn(conn) as c:
        return c.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone() is not None


def username_exists_other(username: str, exclude_user_id: int, conn=None) -> bool:
    """ตรวจสอบว่ามีผู้อื่นใช้ username นี้อยู่หรือไม่"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT 1 FROM users WHERE username = ? AND id != ?",
            (username, int(exclude_user_id)),
        ).fetchone() is not None


def email_exists(email: str, conn=None) -> bool:
    """ตรวจสอบว่ามี email นี้ในระบบหรือยัง"""
    with use_conn(conn) as c:
        return c.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone() is not None


def email_exists_other(email: str, exclude_user_id: int, conn=None) -> bool:
    """ตรวจสอบว่ามีผู้อื่นใช้ email นี้อยู่หรือไม่"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT 1 FROM users WHERE email = ? AND id != ?",
            (email, int(exclude_user_id)),
        ).fetchone() is not None


def create_user(username: str, email: str, password_hash: str, full_name: str,
                phone: str, role: str = ROLE_BUYER, email_verified: int = 1,
                must_change_password: int = 0, conn=None) -> int:
    """สร้างผู้ใช้ใหม่ คืนค่า id ของผู้ใช้ที่เพิ่งสร้าง (lastrowid)"""
    with use_conn(conn) as c:
        cur = c.execute(
            "INSERT INTO users (username, email, password_hash, full_name, phone, role, "
            "email_verified, must_change_password) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, email, password_hash, full_name, phone, role,
             1 if email_verified else 0, 1 if must_change_password else 0),
        )
        return cur.lastrowid


# ---------- ฟังก์ชันจัดการบัญชีและสถานะ ----------

def list_users(role=None, search=None, conn=None):
    """
    รายชื่อผู้ใช้ (ไม่มี password_hash) เรียงใหม่สุดก่อน
    role: ค่าเดียวหรือ list | search: ค้นใน username/email/ชื่อ/เบอร์
    """
    sql = f"SELECT {_SAFE_COLUMNS} FROM users WHERE 1=1"
    params = []
    if role:
        roles = role if isinstance(role, (list, tuple, set)) else [role]
        sql += f" AND role IN ({','.join('?' * len(roles))})"
        params += list(roles)
    if search and search.strip():
        pat = like_pattern(search.strip())
        sql += (" AND (username LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\' "
                "OR full_name LIKE ? ESCAPE '\\' OR phone LIKE ? ESCAPE '\\')")
        params += [pat] * 4
    sql += " ORDER BY id DESC"
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def update_profile(user_id: int, full_name: str, phone: str, avatar_path=None, conn=None) -> bool:
    """แก้ชื่อ/เบอร์/รูปโปรไฟล์ — avatar_path=None หมายถึง 'ไม่เปลี่ยนรูป'"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE users SET full_name = ?, phone = ?, avatar_path = COALESCE(?, avatar_path) "
            "WHERE id = ?",
            (full_name, phone, avatar_path, user_id),
        )
        return cur.rowcount > 0


def update_username(user_id: int, username: str, conn=None) -> bool:
    """แก้ไข username ของผู้ใช้ (T11)"""
    with use_conn(conn) as c:
        cur = c.execute("UPDATE users SET username = ? WHERE id = ?", (username, int(user_id)))
        return cur.rowcount > 0


def update_email(user_id: int, email: str, email_verified: int = 1, conn=None) -> bool:
    """แก้ไข email ของผู้ใช้หลังยืนยัน OTP ใหม่สำเร็จ (T11)"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE users SET email = ?, email_verified = ? WHERE id = ?",
            (email, 1 if email_verified else 0, int(user_id)),
        )
        return cur.rowcount > 0


def update_password(user_id: int, password_hash: str, must_change: bool = False, conn=None) -> bool:
    """เปลี่ยน password_hash (service เป็นคนเข้ารหัสมาให้)"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE users SET password_hash = ?, must_change_password = ? WHERE id = ?",
            (password_hash, 1 if must_change else 0, user_id),
        )
        return cur.rowcount > 0


def update_role_and_password(user_id: int, role: str, password_hash: str,
                             email_verified: bool = True, must_change: bool = False, conn=None) -> bool:
    """เปลี่ยนบทบาทผู้ใช้ (เช่น เลื่อนเป็น admin) พร้อมตั้งรหัสผ่านใหม่"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE users SET role = ?, password_hash = ?, email_verified = ?, must_change_password = ? "
            "WHERE id = ?",
            (role, password_hash, 1 if email_verified else 0, 1 if must_change else 0, user_id),
        )
        return cur.rowcount > 0


def set_email_verified(user_id: int, verified: bool = True, conn=None) -> bool:
    with use_conn(conn) as c:
        cur = c.execute("UPDATE users SET email_verified = ? WHERE id = ?",
                        (1 if verified else 0, user_id))
        return cur.rowcount > 0


def set_must_change_password(user_id: int, must_change: bool, conn=None) -> bool:
    with use_conn(conn) as c:
        cur = c.execute("UPDATE users SET must_change_password = ? WHERE id = ?",
                        (1 if must_change else 0, user_id))
        return cur.rowcount > 0


def touch_last_login(user_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE users SET last_login_at = datetime('now','localtime') WHERE id = ?",
            (user_id,),
        )
        return cur.rowcount > 0


def get_owner(conn=None):
    """คืนบัญชีเจ้าของร้านคนแรก"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM users WHERE role = ? ORDER BY id LIMIT 1",
                         (ROLE_OWNER,)).fetchone()


def set_active(user_id: int, active: bool, conn=None) -> bool:
    """ระงับ/เปิดใช้บัญชี (ระงับแล้วล้างสถานะออนไลน์ด้วย)"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE users SET is_active = ?, is_online = CASE WHEN ? = 0 THEN 0 ELSE is_online END "
            "WHERE id = ?",
            (1 if active else 0, 1 if active else 0, user_id),
        )
        return cur.rowcount > 0


def set_online(user_id: int, online: bool, conn=None) -> bool:
    """ตั้ง/ล้างสถานะออนไลน์"""
    with use_conn(conn) as c:
        cur = c.execute("UPDATE users SET is_online = ? WHERE id = ?", (1 if online else 0, user_id))
        return cur.rowcount > 0


def clear_all_online(conn=None) -> int:
    """ล้างสถานะออนไลน์ทุกคน (เรียกตอนเปิดแอป กันค้าง) คืนจำนวนแถวที่เปลี่ยน"""
    with use_conn(conn) as c:
        return c.execute("UPDATE users SET is_online = 0 WHERE is_online = 1").rowcount


def list_online_staff(conn=None):
    """admin/owner ที่ออนไลน์และยังไม่ถูกระงับ (ใช้ตัดสินว่า AI ต้องตอบแชทไหม)"""
    with use_conn(conn) as c:
        return c.execute(
            f"SELECT {_SAFE_COLUMNS} FROM users "
            "WHERE role IN (?, ?) AND is_online = 1 AND is_active = 1 ORDER BY id",
            (ROLE_ADMIN, ROLE_OWNER),
        ).fetchall()
