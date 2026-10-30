"""
services/banner_service.py
จัดการแบนเนอร์เลื่อนอัตโนมัติหน้าแรก (E2 + ข้อ 2)
และแบนเนอร์รูปรองเท้าสุ่มสลับในหน้า Login & Sign Up (สูงสุด 7 รูป — จัดการโดย Owner เท่านั้น)
"""
import config
from core import permissions
from core.session import Session
from database import repo_banners
from database.db import transaction
from services import audit_service, settings_service
from utils import image_utils, validators

MAX_ACTIVE_BANNERS = 10
MIN_RECOMMENDED_BANNERS = 1
MAX_LOGIN_BANNERS = repo_banners.MAX_LOGIN_BANNERS

DEFAULT_BANNERS = (
    {
        "id": -1,
        "title": "AI.HERE BADᴍᴛ-Zone — อุปกรณ์แบดมินตันครบวงจร",
        "subtitle": "ไม้แบดมินตัน ลูกขนไก่ รองเท้า กระเป๋า และบริการขึ้นเอ็นมาตรฐานแข่งขัน",
        "badge": "OFFICIAL PRO STORE",
        "accent": "yellow",
        "action_route": "category",
        "action_params": {},
        "image_path": None,
    },
    {
        "id": -2,
        "title": "FLASH SALE ลดแรงทุกรุ่นฮิต สูงสุด 30%",
        "subtitle": "ช้อปไม้แบดและอุปกรณ์ราคาพิเศษจำนวนจำกัด รีบสั่งก่อนหมดเวลา!",
        "badge": "HOT DEAL",
        "accent": "red",
        "action_route": "category",
        "action_params": {"on_sale": True},
        "image_path": None,
    },
    {
        "id": -3,
        "title": "ซื้อครบ 3,000 บาท รับฟรี! คูปองลด 300 บาท",
        "subtitle": "รับคูปองส่วนลดอัตโนมัติเมื่อคำสั่งซื้อสำเร็จ ใช้ลดในออเดอร์ถัดไปเมื่อช้อปขั้นต่ำ 1,000 บาท",
        "badge": "REWARD COUPON",
        "accent": "yellow",
        "action_route": "category",
        "action_params": {},
        "image_path": None,
    },
    {
        "id": -4,
        "title": "ตัวช่วยเลือกไม้ & AI แนะนำไม้แบดคู่ใจ 3 รุ่น",
        "subtitle": "วิเคราะห์ตามระดับฝีมือ สไตล์การเล่น (บุก/รับ/สปีด) ความแข็งก้าน และงบประมาณของคุณ",
        "badge": "SMART RACKET FINDER",
        "accent": "dark",
        "action_route": "racket_finder",
        "action_params": {},
        "image_path": None,
    },
    {
        "id": -5,
        "title": "เปรียบเทียบสเปกไม้แบดได้สูงสุด 2 ถึง 5 รุ่นพร้อมกัน",
        "subtitle": "เทียบน้ำหนัก จุดสมดุล ความแข็งก้าน ราคา และคะแนนรีวิวแบบชัดๆ ก่อนตัดสินใจ",
        "badge": "COMPARE 2-5 RACKETS",
        "accent": "red",
        "action_route": "compare",
        "action_params": {},
        "image_path": None,
    },
    {
        "id": -6,
        "title": "รวมแบรนด์ชั้นนำ YONEX · VICTOR · LI-NING · APACS · VS",
        "subtitle": "สินค้าของแท้ 100% คัดสรรสำหรับผู้เล่นตั้งแต่ระดับเริ่มต้นจนถึงนักกีฬาอาชีพ",
        "badge": "TOP BRANDS",
        "accent": "yellow",
        "action_route": "category",
        "action_params": {},
        "image_path": None,
    },
    {
        "id": -7,
        "title": "ชำระเงินง่ายด้วย PromptPay QR พร้อมส่งใบเสร็จทางอีเมล",
        "subtitle": "แนบสลิปสะดวก ตรวจสอบไว พร้อมแจ้งเลขพัสดุและดาวน์โหลดใบเสร็จ PDF ได้ทุกออเดอร์",
        "badge": "FAST & SECURE",
        "accent": "dark",
        "action_route": "orders",
        "action_params": {},
        "image_path": None,
    },
)


