"""
server/serializers.py
ตัวแปลงข้อมูลจาก sqlite3.Row / dict / list / Path เป็นโครงสร้าง JSON ที่ปลอดภัย
ตัดฟิลด์ความลับ (password_hash, code_hash, token_hash) ออกทุกระดับโดยอัตโนมัติ
"""
import sqlite3
from pathlib import Path
from typing import Any

FORBIDDEN_FIELDS = frozenset({
    "password_hash",
    "code_hash",
    "token_hash",
})


def to_jsonable(obj: Any) -> Any:
    """แปลงข้อมูลทุกชนิดให้พร้อมส่งเป็น JSON โดยกรองฟิลด์ความลับออกเสมอ"""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, Path):
        return obj.as_posix()
    if isinstance(obj, sqlite3.Row):
        return {
            str(k): to_jsonable(obj[k])
            for k in obj.keys()
            if str(k) not in FORBIDDEN_FIELDS
        }
    if isinstance(obj, dict):
        return {
            str(k): to_jsonable(v)
            for k, v in obj.items()
            if str(k) not in FORBIDDEN_FIELDS
        }
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [to_jsonable(item) for item in obj]
    return str(obj)
