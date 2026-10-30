"""
database/repo_orders.py
ออเดอร์ + รายการสินค้าในออเดอร์ + ประวัติสถานะ + สถิติ Dashboard + รายงานช่วงเวลา (.xlsx Export)
ไม่มี business logic: ลำดับสถานะ/สิทธิ์/ตัดสต็อก อยู่ที่ order_service
ฟังก์ชันเขียนรับ conn= เพื่อให้ service ครอบ transaction เดียว
"""
from core.constants import (
    ORDER_STATUSES, ORDER_STATUS_CANCELLED, ORDER_STATUS_COMPLETED,
    ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED,
)
from database.repo_base import as_list, use_conn

# สถานะที่นับเป็น "รายได้" (เงินเข้าแล้วและไม่ถูกยกเลิก)
REVENUE_STATUSES = (ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, ORDER_STATUS_COMPLETED)
_REV_IN = ",".join(f"'{s}'" for s in REVENUE_STATUSES)

_ORDER_SELECT = (
    "SELECT o.*, u.username AS buyer_username, u.full_name AS buyer_name, u.email AS buyer_email, "
    "(SELECT COALESCE(SUM(qty), 0) FROM order_items WHERE order_id = o.id) AS item_count "
    "FROM orders o JOIN users u ON u.id = o.user_id"
)


# ==========================================
# ออเดอร์
# ==========================================

def create_order(user_id: int, recipient_name: str, recipient_phone: str, shipping_address: str,
                 subtotal: float, discount: float, shipping_fee: float, total: float,
                 coupon_id=None, conn=None) -> int:
    """สร้างออเดอร์ (สถานะเริ่มต้น pending ตาม schema) คืน order id"""
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO orders (user_id, recipient_name, recipient_phone, shipping_address, "
            "subtotal, discount, shipping_fee, total, coupon_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, recipient_name, recipient_phone, shipping_address,
             round(subtotal, 2), round(discount, 2), round(shipping_fee, 2), round(total, 2), coupon_id),
        ).lastrowid


def add_items(order_id: int, items, conn=None) -> int:
    """
    เพิ่มรายการสินค้าในออเดอร์ items = list ของ dict:
    product_id, option_id (None ได้), product_name, option_label (None ได้), price_at_purchase, qty
    """
    rows = [
        (order_id, i["product_id"], i.get("option_id"), i["product_name"], i.get("option_label"),
         round(i["price_at_purchase"], 2), i["qty"])
        for i in items
    ]
    with use_conn(conn) as c:
        c.executemany(
            "INSERT INTO order_items (order_id, product_id, option_id, product_name, option_label, "
            "price_at_purchase, qty) VALUES (?, ?, ?, ?, ?, ?, ?)", rows,
        )
    return len(rows)


def get_order(order_id: int, conn=None):
    """ออเดอร์ 1 รายการ (มี buyer_username/buyer_name/item_count) หรือ None"""
    with use_conn(conn) as c:
        return c.execute(_ORDER_SELECT + " WHERE o.id = ?", (order_id,)).fetchone()


def _list_where(user_id, status, search, unreviewed_only=False):
    where, params = [], []
    if user_id is not None:
        where.append("o.user_id = ?")
        params.append(user_id)
    if unreviewed_only:
        where.append("o.status = 'completed'")
        where.append(
            "EXISTS(SELECT 1 FROM order_items oi WHERE oi.order_id = o.id "
            "AND NOT EXISTS(SELECT 1 FROM reviews r WHERE r.order_id = o.id "
            "AND r.product_id = oi.product_id AND r.user_id = o.user_id) "
            "AND NOT EXISTS(SELECT 1 FROM review_skips rs WHERE rs.order_id = o.id "
            "AND rs.product_id = oi.product_id AND rs.user_id = o.user_id))"
        )
    elif status:
        statuses = as_list(status)
        where.append(f"o.status IN ({','.join('?' * len(statuses))})")
        params += statuses
    if search and str(search).strip():
        s = str(search).strip().lstrip("#")
        where.append("(CAST(o.id AS TEXT) = ? OR u.username LIKE ? OR u.full_name LIKE ? "
                     "OR o.recipient_name LIKE ?)")
        params += [s, f"%{s}%", f"%{s}%", f"%{s}%"]
    return (" WHERE " + " AND ".join(where)) if where else "", params


