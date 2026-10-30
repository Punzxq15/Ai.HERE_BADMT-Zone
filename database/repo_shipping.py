"""
database/repo_shipping.py
การจัดส่ง (ตาราง shipments) — หนึ่งออเดอร์มีหนึ่งแถว (สร้างตอนชำระเงินยืนยัน)
"""
from database.repo_base import use_conn


def create(order_id: int, carrier=None, tracking_no=None, status: str = "preparing", conn=None) -> int:
    """สร้างข้อมูลจัดส่ง (ค่าเริ่มต้น preparing) คืน id"""
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO shipments (order_id, carrier, tracking_no, status) VALUES (?, ?, ?, ?)",
            (order_id, carrier, tracking_no, status),
        ).lastrowid


def get_by_order(order_id: int, conn=None):
    """ข้อมูลจัดส่งของออเดอร์ (แถวล่าสุด) หรือ None"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM shipments WHERE order_id = ? ORDER BY id DESC LIMIT 1",
                         (order_id,)).fetchone()


def update(order_id: int, carrier=None, tracking_no=None, status=None, conn=None) -> bool:
    """
    แก้ข้อมูลจัดส่งของออเดอร์ — ค่าที่เป็น None = ไม่เปลี่ยน (ใช้ COALESCE) และอัปเดต updated_at เสมอ
    ไม่มีแถวของออเดอร์นี้ -> False
    """
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE shipments SET carrier = COALESCE(?, carrier), "
            "tracking_no = COALESCE(?, tracking_no), status = COALESCE(?, status), "
            "updated_at = datetime('now','localtime') "
            "WHERE id = (SELECT id FROM shipments WHERE order_id = ? ORDER BY id DESC LIMIT 1)",
            (carrier, tracking_no, status, order_id),
        ).rowcount > 0
