"""
services/expense_service.py
จัดการรายจ่ายของร้าน (ตาราง expenses — D5) สำหรับใช้คำนวณกำไรเบื้องต้นและส่งออกรายงาน .xlsx
เข้าถึงและแก้ไขได้เฉพาะเจ้าของร้าน (action dashboard.revenue / backup.manage)
"""
import math
from datetime import datetime

from core import permissions
from core.session import Session
from database import repo_expenses
from services import audit_service


def _clean_date(date_str: str) -> str:
    text = str(date_str or "").strip()
    if not text:
        raise ValueError("กรุณาระบุวันที่รายจ่าย (รูปแบบ ปปปป-ดด-วว)")
    try:
        dt = datetime.strptime(text[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("รูปแบบวันที่ไม่ถูกต้อง (ต้องเป็น ปปปป-ดด-วว เช่น 2026-10-15)") from None


def _clean_expense(spent_on: str, category: str, amount, note: str = None) -> dict:
    clean_date = _clean_date(spent_on)
    cat = str(category or "").strip()
    if not cat:
        raise ValueError("กรุณาระบุหมวดหมู่รายจ่าย (เช่น ค่าเช่า, ค่าขนส่ง, ค่าสต็อกสินค้า)")
    if len(cat) > 100:
        raise ValueError("หมวดหมู่รายจ่ายยาวเกินไป (ไม่เกิน 100 ตัวอักษร)")
    try:
        amt = round(float(str(amount).strip().replace(",", "")), 2)
    except (TypeError, ValueError):
        raise ValueError("จำนวนเงินรายจ่ายต้องเป็นตัวเลข") from None
    if not math.isfinite(amt) or amt < 0:
        raise ValueError("จำนวนเงินรายจ่ายต้องไม่ติดลบ")
    clean_note = str(note or "").strip()[:500] or None
    return {"spent_on": clean_date, "category": cat, "amount": amt, "note": clean_note}


def add_expense(spent_on: str, category: str, amount, note: str = None) -> dict:
    permissions.require(permissions.DASHBOARD_REVENUE)
    clean = _clean_expense(spent_on, category, amount, note)
    eid = repo_expenses.create_expense(
        clean["spent_on"], clean["category"], clean["amount"], clean["note"],
        created_by=Session.get_user_id(),
    )
    audit_service.log("expense.create", "expense", eid, clean)
    return dict(repo_expenses.get_expense(eid))


def update_expense(expense_id: int, spent_on: str, category: str, amount, note: str = None) -> dict:
    permissions.require(permissions.DASHBOARD_REVENUE)
    if repo_expenses.get_expense(expense_id) is None:
        raise ValueError("ไม่พบรายการรายจ่าย")
    clean = _clean_expense(spent_on, category, amount, note)
    repo_expenses.update_expense(expense_id, clean["spent_on"], clean["category"], clean["amount"], clean["note"])
    audit_service.log("expense.update", "expense", expense_id, clean)
    return dict(repo_expenses.get_expense(expense_id))


def delete_expense(expense_id: int) -> bool:
    permissions.require(permissions.DASHBOARD_REVENUE)
    ok = repo_expenses.delete_expense(expense_id)
    if not ok:
        raise ValueError("ไม่พบรายการรายจ่าย")
    audit_service.log("expense.delete", "expense", expense_id)
    return True


def list_expenses(date_from: str = None, date_to: str = None) -> list[dict]:
    permissions.require(permissions.DASHBOARD_REVENUE)
    df = _clean_date(date_from) if date_from else None
    dt = _clean_date(date_to) if date_to else None
    return [dict(r) for r in repo_expenses.list_expenses(date_from=df, date_to=dt)]


def sum_expenses(date_from: str = None, date_to: str = None) -> float:
    permissions.require(permissions.DASHBOARD_REVENUE)
    df = _clean_date(date_from) if date_from else None
    dt = _clean_date(date_to) if date_to else None
    return repo_expenses.sum_expenses(date_from=df, date_to=dt)

_orig_add_expense = add_expense
_orig_list_expenses = list_expenses


def add_expense(arg1: str, arg2, arg3=None, arg4: str = None) -> dict:
    # รองรับทั้ง add_expense(spent_on, category, amount, note) และ add_expense(title, amount, category, expense_date)
    s1 = str(arg1 or "").strip()
    is_date_first = len(s1) >= 10 and s1[:4].isdigit() and s1[4:5] == "-"
    if is_date_first:
        res = _orig_add_expense(s1, str(arg2 or "ทั่วไป"), arg3, arg4)
    else:
        date_str = str(arg4 or datetime.now().strftime("%Y-%m-%d"))
        cat_str = str(arg3 or "ทั่วไป")
        res = _orig_add_expense(date_str, cat_str, arg2, s1)
    res["title"] = res.get("note") or res.get("category")
    res["expense_date"] = res.get("spent_on")
    return res


def list_expenses(date_from: str = None, date_to: str = None) -> list[dict]:
    rows = _orig_list_expenses(date_from=date_from, date_to=date_to)
    for r in rows:
        r.setdefault("title", r.get("note") or r.get("category"))
        r.setdefault("expense_date", r.get("spent_on"))
    return rows
