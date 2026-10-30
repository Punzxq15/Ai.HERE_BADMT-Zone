"""
services/coupon_service.py
โค้ดส่วนลด + กฎซื้อครบรับคูปอง (coupon_rules — OWN-1) + ศูนย์กดรับคูปอง (coupon_claims — BUY-1) + หมวดหมู่คูปอง (T06):
- ตรวจสอบโค้ดส่วนลดและคำนวณส่วนลดฝั่ง Backend เสมอ (ป้องกันใช้ซ้ำ/ยอดไม่ถึง/หมดอายุ/ยังไม่เริ่ม/ส่วนลดติดลบ/คูปองเฉพาะบุคคลของคนอื่น)
- เจ้าของร้านเพิ่ม/แก้ไข/ลบคูปองได้ครบ (รวมโค้ดส่งฟรี, รีโค้ดอัตโนมัติเวลา 12:00 น. ทุกวัน, ตั้งช่วงเวลารับโค้ด, หมวดหมู่คูปอง)
- กฎการใช้โค้ด: 1 โค้ดใช้ได้ 1 ครั้ง จนกว่าจะกดรับใหม่
"""
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    _BKK_TZ = ZoneInfo("Asia/Bangkok")
except Exception:  # pragma: no cover
    _BKK_TZ = timezone(timedelta(hours=7))

from core import permissions
from core.constants import (
    COUPON_CAT_FIXED, COUPON_CAT_FREE_SHIPPING, COUPON_CAT_OTHER, COUPON_CAT_PERCENT,
    COUPON_CATEGORIES, COUPON_CATEGORY_LABELS, DISCOUNT_FIXED, DISCOUNT_PERCENT, DISCOUNT_TYPES,
)
from core.session import Session
from database import repo_coupons
from database.db import transaction
from services import audit_service, notification_service, settings_service
from utils.formatters import format_price, parse_datetime

_CODE_PATTERN = re.compile(r"^[A-Z0-9_-]{3,20}$")
_TIME_HM_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _bkk_now() -> datetime:
    """เวลาปัจจุบันตามเขตเวลา Asia/Bangkok (UTC+7) แบบ naive เพื่อเทียบกับ SQLite localtime ได้ตรงกัน"""
    return datetime.now(_BKK_TZ).replace(tzinfo=None)


def _col(row, key, default=None):
    try:
        val = row[key]
        return default if val is None else val
    except (KeyError, IndexError, TypeError):
        return default


def _is_expired(coupon, now: datetime | None = None) -> bool:
    expires = parse_datetime(_col(coupon, "expires_at"))
    ref = now or _bkk_now()
    return expires is not None and expires < ref


def _not_started(coupon, now: datetime | None = None) -> bool:
    starts = parse_datetime(_col(coupon, "starts_at"))
    ref = now or _bkk_now()
    return starts is not None and starts > ref


def _resolve_coupon_category(row) -> str:
    """คืนรหัสหมวดหมู่คูปอง (T06): free_shipping | percent | fixed | other หรือหมวดที่ Owner ตั้งเพิ่ม"""
    cat = str(_col(row, "coupon_category") or "").strip()
    if cat and cat not in ("percent", "fixed", "free_shipping"):
        return cat
    if int(_col(row, "is_free_shipping", 0)):
        return COUPON_CAT_FREE_SHIPPING
    if cat in (COUPON_CAT_FREE_SHIPPING, COUPON_CAT_PERCENT, COUPON_CAT_FIXED, COUPON_CAT_OTHER):
        return cat
    dtype = _col(row, "discount_type")
    if dtype == DISCOUNT_PERCENT:
        return COUPON_CAT_PERCENT
    if dtype == DISCOUNT_FIXED:
        return COUPON_CAT_FIXED
    return COUPON_CAT_OTHER


def get_coupon_categories() -> list[tuple[str, str]]:
    """
    คืนรายการ (key, label) ของหมวดหมู่คูปองทั้งหมด (T06):
    1. คูปองส่วนลดค่าส่ง
    2. คูปองส่วนลดเป็น %
    3. คูปองส่วนลดเป็น บาท
    4. และอื่นๆ (+ หมวดหมู่ที่ Owner ตั้งค่าเพิ่มใน settings)
    """
    base = [
        (COUPON_CAT_FREE_SHIPPING, COUPON_CATEGORY_LABELS[COUPON_CAT_FREE_SHIPPING]),
        (COUPON_CAT_PERCENT, COUPON_CATEGORY_LABELS[COUPON_CAT_PERCENT]),
        (COUPON_CAT_FIXED, COUPON_CATEGORY_LABELS[COUPON_CAT_FIXED]),
        (COUPON_CAT_OTHER, COUPON_CATEGORY_LABELS[COUPON_CAT_OTHER]),
    ]
    custom_raw = settings_service.get("custom_coupon_categories") or ""
    seen = {k for k, _ in base}
    for item in custom_raw.split(","):
        txt = item.strip()
        if txt and txt not in seen:
            seen.add(txt)
            base.append((txt, txt))
    return base


def get_coupon_category_label(cat_key: str) -> str:
    cat_map = dict(get_coupon_categories())
    return cat_map.get(cat_key, COUPON_CATEGORY_LABELS.get(cat_key, str(cat_key or "และอื่นๆ")))


