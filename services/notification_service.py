"""
services/notification_service.py
การแจ้งเตือน: ฟังก์ชันสร้าง (notify, notify_staff) ใช้ภายใน service อื่น (order/payment/shipping/chat ฯลฯ)
ฟังก์ชันอ่าน/ทำเครื่องหมายอ่านแล้ว (list_my, unread_count, mark_read, mark_all_read) ใช้ได้ทุก role
กับ "ของตัวเอง" เท่านั้น
รองรับการกดดูแบบคร่าวๆ และนำทางไปยังหน้าที่เกี่ยวข้อง พร้อมเก็บสูงสุด 10 รายการล่าสุดสำหรับ Buyer (ข้อ 14)

ข้อตกลง: ไฟล์นี้ห้าม import service อื่น (เป็นใบล่างสุด กันการ import วนกัน)
"""
import json
import re

from core import permissions
from core.constants import ROLE_ADMIN, ROLE_OWNER
from core.session import Session
from database import repo_notifications

MAX_TITLE = 100
MAX_MESSAGE = 500
_ORDER_EXPLICIT_RE = re.compile(r"(?:คำสั่งซื้อ|ออเดอร์|order)\s*#?(\d+)", re.IGNORECASE)
_ORDER_ID_RE = re.compile(r"#(\d+)")


def _clean(title, message):
    title = str(title or "").strip()
    message = str(message or "").strip()
    if not title:
        raise ValueError("หัวข้อการแจ้งเตือนต้องไม่ว่าง")
    return title[:MAX_TITLE], message[:MAX_MESSAGE]


def resolve_notification_target(item: dict, role: str | None = None) -> dict:
    """
    วิเคราะห์ว่าการแจ้งเตือนรายการนี้ควรพาไปหน้าใดเมื่อผู้ใช้กดเข้าไปดู (ข้อ 14)
    คืน {"route": str, "params": dict, "button_label": str}
    """
    user_role = role or Session.get_role()
    is_staff = user_role in (ROLE_ADMIN, ROLE_OWNER)

    raw_route = item.get("target_route")
    raw_params = item.get("target_params")
    if raw_route:
        params = {}
        if isinstance(raw_params, dict):
            params = raw_params
        elif raw_params:
            try:
                params = json.loads(raw_params)
            except Exception:
                params = {}
        return {"route": raw_route, "params": params, "button_label": "เปิดหน้าที่เกี่ยวข้อง ›"}

    title = str(item.get("title") or "")
    msg = str(item.get("message") or "")
    combined = f"{title} {msg}"

    match = _ORDER_EXPLICIT_RE.search(combined) or _ORDER_ID_RE.search(combined)
    order_id = int(match.group(1)) if match else None

    if is_staff:
        if "สลิป" in combined:
            return {"route": "admin_payments", "params": {"order_id": order_id} if order_id else {}, "button_label": "ไปหน้าตรวจสลิป ›"}
        if order_id is not None:
            return {"route": "admin_order_detail", "params": {"order_id": order_id}, "button_label": f"ดูออเดอร์ #{order_id} ›"}
        if "สต็อก" in combined or "สินค้า" in combined:
            return {"route": "admin_products", "params": {}, "button_label": "ไปหน้าจัดการสินค้า ›"}
        if "แชท" in combined or "ข้อความ" in combined:
            return {"route": "admin_chat", "params": {}, "button_label": "ไปหน้าแชทลูกค้า ›"}
        return {"route": "admin_orders", "params": {}, "button_label": "ไปหน้ารายการออเดอร์ ›"}

    # สำหรับผู้ซื้อ (Buyer)
    if order_id is not None:
        if any(k in combined for k in ("กรุณาชำระเงิน", "แนบสลิป", "สลิปไม่ผ่าน", "รอชำระเงิน")):
            return {
                "route": "payment",
                "params": {"order_id": order_id},
                "button_label": f"ไปหน้าชำระเงิน คำสั่งซื้อ #{order_id} ›",
            }
        return {
            "route": "order_detail",
            "params": {"order_id": order_id},
            "button_label": f"ดูคำสั่งซื้อ #{order_id} ›",
        }

    if "คูปอง" in combined or "ส่วนลด" in combined:
        return {"route": "home", "params": {}, "button_label": "ไปดูคูปองหน้าแรก ›"}
    if "แชท" in combined or "ข้อความ" in combined:
        return {"route": "chat", "params": {}, "button_label": "เปิดหน้าแชทร้านค้า ›"}
    return {"route": "orders", "params": {}, "button_label": "ไปหน้าคำสั่งซื้อของฉัน ›"}


def _enrich(row, role: str | None = None) -> dict:
    d = dict(row)
    target = resolve_notification_target(d, role=role)
    d["target_route"] = target["route"]
    d["target_params"] = target["params"]
    d["action_label"] = target["button_label"]
    return d


def notify(user_id: int, title: str, message: str = "", conn=None,
           target_route: str = None, target_params: dict = None) -> int:
    """
    แจ้งเตือนผู้ใช้ 1 คน คืน id — สำหรับ service อื่นเรียกภายในระบบ (ไม่ตรวจสิทธิ์ผู้เรียก)
    ส่ง conn เมื่อเรียกจากใน transaction (เช่น ตอนสร้างออเดอร์) เพื่อให้สำเร็จ/ย้อนกลับพร้อมกัน
    """
    title, message = _clean(title, message)
    params_str = json.dumps(target_params, ensure_ascii=False) if isinstance(target_params, dict) else target_params
    return repo_notifications.create(
        user_id, title, message, target_route=target_route, target_params=params_str, conn=conn
    )


def notify_staff(title: str, message: str = "", conn=None,
                 target_route: str = None, target_params: dict = None) -> int:
    """แจ้งเตือน admin + owner ที่ยังไม่ถูกระงับทุกคน คืนจำนวนคนที่ได้รับ"""
    title, message = _clean(title, message)
    params_str = json.dumps(target_params, ensure_ascii=False) if isinstance(target_params, dict) else target_params
    return repo_notifications.create_for_staff(
        title, message, target_route=target_route, target_params=params_str, conn=conn
    )


def list_my(limit: int = 50, unread_only: bool = False) -> list[dict]:
    """การแจ้งเตือนของผู้ใช้ที่ล็อกอินอยู่ ใหม่สุดก่อน (สำหรับ Buyer เก็บและแสดงไม่เกิน 10 ครั้งล่าสุด)"""
    user_id = permissions.require_login()
    role = Session.get_role()
    limit = min(200, max(1, int(limit)))
    rows = repo_notifications.list(user_id, limit=limit, unread_only=bool(unread_only))
    return [_enrich(r, role=role) for r in rows]


def unread_count() -> int:
    """จำนวนที่ยังไม่อ่านของผู้ใช้ที่ล็อกอินอยู่ (จุดแดงบน navbar)"""
    return repo_notifications.count_unread(permissions.require_login())


def mark_read(notification_id: int) -> bool:
    """ทำเครื่องหมายอ่านแล้ว 1 รายการ — คืน False ถ้าไม่ใช่ของผู้ใช้นี้/ไม่พบ (แก้ของคนอื่นไม่ได้)"""
    return repo_notifications.mark_read(notification_id, user_id=permissions.require_login())


def mark_all_read() -> int:
    """ทำเครื่องหมายอ่านทั้งหมดของตัวเอง คืนจำนวนที่เปลี่ยน"""
    return repo_notifications.mark_all_read(permissions.require_login())
