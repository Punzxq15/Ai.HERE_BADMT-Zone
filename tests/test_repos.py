"""
tests/test_repos.py
ทดสอบ repository (ส่วน B) กับข้อมูล seed บนฐานข้อมูลชั่วคราว (ไม่แตะ data/shop.db จริง)
รันจาก root โปรเจกต์:  python -m unittest tests.test_repos -v
"""
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import database.db as db
from database import (
    repo_addresses, repo_cart, repo_chat, repo_coupons, repo_notifications, repo_orders,
    repo_payments, repo_products, repo_reviews, repo_settings, repo_shipping, repo_users,
    repo_wishlist,
)
from database.seed import run_seed

_TMP = None
_TEMPLATE = None
_REAL = (db.DB_PATH, db.DATA_DIR)


def setUpModule():
    """สร้างฐานข้อมูลต้นแบบที่ seed แล้วหนึ่งครั้ง (แต่ละเทสต์จะคัดลอกไปใช้ จึงไม่กระทบกัน)"""
    global _TMP, _TEMPLATE
    _TMP = Path(tempfile.mkdtemp(prefix="shop_test_"))
    _TEMPLATE = _TMP / "template.db"
    db.DATA_DIR, db.DB_PATH = _TMP, _TEMPLATE
    run_seed()
    db.DB_PATH, db.DATA_DIR = _REAL


def tearDownModule():
    db.DB_PATH, db.DATA_DIR = _REAL
    shutil.rmtree(_TMP, ignore_errors=True)


class RepoTestCase(unittest.TestCase):
    def setUp(self):
        self.path = _TMP / f"{self.id().split('.')[-1]}.db"
        shutil.copy(_TEMPLATE, self.path)
        db.DATA_DIR, db.DB_PATH = _TMP, self.path
        self.addCleanup(lambda: setattr(db, "DB_PATH", _REAL[0]))

    # ตัวช่วย
    def pid(self, name):
        with db.get_connection() as c:
            return c.execute("SELECT id FROM products WHERE name = ?", (name,)).fetchone()["id"]

    def uid(self, username):
        return repo_users.get_by_username(username)["id"]


class TestUsers(RepoTestCase):
    def test_original_functions(self):
        self.assertEqual(repo_users.get_by_username("buyer1")["email"], "buyer@shop.com")
        self.assertEqual(repo_users.get_by_email("owner@shop.com")["role"], "owner")
        self.assertIsNone(repo_users.get_by_id(9999))
        self.assertTrue(repo_users.username_exists("admin1"))
        self.assertFalse(repo_users.email_exists("none@x.com"))
        new_id = repo_users.create_user("u9", "u9@x.com", "hash", "คนที่เก้า", "0899999999")
        self.assertEqual(repo_users.get_by_id(new_id)["role"], "buyer")

    def test_list_update_active_online(self):
        users = repo_users.list_users()
        self.assertEqual(len(users), 3)
        self.assertNotIn("password_hash", users[0].keys())
        self.assertEqual([u["username"] for u in repo_users.list_users(role="admin")], ["admin1"])
        self.assertEqual(len(repo_users.list_users(search="shop.com")), 3)
        self.assertEqual(len(repo_users.list_users(search="100%")), 0)   # % ไม่เป็น wildcard

        buyer = self.uid("buyer1")
        repo_users.update_profile(buyer, "ชื่อใหม่", "0800000000")
        self.assertEqual(repo_users.get_by_id(buyer)["full_name"], "ชื่อใหม่")
        repo_users.update_profile(buyer, "ชื่อใหม่", "0800000000", "assets/a.png")
        repo_users.update_profile(buyer, "ชื่อใหม่", "0800000000", None)   # None = ไม่ล้างรูป
        self.assertEqual(repo_users.get_by_id(buyer)["avatar_path"], "assets/a.png")
        repo_users.update_password(buyer, "newhash")
        self.assertEqual(repo_users.get_by_id(buyer)["password_hash"], "newhash")

        admin = self.uid("admin1")
        self.assertEqual(repo_users.list_online_staff(), [])
        repo_users.set_online(admin, True)
        repo_users.set_online(buyer, True)          # ผู้ซื้อไม่นับเป็น staff
        self.assertEqual([u["username"] for u in repo_users.list_online_staff()], ["admin1"])
        repo_users.set_active(admin, False)         # ระงับแล้วไม่ออนไลน์
        self.assertEqual(repo_users.list_online_staff(), [])
        self.assertEqual(repo_users.clear_all_online(), 1)   # เหลือ buyer1 คนเดียว
        self.assertEqual(repo_users.get_by_id(buyer)["is_online"], 0)