def _check_claim_window(coupon, now: datetime | None = None) -> tuple[bool, str | None]:
    """
    ตรวจว่าคูปองนี้อยู่ในช่วงเวลาที่อนุญาตให้กดรับหรือไม่ (เช่น 10:00 - 12:00 ของวันนี้ หรือทุกวัน)
    คืน (can_claim_now, reason_if_not)
    """
    ref = now or _bkk_now()
    if _not_started(coupon, ref):
        st_txt = str(_col(coupon, "starts_at") or "")[:16]
        return False, f"ยังไม่ถึงเวลาเริ่ม ({st_txt})"
    if _is_expired(coupon, ref):
        return False, "หมดอายุแล้ว"

    start_hm = str(_col(coupon, "claim_start_time") or "").strip()
    end_hm = str(_col(coupon, "claim_end_time") or "").strip()
    if start_hm and end_hm and _TIME_HM_PATTERN.match(start_hm) and _TIME_HM_PATTERN.match(end_hm):
        cur_hm = ref.strftime("%H:%M")
        if start_hm <= end_hm:
            in_time = start_hm <= cur_hm <= end_hm
        else:
            in_time = cur_hm >= start_hm or cur_hm <= end_hm
        if not in_time:
            rep_txt = "ของทุกวัน" if int(_col(coupon, "repeat_daily", 0)) else ""
            return False, f"รับได้เฉพาะเวลา {start_hm} - {end_hm} น. {rep_txt}".strip()
    return True, None


def run_daily_noon_reset(now: datetime | None = None, conn=None) -> int:
    """
    รีเซ็ตคูปองที่ตั้งค่า daily_reset_12 = 1 อัตโนมัติทุกเวลา 12:00 น. (Asia/Bangkok UTC+7)
    - เมื่อถึงเวลา >= 12:00 น. ของวันนั้น และยังไม่ได้รีเซ็ตสำหรับรอบวันนี้:
      จะออกรหัสโค้ดประจำวันใหม่ ล้างสิทธิ์คูปองเก่าที่ยังไม่ได้รับ/ใช้ และเปิดให้ลูกค้ากดรับใหม่ได้
    """
    ref = now or _bkk_now()
    cycle_date = ref.date().isoformat() if ref.hour >= 12 else (ref.date() - timedelta(days=1)).isoformat()
    rows = repo_coupons.list_all(conn=conn)
    reset_count = 0
    for r in rows:
        if not int(_col(r, "daily_reset_12", 0)) or not int(_col(r, "is_active", 1)):
            continue
        last_rst = str(_col(r, "last_reset_date") or "").strip()
        if last_rst == cycle_date:
            continue
        # ถ้ารอบนี้เพิ่งสร้างวันนี้ก่อนเที่ยงและ last_reset_date ยังว่าง ให้บันทึก cycle_date เริ่มต้นโดยไม่เปลี่ยนโค้ดที่เพิ่งตั้ง
        if not last_rst and ref.hour < 12:
            repo_coupons.update(r["id"], {"last_reset_date": cycle_date}, conn=conn)
            continue

        prefix = str(_col(r, "code_prefix") or "").strip().upper()
        if not prefix:
            base = re.sub(r"[0-9_-]+$", "", str(r["code"])).strip().upper()
            prefix = base[:10] if len(base) >= 3 else str(r["code"])[:12]

        mmdd = ref.strftime("%m%d")
        candidate = f"{prefix}{mmdd}"[:20]
        if not _CODE_PATTERN.match(candidate):
            candidate = str(r["code"])
        existing = repo_coupons.get_by_code(candidate, conn=conn)
        if existing is not None and int(existing["id"]) != int(r["id"]):
            candidate = f"{prefix[:12]}{mmdd}{secrets.token_hex(1).upper()}"[:20]

        repo_coupons.reset_coupon_daily(r["id"], candidate, cycle_date, conn=conn)
        reset_count += 1
    return reset_count


def calculate_discount(coupon, subtotal: float, shipping_fee: float = None) -> float:
    """ส่วนลดจริงของคูปองกับยอดสินค้านี้ (ปัด 2 ตำแหน่ง ไม่เกิน max_discount และไม่เกิน subtotal)"""
    subtotal = max(float(subtotal or 0), 0.0)
    if int(_col(coupon, "is_free_shipping", 0)):
        val = float(coupon["value"] or 0)
        if shipping_fee is not None:
            cap = max(float(shipping_fee), 0.0)
            return round(min(val if val > 0 else cap, cap), 2)
        return round(min(val, subtotal), 2)
    if coupon["discount_type"] == DISCOUNT_PERCENT:
        discount = subtotal * float(coupon["value"]) / 100
        max_disc = _col(coupon, "max_discount")
        if max_disc is not None and float(max_disc) > 0:
            discount = min(discount, float(max_disc))
    else:
        discount = float(coupon["value"])
    return round(max(0.0, min(discount, subtotal)), 2)


def _format_coupon_description(coupon) -> str:
    if int(_col(coupon, "is_free_shipping", 0)):
        return f"ฟรีค่าจัดส่ง (สูงสุด {format_price(coupon['value'])})"
    if coupon["discount_type"] == DISCOUNT_PERCENT:
        desc = f"ลด {coupon['value']:g}%"
        if _col(coupon, "max_discount"):
            desc += f" (สูงสุด {format_price(_col(coupon, 'max_discount'))})"
        return desc
    return f"ลด {format_price(coupon['value'])}"


