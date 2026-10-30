"""
server/routes/coupons_settings.py
API สำหรับคูปองส่วนลด กฎซื้อครบรับคูปอง แบนเนอร์ แบนเนอร์หน้า Login/Sign Up การตั้งค่าร้าน และข้อมูลติดต่อเจ้าของร้าน
"""
from fastapi import APIRouter

from core.session import Session
from server import deps
from server.serializers import to_jsonable
from services import banner_service, contact_service, coupon_service, settings_service

router = APIRouter(prefix="/api", tags=["coupons_settings"])


# ==========================================
# คูปองฝั่งผู้ซื้อ / สาธารณะ
# ==========================================

@router.get("/coupons/categories")
def get_coupon_categories():
    return to_jsonable([
        {"key": k, "label": lbl} for k, lbl in coupon_service.get_coupon_categories()
    ])


@router.get("/coupons/public")
def list_public_coupons(category: str | None = None):
    uid = Session.get_user_id() if Session.get_role() == "buyer" else None
    return to_jsonable(coupon_service.list_public_coupons(user_id=uid, category=category))


@router.get("/coupons/shop")
def list_all_shop_coupons(category: str | None = None, include_expired: bool = False):
    uid = Session.get_user_id() if Session.get_role() == "buyer" else None
    return to_jsonable(
        coupon_service.list_all_shop_coupons(
            user_id=uid, category=category, include_expired=include_expired
        )
    )


@router.get("/coupons/my")
def list_my_coupons(category: str | None = None):
    uid = deps.require_user_id()
    return to_jsonable(coupon_service.list_my_coupons(uid, category=category))


@router.get("/coupons/rules")
def list_public_coupon_rules():
    return to_jsonable(coupon_service.list_coupon_rules(active_only=True))


@router.post("/coupons/claim")
def claim_coupon(payload: dict):
    uid = deps.require_user_id()
    if payload.get("coupon_id") is not None and payload.get("coupon_id") != "":
        res = coupon_service.claim_coupon(uid, int(payload["coupon_id"]))
    else:
        code = str(payload.get("code") or "").strip()
        if not code:
            raise ValueError("กรุณาระบุโค้ดคูปอง")
        res = coupon_service.claim_coupon(code, uid)
    return to_jsonable(res)


@router.post("/coupons/validate")
def validate_coupon(payload: dict):
    uid = deps.require_user_id()
    code = payload.get("code") or ""
    subtotal = float(payload.get("subtotal") or 0.0)
    shipping_fee = payload.get("shipping_fee")
    if shipping_fee is not None:
        shipping_fee = float(shipping_fee)
    return to_jsonable(
        coupon_service.validate_coupon(code, uid, subtotal, shipping_fee=shipping_fee)
    )


# ==========================================
# คูปองและกฎคูปองฝั่งเจ้าของร้าน (Admin Coupons)
# ==========================================

@router.get("/admin/coupons")
def admin_list_coupons():
    return to_jsonable({
        "coupons": coupon_service.list_coupons(),
        "rules": coupon_service.list_coupon_rules(active_only=False),
        "categories": [{"key": k, "label": lbl} for k, lbl in coupon_service.get_coupon_categories()],
    })


@router.get("/admin/coupons/{coupon_id}")
def admin_get_coupon(coupon_id: int):
    return to_jsonable(coupon_service.get_coupon(coupon_id))


@router.post("/admin/coupons")
def admin_create_coupon(payload: dict):
    return to_jsonable(
        coupon_service.create_coupon(
            code=payload.get("code") or "",
            discount_type=payload.get("discount_type") or "percent",
            value=payload.get("value", 0),
            min_order=payload.get("min_order", 0),
            max_uses=payload.get("max_uses"),
            expires_at=payload.get("expires_at"),
            is_active=bool(payload.get("is_active", True)),
            claimable=bool(payload.get("claimable", True)),
            max_discount=payload.get("max_discount"),
            starts_at=payload.get("starts_at"),
            is_free_shipping=bool(payload.get("is_free_shipping", False)),
            daily_reset_12=bool(payload.get("daily_reset_12", False)),
            code_prefix=payload.get("code_prefix"),
            claim_start_time=payload.get("claim_start_time"),
            claim_end_time=payload.get("claim_end_time"),
            repeat_daily=bool(payload.get("repeat_daily", False)),
            coupon_category=payload.get("coupon_category"),
        )
    )


