"""
services/chat_service.py
แชทระหว่างลูกค้ากับร้าน + ระบบถามผู้ช่วย AI โดยเฉพาะ + ปุ่มคำถามแนะนำสำเร็จรูป + แนะนำไม้ 3 รุ่นตามสไตล์ (SYS-2a-2d):
- รองรับการส่งรูปภาพในแชทได้ทั้งลูกค้า พนักงาน (Admin) และเจ้าของร้าน (Owner)
- ลูกค้าส่งข้อความปกติ: ถ้าไม่มีแอดมินออนไลน์และเปิด ai_enabled -> AI ตอบแทน
- ลูกค้ากดปุ่ม 'ถาม AI โดยเฉพาะ' (force_ai=True): AI ตอบให้ทันทีแม้มีแอดมินออนไลน์อยู่ โดยไม่กระทบแชทกับเจ้าหน้าที่
- คำถามนอกขอบเขตร้าน: ai_guard จะตอบปฏิเสธอย่างสุภาพตาม PDF ก่อนส่งไปโมเดล
- ปุ่มคำถามแนะนำสำเร็จรูป (Quick Replies): ตอบจากข้อมูลยอดขาย/โปรโมชั่น/การตั้งค่าจริงในฐานข้อมูลทันที
- ฟอร์มแนะนำไม้ 3 รุ่นตามสไตล์/ระดับฝีมือ/ก้าน/จุดสมดุล/งบประมาณ: ดึงไม้จริงจาก catalog พร้อมเหตุผล
"""
import contextvars
import threading
from pathlib import Path

import config
from core import permissions
from core.constants import ROLE_BUYER, SENDER_TYPE_ADMIN, SENDER_TYPE_AI, SENDER_TYPE_USER
from core.session import Session
from database import repo_chat, repo_users
from services import ai_guard, ai_service, coupon_service, product_service, settings_service
from utils.formatters import format_price

MAX_MESSAGE_CHARS = 1000
AI_HISTORY_LIMIT = 10

QUICK_REPLIES = (
    {"id": "best_sellers", "label": "🏆 สินค้าขายดีที่สุด"},
    {"id": "flash_sale", "label": "⚡ สินค้าลดราคาตอนนี้"},
    {"id": "coupons", "label": "🎟️ โปรโมชั่นและคูปองส่วนลด"},
    {"id": "shipping_info", "label": "🚚 ค่าส่งและโปรส่งฟรี"},
    {"id": "payment_how", "label": "💳 วิธีชำระเงินและแนบสลิป"},
    {"id": "shop_contact", "label": "📞 ช่องทางติดต่อร้าน"},
)


def get_quick_replies() -> list[dict]:
    """คืนรายการปุ่มคำถามแนะนำที่กำหนดไว้ล่วงหน้า (SYS-2b)"""
    return [dict(q) for q in QUICK_REPLIES]


def _clean_image_path(image_path) -> str | None:
    if not image_path:
        return None
    raw_str = str(image_path).strip()
    if not raw_str:
        return None
    if ".." in raw_str:
        raise ValueError("พาธรูปภาพแนบไม่ถูกต้อง")
    raw = raw_str.lstrip("/")
    p_cand = Path(raw_str)
    if p_cand.is_absolute() and p_cand.is_file():
        resolved = p_cand.resolve()
        if Path(config.CHAT_IMAGES_DIR).resolve() in resolved.parents or Path(config.ASSETS_DIR).resolve() in resolved.parents:
            return f"assets/images/chat/{resolved.name}"
    if not raw.startswith("assets/"):
        raise ValueError("พาธรูปภาพแนบไม่ถูกต้อง")
    full = (Path(config.BASE_DIR) / raw).resolve()
    chat_alt = (Path(config.CHAT_IMAGES_DIR) / Path(raw).name).resolve()
    if (Path(config.ASSETS_DIR).resolve() in full.parents and full.is_file()):
        return raw
    if chat_alt.is_file():
        return raw
    raise ValueError("ไม่พบไฟล์รูปภาพที่อัปโหลด")


