"""
services/cart_service.py
ตะกร้าสินค้าของผู้ซื้อ: ราคาจริง (Flash Sale + ส่วนต่างตัวเลือก), ตรวจสต็อกก่อนเพิ่ม/แก้จำนวน,
แจ้งสินค้าหมด/ไม่พอ/ถูกลบ, ซื้อคู่กัน (addons) แบบทั้งหมดหรือไม่เลย

ทุกฟังก์ชันรับ user_id และต้องเป็นผู้ซื้อที่ล็อกอินเป็นคนนั้น (action cart.use)
order_service.checkout ใช้ get_cart(user_id, conn=conn) อ่านตะกร้าภายใน transaction เดียวกัน
"""
from core import permissions
from database import repo_cart, repo_products
from database.db import transaction

MAX_QTY_PER_ITEM = 99


def format_option_label(option_type, option_value):
    """'สี' + 'Red' -> 'สี: Red' (ใช้ทั้งตะกร้าและบันทึกในออเดอร์) — ไม่มีตัวเลือก = None"""
    if not option_type and not option_value:
        return None
    return f"{option_type}: {option_value}"


def _check_qty(qty) -> int:
    if isinstance(qty, bool) or not isinstance(qty, int):
        raise ValueError("จำนวนต้องเป็นจำนวนเต็ม")
    if qty < 1:
        raise ValueError("จำนวนต้องไม่น้อยกว่า 1")
    if qty > MAX_QTY_PER_ITEM:
        raise ValueError(f"สั่งได้สูงสุด {MAX_QTY_PER_ITEM} ชิ้นต่อรายการ")
    return qty


def _stock_problem(stock: int, qty: int):
    """ข้อความปัญหาสต็อก (None = สั่งจำนวนนี้ได้)"""
    if stock <= 0:
        return "สินค้าหมด"
    if qty > stock:
        return f"เหลือเพียง {stock} ชิ้น"
    return None


def _col(row, key, default=None):
    try:
        val = row[key]
        return default if val is None else val
    except (KeyError, IndexError, TypeError):
        return default


def _item_dict(row, conn=None) -> dict:
    """แปลงแถวตะกร้า -> dict พร้อมราคา/สต็อก/ปัญหา (problem = None เมื่อซื้อได้)"""
    option_id = row["option_id"]
    unit_price = round(float(row["effective_price"]) + float(row["extra_price"] or 0), 2)
    stock = (row["option_stock"] if option_id is not None else row["product_stock"]) or 0

    problem = None
    if _col(row, "product_deleted_at") is not None:
        problem = "สินค้านี้ไม่มีจำหน่ายแล้ว"
    elif not row["product_active"]:
        problem = "สินค้านี้ปิดการขายแล้ว"
    elif option_id is None and repo_products.list_options(row["product_id"], conn=conn):
        problem = "ตัวเลือกสินค้าถูกลบ กรุณานำออกแล้วเลือกใหม่"
    else:
        problem = _stock_problem(stock, row["qty"])

    is_selected = bool(int(_col(row, "is_selected", 1)))
    return {
        "cart_item_id": row["cart_item_id"],
        "product_id": row["product_id"],
        "option_id": option_id,
        "product_name": row["product_name"],
        "image_path": row["image_path"],
        "option_label": format_option_label(row["option_type"], row["option_value"]),
        "unit_price": unit_price,
        "qty": row["qty"],
        "line_total": round(unit_price * row["qty"], 2),
        "stock_available": stock,
        "problem": problem,
        "is_available": problem is None,
        "is_selected": is_selected,
    }