def _clean_link(link_url: str | None) -> str | None:
    text = str(link_url or "").strip()
    if not text:
        return None
    if text.startswith("/"):
        if len(text) > 200 or "javascript:" in text.lower():
            raise ValueError("ลิงก์ภายในไม่ถูกต้อง")
        return text
    if text in ("category", "racket_finder", "compare", "orders", "cart", "wishlist", "home"):
        return f"/{text}"
    if not validators.is_valid_https_url(text):
        raise ValueError("ลิงก์ปลายทางต้องขึ้นต้นด้วย https:// หรือเป็นเส้นทางภายในที่ขึ้นต้นด้วย /")
    return text[:300]


def list_active_banners() -> list[dict]:
    shop_name = settings_service.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"
    db_rows = [dict(r) for r in repo_banners.list_banners(active_only=True)]
    if db_rows:
        out = []
        for idx, b in enumerate(db_rows[:MAX_ACTIVE_BANNERS]):
            title = (b.get("title") or b.get("alt_text") or "").strip() or f"โปรโมชั่นพิเศษ {shop_name} #{idx + 1}"
            subtitle = (b.get("subtitle") or b.get("link_url") or "").strip() or (
                "อุปกรณ์แบดมินตันคุณภาพจากแบรนด์ชั้นนำ ช้อปเลยที่หน้าร้านและออนไลน์"
            )
            b["title"] = title
            b["subtitle"] = subtitle
            b["image_path"] = b.get("image_path") or None
            b.setdefault("badge", "PROMOTION")
            b.setdefault("accent", "yellow" if idx % 2 == 0 else "red")
            link = str(b.get("link_url") or "").strip()
            if link.startswith("/") and link.lstrip("/") in ("category", "racket_finder", "compare", "orders"):
                b.setdefault("action_route", link.lstrip("/"))
            else:
                b.setdefault("action_route", "category")
            b.setdefault("action_params", {})
            out.append(b)
        return out

    folder = config.BANNER_IMAGES_DIR
    if folder.is_dir():
        files = sorted(
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in config.ALLOWED_IMAGE_EXTENSIONS
        )
        if files:
            return [
                {
                    "id": -(idx + 1),
                    "image_path": f.relative_to(config.BASE_DIR).as_posix(),
                    "alt_text": f.stem,
                    "title": f"โปรโมชั่นพิเศษ {shop_name} #{idx + 1}",
                    "subtitle": "อุปกรณ์แบดมินตันคุณภาพจากแบรนด์ชั้นนำ",
                    "badge": "SPECIAL OFFER",
                    "accent": "yellow" if idx % 2 == 0 else "red",
                    "action_route": "category",
                    "action_params": {},
                }
                for idx, f in enumerate(files[:MAX_ACTIVE_BANNERS])
            ]

    defaults = [dict(b) for b in DEFAULT_BANNERS]
    if defaults:
        defaults[0]["title"] = f"{shop_name} — อุปกรณ์แบดมินตันครบวงจร"
    return defaults


def list_banners() -> list[dict]:
    """รายการแบนเนอร์ทั้งหมดในฐานข้อมูลสำหรับหน้าจัดการของ Owner / Admin"""
    permissions.require(permissions.BANNER_MANAGE)
    rows = [dict(r) for r in repo_banners.list_banners(active_only=False)]
    for idx, b in enumerate(rows):
        b["title"] = (b.get("title") or b.get("alt_text") or "").strip() or f"แบนเนอร์ #{idx + 1}"
        b["subtitle"] = (b.get("subtitle") or "").strip()
    return rows