def _clean_text(text, allow_empty: bool = False) -> str:
    text = str(text or "").strip()
    if not text and not allow_empty:
        raise ValueError("กรุณาพิมพ์ข้อความหรือเลือกรูปภาพก่อนส่ง")
    if len(text) > MAX_MESSAGE_CHARS:
        raise ValueError(f"ข้อความยาวเกินไป (ไม่เกิน {MAX_MESSAGE_CHARS} ตัวอักษร)")
    return text


def _message_dict(row, names: dict) -> dict:
    d = dict(row)
    d["is_read"] = bool(d["is_read"])
    d["image_path"] = d.get("image_path") or None
    if d["sender_type"] == SENDER_TYPE_AI:
        d["sender_name"] = "ผู้ช่วย AI"
    elif d["sender_type"] == SENDER_TYPE_ADMIN:
        sid = d["sender_id"]
        if sid not in names:
            user = repo_users.get_by_id(sid) if sid else None
            names[sid] = (user["full_name"] if user else None) or "แอดมิน"
        d["sender_name"] = names[sid]
    else:
        d["sender_name"] = None
    return d


def should_ai_reply() -> bool:
    """AI ควรตอบอัตโนมัติไหม: ร้านเปิด ai_enabled และไม่มี admin/owner ที่ออนไลน์อยู่"""
    return settings_service.get_bool("ai_enabled") and not repo_users.list_online_staff()


def _run_ai_reply(customer_id: int, question_id: int, question: str, force_ai: bool = False) -> bool:
    """
    ให้ AI ตอบข้อความ question_id แล้วบันทึกเป็น sender_type=ai คืน True ถ้าบันทึกคำตอบ
    ถ้า force_ai=True จะตอบเสมอแม้มีแอดมินออนไลน์อยู่ (ตามข้อกำหนดปุ่มถาม AI โดยเฉพาะ)
    """
    try:
        verdict = ai_guard.classify(question)
        if verdict == "block":
            repo_chat.add_message(customer_id, SENDER_TYPE_AI, None, ai_guard.OUT_OF_SCOPE_MESSAGE)
            return True

        history = [m for m in repo_chat.list_messages(customer_id, limit=AI_HISTORY_LIMIT + 1)
                   if m["id"] < question_id]
        answer = ai_service.ask(history, question)

        if not force_ai:
            if not should_ai_reply():
                return False
            latest = repo_chat.list_messages(customer_id, after_id=question_id)
            if any(m["sender_type"] == SENDER_TYPE_ADMIN for m in latest):
                return False
            if (answer == ai_service.FALLBACK_MESSAGE and history
                    and history[-1]["sender_type"] == SENDER_TYPE_AI and history[-1]["message"] == answer):
                return False

        repo_chat.add_message(customer_id, SENDER_TYPE_AI, None, answer)
        return True
    except Exception:  # noqa: BLE001
        return False


def _orig_send_message(
    customer_id: int,
    text: str = "",
    background: bool = True,
    force_ai: bool = False,
    image_path: str | None = None,
) -> dict:
    """
    ลูกค้าส่งข้อความหรือรูปภาพหาร้าน (ห้องของตัวเองเท่านั้น) คืน {"message": dict, "ai_pending": bool}
    force_ai=True = โหมดถามผู้ช่วย AI โดยเฉพาะ (ทำงานได้แม้มีแอดมินออนไลน์)
    """
    permissions.require_self(permissions.CHAT_CUSTOMER, customer_id)
    clean_img = _clean_image_path(image_path)
    text = _clean_text(text, allow_empty=bool(clean_img))

    # ถ้าส่งเฉพาะรูปภาพโดยไม่มีข้อความและไม่ได้กดถาม AI โดยเฉพาะ ไม่ต้องให้ AI ตอบแทรก
    will_ai = (bool(force_ai) or should_ai_reply()) and bool(text)
    if will_ai and ai_guard.classify(text) != "block":
        ai_guard.check_rate_limit(customer_id)

    message_id = repo_chat.add_message(
        customer_id, SENDER_TYPE_USER, customer_id, text, image_path=clean_img
    )
    message = _message_dict(repo_chat.list_messages(customer_id, after_id=message_id - 1)[0], {})

    if will_ai:
        if background:
            ctx = contextvars.copy_context()
            threading.Thread(
                target=ctx.run, args=(_run_ai_reply, customer_id, message_id, text, bool(force_ai)), daemon=True
            ).start()
        else:
            _run_ai_reply(customer_id, message_id, text, bool(force_ai))
    return {"message": message, "ai_pending": will_ai}


