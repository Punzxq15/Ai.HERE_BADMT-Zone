"""
server/routes/products.py
API สำหรับสินค้า หมวดหมู่ แบรนด์ ตัวเลือกสินค้า ของแถม สเปกไม้แบด เปรียบเทียบไม้ และตัวช่วยเลือกไม้
(ทั้งฝั่งผู้ซื้อ/ผู้เยี่ยมชม และฝั่งแอดมิน/เจ้าของร้าน)
"""
from fastapi import APIRouter, Query

from core.session import Session
from server.serializers import to_jsonable
from services import (
    banner_service,
    contact_service,
    coupon_service,
    product_service,
    review_service,
    settings_service,
)

router = APIRouter(prefix="/api", tags=["products"])


def _parse_bool(val) -> bool | None:
    if val is None or val == "":
        return None
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def _parse_csv_or_list(val) -> list[str] | str | None:
    if val is None or val == "":
        return None
    if isinstance(val, (list, tuple)):
        items = [str(x).strip() for x in val if str(x).strip()]
        return items if len(items) > 1 else (items[0] if items else None)
    s = str(val).strip()
    if "," in s:
        items = [x.strip() for x in s.split(",") if x.strip()]
        return items if len(items) > 1 else (items[0] if items else None)
    return s


@router.get("/home")
def get_home_data():
    """ดึงข้อมูลครบชุดสำหรับหน้า Home ในคำขอเดียว (แบนเนอร์, Flash Sale, คูปอง, หมวดหมู่, แบรนด์, ขายดี, มาใหม่, ดูล่าสุด)"""
    uid = Session.get_user_id() if Session.get_role() == "buyer" else None
    shop = settings_service.get_shop_info()
    contact = contact_service.get_owner_contact_info()
    banners = banner_service.list_active_banners()
    categories = product_service.list_categories(include_inactive=False)
    brands = product_service.list_brands(include_inactive=False)
    flash_sale = product_service.search_products(
        filters={"on_sale": True, "in_stock": True}, sort="popular", page=1, page_size=12, user_id=uid
    )["items"]
    best_sellers = product_service.search_products(
        filters={}, sort="popular", page=1, page_size=15, user_id=uid
    )["items"]
    newest = product_service.search_products(
        filters={}, sort="newest", page=1, page_size=15, user_id=uid
    )["items"]
    recently_viewed = product_service.list_recently_viewed(uid, limit=5) if uid else []
    public_coupons = coupon_service.list_public_coupons(user_id=uid)
    coupon_rules = coupon_service.list_coupon_rules(active_only=True)
    coupon_categories = [
        {"key": k, "label": lbl} for k, lbl in coupon_service.get_coupon_categories()
    ]
    return to_jsonable({
        "shop": shop,
        "contact": contact,
        "banners": banners,
        "categories": categories,
        "brands": brands,
        "flash_sale": flash_sale,
        "best_sellers": best_sellers,
        "newest": newest,
        "recently_viewed": recently_viewed,
        "public_coupons": public_coupons,
        "coupon_rules": coupon_rules,
        "coupon_categories": coupon_categories,
    })


@router.get("/products")
def search_products(
    query: str | None = None,
    q: str | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    weight_class: str | None = None,
    balance: str | None = None,
    flex: str | None = None,
    level: str | None = None,
    min_price: str | None = None,
    max_price: str | None = None,
    on_sale: str | None = None,
    in_stock: str | None = None,
    sort: str = "newest",
    page: int = 1,
    page_size: int = 12,
):
    filters = {}
    if category_id is not None:
        filters["category_id"] = category_id
    if brand_id is not None:
        filters["brand_id"] = brand_id
    for key, raw_val in (
        ("weight_class", weight_class),
        ("balance", balance),
        ("flex", flex),
        ("level", level),
    ):
        parsed = _parse_csv_or_list(raw_val)
        if parsed is not None:
            filters[key] = parsed
    if min_price not in (None, ""):
        filters["min_price"] = min_price
    if max_price not in (None, ""):
        filters["max_price"] = max_price
    if _parse_bool(on_sale):
        filters["on_sale"] = True
    if _parse_bool(in_stock):
        filters["in_stock"] = True

    uid = Session.get_user_id() if Session.get_role() == "buyer" else None
    res = product_service.search_products(
        query=query if query is not None else q,
        filters=filters,
        sort=sort,
        page=page,
        page_size=page_size,
        user_id=uid,
    )
    return to_jsonable(res)


