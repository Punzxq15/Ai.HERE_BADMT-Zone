"""
database/repo_reviews.py
รีวิวสินค้า (ตาราง reviews, review_media และ review_skips) — ไม่มี business logic (สิทธิ์รีวิวตรวจที่ review_service)
"""
from database.repo_base import as_list, use_conn


def create(user_id: int, product_id: int, order_id: int, rating: int, comment=None, conn=None) -> int:
    """เพิ่มรีวิว คืน id — ซ้ำ (user,product,order) หรือดาวนอก 1-5 -> sqlite3.IntegrityError"""
    with use_conn(conn) as c:
        c.execute(
            "DELETE FROM review_skips WHERE user_id = ? AND product_id = ? AND order_id = ?",
            (int(user_id), int(product_id), int(order_id)),
        )
        return c.execute(
            "INSERT INTO reviews (user_id, product_id, order_id, rating, comment) VALUES (?, ?, ?, ?, ?)",
            (user_id, product_id, order_id, rating, comment),
        ).lastrowid


def add_media_many(review_id: int, media_items: list[dict], conn=None) -> None:
    """บันทึกไฟล์สื่อแนบของรีวิว (kind: 'image'|'video', file_path, sort_order)"""
    if not media_items:
        return
    rows = [
        (
            int(review_id),
            str(m["kind"]),
            str(m["file_path"]),
            int(m.get("sort_order", idx)),
        )
        for idx, m in enumerate(media_items, start=1)
    ]
    with use_conn(conn) as c:
        c.executemany(
            "INSERT INTO review_media (review_id, kind, file_path, sort_order) VALUES (?, ?, ?, ?)",
            rows,
        )


def list_media_by_reviews(review_ids, conn=None) -> dict[int, list[dict]]:
    """ดึงสื่อแนบของหลายรีวิวในครั้งเดียว คืน {review_id: [{id, review_id, kind, file_path, sort_order, created_at}, ...]}"""
    ids = [int(i) for i in as_list(review_ids)] if review_ids else []
    result: dict[int, list[dict]] = {i: [] for i in ids}
    if not ids:
        return result
    placeholders = ",".join("?" * len(ids))
    with use_conn(conn) as c:
        rows = c.execute(
            f"SELECT id, review_id, kind, file_path, sort_order, created_at "
            f"FROM review_media WHERE review_id IN ({placeholders}) "
            f"ORDER BY review_id ASC, sort_order ASC, id ASC",
            ids,
        ).fetchall()
    for r in rows:
        rid = int(r["review_id"])
        result.setdefault(rid, []).append(dict(r))
    return result


def list_option_labels_by_order_products(pairs: list[tuple[int, int]], conn=None) -> dict[tuple[int, int], str]:
    """
    ดึงตัวเลือกที่สั่ง (option_label) ของแต่ละ (order_id, product_id) แบบ batch query เดียว
    - แสดงเฉพาะของสินค้านั้นในออเดอร์นั้นเท่านั้น
    - ถ้าสั่งสินค้านี้หลายตัวเลือกในออเดอร์เดียวกัน ให้คั่นด้วย ', '
    - ถ้าไม่มีตัวเลือก คืน ''
    """
    clean_pairs = [(int(oid), int(pid)) for oid, pid in (pairs or []) if oid and pid]
    result: dict[tuple[int, int], str] = {p: "" for p in clean_pairs}
    if not clean_pairs:
        return result
    order_ids = sorted({oid for oid, _ in clean_pairs})
    product_ids = sorted({pid for _, pid in clean_pairs})
    o_ph = ",".join("?" * len(order_ids))
    p_ph = ",".join("?" * len(product_ids))
    with use_conn(conn) as c:
        rows = c.execute(
            f"SELECT order_id, product_id, option_label "
            f"FROM order_items "
            f"WHERE order_id IN ({o_ph}) AND product_id IN ({p_ph}) "
            f"ORDER BY id ASC",
            [*order_ids, *product_ids],
        ).fetchall()
    grouped: dict[tuple[int, int], list[str]] = {}
    target_set = set(clean_pairs)
    for r in rows:
        key = (int(r["order_id"]), int(r["product_id"]))
        if key not in target_set:
            continue
        lbl = str(r["option_label"] or "").strip()
        if lbl and lbl != "-":
            lst = grouped.setdefault(key, [])
            if lbl not in lst:
                lst.append(lbl)
    for key, labels in grouped.items():
        result[key] = ", ".join(labels)
    return result