def send_message(
    customer_id: int,
    text: str = "",
    background: bool = True,
    force_ai: bool = False,
    image_path: str | None = None,
) -> dict:
    res = _orig_send_message(
        customer_id,
        text,
        background=(False if force_ai else background),
        force_ai=force_ai,
        image_path=image_path,
    )
    if force_ai and "ai_message" not in res:
        msgs = repo_chat.list_messages(customer_id, limit=5)
        ai_msgs = [dict(m) for m in msgs if m["sender_type"] == SENDER_TYPE_AI]
        if ai_msgs:
            res["ai_message"] = _message_dict(ai_msgs[-1], {})
    return res


def _build_quick_reply_answer(reply_id: str) -> tuple[str, str]:
    """คืน (ข้อความคำถามของผู้ใช้, คำตอบจากข้อมูลจริงใน DB)"""
    label_map = {q["id"]: q["label"] for q in QUICK_REPLIES}
    question_text = label_map.get(reply_id, "สอบถามข้อมูลร้าน")

    if reply_id == "best_sellers":
        best = product_service.get_best_sellers(limit=5)
        if not best:
            return question_text, "ขณะนี้ยังไม่มีรายการสินค้าในระบบครับ"
        lines = ["🏆 สินค้าขายดีและยอดนิยมของทางร้านตอนนี้:"]
        for idx, p in enumerate(best, start=1):
            sold_txt = f" (ขายแล้ว {p['sold_qty']} ชิ้น)" if p.get("sold_qty") else " (สินค้าแนะนำ)"
            lines.append(f"{idx}. {p.get('brand_name', '')} {p['name']} — {format_price(p['effective_price'])}{sold_txt}")
        return question_text, "\n".join(lines)

    if reply_id == "flash_sale":
        from database import repo_products
        rows = repo_products.list_products({"active_only": True, "on_sale": True}, sort="popular", limit=5)
        if not rows:
            return question_text, "ขณะนี้ยังไม่มีสินค้าจัดรายการลดราคาพิเศษครับ"
        lines = ["⚡ สินค้าลดราคาพิเศษตอนนี้:"]
        for idx, r in enumerate(rows, start=1):
            lines.append(
                f"{idx}. {r['name']} — ลดเหลือ {format_price(r['effective_price'])} "
                f"(จากปกติ {format_price(r['price'])})"
            )
        return question_text, "\n".join(lines)

    if reply_id == "coupons":
        coupons = coupon_service.list_public_coupons()
        rules = coupon_service.list_rules(active_only=True)
        lines = ["🎟️ คูปองส่วนลดและโปรโมชั่นปัจจุบัน:"]
        for c in coupons[:5]:
            disc = f"{c['value']:g}%" if c["discount_type"] == "percent" else format_price(c["value"])
            min_o = f" (ขั้นต่ำ {format_price(c['min_order'])})" if float(c.get("min_order") or 0) > 0 else ""
            lines.append(f"- โค้ด {c['code']}: ลด {disc}{min_o}")
        for rl in rules[:3]:
            r_disc = f"{rl['reward_value']:g}%" if rl["reward_type"] == "percent" else format_price(rl["reward_value"])
            lines.append(
                f"- พิเศษ! ซื้อครบ {format_price(rl['trigger_min_spend'])} รับคูปองลด {r_disc} สำหรับออเดอร์ถัดไป"
            )
        if len(lines) == 1:
            lines.append("- ขณะนี้ยังไม่มีคูปองส่วนลดที่เปิดใช้งาน")
        return question_text, "\n".join(lines)

    if reply_id == "shipping_info":
        shop = settings_service.get_shop_info()
        fee = format_price(shop["shipping_fee"])
        free_min = float(shop["free_shipping_min"] or 0)
        free_txt = f" และส่งฟรีเมื่อสั่งซื้อครบ {format_price(free_min)} ขึ้นไป!" if free_min > 0 else ""
        return (
            question_text,
            f"🚚 ค่าจัดส่งมาตรฐานอยู่ที่ {fee} ต่อคำสั่งซื้อ{free_txt}\n"
            "จัดส่งผ่านขนส่งชั้นนำ (Kerry, Flash, J&T, ไปรษณีย์ไทย) พร้อมแจ้งเลขพัสดุให้ติดตามได้ในหน้าออเดอร์ครับ",
        )

    if reply_id == "payment_how":
        shop = settings_service.get_shop_info()
        return (
            question_text,
            f"💳 วิธีชำระเงิน: สแกน QR PromptPay ({shop['promptpay_name']}) ในหน้าชำระเงินของคำสั่งซื้อ "
            f"จากนั้นกดแนบรูปสลิปโอนเงิน แอดมินจะตรวจสอบและส่งใบเสร็จอิเล็กทรอนิกส์ให้ทางอีเมลครับ "
            f"(กรุณาชำระภายใน {shop['unpaid_cancel_hours']} ชั่วโมงหลังสั่งซื้อ)",
        )

    if reply_id == "shop_contact":
        contact = settings_service.get_contact_info()
        return (
            question_text,
            f"📞 ช่องทางติดต่อร้าน {contact.get('shop_name', 'AI.HERE BADᴍᴛ-Zone')}:\n"
            f"- โทรศัพท์: {contact.get('shop_phone') or '-'}\n"
            f"- อีเมล: {contact.get('shop_email') or '-'}\n"
            f"- LINE: {contact.get('line_name') or '-'}\n"
            f"- Facebook: {contact.get('facebook_name') or '-'}\n"
            f"- Instagram: {contact.get('instagram_name') or '-'}\n"
            f"- เวลาทำการ: {contact.get('shop_hours') or '-'}",
        )

    raise ValueError("ไม่พบหัวข้อคำถามแนะนำที่เลือก")


