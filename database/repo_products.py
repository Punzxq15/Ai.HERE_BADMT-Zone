"""
database/repo_products.py
สินค้า + หมวดหมู่ + แบรนด์ + ตัวเลือกสินค้า (options) + สินค้าเสริมขายคู่ (addons)
+ ชุดตัวเลือกตามหมวดหมู่ (option_groups / option_values — T02)
+ รูปสินค้าหลายรูป (product_images — T04)
คุยกับ DB อย่างเดียว ไม่มี business logic (สิทธิ์/การตรวจค่า อยู่ที่ service)
รองรับ Soft Delete (deleted_at) และการผูกหมวดหมู่กับแบรนด์ (category_brands)
"""
from database.repo_base import EFFECTIVE_PRICE_SQL, as_list, like_pattern, use_conn

# คอลัมน์ของ products ที่ create/update เขียนได้ (กัน SQL injection ผ่านชื่อคอลัมน์)
_PRODUCT_FIELDS = (
    "category_id", "brand_id", "name", "description", "price", "sale_price", "sale_ends_at",
    "stock", "image_path", "is_active", "weight_class", "balance", "flex", "level",
    "cost_price", "deleted_at", "deleted_by",
    "spec_material", "spec_weight_grip", "spec_balance_mm", "spec_balance_type",
    "spec_max_tension", "spec_length",
)
# คอลัมน์สเปกที่ใช้ list_distinct_values ได้
_SPEC_COLUMNS = ("weight_class", "balance", "flex", "level")

_SELECT = (
    "SELECT p.*, c.name AS category_name, b.name AS brand_name, "
    f"{EFFECTIVE_PRICE_SQL} AS effective_price "
    "FROM products p JOIN categories c ON c.id = p.category_id "
    "JOIN brands b ON b.id = p.brand_id"
)

_SORTS = {
    "newest": "p.id DESC",
    "price_asc": "effective_price ASC, p.id DESC",
    "price_desc": "effective_price DESC, p.id DESC",
    "name": "p.name COLLATE NOCASE ASC",
    "popular": ("(SELECT COALESCE(SUM(oi.qty), 0) FROM order_items oi "
                "JOIN orders o ON o.id = oi.order_id "
                "WHERE oi.product_id = p.id AND o.status != 'cancelled') DESC, p.id DESC"),
}


# ==========================================
# สินค้า
# ==========================================

def _build_where(filters):
    """
    สร้างเงื่อนไข WHERE จาก dict filters (คีย์ที่ไม่ได้ใส่ = ไม่กรอง):
      category_id, brand_id            ค่าเดียวหรือ list
      min_price, max_price             ช่วง "ราคาที่ใช้จริง"
      weight_class, balance, flex, level   ค่าเดียวหรือ list (เลือกหลายค่าได้)
      search                           ค้นใน ชื่อสินค้า/คำอธิบาย/ชื่อแบรนด์
      on_sale                          True = เฉพาะที่กำลังลดราคา
      in_stock                         True = เฉพาะที่มีของ
      active_only                      ค่าเริ่มต้น True = เฉพาะสินค้า/หมวด/แบรนด์ที่เปิดอยู่
      include_deleted                  ค่าเริ่มต้น False = ซ่อนสินค้าที่ถูกตั้ง deleted_at
    """
    f = filters or {}
    where, params = [], []

    if not f.get("include_deleted", False):
        where.append("p.deleted_at IS NULL AND c.deleted_at IS NULL AND b.deleted_at IS NULL")

    if f.get("active_only", True):
        where.append("p.is_active = 1 AND c.is_active = 1 AND b.is_active = 1")

    for key, column in (("category_id", "p.category_id"), ("brand_id", "p.brand_id"),
                        ("weight_class", "p.weight_class"), ("balance", "p.balance"),
                        ("flex", "p.flex"), ("level", "p.level")):
        value = f.get(key)
        if value is None or value == [] or value == "":
            continue
        values = as_list(value)
        where.append(f"{column} IN ({','.join('?' * len(values))})")
        params += values

    if f.get("min_price") is not None:
        where.append(f"{EFFECTIVE_PRICE_SQL} >= ?")
        params.append(f["min_price"])
    if f.get("max_price") is not None:
        where.append(f"{EFFECTIVE_PRICE_SQL} <= ?")
        params.append(f["max_price"])

    search = (f.get("search") or "").strip()
    if search:
        pat = like_pattern(search)
        where.append("(p.name LIKE ? ESCAPE '\\' OR p.description LIKE ? ESCAPE '\\' "
                     "OR b.name LIKE ? ESCAPE '\\')")
        params += [pat, pat, pat]

    if f.get("on_sale"):
        where.append("p.sale_price IS NOT NULL AND "
                     "(p.sale_ends_at IS NULL OR p.sale_ends_at > datetime('now','localtime'))")
    if f.get("in_stock"):
        where.append("p.stock > 0")

    return (" WHERE " + " AND ".join(where)) if where else "", params


