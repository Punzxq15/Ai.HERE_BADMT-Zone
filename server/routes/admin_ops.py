"""
server/routes/admin_ops.py
API สำหรับหลังร้าน: Dashboard, จัดการผู้ใช้/แอดมิน, รายจ่ายร้าน, ส่งออกรายงาน .xlsx,
สำรอง/กู้คืนฐานข้อมูล, ข้อความด่วนจากแอดมิน, Audit Log และการอัปโหลดรูปภาพผ่าน image_utils
"""
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

import config
from core import permissions
from core.session import Session
from server.serializers import to_jsonable
from services import (
    audit_service,
    auth_service,
    chat_service,
    contact_service,
    expense_service,
    export_service,
    notification_service,
    order_service,
    payment_service,
    product_service,
    settings_service,
    staff_service,
)
from utils import backup, image_utils

router = APIRouter(prefix="/api", tags=["admin_ops"])


# ==========================================
# Dashboard & Badges
# ==========================================

@router.get("/admin/dashboard")
def get_admin_dashboard(days: int = 7):
    stats = order_service.get_dashboard_stats(days=days)
    low_stock = product_service.get_low_stock_products()
    return to_jsonable({
        **stats,
        "low_stock": low_stock,
        "can_view_revenue": permissions.can(Session.get_role(), permissions.DASHBOARD_REVENUE),
    })


@router.get("/admin/badges")
def get_admin_badges():
    permissions.require(permissions.DASHBOARD_VIEW)
    return to_jsonable({
        "pending_slips": len(payment_service.list_pending_payments()),
        "unread_chat": chat_service.unread_count(),
        "unread_notifications": notification_service.unread_count(),
    })


# ==========================================
# จัดการผู้ใช้ & แอดมิน (Owner Only)
# ==========================================

@router.get("/admin/users")
def admin_list_users(role: str | None = None, search: str | None = None):
    role_filter = None if role in (None, "", "all") else role
    users = auth_service.list_users(role=role_filter, search=search)
    promotable = staff_service.list_promotable_buyers()
    return to_jsonable({
        "users": users,
        "promotable_buyers": promotable,
        "current_user_id": Session.get_user_id(),
    })


@router.get("/admin/users/{user_id}")
def admin_get_user_detail(user_id: int):
    return to_jsonable(staff_service.get_user_full_detail(user_id))


@router.post("/admin/users/staff")
def admin_create_staff(payload: dict):
    created = auth_service.create_staff(
        username=payload.get("username") or "",
        email=payload.get("email") or "",
        password=payload.get("password") or "",
        full_name=payload.get("full_name") or "",
        phone=payload.get("phone") or "",
    )
    return to_jsonable(created)


@router.post("/admin/users/assign-admin")
def admin_assign_by_email(payload: dict):
    pw = payload.get("password") or ""
    confirm = payload.get("confirm_password")
    if confirm is None:
        confirm = pw
    res = staff_service.assign_admin_by_email(
        email=payload.get("email") or "",
        password=pw,
        confirm_password=confirm,
        full_name=payload.get("full_name"),
        phone=payload.get("phone"),
        username=payload.get("username"),
    )
    return to_jsonable(res)


@router.post("/admin/users/{user_id}/active")
def admin_set_user_active(user_id: int, payload: dict):
    return to_jsonable(auth_service.set_user_active(user_id, bool(payload.get("active", True))))


@router.post("/admin/users/{user_id}/reset-password")
def admin_reset_user_password(user_id: int, payload: dict):
    pw = payload.get("temp_password") or payload.get("password") or ""
    confirm = payload.get("confirm_password")
    if confirm is None:
        confirm = pw
    must_change = bool(payload.get("must_change", True))
    return to_jsonable(
        staff_service.reset_user_password(
            user_id=user_id,
            temp_password=pw,
            confirm_password=confirm,
            must_change=must_change,
        )
    )


@router.post("/admin/users/{user_id}/revoke-sessions")
def admin_revoke_user_sessions(user_id: int):
    count = staff_service.revoke_sessions(user_id)
    return {"ok": True, "revoked_count": count}


# ==========================================
# รายจ่ายร้าน (Expenses — Owner Only)
# ==========================================

@router.get("/admin/expenses")
def admin_list_expenses(date_from: str | None = None, date_to: str | None = None):
    items = expense_service.list_expenses(date_from=date_from, date_to=date_to)
    total = expense_service.sum_expenses(date_from=date_from, date_to=date_to)
    return to_jsonable({"items": items, "total": total})


