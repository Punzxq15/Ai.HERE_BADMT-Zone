"""
tests/test_promptpay.py
ทดสอบ CRC16-CCITT และโครงสร้าง payload ของ PromptPay QR
รันจาก root โปรเจกต์:  python -m unittest tests.test_promptpay -v
"""
import binascii
import unittest

from utils.promptpay import build_payload, crc16_ccitt, make_qr_image


def parse_tlv(text):
    """แยก TLV (tag 2 หลัก + ความยาว 2 หลัก + ค่า) เป็น dict"""
    out, i = {}, 0
    while i < len(text):
        tag, length = text[i:i + 2], int(text[i + 2:i + 4])
        out[tag] = text[i + 4:i + 4 + length]
        i += 4 + length
    return out


class TestCrc(unittest.TestCase):
    def test_standard_check_value(self):
        # ค่ามาตรฐานของ CRC-16/CCITT-FALSE: "123456789" -> 0x29B1
        self.assertEqual(crc16_ccitt("123456789"), "29B1")

    def test_matches_stdlib_crc_hqx(self):
        for text in ("", "A", "00020101021129", "ทดสอบ".encode("unicode_escape").decode()):
            self.assertEqual(crc16_ccitt(text), f"{binascii.crc_hqx(text.encode(), 0xFFFF):04X}")


class TestPayload(unittest.TestCase):
    def test_phone_with_amount_structure(self):
        payload = build_payload("081-234-5678", 1290)
        tlv = parse_tlv(payload)
        self.assertEqual(tlv["00"], "01")
        self.assertEqual(tlv["01"], "12")            # ระบุยอด = dynamic
        self.assertEqual(tlv["58"], "TH")
        self.assertEqual(tlv["53"], "764")
        self.assertEqual(tlv["54"], "1290.00")
        merchant = parse_tlv(tlv["29"])
        self.assertEqual(merchant["00"], "A000000677010111")
        self.assertEqual(merchant["01"], "0066812345678")

    def test_crc_is_valid(self):
        payload = build_payload("0899999999", 4.22)
        self.assertEqual(payload[-4:], crc16_ccitt(payload[:-4]))
        self.assertTrue(payload[:-4].endswith("6304"))

    def test_known_body(self):
        # ส่วนก่อน CRC ของตัวอย่างยอด 4.22 บาท
        self.assertEqual(
            build_payload("0899999999", 4.22)[:-4],
            "00020101021229370016A000000677010111011300668999999995802TH530376454044.226304",
        )

    def test_static_without_amount(self):
        tlv = parse_tlv(build_payload("0812345678"))
        self.assertEqual(tlv["01"], "11")
        self.assertNotIn("54", tlv)

    def test_national_id(self):
        merchant = parse_tlv(parse_tlv(build_payload("1234567890123", 100))["29"])
        self.assertEqual(merchant["02"], "1234567890123")

    def test_invalid_inputs(self):
        for bad in ("", "12345", "abc"):
            with self.assertRaises(ValueError):
                build_payload(bad, 100)
        with self.assertRaises(ValueError):
            build_payload("0812345678", 0)

    def test_qr_image(self):
        img = make_qr_image(build_payload("0812345678", 100), 200)
        self.assertEqual(img.size, (200, 200))


if __name__ == "__main__":
    unittest.main()