class TestSettings(RepoTestCase):
    def test_get_set(self):
        self.assertEqual(repo_settings.get("shipping_fee"), "50")
        self.assertEqual(repo_settings.get("missing", "x"), "x")
        self.assertIsNone(repo_settings.get("missing"))
        repo_settings.set("shipping_fee", 70)
        self.assertEqual(repo_settings.get("shipping_fee"), "70")
        repo_settings.set("new_key", "v")
        self.assertEqual(repo_settings.get_all()["new_key"], "v")
        self.assertIn("low_stock_threshold", repo_settings.get_all())
        with db.get_connection() as c:                # เคสไม่มีแถวใน DB -> ใช้ค่าตั้งต้น
            c.execute("DELETE FROM settings WHERE key = 'free_shipping_min'")
            c.commit()
        self.assertEqual(repo_settings.get("free_shipping_min"), "0")


class TestProducts(RepoTestCase):
    def test_spec_filter_heavy_head_stiff(self):
        rows = repo_products.list_products({"balance": "Heavy Head", "flex": "Stiff"})
        self.assertEqual({r["name"] for r in rows}, {"Astrox 99 Pro", "Dragon P"})
        self.assertEqual(repo_products.count_products({"balance": "Heavy Head", "flex": "Stiff"}), 2)
        multi = repo_products.list_products({"flex": ["Stiff", "Flexible"], "weight_class": "4U"})
        self.assertIn("Tectonic 9", {r["name"] for r in multi})

    def test_effective_price_and_price_filter(self):
        by_name = {r["name"]: r for r in repo_products.list_products({"category_id": 1})}
        self.assertEqual(by_name["Astrox 99 Pro"]["effective_price"], 4800)    # Flash Sale ยังไม่หมด
        self.assertEqual(by_name["Z-Ziggler"]["effective_price"], 1200)        # โปรหมดแล้ว = ราคาเต็ม
        self.assertEqual(by_name["Nanoflare 800"]["effective_price"], 4500)    # ไม่มีโปร
        cheap = {r["name"] for r in repo_products.list_products({"max_price": 1300, "category_id": 1})}
        self.assertEqual(cheap, {"Axforce Cannon", "Z-Ziggler"})
        on_sale = {r["name"] for r in repo_products.list_products({"on_sale": True})}
        self.assertIn("Astrox 99 Pro", on_sale)
        self.assertNotIn("Z-Ziggler", on_sale)

    def test_search_sort_paging(self):
        self.assertEqual(len(repo_products.list_products({"search": "yonex"})) > 0, True)
        self.assertEqual([r["name"] for r in repo_products.list_products({"search": "Astrox"})],
                         ["Astrox 99 Pro"])
        asc = repo_products.list_products({"category_id": 1}, sort="price_asc")
        prices = [r["effective_price"] for r in asc]
        self.assertEqual(prices, sorted(prices))
        page1 = repo_products.list_products(limit=5, offset=0)
        page2 = repo_products.list_products(limit=5, offset=5)
        self.assertTrue(set(r["id"] for r in page1).isdisjoint(r["id"] for r in page2))
        self.assertEqual(repo_products.count_products(), 25)
        repo_products.list_products(sort="popular")   # ต้องไม่ error

    def test_get_and_by_ids_keep_order(self):
        a, b = self.pid("Dragon P"), self.pid("Astrox 99 Pro")
        got = repo_products.get_products_by_ids([a, 99999, b])
        self.assertEqual([r["id"] for r in got], [a, b])
        self.assertEqual(repo_products.get_product(a)["brand_name"], "Venson (VS)")
        self.assertIsNone(repo_products.get_product(99999))

    def test_create_update_active(self):
        new_id = repo_products.create_product(1, 1, "ไม้ทดสอบ", "d", 999, stock=3, level="Beginner")
        self.assertEqual(repo_products.get_product(new_id)["level"], "Beginner")
        self.assertTrue(repo_products.update_product(new_id, {"price": 1111, "sale_price": None}))
        self.assertEqual(repo_products.get_product(new_id)["price"], 1111)
        with self.assertRaises(ValueError):
            repo_products.update_product(new_id, {"id": 5})
        before = repo_products.count_products()
        repo_products.set_product_active(new_id, False)
        self.assertEqual(repo_products.count_products(), before - 1)
        self.assertEqual(repo_products.count_products({"active_only": False}), before)

    def test_stock_never_negative(self):
        pid = repo_products.create_product(1, 1, "สต็อกน้อย", "d", 100, stock=2)
        self.assertTrue(repo_products.adjust_stock(pid, -2))
        self.assertFalse(repo_products.adjust_stock(pid, -1))          # ติดลบไม่ได้
        self.assertEqual(repo_products.get_product(pid)["stock"], 0)
        self.assertTrue(repo_products.adjust_stock(pid, 5))
        self.assertEqual(repo_products.get_product(pid)["stock"], 5)

    def test_options_and_low_stock(self):
        tectonic = self.pid("Tectonic 9")
        opts = repo_products.list_options(tectonic)
        self.assertEqual(sorted(o["stock"] for o in opts), [0, 3])
        self.assertEqual(repo_products.get_product(tectonic)["stock"], 3)   # = ผลรวมตัวเลือก
        self.assertIn("Tectonic 9", {r["name"] for r in repo_products.list_low_stock(5)})
        self.assertTrue(any(o["product_name"] == "Tectonic 9" for o in repo_products.list_low_stock_options(5)))
        out = next(o for o in opts if o["stock"] == 0)
        self.assertTrue(repo_products.adjust_option_stock(out["id"], 4))
        self.assertEqual(repo_products.get_product(tectonic)["stock"], 7)   # sync อัตโนมัติ
        self.assertFalse(repo_products.adjust_option_stock(out["id"], -99))
        self.assertEqual(repo_products.get_product(tectonic)["stock"], 7)
        new_opt = repo_products.create_option(tectonic, "สี", "ทอง", 100, 10)
        self.assertEqual(repo_products.get_product(tectonic)["stock"], 17)
        repo_products.update_option(new_opt, "สี", "ทอง", 150, 1)
        self.assertEqual(repo_products.get_product(tectonic)["stock"], 8)
        self.assertTrue(repo_products.delete_option(new_opt))
        self.assertEqual(repo_products.get_product(tectonic)["stock"], 7)

    def test_option_used_by_order_cannot_delete(self):
        buyer = self.uid("buyer1")
        pid = self.pid("Tectonic 9")
        opt = repo_products.list_options(pid)[0]
        order_id = repo_orders.create_order(buyer, "a", "0800000000", "addr", 100, 0, 0, 100)
        repo_orders.add_items(order_id, [{"product_id": pid, "option_id": opt["id"],
                                          "product_name": "Tectonic 9", "price_at_purchase": 100, "qty": 1}])
        self.assertTrue(repo_products.is_option_used(opt["id"]))
        with self.assertRaises(sqlite3.IntegrityError):
            repo_products.delete_option(opt["id"])

    def test_categories_brands_addons_values(self):
        cats = repo_products.list_categories()
        self.assertEqual(len(cats), 6)
        cid = repo_products.create_category("หมวดใหม่")
        with self.assertRaises(sqlite3.IntegrityError):
            repo_products.create_category("หมวดใหม่")
        repo_products.set_category_active(cid, False)
        self.assertEqual(len(repo_products.list_categories()), 6)
        self.assertEqual(len(repo_products.list_categories(active_only=False)), 7)
        # หมวดที่ปิดแล้ว สินค้าในหมวดไม่โผล่ในการเลือกซื้อ
        pid = repo_products.create_product(cid, 1, "ในหมวดปิด", "d", 10, stock=1)
        self.assertNotIn(pid, [r["id"] for r in repo_products.list_products()])
        bid = repo_products.create_brand("แบรนด์ใหม่")
        repo_products.update_brand(bid, "แบรนด์ใหม่2")
        self.assertEqual(repo_products.get_brand(bid)["name"], "แบรนด์ใหม่2")
        self.assertEqual(len(repo_products.list_brands()), 7)

        astrox = self.pid("Astrox 99 Pro")
        addons = repo_products.list_addons(astrox)
        self.assertEqual(len(addons), 3)
        n = repo_products.set_addons(astrox, [astrox, self.pid("เอ็น BG80"), self.pid("เอ็น BG80")])
        self.assertEqual(n, 1)                                  # ข้ามตัวเอง + ซ้ำ
        self.assertEqual([a["name"] for a in repo_products.list_addons(astrox)], ["เอ็น BG80"])

        self.assertEqual(repo_products.list_distinct_values("balance"),
                         ["Even Balance", "Heavy Head", "Light Head"])
        with self.assertRaises(ValueError):
            repo_products.list_distinct_values("price; DROP TABLE products")


