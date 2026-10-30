"""
services/email_outbox_service.py
จัดการคิวส่งอีเมลอัตโนมัติ (ตาราง email_outbox) สำหรับ:
1. ใบเสร็จอิเล็กทรอนิกส์หลังแอดมินตรวจสลิปผ่าน (SYS-3 / D12): ส่งข้อความสรุปรายการ + VAT 7% + แนบ PDF ใบเสร็จ
2. แจ้งสถานะจัดส่งพร้อมเลขพัสดุ (E5)
3. สรุปสินค้าสต็อกต่ำรายวันถึงเจ้าของร้าน (E6)
"""
import contextvars
import threading
from datetime import date
from pathlib import Path

import config
from core import permissions
from database import repo_orders, repo_outbox, repo_users
from services import email_service, notification_service, order_service, receipt_service, settings_service
from utils import validators
from utils.formatters import format_price


def _deliver_outbox_item(outbox_id: int) -> bool:
    """ส่งอีเมลของแถว outbox_id จริง และอัปเดตสถานะ sent/failed"""
    row = repo_outbox.get_outbox(outbox_id)
    if row is None:
        return False
    attachments = [row["attachment_path"]] if row["attachment_path"] and Path(row["attachment_path"]).is_file() else ()
    contact = settings_service.get_contact_info()
    reply_to = contact.get("shop_email") if validators.is_valid_email(contact.get("shop_email") or "") else None
    try:
        email_service.send_mail(
            to_email=row["to_email"],
            subject=row["subject"],
            text=row["body_text"] or "",
            html=row["body_html"],
            attachments=attachments,
            reply_to=reply_to,
        )
        repo_outbox.mark_sent(outbox_id)
        return True
    except Exception as exc:
        repo_outbox.mark_failed(outbox_id, str(exc))
        return False


def _build_receipt_email_content(order_id: int) -> tuple[str, str, str, str | None, int | None]:
    """สร้าง (to_email, subject, body_text, pdf_path, buyer_id) สำหรับใบเสร็จของออเดอร์ (พร้อม VAT 7%)"""
    order = repo_orders.get_order(order_id)
    if order is None:
        raise ValueError("ไม่พบคำสั่งซื้อ")
    buyer = repo_users.get_by_id(order["user_id"])
    if buyer is None:
        raise ValueError("ไม่พบบัญชีผู้ซื้อ")
    to_email = (buyer["email"] or "").strip().lower()
    if not validators.is_valid_email(to_email):
        raise ValueError("อีเมลผู้ซื้อไม่ถูกต้อง")

    items = repo_orders.list_items(order_id)
    contact = settings_service.get_contact_info()
    shop_name = contact.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
    shop_address = contact.get("shop_address") or "-"

    lines = []
    for idx, it in enumerate(items, start=1):
        opt = f" ({it['option_label']})" if it["option_label"] else ""
        line_total = round(float(it["price_at_purchase"]) * int(it["qty"]), 2)
        lines.append(f"  {idx}. {it['product_name']}{opt} × {it['qty']} = {format_price(line_total)}")
    items_block = "\n".join(lines) or "  -"

    vat_info = order_service.compute_vat_breakdown(order["total"])

    subject = f"ยืนยันการชำระเงินและใบเสร็จคำสั่งซื้อ #{order_id} — {shop_name}"
    body_text = (
        f"สวัสดีคุณ {buyer['full_name']},\n\n"
        f"ทางร้าน {shop_name} ได้ตรวจสอบการชำระเงินของคำสั่งซื้อ #{order_id} เรียบร้อยแล้ว\n\n"
        f"รายการสินค้า:\n{items_block}\n\n"
        f"ราคาสินค้า: {format_price(order['subtotal'])}\n"
        f"ส่วนลด: {format_price(order['discount'])}\n"
        f"ค่าจัดส่ง: {format_price(order['shipping_fee'])}\n"
        f"มูลค่าก่อนภาษี: {format_price(vat_info['pre_vat_amount'])}\n"
        f"ภาษีมูลค่าเพิ่ม (VAT 7%): {format_price(vat_info['vat_amount'])}\n"
        f"ยอดรวมที่ชำระสุทธิ (รวม VAT 7%): {format_price(order['total'])}\n\n"
        f"ที่อยู่จัดส่ง: {order['recipient_name']} ({order['recipient_phone']}) {order['shipping_address']}\n"
        f"ที่ตั้งหน้าร้าน: {shop_address}\n"
        f"ขั้นตอนต่อไป: ร้านกำลังเตรียมจัดส่งพัสดุ และจะแจ้งเลขพัสดุให้ทราบในแอป\n"
        f"ติดต่อร้าน: โทร {contact.get('shop_phone') or '-'} | LINE {contact.get('line_name') or '-'}\n"
    )

    pdf_path = None
    try:
        generated = receipt_service.generate_receipt(order_id)
        if generated and Path(generated).is_file():
            pdf_path = str(generated)
    except Exception:
        pdf_path = None

    return to_email, subject, body_text, pdf_path, int(buyer["id"])