def add_banner(src_path=None, link_url: str = None, alt_text: str = None, is_active: bool = True,
               title: str = None, subtitle: str = None) -> dict:
    permissions.require(permissions.BANNER_MANAGE)
    if is_active and repo_banners.count_active_banners() >= MAX_ACTIVE_BANNERS:
        raise ValueError(f"เปิดแสดงแบนเนอร์ได้สูงสุดไม่เกิน {MAX_ACTIVE_BANNERS} ภาพ")
    clean_link = _clean_link(link_url)
    clean_title = str(title or alt_text or "").strip()[:150] or None
    clean_sub = str(subtitle or "").strip()[:300] or None
    clean_alt = str(alt_text or clean_title or "").strip()[:150] or None

    rel_path = ""
    if src_path and str(src_path).strip():
        s = str(src_path).strip()
        if s.startswith("assets/"):
            rel_path = s
        else:
            rel_path = image_utils.save_upload(src_path, config.BANNER_IMAGES_DIR, "banner")
    elif not clean_title:
        raise ValueError("กรุณาเลือกรูปแบนเนอร์ หรือระบุหัวข้อแบนเนอร์")

    bid = repo_banners.create_banner(
        image_path=rel_path,
        link_url=clean_link,
        alt_text=clean_alt,
        title=clean_title,
        subtitle=clean_sub,
        is_active=is_active,
        created_by=Session.get_user_id(),
    )
    audit_service.log("banner.create", "banner", bid, {"image_path": rel_path, "title": clean_title})
    return dict(repo_banners.get_banner(bid))


def update_banner(banner_id: int, link_url: str = None, alt_text: str = None,
                  title: str = None, subtitle: str = None, src_path: str = None) -> dict:
    permissions.require(permissions.BANNER_MANAGE)
    current = repo_banners.get_banner(banner_id)
    if current is None:
        raise ValueError("ไม่พบแบนเนอร์")
    clean_link = _clean_link(link_url) if link_url is not None else current["link_url"]
    clean_title = str(title if title is not None else (alt_text if alt_text is not None else (current["title"] or current["alt_text"] or ""))).strip()[:150] or None
    clean_sub = str(subtitle if subtitle is not None else (current["subtitle"] or "")).strip()[:300] or None
    clean_alt = str(alt_text if alt_text is not None else (clean_title or "")).strip()[:150] or None

    new_img = None
    if src_path is not None:
        s = str(src_path).strip()
        if s == "":
            new_img = ""
        elif s != str(current["image_path"] or ""):
            new_img = s if s.startswith("assets/") else image_utils.save_upload(src_path, config.BANNER_IMAGES_DIR, "banner")

    repo_banners.update_banner(
        banner_id,
        link_url=clean_link,
        alt_text=clean_alt,
        title=clean_title,
        subtitle=clean_sub,
        image_path=new_img,
    )
    audit_service.log("banner.update", "banner", banner_id, {"title": clean_title, "subtitle": clean_sub})
    return dict(repo_banners.get_banner(banner_id))


def set_banner_active(banner_id: int, active: bool) -> dict:
    permissions.require(permissions.BANNER_MANAGE)
    row = repo_banners.get_banner(banner_id)
    if row is None:
        raise ValueError("ไม่พบแบนเนอร์")
    if active and not row["is_active"] and repo_banners.count_active_banners() >= MAX_ACTIVE_BANNERS:
        raise ValueError(f"เปิดแสดงแบนเนอร์ได้สูงสุดไม่เกิน {MAX_ACTIVE_BANNERS} ภาพ")
    repo_banners.set_banner_active(banner_id, bool(active))
    audit_service.log("banner.set_active", "banner", banner_id, {"is_active": bool(active)})
    return dict(repo_banners.get_banner(banner_id))


def reorder_banners(ordered_ids) -> list[dict]:
    permissions.require(permissions.BANNER_MANAGE)
    ids = [int(i) for i in (ordered_ids or [])]
    repo_banners.reorder_banners(ids)
    audit_service.log("banner.reorder", "banner", None, {"order": ids})
    return list_banners()


def delete_banner(banner_id: int) -> bool:
    permissions.require(permissions.BANNER_MANAGE)
    row = repo_banners.get_banner(banner_id)
    if row is None:
        raise ValueError("ไม่พบแบนเนอร์")
    repo_banners.delete_banner(banner_id)
    if row["image_path"]:
        image_utils.delete_upload(row["image_path"])
    audit_service.log("banner.delete", "banner", banner_id)
    return True


def list_all_banners() -> list[dict]:
    return list_banners()


