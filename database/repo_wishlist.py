"""
database/repo_wishlist.py
รายการโปรด (ตาราง wishlist)
"""
from database.repo_base import EFFECTIVE_PRICE_SQL, use_conn


def add(user_id: int, product_id: int, conn=None) -> bool:
    """เพิ่มเข้ารายการโปรด (มีอยู่แล้วไม่ทำซ้ำ) คืน True ถ้าเพิ่มใหม่จริง"""
    with use_conn(conn) as c:
        return c.execute("INSERT OR IGNORE INTO wishlist (user_id, product_id) VALUES (?, ?)",
                         (user_id, product_id)).rowcount > 0


def remove(user_id: int, product_id: int, conn=None) -> bool:
    """เอาออกจากรายการโปรด"""
    with use_conn(conn) as c:
        return c.execute("DELETE FROM wishlist WHERE user_id = ? AND product_id = ?",
                         (user_id, product_id)).rowcount > 0


def is_in(user_id: int, product_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("SELECT 1 FROM wishlist WHERE user_id = ? AND product_id = ?",
                         (user_id, product_id)).fetchone() is not None


def list(user_id: int, conn=None):  # noqa: A001 (ชื่อตามที่กำหนดในแผน)
    """สินค้าในรายการโปรด (เฉพาะที่ยังเปิดขายและไม่ถูกลบ) เพิ่มล่าสุดก่อน พร้อม effective_price"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT p.*, c.name AS category_name, b.name AS brand_name, "
            f"{EFFECTIVE_PRICE_SQL} AS effective_price, w.created_at AS wished_at "
            "FROM wishlist w JOIN products p ON p.id = w.product_id "
            "JOIN categories c ON c.id = p.category_id JOIN brands b ON b.id = p.brand_id "
            "WHERE w.user_id = ? AND p.is_active = 1 AND p.deleted_at IS NULL "
            "AND c.is_active = 1 AND c.deleted_at IS NULL AND b.is_active = 1 AND b.deleted_at IS NULL "
            "ORDER BY w.created_at DESC, p.id DESC",
            (user_id,),
        ).fetchall()


def ids(user_id: int, conn=None) -> set:
    """set ของ product_id ที่ผู้ใช้กดหัวใจไว้ (เช็คทีละการ์ดในกริดได้เร็ว)"""
    with use_conn(conn) as c:
        rows = c.execute("SELECT product_id FROM wishlist WHERE user_id = ?", (user_id,)).fetchall()
    return {r["product_id"] for r in rows}
