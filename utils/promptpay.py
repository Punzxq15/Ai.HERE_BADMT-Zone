"""
utils/promptpay.py
สร้าง PromptPay QR (EMVCo / Thai QR Payment แบบ Credit Transfer)
    payload = build_payload("0812345678", amount=1290)
    img = make_qr_image(payload, 260)      # -> PIL.Image
"""
import re

_AID_PROMPTPAY = "A000000677010111"


def crc16_ccitt(text: str) -> str:
    """CRC16-CCITT (poly 0x1021, init 0xFFFF) -> สตริงฐาน 16 ตัวพิมพ์ใหญ่ 4 หลัก"""
    crc = 0xFFFF
    for byte in text.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def _normalize_target(target: str) -> tuple[str, str]:
    """คืน (sub-tag, ค่า) ตามชนิดของปลายทาง: เบอร์โทร / เลขบัตรประชาชน-ภาษี / e-Wallet"""
    digits = re.sub(r"\D", "", str(target or ""))
    if len(digits) == 10 and digits.startswith("0"):
        return "01", "0066" + digits[1:]          # เบอร์มือถือ -> 0066 + เลขไม่รวม 0 นำหน้า
    if len(digits) == 11 and digits.startswith("66"):
        return "01", "00" + digits                  # 66XXXXXXXXX
    if len(digits) == 13:
        return "02", digits                         # เลขบัตรประชาชน / เลขผู้เสียภาษี
    if len(digits) == 15:
        return "03", digits                         # e-Wallet ID
    raise ValueError("เลขพร้อมเพย์ไม่ถูกต้อง (ต้องเป็นเบอร์โทร 10 หลัก หรือเลขบัตรประชาชน 13 หลัก)")


def build_payload(phone_or_id: str, amount: float | None = None) -> str:
    """
    สร้างข้อความ payload ของ PromptPay QR
    amount = None -> QR แบบไม่ระบุยอด (ผู้จ่ายกรอกเอง) | มียอด -> ล็อกยอด (ทศนิยม 2 ตำแหน่ง)
    ValueError (ไทย) เมื่อเลขปลายทางผิดรูปแบบหรือยอด <= 0
    """
    sub_tag, target = _normalize_target(phone_or_id)

    parts = [
        _tlv("00", "01"),
        _tlv("01", "11" if amount is None else "12"),
        _tlv("29", _tlv("00", _AID_PROMPTPAY) + _tlv(sub_tag, target)),
        _tlv("58", "TH"),
        _tlv("53", "764"),
    ]
    if amount is not None:
        value = round(float(amount), 2)
        if value <= 0:
            raise ValueError("ยอดเงินต้องมากกว่า 0")
        parts.append(_tlv("54", f"{value:.2f}"))

    body = "".join(parts) + "6304"
    return body + crc16_ccitt(body)


def make_qr_image(payload: str, size: int = 260):
    """แปลง payload เป็นรูป QR (PIL.Image, สี่เหลี่ยมจัตุรัส size x size พิกเซล)"""
    import qrcode
    from PIL import Image

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((size, size), Image.NEAREST)