def validate_coupon(code: str, user_id: int, subtotal: float, conn=None, shipping_fee: float = None) -> dict:
    """
    ตรวจโค้ดส่วนลดของผู้ซื้อ (ไม่แก้ DB) คืน dict:
        coupon_id, code, discount_type, value, discount (บาทที่ลดจริง), description, is_free_shipping
    """
    permissions.require_self(permissions.CART_USE, user_id)
    try:
        run_daily_noon_reset(conn=conn)
    except Exception:
        pass
    code = (code or "").strip()
    if not code:
        raise ValueError("กรุณากรอกโค้ดส่วนลด")
    coupon = repo_coupons.get_by_code(code, conn=conn)
    if coupon is None:
        raise ValueError("ไม่พบโค้ดส่วนลดนี้")
    if not coupon["is_active"]:
        raise ValueError("โค้ดส่วนลดนี้ปิดใช้งานแล้ว")
    if _not_started(coupon):
        raise ValueError("โค้ดส่วนลดนี้ยังไม่ถึงเวลาเริ่มใช้งาน")
    if _is_expired(coupon):
        raise ValueError("โค้ดส่วนลดนี้หมดอายุแล้ว")
    owner_uid = _col(coupon, "owner_user_id")
    if owner_uid is not None and int(owner_uid) != int(user_id):
        raise ValueError("โค้ดส่วนลดนี้เป็นคูปองเฉพาะบุคคล คุณไม่มีสิทธิ์ใช้งาน")
    if float(subtotal or 0) < float(coupon["min_order"] or 0):
        raise ValueError(f"ยอดสั่งซื้อไม่ถึงขั้นต่ำ {format_price(coupon['min_order'])} สำหรับโค้ดนี้")
    if repo_coupons.has_used(user_id, coupon["id"], conn=conn):
        raise ValueError("คุณใช้โค้ดส่วนลดนี้ไปแล้ว (กรุณากดรับโค้ดใหม่ก่อนใช้งาน)")
    if coupon["max_uses"] is not None and coupon["used_count"] >= coupon["max_uses"]:
        raise ValueError("โค้ดส่วนลดนี้ถูกใช้ครบสิทธิ์แล้ว")

    is_free_ship = bool(int(_col(coupon, "is_free_shipping", 0)))
    discount = calculate_discount(coupon, subtotal, shipping_fee=shipping_fee if is_free_ship else None)
    description = _format_coupon_description(coupon)
    cat_key = _resolve_coupon_category(coupon)
    return {
        "coupon_id": coupon["id"],
        "code": coupon["code"],
        "discount_type": coupon["discount_type"],
        "value": coupon["value"],
        "discount": discount,
        "description": description,
        "is_free_shipping": is_free_ship,
        "coupon_category": cat_key,
        "category_label": get_coupon_category_label(cat_key),
    }


# ==========================================
# จัดการคูปอง (เจ้าของร้านเท่านั้น)
# ==========================================

def _coupon_dict(row) -> dict:
    d = dict(row)
    d["is_expired"] = _is_expired(row)
    d["not_started"] = _not_started(row)
    d["remaining"] = None if row["max_uses"] is None else max(row["max_uses"] - row["used_count"], 0)
    d["is_free_shipping"] = bool(int(_col(row, "is_free_shipping", 0)))
    d["daily_reset_12"] = bool(int(_col(row, "daily_reset_12", 0)))
    d["repeat_daily"] = bool(int(_col(row, "repeat_daily", 0)))
    d["claim_start_time"] = _col(row, "claim_start_time") or ""
    d["claim_end_time"] = _col(row, "claim_end_time") or ""
    d["code_prefix"] = _col(row, "code_prefix") or ""
    cat_key = _resolve_coupon_category(row)
    d["coupon_category"] = cat_key
    d["category_label"] = get_coupon_category_label(cat_key)
    can_claim_now, claim_reason = _check_claim_window(row)
    d["can_claim_now"] = can_claim_now
    d["claim_window_reason"] = claim_reason
    d["description"] = _format_coupon_description(row)
    return d


def _clean_time_hm(val, label: str) -> str | None:
    if val is None or str(val).strip() == "":
        return None
    txt = str(val).strip()
    if not _TIME_HM_PATTERN.match(txt):
        raise ValueError(f"รูปแบบ{label}ไม่ถูกต้อง (ใช้ HH:MM เช่น 10:00 หรือ 12:00)")
    return txt