def answer_quick_reply(customer_id: int, reply_id: str) -> dict:
    """
    ตอบคำถามจากปุ่มคำถามแนะนำสำเร็จรูป (SYS-2b) โดยอิงข้อมูลจริงในฐานข้อมูลทันที
    บันทึกทั้งข้อความคำถามและคำตอบลงในห้องแชทของลูกค้า
    """
    permissions.require_self(permissions.CHAT_CUSTOMER, customer_id)
    q_text, a_text = _build_quick_reply_answer(reply_id)
    q_id = repo_chat.add_message(customer_id, SENDER_TYPE_USER, customer_id, q_text)
    a_id = repo_chat.add_message(customer_id, SENDER_TYPE_AI, None, a_text)
    rows = repo_chat.list_messages(customer_id, after_id=q_id - 1)
    names = {}
    return {
        "question": _message_dict(rows[0], names),
        "answer": _message_dict(rows[-1], names),
        "answer_id": a_id,
    }


def recommend_from_form(customer_id: int, level: str, style: str, budget=None,
                        flex: str = None, balance: str = None, weight_class: str = None,
                        post_to_chat: bool = True) -> dict:
    """
    วิเคราะห์และแนะนำไม้แบดมินตัน 3 รุ่นจากข้อมูลสเปกจริงในร้านตามความชอบของลูกค้า (SYS-2d)
    """
    permissions.require_self(permissions.CHAT_CUSTOMER, customer_id)
    rackets = product_service.recommend_rackets(
        level=level, style=style, budget=budget, limit=3,
        flex=flex, balance=balance, weight_class=weight_class,
    )
    style_label = product_service.STYLE_LABELS.get(style, style)
    summary_text = ai_service.format_racket_recommendations(rackets, level, style_label, budget=budget)

    messages_added = []
    if post_to_chat:
        user_prompt = (
            f"ขอคำแนะนำไม้แบดมินตัน: ระดับ {level}, สไตล์{style_label}"
            + (f", ก้าน {flex}" if flex else "")
            + (f", สมดุล {balance}" if balance else "")
            + (f", น้ำหนัก {weight_class}" if weight_class else "")
            + (f", งบไม่เกิน {format_price(budget)}" if budget else "")
        )
        q_id = repo_chat.add_message(customer_id, SENDER_TYPE_USER, customer_id, user_prompt)
        repo_chat.add_message(customer_id, SENDER_TYPE_AI, None, summary_text)
        names = {}
        messages_added = [_message_dict(r, names) for r in repo_chat.list_messages(customer_id, after_id=q_id - 1)]

    return {
        "rackets": rackets,
        "summary": summary_text,
        "messages": messages_added,
    }