@router.put("/admin/coupons/{coupon_id}")
def admin_update_coupon(coupon_id: int, payload: dict):
    return to_jsonable(coupon_service.update_coupon(coupon_id, payload))


@router.post("/admin/coupons/{coupon_id}/toggle")
def admin_toggle_coupon(coupon_id: int, payload: dict | None = None):
    active = payload.get("active") if isinstance(payload, dict) and "active" in payload else None
    return to_jsonable(coupon_service.toggle_coupon(coupon_id, active=active))


@router.delete("/admin/coupons/{coupon_id}")
def admin_delete_coupon(coupon_id: int):
    ok = coupon_service.delete_coupon(coupon_id)
    return {"ok": bool(ok)}


@router.get("/admin/coupon-rules")
def admin_list_coupon_rules():
    return to_jsonable(coupon_service.list_coupon_rules(active_only=False))


@router.post("/admin/coupon-rules")
def admin_save_coupon_rule(payload: dict):
    rule_id = payload.get("rule_id") or payload.get("id")
    return to_jsonable(coupon_service.save_coupon_rule(payload, rule_id=int(rule_id) if rule_id else None))


@router.put("/admin/coupon-rules/{rule_id}")
def admin_update_coupon_rule(rule_id: int, payload: dict):
    return to_jsonable(coupon_service.save_coupon_rule(payload, rule_id=rule_id))


@router.post("/admin/coupon-rules/{rule_id}/toggle")
def admin_toggle_coupon_rule(rule_id: int, payload: dict | None = None):
    active = payload.get("active") if isinstance(payload, dict) and "active" in payload else None
    return to_jsonable(coupon_service.toggle_rule(rule_id, active=active))


@router.delete("/admin/coupon-rules/{rule_id}")
def admin_delete_coupon_rule(rule_id: int):
    ok = coupon_service.delete_coupon_rule(rule_id)
    return {"ok": bool(ok)}


# ==========================================
# แบนเนอร์หน้าแรก แบนเนอร์หน้า Login/Sign Up การตั้งค่าร้าน และข้อมูลติดต่อ
# ==========================================

@router.get("/banners")
def list_active_banners():
    return to_jsonable(banner_service.list_active_banners())


@router.get("/admin/banners")
def admin_list_banners():
    return to_jsonable(banner_service.list_all_banners())


@router.post("/admin/banners")
def admin_create_banner(payload: dict):
    bid = payload.get("banner_id") or payload.get("id")
    return to_jsonable(banner_service.save_banner(payload, banner_id=int(bid) if bid else None))


@router.put("/admin/banners/{banner_id}")
def admin_update_banner(banner_id: int, payload: dict):
    return to_jsonable(banner_service.save_banner(payload, banner_id=banner_id))


@router.post("/admin/banners/{banner_id}/active")
def admin_set_banner_active(banner_id: int, payload: dict):
    return to_jsonable(banner_service.set_banner_active(banner_id, bool(payload.get("active", True))))


@router.post("/admin/banners/reorder")
def admin_reorder_banners(payload: dict):
    return to_jsonable(banner_service.reorder_banners(payload.get("ordered_ids") or []))


@router.delete("/admin/banners/{banner_id}")
def admin_delete_banner(banner_id: int):
    ok = banner_service.delete_banner(banner_id)
    return {"ok": bool(ok)}


# ---------- แบนเนอร์หน้า Login & Sign Up (Owner เท่านั้น, สูงสุด 7 รูป) ----------

