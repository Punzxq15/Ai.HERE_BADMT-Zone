"""
tools/reset_password.py
สคริปต์ CLI สำหรับเจ้าของร้านรันบนเครื่องร้านเพื่อตั้งรหัสผ่านใหม่ให้บัญชี Owner หรือ Admin (กรณีลืมรหัสผ่าน D14)
รันจากโฟลเดอร์ root ของโปรเจกต์:
    python -m tools.reset_password
"""
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.constants import ROLE_ADMIN, ROLE_OWNER  # noqa: E402
from database import db, repo_audit, repo_sessions, repo_users  # noqa: E402
from services import auth_service  # noqa: E402


def reset_staff_password_by_email(email: str, new_password: str, confirm_password: str = None) -> dict:
    """
    ตั้งรหัสผ่านใหม่ให้บัญชี owner หรือ admin จากอีเมล (ฟังก์ชันแกนกลาง ใช้ทดสอบอัตโนมัติได้)
    - บังคับเปลี่ยนรหัสเมื่อเข้าสู่ระบบครั้งแรก (must_change_password = 1)
    - ลบเซสชันที่ค้างอยู่ทุกเครื่องของบัญชีนั้น
    - บันทึกเหตุการณ์ลงตาราง audit_log โดยไม่เก็บรหัสผ่าน
    """
    db.init_db()
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("กรุณากรอกอีเมล")
    if confirm_password is not None and (new_password or "") != confirm_password:
        raise ValueError("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
    auth_service._check_new_password(new_password or "")

    user = repo_users.get_by_email(email)
    if user is None or user["role"] not in (ROLE_OWNER, ROLE_ADMIN):
        raise ValueError("ไม่พบบัญชีเจ้าของร้านหรือแอดมินที่ใช้อีเมลนี้")

    pwd_hash = auth_service.hash_password(new_password)
    with db.transaction() as conn:
        repo_users.update_password(user["id"], pwd_hash, must_change=True, conn=conn)
        repo_sessions.delete_user_sessions(user["id"], conn=conn)
        repo_users.set_online(user["id"], False, conn=conn)
        repo_audit.insert_log(
            actor_id=user["id"],
            actor_role="cli_local",
            action="cli.reset_staff_password",
            target_type="user",
            target_id=user["id"],
            detail=f'{{"email": "{email}", "role": "{user["role"]}"}}',
            conn=conn,
        )
        updated = repo_users.get_by_id(user["id"], conn=conn)
    return auth_service._public_user(updated)


def main() -> int:
    print("=== เครื่องมือรีเซ็ตรหัสผ่านพนักงาน/เจ้าของร้าน (AI.HERE BADᴍᴛ-Zone) ===")
    email = input("กรอกอีเมลบัญชี Owner หรือ Admin: ").strip()
    pwd1 = getpass.getpass("รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร): ")
    pwd2 = getpass.getpass("ยืนยันรหัสผ่านใหม่: ")
    try:
        user = reset_staff_password_by_email(email, pwd1, pwd2)
        print(f"สำเร็จ: ตั้งรหัสผ่านใหม่ให้ {user['email']} ({user['role']}) เรียบร้อยแล้ว")
        print("หมายเหตุ: ระบบได้ออกจากระบบทุกเครื่อง และจะให้เปลี่ยนรหัสผ่านอีกครั้งเมื่อเข้าสู่ระบบ")
        return 0
    except ValueError as exc:
        print(f"ผิดพลาด: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