def list_orders(user_id=None, status=None, limit: int = 50, offset: int = 0,
                search=None, unreviewed_only: bool = False, conn=None):
    """
    รายการออเดอร์ใหม่สุดก่อน — user_id=None = ทุกคน (ฝั่งแอดมิน)
    status: ค่าเดียวหรือ list | search: เลขออเดอร์/ username/ชื่อผู้ซื้อ/ชื่อผู้รับ
    unreviewed_only: True = เฉพาะออเดอร์ completed ที่ยังมีสินค้าไม่ถูกรีวิว (แท็บ 'รอรีวิว')
    """
    where, params = _list_where(user_id, status, search, unreviewed_only=unreviewed_only)
    sql = _ORDER_SELECT + where + " ORDER BY o.id DESC"
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [int(limit), int(offset or 0)]
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def count_orders(user_id=None, status=None, search=None, unreviewed_only: bool = False, conn=None) -> int:
    """จำนวนออเดอร์ตามเงื่อนไขเดียวกับ list_orders (ใช้แบ่งหน้า)"""
    where, params = _list_where(user_id, status, search, unreviewed_only=unreviewed_only)
    with use_conn(conn) as c:
        return c.execute("SELECT COUNT(*) AS n FROM orders o JOIN users u ON u.id = o.user_id" + where,
                         params).fetchone()["n"]


def update_status(order_id: int, status: str, expected_status=None, conn=None) -> bool:
    """
    เปลี่ยนสถานะออเดอร์
    expected_status: ถ้าระบุ จะเปลี่ยนก็ต่อเมื่อสถานะปัจจุบันตรงกัน (กันกดซ้ำ/แข่งกัน) -> ไม่ตรงคืน False
    """
    sql, params = "UPDATE orders SET status = ? WHERE id = ?", [status, order_id]
    if expected_status is not None:
        sql += " AND status = ?"
        params.append(expected_status)
    with use_conn(conn) as c:
        return c.execute(sql, params).rowcount > 0


def set_cancel_reason(order_id: int, reason: str, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("UPDATE orders SET cancel_reason = ? WHERE id = ?",
                         (reason, order_id)).rowcount > 0


def list_items(order_id: int, conn=None):
    """รายการสินค้าในออเดอร์ (พร้อม image_path ปัจจุบันของสินค้า ไว้แสดงรูปย่อ)"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT oi.*, p.image_path AS image_path FROM order_items oi "
            "LEFT JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ? ORDER BY oi.id",
            (order_id,),
        ).fetchall()


def list_expired_pending(hours, conn=None):
    """ออเดอร์ pending ที่สร้างมานานเกิน hours ชั่วโมง (ไว้ยกเลิกอัตโนมัติ)"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM orders WHERE status = 'pending' "
            "AND created_at <= datetime('now', 'localtime', ?) ORDER BY id",
            (f"-{float(hours)} hours",),
        ).fetchall()


def find_completed_order_with_product(user_id: int, product_id: int, conn=None):
    """
    ออเดอร์ completed ของผู้ใช้ที่มีสินค้านี้ — เลือกอันที่ "ยังไม่รีวิว" ก่อน แล้วค่อยเอาใหม่สุด
    คืน Row (id, status, ..., already_reviewed 0/1) หรือ None ถ้าไม่เคยซื้อ/ยังไม่ completed
    """
    with use_conn(conn) as c:
        return c.execute(
            "SELECT o.*, CASE WHEN EXISTS(SELECT 1 FROM reviews r WHERE r.user_id = o.user_id "
            "AND r.product_id = ? AND r.order_id = o.id) "
            "OR EXISTS(SELECT 1 FROM review_skips rs WHERE rs.user_id = o.user_id "
            "AND rs.product_id = ? AND rs.order_id = o.id) THEN 1 ELSE 0 END AS already_reviewed "
            "FROM orders o WHERE o.user_id = ? AND o.status = 'completed' "
            "AND EXISTS(SELECT 1 FROM order_items oi WHERE oi.order_id = o.id AND oi.product_id = ?) "
            "ORDER BY already_reviewed ASC, o.id DESC LIMIT 1",
            (product_id, product_id, user_id, product_id, ),
        ).fetchone()


# ==========================================
# ประวัติสถานะ
# ==========================================

def add_status_log(order_id: int, status: str, note=None, changed_by=None, conn=None) -> int:
    """บันทึกประวัติสถานะ (changed_by = users.id หรือ None ถ้าระบบทำเอง) คืน id"""
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO order_status_log (order_id, status, note, changed_by) VALUES (?, ?, ?, ?)",
            (order_id, status, note, changed_by),
        ).lastrowid


