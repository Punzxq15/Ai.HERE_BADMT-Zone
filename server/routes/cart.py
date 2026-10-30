"""
server/routes/cart.py
API สำหรับตะกร้าสินค้าของผู้ซื้อ: ดูตะกร้า เพิ่มสินค้า เพิ่มพร้อมสินค้าเสริม ปรับจำนวน เลือกรายการ และลบรายการ
"""
from fastapi import APIRouter

from server import deps
from server.serializers import to_jsonable
from services import cart_service, settings_service

router = APIRouter(prefix="/api", tags=["cart"])


def _enrich_cart(uid: int) -> dict:
    cart = cart_service.get_cart(uid)
    sel_sub = float(cart.get("selected_subtotal") or 0.0)
    cart["shipping_fee"] = settings_service.shipping_fee_for(sel_sub) if sel_sub > 0 else 0.0
    cart["free_shipping_min"] = settings_service.get_float("free_shipping_min", 0.0)
    cart["base_shipping_fee"] = settings_service.get_float("shipping_fee", 50.0)
    return cart


@router.get("/cart")
def get_cart():
    uid = deps.require_user_id()
    return to_jsonable(_enrich_cart(uid))


@router.post("/cart/items")
def add_to_cart(payload: dict):
    uid = deps.require_user_id()
    product_id = int(payload.get("product_id"))
    option_id = payload.get("option_id")
    if option_id is not None and option_id != "":
        option_id = int(option_id)
    else:
        option_id = None
    qty = int(payload.get("qty", 1))
    res = cart_service.add_to_cart(uid, product_id, option_id=option_id, qty=qty)
    return to_jsonable({**res, "cart": _enrich_cart(uid)})


@router.post("/cart/items-with-addons")
def add_with_addons(payload: dict):
    uid = deps.require_user_id()
    product_id = int(payload.get("product_id"))
    addon_ids = [int(x) for x in (payload.get("addon_ids") or [])]
    option_id = payload.get("option_id")
    if option_id is not None and option_id != "":
        option_id = int(option_id)
    else:
        option_id = None
    qty = int(payload.get("qty", 1))
    raw_addon_opts = payload.get("addon_options") or {}
    addon_options = {
        int(k): (int(v) if v not in (None, "") else None)
        for k, v in raw_addon_opts.items()
    }
    res = cart_service.add_with_addons(
        user_id=uid,
        product_id=product_id,
        addon_ids=addon_ids,
        option_id=option_id,
        qty=qty,
        addon_options=addon_options,
    )
    return to_jsonable({**res, "cart": _enrich_cart(uid)})


@router.patch("/cart/items/{cart_item_id}")
def update_cart_item(cart_item_id: int, payload: dict):
    uid = deps.require_user_id()
    if "qty" in payload and payload["qty"] is not None:
        cart_service.update_qty(uid, cart_item_id, int(payload["qty"]))
    if "selected" in payload and payload["selected"] is not None:
        cart_service.set_item_selected(uid, cart_item_id, bool(payload["selected"]))
    return to_jsonable(_enrich_cart(uid))


@router.post("/cart/select-all")
def select_all_cart_items(payload: dict):
    uid = deps.require_user_id()
    cart_service.set_all_selected(uid, bool(payload.get("selected", True)))
    return to_jsonable(_enrich_cart(uid))


@router.delete("/cart/selected")
def remove_selected_cart_items():
    uid = deps.require_user_id()
    cart_service.remove_selected_items(uid)
    return to_jsonable(_enrich_cart(uid))


@router.delete("/cart/items/{cart_item_id}")
def remove_cart_item(cart_item_id: int):
    uid = deps.require_user_id()
    cart_service.remove_item(uid, cart_item_id)
    return to_jsonable(_enrich_cart(uid))


@router.delete("/cart")
def clear_cart():
    uid = deps.require_user_id()
    cart_service.clear_cart(uid)
    return to_jsonable(_enrich_cart(uid))