def list_by_product(product_id: int, limit: int = 10, offset: int = 0, conn=None):
    """รีวิวของสินค้า ใหม่สุดก่อน (มี reviewer_name, reviewer_avatar)"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT r.*, u.full_name AS reviewer_name, u.avatar_path AS reviewer_avatar "
            "FROM reviews r JOIN users u ON u.id = r.user_id WHERE r.product_id = ? "
            "ORDER BY r.id DESC LIMIT ? OFFSET ?", (product_id, int(limit), int(offset or 0)),
        ).fetchall()


def count_by_product(product_id: int, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute("SELECT COUNT(*) AS n FROM reviews WHERE product_id = ?",
                         (product_id,)).fetchone()["n"]


def get_summary(product_id: int, conn=None) -> tuple:
    """(คะแนนเฉลี่ย ปัด 2 ตำแหน่ง, จำนวนรีวิว) — ไม่มีรีวิว = (0.0, 0)"""
    with use_conn(conn) as c:
        row = c.execute("SELECT AVG(rating) AS a, COUNT(*) AS n FROM reviews WHERE product_id = ?",
                        (product_id,)).fetchone()
    return (round(row["a"], 2) if row["a"] is not None else 0.0, row["n"])


def get_summaries(ids, conn=None) -> dict:
    """{product_id: (avg, count)} ของทุก id ที่ขอ (ไม่มีรีวิว = (0.0, 0)) — ใช้กับกริดสินค้า"""
    ids = [int(i) for i in as_list(ids)] if ids else []
    result = {i: (0.0, 0) for i in ids}
    if not ids:
        return result
    with use_conn(conn) as c:
        rows = c.execute(
            f"SELECT product_id, AVG(rating) AS a, COUNT(*) AS n FROM reviews "
            f"WHERE product_id IN ({','.join('?' * len(ids))}) GROUP BY product_id", ids,
        ).fetchall()
    for r in rows:
        result[r["product_id"]] = (round(r["a"], 2), r["n"])
    return result


def exists(user_id: int, product_id: int, order_id: int, conn=None) -> bool:
    """ผู้ใช้รีวิวสินค้านี้ในออเดอร์นี้แล้วหรือยัง"""
    with use_conn(conn) as c:
        return c.execute("SELECT 1 FROM reviews WHERE user_id = ? AND product_id = ? AND order_id = ?",
                         (user_id, product_id, order_id)).fetchone() is not None


def is_skipped(user_id: int, product_id: int, order_id: int, conn=None) -> bool:
    """ผู้ใช้กดไม่รีวิวสินค้านี้ในออเดอร์นี้ไปแล้วหรือยัง"""
    with use_conn(conn) as c:
        return c.execute(
            "SELECT 1 FROM review_skips WHERE user_id = ? AND product_id = ? AND order_id = ?",
            (int(user_id), int(product_id), int(order_id)),
        ).fetchone() is not None


def skip(user_id: int, order_id: int, product_id: int, conn=None) -> None:
    """บันทึกว่าผู้ใช้กดไม่รีวิวสินค้านี้ในออเดอร์นี้"""
    with use_conn(conn) as c:
        c.execute(
            "INSERT OR IGNORE INTO review_skips (user_id, order_id, product_id) VALUES (?, ?, ?)",
            (int(user_id), int(order_id), int(product_id)),
        )