class TestCartWishlistAddresses(RepoTestCase):
    def test_cart_merge_and_options(self):
        u = self.uid("buyer1")
        tectonic = self.pid("Tectonic 9")
        opt = repo_products.list_options(tectonic)[0]["id"]
        plain = self.pid("เอ็น BG65")
        a = repo_cart.add_or_increase(u, tectonic, opt, 1)
        b = repo_cart.add_or_increase(u, tectonic, opt, 2)       # สินค้า+ตัวเลือกเดิม -> บวกจำนวน
        self.assertEqual(a, b)
        self.assertEqual(repo_cart.get_item(u, a)["qty"], 3)
        c1 = repo_cart.add_or_increase(u, plain, None, 1)         # ไม่มีตัวเลือก (NULL) ก็รวมกันได้
        c2 = repo_cart.add_or_increase(u, plain, None, 1)
        self.assertEqual(c1, c2)
        other = repo_products.list_options(tectonic)[1]["id"]
        d = repo_cart.add_or_increase(u, tectonic, other, 1)      # ตัวเลือกต่างกัน -> แถวใหม่
        self.assertNotEqual(a, d)
        items = repo_cart.list_items(u)
        self.assertEqual(len(items), 3)
        self.assertEqual(repo_cart.count(u), 3 + 2 + 1)
        row = next(i for i in items if i["cart_item_id"] == a)
        self.assertEqual(row["product_name"], "Tectonic 9")
        self.assertEqual(row["effective_price"], 5200)
        self.assertIsNotNone(row["option_value"])
        self.assertTrue(repo_cart.set_qty(u, a, 1))
        self.assertFalse(repo_cart.set_qty(self.uid("admin1"), a, 9))   # ของคนอื่นแก้ไม่ได้
        self.assertFalse(repo_cart.remove(self.uid("admin1"), a))
        self.assertTrue(repo_cart.remove(u, a))
        self.assertEqual(repo_cart.clear(u), 2)
        self.assertEqual(repo_cart.count(u), 0)

    def test_wishlist(self):
        u, p = self.uid("buyer1"), self.pid("Dragon P")
        self.assertTrue(repo_wishlist.add(u, p))
        self.assertFalse(repo_wishlist.add(u, p))                 # ซ้ำไม่ error
        self.assertTrue(repo_wishlist.is_in(u, p))
        self.assertEqual(repo_wishlist.ids(u), {p})
        self.assertEqual(repo_wishlist.list(u)[0]["name"], "Dragon P")
        repo_products.set_product_active(p, False)                # สินค้าปิดแล้วไม่โชว์
        self.assertEqual(repo_wishlist.list(u), [])
        self.assertTrue(repo_wishlist.remove(u, p))
        self.assertFalse(repo_wishlist.is_in(u, p))

    def test_addresses_single_default(self):
        u = self.uid("buyer1")
        rows = repo_addresses.list(u)
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r["is_default"] for r in rows), 1)
        self.assertEqual(repo_addresses.list(u)[0]["is_default"], 1)   # หลักขึ้นก่อน
        new_id = repo_addresses.create(u, "ก", "0811111111", "1/1", "เขต", "กรุงเทพ", "10100", is_default=True)
        self.assertEqual(sum(r["is_default"] for r in repo_addresses.list(u)), 1)
        self.assertEqual(repo_addresses.get_default(u)["id"], new_id)
        other = next(r["id"] for r in repo_addresses.list(u) if r["id"] != new_id)
        self.assertTrue(repo_addresses.set_default(u, other))
        self.assertEqual(sum(r["is_default"] for r in repo_addresses.list(u)), 1)
        self.assertEqual(repo_addresses.get_default(u)["id"], other)
        self.assertFalse(repo_addresses.set_default(self.uid("admin1"), other))   # ไม่ใช่ของเขา
        self.assertEqual(repo_addresses.get_default(u)["id"], other)
        repo_addresses.update(new_id, "ข", "0822222222", "2/2", "เขต2", "นนทบุรี", "11000")
        self.assertEqual(repo_addresses.get(new_id)["province"], "นนทบุรี")
        self.assertEqual(repo_addresses.count(u), 3)
        self.assertTrue(repo_addresses.delete(new_id))
        self.assertEqual(repo_addresses.count(u), 2)