@router.get("/login-banners")
def list_public_login_banners():
    items = banner_service.list_login_banners()
    return to_jsonable({
        "items": items,
        "count": len(items),
        "max_items": banner_service.MAX_LOGIN_BANNERS,
    })


@router.get("/admin/login-banners")
def admin_list_login_banners():
    deps.require_roles("owner")
    items = banner_service.list_login_banners()
    return to_jsonable({
        "items": items,
        "count": len(items),
        "max_items": banner_service.MAX_LOGIN_BANNERS,
    })


@router.post("/admin/login-banners")
def admin_add_login_banners(payload: dict):
    deps.require_roles("owner")
    paths = payload.get("file_paths")
    if not paths:
        single = payload.get("file_path") or payload.get("image_path") or ""
        paths = [single] if single else []
    items = banner_service.add_login_banners(paths)
    return to_jsonable({
        "items": items,
        "count": len(items),
        "max_items": banner_service.MAX_LOGIN_BANNERS,
    })


@router.post("/admin/login-banners/reorder")
def admin_reorder_login_banners(payload: dict):
    deps.require_roles("owner")
    items = banner_service.reorder_login_banners(payload.get("ordered_ids") or [])
    return to_jsonable({
        "items": items,
        "count": len(items),
        "max_items": banner_service.MAX_LOGIN_BANNERS,
    })


@router.delete("/admin/login-banners/{banner_id}")
def admin_delete_login_banner(banner_id: int):
    deps.require_roles("owner")
    items = banner_service.delete_login_banner(banner_id)
    return to_jsonable({
        "ok": True,
        "items": items,
        "count": len(items),
        "max_items": banner_service.MAX_LOGIN_BANNERS,
    })


@router.get("/settings/shop")
def get_shop_settings():
    info = settings_service.get_shop_info()
    info["login_banners"] = banner_service.list_login_banners()
    return to_jsonable(info)


@router.get("/settings/contact")
def get_contact_settings():
    return to_jsonable(contact_service.get_owner_contact_info())


@router.post("/contact/urgent-email")
def send_urgent_email_to_owner(payload: dict):
    res = contact_service.send_urgent_email_to_owner(
        subject=payload.get("subject") or "",
        message=payload.get("message") or payload.get("body") or "",
    )
    return to_jsonable(res)


@router.get("/admin/settings")
def admin_get_all_settings():
    deps.require_roles("owner")
    return to_jsonable({
        "all": settings_service.get_all(),
        "shop": settings_service.get_shop_info(),
        "contact": contact_service.get_owner_contact_info(),
        "login_banners": banner_service.list_login_banners(),
    })


@router.put("/admin/settings")
def admin_update_settings(payload: dict):
    updated_shop = settings_service.update_many(payload)
    return to_jsonable({
        "shop": updated_shop,
        "all": settings_service.get_all(),
        "contact": contact_service.get_owner_contact_info(),
        "login_banners": banner_service.list_login_banners(),
    })


@router.post("/admin/settings/logo")
def admin_set_store_logo(payload: dict):
    deps.require_roles("owner")
    logo_path = str(payload.get("store_logo_path") or payload.get("shop_logo_path") or payload.get("path") or "").strip()
    updated_shop = settings_service.update_many({"store_logo_path": logo_path})
    return to_jsonable({
        "ok": True,
        "store_logo_path": updated_shop.get("store_logo_path") or "",
        "shop": updated_shop,
    })


@router.delete("/admin/settings/logo")
def admin_delete_store_logo():
    deps.require_roles("owner")
    updated_shop = settings_service.update_many({"store_logo_path": ""})
    return to_jsonable({
        "ok": True,
        "store_logo_path": "",
        "shop": updated_shop,
    })


@router.put("/admin/settings/contact")
def admin_update_contact_settings(payload: dict):
    updated_contact = contact_service.update_owner_contact_info(payload)
    return to_jsonable({
        "contact": updated_contact,
        "shop": settings_service.get_shop_info(),
        "all": settings_service.get_all(),
    })
