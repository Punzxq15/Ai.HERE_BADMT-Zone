"""
services/shipping_service.py
จัดส่ง: แอดมิน/เจ้าของกดอัปเดตเอง (ระบบไม่ตามขนส่งอัตโนมัติ)
    paid -> shipped      ship_order(order_id, carrier, tracking_no) / ship_order_and_notify(...)
    shipped -> completed mark_delivered(order_id)
"""
import re

from core import permissions
from core.constants import (
    CARRIERS, ORDER_STATUS_LABELS, ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, SHIPMENT_STATUS_LABELS,
    SHIPMENT_STATUS_SHIPPED,
)
from database import repo_orders, repo_shipping
from database.db import transaction
from services import notification_service, order_service

_TRACKING_PATTERN = re.compile(r"^[A-Za-z0-9-]{4,40}$")


def _clean_shipping_fields(carrier, tracking_no):
    carrier = str(carrier or "").strip()
    if carrier not in CARRIERS:
        raise ValueError("กรุณาเลือกขนส่งจากรายการ")
    tracking_no = str(tracking_no or "").strip().replace(" ", "")
    if not tracking_no:
        raise ValueError("กรุณากรอกเลขพัสดุ")
    if not _TRACKING_PATTERN.match(tracking_no):
        raise ValueError("เลขพัสดุต้องเป็นตัวอักษรอังกฤษ ตัวเลข หรือ - ยาว 4-40 ตัว")
    return carrier, tracking_no


def _get_order(order_id, conn=None):
    order = repo_orders.get_order(order_id, conn=conn)
    if order is None:
        raise ValueError("ไม่พบคำสั่งซื้อ")
    return order


def ship_order(order_id: int, carrier: str, tracking_no: str) -> dict:
    permissions.require(permissions.SHIPMENT_UPDATE)
    staff_id = permissions.require_login()
    carrier, tracking_no = _clean_shipping_fields(carrier, tracking_no)

    with transaction() as conn:
        order = _get_order(order_id, conn)
        if order["status"] != ORDER_STATUS_PAID:
            label = ORDER_STATUS_LABELS.get(order["status"], order["status"])
            raise ValueError(f"จัดส่งได้เฉพาะคำสั่งซื้อที่ชำระเงินแล้ว (ตอนนี้: {label})")
        order_service.apply_status_change(conn, order_id, ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED,
                                          f"จัดส่งโดย {carrier} เลขพัสดุ {tracking_no}", staff_id)
        if not repo_shipping.update(order_id, carrier, tracking_no, SHIPMENT_STATUS_SHIPPED, conn=conn):
            repo_shipping.create(order_id, carrier, tracking_no, SHIPMENT_STATUS_SHIPPED, conn=conn)
        notification_service.notify(
            order["user_id"], "จัดส่งสินค้าแล้ว",
            f"คำสั่งซื้อ #{order_id} จัดส่งโดย {carrier} เลขพัสดุ {tracking_no}", conn=conn)
        return order_service.load_order_detail(order_id, conn=conn)


def ship_order_and_notify(order_id: int, carrier: str, tracking_no: str, background: bool = True) -> dict:
    """บันทึกการจัดส่งและส่งอีเมลแจ้งเลขพัสดุให้ลูกค้าหลัง commit สำเร็จ (E5)"""
    detail = ship_order(order_id, carrier, tracking_no)
    try:
        from services import email_outbox_service
        sh = detail.get("shipment") or {}
        email_outbox_service.queue_shipped_email(
            order_id, sh.get("carrier") or carrier, sh.get("tracking_no") or tracking_no, background=background
        )
    except Exception:
        pass
    return detail


def update_tracking(order_id: int, carrier: str, tracking_no: str) -> dict:
    permissions.require(permissions.SHIPMENT_UPDATE)
    staff_id = permissions.require_login()
    carrier, tracking_no = _clean_shipping_fields(carrier, tracking_no)

    with transaction() as conn:
        order = _get_order(order_id, conn)
        if order["status"] != ORDER_STATUS_SHIPPED:
            raise ValueError("แก้เลขพัสดุได้เฉพาะคำสั่งซื้อที่จัดส่งแล้วและยังไม่เสร็จสิ้น")
        repo_shipping.update(order_id, carrier, tracking_no, conn=conn)
        repo_orders.add_status_log(order_id, ORDER_STATUS_SHIPPED,
                                   f"แก้ไขข้อมูลพัสดุ: {carrier} เลขพัสดุ {tracking_no}", staff_id, conn=conn)
        notification_service.notify(
            order["user_id"], "อัปเดตเลขพัสดุ",
            f"คำสั่งซื้อ #{order_id} ขนส่ง {carrier} เลขพัสดุใหม่ {tracking_no}", conn=conn)
        return order_service.load_order_detail(order_id, conn=conn)


def mark_delivered(order_id: int) -> dict:
    permissions.require(permissions.SHIPMENT_UPDATE)
    staff_id = permissions.require_login()
    with transaction() as conn:
        order = _get_order(order_id, conn)
        if order["status"] != ORDER_STATUS_SHIPPED:
            raise ValueError("ยืนยันส่งถึงได้เฉพาะคำสั่งซื้อที่จัดส่งแล้ว")
        order_service.complete_delivery(conn, order, staff_id, by_buyer=False)
        return order_service.load_order_detail(order_id, conn=conn)


def get_shipment(order_id: int):
    order_service.authorize_view(_get_order(order_id))
    row = repo_shipping.get_by_order(order_id)
    if row is None:
        return None
    d = dict(row)
    d["status_label"] = SHIPMENT_STATUS_LABELS.get(d["status"], d["status"])
    return d
