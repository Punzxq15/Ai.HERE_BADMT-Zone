"""
services/product_service.py
ตรรกะเรื่องสินค้า: ราคาที่ใช้จริง/Flash Sale, ค้นหา+กรองสเปก, รายละเอียด, เปรียบเทียบไม้ (2-5 ไม้),
ตัวช่วยเลือกไม้, สินค้าขายดี, ค้นหาแนะนำ, และงานฝั่งแอดมิน/เจ้าของ:
- แก้สินค้า/สต็อก/ตัวเลือก/สินค้าเสริม/หมวด/แบรนด์
- ลบสินค้าแบบ Soft Delete + แท็บสินค้าที่ถูกลบพร้อมประวัติยอดขาย + กู้คืนสินค้า
- ลบหมวดหมู่/แบรนด์อย่างปลอดภัย (ตรวจสินค้าที่อ้างอิงก่อน) + ผูกหมวดหมู่กับทุกแบรนด์หรือเฉพาะบางแบรนด์
- T02: ชุดตัวเลือกของหมวดหมู่ที่ Owner ตั้งค่าเพิ่ม/แก้/เรียงลำดับ/ปิดใช้งานได้เอง (3U-10U, ความเร็วลูกแบด, ไซส์ ฯลฯ)
- T03: Technical Specifications ของไม้แบดมินตัน 7 หัวข้อ
- T04: รูปสินค้าหลายรูป + ผูกรูปกับสี/สไตล์
- T09: สุ่มสินค้าทั้งหมดสำหรับหน้า Login
"""
import math
import random
import sqlite3
from datetime import datetime

from core import permissions
from core.constants import (
    BALANCES, FLEXES, LEVELS, MAX_COMPARE, MIN_COMPARE, OPTION_TYPES,
    RACKET_TECH_SPEC_FIELDS, ROLE_OWNER, WEIGHT_CLASSES,
)
from core.session import Session
from database import repo_orders, repo_products, repo_reviews, repo_wishlist
from database.db import transaction
from services import audit_service, settings_service
from utils import validators
from utils.formatters import parse_datetime

# ค่าที่ส่งเข้า recommend_rackets (style = สไตล์การเล่น)
STYLE_ATTACK = "attack"      # บุก
STYLE_CONTROL = "control"    # คุมเกม
STYLE_SPEED = "speed"        # สปีด
STYLE_LABELS = {STYLE_ATTACK: "บุก", STYLE_CONTROL: "คุมเกม", STYLE_SPEED: "สปีด"}

_STYLE_RULES = {
    STYLE_ATTACK: (("Heavy Head", "Head Heavy"), ("Stiff", "Medium-Stiff", "Extra Stiff")),
    STYLE_CONTROL: (("Even Balance",), ("Medium", "Medium-Stiff")),
    STYLE_SPEED: (("Light Head", "Head Light"), ("Flexible", "Medium")),
}

MAX_PAGE_SIZE = 60
_FILTER_KEYS = ("category_id", "brand_id", "weight_class", "balance", "flex", "level",
                "min_price", "max_price", "on_sale", "in_stock")
_SORTS = ("newest", "price_asc", "price_desc", "name", "popular")
_SPEC_FIELDS = (("weight_class", "น้ำหนัก", WEIGHT_CLASSES), ("balance", "จุดสมดุล", BALANCES),
                ("flex", "ความแข็งก้าน", FLEXES), ("level", "ระดับ", LEVELS))
_NOT_FOUND = "ไม่พบสินค้า หรือสินค้าถูกปิดการขาย"


# ==========================================
# ราคาที่ใช้จริง / Flash Sale
# ==========================================

def _field(item, key, default=None):
    """อ่านค่าจาก dict หรือ sqlite3.Row โดยไม่ error ถ้าไม่มีคีย์"""
    try:
        val = item[key]
        return default if val is None else val
    except (KeyError, IndexError, TypeError):
        return default


def is_on_sale(product) -> bool:
    """กำลังลดราคาอยู่ไหม: มี sale_price และ (ไม่มี sale_ends_at หรือยังไม่ถึงเวลา) — ตรงกับ SQL ใน repo"""
    if _field(product, "sale_price") is None:
        return False
    ends = _field(product, "sale_ends_at")
    if ends is None or ends == "":
        return True
    end_dt = parse_datetime(ends)
    return end_dt is not None and end_dt > datetime.now()


def get_effective_price(product, extra_price: float = 0) -> float:
    """ราคาที่ใช้จริงต่อชิ้น = (sale_price ถ้ากำลังลด ไม่งั้น price) + extra_price ของตัวเลือก (ปัด 2 ตำแหน่ง)"""
    base = _field(product, "sale_price") if is_on_sale(product) else _field(product, "price")
    return round(float(base or 0) + float(extra_price or 0), 2)


def sale_seconds_left(product):
    """วินาทีที่เหลือของ Flash Sale — ลดตลอดไม่มีเวลาสิ้นสุด/ไม่ได้ลด = None"""
    if not is_on_sale(product):
        return None
    end_dt = parse_datetime(_field(product, "sale_ends_at"))
    if end_dt is None:
        return None
    return max(0, int((end_dt - datetime.now()).total_seconds()))


def build_technical_specs(product) -> list[dict]:
    """
    สร้างรายการ Technical Specifications ของไม้แบดมินตันตามตาราง T03:
    1. Material
    2. Weight Class / Grip
    3. Balance Point
    4. Shaft Flexibility
    5. Max String Tension
    6. Length
    7. Skill Level
    ช่องที่เว้นว่างจะไม่แสดงในรายการ (ไม่แสดง '...')
    """
    material = str(_field(product, "spec_material") or "").strip()
    weight_grip = str(_field(product, "spec_weight_grip") or _field(product, "weight_class") or "").strip()
    bal_mm = str(_field(product, "spec_balance_mm") or "").strip()
    bal_type = str(_field(product, "spec_balance_type") or _field(product, "balance") or "").strip()
    balance_point = validators.format_balance_point_display(bal_mm, bal_type)
    shaft_flex = str(_field(product, "flex") or "").strip()
    max_tension = str(_field(product, "spec_max_tension") or "").strip()
    length_val = str(_field(product, "spec_length") or "").strip()
    if length_val and length_val.isdigit():
        length_val = f"{length_val} mm"
    skill_level = str(_field(product, "level") or "").strip()

    raw_rows = [
        ("material", "Material", material),
        ("weight_grip", "Weight Class / Grip", weight_grip),
        ("balance_point", "Balance Point", balance_point),
        ("flex", "Shaft Flexibility", shaft_flex),
        ("max_tension", "Max String Tension", max_tension),
        ("length", "Length", length_val),
        ("skill_level", "Skill Level", skill_level),
    ]
    return [
        {"key": k, "label": lbl, "value": val}
        for k, lbl, val in raw_rows
        if val and val != "..."
    ]


def _decorate(row, ratings=None, wishlist_ids=None) -> dict:
    """แปลงแถวสินค้าเป็น dict + ฟิลด์คำนวณ (ราคาจริง, สถานะลดราคา, ดาว, wishlist, มีของ, technical_specs)"""
    d = dict(row)
    d["effective_price"] = get_effective_price(row)
    d["is_on_sale"] = is_on_sale(row)
    d["sale_seconds_left"] = sale_seconds_left(row)
    d["in_stock"] = (d.get("stock") or 0) > 0
    d["is_racket"] = _is_racket(row)
    d["technical_specs"] = build_technical_specs(row) if d["is_racket"] else []
    if ratings is not None:
        avg, count = ratings.get(d["id"], (0.0, 0))
        d["avg_rating"], d["review_count"] = avg, count
    if wishlist_ids is not None:
        d["in_wishlist"] = d["id"] in wishlist_ids
    return d


def _buyer_wishlist_ids(user_id=None) -> set:
    """wishlist ของผู้ซื้อ — ผู้เยี่ยมชมหรือ role อื่นไม่มี wishlist"""
    if user_id is not None:
        permissions.require_user(user_id)
    elif Session.get_role() != "buyer":
        return set()
    else:
        user_id = Session.get_user_id()
    return repo_wishlist.ids(user_id) if user_id else set()


def _is_visible(row) -> bool:
    """ผู้ซื้อเห็นสินค้านี้ได้ไหม: สินค้า + หมวด + แบรนด์ต้องเปิดอยู่ และไม่ถูกลบ (deleted_at IS NULL)"""
    if row is None or not row["is_active"] or _field(row, "deleted_at") is not None:
        return False
    cat = repo_products.get_category(row["category_id"])
    brand = repo_products.get_brand(row["brand_id"])
    return bool(
        cat and cat["is_active"] and _field(cat, "deleted_at") is None
        and brand and brand["is_active"] and _field(brand, "deleted_at") is None
    )


