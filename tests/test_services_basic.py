"""
tests/test_services_basic.py
ทดสอบ services ครึ่งแรกของส่วน C (auth, settings, product, review, coupon, cart, notification)
บนฐานข้อมูลชั่วคราวที่ seed แล้ว (ไม่แตะ data/shop.db จริง)
รันจาก root โปรเจกต์:  python -m unittest tests.test_services_basic -v
(ต้องติดตั้ง bcrypt ตาม requirements.txt)
"""
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import database.db as db
from core.session import Session
from database import (
    repo_cart, repo_coupons, repo_notifications, repo_orders, repo_products, repo_users, repo_wishlist,
)
from database.seed import run_seed
from services import (
    auth_service, cart_service, coupon_service, notification_service, product_service,
    review_service, settings_service,
)

_TMP = None
_TEMPLATE = None
_REAL = (db.DB_PATH, db.DATA_DIR)


def setUpModule():
    """seed ฐานข้อมูลต้นแบบหนึ่งครั้ง (แต่ละเทสต์คัดลอกไปใช้ จึงไม่กระทบกัน)"""
    global _TMP, _TEMPLATE
    _TMP = Path(tempfile.mkdtemp(prefix="shop_svc_test_"))
    _TEMPLATE = _TMP / "template.db"
    db.DATA_DIR, db.DB_PATH = _TMP, _TEMPLATE
    run_seed()
    db.DB_PATH, db.DATA_DIR = _REAL


def tearDownModule():
    db.DB_PATH, db.DATA_DIR = _REAL
    Session.logout()
    shutil.rmtree(_TMP, ignore_errors=True)


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.path = _TMP / f"{self.id().split('.')[-1]}.db"
        shutil.copy(_TEMPLATE, self.path)
        db.DATA_DIR, db.DB_PATH = _TMP, self.path
        Session.logout()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        Session.logout()
        db.DB_PATH = _REAL[0]

    # ---- ตัวช่วย ----
    def as_user(self, username):
        """ตั้ง Session เป็นผู้ใช้ seed (ข้ามขั้น bcrypt เพื่อให้เทสต์เร็ว) คืน id"""
        row = repo_users.get_by_username(username)
        Session.login(row)
        return row["id"]

    def pid(self, name):
        with db.get_connection() as c:
            return c.execute("SELECT id FROM products WHERE name = ?", (name,)).fetchone()["id"]

    def make_completed_order(self, user_id, product_id, status="completed"):
        order_id = repo_orders.create_order(user_id, "ผู้รับ", "0812345678", "ที่อยู่", 100, 0, 0, 100)
        repo_orders.add_items(order_id, [{"product_id": product_id, "product_name": "x",
                                          "price_at_purchase": 100, "qty": 1}])
        repo_orders.update_status(order_id, status)
        return order_id


# ==========================================
# auth_service
# ==========================================
class TestAuth(ServiceTestCase):
    def test_login_logout_online_flag(self):
        user = auth_service.login("buyer1", "buyer123")
        self.assertEqual(user["role"], "buyer")
        self.assertNotIn("password_hash", user)
        self.assertEqual(repo_users.get_by_id(user["id"])["is_online"], 1)
        auth_service.logout()
        self.assertIsNone(Session.current_user)
        self.assertEqual(repo_users.get_by_id(user["id"])["is_online"], 0)

    def test_login_by_email_and_generic_error(self):
        self.assertEqual(auth_service.login("admin@shop.com", "admin123")["role"], "admin")
        for ident, pwd in (("admin1", "wrongpass"), ("nobody", "admin123"), ("", "")):
            with self.assertRaises(ValueError) as ctx:
                auth_service.login(ident, pwd)
            self.assertEqual(str(ctx.exception), "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    def test_register_unchanged_behaviour(self):
        user = auth_service.register("newbie_1", "New@Shop.com", "password1", " สมชาย ", "0891234567")
        self.assertEqual((user["role"], user["email"], user["full_name"]), ("buyer", "new@shop.com", "สมชาย"))
        with self.assertRaisesRegex(ValueError, "ชื่อผู้ใช้นี้"):
            auth_service.register("newbie_1", "x@shop.com", "password1", "a", "")
        with self.assertRaisesRegex(ValueError, "อีเมลนี้"):
            auth_service.register("other_1", "new@shop.com", "password1", "a", "")
        with self.assertRaisesRegex(ValueError, "อย่างน้อย 8"):
            auth_service.register("other_2", "o2@shop.com", "short", "a", "")
        with self.assertRaisesRegex(ValueError, "72"):
            auth_service.register("other_3", "o3@shop.com", "ก" * 25, "a", "")

    def test_change_password(self):
        uid = self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "เดิมไม่ถูกต้อง"):
            auth_service.change_password(uid, "wrong", "newpass123")
        with self.assertRaisesRegex(ValueError, "อย่างน้อย 8"):
            auth_service.change_password(uid, "buyer123", "short")
        with self.assertRaisesRegex(ValueError, "ไม่ซ้ำ"):
            auth_service.change_password(uid, "buyer123", "buyer123")
        self.assertTrue(auth_service.change_password(uid, "buyer123", "newpass123"))
        auth_service.logout()
        self.assertEqual(auth_service.login("buyer1", "newpass123")["id"], uid)
        with self.assertRaises(ValueError):
            auth_service.login("buyer1", "buyer123")

    def test_change_password_only_own_account(self):
        self.as_user("buyer1")
        admin_id = repo_users.get_by_username("admin1")["id"]
        with self.assertRaises(PermissionError):
            auth_service.change_password(admin_id, "admin123", "newpass123")
        Session.logout()
        with self.assertRaises(PermissionError):
            auth_service.change_password(admin_id, "admin123", "newpass123")

    def test_update_profile_refreshes_session(self):
        uid = self.as_user("buyer1")
        user = auth_service.update_profile(uid, "ชื่อใหม่", "0899999999")
        self.assertEqual((user["full_name"], user["phone"]), ("ชื่อใหม่", "0899999999"))
        self.assertEqual(Session.current_user["full_name"], "ชื่อใหม่")
        with self.assertRaisesRegex(ValueError, "เบอร์โทร"):
            auth_service.update_profile(uid, "ชื่อ", "123")
        with self.assertRaisesRegex(ValueError, "ชื่อ-นามสกุล"):
            auth_service.update_profile(uid, "  ", "")

    def test_create_staff_owner_only(self):
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            auth_service.create_staff("staff2", "s2@shop.com", "password1", "สต๊าฟ", "")
        self.as_user("owner")
        staff = auth_service.create_staff("staff2", "s2@shop.com", "password1", "สต๊าฟ", "0812345678")
        self.assertEqual(staff["role"], "admin")
        with self.assertRaisesRegex(ValueError, "เฉพาะบัญชีแอดมิน"):
            auth_service.create_staff("staff3", "s3@shop.com", "password1", "x", "", role="owner")
        with self.assertRaisesRegex(ValueError, "ชื่อผู้ใช้นี้"):
            auth_service.create_staff("staff2", "s9@shop.com", "password1", "x", "")

    def test_set_user_active_rules(self):
        buyer_id = repo_users.get_by_username("buyer1")["id"]
        owner_id = repo_users.get_by_username("owner")["id"]
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            auth_service.set_user_active(buyer_id, False)
        self.as_user("owner")
        with self.assertRaisesRegex(ValueError, "ตัวเอง"):
            auth_service.set_user_active(owner_id, False)
        auth_service.login("buyer1", "buyer123")      # buyer ออนไลน์อยู่
        self.as_user("owner")
        self.assertEqual(auth_service.set_user_active(buyer_id, False)["is_active"], 0)
        self.assertEqual(repo_users.get_by_id(buyer_id)["is_online"], 0)
        with self.assertRaisesRegex(ValueError, "ระงับ"):
            auth_service.login("buyer1", "buyer123")
        self.as_user("owner")
        self.assertEqual(auth_service.set_user_active(buyer_id, True)["is_active"], 1)
        with self.assertRaises(ValueError):
            auth_service.set_user_active(9999, True)

    def test_cannot_suspend_other_owner(self):
        self.as_user("owner")
        other = repo_users.create_user("owner2", "o2@shop.com", "x", "เจ้าของสอง", "", role="owner")
        with self.assertRaisesRegex(ValueError, "เจ้าของร้าน"):
            auth_service.set_user_active(other, False)

    def test_list_users(self):
        self.as_user("buyer1")
        with self.assertRaises(PermissionError):
            auth_service.list_users()
        self.as_user("owner")
        users = auth_service.list_users()
        self.assertEqual(len(users), 3)
        self.assertTrue(all("password_hash" not in u for u in users))
        self.assertEqual([u["username"] for u in auth_service.list_users(role="buyer")], ["buyer1"])
        self.assertEqual(len(auth_service.list_users(search="admin")), 1)


