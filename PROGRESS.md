# PROGRESS.md — ความคืบหน้าการย้าย UI สู่ HTML / CSS / JS (หลังบ้าน Python + SQLite)

> อัปเดตไฟล์นี้ **ทันทีที่ทำเสร็จแต่ละข้อ** (เสร็จ = เขียนครบ + รันได้จริง + ทดสอบแล้ว)
> ถ้าเซสชันขาด ให้เริ่มอ่านจากหัวข้อ **"จุดที่ทำถึง"** ด้านล่างนี้ก่อน

---

## จุดที่ทำถึง
- **เฟสปัจจุบัน:** เสร็จสมบูรณ์ครบทุกเฟส (เฟส 0 → เฟส 1 → เฟส 2 → เฟส 3 — 100%)
- **ข้อล่าสุดที่ทำเสร็จ:** `UI-AUTH-REDESIGN` (รื้อ UI หน้า Login และ Sign Up เดิมออกทั้งหมด เปลี่ยนเป็นดีไซน์ใหม่ตาม `Login&Signup Change.pdf` + `login_signup_ui_spec.md` พร้อมระบบตั้งค่าโลโก้ร้าน No BG 115×115 และแบนเนอร์รองเท้าหน้า Login & Sign Up สูงสุด 7 รูป เฉพาะ Owner)
- **ข้อถัดไปที่จะทำ:** ไม่มี — ส่งมอบงานครบ 100%

## ผลเทสต์ล่าสุด
- `tests/test_promptpay.py`: **ผ่าน 7 / 7**
- `tests/test_repos.py`: **ผ่าน 26 / 26**
- `tests/test_services_basic.py`: **ผ่าน 64 / 64**
- `tests/test_order_flow.py`: **ผ่าน 58 / 58**
- `tests/test_web_parity_and_security.py`: **ผ่าน 7 / 7** (ครอบคลุม 30 routes, Role × Route Matrix, Concurrent Sessions + Idle Lock, End-to-End Flow, Security Attacks CSRF/IDOR/Path Traversal/Role Escalation, Performance < 200ms)
- **รวมทั้งหมด:** **ผ่าน 167 / 167 เทสต์ (`OK`)** + Headless Chromium ตรวจครบทั้ง 30 หน้า (38 ภาพหน้าจอใน `docs/web_screens/` รวมโหมดมืด) **`SEVERE console errors = 0`** + `python main.py --check` **ผ่านครบ 6 หมวด**

---

## เฟส 0 — เตรียมการ
- [x] P0-1 สำรองโปรเจกต์ทั้งก้อน (คัดลอก `badminton_shop_backup/` และ `git init` + commit ฐาน `bd6b299`)
- [x] P0-2 เปลี่ยน PROGRESS.md เดิม (`Workflow.md` 652 บรรทัด) → `LEGACY_PROGRESS.md` และวางไฟล์นี้แทน
- [x] P0-3 สร้าง venv + ติดตั้ง dependencies เดิม + รันเทสต์เดิมทั้งหมด บันทึกตัวเลขฐานในตารางด้านบน (155/155 ผ่าน)
- [x] P0-4 Inventory: ไล่ `ui/pages/**` + `ui/components/**` ทุกไฟล์ → กรอกตาราง "แมปหน้า → service/API" (ด้านล่างครบ 30 หน้า)
- [x] P0-5 ค้นงานตอนเปิด/ปิดแอปและงานเบื้องหลัง (`main.py`, `ui/app.py`, ทุกที่ที่มี `threading`/`after`) → จดรายการใน "งานเบื้องหลังที่ต้องย้าย"
- [x] P0-6 ค้นการใช้ `Session.` ทั้งโปรเจกต์ (grep) → จดว่าใครอ่าน/เขียน attribute ตรง ๆ
- [x] P0-7 ตรวจ `utils/image_utils.py`, `utils/icon_utils.py`, `utils/font_installer.py` ว่าส่วนไหนผูก Tkinter → จดวิธีแยก
- [x] P0-8 ตรวจ `database/db.py` (`get_connection` เปิด `foreign_keys=1`, `journal_mode=WAL`, `busy_timeout=10000` อยู่แล้ว) และ `SMTP_PASS` vs `SMTP_PASSWORD`
- [x] P0-9 (ถ้าทำได้) แคปภาพอ้างอิงทุกหน้าของแอปเดิมที่ 1280×800 → เครื่อง VM ไม่มี `_tkinter` C-extension และไม่มี Xvfb จึงสร้างจากโค้ด `ui/pages/**` และ `ui/components/**` บรรทัดต่อบรรทัดตาม PLAN.md หัวข้อ 4 ข้อ 2
- [x] P0-10 ✅ เกณฑ์ผ่านเฟส 0 (ตัวเลขเทสต์ฐานมี 155/155, inventory ครบ 30 หน้า, ตารางพาริตี้ถูกเติมจากโค้ดจริง)

## เฟส 1 — หลังบ้าน (Python API)
- [x] P1-1 `core/session.py` → contextvars (คง API เดิมครบผ่าน `_SessionMeta` + ซิงค์สถานะ lock/idle ต่อ `session_token`) + เทสต์แยกผู้ใช้พร้อมกัน 40 workers และผ่าน TestClient
- [x] P1-2 ตรวจ/ห่อ thread เบื้องหลังที่เรียก Session/permissions (`chat_service`, `email_outbox_service`) ด้วย `contextvars.copy_context().run`
- [x] P1-3 `server/app.py`: FastAPI, middleware session-จากคุกกี้, ตรวจ Origin (CSRF), ตัวแปลง exception → HTTP (ValueError→400, PermissionError→401/403, FileNotFoundError→404, อื่นๆ→500), static (`web/`, `assets/fonts`, `assets/images`, `assets/icons` เฉพาะโฟลเดอร์สาธารณะ)
- [x] P1-4 `server/deps.py` + route guard ตาม `ROUTE_ROLES`/guest (`ROUTE_TABLE` ครบ 30 หน้า)
- [x] P1-5 `server/serializers.py` (Row→dict, ตัดฟิลด์ลับ `password_hash`, `code_hash`, `token_hash` ทุกระดับ)
- [x] P1-6 routes: auth (`server/routes/auth.py` — login/logout/register/OTP/ลืมรหัส/เปลี่ยนรหัส/must_change/guest/lock/unlock/heartbeat/bootstrap)
- [x] P1-7 routes: account/profile (`server/routes/account.py` — แก้ข้อมูล, รูปโปรไฟล์, เปลี่ยนอีเมลด้วย OTP)
- [x] P1-8 routes: สินค้า/หมวด/แบรนด์/ตัวเลือก/ของแถม/ค้นหา/กรอง/เปรียบเทียบ/ตัวช่วยเลือกไม้ (`server/routes/products.py` — ฝั่งผู้ซื้อ + ฝั่งแอดมิน CRUD, ลบ=ซ่อน/กู้คืน, สต็อก)
- [x] P1-9 routes: ตะกร้า (`server/routes/cart.py`), ที่อยู่, รายการโปรด (`server/routes/account.py`)
- [x] P1-10 routes: คูปอง (เก็บ/ใช้/จัดการ/Flash Sale/กฎซื้อครบรับคูปอง), แบนเนอร์, settings + ข้อมูลติดต่อ (`server/routes/coupons_settings.py`)
- [x] P1-11 routes: ออเดอร์ (สร้าง/ยกเลิก/ยืนยันรับ/แท็บสถานะ/รอรีวิว), ชำระเงิน (QR, แนบสลิป, ตรวจสลิปผ่าน/ปฏิเสธ), จัดส่ง, ใบเสร็จ PDF (`server/routes/orders_payments.py`)
- [x] P1-12 routes: รีวิว, แจ้งเตือน, แชท (ลูกค้า/แอดมิน/ข้อความด่วน/AI/แนะนำไม้) (`server/routes/reviews_notifications_chat.py`)
- [x] P1-13 routes: แอดมิน — dashboard/สถิติ, ผู้ใช้, รายจ่าย, ส่งออก .xlsx (+อัตโนมัติ/Sheets), Audit Log, สำรองฐานข้อมูล (`server/routes/admin_ops.py`)
- [x] P1-14 อัปโหลดรูป (สินค้า/แบนเนอร์/หมวด/โลโก้/โปรไฟล์/สลิป) ผ่าน `image_utils` + ตรวจเนื้อไฟล์ + ตั้งชื่อฝั่งเซิร์ฟเวอร์ (`POST /api/uploads/image` และ endpoints เฉพาะ)
- [x] P1-15 endpoint ไฟล์ที่ต้องมีสิทธิ์: สลิป (`/api/files/slips/{id}`, `/api/orders/{id}/slip-image`, `/assets/slips/...`), ใบเสร็จ (`/api/orders/{id}/receipt.pdf`, `/assets/receipts/...`), ดาวน์โหลดรายงาน (`/api/admin/export/download`), QR พร้อมเพย์ (`/api/orders/{id}/promptpay-qr`)
- [x] P1-16 `server/jobs.py` + lifespan: งานทั้งหมดจาก "งานเบื้องหลังที่ต้องย้าย"
- [x] P1-17 `main.py` ใหม่ (เริ่ม uvicorn, เปิดเบราว์เซอร์, `--check`, คำเตือนรหัสเริ่มต้น, ปฏิเสธ bind ภายนอกถ้ารหัสเริ่มต้นยังไม่เปลี่ยน) + `config.py` (HOST/PORT/cookie) + `requirements.txt` + `.env.example`
- [x] P1-18 เทสต์ API (`tests/test_api_web.py`): ทุกโดเมน endpoint (สำเร็จ + สิทธิ์ไม่พอ/ข้อมูลผิด) + flow ครบสั่งซื้อ→จัดส่ง→รีวิว
- [x] P1-19 เทสต์ความปลอดภัยฝั่ง API (IDOR, ข้าม role, ไม่มีคุกกี้=guest, ไม่คืน password_hash, Origin ผิด=403, Idle lock=423)
- [x] P1-20 ✅ เกณฑ์ผ่านเฟส 1 (เทสต์เดิมผ่าน 155/155 + เทสต์ API ใหม่ผ่านครบ 5 ชุดใหญ่ รวม 160/160) → เขียน "สรุปเฟส 1"

## เฟส 2 — หน้าเว็บ
### 2A ฐาน
- [x] P2-1 `web/css/tokens.css` (สี light/dark ครบทุกคีย์ COLORS, ฟอนต์, ปุ่มทุกชนิด×ขนาด) + `@font-face` Kanit/Arimo + `base.css`
- [x] P2-2 `web/index.html` + `js/app.js` + `js/state.js` + `js/api.js`
- [x] P2-3 `js/router.js`: ROUTE_TABLE ครบ 30 route, role guard, guest storefront, จำปลายทางหลัง login, must_change_password, History API, params
- [x] P2-4 ระบบ modal / confirm / toast / loading / empty / error (แทน `dialogs.py`)
- [x] P2-5 idle lock overlay + heartbeat (staff) ; toggle ธีมมืด/สว่างจำค่า (ตั้งก่อนวาดหน้า กันกะพริบ)
### 2B คอมโพเนนต์
- [x] P2-6 navbar (+ ค้นหา, ตะกร้า, แจ้งเตือน/จุดแดง, เมนูผู้ใช้)
- [x] P2-7 sidebar (แอดมิน/เจ้าของ แสดงเมนูตามสิทธิ์)
- [x] P2-8 auth_layout (+ สุ่มสลับรูปสินค้าทุก `login_showcase_seconds`)
- [x] P2-9 product_card / product_grid / product_filter / search_bar
- [x] P2-10 rating / order_timeline / payment_qr / chat_bubble
- [x] P2-11 image_picker (อัปโหลด+พรีวิว+ลากวาง) / date_picker
- [x] P2-12 pager / table / stat_card / pill / segmented (ชุดของ `admin/common.py`) + lightbox รูป

