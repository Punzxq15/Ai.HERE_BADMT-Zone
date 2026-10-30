"""
services/receipt_service.py
ใบเสร็จรับเงิน PDF (reportlab) เก็บที่ assets/receipts/receipt_<เลขออเดอร์>.pdf
รวมการแสดง VAT 7% และที่อยู่หน้าร้าน
ใช้ฟอนต์ Arimo สำหรับภาษาอังกฤษ/ตัวเลข และ Kanit สำหรับภาษาไทย (T01)
"""
import os
import platform
import re
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import config
from core.constants import (
    ORDER_STATUS_COMPLETED, ORDER_STATUS_LABELS, ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED,
    PAYMENT_METHOD_PROMPTPAY, PAYMENT_STATUS_VERIFIED,
)
from services import order_service, settings_service
from utils.formatters import format_datetime, format_phone, format_price

RECEIPT_STATUSES = (ORDER_STATUS_PAID, ORDER_STATUS_SHIPPED, ORDER_STATUS_COMPLETED)
THAI_MARK_LIFT = 0.22  # ยกวรรณยุกต์ที่ซ้อนบนสระบนขึ้นกี่เท่าของขนาดตัวอักษร

_FONT_LATIN = "ReceiptLatin"
_FONT_LATIN_BOLD = "ReceiptLatinBold"
_FONT_THAI = "ReceiptThai"
_FONT_THAI_BOLD = "ReceiptThaiBold"

_THAI_FONT_CANDIDATES = (
    # T01: ฟอนต์ Kanit ใน assets/fonts/ ของโปรเจกต์เป็นอันดับแรก
    ("Kanit-Regular.ttf", "Kanit-Bold.ttf"),
    ("Kanit-Medium.ttf", "Kanit-SemiBold.ttf"),
    # Windows
    ("LeelawUI.ttf", "LeelaUIb.ttf"),
    ("tahoma.ttf", "tahomabd.ttf"),
    ("leelawad.ttf", "leelawdb.ttf"),
    ("angsa.ttf", "angsab.ttf"),
    ("cordia.ttf", "cordiab.ttf"),
    # macOS
    ("Thonburi.ttc", None),
    ("Ayuthaya.ttf", None),
    ("Sathu.ttf", None),
    ("Krungthep.ttf", None),
    # Linux
    ("NotoSansThai-Regular.ttf", "NotoSansThai-Bold.ttf"),
    ("NotoSansThaiUI-Regular.ttf", "NotoSansThaiUI-Bold.ttf"),
    ("Loma.ttf", "Loma-Bold.ttf"),
    ("Garuda.ttf", "Garuda-Bold.ttf"),
    ("Waree.ttf", "Waree-Bold.ttf"),
    ("Norasi.ttf", "Norasi-Bold.ttf"),
    ("Kinnari.ttf", "Kinnari-Bold.ttf"),
    ("Sarabun-Regular.ttf", "Sarabun-Bold.ttf"),
    ("THSarabunNew.ttf", "THSarabunNew Bold.ttf"),
    ("FreeSans.ttf", "FreeSansBold.ttf"),
    ("FreeSerif.ttf", "FreeSerifBold.ttf"),
)

_NO_THAI_FONT_MESSAGE = (
    "ไม่พบฟอนต์ภาษาไทยในเครื่องนี้ จึงสร้างใบเสร็จไม่ได้ — "
    "ตรวจสอบว่ามีไฟล์ Kanit-Regular.ttf ในโฟลเดอร์ assets/fonts/"
)

_THAI_RUN = re.compile(r"[\u0E00-\u0E7F]+(?:[ \u00A0]+[\u0E00-\u0E7F]+)*")
_STACKED_MARK = re.compile("([\u0E31\u0E34-\u0E37\u0E47])([\u0E48-\u0E4C])")

_thai_font_cache = {"done": False, "info": None}
_registered_key = None


# ==========================================
# ค้นหา/ลงทะเบียนฟอนต์
# ==========================================

