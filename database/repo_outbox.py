"""
database/repo_outbox.py
จัดการตาราง email_outbox และ staff_messages สำหรับคิวส่งอีเมล (ใบเสร็จ, แจ้งจัดส่ง, สรุปสต็อกต่ำ, อีเมลด่วนจากแอดมินถึงเจ้าของร้าน)
"""
from database.repo_base import use_conn


def create_outbox(kind: str, to_email: str, subject: str, body_text: str, body_html: str = None,
                  attachment_path: str = None, related_order_id: int = None, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute(
            '''INSERT INTO email_outbox
               (kind, to_email, subject, body_text, body_html, attachment_path, related_order_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')''',
            (kind, to_email, subject, body_text, body_html, attachment_path, related_order_id),
        ).lastrowid


def get_outbox(outbox_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM email_outbox WHERE id = ?", (outbox_id,)).fetchone()


def get_by_order_and_kind(order_id: int, kind: str, conn=None):
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM email_outbox WHERE related_order_id = ? AND kind = ? ORDER BY id DESC LIMIT 1",
            (order_id, kind),
        ).fetchone()


def mark_sent(outbox_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE email_outbox SET status = 'sent', attempts = attempts + 1, last_error = NULL, "
            "sent_at = datetime('now','localtime') WHERE id = ?",
            (outbox_id,),
        ).rowcount > 0


def mark_failed(outbox_id: int, error_msg: str, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE email_outbox SET status = 'failed', attempts = attempts + 1, last_error = ? WHERE id = ?",
            (str(error_msg or "")[:500], outbox_id),
        ).rowcount > 0


def reset_for_resend(outbox_id: int, to_email: str = None, attachment_path: str = None, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE email_outbox SET status = 'pending', to_email = COALESCE(?, to_email), "
            "attachment_path = COALESCE(?, attachment_path), last_error = NULL WHERE id = ?",
            (to_email, attachment_path, outbox_id),
        ).rowcount > 0


def list_retryable(max_attempts: int = 3, conn=None):
    with use_conn(conn) as c:
        return c.execute(
            "SELECT * FROM email_outbox WHERE status IN ('pending', 'failed') AND attempts < ? ORDER BY id",
            (int(max_attempts),),
        ).fetchall()


# ---------- staff_messages (แอดมินส่งอีเมลด่วนถึงเจ้าของร้าน) ----------

def create_staff_message(admin_id: int, subject: str, body: str, sent_ok: bool = False, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO staff_messages (admin_id, subject, body, sent_ok) VALUES (?, ?, ?, ?)",
            (admin_id, subject, body, 1 if sent_ok else 0),
        ).lastrowid


def count_recent_staff_messages(admin_id: int, within_seconds: int = 3600, conn=None) -> int:
    with use_conn(conn) as c:
        row = c.execute(
            "SELECT COUNT(*) AS n FROM staff_messages WHERE admin_id = ? "
            "AND created_at >= datetime('now','localtime', ?)",
            (admin_id, f"-{int(within_seconds)} seconds"),
        ).fetchone()
        return int(row["n"]) if row else 0


def list_staff_messages(limit: int = 50, conn=None):
    with use_conn(conn) as c:
        return c.execute(
            "SELECT m.*, u.full_name AS admin_name, u.email AS admin_email "
            "FROM staff_messages m JOIN users u ON u.id = m.admin_id "
            "ORDER BY m.id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
