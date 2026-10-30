"""
database/repo_banners.py
จัดการตาราง banners สำหรับแบนเนอร์เลื่อนอัตโนมัติในหน้าแรก
และตาราง login_banners สำหรับแบนเนอร์รูปรองเท้าสุ่มสลับในหน้า Login & Sign Up (สูงสุด 7 รูป)
"""
from database.repo_base import use_conn

MAX_LOGIN_BANNERS = 7


def list_banners(active_only: bool = True, conn=None):
    sql = "SELECT * FROM banners"
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY sort_order ASC, id ASC"
    with use_conn(conn) as c:
        return c.execute(sql).fetchall()


def get_banner(banner_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM banners WHERE id = ?", (banner_id,)).fetchone()


def count_active_banners(conn=None) -> int:
    with use_conn(conn) as c:
        return int(c.execute("SELECT COUNT(*) AS n FROM banners WHERE is_active = 1").fetchone()["n"])


def create_banner(image_path: str, link_url: str = None, alt_text: str = None,
                  sort_order: int = None, is_active: bool = True, created_by: int = None,
                  title: str = None, subtitle: str = None, conn=None) -> int:
    with use_conn(conn) as c:
        if sort_order is None:
            max_order = c.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM banners").fetchone()["m"]
            sort_order = int(max_order) + 1
        return c.execute(
            "INSERT INTO banners (image_path, link_url, alt_text, title, subtitle, sort_order, is_active, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (image_path or "", link_url, alt_text, title or alt_text, subtitle,
             int(sort_order), 1 if is_active else 0, created_by),
        ).lastrowid


def update_banner(banner_id: int, link_url: str = None, alt_text: str = None,
                  title: str = None, subtitle: str = None, image_path: str = None, conn=None) -> bool:
    with use_conn(conn) as c:
        row = c.execute("SELECT * FROM banners WHERE id = ?", (banner_id,)).fetchone()
        if row is None:
            return False
        new_img = image_path if image_path is not None else row["image_path"]
        new_title = title if title is not None else (alt_text if alt_text is not None else row["title"])
        new_sub = subtitle if subtitle is not None else row["subtitle"]
        new_alt = alt_text if alt_text is not None else new_title
        return c.execute(
            "UPDATE banners SET image_path = ?, link_url = ?, alt_text = ?, title = ?, subtitle = ? WHERE id = ?",
            (new_img, link_url, new_alt, new_title, new_sub, banner_id),
        ).rowcount > 0


def set_banner_active(banner_id: int, active: bool, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE banners SET is_active = ? WHERE id = ?",
            (1 if active else 0, banner_id),
        ).rowcount > 0


def reorder_banners(ordered_ids, conn=None) -> None:
    with use_conn(conn) as c:
        for idx, bid in enumerate(ordered_ids, start=1):
            c.execute("UPDATE banners SET sort_order = ? WHERE id = ?", (idx, int(bid)))


def delete_banner(banner_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("DELETE FROM banners WHERE id = ?", (banner_id,)).rowcount > 0


# ==========================================
# ตาราง login_banners (หน้า Login & Sign Up — สูงสุด 7 รูป)
# ==========================================

def list_login_banners(conn=None):
    with use_conn(conn) as c:
        return c.execute(
            "SELECT id, file_path, sort_order, created_at FROM login_banners ORDER BY sort_order ASC, id ASC"
        ).fetchall()


def get_login_banner(banner_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute(
            "SELECT id, file_path, sort_order, created_at FROM login_banners WHERE id = ?",
            (int(banner_id),),
        ).fetchone()


def count_login_banners(conn=None) -> int:
    with use_conn(conn) as c:
        return int(c.execute("SELECT COUNT(*) AS n FROM login_banners").fetchone()["n"])


def create_login_banner(file_path: str, sort_order: int = None, conn=None) -> int:
    clean_path = str(file_path or "").strip()
    if not clean_path:
        raise ValueError("กรุณาระบุไฟล์รูปแบนเนอร์")
    with use_conn(conn) as c:
        cnt = int(c.execute("SELECT COUNT(*) AS n FROM login_banners").fetchone()["n"])
        if cnt >= MAX_LOGIN_BANNERS:
            raise ValueError(f"สามารถตั้งค่ารูปแบนเนอร์หน้า Login & Sign Up ได้สูงสุดไม่เกิน {MAX_LOGIN_BANNERS} รูป")
        if sort_order is None:
            max_order = c.execute("SELECT COALESCE(MAX(sort_order), 0) AS m FROM login_banners").fetchone()["m"]
            sort_order = int(max_order) + 1
        return c.execute(
            "INSERT INTO login_banners (file_path, sort_order) VALUES (?, ?)",
            (clean_path, int(sort_order)),
        ).lastrowid


def reorder_login_banners(ordered_ids, conn=None) -> None:
    with use_conn(conn) as c:
        for idx, bid in enumerate(ordered_ids or [], start=1):
            c.execute("UPDATE login_banners SET sort_order = ? WHERE id = ?", (idx, int(bid)))


def delete_login_banner(banner_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("DELETE FROM login_banners WHERE id = ?", (int(banner_id),)).rowcount > 0