@router.get("/products/filters")
def get_filter_values():
    return to_jsonable(product_service.list_filter_values())


@router.get("/products/suggest")
def suggest_products(q: str = "", limit: int = 8):
    return to_jsonable(product_service.suggest_products(q, limit=limit))


@router.get("/products/showcase")
def get_login_showcase(limit: int = 50):
    return to_jsonable({
        "items": product_service.get_login_showcase(limit=limit),
        "rotate_seconds": settings_service.get_int("login_showcase_seconds", 5),
    })


@router.get("/products/best-sellers")
def get_best_sellers(limit: int = 8, rackets_only: bool = False):
    return to_jsonable(product_service.get_best_sellers(limit=limit, rackets_only=rackets_only))


@router.get("/products/recently-viewed")
def get_recently_viewed(ids: str | None = None, limit: int = 5):
    uid = Session.get_user_id() if Session.get_role() == "buyer" else None
    if ids:
        id_list = [x.strip() for x in ids.split(",") if x.strip()]
        return to_jsonable(product_service.get_cards_by_ids(id_list, limit=limit, user_id=uid))
    if uid:
        return to_jsonable(product_service.list_recently_viewed(uid, limit=limit))
    return []


@router.get("/products/compare")
def compare_products(ids: str = Query("")):
    raw_ids = [x.strip() for x in (ids or "").split(",") if x.strip()]
    return to_jsonable(product_service.compare_products(raw_ids))


@router.get("/products/recommend")
def recommend_rackets(
    level: str = "",
    style: str = "",
    budget: str | None = None,
    limit: int = 6,
    flex: str | None = None,
    balance: str | None = None,
    weight_class: str | None = None,
):
    items = product_service.recommend_rackets(
        level=level,
        style=style,
        budget=budget if budget not in (None, "") else None,
        limit=limit,
        flex=flex or None,
        balance=balance or None,
        weight_class=weight_class or None,
    )
    return to_jsonable(items)


@router.get("/products/{product_id}")
def get_product_detail(product_id: int):
    uid = Session.get_user_id() if Session.get_role() == "buyer" else None
    detail = product_service.get_product_detail(product_id, user_id=uid)
    if uid:
        try:
            detail["reviewable_order_id"] = review_service.find_reviewable_order(uid, product_id)
        except Exception:
            detail["reviewable_order_id"] = None
    else:
        detail["reviewable_order_id"] = None
    return to_jsonable(detail)


@router.get("/products/{product_id}/reviews")
def list_product_reviews(product_id: int, page: int = 1, page_size: int = 10):
    return to_jsonable(review_service.list_reviews(product_id, page=page, page_size=page_size))


@router.get("/categories")
def list_public_categories():
    return to_jsonable(product_service.list_categories(include_inactive=False))


@router.get("/brands")
def list_public_brands(category_id: int | None = None):
    return to_jsonable(product_service.list_brands(include_inactive=False, category_id=category_id))


@router.get("/categories/{category_id}/option-groups")
def list_public_category_option_groups(category_id: int):
    return to_jsonable(product_service.list_category_option_groups(category_id, include_inactive=False))


# ==========================================
# ฝั่งแอดมิน / เจ้าของร้าน (Admin Products, Categories, Brands, Options)
# ==========================================

@router.get("/admin/products")
def admin_list_products(
    search: str | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    on_sale: str | None = None,
    in_stock: str | None = None,
    sort: str = "newest",
    page: int = 1,
    page_size: int = 20,
    show_inactive: bool = True,
):
    filters = {}
    if category_id is not None:
        filters["category_id"] = category_id
    if brand_id is not None:
        filters["brand_id"] = brand_id
    if _parse_bool(on_sale):
        filters["on_sale"] = True
    if _parse_bool(in_stock):
        filters["in_stock"] = True
    res = product_service.list_products_admin(
        search=search,
        filters=filters,
        sort=sort,
        page=page,
        page_size=page_size,
        show_inactive=show_inactive,
    )
    res["low_stock_threshold"] = settings_service.get_int("low_stock_threshold", 5)
    return to_jsonable(res)


