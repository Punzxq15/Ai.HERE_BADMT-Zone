"""
services/order_service.py
หัวใจของระบบสั่งซื้อ: สร้างออเดอร์ (checkout), ยกเลิก (คืนสต็อก+คูปอง), ยืนยันรับสินค้า (+ออกคูปองรางวัลครั้งถัดไป),
ดู/ค้นหาออเดอร์, ยกเลิกอัตโนมัติเมื่อไม่จ่ายเงิน, ไทม์ไลน์สถานะ, นับจำนวนตามลำดับ 8 แท็บใน PDF และตัวเลขสำหรับ Dashboard

กติกาสถานะ (ตามตารางใน PROGRESS.md):
    pending -> checking_slip -> paid -> shipped -> completed        (และ -> cancelled ก่อน shipped)
    checking_slip -> pending เมื่อแอดมินปฏิเสธสลิป
ทุกการเปลี่ยนสถานะต้องผ่าน apply_status_change() เพื่อ: ตรวจลำดับ, กันกดซ้ำ (expected_status), เขียน order_status_log
"""
import sqlite3
from datetime import date, datetime, timedelta

from core import permissions
from core.constants import (
    ORDER_STATUS_CANCELLED, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_COMPLETED, ORDER_STATUS_DISPLAY_ORDER,
    ORDER_STATUS_LABELS, ORDER_STATUS_PAID, ORDER_STATUS_PENDING, ORDER_STATUS_SHIPPED, ORDER_STATUSES,
    PAYMENT_STATUS_LABELS, PAYMENT_STATUS_PENDING, SHIPMENT_STATUS_DELIVERED, SHIPMENT_STATUS_LABELS,
)
from core.session import Session
from database import (
    repo_addresses, repo_cart, repo_coupons, repo_orders, repo_payments, repo_products,
    repo_reviews, repo_shipping,
)
from database.db import transaction
from services import audit_service, cart_service, coupon_service, notification_service, settings_service
from utils.formatters import format_price, parse_datetime

CANCEL_REASON_MAX = 300
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
VAT_RATE_PERCENT = 7.0

ALLOWED_TRANSITIONS = {
    ORDER_STATUS_PENDING: (ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_CANCELLED),
    ORDER_STATUS_CHECKING_SLIP: (ORDER_STATUS_PAID, ORDER_STATUS_PENDING, ORDER_STATUS_CANCELLED),
    ORDER_STATUS_PAID: (ORDER_STATUS_SHIPPED, ORDER_STATUS_CANCELLED),
    ORDER_STATUS_SHIPPED: (ORDER_STATUS_COMPLETED,),
    ORDER_STATUS_COMPLETED: (),
    ORDER_STATUS_CANCELLED: (),
}

BUYER_CANCELLABLE = (ORDER_STATUS_PENDING,)
STAFF_CANCELLABLE = (ORDER_STATUS_PENDING, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_PAID)


def _label(status) -> str:
    return ORDER_STATUS_LABELS.get(status, str(status))


def compute_vat_breakdown(total_amount: float) -> dict:
    """คำนวณมูลค่าก่อนภาษีและ VAT 7% จากยอดสุทธิ (Inclusive VAT 7%)"""
    tot = round(max(float(total_amount or 0), 0.0), 2)
    pre_vat = round(tot / (1.0 + VAT_RATE_PERCENT / 100.0), 2)
    vat_amt = round(tot - pre_vat, 2)
    return {
        "vat_rate": VAT_RATE_PERCENT,
        "pre_vat_amount": pre_vat,
        "vat_amount": vat_amt,
    }


# ==========================================
# ตัวช่วยภายใน (ใช้ร่วมกับ payment/shipping/receipt service)
# ==========================================

def apply_status_change(conn, order_id: int, from_status: str, to_status: str,
                        note=None, changed_by=None) -> None:
    if to_status not in ALLOWED_TRANSITIONS.get(from_status, ()):
        raise ValueError(f"เปลี่ยนสถานะจาก \"{_label(from_status)}\" เป็น \"{_label(to_status)}\" ไม่ได้")
    if not repo_orders.update_status(order_id, to_status, expected_status=from_status, conn=conn):
        raise ValueError("สถานะคำสั่งซื้อถูกเปลี่ยนไปแล้ว กรุณารีเฟรชหน้าจอ")
    repo_orders.add_status_log(order_id, to_status, note, changed_by, conn=conn)


def _get_order_or_raise(order_id, conn=None):
    order = repo_orders.get_order(order_id, conn=conn)
    if order is None:
        raise ValueError("ไม่พบคำสั่งซื้อ")
    return order


