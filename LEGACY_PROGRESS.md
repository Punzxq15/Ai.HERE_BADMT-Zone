# PROGRESS.md — แอปร้านขายอุปกรณ์แบดมินตัน (Badminton Pro Shop)

> **ไฟล์นี้คือความจำของโปรเจกต์** ทุกแชทใหม่ให้ Claude อ่านไฟล์นี้ก่อนเริ่มงานเสมอ
> อัปเดตล่าสุด: 2026-10-12 — **จบส่วน A–G ครบทุกส่วนแล้ว** (main.py + README + สำรองอัตโนมัติตอนปิดแอป + ตรวจทั้งแอปบน GUI จริง) · เหลือเฉพาะงานของผู้ใช้: ใส่เลขพร้อมเพย์/คีย์ AI, **เปลี่ยนรหัสผ่านบัญชีตัวอย่าง (FIX-16)**, ลองรันบน Windows ของตัวเอง · AI อัปเดตไฟล์นี้เองท้ายทุกส่วน แล้วส่งไฟล์ใหม่ให้ผู้ใช้ทับของเดิม
> **ตั้งแต่ไฟล์นี้เป็นต้นไป: ส่วน "ฟังก์ชันสาธารณะ" และ "ตารางฐานข้อมูล" ด้านล่างใช้แทนการแนบโค้ดเดิม — เชื่อไฟล์นี้ได้เลย ไม่ต้องขอไฟล์อื่นเพิ่ม**

---

## กติกาการทำงาน (ทุกแชทต้องทำตาม)

### วิธีแนบไฟล์ (ประหยัดโทเคน)
- **โหมด A — ทบทวนทั้งโปรเจกต์:** แนบ `badminton_shop.zip` ทั้งก้อน + PROGRESS.md (ใช้ตอนตรวจ/ส่งงาน/ส่วนสุดท้าย)
- **โหมด B — ทำทีละ "ส่วน" (ใช้เป็นหลัก):** แนบ **เฉพาะไฟล์ที่ระบุในช่อง "แนบ" ของส่วนนั้น** (โฟลเดอร์ในส่วนนั้นอัดเป็น .zip ได้) + PROGRESS.md ฉบับล่าสุด แล้วสั่ง "ทำส่วน X" — AI ต้องทำ **ทุกไฟล์ในส่วนนั้นต่อเนื่องในรอบเดียว** ผู้ใช้จะนำไฟล์ที่ได้ไปแตกใส่โปรเจกต์จริงเอง
- ไฟล์นอกส่วนที่ต้องเรียกใช้ ให้ดูชื่อฟังก์ชัน/พารามิเตอร์/ค่าที่คืนจากหัวข้อ "ฟังก์ชันสาธารณะ" และจากรายการ "ฟังก์ชันที่ส่วนก่อนหน้าสัญญาไว้" ห้ามขอแนบเพิ่มถ้าข้อมูลมีครบ ห้ามเดาชื่อฟังก์ชันที่ไม่อยู่ในนั้น (ถ้าจำเป็นต้องใช้ฟังก์ชันที่ยังไม่มี ให้เขียนเพิ่มในไฟล์ของส่วนที่กำลังทำ หรือบอกชัดว่าต้องเพิ่มที่ไฟล์ไหน)

### เมื่อติดลิมิต → ผู้ใช้พิมพ์ "ดำเนินการต่อ"
- ในแต่ละส่วนมี **เช็คลิสต์รายไฟล์** (`- [ ] path/file.py`) AI ทำเรียงตามลำดับในเช็คลิสต์ และ **ส่งไฟล์ให้ครบทีละไฟล์ ห้ามส่งไฟล์ที่ทำครึ่งเดียว** (ถ้ารู้ว่าใกล้ลิมิต ให้จบไฟล์ปัจจุบันให้สมบูรณ์ก่อน แล้วหยุด)
- **ท้ายคำตอบทุกครั้ง (รวมตอนหยุดกลางทาง)** ให้พิมพ์ "จุดที่ทำถึง": รายชื่อไฟล์ที่เสร็จสมบูรณ์ในรอบนี้ + ไฟล์ถัดไปที่ต้องทำ
- เมื่อผู้ใช้พิมพ์ "ดำเนินการต่อ" ในแชทเดิม: เริ่มจากไฟล์ถัดไปทันที ไม่ต้องอธิบายซ้ำ ไม่ต้องทำไฟล์ที่ส่งไปแล้วใหม่ (ยกเว้นต้องแก้เพราะไฟล์ใหม่ทำให้ขัดกัน ให้บอกและส่งเฉพาะส่วนที่แก้)
- ถ้าเป็นแชทใหม่: ผู้ใช้จะแนบ PROGRESS ที่ติ๊กไฟล์เสร็จแล้ว + ไฟล์ที่ทำไปแล้วของส่วนนั้น → ให้เริ่มจากไฟล์แรกที่ยังเป็น `[ ]`
- ท้ายส่วน (ไฟล์ครบทุกตัว) ต้องส่ง **"บล็อกอัปเดต PROGRESS"** ให้ผู้ใช้วางต่อ (ไม่ต้องส่งทั้งไฟล์ซ้ำ): ติ๊ก `[x]` ทุกไฟล์ + ฟังก์ชันสาธารณะ (ชื่อ + พารามิเตอร์ + ค่าที่คืน + exception) + ข้อควรรู้/บั๊กที่แก้ + "ฟังก์ชันที่ส่วนถัดไปจะเรียกใช้"

### วิธีทำงาน
1. อ่าน PROGRESS.md ทั้งไฟล์ก่อนเริ่ม แล้วทำ **เฉพาะส่วนที่สั่ง** ห้ามข้ามส่วน ห้ามทำไฟล์นอกขอบเขตของส่วน
2. ก่อนเริ่ม เช็ค "เงื่อนไขก่อนเริ่ม" ของส่วนนั้น ถ้าส่วนก่อนหน้ายังไม่ติ๊กครบ ให้หยุดและแจ้งผู้ใช้
3. แก้ไฟล์ที่เสร็จแล้วได้เมื่อ "จำเป็น" (เช่น รายการ FIX-xx หรือบั๊ก) แต่ต้องจดไว้ในบล็อกอัปเดต ห้ามเปลี่ยนชื่อ/พารามิเตอร์ของฟังก์ชันสาธารณะที่ไฟล์อื่นเรียกอยู่โดยไม่แจ้ง
4. **Python ล้วนเท่านั้น** (UI = CustomTkinter) ห้ามเขียน HTML/CSS ห้ามใช้เฟรมเวิร์กเว็บ
5. ชื่อไฟล์/ฟังก์ชัน/ตัวแปรเป็นภาษาอังกฤษ ข้อความที่แสดงบนหน้าจอและ error message เป็นภาษาไทย (ชื่อสินค้า/แบรนด์เป็นอังกฤษได้)
6. ทุกไฟล์ขึ้นต้นด้วย docstring บอกหน้าที่ (ตามสไตล์ไฟล์เดิม) คอมเมนต์ภาษาไทย
7. โค้ดที่ผู้ใช้ตั้งใจเขียนเอง/แก้เอง ถ้าผู้ใช้บอกว่าแก้แล้ว ให้ถือฉบับผู้ใช้เป็นหลัก
8. **รักษา PROGRESS.md ให้เล็ก:** ส่วนที่เสร็จแล้วให้ย่อรายละเอียดเหลือบรรทัดเดียว (ติ๊ก `[x]` + ชื่อไฟล์) แล้วย้ายสิ่งที่ส่วนอื่นต้องใช้ไปไว้ที่ "ฟังก์ชันสาธารณะ" — ไฟล์นี้ถูกแนบทุกครั้ง ยิ่งเล็กยิ่งประหยัดโทเคน

### สถาปัตยกรรมและข้อตกลงโค้ด (ห้ามผิด)
- **ชั้นเดียวกันทิศเดียว:** `ui/` → `services/` → `database/repo_*` → `database/db.py` (UI ห้ามเขียน SQL, repo ห้ามมี business logic, services ห้าม import `ui`)
- **Import แบบ absolute จาก root โปรเจกต์เสมอ** เช่น `from ui.theme import ThemeManager`, `from services import auth_service` (ห้าม `from theme import ...` — ดู FIX-02)
- **รันจากโฟลเดอร์ root เท่านั้น:** `python main.py` / `python -m database.seed` (ห้ามสั่ง `python database/seed.py` — import ไม่เจอ ดู FIX-04)
- **Repo:** ฟังก์ชันละหนึ่งงาน, SQL แบบ parameterized (`?`) เท่านั้น, คืน `sqlite3.Row` / `list[Row]` / `None` / `int` (lastrowid) / `bool`; ฟังก์ชันเขียนรับพารามิเตอร์ท้าย `conn=None` — ถ้าได้ `conn` มาให้ใช้ต่อโดยไม่ commit/close (ให้ service ครอบ transaction) ถ้าไม่ได้ให้เปิดเอง commit เอง ปิดเอง (ตามสไตล์ `repo_users.py`)
- **Service:** ข้อมูลผิด → `raise ValueError("ข้อความไทย")`; ไม่มีสิทธิ์ → `raise PermissionError("ข้อความไทย")`; คืน `dict` / `list[dict]` (ไม่ส่ง `sqlite3.Row` และไม่ส่ง `password_hash` ให้ UI); งานที่แก้ข้อมูลหลายตาราง (สร้างออเดอร์, ยืนยันสลิป, ยกเลิก) **ต้องอยู่ใน transaction เดียว**
- **UI:** ทุกหน้าเป็น `CTkFrame` รับ `(parent, controller)`; สลับหน้า `controller.show("route")`; ออกจากระบบ `controller.logout()`; มี `on_show()` เพื่อรีเฟรชข้อมูล; จับ `(ValueError, PermissionError)` แล้วแสดงข้อความสีแดงในหน้า; งานช้า (AI, สร้าง PDF) ต้องรันใน thread แล้วส่งผลกลับด้วย `after()`
- **เงิน:** เก็บเป็น `REAL` (บาท) ปัดทศนิยม 2 ตำแหน่งด้วย `round(x, 2)` ทุกจุดที่คำนวณ แสดงผลผ่าน `formatters` เท่านั้น
- **เวลา:** เก็บด้วย `datetime('now','localtime')` ใน SQLite (รูปแบบ `YYYY-MM-DD HH:MM:SS`)
- **ลบข้อมูล:** ห้ามลบ products/categories/brands ที่ถูกอ้างอิง ใช้ `is_active = 0` (soft delete)
- **เขียนไฟล์ผู้ใช้อัปโหลด:** สลิป → `assets/slips/`, ใบเสร็จ → `assets/receipts/`, รูปสินค้า → `assets/images/products/` (มีโฟลเดอร์ย่อย `banners/`, `categories/`, `products/`, `users/` อยู่แล้ว) เก็บ path แบบ relative ใน DB

---

## สรุปความคืบหน้า (ใช้ใส่สไลด์)

| ชั้น | มีโค้ดแล้ว / ทั้งหมด | สถานะ |
|---|---|---|
| ไฟล์รากโปรเจกต์ (config, main, requirements, .env, .env.example, .gitignore, README) | 7 / 7 ✅ | A: config, requirements, .env.example, .gitignore · G: `main.py` (+ `--check`), `README.md` · `.env` ผู้ใช้ใส่คีย์เอง |
| core/ | 3 / 3 | ✅ constants, session, permissions (เพิ่มตัวช่วย `require_*` ในส่วน C) |
| database/ (db, seed, repo_*) | 17 / 17 | ✅ db + seed + repo_base + repo_* ครบ 14 ไฟล์ (ส่วน B) ผ่านเทสต์ 26 ข้อ |
| services/ | 14 / 14 | ✅ ครบ: auth, settings, product, review, coupon, cart, notification, order, payment, shipping, receipt, account, ai, chat (ส่วน C) |
| utils/ | 6 / 6 | ✅ formatters, image_utils, validators, promptpay, backup, font_installer |
| ui/ ฐาน (theme, router, app) | 3 / 3 ✅ | theme (สไตล์ปุ่ม/ป้าย, จำโหมดมืด), router (params, go_back, lazy routes), app (ผูก Router + navbar/sidebar) |
| ui/components/ | 12 / 12 ✅ | ครบทุกตัว มี demo รันเดี่ยวได้ |
| ui/pages/buyer/ | 18 / 18 ✅ | login, register, home, category, product_detail, compare, racket_finder, wishlist, cart, addresses, checkout, payment, orders, order_detail, write_review, profile, notifications, chat ✅ (+ `common.py` ตัวช่วยร่วม) |
| ui/pages/admin/ | 12 / 12 ✅ | dashboard, products, product_form, categories, orders, order_detail, payments, coupons, coupon_form, chat, users, settings ✅ (+ `common.py` ตัวช่วยร่วม 🆕) — ครึ่งแรก + ครึ่งหลังเสร็จ 2026-10-12 |
| tests/ | 4 / 4 | ✅ test_promptpay, test_repos (26), test_services_basic (58), `test_order_flow` (44 เทสต์) |
| **รวม** | **ส่วน A–G เสร็จทั้งหมด** | เทสต์อัตโนมัติ 137 ข้อผ่าน (bcrypt จริง) + ทดสอบ GUI จริงบนจอจำลอง: เปิดทุกหน้า 30 route × 3 role, กดทุกปุ่ม 358 ครั้ง, ไล่ครบวงจรผ่านปุ่มจริง — ไม่มี error |

**สิ่งที่ผ่านการทดสอบจริง:** services ทั้งหมดผ่าน 102 เทสต์ (58 + 44 ของครึ่งหลัง), services ครึ่งแรกผ่าน 58 เทสต์ (รันด้วย bcrypt จำลองในเครื่องตรวจ — ผู้ใช้ควรรันซ้ำกับ bcrypt จริง), test_repos 26 เทสต์ยังผ่าน, ทุกไฟล์ที่มีโค้ด compile ผ่าน, ล็อกอินด้วยบัญชี seed ทั้ง 3 (ทั้ง username และ email) ผ่าน, รหัสผิด/สมัครซ้ำ แจ้ง error ไทยถูกต้อง, `init_db()` สร้างครบ 20 ตาราง + WAL + FK, seed ไม่ทับข้อมูลจริง, `--reset`, transaction rollback/commit, CHECK, save_upload, backup/restore, unit test PromptPay 9 ข้อ
**ยังไม่ได้ทดสอบ:** `load_ctk_image` กับ customtkinter ตัวจริง, สแกน PromptPay QR ด้วยแอปธนาคารจริง, ติดตั้งฟอนต์บน Windows, หน้าจอ GUI ทุกหน้า (สภาพแวดล้อมตรวจไม่มีจอ) — ให้ผู้ใช้รัน `python ui/app.py` ทดสอบหน้าตาเองก่อนเริ่มส่วน D (UI)

---

## ภาพรวมโปรเจกต์
- Desktop app ร้านขายอุปกรณ์แบดมินตัน (โปรเจกต์ที่อาจารย์สั่ง — กำหนดแค่ Python + SQLite) ทำคนเดียว รันบนเครื่องตัวเองด้วย VS Code
- หมวดหมู่: ไม้แบด, ลูกแบด, รองเท้า, เสื้อผ้า, กระเป๋า, เอ็น/ด้ามพัน — แต่ละหมวดแยกตามแบรนด์ (Yonex, Victor, Li-Ning, Apacs, FZ Forza, Venson)
- **UI:** Python + CustomTkinter, ธีมพื้นขาวคลีน + โหมดมืด เน้นดำ–เหลือง สไตล์ Shopee / TikTok Shop (การ์ดสินค้าแบบกริด)
- **ฐานข้อมูล:** SQLite ไฟล์เดียว `data/shop.db` (WAL)
- **AI:** Google Gemini (โมเดลฟรี) ผ่าน API key ใน `.env` — ตอบแชทแทนแอดมินเมื่อไม่มีแอดมินออนไลน์
- **ชำระเงิน:** สร้าง PromptPay QR จากเลขพร้อมเพย์ใน settings → ผู้ซื้อแนบสลิป → แอดมินยืนยัน (ระบบจริงแต่ไม่ได้จ่ายเงินจริง)
- **ภาษาในแอป:** ชื่อไม้/สินค้าเป็นอังกฤษ คำอธิบายและข้อความระบบเป็นไทย
- ไลบรารีที่ใช้/จะใช้: customtkinter, bcrypt, pillow, qrcode, reportlab (ใบเสร็จ PDF), google-genai (Gemini), python-dotenv

### ฟีเจอร์ทั้งหมดที่ผู้ใช้ยืนยันว่าต้องมี
ผู้ซื้อ: ล็อกอิน/สมัคร, เลือกซื้อ, ค้นหา, **ตัวกรองสเปกไม้** (น้ำหนัก/จุดสมดุล/ความแข็งก้าน/ระดับ), **เปรียบเทียบไม้**, **ตัวช่วยเลือกไม้**, **ตัวเลือกสินค้า** (สี/ด้าม/เอ็น/ไซซ์), **ขึ้นเอ็น**, **สินค้าเสริมขายคู่**, ตะกร้า, **โค้ดส่วนลด**, **Flash Sale**, ชำระผ่าน PromptPay + แนบสลิป, **ติดตามสถานะจัดส่ง**, **รีวิวให้ดาว**, **Wishlist**, **หลายที่อยู่จัดส่ง**, **ใบเสร็จ PDF**, **การแจ้งเตือน**, **แชทกับแอดมิน (AI ตอบแทนถ้าไม่มีแอดมิน)**, หน้ารายละเอียดสินค้า + รีวิว
เจ้าของ/แอดมิน: **Dashboard**, จัดการสินค้า/หมวด/แบรนด์/ตัวเลือก, จัดการออเดอร์, ตรวจสลิป, อัปเดตสถานะจัดส่ง, คูปอง/Flash Sale, ตอบแชท, **แจ้งเตือนสต็อกใกล้หมด**, จัดการผู้ใช้, ตั้งค่าร้าน, สำรองข้อมูล

---

## กติกาธุรกิจ

**สิทธิ์ (core/permissions.py ต้องเขียนตามตารางนี้ — ดู D-01):**
| ความสามารถ | buyer | admin | owner |
|---|:-:|:-:|:-:|
| ดู/ซื้อสินค้า, ตะกร้า, ออเดอร์/รีวิว/wishlist/ที่อยู่ของตัวเอง | ✔ | – | – |
| แชทเป็นลูกค้า | ✔ | – | – |
| ดูสินค้า/สต็อก, ตอบแชท, ตรวจสลิป, ดูออเดอร์, อัปเดตสถานะจัดส่ง | – | ✔ | ✔ |
| เพิ่ม/แก้สินค้า, ปรับสต็อก | – | ✔ (แก้สต็อกและข้อมูลพื้นฐาน) | ✔ |
| ลบ(ปิด)สินค้า, จัดการหมวด/แบรนด์, คูปอง/Flash Sale | – | ✘ | ✔ |
| ผู้ใช้ (สร้างแอดมิน, ระงับบัญชี), ตั้งค่าร้าน/PromptPay, สำรองข้อมูล, ตัวเลขรายได้ใน Dashboard | – | ✘ | ✔ |

**สถานะออเดอร์:** `pending → checking_slip → paid → shipped → completed` และ `cancelled`
| การเปลี่ยน | ใครทำ | เงื่อนไข / ผลที่ตามมา |
|---|---|---|
| สร้างออเดอร์ → `pending` | buyer | ตัดสต็อก + นับคูปอง + เคลียร์ตะกร้าใน transaction เดียว, บันทึก `order_status_log`, แจ้งเตือนแอดมิน |
| `pending → checking_slip` | buyer | แนบสลิป (jpg/png ≤ 5MB) → สร้าง `payments` สถานะ `pending`, แจ้งเตือนแอดมิน |
| `checking_slip → paid` | admin/owner | `payments` = `verified` (+ `verified_by`, `verified_at`), สร้าง `shipments` สถานะ `preparing`, แจ้งเตือนผู้ซื้อ |
| `checking_slip → pending` | admin/owner | ปฏิเสธสลิป ต้องใส่เหตุผล → `payments` = `rejected` + `reject_reason`, ผู้ซื้อแนบใหม่ได้ |
| `paid → shipped` | admin/owner | ต้องกรอกขนส่ง + เลขพัสดุ → `shipments` = `shipped` |
| `shipped → completed` | buyer กด "ได้รับสินค้าแล้ว" หรือ admin กด "ส่งถึงแล้ว" (`shipments` = `delivered`) | หลังจากนี้ผู้ซื้อรีวิวได้ + ออกใบเสร็จ PDF ได้ |
| → `cancelled` | buyer (เฉพาะ `pending`), admin/owner (ก่อน `shipped`) | ต้องมีเหตุผล (`orders.cancel_reason`), คืนสต็อก + คืนสิทธิ์คูปอง; ยกเลิกหลัง `paid` = คืนเงินด้วยมือ (บันทึกในโน้ต) |
| ยกเลิกอัตโนมัติ | ระบบ | `pending` เกิน `unpaid_cancel_hours` (ค่าเริ่มต้น 24 ชม.) ตรวจตอนเปิดแอปและตอน `on_show` ของหน้าออเดอร์ |
- ทุกการเปลี่ยนสถานะ ต้องเขียน `order_status_log` (status, note, changed_by) และสร้าง `notifications` ให้ฝั่งที่เกี่ยวข้อง

**ราคา:**
- ราคาที่ใช้จริง = `sale_price` ถ้ามี **และ** (`sale_ends_at` เป็น NULL หรือยังไม่ถึงเวลา) ไม่งั้นใช้ `price`; ราคาต่อชิ้น = ราคาที่ใช้จริง + `extra_price` ของตัวเลือก
- `subtotal` = Σ(ราคาต่อชิ้น × qty); `discount` จากคูปอง ไม่เกิน `subtotal`; `shipping_fee` มาจาก settings (`shipping_fee` = 50) และฟรีเมื่อ `subtotal` ≥ `free_shipping_min` (0 = ไม่เปิดใช้); `total = subtotal − discount + shipping_fee`
- `order_items` เก็บสำเนา `product_name` และ `price_at_purchase` (+ ชื่อตัวเลือก `option_label`) ณ วันซื้อ — ห้ามอ่านราคาจาก products ย้อนหลัง

