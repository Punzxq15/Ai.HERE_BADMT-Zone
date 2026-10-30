"""
database/repo_coupons.py
คูปองส่วนลด + การใช้คูปอง + กฎซื้อครบรับคูปอง (coupon_rules) + การกดรับคูปอง (coupon_claims)
ไม่มี business logic (การตรวจหมดอายุ/ขั้นต่ำ/ใช้ซ้ำ อยู่ที่ coupon_service)
"""
from database.repo_base import use_conn

_COUPON_FIELDS = (
    "code", "discount_type", "value", "min_order", "max_uses", "expires_at", "is_active",
    "owner_user_id", "source_rule_id", "source_order_id", "claimable", "max_discount", "starts_at",
    "is_free_shipping", "daily_reset_12", "code_prefix", "last_reset_date",
    "claim_start_time", "claim_end_time", "repeat_daily", "coupon_category",
)


def get_by_code(code: str, conn=None):
    """หาคูปองจากโค้ด (ไม่สนตัวพิมพ์เล็ก/ใหญ่ และตัดช่องว่างหัวท้าย) หรือ None"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM coupons WHERE code = ? COLLATE NOCASE",
                         ((code or "").strip(),)).fetchone()


def get(coupon_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM coupons WHERE id = ?", (coupon_id,)).fetchone()


def list_all(conn=None):
    """คูปองทั้งหมด ใหม่สุดก่อน"""
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM coupons ORDER BY id DESC").fetchall()


def create(code: str, discount_type: str, value: float, min_order: float = 0, max_uses=None,
           expires_at=None, is_active: bool = True, owner_user_id: int = None,
           source_rule_id: int = None, source_order_id: int = None, claimable: bool = False,
           max_discount: float = None, starts_at: str = None, is_free_shipping: bool = False,
           daily_reset_12: bool = False, code_prefix: str = None, last_reset_date: str = None,
           claim_start_time: str = None, claim_end_time: str = None, repeat_daily: bool = False,
           coupon_category: str = None, conn=None) -> int:
    """สร้างคูปอง คืน id (โค้ดซ้ำ -> sqlite3.IntegrityError)"""
    if not coupon_category:
        if is_free_shipping:
            coupon_category = "free_shipping"
        elif discount_type == "percent":
            coupon_category = "percent"
        elif discount_type == "fixed":
            coupon_category = "fixed"
        else:
            coupon_category = "other"
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO coupons (code, discount_type, value, min_order, max_uses, expires_at, is_active, "
            "owner_user_id, source_rule_id, source_order_id, claimable, max_discount, starts_at, "
            "is_free_shipping, daily_reset_12, code_prefix, last_reset_date, claim_start_time, claim_end_time, "
            "repeat_daily, coupon_category) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, discount_type, value, min_order, max_uses, expires_at, 1 if is_active else 0,
             owner_user_id, source_rule_id, source_order_id, 1 if claimable else 0, max_discount, starts_at,
             1 if is_free_shipping else 0, 1 if daily_reset_12 else 0, code_prefix, last_reset_date,
             claim_start_time, claim_end_time, 1 if repeat_daily else 0, coupon_category),
        ).lastrowid


def update(coupon_id: int, fields: dict, conn=None) -> bool:
    """แก้เฉพาะคอลัมน์ที่ส่งมา"""
    if not fields:
        return False
    bad = [k for k in fields if k not in _COUPON_FIELDS]
    if bad:
        raise ValueError(f"คอลัมน์คูปองไม่ถูกต้อง: {', '.join(bad)}")
    sets = ", ".join(f"{k} = ?" for k in fields)
    with use_conn(conn) as c:
        return c.execute(f"UPDATE coupons SET {sets} WHERE id = ?",
                         [*fields.values(), coupon_id]).rowcount > 0


def delete(coupon_id: int, conn=None) -> bool:
    """ลบคูปองออกจากระบบอย่างปลอดภัย (ปลดการอ้างอิงใน orders ก่อนลบเพื่อไม่ให้ติด FK)"""
    with use_conn(conn) as c:
        c.execute("UPDATE orders SET coupon_id = NULL WHERE coupon_id = ?", (coupon_id,))
        c.execute("DELETE FROM coupon_usages WHERE coupon_id = ?", (coupon_id,))
        c.execute("DELETE FROM coupon_claims WHERE coupon_id = ?", (coupon_id,))
        return c.execute("DELETE FROM coupons WHERE id = ?", (coupon_id,)).rowcount > 0


def set_active(coupon_id: int, active: bool, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("UPDATE coupons SET is_active = ? WHERE id = ?",
                         (1 if active else 0, coupon_id)).rowcount > 0


def increment_used(coupon_id: int, conn=None) -> bool:
    """
    นับการใช้ +1 แบบ atomic — คืน False ถ้าสิทธิ์เต็มแล้ว (used_count >= max_uses)
    (กันสองคนใช้สิทธิ์สุดท้ายพร้อมกัน)
    """
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE coupons SET used_count = used_count + 1 WHERE id = ? "
            "AND (max_uses IS NULL OR used_count < max_uses)", (coupon_id,),
        ).rowcount > 0


def decrement_used(coupon_id: int, conn=None) -> bool:
    """คืนสิทธิ์ -1 (ไม่ต่ำกว่า 0) ตอนยกเลิกออเดอร์"""
    with use_conn(conn) as c:
        return c.execute("UPDATE coupons SET used_count = MAX(used_count - 1, 0) WHERE id = ?",
                         (coupon_id,)).rowcount > 0


def add_usage(coupon_id: int, user_id: int, order_id: int, conn=None) -> int:
    """บันทึกว่าผู้ใช้ใช้คูปองนี้แล้ว (ซ้ำ -> sqlite3.IntegrityError จาก UNIQUE(coupon_id,user_id))"""
    with use_conn(conn) as c:
        c.execute(
            "UPDATE coupon_claims SET used_at = datetime('now','localtime') WHERE user_id = ? AND coupon_id = ?",
            (user_id, coupon_id),
        )
        return c.execute("INSERT INTO coupon_usages (coupon_id, user_id, order_id) VALUES (?, ?, ?)",
                         (coupon_id, user_id, order_id)).lastrowid


def has_used(user_id: int, coupon_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("SELECT 1 FROM coupon_usages WHERE user_id = ? AND coupon_id = ?",
                         (user_id, coupon_id)).fetchone() is not None


def remove_usage(order_id: int, conn=None) -> bool:
    """ลบบันทึกการใช้คูปองของออเดอร์นั้น (ตอนยกเลิก เพื่อให้ผู้ใช้ใช้ได้อีก)"""
    with use_conn(conn) as c:
        row = c.execute("SELECT coupon_id, user_id FROM coupon_usages WHERE order_id = ?", (order_id,)).fetchone()
        if row:
            c.execute(
                "UPDATE coupon_claims SET used_at = NULL WHERE user_id = ? AND coupon_id = ?",
                (row["user_id"], row["coupon_id"]),
            )
        return c.execute("DELETE FROM coupon_usages WHERE order_id = ?", (order_id,)).rowcount > 0


def clear_user_usage(user_id: int, coupon_id: int, conn=None) -> bool:
    """ล้างประวัติการใช้คูปองใบนี้ของผู้ใช้เมื่อกดรับโค้ดใหม่ (1 โค้ดใช้ได้ 1 ครั้งจนกว่าจะกดรับใหม่)"""
    with use_conn(conn) as c:
        return c.execute(
            "DELETE FROM coupon_usages WHERE user_id = ? AND coupon_id = ?",
            (user_id, coupon_id),
        ).rowcount > 0


def reset_coupon_daily(coupon_id: int, new_code: str, reset_date: str, conn=None) -> bool:
    """รีเซ็ตโค้ดประจำวันเวลา 12:00 น.: เปลี่ยนรหัสโค้ดใหม่ ล้างสิทธิ์เก่าที่ยังไม่ใช้ และให้กดรับได้ใหม่"""
    with use_conn(conn) as c:
        c.execute("DELETE FROM coupon_claims WHERE coupon_id = ?", (coupon_id,))
        c.execute("DELETE FROM coupon_usages WHERE coupon_id = ?", (coupon_id,))
        return c.execute(
            "UPDATE coupons SET code = ?, used_count = 0, last_reset_date = ? WHERE id = ?",
            (new_code, reset_date, coupon_id),
        ).rowcount > 0


# ---------- กฎซื้อครบรับคูปอง (coupon_rules — OWN-1) ----------

def list_rules(active_only: bool = False, conn=None):
    sql = "SELECT * FROM coupon_rules" + (" WHERE is_active = 1" if active_only else "") + " ORDER BY trigger_min_spend ASC, id ASC"
    with use_conn(conn) as c:
        return c.execute(sql).fetchall()


def get_rule(rule_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM coupon_rules WHERE id = ?", (rule_id,)).fetchone()


def create_rule(name: str, trigger_min_spend: float, reward_type: str, reward_value: float,
                reward_min_order: float = 0, reward_valid_days: int = 30, is_active: bool = True, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO coupon_rules (name, trigger_min_spend, reward_type, reward_value, "
            "reward_min_order, reward_valid_days, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, trigger_min_spend, reward_type, reward_value, reward_min_order,
             int(reward_valid_days), 1 if is_active else 0),
        ).lastrowid


def update_rule(rule_id: int, name: str, trigger_min_spend: float, reward_type: str,
                reward_value: float, reward_min_order: float = 0, reward_valid_days: int = 30,
                is_active: bool = True, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE coupon_rules SET name = ?, trigger_min_spend = ?, reward_type = ?, reward_value = ?, "
            "reward_min_order = ?, reward_valid_days = ?, is_active = ? WHERE id = ?",
            (name, trigger_min_spend, reward_type, reward_value, reward_min_order,
             int(reward_valid_days), 1 if is_active else 0, rule_id),
        ).rowcount > 0


def set_rule_active(rule_id: int, active: bool, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("UPDATE coupon_rules SET is_active = ? WHERE id = ?",
                         (1 if active else 0, rule_id)).rowcount > 0


def delete_rule(rule_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("DELETE FROM coupon_rules WHERE id = ?", (rule_id,)).rowcount > 0


# ---------- การกดรับคูปอง (coupon_claims — BUY-1 / D10) ----------

def claim_coupon(user_id: int, coupon_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO coupon_claims (user_id, coupon_id, claimed_at, used_at) "
            "VALUES (?, ?, datetime('now','localtime'), NULL) "
            "ON CONFLICT(user_id, coupon_id) DO UPDATE SET claimed_at = datetime('now','localtime'), used_at = NULL",
            (user_id, coupon_id),
        ).rowcount > 0


def has_claimed(user_id: int, coupon_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "SELECT 1 FROM coupon_claims WHERE user_id = ? AND coupon_id = ?",
            (user_id, coupon_id),
        ).fetchone() is not None


def list_claimable_coupons(conn=None):
    """คูปองสาธารณะที่เปิดให้กดรับได้ (claimable=1 หรือคูปองสาธารณะที่ไม่มี owner_user_id และเปิดใช้งานอยู่)"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM coupons WHERE is_active = 1 AND owner_user_id IS NULL "
            "AND (expires_at IS NULL OR expires_at > datetime('now','localtime')) "
            "AND (max_uses IS NULL OR used_count < max_uses) ORDER BY id DESC"
        ).fetchall()


def list_public_shop_coupons(conn=None):
    """คูปองสาธารณะทั้งหมดของร้านที่เปิดใช้งานอยู่ (แสดงในหน้า 'คูปองทั้งหมดที่มี' — T06)"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM coupons WHERE is_active = 1 AND owner_user_id IS NULL ORDER BY id DESC"
        ).fetchall()


def list_user_coupons(user_id: int, conn=None):
    """คูปองของผู้ซื้อคนนี้: คูปองรางวัลส่วนตัว (owner_user_id = user_id) + คูปองที่กดรับไว้ใน coupon_claims"""
    with use_conn(conn) as c:
        return c.execute(
            '''SELECT DISTINCT c.* FROM coupons c
               LEFT JOIN coupon_claims cc ON cc.coupon_id = c.id AND cc.user_id = ?
               WHERE (c.owner_user_id = ? OR cc.user_id IS NOT NULL)
               ORDER BY c.id DESC''',
            (user_id, user_id),
        ).fetchall()