### 2C หน้าผู้ซื้อ (ไฟล์เดิม → `web/js/pages/buyer/<ชื่อ>.js` + `web/css/pages/<ชื่อ>.css`)
ติ๊กได้เมื่อ: หน้าตาเทียบของเดิมแล้ว + ทุกปุ่ม/เงื่อนไข/ข้อความมาครบ + ทดสอบกับ API จริง
- [x] P2-13 login (250 บรรทัดเดิม)
- [x] P2-14 register (231) + OTP
- [x] P2-15 home (1,138) — แบนเนอร์, Flash Sale เลื่อน, คูปองสลับชุด, หมวด, รายการสินค้า
- [x] P2-16 category (150)
- [x] P2-17 product_detail (817)
- [x] P2-18 compare (302)
- [x] P2-19 racket_finder (165)
- [x] P2-20 wishlist (46)
- [x] P2-21 cart (346)
- [x] P2-22 addresses (205)
- [x] P2-23 checkout (497)
- [x] P2-24 payment (273) — QR + แนบสลิป
- [x] P2-25 orders (265) — แท็บสถานะ + รอรีวิว
- [x] P2-26 order_detail (345)
- [x] P2-27 write_review (147)
- [x] P2-28 profile (402)
- [x] P2-29 notifications (206)
- [x] P2-30 chat (307) — polling, ข้อความด่วน, AI

### 2D หน้าแอดมิน/เจ้าของ (→ `web/js/pages/admin/<ชื่อ>.js`)
- [x] P2-31 dashboard (218)
- [x] P2-32 products (516)
- [x] P2-33 product_form (775)
- [x] P2-34 categories (599) — หมวด/แบรนด์
- [x] P2-35 orders (119)
- [x] P2-36 order_detail (328)
- [x] P2-37 payments (158) — ตรวจสลิป
- [x] P2-38 coupons (366)
- [x] P2-39 coupon_form (402)
- [x] P2-40 chat (267)
- [x] P2-41 users (495)
- [x] P2-42 settings (754) — ตั้งค่าร้าน/พร้อมเพย์/แบนเนอร์/ติดต่อ/สำรอง/ส่งออก/Audit
- [x] P2-43 ✅ เกณฑ์ผ่านเฟส 2 (เดินครบ 30 หน้า ไม่มี error ใน console, มืด/สว่างอ่านชัด) → เขียน "สรุปเฟส 2"

## เฟส 3 — พาริตี้ ความปลอดภัย ส่งมอบ
- [x] P3-1 สคริปต์ E2E เบราว์เซอร์ (Playwright/Selenium): guest→สมัคร→ซื้อ→ชำระ→แอดมินตรวจ→จัดส่ง→รับของ→รีวิว ; owner: สร้างแอดมิน/คูปอง/Flash Sale/ส่งออก .xlsx ; เก็บภาพ `docs/web_screens/`
- [x] P3-2 ไล่ "ตารางพาริตี้" ครบทุกข้อ (ด้านล่าง)
- [x] P3-3 matrix สิทธิ์ role × route × action ตรงกับ `core/permissions.py`
- [x] P3-4 ทดสอบความปลอดภัยแบบโจมตีจริง: IDOR, ข้ามสิทธิ์, อัปโหลดไฟล์แปลก/`../`, ฉีด `<script>` (ชื่อสินค้า/รีวิว/แชท/ที่อยู่), Origin อื่น, เปิด URL สลิป/ใบเสร็จของคนอื่น
- [x] P3-5 ตรวจประสิทธิภาพเบื้องต้น (หน้าแรก/รายการสินค้า, ขนาดรูป)
- [x] P3-6 ทำความสะอาด: `ui/` → `legacy_desktop/ui/`, เอา customtkinter ออก, ตรวจไม่มี import tkinter ใน flow เว็บ
- [x] P3-7 อัปเดต `README.md` + `.env.example` (ติดตั้ง/รัน/ตั้งค่า/บัญชีเริ่มต้น/เตือนเปลี่ยนรหัส/เปิดให้เครื่องอื่นเข้าอย่างปลอดภัย)
- [x] P3-8 เทสต์ทั้งหมดรันซ้ำครั้งสุดท้าย + `python main.py --check` ผ่าน
- [x] P3-9 ✅ เกณฑ์ผ่านเฟส 3 = Definition of Done ครบ 6 ข้อใน PLAN.md หัวข้อ 1 → เขียน "สรุปส่งมอบ"

---

## ตารางพาริตี้ฟีเจอร์
> เริ่มจากรายการสรุปใน PLAN.md หัวข้อ 6 แล้ว **เติมให้ละเอียดจากโค้ดเดิมจริงในเฟส 0 (P0-4)** — ทุกปุ่ม/ตัวกรอง/เงื่อนไข/ข้อความที่พบให้เป็นหนึ่งแถว
> สถานะ: ⬜ ยังไม่ทำ · 🟨 ทำแล้วยังไม่ทดสอบ · ✅ ทดสอบแล้วผ่าน · ⚠️ ต่างจากเดิม (ใส่เหตุผล)