@router.get("/admin/products/deleted")
def admin_list_deleted_products(search: str | None = None):
    return to_jsonable(product_service.list_deleted_products(search=search))


@router.get("/admin/products/low-stock")
def admin_low_stock_products():
    return to_jsonable(product_service.get_low_stock_products())


@router.get("/admin/products/form-meta")
def admin_product_form_meta(category_id: int | None = None, product_id: int | None = None):
    current = product_service.get_product_for_edit(product_id) if product_id else None
    cat_id = category_id or (current["category_id"] if current else None)
    categories = product_service.list_categories(include_inactive=True)
    brands = product_service.list_brands(include_inactive=True, category_id=cat_id)
    all_brands = product_service.list_brands(include_inactive=True)
    option_types = list(product_service.get_allowed_option_types())
    racket_specs = product_service.get_allowed_racket_spec_options(
        category_id=cat_id, current_product=current
    )
    option_groups = product_service.list_category_option_groups(
        category_id=cat_id, include_inactive=False
    ) if cat_id else []
    all_products = product_service.list_products_admin(page=1, page_size=60, show_inactive=False)["items"]
    return to_jsonable({
        "product": current,
        "categories": categories,
        "brands": brands,
        "all_brands": all_brands,
        "allowed_option_types": option_types,
        "allowed_racket_specs": racket_specs,
        "option_groups": option_groups,
        "all_products": all_products,
    })


@router.get("/admin/products/{product_id}/edit")
def admin_get_product_for_edit(product_id: int):
    return to_jsonable(product_service.get_product_for_edit(product_id))


@router.post("/admin/products")
def admin_create_product(payload: dict):
    return to_jsonable(product_service.save_product(payload, product_id=None))


@router.put("/admin/products/{product_id}")
def admin_update_product(product_id: int, payload: dict):
    return to_jsonable(product_service.save_product(payload, product_id=product_id))


@router.post("/admin/products/{product_id}/active")
def admin_set_product_active(product_id: int, payload: dict):
    return to_jsonable(product_service.set_product_active(product_id, bool(payload.get("active", True))))


@router.delete("/admin/products/{product_id}")
def admin_delete_product(product_id: int):
    return to_jsonable(product_service.soft_delete_product(product_id))


@router.post("/admin/products/{product_id}/restore")
def admin_restore_product(product_id: int):
    return to_jsonable(product_service.restore_product(product_id, activate=True))


@router.post("/admin/products/{product_id}/stock")
def admin_adjust_stock(product_id: int, payload: dict):
    delta = int(payload.get("delta", 0))
    option_id = payload.get("option_id")
    if option_id is not None and option_id != "":
        option_id = int(option_id)
    else:
        option_id = None
    return to_jsonable(product_service.adjust_stock(product_id, delta, option_id=option_id))


@router.post("/admin/products/{product_id}/options")
def admin_save_option(product_id: int, payload: dict):
    opt_id = payload.get("option_id") or payload.get("id")
    return to_jsonable(
        product_service.save_option(
            product_id=product_id,
            option_type=payload.get("option_type") or "",
            option_value=payload.get("option_value") or "",
            extra_price=payload.get("extra_price", 0),
            stock=payload.get("stock", 0),
            option_id=int(opt_id) if opt_id else None,
            image_path=payload.get("image_path"),
        )
    )


@router.put("/admin/products/{product_id}/options/{option_id}")
def admin_update_option(product_id: int, option_id: int, payload: dict):
    return to_jsonable(
        product_service.save_option(
            product_id=product_id,
            option_type=payload.get("option_type") or "",
            option_value=payload.get("option_value") or "",
            extra_price=payload.get("extra_price", 0),
            stock=payload.get("stock", 0),
            option_id=option_id,
            image_path=payload.get("image_path"),
        )
    )


@router.delete("/admin/options/{option_id}")
def admin_delete_option(option_id: int):
    return to_jsonable(product_service.delete_option(option_id))