@router.post("/admin/expenses")
def admin_add_expense(payload: dict):
    spent_on = payload.get("spent_on") or payload.get("expense_date") or ""
    category = payload.get("category") or "ทั่วไป"
    amount = payload.get("amount", 0)
    note = payload.get("note") or payload.get("title") or ""
    return to_jsonable(expense_service.add_expense(spent_on, category, amount, note))


@router.put("/admin/expenses/{expense_id}")
def admin_update_expense(expense_id: int, payload: dict):
    spent_on = payload.get("spent_on") or payload.get("expense_date") or ""
    category = payload.get("category") or "ทั่วไป"
    amount = payload.get("amount", 0)
    note = payload.get("note") or payload.get("title") or ""
    return to_jsonable(expense_service.update_expense(expense_id, spent_on, category, amount, note))


@router.delete("/admin/expenses/{expense_id}")
def admin_delete_expense(expense_id: int):
    ok = expense_service.delete_expense(expense_id)
    return {"ok": bool(ok)}


# ==========================================
# ส่งออกรายงาน Excel (.xlsx) & Google Sheets
# ==========================================

@router.post("/admin/export/xlsx")
def admin_export_xlsx(payload: dict):
    start_date = payload.get("start_date") or ""
    end_date = payload.get("end_date") or ""
    res = export_service.export_report_xlsx(start_date, end_date)
    fname = Path(res["path"]).name
    return to_jsonable({
        **res,
        "filename": fname,
        "download_url": f"/api/admin/export/download?name={fname}",
    })