def get_cart(user_id: int, conn=None) -> dict:
    """
    ตะกร้าของผู้ซื้อ คืน {"items": [dict], "subtotal", "item_count" (ผลรวมชิ้น), "has_problem",
    พร้อมข้อมูลเฉพาะรายการที่ติ๊กเลือก: "selected_items", "selected_subtotal", "selected_item_count",
    "selected_has_problem", "all_selected"}
    """
    permissions.require_self(permissions.CART_USE, user_id)
    items = [_item_dict(r, conn) for r in repo_cart.list_items(user_id, conn=conn)]
    selected_items = [i for i in items if i.get("is_selected", True)]
    return {
        "items": items,
        "subtotal": round(sum(i["line_total"] for i in items), 2),
        "item_count": sum(i["qty"] for i in items),
        "has_problem": any(i["problem"] for i in items),
        "selected_items": selected_items,
        "selected_subtotal": round(sum(i["line_total"] for i in selected_items), 2),
        "selected_item_count": sum(i["qty"] for i in selected_items),
        "selected_has_problem": any(i["problem"] for i in selected_items),
        "all_selected": bool(items) and len(selected_items) == len(items),
    }


def get_cart_count(user_id: int) -> int:
    """จำนวนชิ้นรวมในตะกร้า (เลขบน navbar)"""
    permissions.require_self(permissions.CART_USE, user_id)
    return repo_cart.count(user_id)


def _add(conn, user_id: int, product_id: int, option_id, qty: int) -> int:
    """เพิ่มลงตะกร้าภายใน transaction ที่เปิดไว้แล้ว — ตรวจสินค้า/ตัวเลือก/สต็อก คืน cart_item_id"""
    qty = _check_qty(qty)
    product = repo_products.get_product(product_id, conn=conn)
    category = repo_products.get_category(product["category_id"], conn=conn) if product else None
    brand = repo_products.get_brand(product["brand_id"], conn=conn) if product else None
    if not (
        product and product["is_active"] and _col(product, "deleted_at") is None
        and category and category["is_active"] and _col(category, "deleted_at") is None
        and brand and brand["is_active"] and _col(brand, "deleted_at") is None
    ):
        raise ValueError("ไม่พบสินค้า หรือสินค้าถูกปิดการขาย")

    options = repo_products.list_options(product_id, conn=conn)
    if options:
        if option_id is None:
            raise ValueError("กรุณาเลือกตัวเลือกสินค้า")
        chosen = next((o for o in options if o["id"] == option_id), None)
        if chosen is None:
            raise ValueError("ตัวเลือกที่เลือกไม่ได้เป็นของสินค้านี้")
        stock = chosen["stock"]
    else:
        if option_id is not None:
            raise ValueError("สินค้านี้ไม่มีตัวเลือก")
        stock = product["stock"]

    in_cart = sum(r["qty"] for r in repo_cart.list_items(user_id, conn=conn)
                  if r["product_id"] == product_id and r["option_id"] == option_id)
    if in_cart + qty > MAX_QTY_PER_ITEM:
        raise ValueError(f"สั่งได้สูงสุด {MAX_QTY_PER_ITEM} ชิ้นต่อรายการ")
    if stock <= 0:
        raise ValueError("สินค้าหมด")
    if in_cart + qty > stock:
        raise ValueError(f"สินค้าเหลือเพียง {stock} ชิ้น (ในตะกร้ามี {in_cart} ชิ้นแล้ว)")
    return repo_cart.add_or_increase(user_id, product_id, option_id, qty, conn=conn)


def add_to_cart(user_id: int, product_id: int, option_id=None, qty: int = 1) -> dict:
    """
    เพิ่มสินค้าลงตะกร้า (สินค้า+ตัวเลือกเดิมซ้ำ = บวกจำนวน) คืน {"cart_item_id", "cart_count"}
    """
    permissions.require_self(permissions.CART_USE, user_id)
    with transaction() as conn:
        item_id = _add(conn, user_id, product_id, option_id, qty)
        return {"cart_item_id": item_id, "cart_count": repo_cart.count(user_id, conn=conn)}


