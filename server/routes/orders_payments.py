"""
server/routes/orders_payments.py
API สำหรับเตรียมสั่งซื้อ (Checkout) คำสั่งซื้อ ชำระเงิน PromptPay QR แนบสลิป ตรวจสลิป จัดส่งพัสดุ และใบเสร็จ PDF
"""
import io
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Response, UploadFile
from fastapi.responses import FileResponse

import config
from core import permissions
from core.constants import CARRIERS, ORDER_STATUS_DISPLAY_ORDER
from core.session import Session
from database import repo_payments
from server import deps
from server.serializers import to_jsonable
from services import (
    account_service,
    cart_service,
    coupon_service,
    email_outbox_service,
    order_service,
    payment_service,
    receipt_service,
    settings_service,
    shipping_service,
)
from utils import image_utils, promptpay

router = APIRouter(prefix="/api", tags=["orders_payments"])


@router.get("/checkout/info")
def get_checkout_info(coupon_code: str | None = None, shipping_coupon_code: str | None = None):
    """คำนวณยอดรวม ค่าส่ง ส่วนลดคูปอง และภาษี VAT 7% ที่ฝั่งเซิร์ฟเวอร์สำหรับหน้า Checkout"""
    uid = deps.require_user_id()
    cart = cart_service.get_cart(uid)
    addresses = account_service.list_addresses(uid)
    selected_items = cart.get("selected_items") or []
    subtotal = round(float(cart.get("selected_subtotal") or 0.0), 2)
    base_shipping_fee = settings_service.shipping_fee_for(subtotal) if subtotal > 0 else 0.0
    shipping_fee = base_shipping_fee
    checkout_coupons = coupon_service.list_checkout_coupons(uid, subtotal=subtotal, shipping_fee=base_shipping_fee)

    discount = 0.0
    shipping_discount = 0.0
    applied_coupon = None
    applied_shipping_coupon = None
    coupon_error = None
    shipping_coupon_error = None

    code = str(coupon_code or "").strip()
    if code and subtotal > 0:
        try:
            info = coupon_service.validate_coupon(code, uid, subtotal, shipping_fee=base_shipping_fee)
            applied_coupon = info
            if info.get("is_free_shipping"):
                shipping_discount = min(base_shipping_fee, float(info["discount"]))
                shipping_fee = round(max(0.0, base_shipping_fee - shipping_discount), 2)
            else:
                discount = float(info["discount"])
        except ValueError as exc:
            coupon_error = str(exc)

    ship_code = str(shipping_coupon_code or "").strip()
    if ship_code and ship_code.upper() != code.upper() and subtotal > 0:
        try:
            s_info = coupon_service.validate_coupon(ship_code, uid, subtotal, shipping_fee=shipping_fee)
            if not s_info.get("is_free_shipping"):
                raise ValueError("โค้ดส่วนลดค่าจัดส่งไม่ถูกต้อง")
            applied_shipping_coupon = s_info
            add_disc = min(shipping_fee, float(s_info["discount"]))
            shipping_discount = round(shipping_discount + add_disc, 2)
            shipping_fee = round(max(0.0, shipping_fee - add_disc), 2)
        except ValueError as exc:
            shipping_coupon_error = str(exc)

    total = round(max(0.0, subtotal - discount + shipping_fee), 2) if subtotal > 0 else 0.0
    vat_info = order_service.compute_vat_breakdown(total)

    return to_jsonable({
        "cart": cart,
        "selected_items": selected_items,
        "addresses": addresses,
        "coupons": checkout_coupons,
        "subtotal": subtotal,
        "base_shipping_fee": base_shipping_fee,
        "shipping_fee": shipping_fee,
        "shipping_discount": shipping_discount,
        "discount": discount,
        "total": total,
        **vat_info,
        "free_shipping_min": settings_service.get_float("free_shipping_min", 0.0),
        "applied_coupon": applied_coupon,
        "applied_shipping_coupon": applied_shipping_coupon,
        "coupon_error": coupon_error,
        "shipping_coupon_error": shipping_coupon_error,
    })


