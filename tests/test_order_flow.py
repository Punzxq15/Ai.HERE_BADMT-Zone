"""
tests/test_order_flow.py
ทดสอบ services ครึ่งหลังของส่วน C: order, payment, shipping, receipt, account, ai, chat
ไล่ตั้งแต่ สมัคร -> ตะกร้า -> คูปอง -> checkout -> สลิป -> ยืนยัน -> ส่ง -> รับของ -> รีวิว
รวมกรณีผิดพลาด: ยกเลิก / สต็อกไม่พอ / สลิปถูกปฏิเสธ / ยกเลิกอัตโนมัติ / Flash Sale หมดเวลา / สิทธิ์ admin vs owner vs buyer

ใช้ฐานข้อมูลชั่วคราวที่ seed แล้ว และโฟลเดอร์ชั่วคราวสำหรับสลิป/ใบเสร็จ/รูปโปรไฟล์ (ไม่แตะ data/shop.db และ assets จริง)
AI ถูกจำลองด้วย mock (ไม่เรียกเน็ต)
รันจาก root โปรเจกต์:  python -m unittest tests.test_order_flow -v
(ต้องติดตั้ง bcrypt ตาม requirements.txt · เทสต์ใบเสร็จ PDF จะข้ามถ้าเครื่องไม่มีฟอนต์ไทย)
"""
import shutil
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from PIL import Image

import config
import database.db as db
from core.session import Session
from database import (
    repo_chat, repo_coupons, repo_notifications, repo_orders, repo_payments, repo_products,
    repo_settings, repo_users,
)
from database.seed import run_seed
from services import (
    account_service, ai_service, auth_service, cart_service, chat_service, order_service,
    payment_service, receipt_service, review_service, shipping_service,
)

_TMP = None
_TEMPLATE = None
_REAL_DB = (db.DB_PATH, db.DATA_DIR)
_REAL_DIRS = (config.SLIPS_DIR, config.RECEIPTS_DIR, config.USER_IMAGES_DIR)


def setUpModule():
    global _TMP, _TEMPLATE
    _TMP = Path(tempfile.mkdtemp(prefix="shop_flow_test_"))
    _TEMPLATE = _TMP / "template.db"
    db.DATA_DIR, db.DB_PATH = _TMP, _TEMPLATE
    run_seed()
    db.DB_PATH, db.DATA_DIR = _REAL_DB
    config.SLIPS_DIR = _TMP / "slips"
    config.RECEIPTS_DIR = _TMP / "receipts"
    config.USER_IMAGES_DIR = _TMP / "users"


def tearDownModule():
    db.DB_PATH, db.DATA_DIR = _REAL_DB
    config.SLIPS_DIR, config.RECEIPTS_DIR, config.USER_IMAGES_DIR = _REAL_DIRS
    Session.logout()
    shutil.rmtree(_TMP, ignore_errors=True)


class FlowTestCase(unittest.TestCase):
    def setUp(self):
        self.path = _TMP / f"{self.id().split('.')[-1]}.db"
        shutil.copy(_TEMPLATE, self.path)
        db.DATA_DIR, db.DB_PATH = _TMP, self.path
        Session.logout()
        for folder in (config.SLIPS_DIR, config.RECEIPTS_DIR, config.USER_IMAGES_DIR):
            shutil.rmtree(folder, ignore_errors=True)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        Session.logout()
        db.DB_PATH = _REAL_DB[0]

    # ---------- ตัวช่วย ----------
    def as_user(self, username) -> int:
        row = repo_users.get_by_username(username)
        Session.login(row)
        return row["id"]

    def new_buyer(self, username="buyer2", with_address=True) -> int:
        """สมัครผู้ซื้อใหม่ผ่าน auth_service จริง แล้วล็อกอินเป็นคนนั้น (พร้อมที่อยู่ 1 แห่ง)"""
        user = auth_service.register(username, f"{username}@shop.com", "password1", username, "0891234567")
        uid = self.as_user(user["username"])
        if with_address:
            account_service.add_address(uid, "ผู้รับ ทดสอบ", "0891234567", "99/9 ถ.สุขุมวิท", "คลองเตย", "กรุงเทพ", "10110")
        return uid

    def pid(self, name) -> int:
        return self.row("SELECT id FROM products WHERE name = ?", (name,))["id"]

    def row(self, sql, params=()):
        conn = db.get_connection()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()

    def execute(self, sql, params=()):
        conn = db.get_connection()
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def stock(self, name) -> int:
        return self.row("SELECT stock FROM products WHERE name = ?", (name,))["stock"]

    def option_stock(self, option_id) -> int:
        return self.row("SELECT stock FROM product_options WHERE id = ?", (option_id,))["stock"]

    def address_id(self, user_id) -> int:
        return account_service.list_addresses(user_id)[0]["id"]

    def checkout(self, items, coupon=None):
        """ผู้ซื้อที่ล็อกอินอยู่ใส่ตะกร้า items = [(ชื่อสินค้า, จำนวน[, option_id])] แล้ว checkout ด้วยที่อยู่แรก"""
        uid = Session.get_user_id()
        for item in items:
            name, qty, *rest = item
            cart_service.add_to_cart(uid, self.pid(name), rest[0] if rest else None, qty)
        return order_service.checkout(uid, self.address_id(uid), coupon)

    def slip(self, name="slip.png") -> str:
        path = _TMP / name
        Image.new("RGB", (300, 400), "white").save(path)
        return str(path)

    def pay_and_verify(self, order_id, buyer="buyer1", staff="admin1"):
        self.as_user(buyer)
        payment_service.submit_slip(order_id, self.slip())
        self.as_user(staff)
        pending = payment_service.list_pending_payments()
        pay = next(p for p in pending if p["order_id"] == order_id)
        return payment_service.verify_payment(pay["id"])

    def make_paid_order(self, buyer="buyer1", items=(("Auraspeed 100X", 1),), coupon=None):
        self.as_user(buyer)
        order = self.checkout(list(items), coupon)
        self.pay_and_verify(order["id"], buyer)
        return order["id"]

    def make_shipped_order(self, **kwargs):
        oid = self.make_paid_order(**kwargs)
        self.as_user("admin1")
        shipping_service.ship_order(oid, "Kerry Express", "KER123456")
        return oid

    def backdate_order(self, order_id, hours):
        stamp = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        self.execute("UPDATE orders SET created_at = ? WHERE id = ?", (stamp, order_id))
        self.execute("UPDATE order_status_log SET created_at = ? WHERE order_id = ?", (stamp, order_id))


