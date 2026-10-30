"""
tests/test_api_web.py
ชุดทดสอบชั้น Web API (FastAPI + ContextVar Session) ครบทุกโดเมนและทดสอบความปลอดภัย:
- การแยกเซสชันผู้ใช้หลายคนพร้อมกัน (ContextVar isolation)
- โหมดผู้เยี่ยมชม (Guest) เมื่อไม่มีคุกกี้
- Flow ครบวงจร: สมัคร+OTP -> Login -> ตะกร้า -> คูปอง -> สั่งซื้อ -> QR/แนบสลิป -> แอดมินอนุมัติ -> จัดส่ง -> รับของ -> ใบเสร็จ PDF -> รีวิว
- สิทธิ์ Buyer vs Admin vs Owner ในทุกหมวด API
- ป้องกัน IDOR, ข้ามสิทธิ์, CSRF Origin, รั่วไหลของ password_hash, การเข้าถึงสลิป/ใบเสร็จของคนอื่น และ Idle Lock
"""
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

import config
import database.db as db
from core.session import Session
from database.seed import run_seed
from server.app import create_app

_TMP = None
_TEMPLATE = None
_REAL_DB = (db.DB_PATH, db.DATA_DIR, config.DB_PATH, config.DATA_DIR)
_REAL_DIRS = (
    config.SLIPS_DIR,
    config.RECEIPTS_DIR,
    config.USER_IMAGES_DIR,
    config.PRODUCT_IMAGES_DIR,
    config.CATEGORY_IMAGES_DIR,
    config.BANNER_IMAGES_DIR,
    config.EXPORTS_DIR,
    config.MONTHLY_EXPORTS_DIR,
    config.BACKUP_DIR,
    config.REVIEWS_DIR,
    config.CHAT_IMAGES_DIR,
)