@router.post("/orders")
def create_order(payload: dict):
    uid = deps.require_user_id()
    address_id = payload.get("address_id")
    if address_id is None or address_id == "":
        raise ValueError("กรุณาเลือกที่อยู่จัดส่ง")
    order = order_service.checkout(
        user_id=uid,
        address_id=int(address_id),
        coupon_code=payload.get("coupon_code") or None,
        selected_item_ids=payload.get("selected_item_ids"),
        shipping_coupon_code=payload.get("shipping_coupon_code") or None,
    )
    return to_jsonable(order)


@router.get("/orders/tabs")
def get_order_tabs():
    return to_jsonable([
        {"key": k, "label": lbl, "tooltip": tip, "db_status": st}
        for k, lbl, tip, st in ORDER_STATUS_DISPLAY_ORDER
    ])


@router.get("/orders/my")
def list_my_orders(status: str | None = None, page: int = 1, page_size: int = 10):
    uid = deps.require_user_id()
    try:
        order_service.auto_cancel_unpaid()
    except Exception:
        pass
    res = order_service.list_my_orders(uid, status=status, page=page, page_size=page_size)
    res["counts"] = order_service.get_order_tab_counts(uid)
    res["tabs"] = [
        {"key": k, "label": lbl, "tooltip": tip}
        for k, lbl, tip, _ in ORDER_STATUS_DISPLAY_ORDER
    ]
    return to_jsonable(res)


@router.get("/orders/my/counts")
def count_my_orders():
    uid = deps.require_user_id()
    return to_jsonable(order_service.get_order_tab_counts(uid))


@router.get("/orders/{order_id}")
def get_order_detail(order_id: int):
    detail = order_service.get_order_detail(order_id)
    detail["receipt_email"] = email_outbox_service.get_receipt_email_status(order_id)
    detail["carriers"] = list(CARRIERS)
    return to_jsonable(detail)


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, payload: dict):
    reason = payload.get("reason") or ""
    return to_jsonable(order_service.cancel_order(order_id, reason))


@router.post("/orders/{order_id}/confirm-received")
def confirm_received(order_id: int):
    return to_jsonable(order_service.confirm_received(order_id))


@router.get("/orders/{order_id}/payment-info")
def get_payment_info(order_id: int):
    info = payment_service.get_payment_info(order_id)
    info["unpaid_cancel_hours"] = settings_service.get_int("unpaid_cancel_hours", 24)
    return to_jsonable(info)


@router.get("/orders/{order_id}/promptpay-qr")
def get_promptpay_qr_image(order_id: int, size: int = 260, download: bool = False):
    info = payment_service.get_payment_info(order_id)
    payload_str = info.get("payload")
    if not payload_str:
        raise ValueError("ไม่สามารถสร้าง QR PromptPay สำหรับคำสั่งซื้อนี้ได้")
    px = max(120, min(600, int(size or 260)))
    pil_img = promptpay.make_qr_image(payload_str, size=px)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="promptpay_order_{order_id}.png"'
    return Response(content=buf.getvalue(), media_type="image/png", headers=headers)


@router.post("/orders/{order_id}/slip")
def submit_payment_slip(order_id: int, file: UploadFile = File(...)):
    suffix = Path(file.filename or "slip.jpg").suffix.lower() or ".jpg"
    raw = file.file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)
    try:
        detail = payment_service.submit_slip(order_id, tmp_path)
        return to_jsonable(detail)
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/orders/{order_id}/receipt.pdf")
def download_receipt_pdf(order_id: int, download: bool = False):
    # ตรวจสิทธิ์เจ้าของออเดอร์หรือ staff ภายใน generate_receipt / get_order_detail
    order_service.get_order_detail(order_id)
    pdf_path = Path(receipt_service.generate_receipt(order_id))
    if not pdf_path.is_file():
        raise ValueError("ไม่พบไฟล์ใบเสร็จ PDF")
    disp = "attachment" if download else "inline"
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disp}; filename="receipt_{order_id}.pdf"'},
    )


@router.post("/orders/{order_id}/send-receipt-email")
def send_receipt_email(order_id: int):
    # ผู้ซื้อเจ้าของออเดอร์หรือแอดมิน/เจ้าของร้านสั่งส่งอีเมลใบเสร็จได้
    detail = order_service.get_order_detail(order_id)
    role = Session.get_role()
    if role == "buyer":
        res = email_outbox_service.queue_receipt_email(detail["id"], background=False)
        return to_jsonable({
            **(res or {}),
            "status": (res or {}).get("status", "sent"),
            "message": "ส่งใบเสร็จ PDF ทางอีเมลเรียบร้อยแล้ว",
        })
    return to_jsonable(email_outbox_service.send_receipt_email(order_id))