# ==========================================
# settings_service
# ==========================================
class TestSettings(ServiceTestCase):
    def test_read_types(self):
        info = settings_service.get_shop_info()
        self.assertEqual(info["shipping_fee"], 50.0)
        self.assertEqual(info["low_stock_threshold"], 5)
        self.assertIs(info["ai_enabled"], True)
        self.assertEqual(settings_service.get_int("unpaid_cancel_hours"), 24)
        self.assertEqual(settings_service.get_float("nonexistent_key", 1.5), 1.5)

    def test_shipping_fee_rule(self):
        self.assertEqual(settings_service.shipping_fee_for(100), 50.0)
        self.as_user("owner")
        settings_service.update_many({"free_shipping_min": "1000"})
        self.assertEqual(settings_service.shipping_fee_for(999.99), 50.0)
        self.assertEqual(settings_service.shipping_fee_for(1000), 0.0)

    def test_update_permissions_and_validation(self):
        with self.assertRaises(PermissionError):
            settings_service.update("shop_name", "x")           # ไม่ล็อกอิน
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            settings_service.update("shop_name", "x")
        self.as_user("owner")
        info = settings_service.update("shop_name", "  ร้านแบดของฉัน ")
        self.assertEqual(info["shop_name"], "ร้านแบดของฉัน")
        for key, bad in (("shipping_fee", "-5"), ("shipping_fee", "abc"), ("low_stock_threshold", "2.5"),
                         ("unpaid_cancel_hours", "0"), ("promptpay_no", "12345"), ("shop_name", " "),
                         ("ai_enabled", "maybe"), ("shipping_fee", "inf")):
            with self.assertRaises(ValueError, msg=f"{key}={bad}"):
                settings_service.update(key, bad)
        with self.assertRaisesRegex(ValueError, "ไม่รู้จัก"):
            settings_service.update("hack_key", "1")

    def test_update_many_is_all_or_nothing(self):
        self.as_user("owner")
        with self.assertRaises(ValueError):
            settings_service.update_many({"shop_name": "ชื่อใหม่", "shipping_fee": "-1"})
        self.assertEqual(settings_service.get("shop_name"), "AI.HERE BADᴍᴛ-Zone")

    def test_promptpay_normalized_and_flag(self):
        self.as_user("owner")
        info = settings_service.update_many({"promptpay_no": "081-234-5678", "shipping_fee": "49.5",
                                             "ai_enabled": "0"})
        self.assertEqual(info["promptpay_no"], "0812345678")
        self.assertEqual(info["shipping_fee"], 49.5)
        self.assertIs(info["ai_enabled"], False)


# ==========================================
# product_service
# ==========================================
class TestProductPure(ServiceTestCase):
    def test_price_rules(self):
        flash = repo_products.get_product(self.pid("Astrox 99 Pro"))      # Flash Sale ยังไม่หมด
        self.assertTrue(product_service.is_on_sale(flash))
        self.assertEqual(product_service.get_effective_price(flash), 4800.0)
        self.assertEqual(product_service.get_effective_price(flash, 220), 5020.0)
        self.assertGreater(product_service.sale_seconds_left(flash), 0)
        expired = repo_products.get_product(self.pid("Z-Ziggler"))        # โปรหมดแล้ว = ราคาเต็ม
        self.assertFalse(product_service.is_on_sale(expired))
        self.assertEqual(product_service.get_effective_price(expired), 1200.0)
        self.assertIsNone(product_service.sale_seconds_left(expired))
        always = repo_products.get_product(self.pid("Dragon P"))          # ลดตลอด ไม่มีเวลาสิ้นสุด
        self.assertTrue(product_service.is_on_sale(always))
        self.assertIsNone(product_service.sale_seconds_left(always))
        self.assertEqual(product_service.get_effective_price({"price": 100, "sale_price": None}), 100.0)

    def test_effective_price_matches_sql(self):
        for row in repo_products.list_products():
            self.assertEqual(product_service.get_effective_price(row), round(row["effective_price"], 2))


