"""
database/db.py
สร้าง connection, สร้างตารางทั้งหมด (20 ตารางหลัก + ตารางส่วนขยาย v2/v3 แบบ idempotent) และ helper transaction()
path ทั้งหมดอ่านจาก config.py
"""
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from config import BACKUP_DIR, BASE_DIR, DATA_DIR, DB_PATH, DEFAULT_LOGIN_BANNER_FILES  # noqa: F401
import os as _os
import threading as _threading

_WAL_SUPPORT_CACHE: dict[str, bool] = {}


def _dir_supports_wal(directory: Path) -> bool:
    """ตรวจว่าโฟลเดอร์รองรับ SQLite WAL + POSIX lock หรือไม่ (แคชผลลัพธ์ต่อโฟลเดอร์)"""
    raw_key = str(directory)
    if raw_key in _WAL_SUPPORT_CACHE:
        return _WAL_SUPPORT_CACHE[raw_key]
    directory.mkdir(parents=True, exist_ok=True)
    key = str(directory.resolve())
    if key in _WAL_SUPPORT_CACHE:
        _WAL_SUPPORT_CACHE[raw_key] = _WAL_SUPPORT_CACHE[key]
        return _WAL_SUPPORT_CACHE[key]
    probe = directory / ".wal_probe.db"
    try:
        c = sqlite3.connect(probe, timeout=2)
        try:
            mode = c.execute("PRAGMA journal_mode = WAL").fetchone()[0]
            c.execute("CREATE TABLE IF NOT EXISTS _probe(x INT)")
            c.commit()
            supported = str(mode).lower() == "wal"
        finally:
            c.close()
    except sqlite3.Error:
        supported = False
    finally:
        for suffix in ("", "-wal", "-shm", "-journal"):
            try:
                Path(str(probe) + suffix).unlink(missing_ok=True)
            except OSError:
                pass
    _WAL_SUPPORT_CACHE[key] = supported
    _WAL_SUPPORT_CACHE[raw_key] = supported
    return supported


_NON_WAL_CHECKED: dict[str, int] = {}


def _ensure_non_wal_header_if_needed(db_file: Path) -> None:
    """หากระบบไฟล์ไม่รองรับ WAL แต่ไฟล์ DB เดิมติดสถานะ WAL (byte 18-19 = 2,2) ให้ปรับกลับเป็นโหมดมาตรฐาน"""
    key = str(db_file)
    try:
        st = db_file.stat()
    except OSError:
        return
    if st.st_size < 100:
        return
    if _NON_WAL_CHECKED.get(key) == st.st_ino:
        return
    try:
        with open(db_file, "r+b") as f:
            f.seek(18)
            ver = f.read(2)
            if ver == b"\x02\x02":
                f.seek(18)
                f.write(b"\x01\x01")
                f.flush()
        for suffix in ("-wal", "-shm"):
            Path(str(db_file) + suffix).unlink(missing_ok=True)
        _NON_WAL_CHECKED[key] = st.st_ino
    except OSError:
        pass


_POOL_LOCK = _threading.RLock()
_SHARED_POOL: dict[str, dict] = {}


def _file_sig(path_str: str):
    try:
        st = _os.stat(path_str)
        return (st.st_ino, st.st_mtime_ns, st.st_size)
    except OSError:
        return None


class _PooledConnection:
    """Wrapper รอบ sqlite3.Connection ที่แชร์ page cache ในโปรเซสเดียวกันโดยปลอดภัยด้วย RLock"""
    __slots__ = ("_entry", "_raw", "_closed")

    def __init__(self, entry: dict):
        self._entry = entry
        self._raw = entry["conn"]
        self._closed = False

    def __getattr__(self, name):
        return getattr(self._raw, name)

    def execute(self, *args, **kwargs):
        with _POOL_LOCK:
            res = self._raw.execute(*args, **kwargs)
            self._entry["sig"] = _file_sig(self._entry["path"])
            return res

    def executemany(self, *args, **kwargs):
        with _POOL_LOCK:
            res = self._raw.executemany(*args, **kwargs)
            self._entry["sig"] = _file_sig(self._entry["path"])
            return res

    def executescript(self, *args, **kwargs):
        with _POOL_LOCK:
            res = self._raw.executescript(*args, **kwargs)
            self._entry["sig"] = _file_sig(self._entry["path"])
            return res

    def cursor(self, *args, **kwargs):
        with _POOL_LOCK:
            return self._raw.cursor(*args, **kwargs)

    def commit(self):
        with _POOL_LOCK:
            self._raw.commit()
            self._entry["sig"] = _file_sig(self._entry["path"])

    def rollback(self):
        with _POOL_LOCK:
            self._raw.rollback()
            self._entry["sig"] = _file_sig(self._entry["path"])

    def __enter__(self):
        _POOL_LOCK.acquire()
        self._raw.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            res = self._raw.__exit__(exc_type, exc_val, exc_tb)
            self._entry["sig"] = _file_sig(self._entry["path"])
            return res
        finally:
            _POOL_LOCK.release()

    def close(self):
        if self._closed:
            return
        self._closed = True
        with _POOL_LOCK:
            self._entry["sig"] = _file_sig(self._entry["path"])


