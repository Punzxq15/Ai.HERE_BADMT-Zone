"""
services/payment_service.py
ชำระเงินด้วย PromptPay + สลิป:
    ผู้ซื้อ  : get_payment_info -> submit_slip (แนบสลิป pending -> checking_slip)
    แอดมิน : list_pending_payments -> verify_payment / verify_payment_and_notify (checking_slip -> paid + สร้าง shipments + ส่งใบเสร็จอีเมล)
                                   -> reject_payment (checking_slip -> pending + เหตุผล ผู้ซื้อแนบใหม่ได้)
"""
import config
from core import permissions
from core.constants import (
    ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_LABELS, ORDER_STATUS_PAID, ORDER_STATUS_PENDING,
    PAYMENT_METHOD_PROMPTPAY, PAYMENT_STATUS_LABELS, PAYMENT_STATUS_PENDING,
)
from database import repo_orders, repo_payments, repo_products, repo_shipping
from database.db import transaction
from services import audit_service, notification_service, order_service, settings_service
from utils import image_utils, promptpay
from utils.formatters import format_price

REJECT_REASON_MAX = 200


def _payment_dict(row) -> dict:
    d = dict(row)
    d["status_label"] = PAYMENT_STATUS_LABELS.get(d["status"], d["status"])
    return d


def _get_order(order_id, conn=None):
    order = repo_orders.get_order(order_id, conn=conn)
    if order is None:
        raise ValueError("ไม่พบคำสั่งซื้อ")
    return order


def get_payment_info(order_id: int) -> dict:
    order = _get_order(order_id)
    order_service.authorize_view(order)

    shop = settings_service.get_shop_info()
    if not shop["promptpay_no"]:
        raise ValueError("ร้านยังไม่ได้ตั้งค่าเลขพร้อมเพย์ กรุณาติดต่อร้านค้า")
    amount = round(float(order["total"]), 2)
    payload = promptpay.build_payload(shop["promptpay_no"], amount) if amount > 0 else None

    history = [_payment_dict(r) for r in repo_payments.list_by_order(order_id)]

    # รายการสินค้าแบบคร่าวๆ (ชื่อ / สเปก / ราคา) สำหรับแสดงในหน้าชำระเงิน (ข้อ 9)
    raw_items = repo_orders.list_items(order_id)
    order_items = []
    for r in raw_items:
        it = dict(r)
        it["line_total"] = round(float(it["price_at_purchase"]) * int(it["qty"]), 2)
        prod = repo_products.get_product(it["product_id"])
        spec_parts = []
        if it.get("option_label"):
            spec_parts.append(str(it["option_label"]))
        if prod is not None:
            for k in ("weight_class", "balance", "flex"):
                val = prod[k] if k in prod.keys() else None
                if val:
                    spec_parts.append(str(val))
        it["spec_summary"] = " · ".join(spec_parts) if spec_parts else "-"
        order_items.append(it)

    vat_info = order_service.compute_vat_breakdown(amount)

    return {
        "order_id": order_id,
        "order_status": order["status"],
        "order_status_label": ORDER_STATUS_LABELS.get(order["status"], order["status"]),
        "amount": amount,
        "subtotal": round(float(order["subtotal"]), 2),
        "discount": round(float(order["discount"]), 2),
        "shipping_fee": round(float(order["shipping_fee"]), 2),
        **vat_info,
        "items": order_items,
        "shop_name": shop["shop_name"],
        "promptpay_no": shop["promptpay_no"],
        "promptpay_name": shop["promptpay_name"],
        "payload": payload,
        "payment": history[-1] if history else None,
        "history": history,
        "can_submit_slip": order["status"] == ORDER_STATUS_PENDING,
    }


def submit_slip(order_id: int, file_path) -> dict:
    permissions.require(permissions.ORDER_OWN)
    user_id = permissions.require_login()

    order = _get_order(order_id)
    if order["user_id"] != user_id:
        raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")
    if order["status"] != ORDER_STATUS_PENDING:
        label = ORDER_STATUS_LABELS.get(order["status"], order["status"])
        raise ValueError(f"แนบสลิปได้เฉพาะคำสั่งซื้อที่รอชำระเงิน (ตอนนี้: {label})")

    slip_rel = image_utils.save_upload(file_path, config.SLIPS_DIR, f"slip_{order_id}")
    try:
        with transaction() as conn:
            fresh = _get_order(order_id, conn)
            repo_payments.create(order_id, PAYMENT_METHOD_PROMPTPAY, fresh["total"], slip_rel, conn=conn)
            order_service.apply_status_change(conn, order_id, fresh["status"], ORDER_STATUS_CHECKING_SLIP,
                                              "แนบสลิปชำระเงิน", user_id)
            notification_service.notify_staff(
                "มีสลิปรอตรวจสอบ", f"คำสั่งซื้อ #{order_id} ยอด {format_price(fresh['total'])}", conn=conn)
            return order_service.load_order_detail(order_id, conn=conn)
    except BaseException:
        image_utils.delete_upload(slip_rel)
        raise