# ==========================================
# สั่งซื้อ + ราคา + คูปอง
# ==========================================
class TestCheckout(FlowTestCase):
    def test_full_flow_register_to_review(self):
        """สมัคร -> ตะกร้า -> คูปอง -> checkout -> สลิป -> ยืนยัน -> ส่ง -> รับของ -> รีวิว"""
        uid = self.new_buyer("flowuser")
        order = self.checkout([("Auraspeed 100X", 1), ("Master No.3", 2)], "save200")
        # 4800 + 850*2 = 6500 ; ลด 200 ; ค่าส่ง 50
        self.assertEqual((order["subtotal"], order["discount"], order["shipping_fee"], order["total"]),
                         (6500.0, 200.0, 50.0, 6350.0))
        self.assertEqual(order["status"], "pending")
        self.assertEqual(order["coupon_code"], "SAVE200")
        self.assertEqual(cart_service.get_cart(uid)["items"], [])
        self.assertEqual((self.stock("Auraspeed 100X"), self.stock("Master No.3")), (49, 98))
        self.assertEqual(repo_coupons.get_by_code("SAVE200")["used_count"], 1)
        self.assertIn("99/9", order["shipping_address"])
        self.assertEqual([t["status"] for t in order["timeline"]], ["pending"])
        self.assertTrue(repo_notifications.count_unread(self.row("SELECT id FROM users WHERE username='admin1'")["id"]))

        info = payment_service.get_payment_info(order["id"])
        self.assertEqual((info["amount"], info["can_submit_slip"], info["promptpay_no"]), (6350.0, True, "0812345678"))
        self.assertTrue(info["payload"].startswith("000201") and "6350.00" in info["payload"])

        detail = payment_service.submit_slip(order["id"], self.slip())
        self.assertEqual((detail["status"], detail["payment"]["status"]), ("checking_slip", "pending"))
        self.assertTrue(Path(detail["payment"]["slip_path"]).exists())

        self.as_user("admin1")
        pending = payment_service.list_pending_payments()
        self.assertEqual([p["order_id"] for p in pending], [order["id"]])
        paid = payment_service.verify_payment(pending[0]["id"])
        self.assertEqual((paid["status"], paid["payment"]["status"], paid["shipment"]["status"]),
                         ("paid", "verified", "preparing"))

        shipped = shipping_service.ship_order(order["id"], "Kerry Express", "KER 123456")
        self.assertEqual((shipped["status"], shipped["shipment"]["tracking_no"]), ("shipped", "KER123456"))

        self.as_user("flowuser")
        done = order_service.confirm_received(order["id"])
        self.assertEqual((done["status"], done["shipment"]["status"]), ("completed", "delivered"))
        self.assertEqual([t["status"] for t in done["timeline"]],
                         ["pending", "checking_slip", "paid", "shipped", "completed"])

        pid = self.pid("Auraspeed 100X")
        self.assertTrue(review_service.can_review(uid, pid, order["id"]))
        review_service.add_review(uid, pid, order["id"], 5, "ดีมาก")
        self.assertFalse(review_service.can_review(uid, pid, order["id"]))

        # รายได้นับเมื่อชำระแล้ว: owner เห็นเลข admin ไม่เห็น
        self.as_user("owner")
        self.assertEqual(order_service.get_dashboard_stats()["revenue_total"], 6350.0)
        self.as_user("admin1")
        stats = order_service.get_dashboard_stats()
        self.assertIsNone(stats["revenue_total"])
        self.assertTrue(all(d["revenue"] is None for d in stats["daily_sales"]))
        self.assertEqual(len(stats["daily_sales"]), 7)

    def test_option_price_and_flash_sale_expiry(self):
        """Flash Sale ยังไม่หมด = ราคาโปร + ส่วนต่างตัวเลือก · พอหมดเวลา ใช้ราคาเต็มทั้งในตะกร้าและตอน checkout"""
        uid = self.as_user("buyer1")
        astrox, bg65 = self.pid("Astrox 99 Pro"), 2   # option 2 = ขึ้นเอ็น BG65 (+220)
        cart_service.add_to_cart(uid, astrox, bg65, 1)
        self.assertEqual(cart_service.get_cart(uid)["items"][0]["unit_price"], 4800 + 220)
        repo_products.update_product(astrox, {"sale_ends_at": "2020-01-01 00:00:00"})  # โปรหมดเวลาแล้ว
        self.assertEqual(cart_service.get_cart(uid)["items"][0]["unit_price"], 5200 + 220)
        order = order_service.checkout(uid, self.address_id(uid))
        item = order["items"][0]
        self.assertEqual((item["price_at_purchase"], item["option_label"]), (5420.0, "เอ็น: ขึ้นเอ็น BG65"))
        self.assertEqual(self.option_stock(bg65), 19)
        self.assertEqual(self.stock("Astrox 99 Pro"), 49)  # สต็อกรวม sync จากตัวเลือก
        # ราคาในออเดอร์เป็นสำเนา: เปลี่ยนราคาสินค้าทีหลังไม่กระทบ
        repo_products.update_product(astrox, {"price": 9999})
        self.assertEqual(order_service.get_order_detail(order["id"])["items"][0]["price_at_purchase"], 5420.0)
        # โปรที่หมดแล้วตั้งแต่ seed (Z-Ziggler) ต้องคิดราคาเต็ม
        order2 = self.checkout([("Z-Ziggler", 1)])
        self.assertEqual(order2["subtotal"], 1200.0)

    def test_free_shipping_threshold_uses_subtotal_before_discount(self):
        repo_settings.set("free_shipping_min", "1000")
        self.as_user("buyer1")
        order = self.checkout([("Auraspeed 100X", 1)], "SAVE200")
        self.assertEqual((order["shipping_fee"], order["total"]), (0.0, 4600.0))

    def test_checkout_rejects_bad_input_and_changes_nothing(self):
        uid = self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "ว่างเปล่า"):
            order_service.checkout(uid, self.address_id(uid))
        cart_service.add_to_cart(uid, self.pid("Master No.3"), None, 2)
        with self.assertRaisesRegex(ValueError, "ไม่พบที่อยู่"):
            order_service.checkout(uid, 99999)
        # ที่อยู่ของคนอื่นใช้ไม่ได้
        other = self.new_buyer("other_one")
        foreign = self.address_id(other)
        self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "ไม่พบที่อยู่"):
            order_service.checkout(uid, foreign)
        with self.assertRaisesRegex(ValueError, "ไม่พบโค้ดส่วนลด"):
            order_service.checkout(uid, self.address_id(uid), "NOPE")
        self.assertEqual(self.stock("Master No.3"), 100)
        self.assertEqual(repo_orders.count_orders(), 0)
        self.assertEqual(cart_service.get_cart(uid)["item_count"], 2)

    def test_item_problem_blocks_checkout(self):
        uid = self.as_user("buyer1")
        tectonic_black = 8  # สต็อก 3
        cart_service.add_to_cart(uid, self.pid("Tectonic 9"), tectonic_black, 3)
        repo_products.adjust_option_stock(tectonic_black, -3)   # มีคนซื้อไปก่อน
        with self.assertRaisesRegex(ValueError, "Tectonic 9.*สินค้าหมด"):
            order_service.checkout(uid, self.address_id(uid))
        self.assertEqual(repo_orders.count_orders(), 0)

    def test_last_piece_two_buyers_second_gets_error_stock_never_negative(self):
        repo_products.adjust_stock(self.pid("Auraspeed 100X"), -49)  # เหลือ 1 ชิ้น
        first = self.new_buyer("first_one")
        cart_service.add_to_cart(first, self.pid("Auraspeed 100X"), None, 1)
        second = self.new_buyer("second_one")
        cart_service.add_to_cart(second, self.pid("Auraspeed 100X"), None, 1)
        stale_cart = cart_service.get_cart(second)           # ภาพตะกร้าก่อนคนแรกซื้อ (ยังเห็นว่ามีของ)
        self.assertFalse(stale_cart["has_problem"])

        self.as_user("first_one")
        order_service.checkout(first, self.address_id(first))
        self.assertEqual(self.stock("Auraspeed 100X"), 0)

        self.as_user("second_one")
        with self.assertRaisesRegex(ValueError, "สินค้าหมด"):                    # ทางปกติ: ตะกร้าแจ้งหมด
            order_service.checkout(second, self.address_id(second))
        with mock.patch.object(cart_service, "get_cart", return_value=stale_cart):  # ทางกันพลาด: ข้อมูลตะกร้าเก่า
            with self.assertRaisesRegex(ValueError, "สต็อกไม่พอ"):
                order_service.checkout(second, self.address_id(second))
        self.assertEqual(self.stock("Auraspeed 100X"), 0)
        self.assertEqual(repo_orders.count_orders(user_id=second), 0)
        self.assertEqual(repo_cart_count(second), 1)  # ตะกร้ายังอยู่ ไม่เสียของ

    def test_coupon_rules(self):
        uid = self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "ขั้นต่ำ"):
            self.checkout([("VS 100", 1)], "SAVE200")            # ยอด 550 ไม่ถึงขั้นต่ำ 2000
        self.assertEqual(repo_orders.count_orders(), 0)
        cart_service.clear_cart(uid)
        with self.assertRaisesRegex(ValueError, "หมดอายุ"):
            self.checkout([("Auraspeed 100X", 1)], "OLD50")
        cart_service.clear_cart(uid)
        order = self.checkout([("Auraspeed 100X", 1)], "welcome10")
        self.assertEqual(order["discount"], 480.0)
        self.assertEqual(repo_coupons.get_by_code("WELCOME10")["used_count"], 1)
        # ใช้ซ้ำไม่ได้ และพลาดแล้วตะกร้า/สต็อก/จำนวนใช้คูปองต้องไม่เปลี่ยน
        with self.assertRaisesRegex(ValueError, "ไปแล้ว"):
            self.checkout([("Auraspeed 100X", 1)], "WELCOME10")
        self.assertEqual(repo_coupons.get_by_code("WELCOME10")["used_count"], 1)
        self.assertEqual(self.stock("Auraspeed 100X"), 49)
        self.assertEqual(cart_service.get_cart(uid)["item_count"], 1)

    def test_coupon_max_uses_full(self):
        self.as_user("buyer1")
        self.execute("UPDATE coupons SET max_uses = 1, used_count = 1 WHERE code = 'SAVE200'")
        with self.assertRaisesRegex(ValueError, "ครบสิทธิ์"):
            self.checkout([("Auraspeed 100X", 1)], "SAVE200")

    def test_low_stock_notification_only_when_crossing_threshold(self):
        admin_id = self.row("SELECT id FROM users WHERE username='admin1'")["id"]
        self.as_user("buyer1")
        before = repo_notifications.count_unread(admin_id)
        self.checkout([("Tectonic 9", 1, 8)])   # option 8: 3 -> 2 (3 <= 5 แล้ว ไม่ข้ามเกณฑ์) ไม่แจ้งสต็อกซ้ำ
        titles = [n["title"] for n in repo_notifications.list(admin_id)]
        self.assertEqual(repo_notifications.count_unread(admin_id) - before, 1)  # มีแค่ "คำสั่งซื้อใหม่"
        self.assertNotIn("สินค้าใกล้หมด", titles)
        repo_products.adjust_stock(self.pid("Master No.3"), -94)                  # เหลือ 6 (เหนือเกณฑ์ 5)
        self.checkout([("Master No.3", 2)])                                        # 6 -> 4 ข้ามเกณฑ์
        self.assertIn("สินค้าใกล้หมด", [n["title"] for n in repo_notifications.list(admin_id)])


def repo_cart_count(user_id):
    from database import repo_cart
    return repo_cart.count(user_id)