def queue_receipt_email(order_id: int, background: bool = True) -> dict | None:
    """
    เข้าคิวและส่งอีเมลใบเสร็จอิเล็กทรอนิกส์หลังแอดมินยืนยันสลิปผ่าน (SYS-3)
    ส่งครั้งเดียวต่อออเดอร์ (หากมีแถวอยู่แล้วจะไม่สร้างซ้ำ)
    """
    if not config.RECEIPT_EMAIL_ENABLED:
        return None
    existing = repo_outbox.get_by_order_and_kind(order_id, "receipt")
    if existing is not None:
        return dict(existing)

    to_email, subject, body_text, pdf_path, buyer_id = _build_receipt_email_content(order_id)
    outbox_id = repo_outbox.create_outbox(
        kind="receipt",
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        attachment_path=pdf_path,
        related_order_id=order_id,
    )

    def _job():
        ok = _deliver_outbox_item(outbox_id)
        if ok and buyer_id:
            try:
                notification_service.notify(
                    buyer_id,
                    "ส่งใบเสร็จทางอีเมลแล้ว",
                    f"ส่งใบเสร็จอิเล็กทรอนิกส์ของคำสั่งซื้อ #{order_id} ไปที่อีเมลของคุณแล้ว",
                )
            except Exception:
                pass

    if background:
        threading.Thread(target=contextvars.copy_context().run, args=(_job,), daemon=True).start()
    else:
        _job()

    return dict(repo_outbox.get_outbox(outbox_id))


def resend_receipt_email(order_id: int) -> dict:
    """แอดมิน/เจ้าของร้านกดส่งใบเสร็จทางอีเมลอีกครั้งด้วยมือ"""
    permissions.require_any(permissions.SLIP_VERIFY, permissions.ORDER_VIEW)
    to_email, subject, body_text, pdf_path, buyer_id = _build_receipt_email_content(order_id)
    existing = repo_outbox.get_by_order_and_kind(order_id, "receipt")
    if existing is None:
        outbox_id = repo_outbox.create_outbox(
            kind="receipt",
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            attachment_path=pdf_path,
            related_order_id=order_id,
        )
    else:
        outbox_id = existing["id"]
        repo_outbox.reset_for_resend(outbox_id, to_email=to_email, attachment_path=pdf_path)

    ok = _deliver_outbox_item(outbox_id)
    if ok and buyer_id:
        notification_service.notify(
            buyer_id,
            "ส่งใบเสร็จทางอีเมลแล้ว",
            f"ส่งใบเสร็จอิเล็กทรอนิกส์ของคำสั่งซื้อ #{order_id} ไปที่อีเมลของคุณแล้ว",
        )
    row = repo_outbox.get_outbox(outbox_id)
    if not ok:
        raise ValueError(row["last_error"] or "ส่งอีเมลใบเสร็จไม่สำเร็จ")
    return dict(row)


def get_receipt_email_status(order_id: int) -> dict:
    """สถานะการส่งอีเมลใบเสร็จของออเดอร์ (sent / failed / pending / none)"""
    row = repo_outbox.get_by_order_and_kind(order_id, "receipt")
    if row is None:
        return {"status": "none", "sent_at": None, "to_email": None, "last_error": None}
    return {
        "status": row["status"],
        "sent_at": row["sent_at"],
        "to_email": row["to_email"],
        "last_error": row["last_error"],
        "attempts": row["attempts"],
    }


