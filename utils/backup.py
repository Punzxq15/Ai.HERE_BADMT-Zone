"""
utils/backup.py
สำรอง/กู้คืนฐานข้อมูล SQLite (ใช้ sqlite3.Connection.backup() ปลอดภัยแม้แอปเปิดอยู่ และรองรับ fallback สำหรับระบบไฟล์ 9p/FUSE)
ไฟล์สำรองอยู่ที่ data/backups/shop_YYYYMMDD_HHMMSS.db
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import config

_REQUIRED_TABLES = {"users", "products", "orders", "settings"}


def _connect_sqlite(path: Path, readonly: bool = False):
    p = Path(path).resolve()
    try:
        if readonly:
            conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", timeout=10, uri=True)
        else:
            conn = sqlite3.connect(p, timeout=10)
        conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchall()
        return conn
    except sqlite3.OperationalError:
        mode_q = "mode=ro&nolock=1" if readonly else "nolock=1"
        return sqlite3.connect(f"{p.as_uri()}?{mode_q}", timeout=10, uri=True)


def _copy_db(src_path: Path, dest_path: Path) -> None:
    try:
        src = _connect_sqlite(src_path, readonly=True)
        dst = _connect_sqlite(dest_path, readonly=False)
        try:
            src.backup(dst)
            return
        finally:
            dst.close()
            src.close()
    except sqlite3.OperationalError:
        shutil.copy2(src_path, dest_path)


def _prune(keep: int) -> None:
    bdir = Path(config.BACKUP_DIR)
    files = sorted(bdir.glob("shop_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[max(keep, 1):]:
        try:
            old.unlink()
        except OSError:
            pass  # ลบไม่ได้ก็ข้าม ไม่ให้การสำรองล้ม


def backup_db(keep: int = None, prefix: str = "shop") -> Path:
    """สำรองฐานข้อมูลปัจจุบัน แล้วเก็บไว้แค่ `keep` ไฟล์ล่าสุด | คืน path ไฟล์ที่สร้าง | ValueError ถ้าไม่มี DB"""
    if keep is None:
        keep = config.BACKUP_KEEP_COUNT
    db_path = Path(config.DB_PATH)
    bdir = Path(config.BACKUP_DIR)
    if not db_path.exists():
        raise ValueError("ไม่พบไฟล์ฐานข้อมูลที่จะสำรอง")
    bdir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = bdir / f"{prefix}_{stamp}.db"
    n = 1
    while dest.exists():  # สำรองหลายครั้งในวินาทีเดียวกัน
        dest = bdir / f"{prefix}_{stamp}_{n}.db"
        n += 1

    _copy_db(db_path, dest)
    _prune(keep)
    return dest


def list_backups() -> list[dict]:
    """รายการไฟล์สำรอง ใหม่สุดก่อน: [{'path': Path, 'name': str, 'size': int (ไบต์), 'created_at': 'YYYY-MM-DD HH:MM:SS'}]"""
    bdir = Path(config.BACKUP_DIR)
    if not bdir.exists():
        return []
    items = []
    for path in bdir.glob("shop_*.db"):
        st = path.stat()
        items.append({
            "path": path,
            "name": path.name,
            "size": st.st_size,
            "created_at": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "_mtime": st.st_mtime,
        })
    items.sort(key=lambda d: d["_mtime"], reverse=True)
    for d in items:
        d.pop("_mtime")
    return items


def restore_backup(path) -> None:
    """
    กู้คืนฐานข้อมูลจากไฟล์สำรอง (สำรองข้อมูลปัจจุบันไว้ก่อนเป็น shop_prerestore_*.db)
    ValueError (ไทย) เมื่อไฟล์ไม่มี/ไม่ใช่ฐานข้อมูลของร้านนี้ | หลังกู้คืนควรให้ผู้ใช้เปิดแอปใหม่
    """
    src_path = Path(path)
    if not src_path.is_file():
        raise ValueError("ไม่พบไฟล์สำรองที่เลือก")

    # ตรวจว่าเป็นฐานข้อมูลของโปรเจกต์นี้จริงก่อนทับของเดิม
    try:
        check = _connect_sqlite(src_path, readonly=True)
        try:
            tables = {r[0] for r in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            ok = check.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            check.close()
    except sqlite3.DatabaseError:
        raise ValueError("ไฟล์นี้ไม่ใช่ฐานข้อมูลที่ถูกต้อง") from None
    if not ok or not _REQUIRED_TABLES.issubset(tables):
        raise ValueError("ไฟล์นี้ไม่ใช่ไฟล์สำรองของร้านนี้ หรือไฟล์เสียหาย")

    db_path = Path(config.DB_PATH)
    if db_path.exists():
        backup_db(prefix="shop_prerestore")
    _copy_db(src_path, db_path)


def auto_backup_on_exit(keep: int = None) -> Path | None:
    """
    สำรองอัตโนมัติตอนปิดแอป (ส่วน G) — ชื่อไฟล์ data/backups/shop_auto_YYYYMMDD_HHMMSS.db
    ข้ามถ้าฐานข้อมูลไม่เปลี่ยนตั้งแต่ไฟล์สำรองล่าสุด (กันไฟล์สำรองเก่า ๆ ถูกดันทิ้งเพราะเปิด-ปิดแอปเฉย ๆ)
    คืน path ไฟล์ที่สร้าง หรือ None ถ้าข้าม/ทำไม่ได้ — ไม่โยน exception (ห้ามทำให้ปิดแอปไม่ได้)
    """
    if keep is None:
        keep = config.BACKUP_KEEP_COUNT
    try:
        db_path = Path(config.DB_PATH)
        if not db_path.exists():
            return None
        stamps = [db_path.stat().st_mtime]
        wal = Path(str(db_path) + "-wal")
        if wal.exists():
            stamps.append(wal.stat().st_mtime)
        latest = list_backups()
        if latest and latest[0]["path"].stat().st_mtime >= max(stamps):
            return None
        return backup_db(keep=keep, prefix="shop_auto")
    except Exception:  # noqa: BLE001
        return None
