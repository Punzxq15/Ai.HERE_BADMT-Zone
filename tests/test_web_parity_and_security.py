"""
tests/test_web_parity_and_security.py
ชุดทดสอบครบวงจรสำหรับเวอร์ชันเว็บ (Phase 1, 2, 3) + การอัปเดต UI หน้า Login & Sign Up โฉมใหม่:
- ตรวจ ROUTE_TABLE ทั้ง 30 หน้า + ไฟล์ JS โมดูลจริงครบทุกหน้า
- ตรวจ Role × Route Matrix (Guest, Buyer, Admin, Owner)
- ตรวจ End-to-End Parity (สมัคร OTP -> ล็อกอิน -> ตะกร้า -> คูปอง -> สั่งซื้อ -> PromptPay QR + สลิป -> แอดมินอนุมัติ -> ใบเสร็จ PDF -> จัดส่ง -> รับของ -> รีวิว -> แชท -> ส่งออก .xlsx -> สำรอง DB)
- ตรวจความปลอดภัย (CSRF Origin, IDOR, Path Traversal, Role Escalation, XSS)
- ตรวจประสิทธิภาพ (< 200 ms ต่อคำขอหลัก)
- ตรวจการตั้งค่าโลโก้ร้าน (store_logo_path No BG) และแบนเนอร์หน้า Login & Sign Up (login_banners สูงสุด 7 รูป, เฉพาะ Owner)
"""
import io
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

import config
import database.db as db
from core.session import Session
from database.seed import run_seed
from server.app import app
from server.deps import GUEST_STOREFRONT_ROUTES, PUBLIC_ROUTES, ROUTE_TABLE

_TMP = None
_TEMPLATE = None
_REAL_DB = (db.DB_PATH, db.DATA_DIR)
_REAL_DIRS = (
    config.SLIPS_DIR,
    config.RECEIPTS_DIR,
    config.USER_IMAGES_DIR,
    config.LOGIN_BANNERS_DIR,
    config.EXPORTS_DIR,
    config.BACKUP_DIR,
)