def _clean_fields(fields: dict, current=None) -> dict:
    """ตรวจ/ทำความสะอาดฟิลด์คูปอง"""
    clean = {}
    if "code" in fields:
        code = str(fields["code"] or "").strip().upper()
        if not _CODE_PATTERN.match(code):
            raise ValueError("โค้ดต้องเป็นภาษาอังกฤษ ตัวเลข - หรือ _ ยาว 3-20 ตัวอักษร")
        clean["code"] = code

    raw_dtype = fields.get("discount_type")
    if "is_free_shipping" in fields:
        clean["is_free_shipping"] = 1 if fields["is_free_shipping"] else 0

    if "discount_type" in fields:
        if raw_dtype == "free_shipping":
            clean["discount_type"] = DISCOUNT_FIXED
            clean["is_free_shipping"] = 1
        elif raw_dtype not in DISCOUNT_TYPES:
            raise ValueError("ประเภทส่วนลดไม่ถูกต้อง")
        else:
            clean["discount_type"] = raw_dtype

    is_free_ship = bool(clean.get("is_free_shipping", _col(current, "is_free_shipping", 0) if current else 0))

    if "value" in fields:
        raw_val = fields["value"]
        if is_free_ship and (raw_val is None or str(raw_val).strip() in ("", "0", "0.0")):
            clean["value"] = 50.0
        else:
            try:
                value = round(float(str(raw_val).strip()), 2)
            except ValueError:
                raise ValueError("มูลค่าส่วนลดต้องเป็นตัวเลข") from None
            if not value > 0 or value != value or value == float("inf"):
                raise ValueError("มูลค่าส่วนลดต้องมากกว่า 0")
            clean["value"] = value

    final_type = clean.get("discount_type", current["discount_type"] if current else None)
    final_value = clean.get("value", current["value"] if current else None)
    if final_type == DISCOUNT_PERCENT and final_value is not None and final_value > 100:
        raise ValueError("ส่วนลดแบบเปอร์เซ็นต์ต้องไม่เกิน 100")

    if "min_order" in fields:
        try:
            min_order = round(float(str(fields["min_order"] or 0).strip()), 2)
        except ValueError:
            raise ValueError("ยอดสั่งซื้อขั้นต่ำต้องเป็นตัวเลข") from None
        if min_order < 0:
            raise ValueError("ยอดสั่งซื้อขั้นต่ำต้องไม่ติดลบ")
        clean["min_order"] = min_order
    if "max_discount" in fields:
        raw_md = fields["max_discount"]
        if raw_md is None or str(raw_md).strip() == "":
            clean["max_discount"] = None
        else:
            try:
                md = round(float(str(raw_md).strip()), 2)
            except ValueError:
                raise ValueError("เพดานส่วนลดสูงสุดต้องเป็นตัวเลข") from None
            if md <= 0:
                raise ValueError("เพดานส่วนลดสูงสุดต้องมากกว่า 0")
            clean["max_discount"] = md
    if "max_uses" in fields:
        raw = fields["max_uses"]
        if raw is None or str(raw).strip() == "":
            clean["max_uses"] = None
        else:
            try:
                max_uses = float(str(raw).strip())
            except ValueError:
                raise ValueError("จำนวนสิทธิ์ต้องเป็นตัวเลข") from None
            if max_uses != int(max_uses) or max_uses < 1:
                raise ValueError("จำนวนสิทธิ์ต้องเป็นจำนวนเต็มตั้งแต่ 1 ขึ้นไป (เว้นว่าง = ไม่จำกัด)")
            if current is not None and max_uses < current["used_count"]:
                raise ValueError(f"จำนวนสิทธิ์ต้องไม่น้อยกว่าที่ถูกใช้ไปแล้ว ({current['used_count']})")
            clean["max_uses"] = int(max_uses)
    if "starts_at" in fields:
        raw_st = fields["starts_at"]
        if raw_st is None or str(raw_st).strip() == "":
            clean["starts_at"] = None
        else:
            dt_st = parse_datetime(raw_st)
            if dt_st is None:
                raise ValueError("รูปแบบวันเริ่มต้นไม่ถูกต้อง (ใช้ ปปปป-ดด-วว)")
            clean["starts_at"] = dt_st.strftime("%Y-%m-%d %H:%M:%S")
    if "expires_at" in fields:
        raw = fields["expires_at"]
        if raw is None or str(raw).strip() == "":
            clean["expires_at"] = None
        else:
            dt = parse_datetime(raw)
            if dt is None:
                raise ValueError("รูปแบบวันหมดอายุไม่ถูกต้อง (ใช้ ปปปป-ดด-วว)")
            if len(str(raw).strip()) <= 10:
                dt = dt.replace(hour=23, minute=59, second=59)
            clean["expires_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")

    final_starts = clean.get("starts_at", _col(current, "starts_at") if current else None)
    final_expires = clean.get("expires_at", _col(current, "expires_at") if current else None)
    if final_starts and final_expires:
        dt_s = parse_datetime(final_starts)
        dt_e = parse_datetime(final_expires)
        if dt_s and dt_e and dt_e < dt_s:
            raise ValueError("วันหมดอายุต้องไม่ก่อนวันเริ่มต้น")

    if "claimable" in fields:
        clean["claimable"] = 1 if fields["claimable"] else 0
    if "is_active" in fields:
        clean["is_active"] = 1 if fields["is_active"] else 0
    if "daily_reset_12" in fields:
        clean["daily_reset_12"] = 1 if fields["daily_reset_12"] else 0
    if "code_prefix" in fields:
        pfx = str(fields["code_prefix"] or "").strip().upper()
        clean["code_prefix"] = pfx[:12] if pfx else None
    if "claim_start_time" in fields:
        clean["claim_start_time"] = _clean_time_hm(fields["claim_start_time"], "เวลาเริ่มรับโค้ด")
    if "claim_end_time" in fields:
        clean["claim_end_time"] = _clean_time_hm(fields["claim_end_time"], "เวลาสิ้นสุดรับโค้ด")
    if "repeat_daily" in fields:
        clean["repeat_daily"] = 1 if fields["repeat_daily"] else 0
    if "coupon_category" in fields and fields["coupon_category"]:
        clean["coupon_category"] = str(fields["coupon_category"]).strip()
    elif is_free_ship:
        clean["coupon_category"] = COUPON_CAT_FREE_SHIPPING
    elif final_type == DISCOUNT_PERCENT and (current is None or _col(current, "coupon_category") in (None, "", "percent", "fixed", "free_shipping")):
        clean["coupon_category"] = COUPON_CAT_PERCENT
    elif final_type == DISCOUNT_FIXED and (current is None or _col(current, "coupon_category") in (None, "", "percent", "fixed", "free_shipping")):
        clean["coupon_category"] = COUPON_CAT_FIXED
    return clean


def create_coupon(code: str, discount_type: str, value, min_order=0, max_uses=None,
                  expires_at=None, is_active: bool = True, claimable: bool = True,
                  max_discount=None, starts_at=None, is_free_shipping: bool = False,
                  daily_reset_12: bool = False, code_prefix: str = None,
                  claim_start_time: str = None, claim_end_time: str = None,
                  repeat_daily: bool = False, coupon_category: str = None) -> dict:
    """สร้างคูปอง (เจ้าของร้าน) — code เก็บเป็นตัวพิมพ์ใหญ่, ซ้ำ -> ValueError คืน dict คูปอง"""
    permissions.require(permissions.COUPON_MANAGE)
    clean = _clean_fields({
        "code": code, "discount_type": discount_type, "value": value,
        "min_order": min_order, "max_uses": max_uses, "expires_at": expires_at,
        "is_active": is_active, "claimable": claimable, "max_discount": max_discount,
        "starts_at": starts_at, "is_free_shipping": is_free_shipping,
        "daily_reset_12": daily_reset_12, "code_prefix": code_prefix,
        "claim_start_time": claim_start_time, "claim_end_time": claim_end_time,
        "repeat_daily": repeat_daily, "coupon_category": coupon_category,
    })
    now_bkk = _bkk_now()
    init_reset_date = (
        now_bkk.date().isoformat() if now_bkk.hour >= 12 else (now_bkk.date() - timedelta(days=1)).isoformat()
    ) if clean.get("daily_reset_12") else None
    try:
        coupon_id = repo_coupons.create(
            clean["code"], clean["discount_type"], clean["value"], clean["min_order"],
            clean["max_uses"], clean["expires_at"], bool(clean["is_active"]),
            claimable=bool(clean.get("claimable", 1)),
            max_discount=clean.get("max_discount"),
            starts_at=clean.get("starts_at"),
            is_free_shipping=bool(clean.get("is_free_shipping", 0)),
            daily_reset_12=bool(clean.get("daily_reset_12", 0)),
            code_prefix=clean.get("code_prefix"),
            last_reset_date=init_reset_date,
            claim_start_time=clean.get("claim_start_time"),
            claim_end_time=clean.get("claim_end_time"),
            repeat_daily=bool(clean.get("repeat_daily", 0)),
            coupon_category=clean.get("coupon_category"),
        )
        audit_service.log("coupon.create", "coupon", coupon_id, {"code": clean["code"], "value": clean["value"]})
    except sqlite3.IntegrityError:
        raise ValueError("มีโค้ดส่วนลดนี้อยู่แล้ว") from None
    return _coupon_dict(repo_coupons.get(coupon_id))