def list_products(filters=None, sort="newest", limit=None, offset=0, conn=None):
    """
    รายการสินค้า (join ชื่อหมวด/แบรนด์ + คอลัมน์ effective_price)
    sort: newest | price_asc | price_desc | name | popular (ค่าอื่น = newest)
    """
    where, params = _build_where(filters)
    sql = _SELECT + where + " ORDER BY " + _SORTS.get(sort, _SORTS["newest"])
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [int(limit), int(offset or 0)]
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def count_products(filters=None, conn=None) -> int:
    """จำนวนสินค้าตาม filters เดียวกับ list_products (ใช้ทำแบ่งหน้า)"""
    where, params = _build_where(filters)
    sql = ("SELECT COUNT(*) AS n FROM products p JOIN categories c ON c.id = p.category_id "
           "JOIN brands b ON b.id = p.brand_id" + where)
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchone()["n"]


def get_product(product_id: int, conn=None):
    """สินค้า 1 ชิ้น (ไม่สนว่า active หรือไม่ — service ตัดสินเอง) หรือ None"""
    with use_conn(conn) as c:
        return c.execute(_SELECT + " WHERE p.id = ?", (product_id,)).fetchone()


def get_products_by_ids(ids, conn=None):
    """สินค้าตามรายการ id เรียงตามลำดับที่ส่งมา (id ที่ไม่มีจะถูกข้าม)"""
    ids = [int(i) for i in ids]
    if not ids:
        return []
    with use_conn(conn) as c:
        rows = c.execute(_SELECT + f" WHERE p.id IN ({','.join('?' * len(ids))})", ids).fetchall()
    by_id = {r["id"]: r for r in rows}
    return [by_id[i] for i in ids if i in by_id]


def create_product(category_id, brand_id, name, description, price, sale_price=None,
                   sale_ends_at=None, stock=0, image_path=None, weight_class=None,
                   balance=None, flex=None, level=None, is_active=1, cost_price=None,
                   spec_material=None, spec_weight_grip=None, spec_balance_mm=None,
                   spec_balance_type=None, spec_max_tension=None, spec_length=None,
                   conn=None) -> int:
    """เพิ่มสินค้าใหม่ คืน id"""
    with use_conn(conn) as c:
        cur = c.execute(
            "INSERT INTO products (category_id, brand_id, name, description, price, sale_price, "
            "sale_ends_at, stock, image_path, weight_class, balance, flex, level, is_active, cost_price, "
            "spec_material, spec_weight_grip, spec_balance_mm, spec_balance_type, spec_max_tension, spec_length) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (category_id, brand_id, name, description, price, sale_price, sale_ends_at, stock,
             image_path, weight_class, balance, flex, level, 1 if is_active else 0, cost_price,
             spec_material, spec_weight_grip, spec_balance_mm, spec_balance_type, spec_max_tension, spec_length),
        )
        new_id = cur.lastrowid
        if image_path:
            c.execute(
                "INSERT INTO product_images (product_id, path, sort_order) VALUES (?, ?, 1)",
                (new_id, image_path),
            )
        return new_id


def update_product(product_id: int, fields: dict, conn=None) -> bool:
    """
    แก้เฉพาะคอลัมน์ที่ส่งมาใน dict (ค่า None = ตั้งเป็น NULL ได้ เช่น sale_price)
    คอลัมน์ที่ไม่อยู่ในรายการอนุญาต -> ValueError
    """
    if not fields:
        return False
    bad = [k for k in fields if k not in _PRODUCT_FIELDS]
    if bad:
        raise ValueError(f"คอลัมน์สินค้าไม่ถูกต้อง: {', '.join(bad)}")
    sets = ", ".join(f"{k} = ?" for k in fields)
    with use_conn(conn) as c:
        cur = c.execute(f"UPDATE products SET {sets} WHERE id = ?", [*fields.values(), product_id])
        return cur.rowcount > 0