def queue_shipped_email(order_id: int, carrier: str, tracking_no: str, background: bool = True) -> dict | None:
    """ส่งอีเมลแจ้งเลขพัสดุให้ผู้ซื้อหลังบันทึกการจัดส่ง (E5)"""
    if not config.SHIPPED_EMAIL_ENABLED:
        return None
    existing = repo_outbox.get_by_order_and_kind(order_id, "shipped")
    if existing is not None:
        return dict(existing)

    order = repo_orders.get_order(order_id)
    if order is None:
        return None
    buyer = repo_users.get_by_id(order["user_id"])
    if buyer is None or not validators.is_valid_email(buyer["email"] or ""):
        return None

    contact = settings_service.get_contact_info()
    shop_name = contact.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
    subject = f"คำสั่งซื้อ #{order_id} จัดส่งแล้ว ({carrier}: {tracking_no}) — {shop_name}"
    body_text = (
        f"สวัสดีคุณ {buyer['full_name']},\n\n"
        f"คำสั่งซื้อ #{order_id} ของคุณได้รับการจัดส่งเรียบร้อยแล้ว\n"
        f"- บริษัทขนส่ง: {carrier}\n"
        f"- เลขพัสดุ: {tracking_no}\n"
        f"- ที่อยู่ปลายทาง: {order['recipient_name']} ({order['recipient_phone']}) {order['shipping_address']}\n\n"
        f"ขอบคุณที่ใช้บริการ {shop_name}"
    )
    outbox_id = repo_outbox.create_outbox(
        kind="shipped",
        to_email=buyer["email"].strip().lower(),
        subject=subject,
        body_text=body_text,
        related_order_id=order_id,
    )

    def _job():
        ok = _deliver_outbox_item(outbox_id)
        if ok:
            try:
                notification_service.notify(
                    buyer["id"],
                    "ส่งเลขพัสดุทางอีเมลแล้ว",
                    f"ส่งข้อมูลเลขพัสดุ {tracking_no} ({carrier}) ไปที่อีเมลของคุณแล้ว",
                )
            except Exception:
                pass

    if background:
        threading.Thread(target=contextvars.copy_context().run, args=(_job,), daemon=True).start()
    else:
        _job()

    return dict(repo_outbox.get_outbox(outbox_id))


def send_low_stock_digest() -> dict | None:
    """ส่งอีเมลสรุปสินค้าสต็อกต่ำถึงเจ้าของร้านวันละไม่เกิน 1 ฉบับ (E6)"""
    if not config.LOW_STOCK_EMAIL_ENABLED:
        return None
    today_s = date.today().isoformat()
    if settings_service.get("last_low_stock_email") == today_s:
        return None

    threshold = settings_service.get_int("low_stock_threshold", 5)
    from database import repo_products
    low_prods = repo_products.list_low_stock(threshold)
    low_opts = repo_products.list_low_stock_options(threshold)
    if not low_prods and not low_opts:
        return None

    owner_row = repo_users.get_owner()
    to_email = (config.OWNER_EMAIL or (owner_row["email"] if owner_row else "")).strip().lower()
    if not validators.is_valid_email(to_email):
        return None

    lines = [f"สรุปรายการสินค้าสต็อกต่ำ (เกณฑ์ <= {threshold} ชิ้น) ประจำวันที่ {today_s}:", ""]
    for p in low_prods:
        lines.append(f"- สินค้า: {p['name']} (คงเหลือ {p['stock']} ชิ้น)")
    for o in low_opts:
        lines.append(f"- ตัวเลือก: {o['product_name']} ({o['option_type']}: {o['option_value']}) คงเหลือ {o['stock']} ชิ้น")

    outbox_id = repo_outbox.create_outbox(
        kind="low_stock",
        to_email=to_email,
        subject=f"[แจ้งเตือนสต็อกต่ำ] สรุปสินค้าใกล้หมดประจำวันที่ {today_s}",
        body_text="\n".join(lines),
    )
    if _deliver_outbox_item(outbox_id):
        from database import repo_settings
        repo_settings.set("last_low_stock_email", today_s)
    return dict(repo_outbox.get_outbox(outbox_id))


def retry_failed_outbox(max_attempts: int = 3) -> int:
    """ลองส่งอีเมลที่ค้างหรือส่งไม่สำเร็จซ้ำ (สูงสุด 3 ครั้ง)"""
    sent = 0
    for row in repo_outbox.list_retryable(max_attempts=max_attempts):
        if _deliver_outbox_item(row["id"]):
            sent += 1
    return sent


def send_receipt_email(order_id: int) -> dict:
    res = resend_receipt_email(order_id)
    return {
        **(res or {}),
        "status": (res or {}).get("status", "sent"),
        "message": "ส่งใบเสร็จ PDF ทางอีเมลเรียบร้อยแล้ว",
    }


def send_tracking_email(order_id: int, carrier: str, tracking_no: str) -> dict:
    res = queue_shipped_email(order_id, carrier, tracking_no, background=False)
    return {
        **(res or {}),
        "status": (res or {}).get("status", "sent"),
        "message": "ส่งอีเมลแจ้งเลขพัสดุเรียบร้อยแล้ว",
    }
