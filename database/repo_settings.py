"""
database/repo_settings.py
อ่าน/เขียนตาราง settings (key-value เก็บเป็นข้อความ)
ถ้า key ไม่มีใน DB จะใช้ค่าตั้งต้นจาก config.DEFAULT_SETTINGS
พร้อมแคชหน่วยความจำที่ล้างทันทีเมื่อบันทึกค่าใหม่ (เพื่อให้ชื่อร้านและการตั้งค่าอัปเดตทันทีและ API ตอบสนองรวดเร็ว)
"""
from config import DEFAULT_SETTINGS
import database.db as _db
from database.repo_base import use_conn

_CACHE_KEY = None
_CACHE_DATA: dict | None = None


def clear_cache() -> None:
    """ล้างแคชการตั้งค่าเมื่อมีการแก้ไขข้อมูล"""
    global _CACHE_KEY, _CACHE_DATA
    _CACHE_KEY = None
    _CACHE_DATA = None


def _current_sig():
    p = str(_db.DB_PATH)
    return (p, _db._file_sig(p))


def get_all(conn=None) -> dict:
    """ทุก key = DEFAULT_SETTINGS ถูกทับด้วยค่าใน DB"""
    global _CACHE_KEY, _CACHE_DATA
    if conn is None:
        sig = _current_sig()
        if _CACHE_DATA is not None and _CACHE_KEY == sig and sig[1] is not None:
            return dict(_CACHE_DATA)
    with use_conn(conn) as c:
        rows = c.execute("SELECT key, value FROM settings").fetchall()
    data = dict(DEFAULT_SETTINGS)
    data.update({r["key"]: r["value"] for r in rows if r["value"] is not None})
    if conn is None:
        _CACHE_KEY = _current_sig()
        _CACHE_DATA = dict(data)
    return data


def get(key: str, default=None, conn=None):
    """ค่าของ key (ข้อความ) — ไม่มีใน DB: ใช้ default ถ้าให้มา ไม่งั้น DEFAULT_SETTINGS ไม่มีอีกก็ None"""
    if conn is None:
        all_map = get_all()
        if key in all_map and all_map[key] is not None:
            return all_map[key]
        return default if default is not None else DEFAULT_SETTINGS.get(key)
    with use_conn(conn) as c:
        row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is not None and row["value"] is not None:
        return row["value"]
    return default if default is not None else DEFAULT_SETTINGS.get(key)


def set(key: str, value, conn=None) -> None:  # noqa: A001 (ชื่อตามที่กำหนดในแผน)
    """บันทึกค่า (แปลงเป็นข้อความ) — มีอยู่แล้วทับ ไม่มีสร้างใหม่ และล้างแคชทันที"""
    with use_conn(conn) as c:
        c.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, "" if value is None else str(value)),
        )
    clear_cache()


def set_many(values: dict, conn=None) -> None:
    """บันทึกหลายค่าใน transaction เดียว และล้างแคชทันที"""
    with use_conn(conn) as c:
        for key, value in values.items():
            set(key, value, conn=c)
    clear_cache()