def update_coupon(coupon_id: int, fields: dict) -> dict:
    """แก้คูปอง (เจ้าของร้าน)"""
    permissions.require(permissions.COUPON_MANAGE)
    current = repo_coupons.get(coupon_id)
    if current is None:
        raise ValueError("ไม่พบคูปอง")
    clean = _clean_fields(dict(fields or {}), current)
    try:
        if clean:
            repo_coupons.update(coupon_id, clean)
            audit_service.log("coupon.update", "coupon", coupon_id, clean)
    except sqlite3.IntegrityError:
        raise ValueError("มีโค้ดส่วนลดนี้อยู่แล้ว") from None
    return _coupon_dict(repo_coupons.get(coupon_id))


def delete_coupon(coupon_id: int) -> bool:
    """ลบคูปอง (เจ้าของร้านเท่านั้น — ข้อ 11)"""
    permissions.require(permissions.COUPON_MANAGE)
    current = repo_coupons.get(coupon_id)
    if current is None:
        raise ValueError("ไม่พบคูปอง")
    ok = repo_coupons.delete(coupon_id)
    if ok:
        audit_service.log("coupon.delete", "coupon", coupon_id, {"code": current["code"]})
    return ok


def toggle_coupon(coupon_id: int, active: bool = None) -> dict:
    """เปิด/ปิดคูปอง (เจ้าของร้าน) — ไม่ส่ง active = สลับค่าเดิม"""
    permissions.require(permissions.COUPON_MANAGE)
    current = repo_coupons.get(coupon_id)
    if current is None:
        raise ValueError("ไม่พบคูปอง")
    new_active = (not current["is_active"]) if active is None else bool(active)
    repo_coupons.set_active(coupon_id, new_active)
    audit_service.log("coupon.toggle", "coupon", coupon_id, {"is_active": new_active})
    return _coupon_dict(repo_coupons.get(coupon_id))


def get_coupon(coupon_id: int) -> dict:
    """คูปอง 1 ใบสำหรับฟอร์มแก้ไข (เจ้าของร้าน)"""
    permissions.require(permissions.COUPON_MANAGE)
    row = repo_coupons.get(coupon_id)
    if row is None:
        raise ValueError("ไม่พบคูปอง")
    return _coupon_dict(row)


def list_coupons() -> list[dict]:
    """คูปองทั้งหมด ใหม่สุดก่อน (เจ้าของร้าน)"""
    permissions.require(permissions.COUPON_MANAGE)
    try:
        run_daily_noon_reset()
    except Exception:
        pass
    return [_coupon_dict(r) for r in repo_coupons.list_all()]


# ==========================================
# กฎซื้อครบรับคูปอง (coupon_rules — OWN-1, D9)
# ==========================================

def _clean_rule(name: str, trigger_min_spend, reward_type: str, reward_value,
                reward_min_order=0, reward_valid_days=30, is_active: bool = True) -> dict:
    name = str(name or "").strip()
    if not name:
        raise ValueError("กรุณากรอกชื่อเงื่อนไขคูปองรางวัล")
    if len(name) > 120:
        raise ValueError("ชื่อเงื่อนไขยาวเกินไป (ไม่เกิน 120 ตัวอักษร)")
    try:
        trigger = round(float(str(trigger_min_spend).strip()), 2)
    except (TypeError, ValueError):
        raise ValueError("ยอดซื้อขั้นต่ำเพื่อรับคูปองต้องเป็นตัวเลข") from None
    if trigger <= 0:
        raise ValueError("ยอดซื้อขั้นต่ำเพื่อรับคูปองต้องมากกว่า 0")
    if reward_type not in DISCOUNT_TYPES:
        raise ValueError("ประเภทส่วนลดของคูปองรางวัลไม่ถูกต้อง")
    try:
        val = round(float(str(reward_value).strip()), 2)
    except (TypeError, ValueError):
        raise ValueError("มูลค่าส่วนลดของคูปองรางวัลต้องเป็นตัวเลข") from None
    if val <= 0:
        raise ValueError("มูลค่าส่วนลดต้องมากกว่า 0")
    if reward_type == DISCOUNT_PERCENT and val > 100:
        raise ValueError("ส่วนลดเปอร์เซ็นต์ต้องไม่เกิน 100")
    try:
        min_ord = round(float(str(reward_min_order or 0).strip()), 2)
    except (TypeError, ValueError):
        raise ValueError("ยอดซื้อขั้นต่ำในการใช้คูปองครั้งถัดไปต้องเป็นตัวเลข") from None
    if min_ord < 0:
        raise ValueError("ยอดซื้อขั้นต่ำในการใช้คูปองต้องไม่ติดลบ")
    try:
        days = int(str(reward_valid_days or 30).strip())
    except (TypeError, ValueError):
        raise ValueError("อายุคูปอง (วัน) ต้องเป็นจำนวนเต็ม") from None
    if not 1 <= days <= 365:
        raise ValueError("อายุคูปองต้องอยู่ระหว่าง 1 ถึง 365 วัน")

    return {
        "name": name,
        "trigger_min_spend": trigger,
        "reward_type": reward_type,
        "reward_value": val,
        "reward_min_order": min_ord,
        "reward_valid_days": days,
        "is_active": bool(is_active),
    }