def authorize_view(order) -> None:
    user_id = permissions.require_login()
    role = Session.get_role()
    if permissions.can(role, permissions.ORDER_VIEW):
        return
    if permissions.can(role, permissions.ORDER_OWN) and order["user_id"] == user_id:
        return
    raise PermissionError("คุณไม่มีสิทธิ์ดูคำสั่งซื้อนี้")


def _item_dict(row, user_id: int = None, order_status: str = None, conn=None) -> dict:
    d = dict(row)
    d["line_total"] = round(float(d["price_at_purchase"]) * d["qty"], 2)
    if user_id is not None and order_status == ORDER_STATUS_COMPLETED:
        is_rev = repo_reviews.exists(user_id, d["product_id"], d["order_id"], conn=conn)
        is_skip = repo_reviews.is_skipped(user_id, d["product_id"], d["order_id"], conn=conn)
    else:
        is_rev = False
        is_skip = False
    d["is_reviewed"] = bool(is_rev)
    d["reviewed"] = bool(is_rev)
    d["is_review_skipped"] = bool(is_skip)
    d["can_review"] = bool(order_status == ORDER_STATUS_COMPLETED and not is_rev and not is_skip)
    return d


def _log_dict(row) -> dict:
    d = dict(row)
    d["status_label"] = _label(d["status"])
    return d


def load_order_detail(order_id: int, conn=None) -> dict:
    """รายละเอียดออเดอร์ครบชุด (พร้อมข้อมูล VAT 7%)"""
    order = _get_order_or_raise(order_id, conn)
    d = dict(order)
    d["status_label"] = _label(d["status"])
    d["items"] = [
        _item_dict(r, user_id=d["user_id"], order_status=d["status"], conn=conn)
        for r in repo_orders.list_items(order_id, conn=conn)
    ]
    unrev_pids = {it["product_id"] for it in d["items"] if it.get("product_id") and not it.get("is_reviewed") and not it.get("is_review_skipped")}
    d["awaiting_review_count"] = len(unrev_pids) if d["status"] == ORDER_STATUS_COMPLETED else 0
    d["has_unreviewed"] = bool(d["awaiting_review_count"] > 0)
    d["item_count"] = sum(int(it.get("qty") or 0) for it in d["items"])

    coupon = repo_coupons.get(d["coupon_id"], conn=conn) if d.get("coupon_id") else None
    d["coupon_code"] = coupon["code"] if coupon else None

    payment = repo_payments.get_latest_by_order(order_id, conn=conn)
    if payment is not None:
        payment = dict(payment)
        payment["status_label"] = PAYMENT_STATUS_LABELS.get(payment["status"], payment["status"])
    d["payment"] = payment

    shipment = repo_shipping.get_by_order(order_id, conn=conn)
    if shipment is not None:
        shipment = dict(shipment)
        shipment["status_label"] = SHIPMENT_STATUS_LABELS.get(shipment["status"], shipment["status"])
    d["shipment"] = shipment

    d["timeline"] = [_log_dict(r) for r in repo_orders.list_status_log(order_id, conn=conn)]
    d.update(compute_vat_breakdown(d["total"]))
    return d


def _format_address(address) -> str:
    parts = [address["address_line"], address["district"], address["province"], address["postcode"]]
    return " ".join(str(p).strip() for p in parts if p and str(p).strip())


def _clean_reason(reason) -> str:
    reason = str(reason or "").strip()
    if not reason:
        raise ValueError("กรุณาระบุเหตุผลในการยกเลิก")
    if len(reason) > CANCEL_REASON_MAX:
        raise ValueError(f"เหตุผลยาวเกินไป (ไม่เกิน {CANCEL_REASON_MAX} ตัวอักษร)")
    return reason