def save_banner(fields: dict, banner_id: int = None) -> dict:
    title = fields.get("title") or fields.get("alt_text")
    subtitle = fields.get("subtitle") if "subtitle" in fields else fields.get("link_route")
    link_url = fields.get("link_url")
    if not link_url and fields.get("link_route") and str(fields.get("link_route")).startswith(("https://", "/")):
        link_url = fields.get("link_route")
    if banner_id is not None:
        if "is_active" in fields:
            set_banner_active(banner_id, bool(fields["is_active"]))
        return update_banner(
            banner_id,
            link_url=link_url,
            alt_text=title,
            title=title,
            subtitle=subtitle,
            src_path=fields.get("image_path") if "image_path" in fields else None,
        )
    return add_banner(
        src_path=fields.get("image_path"),
        link_url=link_url,
        alt_text=title,
        title=title,
        subtitle=subtitle,
        is_active=bool(fields.get("is_active", True)),
    )


# ==========================================
# แบนเนอร์หน้า Login & Sign Up (Owner เท่านั้น, สูงสุด 7 รูป)
# ==========================================

def list_login_banners() -> list[dict]:
    """ดึงรายการรูปแบนเนอร์หน้า Login & Sign Up (สาธารณะ เรียงตาม sort_order)"""
    rows = repo_banners.list_login_banners()
    return [dict(r) for r in rows[:MAX_LOGIN_BANNERS]]


def add_login_banners(file_paths: list[str] | str) -> list[dict]:
    """
    เพิ่มรูปแบนเนอร์หน้า Login & Sign Up (Owner เท่านั้น, รวมกันห้ามเกิน 7 รูป)
    ถ้าเลือกหลายไฟล์แล้วรวมกับของเดิมเกิน 7 รูป จะแจ้งเตือนและไม่เพิ่มเลย
    """
    permissions.require(permissions.SETTINGS_MANAGE)
    if isinstance(file_paths, str):
        paths = [file_paths] if file_paths.strip() else []
    else:
        paths = [str(p).strip() for p in (file_paths or []) if str(p or "").strip()]
    if not paths:
        raise ValueError("กรุณาเลือกรูปแบนเนอร์อย่างน้อย 1 รูป")

    current_count = repo_banners.count_login_banners()
    if current_count + len(paths) > MAX_LOGIN_BANNERS:
        raise ValueError(
            f"สามารถตั้งค่ารูปแบนเนอร์หน้า Login & Sign Up ได้สูงสุดไม่เกิน {MAX_LOGIN_BANNERS} รูป "
            f"(ปัจจุบันมี {current_count} รูป เลือกเพิ่ม {len(paths)} รูป)"
        )

    resolved_paths = []
    for p in paths:
        clean_p = p.lstrip("/")
        if clean_p.startswith("assets/"):
            resolved_paths.append(clean_p)
        else:
            saved = image_utils.save_upload(p, config.LOGIN_BANNERS_DIR, "login_banner", max_side=1000)
            resolved_paths.append(saved)

    created_ids = []
    with transaction() as conn:
        for rel_p in resolved_paths:
            bid = repo_banners.create_login_banner(rel_p, conn=conn)
            created_ids.append(bid)

    audit_service.log("login_banner.create", "login_banner", created_ids[0] if len(created_ids) == 1 else None, {
        "count": len(created_ids),
        "file_paths": resolved_paths,
    })
    return list_login_banners()


def reorder_login_banners(ordered_ids: list[int]) -> list[dict]:
    """จัดลำดับรูปแบนเนอร์หน้า Login & Sign Up (Owner เท่านั้น)"""
    permissions.require(permissions.SETTINGS_MANAGE)
    ids = [int(i) for i in (ordered_ids or [])]
    repo_banners.reorder_login_banners(ids)
    audit_service.log("login_banner.reorder", "login_banner", None, {"order": ids})
    return list_login_banners()


def delete_login_banner(banner_id: int) -> list[dict]:
    """ลบรูปแบนเนอร์หน้า Login & Sign Up รายรูป (Owner เท่านั้น)"""
    permissions.require(permissions.SETTINGS_MANAGE)
    row = repo_banners.get_login_banner(banner_id)
    if row is None:
        raise ValueError("ไม่พบรูปแบนเนอร์ที่ต้องการลบ")
    repo_banners.delete_login_banner(banner_id)
    fpath = str(row["file_path"] or "").strip()
    if fpath and fpath not in config.DEFAULT_LOGIN_BANNER_FILES:
        image_utils.delete_upload(fpath)
    audit_service.log("login_banner.delete", "login_banner", int(banner_id), {"file_path": fpath})
    return list_login_banners()
