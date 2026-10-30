"""
database/repo_otp.py
จัดการตาราง email_otps, pending_registrations และ email_change_otps (T11)
สำหรับระบบยืนยันอีเมลตอนสมัครสมาชิก ลืมรหัสผ่าน และเปลี่ยนอีเมลในโปรไฟล์
"""
from database.repo_base import use_conn


def save_pending_registration(email: str, username: str, full_name: str, phone: str,
                              password_hash: str, address_json: str, conn=None) -> None:
    """บันทึกหรือเขียนทับข้อมูลการสมัครที่ยังรอยืนยัน OTP"""
    clean_email = (email or "").strip().lower()
    with use_conn(conn) as c:
        c.execute(
            '''INSERT INTO pending_registrations
               (email, username, full_name, phone, password_hash, address_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))
               ON CONFLICT(email) DO UPDATE SET
                   username = excluded.username,
                   full_name = excluded.full_name,
                   phone = excluded.phone,
                   password_hash = excluded.password_hash,
                   address_json = excluded.address_json,
                   created_at = datetime('now','localtime')''',
            (clean_email, username, full_name, phone, password_hash, address_json),
        )


def get_pending_registration(email: str, conn=None):
    clean_email = (email or "").strip().lower()
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM pending_registrations WHERE email = ?", (clean_email,)).fetchone()


def delete_pending_registration(email: str, conn=None) -> bool:
    clean_email = (email or "").strip().lower()
    with use_conn(conn) as c:
        return c.execute("DELETE FROM pending_registrations WHERE email = ?", (clean_email,)).rowcount > 0


def create_otp(email: str, purpose: str, code_hash: str, expires_at: str, conn=None) -> int:
    """สร้างรหัส OTP ใหม่ และทำให้รหัสเก่าที่ยังไม่ใช้ของ (email, purpose) เดียวกันหมดอายุ"""
    clean_email = (email or "").strip().lower()
    with use_conn(conn) as c:
        c.execute(
            "UPDATE email_otps SET used_at = datetime('now','localtime') "
            "WHERE email = ? AND purpose = ? AND used_at IS NULL",
            (clean_email, purpose),
        )
        return c.execute(
            "INSERT INTO email_otps (email, purpose, code_hash, expires_at) VALUES (?, ?, ?, ?)",
            (clean_email, purpose, code_hash, expires_at),
        ).lastrowid


def delete_otp(otp_id: int, conn=None) -> bool:
    """ลบแถว OTP ออกจากตารางทันที (ใช้กรณีส่งอีเมลไม่สำเร็จเพื่อไม่ให้มีรหัสค้างในฐานข้อมูล)"""
    with use_conn(conn) as c:
        return c.execute("DELETE FROM email_otps WHERE id = ?", (int(otp_id),)).rowcount > 0


def get_latest_active_otp(email: str, purpose: str, conn=None):
    """ดึง OTP ล่าสุดที่ยังไม่ถูกใช้งานของ (email, purpose)"""
    clean_email = (email or "").strip().lower()
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM email_otps WHERE email = ? AND purpose = ? AND used_at IS NULL "
            "ORDER BY id DESC LIMIT 1",
            (clean_email, purpose),
        ).fetchone()


def increment_attempts(otp_id: int, conn=None) -> int:
    """เพิ่มจำนวนครั้งที่กรอกผิด +1 และคืนค่าจำนวนครั้งล่าสุด"""
    with use_conn(conn) as c:
        c.execute("UPDATE email_otps SET attempts = attempts + 1 WHERE id = ?", (int(otp_id),))
        row = c.execute("SELECT attempts FROM email_otps WHERE id = ?", (int(otp_id),)).fetchone()
        return int(row["attempts"]) if row else 0


def mark_used(otp_id: int, conn=None) -> bool:
    """
    ทำเครื่องหมายว่ารหัส OTP ถูกใช้งานแล้วแบบอะตอมมิก (Atomic conditional update):
    คืน True เฉพาะคำขอแรกที่เปลี่ยน used_at จาก NULL เป็นเวลาปัจจุบันสำเร็จเท่านั้น
    คำขอซ้ำที่แข่งกัน (race condition) จะได้ rowcount == 0 -> คืน False
    """
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE email_otps SET used_at = datetime('now','localtime') "
            "WHERE id = ? AND used_at IS NULL",
            (int(otp_id),),
        ).rowcount > 0


def count_recent_otps(email: str, purpose: str, within_seconds: int, conn=None) -> int:
    """นับจำนวน OTP ที่ถูกสร้างภายใน within_seconds วินาทีที่ผ่านมา (ใช้จำกัดการส่งซ้ำ)"""
    clean_email = (email or "").strip().lower()
    with use_conn(conn) as c:
        row = c.execute(
            "SELECT COUNT(*) AS n FROM email_otps WHERE email = ? AND purpose = ? "
            "AND created_at >= datetime('now','localtime', ?)",
            (clean_email, purpose, f"-{int(within_seconds)} seconds"),
        ).fetchone()
        return int(row["n"]) if row else 0