def _is_racket(row) -> bool:
    """ไม้แบด = สินค้าที่มีค่าสเปกไม้อย่างน้อยหนึ่งอย่าง หรืออยู่ในหมวดหมู่ไม้แบดมินตัน"""
    if any(_field(row, key) for key, _label, _values in _SPEC_FIELDS):
        return True
    if any(_field(row, k) for k in ("spec_material", "spec_weight_grip", "spec_balance_mm",
                                    "spec_balance_type", "spec_max_tension", "spec_length")):
        return True
    cat_name = str(_field(row, "category_name") or "")
    if "ไม้แบด" in cat_name:
        return True
    return False


def _paginate(page, page_size):
    try:
        page = max(1, int(page))
        page_size = min(MAX_PAGE_SIZE, max(1, int(page_size)))
    except (TypeError, ValueError):
        raise ValueError("เลขหน้าไม่ถูกต้อง") from None
    return page, page_size


def _clean_filters(filters) -> dict:
    """เก็บเฉพาะตัวกรองที่รู้จัก และแปลงราคาเป็นตัวเลข"""
    clean = {k: v for k, v in (filters or {}).items() if k in _FILTER_KEYS and v not in (None, "", [])}
    for key in ("min_price", "max_price"):
        if key in clean:
            try:
                clean[key] = float(clean[key])
            except (TypeError, ValueError):
                raise ValueError("ช่วงราคาต้องเป็นตัวเลข") from None
    return clean


def _list_page(filters, sort, page, page_size, decorate_for_buyer: bool, user_id=None) -> dict:
    page, page_size = _paginate(page, page_size)
    sort = sort if sort in _SORTS else "newest"
    total = repo_products.count_products(filters)
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    rows = repo_products.list_products(filters, sort, limit=page_size, offset=(page - 1) * page_size)
    ratings = repo_reviews.get_summaries([r["id"] for r in rows])
    wish = _buyer_wishlist_ids(user_id) if decorate_for_buyer else None
    return {
        "items": [_decorate(r, ratings, wish) for r in rows],
        "total": total, "page": page, "page_size": page_size, "pages": pages,
    }


def _product_images_list(product_id: int, fallback_path: str = None, conn=None) -> list[dict]:
    """คืนรายการรูปภาพของสินค้า (ถ้าตาราง product_images ว่างแต่มี image_path เดิม จะสร้างรายการหลักให้ 1 รูป)"""
    rows = [dict(r) for r in repo_products.list_product_images(product_id, conn=conn)]
    if not rows and fallback_path:
        rows = [{
            "id": 0,
            "product_id": product_id,
            "path": fallback_path,
            "sort_order": 1,
            "option_value_id": None,
            "color_value": None,
        }]
    for idx, im in enumerate(rows):
        im["is_primary"] = (idx == 0)
    return rows


# ==========================================
# ฝั่งผู้ซื้อและผู้เยี่ยมชม
# ==========================================

def search_products(query=None, filters=None, sort="newest", page=1, page_size=12, user_id=None) -> dict:
    """
    ค้นหา/กรอง/เรียง/แบ่งหน้า (เฉพาะสินค้า+หมวด+แบรนด์ที่เปิดขายและไม่ถูกลบ)
    """
    permissions.require(permissions.SHOP_BROWSE)
    f = _clean_filters(filters)
    f["active_only"] = True
    f["include_deleted"] = False
    if query and str(query).strip():
        f["search"] = str(query).strip()
    return _list_page(f, sort, page, page_size, decorate_for_buyer=True, user_id=user_id)


def _option_dict(option_row, product_row) -> dict:
    d = dict(option_row)
    d["label"] = f"{d['option_type']}: {d['option_value']}"
    d["final_price"] = get_effective_price(product_row, d["extra_price"])
    d["in_stock"] = (d["stock"] or 0) > 0
    return d


def get_product_detail(product_id: int, user_id=None) -> dict:
    """
    หน้ารายละเอียดสินค้า: ข้อมูลสินค้า + options + images + technical_specs + addons + สรุปรีวิว + in_wishlist
    """
    permissions.require(permissions.SHOP_BROWSE)
    row = repo_products.get_product(product_id)
    if not _is_visible(row):
        raise ValueError(_NOT_FOUND)
    avg, count = repo_reviews.get_summary(product_id)
    detail = _decorate(row, {product_id: (avg, count)}, _buyer_wishlist_ids(user_id))
    detail["review_avg"], detail["review_count"] = avg, count
    detail["options"] = [_option_dict(o, row) for o in repo_products.list_options(product_id)]
    detail["has_options"] = bool(detail["options"])
    detail["images"] = _product_images_list(product_id, fallback_path=_field(row, "image_path"))
    detail["color_image_map"] = {str(im["color_value"]).strip(): im["path"] for im in detail["images"] if im.get("color_value")}
    detail["addons"] = [_decorate(a) for a in repo_products.list_addons(product_id)]
    detail["is_racket"] = _is_racket(row)
    uid = user_id or Session.get_user_id()
    if uid:
        record_recently_viewed(uid, product_id)
    return detail


def compare_products(ids) -> list[dict]:
    """
    เปรียบเทียบไม้ 2–5 ไม้ตามข้อกำหนด PDF (เฉพาะไม้แบดที่เปิดขายและไม่ถูกลบ) คืน list[dict] ตามลำดับที่เลือก
    """
    permissions.require(permissions.SHOP_BROWSE)
    unique = []
    for raw in ids or []:
        try:
            pid = int(raw)
        except (TypeError, ValueError):
            raise ValueError("รหัสสินค้าไม่ถูกต้อง") from None
        if pid not in unique:
            unique.append(pid)
    if not MIN_COMPARE <= len(unique) <= MAX_COMPARE:
        raise ValueError(f"เลือกไม้ {MIN_COMPARE}-{MAX_COMPARE} ไม้เพื่อเปรียบเทียบ (เลือกได้ 2-3 หรือสูงสุด 5 ไม้)")
    rows = repo_products.get_products_by_ids(unique)
    if len(rows) != len(unique) or not all(_is_visible(r) for r in rows):
        raise ValueError("ไม่พบสินค้าที่เลือกบางรายการ หรือสินค้าถูกปิดการขาย")
    if not all(_is_racket(r) for r in rows):
        raise ValueError("เปรียบเทียบได้เฉพาะไม้แบดมินตัน")
    ratings = repo_reviews.get_summaries(unique)
    return [_decorate(r, ratings) for r in rows]


def recommend_rackets(level: str, style: str, budget=None, limit: int = 6,
                      flex: str = None, balance: str = None, weight_class: str = None) -> list[dict]:
    """
    ตัวช่วยเลือกไม้ตามระดับฝีมือ สไตล์การเล่น งบประมาณ และความชอบเพิ่มเติม (ก้าน/จุดสมดุล/น้ำหนัก)
    คืนเฉพาะไม้ที่เปิดขาย ไม่ถูกลบ และมีสต็อก
    """
    permissions.require(permissions.SHOP_BROWSE)
    allowed_levels = _allowed_spec_values("level")
    if level not in allowed_levels:
        raise ValueError("กรุณาเลือกระดับฝีมือ")
    if style not in _STYLE_RULES:
        raise ValueError("กรุณาเลือกสไตล์การเล่น")
    filters = {"active_only": True, "in_stock": True, "include_deleted": False}
    if budget not in (None, ""):
        try:
            budget = float(budget)
        except (TypeError, ValueError):
            raise ValueError("งบประมาณต้องเป็นตัวเลข") from None
        if budget <= 0:
            raise ValueError("งบประมาณต้องมากกว่า 0")
        filters["max_price"] = budget

    good_balance, good_flex = _STYLE_RULES[style]
    user_idx = allowed_levels.index(level) if level in allowed_levels else 0
    scored = []
    for row in repo_products.list_products(filters):
        if not _is_racket(row):
            continue
        score, reasons = 0, []
        if row["level"] in allowed_levels:
            diff = allowed_levels.index(row["level"]) - user_idx
            if diff >= 2:
                continue  # ไม้ยากเกินฝีมือ
            if diff == 0:
                score += 3
                reasons.append(f"ระดับ {row['level']} ตรงกับฝีมือของคุณ")
            elif abs(diff) == 1:
                score += 1
                reasons.append("ระดับใกล้เคียงกับฝีมือของคุณ")
        if row["balance"] in good_balance:
            score += 3
            reasons.append(f"จุดสมดุล {row['balance']} เหมาะกับสไตล์{STYLE_LABELS[style]}")
        if balance and row["balance"] == balance:
            score += 2
            if f"จุดสมดุล {balance}" not in " ".join(reasons):
                reasons.append(f"จุดสมดุล {balance} ตรงกับที่ต้องการ")
        if row["flex"] in good_flex:
            score += 2
            reasons.append(f"ก้าน {row['flex']} เหมาะกับสไตล์{STYLE_LABELS[style]}")
        if flex and row["flex"] == flex:
            score += 2
            if f"ก้าน {flex}" not in " ".join(reasons):
                reasons.append(f"ความแข็งก้าน {flex} ตรงกับที่เลือก")
        if weight_class and row["weight_class"] == weight_class:
            score += 1
            reasons.append(f"น้ำหนัก {weight_class} คล่องตัวตามที่เลือก")
        if score >= 3:
            scored.append((score, get_effective_price(row), row, reasons))

    scored.sort(key=lambda t: (-t[0], t[1], t[2]["id"]))
    top = scored[:max(1, int(limit))]
    ratings = repo_reviews.get_summaries([t[2]["id"] for t in top])
    result = []
    for score, _price, row, reasons in top:
        d = _decorate(row, ratings)
        d["match_score"], d["match_reasons"] = score, reasons
        result.append(d)
    return result