class TestOrderFlow(RepoTestCase):
    def _make_order(self, qty=2, status_after=None):
        u = self.uid("buyer1")
        pid = self.pid("Dragon P")
        with db.transaction() as conn:
            oid = repo_orders.create_order(u, "ผู้รับ", "0833333333", "ที่อยู่", 3000, 100, 50, 2950, conn=conn)
            repo_orders.add_items(oid, [{"product_id": pid, "option_id": None, "product_name": "Dragon P",
                                         "option_label": None, "price_at_purchase": 1500, "qty": qty}], conn=conn)
            repo_orders.add_status_log(oid, "pending", "สร้างออเดอร์", u, conn=conn)
        if status_after:
            repo_orders.update_status(oid, status_after)
        return oid, u, pid

    def test_order_crud_and_log(self):
        oid, u, pid = self._make_order()
        order = repo_orders.get_order(oid)
        self.assertEqual((order["status"], order["total"], order["item_count"]), ("pending", 2950, 2))
        self.assertEqual(order["buyer_username"], "buyer1")
        self.assertEqual(repo_orders.list_items(oid)[0]["product_name"], "Dragon P")
        self.assertEqual(len(repo_orders.list_orders(user_id=u)), 1)
        self.assertEqual(len(repo_orders.list_orders(user_id=self.uid("admin1"))), 0)
        self.assertEqual(repo_orders.count_orders(status=["pending", "paid"]), 1)
        self.assertEqual(len(repo_orders.list_orders(search=str(oid))), 1)
        # expected_status กันกดซ้ำ
        self.assertFalse(repo_orders.update_status(oid, "paid", expected_status="checking_slip"))
        self.assertTrue(repo_orders.update_status(oid, "checking_slip", expected_status="pending"))
        repo_orders.add_status_log(oid, "checking_slip", None, u)
        self.assertEqual([l["status"] for l in repo_orders.list_status_log(oid)], ["pending", "checking_slip"])
        repo_orders.set_cancel_reason(oid, "เปลี่ยนใจ")
        self.assertEqual(repo_orders.get_order(oid)["cancel_reason"], "เปลี่ยนใจ")

    def test_transaction_rollback_leaves_nothing(self):
        u = self.uid("buyer1")
        with self.assertRaises(RuntimeError):
            with db.transaction() as conn:
                repo_orders.create_order(u, "x", "0800000000", "y", 1, 0, 0, 1, conn=conn)
                raise RuntimeError("พังกลางทาง")
        self.assertEqual(repo_orders.count_orders(), 0)

    def test_expired_pending(self):
        oid, _, _ = self._make_order()
        self.assertEqual(repo_orders.list_expired_pending(24), [])
        with db.get_connection() as c:
            c.execute("UPDATE orders SET created_at = datetime('now','localtime','-30 hours') WHERE id = ?", (oid,))
            c.commit()
        self.assertEqual([r["id"] for r in repo_orders.list_expired_pending(24)], [oid])
        self.assertEqual(repo_orders.list_expired_pending(48), [])

    def test_find_completed_order_and_reviews(self):
        oid, u, pid = self._make_order(status_after="paid")
        self.assertIsNone(repo_orders.find_completed_order_with_product(u, pid))   # ยังไม่ completed
        repo_orders.update_status(oid, "completed")
        found = repo_orders.find_completed_order_with_product(u, pid)
        self.assertEqual((found["id"], found["already_reviewed"]), (oid, 0))
        self.assertIsNone(repo_orders.find_completed_order_with_product(u, self.pid("Astrox 99 Pro")))

        self.assertFalse(repo_reviews.exists(u, pid, oid))
        repo_reviews.create(u, pid, oid, 5, "ดีมาก")
        self.assertTrue(repo_reviews.exists(u, pid, oid))
        with self.assertRaises(sqlite3.IntegrityError):
            repo_reviews.create(u, pid, oid, 4, "ซ้ำ")                  # หนึ่งครั้งต่อ (user, product, order)
        with self.assertRaises(sqlite3.IntegrityError):
            repo_reviews.create(u, pid, oid + 100, 6, "ดาวเกิน")
        self.assertEqual(repo_orders.find_completed_order_with_product(u, pid)["already_reviewed"], 1)
        self.assertEqual(repo_reviews.get_summary(pid), (5.0, 1))
        self.assertEqual(repo_reviews.get_summary(self.pid("Astrox 99 Pro")), (0.0, 0))
        sums = repo_reviews.get_summaries([pid, self.pid("Astrox 99 Pro")])
        self.assertEqual(sums[pid], (5.0, 1))
        self.assertEqual(sums[self.pid("Astrox 99 Pro")], (0.0, 0))
        self.assertEqual(repo_reviews.list_by_product(pid)[0]["reviewer_name"], "General Buyer")
        self.assertEqual(repo_reviews.count_by_product(pid), 1)

    def test_dashboard_stats(self):
        oid, u, pid = self._make_order(qty=2, status_after="paid")
        self._make_order(qty=1)                                       # pending ไม่นับรายได้
        self.assertEqual(repo_orders.sum_revenue(), 2950)
        self.assertEqual(repo_orders.sum_revenue("2000-01-01", "2000-01-02"), 0)
        counts = repo_orders.count_by_status()
        self.assertEqual((counts["paid"], counts["pending"], counts["cancelled"]), (1, 1, 0))
        top = repo_orders.top_products(3)
        self.assertEqual((top[0]["product_name"], top[0]["total_qty"], top[0]["total_sales"]),
                         ("Dragon P", 2, 3000))
        daily = repo_orders.daily_sales(7)
        self.assertEqual(len(daily), 1)
        self.assertEqual(daily[0]["revenue"], 2950)

    def test_payments_and_shipping(self):
        oid, u, _ = self._make_order(status_after="checking_slip")
        admin = self.uid("admin1")
        p1 = repo_payments.create(oid, "promptpay", 2950, "assets/slips/a.jpg")
        self.assertEqual(repo_payments.get(p1)["buyer_name"], "General Buyer")
        self.assertEqual(len(repo_payments.list_pending()), 1)
        self.assertTrue(repo_payments.mark_rejected(p1, "ยอดไม่ตรง", admin))
        self.assertFalse(repo_payments.mark_verified(p1, admin))        # ตัดสินแล้วไม่ซ้ำ
        self.assertEqual(repo_payments.get(p1)["reject_reason"], "ยอดไม่ตรง")
        p2 = repo_payments.create(oid, "promptpay", 2950, "assets/slips/b.jpg")
        self.assertEqual(repo_payments.get_latest_by_order(oid)["id"], p2)
        self.assertEqual(len(repo_payments.list_by_order(oid)), 2)
        self.assertTrue(repo_payments.mark_verified(p2, admin))
        self.assertEqual(repo_payments.get(p2)["status"], "verified")
        self.assertEqual(repo_payments.list_pending(), [])

        self.assertIsNone(repo_shipping.get_by_order(oid))
        self.assertFalse(repo_shipping.update(oid, "Kerry Express", "TH123"))   # ยังไม่มีแถว
        repo_shipping.create(oid)
        self.assertEqual(repo_shipping.get_by_order(oid)["status"], "preparing")
        self.assertTrue(repo_shipping.update(oid, "Kerry Express", "TH123", "shipped"))
        s = repo_shipping.get_by_order(oid)
        self.assertEqual((s["carrier"], s["tracking_no"], s["status"]), ("Kerry Express", "TH123", "shipped"))
        repo_shipping.update(oid, status="delivered")                   # None = ไม่เปลี่ยนค่าอื่น
        s = repo_shipping.get_by_order(oid)
        self.assertEqual((s["tracking_no"], s["status"]), ("TH123", "delivered"))