def set_product_active(product_id: int, active: bool, conn=None) -> bool:
    """เปิด/ปิดสินค้า"""
    return update_product(product_id, {"is_active": 1 if active else 0}, conn=conn)


def soft_delete_product(product_id: int, deleted_by: int = None, conn=None) -> bool:
    """ลบสินค้าแบบ Soft Delete (ตั้ง deleted_at และปิด is_active เพื่อเก็บประวัติยอดขาย/ออเดอร์)"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE products SET is_active = 0, deleted_at = datetime('now','localtime'), deleted_by = ? "
            "WHERE id = ?",
            (deleted_by, product_id),
        )
        return cur.rowcount > 0


def restore_product(product_id: int, conn=None) -> bool:
    """กู้คืนสินค้าที่ถูกลบ (ล้าง deleted_at และเปิด is_active = 1)"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE products SET is_active = 1, deleted_at = NULL, deleted_by = NULL WHERE id = ?",
            (product_id,),
        )
        return cur.rowcount > 0


def list_deleted_products(search: str = None, conn=None):
    """
    รายการสินค้าที่ถูกลบ (deleted_at IS NOT NULL) พร้อมสรุปประวัติการขาย:
    total_sold_qty, total_sold_revenue (เฉพาะออเดอร์ที่ไม่ได้ยกเลิก)
    """
    sql = (
        "SELECT p.*, c.name AS category_name, b.name AS brand_name, "
        f"{EFFECTIVE_PRICE_SQL} AS effective_price, "
        "u.full_name AS deleted_by_name, "
        "COALESCE((SELECT SUM(oi.qty) FROM order_items oi JOIN orders o ON o.id = oi.order_id "
        "          WHERE oi.product_id = p.id AND o.status != 'cancelled'), 0) AS total_sold_qty, "
        "ROUND(COALESCE((SELECT SUM(oi.qty * oi.price_at_purchase) FROM order_items oi "
        "                JOIN orders o ON o.id = oi.order_id "
        "                WHERE oi.product_id = p.id AND o.status != 'cancelled'), 0), 2) AS total_sold_revenue "
        "FROM products p JOIN categories c ON c.id = p.category_id "
        "JOIN brands b ON b.id = p.brand_id "
        "LEFT JOIN users u ON u.id = p.deleted_by "
        "WHERE p.deleted_at IS NOT NULL"
    )
    params = []
    if search and search.strip():
        pat = like_pattern(search.strip())
        sql += " AND (p.name LIKE ? ESCAPE '\\' OR b.name LIKE ? ESCAPE '\\' OR c.name LIKE ? ESCAPE '\\')"
        params += [pat, pat, pat]
    sql += " ORDER BY p.deleted_at DESC, p.id DESC"
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def adjust_stock(product_id: int, delta: int, conn=None) -> bool:
    """
    บวก/ลบสต็อกสินค้า (delta ติดลบ = ตัด) แบบ atomic
    คืน False ถ้าไม่มีสินค้า หรือทำให้สต็อกติดลบ (ไม่แก้อะไร)
    """
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ? AND stock + ? >= 0",
            (delta, product_id, delta),
        )
        return cur.rowcount > 0


def sync_stock_from_options(product_id: int, conn=None) -> bool:
    """products.stock = ผลรวม stock ของตัวเลือก (ทำเฉพาะสินค้าที่มีตัวเลือก)"""
    with use_conn(conn) as c:
        cur = c.execute(
            "UPDATE products SET stock = (SELECT COALESCE(SUM(stock), 0) FROM product_options "
            "WHERE product_id = ?) WHERE id = ? "
            "AND EXISTS (SELECT 1 FROM product_options WHERE product_id = ?)",
            (product_id, product_id, product_id),
        )
        return cur.rowcount > 0


def list_low_stock(threshold: int, conn=None):
    """สินค้า active ที่ไม่ถูกลบ และ stock <= threshold (รวม 0) น้อยสุดก่อน"""
    with use_conn(conn) as c:
        return c.execute(
            _SELECT + " WHERE p.is_active = 1 AND p.deleted_at IS NULL AND p.stock <= ? ORDER BY p.stock ASC, p.name",
            (threshold,),
        ).fetchall()