def get_best_sellers(limit: int = 5, rackets_only: bool = False) -> list[dict]:
    """
    สินค้าขายดีอิงจากยอดขายจริงในฐานข้อมูล (เฉพาะออเดอร์ที่ชำระแล้วและสินค้ายังเปิดขายอยู่)
    หากยังไม่มีประวัติยอดขาย จะใช้สินค้าแนะนำที่เปิดขายอยู่เป็น fallback
    """
    limit = max(1, min(20, int(limit or 5)))
    top_rows = repo_orders.top_products(n=limit * 3)
    sold_map = {r["product_id"]: int(r["total_qty"] or 0) for r in top_rows if r["product_id"]}
    result = []
    if sold_map:
        products = repo_products.get_products_by_ids(list(sold_map.keys()))
        ratings = repo_reviews.get_summaries([p["id"] for p in products])
        for p in products:
            if not _is_visible(p):
                continue
            if rackets_only and not _is_racket(p):
                continue
            d = _decorate(p, ratings)
            d["sold_qty"] = sold_map.get(p["id"], 0)
            result.append(d)
            if len(result) >= limit:
                return result

    # Fallback เมื่อยังไม่มีออเดอร์หรือมีไม่ครบจำนวน
    seen = {d["id"] for d in result}
    rows = repo_products.list_products({"active_only": True, "in_stock": True}, sort="popular", limit=limit * 3)
    ratings = repo_reviews.get_summaries([r["id"] for r in rows])
    for r in rows:
        if r["id"] in seen:
            continue
        if rackets_only and not _is_racket(r):
            continue
        d = _decorate(r, ratings)
        d["sold_qty"] = sold_map.get(r["id"], 0)
        result.append(d)
        if len(result) >= limit:
            break
    return result


def suggest_products(query: str, limit: int = 8) -> list[dict]:
    """คำค้นหาแนะนำ (Autocomplete — E8): คืนสินค้า/แบรนด์/หมวดหมู่ที่เปิดขายและไม่ถูกลบ"""
    q = str(query or "").strip()[:50]
    if len(q) < 2:
        return []
    limit = max(1, min(15, int(limit or 8)))
    suggestions = []

    q_lower = q.lower()
    for b in repo_products.list_brands(active_only=True):
        if q_lower in str(b["name"]).lower():
            suggestions.append({"type": "brand", "id": b["id"], "label": f"แบรนด์: {b['name']}"})
    for c in repo_products.list_categories(active_only=True):
        if q_lower in str(c["name"]).lower():
            suggestions.append({"type": "category", "id": c["id"], "label": f"หมวดหมู่: {c['name']}"})

    rows = repo_products.list_products({"active_only": True, "search": q}, sort="popular", limit=limit)
    for r in rows:
        suggestions.append({
            "type": "product",
            "id": r["id"],
            "label": r["name"],
            "brand_name": r["brand_name"],
            "price": get_effective_price(r),
            "image_path": r["image_path"],
        })
        if len(suggestions) >= limit:
            break
    return suggestions[:limit]


def get_cards_by_ids(ids, limit: int = 10, user_id: int = None) -> list[dict]:
    """ดึงการ์ดสินค้าตามรายการ id โดยคงลำดับเดิมและข้ามสินค้าที่ปิดขาย/ถูกลบ (ใช้กับ 'สินค้าที่ดูล่าสุด' E8)"""
    clean_ids = []
    for raw in (ids or [])[:20]:
        try:
            pid = int(raw)
        except (TypeError, ValueError):
            continue
        if pid not in clean_ids:
            clean_ids.append(pid)
    if not clean_ids:
        return []
    rows = repo_products.get_products_by_ids(clean_ids)
    visible = [r for r in rows if _is_visible(r)][:max(1, min(20, int(limit or 10)))]
    ratings = repo_reviews.get_summaries([r["id"] for r in visible])
    wish = _buyer_wishlist_ids(user_id) if user_id is not None else None
    return [_decorate(r, ratings, wish) for r in visible]


def get_login_showcase(limit: int = 50) -> list[dict]:
    """
    รายการสินค้าสำหรับแผงด้านซ้ายของหน้า Login/Register (T09):
    แสดงสุ่มสินค้าทั้งหมดที่เปิดขายในร้าน (ไม่ต้องการการล็อกอิน)
    """
    max_items = max(1, min(200, int(limit or 50)))
    all_rows = list(repo_products.list_products({"active_only": True}, sort="newest", limit=200))
    if not all_rows:
        return []
    with_img = [r for r in all_rows if _field(r, "image_path")]
    pool = with_img if with_img else all_rows
    random.shuffle(pool)
    return [_decorate(r) for r in pool[:max_items]]


def list_filter_values() -> dict:
    """
    ค่าที่ใช้สร้างตัวกรองฝั่งผู้ซื้อ (T02):
    brands/categories (id+name เฉพาะที่เปิด) และค่าสเปกที่ดึงจากชุดตัวเลือกที่ Owner ตั้งค่าไว้
    รวมกับค่าที่มีอยู่จริงในสินค้าที่เปิดขายอยู่
    """
    permissions.require_any(permissions.SHOP_BROWSE, permissions.PRODUCT_VIEW)
    spec_filters = {}
    for key, _label, _values in _SPEC_FIELDS:
        configured = repo_products.list_active_option_values_by_key(key)
        distinct_in_use = repo_products.list_distinct_values(key)
        merged = list(configured)
        for v in distinct_in_use:
            if v not in merged:
                merged.append(v)
        spec_filters[key] = merged
    return {
        "brands": [{"id": b["id"], "name": b["name"]} for b in repo_products.list_brands(True)],
        "categories": [{"id": c["id"], "name": c["name"]} for c in repo_products.list_categories(True)],
        **spec_filters,
    }


def list_categories(include_inactive: bool = False, include_deleted: bool = False) -> list[dict]:
    """หมวดหมู่ (id, name, image_path, is_active, all_brands, brand_ids) — include_inactive ต้องเป็นแอดมิน/เจ้าของ"""
    _require_catalog(include_inactive)
    rows = repo_products.list_categories(not include_inactive, include_deleted=False)
    result = []
    for r in rows:
        d = dict(r)
        d["all_brands"] = bool(_field(r, "all_brands") if _field(r, "all_brands") is not None else 1)
        d["brand_ids"] = repo_products.get_category_brand_ids(d["id"])
        d["product_count"] = repo_products.count_products_in_category(d["id"])
        result.append(d)
    return result


def list_brands(include_inactive: bool = False, category_id: int = None, include_deleted: bool = False) -> list[dict]:
    """แบรนด์ (id, name, logo_path, is_active) — ถ้าระบุ category_id จะกรองเฉพาะแบรนด์ที่ผูกกับหมวดนั้น"""
    _require_catalog(include_inactive)
    if category_id is not None:
        rows = repo_products.list_brands_for_category(int(category_id), active_only=not include_inactive)
    else:
        rows = repo_products.list_brands(not include_inactive, include_deleted=False)
    result = []
    for r in rows:
        d = dict(r)
        d["product_count"] = repo_products.count_products_in_brand(d["id"])
        result.append(d)
    return result


def _require_catalog(include_inactive: bool) -> None:
    if include_inactive:
        permissions.require(permissions.PRODUCT_VIEW)
    else:
        permissions.require_any(permissions.SHOP_BROWSE, permissions.PRODUCT_VIEW)


# ==========================================
# ชุดตัวเลือกตามหมวดหมู่ (T02 — Owner ตั้งค่าเพิ่ม/แก้/ปิดใช้งานได้เอง)
# ==========================================

