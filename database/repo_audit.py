"""
database/repo_audit.py
จัดการตาราง audit_log แบบเพิ่มอย่างเดียว (append-only) ไม่มีฟังก์ชันแก้ไขหรือลบ
"""
from database.repo_base import use_conn


def insert_log(actor_id: int | None, actor_role: str | None, action: str,
               target_type: str = None, target_id: int = None, detail: str = None, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO audit_log (actor_id, actor_role, action, target_type, target_id, detail) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (actor_id, actor_role, action, target_type, target_id, detail),
        ).lastrowid


def list_logs(actor_id: int = None, action: str = None, date_from: str = None,
              date_to: str = None, limit: int = 30, offset: int = 0, conn=None):
    sql, params = _where_clause(actor_id, action, date_from, date_to)
    query = (
        "SELECT a.*, u.username AS actor_username, u.full_name AS actor_name "
        "FROM audit_log a LEFT JOIN users u ON u.id = a.actor_id"
        + sql + " ORDER BY a.id DESC LIMIT ? OFFSET ?"
    )
    with use_conn(conn) as c:
        return c.execute(query, [*params, int(limit), int(offset)]).fetchall()


def count_logs(actor_id: int = None, action: str = None, date_from: str = None,
               date_to: str = None, conn=None) -> int:
    sql, params = _where_clause(actor_id, action, date_from, date_to)
    with use_conn(conn) as c:
        return int(c.execute("SELECT COUNT(*) AS n FROM audit_log a" + sql, params).fetchone()["n"])


def _where_clause(actor_id, action, date_from, date_to):
    where, params = [], []
    if actor_id is not None:
        where.append("a.actor_id = ?")
        params.append(int(actor_id))
    if action:
        where.append("a.action = ?")
        params.append(str(action))
    if date_from:
        where.append("date(a.created_at) >= date(?)")
        params.append(date_from)
    if date_to:
        where.append("date(a.created_at) <= date(?)")
        params.append(date_to)
    return (" WHERE " + " AND ".join(where)) if where else "", params
