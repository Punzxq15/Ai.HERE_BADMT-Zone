"""
services/audit_service.py
บันทึกกิจกรรมสำคัญ (Audit Log) แบบเพิ่มอย่างเดียว (append-only)
ตัดข้อมูลความลับ (password, otp, token, secret, hash) ออกโดยอัตโนมัติก่อนบันทึก
เจ้าของร้านเท่านั้นที่ดูรายการได้ (action audit.view)
"""
import json
import math

from core import permissions
from core.session import Session
from database import repo_audit

_SENSITIVE_SUBSTRINGS = ("password", "pwd", "otp", "token", "secret", "hash", "api_key")


def _sanitize(obj):
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            key_lower = str(k).lower()
            if any(s in key_lower for s in _SENSITIVE_SUBSTRINGS):
                continue
            cleaned[str(k)] = _sanitize(v)
        return cleaned
    if isinstance(obj, (list, tuple)):
        return [_sanitize(x) for x in obj]
    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    return str(obj)[:300]


def log(action: str, target_type: str = None, target_id: int = None,
        detail=None, conn=None) -> int | None:
    """
    บันทึกกิจกรรมสำคัญลงตาราง audit_log
    หากไม่ได้ส่ง conn จะไม่โยน exception ออกไปขัดขวางการทำงานหลัก
    หากส่ง conn จะทำงานใน transaction เดียวกับการกระทำหลัก (rollback พร้อมกัน)
    """
    actor_id = Session.get_user_id()
    actor_role = Session.get_role()
    detail_str = None
    if detail is not None:
        cleaned = _sanitize(detail) if isinstance(detail, (dict, list, tuple)) else str(detail)[:300]
        detail_str = json.dumps(cleaned, ensure_ascii=False)
    try:
        return repo_audit.insert_log(
            actor_id=actor_id,
            actor_role=actor_role,
            action=str(action),
            target_type=target_type,
            target_id=int(target_id) if target_id is not None else None,
            detail=detail_str,
            conn=conn,
        )
    except Exception:
        if conn is not None:
            raise
        return None


def list_logs(filters: dict = None, page: int = 1, page_size: int = 30) -> dict:
    """ดูรายการ Audit Log แบ่งหน้า (เฉพาะเจ้าของร้าน)"""
    permissions.require(permissions.AUDIT_VIEW)
    f = dict(filters or {})
    try:
        page = max(1, int(page))
        page_size = min(100, max(1, int(page_size)))
    except (TypeError, ValueError):
        page, page_size = 1, 30

    actor_id = f.get("actor_id")
    action = (f.get("action") or "").strip() or None
    date_from = (f.get("date_from") or "").strip() or None
    date_to = (f.get("date_to") or "").strip() or None

    total = repo_audit.count_logs(actor_id=actor_id, action=action, date_from=date_from, date_to=date_to)
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    rows = repo_audit.list_logs(
        actor_id=actor_id, action=action, date_from=date_from, date_to=date_to,
        limit=page_size, offset=(page - 1) * page_size,
    )
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }

_orig_list_logs = list_logs


def list_logs(filters=None, page: int = 1, page_size: int = 30, limit: int = None):
    if limit is not None:
        res = _orig_list_logs(filters=filters if isinstance(filters, dict) else None, page=1, page_size=limit)
        return res.get("items", [])
    if isinstance(filters, int):
        res = _orig_list_logs(filters=None, page=1, page_size=filters)
        return res.get("items", [])
    return _orig_list_logs(filters=filters, page=page, page_size=page_size)