def _make_png_bytes(color=(230, 57, 70), size=(80, 80)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _assert_no_secret_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in ("password_hash", "code_hash", "token_hash"), f"Leaked secret key: {k}"
            _assert_no_secret_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_secret_keys(item)


def setUpModule():
    global _TMP, _TEMPLATE
    _TMP = Path(tempfile.mkdtemp(prefix="shop_api_test_"))
    _TEMPLATE = _TMP / "template.db"
    db.DATA_DIR = config.DATA_DIR = _TMP
    db.DB_PATH = config.DB_PATH = _TEMPLATE
    run_seed()


def tearDownModule():
    db.DB_PATH, db.DATA_DIR, config.DB_PATH, config.DATA_DIR = _REAL_DB
    (
        config.SLIPS_DIR,
        config.RECEIPTS_DIR,
        config.USER_IMAGES_DIR,
        config.PRODUCT_IMAGES_DIR,
        config.CATEGORY_IMAGES_DIR,
        config.BANNER_IMAGES_DIR,
        config.EXPORTS_DIR,
        config.MONTHLY_EXPORTS_DIR,
        config.BACKUP_DIR,
        config.REVIEWS_DIR,
        config.CHAT_IMAGES_DIR,
    ) = _REAL_DIRS
    Session.logout()
    shutil.rmtree(_TMP, ignore_errors=True)


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.db_file = _TMP / f"{self.id().split('.')[-1]}.db"
        shutil.copy(_TEMPLATE, self.db_file)
        db.DATA_DIR = config.DATA_DIR = _TMP
        db.DB_PATH = config.DB_PATH = self.db_file

        self.sub_dir = _TMP / f"dirs_{self.id().split('.')[-1]}"
        config.SLIPS_DIR = self.sub_dir / "slips"
        config.RECEIPTS_DIR = self.sub_dir / "receipts"
        config.USER_IMAGES_DIR = self.sub_dir / "users"
        config.PRODUCT_IMAGES_DIR = self.sub_dir / "products"
        config.CATEGORY_IMAGES_DIR = self.sub_dir / "categories"
        config.BANNER_IMAGES_DIR = self.sub_dir / "banners"
        config.EXPORTS_DIR = self.sub_dir / "exports"
        config.MONTHLY_EXPORTS_DIR = self.sub_dir / "exports" / "monthly"
        config.BACKUP_DIR = self.sub_dir / "backups"
        config.ensure_dirs()

        from services import otp_service as _otp_svc
        _otp_svc.reset_ip_rate_limits()
        self.app = create_app()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        Session.logout()
        shutil.rmtree(self.sub_dir, ignore_errors=True)

    def make_client(self) -> TestClient:
        return TestClient(self.app)

    def login_client(self, identifier: str, password: str) -> TestClient:
        c = self.make_client()
        r = c.post("/api/auth/login", json={"identifier": identifier, "password": password})
        self.assertEqual(r.status_code, 200, r.text)
        _assert_no_secret_keys(r.json())
        return c


class TestApiWebAndSecurity(ApiTestCase):
    def test_01_guest_access_and_unauthenticated_401(self):
        guest = self.make_client()

        # Bootstrap without cookies -> guest mode
        b = guest.get("/api/bootstrap")
        self.assertEqual(b.status_code, 200)
        b_data = b.json()
        self.assertFalse(b_data["is_authenticated"])
        self.assertTrue(b_data["is_guest"])

        # Guest can browse storefront endpoints
        for url in (
            "/api/home",
            "/api/products",
            "/api/products/filters",
            "/api/products/showcase",
            "/api/products/1",
            "/api/products/1/reviews",
            "/api/products/compare?ids=1,2",
            "/api/products/recommend?level=Advanced&style=attack",
            "/api/categories",
            "/api/brands",
            "/api/coupons/public",
            "/api/banners",
            "/api/settings/shop",
            "/api/settings/contact",
        ):
            res = guest.get(url)
            self.assertEqual(res.status_code, 200, f"Failed on {url}: {res.text}")
            _assert_no_secret_keys(res.json())

        # Guest cannot access buyer account or admin endpoints -> 401
        for url in (
            "/api/cart",
            "/api/wishlist",
            "/api/addresses",
            "/api/orders/my",
            "/api/account/profile",
            "/api/notifications",
            "/api/admin/dashboard",
            "/api/admin/users",
        ):
            res = guest.get(url)
            self.assertEqual(res.status_code, 401, f"Expected 401 on {url}, got {res.status_code}")

    def test_02_concurrent_multi_user_session_isolation(self):
        # Create second buyer
        anon = self.make_client()
        import re as _re
        from unittest.mock import patch as _patch
        with _patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as _m_mail:
            r_start = anon.post("/api/auth/register/start", json={
                "username": "buyer2_iso",
                "email": "buyer2_iso@example.com",
                "password": "Password123",
                "full_name": "ผู้ซื้อ สอง",
                "phone": "0892223333",
                "address_line": "12/3 ถ.พญาไท",
                "district": "ราชเทวี",
                "province": "กรุงเทพมหานคร",
                "postcode": "10400",
            })
            self.assertEqual(r_start.status_code, 200, r_start.text)
            _txt = _m_mail.call_args.args[2] if len(_m_mail.call_args.args) >= 3 else _m_mail.call_args.kwargs.get("text", "")
            otp = _re.search(r"\b(\d{6})\b", _txt).group(1)
        r_ver = anon.post("/api/auth/register/verify", json={
            "email": "buyer2_iso@example.com",
            "otp_code": otp,
        })
        self.assertEqual(r_ver.status_code, 200, r_ver.text)

        client_a = self.login_client("buyer1", "buyer123")
        client_b = self.login_client("buyer2_iso", "Password123")
        client_admin = self.login_client("admin1", "admin123")

        # Interleave requests between A, B, and Admin
        me_a = client_a.get("/api/auth/me").json()["user"]
        me_b = client_b.get("/api/auth/me").json()["user"]
        me_adm = client_admin.get("/api/auth/me").json()["user"]

        self.assertEqual(me_a["username"], "buyer1")
        self.assertEqual(me_b["username"], "buyer2_iso")
        self.assertEqual(me_adm["username"], "admin1")

        # Buyer A adds product 6 (no option) qty 2; Buyer B adds product 1 with its first option qty 1
        p1_opts = client_b.get("/api/products/1").json()["options"]
        ca = client_a.post("/api/cart/items", json={"product_id": 6, "qty": 2})
        self.assertEqual(ca.status_code, 200, ca.text)
        cb = client_b.post("/api/cart/items", json={"product_id": 1, "option_id": p1_opts[0]["id"], "qty": 1})
        self.assertEqual(cb.status_code, 200, cb.text)

        cart_a = client_a.get("/api/cart").json()
        cart_b = client_b.get("/api/cart").json()
        self.assertEqual([i["product_id"] for i in cart_a["items"]], [6])
        self.assertEqual([i["product_id"] for i in cart_b["items"]], [1])

    def test_03_full_e2e_order_payment_shipping_receipt_review_flow(self):
        buyer = self.login_client("buyer1", "buyer123")
        admin = self.login_client("admin1", "admin123")

        # Clear cart & add product 6 (shuttlecock)
        buyer.delete("/api/cart")
        add_res = buyer.post("/api/cart/items", json={"product_id": 6, "qty": 2})
        self.assertEqual(add_res.status_code, 200, add_res.text)

        # Claim public coupon WELCOME10
        pub_coupons = buyer.get("/api/coupons/public").json()
        welcome = next((c for c in pub_coupons if c["code"] == "WELCOME10"), None)
        if welcome and not welcome["is_claimed"]:
            cl = buyer.post("/api/coupons/claim", json={"coupon_id": welcome["id"]})
            self.assertEqual(cl.status_code, 200, cl.text)

        # Preview checkout
        chk = buyer.get("/api/checkout/info?coupon_code=WELCOME10").json()
        self.assertGreater(chk["subtotal"], 0)
        self.assertGreater(chk["discount"], 0)
        addr_id = chk["addresses"][0]["id"]

        # Create order
        ord_res = buyer.post("/api/orders", json={
            "address_id": addr_id,
            "coupon_code": "WELCOME10",
        })
        self.assertEqual(ord_res.status_code, 200, ord_res.text)
        order = ord_res.json()
        order_id = order["id"]
        self.assertEqual(order["status"], "pending")

        # Get payment info & QR image
        pinfo = buyer.get(f"/api/orders/{order_id}/payment-info")
        self.assertEqual(pinfo.status_code, 200)
        qr_res = buyer.get(f"/api/orders/{order_id}/promptpay-qr")
        self.assertEqual(qr_res.status_code, 200)
        self.assertEqual(qr_res.headers["content-type"], "image/png")

        # Upload payment slip
        slip_bytes = _make_png_bytes()
        slip_res = buyer.post(
            f"/api/orders/{order_id}/slip",
            files={"file": ("slip.png", slip_bytes, "image/png")},
        )
        self.assertEqual(slip_res.status_code, 200, slip_res.text)
        self.assertEqual(slip_res.json()["status"], "checking_slip")

        # Admin lists pending payments & views slip image
        pending = admin.get("/api/admin/payments/pending").json()
        pay_entry = next(p for p in pending if p["order_id"] == order_id)
        slip_img_res = admin.get(f"/api/files/slips/{pay_entry['id']}")
        self.assertEqual(slip_img_res.status_code, 200)

        # Admin verifies slip -> status becomes paid
        ver_res = admin.post(f"/api/admin/payments/{pay_entry['id']}/verify")
        self.assertEqual(ver_res.status_code, 200, ver_res.text)
        self.assertEqual(ver_res.json()["status"], "paid")

        # Admin ships order -> status becomes shipped
        ship_res = admin.post(f"/api/admin/orders/{order_id}/ship", json={
            "carrier": "Kerry Express",
            "tracking_no": "KERRY12345678",
        })
        self.assertEqual(ship_res.status_code, 200, ship_res.text)
        self.assertEqual(ship_res.json()["status"], "shipped")

        # Buyer confirms received -> status becomes completed
        rec_res = buyer.post(f"/api/orders/{order_id}/confirm-received")
        self.assertEqual(rec_res.status_code, 200, rec_res.text)
        self.assertEqual(rec_res.json()["status"], "completed")

        # Buyer downloads PDF receipt
        pdf_res = buyer.get(f"/api/orders/{order_id}/receipt.pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_res.content.startswith(b"%PDF"))

        # Buyer writes review for product 6
        can_rev = buyer.get(f"/api/reviews/can-review?product_id=6&order_id={order_id}").json()
        self.assertTrue(can_rev["can_review"])
        rev_res = buyer.post("/api/reviews", json={
            "product_id": 6,
            "order_id": order_id,
            "rating": 5,
            "comment": "ลูกแบดคุณภาพดีมาก จัดส่งไว",
        })
        self.assertEqual(rev_res.status_code, 200, rev_res.text)
        self.assertEqual(rev_res.json()["rating"], 5)

    def test_04_role_permissions_idor_csrf_and_idle_lock(self):
        buyer1 = self.login_client("buyer1", "buyer123")
        admin = self.login_client("admin1", "admin123")
        owner = self.login_client("owner", "owner123")

        # 1. Dashboard revenue: Admin sees None, Owner sees float
        adm_dash = admin.get("/api/admin/dashboard").json()
        own_dash = owner.get("/api/admin/dashboard").json()
        self.assertFalse(adm_dash["can_view_revenue"])
        self.assertIsNone(adm_dash["revenue_total"])
        self.assertTrue(own_dash["can_view_revenue"])
        self.assertIsNotNone(own_dash["revenue_total"])

        # 2. Admin blocked from Owner-only endpoints (403)
        for url in (
            "/api/admin/users",
            "/api/admin/coupons",
            "/api/admin/expenses",
            "/api/admin/backups",
            "/api/admin/audit-logs",
        ):
            r = admin.get(url)
            self.assertEqual(r.status_code, 403, f"Admin should get 403 on {url}, got {r.status_code}")

        # 3. Owner can manage users, settings, expenses, export xlsx, backups, audit logs
        users_res = owner.get("/api/admin/users")
        self.assertEqual(users_res.status_code, 200)
        _assert_no_secret_keys(users_res.json())

        u_detail = owner.get("/api/admin/users/3")
        self.assertEqual(u_detail.status_code, 200)
        _assert_no_secret_keys(u_detail.json())

        exp_res = owner.post("/api/admin/expenses", json={
            "spent_on": "2026-10-15",
            "category": "ค่าเช่าร้าน",
            "amount": 8500,
            "note": "ค่าเช่าเดือนตุลาคม",
        })
        self.assertEqual(exp_res.status_code, 200, exp_res.text)

        xlsx_res = owner.post("/api/admin/export/xlsx", json={
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        })
        self.assertEqual(xlsx_res.status_code, 200, xlsx_res.text)
        dl_url = xlsx_res.json()["download_url"]
        dl_res = owner.get(dl_url)
        self.assertEqual(dl_res.status_code, 200)

        bkp_res = owner.post("/api/admin/backups")
        self.assertEqual(bkp_res.status_code, 200, bkp_res.text)

        # 4. IDOR protection: create another buyer and try to access buyer1's order/slip
        buyer1.delete("/api/cart")
        buyer1.post("/api/cart/items", json={"product_id": 6, "qty": 1})
        addr1 = buyer1.get("/api/addresses").json()[0]["id"]
        o1 = buyer1.post("/api/orders", json={"address_id": addr1}).json()
        buyer1.post(
            f"/api/orders/{o1['id']}/slip",
            files={"file": ("slip.png", _make_png_bytes(), "image/png")},
        )

        # Register & login attacker buyer
        import re as _re
        from unittest.mock import patch as _patch
        att = self.make_client()
        with _patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as _m_mail:
            st = att.post("/api/auth/register/start", json={
                "username": "attacker1",
                "email": "attacker1@example.com",
                "password": "Password123",
                "full_name": "ผู้ไม่หวังดี",
                "phone": "0897778888",
                "address_line": "1/1 ถ.ทดสอบ",
                "district": "เมือง",
                "province": "กรุงเทพมหานคร",
                "postcode": "10110",
            })
            self.assertEqual(st.status_code, 200, st.text)
            _txt = _m_mail.call_args.args[2] if len(_m_mail.call_args.args) >= 3 else _m_mail.call_args.kwargs.get("text", "")
            _att_otp = _re.search(r"\b(\d{6})\b", _txt).group(1)
            att.post("/api/auth/register/verify", json={"email": "attacker1@example.com", "otp_code": _att_otp})
        attacker = self.login_client("attacker1", "Password123")

        self.assertEqual(attacker.get(f"/api/orders/{o1['id']}").status_code, 403)
        self.assertEqual(attacker.get(f"/api/orders/{o1['id']}/slip-image").status_code, 403)
        self.assertEqual(attacker.get(f"/api/orders/{o1['id']}/receipt.pdf").status_code, 403)
        self.assertEqual(attacker.put(f"/api/addresses/{addr1}", json={
            "recipient": "Hack", "phone": "0897778888", "address_line": "x",
            "district": "x", "province": "x", "postcode": "10110",
        }).status_code, 400)

        # 5. CSRF Origin Mismatch protection
        csrf_res = buyer1.post(
            "/api/cart/items",
            json={"product_id": 6, "qty": 1},
            headers={"Origin": "https://evil-attacker.example.com"},
        )
        self.assertEqual(csrf_res.status_code, 403)

        # 6. Staff Idle Lock enforcement
        lock_res = admin.post("/api/auth/lock")
        self.assertEqual(lock_res.status_code, 200)
        self.assertTrue(lock_res.json()["is_locked"])

        blocked_res = admin.get("/api/admin/dashboard")
        self.assertEqual(blocked_res.status_code, 423)
        self.assertTrue(blocked_res.json().get("locked"))

        bad_unlock = admin.post("/api/auth/unlock", json={"password": "wrongpassword"})
        self.assertEqual(bad_unlock.status_code, 400)

        ok_unlock = admin.post("/api/auth/unlock", json={"password": "admin123"})
        self.assertEqual(ok_unlock.status_code, 200)
        self.assertFalse(ok_unlock.json()["is_locked"])

        after_unlock = admin.get("/api/admin/dashboard")
        self.assertEqual(after_unlock.status_code, 200)


    def test_05_all_remaining_endpoints_products_categories_coupons_chat_notifications_uploads(self):
        buyer = self.login_client("buyer1", "buyer123")
        admin = self.login_client("admin1", "admin123")
        owner = self.login_client("owner", "owner123")

        # 1. Profile & Email OTP change & Wishlist
        prof = buyer.get("/api/account/profile").json()
        self.assertEqual(prof["username"], "buyer1")
        # ต้องยืนยันรหัสผ่านปัจจุบันเมื่อบันทึกโปรไฟล์ (ไม่ส่งหรือส่งผิดต้องถูกปฏิเสธ 400)
        no_pw_prof = buyer.put("/api/account/profile", json={
            "full_name": "ผู้ซื้อ ทดสอบเว็บ",
            "phone": "0833334444",
            "username": "buyer1_web",
        })
        self.assertEqual(no_pw_prof.status_code, 400)
        wrong_pw_prof = buyer.put("/api/account/profile", json={
            "full_name": "ผู้ซื้อ ทดสอบเว็บ",
            "phone": "0833334444",
            "username": "buyer1_web",
            "current_password": "wrongpassword",
        })
        self.assertEqual(wrong_pw_prof.status_code, 400)

        up_prof = buyer.put("/api/account/profile", json={
            "full_name": "ผู้ซื้อ ทดสอบเว็บ",
            "phone": "0833334444",
            "username": "buyer1_web",
            "current_password": "buyer123",
        })
        self.assertEqual(up_prof.status_code, 200, up_prof.text)
        self.assertEqual(up_prof.json()["user"]["username"], "buyer1_web")

        import re as _re
        from unittest.mock import patch as _patch
        with _patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as _m_mail:
            otp_req = buyer.post("/api/account/email/request-otp", json={"new_email": "buyer1_web@example.com"})
            self.assertEqual(otp_req.status_code, 200, otp_req.text)
            _txt = _m_mail.call_args.args[2] if len(_m_mail.call_args.args) >= 3 else _m_mail.call_args.kwargs.get("text", "")
            email_otp = _re.search(r"\b(\d{6})\b", _txt).group(1)
        otp_conf = buyer.post("/api/account/email/confirm-otp", json={
            "new_email": "buyer1_web@example.com",
            "otp_code": email_otp,
        })
        self.assertEqual(otp_conf.status_code, 200, otp_conf.text)
        self.assertEqual(otp_conf.json()["user"]["email"], "buyer1_web@example.com")

        w_tog = buyer.post("/api/wishlist/toggle", json={"product_id": 1})
        self.assertEqual(w_tog.status_code, 200)
        self.assertTrue(w_tog.json()["in_wishlist"])
        w_list = buyer.get("/api/wishlist").json()
        self.assertTrue(any(p["id"] == 1 for p in w_list))

        # 2. Notifications & Chat (Quick reply + AI + Racket recommendation + Staff reply)
        notis = buyer.get("/api/notifications").json()
        self.assertIn("items", notis)
        buyer.post("/api/notifications/read-all")

        qrs = buyer.get("/api/chat/quick-replies").json()
        self.assertGreaterEqual(len(qrs), 6)
        qr_ans = buyer.post("/api/chat/quick-reply", json={"reply_id": "best_sellers"})
        self.assertEqual(qr_ans.status_code, 200, qr_ans.text)

        chat_msg = buyer.post("/api/chat/messages", json={"text": "แนะนำไม้แบดหน่อยครับ", "force_ai": True})
        self.assertEqual(chat_msg.status_code, 200, chat_msg.text)

        rec_chat = buyer.post("/api/chat/recommend-rackets", json={
            "level": "Intermediate",
            "style": "attack",
            "budget": 5000,
        })
        self.assertEqual(rec_chat.status_code, 200, rec_chat.text)
        self.assertGreaterEqual(len(rec_chat.json()["rackets"]), 1)

        threads = admin.get("/api/admin/chat/threads").json()["threads"]
        self.assertGreaterEqual(len(threads), 1)
        s_rep = admin.post("/api/admin/chat/reply", json={
            "customer_id": up_prof.json()["user"]["id"],
            "text": "สวัสดีครับ แอดมินพร้อมดูแลครับ",
        })
        self.assertEqual(s_rep.status_code, 200, s_rep.text)

        # 3. Admin & Owner Product CRUD, Options, Images, Addons, Soft Delete & Restore
        meta = admin.get("/api/admin/products/form-meta").json()
        cat_id = meta["categories"][0]["id"]
        brand_id = meta["brands"][0]["id"]

        # Admin can create product, but cannot change existing product price
        new_prod = admin.post("/api/admin/products", json={
            "category_id": cat_id,
            "brand_id": brand_id,
            "name": "ไม้แบดทดสอบ API",
            "description": "คำอธิบายทดสอบ",
            "price": 2500,
            "stock": 10,
            "weight_class": "4U",
            "balance": "Heavy Head",
            "flex": "Medium",
            "level": "Intermediate",
            "spec_balance_mm": "302 mm",
        })
        self.assertEqual(new_prod.status_code, 200, new_prod.text)
        pid = new_prod.json()["id"]

        # Admin trying to change price -> 403
        adm_price_chg = admin.put(f"/api/admin/products/{pid}", json={"price": 1990})
        self.assertEqual(adm_price_chg.status_code, 403)

        # Owner can change price & sale_price
        own_price_chg = owner.put(f"/api/admin/products/{pid}", json={"price": 2400, "sale_price": 1990})
        self.assertEqual(own_price_chg.status_code, 200, own_price_chg.text)
        self.assertEqual(own_price_chg.json()["sale_price"], 1990.0)

        # Upload image & attach to product
        up_img = admin.post(
            "/api/uploads/image",
            data={"target": "product"},
            files={"file": ("racket.png", _make_png_bytes(), "image/png")},
        )
        self.assertEqual(up_img.status_code, 200, up_img.text)
        img_path = up_img.json()["path"]

        # Invalid image upload rejected (400)
        bad_img = admin.post(
            "/api/uploads/image",
            data={"target": "product"},
            files={"file": ("evil.txt", b"not-an-image", "text/plain")},
        )
        self.assertEqual(bad_img.status_code, 400)

        add_im = admin.post(f"/api/admin/products/{pid}/images", json={
            "path": img_path, "color_value": "แดง", "is_primary": True,
        })
        self.assertEqual(add_im.status_code, 200, add_im.text)

        # Add option & addon
        add_opt = admin.post(f"/api/admin/products/{pid}/options", json={
            "option_type": "สี", "option_value": "แดง", "extra_price": 0, "stock": 5,
        })
        self.assertEqual(add_opt.status_code, 200, add_opt.text)

        set_add = admin.put(f"/api/admin/products/{pid}/addons", json={"addon_ids": [6]})
        self.assertEqual(set_add.status_code, 200, set_add.text)

        # Soft delete & restore (Owner only)
        self.assertEqual(admin.delete(f"/api/admin/products/{pid}").status_code, 403)
        self.assertEqual(owner.delete(f"/api/admin/products/{pid}").status_code, 200)
        self.assertEqual(owner.post(f"/api/admin/products/{pid}/restore").status_code, 200)

        # 4. Categories, Brands, Option Groups, Coupons, Banners, Settings
        cat_res = owner.post("/api/admin/categories", json={"name": "หมวดทดสอบ API", "all_brands": True})
        self.assertEqual(cat_res.status_code, 200, cat_res.text)
        new_cid = cat_res.json()["id"]

        qw_res = owner.post(f"/api/admin/categories/{new_cid}/quick-weights")
        self.assertEqual(qw_res.status_code, 200, qw_res.text)

        cp_res = owner.post("/api/admin/coupons", json={
            "code": "WEBAPI99",
            "discount_type": "fixed",
            "value": 99,
            "min_order": 500,
            "coupon_category": "fixed",
        })
        self.assertEqual(cp_res.status_code, 200, cp_res.text)
        cp_id = cp_res.json()["id"]
        self.assertEqual(owner.post(f"/api/admin/coupons/{cp_id}/toggle").status_code, 200)
        self.assertEqual(owner.delete(f"/api/admin/coupons/{cp_id}").status_code, 200)

        rule_res = owner.post("/api/admin/coupon-rules", json={
            "name": "ซื้อครบ 4000 ลด 10%",
            "min_order_trigger": 4000,
            "discount_type": "percent",
            "discount_value": 10,
            "min_order_next": 1000,
            "valid_days": 30,
        })
        self.assertEqual(rule_res.status_code, 200, rule_res.text)

        ban_res = owner.post("/api/admin/banners", json={
            "title": "แบนเนอร์ทดสอบ API",
            "subtitle": "ลดราคาพิเศษ",
            "link_url": "/category",
            "is_active": True,
        })
        self.assertEqual(ban_res.status_code, 200, ban_res.text)

        set_res = owner.put("/api/admin/settings", json={"shop_name": "AI.HERE BADᴍᴛ-Zone Web"})
        self.assertEqual(set_res.status_code, 200, set_res.text)
        self.assertEqual(set_res.json()["shop"]["shop_name"], "AI.HERE BADᴍᴛ-Zone Web")

    def test_06_reviews_media_option_label_chat_images_address_validation_and_shop_name(self):
        buyer = self.login_client("buyer1", "buyer123")
        admin = self.login_client("admin1", "admin123")
        owner = self.login_client("owner", "owner123")

        # 1. Dynamic shop_name with superscripts (exact character preservation)
        special_name = "Ai.HRER BADᴹᵀ Zone"
        s_res = owner.put("/api/admin/settings", json={"shop_name": special_name})
        self.assertEqual(s_res.status_code, 200, s_res.text)
        self.assertEqual(s_res.json()["shop"]["shop_name"], special_name)
        home_res = buyer.get("/api/home").json()
        self.assertEqual(home_res["shop"]["shop_name"], special_name)
        self.assertEqual(len(home_res["best_sellers"]), 15)

        # 2. Real-time shipping address validation endpoint
        addr_val = buyer.post("/api/addresses/validate", json={
            "recipient": "ก",
            "phone": "12345",
            "address_line": "12",
            "district": "",
            "province": "",
            "postcode": "12A",
        })
        self.assertEqual(addr_val.status_code, 200, addr_val.text)
        v_body = addr_val.json()
        self.assertFalse(v_body["valid"])
        self.assertIn("recipient", v_body["errors"])
        self.assertIn("phone", v_body["errors"])
        self.assertIn("address_line", v_body["errors"])
        self.assertIn("district", v_body["errors"])
        self.assertIn("province", v_body["errors"])
        self.assertIn("postcode", v_body["errors"])

        # 3. Chat image upload & sending for Buyer, Admin, and Owner
        up_chat_b = buyer.post(
            "/api/chat/upload-image",
            files={"file": ("buyer_photo.png", _make_png_bytes((20, 120, 220)), "image/png")},
        )
        self.assertEqual(up_chat_b.status_code, 200, up_chat_b.text)
        b_img_path = up_chat_b.json()["path"]

        b_msg = buyer.post("/api/chat/messages", json={
            "text": "ส่งรูปไม้แบดให้ดูครับ",
            "image_path": b_img_path,
        })
        self.assertEqual(b_msg.status_code, 200, b_msg.text)
        self.assertEqual(b_msg.json()["message"]["image_path"], b_img_path)

        # Image-only message from Admin
        up_chat_a = admin.post(
            "/api/chat/upload-image",
            files={"file": ("admin_photo.png", _make_png_bytes((40, 180, 90)), "image/png")},
        )
        self.assertEqual(up_chat_a.status_code, 200, up_chat_a.text)
        a_img_path = up_chat_a.json()["path"]

        buyer_uid = buyer.get("/api/account/profile").json()["id"]
        a_rep = admin.post("/api/admin/chat/reply", json={
            "customer_id": buyer_uid,
            "text": "",
            "image_path": a_img_path,
        })
        self.assertEqual(a_rep.status_code, 200, a_rep.text)
        self.assertEqual(a_rep.json()["message"]["image_path"], a_img_path)

        # Owner can also send image in chat
        o_rep = owner.post("/api/admin/chat/reply", json={
            "customer_id": buyer_uid,
            "text": "เจ้าของร้านส่งรูปเพิ่มเติมครับ",
            "image_path": a_img_path,
        })
        self.assertEqual(o_rep.status_code, 200, o_rep.text)

        # 4. Complete an order with a specific option_id and test Review Media (0-5 files) + option_label
        prod1 = buyer.get("/api/products/1").json()
        opt_id = prod1["options"][0]["id"] if prod1.get("options") else None
        opt_val = prod1["options"][0]["option_value"] if prod1.get("options") else ""
        buyer.post("/api/cart/items", json={"product_id": 1, "option_id": opt_id, "qty": 1})
        addrs = buyer.get("/api/addresses").json()
        ord_res = buyer.post("/api/orders", json={"address_id": addrs[0]["id"]})
        self.assertEqual(ord_res.status_code, 200, ord_res.text)
        oid = ord_res.json()["id"]

        buyer.post(
            f"/api/orders/{oid}/slip",
            files={"file": ("slip.png", _make_png_bytes(), "image/png")},
        )
        pend = admin.get("/api/admin/payments/pending").json()
        pay_id = next(p["id"] for p in pend if p["order_id"] == oid)
        admin.post(f"/api/admin/payments/{pay_id}/verify")
        admin.post(f"/api/admin/orders/{oid}/ship", json={"carrier": "Kerry Express", "tracking_no": "KER999888777"})
        buyer.post(f"/api/orders/{oid}/confirm-received")

        # Verify awaiting_review_count in /api/orders/my
        my_orders = buyer.get("/api/orders/my", params={"status": "completed"}).json()["items"]
        comp_ord = next(o for o in my_orders if o["id"] == oid)
        self.assertGreaterEqual(comp_ord["awaiting_review_count"], 1)

        # Reject > 5 files on POST /api/reviews
        png_bytes = _make_png_bytes()
        six_files = [("files", (f"img_{i}.png", png_bytes, "image/png")) for i in range(6)]
        too_many = buyer.post(
            "/api/reviews",
            data={"product_id": "1", "order_id": str(oid), "rating": "5", "comment": "เกิน 5 ไฟล์"},
            files=six_files,
        )
        self.assertEqual(too_many.status_code, 400)

        # Reject invalid file type / corrupted video magic bytes
        bad_vid = buyer.post(
            "/api/reviews",
            data={"product_id": "1", "order_id": str(oid), "rating": "5", "comment": "ไฟล์ปลอม"},
            files=[("files", ("fake.mp4", b"not-a-valid-mp4-header", "video/mp4"))],
        )
        self.assertEqual(bad_vid.status_code, 400)

        # Valid multipart review with 1 image + 1 MP4 video
        valid_mp4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + (b"\x00" * 64)
        ok_rev = buyer.post(
            "/api/reviews",
            data={"product_id": "1", "order_id": str(oid), "rating": "5", "comment": "ไม้ตีดีมาก แนบรูปและวิดีโอ"},
            files=[
                ("files", ("photo1.png", png_bytes, "image/png")),
                ("files", ("clip1.mp4", valid_mp4, "video/mp4")),
            ],
        )
        self.assertEqual(ok_rev.status_code, 200, ok_rev.text)
        rev_body = ok_rev.json()
        self.assertEqual(len(rev_body["media"]), 2)
        if opt_val:
            self.assertIn(opt_val, rev_body["option_label"])

        # Product reviews endpoint returns media and option_label
        prod_revs = buyer.get("/api/products/1/reviews").json()["items"]
        latest_rev = next(r for r in prod_revs if r["id"] == rev_body["id"])
        self.assertEqual(len(latest_rev["media"]), 2)
        self.assertEqual({m["kind"] for m in latest_rev["media"]}, {"image", "video"})

        # 5. Test skip-review (/api/reviews/skip) removes completed order from to_review tab without affecting product ratings
        prod2 = buyer.get("/api/products/2").json()
        opt2_id = prod2["options"][0]["id"] if prod2.get("options") else None
        buyer.post("/api/cart/items", json={"product_id": 2, "option_id": opt2_id, "qty": 1})
        ord2_res = buyer.post("/api/orders", json={"address_id": addrs[0]["id"]})
        self.assertEqual(ord2_res.status_code, 200, ord2_res.text)
        oid2 = ord2_res.json()["id"]
        buyer.post(f"/api/orders/{oid2}/slip", files={"file": ("slip2.png", png_bytes, "image/png")})
        pend2 = admin.get("/api/admin/payments/pending").json()
        pay2_id = next(p["id"] for p in pend2 if p["order_id"] == oid2)
        admin.post(f"/api/admin/payments/{pay2_id}/verify")
        admin.post(f"/api/admin/orders/{oid2}/ship", json={"carrier": "Flash Express", "tracking_no": "TH123456789"})
        buyer.post(f"/api/orders/{oid2}/confirm-received")

        to_rev_before = buyer.get("/api/orders/my", params={"status": "to_review"}).json()
        self.assertTrue(any(o["id"] == oid2 for o in to_rev_before["items"]))

        skip_res = buyer.post("/api/reviews/skip", json={"order_id": oid2})
        self.assertEqual(skip_res.status_code, 200, skip_res.text)
        self.assertTrue(skip_res.json().get("ok"))

        to_rev_after = buyer.get("/api/orders/my", params={"status": "to_review"}).json()
        self.assertFalse(any(o["id"] == oid2 for o in to_rev_after["items"]))
        ord2_detail = buyer.get(f"/api/orders/{oid2}").json()
        self.assertEqual(ord2_detail.get("awaiting_review_count"), 0)
        if opt_val:
            self.assertIn(opt_val, latest_rev["option_label"])



    def test_07_otp_security_and_html_email_comprehensive(self):
        """ทดสอบความปลอดภัยของระบบ OTP ทั้งหมดและอีเมล HTML สองภาษาตามข้อกำหนด"""
        import io
        import logging
        import re
        from datetime import datetime, timedelta
        from unittest.mock import MagicMock, patch
        from database import repo_otp, repo_users
        from services import auth_service, email_service, otp_service

        def _extract_otp(mock_send_mail) -> str:
            self.assertTrue(mock_send_mail.called)
            args, kwargs = mock_send_mail.call_args
            text = args[2] if len(args) >= 3 else kwargs.get("text", "")
            m = re.search(r"\b(\d{6})\b", str(text))
            self.assertIsNotNone(m)
            return m.group(1)

        # 1. ส่งไม่สำเร็จหรือยังไม่ได้ตั้งค่า SMTP ต้องไม่เหลือ OTP ค้างในฐานข้อมูล และไม่รั่วรหัสผ่าน SMTP
        email_fail = "fail_smtp@example.com"
        with patch.object(config, "SMTP_USER", ""), patch.object(config, "SMTP_PASSWORD", ""):
            with self.assertRaises(ValueError) as ctx:
                auth_service.register_start(email_fail, "Password123", "ผู้ใช้ ทดสอบ")
            self.assertIn("ส่งอีเมล", str(ctx.exception))
            self.assertIsNone(repo_otp.get_latest_active_otp(email_fail, "register"))
            self.assertIsNone(repo_otp.get_latest_otp_any(email_fail, "register"))

        secret_smtp_pw = "super_secret_app_pw_16"
        with (
            patch.object(config, "SMTP_HOST", "smtp.gmail.com"),
            patch.object(config, "SMTP_PORT", 587),
            patch.object(config, "SMTP_USER", "sender@gmail.com"),
            patch.object(config, "SMTP_PASSWORD", secret_smtp_pw),
            patch("services.email_service._send_via_smtp", side_effect=RuntimeError(f"Auth failed for {secret_smtp_pw}")),
        ):
            with self.assertRaises(ValueError) as ctx2:
                auth_service.register_start(email_fail, "Password123", "ผู้ใช้ ทดสอบ")
            err_msg = str(ctx2.exception)
            self.assertNotIn(secret_smtp_pw, err_msg)
            self.assertNotIn("RuntimeError", err_msg)
            self.assertIsNone(repo_otp.get_latest_active_otp(email_fail, "register"))
            self.assertIsNone(repo_otp.get_latest_otp_any(email_fail, "register"))

        buyer1_row = repo_users.get_by_username("buyer1")
        Session.login(dict(buyer1_row))
        with patch("services.email_service.send_mail", side_effect=ValueError("ส่งอีเมลไม่สำเร็จ")):
            with self.assertRaises(ValueError):
                auth_service.request_email_change_otp(buyer1_row["id"], "new_fail@example.com")
            self.assertIsNone(repo_otp.get_latest_active_email_change_otp(buyer1_row["id"], "new_fail@example.com"))
            self.assertIsNone(repo_otp.get_latest_email_change_otp_any(buyer1_row["id"]))
        Session.logout()

        # 2. กรอกรหัส OTP ผิดครบ 5 ครั้งถูกยกเลิกทันที
        email_brute = "brute@example.com"
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail:
            auth_service.register_start(email_brute, "Password123", "ทดสอบ เดาผิด")
            real_code = _extract_otp(m_mail)
        wrong_code = "000000" if real_code != "000000" else "999999"
        for attempt in range(1, 5):
            with self.assertRaises(ValueError) as ctx_b:
                auth_service.register_verify(email_brute, wrong_code)
            self.assertIn(f"ลองได้อีก {5 - attempt} ครั้ง", str(ctx_b.exception))
        with self.assertRaises(ValueError) as ctx_b5:
            auth_service.register_verify(email_brute, wrong_code)
        self.assertIn("ครบ 5 ครั้ง", str(ctx_b5.exception))
        with self.assertRaises(ValueError):
            auth_service.register_verify(email_brute, real_code)

        # 3. รหัส OTP หมดอายุแล้ว (> 10 นาที) ถูกปฏิเสธ
        email_exp = "expired@example.com"
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail:
            auth_service.register_start(email_exp, "Password123", "ทดสอบ หมดอายุ")
            exp_code = _extract_otp(m_mail)
        row_exp = repo_otp.get_latest_active_otp(email_exp, "register")
        past_str = (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
        with db.get_db() as conn:
            conn.execute("UPDATE email_otps SET expires_at = ? WHERE id = ?", (past_str, row_exp["id"]))
        with self.assertRaisesRegex(ValueError, "หมดอายุ"):
            otp_service.verify_otp(email_exp, "register", exp_code)

        # 4. ใช้ซ้ำไม่ได้ และป้องกัน race condition (atomic mark_used)
        email_single = "singleuse@example.com"
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail:
            otp_service.generate_and_send_otp(email_single, purpose="register", check_cooldown=False)
            single_code = _extract_otp(m_mail)
        self.assertTrue(otp_service.verify_otp(email_single, "register", single_code))
        with self.assertRaises(ValueError):
            otp_service.verify_otp(email_single, "register", single_code)

        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}):
            otp_service.generate_and_send_otp(email_single, purpose="register", check_cooldown=False)
        row_race = repo_otp.get_latest_active_otp(email_single, "register")
        atomic_results = [repo_otp.mark_used(row_race["id"]) for _ in range(5)]
        self.assertEqual(atomic_results.count(True), 1)
        self.assertEqual(atomic_results.count(False), 4)

        # 5. ใช้ข้าม purpose ไม่ได้ และ OTP เปลี่ยนอีเมลผูกกับ user_id + new_email เท่านั้น
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail:
            otp_service.generate_and_send_otp(buyer1_row["email"], purpose="reset", check_cooldown=False)
            rst_code = _extract_otp(m_mail)
        with self.assertRaises(ValueError):
            otp_service.verify_otp(buyer1_row["email"], "register", rst_code)

        Session.login(dict(buyer1_row))
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail2:
            auth_service.request_email_change_otp(buyer1_row["id"], "target_new@example.com", check_cooldown=False)
            chg_code = _extract_otp(m_mail2)
        with self.assertRaises(ValueError):
            auth_service.confirm_email_change_with_otp(buyer1_row["id"], "wrong_new@example.com", chg_code)
        admin1_row = repo_users.get_by_username("admin1")
        Session.login(dict(admin1_row))
        with self.assertRaises(ValueError):
            auth_service.confirm_email_change_with_otp(admin1_row["id"], "target_new@example.com", chg_code)
        Session.login(dict(buyer1_row))
        upd_u = auth_service.confirm_email_change_with_otp(buyer1_row["id"], "target_new@example.com", chg_code)
        self.assertEqual(upd_u["email"], "target_new@example.com")
        # เปลี่ยนกลับเป็น buyer@shop.com
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail3:
            auth_service.request_email_change_otp(buyer1_row["id"], "buyer@shop.com", check_cooldown=False)
            back_code = _extract_otp(m_mail3)
        auth_service.confirm_email_change_with_otp(buyer1_row["id"], "buyer@shop.com", back_code)
        Session.logout()

        # 6. ขอรหัสใหม่แล้วรหัสเก่าใช้ไม่ได้ + ส่งซ้ำก่อน 60 วินาทีถูกปฏิเสธ + เกิน 5 ครั้งต่อชั่วโมงถูกปฏิเสธ
        email_rate = "rate_test@example.com"
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail:
            auth_service.register_start(email_rate, "Password123", "ผู้ใช้ ทดสอบ")
            code_old = _extract_otp(m_mail)
            # ส่งซ้ำทันทีก่อน 60 วินาที -> ถูกปฏิเสธ
            with self.assertRaisesRegex(ValueError, "วินาที"):
                auth_service.resend_register_otp(email_rate)

            row_old = repo_otp.get_latest_active_otp(email_rate, "register")
            older_ts = (datetime.now() - timedelta(seconds=65)).strftime("%Y-%m-%d %H:%M:%S")
            with db.get_db() as conn:
                conn.execute("UPDATE email_otps SET created_at = ? WHERE id = ?", (older_ts, row_old["id"]))

            auth_service.resend_register_otp(email_rate)
            code_new = _extract_otp(m_mail)

            if code_old != code_new:
                with self.assertRaises(ValueError):
                    otp_service.verify_otp(email_rate, "register", code_old)

            # ออกเพิ่มจนครบ 5 ครั้งในชั่วโมงเดียวกัน (รวม 2 ครั้งก่อนหน้า + 3 ครั้ง = 5 ครั้ง)
            for _ in range(3):
                otp_service.generate_and_send_otp(email_rate, purpose="register", check_cooldown=False)

            # ครั้งที่ 6 ใน 1 ชั่วโมง -> ถูกปฏิเสธ
            with self.assertRaisesRegex(ValueError, "5 ครั้งต่อชั่วโมง"):
                otp_service.generate_and_send_otp(email_rate, purpose="register", check_cooldown=False)

        # 7. ข้อความลืมรหัสผ่านเหมือนกันทั้งกรณีมีและไม่มีอีเมล + ยกเลิกเซสชันเดิมหลังรีเซ็ตสำเร็จ
        otp_service.reset_ip_rate_limits()
        with db.get_db() as conn:
            conn.execute("DELETE FROM email_otps WHERE email = 'buyer@shop.com' AND purpose = 'reset'")
        c_anon = self.make_client()
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail:
            r_exist = c_anon.post("/api/auth/reset/start", json={"email": "buyer@shop.com"})
            r_no = c_anon.post("/api/auth/reset/start", json={"email": "nobody_999@shop.com"})
            self.assertEqual(r_exist.status_code, 200)
            self.assertEqual(r_no.status_code, 200)
            b_exist, b_no = r_exist.json(), r_no.json()
            self.assertEqual(set(b_exist.keys()), set(b_no.keys()))
            self.assertEqual(b_exist["mode"], b_no["mode"])
            self.assertIn(auth_service.RESET_GENERIC_NOTICE, b_exist["message"])
            self.assertIn(auth_service.RESET_GENERIC_NOTICE, b_no["message"])
            self.assertEqual(m_mail.call_count, 1)
            reset_otp_code = _extract_otp(m_mail)

        c_buyer_sess = self.login_client("buyer1", "buyer123")
        self.assertEqual(c_buyer_sess.get("/api/orders/my").status_code, 200)
        ver_r = c_anon.post("/api/auth/reset/verify", json={
            "email": "buyer@shop.com",
            "otp_code": reset_otp_code,
            "new_password": "NewPassword999",
        })
        self.assertEqual(ver_r.status_code, 200, ver_r.text)
        # เซสชันเดิมของ buyer ต้องถูกเตะออกทันที (401)
        self.assertEqual(c_buyer_sess.get("/api/orders/my").status_code, 401)

        # 8. Rate limit ต่อ IP ตอบ HTTP 429 พร้อมข้อความไทยเมื่อเกิน 10 ครั้งใน 10 นาที
        otp_service.reset_ip_rate_limits()
        with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}):
            for i in range(10):
                r_ok = c_anon.post("/api/auth/reset/start", json={"email": f"ip_user_{i}@example.com"})
                self.assertEqual(r_ok.status_code, 200)
            r_429 = c_anon.post("/api/auth/reset/start", json={"email": "ip_user_11@example.com"})
            self.assertEqual(r_429.status_code, 429)
            self.assertIn("บ่อยเกินไป", r_429.json().get("detail", ""))
        otp_service.reset_ip_rate_limits()

        # 9. เทมเพลต HTML อีเมลมีรหัสและ escape ถูกต้อง + รองรับพอร์ต 587 (STARTTLS) และ 465 (SSL) + ไม่มีรหัส OTP ใน log/outbox/response
        malicious_shop = "<script>alert(1)</script> & Shop"
        malicious_user = "<img src=x onerror=alert(1)>สมชาย"
        for p_kind in ("register", "reset", "email_change"):
            subj, txt, html_body = otp_service.build_otp_email_content(
                purpose=p_kind,
                code="654321",
                shop_name=malicious_shop,
                recipient_name=malicious_user,
                expires_in_minutes=10,
                expires_at="2026-10-27 21:00:00",
                target_email="user@example.com",
            )
            self.assertIn("|", subj)
            self.assertIn("654321", txt)
            self.assertIn("654321", html_body)
            self.assertIn("<table", html_body)
            self.assertIn("#FFD600", html_body)
            self.assertIn("#141619", html_body)
            self.assertIn("อย่าบอกรหัสนี้กับใคร", html_body)
            self.assertIn("Never share this code", html_body)
            self.assertNotIn("<script>", html_body)
            self.assertNotIn("<img src=x", html_body)
            self.assertIn("&lt;script&gt;", html_body)

        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        try:
            with patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as m_mail:
                res_nolog = c_anon.post("/api/auth/register/start", json={
                    "username": "nolog_user",
                    "email": "nolog_user@example.com",
                    "password": "Password123",
                    "full_name": "ผู้ใช้ ไม่รั่ว",
                })
                self.assertEqual(res_nolog.status_code, 200)
                code_nolog = _extract_otp(m_mail)
                self.assertNotIn(code_nolog, res_nolog.text)
                self.assertNotIn(code_nolog, log_stream.getvalue())
                with db.get_db() as conn:
                    for ob in conn.execute("SELECT * FROM email_outbox").fetchall():
                        self.assertNotIn(code_nolog, str(dict(ob)))
        finally:
            root_logger.removeHandler(handler)

        with (
            patch.object(config, "SMTP_HOST", "smtp.gmail.com"),
            patch.object(config, "SMTP_PORT", 465),
            patch.object(config, "SMTP_USER", "shop@gmail.com"),
            patch.object(config, "SMTP_PASSWORD", "abcdefghijklmnop"),
            patch("smtplib.SMTP_SSL") as mock_ssl,
        ):
            ssl_inst = MagicMock()
            mock_ssl.return_value.__enter__.return_value = ssl_inst
            r465 = email_service.send_mail("buyer@shop.com", "SSL Subject", "SSL Body", html="<p>SSL</p>")
            self.assertTrue(r465["sent"])
            ssl_inst.login.assert_called_once_with("shop@gmail.com", "abcdefghijklmnop")


if __name__ == "__main__":
    unittest.main()