# ==========================================
# เสิร์ฟรูปสลิปโอนเงินแบบตรวจสิทธิ์ (ห้ามเสิร์ฟเป็น static)
# ==========================================

def _resolve_safe_slip_file(slip_rel_path: str) -> Path:
    if not slip_rel_path:
        raise ValueError("ไม่พบรูปสลิปโอนเงิน")
    full_path = image_utils.resolve_path(slip_rel_path).resolve()
    slips_root = Path(config.SLIPS_DIR).resolve()
    if slips_root not in full_path.parents or not full_path.is_file():
        raise ValueError("ไม่พบไฟล์สลิปโอนเงิน")
    return full_path


@router.get("/files/slips/{payment_id}")
def get_slip_image_by_payment(payment_id: int):
    payment = repo_payments.get(payment_id)
    if payment is None:
        raise ValueError("ไม่พบรายการชำระเงิน")
    order = order_service.get_order_detail(payment["order_id"])
    full_path = _resolve_safe_slip_file(payment["slip_path"] or (order.get("payment") or {}).get("slip_path"))
    return FileResponse(path=str(full_path))


@router.get("/orders/{order_id}/slip-image")
def get_slip_image_by_order(order_id: int):
    detail = order_service.get_order_detail(order_id)
    payment = detail.get("payment")
    if not payment or not payment.get("slip_path"):
        raise ValueError("ยังไม่มีสลิปโอนเงินสำหรับคำสั่งซื้อนี้")
    full_path = _resolve_safe_slip_file(payment["slip_path"])
    return FileResponse(path=str(full_path))


# ==========================================
# ฝั่งแอดมิน / เจ้าของร้าน (Admin Orders, Shipping, Slip Verification)
# ==========================================

@router.get("/admin/orders")
def admin_list_orders(
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    try:
        order_service.auto_cancel_unpaid()
    except Exception:
        pass
    res = order_service.list_orders_admin(status=status, search=search, page=page, page_size=page_size)
    res["counts"] = order_service.get_order_tab_counts(None)
    res["carriers"] = list(CARRIERS)
    return to_jsonable(res)


@router.post("/admin/orders/{order_id}/ship")
def admin_ship_order(order_id: int, payload: dict):
    carrier = payload.get("carrier") or ""
    tracking_no = payload.get("tracking_no") or ""
    return to_jsonable(shipping_service.ship_order_and_notify(order_id, carrier, tracking_no))


@router.put("/admin/orders/{order_id}/tracking")
def admin_update_tracking(order_id: int, payload: dict):
    carrier = payload.get("carrier") or ""
    tracking_no = payload.get("tracking_no") or ""
    return to_jsonable(shipping_service.update_tracking(order_id, carrier, tracking_no))


@router.post("/admin/orders/{order_id}/delivered")
def admin_mark_delivered(order_id: int):
    return to_jsonable(shipping_service.mark_delivered(order_id))


@router.post("/admin/orders/{order_id}/send-tracking-email")
def admin_send_tracking_email(order_id: int, payload: dict | None = None):
    detail = order_service.get_order_detail(order_id)
    sh = detail.get("shipment") or {}
    carrier = (payload or {}).get("carrier") or sh.get("carrier") or ""
    tracking_no = (payload or {}).get("tracking_no") or sh.get("tracking_no") or ""
    return to_jsonable(email_outbox_service.send_tracking_email(order_id, carrier, tracking_no))


@router.get("/admin/payments/pending")
def admin_list_pending_payments():
    permissions.require(permissions.SLIP_VERIFY)
    items = payment_service.list_pending_payments()
    return to_jsonable(items)


@router.post("/admin/payments/{payment_id}/verify")
def admin_verify_payment(payment_id: int):
    return to_jsonable(payment_service.verify_payment_and_notify(payment_id))


@router.post("/admin/payments/{payment_id}/reject")
def admin_reject_payment(payment_id: int, payload: dict):
    reason = payload.get("reason") or ""
    return to_jsonable(payment_service.reject_payment(payment_id, reason))