class TestProductBuyer(ServiceTestCase):
    def test_permissions(self):
        with self.assertRaises(PermissionError):
            product_service.search_products()                 # ไม่ล็อกอิน
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            product_service.search_products()                 # staff ไม่ใช่ผู้ซื้อ (ใช้ list_products_admin)

    def test_search_filters_sort_paging(self):
        self.as_user("buyer1")
        res = product_service.search_products(page_size=10)
        self.assertEqual((res["total"], len(res["items"]), res["pages"]), (25, 10, 3))
        self.assertEqual(len(product_service.search_products(page=3, page_size=10)["items"]), 5)
        self.assertEqual(product_service.search_products(page=99, page_size=10)["page"], 3)  # คลัมป์หน้า
        names = {i["name"] for i in product_service.search_products(
            filters={"balance": "Heavy Head", "flex": "Stiff"})["items"]}
        self.assertEqual(names, {"Astrox 99 Pro", "Dragon P"})
        cheap = product_service.search_products(filters={"max_price": 300}, sort="price_asc")["items"]
        self.assertTrue(cheap and all(i["effective_price"] <= 300 for i in cheap))
        self.assertEqual([i["effective_price"] for i in cheap], sorted(i["effective_price"] for i in cheap))
        self.assertEqual(product_service.search_products(query="yonex-no-such")["total"], 0)
        self.assertEqual(product_service.search_products(query="BG65")["items"][0]["name"], "เอ็น BG65")
        with self.assertRaisesRegex(ValueError, "ตัวเลข"):
            product_service.search_products(filters={"max_price": "abc"})
        # ตัวกรองแปลกปลอม/sort แปลกถูกเมินโดยไม่พัง
        self.assertEqual(product_service.search_products(filters={"evil": "1"}, sort="; DROP")["total"], 25)

    def test_items_have_price_rating_wishlist(self):
        uid = self.as_user("buyer1")
        astrox = self.pid("Astrox 99 Pro")
        repo_wishlist.add(uid, astrox)
        item = next(i for i in product_service.search_products(query="Astrox")["items"] if i["id"] == astrox)
        self.assertEqual(item["effective_price"], 4800.0)
        self.assertTrue(item["is_on_sale"] and item["in_wishlist"] and item["in_stock"])
        self.assertEqual((item["avg_rating"], item["review_count"]), (0.0, 0))
        other = next(i for i in product_service.search_products(query="Nanoflare")["items"])
        self.assertFalse(other["in_wishlist"])
        with self.assertRaises(PermissionError):                # ดู wishlist ของคนอื่นไม่ได้
            product_service.search_products(user_id=repo_users.get_by_username("admin1")["id"])

    def test_inactive_hidden_from_buyer(self):
        self.as_user("owner")
        astrox = self.pid("Astrox 99 Pro")
        product_service.set_product_active(astrox, False)
        self.as_user("buyer1")
        self.assertEqual(product_service.search_products()["total"], 24)
        with self.assertRaisesRegex(ValueError, "ไม่พบสินค้า"):
            product_service.get_product_detail(astrox)
        # ปิดหมวดทั้งหมวด -> สินค้าในหมวดหายไปด้วย
        self.as_user("owner")
        cat = repo_products.get_product(self.pid("VS 100"))["category_id"]
        product_service.set_category_active(cat, False)
        self.as_user("buyer1")
        self.assertEqual(product_service.search_products()["total"], 20)
        with self.assertRaises(ValueError):
            product_service.get_product_detail(self.pid("VS 100"))

    def test_detail(self):
        self.as_user("buyer1")
        d = product_service.get_product_detail(self.pid("Astrox 99 Pro"))
        self.assertTrue(d["has_options"] and d["is_racket"])
        labels = {o["label"]: o for o in d["options"]}
        self.assertEqual(labels["เอ็น: ขึ้นเอ็น BG65"]["final_price"], 5020.0)   # 4800 + 220
        self.assertEqual(len(d["addons"]), 3)
        self.assertTrue(all("effective_price" in a for a in d["addons"]))
        self.assertEqual((d["review_avg"], d["review_count"]), (0.0, 0))
        plain = product_service.get_product_detail(self.pid("VS 100"))
        self.assertEqual((plain["has_options"], plain["is_racket"]), (False, False))
        with self.assertRaises(ValueError):
            product_service.get_product_detail(9999)

    def test_compare(self):
        self.as_user("buyer1")
        ids = [self.pid("Astrox 99 Pro"), self.pid("Nanoflare 800"), self.pid("Dragon P")]
        res = product_service.compare_products(ids)
        self.assertEqual([r["name"] for r in res], ["Astrox 99 Pro", "Nanoflare 800", "Dragon P"])
        self.assertTrue(all(r["weight_class"] and "effective_price" in r for r in res))
        self.assertEqual(len(product_service.compare_products([ids[0], ids[0], ids[1]])), 2)  # ซ้ำถูกรวม
        with self.assertRaisesRegex(ValueError, "2-5"):
            product_service.compare_products([ids[0]])
        # รองรับ 2-5 ไม้ตามข้อกำหนดใหม่ (4 และ 5 ไม้ต้องผ่าน, 6 ไม้ต้องไม่ผ่าน)
        four = ids + [self.pid("Z-Ziggler")]
        five = four + [self.pid("TK Ryuga II Pro")]
        six = five + [self.pid("Auraspeed 100X")]
        self.assertEqual(len(product_service.compare_products(four)), 4)
        self.assertEqual(len(product_service.compare_products(five)), 5)
        with self.assertRaisesRegex(ValueError, "2-5"):
            product_service.compare_products(six)
        with self.assertRaisesRegex(ValueError, "เฉพาะไม้"):
            product_service.compare_products([ids[0], self.pid("VS 100")])
        with self.assertRaises(ValueError):
            product_service.compare_products([ids[0], 9999])

    def test_recommend_rackets(self):
        self.as_user("buyer1")
        res = product_service.recommend_rackets("Advanced", product_service.STYLE_ATTACK)
        self.assertTrue(res)
        scores = [r["match_score"] for r in res]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(r["match_reasons"] for r in res))
        self.assertIn(res[0]["name"], ("Astrox 99 Pro", "TK Ryuga II Pro"))   # Heavy Head + Advanced
        # ไม้ Professional ยากเกินฝีมือ Beginner (ห่าง 3 ขั้น) ต้องไม่ถูกแนะนำ
        beginner = product_service.recommend_rackets("Beginner", product_service.STYLE_ATTACK)
        self.assertTrue(all(r["level"] in ("Beginner", "Intermediate") for r in beginner))
        budget = product_service.recommend_rackets("Intermediate", product_service.STYLE_ATTACK, budget=2000)
        self.assertTrue(budget and all(r["effective_price"] <= 2000 for r in budget))
        self.assertEqual(product_service.recommend_rackets("Beginner", product_service.STYLE_SPEED, budget=100), [])
        with self.assertRaises(ValueError):
            product_service.recommend_rackets("Expert", "attack")
        with self.assertRaises(ValueError):
            product_service.recommend_rackets("Beginner", "fly")
        with self.assertRaises(ValueError):
            product_service.recommend_rackets("Beginner", "attack", budget=-5)

    def test_filter_values_and_catalog(self):
        self.as_user("buyer1")
        vals = product_service.list_filter_values()
        self.assertEqual(len(vals["brands"]), 6)
        self.assertIn("3U", vals["weight_class"])
        self.assertEqual(len(product_service.list_categories()), 6)
        with self.assertRaises(PermissionError):
            product_service.list_categories(include_inactive=True)