def _font_search_dirs() -> list[Path]:
    dirs = [Path(config.FONTS_DIR)]
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        windir = Path(os.environ.get("WINDIR") or os.environ.get("SystemRoot") or "C:/Windows")
        dirs.append(windir / "Fonts")
        local = os.environ.get("LOCALAPPDATA")
        if local:
            dirs.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    elif system == "Darwin":
        dirs += [Path("/System/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
                 Path("/Library/Fonts"), home / "Library" / "Fonts"]
    else:
        dirs += [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"),
                 home / ".fonts", home / ".local" / "share" / "fonts"]
    return [d for d in dirs if d.is_dir()]


def _index_fonts() -> dict:
    found = {}
    for folder in _font_search_dirs():
        for root, _dirs, files in os.walk(folder):
            for name in files:
                if name.lower().endswith((".ttf", ".ttc")):
                    found.setdefault(name.lower(), Path(root) / name)
    return found


def _open_ttf(path, index=0):
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        try:
            return TTFont("probe", str(path), subfontIndex=index, shapable=False)
        except TypeError:
            return TTFont("probe", str(path), subfontIndex=index)
    except Exception:  # noqa: BLE001
        return None


def _has_thai(font) -> bool:
    glyphs = font.face.charToGlyph
    return 0x0E01 in glyphs and 0x0E48 in glyphs


def _style_of(font) -> str:
    style = font.face.styleName
    return (style.decode("latin-1") if isinstance(style, bytes) else str(style or "")).lower()


def _ttc_indexes(path):
    regular = bold = None
    for index in range(8):
        font = _open_ttf(path, index)
        if font is None:
            break
        if not _has_thai(font):
            continue
        style = _style_of(font)
        if "bold" in style and not any(w in style for w in ("light", "italic", "oblique")):
            bold = index if bold is None else bold
        elif regular is None and not any(w in style for w in ("light", "italic", "oblique", "bold")):
            regular = index
    if regular is None:
        regular = 0 if _open_ttf(path, 0) is not None else None
    return regular, bold


def _info_for(regular_path, bold_path=None):
    regular_path = Path(regular_path)
    if regular_path.suffix.lower() == ".ttc":
        reg_idx, bold_idx = _ttc_indexes(regular_path)
        if reg_idx is None:
            return None
        return {"regular": regular_path, "regular_index": reg_idx,
                "bold": regular_path if bold_idx is not None else None, "bold_index": bold_idx or 0}
    font = _open_ttf(regular_path)
    if font is None or not _has_thai(font):
        return None
    bold_ok = bold_path is not None and Path(bold_path).is_file() and _open_ttf(bold_path) is not None
    return {"regular": regular_path, "regular_index": 0,
            "bold": Path(bold_path) if bold_ok else None, "bold_index": 0}


def find_thai_font():
    if _thai_font_cache["done"]:
        return _thai_font_cache["info"]
    index = _index_fonts()
    info = None
    for regular_name, bold_name in _THAI_FONT_CANDIDATES:
        regular_path = index.get(regular_name.lower())
        if regular_path is None:
            continue
        info = _info_for(regular_path, index.get(bold_name.lower()) if bold_name else None)
        if info:
            break
    if info is None:
        for path in list(index.values())[:400]:
            try:
                if path.stat().st_size > 15 * 1024 * 1024:
                    continue
            except OSError:
                continue
            info = _info_for(path)
            if info:
                break
    _thai_font_cache.update(done=True, info=info)
    return info


def reset_font_cache() -> None:
    global _registered_key
    _thai_font_cache.update(done=False, info=None)
    _registered_key = None


def _register_fonts(thai) -> dict:
    global _registered_key
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    latin_reg = config.FONTS_DIR / "Arimo-Regular.ttf"
    latin_bold = config.FONTS_DIR / "Arimo-Bold.ttf"
    key = (str(latin_reg), str(latin_bold), str(thai["regular"]), thai["regular_index"],
           str(thai["bold"]), thai["bold_index"])

    def make(name, path, index=0):
        try:
            return TTFont(name, str(path), subfontIndex=index, shapable=False)
        except TypeError:
            return TTFont(name, str(path), subfontIndex=index)

    if _registered_key != key:
        use_arimo = latin_reg.is_file() and latin_bold.is_file()
        if use_arimo:
            pdfmetrics.registerFont(make(_FONT_LATIN, latin_reg))
            pdfmetrics.registerFont(make(_FONT_LATIN_BOLD, latin_bold))
        pdfmetrics.registerFont(make(_FONT_THAI, thai["regular"], thai["regular_index"]))
        bold_src, bold_idx = (thai["bold"], thai["bold_index"]) if thai["bold"] else (thai["regular"], thai["regular_index"])
        pdfmetrics.registerFont(make(_FONT_THAI_BOLD, bold_src, bold_idx))
        _registered_key = key
    use_arimo = latin_reg.is_file() and latin_bold.is_file()
    return {"latin": _FONT_LATIN if use_arimo else "Helvetica",
            "latin_bold": _FONT_LATIN_BOLD if use_arimo else "Helvetica-Bold",
            "thai": _FONT_THAI, "thai_bold": _FONT_THAI_BOLD}


def _markup(text, size: float, fonts: dict, bold: bool = False) -> str:
    text = "" if text is None else str(text)
    thai_name = fonts["thai_bold"] if bold else fonts["thai"]
    parts, last = [], 0
    for match in _THAI_RUN.finditer(text):
        parts.append(escape(text[last:match.start()]))
        run = escape(match.group())
        rise = f"{size * THAI_MARK_LIFT:.2f}"
        run = _STACKED_MARK.sub(lambda m: f'{m.group(1)}<super rise="{rise}" size="{size:g}">{m.group(2)}</super>', run)
        parts.append(f'<font name="{thai_name}">{run}</font>')
        last = match.end()
    parts.append(escape(text[last:]))
    return "".join(parts).replace("\n", "<br/>")


# ==========================================
# สร้าง PDF (พร้อม VAT 7% และที่อยู่หน้าร้าน)
# ==========================================

def _build_pdf(target: Path, order: dict, shop_name: str, fonts: dict) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def para(text, size=10, bold=False, align=None, color=None):
        style = ParagraphStyle(
            "p", fontName=fonts["latin_bold"] if bold else fonts["latin"], fontSize=size,
            leading=size * 1.5, textColor=color or colors.HexColor("#1A1A1A"),
            alignment={"right": TA_RIGHT, "center": TA_CENTER}.get(align, 0), splitLongWords=1,
        )
        return Paragraph(_markup(text, size, fonts, bold), style)

    ink, muted, line = colors.HexColor("#1A1A1A"), colors.HexColor("#666666"), colors.HexColor("#CCCCCC")
    accent = colors.HexColor("#F5B041")
    page_w = A4[0] - 36 * mm

    contact = settings_service.get_contact_info()
    shop_address = contact.get("shop_address") or ""
    shop_phone = contact.get("shop_phone") or ""

    left_head = [para(shop_name, 18, True)]
    if shop_address:
        left_head.append(para(f"ที่ตั้งร้าน: {shop_address}", 9, False, None, muted))
    if shop_phone:
        left_head.append(para(f"โทร: {format_phone(shop_phone)}", 9, False, None, muted))

    story = []
    head = Table([[left_head, [para("ใบเสร็จรับเงิน / ใบกำกับภาษีอย่างย่อ", 14, True, "right"),
                               para("RECEIPT / TAX INVOICE (VAT 7%)", 9, False, "right", muted)]]],
                 colWidths=[page_w * 0.58, page_w * 0.42])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [head, Spacer(1, 3 * mm), HRFlowable(width="100%", thickness=2, color=accent), Spacer(1, 4 * mm)]

    payment = order.get("payment")
    paid_at = payment["verified_at"] if payment and payment["status"] == PAYMENT_STATUS_VERIFIED else None
    method = "PromptPay" if (payment and payment["method"] == PAYMENT_METHOD_PROMPTPAY) else (payment["method"] if payment else "-")
    left = [
        para(f"เลขที่คำสั่งซื้อ: #{order['id']}", 10, True),
        para(f"วันที่สั่งซื้อ: {format_datetime(order['created_at'])}"),
        para(f"วันที่ชำระเงิน: {format_datetime(paid_at)}"),
        para(f"วิธีชำระเงิน: {method}"),
        para(f"สถานะ: {ORDER_STATUS_LABELS.get(order['status'], order['status'])}"),
    ]
    right = [
        para("ผู้รับสินค้า", 10, True),
        para(order["recipient_name"]),
        para(f"โทร {format_phone(order['recipient_phone'])}"),
        para(order["shipping_address"], 9, False, None, muted),
    ]
    info = Table([[left, right]], colWidths=[page_w * 0.5, page_w * 0.5])
    info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    story += [info, Spacer(1, 6 * mm)]

    rows = [[para("#", 9, True, "center"), para("รายการ", 9, True), para("จำนวน", 9, True, "center"),
             para("ราคา/ชิ้น", 9, True, "right"), para("รวม", 9, True, "right")]]
    for no, item in enumerate(order["items"], start=1):
        name_cell = [para(item["product_name"], 10)]
        if item.get("option_label"):
            name_cell.append(para(item["option_label"], 8.5, False, None, muted))
        rows.append([para(str(no), 10, False, "center"), name_cell, para(str(item["qty"]), 10, False, "center"),
                     para(format_price(item["price_at_purchase"]), 10, False, "right"),
                     para(format_price(item["line_total"]), 10, False, "right")])
    items = Table(rows, colWidths=[page_w * 0.07, page_w * 0.45, page_w * 0.12, page_w * 0.18, page_w * 0.18],
                  repeatRows=1)
    items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F2F2")),
        ("LINEBELOW", (0, 0), (-1, 0), 1, ink),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, line),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [items, Spacer(1, 4 * mm)]

    vat_info = order_service.compute_vat_breakdown(order["total"])
    pre_vat = vat_info["pre_vat_amount"]
    vat_amt = vat_info["vat_amount"]

    coupon_label = f"ส่วนลด ({order['coupon_code']})" if order.get("coupon_code") else "ส่วนลด"
    discount_text = f"-{format_price(order['discount'])}" if order["discount"] else format_price(0)
    fee_text = "ฟรี" if not order["shipping_fee"] else format_price(order["shipping_fee"])
    totals = Table([
        [para("ยอดสินค้า", 10, False, "right"), para(format_price(order["subtotal"]), 10, False, "right")],
        [para(coupon_label, 10, False, "right"), para(discount_text, 10, False, "right")],
        [para("ค่าจัดส่ง", 10, False, "right"), para(fee_text, 10, False, "right")],
        [para("มูลค่าก่อนภาษี", 9.5, False, "right", muted), para(format_price(pre_vat), 9.5, False, "right", muted)],
        [para("ภาษีมูลค่าเพิ่ม (VAT 7%)", 9.5, False, "right", muted), para(format_price(vat_amt), 9.5, False, "right", muted)],
        [para("ยอดสุทธิ (รวม VAT 7%)", 12, True, "right"), para(format_price(order["total"]), 12, True, "right")],
    ], colWidths=[page_w * 0.28, page_w * 0.22], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("LINEABOVE", (0, 3), (-1, 3), 0.5, line),
        ("LINEABOVE", (0, 5), (-1, 5), 1, ink),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [
        totals, Spacer(1, 10 * mm), HRFlowable(width="100%", thickness=0.5, color=line), Spacer(1, 3 * mm),
        para("ขอบคุณที่ใช้บริการ (ราคารวมภาษีมูลค่าเพิ่ม VAT 7% แล้ว)", 10.5, True, "center"),
        para(f"{shop_name}" + (f" · {shop_address}" if shop_address else ""), 9, False, "center", muted),
        para(f"ออกเอกสารโดยระบบ เมื่อ {format_datetime(datetime.now())}", 8, False, "center", muted),
    ]

    doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm,
                            title=f"Receipt #{order['id']}", author=shop_name)
    doc.build(story)


