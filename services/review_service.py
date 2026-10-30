"""
services/review_service.py
รีวิวสินค้า: เขียนได้เฉพาะผู้ซื้อที่ออเดอร์ "สำเร็จ (completed)" และมีสินค้านั้นในออเดอร์
ให้ 1–5 ดาว หนึ่งครั้งต่อ (ผู้ใช้, สินค้า, ออเดอร์) พร้อมแนบรูป/วิดีโอรวมกันได้ 0–5 ไฟล์
หรือเลือก "ไม่รีวิว" เพื่อนำออกจากช่องรอรีวิวโดยไม่กระทบคะแนนสินค้า
"""
import io
import math
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image, UnidentifiedImageError

import config
from core import permissions
from core.constants import ORDER_STATUS_COMPLETED
from database import repo_orders, repo_reviews
from database.db import transaction

MAX_COMMENT_LENGTH = 1000


def _reason_cannot_review(user_id: int, product_id: int, order_id: int):
    """ข้อความไทยบอกเหตุผลที่รีวิวไม่ได้ — รีวิวได้ = None"""
    order = repo_orders.get_order(order_id)
    if order is None or order["user_id"] != user_id:
        return "ไม่พบคำสั่งซื้อนี้"
    if order["status"] != ORDER_STATUS_COMPLETED:
        return "รีวิวได้เมื่อคำสั่งซื้อสำเร็จแล้วเท่านั้น"
    if product_id not in {i["product_id"] for i in repo_orders.list_items(order_id)}:
        return "ไม่มีสินค้านี้ในคำสั่งซื้อ"
    if repo_reviews.exists(user_id, product_id, order_id):
        return "คุณรีวิวสินค้านี้ในคำสั่งซื้อนี้ไปแล้ว"
    if repo_reviews.is_skipped(user_id, product_id, order_id):
        return "คุณเลือกไม่รีวิวสินค้านี้ในคำสั่งซื้อนี้ไปแล้ว"
    return None


def can_review(user_id: int, product_id: int, order_id: int) -> bool:
    """ผู้ซื้อคนนี้รีวิวสินค้านี้ในออเดอร์นี้ได้หรือไม่ (ออเดอร์ของตัวเอง + completed + มีสินค้า + ยังไม่เคยรีวิว/ข้ามรีวิว)"""
    permissions.require_self(permissions.REVIEW_WRITE, user_id)
    return _reason_cannot_review(user_id, product_id, order_id) is None


def skip_review(user_id: int, order_id: int, product_id: int | None = None) -> dict:
    """
    ผู้ซื้อเลือก "ไม่รีวิว" สินค้าในออเดอร์ที่สำเร็จแล้ว:
    - ถ้าระบุ product_id จะข้ามเฉพาะสินค้านั้น
    - ถ้าไม่ระบุ product_id จะข้ามสินค้าทุกชิ้นที่ยังไม่ได้รีวิวในออเดอร์นั้น (เอาออเดอร์ออกจากช่องรอรีวิวทันที)
    """
    permissions.require_self(permissions.REVIEW_WRITE, user_id)
    order = repo_orders.get_order(order_id)
    if order is None or order["user_id"] != user_id:
        raise ValueError("ไม่พบคำสั่งซื้อนี้")
    if order["status"] != ORDER_STATUS_COMPLETED:
        raise ValueError("จัดการรีวิวได้เมื่อคำสั่งซื้อสำเร็จแล้วเท่านั้น")

    order_pids = sorted({int(i["product_id"]) for i in repo_orders.list_items(order_id) if i["product_id"]})
    if not order_pids:
        raise ValueError("ไม่มีสินค้าในคำสั่งซื้อนี้")

    if product_id is not None:
        pid = int(product_id)
        if pid not in order_pids:
            raise ValueError("ไม่มีสินค้านี้ในคำสั่งซื้อ")
        target_pids = [pid]
    else:
        target_pids = order_pids

    skipped_pids: list[int] = []
    with transaction() as conn:
        for pid in target_pids:
            if not repo_reviews.exists(user_id, pid, order_id, conn=conn):
                repo_reviews.skip(user_id, order_id, pid, conn=conn)
                skipped_pids.append(pid)

    return {
        "ok": True,
        "order_id": int(order_id),
        "skipped_product_ids": skipped_pids,
    }


def find_reviewable_order(user_id: int, product_id: int):
    """
    หา order_id ที่ผู้ซื้อยังรีวิวสินค้านี้ได้ (ไว้โชว์ปุ่ม "เขียนรีวิว" ในหน้ารายละเอียดสินค้า)
    ไม่มี = None
    """
    permissions.require_self(permissions.REVIEW_WRITE, user_id)
    row = repo_orders.find_completed_order_with_product(user_id, product_id)
    if row is None or row["already_reviewed"]:
        return None
    return row["id"]


