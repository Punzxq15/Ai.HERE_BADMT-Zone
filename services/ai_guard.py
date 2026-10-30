"""
services/ai_guard.py
ตัวกรองขอบเขตคำถาม (Scope Guard) และการป้องกัน Prompt Injection / Rate Limit สำหรับแชท AI (SYS-2a):
- จำกัดขอบเขตคำถามให้อยู่ในเรื่องร้าน สินค้า อุปกรณ์แบดมินตัน การสั่งซื้อ การชำระเงิน และบริการของร้านเท่านั้น
- คำถามนอกขอบเขต (เช่น วันนี้วันอะไร, อากาศเป็นอย่างไร, หวย, หุ้น, การเมือง, เขียนโค้ด, การบ้าน)
  หรือความพยายามเจาะระบบ (Prompt Injection) จะถูกบล็อกและตอบกลับด้วยข้อความสุภาพตามที่ PDF กำหนดทันทีโดยไม่ส่งไปเรียกโมเดล
"""
import re
import time

from database import repo_products

OUT_OF_SCOPE_MESSAGE = (
    "ขออภัยครับ ระบบไม่สามารถตอบคำถามเหล่านี้ได้ เนื่องจากไม่ได้อยู่ในขอบเขตการตอบคำถามของทางร้าน "
    "คุณสามารถสอบถามเกี่ยวกับไม้แบดมินตัน อุปกรณ์แบดมินตัน โปรโมชั่น คูปอง การสั่งซื้อ หรือการจัดส่งได้ครับ"
)

MAX_GUARD_CHARS = 500
RATE_LIMIT_PER_MIN = 10
RATE_LIMIT_PER_DAY = 100

# คำสำคัญเกี่ยวกับร้านและแบดมินตัน
_SHOP_KEYWORDS = (
    "แบด", "ไม้", "ลูกขนไก่", "ลูกแบด", "รองเท้า", "กระเป๋า", "เสื้อ", "กางเกง", "เอ็น", "กริป", "ด้ามพัน",
    "ขึ้นเอ็น", "ก้าน", "หัวหนัก", "หัวเบา", "สมดุล", "3u", "4u", "stiff", "medium", "flexible", "beginner",
    "intermediate", "advanced", "professional", "บุก", "รับ", "สปีด", "คุมเกม", "ตีคู่", "ตีเดี่ยว", "ตบ",
    "ราคา", "ลดราคา", "โปร", "flash sale", "คูปอง", "ส่วนลด", "โค้ด", "สต็อก", "มีของ", "สินค้า", "ขายดี",
    "แนะนำ", "เปรียบเทียบ", "สั่งซื้อ", "ตะกร้า", "ชำระเงิน", "โอน", "พร้อมเพย์", "promptpay", "สลิป",
    "ใบเสร็จ", "จัดส่ง", "ค่าส่ง", "ส่งฟรี", "พัสดุ", "ขนส่ง", "kerry", "flash", "j&t", "ไปรษณีย์",
    "ออเดอร์", "ยกเลิก", "คืนเงิน", "รับประกัน", "รีวิว", "ร้าน", "ติดต่อ", "แอดมิน", "เจ้าของร้าน",
    "เปิดกี่โมง", "ที่อยู่ร้าน", "เบอร์โทร", "line", "facebook", "instagram", "yonex", "victor", "li-ning",
    "lining", "apacs", "forza", "venson", "astrox", "nanoflare", "arcsaber", "ryuga", "auraspeed",
    "axforce", "tectonic", "ziggler",
)

# รูปแบบคำถามนอกขอบเขตที่ต้องปฏิเสธทันทีตาม PDF
_OUT_OF_SCOPE_PATTERNS = (
    r"วันนี้วันอะไร",
    r"พรุ่งนี้วันอะไร",
    r"เมื่อวานวันอะไร",
    r"วันอะไรครับ",
    r"ตอนนี้กี่โมง",
    r"เวลาเท่าไหร่",
    r"อากาศ(เป็นอย่างไร|เป็นยังไง|วันนี้|พรุ่งนี้|ร้อน|หนาว|ฝนตก|ดีไหม)",
    r"พยากรณ์อากาศ",
    r"ฝนจะตกไหม",
    r"อุณหภูมิเท่าไหร่",
    r"หวย(ออก|งวด)",
    r"เลขเด็ด",
    r"ราคาทอง",
    r"หุ้น(ตัวไหน|ขึ้น|ตก|วันนี้)",
    r"บิตคอยน์|bitcoin|crypto",
    r"นายก(ชื่ออะไร|คือใคร)",
    r"การเมือง|เลือกตั้ง|พรรคการเมือง",
    r"เขียน(โค้ด|โปรแกรม|python|javascript|html|sql|เรียงความ|กลอน)",
    r"ทำการบ้าน|แก้สมการ|โจทย์คณิต|คำนวณแคลคูลัส",
    r"แปลภาษา|translate to",
    r"เล่าเรื่องตลก|เล่านิทาน|มุกตลก",
    r"สูตรอาหาร|ทำกับข้าว|วิธีทำ(ต้มยำ|ผัดกะเพรา|เค้ก)",
    r"ดูดวง|ราศี|เนื้อคู่",
    r"ผลบอล|พรีเมียร์ลีก|บอลโลก",
)