def list_low_stock_options(threshold: int, conn=None):
    """ตัวเลือกของสินค้า active ที่ไม่ถูกลบ และ stock <= threshold"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT o.*, p.name AS product_name FROM product_options o "
            "JOIN products p ON p.id = o.product_id "
            "WHERE p.is_active = 1 AND p.deleted_at IS NULL AND o.stock <= ? ORDER BY o.stock ASC, p.name, o.id",
            (threshold,),
        ).fetchall()


def list_distinct_values(column: str, conn=None) -> list:
    """ค่าสเปกที่มีอยู่จริงของสินค้า active (weight_class/balance/flex/level) ไว้สร้างตัวกรอง"""
    if column not in _SPEC_COLUMNS:
        raise ValueError(f"คอลัมน์สเปกไม่ถูกต้อง: {column}")
    with use_conn(conn) as c:
        rows = c.execute(
            f"SELECT DISTINCT {column} AS v FROM products "
            f"WHERE is_active = 1 AND deleted_at IS NULL AND {column} IS NOT NULL AND {column} != '' ORDER BY v"
        ).fetchall()
    return [r["v"] for r in rows]


# ==========================================
# หมวดหมู่ / แบรนด์ + การผูกหมวดหมู่กับแบรนด์ (category_brands)
# ==========================================

def _list_named(table, active_only, include_deleted, conn):
    where = []
    if not include_deleted:
        where.append("deleted_at IS NULL")
    if active_only:
        where.append("is_active = 1")
    sql = f"SELECT * FROM {table}" + ((" WHERE " + " AND ".join(where)) if where else "") + " ORDER BY name"
    with use_conn(conn) as c:
        return c.execute(sql).fetchall()


def _get_named(table, row_id, conn):
    with use_conn(conn) as c:
        return c.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()


def _set_active_named(table, row_id, active, conn):
    with use_conn(conn) as c:
        return c.execute(f"UPDATE {table} SET is_active = ? WHERE id = ?",
                         (1 if active else 0, row_id)).rowcount > 0


def list_categories(active_only: bool = True, include_deleted: bool = False, conn=None):
    """หมวดหมู่ทั้งหมด เรียงตามชื่อ"""
    return _list_named("categories", active_only, include_deleted, conn)


def get_category(category_id: int, conn=None):
    return _get_named("categories", category_id, conn)


def create_category(name: str, image_path=None, all_brands: bool = True, conn=None) -> int:
    """เพิ่มหมวด (ชื่อซ้ำ -> sqlite3.IntegrityError ให้ service แปลงเป็นข้อความไทย)"""
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO categories (name, image_path, all_brands) VALUES (?, ?, ?)",
            (name, image_path, 1 if all_brands else 0),
        ).lastrowid


def update_category(category_id: int, name: str, image_path=None, all_brands: bool = None, conn=None) -> bool:
    """แก้ชื่อหมวด — image_path=None = ไม่เปลี่ยนรูป"""
    with use_conn(conn) as c:
        if all_brands is None:
            return c.execute(
                "UPDATE categories SET name = ?, image_path = COALESCE(?, image_path) WHERE id = ?",
                (name, image_path, category_id),
            ).rowcount > 0
        return c.execute(
            "UPDATE categories SET name = ?, image_path = COALESCE(?, image_path), all_brands = ? WHERE id = ?",
            (name, image_path, 1 if all_brands else 0, category_id),
        ).rowcount > 0


def set_category_active(category_id: int, active: bool, conn=None) -> bool:
    return _set_active_named("categories", category_id, active, conn)


def soft_delete_category(category_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE categories SET is_active = 0, deleted_at = datetime('now','localtime') WHERE id = ?",
            (category_id,),
        ).rowcount > 0


def restore_category(category_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE categories SET is_active = 1, deleted_at = NULL WHERE id = ?",
            (category_id,),
        ).rowcount > 0


def count_products_in_category(category_id: int, active_only: bool = False, conn=None) -> int:
    sql = "SELECT COUNT(*) AS n FROM products WHERE category_id = ? AND deleted_at IS NULL"
    if active_only:
        sql += " AND is_active = 1"
    with use_conn(conn) as c:
        return int(c.execute(sql, (category_id,)).fetchone()["n"])


def list_brands(active_only: bool = True, include_deleted: bool = False, conn=None):
    """แบรนด์ทั้งหมด เรียงตามชื่อ"""
    return _list_named("brands", active_only, include_deleted, conn)


def get_brand(brand_id: int, conn=None):
    return _get_named("brands", brand_id, conn)


def create_brand(name: str, logo_path=None, conn=None) -> int:
    """เพิ่มแบรนด์ (ชื่อซ้ำ -> sqlite3.IntegrityError)"""
    with use_conn(conn) as c:
        bid = c.execute("INSERT INTO brands (name, logo_path) VALUES (?, ?)",
                        (name, logo_path)).lastrowid
        # ผูกแบรนด์ใหม่เข้ากับทุกหมวดหมู่ที่ตั้งค่า all_brands = 1 โดยอัตโนมัติ
        c.execute(
            "INSERT OR IGNORE INTO category_brands (category_id, brand_id) "
            "SELECT id, ? FROM categories WHERE COALESCE(all_brands, 1) = 1",
            (bid,),
        )
        return bid


def update_brand(brand_id: int, name: str, logo_path=None, conn=None) -> bool:
    """แก้ชื่อแบรนด์ — logo_path=None = ไม่เปลี่ยนรูป"""
    with use_conn(conn) as c:
        return c.execute("UPDATE brands SET name = ?, logo_path = COALESCE(?, logo_path) "
                         "WHERE id = ?", (name, logo_path, brand_id)).rowcount > 0


def set_brand_active(brand_id: int, active: bool, conn=None) -> bool:
    return _set_active_named("brands", brand_id, active, conn)


def soft_delete_brand(brand_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE brands SET is_active = 0, deleted_at = datetime('now','localtime') WHERE id = ?",
            (brand_id,),
        ).rowcount > 0


def restore_brand(brand_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE brands SET is_active = 1, deleted_at = NULL WHERE id = ?",
            (brand_id,),
        ).rowcount > 0


def count_products_in_brand(brand_id: int, active_only: bool = False, conn=None) -> int:
    sql = "SELECT COUNT(*) AS n FROM products WHERE brand_id = ? AND deleted_at IS NULL"
    if active_only:
        sql += " AND is_active = 1"
    with use_conn(conn) as c:
        return int(c.execute(sql, (brand_id,)).fetchone()["n"])


def get_category_brand_ids(category_id: int, conn=None) -> list[int]:
    """คืนรายการ brand_id ที่ผูกกับหมวดหมู่นี้"""
    with use_conn(conn) as c:
        cat = get_category(category_id, conn=c)
        if cat is None:
            return []
        if cat["all_brands"]:
            rows = c.execute("SELECT id FROM brands WHERE deleted_at IS NULL ORDER BY name").fetchall()
            return [r["id"] for r in rows]
        rows = c.execute(
            "SELECT brand_id FROM category_brands WHERE category_id = ? ORDER BY brand_id",
            (category_id,),
        ).fetchall()
        return [r["brand_id"] for r in rows]


def set_category_brands(category_id: int, brand_ids=None, all_brands: bool = False, conn=None) -> None:
    """ตั้งค่าการผูกแบรนด์ของหมวดหมู่ (all_brands=True = ผูกทุกแบรนด์รวมแบรนด์ใหม่ในอนาคต)"""
    with use_conn(conn) as c:
        c.execute("UPDATE categories SET all_brands = ? WHERE id = ?",
                  (1 if all_brands else 0, category_id))
        c.execute("DELETE FROM category_brands WHERE category_id = ?", (category_id,))
        if all_brands:
            c.execute(
                "INSERT OR IGNORE INTO category_brands (category_id, brand_id) "
                "SELECT ?, id FROM brands WHERE deleted_at IS NULL",
                (category_id,),
            )
        else:
            clean = []
            for bid in brand_ids or []:
                b = int(bid)
                if b not in clean:
                    clean.append(b)
            c.executemany(
                "INSERT OR IGNORE INTO category_brands (category_id, brand_id) VALUES (?, ?)",
                [(category_id, b) for b in clean],
            )


def list_brands_for_category(category_id: int, active_only: bool = True, conn=None):
    """รายชื่อแบรนด์ที่ผูกกับหมวดหมู่นี้"""
    with use_conn(conn) as c:
        cat = get_category(category_id, conn=c)
        if cat is None:
            return []
        where = "b.deleted_at IS NULL" + (" AND b.is_active = 1" if active_only else "")
        if cat["all_brands"]:
            return c.execute(f"SELECT b.* FROM brands b WHERE {where} ORDER BY b.name").fetchall()
        return c.execute(
            f"SELECT b.* FROM brands b JOIN category_brands cb ON cb.brand_id = b.id "
            f"WHERE cb.category_id = ? AND {where} ORDER BY b.name",
            (category_id,),
        ).fetchall()


# ==========================================
# ชุดตัวเลือกตามหมวดหมู่ (option_groups / option_values — T02)
# ==========================================

def list_option_groups(category_id: int = None, active_only: bool = True, conn=None):
    """รายการชุดตัวเลือกของหมวดหมู่ (เรียงตาม sort_order, id)"""
    where, params = [], []
    if category_id is not None:
        where.append("category_id = ?")
        params.append(int(category_id))
    if active_only:
        where.append("is_active = 1")
    sql = "SELECT * FROM option_groups" + ((" WHERE " + " AND ".join(where)) if where else "") + " ORDER BY sort_order ASC, id ASC"
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def get_option_group(group_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM option_groups WHERE id = ?", (group_id,)).fetchone()


def get_option_group_by_key(category_id: int, key: str, conn=None):
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM option_groups WHERE category_id = ? AND key = ?",
            (int(category_id), str(key).strip()),
        ).fetchone()


def create_option_group(category_id: int, key: str, label: str, sort_order: int = 0,
                        is_active: bool = True, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO option_groups (category_id, key, label, sort_order, is_active) VALUES (?, ?, ?, ?, ?)",
            (int(category_id), str(key).strip(), str(label).strip(), int(sort_order or 0), 1 if is_active else 0),
        ).lastrowid


def update_option_group(group_id: int, label: str = None, sort_order: int = None,
                        is_active: bool = None, conn=None) -> bool:
    sets, params = [], []
    if label is not None:
        sets.append("label = ?")
        params.append(str(label).strip())
    if sort_order is not None:
        sets.append("sort_order = ?")
        params.append(int(sort_order))
    if is_active is not None:
        sets.append("is_active = ?")
        params.append(1 if is_active else 0)
    if not sets:
        return False
    params.append(int(group_id))
    with use_conn(conn) as c:
        return c.execute(f"UPDATE option_groups SET {', '.join(sets)} WHERE id = ?", params).rowcount > 0


def set_option_group_active(group_id: int, active: bool, conn=None) -> bool:
    return update_option_group(group_id, is_active=active, conn=conn)


def list_option_values(group_id: int, active_only: bool = True, conn=None):
    where = ["group_id = ?"]
    params = [int(group_id)]
    if active_only:
        where.append("is_active = 1")
    sql = f"SELECT * FROM option_values WHERE {' AND '.join(where)} ORDER BY sort_order ASC, id ASC"
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def get_option_value(value_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM option_values WHERE id = ?", (value_id,)).fetchone()


def create_option_value(group_id: int, value: str, label: str = None, sort_order: int = 0,
                        is_active: bool = True, conn=None) -> int:
    val = str(value).strip()
    lbl = str(label).strip() if label is not None and str(label).strip() else val
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO option_values (group_id, value, label, sort_order, is_active) VALUES (?, ?, ?, ?, ?)",
            (int(group_id), val, lbl, int(sort_order or 0), 1 if is_active else 0),
        ).lastrowid


def update_option_value(value_id: int, value: str = None, label: str = None,
                        sort_order: int = None, is_active: bool = None, conn=None) -> bool:
    sets, params = [], []
    if value is not None:
        sets.append("value = ?")
        params.append(str(value).strip())
    if label is not None:
        sets.append("label = ?")
        params.append(str(label).strip())
    if sort_order is not None:
        sets.append("sort_order = ?")
        params.append(int(sort_order))
    if is_active is not None:
        sets.append("is_active = ?")
        params.append(1 if is_active else 0)
    if not sets:
        return False
    params.append(int(value_id))
    with use_conn(conn) as c:
        return c.execute(f"UPDATE option_values SET {', '.join(sets)} WHERE id = ?", params).rowcount > 0


def set_option_value_active(value_id: int, active: bool, conn=None) -> bool:
    return update_option_value(value_id, is_active=active, conn=conn)


def list_active_option_values_by_key(key: str, category_id: int = None, conn=None) -> list[str]:
    """คืนรายการ value ที่เปิดใช้งานอยู่ของชุดตัวเลือกตาม key (เรียงตาม sort_order)"""
    where = ["g.key = ?", "g.is_active = 1", "v.is_active = 1"]
    params = [str(key).strip()]
    if category_id is not None:
        where.append("g.category_id = ?")
        params.append(int(category_id))
    sql = (
        "SELECT v.value FROM option_values v "
        "JOIN option_groups g ON g.id = v.group_id "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY g.sort_order ASC, v.sort_order ASC, v.id ASC"
    )
    with use_conn(conn) as c:
        rows = c.execute(sql, params).fetchall()
    out = []
    for r in rows:
        if r["value"] not in out:
            out.append(r["value"])
    return out


# ==========================================
# ตัวเลือกสินค้า (product_options)
# หลังเพิ่ม/แก้/ลบ/ปรับสต็อกตัวเลือก จะ sync products.stock = ผลรวมตัวเลือกให้เอง (ใน conn เดียวกัน)
# ==========================================

def list_options(product_id: int, conn=None):
    """ตัวเลือกทั้งหมดของสินค้า เรียงตามประเภท/id"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM product_options WHERE product_id = ? ORDER BY option_type, id",
                         (product_id,)).fetchall()