def list_rules(active_only: bool = False) -> list[dict]:
    """ดูรายการกฎ 'ซื้อครบรับคูปอง' (active_only=True สำหรับแสดงหน้าแรกให้ผู้ซื้อดูโปรโมชั่น)"""
    if not active_only:
        permissions.require(permissions.COUPON_MANAGE)
    return [dict(r) for r in repo_coupons.list_rules(active_only=active_only)]


def save_rule(name: str, trigger_min_spend, reward_type: str, reward_value,
              reward_min_order=0, reward_valid_days=30, is_active: bool = True,
              rule_id: int = None) -> dict:
    """เพิ่มหรือแก้ไขกฎซื้อครบรับคูปอง (เจ้าของร้านเท่านั้น — OWN-1)"""
    permissions.require(permissions.COUPON_MANAGE)
    clean = _clean_rule(name, trigger_min_spend, reward_type, reward_value,
                        reward_min_order, reward_valid_days, is_active)
    if rule_id is None:
        new_id = repo_coupons.create_rule(**clean)
        audit_service.log("coupon_rule.create", "coupon_rule", new_id, clean)
        return dict(repo_coupons.get_rule(new_id))
    if not repo_coupons.update_rule(rule_id, **clean):
        raise ValueError("ไม่พบกฎคูปองรางวัล")
    audit_service.log("coupon_rule.update", "coupon_rule", rule_id, clean)
    return dict(repo_coupons.get_rule(rule_id))


def toggle_rule(rule_id: int, active: bool = None) -> dict:
    permissions.require(permissions.COUPON_MANAGE)
    row = repo_coupons.get_rule(rule_id)
    if row is None:
        raise ValueError("ไม่พบกฎคูปองรางวัล")
    new_active = (not row["is_active"]) if active is None else bool(active)
    repo_coupons.set_rule_active(rule_id, new_active)
    audit_service.log("coupon_rule.toggle", "coupon_rule", rule_id, {"is_active": new_active})
    return dict(repo_coupons.get_rule(rule_id))


def delete_rule(rule_id: int) -> bool:
    permissions.require(permissions.COUPON_MANAGE)
    ok = repo_coupons.delete_rule(rule_id)
    if ok:
        audit_service.log("coupon_rule.delete", "coupon_rule", rule_id)
    return ok


def issue_reward_coupons(order_id: int, user_id: int, order_total: float, conn=None) -> list[dict]:
    """
    ออกคูปองรางวัลส่วนตัวให้ผู้ซื้ออัตโนมัติเมื่อคำสั่งซื้อสำเร็จ (completed) และยอดสุทธิ >= trigger_min_spend
    ป้องกันการออกซ้ำต่อออเดอร์ด้วย unique index ux_coupon_reward_once
    """
    issued = []
    rules = repo_coupons.list_rules(active_only=True, conn=conn)
    for rule in rules:
        if float(order_total or 0) < float(rule["trigger_min_spend"] or 0):
            continue
        code = f"RWD{order_id}-{secrets.token_hex(2).upper()}"
        expires = (_bkk_now() + timedelta(days=int(rule["reward_valid_days"] or 30))).strftime("%Y-%m-%d 23:59:59")
        try:
            cid = repo_coupons.create(
                code=code,
                discount_type=rule["reward_type"],
                value=float(rule["reward_value"]),
                min_order=float(rule["reward_min_order"] or 0),
                max_uses=1,
                expires_at=expires,
                is_active=True,
                owner_user_id=user_id,
                source_rule_id=rule["id"],
                source_order_id=order_id,
                claimable=False,
                conn=conn,
            )
        except sqlite3.IntegrityError:
            continue

        disc_txt = (f"{rule['reward_value']:g}%" if rule["reward_type"] == DISCOUNT_PERCENT
                    else format_price(rule["reward_value"]))
        min_txt = (f" (เมื่อซื้อขั้นต่ำ {format_price(rule['reward_min_order'])})"
                   if float(rule["reward_min_order"] or 0) > 0 else "")
        notification_service.notify(
            user_id,
            "ได้รับคูปองส่วนลดครั้งถัดไป!",
            f"คุณได้รับคูปอง {code} ลด {disc_txt}{min_txt} จากคำสั่งซื้อ #{order_id}",
            conn=conn,
        )
        issued.append(_coupon_dict(repo_coupons.get(cid, conn=conn)))
    return issued


# ==========================================
# ศูนย์คูปองสำหรับผู้ซื้อและผู้เยี่ยมชม (BUY-1, BUY-2, D10, T06)
# ==========================================

def _annotate_buyer_coupon(row, user_id: int = None) -> dict:
    d = _coupon_dict(row)
    if user_id is not None:
        claimed = repo_coupons.has_claimed(user_id, row["id"]) or (_col(row, "owner_user_id") == user_id)
        used = repo_coupons.has_used(user_id, row["id"])
        d["is_claimed"] = claimed and not used
        d["is_used"] = used
        d["is_personal_reward"] = _col(row, "owner_user_id") == user_id
    else:
        d["is_claimed"] = False
        d["is_used"] = False
        d["is_personal_reward"] = False

    if not row["is_active"]:
        d["status_text"] = "ปิดใช้งาน"
    elif d["is_expired"]:
        d["status_text"] = "หมดอายุ"
    elif d["not_started"]:
        d["status_text"] = "ยังไม่เริ่ม"
    elif row["max_uses"] is not None and row["used_count"] >= row["max_uses"]:
        d["status_text"] = "สิทธิ์เต็ม"
    elif d["is_used"]:
        d["status_text"] = "ใช้แล้ว (กดรับใหม่ได้)" if not d["is_personal_reward"] and d["can_claim_now"] else "ใช้แล้ว"
    elif d["is_claimed"]:
        d["status_text"] = "ใช้ได้ (เก็บแล้ว)"
    elif d["can_claim_now"]:
        d["status_text"] = "ใช้ได้ (กดเก็บได้)"
    else:
        d["status_text"] = d["claim_window_reason"] or "นอกเวลารับโค้ด"
    return d