def _page_args(page, page_size, default_size):
    try:
        page = max(int(page), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(int(page_size), 1), MAX_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = default_size
    return page, page_size


def _check_status_filter(status):
    if status is None or status == "" or status == [] or status == "all":
        return None, False
    if status == "to_review":
        return None, True
    values = status if isinstance(status, (list, tuple, set)) else [status]
    for s in values:
        if s not in ORDER_STATUSES:
            raise ValueError("สถานะที่เลือกไม่ถูกต้อง")
    return status, False


def _list_orders(user_id, status, search, page, page_size, default_size) -> dict:
    db_status, unreviewed_only = _check_status_filter(status)
    page, page_size = _page_args(page, page_size, default_size)
    total = repo_orders.count_orders(
        user_id=user_id, status=db_status, search=search, unreviewed_only=unreviewed_only
    )
    pages = max((total + page_size - 1) // page_size, 1)
    page = min(page, pages)
    rows = repo_orders.list_orders(
        user_id=user_id, status=db_status, limit=page_size,
        offset=(page - 1) * page_size, search=search, unreviewed_only=unreviewed_only,
    )
    items = []
    for row in rows:
        d = dict(row)
        d["status_label"] = _label(d["status"])
        d["items"] = [
            _item_dict(r, user_id=d["user_id"], order_status=d["status"])
            for r in repo_orders.list_items(d["id"])
        ]
        unrev_pids = {it["product_id"] for it in d["items"] if it.get("product_id") and not it.get("is_reviewed") and not it.get("is_review_skipped")}
        d["awaiting_review_count"] = len(unrev_pids) if d["status"] == ORDER_STATUS_COMPLETED else 0
        d["has_unreviewed"] = bool(d["awaiting_review_count"] > 0)
        d["item_count"] = sum(int(it.get("qty") or 0) for it in d["items"])
        d.update(compute_vat_breakdown(d["total"]))
        items.append(d)
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


def get_order_tab_counts(user_id: int = None) -> dict:
    """
    คืนจำนวนออเดอร์สำหรับทั้ง 8 แท็บตามลำดับใน ORDER_STATUS_DISPLAY_ORDER:
    all, pending, paid, checking_slip, shipped, completed, to_review, cancelled
    """
    if user_id is not None:
        permissions.require_self(permissions.ORDER_OWN, user_id)
    else:
        permissions.require(permissions.ORDER_VIEW)
    by_status = repo_orders.count_by_status(user_id=user_id)
    total_all = sum(by_status.values())
    to_review_count = repo_orders.count_orders(user_id=user_id, unreviewed_only=True)
    counts = {"all": total_all, "to_review": to_review_count}
    for key, _label_th, _tip, db_st in ORDER_STATUS_DISPLAY_ORDER:
        if db_st is not None:
            counts[key] = int(by_status.get(db_st, 0))
    return counts


# ==========================================
# สร้างออเดอร์ (checkout)
# ==========================================

def check_low_stock_and_notify(conn, changes) -> int:
    threshold = settings_service.get_int("low_stock_threshold", 5)
    sent = 0
    for ch in changes:
        if ch["after"] <= threshold < ch["before"]:
            name = ch["product_name"] + (f" ({ch['option_label']})" if ch.get("option_label") else "")
            if ch["after"] <= 0:
                notification_service.notify_staff("สินค้าหมดสต็อก", f"{name} หมดสต็อกแล้ว", conn=conn)
            else:
                notification_service.notify_staff("สินค้าใกล้หมด", f"{name} เหลือ {ch['after']} ชิ้น", conn=conn)
            sent += 1
    return sent


def checkout(user_id: int, address_id: int, coupon_code=None, selected_item_ids=None,
             shipping_coupon_code=None) -> dict:
    """
    สั่งซื้อสินค้าในตะกร้า (เฉพาะรายการที่ติ๊กเลือก; สินค้าที่ไม่ได้เลือกจะยังคงอยู่ในตะกร้า)
    ทุกขั้นอยู่ใน transaction เดียว
    """
    permissions.require_self(permissions.ORDER_OWN, user_id)

    with transaction() as conn:
        address = repo_addresses.get(address_id, conn=conn) if address_id is not None else None
        if address is None or address["user_id"] != user_id:
            raise ValueError("ไม่พบที่อยู่จัดส่ง กรุณาเลือกที่อยู่ใหม่")

        cart = cart_service.get_cart(user_id, conn=conn)
        if not cart["items"]:
            raise ValueError("ตะกร้าสินค้าว่างเปล่า")

        if selected_item_ids is not None:
            sel_set = {int(x) for x in selected_item_ids}
            checkout_items = [i for i in cart["items"] if int(i["cart_item_id"]) in sel_set]
        else:
            checkout_items = [i for i in cart["items"] if i.get("is_selected", True)]

        if not checkout_items:
            raise ValueError("กรุณาเลือกสินค้าในตะกร้าอย่างน้อย 1 รายการก่อนชำระเงิน")

        for item in checkout_items:
            if item["problem"]:
                label = f" ({item['option_label']})" if item["option_label"] else ""
                raise ValueError(f"{item['product_name']}{label}: {item['problem']}")

        subtotal = round(sum(i["line_total"] for i in checkout_items), 2)
        base_shipping_fee = settings_service.shipping_fee_for(subtotal)
        shipping_fee = base_shipping_fee

        coupon_id, discount = None, 0.0
        shipping_coupon_id, shipping_discount = None, 0.0

        code = str(coupon_code or "").strip()
        if code:
            info = coupon_service.validate_coupon(
                code, user_id, subtotal, conn=conn, shipping_fee=base_shipping_fee
            )
            if not repo_coupons.increment_used(info["coupon_id"], conn=conn):
                raise ValueError("โค้ดส่วนลดนี้ถูกใช้ครบสิทธิ์แล้ว")
            coupon_id = info["coupon_id"]
            if info.get("is_free_shipping"):
                shipping_discount = min(base_shipping_fee, float(info["discount"]))
                shipping_fee = round(max(0.0, base_shipping_fee - shipping_discount), 2)
            else:
                discount = info["discount"]

        ship_code = str(shipping_coupon_code or "").strip()
        if ship_code and ship_code.upper() != code.upper():
            s_info = coupon_service.validate_coupon(
                ship_code, user_id, subtotal, conn=conn, shipping_fee=shipping_fee
            )
            if not s_info.get("is_free_shipping"):
                raise ValueError("โค้ดส่วนลดค่าจัดส่งไม่ถูกต้อง")
            if not repo_coupons.increment_used(s_info["coupon_id"], conn=conn):
                raise ValueError("โค้ดส่งฟรีนี้ถูกใช้ครบสิทธิ์แล้ว")
            shipping_coupon_id = s_info["coupon_id"]
            add_ship_disc = min(shipping_fee, float(s_info["discount"]))
            shipping_discount = round(shipping_discount + add_ship_disc, 2)
            shipping_fee = round(max(0.0, shipping_fee - add_ship_disc), 2)
            if coupon_id is None:
                coupon_id = shipping_coupon_id

        total = round(subtotal - discount + shipping_fee, 2)

        order_id = repo_orders.create_order(
            user_id, address["recipient"], address["phone"], _format_address(address),
            subtotal, discount, shipping_fee, total, coupon_id, conn=conn,
        )
        if shipping_discount > 0:
            conn.execute("UPDATE orders SET shipping_discount = ? WHERE id = ?", (shipping_discount, order_id))

        repo_orders.add_items(order_id, [
            {"product_id": i["product_id"], "option_id": i["option_id"], "product_name": i["product_name"],
             "option_label": i["option_label"], "price_at_purchase": i["unit_price"], "qty": i["qty"]}
            for i in checkout_items
        ], conn=conn)
        repo_orders.add_status_log(order_id, ORDER_STATUS_PENDING, "สร้างคำสั่งซื้อ", user_id, conn=conn)

        changes = []
        for item in checkout_items:
            if item["option_id"] is not None:
                ok = repo_products.adjust_option_stock(item["option_id"], -item["qty"], conn=conn)
            else:
                ok = repo_products.adjust_stock(item["product_id"], -item["qty"], conn=conn)
            if not ok:
                label = f" ({item['option_label']})" if item["option_label"] else ""
                raise ValueError(f"{item['product_name']}{label} มีสต็อกไม่พอ กรุณาปรับจำนวนในตะกร้า")
            changes.append({"product_name": item["product_name"], "option_label": item["option_label"],
                            "before": item["stock_available"], "after": item["stock_available"] - item["qty"]})

        for used_cid in {cid for cid in (coupon_id, shipping_coupon_id) if cid is not None}:
            try:
                repo_coupons.add_usage(used_cid, user_id, order_id, conn=conn)
            except sqlite3.IntegrityError:
                raise ValueError("คุณใช้โค้ดส่วนลดนี้ไปแล้ว") from None

        # ลบเฉพาะสินค้าที่เลือกสั่งซื้อออกจากตะกร้า (สินค้าที่ไม่ได้เลือกยังคงอยู่ในตะกร้า — ข้อ 7)
        if len(checkout_items) == len(cart["items"]):
            repo_cart.clear(user_id, conn=conn)
        else:
            repo_cart.remove_many(user_id, [i["cart_item_id"] for i in checkout_items], conn=conn)

        notification_service.notify(
            user_id, "สั่งซื้อสำเร็จ",
            f"คำสั่งซื้อ #{order_id} ยอด {format_price(total)} กรุณาชำระเงินและแนบสลิป", conn=conn)
        notification_service.notify_staff(
            "มีคำสั่งซื้อใหม่", f"คำสั่งซื้อ #{order_id} ยอด {format_price(total)} รอชำระเงิน", conn=conn)
        check_low_stock_and_notify(conn, changes)

        return load_order_detail(order_id, conn=conn)


# ==========================================
# ยกเลิก
# ==========================================

def _restore_stock(conn, order_id: int) -> None:
    for item in repo_orders.list_items(order_id, conn=conn):
        if item["option_id"] is not None:
            repo_products.adjust_option_stock(item["option_id"], item["qty"], conn=conn)
        else:
            repo_products.adjust_stock(item["product_id"], item["qty"], conn=conn)


def _cancel_in_txn(conn, order, reason: str, changed_by, actor: str) -> None:
    order_id, was_status = order["id"], order["status"]
    refund_note = " — ชำระเงินแล้ว ต้องคืนเงินให้ลูกค้าด้วยมือ" if was_status == ORDER_STATUS_PAID else ""
    apply_status_change(conn, order_id, was_status, ORDER_STATUS_CANCELLED,
                        f"ยกเลิกคำสั่งซื้อ: {reason}{refund_note}", changed_by)
    repo_orders.set_cancel_reason(order_id, reason, conn=conn)
    _restore_stock(conn, order_id)

    if order["coupon_id"]:
        repo_coupons.decrement_used(order["coupon_id"], conn=conn)
        repo_coupons.remove_usage(order_id, conn=conn)

    payment = repo_payments.get_latest_by_order(order_id, conn=conn)
    if payment is not None and payment["status"] == PAYMENT_STATUS_PENDING:
        repo_payments.mark_rejected(payment["id"], f"ยกเลิกคำสั่งซื้อ: {reason}", changed_by, conn=conn)

    if actor == "buyer":
        notification_service.notify_staff("ลูกค้ายกเลิกคำสั่งซื้อ", f"คำสั่งซื้อ #{order_id}: {reason}", conn=conn)
    else:
        prefix = "ยกเลิกอัตโนมัติ" if actor == "system" else "ถูกยกเลิก"
        extra = " ร้านจะติดต่อเพื่อคืนเงินให้" if refund_note else ""
        notification_service.notify(
            order["user_id"], "คำสั่งซื้อถูกยกเลิก", f"คำสั่งซื้อ #{order_id} {prefix}: {reason}{extra}", conn=conn)
        if actor == "staff":
            audit_service.log("order.cancel_by_staff", "order", order_id, {"reason": reason, "was_status": was_status}, conn=conn)


def cancel_order(order_id: int, reason: str) -> dict:
    user_id = permissions.require_login()
    reason = _clean_reason(reason)
    role = Session.get_role()

    with transaction() as conn:
        order = _get_order_or_raise(order_id, conn)
        if permissions.can(role, permissions.ORDER_CANCEL):
            actor, allowed = "staff", STAFF_CANCELLABLE
        elif permissions.can(role, permissions.ORDER_OWN):
            if order["user_id"] != user_id:
                raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")
            actor, allowed = "buyer", BUYER_CANCELLABLE
        else:
            raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")

        if order["status"] not in allowed:
            if order["status"] == ORDER_STATUS_CANCELLED:
                raise ValueError("คำสั่งซื้อนี้ถูกยกเลิกไปแล้ว")
            if actor == "buyer":
                raise ValueError("ยกเลิกได้เฉพาะคำสั่งซื้อที่ยังไม่ชำระเงิน หากชำระแล้วกรุณาติดต่อร้านค้า")
            raise ValueError(f"ยกเลิกไม่ได้ เพราะคำสั่งซื้อ{_label(order['status'])}แล้ว")

        _cancel_in_txn(conn, order, reason, user_id, actor)
        return load_order_detail(order_id, conn=conn)


def _pending_since(conn, order):
    since = order["created_at"]
    for log in repo_orders.list_status_log(order["id"], conn=conn):
        if log["status"] == ORDER_STATUS_PENDING:
            since = log["created_at"]
    return parse_datetime(since)


def auto_cancel_unpaid() -> int:
    hours = settings_service.get_int("unpaid_cancel_hours", 24)
    if hours <= 0:
        return 0
    reason = f"ไม่ชำระเงินภายใน {hours} ชั่วโมง"
    limit = timedelta(hours=hours)
    cancelled = 0
    with transaction() as conn:
        for order in repo_orders.list_expired_pending(hours, conn=conn):
            since = _pending_since(conn, order)
            if since is not None and datetime.now() - since < limit:
                continue
            _cancel_in_txn(conn, order, reason, None, "system")
            cancelled += 1
    return cancelled


# ==========================================
# ยืนยันรับสินค้า / ส่งถึงปลายทาง (+ ออกคูปองรางวัลตามกฎ OWN-1)
# ==========================================

def complete_delivery(conn, order, changed_by, by_buyer: bool) -> None:
    order_id = order["id"]
    note = "ผู้ซื้อยืนยันได้รับสินค้า" if by_buyer else "แอดมินยืนยันว่าสินค้าส่งถึงปลายทางแล้ว"
    apply_status_change(conn, order_id, order["status"], ORDER_STATUS_COMPLETED, note, changed_by)
    repo_shipping.update(order_id, status=SHIPMENT_STATUS_DELIVERED, conn=conn)
    if by_buyer:
        notification_service.notify_staff("ลูกค้ารับสินค้าแล้ว", f"คำสั่งซื้อ #{order_id} เสร็จสิ้น", conn=conn)
    else:
        notification_service.notify(
            order["user_id"], "สินค้าส่งถึงแล้ว",
            f"คำสั่งซื้อ #{order_id} ส่งถึงปลายทางแล้ว ขอบคุณที่ใช้บริการ รีวิวสินค้าได้เลย", conn=conn)
    coupon_service.issue_reward_coupons(order_id, order["user_id"], order["total"], conn=conn)


def confirm_received(order_id: int) -> dict:
    permissions.require(permissions.ORDER_OWN)
    user_id = permissions.require_login()
    with transaction() as conn:
        order = _get_order_or_raise(order_id, conn)
        if order["user_id"] != user_id:
            raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")
        if order["status"] != ORDER_STATUS_SHIPPED:
            raise ValueError("ยืนยันรับสินค้าได้เฉพาะคำสั่งซื้อที่จัดส่งแล้ว")
        complete_delivery(conn, order, user_id, by_buyer=True)
        return load_order_detail(order_id, conn=conn)


# ==========================================
# ดูข้อมูล
# ==========================================

def get_order_detail(order_id: int) -> dict:
    order = _get_order_or_raise(order_id)
    authorize_view(order)
    return load_order_detail(order_id)


def get_timeline(order_id: int) -> list[dict]:
    order = _get_order_or_raise(order_id)
    authorize_view(order)
    return [_log_dict(r) for r in repo_orders.list_status_log(order_id)]


def list_my_orders(user_id: int, status=None, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> dict:
    permissions.require_self(permissions.ORDER_OWN, user_id)
    return _list_orders(user_id, status, None, page, page_size, DEFAULT_PAGE_SIZE)


def list_orders_admin(status=None, search=None, page: int = 1, page_size: int = 20) -> dict:
    permissions.require(permissions.ORDER_VIEW)
    return _list_orders(None, status, search, page, page_size, 20)


# ==========================================
# Dashboard (admin/owner)
# ==========================================

def get_dashboard_stats(days: int = 7) -> dict:
    permissions.require(permissions.DASHBOARD_VIEW)
    show_revenue = permissions.can(Session.get_role(), permissions.DASHBOARD_REVENUE)
    try:
        days = min(max(int(days), 1), 90)
    except (TypeError, ValueError):
        days = 7

    today = date.today()
    today_s = today.isoformat()
    month_s = today.replace(day=1).isoformat()

    counts = repo_orders.count_by_status()
    sales = {r["day"]: r for r in repo_orders.daily_sales(days)}
    daily = []
    for offset in range(days - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        row = sales.get(day)
        daily.append({"day": day, "orders": row["orders"] if row else 0,
                      "revenue": (row["revenue"] if row else 0.0) if show_revenue else None})

    top = []
    for r in repo_orders.top_products(5):
        d = dict(r)
        if not show_revenue:
            d["total_sales"] = None
        top.append(d)

    return {
        "counts": counts,
        "pending_slips": counts[ORDER_STATUS_CHECKING_SLIP],
        "revenue_today": repo_orders.sum_revenue(today_s, today_s) if show_revenue else None,
        "revenue_month": repo_orders.sum_revenue(month_s, today_s) if show_revenue else None,
        "revenue_total": repo_orders.sum_revenue() if show_revenue else None,
        "top_products": top,
        "daily_sales": daily,
    }


def count_my_orders_by_tab(user_id: int = None) -> dict:
    counts = get_order_tab_counts(user_id=user_id)
    counts[None] = counts.get("all", 0)
    return counts
