"""
server/routes/reviews_notifications_chat.py
API สำหรับรีวิวสินค้า (พร้อมอัปโหลดรูป/วิดีโอ 0–5 ไฟล์) การแจ้งเตือน และระบบแชท (รองรับส่งรูปภาพทั้งลูกค้าและแอดมิน/เจ้าของ)
"""
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile

import config
from core import permissions
from core.session import Session
from server import deps
from server.serializers import to_jsonable
from services import chat_service, notification_service, order_service, review_service, settings_service
from utils import image_utils

router = APIRouter(prefix="/api", tags=["reviews_notifications_chat"])


# ==========================================
# รีวิวสินค้า (Reviews)
# ==========================================

@router.get("/reviews/can-review")
def can_review(product_id: int, order_id: int):
    uid = deps.require_user_id()
    allowed = review_service.can_review(uid, product_id, order_id)
    order = order_service.get_order_detail(order_id)
    return to_jsonable({
        "can_review": bool(allowed),
        "max_comment_length": review_service.MAX_COMMENT_LENGTH,
        "max_review_files": config.MAX_REVIEW_FILES,
        "max_image_bytes": config.MAX_REVIEW_IMAGE_BYTES,
        "max_video_bytes": config.MAX_REVIEW_VIDEO_BYTES,
        "order": order,
    })


@router.post("/reviews/skip")
def skip_review(payload: dict):
    uid = deps.require_user_id()
    raw_oid = payload.get("order_id")
    raw_pid = payload.get("product_id")
    try:
        order_id = int(raw_oid)
        product_id = int(raw_pid) if raw_pid not in (None, "") else None
    except (TypeError, ValueError):
        raise ValueError("ข้อมูลคำสั่งซื้อไม่ถูกต้อง") from None
    res = review_service.skip_review(uid, order_id=order_id, product_id=product_id)
    return to_jsonable(res)


@router.post("/reviews")
async def add_review(request: Request):
    uid = deps.require_user_id()
    content_type = (request.headers.get("content-type") or "").lower()
    files_payload = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        raw_pid = form.get("product_id")
        raw_oid = form.get("order_id")
        raw_rating = form.get("rating", 5)
        comment = form.get("comment")
        raw_files = list(form.getlist("files") or []) + list(form.getlist("media") or [])
        for f in raw_files:
            if hasattr(f, "filename") and f.filename:
                data = await f.read()
                files_payload.append({
                    "filename": f.filename,
                    "content_type": getattr(f, "content_type", "") or "",
                    "data": data,
                })
    else:
        payload = await request.json()
        raw_pid = payload.get("product_id")
        raw_oid = payload.get("order_id")
        raw_rating = payload.get("rating", 5)
        comment = payload.get("comment")
        files_payload = payload.get("files") or []

    try:
        product_id = int(raw_pid)
        order_id = int(raw_oid)
        rating = int(raw_rating)
    except (TypeError, ValueError):
        raise ValueError("ข้อมูลรีวิวไม่ครบถ้วนหรือไม่ถูกต้อง") from None

    res = review_service.add_review(
        user_id=uid,
        product_id=product_id,
        order_id=order_id,
        rating=rating,
        comment=comment,
        media_files=files_payload,
    )
    return to_jsonable(res)


# ==========================================
# การแจ้งเตือน (Notifications)
# ==========================================

@router.get("/notifications")
def list_notifications(limit: int = 50, unread_only: bool = False):
    items = notification_service.list_my(limit=limit, unread_only=unread_only)
    unread = notification_service.unread_count()
    return to_jsonable({"items": items, "unread_count": unread})


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int):
    ok = notification_service.mark_read(notification_id)
    return {"ok": bool(ok), "unread_count": notification_service.unread_count()}


@router.post("/notifications/read-all")
def mark_all_notifications_read():
    count = notification_service.mark_all_read()
    return {"ok": True, "marked_count": count, "unread_count": 0}


# ==========================================
# แชทลูกค้า & แอดมิน & ผู้ช่วย AI (Chat)
# ==========================================

@router.get("/chat/quick-replies")
def get_quick_replies():
    return to_jsonable(chat_service.get_quick_replies())


@router.post("/chat/upload-image")
def upload_chat_image(file: UploadFile = File(...)):
    uid = permissions.require_login()
    orig_name = file.filename or "chat.jpg"
    suffix = Path(orig_name).suffix.lower()
    raw = file.file.read()
    if len(raw) > config.MAX_UPLOAD_BYTES:
        raise ValueError(f"ไฟล์รูปภาพใหญ่เกินไป (ไม่เกิน {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB)")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)
    try:
        rel_path = image_utils.save_upload(
            tmp_path,
            config.CHAT_IMAGES_DIR,
            f"chat_{uid}",
            max_side=config.UPLOAD_MAX_SIDE,
        )
        return {
            "path": rel_path,
            "url": "/" + rel_path.lstrip("/"),
        }
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/chat/messages")
def get_chat_messages(
    customer_id: int | None = None,
    after_id: int = 0,
    limit: int | None = None,
    mark_read: bool = True,
):
    uid = deps.require_user_id()
    target_cid = int(customer_id) if customer_id is not None else uid
    messages = chat_service.get_messages(
        customer_id=target_cid,
        after_id=after_id,
        limit=limit,
        mark_read=mark_read,
    )
    return to_jsonable({
        "messages": messages,
        "should_ai_reply": chat_service.should_ai_reply(),
        "ai_enabled": settings_service.get_bool("ai_enabled", True),
        "unread_count": chat_service.unread_count(),
    })


@router.post("/chat/messages")
def buyer_send_message(payload: dict):
    uid = deps.require_user_id()
    text = payload.get("text") or payload.get("message") or ""
    image_path = payload.get("image_path")
    force_ai = bool(payload.get("force_ai", False))
    background = bool(payload.get("background", False))
    res = chat_service.send_message(
        uid,
        text,
        background=background,
        force_ai=force_ai,
        image_path=image_path,
    )
    return to_jsonable(res)


@router.post("/chat/quick-reply")
def buyer_quick_reply(payload: dict):
    uid = deps.require_user_id()
    reply_id = payload.get("reply_id") or payload.get("id") or ""
    return to_jsonable(chat_service.answer_quick_reply(uid, reply_id))


@router.post("/chat/recommend-rackets")
def buyer_recommend_rackets_in_chat(payload: dict):
    uid = deps.require_user_id()
    res = chat_service.recommend_from_form(
        customer_id=uid,
        level=payload.get("level") or "Beginner",
        style=payload.get("style") or "attack",
        budget=payload.get("budget") if payload.get("budget") not in (None, "") else None,
        flex=payload.get("flex") or None,
        balance=payload.get("balance") or None,
        weight_class=payload.get("weight_class") or None,
        post_to_chat=bool(payload.get("post_to_chat", True)),
    )
    return to_jsonable(res)


@router.get("/admin/chat/threads")
def admin_list_chat_threads():
    threads = chat_service.list_threads()
    return to_jsonable({
        "threads": threads,
        "unread_count": chat_service.unread_count(),
        "should_ai_reply": chat_service.should_ai_reply(),
    })


@router.post("/admin/chat/reply")
def admin_reply_chat(payload: dict):
    customer_id = int(payload.get("customer_id"))
    text = payload.get("text") or payload.get("message") or ""
    image_path = payload.get("image_path")
    msg = chat_service.staff_reply(customer_id, text, image_path=image_path)
    return to_jsonable({"message": msg})