| # | ฟีเจอร์ / เงื่อนไข | ไฟล์เดิมที่มา | API | หน้าเว็บ | สถานะ | หมายเหตุ |
|---|---|---|---|---|---|---|
| 1 | Guest เข้าชมหน้า home, category, product_detail, compare, racket_finder ได้โดยไม่ต้องล็อกอิน | `ui/router.py` | `POST /api/auth/guest` | `router.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 2 | Guest กดใส่ตะกร้า/รายการโปรด/คูปองของฉัน/สั่งซื้อ → พาไปหน้า Login พร้อมข้อความแจ้ง และจำหน้าปลายทางกลับไปหลังล็อกอิน | `ui/router.py`, `home.py`, `product_detail.py` | - | `router.js`, `login.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 3 | หน้า Login: ล็อกอินด้วย username หรืออีเมล, ติ๊กจำเครื่องนี้ (staff 90 วัน, buyer 7 วัน), ปุ่มเข้าชมหน้าร้านแบบไม่ล็อกอิน, โมดอลลืมรหัสผ่านด้วย OTP 6 หลัก | `ui/pages/buyer/login.py` | `POST /api/auth/login`, `POST /api/auth/reset/start`, `POST /api/auth/reset/verify` | `buyer/login.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 4 | AuthSplitLayout: แสดงคำทักทาย Welcome สลับคำพร้อม glitch effect + สลับรูปสินค้าจริงจากร้านทุก `login_showcase_seconds` | `ui/components/auth_layout.py` | `GET /api/products/showcase` | `components/auth_layout.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 5 | บัญชีที่ติด `must_change_password=1` บังคับเปลี่ยนรหัสผ่านก่อนใช้งานส่วนอื่น | `ui/pages/buyer/login.py`, `services/auth_service.py` | `POST /api/auth/change-password` | `router.js`, `buyer/profile.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 6 | หน้า Register: กรอกชื่อผู้ใช้/อีเมล/ชื่อ-นามสกุล/เบอร์/รหัสผ่าน + ที่อยู่จัดส่งเริ่มต้น → ส่ง OTP 6 หลัก (แสดง dev_otp เมื่อ `OTP_DEV_ECHO`) → ยืนยัน OTP สร้างบัญชี+ที่อยู่เริ่มต้น | `ui/pages/buyer/register.py` | `POST /api/auth/register/start`, `POST /api/auth/register/verify`, `POST /api/auth/register/resend` | `buyer/register.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 7 | Staff Idle Lock: ไม่มีกิจกรรมครบ `STAFF_IDLE_TIMEOUT_MINUTES` → ล็อกเซสชัน แสดงหน้าต่างใส่รหัสผ่านปลดล็อกหรือออกจากระบบ | `ui/app.py`, `services/auth_service.py` | `POST /api/auth/heartbeat`, `POST /api/auth/lock`, `POST /api/auth/unlock` | `app.js`, `components/dialogs.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 8 | สลับโหมดสว่าง/มืด (Light/Dark Mode) จำค่าใน localStorage และตั้ง `data-theme` ก่อนวาดหน้า | `ui/theme.py`, `navbar.py`, `sidebar.py` | - | `state.js`, `tokens.css` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 9 | Navbar ผู้ซื้อ/Guest: โลโก้+ชื่อร้าน, ช่องค้นหาพร้อม autocomplete แนะนำสินค้า, ปุ่มหน้าแรก/หมวดหมู่/เปรียบเทียบ/ช่วยเลือกไม้/รายการโปรด/ตะกร้า(badge)/ออเดอร์/แชท(badge)/แจ้งเตือน(badge 9+)/โปรไฟล์/สลับธีม/เข้าหรือออกจากระบบ | `ui/components/navbar.py` | `GET /api/bootstrap`, `GET /api/products/suggest` | `components/navbar.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 10 | Sidebar แอดมิน/เจ้าของ: แสดงเมนูตามสิทธิ์ (`ROUTE_ROLES`), badge จำนวนสลิปรอตรวจ + แชทยังไม่อ่าน, ปุ่มแจ้งเรื่องด่วนถึงเจ้าของร้าน (เฉพาะ admin), สลับธีม, ออกจากระบบ | `ui/components/sidebar.py` | `GET /api/admin/badges`, `POST /api/contact/urgent-email` | `components/sidebar.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 11 | หน้า Home: แบนเนอร์สไลด์อัตโนมัติ + ปุ่มซ้าย/ขวา/จุดตัวบ่งชี้ + คลิกเปิดลิงก์ | `ui/pages/buyer/home.py` | `GET /api/banners` | `buyer/home.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 12 | หน้า Home: แถบ Flash Sale ไฟกระพริบ + นับถอยหลัง + เลื่อนอัตโนมัติตามความเร็ว `flash_sale_scroll_speed` (หยุดเมื่อเมาส์ชี้) | `ui/pages/buyer/home.py` | `GET /api/products` | `buyer/home.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 13 | หน้า Home: แถบคูปองส่วนลด สลับชุดอัตโนมัติทุก `coupon_rotate_seconds` แสดงชุดละ `home_coupons_per_view` ใบ + ปุ่มเก็บคูปอง + โมดอลดูคูปองทั้งหมดแยกตามหมวดคูปอง + กฎซื้อครบรับคูปอง | `ui/pages/buyer/home.py` | `GET /api/coupons/public`, `GET /api/coupons/shop`, `GET /api/coupons/my`, `POST /api/coupons/claim`, `GET /api/coupons/rules` | `buyer/home.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 14 | หน้า Home: แถบหมวดหมู่พร้อมรูป, แถบแบรนด์, สินค้าขายดี, สินค้ามาใหม่, สินค้าดูล่าสุด (`recently_viewed`), ฟุตเตอร์ข้อมูลติดต่อร้านครบทุกช่องทาง | `ui/pages/buyer/home.py` | `GET /api/categories`, `GET /api/brands`, `GET /api/products/recently-viewed`, `GET /api/settings/contact` | `buyer/home.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 15 | หน้า Category: กรองตามหมวดหมู่/แบรนด์/ช่วงราคา/เฉพาะลดราคา/มีของพร้อมส่ง/สเปกไม้แบด (weight_class, balance, flex, level) + ค้นหาคำสำคัญ + เรียงลำดับ (`SORT_OPTIONS`) + แบ่งหน้า | `ui/pages/buyer/category.py`, `product_filter.py`, `product_grid.py` | `GET /api/products`, `GET /api/products/filters` | `buyer/category.js`, `components/product_filter.js`, `components/product_grid.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 16 | การ์ดสินค้า (`ProductCard` สัดส่วน 3:4 รูปจัตุรัส 1:1): ป้ายส่วนลด `-%` หรือ `OUT OF STOCK`, ปุ่มหัวใจรายการโปรดมุมขวาบน, ชื่อแบรนด์, ชื่อสินค้า, ดาวรีวิว, ราคาโปรขีดฆ่าราคาเต็ม, นับถอยหลัง Flash Sale | `ui/components/product_card.py` | `POST /api/wishlist/toggle` | `components/product_card.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 17 | หน้า Product Detail: แกลเลอรีหลายรูป + คลิกเปลี่ยนรูป/เปลี่ยนสีแล้วสลับรูปอัตโนมัติ (`color_image_map`) + เลือกตัวเลือกสินค้า (`options_by_type`) อัปเดตราคาและสต็อกรายตัวเลือก + เลือกบริการเสริม/ของแถม (`addons`) + จำนวนซื้อ + ปุ่มเพิ่มลงตะกร้า/ซื้อเลย/รายการโปรด/เปรียบเทียบ | `ui/pages/buyer/product_detail.py` | `GET /api/products/{id}`, `POST /api/cart/items`, `POST /api/cart/items-with-addons` | `buyer/product_detail.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 18 | หน้า Product Detail: กล่อง Technical Specifications สไตล์สปอร์ตเข้ม (`RACKET_TECH_SPEC_FIELDS` 7 แถว รวม Balance Point mm) + รายการรีวิวและคะแนนเฉลี่ย | `ui/pages/buyer/product_detail.py` | `GET /api/products/{id}`, `GET /api/products/{id}/reviews` | `buyer/product_detail.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 19 | หน้า Compare: เปรียบเทียบไม้แบด 2–5 รุ่น (`MIN_COMPARE`–`MAX_COMPARE`) ค้นหา/เพิ่ม/ลบไม้ แสดงตารางเทียบราคา คะแนนรีวิว น้ำหนัก จุดสมดุล(mm) ก้าน ระดับ สเปกเทคนิค และปุ่มดูสินค้า | `ui/pages/buyer/compare.py` | `GET /api/products/compare` | `buyer/compare.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 20 | หน้า Racket Finder: เลือกระดับผู้เล่น + สไตล์การเล่น (บุก/สปีด/คอนโทรล) + งบประมาณ → แนะนำไม้แบดที่เหมาะสมพร้อมคะแนนจับคู่และเหตุผล | `ui/pages/buyer/racket_finder.py` | `GET /api/products/recommend` | `buyer/racket_finder.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 21 | หน้า Wishlist: แสดงรายการสินค้าที่ถูกใจ กดหัวใจซ้ำเพื่อเอาออกทันที | `ui/pages/buyer/wishlist.py` | `GET /api/wishlist`, `POST /api/wishlist/toggle` | `buyer/wishlist.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 22 | หน้า Cart: เลือกบางรายการ (`is_selected`) หรือเลือกทั้งหมด, ปรับจำนวน `+`/`-`, ลบรายชิ้น, ลบที่เลือก, แจ้งเตือนรายการที่มีปัญหา (`problems` เช่น สต็อกไม่พอ/สินค้าถูกปิด/ตัวเลือกถูกลบ), คำนวณยอดรวมและค่าส่งเบื้องต้น | `ui/pages/buyer/cart.py` | `GET /api/cart`, `PATCH /api/cart/items/{id}`, `POST /api/cart/select-all`, `DELETE /api/cart/items/{id}`, `DELETE /api/cart/selected` | `buyer/cart.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 23 | หน้า Addresses: รายการที่อยู่จัดส่ง (สูงสุด `MAX_ADDRESSES=10`), เพิ่ม/แก้ไข/ลบ/ตั้งเป็นค่าเริ่มต้น, ตรวจเบอร์โทร 10 หลักและรหัสไปรษณีย์ 5 หลัก | `ui/pages/buyer/addresses.py` | `GET /api/addresses`, `POST /api/addresses`, `PUT /api/addresses/{id}`, `DELETE /api/addresses/{id}`, `POST /api/addresses/{id}/default` | `buyer/addresses.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 24 | หน้า Checkout: เลือกที่อยู่จัดส่ง, เลือกคูปองส่วนลดร้าน + คูปองส่งฟรีแยกกัน (หรือกรอกโค้ดเก็บคูปองเพิ่ม), แสดงรายการสินค้าที่เลือกจากตะกร้า, คำนวณราคาสินค้า/ส่วนลด/ค่าส่ง/ภาษี VAT 7% (`compute_vat_breakdown`) ตรงตามหลังบ้าน, สร้างคำสั่งซื้อและพาไปหน้าชำระเงิน | `ui/pages/buyer/checkout.py` | `GET /api/checkout/info`, `POST /api/orders` | `buyer/checkout.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 25 | หน้า Payment: แสดง QR PromptPay (ดาวน์โหลดรูป QR ได้), ข้อมูลบัญชีพร้อมเพย์, ยอดชำระ, เวลาที่เหลือ (`unpaid_cancel_hours`), อัปโหลดรูปสลิปโอนเงิน, ปุ่มยกเลิกคำสั่งซื้อพร้อมระบุเหตุผล | `ui/pages/buyer/payment.py`, `payment_qr.py` | `GET /api/orders/{id}/payment-info`, `GET /api/orders/{id}/promptpay-qr`, `POST /api/orders/{id}/slip`, `POST /api/orders/{id}/cancel` | `buyer/payment.js`, `components/payment_qr.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 26 | หน้า Orders (ผู้ซื้อ): แท็บสถานะครบ 8 แท็บตาม `ORDER_STATUS_DISPLAY_ORDER` (การสั่งซื้อ, รอชำระเงิน, ชำระเงินแล้ว, รอตรวจสลิป, จัดส่งแล้ว, สำเร็จ, รอรีวิว, สินค้าที่คุณยกเลิก) พร้อมจำนวนต่อแท็บ, ปุ่มชำระเงิน/ยืนยันรับสินค้า/เขียนรีวิว/ดูรายละเอียด | `ui/pages/buyer/orders.py` | `GET /api/orders/my`, `GET /api/orders/my/counts`, `POST /api/orders/{id}/confirm-received` | `buyer/orders.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 27 | หน้า Order Detail (ผู้ซื้อ): ไทม์ไลน์สถานะออเดอร์ (`OrderTimeline`), รายการสินค้า, สรุปยอด+VAT 7%, ข้อมูลชำระเงิน/เหตุผลปฏิเสธสลิป, ข้อมูลขนส่ง+เลขพัสดุ, ปุ่มดาวน์โหลดใบเสร็จ PDF, ส่งใบเสร็จเข้าอีเมล, ยกเลิกออเดอร์(เมื่อ pending), ยืนยันรับของ(เมื่อ shipped), เขียนรีวิวรายสินค้า | `ui/pages/buyer/order_detail.py` | `GET /api/orders/{id}`, `GET /api/orders/{id}/receipt.pdf`, `POST /api/orders/{id}/send-receipt-email` | `buyer/order_detail.js`, `components/order_timeline.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 28 | หน้า Write Review: ให้คะแนนดาว 1–5 (`StarRatingInput`) + ความคิดเห็น (สูงสุด 1,000 ตัวอักษร) เฉพาะสินค้าในออเดอร์ที่สำเร็จแล้วและยังไม่เคยรีวิว | `ui/pages/buyer/write_review.py` | `GET /api/reviews/can-review`, `POST /api/reviews` | `buyer/write_review.js`, `components/rating.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 29 | หน้า Profile: แก้ชื่อ-นามสกุล/เบอร์โทร/ชื่อผู้ใช้ (`username`), อัปโหลดรูปโปรไฟล์, เปลี่ยนอีเมลด้วยรหัส OTP 6 หลัก, เปลี่ยนรหัสผ่าน (รองรับกรณีบังคับเปลี่ยนรหัสครั้งแรก) | `ui/pages/buyer/profile.py` | `GET /api/account/profile`, `PUT /api/account/profile`, `POST /api/account/avatar`, `POST /api/account/email/request-otp`, `POST /api/account/email/confirm-otp`, `POST /api/auth/change-password` | `buyer/profile.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 30 | หน้า Notifications: แสดงรายการแจ้งเตือนล่าสุด, กดอ่านทีละรายการและนำทางไปยังหน้าที่เกี่ยวข้อง (`target_route`/`target_params`), ปุ่มทำเครื่องหมายว่าอ่านทั้งหมด | `ui/pages/buyer/notifications.py` | `GET /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all` | `buyer/notifications.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 31 | หน้า Chat (ผู้ซื้อ): แชทกับร้าน real-time polling (`after_id`), ปุ่มคำถามแนะนำสำเร็จรูป 6 ข้อ (`QUICK_REPLIES`), ปุ่มถาม AI โดยเฉพาะ (`force_ai`), โมดอลฟอร์มให้ AI แนะนำไม้ 3 รุ่นตามสเปก/งบประมาณ | `ui/pages/buyer/chat.py`, `chat_bubble.py` | `GET /api/chat/messages`, `POST /api/chat/messages`, `GET /api/chat/quick-replies`, `POST /api/chat/quick-reply`, `POST /api/chat/recommend-rackets` | `buyer/chat.js`, `components/chat_bubble.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 32 | หน้า Admin Dashboard: การ์ดสรุปสถิติ (รายได้รวมแสดงเฉพาะ Owner ตาม `DASHBOARD_REVENUE`, แอดมินเห็น "เฉพาะเจ้าของร้าน"), กราฟยอดขายรายวัน, สินค้าขายดี 5 อันดับ, รายการสินค้า/ตัวเลือกที่สต็อกต่ำกว่าเกณฑ์ | `ui/pages/admin/dashboard.py` | `GET /api/admin/dashboard` | `admin/dashboard.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 33 | หน้า Admin Products: ค้นหา/กรองหมวดหมู่/แบรนด์/สถานะ/สลับดูถังขยะสินค้าที่ถูกลบ (พร้อมยอดขายสะสม), ปุ่มเพิ่มสินค้า, แก้ไข, ตั้งราคาโปร Flash Sale ด่วน, ซ่อน/แสดง, ลบ(Soft delete)/กู้คืน (เฉพาะ Owner), จัดการแบนเนอร์ด่วน | `ui/pages/admin/products.py` | `GET /api/admin/products`, `GET /api/admin/products/deleted`, `POST /api/admin/products/{id}/active`, `DELETE /api/admin/products/{id}`, `POST /api/admin/products/{id}/restore` | `admin/products.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 34 | หน้า Admin Product Form: เพิ่ม/แก้ไขสินค้าครบทุกฟิลด์ (ราคา/ต้นทุน/ราคาโปร/วันหมดโปร `DateTimePickerField`/สต็อกเมื่อไม่มีตัวเลือก), แกลเลอรีหลายรูป+ผูกสี+ตั้งรูปหลัก, สเปกไม้แบด (`RACKET_TECH_SPEC_FIELDS` + ตรวจ Balance Point mm), ตัวเลือกสินค้า (`product_options` + รูปตัวเลือก), ของแถม/บริการเสริม (`product_addons`) | `ui/pages/admin/product_form.py` | `GET /api/admin/products/{id}/edit`, `POST /api/admin/products`, `PUT /api/admin/products/{id}`, `POST /api/admin/products/{id}/images`, `PUT /api/admin/product-images/{id}/primary`, `DELETE /api/admin/product-images/{id}`, `POST /api/admin/products/{id}/options`, `DELETE /api/admin/options/{id}`, `PUT /api/admin/products/{id}/addons` | `admin/product_form.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 35 | หน้า Admin Categories (Owner): จัดการหมวดหมู่ (รูป, ผูกทุกแบรนด์หรือเลือกแบรนด์เฉพาะ `category_brands`, ซ่อน/ลบ/กู้คืน), จัดการแบรนด์ (โลโก้, ซ่อน/ลบ/กู้คืน), จัดการชุดตัวเลือกประจำหมวด (`option_groups` / `option_values`, ปุ่มเพิ่มน้ำหนักไม้ 3U–10U ด่วน, เรียงลำดับ) | `ui/pages/admin/categories.py` | `GET /api/admin/categories`, `POST /api/admin/categories`, `PUT /api/admin/categories/{id}`, `DELETE /api/admin/categories/{id}`, `POST /api/admin/categories/{id}/restore`, `POST /api/admin/brands`, `PUT /api/admin/brands/{id}`, `DELETE /api/admin/brands/{id}`, `POST /api/admin/brands/{id}/restore`, `POST /api/admin/option-groups`, `POST /api/admin/option-values` | `admin/categories.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 36 | หน้า Admin Orders & Order Detail: ค้นหา/กรองตามสถานะ+ช่วงวันที่+แบ่งหน้า, ดูรายละเอียดออเดอร์+สลิป(lightbox)+ใบเสร็จ PDF, บันทึกจัดส่ง (`CARRIERS` + เลขพัสดุ) พร้อมส่งอีเมลแจ้งเลขพัสดุ, อัปเดตเลขพัสดุ, ทำเครื่องหมายว่าส่งถึงแล้ว, ยกเลิกออเดอร์พร้อมเหตุผล | `ui/pages/admin/orders.py`, `admin/order_detail.py` | `GET /api/admin/orders`, `POST /api/admin/orders/{id}/ship`, `PUT /api/admin/orders/{id}/tracking`, `POST /api/admin/orders/{id}/delivered`, `POST /api/admin/orders/{id}/send-tracking-email` | `admin/orders.js`, `admin/order_detail.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 37 | หน้า Admin Payments: รายการสลิปรอตรวจสอบ, ดูรูปสลิปขนาดเต็ม (lightbox), ปุ่มอนุมัติสลิป (เปลี่ยนสถานะเป็น paid + ออกใบเสร็จ + ส่งอีเมลใบเสร็จ), ปุ่มปฏิเสธสลิปพร้อมระบุเหตุผล | `ui/pages/admin/payments.py` | `GET /api/admin/payments/pending`, `POST /api/admin/payments/{id}/verify`, `POST /api/admin/payments/{id}/reject` | `admin/payments.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 38 | หน้า Admin Coupons & Coupon Form (Owner): รายการคูปอง, ค้นหา, เปิด/ปิด, ลบ, สร้าง/แก้ไขคูปอง (percent/fixed/free_shipping, หมวดคูปอง, ขั้นต่ำ, จำกัดจำนวน, วันเริ่ม-หมดอายุ, ช่วงเวลาเก็บรายวัน, รีเซ็ตเที่ยงวัน `daily_reset_12`), จัดการกฎซื้อครบรับคูปองอัตโนมัติ (`coupon_rules`) | `ui/pages/admin/coupons.py`, `admin/coupon_form.py` | `GET /api/admin/coupons`, `GET /api/admin/coupons/{id}`, `POST /api/admin/coupons`, `PUT /api/admin/coupons/{id}`, `POST /api/admin/coupons/{id}/toggle`, `DELETE /api/admin/coupons/{id}`, `GET /api/admin/coupon-rules`, `POST /api/admin/coupon-rules`, `DELETE /api/admin/coupon-rules/{id}` | `admin/coupons.js`, `admin/coupon_form.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 39 | หน้า Admin Chat: รายชื่อห้องแชทลูกค้าเรียงตามข้อความล่าสุดพร้อมจุดแดงยังไม่อ่าน, ดูประวัติข้อความและตอบกลับลูกค้า real-time polling | `ui/pages/admin/chat.py` | `GET /api/admin/chat/threads`, `GET /api/chat/messages`, `POST /api/admin/chat/reply` | `admin/chat.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 40 | หน้า Admin Users (Owner): รายชื่อผู้ใช้ทั้งหมด กรองตาม role/ค้นหา, แสดงป้ายสถานะ ออนไลน์/ออฟไลน์/ถูกระงับ, สร้างแอดมินใหม่, แต่งตั้งผู้ซื้อเป็นแอดมินด้วยอีเมล, ดูรายละเอียดผู้ใช้แบบเต็ม, รีเซ็ตรหัสผ่าน(บังคับเปลี่ยนครั้งแรก), เตะออกจากระบบทุกเครื่อง, ระงับ/ปลดระงับบัญชี | `ui/pages/admin/users.py` | `GET /api/admin/users`, `GET /api/admin/users/{id}`, `POST /api/admin/users/staff`, `POST /api/admin/users/assign-admin`, `POST /api/admin/users/{id}/active`, `POST /api/admin/users/{id}/reset-password`, `POST /api/admin/users/{id}/revoke-sessions` | `admin/users.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |
| 41 | หน้า Admin Settings (Owner): ตั้งค่าร้าน & PromptPay & ความเร็วอนิเมชัน/หมวดคูปอง/ตัวเลือกเพิ่ม, ข้อมูลติดต่อร้าน+โลโก้, จัดการแบนเนอร์หน้าแรก, บันทึกรายจ่ายร้าน (`expenses`), ส่งออกรายงาน `.xlsx` (ดาวน์โหลดผ่านเบราว์เซอร์ + ตั้งค่าโฟลเดอร์ส่งออกอัตโนมัติรายเดือน), สำรอง/กู้คืนฐานข้อมูล, ดูข้อความด่วนจากแอดมิน (`staff_messages`), ดู Audit Log | `ui/pages/admin/settings.py` | `GET /api/admin/settings`, `PUT /api/admin/settings`, `PUT /api/admin/settings/contact`, `GET /api/admin/banners`, `POST /api/admin/banners`, `DELETE /api/admin/banners/{id}`, `GET /api/admin/expenses`, `POST /api/admin/expenses`, `DELETE /api/admin/expenses/{id}`, `POST /api/admin/export/xlsx`, `POST /api/admin/export/auto-config`, `GET /api/admin/backups`, `POST /api/admin/backups`, `POST /api/admin/backups/restore`, `GET /api/admin/staff-messages`, `GET /api/admin/audit-logs` | `admin/settings.js` | ✅ | ทดสอบผ่านทั้ง API และหน้าเว็บจริง (Chromium + E2E) |

## งานเบื้องหลังที่ต้องย้าย (กรอกใน P0-5)
| งาน | เดิมสั่งที่ไหน/เมื่อไหร่ | ย้ายไป | สถานะ |
|---|---|---|---|
| สำรองฐานข้อมูลตอนเปิด/ปิดแอป (`auto_backup_on_exit`) | `ui/app.py` (`_on_close`), `database/db.py` (`_backup_before_migration_if_needed`) | `server/jobs.py` + FastAPI `lifespan` (startup/shutdown) | ✅ |
| ล้างสถานะออนไลน์ค้างตอนเปิด/ปิด (`auth_service.clear_all_online`) | `ui/app.py` (`_start_backend`, `_on_close`) | `server/jobs.py` + `lifespan` (startup/shutdown) | ✅ |
| ยกเลิกออเดอร์ pending เกิน `unpaid_cancel_hours` (`order_service.auto_cancel_unpaid`) | `ui/app.py` (`_start_backend`), `buyer/orders.py`, `admin/orders.py` | `server/jobs.py` (startup + รอบทุก 5 นาที) และคงใน route รายการออเดอร์ | ✅ |
| รีเซ็ตคูปองรายวันตอนเที่ยง (`coupon_service.run_daily_noon_reset`) | `ui/app.py` (`_start_backend`, `_check_idle_timeout` ทุก 15 วินาที) | `server/jobs.py` (startup + รอบทุก 1 นาที) | ✅ |
| ส่งออกรายงานรายเดือนอัตโนมัติ (`export_service.auto_export_previous_month`) | `ui/app.py` (`_start_backend`) | `server/jobs.py` (startup + รอบทุก 60 นาที) | ✅ |
| อีเมลสรุปสต็อกต่ำ (`email_outbox_service.send_low_stock_digest`) | `services/email_outbox_service.py` | `server/jobs.py` (startup + รอบทุก 30 นาที) | ✅ |
| retry อีเมลที่ส่งไม่สำเร็จ (`email_outbox_service.retry_failed_outbox`) | `services/email_outbox_service.py` | `server/jobs.py` (รอบทุก 5 นาที) | ✅ |
| ล้าง OTP/session หมดอายุ (`repo_otp.purge_expired`, `repo_sessions.purge_expired`) | `services/otp_service.py`, `database/repo_sessions.py` | `server/jobs.py` (รอบทุก 15 นาที) | ✅ |
| Thread ตอบแชทด้วย AI (`chat_service._run_ai_reply`) และส่งอีเมล outbox (`email_outbox_service._job`) | `services/chat_service.py`, `services/email_outbox_service.py` | คง `threading.Thread` แต่ห่อด้วย `contextvars.copy_context().run` เพื่อส่งต่อ Session context | ✅ |

## การแก้ชั้นเดิม (services / database / core / utils)
> จดทุกครั้งที่แก้ไฟล์เดิมนอกเหนือจาก `core/session.py` — ไฟล์ · ฟังก์ชัน · เปลี่ยนอะไร · เหตุผล · เทสต์เดิมยังผ่านหรือไม่

| วันที่ | ไฟล์ | เปลี่ยนอะไร | เหตุผล | เทสต์เดิม |
|---|---|---|---|---|
| 2026-10-24 | `services/chat_service.py`, `services/email_outbox_service.py` | ห่อ `threading.Thread` ด้วย `contextvars.copy_context().run` | ตาม PLAN.md หัวข้อ 5.1 (P1-2) เพื่อให้ thread เบื้องหลังได้รับ Session context ของคำขอนั้น | ผ่าน 155/155 |
| 2026-10-24 | `database/repo_otp.py` | เพิ่มฟังก์ชัน `purge_expired(conn=None)` | ให้ `server/jobs.py` ล้างรหัส OTP ที่หมดอายุตามตารางงานเบื้องหลังใน PROGRESS.md | ผ่าน 155/155 |
| 2026-10-24 | `services/product_service.py` | เพิ่ม `record_recently_viewed` และเรียกเมื่อเปิด `get_product_detail` | ให้ส่วน "สินค้าที่ดูล่าสุด" บนหน้าแรกแสดงผลอัตโนมัติเมื่อผู้ใช้กดดูรายละเอียดสินค้า | ผ่าน 155/155 |
| 2026-10-24 | `utils/backup.py` | อ่าน `config.DB_PATH` / `config.BACKUP_DIR` แบบไดนามิก และรองรับ `?nolock=1` / `shutil.copy2` fallback | ให้สำรอง/กู้คืนฐานข้อมูลผ่าน API บนระบบไฟล์ 9p/FUSE และในชุดทดสอบที่ใช้ temp dir ได้โดยไม่เกิด `disk I/O error` | ผ่าน 155/155 |
| 2026-10-24 | `config.py` | เพิ่ม `HOST`, `PORT`, `SESSION_COOKIE_NAME`, `WEB_DIR` และรองรับทั้ง `SMTP_PASSWORD` และ `SMTP_PASS` | ตาม PLAN.md หัวข้อ 2, 3, 5.2 (P0-8, P1-17) | ผ่าน 155/155 |
| 2026-10-24 | `tests/test_order_flow.py` | เอา `"fastapi"` ออกจากรายการ `forbidden` ใน `test_theme_contrast_and_router_and_no_web_dependencies` | ตาม PLAN.md หัวข้อ 3 บรรทัด 80 และหัวข้อ 9 บรรทัด 16 ที่กำหนดให้ใส่ `fastapi` ใน `requirements.txt` และยกเลิกกฎห้ามใช้เว็บเฟรมเวิร์กเดิม | ผ่าน 155/155 |
| 2026-10-24 | `database/db.py`, `services/settings_service.py` | แคชการตรวจ header non-WAL + แชร์ page-cached connection บนระบบไฟล์ 9p และอ่าน `repo_settings.get_all()` ครั้งเดียวใน `get_shop_info`/`get_contact_info` | ลดเวลาตอบสนองของ `/api/bootstrap` และ `/api/home` จาก ~8.4s เหลือ 1.2–15ms (< 200ms ตามเกณฑ์ P3-5) โดยไม่เปลี่ยน schema หรือพฤติกรรมธุรกิจ | ผ่าน 155/155 |
| 2026-10-24 | `tests/test_order_flow.py` | เพิ่ม fallback path ชี้ไปยัง `legacy_desktop/` เมื่อย้าย `ui/` ไปไว้ใน `legacy_desktop/ui/` ตามข้อ P3-6 | ให้เทสต์เดิมที่ตรวจค่าคงที่ใน `ui.router`/`ui.theme` ยังรันผ่านได้หลังย้าย `ui/` ออกจากรากโปรเจกต์ | ผ่าน 155/155 |

## บันทึกการตัดสินใจ
- สร้างโฟลเดอร์ `/working_dir/c_a07cba1612756d11/pylibs` ที่มีโมดูล `bcrypt` (ผูกกับ `libcrypt.so.1` ของระบบ C รองรับ `$2b$12$` ตรงกับ `data/shop.db`) และ `qrcode` (ผูกกับ `reportlab.graphics.barcode.qrencoder` + `PIL.Image`) รวมถึง stub `tkinter`/`customtkinter` สำหรับรันเทสต์เดิมในสภาพแวดล้อมไร้จอ X11
- ใช้ `contextvars.ContextVar` ร่วมกับ metaclass `_SessionMeta` ใน `core/session.py` และซิงค์สถานะ `is_locked`/`last_activity_at` ต่อ `session_token` ทำให้รองรับทั้งโค้ดเดิมที่อ่าน `Session.current_user` แบบ attribute และการแยกเซสชันระหว่างผู้ใช้หลายคนบนเว็บ

## บันทึกปัญหา (อาการ → สาเหตุ → วิธีแก้)
- อาการ: รัน `unittest` ครั้งแรกไม่พบโมดูล `bcrypt`, `qrcode`, `customtkinter` เพราะ VM ปิดการติดตั้งแพ็กเกจผ่านอินเทอร์เน็ต
  สาเหตุ: แพ็กเกจบางตัวไม่ได้ติดตั้งไว้ใน `/usr/lib/python3.11` แต่มีไลบรารีระดับระบบ (`libcrypt.so.1` และ `reportlab` + `PIL`) อยู่แล้ว
  วิธีแก้: เขียน wrapper `bcrypt.py` (เรียก `libcrypt.so.1`) และ `qrcode` (เรียก `reportlab.graphics.barcode.qrencoder`) ไว้ใน `pylibs` แล้วทดสอบกับ hash จริงใน `data/shop.db` และ `test_promptpay.py` จนผ่านครบ 155/155 ข้อ
- อาการ: `backup_db()` โยน `sqlite3.OperationalError: disk I/O error` เมื่อรันผ่าน API บนระบบไฟล์ 9p/FUSE ของ VM
  สาเหตุ: `sqlite3.connect` โดยไม่ระบุ `?nolock=1` บน 9p/FUSE ทำ POSIX lock ไม่ได้ (ซึ่ง `database/db.py` แก้ไว้แล้วด้วย `?nolock=1`)
  วิธีแก้: ปรับ `utils/backup.py` ให้เชื่อมต่อไปยังไฟล์ SQLite ด้วย `?nolock=1` fallback และใช้ `shutil.copy2` เมื่อระบบไฟล์ไม่รองรับ online backup lock

## ความต่างที่ยอมรับ (หน้าตา/พฤติกรรมที่เว็บทำให้เหมือน 100% ไม่ได้)
- ในเครื่อง VM ไม่มี `_tkinter` และ Xvfb จึงไม่สามารถแคปภาพหน้าจอ CustomTkinter จากการรันจริงใน P0-9 ได้ แต่อาศัยการถอดโครงสร้าง สี ขนาด padding ฟอนต์ และข้อความภาษาไทยทุกตัวอักษรจากไฟล์ `ui/theme.py`, `ui/components/*.py` และ `ui/pages/**/*.py` โดยตรง

## สิ่งที่ผู้ใช้ต้องทำเอง (เติมตอนส่งมอบ)
- ใส่เลขพร้อมเพย์ + ชื่อบัญชีจริงในหน้าตั้งค่าร้าน
- ใส่ `GEMINI_API_KEY` (ถ้าต้องการให้ AI ตอบแชท) และตั้ง SMTP (ถ้าต้องการส่งอีเมลจริง) ใน `.env`
- **เปลี่ยนรหัสผ่านบัญชีตัวอย่าง** (owner/admin) ก่อนใช้งานจริงหรือก่อนเปิดให้เครื่องอื่นเข้าถึง
- ตัดสินใจเรื่องลบโฟลเดอร์ `legacy_desktop/` เมื่อมั่นใจว่าเว็บครบแล้ว

## สรุปเฟส
### สรุปเฟส 0
- สำรองโปรเจกต์ไว้ที่ `badminton_shop_backup/` และสร้าง Git commit ฐาน (`bd6b299`) เรียบร้อย
- เปลี่ยนไฟล์ความจำเดิม (`Workflow.md`, 652 บรรทัด) เป็น `LEGACY_PROGRESS.md` และตั้งค่าสภาพแวดล้อม Python จนรันชุดทดสอบเดิม 4 ไฟล์ (`test_promptpay`, `test_repos`, `test_services_basic`, `test_order_flow`) ผ่านครบ **155 / 155 ข้อ**
- สำรวจโค้ดหน้าจอเดิมครบทั้ง 30 หน้า (`ROUTE_TABLE`) และ 16 คอมโพเนนต์/ไฟล์ช่วย พร้อมบันทึกตารางแมปหน้า → service/API, ตารางงานเบื้องหลัง 9 รายการ และตารางพาริตี้ฟีเจอร์ 41 หัวข้อหลักครบถ้วน

### สรุปเฟส 1
- ปรับ `core/session.py` ให้เก็บสถานะด้วย `contextvars.ContextVar` แยกอิสระต่อคำขอ พร้อมซิงค์สถานะ `is_locked` และ `last_activity_at` ต่อ `session_token` และห่อ thread เบื้องหลังใน `chat_service` กับ `email_outbox_service` ด้วย `contextvars.copy_context().run`
- สร้างชั้น `server/` (`app.py`, `deps.py`, `serializers.py`, `jobs.py`, และ `routes/` ครบทุกโดเมนรวมกว่า 90 API endpoints) พร้อมการป้องกัน CSRF Origin, การป้องกันการเข้าถึงสลิป/ใบเสร็จของผู้อื่น และการกรอง `password_hash` อัตโนมัติทุกการตอบกลับ
- อัปเดต `main.py`, `config.py`, `requirements.txt`, `.env.example` และเขียนชุดทดสอบ API & ความปลอดภัยใน `tests/test_api_web.py` ผลทดสอบรวมผ่านครบ **160 / 160 ข้อ** (เทสต์เดิม 155/155 + เทสต์ API ใหม่ 5/5 ชุดใหญ่)

### สรุปเฟส 2
- สร้างระบบดีไซน์เว็บใน `web/css/` (`tokens.css`, `base.css`, `components.css`) ถอดสี Light/Dark ฟอนต์ `Kanit`/`Arimo` ขนาดปุ่มและการ์ดจาก `ui/theme.py` ครบถ้วน
- สร้างแกน SPA (`web/index.html`, `web/js/state.js`, `web/js/api.js`, `web/js/router.js`, `web/js/app.js`) และคอมโพเนนต์กลางครบ 16 ชิ้นใน `web/js/components/` (รวม `image_picker.js` ครอบรูป 3:4 / 1:1 บน `<canvas>`, `date_picker.js` ปฏิทินไทย พ.ศ., `payment_qr.js`, `order_timeline.js`, `product_card.js` นับถอยหลัง Flash Sale)
- สร้างหน้าผู้ซื้อครบ 18 หน้า (`web/js/pages/buyer/*.js`) และหน้าแอดมิน/เจ้าของร้านครบ 12 หน้า (`web/js/pages/admin/*.js`) รวม 30 หน้าตรงตาม `ROUTE_TABLE`
- ตรวจสอบไวยากรณ์ ES Module และการจับคู่ `import`/`export` ครบทั้ง 51 โมดูล และเปิดหน้าเว็บจริงทุกหน้าด้วย Headless Chromium ผ่านครบโดยไม่มี JS console error (`SEVERE = 0`)

### สรุปส่งมอบ (เฟส 3)
- **P3-1 & DoD #1, #4 (หน้าตาและครบ 30 หน้า):** รัน Headless Chromium เข้าชมครบทั้ง 30 หน้าในทุกบทบาท (Guest, Buyer, Admin, Owner) ทั้งโหมดสว่างและโหมดมืด พร้อมบันทึกภาพหน้าจอไว้ใน `docs/web_screens/01_guest_home.png` ถึง `38_dark_admin_dashboard.png` (รวม 38 ภาพ) โดยไม่มี error ในคอนโซลแม้แต่รายการเดียว
- **P3-2 & DoD #2 (ตารางพาริตี้ฟีเจอร์):** ทดสอบและติ๊กผ่าน `✅` ครบทั้ง 41 แถวในตารางพาริตี้ฟีเจอร์
- **P3-3 & DoD #3 (กฎธุรกิจและตารางสิทธิ์):** ทดสอบ Role × Route Matrix ทั้ง 30 หน้า × 4 บทบาท และรันชุดทดสอบเดิม 4 ไฟล์ (`155 ข้อ`) + ชุดทดสอบเว็บ/ความปลอดภัย/ประสิทธิภาพ (`6 ชุดใหญ่`) ผ่านครบ **161 / 161 ข้อ (`OK`)**
- **P3-4 (ความปลอดภัย):** ทดสอบป้องกัน CSRF ข้ามโดเมน (`403`), IDOR ข้ามบัญชีผู้ซื้อ (`403`), Path Traversal บนสลิป/ใบเสร็จ (`400/404`), การยกระดับสิทธิ์ข้ามบทบาท (`403`), และการเข้ารหัสข้อความผู้ใช้ด้วย `esc()` ป้องกัน XSS
- **P3-5 (ประสิทธิภาพ):** วัดความเร็ว API บนเครื่องเดียวกัน: `GET /api/bootstrap` ~1.3 ms, `GET /api/home` ~12 ms, `GET /api/products?category_id=1` ~5 ms, `GET /api/products?search=Yonex` ~8 ms, `GET /api/admin/dashboard` ~14 ms (ผ่านเกณฑ์ `< 200 ms` ทุกหน้า)
- **P3-6 & DoD #5 (แยกโค้ดเดสก์ท็อปเดิม):** ย้าย `ui/` ไปไว้ใน `legacy_desktop/ui/` และยืนยันว่าไม่มีการ import `customtkinter` หรือ `tkinter` ในเส้นทางรันเว็บ
- **P3-7, P3-8, P3-9 & DoD #6 (ความพร้อมรันและเอกสาร):** อัปเดต `README.md` และ `.env.example` พร้อมตรวจสอบด้วย `python main.py --check` ผ่านครบทั้ง 6 หมวด (30 หน้า, 186 API endpoints, 35 ตาราง SQLite, PromptPay QR, ฟอนต์ไทย/อังกฤษครบ)


---

## อัปเดตพิเศษ: รื้อและสร้าง UI หน้า LOGIN / SIGN UP ใหม่ ("AI.HERE Bad🅜-Zone") + ตั้งค่าโลโก้ & แบนเนอร์รองเท้า (Owner Only)

### 1. สรุปไฟล์ที่ลบโค้ด UI เดิม / แก้ไข / เพิ่มใหม่
- **รื้อ UI Login & Sign Up เดิมออกทั้งหมดและเขียนใหม่ตามสเปก (`login_signup_ui_spec.md` & `Login&Signup Change.pdf` 3 หน้า):**
  - `web/js/components/auth_layout.js`: ลบ `AuthSplitLayout` แบบเดิม (glitch welcome text / สินค้าจากตาราง products) ออกทั้งหมด แทนที่ด้วย `renderAuthExperience()` บนพิกัดอ้างอิง 1456×819 px, การ์ดหลัก 1294×657 px มุมโค้ง 50 px แบ่งครึ่ง 50/50 ที่ x=647 (647×657), โซนแบนเนอร์สีเหลือง `#FFB600` พร้อม radial glow + เงาพื้นวงรี (`#7A4E00`) + drop shadow ของรูปรองเท้า + สุ่มเปลี่ยนรูปรองเท้าทุก 5 วินาทีแบบไม่ซ้ำรูปเดิมติดกันพร้อม cross-fade 700ms และเอฟเฟกต์ลอยขึ้นลง, เงาตะเข็บกลาง (seam shadow กว้าง 110 px สลับด้านตามแบนเนอร์), ปุ่มแคปซูลสลับโหมด `SIGN UP` / `LOGIN` (260×60 px คร่อมรอยต่อกลางที่ 647,97), กรอบโลโก้ร้าน 115×115 px แบบ No BG (ไร้พื้นหลัง ไร้ขอบ ไร้วงกลม ไร้เงา), ข้อความแบรนด์ `AI.HERE Bad🅜-Zone` มุมบนขวาเฉพาะหน้า Login, การ์ดฟอร์ม Login (449×411 px) และโซนฟอร์ม Sign Up เลื่อนขึ้นลงได้ (การ์ด 451×949 px ระยะเลื่อน 503 px แบนเนอร์และปุ่ม Pill ไม่ขยับตาม) พร้อมอนิเมชันสลับฝั่ง 650ms (`easeInOutCubic`)
  - `web/js/pages/buyer/login.js` และ `web/js/pages/buyer/register.js`: เปลี่ยนให้เรียก `renderAuthExperience()` โดยคงการเชื่อมต่อฟังก์ชันเดิมครบทุกปุ่ม (เข้าสู่ระบบ, ลืมรหัสผ่านด้วย OTP, แอดมินลืมรหัส/ติดต่อเจ้าของ, สลับหน้า Login⇄Sign Up, เข้าชมสินค้าโดยไม่ล็อกอิน, ส่งรหัส OTP และยืนยัน OTP สร้างบัญชี)
  - `web/css/components.css`: ลบคลาส `.auth-stage` / `.auth-split` / `.auth-showcase` เดิมออกทั้งหมด แทนที่ด้วย `.auth2-*` ตามสเปกพิกัดและเงาทั้ง 5 จุด
  - `legacy_desktop/ui/components/auth_layout.py`: อัปเดตคลาส `AuthSplitLayout` ฝั่ง legacy ให้ปลอดจากโค้ด glitch/คำทักทายเก่าและชี้ไปยังระบบแบนเนอร์/โลโก้ใหม่
- **เพิ่มรูปแบนเนอร์รองเท้าต้นฉบับพื้นหลังโปร่งใส (PNG) 2 รูปเริ่มต้น:**
  - `assets/images/login_banners/vs169.png` (ตัดพื้นหลังสีดำจาก `VS169.jpg` ต้นฉบับ)
  - `assets/images/login_banners/power_cushion_shb101cr.png` (ตัดพื้นหลังสีดำจาก `POWER CUSHION SHB101CR.jpg` ต้นฉบับ)
- **เพิ่มระบบจัดการโลโก้ร้าน (No BG) และแบนเนอร์หน้า Login & Sign Up (สูงสุด 7 รูป) เฉพาะ Owner:**
  - `web/js/pages/admin/settings.js`: เพิ่ม **ส่วน A: โลโก้ร้านสำหรับหน้า Login & Sign Up (No BG)** (พรีวิวตารางหมากรุก 115×115 px แบบ contain, ปุ่มอัปโหลดโลโก้ PNG/WEBP/JPG ย่อด้านยาวไม่เกิน 1024 px, ปุ่มลบโลโก้) และ **ส่วน B: แบนเนอร์หน้า Login & Sign Up** (แสดงรายการรูปพร้อมตัวนับ `n / 7`, ปุ่มเพิ่มหลายไฟล์รวมไม่เกิน 7 รูป, ปุ่มเลื่อนลำดับซ้าย/ขวา, ปุ่มลบรายรูป, และปุ่มดูตัวอย่างหน้า Login & Sign Up ทันที)
- **ชั้นฐานข้อมูล / Repository / Service / API (แก้เท่าที่จำเป็นตามข้อ 11):**
  - `config.py`: เพิ่ม `LOGIN_BANNERS_DIR`, `DEFAULT_LOGIN_BANNER_FILES`, `LOGO_MAX_SIDE = 1024`, และคีย์ `store_logo_path` ใน `DEFAULT_SETTINGS`
  - `utils/image_utils.py`: รองรับการคงพื้นหลังโปร่งใส (`.png` RGBA) สำหรับไฟล์ PNG และ WEBP ที่อัปโหลดเป็นโลโก้ร้านและแบนเนอร์รองเท้า
  - `database/db.py` และ `database/seed.py`: เพิ่มตาราง `login_banners` (`CREATE TABLE IF NOT EXISTS login_banners (id, file_path, sort_order, created_at)`) และ seed รูปเริ่มต้น 2 รูปเฉพาะครั้งแรกที่ติดตั้ง (`login_banners_seeded`)
  - `database/repo_banners.py` และ `services/banner_service.py`: เพิ่มฟังก์ชัน `list_login_banners`, `add_login_banners`, `reorder_login_banners`, `delete_login_banner` จำกัดสูงสุด `MAX_LOGIN_BANNERS = 7` และตรวจสิทธิ์ `permissions.SETTINGS_MANAGE` (เฉพาะ Owner)
  - `services/settings_service.py`: ซิงค์ `store_logo_path` กับ `shop_logo_path` และรองรับการลบโลโก้ร้าน
  - `services/auth_service.py`: ปรับให้ช่องเบอร์โทรศัพท์และที่อยู่จัดส่งเริ่มต้นในหน้า Sign Up เป็นตัวเลือกเสริม (ไม่บังคับกรอกตามดีไซน์ที่ไม่มี `*`) แต่หากผู้สมัครกรอกข้อมูลที่อยู่มา ระบบจะตรวจสอบและบันทึกเป็นที่อยู่จัดส่งเริ่มต้นให้อัตโนมัติเหมือนเดิม
  - `server/routes/auth.py`, `server/routes/coupons_settings.py`, `server/routes/admin_ops.py`: เพิ่ม `GET /api/auth/ui-config`, `GET /api/login-banners`, `GET/POST/PUT/DELETE /api/admin/login-banners`, และ `POST/DELETE /api/admin/settings/logo`

### 2. เช็คลิสต์ตรวจรับตาม `login_signup_ui_spec.md` ข้อ 14
- [x] เปิดแอปแล้วเจอหน้า Login: แบนเนอร์ซ้าย ฟอร์มขวา สัดส่วน 50/50 ตรงตาม PDF หน้า 1 (`docs/web_screens/06_guest_login.png`)
- [x] Pill กึ่งกลางพอดี ซีกซ้ายขาว "SIGN UP" ซีกขวาเหลือง "LOGIN"; กดได้ทั้งสองซีก
- [x] กดสลับแล้วแบนเนอร์เลื่อนไปขวา ฟอร์มสลับ + fade ข้อความ Pill สลับซีกและสี ตรงกับ PDF หน้า 2 (`docs/web_screens/07_guest_register.png`)
- [x] Sign Up เลื่อนขึ้นลงได้ ตรงกับ PDF หน้า 2→3 ส่วนแบนเนอร์และ Pill ไม่ขยับ
- [x] เงาครบ: เงาการ์ดหลัก เงาตะเข็บกลาง เงาการ์ดฟอร์ม เงาพื้นใต้รองเท้า เงาของรูปรองเท้า
- [x] โลโก้ไม่มีขอบ/พื้นหลัง/วงกลม และอัปโหลดได้เฉพาะ Owner (`docs/web_screens/36_admin_settings.png`)
- [x] แบนเนอร์สุ่มเปลี่ยนรูปได้ ไม่ซ้ำติดกัน, เพิ่มได้ไม่เกิน 7 รูป, ลบได้, 0 รูปไม่พัง
- [x] ปุ่มทุกปุ่มเรียก logic เดิมได้ครบ (login, OTP, สมัคร, เข้าชมแบบผู้เยี่ยมชม)
- [x] UI Login/Sign Up เก่าถูกลบจริง ไม่มีโค้ดตกค้างที่ import ไม่ได้
- [x] หน้าอื่นของแอปทำงานเหมือนเดิม ไม่มีไฟล์ที่ไม่เกี่ยวข้องถูกแก้ (ผ่านชุดทดสอบทั้งหมด 167/167 ข้อ)
- [x] อัปเดต `PROGRESS.md` เรียบร้อย

### 3. การปรับปรุงเพิ่มเติมตาม Feedback (แก้ไขอนิเมชันปุ่มแคปซูล, ขอบมน 12px, พื้นหลังตัวอักษรวิ่งเฉียง -40° และเงาวงรีใต้รองเท้า)
- **ปุ่มแคปซูล `SIGN UP` | `LOGIN` และการสลับฉาก (`web/js/components/auth_layout.js`, `web/css/components.css`):**
  - ล็อกตำแหน่งคำไม่ให้สลับฝั่ง (`ซ้าย = SIGN UP`, `ขวา = LOGIN` ตลอดเวลา) เปลี่ยนเฉพาะสีพื้นหลังของแต่ละซีก (`#FFB600` เมื่ออยู่ในโหมดนั้น และ `#FFFFFF` เมื่อเป็นอีกโหมด) กดฝั่ง `LOGIN` ไปหน้า Login และกดฝั่ง `SIGN UP` ไปหน้า Sign Up ทันทีโดยตัวหนังสือไม่จางหาย
  - ผูกเงาตะเข็บกลาง (`box-shadow`) เข้ากับขอบของ `.auth2-banner-zone` โดยตรง ทำให้เงาเคลื่อนที่ตามแบนเนอร์อย่างลื่นไหลตลอด 650ms ไม่เกิดอาการเงากระโดดหรือกลับด้านระหว่างสลับฉาก
- **ลดความโค้งมนของกล่องกรอกข้อมูล (`.auth2-login-card`, `.auth2-signup-card`):**
  - ปรับ `border-radius` จาก `38px` ลงเป็น `12px` (อยู่ในช่วง 10–15 px ตามที่กำหนด)
- **พื้นหลังสุดแบบโค้ดตัวอักษรวิ่งเฉียง -40 องศา (`.auth2-bg-pattern`):**
  - สร้างด้วยโค้ด HTML/CSS/JS บนพื้นหลังสี `#E9E9E9` เอียง `-40deg` แถวคู่และแถวคี่วิ่งสวนทางกันเฉียงขึ้น-ลงแบบสลับฟันปลาอย่างช้าๆ (`75s linear infinite`) โดยสุ่มลำดับคำทั้ง 5 คำ: `BADMINTON`, `AI.HERE BADM`, `LEGEND`, `WELCOME`, `BAD ZONE`
- **รูปสินค้าตัวอย่าง No BG และเงาวงรีเบลอใต้สินค้า (`assets/images/login_banners/vs169.png`, `power_cushion_shb101cr.png`):**
  - แนบไฟล์ PNG พื้นหลังโปร่งใส (No BG) ทั้ง 2 รูปไว้ใน `assets/images/login_banners/` พร้อมตั้งค่าเริ่มต้นใน `login_banners` (Owner แก้ไข/ลบ/เพิ่มภายหลังได้ในหน้าตั้งค่าร้าน)
  - นำ `filter: drop-shadow(...)` ออกจากตัวรูปรองเท้า (`filter: none`) และใช้เฉพาะเงาวงรีเบลอ (`.auth2-ground-shadow-oval`) วางไว้ด้านใต้รูปรองเท้า


---

## อัปเดตใหญ่ตามคำสั่งแก้ไข 5 ส่วน (`AI.HERE_fix_instructions.md` & `Fixed.pdf`) + 3 ฟีเจอร์สำคัญเพิ่มเติม

### 1. สรุปการแก้ไขทั้ง 8 หัวข้อ

1. **ส่วนที่ 1 — ชื่อร้าน (`shop_name`) แสดงตรงตามที่ Owner ตั้งทุกจุดทั่วทั้งระบบ:**
   - `web/js/components/navbar.js`, `web/js/state.js`, `web/js/pages/buyer/home.js`, `web/js/pages/admin/settings.js`: ดึง `shop_name` จากการตั้งค่าร้านมาแสดงบนโลโก้/ชื่อร้านมุมซ้ายบนของ Navbar (แทนข้อความตายตัว `"Badminton Pro Shop"`), ชื่อแท็บเบราว์เซอร์ (`document.title`), ป้ายแบนเนอร์หน้าแรก (`<shop_name> Official`), หัวข้อหน้าแรก, ศูนย์รวมคูปอง, Footer และชื่อ Facebook fallback
   - รักษาตัวอักษรทุกตัวที่ Owner พิมพ์ตรงตามต้นฉบับ 100% (รวมตัวอักษรตัวยก เช่น `Ai.HRER BADᴹᵀ Zone`, จุด, เว้นวรรคภายใน และตัวพิมพ์ใหญ่-เล็ก โดยไม่แปลง `.toUpperCase()`) พร้อมตัดคำด้วย `text-overflow: ellipsis` และแสดง `title` tooltip เมื่อชื่อร้านยาวเกินพื้นที่ Navbar
   - `database/repo_settings.py`, `services/settings_service.py`, `services/banner_service.py`, `services/email_service.py`: เพิ่มระบบแคชหน่วยความจำที่ล้างแคชทันทีเมื่อ Owner บันทึกค่าใหม่ ทำให้ชื่อร้านบน Navbar และชื่อแท็บเบราว์เซอร์เปลี่ยนทันทีโดยไม่ต้องรีเฟรชหน้าเว็บเอง และใช้ `shop_name` ในหัวข้อแบนเนอร์เริ่มต้น รวมถึงผู้ส่งอีเมล (`SMTP_FROM` แบบไดนามิก)

2. **ส่วนที่ 2 — กริด "สินค้าแนะนำยอดนิยม" แถวละ 5 ชิ้นเต็มความกว้าง (`.wrap-grid--cols-5`):**
   - `web/js/pages/buyer/home.js`, `web/css/components.css`, `server/routes/products.py`: เพิ่มคลาสเฉพาะ `.wrap-grid--cols-5` (`grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 18px; width: 100%`) ให้การ์ดสินค้าในส่วนสินค้าแนะนำยอดนิยมขยายเต็มคอลัมน์อย่างสมดุลโดยคงสัดส่วนภาพ 1:1 เดิม และกำหนดค่าคงที่ `RECOMMEND_COUNT = 15` (3 แถว × 5 ชิ้น) ทั้งตอนโหลดหน้าแรกและตอนกดปุ่ม `"🎲 สุ่มสินค้าใหม่"`
   - รองรับ Responsive Breakpoints (`5 → 4 → 3 → 2` คอลัมน์ตามความกว้างหน้าจอ) โดย **ไม่แก้ไข `.wrap-grid` ตัวกลาง** และไม่กระทบกริดสินค้าในหน้าอื่น

3. **ส่วนที่ 3 — หน้าโปรไฟล์: โหมดอ่านอย่างเดียว + ปุ่มแก้ไขข้อมูล + ยืนยันรหัสผ่านปัจจุบัน:**
   - `web/js/pages/buyer/profile.js`, `web/js/components/image_picker.js`: เริ่มต้นในโหมดอ่านอย่างเดียว (`readonly`/`disabled` บนช่อง Username, ชื่อ-นามสกุล, เบอร์โทรศัพท์, อีเมล, ปุ่มเปลี่ยนรูปโปรไฟล์ และปุ่มส่ง OTP; ซ่อนปุ่มบันทึกโปรไฟล์) เมื่อกด `"แก้ไขข้อมูลของฉัน"` จึงปลดล็อกช่องทั้งหมดและแสดงปุ่ม `"ยกเลิกการแก้ไข"` (คืนค่าข้อมูลเดิมจาก `currentProfile`) คู่กับ `"บันทึกโปรไฟล์"`
   - เมื่อกด `"บันทึกโปรไฟล์"` ระบบตรวจสอบความถูกต้องของข้อมูลผ่าน `POST /api/account/profile/validate` ก่อน หากผ่านจึงเปิด Modal (`openModal`) ให้กรอกรหัสผ่านปัจจุบัน 1 ครั้งเพื่อยืนยันตัวตน
   - `services/auth_service.py`, `services/account_service.py`, `server/routes/account.py`: บังคับตรวจรหัสผ่านปัจจุบันกับ `password_hash` ที่ฝั่งเซิร์ฟเวอร์ทุกครั้ง (`PUT /api/account/profile`) พร้อมกลไกจำกัดจำนวนครั้งที่กรอกผิด (Rate Limit 5 ครั้งใน 5 นาที)

4. **ส่วนที่ 4 — ระบบรีวิวสินค้า (ปุ่มลัดบนการ์ดออเดอร์ + อัปโหลดรูป/วิดีโอ 0–5 ไฟล์ + แสดงตัวเลือกที่สั่ง):**
   - **4.1 หน้า "ออเดอร์ของฉัน" (`web/js/pages/buyer/orders.js`, `services/order_service.py`):** เพิ่มข้อมูล `awaiting_review_count`, `is_reviewed`, `reviewed`, `can_review` ในรายการออเดอร์และรายการสินค้าย่อย แสดงปุ่ม `"⭐ เขียนรีวิวสินค้า"` คู่กับปุ่ม `"ดูรายละเอียด"` บนการ์ดออเดอร์ที่สถานะ `completed` ทันที (พร้อมปุ่มรีวิวรายสินค้าสำหรับออเดอร์ที่มีหลายรายการ และป้าย `"✓ รีวิวแล้ว"` สำหรับสินค้าที่รีวิวเสร็จแล้ว)
   - **4.2 หน้า "เขียนรีวิวสินค้า" (`web/js/pages/buyer/write_review.js`, `database/db.py`, `database/repo_reviews.py`, `services/review_service.py`, `server/routes/reviews_notifications_chat.py`, `config.py`):** จัดเลย์เอาต์การ์ดให้อยู่กึ่งกลางหน้า (`max-width: 760px`) กระชับสวยงาม รองรับการอัปโหลดรูปภาพ (`.jpg`, `.jpeg`, `.png`, `.webp` ไม่เกิน 5 MB/ไฟล์) และวิดีโอ (`.mp4`, `.webm`, `.mov` ไม่เกิน 50 MB/ไฟล์) รวมกัน **0–5 ไฟล์** พร้อมพรีวิวภาพ/วิดีโอ ตัวนับ `n/5 ไฟล์` ปุ่มลบรายไฟล์ และการตรวจนามสกุล + ขนาด + Magic Bytes ที่ฝั่งเซิร์ฟเวอร์ บันทึกลงตารางใหม่ `review_media` และโฟลเดอร์ `assets/reviews/` แบบ Atomic (ลบไฟล์ทิ้งอัตโนมัติหากเกิดข้อผิดพลาดกลางทาง)
   - **4.3 การแสดงรีวิวในหน้าสินค้า (`web/js/pages/buyer/product_detail.js`, `database/repo_reviews.py`, `services/review_service.py`):** ดึงข้อมูล `option_label` ของสินค้านั้นในออเดอร์นั้นและรายการ `media` แบบ Batch Query (ไม่เกิด N+1 query) แสดงข้อความ `"ตัวเลือกที่สั่ง: <ตัวเลือก>"` เฉพาะของสินค้านั้น (ถ้าสั่งหลายตัวเลือกในออเดอร์เดียวกันจะคั่นด้วย `, ` และซ่อนบรรทัดนี้หากไม่มีตัวเลือก) พร้อมแสดงรูปภาพแนบ (คลิกดูภาพขยายใน Lightbox Modal ได้) และวิดีโอแนบ (`<video controls preload="metadata">`)

5. **ส่วนที่ 5 — ระบบการแจ้งเตือนแบบใหม่ทั่วทั้งเว็บ (Inline สีแดงใต้ช่อง + Toast เลื่อนจากมุมขวาบน 5 วินาที):**
   - `web/js/components/toast.js`, `web/css/components.css`, `web/js/components/dialogs.js`: สร้างคอมโพเนนต์ `showToast(message, kind)` (`'success'` สีเขียว / `'error'` สีแดง) ตำแหน่งมุมบนขวา (`position: fixed; z-index: 2500`) เลื่อนเข้าจากขวา ค้างไว้ 5 วินาที แล้วเลื่อนกลับออกไปทางขวาพร้อมลบ DOM อัตโนมัติ ซ้อนหลายแจ้งเตือนได้ รองรับ `role="alert"` / `role="status"` และ `prefers-reduced-motion`
   - กติกาการแจ้งเตือนทั่วทั้งเว็บ: กรณี **ผิดพลาด** แสดงข้อความสีแดงใต้ช่องกรอก (`setFieldError` พร้อมขอบช่องสีแดงที่ล้างออกทันทีเมื่อพิมพ์แก้ไข) **คู่กับ Toast สีแดง 5 วินาที**; กรณี **สำเร็จ** แสดง **Toast สีเขียว 5 วินาที** อย่างเดียว (โดยคง Modal ยืนยันการตัดสินใจ `confirm`, `askReason`, ยืนยันรหัสผ่าน, OTP และระบบแจ้งเตือนกระดิ่งไว้ครบถ้วน)
   - ปรับปรุงหน้าอ้างอิง `web/js/pages/admin/order_detail.js` (ลบข้อความแดงเล็กใต้หัวออเดอร์, ตรวจรูปแบบเลขพัสดุ `A-Z, 0-9, -` ยาว 4–40 ตัว แสดงข้อความแดงใต้ช่องเลขพัสดุคู่กับ Toast แดงเมื่อผิด และ Toast เขียวเมื่อบันทึกสำเร็จ) รวมถึงทุกหน้าใน `web/js/pages/buyer/`, `web/js/pages/admin/` และ `web/js/components/`

6. **ฟีเจอร์เพิ่มเติมที่ 1 — การพิมพ์เพิ่ม/แก้ไขที่อยู่จัดส่ง แจ้งจุดที่ทำผิดใต้ช่องทันที (Real-Time Per-Field Validation):**
   - `web/js/pages/buyer/addresses.js`, `web/js/components/auth_layout.js`, `services/account_service.py`, `server/routes/account.py`: เพิ่มฟังก์ชันตรวจสอบที่อยู่จัดส่งรายช่องแบบเรียลไทม์ (`recipient`, `phone`, `address_line`, `district`, `province`, `postcode`) แสดงข้อความภาษาไทยระบุสาเหตุที่ผิดพลาดใต้ช่องนั้นทันทีขณะพิมพ์หรือเลื่อนออก (เช่น เบอร์โทรไม่ขึ้นต้นด้วย 0 หรือยังไม่ครบ 10 หลัก, รหัสไปรษณีย์มีตัวอักษรปนหรือยังไม่ครบ 5 หลัก, บ้านเลขที่สั้นเกินไป) เพื่อให้ผู้ใช้แก้ไขได้ทันที

7. **ฟีเจอร์เพิ่มเติมที่ 2 — ปฏิทินและตารางเลือกเวลาด่วน (Interactive Calendar & Time-Table Picker) สำหรับตั้งเวลา Flash Sale และคูปอง:**
   - `web/js/components/date_picker.js`, `web/js/pages/admin/products.js`, `web/js/pages/admin/product_form.js`, `web/js/pages/admin/coupon_form.js`: อัปเกรดตัวเลือกวันและเวลาให้มี **ปุ่มลัดเลือกวัน** (`วันนี้`, `พรุ่งนี้`, `+3 วัน`, `+7 วัน`, `+30 วัน`) และ **ตารางเวลาด่วน (Time-Slot Grid)** (`00:00`, `06:00`, `08:00`, `09:00`, `10:00`, `12:00`, `14:00`, `16:00`, `18:00`, `20:00`, `22:00`, `23:59` น. รวมถึงตารางชั่วโมง `00:00–23:00`) พร้อมปุ่มลัดตั้งเวลา Flash Sale ในคลิกเดียว

8. **ฟีเจอร์เพิ่มเติมที่ 3 — ช่องแชทรองรับการส่งรูปภาพได้ทั้งลูกค้า พนักงานแอดมิน และเจ้าของร้าน:**
   - `database/db.py`, `database/repo_chat.py`, `services/chat_service.py`, `server/routes/reviews_notifications_chat.py`, `server/routes/admin_ops.py`, `web/js/components/chat_bubble.js`, `web/js/pages/buyer/chat.js`, `web/js/pages/admin/chat.js`: เพิ่มคอลัมน์ `image_path` ในตาราง `chat_messages` แบบไม่กระทบข้อมูลเดิม เพิ่มปุ่ม `"📷 ส่งรูป"` พร้อมแถบพรีวิวรูปก่อนส่งทั้งในหน้าแชทฝั่งลูกค้า (`buyer/chat.js`) และหน้าแชทฝั่งแอดมิน/เจ้าของร้าน (`admin/chat.js`) แสดงรูปภาพในบอลลูนแชทพร้อมคลิกดูภาพขยายได้ทันที

---

### 2. โครงสร้างฐานข้อมูลที่เพิ่มใหม่ (Additive Schema ใน `database/db.py`)
- ตารางใหม่ `review_media`:
  - `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - `review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE`
  - `kind TEXT NOT NULL CHECK(kind IN ('image', 'video'))`
  - `file_path TEXT NOT NULL`
  - `sort_order INTEGER DEFAULT 0`
  - `created_at TIMESTAMP DEFAULT (datetime('now','localtime'))`
  - ดัชนี `ix_review_media_review ON review_media(review_id, sort_order, id)`
- คอลัมน์ใหม่ในตาราง `chat_messages`:
  - `image_path TEXT` (ผ่าน `_ensure_column(cursor, "chat_messages", "image_path", "TEXT")`)

---

### 3. ข้อสมมติและค่าคงที่ที่ใช้ (ปรับแต่งได้ใน `config.py` / โค้ด)
- `RECOMMEND_COUNT = 15` (แสดงสินค้าแนะนำยอดนิยม 3 แถว × 5 คอลัมน์ = 15 ชิ้น ใน `web/js/pages/buyer/home.js`)
- `MAX_REVIEW_FILES = 5` (อัปโหลดรูปภาพและวิดีโอในรีวิวรวมกันได้ 0–5 ไฟล์ ใน `config.py`)
- `MAX_REVIEW_IMAGE_BYTES = 5 * 1024 * 1024` (รูปภาพรีวิวไม่เกิน 5 MB ต่อไฟล์ ใน `config.py`)
- `MAX_REVIEW_VIDEO_BYTES = 50 * 1024 * 1024` (วิดีโอรีวิวไม่เกิน 50 MB ต่อไฟล์ ใน `config.py`)

---

### 4. ผลการตรวจสอบและชุดทดสอบก่อนส่งมอบ
- [x] `python main.py --check` ผ่านครบทุกหมวด (30 หน้า, 198 API endpoints, 37 ตาราง SQLite)
- [x] `node --input-type=module --check` ผ่านครบทั้ง 51 ไฟล์ JavaScript ES Modules
- [x] ชุดทดสอบอัตโนมัติใน `tests/` (`test_promptpay`, `test_repos`, `test_services_basic`, `test_order_flow`, `test_api_web`, `test_web_parity_and_security`) ผ่านครบ **168 / 168 ข้อ (`OK`)**

---

## บันทึกการปรับปรุงระบบ OTP ยืนยันทางอีเมลจริงและความปลอดภัย (2026-10-27)

| วันที่ | ไฟล์ | สิ่งที่แก้ | เหตุผล | ผลเทสต์ |
|---|---|---|---|---|
| 2026-10-27 | `.env.example` | ลบ `OTP_DEV_ECHO` เพิ่ม `OTP_SECRET`, `SMTP_FROM_NAME` และคำอธิบายภาษาไทยพร้อมแยกโหมด A (Local) และโหมด B (HTTPS Server) | ให้ผู้ใช้ตั้งค่าอีเมลผู้ส่งและคีย์ลับ HMAC ได้ชัดเจนปลอดภัยทั้งในเครื่องและบนเซิร์ฟเวอร์จริง | ผ่าน (169/169) |
| 2026-10-27 | `config.py`, `main.py`, `server/app.py` | ลบ `OTP_DEV_ECHO` เพิ่มการอ่าน `OTP_SECRET`, `SMTP_FROM_NAME` และฟังก์ชัน `check_otp_and_smtp_startup_warnings()` แจ้งเตือนตอนเริ่มระบบโดยไม่พิมพ์ค่าลับ | ป้องกันการลืมตั้งค่า `OTP_SECRET` และ SMTP ในโหมดใช้งานจริง (`COOKIE_SECURE=1`) และตัดโหมดทดสอบทิ้ง | ผ่าน (169/169) |
| 2026-10-27 | `services/email_service.py`, `services/contact_service.py` | ลบกิ่ง `dev_echo` รองรับทั้งพอร์ต 587 (`STARTTLS`) และ 465 (`SMTP_SSL`) พร้อมข้อความผิดพลาดภาษาไทยที่ไม่เปิดเผยรหัสผ่าน SMTP และให้ผู้เรียกจุดอื่นจัดการข้อผิดพลาดได้อย่างปลอดภัย | ส่งอีเมลจริงอย่างปลอดภัยและไม่ทำให้ฟีเจอร์อีเมลใบเสร็จ/เลขพัสดุ/สต็อกต่ำ/อีเมลด่วนล้มเมื่อยังไม่ตั้งค่า SMTP | ผ่าน (169/169) |
| 2026-10-27 | `database/db.py`, `database/repo_otp.py` | เพิ่ม migration `otp_hmac_migrated_v1` ยกเลิก OTP เก่าที่ค้างอยู่ เพิ่ม `delete_otp`/`delete_email_change_otp` และปรับ `mark_used`/`mark_email_change_used` ให้เป็นแบบอะตอมมิก (`WHERE id = ? AND used_at IS NULL`) | ป้องกัน race condition ตอนยืนยันรหัสซ้ำพร้อมกัน และลบ OTP ทันทีเมื่อส่งอีเมลไม่สำเร็จ | ผ่าน (169/169) |
| 2026-10-27 | `services/otp_service.py`, `services/auth_service.py` | เปลี่ยนแฮชเป็น `HMAC-SHA256` ด้วย `OTP_SECRET` ผสม `email + purpose + user_context` แยกเทมเพลตอีเมล Multipart (Plain text + HTML ตาราง inline CSS ธีมเหลือง-ดำ-ขาว สองภาษา พร้อม `html.escape`) เพิ่มตัวจำกัดอัตราต่อ IP (10 ครั้ง/10 นาที) และปรับข้อความลืมรหัสผ่านให้เหมือนกันทุกกรณี | ปิดช่องโหว่การเดารหัส การใช้รหัสข้าม purpose การเดาบัญชีผู้ใช้ และ XSS ในอีเมล HTML | ผ่าน (169/169) |
| 2026-10-27 | `server/routes/auth.py`, `server/routes/account.py` | ลบ `dev_otp`/`otp_code_dev` ออกจากทุก API response และเชื่อมต่อตัวจำกัดอัตราต่อ IP ตอบ HTTP 429 พร้อมข้อความไทยบนทั้ง 8 OTP endpoints | ป้องกันการรั่วไหลของรหัส OTP ใน API response และป้องกันการยิงสแปมขอ/เดารหัส OTP | ผ่าน (169/169) |
| 2026-10-27 | `web/js/components/auth_layout.js`, `web/js/pages/buyer/profile.js` | ลบการอ่านและเติม `dev_otp`/`otp_code_dev` อัตโนมัติ แสดงข้อความส่งรหัสไปที่อีเมลแบบย่อ (`xx***@domain`) เพิ่มตัวนับถอยหลัง 60 วินาทีบนปุ่มขอรหัสใหม่ และใช้ `textContent` แสดงข้อความ | ให้ขั้นตอน UX บนหน้าเว็บสมบูรณ์ปลอดภัยตามกติกาการแจ้งเตือนของโปรเจกต์โดยไม่มีรหัสทดสอบรั่วไหล | ผ่าน (169/169) |
| 2026-10-27 | `tests/test_order_flow.py`, `tests/test_api_web.py`, `tests/test_web_parity_and_security.py`, `README.md` | อัปเดตเทสต์เดิมให้ใช้ `mock` ของ `email_service.send_mail` เพิ่มชุดทดสอบความปลอดภัย OTP และอีเมล HTML ครบทุกกรณี และอัปเดตคู่มือ `README.md` ภาษาไทย | ยืนยันความถูกต้องครบทุกเงื่อนไขโดยไม่ส่งอีเมลจริงตอนรันเทสต์ และมีคู่มือพร้อมใช้งานจริง | ผ่าน (169/169) |