class TestProductAdmin(ServiceTestCase):
    def _new_fields(self, **extra):
        cat = repo_products.list_categories()[0]["id"]
        brand = repo_products.list_brands()[0]["id"]
        return {"category_id": cat, "brand_id": brand, "name": "ไม้ทดสอบ", "price": 1000, **extra}

    def test_list_and_edit_view(self):
        self.as_user("buyer1")
        with self.assertRaises(PermissionError):
            product_service.list_products_admin()
        self.as_user("admin1")
        res = product_service.list_products_admin(page_size=100)
        self.assertEqual(res["total"], 25)
        self.as_user("owner")
        product_service.set_product_active(self.pid("VS 100"), False)
        self.as_user("admin1")
        self.assertEqual(product_service.list_products_admin()["total"], 25)                # เห็นของที่ปิดขายด้วย
        self.assertEqual(product_service.list_products_admin(show_inactive=False)["total"], 24)
        d = product_service.get_product_for_edit(self.pid("Astrox 99 Pro"))
        self.assertEqual((len(d["options"]), len(d["addons"])), (3, 3))

    def test_admin_create_and_price_restrictions(self):
        self.as_user("admin1")
        p = product_service.save_product(self._new_fields(stock="12"))
        self.assertEqual((p["name"], p["price"], p["stock"]), ("ไม้ทดสอบ", 1000.0, 12))
        pid = p["id"]
        # แอดมินแก้ข้อมูลพื้นฐานได้
        p = product_service.save_product({"name": "ไม้ทดสอบ2", "description": "ดี"}, pid)
        self.assertEqual(p["name"], "ไม้ทดสอบ2")
        # ส่งราคาเดิมซ้ำ (ฟอร์มส่งทุกช่อง) ต้องผ่าน
        product_service.save_product({"name": "ไม้ทดสอบ3", "price": 1000, "sale_price": None}, pid)
        # เปลี่ยนราคา/ตั้งโปรไม่ได้
        with self.assertRaises(PermissionError):
            product_service.save_product({"price": 900}, pid)
        with self.assertRaises(PermissionError):
            product_service.save_product({"sale_price": 800}, pid)
        with self.assertRaises(PermissionError):
            product_service.save_product(self._new_fields(sale_price=500))
        # ปิดขายได้เฉพาะเจ้าของ
        with self.assertRaises(PermissionError):
            product_service.set_product_active(pid, False)

    def test_owner_price_and_sale(self):
        self.as_user("owner")
        pid = product_service.save_product(self._new_fields())["id"]
        end = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        p = product_service.save_product({"price": 1200, "sale_price": 999, "sale_ends_at": end}, pid)
        self.assertEqual((p["price"], p["sale_price"], p["is_on_sale"]), (1200.0, 999.0, True))
        self.assertTrue(p["sale_ends_at"].endswith("23:59:59"))
        with self.assertRaisesRegex(ValueError, "น้อยกว่า"):
            product_service.save_product({"sale_price": 1200}, pid)
        with self.assertRaisesRegex(ValueError, "น้อยกว่า"):
            product_service.save_product({"price": 900}, pid)           # ราคาปกติต่ำกว่าราคาลดเดิม
        p = product_service.save_product({"sale_price": None}, pid)      # ล้างราคาลด = ล้างเวลาด้วย
        self.assertEqual((p["sale_price"], p["sale_ends_at"], p["is_on_sale"]), (None, None, False))
        with self.assertRaisesRegex(ValueError, "ราคาลด"):
            product_service.save_product({"sale_ends_at": end}, pid)
        with self.assertRaisesRegex(ValueError, "รูปแบบ"):
            product_service.save_product({"sale_price": 500, "sale_ends_at": "พรุ่งนี้"}, pid)

    def test_save_product_validation(self):
        self.as_user("owner")
        for bad in ({"name": " "}, {"price": 0}, {"price": "abc"}, {"price": -5}, {"stock": -1},
                    {"stock": 1.5}, {"weight_class": "5U"}, {"level": "God"}, {"category_id": 9999},
                    {"brand_id": None}):
            with self.assertRaises(ValueError, msg=str(bad)):
                product_service.save_product(self._new_fields(**bad))
        with self.assertRaises(ValueError):
            product_service.save_product({"name": "x"}, 9999)
        p = product_service.save_product(self._new_fields(weight_class="4U", balance="", level="Advanced"))
        self.assertEqual((p["weight_class"], p["balance"], p["level"]), ("4U", None, "Advanced"))

    def test_stock_ignored_when_product_has_options(self):
        self.as_user("owner")
        astrox = self.pid("Astrox 99 Pro")
        before = repo_products.get_product(astrox)["stock"]
        p = product_service.save_product({"name": "Astrox 99 Pro", "stock": 9999}, astrox)
        self.assertEqual(p["stock"], before)

    def test_adjust_stock(self):
        self.as_user("buyer1")
        with self.assertRaises(PermissionError):
            product_service.adjust_stock(self.pid("VS 100"), 1)
        self.as_user("admin1")
        vs = self.pid("VS 100")
        self.assertEqual(product_service.adjust_stock(vs, -10)["stock"], 90)
        self.assertEqual(product_service.adjust_stock(vs, 5)["stock"], 95)
        with self.assertRaisesRegex(ValueError, "ติดลบ"):
            product_service.adjust_stock(vs, -1000)
        self.assertEqual(repo_products.get_product(vs)["stock"], 95)
        for bad in (0, 1.5, True, "5"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                product_service.adjust_stock(vs, bad)
        with self.assertRaises(ValueError):
            product_service.adjust_stock(vs, 1, option_id=1)             # สินค้าไม่มีตัวเลือก
        # สินค้ามีตัวเลือก ต้องระบุตัวเลือก และสต็อกรวมถูก sync
        astrox = self.pid("Astrox 99 Pro")
        with self.assertRaisesRegex(ValueError, "เลือกตัวเลือก"):
            product_service.adjust_stock(astrox, 1)
        total_before = repo_products.get_product(astrox)["stock"]
        self.assertEqual(product_service.adjust_stock(astrox, 4, option_id=1)["stock"], total_before + 4)
        with self.assertRaisesRegex(ValueError, "ไม่ได้เป็นของ"):
            product_service.adjust_stock(astrox, 1, option_id=8)         # ตัวเลือกของ Tectonic 9
        with self.assertRaises(ValueError):
            product_service.adjust_stock(9999, 1)

    def test_low_stock(self):
        self.as_user("buyer1")
        with self.assertRaises(PermissionError):
            product_service.get_low_stock_products()
        self.as_user("admin1")
        low = product_service.get_low_stock_products()
        self.assertEqual(low["threshold"], 5)
        self.assertIn("Tectonic 9", [p["name"] for p in low["products"]])      # สต็อกรวม 3
        tectonic_opts = {(o["option_value"], o["stock"]) for o in low["options"] if o["product_name"] == "Tectonic 9"}
        self.assertEqual(tectonic_opts, {("ดำ/ทอง", 3), ("ขาว/แดง", 0)})        # ตัวเลือกสต็อก 3 และ 0
        self.assertTrue(all(o["stock"] <= 5 for o in low["options"]))
        self.as_user("owner")
        settings_service.update("low_stock_threshold", 0)
        zero = product_service.get_low_stock_products()
        self.assertEqual((zero["threshold"], [o["stock"] for o in zero["options"]]), (0, [0]))   # เหลือแต่ที่หมดจริง

    def test_options_and_addons(self):
        self.as_user("admin1")
        vs = self.pid("VS 100")
        p = product_service.save_option(vs, "ไซซ์", "M", 0, 5)
        self.assertEqual((len(p["options"]), p["stock"]), (1, 5))
        opt_id = p["options"][0]["id"]
        p = product_service.save_option(vs, "ไซซ์", "L", extra_price=30, stock=7, option_id=opt_id)
        self.assertEqual((p["options"][0]["option_value"], p["stock"]), ("L", 7))
        for args in (("สีรุ้ง", "x", 0, 0), ("ไซซ์", " ", 0, 0), ("ไซซ์", "S", -1, 0), ("ไซซ์", "S", 0, -1)):
            with self.assertRaises(ValueError, msg=str(args)):
                product_service.save_option(vs, *args)
        with self.assertRaisesRegex(ValueError, "ไม่พบตัวเลือก"):
            product_service.save_option(self.pid("A+ 300"), "ไซซ์", "S", 0, 0, option_id=opt_id)
        p = product_service.delete_option(opt_id)
        self.assertEqual(p["options"], [])
        with self.assertRaises(ValueError):
            product_service.delete_option(opt_id)
        # ตัวเลือกที่เคยถูกสั่งซื้อ ลบไม่ได้
        used = 1
        buyer_id = repo_users.get_by_username("buyer1")["id"]
        oid = repo_orders.create_order(buyer_id, "a", "b", "c", 1, 0, 0, 1)
        repo_orders.add_items(oid, [{"product_id": self.pid("Astrox 99 Pro"), "option_id": used,
                                     "product_name": "x", "price_at_purchase": 1, "qty": 1}])
        with self.assertRaisesRegex(ValueError, "เคยถูกสั่งซื้อ"):
            product_service.delete_option(used)
        # addons
        p = product_service.set_addons(vs, [self.pid("เอ็น BG65"), self.pid("เอ็น BG80")])
        self.assertEqual(len(p["addons"]), 2)
        with self.assertRaises(ValueError):
            product_service.set_addons(vs, [9999])
        self.as_user("buyer1")
        with self.assertRaises(PermissionError):
            product_service.set_addons(vs, [])

    def test_categories_and_brands_owner_only(self):
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            product_service.save_category("หมวดใหม่")
        with self.assertRaises(PermissionError):
            product_service.save_brand("แบรนด์ใหม่")
        self.as_user("owner")
        cat = product_service.save_category("  อุปกรณ์เสริม ")
        self.assertEqual(cat["name"], "อุปกรณ์เสริม")
        self.assertEqual(product_service.save_category("อุปกรณ์เสริมใหม่", cat["id"])["name"], "อุปกรณ์เสริมใหม่")
        with self.assertRaisesRegex(ValueError, "ชื่อนี้อยู่แล้ว"):
            product_service.save_category("รองเท้า")
        with self.assertRaises(ValueError):
            product_service.save_category("x", 9999)
        with self.assertRaises(ValueError):
            product_service.save_category(" ")
        brand = product_service.save_brand("Mizuno")
        self.assertEqual(product_service.set_brand_active(brand["id"], False)["is_active"], 0)
        with self.assertRaisesRegex(ValueError, "ชื่อนี้อยู่แล้ว"):
            product_service.save_brand("Yonex")
        names = [c["name"] for c in product_service.list_categories(include_inactive=True)]
        self.assertIn("อุปกรณ์เสริมใหม่", names)


# ==========================================
# review_service
# ==========================================
class TestReviews(ServiceTestCase):
    def test_review_flow_and_rules(self):
        uid = self.as_user("buyer1")
        astrox = self.pid("Astrox 99 Pro")
        pending = self.make_completed_order(uid, astrox, status="pending")
        done = self.make_completed_order(uid, astrox)
        # ยังไม่สำเร็จ / ไม่มีสินค้านั้น / ออเดอร์ไม่ใช่ของเรา
        self.assertFalse(review_service.can_review(uid, astrox, pending))
        with self.assertRaisesRegex(ValueError, "สำเร็จแล้ว"):
            review_service.add_review(uid, astrox, pending, 5)
        self.assertFalse(review_service.can_review(uid, self.pid("VS 100"), done))
        with self.assertRaisesRegex(ValueError, "ไม่มีสินค้านี้"):
            review_service.add_review(uid, self.pid("VS 100"), done, 5)
        admin_id = repo_users.get_by_username("admin1")["id"]
        other_order = self.make_completed_order(admin_id, astrox)
        with self.assertRaisesRegex(ValueError, "ไม่พบคำสั่งซื้อ"):
            review_service.add_review(uid, astrox, other_order, 5)
        # ให้ดาวผิด
        for bad in (0, 6, True, 4.5, "5", None):
            with self.assertRaisesRegex(ValueError, "1-5", msg=repr(bad)):
                review_service.add_review(uid, astrox, done, bad)
        with self.assertRaisesRegex(ValueError, "ยาวเกินไป"):
            review_service.add_review(uid, astrox, done, 5, "ก" * 1001)
        # รีวิวสำเร็จ แล้วซ้ำไม่ได้
        self.assertEqual(review_service.find_reviewable_order(uid, astrox), done)
        self.assertTrue(review_service.can_review(uid, astrox, done))
        rv = review_service.add_review(uid, astrox, done, 4, "  ไม้ดีมาก  ")
        self.assertEqual((rv["rating"], rv["comment"]), (4, "ไม้ดีมาก"))
        self.assertFalse(review_service.can_review(uid, astrox, done))
        with self.assertRaisesRegex(ValueError, "ไปแล้ว"):
            review_service.add_review(uid, astrox, done, 5)
        self.assertIsNone(review_service.find_reviewable_order(uid, astrox))

    def test_list_reviews_and_summary(self):
        uid = self.as_user("buyer1")
        astrox = self.pid("Astrox 99 Pro")
        for rating in (5, 3):
            review_service.add_review(uid, astrox, self.make_completed_order(uid, astrox), rating, f"r{rating}")
        res = review_service.list_reviews(astrox)
        self.assertEqual((res["count"], res["avg"], res["total"]), (2, 4.0, 2))
        self.assertEqual([r["comment"] for r in res["items"]], ["r3", "r5"])        # ใหม่สุดก่อน
        self.assertTrue(all("reviewer_name" in r and "user_id" not in r for r in res["items"]))
        self.assertEqual(len(review_service.list_reviews(astrox, page=2, page_size=1)["items"]), 1)
        self.assertEqual(review_service.list_reviews(self.pid("VS 100"))["count"], 0)
        # คะแนนไปปรากฏในผลค้นหา/รายละเอียด
        d = product_service.get_product_detail(astrox)
        self.assertEqual((d["review_avg"], d["review_count"]), (4.0, 2))
        self.as_user("admin1")
        self.assertEqual(review_service.list_reviews(astrox)["count"], 2)           # แอดมินดูได้

    def test_only_own_identity(self):
        uid = self.as_user("buyer1")
        astrox = self.pid("Astrox 99 Pro")
        order = self.make_completed_order(uid, astrox)
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            review_service.add_review(uid, astrox, order, 5)            # แอดมินรีวิวแทนไม่ได้
        Session.logout()
        with self.assertRaises(PermissionError):
            review_service.list_reviews(astrox)


# ==========================================
# coupon_service
# ==========================================
class TestCoupons(ServiceTestCase):
    def test_validate_discounts(self):
        uid = self.as_user("buyer1")
        r = coupon_service.validate_coupon(" welcome10 ", uid, 1000)               # ไม่สนตัวพิมพ์/ช่องว่าง
        self.assertEqual((r["code"], r["discount"], r["discount_type"]), ("WELCOME10", 100.0, "percent"))
        self.assertEqual(r["description"], "ลด 10%")
        self.assertEqual(coupon_service.validate_coupon("SAVE200", uid, 2500)["discount"], 200.0)
        self.assertEqual(coupon_service.validate_coupon("WELCOME10", uid, 999.99)["discount"], 100.0)
        # ไม่แก้ DB (validate เฉยๆ ไม่นับสิทธิ์)
        self.assertEqual(repo_coupons.get_by_code("WELCOME10")["used_count"], 0)

    def test_discount_capped_at_subtotal(self):
        self.as_user("owner")
        coupon_service.create_coupon("BIG500", "fixed", 500)
        uid = self.as_user("buyer1")
        self.assertEqual(coupon_service.validate_coupon("BIG500", uid, 300)["discount"], 300.0)

    def test_error_cases_distinct_messages(self):
        uid = self.as_user("buyer1")
        cases = [("", 1000, "กรุณากรอก"), ("NOPE", 1000, "ไม่พบโค้ด"), ("OLD50", 1000, "หมดอายุ"),
                 ("WELCOME10", 400, "ไม่ถึงขั้นต่ำ"), ("SAVE200", 1999, "ไม่ถึงขั้นต่ำ")]
        for code, subtotal, text in cases:
            with self.assertRaisesRegex(ValueError, text, msg=code):
                coupon_service.validate_coupon(code, uid, subtotal)
        # ใช้ไปแล้ว
        oid = repo_orders.create_order(uid, "a", "b", "c", 1000, 100, 0, 900)
        repo_coupons.add_usage(repo_coupons.get_by_code("WELCOME10")["id"], uid, oid)
        with self.assertRaisesRegex(ValueError, "ใช้โค้ดส่วนลดนี้ไปแล้ว"):
            coupon_service.validate_coupon("WELCOME10", uid, 1000)
        coupon_service.validate_coupon("SAVE200", uid, 2500)             # คูปองอื่นยังใช้ได้
        # ครบสิทธิ์
        self.as_user("owner")
        sid = repo_coupons.get_by_code("SAVE200")["id"]
        coupon_service.update_coupon(sid, {"max_uses": 1})
        repo_coupons.increment_used(sid)
        self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "ครบสิทธิ์"):
            coupon_service.validate_coupon("SAVE200", uid, 2500)
        # ปิดใช้งาน
        self.as_user("owner")
        coupon_service.toggle_coupon(repo_coupons.get_by_code("WELCOME10")["id"], False)
        self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "ปิดใช้งาน"):
            coupon_service.validate_coupon("WELCOME10", uid, 1000)

    def test_validate_permissions(self):
        uid = repo_users.get_by_username("buyer1")["id"]
        with self.assertRaises(PermissionError):
            coupon_service.validate_coupon("WELCOME10", uid, 1000)       # ไม่ล็อกอิน
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            coupon_service.validate_coupon("WELCOME10", uid, 1000)       # ไม่ใช่ผู้ซื้อ

    def test_manage_owner_only_and_validation(self):
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            coupon_service.create_coupon("NEW10", "percent", 10)
        with self.assertRaises(PermissionError):
            coupon_service.list_coupons()
        self.as_user("owner")
        c = coupon_service.create_coupon("new10", "percent", 10, min_order=300, max_uses=5, expires_at="2030-01-31")
        self.assertEqual((c["code"], c["expires_at"], c["remaining"], c["is_expired"]),
                         ("NEW10", "2030-01-31 23:59:59", 5, False))
        with self.assertRaisesRegex(ValueError, "มีโค้ด"):
            coupon_service.create_coupon("NEW10", "fixed", 50)
        for kwargs in (dict(code="ab", discount_type="fixed", value=10), dict(code="OK1", discount_type="bogus", value=1),
                       dict(code="OK2", discount_type="percent", value=101), dict(code="OK3", discount_type="fixed", value=0),
                       dict(code="OK4", discount_type="fixed", value="x"), dict(code="OK5", discount_type="fixed", value=5, min_order=-1),
                       dict(code="OK6", discount_type="fixed", value=5, max_uses=0),
                       dict(code="OK7", discount_type="fixed", value=5, expires_at="เร็วๆนี้")):
            with self.assertRaises(ValueError, msg=str(kwargs)):
                coupon_service.create_coupon(**kwargs)
        # แก้ไข
        c = coupon_service.update_coupon(c["id"], {"value": 15, "max_uses": ""})
        self.assertEqual((c["value"], c["max_uses"], c["remaining"]), (15.0, None, None))
        with self.assertRaisesRegex(ValueError, "ไม่เกิน 100"):
            coupon_service.update_coupon(c["id"], {"value": 150})
        with self.assertRaisesRegex(ValueError, "ไม่เกิน 100"):
            coupon_service.update_coupon(c["id"], {"discount_type": "percent", "value": 101})
        with self.assertRaises(ValueError):
            coupon_service.update_coupon(9999, {"value": 5})
        # ไม่ให้ตั้งสิทธิ์ต่ำกว่าที่ใช้ไปแล้ว
        sid = repo_coupons.get_by_code("SAVE200")["id"]
        repo_coupons.increment_used(sid)
        repo_coupons.increment_used(sid)
        with self.assertRaisesRegex(ValueError, "ที่ถูกใช้ไปแล้ว"):
            coupon_service.update_coupon(sid, {"max_uses": 1})
        # toggle / list
        self.assertEqual(coupon_service.toggle_coupon(c["id"])["is_active"], 0)
        self.assertEqual(coupon_service.toggle_coupon(c["id"])["is_active"], 1)
        listing = coupon_service.list_coupons()
        self.assertEqual(len(listing), 4)
        self.assertTrue(next(x for x in listing if x["code"] == "OLD50")["is_expired"])
        self.assertEqual(coupon_service.get_coupon(sid)["code"], "SAVE200")