def list_public_coupons(user_id: int = None, category: str = None) -> list[dict]:
    """
    แสดงคูปองสาธารณะที่เปิดให้กดรับได้ (ผู้เยี่ยมชมก็ดูได้ แต่ถ้าจะกดรับต้องล็อกอิน)
    """
    try:
        run_daily_noon_reset()
    except Exception:
        pass
    rows = repo_coupons.list_claimable_coupons()
    result = []
    for r in rows:
        if _is_expired(r) or _not_started(r):
            continue
        d = _annotate_buyer_coupon(r, user_id=user_id)
        if category and category != "all" and d["coupon_category"] != category:
            continue
        result.append(d)
    return result


def list_all_shop_coupons(user_id: int = None, category: str = None, include_expired: bool = False) -> list[dict]:
    """
    แสดงคูปองทั้งหมดที่ร้านมี (T06) พร้อมแยกตามหมวดหมู่คูปอง:
    - คูปองส่วนลดค่าส่ง (free_shipping)
    - คูปองส่วนลดเป็น % (percent)
    - คูปองส่วนลดเป็น บาท (fixed)
    - และอื่นๆ (other / custom)
    """
    try:
        run_daily_noon_reset()
    except Exception:
        pass
    rows = repo_coupons.list_public_shop_coupons()
    result = []
    for r in rows:
        if not include_expired and _is_expired(r):
            continue
        d = _annotate_buyer_coupon(r, user_id=user_id)
        if category and category != "all" and d["coupon_category"] != category:
            continue
        result.append(d)
    return result


def _claim_coupon_by_id(user_id: int, coupon_id: int) -> dict:
    """
    ผู้ซื้อกดรับคูปองเก็บไว้ในบัญชี (ต้องล็อกอินเป็นผู้ซื้อ)
    กฎข้อ 8: ให้ 1 โค้ดใช้ได้ 1 ครั้ง จนกว่าจะกดรับใหม่
    """
    permissions.require_self(permissions.CART_USE, user_id)
    try:
        run_daily_noon_reset()
    except Exception:
        pass
    row = repo_coupons.get(coupon_id)
    if row is None or not row["is_active"] or _is_expired(row):
        raise ValueError("คูปองนี้ไม่สามารถกดรับได้ หรือหมดอายุแล้ว")
    if _col(row, "owner_user_id") not in (None, user_id):
        raise ValueError("คูปองนี้เป็นคูปองเฉพาะบุคคลของบัญชีอื่น")
    if row["max_uses"] is not None and row["used_count"] >= row["max_uses"]:
        raise ValueError("คูปองนี้ถูกใช้ครบสิทธิ์แล้ว")

    can_claim_now, reason = _check_claim_window(row)
    if not can_claim_now:
        raise ValueError(f"ยังไม่สามารถกดรับโค้ดได้ ({reason})")

    already_used = repo_coupons.has_used(user_id, coupon_id)
    if already_used and _col(row, "owner_user_id") is not None:
        raise ValueError("คูปองรางวัลเฉพาะบุคคลนี้ถูกใช้ไปแล้ว")

    with transaction() as conn:
        if already_used:
            # กดรับโค้ดใหม่หลังใช้ไปแล้ว -> ล้างสถานะการใช้เดิมของลูกค้ารายนี้ให้ใช้ได้อีก 1 ครั้ง
            repo_coupons.clear_user_usage(user_id, coupon_id, conn=conn)
        repo_coupons.claim_coupon(user_id, coupon_id, conn=conn)

    d = _annotate_buyer_coupon(repo_coupons.get(coupon_id), user_id=user_id)
    d["is_claimed"] = True
    d["is_used"] = False
    d["claimed"] = True
    return d


def claim_coupon(first_arg, second_arg=None) -> dict:
    if isinstance(first_arg, str):
        code = first_arg.strip().upper()
        uid = int(second_arg) if second_arg is not None else Session.get_user_id()
        row = repo_coupons.get_by_code(code)
        if row is None:
            raise ValueError("ไม่พบโค้ดคูปองนี้")
        return _claim_coupon_by_id(uid, row["id"])
    return _claim_coupon_by_id(int(first_arg), int(second_arg))


def list_my_coupons(user_id: int, category: str = None) -> list[dict]:
    """รายการคูปองของฉัน (คูปองรางวัลส่วนตัวที่ได้จากการซื้อครบ + คูปองที่กดรับไว้)"""
    permissions.require_self(permissions.CART_USE, user_id)
    try:
        run_daily_noon_reset()
    except Exception:
        pass
    rows = repo_coupons.list_user_coupons(user_id)
    result = []
    for r in rows:
        d = _annotate_buyer_coupon(r, user_id=user_id)
        d["is_claimed"] = True
        if category and category != "all" and d["coupon_category"] != category:
            continue
        result.append(d)
    return result