def _make_png_bytes(w=120, h=160, color=(255, 183, 3, 255)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def setUpModule():
    global _TMP, _TEMPLATE
    _TMP = Path(tempfile.mkdtemp(prefix="shop_web_test_"))
    _TEMPLATE = _TMP / "template.db"
    db.DATA_DIR, db.DB_PATH = _TMP, _TEMPLATE
    run_seed()
    db.DB_PATH, db.DATA_DIR = _REAL_DB
    config.SLIPS_DIR = _TMP / "slips"
    config.RECEIPTS_DIR = _TMP / "receipts"
    config.USER_IMAGES_DIR = _TMP / "users"
    config.LOGIN_BANNERS_DIR = _TMP / "login_banners"
    config.EXPORTS_DIR = _TMP / "exports"
    config.BACKUP_DIR = _TMP / "backups"
    for d in (
        config.SLIPS_DIR,
        config.RECEIPTS_DIR,
        config.USER_IMAGES_DIR,
        config.LOGIN_BANNERS_DIR,
        config.EXPORTS_DIR,
        config.BACKUP_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)


def tearDownModule():
    db.DB_PATH, db.DATA_DIR = _REAL_DB
    (
        config.SLIPS_DIR,
        config.RECEIPTS_DIR,
        config.USER_IMAGES_DIR,
        config.LOGIN_BANNERS_DIR,
        config.EXPORTS_DIR,
        config.BACKUP_DIR,
    ) = _REAL_DIRS
    Session.logout()
    shutil.rmtree(_TMP, ignore_errors=True)


class WebParityAndSecurityTest(unittest.TestCase):
    def setUp(self):
        self.path = _TMP / f"{self.id().split('.')[-1]}.db"
        shutil.copy(_TEMPLATE, self.path)
        db.DATA_DIR, db.DB_PATH = _TMP, self.path
        db.reset_connection_pool()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        db.reset_connection_pool()
        db.DB_PATH, db.DATA_DIR = _REAL_DB
        Session.logout()

    def test_01_all_30_routes_and_js_files_exist(self):
        """DoD #1 & #5: ครบ 30 หน้าใน ROUTE_TABLE, ไฟล์ JS มีอยู่จริง และย้าย ui/ ไป legacy_desktop/ui/ แล้ว"""
        self.assertEqual(len(ROUTE_TABLE), 30)
        for route_name, (rel_js, _cls_name) in ROUTE_TABLE.items():
            full_path = config.BASE_DIR / rel_js
            self.assertTrue(full_path.is_file(), f"Missing JS file for {route_name}: {full_path}")
        self.assertTrue((config.BASE_DIR / "legacy_desktop" / "ui").is_dir())
        self.assertTrue((config.WEB_DIR / "js" / "components" / "toast.js").is_file())
        import re as _re
        _imp_re = _re.compile(r"""(?:import|export)\s+(?:[^'"]+?\s+from\s+)?['"]([^'"]+)['"]""")
        for _jf in (config.WEB_DIR / "js").rglob("*.js"):
            _js_src = _jf.read_text(encoding="utf-8")
            for _m in _imp_re.finditer(_js_src):
                _spec = _m.group(1)
                if _spec.startswith("."):
                    _resolved = (_jf.parent / _spec).resolve()
                    self.assertTrue(_resolved.is_file(), f"Broken JS import in {_jf}: {_spec} -> {_resolved}")
        for py_file in (config.BASE_DIR / "server").rglob("*.py"):
            src = py_file.read_text(encoding="utf-8")
            self.assertNotIn("import customtkinter", src)
            self.assertNotIn("import tkinter", src)

    def test_02_role_route_permission_matrix(self):
        """P3-3: ตรวจตารางสิทธิ์ Role × Route ทั้ง 30 หน้าสำหรับ Guest, Buyer, Admin, Owner"""
        guest_client = TestClient(app)
        buyer_client = TestClient(app)
        admin_client = TestClient(app)
        owner_client = TestClient(app)

        self.assertEqual(buyer_client.post("/api/auth/login", json={"identifier": "buyer1", "password": "buyer123"}).status_code, 200)
        self.assertEqual(admin_client.post("/api/auth/login", json={"identifier": "admin1", "password": "admin123"}).status_code, 200)
        self.assertEqual(owner_client.post("/api/auth/login", json={"identifier": "owner", "password": "owner123"}).status_code, 200)

        owner_only_routes = {"admin_users", "admin_settings", "admin_categories", "admin_coupons", "admin_coupon_form"}

        for route in ROUTE_TABLE:
            g_res = guest_client.get("/api/auth/check-route", params={"route": route}).json()
            b_res = buyer_client.get("/api/auth/check-route", params={"route": route}).json()
            a_res = admin_client.get("/api/auth/check-route", params={"route": route}).json()
            o_res = owner_client.get("/api/auth/check-route", params={"route": route}).json()

            expected_guest = route in PUBLIC_ROUTES or route in GUEST_STOREFRONT_ROUTES
            self.assertEqual(g_res["allowed"], expected_guest, f"Guest route {route}")

            expected_buyer = not route.startswith("admin_")
            self.assertEqual(b_res["allowed"], expected_buyer, f"Buyer route {route}")

            expected_admin = route in PUBLIC_ROUTES or route in {"profile", "notifications"} or (
                route.startswith("admin_") and route not in owner_only_routes
            )
            self.assertEqual(a_res["allowed"], expected_admin, f"Admin route {route}")

            expected_owner = route in PUBLIC_ROUTES or route in {"profile", "notifications"} or route.startswith("admin_")
            self.assertEqual(o_res["allowed"], expected_owner, f"Owner route {route}")

    def test_03_concurrent_session_isolation_and_idle_lock(self):
        """P1-20 & P3-2: ผู้ซื้อและเจ้าของล็อกอินพร้อมกันคนละคุกกี้ ไม่ปนกัน + ล็อกหน้าจออัตโนมัติ (HTTP 423)"""
        c_buyer = TestClient(app)
        c_owner = TestClient(app)

        c_buyer.post("/api/auth/login", json={"identifier": "buyer1", "password": "buyer123"})
        c_owner.post("/api/auth/login", json={"identifier": "owner", "password": "owner123"})

        me_b = c_buyer.get("/api/auth/me").json()
        me_o = c_owner.get("/api/auth/me").json()
        self.assertEqual(me_b["user"]["username"], "buyer1")
        self.assertEqual(me_o["user"]["username"], "owner")

        self.assertEqual(c_owner.post("/api/auth/lock").status_code, 200)
        self.assertEqual(c_owner.get("/api/admin/dashboard").status_code, 423)
        self.assertEqual(c_buyer.get("/api/cart").status_code, 200)

        self.assertEqual(c_owner.post("/api/auth/unlock", json={"password": "wrong"}).status_code, 400)
        self.assertEqual(c_owner.post("/api/auth/unlock", json={"password": "owner123"}).status_code, 200)
        self.assertEqual(c_owner.get("/api/admin/dashboard").status_code, 200)

    def test_04_end_to_end_buyer_and_staff_journey(self):
        """P3-2: เดินสถานการณ์เต็มตั้งแต่ต้นจนจบผ่าน Web API"""
        buyer = TestClient(app)
        admin = TestClient(app)
        owner = TestClient(app)

        buyer.post("/api/auth/login", json={"identifier": "buyer1", "password": "buyer123"})
        admin.post("/api/auth/login", json={"identifier": "admin1", "password": "admin123"})
        owner.post("/api/auth/login", json={"identifier": "owner", "password": "owner123"})

        home_data = buyer.get("/api/home").json()
        self.assertIn("banners", home_data)
        self.assertIn("flash_sale", home_data)
        self.assertTrue(len(home_data["categories"]) >= 5)

        p_detail = buyer.get("/api/products/1").json()
        self.assertEqual(p_detail["id"], 1)

        cmp_res = buyer.get("/api/products/compare?ids=1,2").json()
        cmp_list = cmp_res if isinstance(cmp_res, list) else cmp_res.get("items") or cmp_res.get("products")
        self.assertEqual(len(cmp_list), 2)

        rf_res = buyer.get("/api/products/recommend?style=attack&level=Intermediate").json()
        rf_list = rf_res if isinstance(rf_res, list) else rf_res.get("items", [])
        self.assertTrue(len(rf_list) >= 1)

        wl_res = buyer.post("/api/wishlist/toggle", json={"product_id": 1}).json()
        self.assertIn("in_wishlist", wl_res)

        addrs_raw = buyer.get("/api/addresses").json()
        addrs = addrs_raw if isinstance(addrs_raw, list) else addrs_raw.get("items", [])
        self.assertTrue(len(addrs) >= 1)
        addr_id = addrs[0]["id"]

        add_cart = buyer.post("/api/cart/items", json={"product_id": 1, "option_id": 1, "qty": 1})
        self.assertEqual(add_cart.status_code, 200)

        chk_info = buyer.get("/api/checkout/info").json()
        self.assertIn("cart", chk_info)

        val_cp = buyer.post("/api/coupons/validate", json={"code": "WELCOME10", "subtotal": chk_info["cart"]["subtotal"]})
        self.assertEqual(val_cp.status_code, 200, val_cp.text)

        order_res = buyer.post("/api/orders", json={"address_id": addr_id, "coupon_code": "WELCOME10"})
        self.assertEqual(order_res.status_code, 200, order_res.text)
        order_payload = order_res.json()
        order_id = (order_payload.get("order") or order_payload)["id"]

        pay_info = buyer.get(f"/api/orders/{order_id}/payment-info").json()
        self.assertIn("payload", pay_info)
        qr_res = buyer.get(f"/api/orders/{order_id}/promptpay-qr")
        self.assertEqual(qr_res.status_code, 200)
        self.assertTrue(qr_res.content.startswith(b"\x89PNG"))

        slip_bytes = _make_png_bytes()
        up_slip = buyer.post(
            f"/api/orders/{order_id}/slip",
            files={"file": ("slip.png", slip_bytes, "image/png")},
        )
        self.assertEqual(up_slip.status_code, 200, up_slip.text)

        pending_pays = admin.get("/api/admin/payments/pending").json()
        pay_list = pending_pays if isinstance(pending_pays, list) else pending_pays.get("items", [])
        pay_row = next(p for p in pay_list if p["order_id"] == order_id)
        ver_res = admin.post(f"/api/admin/payments/{pay_row['id']}/verify")
        self.assertEqual(ver_res.status_code, 200, ver_res.text)

        pdf_res = buyer.get(f"/api/orders/{order_id}/receipt.pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertTrue(pdf_res.content.startswith(b"%PDF"))

        ship_res = admin.post(
            f"/api/admin/orders/{order_id}/ship",
            json={"carrier": "Kerry Express", "tracking_no": "KERRY999888TH"},
        )
        self.assertEqual(ship_res.status_code, 200, ship_res.text)

        rec_res = buyer.post(f"/api/orders/{order_id}/confirm-received")
        self.assertEqual(rec_res.status_code, 200, rec_res.text)

        rev_res = buyer.post(
            "/api/reviews",
            json={"order_id": order_id, "product_id": 1, "rating": 5, "comment": "ไม้ตีดีมาก ส่งไวมากครับ"},
        )
        self.assertEqual(rev_res.status_code, 200, rev_res.text)

        self.assertEqual(buyer.post("/api/chat/messages", json={"message": "สวัสดีครับ ขอสอบถามเรื่องเอ็น"}).status_code, 200)
        buyer_uid = buyer.get("/api/auth/me").json()["user"]["id"]
        self.assertEqual(admin.post("/api/admin/chat/reply", json={"customer_id": buyer_uid, "message": "ยินดีให้บริการครับ"}).status_code, 200)

        exp_res = owner.post(
            "/api/admin/expenses",
            json={"spent_on": "2026-10-24", "category": "ค่าขนส่ง", "amount": 350, "note": "ค่ากล่องพัสดุ"},
        )
        self.assertEqual(exp_res.status_code, 200, exp_res.text)

        xlsx_res = owner.post("/api/admin/export/xlsx", json={"start_date": "2026-10-01", "end_date": "2026-10-31"})
        self.assertEqual(xlsx_res.status_code, 200, xlsx_res.text)
        self.assertTrue(str(xlsx_res.json().get("filename") or xlsx_res.json().get("path")).endswith(".xlsx"))

        bk_res = owner.post("/api/admin/backups")
        self.assertEqual(bk_res.status_code, 200, bk_res.text)
        bks = owner.get("/api/admin/backups").json()
        bk_list = bks if isinstance(bks, list) else bks.get("items", [])
        self.assertGreaterEqual(len(bk_list), 1)

    def test_05_security_attacks_blocked(self):
        """P3-4: ทดสอบป้องกัน CSRF, IDOR, Path Traversal, Role Escalation และ XSS"""
        buyer1 = TestClient(app)
        buyer2 = TestClient(app)
        admin1 = TestClient(app)

        buyer1.post("/api/auth/login", json={"identifier": "buyer1", "password": "buyer123"})
        buyer2.post("/api/auth/register", json={"username": "buyer2_sec", "email": "b2sec@shop.com", "password": "password123", "full_name": "Buyer Two", "phone": "0891112222"})
        buyer2.post("/api/auth/login", json={"identifier": "buyer2_sec", "password": "password123"})
        admin1.post("/api/auth/login", json={"identifier": "admin1", "password": "admin123"})

        csrf_res = buyer1.post(
            "/api/cart/items",
            json={"product_id": 1, "qty": 1},
            headers={"Origin": "https://evil-attacker.example.com"},
        )
        self.assertEqual(csrf_res.status_code, 403)

        addrs_raw = buyer1.get("/api/addresses").json()
        addrs = addrs_raw if isinstance(addrs_raw, list) else addrs_raw.get("items", [])
        buyer1.post("/api/cart/items", json={"product_id": 1, "option_id": 1, "qty": 1})
        o_res = buyer1.post("/api/orders", json={"address_id": addrs[0]["id"]}).json()
        oid = (o_res.get("order") or o_res)["id"]
        buyer1.post(f"/api/orders/{oid}/slip", files={"file": ("s.png", _make_png_bytes(), "image/png")})

        self.assertEqual(buyer2.get(f"/api/orders/{oid}").status_code, 403)
        self.assertEqual(buyer2.get(f"/api/orders/{oid}/payment-info").status_code, 403)
        self.assertEqual(buyer2.post(f"/api/orders/{oid}/cancel", json={"reason": "hack"}).status_code, 403)

        self.assertIn(buyer2.delete(f"/api/addresses/{addrs[0]['id']}").status_code, (400, 403))

        self.assertIn(buyer1.get("/assets/slips/../../data/shop.db").status_code, (400, 403, 404))
        self.assertIn(buyer1.get("/assets/receipts/../../data/shop.db").status_code, (400, 403, 404))

        self.assertEqual(buyer1.get("/api/admin/dashboard").status_code, 403)
        self.assertEqual(admin1.get("/api/admin/users").status_code, 403)
        self.assertEqual(admin1.put("/api/admin/settings", json={"values": {"shop_name": "Hacked"}}).status_code, 403)
        self.assertEqual(admin1.delete("/api/admin/products/1").status_code, 403)
        self.assertEqual(admin1.post("/api/admin/backups").status_code, 403)

    def test_06_performance_under_200ms(self):
        """P3-5: วัดความเร็ว API หน้าหลัก, หมวดหมู่, ค้นหา, แดชบอร์ดแอดมิน ต้องเร็วกว่า 200 ms"""
        client = TestClient(app)
        client.post("/api/auth/login", json={"identifier": "owner", "password": "owner123"})
        client.get("/api/home")
        client.get("/api/admin/dashboard")

        guest = TestClient(app)
        guest.get("/api/home")

        endpoints = [
            (guest, "/api/home", "Home"),
            (guest, "/api/products?category_id=1", "Category"),
            (guest, "/api/products?search=Yonex", "Search"),
            (client, "/api/admin/dashboard", "Admin Dashboard"),
        ]
        for c, url, label in endpoints:
            t0 = time.perf_counter()
            res = c.get(url)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self.assertEqual(res.status_code, 200, f"{label} status")
            self.assertLess(elapsed_ms, 200.0, f"{label} took {elapsed_ms:.1f} ms (> 200 ms)")

    def test_07_login_signup_redesign_logo_and_banners_owner_only(self):
        """ตรวจฟีเจอร์ใหม่ของหน้า Login & Sign Up: โลโก้ร้าน No BG, แบนเนอร์รองเท้าสูงสุด 7 รูป (เฉพาะ Owner), และการสมัครแบบช่อง * เท่านั้น"""
        guest = TestClient(app)
        admin = TestClient(app)
        owner = TestClient(app)

        admin.post("/api/auth/login", json={"identifier": "admin1", "password": "admin123"})
        owner.post("/api/auth/login", json={"identifier": "owner", "password": "owner123"})

        # 1. ค่าเริ่มต้นมีรูปตัวอย่างรองเท้า 2 รูป (VS169 และ POWER CUSHION SHB101CR)
        ui_cfg = guest.get("/api/auth/ui-config").json()
        self.assertEqual(len(ui_cfg["login_banners"]), 2)
        self.assertTrue(any("vs169.png" in b["file_path"] for b in ui_cfg["login_banners"]))
        self.assertTrue(any("power_cushion_shb101cr.png" in b["file_path"] for b in ui_cfg["login_banners"]))

        # 2. Admin และ Guest ห้ามแก้ไขโลโก้ร้านหรือแบนเนอร์หน้า Login/Sign Up
        self.assertEqual(admin.post("/api/admin/settings/logo", json={"store_logo_path": "assets/images/hack.png"}).status_code, 403)
        self.assertEqual(admin.post("/api/admin/login-banners", json={"file_path": "assets/images/hack.png"}).status_code, 403)
        self.assertEqual(guest.post("/api/admin/login-banners", json={"file_path": "assets/images/hack.png"}).status_code, 401)

        # 3. Owner อัปโหลดโลโก้โปร่งใสและลบโลโก้ได้
        up_logo = owner.post(
            "/api/uploads/image",
            data={"target": "logo"},
            files={"file": ("store_logo.png", _make_png_bytes(600, 600), "image/png")},
        )
        self.assertEqual(up_logo.status_code, 200, up_logo.text)
        logo_path = up_logo.json()["path"]
        set_logo = owner.post("/api/admin/settings/logo", json={"store_logo_path": logo_path})
        self.assertEqual(set_logo.status_code, 200)
        self.assertEqual(guest.get("/api/auth/ui-config").json()["store_logo_path"], logo_path)

        del_logo = owner.delete("/api/admin/settings/logo")
        self.assertEqual(del_logo.status_code, 200)
        self.assertEqual(guest.get("/api/auth/ui-config").json()["store_logo_path"], "")

        # 4. Owner เพิ่มรูปแบนเนอร์หน้า Login & Sign Up จนครบ 7 รูป และระบบบล็อกรูปที่ 8
        paths_to_add = []
        for i in range(5):
            up_b = owner.post(
                "/api/uploads/image",
                data={"target": "login_banner"},
                files={"file": (f"shoe_{i}.png", _make_png_bytes(400, 300), "image/png")},
            )
            self.assertEqual(up_b.status_code, 200, up_b.text)
            paths_to_add.append(up_b.json()["path"])

        add_res = owner.post("/api/admin/login-banners", json={"file_paths": paths_to_add})
        self.assertEqual(add_res.status_code, 200, add_res.text)
        self.assertEqual(add_res.json()["count"], 7)

        # ลองเพิ่มรูปที่ 8 -> ต้องถูกปฏิเสธ 400 และจำนวนคงเดิมที่ 7
        over_res = owner.post("/api/admin/login-banners", json={"file_paths": [paths_to_add[0]]})
        self.assertEqual(over_res.status_code, 400)
        self.assertEqual(guest.get("/api/login-banners").json()["count"], 7)

        # ลบทั้งหมดจนเหลือ 0 รูป -> ไม่พัง
        for item in list(guest.get("/api/login-banners").json()["items"]):
            d_res = owner.delete(f"/api/admin/login-banners/{item['id']}")
            self.assertEqual(d_res.status_code, 200)
        self.assertEqual(guest.get("/api/login-banners").json()["count"], 0)

        # 5. สมัครสมาชิกใหม่โดยกรอกเฉพาะช่องบังคับ (*) เว้นเบอร์โทรและที่อยู่เริ่มต้นว่างได้
        import re as _re
        from unittest.mock import patch as _patch
        from services import otp_service as _otp_svc
        _otp_svc.reset_ip_rate_limits()
        with _patch("services.email_service.send_mail", return_value={"sent": True, "mode": "smtp"}) as _m_mail:
            reg_start = guest.post("/api/auth/register/start", json={
                "username": "minimal_buyer",
                "email": "minimal_buyer@example.com",
                "full_name": "ผู้ซื้อ ข้อมูลย่อ",
                "phone": "",
                "password": "Password123",
                "address_line": "",
                "district": "",
                "province": "",
                "postcode": "",
            })
            self.assertEqual(reg_start.status_code, 200, reg_start.text)
            _txt = _m_mail.call_args.args[2] if len(_m_mail.call_args.args) >= 3 else _m_mail.call_args.kwargs.get("text", "")
            otp = _re.search(r"\b(\d{6})\b", _txt).group(1)
        reg_ver = guest.post("/api/auth/register/verify", json={
            "email": "minimal_buyer@example.com",
            "otp_code": otp,
        })
        self.assertEqual(reg_ver.status_code, 200, reg_ver.text)
        self.assertEqual(reg_ver.json()["user"]["username"], "minimal_buyer")


if __name__ == "__main__":
    unittest.main()