# ==========================================
# cart_service
# ==========================================
class TestCart(ServiceTestCase):
    def test_permissions(self):
        uid = repo_users.get_by_username("buyer1")["id"]
        with self.assertRaises(PermissionError):
            cart_service.get_cart(uid)
        self.as_user("admin1")
        with self.assertRaises(PermissionError):
            cart_service.get_cart(uid)
        self.as_user("buyer1")
        other = repo_users.get_by_username("admin1")["id"]
        with self.assertRaises(PermissionError):
            cart_service.add_to_cart(other, self.pid("VS 100"))          # ตะกร้าของคนอื่น

    def test_add_and_totals(self):
        uid = self.as_user("buyer1")
        vs, astrox = self.pid("VS 100"), self.pid("Astrox 99 Pro")
        self.assertEqual(cart_service.add_to_cart(uid, vs)["cart_count"], 1)
        self.assertEqual(cart_service.add_to_cart(uid, vs, qty=2)["cart_count"], 3)      # บวกจำนวน
        astrox_opt = repo_products.list_options(astrox)[1]                                # ขึ้นเอ็น BG65 +220
        cart_service.add_to_cart(uid, astrox, astrox_opt["id"])
        cart = cart_service.get_cart(uid)
        self.assertEqual(len(cart["items"]), 2)
        by_name = {i["product_name"]: i for i in cart["items"]}
        self.assertEqual((by_name["VS 100"]["qty"], by_name["VS 100"]["line_total"]), (3, 1650.0))
        self.assertEqual(by_name["Astrox 99 Pro"]["unit_price"], 5020.0)                  # Flash 4800 + 220
        self.assertEqual(by_name["Astrox 99 Pro"]["option_label"], "เอ็น: ขึ้นเอ็น BG65")
        self.assertEqual((cart["subtotal"], cart["item_count"], cart["has_problem"]), (6670.0, 4, False))
        self.assertEqual(cart_service.get_cart_count(uid), 4)

    def test_validation_errors(self):
        uid = self.as_user("buyer1")
        vs, astrox, tectonic = self.pid("VS 100"), self.pid("Astrox 99 Pro"), self.pid("Tectonic 9")
        with self.assertRaisesRegex(ValueError, "เลือกตัวเลือก"):
            cart_service.add_to_cart(uid, astrox)                         # มีตัวเลือกแต่ไม่เลือก
        with self.assertRaisesRegex(ValueError, "ไม่ได้เป็นของสินค้านี้"):
            cart_service.add_to_cart(uid, astrox, option_id=8)            # ตัวเลือกของสินค้าอื่น
        with self.assertRaisesRegex(ValueError, "ไม่มีตัวเลือก"):
            cart_service.add_to_cart(uid, vs, option_id=1)
        with self.assertRaisesRegex(ValueError, "ไม่พบสินค้า"):
            cart_service.add_to_cart(uid, 9999)
        for bad in (0, -1, 1.5, True, "2", 100):
            with self.assertRaises(ValueError, msg=repr(bad)):
                cart_service.add_to_cart(uid, vs, qty=bad)
        with self.assertRaisesRegex(ValueError, "สินค้าหมด"):
            cart_service.add_to_cart(uid, tectonic, option_id=9)          # ตัวเลือกสต็อก 0
        self.assertEqual(cart_service.get_cart_count(uid), 0)             # ล้มเหลวทั้งหมดไม่เหลือเศษ

    def test_stock_limit_including_cart(self):
        uid = self.as_user("buyer1")
        tectonic = self.pid("Tectonic 9")
        opt = 8                                                            # ดำ/ทอง สต็อก 3
        cart_service.add_to_cart(uid, tectonic, opt, qty=2)
        with self.assertRaisesRegex(ValueError, "เหลือเพียง 3.*ในตะกร้ามี 2"):
            cart_service.add_to_cart(uid, tectonic, opt, qty=2)
        self.assertEqual(cart_service.add_to_cart(uid, tectonic, opt, qty=1)["cart_count"], 3)
        self.assertEqual(cart_service.get_cart(uid)["items"][0]["qty"], 3)

    def test_inactive_product_blocked(self):
        uid = self.as_user("buyer1")
        vs = self.pid("VS 100")
        self.as_user("owner")
        product_service.set_product_active(vs, False)
        self.as_user("buyer1")
        with self.assertRaisesRegex(ValueError, "ปิดการขาย"):
            cart_service.add_to_cart(uid, vs)

    def test_update_qty_and_remove(self):
        uid = self.as_user("buyer1")
        vs = self.pid("VS 100")
        item = cart_service.add_to_cart(uid, vs)["cart_item_id"]
        cart = cart_service.update_qty(uid, item, 5)
        self.assertEqual((cart["items"][0]["qty"], cart["subtotal"]), (5, 2750.0))
        with self.assertRaisesRegex(ValueError, "ไม่น้อยกว่า 1"):
            cart_service.update_qty(uid, item, 0)
        repo_products.adjust_stock(vs, -97)                                # เหลือ 3 ชิ้น
        with self.assertRaisesRegex(ValueError, "เหลือเพียง 3"):
            cart_service.update_qty(uid, item, 4)
        with self.assertRaises(ValueError):
            cart_service.update_qty(uid, 9999, 1)
        self.assertTrue(cart_service.remove_item(uid, item))
        self.assertFalse(cart_service.remove_item(uid, item))
        self.assertEqual(cart_service.get_cart(uid)["items"], [])

    def test_problems_flagged(self):
        uid = self.as_user("buyer1")
        vs = self.pid("VS 100")
        cart_service.add_to_cart(uid, vs, qty=3)
        repo_products.adjust_stock(vs, -98)                                # เหลือ 2 < 3 ในตะกร้า
        cart = cart_service.get_cart(uid)
        self.assertTrue(cart["has_problem"])
        self.assertEqual(cart["items"][0]["problem"], "เหลือเพียง 2 ชิ้น")
        repo_products.adjust_stock(vs, -2)
        self.assertEqual(cart_service.get_cart(uid)["items"][0]["problem"], "สินค้าหมด")
        repo_products.set_product_active(vs, False)
        self.assertEqual(cart_service.get_cart(uid)["items"][0]["problem"], "สินค้านี้ปิดการขายแล้ว")

    def test_deleted_option_flagged(self):
        uid = self.as_user("buyer1")
        astrox = self.pid("Astrox 99 Pro")
        cart_service.add_to_cart(uid, astrox, 3)                           # ขึ้นเอ็น BG80
        repo_products.delete_option(3)                                     # option_id ถูก SET NULL
        item = cart_service.get_cart(uid)["items"][0]
        self.assertIsNone(item["option_id"])
        self.assertIn("ตัวเลือกสินค้าถูกลบ", item["problem"])

    def test_add_with_addons_all_or_nothing(self):
        uid = self.as_user("buyer1")
        astrox = self.pid("Astrox 99 Pro")
        addons = [a["id"] for a in repo_products.list_addons(astrox)]
        res = cart_service.add_with_addons(uid, astrox, addons[:2], option_id=1)
        self.assertEqual((len(res["cart_item_ids"]), res["cart_count"]), (3, 3))
        # สินค้าเสริมที่ไม่ได้ขายคู่กัน -> ไม่เพิ่มอะไรเลย (แม้สินค้าหลักผ่านแล้ว)
        repo_cart.clear(uid)
        with self.assertRaisesRegex(ValueError, "ไม่ได้ขายคู่กับ"):
            cart_service.add_with_addons(uid, astrox, [addons[0], self.pid("VS 100")], option_id=1)
        self.assertEqual(cart_service.get_cart_count(uid), 0)
        # addon สต็อกหมด -> ย้อนกลับทั้งชุด และบอกชื่อสินค้าที่มีปัญหา
        repo_products.adjust_stock(addons[1], -200)
        with self.assertRaisesRegex(ValueError, ".*: สินค้าหมด"):
            cart_service.add_with_addons(uid, astrox, addons, option_id=1)
        self.assertEqual(cart_service.get_cart_count(uid), 0)
        # สินค้าหลักผิด (ไม่เลือกตัวเลือก) ก็ไม่เพิ่ม addon
        with self.assertRaises(ValueError):
            cart_service.add_with_addons(uid, astrox, [addons[0]])
        self.assertEqual(cart_service.get_cart_count(uid), 0)

    def test_clear(self):
        uid = self.as_user("buyer1")
        cart_service.add_to_cart(uid, self.pid("VS 100"))
        cart_service.add_to_cart(uid, self.pid("A+ 300"))
        self.assertEqual(cart_service.clear_cart(uid), 2)
        self.assertEqual(cart_service.get_cart(uid)["subtotal"], 0)


