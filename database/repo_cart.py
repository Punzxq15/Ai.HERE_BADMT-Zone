"""
database/repo_cart.py
ตะกร้าสินค้า (ตาราง cart_items) — ไม่มี business logic (ตรวจสต็อก/คำนวณราคาอยู่ที่ service)
"""
from database.repo_base import EFFECTIVE_PRICE_SQL, use_conn

_ITEM_SELECT = (
    "SELECT ci.id AS cart_item_id, ci.user_id, ci.product_id, ci.option_id, ci.qty, "
    "COALESCE(ci.is_selected, 1) AS is_selected, "
    "p.name AS product_name, p.price, p.sale_price, p.sale_ends_at, p.image_path, "
    "p.stock AS product_stock, p.is_active AS product_active, p.deleted_at AS product_deleted_at, "
    f"{EFFECTIVE_PRICE_SQL} AS effective_price, "
    "po.option_type, po.option_value, COALESCE(po.extra_price, 0) AS extra_price, "
    "po.stock AS option_stock "
    "FROM cart_items ci JOIN products p ON p.id = ci.product_id "
    "LEFT JOIN product_options po ON po.id = ci.option_id"
)


def list_items(user_id: int, conn=None):
    """รายการในตะกร้า (join สินค้า/ตัวเลือก + effective_price) เรียงตามที่เพิ่มก่อน"""
    with use_conn(conn) as c:
        return c.execute(_ITEM_SELECT + " WHERE ci.user_id = ? ORDER BY ci.id", (user_id,)).fetchall()


def get_item(user_id: int, cart_item_id: int, conn=None):
    """แถวในตะกร้า 1 แถว (ต้องเป็นของ user นี้) หรือ None"""
    with use_conn(conn) as c:
        return c.execute(_ITEM_SELECT + " WHERE ci.user_id = ? AND ci.id = ?",
                         (user_id, cart_item_id)).fetchone()


def add_or_increase(user_id: int, product_id: int, option_id, qty: int = 1, conn=None) -> int:
    """
    เพิ่มสินค้า+ตัวเลือกเดียวกันที่มีอยู่แล้ว -> บวกจำนวน, ไม่มี -> เพิ่มแถวใหม่
    option_id = None คือสินค้าไม่มีตัวเลือก  คืน id ของแถวในตะกร้า
    """
    with use_conn(conn) as c:
        row = c.execute(
            "SELECT id FROM cart_items WHERE user_id = ? AND product_id = ? AND option_id IS ?",
            (user_id, product_id, option_id),
        ).fetchone()
        if row:
            c.execute("UPDATE cart_items SET qty = qty + ?, is_selected = 1 WHERE id = ?", (qty, row["id"]))
            return row["id"]
        return c.execute(
            "INSERT INTO cart_items (user_id, product_id, option_id, qty, is_selected) VALUES (?, ?, ?, ?, 1)",
            (user_id, product_id, option_id, qty),
        ).lastrowid


def set_qty(user_id: int, cart_item_id: int, qty: int, conn=None) -> bool:
    """ตั้งจำนวนของแถวนั้น (service ต้องกันค่า < 1 เอง)"""
    with use_conn(conn) as c:
        return c.execute("UPDATE cart_items SET qty = ? WHERE id = ? AND user_id = ?",
                         (qty, cart_item_id, user_id)).rowcount > 0


def set_selected(user_id: int, cart_item_id: int, selected: bool, conn=None) -> bool:
    """ตั้งสถานะเลือก/ไม่เลือกรายการในตะกร้า"""
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE cart_items SET is_selected = ? WHERE id = ? AND user_id = ?",
            (1 if selected else 0, cart_item_id, user_id),
        ).rowcount > 0


def set_all_selected(user_id: int, selected: bool, conn=None) -> int:
    """เลือกหรือยกเลิกเลือกสินค้าทั้งหมดในตะกร้าของผู้ใช้"""
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE cart_items SET is_selected = ? WHERE user_id = ?",
            (1 if selected else 0, user_id),
        ).rowcount


def remove(user_id: int, cart_item_id: int, conn=None) -> bool:
    """ลบแถวเดียวออกจากตะกร้า"""
    with use_conn(conn) as c:
        return c.execute("DELETE FROM cart_items WHERE id = ? AND user_id = ?",
                         (cart_item_id, user_id)).rowcount > 0


def remove_many(user_id: int, cart_item_ids, conn=None) -> int:
    """ลบหลายแถวที่ระบุออกจากตะกร้าของผู้ใช้"""
    ids = [int(i) for i in (cart_item_ids or [])]
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    with use_conn(conn) as c:
        return c.execute(
            f"DELETE FROM cart_items WHERE user_id = ? AND id IN ({placeholders})",
            [user_id, *ids],
        ).rowcount


def remove_selected(user_id: int, conn=None) -> int:
    """ลบเฉพาะรายการที่ติ๊กเลือกออกจากตะกร้าของผู้ใช้"""
    with use_conn(conn) as c:
        return c.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND COALESCE(is_selected, 1) = 1",
            (user_id,),
        ).rowcount


def clear(user_id: int, conn=None) -> int:
    """ล้างตะกร้าทั้งหมดของผู้ใช้ คืนจำนวนแถวที่ลบ"""
    with use_conn(conn) as c:
        return c.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,)).rowcount


def count(user_id: int, conn=None) -> int:
    """จำนวนชิ้นรวมในตะกร้า (ผลรวม qty) ใช้โชว์เลขบน navbar"""
    with use_conn(conn) as c:
        return c.execute("SELECT COALESCE(SUM(qty), 0) AS n FROM cart_items WHERE user_id = ?",
                         (user_id,)).fetchone()["n"]