def reset_connection_pool() -> None:
    """ปิดและล้าง connection ที่แคชไว้เมื่อสลับไฟล์ DB หรือกู้คืนสำรองข้อมูล"""
    with _POOL_LOCK:
        for entry in list(_SHARED_POOL.values()):
            try:
                entry["conn"].close()
            except Exception:
                pass
        _SHARED_POOL.clear()


def _open_raw_connection(db_file: Path, use_wal: bool) -> sqlite3.Connection:
    if not use_wal:
        _ensure_non_wal_header_if_needed(db_file)
        conn = sqlite3.connect(
            f"{db_file.as_uri()}?nolock=1",
            timeout=10,
            uri=True,
            check_same_thread=False,
        )
    else:
        conn = sqlite3.connect(db_file, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = 1")
    if use_wal:
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            conn.execute("PRAGMA journal_mode = MEMORY")
    else:
        conn.execute("PRAGMA locking_mode = EXCLUSIVE")
        conn.execute("PRAGMA journal_mode = MEMORY")
        conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def get_connection():
    """
    สร้างและคืนค่า connection สำหรับฐานข้อมูล SQLite (ผู้เรียกต้อง close() เอง)
    เปิด foreign_keys + WAL ให้ทุก connection (หากระบบไฟล์ไม่รองรับ POSIX lock/WAL เช่น 9p/network drive จะสลับใช้ nolock + MEMORY อัตโนมัติ)
    """
    db_file = Path(DB_PATH)
    use_wal = _dir_supports_wal(db_file.parent if db_file.parent.exists() else db_file.resolve().parent)
    if use_wal:
        db_file = db_file.resolve()
        db_file.parent.mkdir(parents=True, exist_ok=True)
        return _open_raw_connection(db_file, True)

    key = str(DB_PATH)
    with _POOL_LOCK:
        cur_sig = _file_sig(key)
        entry = _SHARED_POOL.get(key)
        if entry is not None:
            if cur_sig is None or cur_sig != entry["sig"]:
                try:
                    entry["conn"].close()
                except Exception:
                    pass
                _SHARED_POOL.pop(key, None)
                entry = None
        if entry is None:
            resolved = db_file.resolve()
            resolved.parent.mkdir(parents=True, exist_ok=True)
            raw = _open_raw_connection(resolved, False)
            entry = {"path": key, "conn": raw, "sig": _file_sig(key)}
            _SHARED_POOL[key] = entry
        return _PooledConnection(entry)


@contextmanager
def get_db():
    """Context manager สำหรับเปิด/ปิด connection พร้อม commit อัตโนมัติเมื่อสำเร็จ"""
    with _POOL_LOCK:
        conn = get_connection()
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()


@contextmanager
def transaction():
    """ครอบงานที่แก้ข้อมูลหลายตารางให้อยู่ใน transaction เดียว"""
    with _POOL_LOCK:
        conn = get_connection()
        try:
            if not conn.in_transaction:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()


def _ensure_column(cursor, table, column, definition):
    """เพิ่มคอลัมน์ให้ DB เดิมที่สร้างก่อนหน้า (CREATE IF NOT EXISTS ไม่เพิ่มคอลัมน์ให้เอง)"""
    cursor.execute(f"PRAGMA table_info({table})")
    if column not in [row["name"] for row in cursor.fetchall()]:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _backup_before_migration_if_needed():
    """สำรองฐานข้อมูลจริงก่อนทำ migration v2/v3 ครั้งแรก (เฉพาะไฟล์ DB จริงที่มีอยู่แล้ว)"""
    try:
        db_file = Path(DB_PATH).resolve()
        if not db_file.exists() or db_file.stat().st_size == 0:
            return
        use_wal = _dir_supports_wal(db_file.parent)
        if not use_wal:
            _ensure_non_wal_header_if_needed(db_file)
            conn = sqlite3.connect(f"{db_file.as_uri()}?nolock=1", timeout=5, uri=True)
        else:
            conn = sqlite3.connect(db_file, timeout=5)
        try:
            has_v2 = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='email_otps'"
            ).fetchone()
            has_v3 = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='option_groups'"
            ).fetchone()
        finally:
            conn.close()
        if (has_v2 is None or has_v3 is None) and Path(DATA_DIR).resolve() == db_file.parent.resolve():
            bdir = Path(BACKUP_DIR)
            bdir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tag = "v2" if has_v2 is None else "v3"
            dest = bdir / f"shop_pre_migrate_{tag}_{stamp}.db"
            if not dest.exists():
                shutil.copy2(db_file, dest)
    except Exception:  # noqa: BLE001
        pass