def add_with_addons(user_id: int, product_id: int, addon_ids, option_id=None, qty: int = 1,
                    addon_options: dict = None) -> dict:
    """
    "ซื้อคู่กัน": เพิ่มสินค้าหลัก + สินค้าเสริมที่เลือก (ชิ้นละ 1) ในคลิกเดียว — สำเร็จทั้งหมดหรือไม่เพิ่มเลย
    """
    permissions.require_self(permissions.CART_USE, user_id)
    addon_options = addon_options or {}
    with transaction() as conn:
        allowed = {a["id"]: a for a in repo_products.list_addons(product_id, conn=conn)}
        ids = []
        for raw in addon_ids or []:
            if raw not in allowed:
                raise ValueError("สินค้าเสริมที่เลือกไม่ได้ขายคู่กับสินค้านี้")
            if raw not in ids:
                ids.append(raw)
        item_ids = [_add(conn, user_id, product_id, option_id, qty)]
        for addon_id in ids:
            try:
                item_ids.append(_add(conn, user_id, addon_id, addon_options.get(addon_id), 1))
            except ValueError as err:
                raise ValueError(f"{allowed[addon_id]['name']}: {err}") from None
        return {"cart_item_ids": item_ids, "cart_count": repo_cart.count(user_id, conn=conn)}


def update_qty(user_id: int, cart_item_id: int, qty: int) -> dict:
    """ตั้งจำนวนของรายการในตะกร้า (ตรวจสต็อก; qty < 1 = ValueError — จะลบให้เรียก remove_item) คืน get_cart() ล่าสุด"""
    permissions.require_self(permissions.CART_USE, user_id)
    qty = _check_qty(qty)
    with transaction() as conn:
        row = repo_cart.get_item(user_id, cart_item_id, conn=conn)
        if row is None:
            raise ValueError("ไม่พบสินค้าในตะกร้า")
        stock = (row["option_stock"] if row["option_id"] is not None else row["product_stock"]) or 0
        problem = _stock_problem(stock, qty)
        if problem:
            raise ValueError(problem if stock <= 0 else f"สินค้า{problem}")
        repo_cart.set_qty(user_id, cart_item_id, qty, conn=conn)
        return get_cart(user_id, conn=conn)


def set_item_selected(user_id: int, cart_item_id: int, selected: bool) -> dict:
    """ติ๊กเลือกหรือยกเลิกเลือกสินค้า 1 รายการในตะกร้า คืน get_cart() ล่าสุด"""
    permissions.require_self(permissions.CART_USE, user_id)
    with transaction() as conn:
        repo_cart.set_selected(user_id, cart_item_id, bool(selected), conn=conn)
        return get_cart(user_id, conn=conn)


def set_all_selected(user_id: int, selected: bool) -> dict:
    """เลือกทั้งหมด หรือ ยกเลิกเลือกทั้งหมด ในตะกร้า คืน get_cart() ล่าสุด"""
    permissions.require_self(permissions.CART_USE, user_id)
    with transaction() as conn:
        repo_cart.set_all_selected(user_id, bool(selected), conn=conn)
        return get_cart(user_id, conn=conn)


def remove_selected_items(user_id: int) -> dict:
    """ลบเฉพาะรายการที่ติ๊กเลือกออกจากตะกร้า คืน get_cart() ล่าสุด"""
    permissions.require_self(permissions.CART_USE, user_id)
    with transaction() as conn:
        repo_cart.remove_selected(user_id, conn=conn)
        return get_cart(user_id, conn=conn)


def remove_item(user_id: int, cart_item_id: int) -> bool:
    """เอาสินค้า 1 รายการออกจากตะกร้า — คืน False ถ้าไม่มีรายการนั้นของผู้ใช้"""
    permissions.require_self(permissions.CART_USE, user_id)
    return repo_cart.remove(user_id, cart_item_id)


def clear_cart(user_id: int) -> int:
    """ล้างตะกร้าทั้งหมด คืนจำนวนรายการที่ลบ"""
    permissions.require_self(permissions.CART_USE, user_id)
    return repo_cart.clear(user_id)