@router.post("/admin/products/{product_id}/images")
def admin_add_product_image(product_id: int, payload: dict):
    return to_jsonable(
        product_service.add_product_image(
            product_id=product_id,
            path=payload.get("path") or payload.get("image_path") or "",
            color_value=payload.get("color_value") or None,
            option_value_id=payload.get("option_value_id"),
            sort_order=payload.get("sort_order"),
            is_primary=bool(payload.get("is_primary", False)),
        )
    )


@router.put("/admin/product-images/{image_id}")
def admin_update_product_image(image_id: int, payload: dict):
    return to_jsonable(
        product_service.update_product_image(
            image_id=image_id,
            color_value=payload.get("color_value", "__keep__"),
            option_value_id=payload.get("option_value_id"),
            sort_order=payload.get("sort_order"),
        )
    )


@router.put("/admin/product-images/{image_id}/primary")
def admin_set_primary_image_by_id(image_id: int):
    return to_jsonable(product_service.set_primary_product_image(image_id))


@router.put("/admin/products/{product_id}/images/{image_id}/primary")
def admin_set_primary_image(product_id: int, image_id: int):
    return to_jsonable(product_service.set_primary_product_image(product_id, image_id))


@router.post("/admin/products/{product_id}/images/reorder")
def admin_reorder_product_images(product_id: int, payload: dict):
    ids = [int(x) for x in (payload.get("image_ids") or [])]
    return to_jsonable(product_service.reorder_product_images(product_id, ids))


@router.delete("/admin/product-images/{image_id}")
def admin_delete_product_image(image_id: int):
    return to_jsonable(product_service.delete_product_image(image_id))


@router.put("/admin/products/{product_id}/addons")
def admin_set_addons(product_id: int, payload: dict):
    addon_ids = payload.get("addon_ids") or []
    return to_jsonable(product_service.set_addons(product_id, addon_ids))


# ==========================================
# หมวดหมู่ แบรนด์ และชุดตัวเลือกหมวดหมู่ (Categories, Brands, Option Groups)
# ==========================================

@router.get("/admin/categories")
def admin_list_categories_and_brands():
    categories = product_service.list_categories(include_inactive=True)
    brands = product_service.list_brands(include_inactive=True)
    deleted_categories = []
    deleted_brands = []
    try:
        deleted_categories = product_service.list_deleted_categories()
        deleted_brands = product_service.list_deleted_brands()
    except PermissionError:
        pass
    option_groups = product_service.list_category_option_groups(include_inactive=True)
    return to_jsonable({
        "categories": categories,
        "deleted_categories": deleted_categories,
        "brands": brands,
        "deleted_brands": deleted_brands,
        "option_groups": option_groups,
    })


@router.post("/admin/categories")
def admin_create_category(payload: dict):
    return to_jsonable(
        product_service.save_category(
            name=payload.get("name") or "",
            category_id=None,
            image_path=payload.get("image_path"),
            brand_ids=payload.get("brand_ids"),
            all_brands=payload.get("all_brands"),
            bind_all_brands=payload.get("bind_all_brands"),
        )
    )


@router.put("/admin/categories/{category_id}")
def admin_update_category(category_id: int, payload: dict):
    return to_jsonable(
        product_service.save_category(
            name=payload.get("name") or "",
            category_id=category_id,
            image_path=payload.get("image_path"),
            brand_ids=payload.get("brand_ids"),
            all_brands=payload.get("all_brands"),
            bind_all_brands=payload.get("bind_all_brands"),
        )
    )


@router.post("/admin/categories/{category_id}/active")
def admin_set_category_active(category_id: int, payload: dict):
    return to_jsonable(product_service.set_category_active(category_id, bool(payload.get("active", True))))


@router.delete("/admin/categories/{category_id}")
def admin_delete_category(category_id: int, cascade: bool = False):
    return to_jsonable(product_service.delete_category(category_id, cascade=cascade))


@router.post("/admin/categories/{category_id}/restore")
def admin_restore_category(category_id: int):
    return to_jsonable(product_service.restore_category(category_id))