class TestCoupons(RepoTestCase):
    def test_lookup_usage_and_limits(self):
        c = repo_coupons.get_by_code(" welcome10 ")                     # ไม่สนตัวพิมพ์/ช่องว่าง
        self.assertEqual(c["code"], "WELCOME10")
        self.assertIsNone(repo_coupons.get_by_code("NOPE"))
        self.assertEqual(len(repo_coupons.list_all()), 3)
        u = self.uid("buyer1")
        oid = repo_orders.create_order(u, "a", "0800000000", "b", 1000, 100, 0, 900, coupon_id=c["id"])
        self.assertFalse(repo_coupons.has_used(u, c["id"]))
        repo_coupons.add_usage(c["id"], u, oid)
        self.assertTrue(repo_coupons.has_used(u, c["id"]))
        with self.assertRaises(sqlite3.IntegrityError):
            repo_coupons.add_usage(c["id"], u, oid)
        self.assertTrue(repo_coupons.increment_used(c["id"]))
        self.assertEqual(repo_coupons.get(c["id"])["used_count"], 1)
        # คืนสิทธิ์ตอนยกเลิก
        self.assertTrue(repo_coupons.remove_usage(oid))
        self.assertTrue(repo_coupons.decrement_used(c["id"]))
        self.assertTrue(repo_coupons.decrement_used(c["id"]))           # ไม่ต่ำกว่า 0
        self.assertEqual(repo_coupons.get(c["id"])["used_count"], 0)
        self.assertFalse(repo_coupons.has_used(u, c["id"]))

    def test_max_uses_atomic_and_admin_ops(self):
        cid = repo_coupons.create("LIMIT1", "fixed", 50, 0, max_uses=1)
        self.assertTrue(repo_coupons.increment_used(cid))
        self.assertFalse(repo_coupons.increment_used(cid))              # เต็มแล้ว
        with self.assertRaises(sqlite3.IntegrityError):
            repo_coupons.create("LIMIT1", "fixed", 50)
        with self.assertRaises(sqlite3.IntegrityError):
            repo_coupons.create("BAD", "weird", 50)                     # CHECK discount_type
        repo_coupons.update(cid, {"value": 80, "max_uses": None})
        self.assertEqual(repo_coupons.get(cid)["value"], 80)
        with self.assertRaises(ValueError):
            repo_coupons.update(cid, {"used_count": 0})
        repo_coupons.set_active(cid, False)
        self.assertEqual(repo_coupons.get(cid)["is_active"], 0)