@router.get("/admin/export/download")
def admin_download_export_xlsx(
    name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    permissions.require_any(permissions.BACKUP_MANAGE, permissions.DASHBOARD_REVENUE)
    if name:
        clean_name = Path(name).name
        candidates = [
            Path(config.EXPORTS_DIR) / clean_name,
            Path(config.MONTHLY_EXPORTS_DIR) / clean_name,
        ]
        custom_dir = (settings_service.get("auto_export_dir") or "").strip()
        if custom_dir:
            candidates.append(Path(custom_dir) / clean_name)
        target = next((p.resolve() for p in candidates if p.is_file()), None)
        if target is None:
            raise ValueError("ไม่พบไฟล์รายงานที่ต้องการดาวน์โหลด")
    elif start_date and end_date:
        target = export_service.export_range(start_date, end_date, require_auth=True)
    else:
        raise ValueError("กรุณาระบุชื่อไฟล์หรือช่วงวันที่สำหรับดาวน์โหลดรายงาน")

    return FileResponse(
        path=str(target),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{target.name}"'},
    )


@router.get("/admin/export/files")
def admin_list_exported_files():
    return to_jsonable(export_service.list_exported_files())


@router.post("/admin/export/auto-config")
def admin_configure_auto_export(payload: dict):
    enabled = bool(payload.get("enabled", True))
    folder_path = payload.get("folder_path") or payload.get("auto_export_dir") or ""
    return to_jsonable(export_service.configure_auto_monthly_export(enabled, folder_path))


@router.post("/admin/export/monthly-now")
def admin_trigger_monthly_export():
    permissions.require(permissions.BACKUP_MANAGE)
    res = export_service.auto_export_previous_month(force=True)
    if res.get("path"):
        res["filename"] = Path(res["path"]).name
        res["download_url"] = f"/api/admin/export/download?name={res['filename']}"
    return to_jsonable(res)


@router.post("/admin/export/google-sheets")
def admin_sync_google_sheets(payload: dict):
    return to_jsonable(
        export_service.sync_to_google_sheets(
            start_date=payload.get("start_date") or "",
            end_date=payload.get("end_date") or "",
            include_personal=bool(payload.get("include_personal", False)),
        )
    )


# ==========================================
# สำรองและกู้คืนฐานข้อมูล (Backups — Owner Only)
# ==========================================

@router.get("/admin/backups")
def admin_list_backups():
    permissions.require(permissions.BACKUP_MANAGE)
    return to_jsonable(backup.list_backups())


@router.post("/admin/backups")
def admin_create_backup():
    permissions.require(permissions.BACKUP_MANAGE)
    dest = backup.backup_db()
    audit_service.log("backup.create", "database", None, {"file": dest.name})
    return to_jsonable({
        "name": dest.name,
        "path": dest.as_posix(),
        "size": dest.stat().st_size,
        "backups": backup.list_backups(),
    })


@router.post("/admin/backups/restore")
def admin_restore_backup(payload: dict):
    permissions.require(permissions.BACKUP_MANAGE)
    raw_name = payload.get("name") or payload.get("path") or ""
    if not raw_name:
        raise ValueError("กรุณาเลือกไฟล์สำรองที่ต้องการกู้คืน")
    clean_name = Path(str(raw_name)).name
    target = (Path(config.BACKUP_DIR) / clean_name).resolve()
    if Path(config.BACKUP_DIR).resolve() not in target.parents or not target.is_file():
        raise ValueError("ไม่พบไฟล์สำรองในโฟลเดอร์สำรองของระบบ")
    backup.restore_backup(target)
    audit_service.log("backup.restore", "database", None, {"file": target.name})
    return to_jsonable({
        "ok": True,
        "restored": target.name,
        "message": f"กู้คืนฐานข้อมูลจาก {target.name} เรียบร้อยแล้ว",
        "backups": backup.list_backups(),
    })


@router.get("/admin/backups/{backup_name}/download")
def admin_download_backup(backup_name: str):
    permissions.require(permissions.BACKUP_MANAGE)
    clean_name = Path(backup_name).name
    target = (Path(config.BACKUP_DIR) / clean_name).resolve()
    if Path(config.BACKUP_DIR).resolve() not in target.parents or not target.is_file():
        raise ValueError("ไม่พบไฟล์สำรองที่เลือก")
    return FileResponse(
        path=str(target),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{target.name}"'},
    )


# ==========================================
# ข้อความด่วนจากแอดมิน & Audit Log
# ==========================================

@router.get("/admin/staff-messages")
def admin_list_staff_messages(limit: int = 50):
    return to_jsonable(contact_service.list_staff_messages_for_owner(limit=limit))


@router.get("/admin/audit-logs")
def admin_list_audit_logs(
    actor_id: int | None = None,
    action: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 30,
):
    filters = {
        "actor_id": actor_id,
        "action": action,
        "date_from": date_from,
        "date_to": date_to,
    }
    return to_jsonable(audit_service.list_logs(filters=filters, page=page, page_size=page_size))


# ==========================================
# อัปโหลดรูปภาพ (ผ่าน image_utils.save_upload)
# ==========================================

_UPLOAD_TARGETS = {
    "product": (config.PRODUCT_IMAGES_DIR, "product", (permissions.PRODUCT_CREATE, permissions.PRODUCT_EDIT), config.UPLOAD_MAX_SIDE),
    "category": (config.CATEGORY_IMAGES_DIR, "category", (permissions.CATEGORY_MANAGE,), config.UPLOAD_MAX_SIDE),
    "brand": (config.CATEGORY_IMAGES_DIR, "brand", (permissions.BRAND_MANAGE,), config.UPLOAD_MAX_SIDE),
    "banner": (config.BANNER_IMAGES_DIR, "banner", (permissions.BANNER_MANAGE,), config.UPLOAD_MAX_SIDE),
    "login_banner": (config.LOGIN_BANNERS_DIR, "login_banner", (permissions.SETTINGS_MANAGE,), 1000),
    "logo": (config.IMAGES_DIR, "logo", (permissions.SETTINGS_MANAGE,), config.LOGO_MAX_SIDE),
    "avatar": (config.USER_IMAGES_DIR, "user", (), config.UPLOAD_MAX_SIDE),
    "slip": (config.SLIPS_DIR, "slip", (permissions.ORDER_OWN,), config.UPLOAD_MAX_SIDE),
    "chat": (config.CHAT_IMAGES_DIR, "chat", (), config.UPLOAD_MAX_SIDE),
}


@router.post("/uploads/image")
def upload_image(
    file: UploadFile = File(...),
    target: str = Form("product"),
):
    target_key = (target or "product").strip().lower()
    if target_key not in _UPLOAD_TARGETS:
        raise ValueError("ประเภทการอัปโหลดรูปภาพไม่ถูกต้อง")

    dest_dir, prefix, req_actions, max_side = _UPLOAD_TARGETS[target_key]
    if req_actions:
        permissions.require_any(*req_actions)
    else:
        permissions.require_login()

    orig_name = file.filename or "upload.jpg"
    suffix = Path(orig_name).suffix.lower()
    raw = file.file.read()
    if len(raw) > config.MAX_UPLOAD_BYTES:
        raise ValueError(f"ไฟล์ใหญ่เกินไป (ไม่เกิน {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)
    try:
        rel_path = image_utils.save_upload(tmp_path, dest_dir, prefix, max_side=max_side)
        return {
            "path": rel_path,
            "url": "/" + rel_path.lstrip("/"),
        }
    finally:
        tmp_path.unlink(missing_ok=True)
