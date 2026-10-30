"""
server/jobs.py
งานเบื้องหลังตามเวลาและงานตอนเปิด/ปิดเซิร์ฟเวอร์ (ย้ายจาก main.py และ ui/app.py มาครบทุกงาน):
1. ตอนเริ่มระบบ (Startup):
   - สร้างโฟลเดอร์ + init_db()
   - ล้างสถานะออนไลน์ที่ค้าง (auth_service.clear_all_online)
   - ยกเลิกออเดอร์ค้างชำระเกิน unpaid_cancel_hours (order_service.auto_cancel_unpaid)
   - รีเซ็ตคูปองรายวันตอนเที่ยง (coupon_service.run_daily_noon_reset)
   - ส่งออกรายงานรายเดือนอัตโนมัติ (export_service.auto_export_previous_month)
   - ส่งอีเมลสรุปสต็อกต่ำรายวัน (email_outbox_service.send_low_stock_digest)
   - ลองส่งอีเมลใน outbox ที่ค้างซ้ำ (email_outbox_service.retry_failed_outbox)
   - ล้าง OTP และเซสชันที่หมดอายุ (repo_otp.purge_expired, repo_sessions.purge_expired)
2. งานตามรอบเวลา (Periodic Scheduler Thread):
   - รันงานข้างต้นเป็นรอบอัตโนมัติโดยไม่บล็อกคำขอหลัก
3. ตอนปิดระบบ (Shutdown):
   - หยุด thread งานตามเวลา
   - ล้างสถานะออนไลน์ทุกคน (auth_service.clear_all_online)
   - สำรองฐานข้อมูลอัตโนมัติ (utils.backup.auto_backup_on_exit)
"""
import threading
import traceback

import config
from database import db, repo_otp, repo_sessions
from services import (
    auth_service,
    coupon_service,
    email_outbox_service,
    export_service,
    order_service,
)
from utils import backup

_stop_event = threading.Event()
_worker_thread: threading.Thread | None = None


def _safe_run(label: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return None


def purge_expired_auth_records() -> dict:
    """ล้างรหัส OTP และเซสชันที่หมดอายุออกจากฐานข้อมูล"""
    sessions_purged = _safe_run("purge_sessions", repo_sessions.purge_expired) or 0
    otps_purged = 0
    if hasattr(repo_otp, "purge_expired"):
        otps_purged = _safe_run("purge_otps", repo_otp.purge_expired) or 0
    return {"sessions_purged": sessions_purged, "otps_purged": otps_purged}


def run_startup_jobs() -> dict:
    """รันงานเริ่มต้นระบบทั้งหมดเมื่อเปิดเซิร์ฟเวอร์"""
    config.ensure_dirs()
    db.init_db()
    online_cleared = _safe_run("clear_all_online", auth_service.clear_all_online)
    unpaid_cancelled = _safe_run("auto_cancel_unpaid", order_service.auto_cancel_unpaid)
    coupons_reset = _safe_run("run_daily_noon_reset", coupon_service.run_daily_noon_reset)
    auto_export = _safe_run("auto_export_previous_month", export_service.auto_export_previous_month)
    low_stock_digest = _safe_run("send_low_stock_digest", email_outbox_service.send_low_stock_digest)
    outbox_retried = _safe_run("retry_failed_outbox", email_outbox_service.retry_failed_outbox)
    purged = purge_expired_auth_records()
    return {
        "online_cleared": online_cleared,
        "unpaid_cancelled": unpaid_cancelled,
        "coupons_reset": coupons_reset,
        "auto_export": auto_export,
        "low_stock_digest": low_stock_digest,
        "outbox_retried": outbox_retried,
        "purged": purged,
    }


def run_periodic_tick(tick_minute: int = 0) -> None:
    """รันงานตามรอบนาที (เรียกจาก scheduler loop หรือเรียกทดสอบได้โดยตรง)"""
    # ทุก 1 นาที: รีเซ็ตคูปองเที่ยงวัน
    _safe_run("run_daily_noon_reset", coupon_service.run_daily_noon_reset)

    # ทุก 5 นาที: ยกเลิกออเดอร์เกินเวลา + retry อีเมลที่ค้าง
    if tick_minute % 5 == 0:
        _safe_run("auto_cancel_unpaid", order_service.auto_cancel_unpaid)
        _safe_run("retry_failed_outbox", email_outbox_service.retry_failed_outbox)

    # ทุก 15 นาที: ล้าง OTP และเซสชันหมดอายุ
    if tick_minute % 15 == 0:
        purge_expired_auth_records()

    # ทุก 30 นาที: ส่งอีเมลสรุปสต็อกต่ำรายวัน (ส่งไม่เกินวันละ 1 ครั้ง)
    if tick_minute % 30 == 0:
        _safe_run("send_low_stock_digest", email_outbox_service.send_low_stock_digest)

    # ทุก 60 นาที: ตรวจส่งออกรายงานรายเดือนอัตโนมัติ
    if tick_minute % 60 == 0:
        _safe_run("auto_export_previous_month", export_service.auto_export_previous_month)


def _scheduler_loop() -> None:
    tick = 1
    while not _stop_event.wait(timeout=60.0):
        run_periodic_tick(tick)
        tick = (tick + 1) % 1440


def start_background_jobs() -> None:
    """เริ่มงานตอนเปิดเซิร์ฟเวอร์และสตาร์ท background scheduler thread"""
    global _worker_thread
    run_startup_jobs()
    _stop_event.clear()
    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_thread = threading.Thread(
            target=_scheduler_loop, name="BadmintonShopScheduler", daemon=True
        )
        _worker_thread.start()


def stop_background_jobs() -> None:
    """หยุด scheduler thread ล้างสถานะออนไลน์ และสำรองฐานข้อมูลอัตโนมัติก่อนปิดเซิร์ฟเวอร์"""
    global _worker_thread
    _stop_event.set()
    if _worker_thread is not None and _worker_thread.is_alive():
        _worker_thread.join(timeout=2.0)
    _worker_thread = None
    _safe_run("clear_all_online", auth_service.clear_all_online)
    _safe_run("auto_backup_on_exit", backup.auto_backup_on_exit)