def get_latest_otp_any(email: str, purpose: str, conn=None):
    """ดึง OTP ล่าสุด (ไม่ว่าจะใช้แล้วหรือไม่) เพื่อเช็ค cooldown 60 วินาที"""
    clean_email = (email or "").strip().lower()
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM email_otps WHERE email = ? AND purpose = ? ORDER BY id DESC LIMIT 1",
            (clean_email, purpose),
        ).fetchone()


# ---------- OTP สำหรับการเปลี่ยนอีเมลในหน้าโปรไฟล์ (email_change_otps — T11) ----------

def create_email_change_otp(user_id: int, new_email: str, code_hash: str, expires_at: str, conn=None) -> int:
    """สร้างรหัส OTP สำหรับยืนยันอีเมลใหม่ และยกเลิกรหัสเก่าที่ยังไม่ใช้ของผู้ใช้คนนั้น"""
    clean_email = (new_email or "").strip().lower()
    with use_conn(conn) as c:
        c.execute(
            "UPDATE email_change_otps SET used_at = datetime('now','localtime') "
            "WHERE user_id = ? AND used_at IS NULL",
            (int(user_id),),
        )
        return c.execute(
            "INSERT INTO email_change_otps (user_id, new_email, code_hash, expires_at) VALUES (?, ?, ?, ?)",
            (int(user_id), clean_email, code_hash, expires_at),
        ).lastrowid


def delete_email_change_otp(otp_id: int, conn=None) -> bool:
    """ลบแถว OTP เปลี่ยนอีเมลออกจากตารางทันที (ใช้กรณีส่งอีเมลไม่สำเร็จ)"""
    with use_conn(conn) as c:
        return c.execute("DELETE FROM email_change_otps WHERE id = ?", (int(otp_id),)).rowcount > 0


def get_latest_active_email_change_otp(user_id: int, new_email: str, conn=None):
    clean_email = (new_email or "").strip().lower()
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM email_change_otps WHERE user_id = ? AND new_email = ? AND used_at IS NULL "
            "ORDER BY id DESC LIMIT 1",
            (int(user_id), clean_email),
        ).fetchone()


def get_latest_email_change_otp_any(user_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM email_change_otps WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (int(user_id),),
        ).fetchone()


def increment_email_change_attempts(otp_id: int, conn=None) -> int:
    with use_conn(conn) as c:
        c.execute("UPDATE email_change_otps SET attempts = attempts + 1 WHERE id = ?", (int(otp_id),))
        row = c.execute("SELECT attempts FROM email_change_otps WHERE id = ?", (int(otp_id),)).fetchone()
        return int(row["attempts"]) if row else 0


def mark_email_change_used(otp_id: int, conn=None) -> bool:
    """ทำเครื่องหมายว่า OTP เปลี่ยนอีเมลถูกใช้แล้วแบบอะตอมมิก (used_at IS NULL)"""
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE email_change_otps SET used_at = datetime('now','localtime') "
            "WHERE id = ? AND used_at IS NULL",
            (int(otp_id),),
        ).rowcount > 0


def count_recent_email_change_otps(user_id: int, within_seconds: int, conn=None, new_email: str = None) -> int:
    with use_conn(conn) as c:
        if new_email is not None:
            clean_email = new_email.strip().lower()
            row = c.execute(
                "SELECT COUNT(*) AS n FROM email_change_otps WHERE (user_id = ? OR new_email = ?) "
                "AND created_at >= datetime('now','localtime', ?)",
                (int(user_id), clean_email, f"-{int(within_seconds)} seconds"),
            ).fetchone()
        else:
            row = c.execute(
                "SELECT COUNT(*) AS n FROM email_change_otps WHERE user_id = ? "
                "AND created_at >= datetime('now','localtime', ?)",
                (int(user_id), f"-{int(within_seconds)} seconds"),
            ).fetchone()
        return int(row["n"]) if row else 0


def purge_expired(conn=None) -> int:
    """ลบรหัส OTP ที่หมดอายุแล้วออกจากตาราง email_otps และ email_change_otps"""
    with use_conn(conn) as c:
        n1 = c.execute("DELETE FROM email_otps WHERE expires_at <= datetime('now','localtime')").rowcount
        n2 = c.execute("DELETE FROM email_change_otps WHERE expires_at <= datetime('now','localtime')").rowcount
        return int(n1 or 0) + int(n2 or 0)