def _allowed_spec_values(key: str, category_id: int = None, current_value: str = None) -> tuple[str, ...]:
    """รวมค่ามาตรฐานเดิมกับค่าที่ Owner ตั้งไว้ใน option_values (และอนุญาตค่าเดิมของสินค้าหากถูกปิดใช้งานภายหลัง)"""
    base_map = {
        "weight_class": WEIGHT_CLASSES,
        "balance": BALANCES,
        "flex": FLEXES,
        "level": LEVELS,
    }
    configured = repo_products.list_active_option_values_by_key(key, category_id=category_id)
    if not configured and category_id is not None:
        configured = repo_products.list_active_option_values_by_key(key, category_id=None)
    merged = []
    for val in list(configured) + list(base_map.get(key, ())):
        if val and val not in merged:
            merged.append(val)
    if current_value and current_value not in merged:
        merged.append(current_value)
    return tuple(merged)


def get_allowed_racket_spec_options(category_id: int = None, current_product: dict = None) -> dict[str, list[str]]:
    """คืนตัวเลือกที่อนุญาตให้เลือกสำหรับไม้แบด (weight_class, balance, flex, level) จากที่ Owner ตั้งค่าไว้"""
    permissions.require_any(permissions.SHOP_BROWSE, permissions.PRODUCT_VIEW)
    cur = current_product or {}
    out = {}
    for key in ("weight_class", "balance", "flex", "level"):
        vals = list(_allowed_spec_values(key, category_id=category_id, current_value=cur.get(key)))
        out[key] = vals
    return out


def list_category_option_groups(category_id: int = None, include_inactive: bool = False) -> list[dict]:
    """
    ดึงรายการชุดตัวเลือก (option_groups) พร้อมรายการค่า (option_values) ของหมวดหมู่
    - อ่านเฉพาะที่ active: ผู้ซื้อ/แอดมิน/เจ้าของดูได้
    - include_inactive=True: ต้องมีสิทธิ์ดูสินค้าหลังบ้านหรือจัดการหมวดหมู่
    """
    if include_inactive:
        permissions.require_any(permissions.PRODUCT_VIEW, permissions.CATEGORY_MANAGE)
    else:
        permissions.require_any(permissions.SHOP_BROWSE, permissions.PRODUCT_VIEW, permissions.CATEGORY_MANAGE)
    groups = repo_products.list_option_groups(category_id=category_id, active_only=not include_inactive)
    result = []
    for g in groups:
        gd = dict(g)
        gd["is_active"] = bool(gd.get("is_active", 1))
        vals = repo_products.list_option_values(gd["id"], active_only=not include_inactive)
        gd["values"] = [
            {**dict(v), "is_active": bool(v["is_active"])}
            for v in vals
        ]
        result.append(gd)
    return result