@router.post("/admin/brands")
def admin_create_brand(payload: dict):
    return to_jsonable(
        product_service.save_brand(
            name=payload.get("name") or "",
            brand_id=None,
            logo_path=payload.get("logo_path"),
        )
    )


@router.put("/admin/brands/{brand_id}")
def admin_update_brand(brand_id: int, payload: dict):
    return to_jsonable(
        product_service.save_brand(
            name=payload.get("name") or "",
            brand_id=brand_id,
            logo_path=payload.get("logo_path"),
        )
    )


@router.post("/admin/brands/{brand_id}/active")
def admin_set_brand_active(brand_id: int, payload: dict):
    return to_jsonable(product_service.set_brand_active(brand_id, bool(payload.get("active", True))))


@router.delete("/admin/brands/{brand_id}")
def admin_delete_brand(brand_id: int, cascade: bool = False):
    return to_jsonable(product_service.delete_brand(brand_id, cascade=cascade))


@router.post("/admin/brands/{brand_id}/restore")
def admin_restore_brand(brand_id: int):
    return to_jsonable(product_service.restore_brand(brand_id))


@router.get("/admin/option-groups")
def admin_list_option_groups(category_id: int | None = None):
    return to_jsonable(product_service.list_category_option_groups(category_id=category_id, include_inactive=True))


@router.post("/admin/option-groups")
def admin_save_option_group(payload: dict):
    return to_jsonable(
        product_service.save_category_option_group(
            category_id=int(payload.get("category_id")),
            key=payload.get("key") or "",
            label=payload.get("label") or "",
            sort_order=int(payload.get("sort_order", 0)),
            is_active=bool(payload.get("is_active", True)),
            group_id=payload.get("group_id") or payload.get("id"),
        )
    )


@router.put("/admin/option-groups/{group_id}")
def admin_update_option_group(group_id: int, payload: dict):
    return to_jsonable(
        product_service.save_category_option_group(
            category_id=int(payload.get("category_id")),
            key=payload.get("key") or "",
            label=payload.get("label") or "",
            sort_order=int(payload.get("sort_order", 0)),
            is_active=bool(payload.get("is_active", True)),
            group_id=group_id,
        )
    )


@router.post("/admin/option-groups/{group_id}/toggle")
def admin_toggle_option_group(group_id: int, payload: dict | None = None):
    active = payload.get("active") if isinstance(payload, dict) and "active" in payload else None
    return to_jsonable(product_service.toggle_category_option_group(group_id, active=active))


@router.post("/admin/option-values")
def admin_save_option_value(payload: dict):
    return to_jsonable(
        product_service.save_category_option_value(
            group_id=int(payload.get("group_id")),
            value=payload.get("value") or "",
            label=payload.get("label"),
            sort_order=payload.get("sort_order"),
            is_active=bool(payload.get("is_active", True)),
            value_id=payload.get("value_id") or payload.get("id"),
        )
    )


@router.put("/admin/option-values/{value_id}")
def admin_update_option_value(value_id: int, payload: dict):
    return to_jsonable(
        product_service.save_category_option_value(
            group_id=int(payload.get("group_id")),
            value=payload.get("value") or "",
            label=payload.get("label"),
            sort_order=payload.get("sort_order"),
            is_active=bool(payload.get("is_active", True)),
            value_id=value_id,
        )
    )


@router.post("/admin/option-values/{value_id}/toggle")
def admin_toggle_option_value(value_id: int, payload: dict | None = None):
    active = payload.get("active") if isinstance(payload, dict) and "active" in payload else None
    return to_jsonable(product_service.toggle_category_option_value(value_id, active=active))


@router.post("/admin/option-groups/{group_id}/reorder")
def admin_reorder_option_values(group_id: int, payload: dict):
    value_ids = [int(x) for x in (payload.get("value_ids") or [])]
    return to_jsonable(product_service.reorder_category_option_values(group_id, value_ids))


@router.post("/admin/categories/{category_id}/quick-weights")
def admin_quick_add_weights(category_id: int, payload: dict | None = None):
    weights = payload.get("weights") if isinstance(payload, dict) else None
    return to_jsonable(product_service.quick_add_racket_weights(category_id, weights=weights))