def _migrate_v2(cursor):
    """อัปเกรดสคีมา v2 แบบ idempotent"""
    _ensure_column(cursor, "users", "email_verified", "INTEGER DEFAULT 1")
    _ensure_column(cursor, "users", "must_change_password", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "users", "last_login_at", "TIMESTAMP")

    _ensure_column(cursor, "products", "deleted_at", "TIMESTAMP")
    _ensure_column(cursor, "products", "deleted_by", "INTEGER")
    _ensure_column(cursor, "products", "cost_price", "REAL")

    _ensure_column(cursor, "categories", "deleted_at", "TIMESTAMP")
    _ensure_column(cursor, "categories", "all_brands", "INTEGER DEFAULT 1")

    _ensure_column(cursor, "brands", "deleted_at", "TIMESTAMP")

    _ensure_column(cursor, "cart_items", "is_selected", "INTEGER DEFAULT 1")

    _ensure_column(cursor, "coupons", "owner_user_id", "INTEGER")
    _ensure_column(cursor, "coupons", "source_rule_id", "INTEGER")
    _ensure_column(cursor, "coupons", "source_order_id", "INTEGER")
    _ensure_column(cursor, "coupons", "claimable", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "coupons", "max_discount", "REAL")
    _ensure_column(cursor, "coupons", "starts_at", "TIMESTAMP")
    _ensure_column(cursor, "coupons", "is_free_shipping", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "coupons", "daily_reset_12", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "coupons", "code_prefix", "TEXT")
    _ensure_column(cursor, "coupons", "last_reset_date", "TEXT")
    _ensure_column(cursor, "coupons", "claim_start_time", "TEXT")
    _ensure_column(cursor, "coupons", "claim_end_time", "TEXT")
    _ensure_column(cursor, "coupons", "repeat_daily", "INTEGER DEFAULT 0")

    _ensure_column(cursor, "orders", "shipping_discount", "REAL DEFAULT 0")

    _ensure_column(cursor, "notifications", "target_route", "TEXT")
    _ensure_column(cursor, "notifications", "target_params", "TEXT")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        purpose TEXT NOT NULL CHECK(purpose IN ('register', 'reset')),
        code_hash TEXT NOT NULL,
        attempts INTEGER DEFAULT 0,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pending_registrations (
        email TEXT PRIMARY KEY,
        username TEXT,
        full_name TEXT NOT NULL,
        phone TEXT,
        password_hash TEXT NOT NULL,
        address_json TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        remember INTEGER DEFAULT 0,
        user_agent TEXT,
        ip TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        last_seen_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS category_brands (
        category_id INTEGER NOT NULL,
        brand_id INTEGER NOT NULL,
        PRIMARY KEY(category_id, brand_id),
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE,
        FOREIGN KEY(brand_id) REFERENCES brands(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupon_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        trigger_min_spend REAL NOT NULL,
        reward_type TEXT NOT NULL CHECK(reward_type IN ('fixed', 'percent')),
        reward_value REAL NOT NULL,
        reward_min_order REAL DEFAULT 0,
        reward_valid_days INTEGER DEFAULT 30,
        is_active INTEGER DEFAULT 1
    )
    ''')

    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS ux_coupon_reward_once
    ON coupons(source_rule_id, source_order_id) WHERE source_rule_id IS NOT NULL
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupon_claims (
        user_id INTEGER NOT NULL,
        coupon_id INTEGER NOT NULL,
        claimed_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        used_at TIMESTAMP,
        PRIMARY KEY(user_id, coupon_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(coupon_id) REFERENCES coupons(id) ON DELETE CASCADE
    )
    ''')
    _ensure_column(cursor, "coupon_claims", "used_at", "TIMESTAMP")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spent_on DATE NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount >= 0),
        note TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL,
        subject TEXT,
        body TEXT NOT NULL,
        sent_ok INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(admin_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL CHECK(kind IN ('receipt', 'staff_urgent', 'shipped', 'low_stock')),
        to_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        body_text TEXT,
        body_html TEXT,
        attachment_path TEXT,
        related_order_id INTEGER,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'failed')),
        attempts INTEGER DEFAULT 0,
        last_error TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        sent_at TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS ux_outbox_receipt_once
    ON email_outbox(related_order_id) WHERE kind = 'receipt'
    ''')

    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS ux_outbox_shipped_once
    ON email_outbox(related_order_id) WHERE kind = 'shipped'
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT NOT NULL,
        link_url TEXT,
        alt_text TEXT,
        title TEXT,
        subtitle TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    )
    ''')
    _ensure_column(cursor, "banners", "title", "TEXT")
    _ensure_column(cursor, "banners", "subtitle", "TEXT")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_id INTEGER,
        actor_role TEXT,
        action TEXT NOT NULL,
        target_type TEXT,
        target_id INTEGER,
        detail TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    )
    ''')

    cursor.execute("CREATE INDEX IF NOT EXISTS ix_audit_created ON audit_log(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_email_otps_email ON email_otps(email, purpose, created_at)")

    cursor.execute("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL")
    cursor.execute("UPDATE categories SET all_brands = 1 WHERE all_brands IS NULL")
    cursor.execute("UPDATE cart_items SET is_selected = 1 WHERE is_selected IS NULL")
    cursor.execute('''
        INSERT OR IGNORE INTO category_brands (category_id, brand_id)
        SELECT DISTINCT category_id, brand_id FROM products
        WHERE category_id IS NOT NULL AND brand_id IS NOT NULL
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO category_brands (category_id, brand_id)
        SELECT c.id, b.id FROM categories c CROSS JOIN brands b
        WHERE COALESCE(c.all_brands, 1) = 1
    ''')


def sync_default_option_groups(cursor) -> None:
    """สร้างชุดตัวเลือกเริ่มต้น (option_groups + option_values) ให้แต่ละหมวดหมู่แบบ idempotent (T02)"""
    cat_rows = cursor.execute("SELECT id, name FROM categories").fetchall()
    cat_by_name = {r["name"]: r["id"] for r in cat_rows}

    racket_cat_id = cat_by_name.get("ไม้แบดมินตัน")
    shuttle_cat_id = cat_by_name.get("ลูกแบดมินตัน")
    shoes_cat_id = cat_by_name.get("รองเท้า")
    apparel_cat_id = cat_by_name.get("เสื้อผ้า")
    bag_cat_id = cat_by_name.get("กระเป๋า")
    grip_cat_id = cat_by_name.get("เอ็น/ด้ามพัน")

    default_groups = []
    if racket_cat_id:
        default_groups += [
            (racket_cat_id, "weight_class", "น้ำหนักไม้ (Weight Class)", 1, [
                ("3U", "3U (85-89g)"),
                ("4U", "4U (80-84g)"),
            ]),
            (racket_cat_id, "balance", "จุดสมดุล / ความหนักหัว (Balance)", 2, [
                ("Heavy Head", "Heavy Head (หัวหนัก)"),
                ("Even Balance", "Even Balance (สมดุล)"),
                ("Light Head", "Light Head (หัวเบา)"),
            ]),
            (racket_cat_id, "flex", "ความแข็งก้าน (Shaft Flexibility)", 3, [
                ("Stiff", "Stiff (ก้านแข็ง)"),
                ("Medium", "Medium (ก้านกลาง)"),
                ("Flexible", "Flexible (ก้านอ่อน)"),
            ]),
            (racket_cat_id, "level", "ระดับผู้เล่น (Skill Level)", 4, [
                ("Beginner", "Beginner (ผู้เริ่มต้น)"),
                ("Intermediate", "Intermediate (ปานกลาง)"),
                ("Advanced", "Advanced (ชำนาญ)"),
                ("Professional", "Professional (ระดับโปร)"),
            ]),
            (racket_cat_id, "color", "สีไม้แบดมินตัน", 5, [
                ("แดง", "แดง"), ("น้ำเงิน", "น้ำเงิน"), ("ดำ/ทอง", "ดำ/ทอง"),
                ("ขาว/แดง", "ขาว/แดง"), ("ชมพู", "ชมพู"), ("เขียว", "เขียว"),
            ]),
            (racket_cat_id, "grip_size", "ขนาดด้าม (Grip Size)", 6, [
                ("G4", "G4"), ("G5", "G5"), ("G6", "G6"),
            ]),
            (racket_cat_id, "string_service", "การปรับแต่งไม้ / ขึ้นเอ็น", 7, [
                ("ไม่ขึ้นเอ็น", "ไม่ขึ้นเอ็น"), ("ขึ้นเอ็น BG65", "ขึ้นเอ็น BG65"), ("ขึ้นเอ็น BG80", "ขึ้นเอ็น BG80"),
            ]),
        ]
    if shuttle_cat_id:
        default_groups += [
            (shuttle_cat_id, "speed", "ความเร็วลูกแบด (Speed)", 1, [
                ("74", "สปีด 74"), ("75", "สปีด 75"), ("76", "สปีด 76"), ("77", "สปีด 77"),
            ]),
        ]
    if shoes_cat_id:
        default_groups += [
            (shoes_cat_id, "size", "ขนาดไซซ์รองเท้า (EUR)", 1, [
                ("39", "39"), ("40", "40"), ("41", "41"), ("42", "42"), ("43", "43"), ("44", "44"),
            ]),
            (shoes_cat_id, "color", "สี / สไตล์รองเท้า", 2, [
                ("ขาว", "ขาว"), ("ดำ", "ดำ"), ("แดง", "แดง"), ("น้ำเงิน", "น้ำเงิน"),
            ]),
        ]
    if apparel_cat_id:
        default_groups += [
            (apparel_cat_id, "size", "ขนาดไซซ์เสื้อ / กางเกง", 1, [
                ("S", "S"), ("M", "M"), ("L", "L"), ("XL", "XL"), ("2XL", "2XL"),
            ]),
            (apparel_cat_id, "color", "สี / สไตล์เสื้อผ้า", 2, [
                ("ขาว", "ขาว"), ("ดำ", "ดำ"), ("น้ำเงิน", "น้ำเงิน"), ("แดง", "แดง"), ("ชมพู", "ชมพู"),
            ]),
        ]
    if bag_cat_id:
        default_groups += [
            (bag_cat_id, "color", "สี / สไตล์กระเป๋า", 1, [
                ("ดำ", "ดำ"), ("น้ำเงิน", "น้ำเงิน"), ("แดง", "แดง"), ("ขาว/ทอง", "ขาว/ทอง"),
            ]),
        ]
    if grip_cat_id:
        default_groups += [
            (grip_cat_id, "color", "สีเอ็น / ด้ามพัน", 1, [
                ("ขาว", "ขาว"), ("ดำ", "ดำ"), ("เหลือง", "เหลือง"), ("แดง", "แดง"), ("น้ำเงิน", "น้ำเงิน"),
            ]),
        ]

    for cat_id, gkey, glabel, gsort, values in default_groups:
        cursor.execute(
            '''INSERT OR IGNORE INTO option_groups (category_id, key, label, sort_order, is_active)
               VALUES (?, ?, ?, ?, 1)''',
            (cat_id, gkey, glabel, gsort),
        )
        grp_row = cursor.execute(
            "SELECT id FROM option_groups WHERE category_id = ? AND key = ?",
            (cat_id, gkey),
        ).fetchone()
        if not grp_row:
            continue
        gid = grp_row["id"]
        for vsort, (val, vlabel) in enumerate(values, start=1):
            cursor.execute(
                '''INSERT OR IGNORE INTO option_values (group_id, value, label, sort_order, is_active)
                   VALUES (?, ?, ?, ?, 1)''',
                (gid, val, vlabel, vsort),
            )

    if racket_cat_id:
        for spec_col in ("weight_class", "balance", "flex", "level"):
            grp_row = cursor.execute(
                "SELECT id FROM option_groups WHERE category_id = ? AND key = ?",
                (racket_cat_id, spec_col),
            ).fetchone()
            if not grp_row:
                continue
            gid = grp_row["id"]
            existing_vals = cursor.execute(
                f"SELECT DISTINCT {spec_col} AS v FROM products WHERE {spec_col} IS NOT NULL AND {spec_col} != ''"
            ).fetchall()
            for idx, r in enumerate(existing_vals, start=50):
                val = str(r["v"]).strip()
                if val:
                    cursor.execute(
                        '''INSERT OR IGNORE INTO option_values (group_id, value, label, sort_order, is_active)
                           VALUES (?, ?, ?, ?, 1)''',
                        (gid, val, val, idx),
                    )


def _migrate_v3(cursor):
    """อัปเกรดสคีมา v3 แบบ additive และ idempotent"""
    _ensure_column(cursor, "products", "spec_material", "TEXT")
    _ensure_column(cursor, "products", "spec_weight_grip", "TEXT")
    _ensure_column(cursor, "products", "spec_balance_mm", "TEXT")
    _ensure_column(cursor, "products", "spec_balance_type", "TEXT")
    _ensure_column(cursor, "products", "spec_max_tension", "TEXT")
    _ensure_column(cursor, "products", "spec_length", "TEXT")

    _ensure_column(cursor, "product_options", "image_path", "TEXT")

    _ensure_column(cursor, "coupons", "coupon_category", "TEXT")
    cursor.execute('''
        UPDATE coupons
        SET coupon_category = CASE
            WHEN COALESCE(is_free_shipping, 0) = 1 THEN 'free_shipping'
            WHEN discount_type = 'percent' THEN 'percent'
            WHEN discount_type = 'fixed' THEN 'fixed'
            ELSE 'other'
        END
        WHERE coupon_category IS NULL OR coupon_category = ''
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS option_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        key TEXT NOT NULL,
        label TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE,
        UNIQUE(category_id, key)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS option_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        value TEXT NOT NULL,
        label TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY(group_id) REFERENCES option_groups(id) ON DELETE CASCADE,
        UNIQUE(group_id, value)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        path TEXT NOT NULL,
        sort_order INTEGER DEFAULT 1,
        option_value_id INTEGER,
        color_value TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY(option_value_id) REFERENCES option_values(id) ON DELETE SET NULL
    )
    ''')
    _ensure_column(cursor, "product_images", "path", "TEXT")
    _ensure_column(cursor, "product_images", "option_value_id", "INTEGER")
    _ensure_column(cursor, "product_images", "color_value", "TEXT")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_product_images_prod ON product_images(product_id, sort_order, id)")

    cursor.execute('''
        INSERT INTO product_images (product_id, path, sort_order)
        SELECT p.id, p.image_path, 1
        FROM products p
        WHERE p.image_path IS NOT NULL AND p.image_path != ''
          AND NOT EXISTS (SELECT 1 FROM product_images pi WHERE pi.product_id = p.id)
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_change_otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        new_email TEXT NOT NULL,
        code_hash TEXT NOT NULL,
        attempts INTEGER DEFAULT 0,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_email_change_otps_user ON email_change_otps(user_id, new_email)")
    _ensure_column(cursor, "email_otps", "hash_version", "INTEGER DEFAULT 2")
    _ensure_column(cursor, "email_change_otps", "hash_version", "INTEGER DEFAULT 2")

    hmac_migrated = cursor.execute(
        "SELECT value FROM settings WHERE key = 'otp_hmac_migrated_v1'"
    ).fetchone()
    if hmac_migrated is None:
        cursor.execute("UPDATE email_otps SET used_at = datetime('now','localtime') WHERE used_at IS NULL")
        cursor.execute("UPDATE email_change_otps SET used_at = datetime('now','localtime') WHERE used_at IS NULL")
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('otp_hmac_migrated_v1', '1')")

    # ตารางใหม่สำหรับแบนเนอร์รูปรองเท้าในหน้า Login & Sign Up (สูงสุด 7 รูป)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS login_banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    )
    ''')

    # ใส่รูปตัวอย่าง 2 รูปเริ่มต้นตอนติดตั้งครั้งแรก (ลบ/แทนที่ได้โดยไม่เด้งกลับมาเองหลังตั้งค่าแล้ว)
    seeded_row = cursor.execute(
        "SELECT value FROM settings WHERE key = 'login_banners_seeded_v2'"
    ).fetchone()
    if seeded_row is None:
        existing_cnt = cursor.execute("SELECT COUNT(*) AS n FROM login_banners").fetchone()["n"]
        if int(existing_cnt) == 0:
            for idx, rel_path in enumerate(DEFAULT_LOGIN_BANNER_FILES, start=1):
                cursor.execute(
                    "INSERT INTO login_banners (file_path, sort_order) VALUES (?, ?)",
                    (rel_path, idx),
                )
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('login_banners_seeded_v2', '1')"
        )

    sync_default_option_groups(cursor)

    cursor.execute('''
        UPDATE products
        SET
            spec_material = COALESCE(spec_material, '46T Mitsubishi Carbon Sheet + M40X Carbon'),
            spec_weight_grip = COALESCE(
                spec_weight_grip,
                CASE
                    WHEN weight_class = '3U' THEN '3U (87±2 grams) / G5 grip size'
                    ELSE COALESCE(weight_class, '4U') || ' (82±2 grams) / G6 grip size'
                END
            ),
            spec_balance_mm = COALESCE(
                spec_balance_mm,
                CASE
                    WHEN balance IN ('Heavy Head', 'Head Heavy') THEN '305±3 mm'
                    WHEN balance = 'Even Balance' THEN '295±3 mm'
                    ELSE '288±3 mm'
                END
            ),
            spec_balance_type = COALESCE(spec_balance_type, balance),
            spec_max_tension = COALESCE(
                spec_max_tension,
                CASE
                    WHEN weight_class = '3U' THEN 'Up to 29 lbs'
                    ELSE 'Up to 28 lbs'
                END
            ),
            spec_length = COALESCE(spec_length, '675 mm')
        WHERE weight_class IS NOT NULL AND weight_class != ''
          AND spec_material IS NULL
    ''')



    # ตาราง review_media สำหรับรูปภาพและวิดีโอแนบรีวิวสินค้า (0–5 ไฟล์ต่อรีวิว)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS review_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER NOT NULL,
        kind TEXT NOT NULL CHECK(kind IN ('image', 'video')),
        file_path TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(review_id) REFERENCES reviews(id) ON DELETE CASCADE
    )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_review_media_review ON review_media(review_id, sort_order, id)")

    # คอลัมน์รูปภาพในข้อความแชท (ส่งได้ทั้งผู้ซื้อ พนักงาน และเจ้าของร้าน)
    _ensure_column(cursor, "chat_messages", "image_path", "TEXT")

    # ตาราง review_skips สำหรับบันทึกเมื่อผู้ซื้อกด "ไม่รีวิว" เพื่อนำออกจากช่องรอรีวิวโดยไม่กระทบคะแนนสินค้า
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS review_skips (
        user_id INTEGER NOT NULL,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        PRIMARY KEY(user_id, order_id, product_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_review_skips_order ON review_skips(order_id, user_id, product_id)")

    # อัปเดต settings.shop_name เป็น AI.HERE BADᴍᴛ-Zone เฉพาะเมื่อยังเป็นค่าตั้งต้นเดิมพอดี (รันซ้ำได้ ไม่ทับชื่อที่เจ้าของตั้งเอง)
    cursor.execute(
        "UPDATE settings SET value = 'AI.HERE BADᴍᴛ-Zone' WHERE key = 'shop_name' AND value = 'Badminton Pro Shop'"
    )


def init_db():
    """ฟังก์ชันสร้างตารางทั้งหมด 20 ตารางหลัก + ส่วนขยาย v2/v3 + INDEX (เรียกซ้ำได้ ไม่ทำลายข้อมูลเดิม)"""
    reset_connection_pool()
    _backup_before_migration_if_needed()
    conn = get_connection()
    cursor = conn.cursor()

    # 1. users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        phone TEXT,
        role TEXT DEFAULT 'buyer' CHECK(role IN ('owner', 'admin', 'buyer')),
        avatar_path TEXT,
        is_online BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    )
    ''')

    # 2. addresses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipient TEXT NOT NULL,
        phone TEXT NOT NULL,
        address_line TEXT NOT NULL,
        district TEXT NOT NULL,
        province TEXT NOT NULL,
        postcode TEXT NOT NULL,
        is_default BOOLEAN DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # 3. categories
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        image_path TEXT,
        is_active BOOLEAN DEFAULT 1
    )
    ''')

    # 4. brands
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        logo_path TEXT,
        is_active BOOLEAN DEFAULT 1
    )
    ''')

    # 5. products
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        brand_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        sale_price REAL,
        sale_ends_at TIMESTAMP,
        stock INTEGER DEFAULT 0,
        image_path TEXT,
        is_active BOOLEAN DEFAULT 1,
        weight_class TEXT,
        balance TEXT,
        flex TEXT,
        level TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(category_id) REFERENCES categories(id),
        FOREIGN KEY(brand_id) REFERENCES brands(id)
    )
    ''')

    # 6. product_options
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        option_type TEXT NOT NULL,
        option_value TEXT NOT NULL,
        extra_price REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    ''')

    # 7. cart_items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        option_id INTEGER,
        qty INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY(option_id) REFERENCES product_options(id) ON DELETE SET NULL
    )
    ''')

    # 8. coupons
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_type TEXT NOT NULL CHECK(discount_type IN ('percent', 'fixed')),
        value REAL NOT NULL,
        min_order REAL DEFAULT 0,
        max_uses INTEGER,
        used_count INTEGER DEFAULT 0,
        expires_at TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')

    # 9. orders
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipient_name TEXT NOT NULL,
        recipient_phone TEXT NOT NULL,
        shipping_address TEXT NOT NULL,
        subtotal REAL NOT NULL,
        discount REAL DEFAULT 0,
        shipping_fee REAL DEFAULT 0,
        total REAL NOT NULL,
        coupon_id INTEGER,
        cancel_reason TEXT,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'checking_slip', 'paid', 'shipped', 'completed', 'cancelled')),
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(coupon_id) REFERENCES coupons(id)
    )
    ''')

    # 10. order_items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        option_id INTEGER,
        product_name TEXT NOT NULL,
        option_label TEXT,
        price_at_purchase REAL NOT NULL,
        qty INTEGER NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(option_id) REFERENCES product_options(id)
    )
    ''')

    # 11. payments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        method TEXT NOT NULL,
        amount REAL NOT NULL,
        slip_path TEXT,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'verified', 'rejected')),
        reject_reason TEXT,
        verified_by INTEGER,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        verified_at TIMESTAMP,
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(verified_by) REFERENCES users(id)
    )
    ''')

    # 12. shipments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        carrier TEXT,
        tracking_no TEXT,
        status TEXT DEFAULT 'preparing' CHECK(status IN ('preparing', 'shipped', 'delivered')),
        updated_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
    )
    ''')

    # 13. order_status_log
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_status_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        note TEXT,
        changed_by INTEGER,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(changed_by) REFERENCES users(id)
    )
    ''')

    # 14. reviews
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        order_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        UNIQUE(user_id, product_id, order_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(product_id) REFERENCES products(id),
        FOREIGN KEY(order_id) REFERENCES orders(id)
    )
    ''')

    # 15. wishlist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlist (
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        PRIMARY KEY(user_id, product_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    ''')

    # 16. chat_messages
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        sender_type TEXT NOT NULL CHECK(sender_type IN ('user', 'admin', 'ai')),
        sender_id INTEGER,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # 17. notifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # 18. settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    # 19. coupon_usages
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupon_usages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coupon_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        order_id INTEGER,
        used_at TIMESTAMP DEFAULT (datetime('now','localtime')),
        UNIQUE(coupon_id, user_id),
        FOREIGN KEY(coupon_id) REFERENCES coupons(id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
    )
    ''')

    # 20. product_addons
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_addons (
        product_id INTEGER NOT NULL,
        addon_product_id INTEGER NOT NULL,
        PRIMARY KEY(product_id, addon_product_id),
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY(addon_product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    ''')

    _ensure_column(cursor, "categories", "is_active", "BOOLEAN DEFAULT 1")
    _ensure_column(cursor, "brands", "is_active", "BOOLEAN DEFAULT 1")
    _ensure_column(cursor, "order_items", "option_label", "TEXT")
    _ensure_column(cursor, "orders", "cancel_reason", "TEXT")

    _migrate_v2(cursor)
    _migrate_v3(cursor)

    for ddl in (
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_cart_items_user ON cart_items(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_customer_time ON chat_messages(customer_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)",
    ):
        cursor.execute(ddl)

    conn.commit()
    conn.close()
    print("Database and tables have been initialized successfully.")


if __name__ == "__main__":
    init_db()