def get_option(option_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM product_options WHERE id = ?", (option_id,)).fetchone()


def create_option(product_id: int, option_type: str, option_value: str,
                  extra_price: float = 0, stock: int = 0, image_path: str = None, conn=None) -> int:
    """เพิ่มตัวเลือก คืน id"""
    with use_conn(conn) as c:
        new_id = c.execute(
            "INSERT INTO product_options (product_id, option_type, option_value, extra_price, stock, image_path) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, option_type, option_value, extra_price, stock, image_path),
        ).lastrowid
        sync_stock_from_options(product_id, conn=c)
        return new_id


def update_option(option_id: int, option_type: str, option_value: str,
                  extra_price: float, stock: int, image_path: str = None, conn=None) -> bool:
    """แก้ตัวเลือก (ส่งครบทุกช่อง)"""
    with use_conn(conn) as c:
        row = get_option(option_id, conn=c)
        if row is None:
            return False
        if image_path is None:
            c.execute(
                "UPDATE product_options SET option_type = ?, option_value = ?, extra_price = ?, "
                "stock = ? WHERE id = ?",
                (option_type, option_value, extra_price, stock, option_id),
            )
        else:
            c.execute(
                "UPDATE product_options SET option_type = ?, option_value = ?, extra_price = ?, "
                "stock = ?, image_path = ? WHERE id = ?",
                (option_type, option_value, extra_price, stock, image_path or None, option_id),
            )
        sync_stock_from_options(row["product_id"], conn=c)
        return True


def is_option_used(option_id: int, conn=None) -> bool:
    """ตัวเลือกนี้ถูกอ้างอิงในออเดอร์แล้วหรือยัง (ถ้าใช่ลบไม่ได้)"""
    with use_conn(conn) as c:
        return c.execute("SELECT 1 FROM order_items WHERE option_id = ? LIMIT 1",
                         (option_id,)).fetchone() is not None


def delete_option(option_id: int, conn=None) -> bool:
    """
    ลบตัวเลือก (ตะกร้าที่อ้างอิงจะถูกตั้ง option_id เป็น NULL เอง)
    ถ้าเคยถูกสั่งซื้อแล้ว -> sqlite3.IntegrityError (ควรเช็ค is_option_used ก่อนใน service)
    """
    with use_conn(conn) as c:
        row = get_option(option_id, conn=c)
        if row is None:
            return False
        c.execute("DELETE FROM product_options WHERE id = ?", (option_id,))
        sync_stock_from_options(row["product_id"], conn=c)
        return True


def adjust_option_stock(option_id: int, delta: int, conn=None) -> bool:
    """บวก/ลบสต็อกตัวเลือกแบบ atomic (ติดลบไม่ได้ -> False) แล้ว sync สต็อกรวมของสินค้า"""
    with use_conn(conn) as c:
        row = get_option(option_id, conn=c)
        if row is None:
            return False
        cur = c.execute("UPDATE product_options SET stock = stock + ? WHERE id = ? AND stock + ? >= 0",
                        (delta, option_id, delta))
        if cur.rowcount == 0:
            return False
        sync_stock_from_options(row["product_id"], conn=c)
        return True


# ==========================================
# รูปภาพหลายรูปของสินค้า (product_images — T04)
# ==========================================

def list_product_images(product_id: int, conn=None):
    """รายการรูปทั้งหมดของสินค้า เรียงตาม sort_order ASC, id ASC"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM product_images WHERE product_id = ? ORDER BY sort_order ASC, id ASC",
            (int(product_id),),
        ).fetchall()


def get_product_image(image_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM product_images WHERE id = ?", (int(image_id),)).fetchone()


def sync_primary_product_image(product_id: int, conn=None) -> str | None:
    """ตั้ง products.image_path ให้ตรงกับรูปแรกสุด (sort_order ต่ำสุด) ใน product_images"""
    with use_conn(conn) as c:
        first = c.execute(
            "SELECT path FROM product_images WHERE product_id = ? ORDER BY sort_order ASC, id ASC LIMIT 1",
            (int(product_id),),
        ).fetchone()
        if first is not None:
            c.execute("UPDATE products SET image_path = ? WHERE id = ?", (first["path"], int(product_id)))
            return first["path"]
        return None


def add_product_image(product_id: int, path: str, sort_order: int = None,
                      option_value_id: int = None, color_value: str = None, conn=None) -> int:
    with use_conn(conn) as c:
        if sort_order is None:
            row = c.execute(
                "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_ord FROM product_images WHERE product_id = ?",
                (int(product_id),),
            ).fetchone()
            sort_order = int(row["next_ord"] or 1)
        img_id = c.execute(
            "INSERT INTO product_images (product_id, path, sort_order, option_value_id, color_value) "
            "VALUES (?, ?, ?, ?, ?)",
            (int(product_id), str(path).strip(), int(sort_order), option_value_id,
             str(color_value).strip() if color_value else None),
        ).lastrowid
        sync_primary_product_image(product_id, conn=c)
        return img_id


def update_product_image(image_id: int, path: str = None, sort_order: int = None,
                         option_value_id: int = None, color_value: str = "__keep__", conn=None) -> bool:
    with use_conn(conn) as c:
        row = get_product_image(image_id, conn=c)
        if row is None:
            return False
        sets, params = [], []
        if path is not None:
            sets.append("path = ?")
            params.append(str(path).strip())
        if sort_order is not None:
            sets.append("sort_order = ?")
            params.append(int(sort_order))
        if option_value_id is not None:
            sets.append("option_value_id = ?")
            params.append(option_value_id if option_value_id > 0 else None)
        if color_value != "__keep__":
            sets.append("color_value = ?")
            params.append(str(color_value).strip() if color_value else None)
        if not sets:
            return False
        params.append(int(image_id))
        c.execute(f"UPDATE product_images SET {', '.join(sets)} WHERE id = ?", params)
        sync_primary_product_image(row["product_id"], conn=c)
        return True


def delete_product_image(image_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        row = get_product_image(image_id, conn=c)
        if row is None:
            return False
        c.execute("DELETE FROM product_images WHERE id = ?", (int(image_id),))
        remaining = list_product_images(row["product_id"], conn=c)
        if remaining:
            sync_primary_product_image(row["product_id"], conn=c)
        else:
            c.execute("UPDATE products SET image_path = NULL WHERE id = ?", (row["product_id"],))
        return True


def reorder_product_images(product_id: int, image_ids: list[int], conn=None) -> None:
    with use_conn(conn) as c:
        for idx, img_id in enumerate(image_ids or [], start=1):
            c.execute(
                "UPDATE product_images SET sort_order = ? WHERE id = ? AND product_id = ?",
                (idx, int(img_id), int(product_id)),
            )
        sync_primary_product_image(product_id, conn=c)


# ==========================================
# สินค้าเสริมขายคู่ (product_addons)
# ==========================================

def list_addons(product_id: int, conn=None):
    """สินค้าเสริมของสินค้านี้ (เฉพาะที่ active และไม่ถูกลบ) พร้อม effective_price"""
    with use_conn(conn) as c:
        return c.execute(
            _SELECT + " JOIN product_addons a ON a.addon_product_id = p.id "
            "WHERE a.product_id = ? AND p.is_active = 1 AND p.deleted_at IS NULL ORDER BY p.id", (product_id,),
        ).fetchall()


def set_addons(product_id: int, addon_ids, conn=None) -> int:
    """แทนที่รายการสินค้าเสริมทั้งหมด (ข้ามตัวเอง/ซ้ำ) คืนจำนวนที่บันทึก"""
    clean = []
    for i in addon_ids or []:
        i = int(i)
        if i != product_id and i not in clean:
            clean.append(i)
    with use_conn(conn) as c:
        c.execute("DELETE FROM product_addons WHERE product_id = ?", (product_id,))
        c.executemany("INSERT INTO product_addons (product_id, addon_product_id) VALUES (?, ?)",
                      [(product_id, i) for i in clean])
    return len(clean)
