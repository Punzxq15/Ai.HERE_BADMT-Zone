"""
services/staff_service.py
จัดการบัญชีพนักงาน/แอดมินและเซสชันของร้าน (เฉพาะเจ้าของร้าน — action user.manage):
- เลือกอีเมลผู้ใช้ที่มีอยู่แล้วในระบบ แล้วกำหนดบทบาทเป็น Admin พร้อมตั้งรหัสผ่านใหม่และยืนยันรหัสผ่าน (ตามข้อกำหนด PDF)
- หรือสร้างบัญชี Admin ใหม่จากอีเมล
- ตั้งรหัสผ่านชั่วคราว (บังคับเปลี่ยนรหัสเมื่อเข้าสู่ระบบครั้งแรก)
- สั่งออกจากระบบทุกเครื่อง (revoke sessions)
- ดูข้อมูลรายละเอียดของลูกค้าและแอดมินทุกคนได้ (ข้อ 12 — ไม่รวมรหัสผ่าน)
"""
from core import permissions
from core.constants import ORDER_STATUS_LABELS, ROLE_ADMIN, ROLE_BUYER, ROLE_LABELS, ROLE_OWNER
from database import repo_addresses, repo_orders, repo_sessions, repo_users
from database.db import transaction
from services import audit_service, auth_service
from utils import validators


def list_staff() -> list[dict]:
    """รายชื่อเจ้าของร้านและแอดมินทั้งหมด"""
    permissions.require(permissions.USER_MANAGE)
    rows = repo_users.list_users(role=[ROLE_OWNER, ROLE_ADMIN])
    return [dict(r) for r in rows]


def list_promotable_buyers() -> list[dict]:
    """รายชื่อบัญชีผู้ซื้อที่ยืนยันอีเมลแล้ว สำหรับให้เจ้าของร้านเลือกอีเมลมาแต่งตั้งเป็นแอดมิน"""
    permissions.require(permissions.USER_MANAGE)
    rows = repo_users.list_users(role=ROLE_BUYER)
    return [dict(r) for r in rows if int(r["email_verified"] if "email_verified" in r.keys() else 1)]


def get_user_full_detail(user_id: int) -> dict:
    """
    เจ้าของร้านกดดูข้อมูลรายละเอียดของลูกค้าทุกคน รวมถึงแอดมิน (ข้อ 12)
    ห้ามแสดง password_hash หรือข้อมูลลับเด็ดขาด
    คืน dict: user (ข้อมูลโปรไฟล์), addresses (ที่อยู่จัดส่ง), orders (ประวัติคำสั่งซื้อ), stats (สรุปยอด)
    """
    permissions.require(permissions.USER_MANAGE)
    row = repo_users.get_by_id(int(user_id))
    if row is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")

    pub = auth_service._public_user(row)
    pub["role_label"] = ROLE_LABELS.get(pub["role"], pub["role"])
    pub["email_verified"] = bool(int(row["email_verified"])) if "email_verified" in row.keys() and row["email_verified"] is not None else True
    pub["last_login_at"] = row["last_login_at"] if "last_login_at" in row.keys() else None

    addresses = [dict(a) for a in repo_addresses.list(int(user_id))]
    order_rows = repo_orders.list_orders(user_id=int(user_id), limit=25, offset=0)
    orders = []
    total_spent = 0.0
    paid_count = 0
    for o in order_rows:
        od = dict(o)
        od["status_label"] = ORDER_STATUS_LABELS.get(od["status"], od["status"])
        if od["status"] in repo_orders.REVENUE_STATUSES:
            total_spent += float(od["total"] or 0)
            paid_count += 1
        orders.append(od)

    active_sessions = [dict(s) for s in repo_sessions.list_active_sessions(user_id=int(user_id))]
    return {
        "user": pub,
        "addresses": addresses,
        "orders": orders,
        "stats": {
            "total_orders": repo_orders.count_orders(user_id=int(user_id)),
            "paid_orders": paid_count,
            "total_spent": round(total_spent, 2),
            "active_sessions": len(active_sessions),
        },
    }