def list_status_log(order_id: int, conn=None):
    """ประวัติสถานะเก่า -> ใหม่ (มี changed_by_name)"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT l.*, u.full_name AS changed_by_name FROM order_status_log l "
            "LEFT JOIN users u ON u.id = l.changed_by WHERE l.order_id = ? ORDER BY l.id",
            (order_id,),
        ).fetchall()


# ==========================================
# สถิติ Dashboard และรายงานส่งออก .xlsx (นับเฉพาะสถานะที่เป็นรายได้: paid/shipped/completed)
# วันที่รับรูปแบบ 'YYYY-MM-DD' — date_to นับรวมทั้งวัน
# ==========================================

def _date_clause(column, date_from, date_to):
    sql, params = "", []
    if date_from:
        sql += f" AND date({column}) >= date(?)"
        params.append(date_from)
    if date_to:
        sql += f" AND date({column}) <= date(?)"
        params.append(date_to)
    return sql, params


def sum_revenue(date_from=None, date_to=None, conn=None) -> float:
    """ยอดขายรวม (บาท) ของออเดอร์ที่ชำระแล้วในช่วงวันที่"""
    extra, params = _date_clause("created_at", date_from, date_to)
    with use_conn(conn) as c:
        value = c.execute(f"SELECT COALESCE(SUM(total), 0) AS s FROM orders "
                          f"WHERE status IN ({_REV_IN}){extra}", params).fetchone()["s"]
    return round(value, 2)


def count_by_status(user_id: int = None, conn=None) -> dict:
    """จำนวนออเดอร์แยกตามสถานะ (มีครบทุกสถานะ ไม่มี = 0)"""
    result = {s: 0 for s in ORDER_STATUSES}
    sql = "SELECT status, COUNT(*) AS n FROM orders"
    params = []
    if user_id is not None:
        sql += " WHERE user_id = ?"
        params.append(user_id)
    sql += " GROUP BY status"
    with use_conn(conn) as c:
        for r in c.execute(sql, params).fetchall():
            result[r["status"]] = r["n"]
    return result


def top_products(n: int = 5, date_from=None, date_to=None, conn=None):
    """สินค้าขายดี n อันดับ: product_id, product_name, total_qty, total_sales"""
    extra, params = _date_clause("o.created_at", date_from, date_to)
    with use_conn(conn) as c:
        return c.execute(
            "SELECT oi.product_id, oi.product_name, SUM(oi.qty) AS total_qty, "
            "ROUND(SUM(oi.qty * oi.price_at_purchase), 2) AS total_sales "
            "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
            f"WHERE o.status IN ({_REV_IN}){extra} "
            "GROUP BY oi.product_id, oi.product_name ORDER BY total_qty DESC, total_sales DESC LIMIT ?",
            [*params, int(n)],
        ).fetchall()


def daily_sales(days: int = 7, conn=None):
    """ยอดขายรายวันย้อนหลัง days วัน (รวมวันนี้): day, orders, revenue — เฉพาะวันที่มียอด เก่า->ใหม่"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT date(created_at) AS day, COUNT(*) AS orders, ROUND(SUM(total), 2) AS revenue "
            f"FROM orders WHERE status IN ({_REV_IN}) "
            "AND date(created_at) >= date('now', 'localtime', ?) "
            "GROUP BY date(created_at) ORDER BY day",
            (f"-{int(days) - 1} days",),
        ).fetchall()


def list_orders_in_range(date_from: str = None, date_to: str = None, conn=None):
    """รายการออเดอร์ทั้งหมดในช่วงวันที่ (ใช้สร้างรายงานส่งออก .xlsx)"""
    extra, params = _date_clause("o.created_at", date_from, date_to)
    with use_conn(conn) as c:
        return c.execute(
            _ORDER_SELECT + " WHERE 1=1" + extra + " ORDER BY o.created_at ASC, o.id ASC",
            params,
        ).fetchall()


def list_sold_items_in_range(date_from: str = None, date_to: str = None, conn=None):
    """รายการสินค้าที่ขายได้ (เฉพาะออเดอร์ที่ชำระเงินแล้ว paid/shipped/completed) ในช่วงวันที่"""
    extra, params = _date_clause("o.created_at", date_from, date_to)
    with use_conn(conn) as c:
        return c.execute(
            "SELECT o.id AS order_id, o.created_at AS order_date, o.status AS order_status, "
            "u.id AS user_id, u.full_name AS buyer_name, u.email AS buyer_email, o.recipient_phone, "
            "oi.product_id, oi.product_name, oi.option_label, oi.qty, oi.price_at_purchase, "
            "ROUND(oi.qty * oi.price_at_purchase, 2) AS line_total, "
            "COALESCE(p.cost_price, 0) AS unit_cost "
            "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
            "JOIN users u ON u.id = o.user_id "
            "LEFT JOIN products p ON p.id = oi.product_id "
            f"WHERE o.status IN ({_REV_IN}){extra} "
            "ORDER BY o.created_at ASC, o.id ASC, oi.id ASC",
            params,
        ).fetchall()


def list_customer_summaries_in_range(date_from: str = None, date_to: str = None, conn=None):
    """สรุปยอดซื้อของลูกค้าแต่ละรายในช่วงวันที่ (เฉพาะออเดอร์ที่เป็นรายได้)"""
    extra, params = _date_clause("o.created_at", date_from, date_to)
    with use_conn(conn) as c:
        return c.execute(
            "SELECT u.id AS user_id, u.username, u.full_name, u.email, "
            "COALESCE(u.phone, MAX(o.recipient_phone)) AS phone, "
            "COUNT(o.id) AS order_count, ROUND(SUM(o.total), 2) AS total_spent "
            "FROM orders o JOIN users u ON u.id = o.user_id "
            f"WHERE o.status IN ({_REV_IN}){extra} "
            "GROUP BY u.id ORDER BY total_spent DESC, order_count DESC",
            params,
        ).fetchall()