def _is_valid_video_bytes(raw: bytes, ext: str) -> bool:
    """ตรวจ magic bytes ของไฟล์วิดีโอ (.mp4, .mov, .webm)"""
    if not raw or len(raw) < 12:
        return False
    if ext == ".webm":
        return raw[:4] == b"\x1a\x45\xdf\xa3"
    if ext in (".mp4", ".mov"):
        header_window = raw[:64]
        return any(
            sig in header_window
            for sig in (b"ftyp", b"moov", b"mdat", b"wide", b"free", b"skip", b"pnot")
        )
    return False


def _validate_and_prepare_media(user_id: int, media_files: list | None) -> list[dict]:
    """
    ตรวจสอบไฟล์สื่อที่แนบมากับรีวิว (0–5 ไฟล์รวมกัน):
    - ตรวจจำนวนรวม <= config.MAX_REVIEW_FILES
    - ตรวจนามสกุล + ขนาดไฟล์ + magic bytes/PIL
    คืนรายการ dict สำหรับเตรียมเขียนลงดิสก์
    """
    files = list(media_files or [])
    if len(files) > config.MAX_REVIEW_FILES:
        raise ValueError(f"อัปโหลดรูปภาพและวิดีโอรวมกันได้ไม่เกิน {config.MAX_REVIEW_FILES} ไฟล์")

    prepared = []
    img_limit_mb = config.MAX_REVIEW_IMAGE_BYTES // (1024 * 1024)
    vid_limit_mb = config.MAX_REVIEW_VIDEO_BYTES // (1024 * 1024)

    for idx, f in enumerate(files, start=1):
        if not isinstance(f, dict):
            raise ValueError("รูปแบบข้อมูลไฟล์แนบไม่ถูกต้อง")
        orig_name = Path(str(f.get("filename") or "")).name
        ext = Path(orig_name).suffix.lower()
        raw = f.get("data")
        if isinstance(raw, memoryview):
            raw = bytes(raw)
        if not isinstance(raw, (bytes, bytearray)) or len(raw) == 0:
            raise ValueError("ไฟล์ที่อัปโหลดว่างเปล่าหรือไม่ถูกต้อง")
        raw_bytes = bytes(raw)

        if ext in config.ALLOWED_REVIEW_IMAGE_EXTENSIONS:
            if len(raw_bytes) > config.MAX_REVIEW_IMAGE_BYTES:
                raise ValueError(f"ไฟล์รูปภาพ '{orig_name}' มีขนาดเกิน {img_limit_mb} MB")
            try:
                with Image.open(io.BytesIO(raw_bytes)) as opened:
                    opened.load()
                    fmt = (opened.format or "").upper()
                    img_copy = opened.copy()
            except (OSError, UnidentifiedImageError):
                raise ValueError(f"ไฟล์รูปภาพ '{orig_name}' ไม่ถูกต้องหรือเสียหาย") from None
            if fmt not in ("JPEG", "PNG", "WEBP"):
                raise ValueError("รองรับเฉพาะไฟล์รูปภาพ .jpg, .png และ .webp เท่านั้น")
            if max(img_copy.size) > config.UPLOAD_MAX_SIDE:
                img_copy.thumbnail((config.UPLOAD_MAX_SIDE, config.UPLOAD_MAX_SIDE), Image.LANCZOS)
            out_buf = io.BytesIO()
            has_alpha = img_copy.mode in ("RGBA", "LA") or "transparency" in img_copy.info
            if fmt == "PNG" or (fmt == "WEBP" and has_alpha):
                out_ext = ".png"
                img_copy.save(out_buf, "PNG", optimize=True)
            elif fmt == "WEBP":
                out_ext = ".webp"
                img_copy.save(out_buf, "WEBP", quality=88)
            else:
                out_ext = ".jpg"
                img_copy.convert("RGB").save(out_buf, "JPEG", quality=88, optimize=True)
            prepared.append({
                "kind": "image",
                "ext": out_ext,
                "bytes": out_buf.getvalue(),
                "sort_order": idx,
            })

        elif ext in config.ALLOWED_REVIEW_VIDEO_EXTENSIONS:
            if len(raw_bytes) > config.MAX_REVIEW_VIDEO_BYTES:
                raise ValueError(f"ไฟล์วิดีโอ '{orig_name}' มีขนาดเกิน {vid_limit_mb} MB")
            if not _is_valid_video_bytes(raw_bytes, ext):
                raise ValueError(f"ไฟล์วิดีโอ '{orig_name}' ไม่ถูกต้องหรือเสียหาย (รองรับเฉพาะ .mp4, .webm, .mov)")
            prepared.append({
                "kind": "video",
                "ext": ext,
                "bytes": raw_bytes,
                "sort_order": idx,
            })
        else:
            raise ValueError(
                "ชนิดไฟล์ไม่รองรับ กรุณาเลือกเฉพาะรูปภาพ (.jpg, .png, .webp) หรือวิดีโอ (.mp4, .webm, .mov)"
            )

    return prepared