# รูปแบบ Prompt Injection / การขอข้อมูลลับของระบบ
_INJECTION_PATTERNS = (
    r"ignore (all )?(previous|above|prior) instructions",
    r"disregard (all )?(previous|above) instructions",
    r"system prompt",
    r"reveal your prompt",
    r"ลืมคำสั่ง(ก่อนหน้า|ทั้งหมด)",
    r"ไม่ต้องทำตามกฎ",
    r"ขอ(ดู)?\s*(api\s*key|gemini_api_key|secret_key|password_hash|\.env)",
    r"drop\s+table|select\s+\*\s+from\s+users",
)

_OUT_OF_SCOPE_RE = re.compile("|".join(_OUT_OF_SCOPE_PATTERNS), re.IGNORECASE)
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

_user_timestamps: dict[int, list[float]] = {}


def check_rate_limit(user_id: int) -> bool:
    """ตรวจว่าผู้ใช้ส่งข้อความถาม AI เกินอัตราที่กำหนดหรือไม่ (คืน True ถ้าผ่าน, โยน ValueError ถ้าเกิน)"""
    if user_id is None:
        return True
    now = time.time()
    history = [t for t in _user_timestamps.get(user_id, []) if now - t < 86400]
    recent_min = [t for t in history if now - t < 60]
    if len(recent_min) >= RATE_LIMIT_PER_MIN:
        raise ValueError("คุณส่งคำถามถี่เกินไป กรุณารอสักครู่แล้วลองใหม่อีกครั้ง (สูงสุด 10 ครั้งต่อนาที)")
    if len(history) >= RATE_LIMIT_PER_DAY:
        raise ValueError("คุณใช้โควตาถาม AI ครบจำนวนสูงสุดต่อวันแล้ว กรุณาติดต่อแอดมิน")
    history.append(now)
    _user_timestamps[user_id] = history
    return True


def reset_rate_limits() -> None:
    """ล้างตัวนับ rate limit (ใช้ในชุดทดสอบ)"""
    _user_timestamps.clear()


def _catalog_keywords() -> list[str]:
    try:
        names = []
        for b in repo_products.list_brands(active_only=True):
            names.append(str(b["name"]).lower())
        for c in repo_products.list_categories(active_only=True):
            names.append(str(c["name"]).lower())
        for p in repo_products.list_products({"active_only": True}, limit=60):
            names.append(str(p["name"]).lower())
        return [n for n in names if len(n) >= 2]
    except Exception:
        return []


def classify(text: str) -> str:
    """
    จำแนกข้อความของผู้ซื้อก่อนส่งไป Gemini (ตามข้อกำหนด Phase 3A):
    คืนค่า:
      - "block"     : คำถามนอกขอบเขตชัดเจน หรือพยายามทำ Prompt Injection (ให้ตอบ OUT_OF_SCOPE_MESSAGE ทันที)
      - "allow"     : คำถามเกี่ยวกับร้าน/สินค้า/แบดมินตันชัดเจน
      - "uncertain" : ข้อความทั่วไปที่ไม่เข้าข่ายนอกเรื่อง ส่งต่อให้โมเดลแต่บังคับด้วย System Prompt
    """
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", str(text or "")).strip()[:MAX_GUARD_CHARS]
    if not cleaned:
        return "block"

    if _INJECTION_RE.search(cleaned):
        return "block"

    if _OUT_OF_SCOPE_RE.search(cleaned):
        return "block"

    low = cleaned.lower()
    if any(k in low for k in _SHOP_KEYWORDS):
        return "allow"

    if any(k in low for k in _catalog_keywords()):
        return "allow"

    return "uncertain"

def check_scope(text: str) -> tuple[bool, str]:
    verdict = classify(text)
    if verdict == "block":
        return False, OUT_OF_SCOPE_MESSAGE
    return True, ""
