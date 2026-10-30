"""
database/repo_payments.py
การชำระเงิน/สลิป (ตาราง payments) — ไม่มี business logic
"""
from database.repo_base import use_conn

_SELECT = (
    "SELECT pay.*, o.user_id AS buyer_id, o.total AS order_total, o.status AS order_status, "
    "u.full_name AS buyer_name, u.username AS buyer_username "
    "FROM payments pay JOIN orders o ON o.id = pay.order_id JOIN users u ON u.id = o.user_id"
)


def create(order_id: int, method: str, amount: float, slip_path=None, conn=None) -> int:
    """สร้างรายการชำระเงิน (สถานะ pending) คืน payment id"""
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO payments (order_id, method, amount, slip_path) VALUES (?, ?, ?, ?)",
            (order_id, method, round(amount, 2), slip_path),
        ).lastrowid


def get(payment_id: int, conn=None):
    """รายการชำระเงิน 1 รายการ (join ออเดอร์/ผู้ซื้อ) หรือ None"""
    with use_conn(conn) as c:
        return c.execute(_SELECT + " WHERE pay.id = ?", (payment_id,)).fetchone()


def get_latest_by_order(order_id: int, conn=None):
    """รายการล่าสุดของออเดอร์ (ส่งสลิปใหม่หลังถูกปฏิเสธจะมีหลายแถว) หรือ None"""
    with use_conn(conn) as c:
        return c.execute(_SELECT + " WHERE pay.order_id = ? ORDER BY pay.id DESC LIMIT 1",
                         (order_id,)).fetchone()


def list_by_order(order_id: int, conn=None):
    """ประวัติการส่งสลิปทั้งหมดของออเดอร์ เก่า -> ใหม่"""
    with use_conn(conn) as c:
        return c.execute(_SELECT + " WHERE pay.order_id = ? ORDER BY pay.id", (order_id,)).fetchall()


def list_pending(conn=None):
    """สลิปที่รอตรวจ (pending) เก่าสุดก่อน"""
    with use_conn(conn) as c:
        return c.execute(_SELECT + " WHERE pay.status = 'pending' ORDER BY pay.id").fetchall()


def mark_verified(payment_id: int, verified_by: int, conn=None) -> bool:
    """ยืนยันสลิป — ทำได้เฉพาะที่ยัง pending (กดซ้ำ -> False)"""
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE payments SET status = 'verified', verified_by = ?, "
            "verified_at = datetime('now','localtime') WHERE id = ? AND status = 'pending'",
            (verified_by, payment_id),
        ).rowcount > 0


def mark_rejected(payment_id: int, reason: str, verified_by: int, conn=None) -> bool:
    """ปฏิเสธสลิป (เก็บเหตุผล + ผู้ตรวจ + เวลา) — เฉพาะที่ยัง pending"""
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE payments SET status = 'rejected', reject_reason = ?, verified_by = ?, "
            "verified_at = datetime('now','localtime') WHERE id = ? AND status = 'pending'",
            (reason, verified_by, payment_id),
        ).rowcount > 0