def list_checkout_coupons(user_id: int, subtotal: float, shipping_fee: float = 0.0) -> list[dict]:
    """
    สำหรับหน้าเตรียมชำระเงิน (ข้อ 8):
    ตรวจสอบว่าลูกค้าคนนี้รับโค้ดอะไรไว้บ้าง + โค้ดสาธารณะที่กดรับเองได้ (รวมโค้ดส่งฟรี)
    พร้อมบอกสถานะว่าโค้ดนี้ใช้ได้ไหม (พร้อมเหตุผลสั้นๆ) และคำนวณส่วนลดที่จะได้รับ
    """
    permissions.require_self(permissions.CART_USE, user_id)
    try:
        run_daily_noon_reset()
    except Exception:
        pass

    subtotal = max(float(subtotal or 0), 0.0)
    shipping_fee = max(float(shipping_fee or 0), 0.0)

    user_rows = {r["id"]: r for r in repo_coupons.list_user_coupons(user_id)}
    public_rows = {r["id"]: r for r in repo_coupons.list_claimable_coupons()}
    all_ids = list(user_rows.keys()) + [cid for cid in public_rows if cid not in user_rows]

    out = []
    for cid in all_ids:
        row = user_rows.get(cid) or public_rows.get(cid)
        if row is None:
            continue
        d = _coupon_dict(row)
        claimed = cid in user_rows
        used = repo_coupons.has_used(user_id, cid)
        is_personal = _col(row, "owner_user_id") == user_id
        is_free_ship = d["is_free_shipping"]
        min_ord = float(row["min_order"] or 0)
        can_claim_now, claim_reason = _check_claim_window(row)

        can_use = False
        can_claim = False
        if not row["is_active"]:
            status_text = "ปิดใช้งาน"
            reason = "โค้ดนี้ถูกปิดการใช้งาน"
        elif _is_expired(row):
            status_text = "หมดอายุ"
            reason = "โค้ดส่วนลดหมดอายุแล้ว"
        elif _not_started(row):
            status_text = "ยังไม่เริ่ม"
            reason = "ยังไม่ถึงวันเริ่มใช้งาน"
        elif row["max_uses"] is not None and row["used_count"] >= row["max_uses"]:
            status_text = "สิทธิ์เต็ม"
            reason = "ถูกใช้ครบจำนวนสิทธิ์แล้ว"
        elif used:
            if not is_personal and can_claim_now:
                status_text = "ใช้แล้ว (กดรับใหม่ได้)"
                reason = "ใช้ไปแล้ว 1 ครั้ง กดรับโค้ดใหม่เพื่อใช้ซ้ำได้"
                can_claim = True
            elif not is_personal and not can_claim_now:
                status_text = "ใช้แล้ว"
                reason = claim_reason or "นอกช่วงเวลารับโค้ดใหม่"
            else:
                status_text = "ใช้แล้ว"
                reason = "คูปองเฉพาะบุคคลใช้ไปแล้ว"
        elif not claimed and not is_personal:
            if can_claim_now:
                status_text = "ยังไม่ได้กดรับ"
                reason = (f"กดรับโค้ดเพื่อใช้ได้ทันที (ขั้นต่ำ {format_price(min_ord)})"
                          if min_ord > 0 else "กดรับโค้ดเพื่อใช้ได้ทันที")
                can_claim = True
            else:
                status_text = "นอกเวลารับโค้ด"
                reason = claim_reason or "ไม่อยู่ในช่วงเวลารับโค้ด"
        elif subtotal < min_ord:
            status_text = "ยอดไม่ถึงขั้นต่ำ"
            reason = f"ต้องมียอดสั่งซื้อขั้นต่ำ {format_price(min_ord)} (ขาดอีก {format_price(min_ord - subtotal)})"
        elif is_free_ship and shipping_fee <= 0:
            status_text = "ส่งฟรีอยู่แล้ว"
            reason = "คำสั่งซื้อนี้ฟรีค่าจัดส่งอยู่แล้ว"
        else:
            can_use = True
            status_text = "ใช้ได้"
            disc_amt = calculate_discount(row, subtotal, shipping_fee=shipping_fee if is_free_ship else None)
            reason = f"ลดค่าจัดส่ง {format_price(disc_amt)}" if is_free_ship else f"ลดทันที {format_price(disc_amt)}"

        d.update({
            "is_claimed": claimed and not used,
            "is_used": used,
            "is_personal_reward": is_personal,
            "can_use": can_use,
            "can_claim": can_claim,
            "status_text": status_text,
            "reason": reason,
            "discount_preview": calculate_discount(row, subtotal, shipping_fee=shipping_fee if is_free_ship else None),
        })
        out.append(d)

    # เรียงโค้ดที่ใช้ได้ขึ้นก่อน ตามด้วยโค้ดที่กดรับได้ และโค้ดอื่นๆ
    out.sort(key=lambda x: (0 if x["can_use"] else (1 if x["can_claim"] else 2), -int(x["id"])))
    return out


def list_coupon_rules(active_only: bool = False) -> list[dict]:
    try:
        rows = list_rules(active_only=active_only)
    except PermissionError:
        rows = list_rules(active_only=True)
    out = []
    for r in rows:
        d = dict(r)
        d.setdefault("min_order_trigger", d.get("trigger_min_spend", 0))
        d.setdefault("discount_type", d.get("reward_type", DISCOUNT_PERCENT))
        d.setdefault("discount_value", d.get("reward_value", 0))
        d.setdefault("min_order_next", d.get("reward_min_order", 0))
        d.setdefault("valid_days", d.get("reward_valid_days", 30))
        d.setdefault("code_prefix", d.get("code_prefix") or "RWD")
        out.append(d)
    return out


def save_coupon_rule(fields: dict, rule_id: int = None) -> dict:
    saved = save_rule(
        name=fields.get("name") or "โปรซื้อครบรับคูปอง",
        trigger_min_spend=fields.get("min_order_trigger", fields.get("trigger_min_spend", 0)),
        reward_type=fields.get("discount_type", fields.get("reward_type", DISCOUNT_PERCENT)),
        reward_value=fields.get("discount_value", fields.get("reward_value", 10)),
        reward_min_order=fields.get("min_order_next", fields.get("reward_min_order", 0)),
        reward_valid_days=fields.get("valid_days", fields.get("reward_valid_days", 30)),
        is_active=bool(fields.get("is_active", True)),
        rule_id=rule_id,
    )
    prefix = (fields.get("code_prefix") or "RWD").strip().upper()
    saved["code_prefix"] = prefix
    saved["min_order_trigger"] = saved.get("trigger_min_spend", 0)
    saved["discount_type"] = saved.get("reward_type")
    saved["discount_value"] = saved.get("reward_value")
    saved["min_order_next"] = saved.get("reward_min_order", 0)
    saved["valid_days"] = saved.get("reward_valid_days", 30)
    return saved


def delete_coupon_rule(rule_id: int) -> bool:
    return delete_rule(rule_id)


def evaluate_and_issue_reward_coupons(user_id: int, order_total: float, order_id: int = 99999) -> list[dict]:
    return issue_reward_coupons(order_id=order_id, user_id=user_id, order_total=order_total)