def promote_to_admin(email: str, new_password: str, confirm_password: str = None) -> dict:
    """
    เจ้าของร้านเลือกอีเมลที่มีอยู่แล้วในระบบ (หรือเป็นแอดมินอยู่แล้ว) กำหนด role เป็น Admin
    พร้อมตั้งรหัสผ่านและยืนยันรหัสผ่านใหม่
    """
    permissions.require(permissions.USER_MANAGE)
    email = (email or "").strip().lower()
    if not validators.is_valid_email(email):
        raise ValueError("กรุณาเลือกหรือกรอกอีเมลที่ถูกต้อง")
    new_password = new_password or ""
    if confirm_password is not None and new_password != confirm_password:
        raise ValueError("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
    auth_service._check_new_password(new_password)

    target = repo_users.get_by_email(email)
    if target is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้ที่มีอีเมลนี้ในระบบ")
    if target["role"] == ROLE_OWNER:
        raise ValueError("ไม่สามารถเปลี่ยนบทบาทของบัญชีเจ้าของร้านได้")

    pwd_hash = auth_service.hash_password(new_password)
    with transaction() as conn:
        repo_users.update_role_and_password(
            target["id"], ROLE_ADMIN, pwd_hash, email_verified=True, must_change=False, conn=conn
        )
        repo_users.set_active(target["id"], True, conn=conn)
        repo_sessions.delete_user_sessions(target["id"], conn=conn)
        audit_service.log(
            "staff.promote_to_admin", "user", target["id"],
            {"email": email, "previous_role": target["role"]}, conn=conn,
        )
        updated = repo_users.get_by_id(target["id"], conn=conn)
    return auth_service._public_user(updated)


def assign_admin_by_email(email: str, password: str, confirm_password: str,
                          full_name: str = None, phone: str = None, username: str = None) -> dict:
    """
    รองรับทั้ง 2 กรณี (D7):
    1. ถ้าอีเมลมีบัญชีผู้ใช้อยู่แล้ว -> เลื่อนขั้นเป็น Admin และตั้งรหัสผ่านใหม่ตามที่กำหนด
    2. ถ้าอีเมลยังไม่มีในระบบ -> สร้างบัญชี Admin ใหม่ (email_verified=1)
    """
    permissions.require(permissions.USER_MANAGE)
    email = (email or "").strip().lower()
    if not validators.is_valid_email(email):
        raise ValueError("รูปแบบอีเมลไม่ถูกต้อง")
    if (password or "") != (confirm_password or ""):
        raise ValueError("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
    auth_service._check_new_password(password or "")

    existing = repo_users.get_by_email(email)
    if existing is not None:
        return promote_to_admin(email, password, confirm_password)

    uname = auth_service._generate_unique_username(email, preferred=username)
    name = (full_name or "").strip() or email.split("@", 1)[0]
    clean_phone = (phone or "").strip()
    return auth_service.create_staff(uname, email, password, name, clean_phone, role=ROLE_ADMIN)


def reset_user_password(user_id: int, temp_password: str, confirm_password: str = None,
                        must_change: bool = True) -> dict:
    """
    เจ้าของร้านตั้งรหัสผ่านใหม่/รหัสชั่วคราวให้แอดมินหรือผู้ซื้อ (บังคับเปลี่ยนรหัสเมื่อเข้าครั้งแรก และเตะเซสชันเดิม)
    """
    permissions.require(permissions.USER_MANAGE)
    if confirm_password is not None and (temp_password or "") != confirm_password:
        raise ValueError("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
    auth_service._check_new_password(temp_password or "")

    target = repo_users.get_by_id(user_id)
    if target is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")

    pwd_hash = auth_service.hash_password(temp_password)
    with transaction() as conn:
        repo_users.update_password(user_id, pwd_hash, must_change=must_change, conn=conn)
        repo_sessions.delete_user_sessions(user_id, conn=conn)
        audit_service.log(
            "staff.reset_password", "user", user_id,
            {"email": target["email"], "must_change": bool(must_change)}, conn=conn,
        )
        updated = repo_users.get_by_id(user_id, conn=conn)
    return auth_service._public_user(updated)


def revoke_sessions(user_id: int) -> int:
    """สั่งออกจากระบบทุกเครื่องของผู้ใช้นี้ (เจ้าของร้านเท่านั้น)"""
    permissions.require(permissions.USER_MANAGE)
    target = repo_users.get_by_id(user_id)
    if target is None:
        raise ValueError("ไม่พบบัญชีผู้ใช้")
    with transaction() as conn:
        count = repo_sessions.delete_user_sessions(user_id, conn=conn)
        repo_users.set_online(user_id, False, conn=conn)
        audit_service.log("staff.revoke_sessions", "user", user_id, {"revoked": count}, conn=conn)
    return count


def list_active_sessions(user_id: int = None) -> list[dict]:
    """ดูรายการเซสชันที่ยังล็อกอินค้างอยู่ (เจ้าของร้านเท่านั้น)"""
    permissions.require(permissions.USER_MANAGE)
    return [dict(r) for r in repo_sessions.list_active_sessions(user_id=user_id)]