def list_pending_payments() -> list[dict]:
    permissions.require(permissions.SLIP_VERIFY)
    return [_payment_dict(r) for r in repo_payments.list_pending()]


def _load_pending_payment(conn, payment_id):
    payment = repo_payments.get(payment_id, conn=conn)
    if payment is None:
        raise ValueError("ไม่พบรายการชำระเงิน")
    if payment["status"] != PAYMENT_STATUS_PENDING:
        raise ValueError("รายการชำระเงินนี้ถูกตรวจสอบไปแล้ว")
    if payment["order_status"] != ORDER_STATUS_CHECKING_SLIP:
        label = ORDER_STATUS_LABELS.get(payment["order_status"], payment["order_status"])
        raise ValueError(f"ตรวจสลิปไม่ได้ เพราะคำสั่งซื้อ{label}")
    return payment


def verify_payment(payment_id: int) -> dict:
    """
    แอดมิน/เจ้าของ ยืนยันสลิปถูกต้อง: payments = verified · ออเดอร์ checking_slip -> paid
    · สร้าง shipments (preparing) · แจ้งผู้ซื้อ — transaction เดียว คืน dict รายละเอียดออเดอร์
    """
    permissions.require(permissions.SLIP_VERIFY)
    staff_id = permissions.require_login()
    with transaction() as conn:
        payment = _load_pending_payment(conn, payment_id)
        order_id = payment["order_id"]
        if not repo_payments.mark_verified(payment_id, staff_id, conn=conn):
            raise ValueError("รายการชำระเงินนี้ถูกตรวจสอบไปแล้ว")
        order_service.apply_status_change(conn, order_id, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_PAID,
                                          "ตรวจสลิปแล้ว ชำระเงินสำเร็จ", staff_id)
        if repo_shipping.get_by_order(order_id, conn=conn) is None:
            repo_shipping.create(order_id, conn=conn)
        notification_service.notify(
            payment["buyer_id"], "ชำระเงินสำเร็จ",
            f"คำสั่งซื้อ #{order_id} ตรวจสอบการชำระเงินแล้ว ร้านกำลังเตรียมจัดส่ง", conn=conn)
        audit_service.log("payment.verify", "order", order_id, {"payment_id": payment_id}, conn=conn)
        return order_service.load_order_detail(order_id, conn=conn)


def verify_payment_and_notify(payment_id: int, background: bool = True) -> dict:
    """
    ตัวห่อสำหรับหน้าจอ: เรียก verify_payment (commit เรียบร้อย) แล้วส่งใบเสร็จทางอีเมลให้ลูกค้า (SYS-3)
    """
    detail = verify_payment(payment_id)
    try:
        from services import email_outbox_service
        email_outbox_service.queue_receipt_email(detail["id"], background=background)
    except Exception:
        pass
    return detail


def reject_payment(payment_id: int, reason: str) -> dict:
    permissions.require(permissions.SLIP_VERIFY)
    staff_id = permissions.require_login()
    reason = str(reason or "").strip()
    if not reason:
        raise ValueError("กรุณาระบุเหตุผลที่ปฏิเสธสลิป")
    if len(reason) > REJECT_REASON_MAX:
        raise ValueError(f"เหตุผลยาวเกินไป (ไม่เกิน {REJECT_REASON_MAX} ตัวอักษร)")

    with transaction() as conn:
        payment = _load_pending_payment(conn, payment_id)
        order_id = payment["order_id"]
        if not repo_payments.mark_rejected(payment_id, reason, staff_id, conn=conn):
            raise ValueError("รายการชำระเงินนี้ถูกตรวจสอบไปแล้ว")
        order_service.apply_status_change(conn, order_id, ORDER_STATUS_CHECKING_SLIP, ORDER_STATUS_PENDING,
                                          f"สลิปไม่ผ่าน: {reason}", staff_id)
        notification_service.notify(
            payment["buyer_id"], "สลิปไม่ผ่านการตรวจสอบ",
            f"คำสั่งซื้อ #{order_id}: {reason} กรุณาแนบสลิปใหม่", conn=conn)
        audit_service.log("payment.reject", "order", order_id, {"payment_id": payment_id, "reason": reason}, conn=conn)
        return order_service.load_order_detail(order_id, conn=conn)