class TestChatNotifications(RepoTestCase):
    def test_chat(self):
        u, admin = self.uid("buyer1"), self.uid("admin1")
        self.assertEqual(repo_chat.list_threads(), [])
        m1 = repo_chat.add_message(u, "user", u, "สวัสดี")
        repo_chat.add_message(u, "ai", None, "สวัสดีครับ")
        m3 = repo_chat.add_message(u, "user", u, "ไม้ไหนดี")
        self.assertEqual([m["id"] for m in repo_chat.list_messages(u, after_id=m1)], [m1 + 1, m3])
        self.assertEqual(len(repo_chat.list_messages(u, limit=2)), 2)
        self.assertEqual(repo_chat.list_messages(u, limit=2)[-1]["id"], m3)
        threads = repo_chat.list_threads()
        self.assertEqual((len(threads), threads[0]["unread_count"], threads[0]["last_message"]),
                         (1, 2, "ไม้ไหนดี"))
        self.assertEqual(repo_chat.count_unread_for_staff(), 2)
        self.assertEqual(repo_chat.count_unread_for_customer(u), 1)
        self.assertEqual(repo_chat.mark_read(u, "staff"), 2)
        self.assertEqual(repo_chat.count_unread_for_staff(), 0)
        repo_chat.add_message(u, "admin", admin, "ตอบแล้ว")
        self.assertEqual(repo_chat.count_unread_for_customer(u), 2)
        self.assertEqual(repo_chat.mark_read(u, "customer"), 2)
        with self.assertRaises(ValueError):
            repo_chat.mark_read(u, "nobody")

    def test_notifications(self):
        u = self.uid("buyer1")
        n1 = repo_notifications.create(u, "หัวข้อ", "ข้อความ")
        repo_notifications.create(u, "อีกอัน", "ข้อความ2")
        self.assertEqual(repo_notifications.count_unread(u), 2)
        self.assertEqual(repo_notifications.list(u)[0]["title"], "อีกอัน")
        self.assertFalse(repo_notifications.mark_read(n1, user_id=self.uid("admin1")))   # ของคนอื่น
        self.assertTrue(repo_notifications.mark_read(n1, user_id=u))
        self.assertEqual(len(repo_notifications.list(u, unread_only=True)), 1)
        self.assertEqual(repo_notifications.mark_all_read(u), 1)
        self.assertEqual(repo_notifications.count_unread(u), 0)

    def test_notify_staff_only_active_staff(self):
        repo_users.set_active(self.uid("admin1"), False)
        self.assertEqual(repo_notifications.create_for_staff("มีออเดอร์", "ใหม่"), 1)   # owner คนเดียว
        self.assertEqual(repo_notifications.count_unread(self.uid("owner")), 1)
        self.assertEqual(repo_notifications.count_unread(self.uid("buyer1")), 0)
        repo_users.set_active(self.uid("admin1"), True)
        self.assertEqual(repo_notifications.create_for_staff("อีกครั้ง", "x"), 2)


if __name__ == "__main__":
    unittest.main()