def add_review(
    user_id: int,
    product_id: int,
    order_id: int,
    rating: int,
    comment=None,
    media_files: list | None = None,
) -> dict:
    """
    เพิ่มรีวิวพร้อมสื่อแนบ 0–5 ไฟล์แบบ atomic — คืน dict รีวิวที่บันทึก
    ValueError (ข้อความไทย): ให้ดาวไม่ใช่ 1–5, ความเห็นยาวเกิน, รีวิวไม่ได้ตามกติกา, รีวิวซ้ำ, ไฟล์ไม่ถูกต้อง
    """
    permissions.require_self(permissions.REVIEW_WRITE, user_id)
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        raise ValueError("กรุณาให้คะแนน 1-5 ดาว")
    comment = (comment or "").strip() or None
    if comment and len(comment) > MAX_COMMENT_LENGTH:
        raise ValueError(f"ความเห็นยาวเกินไป (ไม่เกิน {MAX_COMMENT_LENGTH} ตัวอักษร)")
    reason = _reason_cannot_review(user_id, product_id, order_id)
    if reason:
        raise ValueError(reason)

    prepared_media = _validate_and_prepare_media(user_id, media_files)

    out_dir = Path(config.REVIEWS_DIR).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    written_files: list[Path] = []
    media_records: list[dict] = []

    try:
        for item in prepared_media:
            fname = f"review_{int(user_id)}_{stamp}_{uuid.uuid4().hex[:8]}{item['ext']}"
            dest = (out_dir / fname).resolve()
            if out_dir not in dest.parents:
                raise ValueError("ตำแหน่งจัดเก็บไฟล์ไม่ปลอดภัย")
            dest.write_bytes(item["bytes"])
            written_files.append(dest)
            try:
                rel_path = dest.relative_to(Path(config.BASE_DIR).resolve()).as_posix()
            except ValueError:
                rel_path = f"assets/reviews/{dest.name}"
            media_records.append({
                "kind": item["kind"],
                "file_path": rel_path,
                "sort_order": item["sort_order"],
            })

        with transaction() as conn:
            try:
                review_id = repo_reviews.create(user_id, product_id, order_id, rating, comment, conn=conn)
            except sqlite3.IntegrityError:
                raise ValueError("คุณรีวิวสินค้านี้ในคำสั่งซื้อนี้ไปแล้ว") from None
            if media_records:
                repo_reviews.add_media_many(review_id, media_records, conn=conn)
            opt_map = repo_reviews.list_option_labels_by_order_products([(order_id, product_id)], conn=conn)
            opt_label = opt_map.get((int(order_id), int(product_id)), "")
            saved_media = repo_reviews.list_media_by_reviews([review_id], conn=conn).get(int(review_id), [])
    except BaseException:
        for fp in written_files:
            try:
                fp.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    return {
        "id": review_id,
        "product_id": product_id,
        "order_id": order_id,
        "rating": rating,
        "comment": comment,
        "option_label": opt_label,
        "media": saved_media,
    }


def list_reviews(product_id: int, page: int = 1, page_size: int = 10) -> dict:
    """
    รีวิวของสินค้า ใหม่สุดก่อน (ผู้ซื้อและแอดมินดูได้)
    คืน {"items": [dict], "total", "avg", "count", "page", "page_size", "pages"}
    item: id, rating, comment, created_at, reviewer_name, reviewer_avatar, option_label, media
    """
    permissions.require_any(permissions.SHOP_BROWSE, permissions.PRODUCT_VIEW)
    try:
        page, page_size = max(1, int(page)), min(50, max(1, int(page_size)))
    except (TypeError, ValueError):
        raise ValueError("เลขหน้าไม่ถูกต้อง") from None
    avg, count = repo_reviews.get_summary(product_id)
    pages = max(1, math.ceil(count / page_size))
    page = min(page, pages)
    rows = repo_reviews.list_by_product(product_id, limit=page_size, offset=(page - 1) * page_size)

    review_ids = [int(r["id"]) for r in rows]
    order_product_pairs = [(int(r["order_id"]), int(r["product_id"])) for r in rows]
    media_map = repo_reviews.list_media_by_reviews(review_ids)
    option_map = repo_reviews.list_option_labels_by_order_products(order_product_pairs)

    items = []
    for r in rows:
        rid = int(r["id"])
        oid = int(r["order_id"])
        pid = int(r["product_id"])
        items.append({
            "id": rid,
            "order_id": oid,
            "product_id": pid,
            "rating": r["rating"],
            "comment": r["comment"],
            "created_at": r["created_at"],
            "reviewer_name": r["reviewer_name"],
            "reviewer_avatar": r["reviewer_avatar"],
            "option_label": option_map.get((oid, pid), ""),
            "media": media_map.get(rid, []),
        })

    return {
        "items": items,
        "total": count,
        "avg": avg,
        "count": count,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