# ==========================================
# ยกเลิก + ยกเลิกอัตโนมัติ
# ==========================================
class TestCancel(FlowTestCase):
    def test_buyer_cancel_pending_restores_stock_and_coupon(self):
        uid = self.as_user("buyer1")
        order = self.checkout([("Auraspeed 100X", 2), ("Astrox 99 Pro", 1, 3)], "SAVE200")
        self.assertEqual((self.stock("Auraspeed 100X"), self.option_stock(3), self.stock("Astrox 99 Pro")), (48, 9, 49))
        coupon_id = repo_coupons.get_by_code("SAVE200")["id"]
        with self.assertRaisesRegex(ValueError, "เหตุผล"):
            order_service.cancel_order(order["id"], "  ")
        cancelled = order_service.cancel_order(order["id"], "เปลี่ยนใจ")
        self.assertEqual((cancelled["status"], cancelled["cancel_reason"]), ("cancelled", "เปลี่ยนใจ"))
        self.assertEqual((self.stock("Auraspeed 100X"), self.option_stock(3), self.stock("Astrox 99 Pro")), (50, 10, 50))
        self.assertEqual(repo_coupons.get_by_code("SAVE200")["used_count"], 0)
        self.assertFalse(repo_coupons.has_used(uid, coupon_id))
        with self.assertRaisesRegex(ValueError, "ยกเลิกไปแล้ว"):
            order_service.cancel_order(order["id"], "อีกที")
        # คูปองกลับมาใช้ได้อีก
        again = self.checkout([("Auraspeed 100X", 1)], "SAVE200")
        self.assertEqual(again["discount"], 200.0)

    def test_buyer_cannot_cancel_after_slip_or_others_orders(self):
        self.as_user("buyer1")
        order = self.checkout([("Auraspeed 100X", 1)])
        payment_service.submit_slip(order["id"], self.slip())
        with self.assertRaisesRegex(ValueError, "ยังไม่ชำระเงิน"):
            order_service.cancel_order(order["id"], "ขอยกเลิก")
        self.new_buyer("intruder")
        with self.assertRaises(PermissionError):
            order_service.cancel_order(order["id"], "ขอยกเลิก")
        self.as_user("buyer1")
        order2 = self.checkout([("VS 100", 1)])
        self.as_user("intruder")
        with self.assertRaises(PermissionError):
            order_service.cancel_order(order2["id"], "ขอยกเลิก")

    def test_staff_cancel_checking_slip_closes_pending_payment(self):
        self.as_user("buyer1")
        order = self.checkout([("Auraspeed 100X", 1)])
        payment_service.submit_slip(order["id"], self.slip())
        self.as_user("admin1")
        self.assertEqual(len(payment_service.list_pending_payments()), 1)
        order_service.cancel_order(order["id"], "ลูกค้าขอยกเลิก")
        self.assertEqual(payment_service.list_pending_payments(), [])
        self.assertEqual(self.stock("Auraspeed 100X"), 50)

    def test_staff_cancel_paid_notes_manual_refund_but_not_shipped(self):
        paid_id = self.make_paid_order()
        self.as_user("admin1")
        cancelled = order_service.cancel_order(paid_id, "สินค้าหมดจริง")
        self.assertIn("คืนเงิน", cancelled["timeline"][-1]["note"])
        self.assertEqual(self.stock("Auraspeed 100X"), 50)
        buyer_id = self.row("SELECT id FROM users WHERE username='buyer1'")["id"]
        self.assertIn("คำสั่งซื้อถูกยกเลิก", [n["title"] for n in repo_notifications.list(buyer_id)])

        shipped_id = self.make_shipped_order(items=(("VS 100", 1),))
        self.as_user("owner")
        with self.assertRaisesRegex(ValueError, "ยกเลิกไม่ได้"):
            order_service.cancel_order(shipped_id, "ทดสอบ")

    def test_auto_cancel_unpaid(self):
        self.as_user("buyer1")
        old = self.checkout([("Auraspeed 100X", 1)], "SAVE200")
        recent = self.checkout([("VS 100", 1)])
        self.backdate_order(old["id"], 25)
        self.backdate_order(recent["id"], 2)
        self.assertEqual(order_service.auto_cancel_unpaid(), 1)
        self.assertEqual(order_service.get_order_detail(old["id"])["status"], "cancelled")
        self.assertIn("24 ชั่วโมง", order_service.get_order_detail(old["id"])["cancel_reason"])
        self.assertEqual(order_service.get_order_detail(recent["id"])["status"], "pending")
        self.assertEqual((self.stock("Auraspeed 100X"), repo_coupons.get_by_code("SAVE200")["used_count"]), (50, 0))
        self.assertEqual(order_service.auto_cancel_unpaid(), 0)   # รอบสอง ไม่มีอะไรให้ยกเลิก

    def test_auto_cancel_disabled_and_ignores_paid(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        self.backdate_order(order["id"], 100)
        repo_settings.set("unpaid_cancel_hours", "0")
        self.assertEqual(order_service.auto_cancel_unpaid(), 0)
        repo_settings.set("unpaid_cancel_hours", "24")
        paid_id = self.make_paid_order()
        self.backdate_order(paid_id, 100)
        self.assertEqual(order_service.auto_cancel_unpaid(), 1)   # เฉพาะใบ pending
        self.assertEqual(order_service.get_order_detail(paid_id)["status"], "paid")

    def test_rejected_slip_restarts_unpaid_timer(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        payment_service.submit_slip(order["id"], self.slip())
        self.backdate_order(order["id"], 30)            # สั่งไว้ 30 ชม. ก่อน
        self.as_user("admin1")
        payment_service.reject_payment(payment_service.list_pending_payments()[0]["id"], "ยอดไม่ตรง")
        self.assertEqual(order_service.auto_cancel_unpaid(), 0)   # เพิ่งกลับมา pending ให้เวลาแนบใหม่


# ==========================================
# ชำระเงิน / จัดส่ง
# ==========================================
class TestPaymentShipping(FlowTestCase):
    def test_reject_then_resubmit_then_verify(self):
        self.as_user("buyer1")
        order = self.checkout([("Auraspeed 100X", 1)])
        payment_service.submit_slip(order["id"], self.slip("a.png"))
        self.as_user("admin1")
        first = payment_service.list_pending_payments()[0]["id"]
        with self.assertRaisesRegex(ValueError, "เหตุผล"):
            payment_service.reject_payment(first, " ")
        rejected = payment_service.reject_payment(first, "ยอดเงินไม่ตรง")
        self.assertEqual((rejected["status"], rejected["payment"]["status"], rejected["payment"]["reject_reason"]),
                         ("pending", "rejected", "ยอดเงินไม่ตรง"))
        with self.assertRaisesRegex(ValueError, "ตรวจสอบไปแล้ว"):
            payment_service.verify_payment(first)

        self.as_user("buyer1")
        info = payment_service.get_payment_info(order["id"])
        self.assertTrue(info["can_submit_slip"])
        self.assertEqual(info["payment"]["reject_reason"], "ยอดเงินไม่ตรง")
        payment_service.submit_slip(order["id"], self.slip("b.png"))
        self.assertEqual(len(payment_service.get_payment_info(order["id"])["history"]), 2)
        self.as_user("admin1")
        paid = payment_service.verify_payment(payment_service.list_pending_payments()[0]["id"])
        self.assertEqual(paid["status"], "paid")
        with self.assertRaisesRegex(ValueError, "ตรวจสอบไปแล้ว"):
            payment_service.verify_payment(paid["payment"]["id"])
        self.assertEqual(self.row("SELECT COUNT(*) AS n FROM shipments WHERE order_id=?", (order["id"],))["n"], 1)

    def test_submit_slip_validations_and_cleanup(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        bad = _TMP / "note.txt"
        bad.write_text("not an image")
        with self.assertRaisesRegex(ValueError, "jpg"):
            payment_service.submit_slip(order["id"], str(bad))
        with self.assertRaisesRegex(ValueError, "ไม่พบไฟล์"):
            payment_service.submit_slip(order["id"], str(_TMP / "missing.png"))
        self.assertEqual(order_service.get_order_detail(order["id"])["status"], "pending")
        # DB พลาดหลังบันทึกไฟล์ -> ไฟล์สลิปถูกลบ สถานะไม่เปลี่ยน
        with mock.patch.object(repo_payments, "create", side_effect=sqlite3.OperationalError("boom")):
            with self.assertRaises(sqlite3.OperationalError):
                payment_service.submit_slip(order["id"], self.slip())
        self.assertEqual(list(Path(config.SLIPS_DIR).glob("*")) if Path(config.SLIPS_DIR).exists() else [], [])
        self.assertEqual(order_service.get_order_detail(order["id"])["status"], "pending")
        payment_service.submit_slip(order["id"], self.slip())
        with self.assertRaisesRegex(ValueError, "รอชำระเงิน"):   # แนบซ้ำตอนรอตรวจไม่ได้
            payment_service.submit_slip(order["id"], self.slip())

    def test_payment_info_permissions_and_missing_promptpay(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        self.new_buyer("peeker")
        with self.assertRaises(PermissionError):
            payment_service.get_payment_info(order["id"])
        with self.assertRaises(PermissionError):
            payment_service.submit_slip(order["id"], self.slip())
        self.as_user("buyer1")
        repo_settings.set("promptpay_no", "")
        with self.assertRaisesRegex(ValueError, "เลขพร้อมเพย์"):
            payment_service.get_payment_info(order["id"])

    def test_ship_order_validations(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        self.as_user("admin1")
        with self.assertRaisesRegex(ValueError, "ชำระเงินแล้ว"):
            shipping_service.ship_order(order["id"], "Kerry Express", "KER123456")   # ยังไม่จ่าย = ข้ามขั้นไม่ได้
        paid_id = self.make_paid_order(items=(("Master No.3", 1),))
        self.as_user("admin1")
        with self.assertRaisesRegex(ValueError, "ขนส่ง"):
            shipping_service.ship_order(paid_id, "รถเมล์", "KER123456")
        with self.assertRaisesRegex(ValueError, "เลขพัสดุ"):
            shipping_service.ship_order(paid_id, "Flash Express", "  ")
        with self.assertRaisesRegex(ValueError, "เลขพัสดุ"):
            shipping_service.ship_order(paid_id, "Flash Express", "ก๊อกๆ!")
        self.as_user("buyer1")
        with self.assertRaises(PermissionError):
            shipping_service.ship_order(paid_id, "Flash Express", "TH12345678")
        self.as_user("admin1")
        shipping_service.ship_order(paid_id, "Flash Express", "TH12345678")
        with self.assertRaisesRegex(ValueError, "ชำระเงินแล้ว"):
            shipping_service.ship_order(paid_id, "Flash Express", "TH12345678")   # ส่งซ้ำไม่ได้
        fixed = shipping_service.update_tracking(paid_id, "J&T Express", "JT99887766")
        self.assertEqual((fixed["status"], fixed["shipment"]["carrier"]), ("shipped", "J&T Express"))
        self.assertIn("แก้ไขข้อมูลพัสดุ", fixed["timeline"][-1]["note"])

    def test_mark_delivered_and_confirm_received_rules(self):
        oid = self.make_paid_order()
        self.as_user("admin1")
        with self.assertRaisesRegex(ValueError, "จัดส่งแล้ว"):
            shipping_service.mark_delivered(oid)            # ยังไม่ได้ส่ง
        self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "จัดส่งแล้ว"):
            order_service.confirm_received(oid)
        self.as_user("admin1")
        shipping_service.ship_order(oid, "ไปรษณีย์ไทย", "EF123456789TH")
        self.new_buyer("not_mine")
        with self.assertRaises(PermissionError):
            order_service.confirm_received(oid)
        with self.assertRaises(PermissionError):
            shipping_service.get_shipment(oid)
        self.as_user("admin1")
        self.assertEqual(shipping_service.get_shipment(oid)["status_label"], "ส่งมอบขนส่งแล้ว")
        done = shipping_service.mark_delivered(oid)
        self.assertEqual((done["status"], done["shipment"]["status"]), ("completed", "delivered"))
        with self.assertRaisesRegex(ValueError, "จัดส่งแล้ว"):
            shipping_service.mark_delivered(oid)            # กดซ้ำไม่ได้
        buyer_id = self.row("SELECT id FROM users WHERE username='buyer1'")["id"]
        self.assertIn("สินค้าส่งถึงแล้ว", [n["title"] for n in repo_notifications.list(buyer_id)])

    def test_get_shipment_none_before_payment(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        self.assertIsNone(shipping_service.get_shipment(order["id"]))


# ==========================================
# สิทธิ์ + การดูข้อมูล
# ==========================================
class TestPermissionsAndListing(FlowTestCase):
    def test_order_visibility(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        self.new_buyer("stranger")
        with self.assertRaises(PermissionError):
            order_service.get_order_detail(order["id"])
        with self.assertRaises(PermissionError):
            order_service.get_timeline(order["id"])
        with self.assertRaises(PermissionError):
            order_service.list_my_orders(self.row("SELECT id FROM users WHERE username='buyer1'")["id"])
        with self.assertRaises(PermissionError):
            order_service.list_orders_admin()
        with self.assertRaises(PermissionError):
            order_service.get_dashboard_stats()
        for who in ("admin1", "owner"):
            self.as_user(who)
            self.assertEqual(order_service.get_order_detail(order["id"])["buyer_username"], "buyer1")
        with self.assertRaisesRegex(ValueError, "ไม่พบ"):
            order_service.get_order_detail(99999)

    def test_only_buyers_can_checkout_and_login_required(self):
        with self.assertRaises(PermissionError):
            order_service.checkout(3, 1)
        uid = self.as_user("owner")
        with self.assertRaises(PermissionError):
            order_service.checkout(uid, 1)           # เจ้าของร้านไม่ใช่ผู้ซื้อ (ตามตารางสิทธิ์)
        self.as_user("buyer1")
        with self.assertRaises(PermissionError):
            payment_service.verify_payment(1)
        with self.assertRaises(PermissionError):
            payment_service.list_pending_payments()
        with self.assertRaises(PermissionError):
            shipping_service.mark_delivered(1)

    def test_listing_filters_search_and_paging(self):
        uid = self.as_user("buyer1")
        ids = [self.checkout([(n, 1)])["id"] for n in ("VS 100", "A+ 300", "Master No.3")]
        order_service.cancel_order(ids[0], "ทดสอบ")
        page = order_service.list_my_orders(uid, page=1, page_size=2)
        self.assertEqual((page["total"], page["pages"], [o["id"] for o in page["items"]]), (3, 2, [ids[2], ids[1]]))
        self.assertEqual(page["items"][0]["items"][0]["product_name"], "Master No.3")
        only = order_service.list_my_orders(uid, status="cancelled")
        self.assertEqual([o["id"] for o in only["items"]], [ids[0]])
        multi = order_service.list_my_orders(uid, status=["pending", "cancelled"])
        self.assertEqual(multi["total"], 3)
        with self.assertRaisesRegex(ValueError, "สถานะ"):
            order_service.list_my_orders(uid, status="weird")
        self.as_user("admin1")
        self.assertEqual(order_service.list_orders_admin(search="buyer1")["total"], 3)
        self.assertEqual(order_service.list_orders_admin(search=f"#{ids[1]}")["total"], 1)
        self.assertEqual(order_service.list_orders_admin(status="paid")["total"], 0)
        self.assertEqual(order_service.list_orders_admin(page=99)["page"], 1)

    def test_dashboard_counts_and_top_products(self):
        self.make_paid_order(items=(("Master No.3", 3),))
        self.as_user("buyer1")
        self.checkout([("VS 100", 1)])
        self.as_user("owner")
        stats = order_service.get_dashboard_stats(days=3)
        self.assertEqual((stats["counts"]["paid"], stats["counts"]["pending"], stats["pending_slips"]), (1, 1, 0))
        self.assertEqual(stats["top_products"][0]["product_name"], "Master No.3")
        self.assertEqual(stats["top_products"][0]["total_sales"], 2550.0)
        self.assertEqual((len(stats["daily_sales"]), stats["daily_sales"][-1]["orders"]), (3, 1))
        self.assertEqual(stats["revenue_today"], stats["revenue_month"])
        self.as_user("admin1")
        self.assertIsNone(order_service.get_dashboard_stats()["top_products"][0]["total_sales"])


# ==========================================
# ใบเสร็จ PDF
# ==========================================
class TestReceipt(FlowTestCase):
    def test_markup_font_split_marks_and_escape(self):
        fonts = {"latin": "L", "latin_bold": "LB", "thai": "T", "thai_bold": "TB"}
        m = receipt_service._markup("Yonex ราคา 1,290 บาท & <ok>", 10, fonts)
        self.assertIn('<font name="T">ราคา</font>', m)
        self.assertIn('<font name="T">บาท</font>', m)
        self.assertTrue(m.startswith("Yonex ") and "&amp; &lt;ok&gt;" in m)
        stacked = receipt_service._markup("ชื่อ", 10, fonts, bold=True)
        self.assertIn('<font name="TB">', stacked)
        self.assertIn("<super", stacked)                       # วรรณยุกต์บนสระบนถูกยกขึ้น
        self.assertNotIn("<super", receipt_service._markup("น้ำ", 10, fonts))   # ไม่มีสระบนไม่ต้องยก
        self.assertNotIn("฿", receipt_service._markup("ราคา", 10, fonts))

    def test_status_rules_and_missing_thai_font(self):
        self.as_user("buyer1")
        order = self.checkout([("VS 100", 1)])
        with self.assertRaisesRegex(ValueError, "ชำระเงินแล้ว"):
            receipt_service.generate_receipt(order["id"])
        paid_id = self.make_paid_order()
        self.as_user("buyer1")
        with mock.patch.object(receipt_service, "find_thai_font", return_value=None):
            with self.assertRaisesRegex(ValueError, "ฟอนต์ภาษาไทย"):
                receipt_service.generate_receipt(paid_id)
        self.as_user("admin1")
        order_service.cancel_order(paid_id, "ทดสอบ")
        with self.assertRaisesRegex(ValueError, "ชำระเงินแล้ว"):
            receipt_service.generate_receipt(paid_id)
        with self.assertRaisesRegex(ValueError, "ไม่พบ"):
            receipt_service.generate_receipt(99999)

    @unittest.skipUnless(receipt_service.find_thai_font(), "เครื่องนี้ไม่มีฟอนต์ไทยของระบบ")
    def test_generate_pdf_with_os_thai_font(self):
        oid = self.make_paid_order(items=(("Auraspeed 100X", 1), ("Astrox 99 Pro", 1, 2)), coupon="SAVE200")
        self.as_user("buyer1")
        rel = receipt_service.generate_receipt(oid)
        pdf = Path(rel) if Path(rel).is_absolute() else Path(config.BASE_DIR) / rel
        self.assertTrue(pdf.exists() and pdf.name == f"receipt_{oid}.pdf")
        data = pdf.read_bytes()
        self.assertTrue(data.startswith(b"%PDF") and b"%%EOF" in data[-32:] and len(data) > 2000)
        first_size = pdf.stat().st_size
        self.assertEqual(receipt_service.generate_receipt(oid), rel)       # สร้างซ้ำได้ เขียนทับ
        self.assertEqual(len(list(pdf.parent.glob("*"))), 1)               # ไม่มีไฟล์ชั่วคราวค้าง
        self.assertGreater(first_size, 0)
        self.new_buyer("snoop")
        with self.assertRaises(PermissionError):
            receipt_service.generate_receipt(oid)
        self.as_user("admin1")
        self.assertEqual(receipt_service.generate_receipt(oid), rel)       # staff ออกให้ได้


# ==========================================
# ที่อยู่ / wishlist / โปรไฟล์
# ==========================================
class TestAccount(FlowTestCase):
    def test_address_lifecycle_and_ownership(self):
        uid = self.new_buyer("addr_user", with_address=False)
        first = account_service.add_address(uid, " สมชาย  ใจดี ", "089-123 4567", "1/1 ซ.1", "บางรัก", "กรุงเทพ", "10500")
        self.assertTrue(first["is_default"])                      # ที่อยู่แรกเป็นหลักเสมอ
        self.assertEqual((first["recipient"], first["phone"]), ("สมชาย ใจดี", "0891234567"))
        second = account_service.add_address(uid, "สมหญิง", "0812345678", "2/2", "เมือง", "เชียงใหม่", "50000")
        self.assertFalse(second["is_default"])
        third = account_service.add_address(uid, "สมศรี", "0812345679", "3/3", "เมือง", "ขอนแก่น", "40000", True)
        self.assertEqual([a["is_default"] for a in account_service.list_addresses(uid)], [True, False, False])
        self.assertEqual(account_service.list_addresses(uid)[0]["id"], third["id"])
        account_service.set_default_address(uid, second["id"])
        self.assertEqual(account_service.get_address(uid, second["id"])["is_default"], True)
        updated = account_service.update_address(uid, first["id"], "ใหม่", "0899999999", "9/9", "ดินแดง", "กรุงเทพ", "10400")
        self.assertEqual((updated["recipient"], updated["is_default"]), ("ใหม่", False))
        account_service.delete_address(uid, second["id"])        # ลบหลัก -> ตั้งตัวที่เหลือเป็นหลักให้
        self.assertEqual(sum(a["is_default"] for a in account_service.list_addresses(uid)), 1)

        for bad_args, msg in (
            (("", "0812345678", "x", "y", "z", "10000"), "ชื่อผู้รับ"),
            (("a", "12345", "x", "y", "z", "10000"), "เบอร์โทร"),
            (("a", "0812345678", "x", "y", "z", "1000"), "รหัสไปรษณีย์"),
            (("a", "0812345678", "", "y", "z", "10000"), "ที่อยู่"),
        ):
            with self.assertRaisesRegex(ValueError, msg):
                account_service.add_address(uid, *bad_args)

        other = self.new_buyer("addr_other")
        with self.assertRaisesRegex(ValueError, "ไม่พบที่อยู่"):
            account_service.delete_address(other, first["id"])
        with self.assertRaisesRegex(ValueError, "ไม่พบที่อยู่"):
            account_service.set_default_address(other, first["id"])
        with self.assertRaises(PermissionError):
            account_service.list_addresses(uid)                   # ดูของคนอื่นไม่ได้

    def test_address_limit_and_address_copy_in_order(self):
        uid = self.as_user("buyer1")                              # seed มี 2 แห่ง
        for i in range(account_service.MAX_ADDRESSES - 2):
            account_service.add_address(uid, "ผู้รับ", "0812345678", f"{i}/1", "เมือง", "ภูเก็ต", "83000")
        with self.assertRaisesRegex(ValueError, "สูงสุด"):
            account_service.add_address(uid, "ผู้รับ", "0812345678", "x", "เมือง", "ภูเก็ต", "83000")
        order = self.checkout([("VS 100", 1)])
        addr = account_service.list_addresses(uid)[0]
        account_service.delete_address(uid, addr["id"])           # ลบที่อยู่แล้ว ออเดอร์ต้องยังมีที่อยู่เดิม
        self.assertIn(addr["address_line"], order_service.get_order_detail(order["id"])["shipping_address"])

    def test_wishlist(self):
        uid = self.as_user("buyer1")
        pid = self.pid("Astrox 99 Pro")
        self.assertEqual(account_service.toggle_wishlist(uid, pid), {"in_wishlist": True})
        account_service.toggle_wishlist(uid, self.pid("VS 100"))
        items = account_service.list_wishlist(uid)
        self.assertEqual([i["name"] for i in items], ["VS 100", "Astrox 99 Pro"])
        astrox = items[1]
        self.assertTrue(astrox["is_on_sale"] and astrox["in_wishlist"] and astrox["effective_price"] == 4800)
        self.assertEqual(account_service.wishlist_ids(uid), {pid, self.pid("VS 100")})
        self.assertEqual(account_service.toggle_wishlist(uid, pid), {"in_wishlist": False})
        repo_products.set_product_active(self.pid("VS 100"), False)
        self.assertEqual(account_service.list_wishlist(uid), [])                 # ปิดขายแล้วไม่โชว์
        self.assertEqual(account_service.toggle_wishlist(uid, self.pid("VS 100")), {"in_wishlist": False})  # เอาออกได้เสมอ
        with self.assertRaisesRegex(ValueError, "ไม่พบสินค้า"):
            account_service.toggle_wishlist(uid, self.pid("VS 100"))             # เพิ่มสินค้าปิดขายไม่ได้
        with self.assertRaisesRegex(ValueError, "ไม่พบสินค้า"):
            account_service.toggle_wishlist(uid, 99999)
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            account_service.wishlist_ids(uid)

    def test_profile_and_avatar(self):
        uid = self.as_user("buyer1")
        profile = account_service.get_profile(uid)
        self.assertEqual((profile["address_count"], profile["role_label"], profile["wishlist_count"]), (2, "ผู้ซื้อ", 0))
        self.assertTrue(profile["default_address"]["is_default"])
        self.assertNotIn("password_hash", profile)
        self.checkout([("VS 100", 1)])
        self.assertEqual(account_service.get_profile(uid)["order_count"], 1)
        updated = account_service.set_avatar(uid, self.slip("me.png"))
        self.assertTrue(Path(updated["avatar_path"]).exists())
        self.assertEqual(updated["full_name"], profile["full_name"])
        with self.assertRaisesRegex(ValueError, "ไม่พบไฟล์"):
            account_service.set_avatar(uid, str(_TMP / "none.png"))
        with self.assertRaises(PermissionError):
            account_service.get_profile(uid + 1)
        admin_id = self.as_user("admin1")
        staff = account_service.get_profile(admin_id)
        self.assertEqual((staff["address_count"], staff["order_count"], staff["default_address"]), (0, 0, None))


# ==========================================
# AI (จำลองด้วย mock — ไม่เรียกเน็ต)
# ==========================================
class TestAI(FlowTestCase):
    def test_not_configured_returns_fallback_without_calling_api(self):
        with mock.patch.object(config, "GEMINI_API_KEY", ""), \
                mock.patch.object(ai_service, "_call_gemini") as api:
            self.assertFalse(ai_service.is_configured())
            self.assertEqual(ai_service.ask([], "ไม้ราคาไม่เกิน 3000"), ai_service.FALLBACK_MESSAGE)
            api.assert_not_called()

    def test_ask_success_and_every_failure_returns_fallback(self):
        with mock.patch.object(ai_service, "is_configured", return_value=True):
            with mock.patch.object(ai_service, "_call_gemini", return_value="  แนะนำ Auraspeed 100X ครับ ") as api:
                history = [{"sender_type": "admin", "message": "สวัสดี"}, {"sender_type": "user", "message": "ถาม"},
                           {"sender_type": "user", "message": "อีกข้อ"}]
                self.assertEqual(ai_service.ask(history, "มีไม้ไหม"), "แนะนำ Auraspeed 100X ครับ")
                prompt, contents = api.call_args[0]
                self.assertEqual([c["role"] for c in contents], ["user"])           # ตัด model นำหน้า + รวมเทิร์นซ้ำ
                self.assertIn("ถาม\nอีกข้อ\nมีไม้ไหม", contents[0]["text"])
            for failure in (TimeoutError("timeout"), ConnectionError("offline"), RuntimeError("quota")):
                with mock.patch.object(ai_service, "_call_gemini", side_effect=failure):
                    self.assertEqual(ai_service.ask([], "ทดสอบ"), ai_service.FALLBACK_MESSAGE)
            with mock.patch.object(ai_service, "_call_gemini", return_value="   "):
                self.assertEqual(ai_service.ask([], "ทดสอบ"), ai_service.FALLBACK_MESSAGE)
            self.assertEqual(ai_service.ask([], "   "), ai_service.FALLBACK_MESSAGE)

    def test_system_prompt_uses_live_db_data(self):
        repo_settings.set("shop_name", "ร้านทดสอบ")
        prompt = ai_service.build_system_prompt()
        self.assertIn("ร้านทดสอบ", prompt)
        self.assertIn("Auraspeed 100X | Victor", prompt) if "Victor" in prompt else self.assertIn("Auraspeed 100X", prompt)
        self.assertIn("ห้ามแต่งราคา", prompt)
        self.assertNotIn("฿", prompt)
        repo_products.update_product(self.pid("Auraspeed 100X"), {"price": 4321})
        self.assertIn("4,321 บาท", ai_service.build_system_prompt())
        repo_products.set_product_active(self.pid("Auraspeed 100X"), False)
        self.assertNotIn("Auraspeed 100X", ai_service.build_system_prompt())


# ==========================================
# แชท
# ==========================================
class TestChat(FlowTestCase):
    def set_staff_online(self, username, online=True):
        repo_users.set_online(repo_users.get_by_username(username)["id"], online)

    def test_ai_replies_when_no_staff_online(self):
        uid = self.as_user("buyer1")
        with mock.patch.object(ai_service, "ask", return_value="AI ตอบแล้ว") as ask:
            result = chat_service.send_message(uid, "  อยากได้ไม้บุก  ", background=False)
        self.assertTrue(result["ai_pending"])
        self.assertEqual(result["message"]["message"], "อยากได้ไม้บุก")
        history, question = ask.call_args[0]
        self.assertEqual((history, question), ([], "อยากได้ไม้บุก"))
        msgs = chat_service.get_messages(uid)
        self.assertEqual([(m["sender_type"], m["sender_name"]) for m in msgs], [("user", None), ("ai", "ผู้ช่วย AI")])
        self.assertEqual(msgs[1]["message"], "AI ตอบแล้ว")

    def test_no_ai_when_staff_online_or_ai_disabled(self):
        uid = self.as_user("buyer1")
        self.set_staff_online("admin1")
        with mock.patch.object(ai_service, "ask") as ask:
            self.assertFalse(chat_service.send_message(uid, "สวัสดี", background=False)["ai_pending"])
            ask.assert_not_called()
        self.assertEqual(len(chat_service.get_messages(uid)), 1)
        self.set_staff_online("admin1", False)
        repo_settings.set("ai_enabled", "0")
        with mock.patch.object(ai_service, "ask") as ask:
            self.assertFalse(chat_service.send_message(uid, "สวัสดีอีกที", background=False)["ai_pending"])
            ask.assert_not_called()

    def test_ai_reply_dropped_if_staff_comes_online_while_waiting(self):
        uid = self.as_user("buyer1")
        def slow_ask(history, question):
            self.set_staff_online("admin1")        # แอดมินเพิ่งเข้าระบบระหว่างรอ AI
            return "ตอบช้า"
        with mock.patch.object(ai_service, "ask", side_effect=slow_ask):
            chat_service.send_message(uid, "ถามหน่อย", background=False)
        self.assertEqual([m["sender_type"] for m in chat_service.get_messages(uid)], ["user"])

    def test_ai_reply_dropped_if_staff_already_replied(self):
        uid = self.as_user("buyer1")
        admin_id = repo_users.get_by_username("admin1")["id"]
        def ask_then_staff_replies(history, question):
            repo_chat.add_message(uid, "admin", admin_id, "แอดมินตอบเองแล้ว")
            return "คำตอบ AI"
        with mock.patch.object(ai_service, "ask", side_effect=ask_then_staff_replies):
            chat_service.send_message(uid, "ถามหน่อย", background=False)
        self.assertEqual([m["sender_type"] for m in chat_service.get_messages(uid)], ["user", "admin"])

    def test_fallback_message_not_repeated_and_ai_crash_never_raises(self):
        uid = self.as_user("buyer1")
        with mock.patch.object(ai_service, "ask", return_value=ai_service.FALLBACK_MESSAGE):
            chat_service.send_message(uid, "ข้อ 1", background=False)
            chat_service.send_message(uid, "ข้อ 2", background=False)
        senders = [m["sender_type"] for m in chat_service.get_messages(uid)]
        self.assertEqual(senders, ["user", "ai", "user"])           # ข้อความสำรองส่งครั้งเดียว
        with mock.patch.object(ai_service, "ask", side_effect=RuntimeError("พัง")):
            result = chat_service.send_message(uid, "ข้อ 3", background=False)   # ต้องไม่โยน error ให้ลูกค้า
        self.assertEqual(result["message"]["message"], "ข้อ 3")

    def test_background_thread_saves_ai_reply(self):
        uid = self.as_user("buyer1")
        with mock.patch.object(ai_service, "ask", return_value="ตอบใน thread"):
            chat_service.send_message(uid, "สวัสดี")                # background=True (ค่าปกติ)
            for _ in range(50):
                if len(repo_chat.list_messages(uid)) == 2:
                    break
                time.sleep(0.05)
        self.assertEqual([m["message"] for m in repo_chat.list_messages(uid)], ["สวัสดี", "ตอบใน thread"])

    def test_staff_reply_unread_counts_and_polling(self):
        uid = self.as_user("buyer1")
        self.set_staff_online("admin1")
        chat_service.send_message(uid, "ไม้ยังมีไหม", background=False)
        self.as_user("admin1")
        self.assertEqual(chat_service.unread_count(), 1)
        threads = chat_service.list_threads()
        self.assertEqual((threads[0]["customer_id"], threads[0]["unread_count"]), (uid, 1))
        reply = chat_service.staff_reply(uid, "มีครับ")
        self.assertEqual((reply["sender_type"], reply["sender_name"]), ("admin", "Shop Admin"))
        self.assertEqual(len(chat_service.get_messages(uid)), 2)       # แอดมินเปิดห้อง = อ่านข้อความลูกค้าแล้ว
        self.assertEqual(chat_service.unread_count(), 0)
        self.as_user("buyer1")
        self.assertEqual(chat_service.unread_count(), 1)
        last_id = chat_service.get_messages(uid, mark_read=False)[0]["id"]
        new_only = chat_service.get_messages(uid, after_id=last_id)    # โพลเอาเฉพาะข้อความใหม่
        self.assertEqual([m["message"] for m in new_only], ["มีครับ"])
        self.assertEqual(chat_service.unread_count(), 0)
        self.assertEqual(chat_service.get_messages(uid, after_id=new_only[-1]["id"]), [])

    def test_chat_permissions_and_validation(self):
        uid = self.as_user("buyer1")
        other = self.new_buyer("chat_other")
        with self.assertRaises(PermissionError):
            chat_service.send_message(uid, "แอบส่ง")
        with self.assertRaises(PermissionError):
            chat_service.get_messages(uid)
        self.as_user("buyer1")
        for bad in ("", "   ", "ก" * (chat_service.MAX_MESSAGE_CHARS + 1)):
            with self.assertRaises(ValueError):
                chat_service.send_message(uid, bad)
        with self.assertRaises(PermissionError):
            chat_service.staff_reply(uid, "ผู้ซื้อตอบเป็นแอดมินไม่ได้")
        with self.assertRaises(PermissionError):
            chat_service.list_threads()
        self.as_user("admin1")
        with self.assertRaisesRegex(ValueError, "ไม่พบลูกค้า"):
            chat_service.staff_reply(99999, "สวัสดี")
        with self.assertRaisesRegex(ValueError, "ไม่พบลูกค้า"):
            chat_service.staff_reply(repo_users.get_by_username("owner")["id"], "สวัสดี")   # ไม่ใช่ผู้ซื้อ
        with self.assertRaisesRegex(ValueError, "พิมพ์ข้อความ"):
            chat_service.staff_reply(other, " ")


if __name__ == "__main__":
    unittest.main()


# ===========================================================================
# ชุดทดสอบฟีเจอร์ใหม่ทั้งหมด (v2 Specification Upgrade)
# ===========================================================================
from core.constants import (  # noqa: E402
    DISCOUNT_PERCENT,
    MAX_COMPARE,
    MIN_COMPARE,
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_DISPLAY_ORDER,
    ORDER_TAB_AWAITING_REVIEW,
    ROLE_ADMIN,
    ROLE_BUYER,
)
from services import (  # noqa: E402
    ai_guard,
    audit_service,
    banner_service,
    contact_service,
    coupon_service,
    expense_service,
    export_service,
    product_service,
    staff_service,
)
import sys as _sys  # noqa: E402
_LEGACY_DIR = Path(__file__).resolve().parent.parent / "legacy_desktop"
if _LEGACY_DIR.is_dir() and str(_LEGACY_DIR) not in _sys.path:
    _sys.path.insert(0, str(_LEGACY_DIR))
try:
    import customtkinter  # noqa: F401
except ModuleNotFoundError:
    import types as _types
    _ctk = _types.ModuleType("customtkinter")
    class _DummyWidget:
        def __init__(self, *a, **kw):
            self._val = ""
            self.children = {}
        def pack(self, *a, **kw): pass
        def grid(self, *a, **kw): pass
        def place(self, *a, **kw): pass
        def pack_forget(self, *a, **kw): pass
        def grid_forget(self, *a, **kw): pass
        def place_forget(self, *a, **kw): pass
        def destroy(self, *a, **kw): pass
        def configure(self, *a, **kw): pass
        config = configure
        def cget(self, key=None): return 'normal'
        def bind(self, *a, **kw): pass
        def after(self, *a, **kw): return "after_id"
        def after_cancel(self, *a, **kw): pass
        def winfo_children(self): return []
        def winfo_exists(self): return True
        def winfo_toplevel(self): return self
        def focus_set(self): pass
        def grab_set(self): pass
        def title(self, *a): pass
        def geometry(self, *a): pass
        def minsize(self, *a): pass
        def resizable(self, *a): pass
        def protocol(self, *a): pass
        def grid_columnconfigure(self, *a, **kw): pass
        def grid_rowconfigure(self, *a, **kw): pass
        def insert(self, idx, text):
            self._val = str(text)
        def delete(self, start, end=None):
            self._val = ""
        def get(self):
            return self._val
        def set(self, v):
            self._val = str(v)
    for _cls_name in (
        "CTk", "CTkToplevel", "CTkFrame", "CTkScrollableFrame", "CTkLabel",
        "CTkButton", "CTkEntry", "CTkTextbox", "CTkOptionMenu", "CTkComboBox",
        "CTkCheckBox", "CTkRadioButton", "CTkSwitch", "CTkSlider", "CTkProgressBar",
        "CTkSegmentedButton", "CTkTabview", "CTkCanvas", "CTkScrollbar",
    ):
        setattr(_ctk, _cls_name, type(_cls_name, (_DummyWidget,), {}))
    class _DummyVar:
        def __init__(self, value="", *a, **kw): self._v = value
        def get(self): return self._v
        def set(self, v): self._v = v
    _ctk.StringVar = _DummyVar
    _ctk.IntVar = _DummyVar
    _ctk.BooleanVar = _DummyVar
    _ctk.DoubleVar = _DummyVar
    _ctk.CTkFont = lambda *a, **kw: None
    _ctk.CTkImage = lambda *a, **kw: None
    _ctk.set_appearance_mode = lambda *a, **kw: None
    _ctk.set_default_color_theme = lambda *a, **kw: None
    _ctk.get_appearance_mode = lambda: "Light"
    _ctk.Canvas = _DummyWidget
    _ctk.Frame = _DummyWidget
    _ctk.Toplevel = _DummyWidget
    _ctk.Tk = _DummyWidget
    _ctk.END = 'end'
    _ctk.BOTH = 'both'
    _ctk.LEFT = 'left'
    _ctk.RIGHT = 'right'
    _ctk.TOP = 'top'
    _ctk.BOTTOM = 'bottom'
    _ctk.X = 'x'
    _ctk.Y = 'y'
    _sys.modules["customtkinter"] = _ctk
    _ctk.filedialog = _types.SimpleNamespace(askopenfilename=lambda **k: "", asksaveasfilename=lambda **k: "", askdirectory=lambda **k: "")
    _sys.modules.setdefault("tkinter", _ctk)
    _sys.modules.setdefault("tkinter.filedialog", _ctk.filedialog)
from ui.router import ROUTE_TABLE, Router  # noqa: E402
from ui.theme import COLORS, ON_PRIMARY  # noqa: E402


def _rel_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    vals = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def _contrast_ratio(hex1: str, hex2: str) -> float:
    l1, l2 = _rel_luminance(hex1), _rel_luminance(hex2)
    bright, dark = max(l1, l2), min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)


class TestV2NewFeatures(FlowTestCase):
    def test_otp_registration_with_initial_address_and_password_reset(self):
        import re as _re
        from unittest.mock import patch as _patch
        with _patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as mock_mail:
            res = auth_service.start_registration_with_otp(
                username="newbuyer99",
                email="newbuyer99@example.com",
                password="Password123",
                full_name="ลูกค้า ทดสอบ",
                phone="0891234567",
                address_line="88/9 ถ.สุขุมวิท",
                district="คลองเตย",
                province="กรุงเทพมหานคร",
                postcode="10110",
            )
            self.assertTrue(res["otp_required"])
            self.assertEqual(mock_mail.call_count, 1)
            sent_text = mock_mail.call_args.args[2] if len(mock_mail.call_args.args) >= 3 else mock_mail.call_args.kwargs.get("text", "")
            m_otp = _re.search(r"\b(\d{6})\b", sent_text)
            otp_code = m_otp.group(1) if m_otp else ""
            self.assertTrue(otp_code and len(otp_code) == 6)

            bad_try = "111111" if otp_code != "111111" else "222222"
            with self.assertRaises(ValueError):
                auth_service.complete_registration_with_otp("newbuyer99@example.com", bad_try)

            user = auth_service.complete_registration_with_otp("newbuyer99@example.com", otp_code)
            self.assertEqual(user["username"], "newbuyer99")
            self.assertEqual(user["role"], ROLE_BUYER)

            Session.login(user)
            addrs = account_service.list_addresses(user["id"])
            self.assertEqual(len(addrs), 1)
            self.assertEqual(addrs[0]["postcode"], "10110")

            Session.logout()
            reset_req = auth_service.request_password_reset_otp("newbuyer99@example.com")
            self.assertIn("masked_email", reset_req)
            reset_text = mock_mail.call_args.args[2] if len(mock_mail.call_args.args) >= 3 else mock_mail.call_args.kwargs.get("text", "")
            m_reset = _re.search(r"\b(\d{6})\b", reset_text)
            reset_otp = m_reset.group(1) if m_reset else ""
            self.assertTrue(reset_otp and len(reset_otp) == 6)
            auth_service.reset_password_with_otp("newbuyer99@example.com", reset_otp, "NewPass999")
            logged_in = auth_service.login("newbuyer99@example.com", "NewPass999")
            self.assertEqual(logged_in["id"], user["id"])

    def test_guest_mode_and_idle_lock_and_assign_admin(self):
        Session.enter_guest()
        self.assertTrue(Session.is_guest())
        self.assertFalse(Session.is_authenticated())

        self.as_user("owner")
        buyer = repo_users.get_by_username("buyer1")
        promoted = staff_service.assign_admin_by_email(
            buyer["email"], "AdminPass123", "AdminPass123"
        )
        self.assertEqual(promoted["role"], ROLE_ADMIN)

        staff_service.reset_user_password(promoted["id"], "AdminPass456", "AdminPass456")
        revoked = staff_service.revoke_sessions(promoted["id"])
        self.assertIsNotNone(revoked)

        Session.lock()
        self.assertTrue(Session.is_locked)
        ok, _ = auth_service.verify_active_session_password("owner123")
        self.assertTrue(ok)
        self.assertFalse(Session.is_locked)

    def test_soft_delete_restore_and_category_brand_binding(self):
        self.as_user("owner")
        brands = product_service.list_brands()
        b_ids = [brands[0]["id"], brands[1]["id"]]

        cat = product_service.save_category(
            "กระเป๋าทดสอบ", bind_all_brands=False, brand_ids=b_ids
        )
        self.assertEqual(cat["bind_all_brands"], 0)
        filtered_brands = product_service.list_brands(category_id=cat["id"])
        self.assertEqual(len(filtered_brands), 2)

        prods = product_service.list_products_admin()["items"]
        target_pid = prods[0]["id"]
        product_service.soft_delete_product(target_pid)

        deleted_list = product_service.list_deleted_products()
        self.assertTrue(any(p["id"] == target_pid for p in deleted_list))
        for p in deleted_list:
            if p["id"] == target_pid:
                self.assertIn("total_sold_qty", p)
                self.assertIn("total_sold_revenue", p)

        restored = product_service.restore_product(target_pid, activate=True)
        self.assertIsNone(restored.get("deleted_at"))
        self.assertEqual(restored.get("is_active"), 1)

        product_service.delete_category(cat["id"], force_deactivate_products=True)
        product_service.restore_category(cat["id"])

    def test_coupon_claim_and_reward_rules(self):
        self.as_user("owner")
        rule = coupon_service.save_coupon_rule({
            "name": "ซื้อครบ 2,000 รับส่วนลด 15%",
            "min_order_trigger": 2000,
            "discount_type": DISCOUNT_PERCENT,
            "discount_value": 15,
            "min_order_next": 500,
            "valid_days": 30,
            "code_prefix": "VIP15",
            "is_active": True,
        })
        self.assertEqual(rule["code_prefix"], "VIP15")

        uid = self.as_user("buyer1")
        pub = coupon_service.list_public_coupons(uid)
        self.assertTrue(len(pub) > 0)
        claim_res = coupon_service.claim_coupon(pub[0]["code"], uid)
        self.assertTrue(claim_res["claimed"])

        issued = coupon_service.evaluate_and_issue_reward_coupons(uid, 3500)
        self.assertTrue(len(issued) > 0)

    def test_8_order_status_tabs_and_5_racket_compare(self):
        labels = [item[1] for item in ORDER_STATUS_DISPLAY_ORDER]
        self.assertEqual(
            labels,
            [
                "การสั่งซื้อ",
                "รอชำระเงิน",
                "ชำระเงินแล้ว",
                "รอตรวจสลิป",
                "จัดส่งแล้ว",
                "สำเร็จ",
                "รอรีวิว",
                "สินค้าที่คุณยกเลิก",
            ],
        )
        self.assertEqual(MIN_COMPARE, 2)
        self.assertEqual(MAX_COMPARE, 5)

        uid = self.as_user("buyer1")
        counts = order_service.count_my_orders_by_tab(uid)
        self.assertIn(ORDER_TAB_AWAITING_REVIEW, counts)
        self.assertIn(ORDER_STATUS_CANCELLED, counts)
        self.assertIn(ORDER_STATUS_COMPLETED, counts)

        rackets = product_service.search_products(
            filters={"weight_class": ["3U", "4U", "5U"]}, page_size=10
        )["items"]
        self.assertGreaterEqual(len(rackets), 5)
        compared_5 = product_service.compare_products([r["id"] for r in rackets[:5]])
        self.assertEqual(len(compared_5), 5)

    def test_owner_xlsx_export_and_expenses(self):
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            export_service.export_report_xlsx("2026-01-01", "2026-12-31")

        self.as_user("owner")
        exp = expense_service.add_expense("ค่าเช่าร้านประจำเดือน", 12000, "ค่าเช่า", "2026-10-01")
        self.assertEqual(float(exp["amount"]), 12000.0)

        out_file = _TMP / "yearly_report.xlsx"
        res = export_service.export_report_xlsx("2026-01-01", "2026-12-31", out_file)
        self.assertTrue(Path(res["path"]).is_file())
        self.assertIn("gross_revenue", res)
        self.assertIn("net_profit", res)

        with self.assertRaises(ValueError):
            export_service.export_report_xlsx("2025-01-01", "2026-12-31", out_file)

    def test_ai_scope_guard_and_chat_features(self):
        allowed, msg = ai_guard.check_scope("วันนี้อากาศเป็นอย่างไร ฝนตกไหม")
        self.assertFalse(allowed)
        self.assertIn("แบดมินตัน", msg)

        allowed2, _ = ai_guard.check_scope("แนะนำไม้แบดมินตัน 4U หัวหนักหน่อยครับ")
        self.assertTrue(allowed2)

        uid = self.as_user("buyer1")
        qrs = chat_service.get_quick_replies()
        self.assertGreaterEqual(len(qrs), 3)

        chat_res = chat_service.send_message(uid, "วันนี้อากาศเป็นอย่างไร", force_ai=True)
        self.assertIsNotNone(chat_res.get("ai_message"))
        self.assertIn("แบดมินตัน", chat_res["ai_message"]["message"])

        rec_res = chat_service.send_racket_recommendation(
            uid, weight_class="4U", level="Beginner", budget=4000
        )
        self.assertIn("ai_message", rec_res)
        self.assertIn("แนะนำ", rec_res["ai_message"]["message"])

    def test_contact_urgent_email_banners_and_audit(self):
        self.as_user("admin1")
        info = contact_service.get_owner_contact_info()
        self.assertIn("phone", info)
        sent = contact_service.send_urgent_email_to_owner("แจ้งสลิปด่วน", "ลูกค้าโอนยอด 4,500 บาท รอตรวจสอบ")
        self.assertIn("status", sent)

        self.as_user("owner")
        updated = contact_service.update_owner_contact_info({
            "owner_phone": "0819998888",
            "owner_email": "owner@badmintonpro.th",
            "facebook_name": "Badminton Pro TH",
            "facebook_url": "https://www.facebook.com/badmintonpro",
            "line_id": "@badmintonpro",
            "instagram_name": "@badmintonpro.th",
            "instagram_url": "https://www.instagram.com/badmintonpro.th",
        })
        self.assertEqual(updated["phone"], "0819998888")

        banners = banner_service.list_active_banners()
        self.assertGreaterEqual(len(banners), 7)

        logs = audit_service.list_logs(limit=20)
        self.assertTrue(len(logs) > 0)

    def test_theme_contrast_and_router_and_no_web_dependencies(self):
        self.assertGreaterEqual(_contrast_ratio(COLORS["primary"]["light"], ON_PRIMARY), 7.0)
        self.assertGreaterEqual(_contrast_ratio(COLORS["surface"]["light"], COLORS["text_main"]["light"]), 12.0)
        self.assertGreaterEqual(_contrast_ratio(COLORS["surface"]["dark"], COLORS["text_main"]["dark"]), 10.0)
        self.assertGreaterEqual(_contrast_ratio(COLORS["surface"]["light"], COLORS["text_muted"]["light"]), 4.5)
        self.assertGreaterEqual(_contrast_ratio(COLORS["surface"]["dark"], COLORS["text_muted"]["dark"]), 4.5)
        self.assertGreaterEqual(_contrast_ratio(COLORS["secondary"]["light"], "#FFFFFF"), 14.0)

        import customtkinter as ctk
        root = ctk.CTk()
        router = Router(root)
        self.assertEqual(len(ROUTE_TABLE), 30)
        for route_name in ROUTE_TABLE:
            cls = router._resolve_page_class(route_name)
            self.assertIsNotNone(cls)

        req_text = (Path(__file__).resolve().parent.parent / "requirements.txt").read_text(encoding="utf-8").lower()
        for forbidden in ("flask", "django", "nicegui", "jinja2", "tornado"):
            self.assertNotIn(forbidden, req_text)

    def test_ui_update_and_owner_features(self):
        from services import notification_service, settings_service, staff_service
        # 1. Owner store settings (logo + physical store address)
        self.as_user("owner")
        updated_shop = settings_service.update_many({
            "shop_name": "Badminton Pro Arena",
            "shop_address": "99/9 ถนนพระราม 1 แขวงวังใหม่ เขตปทุมวัน กรุงเทพฯ 10330",
            "shop_logo_path": "assets/images/logo_test.png",
        })
        self.assertEqual(updated_shop["shop_name"], "Badminton Pro Arena")
        self.assertIn("ปทุมวัน", updated_shop["shop_address"])
        self.assertEqual(updated_shop["shop_logo_path"], "assets/images/logo_test.png")

        # 2. Owner can view full detail of buyer and admin without password_hash leak
        buyer_detail = staff_service.get_user_full_detail(repo_users.get_by_username("buyer1")["id"])
        self.assertEqual(buyer_detail["user"]["username"], "buyer1")
        self.assertNotIn("password_hash", buyer_detail["user"])
        admin_detail = staff_service.get_user_full_detail(repo_users.get_by_username("admin1")["id"])
        self.assertEqual(admin_detail["user"]["username"], "admin1")
        self.assertNotIn("password_hash", admin_detail["user"])

        # 3. Owner creates Free Shipping coupon + daily_reset_12 coupon + deletes a temp coupon
        temp_cp = coupon_service.create_coupon("TMPDEL99", "fixed", 50, min_order=0)
        self.assertTrue(coupon_service.delete_coupon(temp_cp["id"]))

        free_ship_cp = coupon_service.create_coupon(
            "FREESHIP0", "free_shipping", 0, min_order=100,
            is_free_shipping=True, daily_reset_12=True, repeat_daily=True,
            claim_start_time="00:00", claim_end_time="23:59",
        )
        self.assertTrue(free_ship_cp["is_free_shipping"])

        # 4. Buyer partial cart selection & checkout with Free Shipping coupon + VAT 7%
        b1 = self.as_user("buyer1")
        cart_service.clear_cart(b1)
        # Product 2 (shoes, option) & Product 6 (shuttlecock, no option)
        opts_p2 = repo_products.list_options(2)
        cart_after_1 = cart_service.add_to_cart(b1, 2, option_id=opts_p2[0]["id"], qty=1)
        cart_after_2 = cart_service.add_to_cart(b1, 6, option_id=None, qty=1)
        item_p6 = cart_after_2
        # Unselect second item (product 6)
        cart_sel = cart_service.set_item_selected(b1, item_p6["cart_item_id"], False)
        self.assertEqual(cart_sel["selected_item_count"], 1)
        self.assertEqual(len(cart_sel["items"]), 2)

        # Claim and apply FREESHIP0
        coupon_service.claim_coupon(b1, free_ship_cp["id"])
        checkout_list = coupon_service.list_checkout_coupons(
            b1, subtotal=cart_sel["subtotal"], shipping_fee=60.0
        )
        fs_entry = next(x for x in checkout_list if x["code"] == "FREESHIP0")
        self.assertTrue(fs_entry["can_use"])

        addrs = account_service.list_addresses(b1)
        order = order_service.checkout(
            b1, addrs[0]["id"], shipping_coupon_code="FREESHIP0"
        )
        self.assertEqual(order["shipping_fee"], 0.0)
        self.assertAlmostEqual(order["vat_amount"], round(order["total"] * 7.0 / 107.0, 2), places=2)

        # Unselected item (product 6) must still be in cart!
        remaining = cart_service.get_cart(b1)
        self.assertEqual(len(remaining["items"]), 1)
        self.assertEqual(remaining["items"][0]["product_id"], 6)

        # Coupon FREESHIP0 is now marked used; buyer can re-claim after use or after 12:00 reset
        reclaimed = coupon_service.claim_coupon(b1, free_ship_cp["id"])
        self.assertEqual(reclaimed["code"], "FREESHIP0")

        # 5. Buyer notifications capped at 10 most recent + target route resolution
        for idx in range(14):
            notification_service.notify(b1, f"แจ้งเตือนทดสอบ #{idx}", f"กรุณาชำระเงินสำหรับออเดอร์ #{order['id']}")
        my_notis = notification_service.list_my()
        self.assertLessEqual(len(my_notis), 10)
        self.assertEqual(my_notis[0]["target_route"], "payment")
        self.assertEqual(my_notis[0]["target_params"].get("order_id"), order["id"])


class TestT01ToT15Features(FlowTestCase):
    """Tests for T01-T15 feature updates (Fonts, Category Option Groups, Tech Specs, Multi-Images,
    Coupon Categories, Email Change OTP, Date Picker, Product Card 3:4, and Owner Settings)."""

    def test_t01_kanit_and_arimo_fonts_present_and_loaded(self):
        from utils.font_installer import get_project_font_status
        from ui.theme import FONT_FAMILY, FONT_FAMILY_LATIN, FONT_FAMILY_THAI, get_font, get_latin_font, get_thai_font

        self.assertEqual(FONT_FAMILY_LATIN, "Arimo")
        self.assertEqual(FONT_FAMILY_THAI, "Kanit")
        self.assertEqual(FONT_FAMILY, "Kanit")
        status = get_project_font_status()
        self.assertTrue(status["arimo_ready"])
        self.assertTrue(status["kanit_ready"])
        self.assertGreaterEqual(len(status["kanit_files"]), 9)
        self.assertEqual(get_font("body_bold")[0], "Kanit")
        self.assertEqual(get_font("body_bold", text="YONEX 100")[0], "Arimo")
        self.assertEqual(get_latin_font("body_bold", 14)[0], "Arimo")
        self.assertEqual(get_thai_font("body", 14)[0], "Kanit")

        thai_font_path = receipt_service.find_thai_font()
        self.assertIsNotNone(thai_font_path)
        self.assertIn("Kanit", Path(thai_font_path["regular"]).name)

    def test_t02_category_option_groups_and_3u_to_10u_weights(self):
        # Buyer/Admin cannot modify category option groups
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            product_service.save_category_option_group(1, "weight_class", "น้ำหนัก (U)")

        self.as_user("owner")
        racket_cat = next(c for c in product_service.list_categories() if "ไม้" in c["name"])
        product_service.quick_add_racket_weights(racket_cat["id"])
        groups = product_service.list_category_option_groups(racket_cat["id"], include_inactive=True)
        self.assertGreaterEqual(len(groups), 4)
        w_group = next(g for g in groups if g["key"] == "weight_class")
        w_vals = [v["value"] for v in w_group["values"]]
        for w in ("3U", "4U", "5U", "6U", "7U", "8U", "9U", "10U"):
            self.assertIn(w, w_vals)

        # Create custom group, add value, toggle active, reorder
        custom_grp = product_service.save_category_option_group(
            racket_cat["id"], "custom_grip_color", "สีพันด้ามแถม", sort_order=99
        )
        self.assertEqual(custom_grp["label"], "สีพันด้ามแถม")
        v1 = product_service.save_category_option_value(custom_grp["id"], "เหลืองนีออน", sort_order=1)
        v2 = product_service.save_category_option_value(custom_grp["id"], "ชมพูพาสเทล", sort_order=2)
        reordered = product_service.reorder_category_option_values(custom_grp["id"], [v2["id"], v1["id"]])
        self.assertEqual([v["value"] for v in reordered], ["ชมพูพาสเทล", "เหลืองนีออน"])
        toggled_val = product_service.toggle_category_option_value(v1["id"], False)
        self.assertEqual(toggled_val["is_active"], 0)
        toggled_grp = product_service.toggle_category_option_group(custom_grp["id"], False)
        self.assertEqual(toggled_grp["is_active"], 0)

    def test_t03_technical_specifications_and_balance_mm_validator(self):
        from utils.validators import (
            format_balance_point_display,
            is_valid_balance_point_mm,
            normalize_balance_point_mm,
        )

        self.assertTrue(is_valid_balance_point_mm("295"))
        self.assertTrue(is_valid_balance_point_mm("305±3 mm"))
        self.assertFalse(is_valid_balance_point_mm("99"))
        self.assertFalse(is_valid_balance_point_mm("abc"))
        self.assertEqual(normalize_balance_point_mm("300mm"), "300 mm")
        self.assertEqual(format_balance_point_display("305", "Head Heavy"), "305 mm (Head Heavy)")

        self.as_user("buyer1")
        pid = self.pid("Astrox 99 Pro")
        detail = product_service.get_product_detail(pid)
        self.as_user("owner")
        spec_labels = [row["label"] for row in detail["technical_specs"]]
        self.assertIn("Material", spec_labels)
        self.assertIn("Weight Class / Grip", spec_labels)
        self.assertIn("Balance Point", spec_labels)
        self.assertIn("Shaft Flexibility", spec_labels)
        self.assertIn("Max String Tension", spec_labels)
        self.assertIn("Skill Level", spec_labels)
        self.assertIn("Length", spec_labels)

        # Updating product with invalid balance_mm raises ValueError
        with self.assertRaisesRegex(ValueError, "Balance Point"):
            product_service.save_product(
                {
                    "category_id": detail["category_id"],
                    "brand_id": detail["brand_id"],
                    "name": detail["name"],
                    "price": detail["price"],
                    "spec_balance_mm": "999",
                },
                product_id=pid,
            )

    def test_t04_multi_image_gallery_and_color_binding(self):
        self.as_user("owner")
        pid = self.pid("Nanoflare 800")
        img1 = self.slip("racket_red.png")
        img2 = self.slip("racket_blue.png")

        detail1 = product_service.add_product_image(
            pid, img1, color_value="แดงเมทัลลิก", is_primary=True
        )
        detail2 = product_service.add_product_image(
            pid, img2, color_value="น้ำเงินเข้ม", is_primary=False
        )
        self.assertGreaterEqual(len(detail2["images"]), 2)
        self.assertIn("แดงเมทัลลิก", detail2["color_image_map"])
        self.assertIn("น้ำเงินเข้ม", detail2["color_image_map"])

        # Set second image as primary
        second_img_id = detail2["images"][-1]["id"]
        after_primary = product_service.set_primary_product_image(second_img_id)
        primary_imgs = [im for im in after_primary["images"] if im["is_primary"]]
        self.assertEqual(len(primary_imgs), 1)
        self.assertEqual(primary_imgs[0]["id"], second_img_id)

        # Delete image
        after_del = product_service.delete_product_image(second_img_id)
        self.assertTrue(all(im["id"] != second_img_id for im in after_del["images"]))

    def test_t06_coupon_categories_and_shop_coupons_listing(self):
        self.as_user("owner")
        cats = coupon_service.get_coupon_categories()
        cat_keys = [k for k, _ in cats]
        self.assertIn("free_shipping", cat_keys)
        self.assertIn("percent", cat_keys)
        self.assertIn("fixed", cat_keys)
        self.assertIn("other", cat_keys)

        cp = coupon_service.create_coupon(
            "CAMP500",
            "fixed",
            100,
            min_order=500,
            coupon_category="other",
        )
        self.assertEqual(cp["coupon_category"], "other")

        uid = self.as_user("buyer1")
        all_shop = coupon_service.list_all_shop_coupons(uid)
        self.assertTrue(any(c["code"] == "CAMP500" for c in all_shop))
        other_only = coupon_service.list_all_shop_coupons(uid, category="other")
        self.assertTrue(all(c["coupon_category"] == "other" for c in other_only))

        coupon_service.claim_coupon(uid, cp["id"])
        my_other = coupon_service.list_my_coupons(uid, category="other")
        self.assertTrue(any(c["code"] == "CAMP500" for c in my_other))

    def test_t09_login_showcase_and_t15_owner_settings(self):
        from services import settings_service
        showcase = product_service.get_login_showcase(limit=5)
        self.assertGreaterEqual(len(showcase), 1)
        self.assertIn("effective_price", showcase[0])

        self.as_user("owner")
        info = settings_service.update_many({
            "flash_sale_scroll_speed": "3",
            "coupon_rotate_seconds": "6",
            "home_coupons_per_view": "3",
            "login_showcase_seconds": "5",
            "custom_coupon_categories": "คูปอง VIP,คูปองเทศกาล",
            "custom_option_types": "ความตึงเอ็น,สีปลอกไม้",
        })
        self.assertEqual(info["flash_sale_scroll_speed"], 3)
        self.assertEqual(info["coupon_rotate_seconds"], 6)
        self.assertEqual(info["home_coupons_per_view"], 3)
        self.assertEqual(info["login_showcase_seconds"], 5)
        self.assertIn("คูปอง VIP", [k for k, _ in coupon_service.get_coupon_categories()])

    def test_t11_profile_username_edit_and_email_change_otp(self):
        import re as _re
        from unittest.mock import patch as _patch
        uid = self.as_user("buyer1")
        updated = account_service.update_profile(
            uid, "สมชาย นักแบด", "0891112222", username="buyer1_pro"
        )
        self.assertEqual(updated["username"], "buyer1_pro")
        self.assertEqual(Session.current_user["username"], "buyer1_pro")

        # Request email change OTP
        with _patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as mock_mail:
            req = account_service.request_email_change_otp(uid, "buyer1_new@example.com")
            self.assertIn("masked_email", req)
            sent_text = mock_mail.call_args.args[2] if len(mock_mail.call_args.args) >= 3 else mock_mail.call_args.kwargs.get("text", "")
            m_otp = _re.search(r"\b(\d{6})\b", sent_text)
            otp_code = m_otp.group(1) if m_otp else ""
            self.assertTrue(otp_code and len(otp_code) == 6)

            bad_try = "111111" if otp_code != "111111" else "222222"
            with self.assertRaisesRegex(ValueError, "OTP"):
                account_service.confirm_email_change_with_otp(uid, "buyer1_new@example.com", bad_try)

            confirmed = account_service.confirm_email_change_with_otp(uid, "buyer1_new@example.com", otp_code)
            self.assertEqual(confirmed["email"], "buyer1_new@example.com")
            self.assertEqual(Session.current_user["email"], "buyer1_new@example.com")

    def test_t07_t08_ui_components_date_picker_and_product_card_dimensions(self):
        import customtkinter as ctk
        from ui.components.date_picker import DatePickerField, DateTimePickerField
        from ui.components.product_card import CARD_HEIGHT, CARD_WIDTH, IMAGE_SIZE
        from utils.validators import is_valid_date_range

        # 3:4 card ratio and 1:1 square image
        self.assertEqual(CARD_WIDTH * 4, CARD_HEIGHT * 3)
        self.assertEqual(IMAGE_SIZE[0], IMAGE_SIZE[1])

        self.assertTrue(is_valid_date_range("2026-01-01", "2026-12-31"))
        self.assertFalse(is_valid_date_range("2026-12-31", "2026-01-01"))

        root = ctk.CTk()
        dp = DatePickerField(root)
        dp.insert(0, "2026-10-16")
        self.assertEqual(dp.get(), "2026-10-16")
        dp.delete(0, "end")
        self.assertEqual(dp.get(), "")

        dtp = DateTimePickerField(root)
        dtp.set_value("2026-10-16 18:30")
        self.assertEqual(dtp.get(), "2026-10-16 18:30")