# ==========================================
# notification_service
# ==========================================
class TestNotifications(ServiceTestCase):
    def test_notify_and_read_flow(self):
        uid = repo_users.get_by_username("buyer1")["id"]
        notification_service.notify(uid, "  ออเดอร์ใหม่ ", "รายละเอียด")
        notification_service.notify(uid, "อีกอัน", "x" * 1000)
        self.as_user("buyer1")
        mine = notification_service.list_my()
        self.assertEqual([n["title"] for n in mine], ["อีกอัน", "ออเดอร์ใหม่"])           # ใหม่สุดก่อน
        self.assertEqual(len(mine[0]["message"]), 500)                                    # ตัดข้อความยาว
        self.assertEqual(notification_service.unread_count(), 2)
        self.assertTrue(notification_service.mark_read(mine[0]["id"]))
        self.assertEqual(notification_service.unread_count(), 1)
        self.assertEqual([n["title"] for n in notification_service.list_my(unread_only=True)], ["ออเดอร์ใหม่"])
        self.assertEqual(notification_service.mark_all_read(), 1)
        self.assertEqual(notification_service.unread_count(), 0)

    def test_cannot_touch_others(self):
        buyer_id = repo_users.get_by_username("buyer1")["id"]
        nid = notification_service.notify(buyer_id, "ส่วนตัว", "ลับ")
        self.as_user("admin1")
        self.assertFalse(notification_service.mark_read(nid))
        self.assertEqual(notification_service.list_my(), [])
        self.assertEqual(repo_notifications.count_unread(buyer_id), 1)

    def test_notify_staff(self):
        self.assertEqual(notification_service.notify_staff("ออเดอร์ใหม่", "#1"), 2)        # admin + owner
        self.as_user("buyer1")
        self.assertEqual(notification_service.unread_count(), 0)
        self.as_user("owner")
        self.assertEqual(notification_service.unread_count(), 1)
        repo_users.set_active(repo_users.get_by_username("admin1")["id"], False)
        self.assertEqual(notification_service.notify_staff("อีกอัน"), 1)                   # ข้ามบัญชีที่ระงับ

    def test_validation_and_login_required(self):
        with self.assertRaises(PermissionError):
            notification_service.list_my()
        with self.assertRaises(PermissionError):
            notification_service.unread_count()
        with self.assertRaises(ValueError):
            notification_service.notify(1, "  ", "x")

    def test_notify_inside_transaction_rolls_back(self):
        uid = repo_users.get_by_username("buyer1")["id"]
        with self.assertRaises(RuntimeError):
            with db.transaction() as conn:
                notification_service.notify(uid, "จะถูกย้อนกลับ", "x", conn=conn)
                raise RuntimeError("boom")
        self.assertEqual(repo_notifications.count_unread(uid), 0)


class TestImports(unittest.TestCase):
    def test_no_ui_import_in_services(self):
        """ข้อตกลงชั้น: services ห้าม import ui"""
        import inspect
        for module in (auth_service, settings_service, product_service, review_service,
                       coupon_service, cart_service, notification_service):
            source = inspect.getsource(module)
            self.assertNotIn("import ui", source)
            self.assertNotIn("from ui", source)


if __name__ == "__main__":
    unittest.main()