def save_category_option_group(category_id: int, key: str, label: str,
                               sort_order: int = 0, is_active: bool = True,
                               group_id: int = None) -> dict:
    """เพิ่มหรือแก้ไขชุดตัวเลือกของหมวดหมู่ (Owner เท่านั้น — T02)"""
    permissions.require(permissions.CATEGORY_MANAGE)
    if repo_products.get_category(int(category_id)) is None:
        raise ValueError("ไม่พบหมวดหมู่สินค้า")
    clean_key = str(key or "").strip().lower().replace(" ", "_")
    clean_label = str(label or "").strip()
    if not clean_key:
        raise ValueError("กรุณาระบุรหัสชุดตัวเลือก (key)")
    if not clean_label:
        raise ValueError("กรุณากรอกชื่อชุดตัวเลือก")
    if len(clean_label) > 100:
        raise ValueError("ชื่อชุดตัวเลือกยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    try:
        if group_id is None:
            existing = repo_products.get_option_group_by_key(int(category_id), clean_key)
            if existing is not None:
                group_id = existing["id"]
                repo_products.update_option_group(group_id, label=clean_label, sort_order=sort_order, is_active=is_active)
            else:
                group_id = repo_products.create_option_group(
                    int(category_id), clean_key, clean_label, sort_order=sort_order, is_active=is_active
                )
        else:
            if not repo_products.update_option_group(group_id, label=clean_label, sort_order=sort_order, is_active=is_active):
                raise ValueError("ไม่พบชุดตัวเลือก")
        audit_service.log("option_group.save", "option_group", group_id, {"key": clean_key, "label": clean_label})
    except sqlite3.IntegrityError:
        raise ValueError("มีชุดตัวเลือกรหัสนี้ในหมวดหมู่นี้แล้ว") from None
    g = dict(repo_products.get_option_group(group_id))
    g["values"] = [dict(v) for v in repo_products.list_option_values(group_id, active_only=False)]
    return g


def toggle_category_option_group(group_id: int, active: bool = None) -> dict:
    """เปิด/ปิดใช้งานชุดตัวเลือก (Owner เท่านั้น — ห้ามลบจริงเพื่อรักษาข้อมูลเก่า)"""
    permissions.require(permissions.CATEGORY_MANAGE)
    row = repo_products.get_option_group(group_id)
    if row is None:
        raise ValueError("ไม่พบชุดตัวเลือก")
    new_active = (not bool(row["is_active"])) if active is None else bool(active)
    repo_products.set_option_group_active(group_id, new_active)
    audit_service.log("option_group.toggle", "option_group", group_id, {"is_active": new_active})
    return dict(repo_products.get_option_group(group_id))


def save_category_option_value(group_id: int, value: str, label: str = None,
                               sort_order: int = None, is_active: bool = True,
                               value_id: int = None) -> dict:
    """เพิ่มหรือแก้ไขค่าตัวเลือกในชุดตัวเลือก (Owner เท่านั้น — เช่น เพิ่ม 5U..10U, ความเร็วลูก 74-77, ไซส์, สี)"""
    permissions.require(permissions.CATEGORY_MANAGE)
    grp = repo_products.get_option_group(int(group_id))
    if grp is None:
        raise ValueError("ไม่พบชุดตัวเลือก")
    clean_val = str(value or "").strip()
    if not clean_val:
        raise ValueError("กรุณากรอกค่าตัวเลือก")
    if len(clean_val) > 100:
        raise ValueError("ค่าตัวเลือกยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    clean_lbl = str(label or "").strip() or clean_val
    existing_vals = repo_products.list_option_values(int(group_id), active_only=False)
    if sort_order is None:
        sort_order = (max((int(v["sort_order"] or 0) for v in existing_vals), default=0) + 1)
    try:
        if value_id is None:
            # ถ้ามีค่านี้อยู่แล้วแต่ถูกปิดใช้งาน ให้เปิดใช้งานและอัปเดต label แทน
            dup = next((v for v in existing_vals if str(v["value"]).strip().lower() == clean_val.lower()), None)
            if dup is not None:
                value_id = dup["id"]
                repo_products.update_option_value(
                    value_id, value=clean_val, label=clean_lbl, sort_order=sort_order, is_active=True
                )
            else:
                value_id = repo_products.create_option_value(
                    int(group_id), clean_val, label=clean_lbl, sort_order=sort_order, is_active=is_active
                )
        else:
            if not repo_products.update_option_value(
                int(value_id), value=clean_val, label=clean_lbl, sort_order=sort_order, is_active=is_active
            ):
                raise ValueError("ไม่พบค่าตัวเลือก")
        audit_service.log("option_value.save", "option_value", value_id, {"group_id": group_id, "value": clean_val})
    except sqlite3.IntegrityError:
        raise ValueError("มีค่าตัวเลือกนี้อยู่ในชุดตัวเลือกแล้ว") from None
    return dict(repo_products.get_option_value(value_id))


def toggle_category_option_value(value_id: int, active: bool = None) -> dict:
    """เปิด/ปิดใช้งานค่าตัวเลือก (Owner เท่านั้น — สินค้าเดิมที่ใช้อยู่ยังแสดงค่าเดิมได้)"""
    permissions.require(permissions.CATEGORY_MANAGE)
    row = repo_products.get_option_value(int(value_id))
    if row is None:
        raise ValueError("ไม่พบค่าตัวเลือก")
    new_active = (not bool(row["is_active"])) if active is None else bool(active)
    repo_products.set_option_value_active(int(value_id), new_active)
    audit_service.log("option_value.toggle", "option_value", value_id, {"is_active": new_active})
    return dict(repo_products.get_option_value(int(value_id)))


def reorder_category_option_values(group_id: int, value_ids: list[int]) -> list[dict]:
    """เรียงลำดับค่าตัวเลือกในชุดตัวเลือก (Owner เท่านั้น)"""
    permissions.require(permissions.CATEGORY_MANAGE)
    with transaction() as conn:
        for idx, vid in enumerate(value_ids or [], start=1):
            repo_products.update_option_value(int(vid), sort_order=idx, conn=conn)
    return [dict(v) for v in repo_products.list_option_values(int(group_id), active_only=False)]


def quick_add_racket_weights(category_id: int = None, weights: list[str] = None) -> list[dict]:
    """ช่วย Owner เพิ่มน้ำหนักไม้แบด (เช่น 3U, 4U, 5U ... 10U) เข้าหมวดไม้แบดมินตันได้ทันที"""
    permissions.require(permissions.CATEGORY_MANAGE)
    if category_id is None:
        cats = repo_products.list_categories(active_only=False)
        racket_cat = next((c for c in cats if "ไม้แบด" in str(c["name"])), None)
        if racket_cat is None:
            raise ValueError("ไม่พบหมวดหมู่ไม้แบดมินตัน")
        category_id = racket_cat["id"]
    grp = repo_products.get_option_group_by_key(int(category_id), "weight_class")
    if grp is None:
        gid = repo_products.create_option_group(int(category_id), "weight_class", "น้ำหนักไม้ (Weight Class)", sort_order=1)
    else:
        gid = grp["id"]
    target_weights = weights or ["3U", "4U", "5U", "6U", "7U", "8U", "9U", "10U"]
    added = []
    for idx, w in enumerate(target_weights, start=1):
        added.append(save_category_option_value(gid, w, label=w, sort_order=idx, is_active=True))
    return added


# ==========================================
# ฝั่งแอดมิน/เจ้าของ — ดูข้อมูล
# ==========================================

def list_products_admin(search=None, filters=None, sort="newest", page=1, page_size=20,
                        show_inactive: bool = True) -> dict:
    """รายการสินค้าหลังบ้าน (รวมสินค้าที่ปิดขายเมื่อ show_inactive แต่ไม่รวมที่ถูกลบเข้าถัง)"""
    permissions.require(permissions.PRODUCT_VIEW)
    f = _clean_filters(filters)
    f["active_only"] = not show_inactive
    f["include_deleted"] = False
    if search and str(search).strip():
        f["search"] = str(search).strip()
    return _list_page(f, sort, page, page_size, decorate_for_buyer=False)


def _admin_detail(product_id: int, conn=None) -> dict:
    row = repo_products.get_product(product_id, conn=conn)
    if row is None:
        raise ValueError("ไม่พบสินค้า")
    d = _decorate(row)
    d["options"] = [_option_dict(o, row) for o in repo_products.list_options(product_id, conn=conn)]
    d["has_options"] = bool(d["options"])
    d["images"] = _product_images_list(product_id, fallback_path=_field(row, "image_path"), conn=conn)
    d["color_image_map"] = {str(im["color_value"]).strip(): im["path"] for im in d["images"] if im.get("color_value")}
    d["addons"] = [dict(a) for a in repo_products.list_addons(product_id, conn=conn)]
    return d


def get_product_for_edit(product_id: int) -> dict:
    """สินค้า 1 ชิ้นสำหรับฟอร์มแก้ไข (แม้ปิดขายอยู่): ข้อมูล + options + images + addons"""
    permissions.require(permissions.PRODUCT_VIEW)
    return _admin_detail(product_id)


def get_low_stock_products() -> dict:
    """
    สินค้า/ตัวเลือกที่สต็อก <= เกณฑ์ใน settings (low_stock_threshold) สำหรับ Dashboard
    """
    permissions.require(permissions.PRODUCT_VIEW)
    threshold = settings_service.get_int("low_stock_threshold", 5)
    return {
        "threshold": threshold,
        "products": [dict(r) for r in repo_products.list_low_stock(threshold)],
        "options": [dict(r) for r in repo_products.list_low_stock_options(threshold)],
    }


# ==========================================
# ฝั่งแอดมิน/เจ้าของ — แก้ข้อมูล
# ==========================================

def _clean_number(value, label: str, *, allow_none=False, integer=False, minimum=0, strict_min=False):
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_none:
            return None
        raise ValueError(f"กรุณากรอก{label}")
    try:
        number = float(str(value).strip().replace(",", ""))
    except ValueError:
        raise ValueError(f"{label}ต้องเป็นตัวเลข") from None
    if not math.isfinite(number):
        raise ValueError(f"{label}ต้องเป็นตัวเลข")
    if integer:
        if number != int(number):
            raise ValueError(f"{label}ต้องเป็นจำนวนเต็ม")
        number = int(number)
    else:
        number = round(number, 2)
    if (number <= minimum) if strict_min else (number < minimum):
        raise ValueError(f"{label}ต้องมากกว่า {minimum}" if strict_min else f"{label}ต้องไม่น้อยกว่า {minimum}")
    return number


def _clean_sale_end(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    dt = parse_datetime(value)
    if dt is None:
        raise ValueError("รูปแบบเวลาสิ้นสุดโปรโมชันไม่ถูกต้อง (ใช้ ปปปป-ดด-วว ชช:นน)")
    if isinstance(value, str) and len(value.strip()) <= 10:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _clean_spec(value, label, allowed):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    val = str(value).strip()
    if val not in allowed:
        raise ValueError(f"ค่า{label}ไม่ถูกต้อง (เลือกได้: {', '.join(allowed)})")
    return val


def _clean_free_spec(value, label: str, max_len: int = 250) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    txt = str(value).strip()
    if len(txt) > max_len:
        raise ValueError(f"{label}ยาวเกินไป (ไม่เกิน {max_len} ตัวอักษร)")
    return txt


def _same_number(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) < 0.005


def save_product(fields: dict, product_id: int = None) -> dict:
    """
    เพิ่ม (product_id=None) หรือแก้สินค้า — คืน dict สินค้าล่าสุด (เหมือน get_product_for_edit)
    รองรับ Technical Specifications (T03) และค่าตัวเลือกที่ Owner ตั้งค่าเพิ่มไว้ (T02)
    """
    creating = product_id is None
    permissions.require(permissions.PRODUCT_CREATE if creating else permissions.PRODUCT_EDIT)
    is_owner = Session.get_role() == ROLE_OWNER

    current = None
    if not creating:
        current = repo_products.get_product(product_id)
        if current is None:
            raise ValueError("ไม่พบสินค้า")
    fields = dict(fields or {})
    clean = {}

    if creating or "name" in fields:
        name = str(fields.get("name") or "").strip()
        if not name:
            raise ValueError("กรุณากรอกชื่อสินค้า")
        if len(name) > 200:
            raise ValueError("ชื่อสินค้ายาวเกินไป (ไม่เกิน 200 ตัวอักษร)")
        clean["name"] = name
    if "description" in fields or creating:
        desc = str(fields.get("description") or "").strip()
        if len(desc) > 5000:
            raise ValueError("คำอธิบายยาวเกินไป (ไม่เกิน 5,000 ตัวอักษร)")
        clean["description"] = desc
    for key, label, getter in (("category_id", "หมวดหมู่", repo_products.get_category),
                               ("brand_id", "แบรนด์", repo_products.get_brand)):
        if creating or key in fields:
            try:
                ref = getter(int(fields.get(key)))
            except (TypeError, ValueError):
                ref = None
            if ref is None or _field(ref, "deleted_at") is not None:
                raise ValueError(f"กรุณาเลือก{label}")
            clean[key] = ref["id"]

    # ตรวจความสอดคล้องของหมวดหมู่และแบรนด์ (เมื่อหมวดนั้นกำหนดเฉพาะบางแบรนด์)
    final_cat_id = clean.get("category_id", current["category_id"] if current else None)
    final_brand_id = clean.get("brand_id", current["brand_id"] if current else None)
    if final_cat_id is not None and final_brand_id is not None:
        cat_row = repo_products.get_category(final_cat_id)
        if cat_row is not None and not (_field(cat_row, "all_brands") if _field(cat_row, "all_brands") is not None else 1):
            allowed_brands = repo_products.get_category_brand_ids(final_cat_id)
            if allowed_brands and final_brand_id not in allowed_brands:
                raise ValueError("แบรนด์ที่เลือกไม่ได้ผูกกับหมวดหมู่นี้")

    if creating or "price" in fields:
        clean["price"] = _clean_number(fields.get("price"), "ราคา", minimum=0, strict_min=True)
    if "sale_price" in fields:
        clean["sale_price"] = _clean_number(fields["sale_price"], "ราคาลด", allow_none=True,
                                            minimum=0, strict_min=True)
    if "sale_ends_at" in fields:
        clean["sale_ends_at"] = _clean_sale_end(fields["sale_ends_at"])
    if "cost_price" in fields:
        clean["cost_price"] = _clean_number(fields["cost_price"], "ราคาต้นทุน", allow_none=True, minimum=0)
    if "image_path" in fields:
        clean["image_path"] = fields["image_path"] or None

    for key, label, _default_allowed in _SPEC_FIELDS:
        if key in fields:
            cur_val = _field(current, key) if current else None
            allowed_vals = _allowed_spec_values(key, category_id=final_cat_id, current_value=cur_val)
            clean[key] = _clean_spec(fields[key], label, allowed_vals)

    # Technical Specifications (T03)
    if "spec_material" in fields:
        clean["spec_material"] = _clean_free_spec(fields["spec_material"], "Material", 300)
    if "spec_weight_grip" in fields:
        clean["spec_weight_grip"] = _clean_free_spec(fields["spec_weight_grip"], "Weight Class / Grip", 200)
    if "spec_balance_mm" in fields:
        clean["spec_balance_mm"] = validators.normalize_balance_point_mm(fields["spec_balance_mm"])
    if "spec_balance_type" in fields:
        cur_bt = _field(current, "spec_balance_type") or (_field(current, "balance") if current else None)
        allowed_bal = _allowed_spec_values("balance", category_id=final_cat_id, current_value=cur_bt)
        clean["spec_balance_type"] = _clean_spec(fields["spec_balance_type"], "จุดสมดุล (Balance Type)", allowed_bal)
        if "balance" not in clean and clean["spec_balance_type"] is not None:
            clean["balance"] = clean["spec_balance_type"]
    elif "balance" in clean and clean["balance"] is not None:
        clean["spec_balance_type"] = clean["balance"]
    if "spec_max_tension" in fields:
        clean["spec_max_tension"] = _clean_free_spec(fields["spec_max_tension"], "Max String Tension", 120)
    if "spec_length" in fields:
        clean["spec_length"] = _clean_free_spec(fields["spec_length"], "Length", 120)

    has_options = bool(current) and bool(repo_products.list_options(product_id))
    if "stock" in fields and not has_options:
        clean["stock"] = _clean_number(fields["stock"], "สต็อก", integer=True, minimum=0)
    elif creating and "stock" not in fields:
        clean["stock"] = 0

    final_price = clean.get("price", current["price"] if current else None)
    final_sale = clean["sale_price"] if "sale_price" in clean else (current["sale_price"] if current else None)
    if final_sale is None:
        if clean.get("sale_ends_at"):
            raise ValueError("กำหนดเวลาโปรโมชันต้องมีราคาลดด้วย")
        if "sale_price" in clean:
            clean["sale_ends_at"] = None
    elif final_sale >= final_price:
        raise ValueError("ราคาลดต้องน้อยกว่าราคาปกติ")

    if not is_owner:
        old_price = current["price"] if current else None
        old_sale = current["sale_price"] if current else None
        old_end = current["sale_ends_at"] if current else None
        price_changed = (not creating) and "price" in clean and not _same_number(clean["price"], old_price)
        sale_changed = (("sale_price" in clean and not _same_number(clean["sale_price"], old_sale))
                        or ("sale_ends_at" in clean and clean["sale_ends_at"] != old_end))
        if price_changed or sale_changed:
            raise PermissionError("เฉพาะเจ้าของร้านเท่านั้นที่เปลี่ยนราคาหรือตั้งโปรโมชันได้")

    try:
        if creating:
            new_id = repo_products.create_product(
                clean["category_id"], clean["brand_id"], clean["name"], clean.get("description", ""),
                clean["price"], sale_price=clean.get("sale_price"), sale_ends_at=clean.get("sale_ends_at"),
                stock=clean.get("stock", 0), image_path=clean.get("image_path"),
                weight_class=clean.get("weight_class"), balance=clean.get("balance"),
                flex=clean.get("flex"), level=clean.get("level"),
                cost_price=clean.get("cost_price"),
                spec_material=clean.get("spec_material"),
                spec_weight_grip=clean.get("spec_weight_grip"),
                spec_balance_mm=clean.get("spec_balance_mm"),
                spec_balance_type=clean.get("spec_balance_type"),
                spec_max_tension=clean.get("spec_max_tension"),
                spec_length=clean.get("spec_length"),
            )
            audit_service.log("product.create", "product", new_id, {"name": clean["name"], "price": clean["price"]})
            return _admin_detail(new_id)
        if clean:
            repo_products.update_product(product_id, clean)
            if "image_path" in clean and clean["image_path"]:
                imgs = repo_products.list_product_images(product_id)
                if not imgs:
                    repo_products.add_product_image(product_id, clean["image_path"], sort_order=1)
            audit_service.log("product.update", "product", product_id, clean)
        return _admin_detail(product_id)
    except sqlite3.IntegrityError:
        raise ValueError("บันทึกสินค้าไม่สำเร็จ ข้อมูลไม่ถูกต้อง") from None


def set_product_active(product_id: int, active: bool) -> dict:
    """เปิด/ปิดขายสินค้า (เจ้าของร้านเท่านั้น)"""
    permissions.require(permissions.PRODUCT_DELETE)
    if not repo_products.set_product_active(product_id, bool(active)):
        raise ValueError("ไม่พบสินค้า")
    audit_service.log("product.set_active", "product", product_id, {"is_active": bool(active)})
    return _admin_detail(product_id)


def delete_product(product_id: int) -> dict:
    """
    ลบสินค้าแบบ Soft Delete (OWN-2):
    ตั้ง deleted_at และปิด is_active = 0 เพื่อย้ายเข้าหน้า 'สินค้าที่ถูกลบ' โดยไม่ทำลายประวัติออเดอร์/ยอดขาย
    """
    permissions.require(permissions.PRODUCT_DELETE)
    row = repo_products.get_product(product_id)
    if row is None:
        raise ValueError("ไม่พบสินค้า")
    actor_id = Session.get_user_id()
    with transaction() as conn:
        repo_products.soft_delete_product(product_id, deleted_by=actor_id, conn=conn)
        audit_service.log("product.delete", "product", product_id, {"name": row["name"]}, conn=conn)
    return _admin_detail(product_id)


def restore_product(product_id: int, activate: bool = True) -> dict:
    """กู้คืนสินค้าที่ถูกลบให้กลับมาเปิดขายตามปกติ (OWN-2)"""
    permissions.require(permissions.PRODUCT_DELETE)
    row = repo_products.get_product(product_id)
    if row is None:
        raise ValueError("ไม่พบสินค้า")
    with transaction() as conn:
        repo_products.restore_product(product_id, conn=conn)
        audit_service.log("product.restore", "product", product_id, {"name": row["name"]}, conn=conn)
    return _admin_detail(product_id)


def list_deleted_products(search: str = None) -> list[dict]:
    """รายการสินค้าในถัง 'สินค้าที่ถูกลบ' พร้อมจำนวนที่เคยขายได้และรายได้รวม (OWN-2)"""
    permissions.require(permissions.PRODUCT_VIEW)
    rows = repo_products.list_deleted_products(search=search)
    return [dict(r) for r in rows]


def adjust_stock(product_id: int, delta: int, option_id: int = None) -> dict:
    """
    ปรับสต็อกแบบ +/- (แอดมิน+เจ้าของ) — สินค้าที่มีตัวเลือกต้องระบุ option_id (สต็อกรวมถูก sync ให้เอง)
    """
    permissions.require(permissions.STOCK_UPDATE)
    if isinstance(delta, bool) or not isinstance(delta, int) or delta == 0:
        raise ValueError("จำนวนที่ปรับต้องเป็นจำนวนเต็มและไม่เท่ากับ 0")
    with transaction() as conn:
        if repo_products.get_product(product_id, conn=conn) is None:
            raise ValueError("ไม่พบสินค้า")
        options = repo_products.list_options(product_id, conn=conn)
        if options:
            if option_id is None:
                raise ValueError("สินค้านี้มีตัวเลือก กรุณาเลือกตัวเลือกที่จะปรับสต็อก")
            if option_id not in {o["id"] for o in options}:
                raise ValueError("ตัวเลือกนี้ไม่ได้เป็นของสินค้านี้")
            ok = repo_products.adjust_option_stock(option_id, delta, conn=conn)
        else:
            if option_id is not None:
                raise ValueError("สินค้านี้ไม่มีตัวเลือก")
            ok = repo_products.adjust_stock(product_id, delta, conn=conn)
        if not ok:
            raise ValueError("สต็อกไม่พอ ปรับให้ติดลบไม่ได้")
        return _admin_detail(product_id, conn=conn)


def get_allowed_option_types() -> tuple[str, ...]:
    """คืนรายการประเภทตัวเลือกสินค้าทั้งหมด (จาก OPTION_TYPES + ที่ตั้งไว้ใน settings)"""
    custom_raw = settings_service.get("custom_option_types") or ""
    custom = [x.strip() for x in custom_raw.split(",") if x.strip()]
    merged = list(OPTION_TYPES)
    for item in custom:
        if item not in merged:
            merged.append(item)
    return tuple(merged)


def save_option(product_id: int, option_type: str, option_value: str, extra_price=0, stock=0,
                option_id: int = None, image_path: str = None) -> dict:
    """เพิ่ม (option_id=None) หรือแก้ตัวเลือกสินค้า (สี/สไตล์/ด้าม/เอ็น/ไซซ์/ความเร็วลูก ฯลฯ) คืน dict สินค้าล่าสุด"""
    permissions.require(permissions.PRODUCT_EDIT)
    allowed_types = get_allowed_option_types()
    if option_type not in allowed_types:
        raise ValueError(f"ประเภทตัวเลือกไม่ถูกต้อง (เลือกได้: {', '.join(allowed_types)})")
    option_value = str(option_value or "").strip()
    if not option_value:
        raise ValueError("กรุณากรอกชื่อตัวเลือก")
    if len(option_value) > 100:
        raise ValueError("ชื่อตัวเลือกยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    extra = _clean_number(extra_price, "ราคาเพิ่ม", minimum=0)
    qty = _clean_number(stock, "สต็อก", integer=True, minimum=0)
    with transaction() as conn:
        if repo_products.get_product(product_id, conn=conn) is None:
            raise ValueError("ไม่พบสินค้า")
        if option_id is None:
            repo_products.create_option(
                product_id, option_type, option_value, extra, qty, image_path=image_path, conn=conn
            )
        else:
            existing = repo_products.get_option(option_id, conn=conn)
            if existing is None or existing["product_id"] != product_id:
                raise ValueError("ไม่พบตัวเลือกของสินค้านี้")
            repo_products.update_option(
                option_id, option_type, option_value, extra, qty, image_path=image_path, conn=conn
            )
        return _admin_detail(product_id, conn=conn)


def delete_option(option_id: int) -> dict:
    """ลบตัวเลือก — ตัวเลือกที่เคยถูกสั่งซื้อลบไม่ได้ ให้ตั้งสต็อกเป็น 0 แทน"""
    permissions.require(permissions.PRODUCT_EDIT)
    with transaction() as conn:
        option = repo_products.get_option(option_id, conn=conn)
        if option is None:
            raise ValueError("ไม่พบตัวเลือก")
        if repo_products.is_option_used(option_id, conn=conn):
            raise ValueError("ตัวเลือกนี้เคยถูกสั่งซื้อแล้ว ลบไม่ได้ (ตั้งสต็อกเป็น 0 แทน)")
        try:
            repo_products.delete_option(option_id, conn=conn)
        except sqlite3.IntegrityError:
            raise ValueError("ตัวเลือกนี้ถูกใช้งานอยู่ ลบไม่ได้") from None
        return _admin_detail(option["product_id"], conn=conn)


# ==========================================
# รูปภาพหลายรูปของสินค้า (T04)
# ==========================================

def add_product_image(product_id: int, path: str, color_value: str = None,
                      option_value_id: int = None, sort_order: int = None,
                      is_primary: bool = False) -> dict:
    """เพิ่มรูปภาพให้สินค้า (ผูกกับสี/สไตล์ได้) และอัปเดตรูปหลักอัตโนมัติถ้าเป็นรูปแรกหรือระบุ is_primary=True"""
    permissions.require(permissions.PRODUCT_EDIT)
    clean_path = str(path or "").strip()
    if not clean_path:
        raise ValueError("กรุณาเลือกรูปภาพ")
    with transaction() as conn:
        if repo_products.get_product(int(product_id), conn=conn) is None:
            raise ValueError("ไม่พบสินค้า")
        new_id = repo_products.add_product_image(
            int(product_id), clean_path, sort_order=1 if is_primary else sort_order,
            option_value_id=option_value_id, color_value=color_value, conn=conn,
        )
        if is_primary:
            imgs = repo_products.list_product_images(int(product_id), conn=conn)
            ordered_ids = [int(new_id)] + [int(im["id"]) for im in imgs if int(im["id"]) != int(new_id)]
            repo_products.reorder_product_images(int(product_id), ordered_ids, conn=conn)
        return _admin_detail(int(product_id), conn=conn)


def update_product_image(image_id: int, color_value: str = "__keep__",
                         option_value_id: int = None, sort_order: int = None) -> dict:
    """แก้ข้อมูลการผูกรูปกับสี/สไตล์ หรือลำดับการแสดง"""
    permissions.require(permissions.PRODUCT_EDIT)
    with transaction() as conn:
        row = repo_products.get_product_image(int(image_id), conn=conn)
        if row is None:
            raise ValueError("ไม่พบรูปภาพสินค้า")
        repo_products.update_product_image(
            int(image_id), sort_order=sort_order,
            option_value_id=option_value_id, color_value=color_value, conn=conn,
        )
        return _admin_detail(row["product_id"], conn=conn)


def delete_product_image(image_id: int) -> dict:
    """ลบรูปภาพออกจากแกลเลอรีสินค้า และเลื่อนรูปถัดไปขึ้นเป็นรูปหลัก"""
    permissions.require(permissions.PRODUCT_EDIT)
    with transaction() as conn:
        row = repo_products.get_product_image(int(image_id), conn=conn)
        if row is None:
            raise ValueError("ไม่พบรูปภาพสินค้า")
        pid = row["product_id"]
        repo_products.delete_product_image(int(image_id), conn=conn)
        return _admin_detail(pid, conn=conn)


def set_primary_product_image(product_id: int, image_id: int = None) -> dict:
    """ตั้งรูปที่เลือกให้เป็นรูปหลัก (sort_order = 1) รองรับทั้ง (product_id, image_id) และ (image_id)"""
    permissions.require(permissions.PRODUCT_EDIT)
    with transaction() as conn:
        if image_id is None:
            row = repo_products.get_product_image(int(product_id), conn=conn)
            if row is None:
                raise ValueError("ไม่พบรูปภาพสินค้า")
            image_id = int(row["id"])
            product_id = int(row["product_id"])
        imgs = repo_products.list_product_images(int(product_id), conn=conn)
        target = next((img for img in imgs if int(img["id"]) == int(image_id)), None)
        if target is None:
            raise ValueError("ไม่พบรูปภาพสินค้า")
        ordered_ids = [int(image_id)] + [int(img["id"]) for img in imgs if int(img["id"]) != int(image_id)]
        repo_products.reorder_product_images(int(product_id), ordered_ids, conn=conn)
        return _admin_detail(int(product_id), conn=conn)


def reorder_product_images(product_id: int, image_ids: list[int]) -> dict:
    """จัดลำดับรูปภาพของสินค้าใหม่"""
    permissions.require(permissions.PRODUCT_EDIT)
    with transaction() as conn:
        if repo_products.get_product(int(product_id), conn=conn) is None:
            raise ValueError("ไม่พบสินค้า")
        repo_products.reorder_product_images(int(product_id), image_ids, conn=conn)
        return _admin_detail(int(product_id), conn=conn)


def set_addons(product_id: int, addon_ids) -> dict:
    """ตั้งสินค้าเสริม "ซื้อคู่กัน" ของสินค้า"""
    permissions.require(permissions.PRODUCT_EDIT)
    if repo_products.get_product(product_id) is None:
        raise ValueError("ไม่พบสินค้า")
    try:
        ids = [int(i) for i in (addon_ids or [])]
    except (TypeError, ValueError):
        raise ValueError("รหัสสินค้าเสริมไม่ถูกต้อง") from None
    if len(repo_products.get_products_by_ids(ids)) != len(set(ids)):
        raise ValueError("ไม่พบสินค้าเสริมบางรายการ")
    repo_products.set_addons(product_id, ids)
    return _admin_detail(product_id)


# ==========================================
# หมวดหมู่ / แบรนด์ (เจ้าของร้านเท่านั้น — OWN-3)
# ==========================================

def _clean_name(value, label):
    name = str(value or "").strip()
    if not name:
        raise ValueError(f"กรุณากรอกชื่อ{label}")
    if len(name) > 100:
        raise ValueError(f"ชื่อ{label}ยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    return name


def save_category(name: str, category_id: int = None, image_path=None,
                  brand_ids=None, all_brands: bool = None, bind_all_brands: bool = None) -> dict:
    """
    เพิ่ม/แก้หมวดหมู่ พร้อมกำหนดการผูกแบรนด์ (OWN-3):
    - all_brands=True (ค่าเริ่มต้นตอนสร้างใหม่ถ้าไม่ระบุ brand_ids): ผูกกับทุกแบรนด์รวมถึงแบรนด์ใหม่ในอนาคต
    - all_brands=False และส่ง brand_ids: ผูกเฉพาะแบรนด์ที่เลือก
    """
    permissions.require(permissions.CATEGORY_MANAGE)
    name = _clean_name(name, "หมวดหมู่")
    if all_brands is None and bind_all_brands is not None:
        all_brands = bind_all_brands
    if all_brands is None:
        use_all = (brand_ids is None) if category_id is None else None
    else:
        use_all = bool(all_brands)

    try:
        with transaction() as conn:
            if category_id is None:
                category_id = repo_products.create_category(
                    name, image_path, all_brands=True if use_all is None else use_all, conn=conn
                )
                repo_products.set_category_brands(
                    category_id, brand_ids=brand_ids,
                    all_brands=True if use_all is None else use_all, conn=conn
                )
            else:
                if not repo_products.update_category(category_id, name, image_path, all_brands=use_all, conn=conn):
                    raise ValueError("ไม่พบหมวดหมู่")
                if brand_ids is not None or use_all is not None:
                    cat_row = repo_products.get_category(category_id, conn=conn)
                    final_all = bool(_field(cat_row, "all_brands", 1)) if use_all is None else use_all
                    repo_products.set_category_brands(
                        category_id, brand_ids=brand_ids, all_brands=final_all, conn=conn
                    )
            audit_service.log("category.save", "category", category_id, {"name": name}, conn=conn)
    except sqlite3.IntegrityError:
        raise ValueError("มีหมวดหมู่ชื่อนี้อยู่แล้ว") from None

    cat = dict(repo_products.get_category(category_id))
    cat["brand_ids"] = repo_products.get_category_brand_ids(category_id)
    cat["all_brands"] = bool(cat.get("all_brands", 1))
    cat["bind_all_brands"] = 1 if cat["all_brands"] else 0
    return cat


def set_category_active(category_id: int, active: bool) -> dict:
    """เปิด/ปิดหมวด — เจ้าของร้านเท่านั้น"""
    permissions.require(permissions.CATEGORY_MANAGE)
    if not repo_products.set_category_active(category_id, bool(active)):
        raise ValueError("ไม่พบหมวดหมู่")
    return dict(repo_products.get_category(category_id))


def delete_category(category_id: int, cascade: bool = False, force_deactivate_products: bool = False) -> dict:
    cascade = bool(cascade or force_deactivate_products)
    """
    ลบหมวดหมู่แบบ Soft Delete (OWN-3):
    ตรวจสินค้าที่อ้างอิงก่อน หากมีสินค้าอยู่และไม่ได้ยืนยัน cascade=True จะโยน ValueError แจ้งจำนวนสินค้า
    """
    permissions.require(permissions.CATEGORY_MANAGE)
    cat = repo_products.get_category(category_id)
    if cat is None:
        raise ValueError("ไม่พบหมวดหมู่")
    prod_count = repo_products.count_products_in_category(category_id)
    if prod_count > 0 and not cascade:
        raise ValueError(
            f"หมวดหมู่ “{cat['name']}” มีสินค้าใช้งานอยู่ {prod_count} รายการ "
            "กรุณาย้ายสินค้าออกก่อน หรือยืนยันการลบพร้อมย้ายสินค้าเข้าถังสินค้าที่ถูกลบ"
        )
    actor_id = Session.get_user_id()
    with transaction() as conn:
        if prod_count > 0 and cascade:
            for p in repo_products.list_products({"category_id": category_id, "active_only": False}, conn=conn):
                repo_products.soft_delete_product(p["id"], deleted_by=actor_id, conn=conn)
        repo_products.soft_delete_category(category_id, conn=conn)
        audit_service.log("category.delete", "category", category_id, {"name": cat["name"], "cascade": cascade}, conn=conn)
    return dict(repo_products.get_category(category_id))


def restore_category(category_id: int) -> dict:
    permissions.require(permissions.CATEGORY_MANAGE)
    cat = repo_products.get_category(category_id)
    if cat is None:
        raise ValueError("ไม่พบหมวดหมู่")
    with transaction() as conn:
        repo_products.restore_category(category_id, conn=conn)
        audit_service.log("category.restore", "category", category_id, {"name": cat["name"]}, conn=conn)
    return dict(repo_products.get_category(category_id))


def list_deleted_categories() -> list[dict]:
    permissions.require(permissions.CATEGORY_MANAGE)
    rows = repo_products.list_categories(active_only=False, include_deleted=True)
    return [dict(r) for r in rows if _field(r, "deleted_at") is not None]


def save_brand(name: str, brand_id: int = None, logo_path=None) -> dict:
    """เพิ่ม/แก้แบรนด์ — ชื่อซ้ำ -> ValueError"""
    permissions.require(permissions.BRAND_MANAGE)
    name = _clean_name(name, "แบรนด์")
    try:
        if brand_id is None:
            brand_id = repo_products.create_brand(name, logo_path)
        elif not repo_products.update_brand(brand_id, name, logo_path):
            raise ValueError("ไม่พบแบรนด์")
        audit_service.log("brand.save", "brand", brand_id, {"name": name})
    except sqlite3.IntegrityError:
        raise ValueError("มีแบรนด์ชื่อนี้อยู่แล้ว") from None
    return dict(repo_products.get_brand(brand_id))


def set_brand_active(brand_id: int, active: bool) -> dict:
    """เปิด/ปิดแบรนด์ — เจ้าของร้านเท่านั้น"""
    permissions.require(permissions.BRAND_MANAGE)
    if not repo_products.set_brand_active(brand_id, bool(active)):
        raise ValueError("ไม่พบแบรนด์")
    return dict(repo_products.get_brand(brand_id))


def delete_brand(brand_id: int, cascade: bool = False, force_deactivate_products: bool = False) -> dict:
    cascade = bool(cascade or force_deactivate_products)
    """
    ลบแบรนด์แบบ Soft Delete (OWN-3):
    ตรวจสินค้าที่อ้างอิงก่อน หากมีสินค้าอยู่และไม่ได้ยืนยัน cascade=True จะโยน ValueError แจ้งจำนวนสินค้า
    """
    permissions.require(permissions.BRAND_MANAGE)
    brand = repo_products.get_brand(brand_id)
    if brand is None:
        raise ValueError("ไม่พบแบรนด์")
    prod_count = repo_products.count_products_in_brand(brand_id)
    if prod_count > 0 and not cascade:
        raise ValueError(
            f"แบรนด์ “{brand['name']}” มีสินค้าใช้งานอยู่ {prod_count} รายการ "
            "กรุณาย้ายสินค้าออกก่อน หรือยืนยันการลบพร้อมย้ายสินค้าเข้าถังสินค้าที่ถูกลบ"
        )
    actor_id = Session.get_user_id()
    with transaction() as conn:
        if prod_count > 0 and cascade:
            for p in repo_products.list_products({"brand_id": brand_id, "active_only": False}, conn=conn):
                repo_products.soft_delete_product(p["id"], deleted_by=actor_id, conn=conn)
        repo_products.soft_delete_brand(brand_id, conn=conn)
        audit_service.log("brand.delete", "brand", brand_id, {"name": brand["name"], "cascade": cascade}, conn=conn)
    return dict(repo_products.get_brand(brand_id))


def restore_brand(brand_id: int) -> dict:
    permissions.require(permissions.BRAND_MANAGE)
    brand = repo_products.get_brand(brand_id)
    if brand is None:
        raise ValueError("ไม่พบแบรนด์")
    with transaction() as conn:
        repo_products.restore_brand(brand_id, conn=conn)
        audit_service.log("brand.restore", "brand", brand_id, {"name": brand["name"]}, conn=conn)
    return dict(repo_products.get_brand(brand_id))


def list_deleted_brands() -> list[dict]:
    permissions.require(permissions.BRAND_MANAGE)
    rows = repo_products.list_brands(active_only=False, include_deleted=True)
    return [dict(r) for r in rows if _field(r, "deleted_at") is not None]


_recent_views: dict[int, list[int]] = {}


def soft_delete_product(product_id: int) -> dict:
    return delete_product(product_id)


def list_recently_viewed(user_id: int = None, limit: int = 5) -> list[dict]:
    if not user_id:
        return []
    ids = _recent_views.get(int(user_id), [])[:limit]
    return get_cards_by_ids(ids, limit=limit, user_id=user_id) if ids else []


def record_recently_viewed(user_id: int, product_id: int) -> None:
    if not user_id or not product_id:
        return
    uid = int(user_id)
    pid = int(product_id)
    cur = [x for x in _recent_views.get(uid, []) if x != pid]
    cur.insert(0, pid)
    _recent_views[uid] = cur[:15]