def generate_receipt(order_id: int) -> str:
    """
    สร้างใบเสร็จ PDF ของออเดอร์ แล้วคืน path แบบ relative จาก root (เช่น 'assets/receipts/receipt_12.pdf')
    """
    order = order_service.get_order_detail(order_id)
    if order["status"] not in RECEIPT_STATUSES:
        raise ValueError("ออกใบเสร็จได้เฉพาะคำสั่งซื้อที่ชำระเงินแล้ว")

    thai = find_thai_font()
    if thai is None:
        raise ValueError(_NO_THAI_FONT_MESSAGE)
    try:
        fonts = _register_fonts(thai)
    except ImportError:
        raise ValueError("ยังไม่ได้ติดตั้งไลบรารี reportlab (pip install reportlab)") from None

    shop_name = settings_service.get("shop_name") or "AI.HERE BADᴍᴛ-Zone"

    out_dir = Path(config.RECEIPTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"receipt_{order_id}.pdf"
    temp = out_dir / f".receipt_{order_id}.tmp"
    try:
        _build_pdf(temp, order, shop_name, fonts)
        os.replace(temp, target)
    except OSError:
        raise ValueError("บันทึกไฟล์ใบเสร็จไม่สำเร็จ (ตรวจสอบสิทธิ์เขียนไฟล์ในโฟลเดอร์ assets/receipts)") from None
    finally:
        temp.unlink(missing_ok=True)

    try:
        return target.resolve().relative_to(Path(config.BASE_DIR).resolve()).as_posix()
    except ValueError:
        return str(target)
