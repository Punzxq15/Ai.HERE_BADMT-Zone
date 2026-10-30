"""
database/repo_expenses.py
จัดการตาราง expenses (รายจ่ายของร้าน สำหรับรายงานรายรับ-รายจ่ายและส่งออก .xlsx)
"""
from database.repo_base import use_conn


def create_expense(spent_on: str, category: str, amount: float, note: str = None,
                   created_by: int = None, conn=None) -> int:
    with use_conn(conn) as c:
        return c.execute(
            "INSERT INTO expenses (spent_on, category, amount, note, created_by) VALUES (?, ?, ?, ?, ?)",
            (spent_on, category, round(float(amount), 2), note, created_by),
        ).lastrowid


def update_expense(expense_id: int, spent_on: str, category: str, amount: float,
                   note: str = None, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute(
            "UPDATE expenses SET spent_on = ?, category = ?, amount = ?, note = ? WHERE id = ?",
            (spent_on, category, round(float(amount), 2), note, expense_id),
        ).rowcount > 0


def delete_expense(expense_id: int, conn=None) -> bool:
    with use_conn(conn) as c:
        return c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,)).rowcount > 0


def get_expense(expense_id: int, conn=None):
    with use_conn(conn) as c:
        return c.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()


def list_expenses(date_from: str = None, date_to: str = None, conn=None):
    sql = (
        "SELECT e.*, u.full_name AS created_by_name FROM expenses e "
        "LEFT JOIN users u ON u.id = e.created_by WHERE 1=1"
    )
    params = []
    if date_from:
        sql += " AND date(e.spent_on) >= date(?)"
        params.append(date_from)
    if date_to:
        sql += " AND date(e.spent_on) <= date(?)"
        params.append(date_to)
    sql += " ORDER BY date(e.spent_on) DESC, e.id DESC"
    with use_conn(conn) as c:
        return c.execute(sql, params).fetchall()


def sum_expenses(date_from: str = None, date_to: str = None, conn=None) -> float:
    sql = "SELECT COALESCE(SUM(amount), 0) AS s FROM expenses WHERE 1=1"
    params = []
    if date_from:
        sql += " AND date(spent_on) >= date(?)"
        params.append(date_from)
    if date_to:
        sql += " AND date(spent_on) <= date(?)"
        params.append(date_to)
    with use_conn(conn) as c:
        val = c.execute(sql, params).fetchone()["s"]
    return round(float(val or 0), 2)