**สต็อก:** ตัดตอนสร้างออเดอร์ (D-02), คืนตอนยกเลิก; สินค้าที่มีตัวเลือก ใช้ `product_options.stock` เป็นตัวตัดสิน และ `products.stock` = ผลรวมของตัวเลือก; สต็อก = 0 → ซื้อไม่ได้ (ปุ่มเทา "สินค้าหมด"); สต็อก ≤ `low_stock_threshold` (ค่าเริ่มต้น 5) → แจ้งเตือนแอดมิน/เจ้าของ + ขึ้นในรายการ Dashboard

**คูปอง:** `discount_type` = `percent` | `fixed`; ใช้ได้เมื่อ `is_active`, ยังไม่หมดอายุ, `subtotal ≥ min_order`, `used_count < max_uses` (NULL = ไม่จำกัด), และผู้ใช้คนนี้ยังไม่เคยใช้ (ตาราง `coupon_usages` ที่จะเพิ่ม); โค้ดไม่สนตัวพิมพ์เล็ก/ใหญ่
**Flash Sale:** ใช้ `sale_price` + `sale_ends_at` (แสดงเวลานับถอยหลังบนการ์ดสินค้า)
**รีวิว:** เฉพาะผู้ซื้อที่ออเดอร์ `completed` และมีสินค้านั้น; 1–5 ดาว; หนึ่งครั้งต่อ (user, product, order)
**สินค้าเสริมขายคู่:** ตาราง `product_addons` — หน้ารายละเอียดสินค้าแสดง "ซื้อคู่กัน" กดเพิ่มลงตะกร้าได้ในคลิกเดียว
**เปรียบเทียบไม้:** 2–3 ไม้ ตารางสเปกเทียบกัน (น้ำหนัก, สมดุล, ก้าน, ระดับ, ราคา, คะแนนรีวิว)
**ตัวช่วยเลือกไม้:** ถามแบบตัวเลือก (ระดับฝีมือ, สไตล์การเล่น บุก/คุมเกม/สปีด, งบ) → กรองไม้ด้วยกติกาตายตัวใน `product_service` (ไม่ใช้ AI) → แสดงผลเป็น product grid (ไฟล์ใหม่ `racket_finder.py` — D-03)
**ขึ้นเอ็น:** เป็น `product_options` ประเภท `เอ็น` (ชื่อเอ็น/ค่าแรง = `extra_price`) + ช่องแจ้งความตึง (lbs) เก็บใน `option_value` เช่น `"BG65 / 24 lbs"` — ทำตอนขั้น UI หน้ารายละเอียดสินค้า
**แชท:** ข้อความผูกกับ `customer_id` (หนึ่งห้องต่อลูกค้า); `sender_type` = `user|admin|ai`; AI จะตอบเมื่อ **ไม่มี admin/owner ที่ `is_online = 1`** (D-07); `is_online` ตั้งเมื่อล็อกอิน/ล้างเมื่อออกจากระบบ/ปิดแอป และล้างทุกคนตอนเปิดแอป (กันค้าง); หน้าแชทโพลทุก 3 วินาทีด้วย `after()`
**AI (Gemini):** key จาก `.env` (`GEMINI_API_KEY`, `GEMINI_MODEL`); system prompt ใส่ข้อมูลร้าน + รายการสินค้าย่อ (ชื่อ/ราคา/สเปก) จาก DB; ห้ามแต่งราคา/โปร/สต็อกเอง; ถ้าเรียก API ไม่สำเร็จ → ข้อความสำรอง "ขออภัย ระบบ AI ใช้งานไม่ได้ชั่วคราว แอดมินจะตอบกลับโดยเร็ว"; รันใน thread
**จัดส่ง:** ตามขนส่งอัตโนมัติทำไม่ได้ฟรี → **แอดมินกดอัปเดตเอง** (ขนส่งในตัวเลือก: Kerry, Flash, J&T, ไปรษณีย์ไทย, อื่นๆ) ผู้ซื้อเห็น timeline จาก `order_status_log` + `shipments`
**PromptPay QR:** payload EMV (merchant tag 29, AID `A000000677010111`, เบอร์แปลงเป็น `0066xxxxxxxxx`, สกุล 764, จำนวนเงิน = `orders.total`, CRC16-CCITT) → วาดด้วย `qrcode` — เลข/ชื่อพร้อมเพย์อ่านจาก settings (`promptpay_no`, `promptpay_name`)
**ธีม:** พื้นขาวคลีน (`background` #F8F9FA), เหลือง `primary` #F5B041 ปุ่มตัวอักษรดำ, ดำ/เทาเข้มเป็น `secondary`, มีโหมดมืด (สลับได้ทุกหน้า)

---

## โครงสร้างไฟล์ (✅ เสร็จ · 🔧 มีโค้ดแต่ต้องแก้ · ⚠️ ชั่วคราว · ⬜ ว่าง · 🆕 เสนอเพิ่ม)

```
badminton_shop/
├── PROGRESS.md                         # ไฟล์นี้
├── main.py                       ✅    # จุดเริ่มโปรแกรม + `--check` (ส่วน G)
├── config.py                     ✅    # path, ค่าตั้งต้น, โหลด .env
├── requirements.txt              ✅
├── .env / .env.example           ✅    # .env ผู้ใช้คัดลอกจาก .env.example แล้วใส่คีย์เอง
├── .gitignore                    ✅
├── README.md                     ✅    # วิธีติดตั้ง/รัน (ส่วน G)
├── core/
│   ├── constants.py              ✅
│   ├── session.py                ✅
│   └── permissions.py            ✅
├── data/                               # shop.db, backups/ (สร้างอัตโนมัติ)
├── database/
│   ├── db.py                     ✅    # schema 20 ตาราง + transaction()
│   ├── seed.py                   ✅
│   ├── repo_base.py              ✅🆕 # use_conn(conn) + EFFECTIVE_PRICE_SQL (ตัวช่วยร่วมของ repo)
│   ├── repo_users.py             ✅
│   ├── repo_settings.py          ✅🆕
│   ├── repo_products.py          ✅    # products + categories + brands + options + addons
│   ├── repo_cart.py / repo_wishlist.py / repo_addresses.py                  ✅
│   ├── repo_orders.py / repo_payments.py / repo_shipping.py                 ✅
│   ├── repo_coupons.py / repo_reviews.py                                    ✅
│   └── repo_chat.py / repo_notifications.py                                 ✅
├── services/
│   ├── auth_service.py           ✅    # (FIX-11 เสร็จ) login/logout ตั้ง-ล้างออนไลน์, เปลี่ยนรหัส, โปรไฟล์, จัดการบัญชี
│   ├── settings_service.py       ✅🆕
│   ├── product_service.py        ✅🆕  # ราคาจริง, กรองสเปก, ค้นหา, เปรียบเทียบ, ตัวช่วยเลือกไม้, addons, งานแอดมิน
│   ├── account_service.py        ✅🆕  # ที่อยู่จัดส่ง + wishlist + แก้โปรไฟล์ (ใช้ auth_service.update_profile ได้)
│   ├── cart_service.py / coupon_service.py / review_service.py              ✅
│   ├── order_service.py / payment_service.py / shipping_service.py          ✅
│   ├── notification_service.py                                              ✅
│   ├── receipt_service.py                                                   ✅    # Arimo (อังกฤษ) + ฟอนต์ไทยของ OS
│   ├── chat_service.py           ✅🆕
│   └── ai_service.py                                                        ✅
├── utils/
│   ├── validators.py             ✅
│   ├── font_installer.py         ✅
│   └── formatters.py / image_utils.py / promptpay.py / backup.py            ✅
├── ui/
│   ├── theme.py                  ✅
│   ├── router.py                 ✅    # ROUTE_TABLE lazy, params, go_back, สิทธิ์ครบ
│   ├── app.py                    ✅    # Router + Navbar/Sidebar + init_db
│   ├── components/  navbar, sidebar, dialogs, rating, search_bar, product_card,
│   │                product_grid, product_filter, image_picker, order_timeline,
│   │                payment_qr, chat_bubble                                  ✅ (12 ไฟล์)
│   └── pages/
│       ├── buyer/  login, register, home, category, product_detail, compare, racket_finder 🆕,
│       │           wishlist, cart, addresses, common 🆕, checkout, payment, orders,
│       │           order_detail, write_review, profile, notifications, chat ✅ (18 หน้า + common)
│       └── admin/  dashboard, products, product_form, categories, orders, order_detail,
│                   payments, coupons, coupon_form, chat, users, settings   ✅ (12 ไฟล์ + common 🆕)
├── assets/  fonts/ (Arimo ✅ — ฟอนต์ไทยใช้ของ OS ไม่ต้องใส่เพิ่ม), icons/, images/, receipts/, slips/
└── tests/   test_promptpay.py ✅ | test_repos.py ✅🆕 | test_services_basic.py ✅🆕 | test_order_flow.py ✅🆕
```

---

## ตารางฐานข้อมูล (ปัจจุบัน 20 ตาราง — เชื่อรายการนี้ ไม่ต้องแนบ db.py)
(PK = `id INTEGER AUTOINCREMENT` ถ้าไม่ระบุ · `ts` = TIMESTAMP DEFAULT localtime · FK ทั้งหมดเปิด `foreign_keys=1`)

1. **users**: username UNIQUE, email UNIQUE, password_hash, full_name, phone, role (`owner|admin|buyer` CHECK, default buyer), avatar_path, is_online (0), is_active (1), created_at
2. **addresses**: user_id→users (CASCADE), recipient, phone, address_line, district, province, postcode, is_default
3. **categories**: name UNIQUE, image_path
4. **brands**: name UNIQUE, logo_path
5. **products**: category_id→categories, brand_id→brands, name, description, price, sale_price, sale_ends_at, stock (0), image_path, is_active (1), weight_class (`3U|4U`…), balance, flex, level, created_at
6. **product_options**: product_id→products (CASCADE), option_type (สี/ด้าม/เอ็น/ไซซ์), option_value, extra_price (0), stock (0)
7. **cart_items**: user_id (CASCADE), product_id (CASCADE), option_id→product_options (SET NULL), qty (1)
8. **coupons**: code UNIQUE, discount_type (`percent|fixed`), value, min_order (0), max_uses, used_count (0), expires_at, is_active (1)
9. **orders**: user_id, recipient_name, recipient_phone, shipping_address, subtotal, discount (0), shipping_fee (0), total, coupon_id→coupons, status (CHECK 6 สถานะ, default pending), created_at
10. **order_items**: order_id→orders (CASCADE), product_id, option_id, product_name, price_at_purchase, qty
11. **payments**: order_id (CASCADE), method (เช่น promptpay), amount, slip_path, status (`pending|verified|rejected` — ไม่มี CHECK), reject_reason, verified_by→users, created_at, verified_at
12. **shipments**: order_id (CASCADE), carrier, tracking_no, status (`preparing|shipped|delivered` — ไม่มี CHECK), updated_at
13. **order_status_log**: order_id (CASCADE), status, note, changed_by→users, created_at
14. **reviews**: user_id, product_id, order_id, rating (CHECK 1–5), comment, created_at, UNIQUE(user_id, product_id, order_id)
15. **wishlist**: PK(user_id, product_id), created_at (CASCADE ทั้งคู่)
16. **chat_messages**: customer_id→users (CASCADE), sender_type (`user|admin|ai`), sender_id, message, is_read (0), created_at
17. **notifications**: user_id (CASCADE), title, message, is_read (0), created_at
18. **settings**: key PK, value — มีอยู่: `shop_name`, `promptpay_no`, `promptpay_name`, `shipping_fee`

**เพิ่ม/แก้แล้วในส่วน A (`db.py`):**
19. **coupon_usages**: coupon_id→coupons, user_id→users, order_id→orders (CASCADE), used_at, UNIQUE(coupon_id, user_id)
20. **product_addons**: PK(product_id, addon_product_id), ทั้งคู่→products (CASCADE)
- คอลัมน์ใหม่: `categories.is_active`, `brands.is_active` (default 1), `order_items.option_label` TEXT, `orders.cancel_reason` TEXT
- CHECK แล้ว: `payments.status`, `shipments.status`, `chat_messages.sender_type`, `coupons.discount_type` (มีผลเฉพาะ DB ที่สร้างใหม่; DB เก่าได้แค่คอลัมน์ใหม่ผ่าน `_ensure_column`)
- INDEX: products(category_id), products(brand_id), orders(user_id,status), cart_items(user_id), chat_messages(customer_id,created_at), notifications(user_id,is_read)
- settings ปัจจุบัน 8 key: `shop_name`, `promptpay_no`, `promptpay_name`, `shipping_fee`=50, `free_shipping_min`=0, `low_stock_threshold`=5, `unpaid_cancel_hours`=24, `ai_enabled`=1 (ค่าตั้งต้นอยู่ที่ `config.DEFAULT_SETTINGS`, ค่าเก็บเป็นข้อความ)

---

## แผนการทำ — 7 ส่วนใหญ่ (ทำทีละส่วนให้จบในรอบเดียว ติดลิมิตค่อยพิมพ์ "ดำเนินการต่อ")

> รูปแบบแต่ละส่วน: **เงื่อนไขก่อนเริ่ม** · **แนบ** · **เช็คลิสต์รายไฟล์ + รายละเอียดที่ต้องทำ** · **เสร็จเมื่อ**
> สัญลักษณ์: `[x]` เสร็จ · `[~]` มีโค้ดแล้วแต่ต้องแก้/ต่อเติม · `[ ]` ยังไม่ทำ · ไฟล์ 🆕 = ไฟล์ใหม่ที่เสนอเพิ่ม (ผู้ใช้สร้างไฟล์ว่างหรือให้ AI ส่งไฟล์ใหม่)
> ลำดับในเช็คลิสต์ = ลำดับที่ต้องทำ (ไฟล์ท้ายพึ่งไฟล์หน้า)

| ส่วน | เนื้อหา | ไฟล์ | สถานะ |
|---|---|:-:|---|
| **A** | ฐานราก: รากโปรเจกต์, core, db, seed, utils | 15 | ✅ เสร็จ 2026-10-11 |
| **B** | Repository ทั้งหมด (`database/repo_*`) | 13 (+repo_base +test_repos) | ✅ เสร็จ 2026-10-11 |
| **C** | Services ทั้งหมด + ทดสอบ backend | 15 | ✅ เสร็จ 2026-10-12 (15/15) |
| **D** | UI ฐาน (theme/router/app) + components ทั้ง 12 | 15 | ✅ เสร็จ 2026-10-12 (15/15) |
| **E** | หน้าผู้ซื้อทั้งหมด (`ui/pages/buyer`) | 18 | ✅ เสร็จ 2026-10-12 (18/18) |
| **F** | หน้าแอดมินทั้งหมด (`ui/pages/admin`) | 12 (+common) | ✅ เสร็จ 2026-10-12 (12/12) |
| **G** | ประกอบร่าง main.py + README + ทดสอบรวม + ตกแต่ง | 5 | ✅ เสร็จ 2026-10-12 (เหลือ FIX-16 ให้ผู้ใช้เปลี่ยนรหัสผ่านเอง) |

---

### ส่วน A — ฐานราก ✅ เสร็จ (2026-10-11)
- [x] `.gitignore` · [x] `requirements.txt` · [x] `.env.example` · [x] `config.py`
- [x] `core/constants.py` · [x] `core/permissions.py` · [x] `core/session.py`
- [x] `database/db.py` · [x] `database/seed.py`
- [x] `utils/formatters.py` · [x] `utils/image_utils.py` · [x] `utils/validators.py` · [x] `utils/promptpay.py` · [x] `utils/backup.py` · [x] `utils/font_installer.py`
- ไฟล์เพิ่ม: `tests/test_promptpay.py`, `assets/slips/.gitkeep`, `assets/receipts/.gitkeep`
- รายละเอียดฟังก์ชันอยู่ที่หัวข้อ "ฟังก์ชันสาธารณะ" และ "บันทึกความคืบหน้า" ด้านล่าง

### ส่วน B — Repository ✅ เสร็จ (2026-10-11)
- [x] `repo_users.py` (เพิ่ม FIX-10 ครบ ฟังก์ชันเดิมพฤติกรรมเดิม) · [x] `repo_settings.py` 🆕 · [x] `repo_products.py` · [x] `repo_cart.py` · [x] `repo_wishlist.py` · [x] `repo_addresses.py` · [x] `repo_orders.py` · [x] `repo_payments.py` · [x] `repo_shipping.py` · [x] `repo_coupons.py` · [x] `repo_reviews.py` · [x] `repo_chat.py` · [x] `repo_notifications.py`
- ไฟล์เพิ่ม: `database/repo_base.py` (ตัวช่วย `use_conn`), `tests/test_repos.py` (26 เทสต์ รันด้วย `python -m unittest tests.test_repos -v`)
- รายละเอียดฟังก์ชันอยู่ที่หัวข้อ "ฟังก์ชันสาธารณะ" (database.repo_*) และ "จบส่วน B" ด้านล่าง

---

### ส่วน C — Services + ทดสอบ backend ✅ เสร็จ (2026-10-12)
- [x] `auth_service` · [x] 🆕 `settings_service` · [x] 🆕 `product_service` · [x] `review_service` · [x] `coupon_service` · [x] `cart_service` · [x] `notification_service` (ครึ่งแรก 2026-10-11)
- [x] `order_service` · [x] `payment_service` · [x] `shipping_service` · [x] `receipt_service` · [x] 🆕 `account_service` · [x] `ai_service` · [x] 🆕 `chat_service` · [x] `tests/test_order_flow.py` (ครึ่งหลัง 2026-10-12)
- รายละเอียดฟังก์ชันอยู่ที่หัวข้อ "ฟังก์ชันสาธารณะ" และ "จบส่วน C" ด้านล่าง · รันเทสต์: `python -m unittest tests.test_order_flow tests.test_services_basic tests.test_repos -v`

---

### ส่วน D — UI ฐาน + components ✅ เสร็จ (2026-10-12)
- [x] `theme.py` · [x] `router.py` · [x] `app.py`
- [x] components 12 ตัว: navbar, sidebar, dialogs, rating, search_bar, product_card, product_grid, product_filter, image_picker, order_timeline, payment_qr, chat_bubble
- [x] แก้ `pages/buyer/login.py` ให้ import ถูก (เพื่อให้ล็อกอินได้ตั้งแต่ D)
**ยังเหลือให้ผู้ใช้ทำ:** รัน `python -m ui.app` (ล็อกอิน 3 role, สลับมืด/สว่าง) และ demo ของแต่ละ component `python -m ui.components.<ชื่อ>`

---

### ส่วน E — หน้าผู้ซื้อ (`ui/pages/buyer/`)
**เงื่อนไขก่อนเริ่ม:** ส่วน D ติ๊กครบ
**แนบ:** `ui/pages/buyer/` ทั้งโฟลเดอร์ (login.py ต้องแนบเพราะต้องแก้) + ถ้า D เปลี่ยน API ของ components ให้แนบบล็อกอัปเดตของ D
**ส่วน E เสร็จครบ 2026-10-12 (ครึ่งแรก 9 หน้า + common.py · ครึ่งหลัง 8 หน้า)**
**เช็คลิสต์:**
- [x] `login.py` — แก้ import แล้วในส่วน D (ล็อกอินผูก auth_service ใช้ได้)
- [x] `register.py` — ผูก `auth_service.register`, ยืนยันรหัสผ่าน, ไปหน้า login พร้อมข้อความสำเร็จ
- [x] `home.py` — แบนเนอร์, Flash Sale, หมวด, สินค้าแนะนำ
- [x] `category.py` — กริด + ตัวกรอง + ค้นหา + เรียง
- [x] `product_detail.py` — รูป, สเปก, ตัวเลือก/ขึ้นเอ็น, ซื้อคู่กัน, รีวิว, เพิ่มตะกร้า/ซื้อเลย/wishlist
- [x] `compare.py`
- [x] 🆕 `racket_finder.py` — route `racket_finder` → `RacketFinderPage` ลงทะเบียนไว้แล้วใน router
- [x] `wishlist.py`
- [x] `cart.py`
- [x] `addresses.py`
- [x] `checkout.py` — เลือกที่อยู่, กรอกคูปอง, สรุปราคา
- [x] `payment.py` — QR + ยอด + แนบสลิป
- [x] `orders.py` — แท็บตามสถานะ
- [x] `order_detail.py` — timeline, เลขพัสดุ, ยกเลิก, ได้รับของแล้ว, ใบเสร็จ PDF
- [x] `write_review.py`
- [x] `profile.py` — แก้โปรไฟล์/เปลี่ยนรหัสผ่าน
- [x] `notifications.py`
- [x] `chat.py` — โพลทุก 3 วินาทีด้วย `after()`
**เสร็จเมื่อ:** buyer1 สั่งซื้อครบวงจรผ่านหน้าจอได้ (เลือกสินค้า → ตะกร้า → คูปอง → สลิป) · ไม่มีหน้าไหนจับ exception ไม่ครบ (แสดง error ไทยสีแดงแทน traceback)

---

### ส่วน F — หน้าแอดมิน (`ui/pages/admin/`)
**เงื่อนไขก่อนเริ่ม:** ส่วน D ติ๊กครบ (ไม่ต้องรอ E)
**แนบ:** `ui/pages/admin/` ทั้งโฟลเดอร์ + `ui/components/sidebar.py`
**เช็คลิสต์:**
- [x] 🆕 `common.py` — ตัวช่วยร่วมของหน้าแอดมิน (คลาสฐาน `AdminPage`, ปุ่ม/ช่องกรอก/ป้าย/ตาราง/แบ่งหน้า, ดูรูปขยาย)
- [x] `dashboard.py` — รายได้/ออเดอร์/สินค้าขายดี/สต็อกต่ำ/ยอดขายรายวัน (วาดด้วย Canvas/CTk **ห้ามเพิ่มไลบรารีโดยไม่ถาม**); admin ไม่เห็นตัวเลขรายได้
- [x] `products.py`
- [x] `product_form.py` — รวมจัดการตัวเลือก/addons/อัปโหลดรูป
- [x] `categories.py` — หมวด + แบรนด์ (owner)
- [x] `orders.py`
- [x] `order_detail.py`
- [x] `payments.py` — ดูสลิปขยายใหญ่, ยืนยัน/ปฏิเสธ+เหตุผล
- [x] `coupons.py` (owner)
- [x] `coupon_form.py` (owner)
- [x] `chat.py` — รายการห้อง + ข้อความยังไม่อ่าน
- [x] `users.py` (owner)
- [x] `settings.py` (owner) — ชื่อร้าน, พร้อมเพย์, ค่าส่ง, เกณฑ์สต็อก, สำรอง/กู้คืนข้อมูล
**เสร็จเมื่อ:** owner ทำได้ทุกเมนู, admin เข้าหน้า owner-only ไม่ได้ (redirect) · ตรวจสลิป→ส่งพัสดุ→ลูกค้าเห็นสถานะเปลี่ยน

---

### ส่วน G — ประกอบร่างและทดสอบรวม ✅ เสร็จ (2026-10-12)
**เงื่อนไขก่อนเริ่ม:** ส่วน E และ F ติ๊กครบ
**แนบ:** `badminton_shop.zip` ทั้งก้อน (โหมด A) + PROGRESS
**เช็คลิสต์:**
- [x] `main.py` — `init_db()` → seed ถ้า DB ว่าง → เตือนรหัสผ่านตั้งต้น → เริ่ม App · `--check` ตรวจความพร้อม
- [x] `README.md` — ติดตั้ง/รัน/บัญชีทดลอง/ตั้งค่าร้าน/API key/ฟอนต์ไทย/สำรอง/ทดสอบ/แก้ปัญหา
- [x] สำรองข้อมูลอัตโนมัติตอนปิดแอป — `utils.backup.auto_backup_on_exit()` เรียกใน `App._on_close`
- [x] ตรวจ route ครบทุกหน้า + ไล่ทดสอบตามกติกาธุรกิจทั้งหมด (สั่งซื้อครบวงจร, ยกเลิก, สลิปถูกปฏิเสธ, Flash Sale หมดเวลา, คูปอง, สต็อกต่ำ, แชท+AI, ใบเสร็จ, มืด/สว่าง, ทุก role)
- [~] แก้บั๊กที่เจอ 2 จุด ✅ · เปลี่ยนรหัสผ่านบัญชี seed (FIX-16) = **ผู้ใช้ทำเอง** (มีคำเตือนตอนเปิดแอป + `--check`) · ภาพสไลด์: ผู้ใช้แคปจากเครื่องตัวเอง
**เสร็จเมื่อ:** รัน `python main.py` ครั้งแรกบนเครื่องสะอาด (ไม่มี shop.db) ใช้งานได้ครบทุกฟีเจอร์ในรายการ "ฟีเจอร์ทั้งหมดที่ผู้ใช้ยืนยัน"

---

## รายการที่ต้องแก้ (ตรวจจากโค้ดจริง — ✔ = ยืนยันด้วยการรัน, ○ = ตรวจจากการอ่านโค้ด)

| รหัส | ความเร่งด่วน | ปัญหา | แก้ที่ส่วน |
|---|:-:|---|:-:|
| ~~FIX-01~~ ○ | สูง | `.gitignore` ว่าง → `.env` (ที่จะใส่ API key) และ `data/shop.db` จะถูก commit ขึ้น git | ✅ แก้แล้ว (A) |
| ~~FIX-02~~ ✔ | สูง | import `from theme` → `from ui.theme` | ✅ แก้แล้ว (D: app.py, login.py) |
| ~~FIX-03~~ ✔ | สูง | `seed.run_seed()` **ลบข้อมูลจริงทิ้ง** (users, products, settings ฯลฯ) ทุกครั้งที่รัน — ทดสอบแล้ว ผู้ใช้ที่สมัครเองหาย และ PromptPay ที่เจ้าของตั้งไว้ถูกรีเซ็ต | ✅ แก้แล้ว (A) |
| ~~FIX-04~~ ✔ | กลาง | `python database/seed.py` ล้มด้วย `ModuleNotFoundError: database` ต้องรัน `python -m database.seed` จาก root; และ `seed.py` (ชั้น database) import `services.auth_service` (ผิดทิศชั้น) | ✅ แก้แล้ว (A) |
| ~~FIX-05~~ ✔ | สูง | ฟอนต์ Arimo ไม่มีอักษรไทยและไม่มี ฿ → ใบเสร็จ PDF ต้องมีฟอนต์ไทย | ✅ แก้แล้ว (C): **ตัดสินใจใหม่ — อังกฤษใช้ Arimo จาก assets/fonts, ไทยใช้ฟอนต์ของ OS เครื่องนั้น** (ดู D-05) · ไม่ใช้ ฿ |
| ~~FIX-06~~ ○ | ต่ำ | `data/.fonts_installed` (marker) อยู่ใน zip: ถ้าย้ายโปรเจกต์ไปเครื่องอื่น marker ทำให้ข้ามการติดตั้งฟอนต์ทั้งที่เครื่องนั้นยังไม่มี | ✅ แก้แล้ว (A) |
| ~~FIX-07~~ ○ | สูง | schema ขาด: `coupon_usages`, `product_addons`, `order_items.option_label`, `orders.cancel_reason`, `is_active` ของหมวด/แบรนด์, CHECK ของ payments/shipments/chat/coupons, INDEX | ✅ แก้แล้ว (A) |
| ~~FIX-08~~ ✔ | สูง | Router ส่ง params ไม่ได้ / ROUTE_ROLES ไม่ครบ / routes ว่าง | ✅ แก้แล้ว (D) |
| ~~FIX-09~~ ✔ | กลาง | app.py เป็นหน้าจำลอง ไม่ใช้ Router | ✅ แก้แล้ว (D) |
| ~~FIX-10~~ ✔ | กลาง | `repo_users` ไม่มี list/update/set_active/set_online/update_password | ✅ แก้แล้ว (B) |
| ~~FIX-11~~ ✔ | กลาง | `auth_service` ไม่มี change_password, update_profile, สร้างแอดมิน, ระงับบัญชี; ไม่ตั้ง/ล้าง `is_online` | ✅ แก้แล้ว (C) |
| ~~FIX-12~~ ✔ | กลาง | ข้อมูล seed: สินค้า 7 ชิ้นมี `sale_price` แต่ `sale_ends_at` เป็น NULL ทั้งหมด (= ลดตลอด ไม่ใช่ Flash Sale); ค่าสเปก `level` ไม่เป็นมาตรฐาน (`Beginner/Intermediate` ปนกับค่าเดี่ยว) | ✅ แก้แล้ว (A) |
| ~~FIX-13~~ ✔ | กลาง | ไม่มีรูปสินค้าเลย (`image_path` เป็น NULL ทั้ง 25 ชิ้น, โฟลเดอร์ใน `assets/images/` ว่าง) → ต้องมี placeholder ก่อนทำหน้า UI | ✅ แก้แล้ว (A) ใช้ placeholder |
| ~~FIX-14~~ ✔ | กลาง | seed ไม่มี `product_options`, คูปอง, ที่อยู่ตัวอย่าง, addons → ทดสอบหน้าต่าง ๆ ไม่ได้ | ✅ แก้แล้ว (A) |
| ~~FIX-15~~ ○ | ต่ำ | `db.py` กำหนด path เอง (ควรอ่านจาก `config.py`), ไม่มี helper `transaction()` ทั้งที่การสั่งซื้อต้องอาศัย | ✅ แก้แล้ว (A) |
| FIX-16 ○ | ต่ำ | บัญชี seed (`owner123`/`admin123`/`buyer123`) เดาง่าย — ใช้ทดสอบเท่านั้น ต้องเปลี่ยนก่อนนำเสนอ/ส่งงาน | G: **ผู้ใช้ทำเอง** — ล็อกอินแล้วเปลี่ยนที่หน้าโปรไฟล์; `main.py` เตือนบน console ทุกครั้งที่เปิดจนกว่าจะเปลี่ยนครบ 3 บัญชี (ตรวจได้ด้วย `python main.py --check`) |

---

## ฟังก์ชันสาธารณะของแต่ละโมดูลที่มีอยู่ (ตรวจจากโค้ดจริง)

**config** — path: `BASE_DIR, DATA_DIR, DB_PATH, BACKUP_DIR, ASSETS_DIR, FONTS_DIR, ICONS_DIR, IMAGES_DIR, BANNER_IMAGES_DIR, CATEGORY_IMAGES_DIR, PRODUCT_IMAGES_DIR, USER_IMAGES_DIR, SLIPS_DIR, RECEIPTS_DIR`; `ensure_dirs()`; `GEMINI_API_KEY`, `GEMINI_MODEL` (ค่าเริ่มต้น `gemini-2.5-flash`); `ALLOWED_IMAGE_EXTENSIONS, MAX_UPLOAD_BYTES (5MB), UPLOAD_MAX_SIDE (1200), BACKUP_KEEP_COUNT (10)`; `DEFAULT_SETTINGS` (dict key→ข้อความ 8 key)

**core.constants** — `ROLE_OWNER/ADMIN/BUYER`, `ALL_ROLES`, `ROLE_LABELS`; `ORDER_STATUS_PENDING/CHECKING_SLIP/PAID/SHIPPED/COMPLETED/CANCELLED` (= `"pending"`, `"checking_slip"`, `"paid"`, `"shipped"`, `"completed"`, `"cancelled"`), `ORDER_STATUSES`, `ORDER_STATUS_LABELS`; `PAYMENT_STATUS_PENDING/VERIFIED/REJECTED`, `PAYMENT_STATUS_LABELS`; `SHIPMENT_STATUS_PREPARING/SHIPPED/DELIVERED`, `SHIPMENT_STATUS_LABELS`; `SENDER_TYPE_USER/ADMIN/AI`; `DISCOUNT_PERCENT/FIXED`, `DISCOUNT_TYPES`; `PAYMENT_METHOD_PROMPTPAY`; `CARRIERS`; `OPTION_TYPES = ("สี","ด้าม","เอ็น","ไซซ์")`; `WEIGHT_CLASSES = ("3U","4U")`, `BALANCES`, `FLEXES`, `LEVELS = ("Beginner","Intermediate","Advanced","Professional")`

**core.permissions** — `can(role, action) -> bool`, `require(action, role=None)` (ไม่ส่ง role = ใช้ Session; ไม่ล็อกอิน → `PermissionError("กรุณาเข้าสู่ระบบก่อน")`; ไม่มีสิทธิ์ → `PermissionError("คุณไม่มีสิทธิ์ทำรายการนี้")`; ชื่อ action ผิด → `ValueError`) · action (ใช้เป็นค่าคงที่หรือ string ก็ได้): buyer = `SHOP_BROWSE "shop.browse", CART_USE, ORDER_OWN, REVIEW_WRITE, WISHLIST_USE, ADDRESS_MANAGE, CHAT_CUSTOMER` · admin+owner = `PRODUCT_VIEW, PRODUCT_CREATE, PRODUCT_EDIT, STOCK_UPDATE, CHAT_REPLY, SLIP_VERIFY, ORDER_VIEW, ORDER_CANCEL, SHIPMENT_UPDATE, DASHBOARD_VIEW` · owner เท่านั้น = `PRODUCT_DELETE, CATEGORY_MANAGE, BRAND_MANAGE, COUPON_MANAGE, USER_MANAGE, SETTINGS_MANAGE, BACKUP_MANAGE, DASHBOARD_REVENUE` · **owner ไม่มีสิทธิ์ฝั่งผู้ซื้อ** ตามตาราง

**core.session.Session** (class เมธอดล้วน, เก็บ global) — `current_user` (dict: `id, username, role, full_name` หรือ `None`), `login(user_row)`, `logout()`, `is_authenticated() -> bool`, `get_role() -> str | None`, `get_user_id() -> int | None`

**database.db** — `BASE_DIR`, `DATA_DIR`, `DB_PATH` (ส่งต่อจาก config); `get_connection() -> sqlite3.Connection` (`row_factory=sqlite3.Row`, foreign_keys + WAL + busy_timeout; **ผู้เรียกต้อง `close()`**); `transaction()` context manager → yield `conn` (`BEGIN IMMEDIATE`; จบปกติ commit, exception → rollback แล้วโยนต่อ, ปิด conn เสมอ); `init_db()` (20 ตาราง + INDEX เรียกซ้ำได้ เติมคอลัมน์ใหม่ให้ DB เก่า `print` ผลลัพธ์)

**database.repo_users** — `get_by_username(username)`, `get_by_email(email)`, `get_by_id(user_id)` → `Row | None` (มี `password_hash`); `username_exists(username)`, `email_exists(email)` → `bool`; `create_user(username, email, password_hash, full_name, phone, role=ROLE_BUYER) -> int`

**database.repo_base** (ภายในชั้น repo) — `use_conn(conn=None)` context manager (ได้ conn = ใช้ต่อไม่ commit/close; ไม่ได้ = เปิด/commit/rollback/ปิดเอง), `EFFECTIVE_PRICE_SQL` (นิพจน์ราคาที่ใช้จริง alias `p`), `like_pattern(text)`, `as_list(v)` · **ทุกฟังก์ชัน repo ด้านล่างรับ `conn=None` ท้ายสุด** (ไม่ระบุซ้ำ) และไม่มี business logic · "→ Row" = `sqlite3.Row` (เข้าถึงด้วยชื่อคอลัมน์)

**database.repo_users** (+ใหม่) — `list_users(role=None, search=None)` (role ค่าเดียว/list; ไม่มี password_hash), `update_profile(user_id, full_name, phone, avatar_path=None)` (None = ไม่เปลี่ยนรูป), `update_password(user_id, password_hash)`, `set_active(user_id, bool)` (ระงับ = ล้างออนไลน์ด้วย), `set_online(user_id, bool)`, `clear_all_online() -> int`, `list_online_staff()` (admin/owner ที่ is_online=1 และ is_active=1) · ฟังก์ชันเดิมรับ `conn` เพิ่มได้ ไม่เปลี่ยนพฤติกรรม
**database.repo_settings** — `get(key, default=None) -> str|None` (ไม่มีใน DB → default → `config.DEFAULT_SETTINGS`), `get_all() -> dict`, `set(key, value)`, `set_many(dict)` (ค่าเก็บเป็นข้อความ)
**database.repo_products** — สินค้า: `list_products(filters=None, sort="newest", limit=None, offset=0)`, `count_products(filters)`, `get_product(id)`, `get_products_by_ids(ids)` (คงลำดับ), `create_product(category_id, brand_id, name, description, price, sale_price=None, sale_ends_at=None, stock=0, image_path=None, weight_class=None, balance=None, flex=None, level=None, is_active=1) -> id`, `update_product(id, fields: dict) -> bool` (None = NULL; คอลัมน์นอกลิสต์ → `ValueError`), `set_product_active`, `adjust_stock(id, delta) -> bool` (atomic, ติดลบ → False ไม่แก้), `sync_stock_from_options(id)`, `list_low_stock(threshold)`, `list_low_stock_options(threshold)`, `list_distinct_values(column)` (weight_class/balance/flex/level) · **filters** (dict, ไม่ใส่ = ไม่กรอง): `category_id, brand_id, weight_class, balance, flex, level` (ค่าเดียวหรือ list), `min_price, max_price` (กับราคาที่ใช้จริง), `search` (ชื่อ/คำอธิบาย/แบรนด์), `on_sale`, `in_stock`, `active_only` (ค่าเริ่มต้น True = สินค้า+หมวด+แบรนด์ต้องเปิดอยู่) · **sort**: `newest|price_asc|price_desc|name|popular` · แถวสินค้ามี `category_name, brand_name, effective_price` เพิ่ม · หมวด/แบรนด์: `list_categories(active_only=True)`, `get_category`, `create_category(name, image_path=None)`, `update_category(id, name, image_path=None)`, `set_category_active` และ `list_brands/get_brand/create_brand(name, logo_path=None)/update_brand/set_brand_active` (ชื่อซ้ำ → `sqlite3.IntegrityError`) · ตัวเลือก: `list_options(product_id)`, `get_option(id)`, `create_option(product_id, option_type, option_value, extra_price=0, stock=0) -> id`, `update_option(id, option_type, option_value, extra_price, stock)`, `delete_option(id)` (เคยถูกสั่งซื้อ → `IntegrityError`; เช็คก่อนด้วย `is_option_used(id)`), `adjust_option_stock(id, delta) -> bool` (atomic) — **เพิ่ม/แก้/ลบ/ปรับสต็อกตัวเลือกแล้ว `products.stock` ถูก sync เป็นผลรวมตัวเลือกให้เอง** · addons: `list_addons(product_id)` (เฉพาะ active), `set_addons(product_id, ids) -> int` (แทนที่ทั้งชุด ข้ามตัวเอง/ซ้ำ)
**database.repo_cart** — `list_items(user_id)` (คอลัมน์: `cart_item_id, product_id, option_id, qty, product_name, price, sale_price, sale_ends_at, effective_price, image_path, product_stock, product_active, option_type, option_value, extra_price, option_stock`), `get_item(user_id, cart_item_id)`, `add_or_increase(user_id, product_id, option_id, qty=1) -> cart_item_id` (สินค้า+ตัวเลือกเดิมบวกจำนวน; option_id None รวมกันได้), `set_qty(user_id, cart_item_id, qty)`, `remove(user_id, cart_item_id)`, `clear(user_id) -> int`, `count(user_id) -> int` (ผลรวม qty)
**database.repo_wishlist** — `add(user_id, product_id) -> bool`, `remove`, `is_in`, `list(user_id)` (สินค้า active + effective_price), `ids(user_id) -> set`
**database.repo_addresses** — `list(user_id)` (หลักก่อน), `get(address_id)`, `get_default(user_id)`, `count(user_id)`, `create(user_id, recipient, phone, address_line, district, province, postcode, is_default=False) -> id` (is_default=True ล้างหลักเดิมให้), `update(address_id, recipient, phone, address_line, district, province, postcode)`, `delete(address_id)`, `set_default(user_id, address_id) -> bool` (ไม่ใช่ของ user → False) — **ไม่ตรวจเจ้าของใน get/update/delete → service ต้องตรวจเอง**; ที่อยู่แรกของผู้ใช้ให้เป็น default → service ทำ
**database.repo_orders** — `create_order(user_id, recipient_name, recipient_phone, shipping_address, subtotal, discount, shipping_fee, total, coupon_id=None) -> id` (status = pending; ปัดเงิน 2 ตำแหน่ง), `add_items(order_id, items) -> int` (item dict: `product_id, option_id, product_name, option_label, price_at_purchase, qty`), `get_order(id)` (+`buyer_username, buyer_name, item_count`), `list_orders(user_id=None, status=None, limit=50, offset=0, search=None)` (status ค่าเดียว/list), `count_orders(user_id, status, search)`, `update_status(order_id, status, expected_status=None) -> bool` (ระบุ expected = เปลี่ยนเมื่อสถานะปัจจุบันตรงเท่านั้น), `set_cancel_reason(order_id, reason)`, `list_items(order_id)` (+`image_path`), `list_expired_pending(hours)`, `find_completed_order_with_product(user_id, product_id)` (Row + `already_reviewed` 0/1; เลือกอันที่ยังไม่รีวิวก่อน) · `add_status_log(order_id, status, note=None, changed_by=None) -> id`, `list_status_log(order_id)` (+`changed_by_name`) · สถิติ (นับสถานะ paid/shipped/completed; วันที่ `YYYY-MM-DD`): `sum_revenue(date_from=None, date_to=None) -> float`, `count_by_status() -> dict` (ครบทุกสถานะ), `top_products(n=5, date_from, date_to)` (`product_id, product_name, total_qty, total_sales`), `daily_sales(days=7)` (`day, orders, revenue` เฉพาะวันที่มียอด — ให้ service เติมวันว่างเอง) · ค่าคงที่ `REVENUE_STATUSES`
**database.repo_payments** — `create(order_id, method, amount, slip_path=None) -> id`, `get(id)`/`get_latest_by_order(order_id)`/`list_by_order`/`list_pending()` (คอลัมน์เพิ่ม `buyer_id, order_total, order_status, buyer_name, buyer_username`), `mark_verified(payment_id, verified_by) -> bool`, `mark_rejected(payment_id, reason, verified_by) -> bool` (ทำได้เฉพาะที่ยัง pending; ปฏิเสธก็เก็บ `verified_by/verified_at` = คนที่ตรวจ)
**database.repo_shipping** — `create(order_id, carrier=None, tracking_no=None, status="preparing") -> id`, `get_by_order(order_id)`, `update(order_id, carrier=None, tracking_no=None, status=None) -> bool` (None = ไม่เปลี่ยนค่านั้น; อัปเดต `updated_at` เสมอ; ไม่มีแถว → False)
**database.repo_coupons** — `get_by_code(code)` (ไม่สนตัวพิมพ์/ช่องว่าง), `get(id)`, `list_all()`, `create(code, discount_type, value, min_order=0, max_uses=None, expires_at=None, is_active=True) -> id` (โค้ดซ้ำ/ประเภทผิด → `IntegrityError`), `update(id, fields: dict)`, `set_active`, `increment_used(id) -> bool` (atomic; เต็มแล้ว → False), `decrement_used(id)` (ไม่ต่ำกว่า 0), `add_usage(coupon_id, user_id, order_id)` (ซ้ำ → `IntegrityError`), `has_used(user_id, coupon_id)`, `remove_usage(order_id)`
**database.repo_reviews** — `create(user_id, product_id, order_id, rating, comment=None) -> id` (ซ้ำ/ดาวนอก 1–5 → `IntegrityError`), `list_by_product(product_id, limit=10, offset=0)` (+`reviewer_name, reviewer_avatar`), `count_by_product`, `get_summary(product_id) -> (avg, count)` ((0.0, 0) ถ้าไม่มี), `get_summaries(ids) -> {id: (avg, count)}`, `exists(user_id, product_id, order_id)`
**database.repo_chat** — `add_message(customer_id, sender_type, sender_id, message) -> id`, `list_messages(customer_id, after_id=0, limit=None)` (เก่า→ใหม่; limit = ล่าสุด N), `list_threads()` (`customer_id, full_name, username, avatar_path, last_message, last_sender_type, last_at, unread_count`), `mark_read(customer_id, reader_side)` (`"staff"`|`"customer"` มิฉะนั้น `ValueError`; ค่าคงที่ `READER_STAFF/READER_CUSTOMER`), `count_unread_for_staff()`, `count_unread_for_customer(customer_id)`
**database.repo_notifications** — `create(user_id, title, message) -> id`, `create_for_staff(title, message) -> int` (admin+owner ที่ active), `list(user_id, limit=50, unread_only=False)`, `count_unread(user_id)`, `mark_read(notification_id, user_id=None) -> bool` (ใส่ user_id = ตรวจเจ้าของ), `mark_all_read(user_id) -> int`

**database.seed** — `run_seed(reset=False, assume_yes=False) -> bool` · `python -m database.seed` (ข้ามถ้ามีผู้ใช้แล้ว) · `--reset` (สำรอง DB → พิมพ์ YES → ล้างทุกตาราง → ใส่ใหม่); เข้ารหัสด้วย bcrypt ตรง ไม่พึ่ง services
 ข้อมูล seed: users `owner/owner123`, `admin1/admin123`, `buyer1/buyer123` (อีเมล `owner@shop.com`, `admin@shop.com`, `buyer@shop.com`); หมวด 6; แบรนด์ 6; สินค้า 25 (ไม้ 10 / ลูกแบด 4 / รองเท้า 3 / อื่น ๆ 8); `product_options` 35 แถว (Astrox 99 Pro = เอ็น, Nanoflare 800 = สี, ArCSaber 11 Pro = ด้าม, Tectonic 9 = สี **(สต็อก 3 และ 0 ไว้ทดสอบใกล้หมด/หมด)**, Dragon P = สี, รองเท้า 3 + เสื้อ 2 = ไซซ์, กระเป๋า BA92226EX = สี; `products.stock` = ผลรวมตัวเลือกแล้ว); `product_addons` 30 แถว (ไม้ทุกรุ่นคู่กับ เอ็น BG65 / ด้ามพัน AC102EX / Master No.3); คูปอง `WELCOME10` (10% min 500), `SAVE200` (ลด 200 min 2000), `OLD50` (หมดอายุแล้ว); ที่อยู่ buyer1 2 ที่; settings 8 key
 Flash Sale (วันที่นับจากเวลารัน seed): Astrox 99 Pro (+2 วัน), TK Ryuga II Pro (+5), Axforce Cannon (+7) · ลดต่อเนื่อง (`sale_ends_at` NULL): ArCSaber, Tectonic 9, Dragon P · **โปรหมดแล้ว (ต้องคิดราคาเต็ม): Z-Ziggler**
 ค่าสเปกไม้: weight_class `3U`,`4U` · balance `Heavy Head`,`Light Head`,`Even Balance` · flex `Stiff`,`Medium`,`Flexible` · level `Beginner`,`Intermediate`,`Advanced`,`Professional`

**core.permissions (เพิ่มส่วน C)** — `require_login() -> int` (id ผู้ใช้ปัจจุบัน; ไม่ล็อกอิน → PermissionError), `require_user(user_id)` (ต้องเป็นตัวเอง), `require_self(action, user_id)` (มีสิทธิ์ action **และ** เป็นตัวเอง — ใช้กับ cart/ออเดอร์/รีวิว), `require_any(*actions)` (มีสิทธิ์อย่างน้อยหนึ่งอย่าง) · ฟังก์ชันเดิมไม่เปลี่ยน

**services.auth_service** — `MAX_PASSWORD_BYTES = 72`; `hash_password`, `verify_password` (เดิม); `register(username, email, password, full_name, phone) -> dict` (บังคับ buyer); `login(identifier, password) -> dict` (ตั้ง Session + `is_online=1`; `ValueError` generic / "บัญชีนี้ถูกระงับการใช้งาน"); `logout()` (ล้างออนไลน์ + Session เสมอ); `clear_all_online() -> int` (เรียกตอนเปิด/ปิดแอป) · **ใหม่:** `change_password(user_id, old, new) -> True`, `update_profile(user_id, full_name, phone, avatar_path=None) -> dict` (อัปเดต `Session.current_user["full_name"]` ด้วย), `create_staff(username, email, password, full_name, phone, role="admin") -> dict` (owner; role อื่น → ValueError), `set_user_active(user_id, bool) -> dict` (owner; ห้ามระงับตัวเอง/เจ้าของ), `list_users(role=None, search=None) -> list[dict]` (owner; มี `is_online`) — dict ผู้ใช้: `id, username, email, full_name, phone, role, avatar_path, is_active, created_at` (ไม่มี `password_hash`) · `change_password` และ `update_profile`: ผู้ใช้ทุก role ทำได้เฉพาะบัญชีของตัวเอง (PermissionError ถ้า user_id ไม่ตรง Session)

**services.settings_service** — อ่าน (ทุกคน): `get(key, default=None) -> str`, `get_float(key, default=0.0)`, `get_int(key, default=0)`, `get_bool(key, default=False)`, `get_all() -> dict`, `get_shop_info() -> dict` (`shop_name, promptpay_no, promptpay_name, shipping_fee, free_shipping_min, low_stock_threshold, unpaid_cancel_hours, ai_enabled` แปลงชนิดแล้ว), `shipping_fee_for(subtotal) -> float` (**กติกาค่าส่งใบเดียว**: ฟรีเมื่อ `free_shipping_min` > 0 และ subtotal ≥ เกณฑ์) · แก้ (owner, `settings.manage`): `update(key, value)`, `update_many(dict)` → คืน `get_shop_info()` (ตรวจครบก่อนบันทึก ผิดอันเดียว = ไม่บันทึกเลย; promptpay_no เก็บเป็นตัวเลขล้วน ตรวจด้วย `promptpay.build_payload`) · `EDITABLE_KEYS`

**services.product_service** — **ฟังก์ชันล้วน (ไม่แตะ DB รับ dict/Row ได้):** `get_effective_price(product, extra_price=0) -> float`, `is_on_sale(product) -> bool`, `sale_seconds_left(product) -> int|None` · **ผู้ซื้อ (`shop.browse`):** `search_products(query=None, filters=None, sort="newest", page=1, page_size=12, user_id=None) -> {items, total, page, page_size, pages}` (item = แถวสินค้า + `effective_price, is_on_sale, sale_seconds_left, in_stock, avg_rating, review_count, in_wishlist`; filters: `category_id, brand_id, weight_class, balance, flex, level, min_price, max_price, on_sale, in_stock`; เห็นเฉพาะสินค้า+หมวด+แบรนด์ที่เปิดขาย), `get_product_detail(product_id, user_id=None) -> dict` (+`options` [`label, final_price, in_stock`], `has_options`, `addons`, `review_avg, review_count, in_wishlist, is_racket`; ปิดขาย/ไม่พบ → ValueError), `compare_products(ids) -> list[dict]` (2–3 ไม้เท่านั้น), `recommend_rackets(level, style, budget=None, limit=6) -> list[dict]` (+`match_score, match_reasons`; ค่า `STYLE_ATTACK="attack"`, `STYLE_CONTROL="control"`, `STYLE_SPEED="speed"`, `STYLE_LABELS`), `list_filter_values() -> {brands, categories, weight_class, balance, flex, level}`, `list_categories(include_inactive=False)`, `list_brands(include_inactive=False)` · **แอดมิน/เจ้าของ:** `list_products_admin(search=None, filters=None, sort, page, page_size=20, show_inactive=True)` (รูปแบบเหมือน search_products), `get_product_for_edit(id)` (+options+addons), `save_product(fields: dict, product_id=None) -> dict`, `adjust_stock(product_id, delta, option_id=None) -> dict`, `get_low_stock_products() -> {threshold, products, options}`, `save_option(product_id, option_type, option_value, extra_price=0, stock=0, option_id=None) -> dict`, `delete_option(option_id) -> dict`, `set_addons(product_id, addon_ids) -> dict` · **เจ้าของ:** `set_product_active(id, bool)`, `save_category(name, category_id=None, image_path=None)`, `set_category_active`, `save_brand(name, brand_id=None, logo_path=None)`, `set_brand_active` — คืน dict สินค้าล่าสุดเสมอ · กติกา: แอดมิน "ตั้งราคาปกติตอนเพิ่มสินค้า" ได้ แต่ **เปลี่ยนราคา/ตั้งราคาลด/Flash Sale ของสินค้าที่มีอยู่ได้เฉพาะเจ้าของ**; สินค้าที่มีตัวเลือกจะละเว้นคีย์ `stock` (ปรับผ่าน adjust_stock/save_option)

**services.review_service** — `can_review(user_id, product_id, order_id) -> bool`, `find_reviewable_order(user_id, product_id) -> int|None` (ไว้โชว์ปุ่มรีวิว), `add_review(user_id, product_id, order_id, rating, comment=None) -> dict` (rating ต้องเป็น int 1–5), `list_reviews(product_id, page=1, page_size=10) -> {items, total, avg, count, page, page_size, pages}` (item: `id, rating, comment, created_at, reviewer_name, reviewer_avatar`)

**services.coupon_service** — `validate_coupon(code, user_id, subtotal, conn=None) -> {coupon_id, code, discount_type, value, discount, description}` (ไม่แก้ DB; ValueError แยกกรณี), `calculate_discount(coupon, subtotal) -> float` · owner: `create_coupon(code, discount_type, value, min_order=0, max_uses=None, expires_at=None, is_active=True)`, `update_coupon(id, fields)`, `toggle_coupon(id, active=None)`, `get_coupon(id)`, `list_coupons()` (dict + `is_expired`, `remaining`) — วันหมดอายุแบบวันที่ล้วน = ใช้ได้ถึง 23:59:59 ของวันนั้น

**services.cart_service** — ทุกฟังก์ชันต้องเป็นผู้ซื้อและ `user_id` = ตัวเอง: `get_cart(user_id, conn=None) -> {items, subtotal, item_count, has_problem}` (item: `cart_item_id, product_id, option_id, product_name, image_path, option_label, unit_price, qty, line_total, stock_available, problem (ข้อความไทยหรือ None), is_available`), `get_cart_count(user_id)`, `add_to_cart(user_id, product_id, option_id=None, qty=1) -> {cart_item_id, cart_count}`, `add_with_addons(user_id, product_id, addon_ids, option_id=None, qty=1, addon_options=None) -> {cart_item_ids, cart_count}` (ทั้งชุดหรือไม่เลย), `update_qty(user_id, cart_item_id, qty) -> get_cart()`, `remove_item(...) -> bool`, `clear_cart(user_id) -> int`, `format_option_label(type, value) -> str|None`, `MAX_QTY_PER_ITEM = 99`

**services.notification_service** — ภายในระบบ (ไม่ตรวจสิทธิ์ผู้เรียก): `notify(user_id, title, message="", conn=None) -> id`, `notify_staff(title, message="", conn=None) -> จำนวนคน` · ของตัวเอง (ทุก role ที่ล็อกอิน): `list_my(limit=50, unread_only=False) -> list[dict]`, `unread_count()`, `mark_read(notification_id) -> bool`, `mark_all_read() -> int` — **ห้าม import service อื่น**

**services.order_service** — ผู้ซื้อ (`order.own`, ต้องเป็นเจ้าของ): `checkout(user_id, address_id, coupon_code=None) -> dict` (transaction เดียว: ตรวจที่อยู่/ตะกร้า → คูปอง → ค่าส่งจาก subtotal ก่อนหักส่วนลด → สร้างออเดอร์+รายการ+log → ตัดสต็อก → นับคูปอง → ล้างตะกร้า → แจ้งเตือน), `cancel_order(order_id, reason) -> dict` (ผู้ซื้อ: เฉพาะ pending ของตัวเอง · admin/owner: pending/checking_slip/paid; คืนสต็อก+คูปอง, ปิดสลิปที่ค้างตรวจ, ยกเลิกหลัง paid จดว่าต้องคืนเงินด้วยมือ), `confirm_received(order_id) -> dict` (shipped → completed), `list_my_orders(user_id, status=None, page=1, page_size=10)` → `{items, total, page, page_size, pages}` (item = orders + `status_label`, `items` ย่อ) · ทั้ง buyer/staff (เจ้าของหรือ `order.view`): `get_order_detail(order_id) -> dict` (orders + `status_label, buyer_username, buyer_name, item_count, coupon_code, items[{…, line_total, image_path}], payment|None, shipment|None, timeline`), `get_timeline(order_id)` · staff: `list_orders_admin(status=None, search=None, page=1, page_size=20)`, `get_dashboard_stats(days=7)` → `counts, pending_slips, revenue_today/month/total, top_products, daily_sales (เติมวันว่างแล้ว)` (**รายได้เห็นเฉพาะ owner** — admin ได้ None) · ระบบ: `auto_cancel_unpaid() -> int` (ไม่ต้องล็อกอิน; เรียกตอนเปิดแอปและ `on_show` หน้าออเดอร์; ปิดได้ด้วย `unpaid_cancel_hours <= 0`; นับเวลาจากครั้งล่าสุดที่เข้า pending จึงให้เวลาแนบสลิปใหม่หลังถูกปฏิเสธ) · ภายใน (ใช้ร่วมกับ service อื่น ไม่ตรวจสิทธิ์): `apply_status_change(conn, order_id, from, to, note, changed_by)`, `complete_delivery(conn, order, changed_by, by_buyer)`, `load_order_detail(order_id, conn=None)`, `authorize_view(order)`, `check_low_stock_and_notify(conn, changes)` (แจ้งเมื่อสต็อก **ข้ามเกณฑ์** ใกล้หมดเท่านั้น), ค่าคงที่ `ALLOWED_TRANSITIONS`
**services.payment_service** — `get_payment_info(order_id) -> dict` (`amount, promptpay_no/name, shop_name, payload` สำหรับ `promptpay.make_qr_image`, `payment` ล่าสุด, `history`, `can_submit_slip`) · ผู้ซื้อ: `submit_slip(order_id, file_path) -> order detail` (pending → checking_slip; บันทึกลง `config.SLIPS_DIR`; DB พลาด = ลบไฟล์ให้) · staff (`slip.verify`): `list_pending_payments()`, `verify_payment(payment_id) -> order detail` (→ paid + สร้าง shipments preparing), `reject_payment(payment_id, reason) -> order detail` (→ pending ผู้ซื้อแนบใหม่ได้)
**services.shipping_service** — staff (`shipment.update`): `ship_order(order_id, carrier, tracking_no)` (carrier ต้องอยู่ใน `constants.CARRIERS`; เลขพัสดุ A-Z 0-9 - ยาว 4-40), `update_tracking(order_id, carrier, tracking_no)` (แก้ตอน shipped), `mark_delivered(order_id)` (→ completed) · เจ้าของ/staff: `get_shipment(order_id) -> dict|None` — ทุกฟังก์ชันคืน order detail (ยกเว้น get_shipment)
**services.receipt_service** — `generate_receipt(order_id) -> str` (path relative เช่น `assets/receipts/receipt_12.pdf` เปิดด้วย `image_utils.resolve_path`; เจ้าของ/staff; เฉพาะ paid/shipped/completed; เขียนทับได้), `find_thai_font() -> dict|None`, `reset_font_cache()`, `THAI_MARK_LIFT` (ปรับความสูงวรรณยุกต์) · ไม่มีฟอนต์ไทยในเครื่อง → `ValueError` บอกวิธีติดตั้ง
**services.account_service** — ที่อยู่ (`address.manage`, ของตัวเองเท่านั้น): `list_addresses(user_id)`, `get_address`, `add_address(user_id, recipient, phone, address_line, district, province, postcode, is_default=False)` (สูงสุด `MAX_ADDRESSES`=10; แห่งแรกเป็นหลักเสมอ; เบอร์ตัดขีด/ช่องว่างให้), `update_address(user_id, address_id, recipient, …, postcode)`, `delete_address` (ลบหลัก → ตั้งอันที่เหลือเป็นหลัก), `set_default_address` · wishlist (`wishlist.use`): `toggle_wishlist(user_id, product_id) -> {"in_wishlist"}`, `list_wishlist(user_id)` (dict เหมือนการ์ดสินค้า), `wishlist_ids(user_id) -> set` · `get_profile(user_id)` (+`address_count, default_address, wishlist_count, order_count`), `set_avatar(user_id, src_path)` (แก้ชื่อ/เบอร์ใช้ `auth_service.update_profile`)
**services.ai_service** — `is_configured()`, `build_system_prompt()`, `ask(history, question) -> str` (**ไม่โยน exception**; พลาด/ไม่มีคีย์/ไม่มีเน็ต = `FALLBACK_MESSAGE`; history = list dict `sender_type, message` ก่อนคำถาม)
**services.chat_service** — ลูกค้า (`chat.customer`, ห้องตัวเอง): `send_message(customer_id, text, background=True) -> {"message", "ai_pending"}` (AI ตอบใน thread เมื่อ `should_ai_reply()`), staff (`chat.reply`): `staff_reply(customer_id, text)`, `list_threads()` · ทั้งสองฝั่ง: `get_messages(customer_id, after_id=0, limit=None, mark_read=True) -> list[dict]` (+`sender_name`; ใช้โพลทุก 3 วินาที), `unread_count() -> int`, `should_ai_reply() -> bool` · AI ไม่ส่งซ้อนถ้าแอดมินออนไลน์/ตอบเองระหว่างรอ และไม่ส่งข้อความสำรองซ้ำ

**utils.validators** — `is_valid_email`, `is_valid_phone` (`^0\d{9}$`), `is_strong_password` (≥ 8 ตัว), `is_valid_username`, `is_valid_postcode` (5 หลัก) → `bool`

**utils.formatters** — `format_price(x)` ("1,290 บาท" / "1,290.50 บาท"; None → "0 บาท"), `format_datetime(v)` ("11 ต.ค. 2569 07:12"), `format_date_thai(v)` ("11 ต.ค. 2569"), `format_phone(p)` ("081-234-5678"), `parse_datetime(v) -> datetime | None` · ปี **พ.ศ.** · ไม่มีค่า → `"-"` · **ห้ามใช้ ฿**

**utils.image_utils** — `load_ctk_image(path, (w,h)) -> CTkImage` (cache; None/ไม่พบ/เสีย → placeholder), `make_placeholder((w,h), text="No Image") -> PIL.Image`, `save_upload(src, dest_dir, prefix, max_side=1200) -> str` (คืน path relative จาก root เช่น `assets/slips/slip_5_....jpg`; `ValueError` ไทย: ไม่พบไฟล์/นามสกุล/ใหญ่เกิน 5MB/ไม่ใช่รูป), `delete_upload(rel_path)`, `resolve_path(rel) -> Path`, `clear_cache()`

**utils.promptpay** — `build_payload(phone_or_id, amount=None) -> str` (เบอร์ 10 หลัก/บัตร 13 หลัก/e-wallet 15 หลัก; `ValueError` ถ้าเลขผิดหรือยอด ≤ 0), `make_qr_image(payload, size=260) -> PIL.Image`, `crc16_ccitt(text) -> str`

**utils.backup** — `backup_db(keep=10, prefix="shop") -> Path`, `list_backups() -> list[dict]` (`path, name, size, created_at` ใหม่สุดก่อน), `auto_backup_on_exit(keep) -> Path|None` (ส่วน G; สำรองเป็น `shop_auto_*.db` ข้ามถ้า DB ไม่เปลี่ยนจากไฟล์สำรองล่าสุด; ไม่โยน exception), `restore_backup(path)` (`ValueError` ไทย; สำรองของเดิมเป็น `shop_prerestore_*.db` ก่อน; หลังกู้คืนให้เปิดแอปใหม่)

**main** — `python main.py` (เปิดแอป) · `python main.py --check` (ตรวจ ไลบรารี/DB/ทุกหน้า/พร้อมเพย์/ฟอนต์ไทย/AI/รหัสผ่านตั้งต้น คืน exit code 0/1) · `prepare_database() -> bool` (init_db + seed ถ้าไม่มีผู้ใช้), `warn_default_passwords() -> list`, `run_check() -> int`, `main(argv) -> int`

**utils.font_installer** — `install_project_fonts(force=False) -> list[str]` (ติดตั้ง `.ttf/.otf` ใน `assets/fonts` ให้ผู้ใช้ปัจจุบัน; marker `data/.fonts_installed` ผูกกับเครื่อง + ชุดไฟล์ฟอนต์ — ใส่ฟอนต์ไทยเพิ่มแล้วติดตั้งใหม่เองรอบถัดไป)

**ui.theme** — `COLORS` (เดิม + `surface_alt, danger_hover, star, star_off`), `ON_PRIMARY`, `FONTS` (เดิม + `small_bold, tiny, price, price_big`), `ThemeManager`: `setup()` (โหลดโหมดที่จำไว้จาก `data/ui_prefs.json`), `set_mode`, `toggle_mode()` (สลับจากโหมดที่เห็นจริง), `is_dark()`, `get_color`, `get_color_pair`, `get_font`, `get_font_obj(style, overstrike=..)`, `apply_card_style`, `button_style(kind="primary|secondary|danger|success|ghost|outline", size="sm|md|lg") -> dict` (ใช้ `CTkButton(..., **ThemeManager.button_style("primary"))`), `entry_style(height=40) -> dict`, `make_card(parent, **kw)`, `make_badge(parent, text, kind)`, `status_badge(parent, status)` (ออเดอร์/สลิป/จัดส่ง)

**ui.router** — `ROUTE_TABLE` (route → (โมดูล, คลาส) แบบ lazy import), `PUBLIC_ROUTES`, `ROUTE_ROLES` (ผู้ซื้อ: หน้าซื้อของ · admin+owner: dashboard/products/product_form/orders/order_detail/payments/chat · owner เท่านั้น: users/settings/categories/coupons/coupon_form · `profile`, `notifications` ทุก role) · `Router(container)`: `.show(route, **params)` (เรียก `on_show(**params)`; ไม่มี params เรียก `on_show()`), `.go_back(default=None)`, `.refresh()`, `.refresh_shell()` (อัปเดตตัวเลข navbar/sidebar), `.go_after_login(user)`, `.logout()`, `.register_route(name, page)`, `.register_temp_routes(dict)`, `.add_listener(f(route, params))`, `.current_route`, `.current_params`, `.history` · หน้าที่ไฟล์ยังว่าง/ไม่มีคลาส → แสดงหน้า "ยังไม่พร้อมใช้งาน" (เงียบ); หน้าที่ import/สร้างพัง → พิมพ์ traceback + แสดงข้อความบนหน้าแทน

**ui.app** — `App(ctk.CTk)` (1100×760, min 900×600), `main()`; เริ่มระบบ: `install_project_fonts` → `ThemeManager.setup` → `config.ensure_dirs` + `db.init_db()` → `auth_service.clear_all_online()` + `order_service.auto_cancel_unpaid()` → แสดง login; ปิดหน้าต่าง = `clear_all_online()`; error หลุดจาก callback ของ Tk = พิมพ์ traceback + กล่องข้อความ · navbar แสดงเฉพาะ buyer (ไม่ใช่ login/register), sidebar เฉพาะ admin/owner

**ui.components** (ทุกตัวรันเดี่ยว `python -m ui.components.<ชื่อ>`):
- `rating.RatingStars(parent, value, count=None, size=16, interactive=False, command=None)` → `.set(v, count)`, `.get() -> int`
- `search_bar.SearchBar(parent, command(text), placeholder, width, height)` → `.get/.set/.clear/.focus/.submit`
- `dialogs`: `confirm(parent, title, message, confirm_text, cancel_text, danger) -> bool`, `show_message(parent, title, message, kind="info|success|error|warning")`, `ask_reason(parent, title, message, required=True, confirm_text, placeholder, danger) -> str|None`
- `product_card.ProductCard(parent, product, on_open(pid), on_wishlist(pid)->bool|None, width)` + `format_countdown(sec)`, `discount_percent(price, eff)`
- `product_grid.ProductGrid(parent, controller, card_width, on_page_change(page), on_open, on_wishlist="auto"|callable|None, empty_text)` → `.set_result(search_products_result)`, `.set_products(items)`, `.remove_product(id)`, `.clear()`; คลิกการ์ด → `show("product_detail", product_id=)`; หัวใจเรียก `account_service.toggle_wishlist` เอง
- `product_filter.ProductFilter(parent, on_apply(filters), show_category=False, show_spec=True)` → `.get_filters()` (ราคาผิด → ValueError ไทย), `.set_filters(d)`, `.reset()`, `.set_spec_visible(b)`, `.reload_options()`
- `image_picker.ImagePicker(parent, size, initial_path, on_change, allow_clear)` → `.get_selected_file()` (path เต็ม ยังไม่บันทึก — หน้าเรียก `image_utils.save_upload` เอง), `.get_existing_path()`, `.is_cleared()`, `.has_change()`, `.set_image(rel_path)`
- `order_timeline.OrderTimeline(parent)` → `.set_order(order_detail)` หรือ `.set_data(timeline, shipment)`
- `payment_qr.PaymentQR(parent, size=240)` → `.set_info(get_payment_info)`, `.clear()`
- `chat_bubble.ChatBubble(parent, message, is_mine)`, `ChatMessageList(parent, viewer="customer"|"staff")` → `.set_messages`, `.append_messages(list) -> จำนวนที่เพิ่ม` (ไม่ซ้ำ), `.last_id`, `.show_typing()/.hide_typing()`, `.clear()`
- `navbar.Navbar(parent, controller)` / `sidebar.Sidebar(parent, controller)` — อยู่ถาวรที่ app.py ไม่ต้องสร้างในหน้า; `.refresh()`, `sidebar.set_active(route)`

**ui.pages.buyer.login.LoginPage(parent, controller)** — `handle_login()`, `on_show()` · `auth_service.login` → `controller.go_after_login(user)`
**ui.pages.buyer.common** (ใหม่ ส่วน E — หน้าผู้ซื้อทุกหน้าใช้ร่วมกัน) — `user_id()`, `toggle_wishlist(parent, product_id) -> bool|None` (error แสดง dialog), `page_title(parent, text, subtitle=None)`, `section_header(parent, text, action_text=None, action=None)`, `error_label(parent, **kw)`, `product_cards(parent, items, controller, width) -> [ProductCard]`, `WrapGrid(parent, item_width, gap)` (`.set_items(widgets)` / `.clear()` — วิดเจ็ตต้องสร้างโดยมี WrapGrid เป็น parent; ขึ้นบรรทัดใหม่ตามความกว้าง)
**หน้าผู้ซื้อที่เสร็จ (คลาส + on_show):** `RegisterPage.on_show()` · `HomePage.on_show()` · `CategoryPage.on_show(category_id=None, brand_id=None, search=None, on_sale=None)` · `ProductDetailPage.on_show(product_id)` · `ComparePage.on_show(ids=None)` · `RacketFinderPage.on_show()` · `WishlistPage.on_show()` · `CartPage.on_show()` · `AddressesPage.on_show()` — หน้าเหล่านี้เรียก route: `product_detail(product_id)`, `category(category_id|search|on_sale)`, `compare(ids=[...])`, `racket_finder`, `cart`, `checkout`, `login`

**ui.pages.admin.common** (ใหม่ ส่วน F — หน้าแอดมินทุกหน้าใช้ร่วมกัน; **ครึ่งหลังต้องสืบทอด/ใช้ต่อ ไม่เขียนซ้ำ**) — `AdminPage(parent, controller)` (คลาสฐาน: `.content` กรอบเนื้อหา, `.clear_content()`, `.set_error(msg)`, `.call(func, *a, **kw) -> (ok, ผล)` จับ ValueError/PermissionError แสดงแดงในหน้า, `.allowed()` + `OWNER_ONLY = True` สำหรับหน้าเจ้าของ, `.refresh_shell()`) · ปุ่ม/ช่อง: `btn(parent, text, command, kind, size, **kw)`, `entry(parent, placeholder, height, **kw)`, `option_menu(parent, values, variable, command, width)`, `card(parent)`, `label(parent, text, style, muted=False, **kw)`, `pill(parent, text, kind=success|warning|danger|info|muted)`, `error_label`, `page_header(parent, title, subtitle) -> (header, actions)`, `stat_card`, `place_grid(widgets, columns)`, `table_header/table_row/configure_columns/empty_state`, `Pager(parent, on_change).set(page, pages, total)` · สี/ฟอนต์: `color(name)`, `resolve_color(pair)` (สำหรับ Canvas), `font(style)` (มีค่าสำรองถ้า ThemeManager ไม่มีชื่อนั้น) · รูป/ไฟล์: `thumb(parent, path, size)`, `load_fit_image(path, max_w, max_h)`, `show_image_window(parent, path, title)`, `open_file(path)` · แปลงค่า: `as_dict(row)`, `is_owner()`, `parse_money(text, label, required, minimum)`, `parse_int(text, label, required, minimum)` (ValueError ไทย) — **กฎ: CTkFrame ที่ไม่มีลูกจะสูง 200px → กรอบรายการต้องมีวิดเจ็ตอย่างน้อยหนึ่งตัวเสมอ**
**หน้าแอดมินที่เสร็จ (คลาส + on_show) — ครบ 12 หน้า:** `AdminDashboardPage.on_show()` · `AdminProductsPage.on_show()` · `AdminProductFormPage.on_show(product_id=None)` · `AdminCategoriesPage.on_show()` (owner) · `AdminOrdersPage.on_show(status=None)` · `AdminOrderDetailPage.on_show(order_id)` · `AdminPaymentsPage.on_show()` · `AdminCouponsPage.on_show()` (owner) · `AdminCouponFormPage.on_show(coupon_id=None)` (owner) · `AdminChatPage.on_show(customer_id=None)` · `AdminUsersPage.on_show()` (owner) · `AdminSettingsPage.on_show()` (owner) — เรียก route: `admin_payments` (ไม่ส่ง params), `admin_orders(status)`, `admin_order_detail(order_id)`, `admin_product_form(product_id)`, `admin_coupons`, `admin_coupon_form(coupon_id)`, `admin_chat(customer_id)`, `admin_dashboard` (หน้า owner-only ถูกเด้งมาที่นี่ถ้าเป็น admin)

---

## บันทึกความคืบหน้า (อัปเดตท้ายทุกส่วน — วางบล็อกที่ AI ส่งให้ต่อท้ายหัวข้อนี้)

### สถานะปัจจุบัน
**ส่วน A, B เสร็จครบ (2026-10-11)** — ฐานราก + repository ทั้งหมด (14 ไฟล์) ผ่านเทสต์ 26 ข้อ
**ส่วน C เสร็จครบ (15/15 ไฟล์, 2026-10-12)** — เทสต์รวม 128 ข้อผ่าน (repos 26 + services ครึ่งแรก 58 + order flow 44)
**ส่วน D เสร็จครบ (15 ไฟล์ + แก้ login.py, 2026-10-12)** — ตรวจด้วย stub/AST เท่านั้น ยังไม่เคยรัน GUI
**ส่วน E เสร็จครบ (2026-10-12)** — หน้าผู้ซื้อ 18 หน้า + `common.py`
**ส่วน F เสร็จครบ (2026-10-12)** — `common.py` + หน้าแอดมิน 12 หน้า
**ส่วน G เสร็จครบ (2026-10-12)** — main.py, README, สำรองอัตโนมัติ, ตรวจทั้งแอปบน GUI จริง · **เหลือ: FIX-16 (ผู้ใช้เปลี่ยนรหัสผ่านเอง), ลองรันบน Windows, และข้อจำกัดที่ยังไม่ทำด้านล่าง**

### ไฟล์ที่เสร็จและใช้งานได้แล้ว (ไม่ต้องแก้ ยกเว้นระบุใน FIX)
ส่วน A ทั้งหมด (15 ไฟล์ + `tests/test_promptpay.py`) · ส่วน B ทั้งหมด (`database/repo_*.py` + `repo_base.py` + `tests/test_repos.py`) · ส่วน C ทั้งหมด (`services/*.py` ครบ 14 ไฟล์ + tests/test_order_flow.py`; ครึ่งแรก: `auth/settings/product/review/coupon/cart/notification_service.py` + `core/permissions.py` ที่เพิ่มตัวช่วย + `tests/test_services_basic.py`) · ส่วน D ทั้งหมด (`ui/theme.py`, `router.py`, `app.py`, `components/*` 12 ไฟล์) · `ui/pages/buyer/login.py` (แก้ import แล้ว) · ส่วน E ทั้งหมด (`ui/pages/buyer/*` 18 หน้า + `common.py`) · ส่วน F ทั้งหมด (`ui/pages/admin/*` 12 หน้า + `common.py` + `__init__.py`)

### การตัดสินใจที่ AI ตั้งต้นไว้ให้ — ผู้ใช้ยืนยันหรือแก้ได้ (ถ้าไม่ตอบ ให้ใช้ค่าเริ่มต้นนี้)
| รหัส | เรื่อง | ค่าเริ่มต้นที่ใช้ |
|---|---|---|
| D-01 | สิทธิ์ admin | ตามตารางสิทธิ์ — admin เช็คสินค้า/แก้สต็อก, ตอบแชท, ตรวจสลิป, อัปเดตจัดส่ง; owner ทำได้ทุกอย่าง |
| D-02 | ตัดสต็อกเมื่อไร | ตอนสร้างออเดอร์ (คืนเมื่อยกเลิก/หมดเวลาจ่าย) |
| D-03 | หน้า "ตัวช่วยเลือกไม้" | เพิ่มไฟล์ใหม่ `ui/pages/buyer/racket_finder.py` |
| D-04 | ไฟล์ที่เสนอเพิ่มจากโครงที่ยืนยันไว้ | `database/repo_settings.py`, `services/settings_service.py`, `services/product_service.py`, `services/account_service.py`, `services/chat_service.py`, `ui/pages/buyer/racket_finder.py` (6 ไฟล์) |
| D-05 | ฟอนต์ไทย | **(แก้ตามผู้ใช้สั่ง 2026-10-12)** ไม่ต้องใส่ฟอนต์ไทยใน `assets/fonts` — ตัวอังกฤษ/ตัวเลขใช้ Arimo, ตัวไทยใช้ฟอนต์ที่มากับ OS (Windows: Leelawadee UI/Tahoma · macOS: Thonburi · Linux: Noto Sans Thai/Loma/Garuda) ใบเสร็จ PDF ทำตามนี้แล้ว; **ส่วน D (`ui/theme.py`) ต้องตั้ง `FONTS` ให้ตรงกัน** (ไทยตามระบบ — Tk/CustomTkinter จะ fallback ฟอนต์ไทยให้เองเมื่อ family เป็น Arimo) |
| D-06 | ต้องล็อกอินก่อนดูสินค้าไหม | ใช่ (ตามที่ทำไว้: ไม่ล็อกอิน = เห็นแค่หน้า login/register) |
| D-07 | AI ตอบเมื่อไร | เมื่อไม่มี admin/owner ที่ `is_online = 1` |

### ข้อควรรู้ / บั๊กที่แก้ / การตัดสินใจเพิ่มเติม
**จบส่วน A**
- ส่วน B: repo ฟังก์ชันเขียนให้รับ `conn=None`; งานหลายตารางครอบด้วย `database.db.transaction()`; `categories`/`brands` มี `is_active`; `order_items.option_label`, `orders.cancel_reason`, `coupon_usages`, `product_addons` พร้อมใช้; `repo_settings` (ใหม่) ควรอ่านค่าตั้งต้นจาก `config.DEFAULT_SETTINGS` เมื่อ key ไม่มีใน DB
- `seed.py` ไม่ import services แล้ว; bcrypt ตรงให้ผล verify ร่วมกับ `auth_service` ได้ (ทดสอบแล้ว)
- `core.permissions`: owner **ไม่มี** สิทธิ์ฝั่งผู้ซื้อ (ตามตาราง) — ถ้าอยากให้เจ้าของลองซื้อของเอง ต้องแก้ตาราง
- CHECK ใหม่ของ `payments/shipments/chat_messages/coupons` มีผลเฉพาะ DB ที่สร้างใหม่ → ให้ลบ `data/shop.db` แล้วรัน `python -m database.seed` (ข้อมูลเก่าเป็นของ seed ทั้งหมด)
- ทดสอบแล้วด้วยการรันจริง: init_db 2 รอบ = 20 ตาราง + WAL + FK; seed 2 รอบไม่ลบผู้ใช้ที่สมัครเอง; `--reset`; transaction rollback/commit; CHECK ปฏิเสธค่าผิด; เติมคอลัมน์ให้ DB เก่า; save_upload (ย่อรูป/ปฏิเสธ gif/ไฟล์เสีย/เกิน 5MB); backup/restore/prune; unit test PromptPay 9 ข้อ (CRC ตรงค่ามาตรฐาน `29B1` และตรงกับ `binascii.crc_hqx`)
- **ยังไม่ได้ทดสอบ:** `load_ctk_image` กับ customtkinter ตัวจริง (เครื่องตรวจไม่มี tkinter — ทดสอบตรรกะด้วย stub), สแกน QR ด้วยแอปธนาคารจริง, ติดตั้งฟอนต์บน Windows
- ค้างไว้: ฟอนต์ไทยใน `assets/fonts/` ต้องมีก่อนทำใบเสร็จ PDF (ส่วน C, D-05); ก่อนส่งงานเปลี่ยนรหัสผ่านบัญชี seed และเลขพร้อมเพย์ (FIX-16, ส่วน G)
**จบส่วน B**
- ทำงานตามตกลง: โค้ดเก่าใน B มีแค่ `repo_users.py` (6 ฟังก์ชัน) — ทดสอบแล้วใช้ได้ จึงคงฟังก์ชันเดิมไว้ทั้งหมด (เปลี่ยนเป็น `use_conn` + รับ `conn` เพิ่ม) แล้วต่อเติม 7 ฟังก์ชันตาม FIX-10; `auth_service` เดิม login/register ยังทำงานปกติ
- เพิ่มไฟล์ `database/repo_base.py` (ไม่ได้อยู่ในแผนเดิม) เพื่อไม่ให้ซ้ำโค้ดจัดการ `conn=None` 13 ที่; **ผู้ใช้ต้องคัดลอกไฟล์นี้ไปด้วย**
- **หน้าที่ของ service ที่ repo ไม่ทำ (ส่วน C ต้องทำ):** ตรวจเจ้าของ (addresses get/update/delete, orders, payments), ตรวจ qty ≥ 1, ตรวจสต็อกก่อนตัด, ตรวจ role/สิทธิ์, ลำดับสถานะออเดอร์, คำนวณราคา/ส่วนลด/ค่าส่ง, ตั้งที่อยู่แรกเป็น default, normalize รหัสคูปองเป็นตัวพิมพ์ใหญ่ก่อน `create`, แปลง `sqlite3.IntegrityError` → `ValueError` ไทย, เติมวันว่างให้ `daily_sales`, แปลง `Row` → `dict` ก่อนส่ง UI
- **ตัดสต็อกตอน checkout:** ใช้ `repo_products.adjust_stock(pid, -qty, conn=conn)` (สินค้าไม่มีตัวเลือก) หรือ `adjust_option_stock(option_id, -qty, conn=conn)` (มีตัวเลือก — สต็อกรวมสินค้า sync ให้เอง) ถ้าได้ `False` = สต็อกไม่พอ → `raise ValueError` ให้ transaction rollback (กันติดลบ/กันสองคนซื้อชิ้นสุดท้าย); คืนสต็อกตอนยกเลิกด้วย delta บวก; คูปอง: `increment_used` False = สิทธิ์เต็ม
- เปลี่ยนสถานะออเดอร์ให้ใช้ `update_status(..., expected_status=สถานะเดิม)` แล้วเช็คผล `False` = มีคนเปลี่ยนไปแล้ว (กันกดซ้ำ)
- สินค้าที่หมวด/แบรนด์ถูกปิด (`is_active=0`) จะไม่ขึ้นในรายการ/ค้นหา (`active_only` ค่าเริ่มต้น); `get_product(id)` ยังคืนให้ทุกกรณี — service ตัดสินเองว่าให้ผู้ซื้อเห็นไหม
- ทดสอบแล้ว (26 เทสต์ผ่าน บน DB ชั่วคราวที่ seed): กรอง Heavy Head+Stiff = Astrox 99 Pro + Dragon P · ราคาจริง (Flash Sale ยังไม่หมด/โปรหมดแล้ว=ราคาเต็ม) · เพิ่มสินค้า+ตัวเลือกเดิมซ้ำ = บวกจำนวน · ที่อยู่ default มีได้ 1 ต่อผู้ใช้ · สต็อกไม่ติดลบ · sync สต็อกตัวเลือก→สินค้า · transaction rollback · ออเดอร์/สถานะ/ยกเลิกอัตโนมัติ (pending เกินเวลา) · สถิติ Dashboard · คูปอง (ซ้ำ/ครบสิทธิ์/คืนสิทธิ์) · รีวิว (ซ้ำถูกปฏิเสธ) · แชท/แจ้งเตือน
- รันเทสต์: `python -m unittest tests.test_repos -v` (ใช้ DB ชั่วคราว ไม่แตะ `data/shop.db`); เครื่องตรวจไม่มี bcrypt/qrcode จึงใช้ stub bcrypt ทดสอบ — `test_promptpay` ไม่ได้รันในเครื่องตรวจ (ขาด qrcode) ให้ผู้ใช้รันเอง
- ฟังก์ชันที่ส่วน C จะเรียกใช้: ทุกฟังก์ชันใน "ฟังก์ชันสาธารณะ" ของ `database.repo_*` ด้านบน
- วิธีทำงานที่ตกลงกันเพิ่ม: **AI อัปเดต PROGRESS.md เอง** (ติ๊ก `[x]`, ย่อส่วนที่เสร็จ, เติมฟังก์ชันสาธารณะ/ข้อควรรู้) แล้วส่งไฟล์เต็มกลับให้ผู้ใช้ทับของเดิม — ไม่ต้องวางบล็อกเอง

**จบส่วน C ครึ่งแรก (2026-10-11)** — ทำ 7 ไฟล์: auth, settings, product, review, coupon, cart, notification
- โค้ดเก่าที่มีอยู่: `services/auth_service.py` (176 บรรทัด) ใช้ต่อได้ — เก็บ `hash_password/verify_password/register/login/logout` พฤติกรรมเดิมครบ (ข้อความ error เดิมทุกข้อ) แค่ยุบขั้นตอนสร้างบัญชีเป็น `_create_account()` ใช้ร่วมกับ `create_staff`; `tests/test_repos.py` และ `tests/test_promptpay.py` เดิมใช้ต่อได้ไม่แก้ (ไฟล์ว่าง: `tests/test_order_flow.py` และ services อื่น ๆ ยังไม่ได้เขียน)
- `core/permissions.py` เพิ่ม 4 ตัวช่วย (`require_login/require_user/require_self/require_any`) — **ผู้ใช้ต้องคัดลอกไฟล์นี้ไปทับด้วย**
- เพิ่มนอกเช็คลิสต์เดิม (หน้าแอดมินจะต้องใช้): product_service ส่วนแอดมิน (`list_products_admin, get_product_for_edit, save_option, delete_option, set_addons, set_product_active, save/set_*_active` ของหมวด/แบรนด์), `coupon_service.get_coupon/list_coupons`, `review_service.find_reviewable_order`, `cart_service.get_cart_count/clear_cart`, `auth_service.clear_all_online`, `settings_service.update_many/get_bool/shipping_fee_for`
- **การตัดสินใจ (D-01 ตีความเพิ่ม):** แอดมินเพิ่มสินค้าและตั้ง "ราคาปกติ" ตอนสร้างได้ แต่เปลี่ยนราคา/ตั้งราคาลด/Flash Sale ของสินค้าที่มีแล้วไม่ได้ (เจ้าของเท่านั้น) — ตรงกับตาราง "แก้ราคา = owner"; ถ้าอยากให้แอดมินแก้ราคาได้ ให้แก้เงื่อนไข `is_owner` ใน `product_service.save_product`
- ผู้ซื้อ (role buyer) เท่านั้นที่ค้นหา/ดูรายละเอียด/เปรียบเทียบ/ใส่ตะกร้าได้ — แอดมินและเจ้าของใช้ `list_products_admin/get_product_for_edit` (ตรงตาราง: owner ไม่มีสิทธิ์ฝั่งผู้ซื้อ)
- `login()` ตั้ง `is_online = 1` ให้ทุก role (ใช้จริงเฉพาะ admin/owner ตอนตัดสินว่า AI ตอบแชท); `logout()` ล้างทุกกรณี; **app.py (ส่วน D) ต้องเรียก `auth_service.clear_all_online()` ตอนเปิดแอป และตอนปิดหน้าต่าง**
- **ข้อตกลงที่ order_service ครึ่งหลังต้องทำตาม:**
  1. `checkout` อ่านตะกร้าด้วย `cart_service.get_cart(user_id, conn=conn)` ใน transaction เดียว; `has_problem` = True → `ValueError`; ใช้ `unit_price` เป็น `price_at_purchase`, `option_label` ใส่ `order_items.option_label`; ก่อนตัดสต็อกตรวจซ้ำเองด้วย `repo_products.adjust_stock/adjust_option_stock(..., conn=conn)` (False = สต็อกไม่พอ → raise ให้ rollback)
  2. คูปอง: `coupon_service.validate_coupon(code, user_id, subtotal, conn=conn)` แล้ว `repo_coupons.increment_used(id, conn=conn)` (False → "ใช้ครบสิทธิ์แล้ว") + `add_usage` (IntegrityError → "ใช้ไปแล้ว")
  3. ค่าส่ง: `settings_service.shipping_fee_for(subtotal)` โดยส่ง **subtotal ก่อนหักส่วนลด** (ตามกติกา "ฟรีเมื่อ subtotal ≥ free_shipping_min"); `total = round(subtotal - discount + shipping_fee, 2)`
  4. แจ้งเตือนใน transaction: `notification_service.notify(user_id, title, msg, conn=conn)` / `notify_staff(title, msg, conn=conn)` (ถ้า rollback การแจ้งเตือนหายไปด้วย — ทดสอบแล้ว)
  5. เกณฑ์สต็อกต่ำ/ชั่วโมงยกเลิกอัตโนมัติ: `settings_service.get_int("low_stock_threshold")`, `get_int("unpaid_cancel_hours", 24)`; หลังตัดสต็อกใช้ `repo_products.list_low_stock/list_low_stock_options` เทียบเกณฑ์
  6. สิทธิ์: ผู้ซื้อใช้ `permissions.require_self(ORDER_OWN, user_id)`; staff ใช้ `ORDER_VIEW/ORDER_CANCEL/SLIP_VERIFY/SHIPMENT_UPDATE`; service ทุกตัวต้องไม่ import `ui`
- ทดสอบแล้ว (58 เทสต์ ใน `tests/test_services_basic.py`): ล็อกอิน/ออนไลน์/เปลี่ยนรหัส/ระงับบัญชี · ค่าตั้งค่า (ผิดอันเดียวไม่บันทึกเลย, เลขพร้อมเพย์) · ราคาจริงตรงกับ SQL ทุกสินค้า (Flash Sale/โปรหมดอายุ/ลดตลอด) · ค้นหา+กรองสเปก+แบ่งหน้า+wishlist · สินค้า/หมวดปิดแล้วผู้ซื้อไม่เห็น · เปรียบเทียบ 2–3 ไม้ · ตัวช่วยเลือกไม้ · แอดมินแก้ราคาไม่ได้/เจ้าของแก้ได้ · ปรับสต็อกติดลบไม่ได้ · ตัวเลือกที่เคยสั่งซื้อลบไม่ได้ · รีวิว (เฉพาะ completed, ซ้ำไม่ได้) · คูปองทุกกรณีผิดพลาด · ตะกร้า (สต็อกรวมที่อยู่ในตะกร้า, ตัวเลือกถูกลบ, ซื้อคู่กันทั้งชุดหรือไม่เลย) · แจ้งเตือน (แก้ของคนอื่นไม่ได้, rollback)
- รันเทสต์: `python -m unittest tests.test_services_basic -v` (ต้องมี bcrypt จริงตาม requirements.txt; เครื่องตรวจไม่มี bcrypt จึงใช้ตัวจำลองในการรัน)
- **ยังไม่ได้ทดสอบ:** bcrypt จริง (ผ่านตัวจำลอง), การทำงานพร้อมกันของสองโปรเซสจริง, Windows
- ครึ่งหลังของส่วน C (order → payment → shipping → receipt → account → ai → chat → test_order_flow) ทำเสร็จแล้ว ดู "จบส่วน C ครึ่งหลัง" ท้ายไฟล์

**จบส่วน C ครึ่งหลัง (2026-10-12)** — ทำ 8 ไฟล์: order, payment, shipping, receipt, account, ai, chat, test_order_flow
- **ฟอนต์ใบเสร็จ (ตามที่ผู้ใช้สั่ง):** Arimo จาก `assets/fonts` สำหรับอังกฤษ/ตัวเลข + ฟอนต์ไทยของ OS (ไม่ต้องใส่ฟอนต์ไทยในโปรเจกต์) ข้อความที่ปนกันถูกแยกเป็นช่วง ๆ ให้เอง · reportlab ไม่มี text shaping ทำให้วรรณยุกต์ซ้อนสระบน (ชื่อ ที่ ปี้) ทับกัน → ยกวรรณยุกต์เองด้วย `THAI_MARK_LIFT = 0.22` และปิด shaping ของ reportlab (`shapable=False`) ให้ผลเหมือนกันทุกเครื่อง · **ตรวจหน้าตาจริงด้วยฟอนต์ FreeSerif เท่านั้น** (เครื่องตรวจไม่มี Tahoma/Leelawadee/Thonburi) — ถ้าบนเครื่องจริงวรรณยุกต์สูง/ต่ำไป ให้ปรับค่านี้ตัวเดียว
- สต็อก: `checkout` ใช้ `adjust_stock/adjust_option_stock` แบบ atomic — ทดสอบแล้ว ชิ้นสุดท้ายสองคนซื้อ คนที่สองได้ error สต็อกไม่ติดลบ (ทดสอบทั้งทางตะกร้าแจ้งหมด และทางข้อมูลตะกร้าเก่า) · ยกเลิกแล้วสต็อก/สิทธิ์คูปองกลับครบ
- ข้อตกลงที่ UI ต้องรู้: (1) service ที่เปลี่ยนสถานะคืน **order detail dict** ทุกตัว — UI ใช้ผลนี้รีเฟรชหน้าได้เลย (2) เรียก `order_service.auto_cancel_unpaid()` ตอนเปิดแอปและใน `on_show` หน้าออเดอร์ (list_* ไม่เรียกให้เอง) (3) `chat_service.send_message` ปล่อย AI ตอบใน thread — UI โพล `get_messages(customer_id, after_id)` ทุก 3 วินาที (4) เปิดไฟล์ใบเสร็จ/สลิปด้วย `image_utils.resolve_path(path)`; path อาจเป็น absolute ถ้าอยู่นอกโฟลเดอร์โปรเจกต์ (5) QR: `promptpay.make_qr_image(info["payload"], 260)` (6) เจ้าของร้าน (owner) ไม่ใช่ผู้ซื้อ — เรียก checkout/ตะกร้า/wishlist/ที่อยู่ไม่ได้ตามตารางสิทธิ์
- เพิ่มนอกเช็คลิสต์เดิม (หน้าแอดมินต้องใช้): `order_service.get_dashboard_stats`, `get_timeline`; `shipping_service.update_tracking`; `account_service.get_address/get_profile/set_avatar`; `chat_service.unread_count`; `check_low_stock_and_notify(conn, changes)` (ต่างจากแผนเดิมที่เป็น `(conn)` — รับ `changes` เพื่อแจ้งเฉพาะตอนข้ามเกณฑ์ ไม่แจ้งซ้ำทุกออเดอร์)
- เหตุผลด้านพฤติกรรมที่ตั้งไว้ (เปลี่ยนได้): ผู้ซื้อยกเลิกได้เฉพาะ `pending` · admin ยกเลิกได้จนก่อน `shipped` · ขนส่งต้องอยู่ใน `CARRIERS` (ไม่มี "อื่นๆ") · AI ไม่ส่งข้อความสำรองซ้ำถ้าข้อความสำรองเดิมเพิ่งส่งไปแล้ว
- ทดสอบแล้ว (44 เทสต์ใน `tests/test_order_flow.py`): flow เต็มสมัคร→รีวิว · ราคา Flash Sale/หมดเวลา/ตัวเลือก · ค่าส่งฟรี · คูปอง (ขั้นต่ำ/หมดอายุ/ใช้ซ้ำ/ครบสิทธิ์ แล้วไม่มีอะไรเปลี่ยน) · สต็อกไม่พอ · ยกเลิก (ผู้ซื้อ/แอดมิน/อัตโนมัติ/หลังจ่ายเงิน) · สลิปถูกปฏิเสธแล้วแนบใหม่ · ข้ามขั้นสถานะ · สิทธิ์ buyer/admin/owner · Dashboard (owner เห็นรายได้ admin ไม่เห็น) · ใบเสร็จ PDF · ที่อยู่/wishlist/โปรไฟล์ · AI (mock: ไม่มีคีย์/timeout/ตอบว่าง/แอดมินเข้ามาระหว่างรอ) · แชท
- รันเทสต์: `python -m unittest tests.test_order_flow -v` (ใช้ DB/โฟลเดอร์ชั่วคราว ไม่แตะ `data/` และ `assets/` จริง; เทสต์ใบเสร็จ PDF จะข้ามถ้าเครื่องไม่มีฟอนต์ไทย)
- **ยังไม่ได้ทดสอบ:** bcrypt จริง (เครื่องตรวจใช้ตัวจำลอง), Gemini จริง (ไม่มีคีย์/เน็ต — ทดสอบด้วย mock; โค้ดเรียก `google-genai` ใน `_call_gemini` เขียนตามเอกสาร SDK แต่ยังไม่เคยรันจริง ถ้าพลาดผู้ใช้จะเห็นข้อความสำรอง), ฟอนต์ไทยจริงของ Windows/macOS (ดูข้างบน), สองโปรเซสซื้อพร้อมกันจริง (ใช้ `BEGIN IMMEDIATE` + atomic update), `test_promptpay` (ขาด qrcode ในเครื่องตรวจ)
- ฟังก์ชันที่ส่วน D/E/F จะเรียกใช้: ทุกฟังก์ชันใน "ฟังก์ชันสาธารณะ" ของ `services.*` ด้านบน

**จบส่วน D (2026-10-12)**
- **ข้อตกลงสำหรับ E/F (ต้องทำตาม):**
  1. ชื่อคลาสหน้า (ไฟล์เดิมใน `ui/pages/...` ชื่อไฟล์ = route ตัด `admin_` ออก): ผู้ซื้อ `LoginPage, RegisterPage, HomePage, CategoryPage, ProductDetailPage, ComparePage, RacketFinderPage, WishlistPage, CartPage, CheckoutPage, AddressesPage, PaymentPage, OrdersPage, OrderDetailPage, WriteReviewPage, ProfilePage, NotificationsPage, ChatPage` · แอดมิน `AdminDashboardPage, AdminProductsPage, AdminProductFormPage, AdminCategoriesPage, AdminOrdersPage, AdminOrderDetailPage, AdminPaymentsPage, AdminCouponsPage, AdminCouponFormPage, AdminChatPage, AdminUsersPage, AdminSettingsPage` (route แอดมินขึ้นต้น `admin_`) — ถ้าอยากเปลี่ยนชื่อ แก้ที่ `ROUTE_TABLE` ที่เดียว
  2. params ของ `on_show(self, ..., **kwargs)`: `product_detail(product_id)`, `category(category_id=None, brand_id=None, search=None)` (navbar ค้นหาส่ง `search`), `order_detail(order_id)`, `payment(order_id)`, `write_review(product_id, order_id)`, `compare(ids=None)`, `orders(status=None)`, `admin_order_detail(order_id)`, `admin_product_form(product_id=None)` (None = เพิ่มใหม่), `admin_coupon_form(coupon_id=None)`, `admin_chat(customer_id=None)`; หน้าที่ไม่รับ params ประกาศ `on_show(self)`
  3. หน้าอยู่ใน container เต็มพื้นที่ — **ไม่ต้องสร้าง navbar/sidebar เอง**; หลังแก้ตะกร้า/แจ้งเตือน/อ่านแชท เรียก `self.controller.refresh_shell()`; ย้อนกลับใช้ `self.controller.go_back(default="home")`
  4. ทุกหน้าต้องจับ `ValueError`/`PermissionError` จาก service แล้วแสดงด้วย `dialogs.show_message(..., kind="error")` หรือข้อความแดงในหน้า
- **การตัดสินใจ:** โหมดเริ่มต้นยังเป็น `system` แต่จำค่าที่ผู้ใช้สลับล่าสุดใน `data/ui_prefs.json` · `toggle_mode` สลับจากโหมดที่เห็นจริง (แก้บั๊กเดิมที่สลับครั้งแรกไม่เปลี่ยนเมื่ออยู่โหมด system+มืด) · owner/admin เข้าหน้าซื้อของไม่ได้ (ตามตารางสิทธิ์), `profile`/`notifications` เข้าได้ทุก role · navbar ค้นหาว่าง = ไปหน้าแรก · `App` เรียก `init_db()` เองตอนเริ่ม (main.py ส่วน G เรียกซ้ำได้)
- **สมมติฐานที่ยังไม่ยืนยันกับของจริง:** `product_service.list_filter_values()` ให้ brands/categories เป็นรายการที่มี `id`+`name`; `core.constants.ROLE_LABELS` เป็น dict; timeline item มี `status, note, changed_by_name, created_at`; `chat_service.unread_count()` และ `notification_service.unread_count()` ไม่รับพารามิเตอร์ — ถ้าผิด ตัวเลขบนไอคอนจะเป็น 0 / เมนูตัวกรองว่าง (ไม่พัง) แต่ต้องแก้
- **ทดสอบแล้ว:** `py_compile` ทุกไฟล์, ตรวจชื่อที่ไม่ได้ประกาศด้วย AST, Router ด้วย stub (สิทธิ์ 3 role, params ถึง on_show, go_back, logout ล้างหน้า, หน้าที่ว่าง/พังไม่ทำแอปล้ม), ฟังก์ชันล้วน (นับถอยหลัง, ส่วนลด %, แบ่งหน้า, ตรวจราคา)
- **ยังไม่ได้ทดสอบ:** ทุกอย่างที่เป็นหน้าจอจริง (เครื่องตรวจไม่มี tkinter/customtkinter) — จุดเสี่ยงที่ควรดู: dialogs (modal grab บน Windows), การ์ดสินค้า (hover/คลิก/นับถอยหลัง), กริดปรับคอลัมน์ตามความกว้าง, ฟอนต์ไทย/emoji ใน navbar-sidebar, เมนูผู้ใช้ (`tk.Menu`), OptionMenu ตัวกรอง, ปุ่มบันทึก QR

**จบส่วน E ครึ่งแรก (2026-10-12)** — ทำ 10 ไฟล์ใน `ui/pages/buyer/`: common 🆕, register, home, category, product_detail, compare, racket_finder, wishlist, cart, addresses
- **ไฟล์เพิ่มนอกแผน:** `ui/pages/buyer/common.py` (ตัวช่วยร่วม ดู "ฟังก์ชันสาธารณะ") — **ผู้ใช้ต้องคัดลอกไปด้วย** หน้าของ E ครึ่งหลังควรใช้ `common.*` ต่อ
- **การตัดสินใจ (เปลี่ยนได้):** (1) ปุ่ม "ซื้อเลย" เพิ่มลงตะกร้าแล้วไปหน้า `cart` (ไม่ข้ามไป checkout เพื่อให้เห็นของอื่นในตะกร้าด้วย) (2) สมัครสำเร็จ → กล่องข้อความ แล้วไปหน้า login (LoginPage ไม่รับข้อความ) (3) Flash Sale บนหน้าแรก = สินค้าลดราคาที่มี `sale_seconds_left` (ลดต่อเนื่องไม่นับ) (4) แบนเนอร์หน้าแรกเป็นกล่องข้อความสีเหลือง (ยังไม่มีรูป banner) (5) `category` รับ `on_sale=True` เพิ่ม (ปุ่ม "ดูสินค้าลดราคา") (6) `compare` เลือกจากไม้ที่มี `weight_class` (ไม้แบดทั้งหมดที่ขายอยู่)
- **ยังทำไม่ได้ (ต้องแก้ schema):** ช่องแจ้งความตึงเอ็น (lbs) ต่อสินค้าในตะกร้า — `cart_items`/`order_items` ไม่มีที่เก็บ จึงแสดงข้อความแนะนำให้แจ้งทางแชทแทน (ถ้าอยากได้จริงต้องเพิ่มคอลัมน์ `note` ใน cart_items/order_items + แก้ cart/order service)
- **ทดสอบแล้ว:** py_compile ทุกไฟล์ + รันจริงกับ services บน DB seed ด้วย customtkinter จำลอง (27 รายการ: เปิดทุกหน้า, หน้าสินค้าครบ 25 ชิ้น, เพิ่มตะกร้า/ซื้อคู่กัน/wishlist, เปรียบเทียบ 1–3 ไม้, ตัวช่วยเลือกไม้ รวมงบน้อยเกินไป, ตะกร้า ปรับจำนวน/ลบ/ว่าง, ที่อยู่ เพิ่ม/แก้/ลบ, สมัครสมาชิก) — **จับบั๊กได้ 1 จุดแล้วแก้** (home ส่ง `height` ซ้ำกับ `button_style`) · **ยังไม่ได้ทดสอบบนจอจริง:** layout/ขนาด/การเลื่อน, กริดปรับคอลัมน์, นับถอยหลัง Flash Sale, กล่อง dialog
- ฟังก์ชันที่ E ครึ่งหลังจะเรียกใช้: `order_service.checkout/list_my_orders/get_order_detail/cancel_order/confirm_received`, `payment_service.get_payment_info/submit_slip`, `receipt_service.generate_receipt`, `review_service.add_review/can_review`, `account_service.get_profile/set_avatar`, `auth_service.update_profile/change_password`, `notification_service.*`, `chat_service.*` (ดู "ฟังก์ชันสาธารณะ")

**จบส่วน E ครึ่งหลัง (2026-10-12)** — ทำ 8 ไฟล์ใน `ui/pages/buyer/`: checkout, payment, orders, order_detail, write_review, profile, notifications, chat (ไม่แก้ไฟล์เดิมใดเลย รวมถึง `common.py`)
- **checkout:** เลือกที่อยู่ด้วย radio (คลิกทั้งการ์ดได้, เลือกค่าเริ่มต้นให้) · กรอกโค้ดแล้ว "ใช้โค้ด" → เรียก `coupon_service.validate_coupon` แสดงส่วนลด/ค่าส่ง/ยอดชำระสดก่อนสั่ง (ค่าส่งคิดจาก subtotal ก่อนหักส่วนลด ตรงกับ `order_service`) · สั่งซื้อสำเร็จ → `show("payment", order_id=...)` · ถ้า checkout พลาดเพราะโค้ด จะล้างโค้ดให้กรอกใหม่ ถ้าพลาดเพราะสต็อก/ตะกร้า จะโหลดตะกร้าใหม่
- **payment:** `PaymentQR` + ยอด + `ImagePicker` สลิป → `submit_slip` · แสดงตามสถานะ: pending (แนบสลิป, เตือนเวลาจ่ายจาก `unpaid_cancel_hours`, ถ้าสลิปถูกปฏิเสธโชว์เหตุผล) / checking_slip (รอตรวจ + รูปสลิปที่ส่ง) / ชำระแล้ว / ยกเลิก · ปุ่มยกเลิกคำสั่งซื้อ (ถามเหตุผล) เฉพาะ pending
- **orders:** แท็บสถานะ 7 แท็บ + แบ่งหน้า 6 รายการ · `on_show(status=None)` เรียก `auto_cancel_unpaid()` ก่อนโหลด · ปุ่มลัด ชำระเงิน (pending) / ได้รับสินค้าแล้ว (shipped) / ดูรายละเอียด
- **order_detail:** timeline, เลขพัสดุ (+ปุ่มคัดลอก), รายการสินค้า, สรุปยอด (ชื่อโค้ดส่วนลด), ที่อยู่, สถานะชำระเงิน, ปุ่มตามสถานะ (ชำระ/ยกเลิก/ได้รับสินค้าแล้ว/ดูสถานะสลิป) · **ปุ่ม "⭐ เขียนรีวิว" อยู่ที่นี่** (ต่อสินค้า เมื่อ completed และ `can_review`) · ใบเสร็จ PDF สร้างใน thread แล้วเปิดด้วยโปรแกรมเริ่มต้นของเครื่อง (ฟังก์ชัน `open_file` ในไฟล์นี้: Windows `os.startfile`, macOS `open`, Linux `xdg-open`; เปิดไม่ได้จะแจ้งตำแหน่งไฟล์) — หน้าที่ต้องรอ thread ใช้รูปแบบ "thread ใส่ผลลง dict + หน้าโพลด้วย `after()`" ห้ามเรียก tkinter จาก thread
- **write_review:** `on_show(product_id, order_id)` · ดาว (`RatingStars` interactive) + ความเห็น (นับตัวอักษร/1000) · เช็ค `can_review` ก่อนเปิดปุ่มส่ง · สำเร็จ → กลับ `order_detail`
- **profile (ทุก role):** แก้ชื่อ/เบอร์/รูป (`auth_service.update_profile` + `account_service.set_avatar`), เปลี่ยนรหัสผ่าน (ยืนยันรหัสใหม่ในหน้า), สถิติ+ทางลัด 3 ช่อง (เฉพาะผู้ซื้อ), ปุ่มออกจากระบบ
- **notifications (ทุก role):** การ์ดใหม่สุดก่อน (สูงสุด 100) · จุด/ขอบเหลืองคือยังไม่อ่าน · คลิกการ์ดเพื่อทำเครื่องหมายอ่าน · "อ่านทั้งหมด" · ยังไม่มีลิงก์ไปหน้าออเดอร์ (ตาราง notifications ไม่มีที่เก็บ target)
- **chat:** `ChatMessageList` + ช่องพิมพ์ (Enter ส่ง) · โหลดประวัติล่าสุด 100 ข้อความ · โพลทุก 3 วินาทีด้วย `after()` เฉพาะตอนหน้าแสดงอยู่ (`winfo_ismapped`) · แสดง "AI กำลังพิมพ์..." เมื่อ `ai_pending` และซ่อนเมื่อร้าน/AI ตอบ (หรือครบ 60 วินาที) · `destroy()` ยกเลิกตัวโพลให้ · หัวหน้าบอกโหมด (แอดมินออนไลน์/AI ตอบแทน)
- **ทดสอบแล้ว:** py_compile + รันจริงกับ services บน DB seed ด้วย customtkinter/tkinter จำลอง (67 รายการ: checkout เลือกที่อยู่/โค้ดผิด/WELCOME10/ยกเลิกโค้ด/สั่งซื้อ/ตะกร้าว่าง/สต็อกหมด · payment ไม่เลือกสลิป/ส่งสลิป/ถูกปฏิเสธแล้วส่งใหม่/ชำระแล้ว/ออเดอร์ไม่มี · orders แท็บ/status ผิด/แบ่งหน้า/ยืนยันรับของ · order_detail ดูของคนอื่นไม่ได้/ยกเลิก/ใบเสร็จ PDF · write_review ไม่ให้ดาว/สำเร็จ/รีวิวซ้ำ · profile แก้ข้อมูล/เบอร์ผิด/เปลี่ยนรหัส/avatar/admin เปิดได้ · notifications อ่านทีละรายการ/ทั้งหมด/owner · chat ส่ง/ว่าง/ยาวเกิน/โพลข้อความแอดมิน/ไม่ซ้ำ) — สคริปต์ไม่ได้อยู่ในโปรเจกต์
- **ยังไม่ได้ทดสอบ:** ทุกอย่างที่เป็นหน้าจอจริง (จำลองไม่เห็นเลย์เอาต์) — จุดเสี่ยงที่ควรดูเมื่อรันจริง: checkout (radio+การ์ดที่อยู่, แผงสรุปยอดทางขวาในหน้าต่างเล็ก), payment (ภาพ QR/สลิปขนาดใหญ่), profile (กริดฟอร์ม 3 คอลัมน์ข้างรูปโปรไฟล์), chat (การเลื่อนลงล่างสุด/typing), ปุ่มเปิดใบเสร็จ PDF บน Windows, ฟอนต์ไทยใน PDF
- **ข้อจำกัดที่ยังไม่ทำ:** ช่องแจ้งความตึงเอ็นต่อสินค้า (ต้องเพิ่มคอลัมน์ใน schema) · แชทส่งรูปไม่ได้ · แจ้งเตือนกดไปหน้าที่เกี่ยวข้องไม่ได้
- ฟังก์ชันสาธารณะใหม่: `ui.pages.buyer.order_detail.open_file(path)` (F อาจใช้ซ้ำสำหรับใบเสร็จฝั่งแอดมิน) · ส่วน F ใช้ `ChatMessageList(viewer="staff")`, `OrderTimeline`, `PaymentQR`/ดูสลิป จาก components ได้เลยเหมือนหน้าผู้ซื้อ

**จบส่วน F ครึ่งแรก (2026-10-12)** — ทำ 7 ไฟล์ใน `ui/pages/admin/`: common 🆕, dashboard, products, product_form, categories, orders, order_detail (+ `__init__.py` ว่างที่มากับ admin.zip) — ไม่แก้ไฟล์เดิมใดเลย
- **ไฟล์เพิ่มนอกแผน:** `ui/pages/admin/common.py` (ผู้ใช้ต้องคัดลอกไปด้วย) — ครึ่งหลังต้องใช้ต่อ (ดู "ฟังก์ชันสาธารณะ")
- **dashboard:** การ์ดสลิปรอตรวจ (คลิกไป `admin_payments`) + รายได้วันนี้/เดือน/รวม (เฉพาะ owner; admin เห็น "แสดงเฉพาะเจ้าของร้าน") · การ์ดนับออเดอร์ตามสถานะ (คลิก → `admin_orders(status=)`) · กราฟแท่งรายวันวาดด้วย `tk.Canvas` (owner = รายได้, admin = จำนวนออเดอร์) เลือก 7/14/30 วัน · สินค้าขายดี · สต็อกต่ำ (สินค้า+ตัวเลือก, ปุ่มแก้ไข → `admin_product_form`)
- **products:** ค้นหา + กรองหมวด/แบรนด์/สถานะ + เรียง + แบ่งหน้า 20 · เจ้าของเห็นปุ่ม ปิดขาย/เปิดขาย · "ทุกสถานะ" = รวมสินค้าที่ปิดอยู่ (`show_inactive=True`); ยังไม่มีตัวกรอง "เฉพาะที่ปิดขาย" เพราะ `list_products_admin` ไม่มีพารามิเตอร์นี้
- **product_form:** ข้อมูล+รูป (`ImagePicker` → `save_upload` ลง `PRODUCT_IMAGES_DIR`) · สเปกไม้ 4 ช่อง · ตัวเลือก เพิ่ม/แก้/ลบ · addons ค้นหาแล้วกดเพิ่ม/เอาออก (เรียก `set_addons` ทั้งชุดทุกครั้ง) · **ตัวเลือกกับ addons ใช้ได้หลังบันทึกสินค้าครั้งแรก** (บันทึกแล้วหน้าโหลดซ้ำเป็นโหมดแก้ไขอัตโนมัติ) · สินค้ามีตัวเลือก = ล็อกช่องสต็อก
- **สิทธิ์ในฟอร์ม (ตามการตีความ D-01):** admin เพิ่มสินค้าใหม่ → ส่งแค่ `price` (ช่องราคาลด/วันสิ้นสุดโปรถูกล็อก); admin แก้สินค้าเดิม → ไม่ส่ง `price/sale_price/sale_ends_at` เลย (ช่องถูกล็อก); owner ส่งครบ · ฟอร์ม **ไม่ส่ง `is_active`** — ปิด/เปิดขายใช้ปุ่มแยก (`set_product_active`) เพื่อไม่ชนกฎของ `save_product` · ราคาลดต้อง < ราคาปกติ; กรอกวันสิ้นสุดโปรโดยไม่มีราคาลด = error; วันที่ล้วน (`2026-10-20`) = สิ้นสุด 23:59:59
- **categories (owner):** แท็บ หมวดหมู่/แบรนด์ ใช้แผง `_Panel` เดียวกัน · แก้ชื่อ/รูป (ไม่เลือกรูปใหม่ = ส่ง `image_path=None` = ไม่เปลี่ยนรูปเดิม — **สมมติฐานตามกติกา repo ของผู้ใช้/สินค้า ยังไม่ยืนยันกับ `save_category`/`save_brand` จริง**; ลบรูปเดิมออกไม่ได้) · โลโก้แบรนด์เก็บใน `assets/images/categories/` ชื่อ `brand_*` (โครงโฟลเดอร์ไม่มี `brands/`)
- **orders:** กรองสถานะ + ค้นหา + แบ่งหน้า 15 · เรียก `auto_cancel_unpaid()` ใน `on_show` · รับ `status` จากแดชบอร์ด
- **order_detail:** รายการ/สรุปยอด, timeline (`OrderTimeline.set_order`), ที่อยู่, สลิป (คลิกดูขยาย), บันทึกการจัดส่ง (`ship_order`), แก้เลขพัสดุ (`update_tracking`), ส่งถึงแล้ว (`mark_delivered`), ยกเลิกพร้อมเหตุผล (`cancel_order`; หลัง paid เตือนว่าต้องคืนเงินเอง), ใบเสร็จ PDF ใน thread · ผลที่ service คืน (order detail) ใช้วาดหน้าใหม่ + `refresh_shell()` · **ยืนยัน/ปฏิเสธสลิป ไม่ได้ทำในหน้านี้** — มีปุ่มลัดไป `admin_payments`
- **ทดสอบแล้ว:** py_compile + ตรวจชื่อที่ไม่ได้ประกาศด้วย AST + รันจริงด้วย customtkinter/tkinter/services จำลอง (34 รายการ: dashboard owner/admin/เปลี่ยนช่วงวัน · products กรอง/ค้นหา/ปิดขาย · ฟอร์ม เพิ่ม/แก้/ตรวจราคา/วันที่/ตัวเลือก/addons/สิทธิ์ admin · categories เพิ่ม/แก้/เปิดปิด/admin ถูกเด้ง · orders กรอง/ค้นหา · order_detail ทุกสถานะ/ship/delivered/cancel/ไม่พบออเดอร์/ใบเสร็จ) — สคริปต์ไม่ได้อยู่ในโปรเจกต์
- **ยังไม่ได้ทดสอบ:** ทุกอย่างที่เป็นหน้าจอจริง — จุดเสี่ยงเมื่อรัน: กราฟแท่ง (สีพื้น Canvas ตามโหมดมืด/สว่าง), ตารางสินค้า/ออเดอร์ในหน้าต่างแคบ, `ImagePicker(size=170/80)` (เดาว่ารับ int), สีที่ ThemeManager ไม่มี (ใช้ค่าสำรองใน `common.color`), หน้า order_detail 2 คอลัมน์, เปิดไฟล์ PDF บน Windows
- **สมมติฐานที่ยังไม่ยืนยันกับของจริง:** `get_dashboard_stats()["pending_slips"]` เป็นตัวเลขหรือ list (รองรับทั้งคู่) · `get_low_stock_products()["options"]` มี `product_id`, `product_name`, `option_type`, `option_value`, `stock` · `get_product_for_edit()["addons"]` มี `id` (หรือ `addon_product_id`) + `name` · `list_categories/list_brands(include_inactive=True)` คืน dict ที่มี `id, name, is_active, image_path|logo_path` — ถ้าชื่อคีย์ต่าง ช่องนั้นจะว่างหรือแสดง "-" (ไม่พัง)
- **ฟังก์ชันที่ครึ่งหลังเรียกใช้ (ทำแล้วใน F ครึ่งหลัง):** `payment_service.list_pending_payments/verify_payment/reject_payment` (payments.py — ควรรับ `on_show()` ไม่มี params), `coupon_service.list_coupons/get_coupon/create_coupon/update_coupon/toggle_coupon` (coupons, coupon_form), `chat_service.list_threads/get_messages/staff_reply/unread_count` + `ChatMessageList(viewer="staff")` (chat.py `on_show(customer_id=None)`), `auth_service.list_users/create_staff/set_user_active` (users.py), `settings_service.get_shop_info/update_many` + `utils.backup.backup_db/list_backups/restore_backup` (settings.py) · ทุกหน้าสืบทอด `AdminPage` จาก `common.py`

**จบส่วน F ครึ่งหลัง (2026-10-12)** — ทำ 6 ไฟล์ใน `ui/pages/admin/`: payments, coupons, coupon_form, chat, users, settings — **ส่วน F ครบ 12/12** (ไม่แก้ไฟล์เดิมใดเลย รวมถึง `common.py`; ทุกหน้าสืบทอด `AdminPage`)
- **payments:** การ์ดสลิปรอตรวจ (เก่าสุดก่อน) = รูปสลิป (คลิก/ปุ่มดูขยาย), ผู้ซื้อ, ยอดโอน เทียบยอดออเดอร์ (ไม่ตรง → เตือนแดง), ปุ่ม ยืนยัน (กล่องยืนยันก่อน) / ปฏิเสธ (บังคับเหตุผล ผู้ซื้อเห็น) / ดูออเดอร์ · ทำเสร็จโหลดรายการใหม่ + ข้อความเขียว + `refresh_shell()` · ถ้ามีคนตรวจไปก่อน แสดง error ของ service แล้วโหลดรายการใหม่โดยคง error ไว้
- **coupons (owner):** ตาราง โค้ด/ส่วนลด/ขั้นต่ำ/ใช้แล้ว-สิทธิ์/หมดอายุ/สถานะ · สถานะ = ปิดอยู่ → หมดอายุ → ครบสิทธิ์ → ใช้งานได้ (ฟังก์ชัน `coupon_status`) · กรองสถานะ + ค้นหาโค้ด (กรองในหน้า ไม่ยิง service ซ้ำ) · ปุ่ม เปิด/ปิด (`toggle_coupon(id, active=ตรงข้าม)`) · แก้ไข/เพิ่ม → `admin_coupon_form`
- **coupon_form (owner):** โค้ด (**ล็อกช่องหลังสร้าง** — แก้โค้ดไม่ได้), ประเภท %/บาท, มูลค่า (> 0, % ไม่เกิน 100), ขั้นต่ำ (ว่าง = 0), สิทธิ์ทั้งหมด (ว่าง = ไม่จำกัด; แก้ให้ต่ำกว่าที่ใช้ไปแล้วไม่ได้), วันหมดอายุ `YYYY-MM-DD` (ปี ค.ศ.; ว่าง = ไม่หมดอายุ; ตัด ` 23:59:59` ออกตอนแสดงในช่อง) · สร้าง → `create_coupon(...)`; แก้ → `update_coupon(id, {discount_type, value, min_order, max_uses, expires_at, is_active(1/0)})` · สำเร็จ → กล่องข้อความ แล้ว `go_back(default="admin_coupons")`
- **chat:** ซ้ายรายการห้อง (ชื่อ, ตัวอย่างข้อความ + คำนำหน้า "AI:"/"ร้าน:", เวลา, ป้ายแดงยังไม่อ่าน, ค้นหา) · ขวา `ChatMessageList(viewer="staff")` ในกรอบสูงคงที่ + ช่องพิมพ์ (Enter ส่ง; ผิด เช่น ยาวเกิน → error และคงข้อความในช่อง) · โหลดประวัติล่าสุด 200 ข้อความ · โพลทุก 3 วินาทีด้วย `after()` **เฉพาะตอนหน้าแสดงอยู่** (หยุดเองเมื่อซ่อน, `on_show` เริ่มใหม่, ไม่สะสมงานซ้ำ, `destroy()` ยกเลิก) · **ลำดับในโพล = ดึงข้อความใหม่ก่อน แล้วค่อยโหลดรายการห้อง** (การดึงข้อความคือสิ่งที่ทำเครื่องหมายอ่าน ไม่งั้นป้ายแดงของห้องที่เปิดค้างอีกรอบ — เทสต์จับได้และแก้แล้ว) · รายการห้องวาดใหม่เฉพาะเมื่อข้อมูลเปลี่ยน (กันกะพริบ) · `on_show(customer_id)` เปิดห้องนั้นทันที (ไม่มีข้อความ/ไม่อยู่ในรายการ → ใช้ชื่อ "ลูกค้า #id") · ไม่ใช่หน้า owner-only
- **users (owner):** ตาราง ชื่อ+รูป/อีเมล+เบอร์/บทบาท/สถานะ (ออนไลน์·ถูกระงับ·ปกติ)/วันที่สมัคร · ค้นหา (ส่งให้ `list_users`) + กรองบทบาท + แบ่งหน้า 15 **ในหน้า** (service ไม่มีแบ่งหน้า) · ปุ่ม ระงับ (ถามยืนยัน) / เปิดใช้งาน (ไม่ถาม) — **ไม่แสดงปุ่มกับเจ้าของร้านและตัวเอง** · ฟอร์มเพิ่มแอดมิน (พับเก็บได้): ยืนยันรหัสผ่านตรวจในหน้า, ที่เหลือให้ `create_staff(..., role="admin")` ตัดสิน; สำเร็จ → ล้างฟอร์ม+กล่องข้อความ (ไม่แสดงรหัสผ่านซ้ำ) 
- **settings (owner):** แบ่งหมวด ร้านค้า / พร้อมเพย์ / ค่าส่ง (ค่าส่ง, ฟรีเมื่อครบ) / สต็อกและออเดอร์ (เกณฑ์ใกล้หมด, ชั่วโมงยกเลิก) / AI (สวิตช์) → `update_many(dict)` · ปุ่ม "ยกเลิกการแก้ไข" โหลดค่าเดิมกลับ · สำรองข้อมูล: ปุ่ม "สำรองตอนนี้" (`backup_db()`), ตารางไฟล์สำรอง (ชื่อ/เวลา/ขนาด), "กู้คืน" (กล่องยืนยันสีแดง → `restore_backup(path)`) → ข้อความเตือน **"ต้องปิดแอปแล้วเปิดใหม่"** ค้างไว้แม้เปิดหน้าใหม่ · งานไฟล์เรียกผ่าน `_run()` ที่เช็ค `is_owner()` อีกชั้น + จับ `OSError` เป็นข้อความแดง (utils.backup ไม่ตรวจสิทธิ์เอง)
- **สมมติฐานที่ยังไม่ยืนยันกับของจริง (ถ้าผิดจุดนั้นจะว่าง/แจ้ง error ไม่ทำให้แอปพัง):** (1) `settings_service.update_many` รับค่าเป็น **ข้อความทั้งหมด** รวม `ai_enabled` = `"1"`/`"0"` (ตามค่าตั้งต้นใน `DEFAULT_SETTINGS`) — ถ้าต้องการ int/bool ให้แก้ใน `settings._save_settings` · (2) `coupon_service.update_coupon` รับคีย์ตามชื่อคอลัมน์ และ `max_uses=None` หมายถึงล้างเป็นไม่จำกัด · (3) `list_coupons()` มี `is_expired` และ `remaining` (None = ไม่จำกัด) · (4) `list_pending_payments()` แถวมี `id, order_id, amount, order_total, slip_path, created_at, buyer_name, buyer_username` · (5) `chat_service.list_threads()` ตาม `repo_chat.list_threads`; `ChatMessageList.last_id` เป็น 0 เมื่อว่าง; `get_messages(..., limit=)` รับ limit · (6) `auth_service.list_users` dict มี `is_online, created_at, avatar_path` · (7) `backup.list_backups()` มี `path, name, size, created_at` (created_at เป็นข้อความหรือ datetime ก็ได้) · (8) `dialogs.ask_reason(..., placeholder=...)` รับ placeholder
- **ทดสอบแล้ว:** py_compile + ตรวจชื่อที่ไม่ได้ประกาศ/import ที่ไม่ได้ใช้ด้วย AST + รันจริงด้วย customtkinter/tkinter/services จำลอง **109 รายการ** (payments: ยืนยัน/ปฏิเสธ/ยกเลิกกล่อง/ยอดไม่ตรง/ไม่พบรูป/มีคนตรวจไปก่อน · coupons: สถานะ 4 แบบ/กรอง/ค้นหา/toggle/เด้ง admin · coupon_form: ตรวจข้อมูลผิด 9 แบบ/สร้าง % และ บาท/โค้ดซ้ำ/แก้ไข ช่องล็อก/สิทธิ์ต่ำกว่าที่ใช้แล้ว/ไม่พบคูปอง · chat: เลือกห้อง/ส่ง/Enter/ยาวเกิน/โพลข้อความใหม่/ไม่วาดซ้ำ/ค้นหา/หยุดโพลเมื่อซ่อน/ไม่สะสมงาน/destroy/เปิดห้องจาก params · users: แบ่งหน้า/กรอง/ค้นหา/ระงับ-เปิด/ฟอร์มเพิ่มแอดมิน 4 กรณี · settings: โหลด/บันทึก/ข้อมูลผิด/ยกเลิกแก้/สำรอง/กู้คืน ปกติและไฟล์เสีย/เตือนค้าง/ชั้นป้องกันสิทธิ์) — วิดเจ็ตจำลองเลียนพฤติกรรมจริง 2 จุด: `CTkEntry` ที่ `state="disabled"` แก้ข้อความไม่ได้ และ `pack(before/after=)` ต้องอ้างวิดเจ็ตที่ pack แล้ว — สคริปต์ไม่ได้อยู่ในโปรเจกต์
- **ยังไม่ได้ทดสอบ:** ทุกอย่างที่เป็นหน้าจอจริง — จุดเสี่ยงเมื่อรัน: chat (CTkScrollableFrame รายการห้องซ้อนอยู่ในหน้าที่เลื่อนได้ → ล้อเมาส์อาจเลื่อนผิดชั้น; `ChatMessageList` ในกรอบสูงคงที่ 400px เลื่อนลงล่างสุดได้ไหม), การ์ดสลิป (รูป 150×200 + ปุ่มขวา ในหน้าต่างแคบ), ตารางผู้ใช้/คูปองในหน้าต่างแคบ, สวิตช์ `CTkSwitch` ในโหมดมืด, `CTkLabel(justify=...)` (ใช้ตามสไตล์เดิมของโปรเจกต์ — ถ้า customtkinter รุ่นที่ติดตั้งไม่รับจะ error ทุกหน้า ให้ดู traceback)
- **ข้อควรรู้สำหรับ G:** (1) สำรองอัตโนมัติตอนปิดแอปยังไม่ทำ — ใช้ `utils.backup.backup_db()` ใน `App` ตอนปิดหน้าต่าง (ข้างๆ `clear_all_online()`) · (2) หน้า settings ยังไม่มีช่องตั้งจำนวนไฟล์สำรองที่เก็บ (ใช้ค่า `config.BACKUP_KEEP_COUNT`) · (3) การกู้คืนทับ DB ขณะแอปเปิดอยู่ — ผู้ใช้ต้องปิด/เปิดแอปใหม่เอง (ไม่มีรีสตาร์ตอัตโนมัติ) · (4) ยังไม่มีช่องแก้โค้ดคูปองหลังสร้าง / ลบคูปอง (ใช้ปิดแทน) · (5) ทดสอบรวมควรไล่ flow: ผู้ซื้อแนบสลิป → payments ยืนยัน → order_detail บันทึกพัสดุ → ผู้ซื้อเห็น timeline เปลี่ยน, แชทผู้ซื้อ↔แอดมิน (ทั้ง AI/แอดมินออนไลน์), owner เห็นทุกเมนู/admin ถูกเด้งจากหน้า owner-only

**จบส่วน G (2026-10-12)** — ไฟล์: `main.py` 🆕เนื้อหา, `README.md` 🆕เนื้อหา, `utils/backup.py` (+`auto_backup_on_exit`), `ui/app.py` (`_on_close` เรียกสำรองอัตโนมัติ), แก้บั๊ก `ui/pages/admin/dashboard.py` และ `ui/components/image_picker.py`
- **บั๊กที่เจอจากการรัน GUI จริงครั้งแรก (แก้แล้ว):** (1) `dashboard.BarChart` ตั้งชื่อเมธอด `_draw` ชนกับ `CTkFrame._draw` → หน้า Dashboard ของ admin/owner เปิดไม่ขึ้น (`TypeError ... no_color_updates`) แก้เป็น `_draw_chart` (และ `_data` → `_series`) (2) `ImagePicker(size=170)` / `size=80` ส่งตัวเลขเดี่ยว แต่คอมโพเนนต์รับเฉพาะ `(กว้าง, สูง)` → หน้า "เพิ่ม/แก้สินค้า" และ "หมวดหมู่/แบรนด์" เปิดไม่ขึ้น แก้ที่ `ImagePicker` ให้รับตัวเลขเดี่ยว = สี่เหลี่ยมจัตุรัส (ไม่เปลี่ยนการใช้งานเดิม)
- **main.py:** ตั้ง cwd = root, ตรวจไลบรารีก่อน (ขาด = กล่องข้อความ + คำสั่งติดตั้ง), `prepare_database()` สร้างโฟลเดอร์/ตาราง + seed เมื่อ `repo_users.list_users()` ว่าง (ไม่ seed ซ้ำ ไม่ทับข้อมูลจริง), เตือนรหัสผ่านตั้งต้นของ owner/admin1/buyer1 บน console, แล้ว `App().mainloop()`
- **สำรองอัตโนมัติ:** ตอนปิดแอป (`App._on_close`, หลัง `clear_all_online`) → `shop_auto_<วันที่>_<เวลา>.db` ใน `data/backups/` · ข้ามถ้า `shop.db`/`-wal` ไม่ใหม่กว่าไฟล์สำรองล่าสุด · ใช้โควตา `BACKUP_KEEP_COUNT` (10) ร่วมกับไฟล์สำรองมือ — ไฟล์เก่าสุดถูกลบเมื่อเกิน
- **ทดสอบแล้ว (เครื่องตรวจ Linux + Xvfb + Python 3.12 + customtkinter/bcrypt/pillow/qrcode/reportlab ตัวจริง):** (1) unittest 137 ข้อผ่าน (promptpay, repos 26, services_basic, order_flow) (2) เปิดทุกหน้า 30 route ด้วย buyer1/admin1/owner + ตรวจ redirect (admin เข้าหน้า owner-only → admin_dashboard, staff เข้าหน้าซื้อของ → admin_dashboard) = 0 error (3) กดทุกปุ่มทุกหน้า 358 ครั้ง (dialog/ไฟล์ถูกจำลอง) = 0 error (4) ไล่ครบวงจรผ่านปุ่มจริง: ตะกร้า→checkout→ตัดสต็อก→แนบสลิป→admin ยืนยัน→บันทึกจัดส่ง+เลขพัสดุ→ผู้ซื้อรับของ→ปุ่มรีวิว→ใบเสร็จ PDF; ปฏิเสธสลิป→แนบใหม่; ผู้ซื้อยกเลิก pending→คืนสต็อก; คูปอง WELCOME10 หักส่วนลด; admin ไม่เห็นรายได้/owner เห็น (5) รัน `main.py` บนโฟลเดอร์ไม่มี `shop.db`: สร้าง+seed ครั้งแรก, ปิดแอปแล้วสำรองอัตโนมัติ, รันซ้ำไม่ seed ซ้ำและไม่สำรองซ้ำ (6) `python main.py --check` ผ่าน
- **ยังไม่ได้ทดสอบ / ให้ผู้ใช้ลองบน Windows:** หน้าตา/ขนาดฟอนต์จริง (เครื่องตรวจฟอนต์ไทยต่างจาก Windows), การติดตั้งฟอนต์ Arimo, สแกน PromptPay QR ด้วยแอปธนาคารจริง (ใส่เลขพร้อมเพย์จริงก่อน), Gemini จริง (ไม่มีคีย์/เน็ต), กล่องเลือกไฟล์ของ Windows, ปุ่มเปิดไฟล์ PDF/รูปสลิปด้วยโปรแกรมของระบบ
- **ข้อจำกัดที่ยังไม่ทำ (ตั้งใจเก็บไว้):** ช่องแจ้งความตึงเอ็น (lbs) ต่อสินค้าในตะกร้า — ต้องเพิ่มคอลัมน์ใน `cart_items`/`order_items` (ตอนนี้ขึ้นเอ็นทำได้ผ่านตัวเลือกประเภท "เอ็น" แต่ยังไม่มีช่องกรอกความตึง) · เลขพร้อมเพย์ใน seed เป็นค่าตัวอย่าง `0812345678`
- **สิ่งที่ผู้ใช้ต้องทำก่อนนำเสนอ:** (1) เปลี่ยนรหัสผ่าน owner/admin1/buyer1 (FIX-16) (2) ใส่เลขพร้อมเพย์จริงที่ ตั้งค่าร้าน (3) ใส่ `GEMINI_API_KEY` ใน `.env` ถ้าอยากโชว์แชท AI (4) รัน `python main.py --check` ให้ไม่มี ✘ (5) แคปหน้าจอ/นำตารางความคืบหน้าด้านบนไปใส่สไลด์


---

## อัปเดต v2 (2026-10-15) — อัปเกรดตามเอกสาร UX/UI และฟีเจอร์เพิ่มเติมครบสมบูรณ์ (CustomTkinter 100%)
- **ฐานข้อมูล (`database/db.py`)**: อัปเกรดแบบ idempotent (`_migrate_v2`) เพิ่มตารางใหม่รวม 31 ตาราง (`email_otps`, `pending_registrations`, `sessions`, `category_brands`, `coupon_rules`, `coupon_claims`, `expenses`, `staff_messages`, `email_outbox`, `banners`, `audit_log` + คอลัมน์ soft delete และ `cost_price`)
- **Repositories & Services**: เพิ่ม `repo_otp`, `repo_sessions`, `repo_expenses`, `repo_outbox`, `repo_banners`, `repo_audit` และ `email_service`, `otp_service`, `ai_guard`, `expense_service`, `export_service`, `staff_service`, `contact_service`, `banner_service`, `audit_service`, `email_outbox_service`
- **UI/UX (`ui/`)**: อัปเกรดธีมสีเหลือง (`#FFB703`) · แดง (`#E63946`) · ขาว/ดำ (`#FFFFFF`/`#141619`) และสีเสริม คอนทราสต์สูง ตัวอักษรไม่ซ้อนทับกัน รองรับโหมดผู้เยี่ยมชม (Guest), สมัครด้วย OTP + ที่อยู่เริ่มต้น, ลืมรหัสผ่าน OTP, เปรียบเทียบไม้ 2–5 รุ่น, ออเดอร์ 8 แท็บสถานะ, แชท AI Guard + Quick Replies + แนะนำไม้ 3 รุ่น, กฎคูปอง, Soft Delete/กู้คืนสินค้า-หมวด-แบรนด์, แต่งตั้งแอดมินด้วยอีเมล, ส่งออก `.xlsx` ย้อนหลังสูงสุด 1 ปี + รายเดือนอัตโนมัติ, และปุ่มติดต่อเจ้าของร้าน/ส่งอีเมลด่วน
- **ผลการทดสอบ**: `unittest` ผ่านครบ 146 ข้อ และทดสอบเปิดหน้าจอ GUI ครบ 30 routes ผ่าน 100%

---

## อัปเดต v3 (2026-10-16) — แก้ไขและเพิ่มฟีเจอร์ตามคำสั่ง T01–T15 ครบสมบูรณ์ (CustomTkinter + SQLite 100%)

- **T01 (ฟอนต์อังกฤษ Arimo + ไทย Kanit จากจุดเดียว)**:
  - เพิ่มไฟล์ฟอนต์ `Kanit-*.ttf` ครบชุดใน `assets/fonts/` คู่กับ `Arimo-*.ttf`
  - อัปเดต `utils/font_installer.py` (`ARIMO_WEIGHTS`, `KANIT_WEIGHTS`, `get_project_font_status()`) และ `ui/theme.py` (`FONT_FAMILY_LATIN = "Arimo"`, `FONT_FAMILY_THAI = "Kanit"`, `get_font()`, `get_latin_font()`, `get_thai_font()`)
  - อัปเดต `services/receipt_service.py` ให้ดึง `Kanit-Regular.ttf`/`Kanit-Bold.ttf` จาก `assets/fonts/` สำหรับใบเสร็จ PDF ภาษาไทยโดยตรง
- **T02 (Owner จัดการชุดตัวเลือกและค่าตัวเลือกประจำหมวดหมู่แบบไม่ต้องแก้โค้ด)**:
  - เพิ่มตาราง `option_groups` และ `option_values` ใน `database/db.py` (`_migrate_v3`) พร้อม seed ค่าเริ่มต้นของหมวดไม้แบดมินตัน (`3U–10U`, จุดสมดุล, ความอ่อนแข็งก้าน, ระดับผู้เล่น), ลูกแบดมินตัน (ความเร็วลูก `74–78`), รองเท้า/เสื้อผ้า (ไซซ์), กริป/เอ็น/กระเป๋า (สี)
  - เพิ่มฟังก์ชันใน `database/repo_products.py` และ `services/product_service.py` (`list_category_option_groups`, `save_category_option_group`, `toggle_category_option_group`, `save_category_option_value`, `toggle_category_option_value`, `reorder_category_option_values`, `quick_add_racket_weights`, `get_allowed_racket_spec_options`) โดยจำกัดสิทธิ์เฉพาะ Owner (`permissions.CATEGORY_MANAGE`)
  - เพิ่มแท็บ `ตัวเลือกประจำหมวดหมู่` (`_CategoryOptionsPanel`) ใน `ui/pages/admin/categories.py` และเชื่อมต่อกับ `ui/pages/admin/product_form.py`
- **T03 (ตาราง Technical Specifications 7 หัวข้อภาษาอังกฤษสำหรับไม้แบดมินตัน)**:
  - เพิ่มคอลัมน์ `spec_material`, `spec_weight_grip`, `spec_balance_mm`, `spec_balance_type`, `spec_max_tension`, `spec_length` ในตาราง `products`
  - เพิ่มฟังก์ชันตรวจสอบค่าตัวเลข Balance Point (mm) ใน `utils/validators.py` (`is_valid_balance_point_mm`, `normalize_balance_point_mm`, `format_balance_point_display`) และ `build_technical_specs(product)` ใน `services/product_service.py` (ซ่อนแถวที่ว่างโดยไม่แสดง `...`)
  - แสดงตาราง Technical Specifications โทนสีเข้มอ่านชัดใน `ui/pages/buyer/product_detail.py` และ `ui/pages/buyer/compare.py` พร้อมช่องกรอกใน `ui/pages/admin/product_form.py`
- **T04 (อัปโหลดรูปสินค้าหลายรูป + ผูกรูปกับตัวเลือกสี/สไตล์)**:
  - เพิ่มตาราง `product_images` และคอลัมน์ `product_options.image_path` ใน `database/db.py`
  - เพิ่มฟังก์ชันจัดการแกลเลอรีรูปภาพใน `database/repo_products.py` และ `services/product_service.py` (`add_product_image`, `update_product_image`, `delete_product_image`, `set_primary_product_image`, `reorder_product_images`)
  - อัปเดต `ui/pages/admin/product_form.py` ให้เพิ่ม/ลบ/ตั้งรูปหลัก/ผูกรูปกับสี และอัปเดต `ui/pages/buyer/product_detail.py` ให้แสดงแกลเลอรีหลายรูปพร้อมเปลี่ยนรูปหลักอัตโนมัติเมื่อผู้ซื้อคลิกเลือกสี/สไตล์
- **T05 (แถบ Flash Sale หน้าแรกเลื่อนอัตโนมัติจากขวาไปซ้าย)**:
  - อัปเดต `ui/pages/buyer/home.py` ให้แสดงสินค้าลดราคาทุกชิ้นในแถบแนวนอน เลื่อนอัตโนมัติจากขวาไปซ้ายอย่างนุ่มนวล หยุดชั่วคราวเมื่อเมาส์ชี้ (hover) และเลื่อนต่อเมื่อเอาเมาส์ออก (หากจำนวนสินค้าไม่เต็มความกว้างจะแสดงนิ่งไม่เลื่อน)
- **T06 (แถบคูปองหน้าแรกแสดงทีละ 3 ใบสลับช้าๆ + หน้าต่างคูปองแยกหมวดหมู่)**:
  - เพิ่มคอลัมน์ `coupons.coupon_category` และฟังก์ชัน `get_coupon_categories()`, `list_all_shop_coupons()`, และการกรองหมวดหมู่ใน `list_my_coupons()` / `list_public_coupons()`
  - อัปเดตแถบคูปองใน `ui/pages/buyer/home.py` ให้แสดงทีละ 3 ใบ สลับชุดช้าๆ พร้อมปุ่ม `"คูปองของฉัน (ที่เก็บไว้)"` และ `"ดูคูปองทั้งหมดของร้าน"` ที่เปิดหน้าต่างแยกแท็บหมวดหมู่ (`ทั้งหมด`, `คูปองส่วนลดค่าส่ง`, `คูปองส่วนลดเป็น %`, `คูปองส่วนลดเป็น บาท`, `และอื่นๆ`)
- **T07 (การ์ดสินค้าสัดส่วน 3:4 + รูปสินค้าสัดส่วน 1:1 จัตุรัสส่วนบน)**:
  - อัปเดต `ui/components/product_card.py` (`CARD_WIDTH = 216`, `CARD_HEIGHT = 288` สัดส่วน 3:4, รูปด้านบนขนาด `196x196` สัดส่วน 1:1) และ `utils/image_utils.py` (`load_product_card_image`) โดยคงป้ายส่วนลดมุมซ้ายบน ปุ่มหัวใจมุมขวาบน และรายละเอียดด้านล่างครบถ้วน
- **T08 (ตัวเลือกวันที่แบบปฏิทิน CustomTkinter แทนการพิมพ์เอง)**:
  - สร้าง `ui/components/date_picker.py` (`DatePickerField`, `DateTimePickerField`) ด้วย CustomTkinter + `calendar` มาตรฐาน รองรับปี พ.ศ./ค.ศ. และคืนค่า ISO `YYYY-MM-DD` / `YYYY-MM-DD HH:MM:SS` เข้ากับโค้ดเดิม 100%
  - นำไปใช้ใน `ui/pages/admin/settings.py` (ช่วงวันที่รายงาน Excel และวันที่รายจ่าย), `ui/pages/admin/product_form.py` (วันสิ้นสุด Flash Sale), และ `ui/pages/admin/coupon_form.py` (วันเริ่ม/วันหมดอายุคูปอง)
- **T09 & T10 (ปรับโฉมหน้าเข้าสู่ระบบ / สมัครสมาชิก `ui/components/auth_layout.py`)**:
  - ฝั่งซ้าย (T09): พื้นหลังสีเหลือง (`#FFB703`) นำชื่อร้าน/สโลแกนด้านบนและปุ่มผู้เยี่ยมชมมุมล่างซ้ายออก แสดงการ์ดสีขาวมุมมน (`#FFFFFF`) พร้อมรูปสินค้ามุมมนและตัวหนังสือสีเหลือง+แดง สุ่มสินค้าจริงจากร้านสไลด์เปลี่ยนอัตโนมัติ (ไม่มีปุ่ม `<` `>`)
  - ฝั่งขวา (T10): นำกรอบสี่เหลี่ยมรอบคำว่า `Welcome` ออก ขยายตัวอักษรใหญ่ขึ้น (`36pt`) พร้อมเงาสีดำเบลอเฉียงลงด้านล่างเล็กน้อย (`make_welcome_shadow_ctk_image`) และคงแอนิเมชันคำสลับ (`WELCOME_WORDS`) เดิมไว้ครบถ้วน
- **T11 (หน้าโปรไฟล์: การ์ดสถิติมีสีสันคลิกได้ + ปุ่มแก้ไขข้อมูลของฉัน + เปลี่ยนอีเมลด้วย OTP)**:
  - อัปเดต `ui/pages/buyer/profile.py` ให้การ์ด `คำสั่งซื้อ` (สีเหลือง), `ที่อยู่จัดส่ง` (สีฟ้า), `รายการโปรด` (สีแดง/ชมพู) มีสีพื้นและขอบชัดเจนพร้อมเอฟเฟกต์ hover และคลิกเปลี่ยนหน้าได้จริง
  - เพิ่มปุ่ม `"แก้ไขข้อมูลของฉัน"` ให้แก้ไข `username`, `full_name`, `phone` ได้โดยตรง และเปลี่ยน `email` ผ่านการส่งรหัส OTP 6 หลักไปยังอีเมลใหม่ (`request_email_change_otp`, `confirm_email_change_with_otp` + ตาราง `email_change_otps`)
- **T12 (หน้ารายละเอียดสินค้าสีสันสดใสและกรอบพอดีข้อความ)**:
  - อัปเดต `ui/pages/buyer/product_detail.py` ให้ใช้โทนสีสดใสตัดกันชัดเจน (ป้ายหมวดหมู่/แบรนด์/ราคา/ชิปตัวเลือก/ปุ่มแอ็กชัน) และปรับกรอบข้อความให้กระชับพอดีกับเนื้อหา ไม่ยืดยาวเกินจำเป็น
- **T13 (หน้าจัดการผู้ใช้: ระยะห่างปุ่มดูข้อมูลไม่ชิดขอบขวา + สีสถานะผู้ใช้ 3 สถานะ)**:
  - อัปเดต `ui/pages/admin/users.py` เพิ่มระยะห่างขอบขวา (`padx=(8, 18)`) ให้ปุ่ม `"ดูข้อมูล"` และปุ่มจัดการไม่ชิดขอบตาราง และแยกสีป้ายสถานะชัดเจน: `ออฟไลน์` = สีเทา (`offline`), `ออนไลน์` = สีเขียว (`online`), `ถูกระงับ` = สีแดง (`suspended`)
- **T14 (ลดช่องว่าง 200px ระหว่างหัวเรื่องกับเนื้อหาในหน้าตั้งค่าร้าน/จัดการผู้ใช้)**:
  - แก้ `page_header()` ใน `ui/pages/admin/common.py` ให้กำหนด `width=1, height=1` บนเฟรม `actions` เพื่อไม่ให้ `CTkFrame` จองความสูงเริ่มต้น 200px เมื่อไม่มีปุ่มด้านขวา
- **T15 (การตั้งค่าระบบเพิ่มเติมสำหรับ Owner)**:
  - เพิ่มคีย์ตั้งค่าใน `config.py`, `services/settings_service.py`, และ `ui/pages/admin/settings.py` ให้ Owner ปรับความเร็วแถบ Flash Sale, เวลาสลับคูปองหน้าแรก, จำนวนคูปองที่แสดงต่อรอบ, เวลาสลับสินค้าหน้าล็อกอิน, หมวดหมู่คูปองเพิ่มเติม, และประเภทตัวเลือกสินค้าเพิ่มเติมได้โดยไม่ต้องแก้โค้ด
- **ผลการทดสอบ**: `unittest` ผ่านครบ **155 ข้อ (OK)** และทดสอบเปิดหน้าจอครบ 30 routes + `python main.py --check` ผ่าน 100%