def staff_reply(customer_id: int, text: str = "", image_path: str | None = None) -> dict:
    """แอดมิน/เจ้าของ ตอบลูกค้าพร้อมข้อความและ/หรือรูปภาพ (ห้องของ customer_id) คืน dict ข้อความ"""
    permissions.require(permissions.CHAT_REPLY)
    staff_id = permissions.require_login()
    clean_img = _clean_image_path(image_path)
    text = _clean_text(text, allow_empty=bool(clean_img))
    customer = repo_users.get_by_id(customer_id)
    if customer is None or customer["role"] != ROLE_BUYER:
        raise ValueError("ไม่พบลูกค้า")
    message_id = repo_chat.add_message(
        customer_id, SENDER_TYPE_ADMIN, staff_id, text, image_path=clean_img
    )
    return _message_dict(repo_chat.list_messages(customer_id, after_id=message_id - 1)[0], {})


def get_messages(customer_id: int, after_id: int = 0, limit=None, mark_read: bool = True) -> list[dict]:
    user_id = permissions.require_login()
    role = Session.get_role()
    if permissions.can(role, permissions.CHAT_REPLY):
        reader, other = repo_chat.READER_STAFF, SENDER_TYPE_USER
    elif permissions.can(role, permissions.CHAT_CUSTOMER) and customer_id == user_id:
        reader, other = repo_chat.READER_CUSTOMER, None
    else:
        raise PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")

    rows = repo_chat.list_messages(customer_id, after_id=after_id, limit=limit)
    names = {}
    messages = [_message_dict(r, names) for r in rows]
    if mark_read:
        unread_from_other = any(
            not m["is_read"] and ((m["sender_type"] == other) if other else (m["sender_type"] != SENDER_TYPE_USER))
            for m in messages)
        if unread_from_other:
            repo_chat.mark_read(customer_id, reader)
    return messages


def list_threads() -> list[dict]:
    permissions.require(permissions.CHAT_REPLY)
    return [dict(r) for r in repo_chat.list_threads()]


def unread_count() -> int:
    user_id = permissions.require_login()
    role = Session.get_role()
    if permissions.can(role, permissions.CHAT_REPLY):
        return repo_chat.count_unread_for_staff()
    if permissions.can(role, permissions.CHAT_CUSTOMER):
        return repo_chat.count_unread_for_customer(user_id)
    return 0


def send_racket_recommendation(
    customer_id: int,
    weight_class: str = None,
    balance: str = None,
    flex: str = None,
    level: str = None,
    budget=None,
) -> dict:
    level_map = {"มือใหม่": "Beginner", "ระดับกลาง": "Intermediate", "ก้าวหน้า": "Advanced", "แข่งขัน": "Professional"}
    mapped_level = level_map.get(str(level or ""), level if level in ("Beginner", "Intermediate", "Advanced", "Professional") else "Beginner")
    res = recommend_from_form(
        customer_id=customer_id,
        level=mapped_level,
        style='attack',
        budget=budget,
        flex=flex,
        balance=balance,
        weight_class=weight_class,
        post_to_chat=True,
    )
    msgs = res.get("messages") or []
    user_msg = msgs[0] if len(msgs) >= 1 else {"message": "ขอคำแนะนำไม้แบดมินตัน"}
    ai_msg = msgs[-1] if len(msgs) >= 2 else {"message": res.get("summary", "")}
    return {
        **res,
        "user_message": user_msg,
        "ai_message": ai_msg,
    }
