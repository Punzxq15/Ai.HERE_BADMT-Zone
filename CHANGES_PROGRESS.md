# CHANGES_PROGRESS.md — แผนแก้ไข ปรับปรุง และเพิ่มเติม (Badminton Pro Shop · ฉบับ v5 อ่านครบในไฟล์เดียว)

> ไฟล์นี้คู่กับ `PROGRESS.md` เดิม (มีอยู่ในซิป — บันทึกของที่ทำเสร็จแล้ว) ไฟล์นี้บันทึก **สิ่งที่จะแก้/เพิ่ม และลำดับการทำ** อ้างอิงจากเอกสาร "UXUI และเพิ่มเติม.pdf" (ส่วนระบบรวม / Owner / Admin / Buyer / ตัวอย่างหน้าแอป) และโค้ดจริงในโปรเจกต์
> ต้นแบบหน้าจอ: **ฝังอยู่ในไฟล์นี้แล้ว (ภาคผนวก A–F ท้ายไฟล์)** — ซิปที่ส่งมาไม่มีโฟลเดอร์ `prototype/` และไม่มี `UI_PROGRESS.md` จึงย้ายสิ่งที่ต้องใช้ (โทเค็นสี/CSS, โครงหน้า, แผนที่ route, โค้ด contextvars, แม่แบบอีเมล, แผนผังขั้นตอนการทำงาน) มาไว้ในไฟล์นี้ ไม่ต้องหาไฟล์อื่นประกอบ
> **ฉบับอัปเดต (v2):** ยืนยัน D3 (OTP ตอนสมัครครั้งเดียวต่ออีเมล) และ D4 (ลำดับสถานะตามที่เจ้าของโปรเจกต์กำหนด) แล้ว + เพิ่ม SYS-3 (ส่งใบเสร็จอิเล็กทรอนิกส์ไปอีเมลผู้ซื้อหลังตรวจสลิปผ่าน)
> **ฉบับ v6 (ล่าสุด):** เจ้าของโปรเจกต์ **อนุมัติข้อเสนอเพิ่มเติม E1–E9 ทั้งหมด** (E9 อนุมัติใน v4) → ย้ายเข้าแผนหลักแล้ว: E1 ที่อยู่/เวลาเปิดปิด/แผนที่ร้าน · E2 จัดการแบนเนอร์ · E3 LINE Official/TikTok · E4 บันทึกกิจกรรม (audit log) · E5 อีเมลแจ้งจัดส่ง+เลขพัสดุ · E6 อีเมลสรุปสต็อกต่ำถึงเจ้าของ · E7 ส่งออกไป Google Sheets · E8 ค้นหาแนะนำ+สินค้าที่ดูล่าสุด — ดูหัวข้อ 2.6, 5.2–5.4, Phase 2 (2D, 2I–2N), Phase 5–6, 8–12 (12.14–12.18)
>
> **ฉบับ v5:** (1) ทุกเฟส 0–9 มีกล่อง **📦 ไฟล์ที่ต้องแนบ** (แก้ / อ้างอิง) + วิธีแพ็กซิปในภาคผนวก G — แนบแค่ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนั้น (2) **D14 ยืนยันแล้ว:** Admin ลืมรหัส → หน้าแสดงช่องทางติดต่อ Owner → Owner รันสคริปต์ `tools/reset_password.py` บนเครื่องร้าน (ไม่มี OTP สำหรับพนักงาน)
>
> **ฉบับ v4:** (1) **อนุมัติ E9 แล้ว** — ลืมรหัสผ่านด้วย OTP ทางอีเมล (OTP มี 2 กรณีเท่านั้น: สมัครอีเมลใหม่ และลืมรหัสผ่าน; ล็อกอินปกติไม่มี OTP) (2) **สลิปออนไลน์** = ข้อความในอีเมล (และแนบ PDF ถ้าสร้างได้) ส่งจากอีเมลของร้านในชื่อร้านไปที่อีเมลผู้ซื้อ (3) **หน้าล็อกอิน/สมัครแบบใหม่** ตาม PDF ฉบับล่าสุด: แบ่งสองฝั่ง ซ้ายเหลืองแสดงภาพสินค้าตัวอย่างเปลี่ยนไปเรื่อยๆ ขวาเป็นฟอร์ม; สมัครเสร็จแล้วกลับมาหน้าล็อกอิน (ไม่ล็อกอินให้อัตโนมัติ) (4) **ระบบติ๊กความคืบหน้า [ ] → [X]** (ดูหัวข้อ 0 ข้อ 11–12)
>
> **ฉบับ v3:** (1) ตรวจเทียบกับโค้ดจริงในซิปแล้ว (หัวข้อ 1.1) (2) เพิ่ม **หัวข้อ 12 แผนผังขั้นตอนการทำงานทุกระบบ** ตามลำดับที่ต้องการ (3) ทำให้เอกสารอ่านครบในไฟล์เดียว (ภาคผนวก A–F) (4) ใส่ข้อสังเกต/ข้อควรแก้ที่พบจากโค้ดจริง (หัวข้อ 1.1) — ไม่เปลี่ยนการตัดสินใจที่ยืนยันแล้ว (D3, D4, D12)

สถานะ: ⬜ ยังไม่เริ่ม · 🟨 กำลังทำ · ✅ เสร็จ · ❓ รอคุณยืนยัน

---

## 0. กติกาสำหรับ AI ที่มาทำงานต่อ (อ่านก่อนเสมอ)

1. **ทำทีละเฟสตามลำดับ** (Phase 0 → 9) ห้ามข้ามเฟสที่เป็นฐานของเฟสถัดไป จบแต่ละเฟสให้ติ๊ก ✅ และอัปเดตหัวข้อ "บันทึกความคืบหน้า" ท้ายไฟล์
2. **สถาปัตยกรรมต้องไม่พัง:** `UI → services → database/repo_* → db.py` ทิศทางเดียว UI ห้ามเขียน SQL, services ห้าม import UI/Flask
3. **สิทธิ์บังคับที่ services เสมอ** (`permissions.require(...)`) ฝั่ง UI/route แค่ซ่อนปุ่มและเตือน ไม่ใช่ที่กั้นจริง
4. **ข้อความที่ผู้ใช้เห็นเป็นภาษาไทย** services โยน `ValueError` (ข้อความไทย) และ `PermissionError` ตามเดิม
5. **เปลี่ยนฐานข้อมูลแบบไม่ทำลายข้อมูลเดิม** ใช้ `_ensure_column()` / `CREATE TABLE IF NOT EXISTS` ใน `database/db.py` (`init_db()` เรียกซ้ำได้) ห้าม DROP ตารางเดิม
6. **ทุกฟีเจอร์ใหม่ใน services ต้องมี unittest** ใน `tests/` (ใช้ DB ชั่วคราวเหมือนเทสต์เดิม) และรัน `python -m unittest tests.test_promptpay tests.test_repos tests.test_services_basic tests.test_order_flow` ให้ผ่านก่อนจบเฟส
7. **ข้อใดมีเครื่องหมาย ❓** ในหัวข้อ 3 ให้ใช้ค่า "ค่าเริ่มต้นที่แนะนำ" ไปก่อน และบันทึกไว้ว่าใช้ค่าไหน ห้ามเดาเงียบๆ
8. **อะไรที่ไม่ได้ระบุในไฟล์นี้ ห้ามเพิ่มเอง** ถ้าคิดว่าจำเป็น ให้เขียนไว้ใน "ข้อเสนอเพิ่มเติม" (หัวข้อ 11) แล้วรอเจ้าของโปรเจกต์อนุมัติ (ตามที่ PDF สั่งว่า "เพิ่มส่วนที่จำเป็นได้แต่ให้บอกก่อน") — **E1–E9 อนุมัติแล้ว (v6) ถือเป็นส่วนของแผนหลัก**; ข้อเสนอใหม่ให้ใช้เลข E10 เป็นต้นไป
9. **ห้ามเก็บความลับในโค้ด** (SMTP รหัสผ่าน, GEMINI_API_KEY) ใช้ `.env` เท่านั้น และห้าม commit `.env`
10. ก่อนเริ่มทุกเฟส: สำรอง `data/shop.db` (`utils/backup.py`) และ commit git
11. **ระบบติ๊กความคืบหน้า:** ทุกขั้นตอนในไฟล์นี้ที่เป็นงานต้องมีกล่อง — ยังไม่ทำ = `[ ]`, ทำเสร็จและเทสต์ผ่านแล้ว = `[X]` (X ตัวใหญ่) เจ้าของโปรเจกต์จะสั่งว่า "ทำข้อนี้เสร็จแล้ว" หรือ AI ทำเสร็จเอง → AI ต้องเปลี่ยน `[ ]` เป็น `[X]` เฉพาะข้อนั้น **ห้ามติ๊กล่วงหน้า** และห้ามติ๊กข้อที่ยังไม่ได้ทำ/ทดสอบ
12. **ขอบเขตไฟล์ต่อเฟส (ประหยัดบริบท):** แต่ละเฟสในหัวข้อ 7 มีกล่อง "📦 ไฟล์ที่ต้องแนบ" ระบุไฟล์ที่ต้อง **แก้** กับไฟล์ที่ **อ้างอิง** (ไม่แก้) พร้อมคำสั่ง zip — เจ้าของโปรเจกต์แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + zip ของเฟสนั้นเท่านั้น; AI **ห้ามแก้ไฟล์นอกรายการ "แก้"** ถ้าจำเป็นต้องแก้ไฟล์อื่น ให้หยุดและแจ้งว่าต้องการไฟล์ใด; ไฟล์ที่ "สร้างใหม่" ไม่ต้องมีใน zip; ให้ใช้ไฟล์เวอร์ชันล่าสุดที่ได้จากเฟสก่อนหน้าเสมอ (ไม่ใช่ของเดิมในซิปแรก)
13. **สถานะเฟส:** ⬜ = ยังไม่เริ่ม · 🟨 = มีข้อที่ติ๊ก `[X]` แล้วบางข้อ · ✅ = ทุกข้อในเฟส (รวมบรรทัด "เสร็จเมื่อ") เป็น `[X]` ครบ; ทุกครั้งที่ติ๊กให้เพิ่มแถวในหัวข้อ 13 (วันที่ / ข้อที่ติ๊ก / ไฟล์ที่แตะ / ผลเทสต์)

---

## 1. สถานะปัจจุบัน (จากโค้ดจริง)

- แอป Desktop เขียนด้วย Python + CustomTkinter, ฐานข้อมูล SQLite (`data/shop.db`, WAL), รัน `python main.py`
- โครง: `ui/` → `services/` → `database/repo_*` → `db.py` · `core/` (constants, permissions, session) · `utils/` · `tests/`
- บทบาท: `owner`, `admin`, `buyer` (CHECK ในตาราง users)
- สถานะออเดอร์ใน DB: `pending → checking_slip → paid → shipped → completed` หรือ `cancelled`
- ตัวเลือกสินค้ามี `flex`, `balance`, `level`, `weight_class` (ใช้กับตัวช่วยเลือกไม้/AI ได้เลย)
- ล็อกอินปัจจุบันใช้ username หรืออีเมล + รหัสผ่าน (bcrypt) ยังไม่มี OTP/ยืนยันอีเมล
- การเปรียบเทียบไม้จำกัด 2–3 ไม้ (`product_service.compare_products`, `ui/pages/buyer/compare.py`)
- ลบสินค้า = `set_product_active` (ซ่อน/ปิดขาย) ยังไม่มี "ถังสินค้าที่ถูกลบ"; หมวด/แบรนด์ก็มีแค่ `is_active`
- ยังไม่มีตารางค่าใช้จ่าย/ต้นทุนสินค้า, ยังไม่มีการส่งอีเมล, ยังไม่มีหน้าเว็บ
- `core/session.py` เป็น global (ใช้ได้กับ Desktop คนเดียว แต่เว็บต้องแก้ ดู Phase 4)
- มีกลไกสำรอง DB (`utils/backup.py`) แต่ยังไม่มีส่งออก Excel
- มีใบเสร็จ PDF (`receipt_service.generate_receipt(order_id)`) และ `payment_service.verify_payment` อยู่แล้ว ใช้เป็นฐานของ SYS-3

### 1.1 ผลตรวจเทียบกับโค้ดจริง (v3) — สิ่งที่ยืนยันแล้ว และสิ่งที่ต้องแก้

ยืนยันตรงกับโค้ด: `compare_products` จำกัด 2–3 (`services/product_service.py`) · `recommend_rackets(level, style, budget=None, limit=6)` ยังไม่มีพารามิเตอร์ flex/balance · `chat_service.send_message(customer_id, text, background=True)` ยังไม่มี `force_ai` · `should_ai_reply()` = เปิด `ai_enabled` และไม่มี staff ออนไลน์ · `payment_service.verify_payment(payment_id)` ทำทุกอย่างใน transaction เดียวแล้วคืนรายละเอียดออเดอร์ (จุดเสียบอีเมลใบเสร็จคือ **หลังออกจาก `with transaction()`** ซึ่งต้องทำที่ผู้เรียก/ห่อฟังก์ชัน ไม่ใช่ใน transaction) · `receipt_service.generate_receipt(order_id)` คืน path ไฟล์ PDF · `core/session.py` เป็น global จริง · ตาราง `users` มี `username` และ `email` เป็น `UNIQUE NOT NULL` อยู่แล้ว (ไม่ต้องเพิ่มคอลัมน์ email) · `config.py` มี `BANNER_IMAGES_DIR` = `assets/images/banners` อยู่แล้ว

ข้อควรแก้ที่พบ (ใส่ใน Phase ที่ระบุ):

| # | พบอะไร | ต้องทำ | เฟส |
|---|---|---|---|
| F1 | `config.ALLOWED_IMAGE_EXTENSIONS = (.jpg, .jpeg, .png)` ไม่รวม `.webp` แต่หัวข้อ 6 แนะนำแบนเนอร์ `.webp` | เพิ่ม `.webp` (Pillow รองรับ) หรือกำหนดว่าแบนเนอร์ใช้ `.jpg/.png` เท่านั้น — ใช้ค่านี้: **เพิ่ม `.webp`** | 0 |
| F2 | ซิปมี `.env` อยู่ในโฟลเดอร์ (แม้ `.gitignore` กันไว้แล้ว) | ตรวจว่าไม่มี `GEMINI_API_KEY`/รหัสจริงหลุดไปกับซิปที่แชร์; ถ้ามี **ให้หมุนคีย์ใหม่** แล้วสร้าง `.env.example` ไม่มีค่าจริง | 0 |
| F3 | `ORDER_STATUS_LABELS` เป็น dict ไม่มีลำดับแสดงผลและไม่มี "รอรีวิว"/"การสั่งซื้อ (ทั้งหมด)" | เพิ่ม `ORDER_STATUS_DISPLAY_ORDER` ตามหัวข้อ 3.1 (ค่าเสมือน `all` และ `to_review` ไม่ใช่สถานะใน DB) | 2 |
| F4 | `verify_payment` อยู่ใน transaction; อีเมลห้ามอยู่ข้างใน | เรียก `queue_receipt_email` หลัง commit (ดูภาคผนวก D.3) | 2H |
| F5 | `core/constants.py` ไม่มี `MAX_COMPARE` และข้อความ error ฝังเลข 2-3 | ตามหัวข้อ 2G | 2 |

---

## 2. ทะเบียนข้อกำหนด (Requirements) — ไล่ตาม PDF

รหัส: SYS = ระบบรวม · OWN = Owner · ADM = Admin · BUY = Buyer · UX = หน้าตา/ประสบการณ์ใช้งาน
คอลัมน์ "เฟส" ชี้ไปหัวข้อ 7

### 2.1 ระบบรวม

| รหัส | ข้อกำหนด (ตาม PDF) | ความหมายที่ใช้ทำงาน | เฟส |
|---|---|---|---|
| SYS-1 | ล็อกอินต้องใช้อีเมลจริง และส่ง OTP ยืนยัน | ล็อกอินด้วยอีเมล+รหัสผ่าน (ไม่ใช้ username แล้ว); **OTP 6 หลักส่งตอนสมัครเท่านั้น ครั้งเดียวต่อ 1 อีเมล** (D3 ยืนยันแล้ว) ยืนยันแล้วคราวต่อไปเข้าด้วยอีเมล+รหัสผ่านได้เลย ไม่มี OTP ตอนล็อกอิน; **OTP ใช้อีก 1 กรณีคือ "ลืมรหัสผ่าน" (E9 อนุมัติแล้ว, หัวข้อ 12.13)** | 1, 4 |
| SYS-2a | AI แชท: กันคำถามแปลก (เช่น วันนี้วันอะไร, อากาศ) ก่อนส่งให้ AI คำนวณ → ไม่ตอบ และตอบกลับว่าอยู่นอกขอบเขตของร้าน | ชั้นกรอง (guard) ก่อนเรียก Gemini + ข้อความปฏิเสธคงที่ | 3 |
| SYS-2b | ปุ่มคำถามสำเร็จรูป เช่น "แนะนำไม้ที่ขายดีที่สุดในร้าน" | Quick replies; ตอบจากข้อมูลจริงใน DB (ไม่ต้องให้ AI เดา) | 3 |
| SYS-2c | ปุ่มพิเศษ "ถาม AI โดยเฉพาะ" ใช้ได้แม้แอดมินออนไลน์อยู่ | พารามิเตอร์ `force_ai=True` ข้ามเงื่อนไข `should_ai_reply()` | 3 |
| SYS-2d | ปุ่มให้กรอกสไตล์การเล่น (ชอบแบบไหน ก้านแข็ง/อ่อน ฯลฯ) แล้ว AI แนะนำไม้ในร้าน ~3 ไม้ที่เหมาะกับฝีมือที่สุด | ฟอร์มตัวช่วย → `recommend_rackets` (ขยายด้วย flex/balance) → AI อธิบายเฉพาะไม้ที่ระบบเลือก | 3 |
| SYS-3 | ผู้ซื้อสมัครด้วยอีเมลจริง → ส่ง **"สลิปออนไลน์"** ไปอีเมลผู้ซื้อ **หลังตรวจสลิปผ่าน** เป็นข้อความหรือ .pdf ก็ได้ ส่งจากทางร้านในนามอีเมลของร้าน | **ยืนยันแล้ว (v4):** สลิปออนไลน์ = ใบเสร็จ/ยืนยันการชำระเงินที่ระบบสร้าง — **เนื้อหาอยู่ในตัวอีเมลเป็นข้อความ/HTML** (อ่านได้ทันทีแม้เปิด PDF ไม่ได้) และ **แนบ PDF** เพิ่มถ้าสร้างได้; ผู้ส่ง = บัญชีอีเมลของร้าน ชื่อผู้ส่ง = ชื่อร้าน; ผู้รับ = อีเมลผู้ซื้อเจ้าของออเดอร์ (ไม่ใช่รูปสลิปโอนที่ผู้ซื้อแนบ); ส่งหลัง `verify_payment` สำเร็จ + คิวส่งซ้ำ + ปุ่มส่งใหม่ (D12) | 2H, 5, 6 |

### 2.2 Owner

| รหัส | ข้อกำหนด | ความหมายที่ใช้ทำงาน | เฟส |
|---|---|---|---|
| OWN-1 | แก้เงื่อนไขการได้รับคูปองได้ เช่น ซื้อเกิน 3,000 ได้คูปองลด 300 เมื่อซื้อขั้นต่ำ 1,000 ใช้ครั้งถัดไป | กฎ "ซื้อครบรับคูปอง" (reward rule) ที่เจ้าของแก้ตัวเลขได้; ออกคูปองส่วนตัวให้ผู้ซื้อ + แก้เงื่อนไขคูปองปกติได้ครบ | 2, 6 |
| OWN-2 | ลบสินค้าได้ แต่มีช่อง/แท็บ "สินค้าที่ถูกลบ" เก็บไว้ดูว่าเคยขายอะไร | Soft delete (`deleted_at`) + แท็บถังสินค้าที่ถูกลบ พร้อมประวัติยอดขาย + กู้คืนได้ | 2, 6 |
| OWN-3 | หมวดหมู่และแบรนด์ลบได้เหมือนกัน; ตอนเพิ่มหมวดเลือกได้ว่าใช้กับทุกแบรนด์หรือเฉพาะบางแบรนด์ | Soft delete + ตารางผูกหมวด↔แบรนด์ | 2, 6 |
| OWN-4 | อีเมลเจ้าของร้านเขียนตายตัวในระบบ; เจ้าของเพิ่ม Admin โดยดึงอีเมลมาตั้งเป็น Admin แล้วตั้งรหัสผ่านและยืนยัน; Admin ใช้อีเมล+รหัสนั้นเข้าเครื่อง; Admin ค้างล็อกอินที่คอมร้านไว้ ไม่ต้องล็อกอินซ้ำ เพื่อไม่ให้รหัสผ่านรั่วไปยังพนักงาน | `OWNER_EMAIL` ใน `.env`; หน้า "จัดการผู้ดูแล"; เซสชันถาวรเก็บใน DB (ล็อกอินค้าง 90 วัน) + เจ้าของสั่งเตะออกได้ | 1, 4, 6 |
| OWN-5 | สำรองข้อมูลเป็น .xlsx กดเมื่อไรก็ได้; อัตโนมัติทุกเดือนลงเครื่อง; มีรายรับรายจ่ายทั้งหมด ลูกค้า ซื้ออะไร ราคาเท่าไหร่ ในเดือนนั้น; เลือกช่วงเวลาได้ (ย้อนหลังสุด 1 ปี หรือ 1 ม.ค.–31 ธ.ค.) | `export_service` (openpyxl) + งานตั้งเวลารายเดือน + ตัวเลือกช่วงเวลา; **รายจ่ายต้องมีที่เก็บข้อมูล** (ดู D5) | 2, 6 |
| OWN-6 | หน้าแก้ข้อมูลตัวเอง: เบอร์โทร, อีเมล, เฟซบุ๊ก (ชื่อ+ลิงก์), ไลน์ (ชื่อ), อินสตาแกรม (ชื่อ+ลิงก์) | เก็บใน `settings`; แสดงที่ footer, ปุ่มติดต่อของ Admin | 2, 6 |
| OWN-X | "ให้คิดให้ดี เพิ่มส่วนที่จำเป็นได้ แต่ให้บอกก่อน" | ข้อเสนอ E1–E9 **อนุมัติครบแล้ว (v6)** ดูหัวข้อ 2.6 และ 11 | — |

### 2.3 Admin

| รหัส | ข้อกำหนด | ความหมายที่ใช้ทำงาน | เฟส |
|---|---|---|---|
| ADM-0 | ส่วนแอดมินดีอยู่แล้ว (ไม่แก้ลอจิกเดิม) | คงฟังก์ชันเดิมทั้งหมด: สต็อก/ข้อมูลพื้นฐานสินค้า ตอบแชท ตรวจสลิป จัดส่ง (ไม่เห็นรายได้) | 6 |
| ADM-1 | ปุ่ม "ข้อมูลติดต่อเจ้าของร้าน": เบอร์โทร, อีเมล (ปุ่มส่งด่วน พิมพ์ข้อความ ระบบแพ็กแล้วส่งไปอีเมลเจ้าของอัตโนมัติ), เฟซบุ๊ก (ชื่อ+ลิงก์), ไลน์ (ชื่อ), IG (ชื่อ) | ดึงจาก OWN-6; ส่งอีเมลผ่าน SMTP ของระบบ ใส่ชื่อ/อีเมลแอดมินเป็น Reply-To (ดู D6) | 2, 6, 7 |

### 2.4 Buyer

| รหัส | ข้อกำหนด | ความหมายที่ใช้ทำงาน | เฟส |
|---|---|---|---|
| BUY-1 | กดรับคูปอง เพิ่มสินค้า/ทำอย่างอื่น ต้องล็อกอินก่อน = สมัครบัญชี กรอกที่อยู่จัดส่งเริ่มต้น ใส่เบอร์โทร ยืนยันโอทีพีว่าอีเมลจริง | ฟอร์มสมัคร: ชื่อ, เบอร์, อีเมล, ที่อยู่, รหัสผ่าน → OTP → สร้างบัญชี + ที่อยู่ตั้งต้น | 1, 4, 5 |
| BUY-2 | เข้าแอปมาเห็นหน้าแรก/สินค้า/คูปองได้ แต่ทำอะไรไม่ได้มาก ต้องสมัครก่อนสั่งซื้อ | โหมดผู้เยี่ยมชม (guest): ดูได้, ปุ่มสั่ง/ตะกร้า/หัวใจ/รับคูปองพาไปล็อกอิน (ดูหัวข้อ 12.3) | 4, 5 |
| BUY-3 | หน้าออเดอร์เรียงขั้นตอน: การสั่งซื้อ → รอชำระเงิน → ชำระเงินแล้ว → รอตรวจสลิป → จัดส่งแล้ว → สำเร็จ → รอรีวิว, สินค้าที่ยกเลิก | **ยืนยันแล้ว (D4):** แท็บ/ตัวกรอง/ตัวนับสถานะเรียงตามลำดับของเจ้าของโปรเจกต์ (หัวข้อ 3.1) ใช้ทั้งฝั่งผู้ซื้อและหลังบ้านทุกหน้า (ออเดอร์แอดมิน, ตรวจสลิป, dashboard) | 5, 6 |
| BUY-4 | ที่อยู่จัดส่งเพิ่มได้ตามปกติ; สมัครใหม่ก็ต้องเพิ่มใหม่ตามบัญชี | ที่อยู่ผูกกับบัญชี; บังคับมีอย่างน้อย 1 ที่อยู่ก่อนสั่งซื้อ | 1, 5 |
| BUY-5 | เปรียบเทียบไม้ได้ตั้งแต่ 2 ถึง 5 ไม้ | แก้จาก 2–3 เป็น 2–5 ใน service + UI (ตารางเลื่อนแนวนอนบนมือถือ) | 2, 5 |

### 2.5 UX/UI (จากหน้า "ตัวอย่างหน้าแอป" และข้อความที่ส่งเพิ่ม)

| รหัส | ข้อกำหนด | เฟส |
|---|---|---|
| UX-1 | ทำให้สวยขึ้น แอนิเมชันลื่น ใช้สีเยอะๆ ธีมสีหลักเหลือง สีแดงสำหรับของตื่นเต้น/ลดราคา | 4, 8 |
| UX-2 | สลับธีมเปลี่ยน **เฉพาะพื้นหลัง/พื้นผิว/ตัวอักษร** สีหลักเหลืองและสีแดงคงเดิมทุกธีม | 4 |
| UX-3 | โครงหน้าแรกผู้ซื้อ: แถบบน → แบนเนอร์ยาวเลื่อนอัตโนมัติ 7–10 ภาพ → Flash Sale (สีแดง) → หมวดหมู่/แบรนด์ (ปุ่มเหลือง) → สินค้าแนะนำ (กริด 5 คอลัมน์บน PC) → ส่วนท้ายเกี่ยวกับเรา/ช่องทางติดต่อ (สไตล์ 7-Eleven) | 5 |
| UX-4 | หน้าสินค้า: ชื่อกับราคาเด่นสุด; ดาวรีวิว/รายละเอียดเล็กลง | 5 |
| UX-5 | หน้า Login/Sign up สไตล์โมเดิร์นเหมือนแอปทั่วไป (Shopee / 7-Eleven) | 4 |
| UX-6 | Buyer ใช้ได้ทั้ง PC และมือถือ; Owner/Admin ใช้บน PC เท่านั้น | 4, 6, 8 |
| UX-7 | รูปแบนเนอร์ทั้งหมดจะเอามาใส่ทีหลัง → ใช้ตัวแทน (placeholder) ไปก่อน | 5 |

### 2.6 ข้อกำหนดเพิ่มเติมที่อนุมัติแล้ว (E1–E8 — v6)

| รหัส | ข้อกำหนด | ความหมายที่ใช้ทำงาน | เฟส |
|---|---|---|---|
| E1 | ที่อยู่ร้าน + เวลาเปิดปิด + ลิงก์ Google Maps | เพิ่มคีย์ `shop_address`, `shop_hours`, `maps_url` ใน `settings` (owner แก้ในหน้าเดียวกับ OWN-6); แสดงที่ footer, หน้า `/contact`, ปุ่ม "นำทาง" | 2D, 5A, 6 |
| E2 | จัดการแบนเนอร์ในหน้าเจ้าของ | ตาราง `banners`; owner อัปโหลด/เรียง/ซ่อน-แสดง/ใส่ลิงก์ปลายทาง/ลบ; หน้าแรกอ่านจาก DB (ไม่มี → ดูโฟลเดอร์ `assets/images/banners/` → ไม่มี → ตัวแทนพื้นไล่สี) | 2I, 5A, 6 |
| E3 | ลิงก์ LINE Official / TikTok | เพิ่ม `line_oa_url`, `tiktok_name`, `tiktok_url` ต่อจากช่องทางเดิม (เบอร์/อีเมล/FB/LINE/IG) | 2D, 5A, 6 |
| E4 | บันทึกกิจกรรมสำคัญ (audit log) | ตาราง `audit_log` เพิ่มอย่างเดียว; owner ดูได้; บันทึกการลบสินค้า/แก้คูปอง/เพิ่มแอดมิน/แก้ตั้งค่า ฯลฯ | 2J, 6 |
| E5 | อีเมลแจ้ง "จัดส่งแล้ว + เลขพัสดุ" ให้ผู้ซื้อ | ใช้ `email_outbox` เดียวกับใบเสร็จ (`kind='shipped'`), ส่งหลัง commit ของการจัดส่ง, ส่งครั้งเดียวต่อออเดอร์ + ปุ่มส่งซ้ำ | 2K, 6 |
| E6 | อีเมลแจ้งสต็อกต่ำถึงเจ้าของ | **สรุปรายวัน** (ไม่เกิน 1 ฉบับ/วัน) ไป `OWNER_EMAIL`; ตัวตั้งเวลาเรียกวันละครั้ง | 2L, 4 |
| E7 | ส่งออกไป Google Sheets (นอกจาก .xlsx) | ปุ่มกดเอง (ไม่อัตโนมัติ) ผ่าน service account; **ค่าเริ่มต้นตัดเบอร์/ที่อยู่ลูกค้าออก** เพราะขึ้นคลาวด์บุคคลที่สาม; .xlsx ยังเป็นวิธีหลัก (D8) | 2M, 6 |
| E8 | คำค้นหาแนะนำ (autocomplete) + สินค้าที่ดูล่าสุด | `suggest_products` + `get_cards_by_ids` (สาธารณะ); "ดูล่าสุด" เก็บ id ใน `localStorage` ของเบราว์เซอร์ ไม่เก็บใน DB | 2N, 5A, 5B |

> E9 (ลืมรหัสผ่านด้วย OTP) อยู่ในแผนหลักแล้วตั้งแต่ v4 (D13). ค่าที่ AI เลือกให้ในข้อ E5–E8 เป็น "ค่าเริ่มต้นที่แนะนำ" เปลี่ยนได้ — บันทึกไว้ในหัวข้อ 13

> หมายเหตุการอ่าน PDF: ข้อความใน PDF บางส่วนถูกสกัดเป็นตัวอักษรเพี้ยน ผมอ่านจากภาพหน้าเอกสารเป็นหลัก ถ้ามีข้อใดตีความผิด ให้แก้ในตารางนี้ก่อนเริ่มทำเฟสที่เกี่ยวข้อง

---

## 3. ข้อที่ต้องตัดสินใจ / ยืนยัน (Decisions) ❓

ทุกข้อมี "ค่าเริ่มต้นที่แนะนำ" ถ้าเจ้าของโปรเจกต์ยังไม่ตอบให้ใช้ค่านั้น

| # | คำถาม | ตัวเลือก | ค่าเริ่มต้นที่แนะนำ |
|---|---|---|---|
| D1 | เทคโนโลยีหน้าจอ | (A) เว็บ (Flask + HTML/CSS/JS) ทั้ง Buyer และ Owner/Admin; (B) ทำเว็บเฉพาะ Buyer แล้วคงแอป Desktop ไว้สำหรับ Owner/Admin | **A** (โค้ดเดียว ดีไซน์เดียว) ระหว่างทางคง Desktop ไว้ใช้ได้ (ใช้ DB เดียวกัน WAL รองรับ) จนเว็บฝั่งแอดมินครบแล้วค่อยเลิกใช้ |
| D2 | บังคับ "Owner/Admin ใช้ที่คอมเท่านั้น" | หน้าแอดมินแสดงเฉพาะจอ ≥ 1000px + บล็อก User-Agent มือถือ + (เลือกได้) จำกัด IP/คอมร้าน | ทำ 2 ชั้นแรก; ชั้น IP เป็นตัวเลือกใน config (`STAFF_ALLOWED_IPS`) เพราะ User-Agent ไม่ใช่ความปลอดภัยจริง |
| D3 | OTP ตอนล็อกอิน | — | ✅ **ยืนยันแล้ว:** OTP ส่งเฉพาะตอนสมัครด้วยอีเมลใหม่ ครั้งเดียวต่ออีเมล หลังยืนยัน (`email_verified=1`) ล็อกอินด้วยอีเมล+รหัสผ่านได้เลย ไม่มี OTP ตอนล็อกอิน/เครื่องใหม่ (ตัด `LOGIN_OTP_MODE` ออก); OTP เพิ่มเฉพาะตอนลืมรหัสผ่าน (D13) |
| D4 | ลำดับแท็บ/สถานะ | — | ✅ **ยืนยันแล้ว:** ใช้ลำดับของเจ้าของโปรเจกต์ ดูหัวข้อ 3.1 |
| D5 | ที่มาของ "รายจ่าย" ในไฟล์สำรอง | (ก) ตาราง `expenses` ให้เจ้าของกรอก; (ข) เพิ่ม `cost_price` ต่อสินค้า คำนวณต้นทุนขาย; (ค) ทั้งสอง | **ค** เริ่มจาก (ก) ก่อน (ง่าย) และ `cost_price` เป็นช่องไม่บังคับ |
| D6 | ส่งอีเมลด่วนของ Admin ถึงเจ้าของ | ระบบส่งจากอีเมลบัญชีร้าน (SMTP) โดยตั้ง Reply-To เป็นอีเมลแอดมิน | ใช้แบบนี้ (การส่ง "จาก" กล่องจดหมายแอดมินจริงต้องรู้รหัสผ่านอีเมลของเขา ซึ่งไม่ควรเก็บ) |
| D7 | เพิ่ม Admin | (ก) เลือกจากบัญชีที่ลงทะเบียนแล้ว (อีเมลยืนยันแล้ว) แล้วเลื่อนเป็น Admin + ตั้งรหัสใหม่; (ข) พิมพ์อีเมลใหม่ | รองรับทั้งสอง; Admin ที่เลื่อนขั้นจะใช้ซื้อของเป็นผู้ซื้อไม่ได้ (บทบาทเดียวต่อบัญชี) |
| D8 | Google Sheets | PDF เขียน "Sheets หรือ .xlsx" | ทำ .xlsx ก่อน (ไม่ต้องใช้บัญชี Google) ส่วน Sheets เป็นงานเสริมภายหลัง |
| D9 | ออกคูปองรางวัลเมื่อไหร่ | เมื่อชำระเงินแล้ว (`paid`) หรือเมื่อสำเร็จ (`completed`) | **completed** (กันยกเลิก/คืนของแล้วได้คูปองไปฟรี) |
| D10 | "กดรับคูปอง" (ข้อ BUY-1) | เพิ่มศูนย์คูปองให้ผู้ซื้อกดรับคูปองสาธารณะ | ทำแบบง่าย: คูปองที่ติดธง `claimable` กด "รับ" แล้วเก็บในคูปองของฉัน; ยังพิมพ์โค้ดที่หน้าชำระเงินได้เหมือนเดิม |
| D11 | โฮสต์ | เครื่องร้าน + tunnel / PythonAnywhere / VPS | เริ่มบนเครื่องร้าน + Cloudflare Tunnel (ได้ HTTPS ฟรี) ระหว่างพัฒนา ตัดสินใจจริงตอน Phase 9 |
| D12 | ผู้ส่งอีเมลใบเสร็จ (SYS-3) | (ก) ส่งอัตโนมัติจากระบบ; (ข) ส่งจากอีเมลเจ้าของร้าน | ✅ ใช้บัญชี SMTP เดียวของร้าน: ตั้ง `SMTP_USER/SMTP_FROM` เป็นอีเมลเจ้าของร้าน (หรือบัญชีใหม่ของร้าน) ระบบส่งให้อัตโนมัติผ่านบัญชีนี้ จึงครอบคลุมทั้ง (ก) และ (ข); ตั้ง `Reply-To` = `shop_email`; **ส่งในนามอีเมลของผู้ใช้/แอดมินคนอื่นไม่ได้** (ต้องรู้รหัสผ่านอีเมลเขา และมักถูกตีเป็นสแปม) |
| D13 | ลืมรหัสผ่านของผู้ซื้อ | — | ✅ **ยืนยันแล้ว (E9 อนุมัติ):** ผู้ซื้อกด "ลืมรหัสผ่าน?" → กรอกอีเมล → รับ OTP 6 หลักทางอีเมล → ตั้งรหัสใหม่ → กลับมาหน้าล็อกอิน; ใช้ได้กับบัญชีผู้ซื้อที่ยืนยันอีเมลแล้วเท่านั้น; ล็อกอินปกติยังไม่มี OTP; เจ้าของยังตั้งรหัสชั่วคราวให้ได้ (`must_change_password=1`) |
| D14 | ลืมรหัสผ่านของ Owner/Admin | — | ✅ **ยืนยันแล้ว (v5):** **เฉพาะ Owner เท่านั้นที่แก้รหัสของ Admin/Owner ได้** — ไม่มี OTP ให้บัญชีพนักงาน; Admin กด "ลืมรหัสผ่าน (พนักงาน)" → ระบบ **แสดงช่องทางติดต่อ Owner** (เบอร์, อีเมล, FB, LINE, IG จาก `get_contact_info()`) → ติดต่อ Owner → Owner รันสคริปต์ `tools/reset_password.py` บนเครื่องร้านเพื่อตั้งรหัสใหม่ให้ทันที (บังคับเปลี่ยนรหัสตอนเข้าครั้งแรก + ออกจากระบบทุกเครื่อง); Owner ลืมรหัสตัวเอง → รันสคริปต์เดียวกันบนเครื่องร้าน |

### 3.1 ลำดับสถานะที่แสดง (D4 ยืนยันแล้ว)

| ลำดับ | ป้ายที่แสดง | ค่าใน DB | คำอธิบาย (tooltip) |
|---|---|---|---|
| 1 | การสั่งซื้อ (ทั้งหมด) | ทุกสถานะ | แท็บรวมทุกออเดอร์ |
| 2 | รอชำระเงิน | `pending` | ยังไม่ชำระ/ยังไม่แนบสลิป |
| 3 | ชำระเงินแล้ว | `paid` | แอดมินยืนยันสลิปแล้ว |
| 4 | รอตรวจสลิป | `checking_slip` | ผู้ซื้อแนบสลิปแล้ว รอแอดมินตรวจ |
| 5 | จัดส่งแล้ว | `shipped` | มีเลขพัสดุ |
| 6 | สำเร็จ | `completed` | ผู้ซื้อยืนยันรับของ/ครบกำหนด |
| 7 | รอรีวิว | (คำนวณ) | ออเดอร์ `completed` ที่ยังมีสินค้าไม่ถูกรีวิว |
| 8 | สินค้าที่ยกเลิก | `cancelled` | ยกเลิกแล้ว |

- เก็บลำดับนี้ในค่าคงที่เดียว `ORDER_STATUS_DISPLAY_ORDER` (+ ป้ายไทย + tooltip) ใน `core/constants.py` แล้วใช้ทุกที่: แท็บออเดอร์ผู้ซื้อ, แท็บ/ตัวกรองออเดอร์แอดมิน, หน้าตรวจสลิป, ตัวนับสถานะบน dashboard, ตัวเลือกสถานะ, คำอธิบายสถานะ
- **ไม่แตะ state machine ใน `order_service`** (การเปลี่ยนสถานะจริงยังเป็น `pending → checking_slip → paid → shipped → completed` และ `cancelled`) และไม่เปลี่ยนชื่อค่าใน DB; ลำดับนี้เป็นเรื่อง "การแสดงผล" เท่านั้น
- timeline ในหน้ารายละเอียดออเดอร์แสดงเหตุการณ์จริงตามเวลาจาก `order_status_log` (ประวัติย้อนลำดับไม่ได้) ส่วนป้าย/ตัวกรอง/ตัวนับทั้งหมดใช้ลำดับในตารางนี้
- ถ้าภายหลังลำดับนี้ชวนสับสน แก้ได้ที่ค่าคงที่ตัวเดียว

---

## 4. สถาปัตยกรรมเป้าหมาย

```
มือถือ/PC ผู้ซื้อ ─┐
                    ├─► Flask (web/) ──► services/ ──► database/ ──► data/shop.db
PC เจ้าของ/แอดมิน ──┘      ▲                 ▲
   (ลอจิกชุดเดียว)         templates + static   ใช้ของเดิมเกือบทั้งหมด
```

- **โครงที่เพิ่ม** (โค้ดตัวอย่างอยู่ในภาคผนวก D และแผนที่ route อยู่ในภาคผนวก C)
  ```
  web/            app.py, auth.py, routes_buyer.py, routes_admin.py, routes_api.py
  web/templates/  base.html, buyer/*, admin/*, partials/*, auth/*
  web/static/     css/ (theme.css, base.css, components.css), js/, icons/, manifest.json, sw.js
  services/       email_service.py, otp_service.py, ai_guard.py, export_service.py,
                  expense_service.py, staff_service.py, contact_service.py (หรือรวมใน settings_service),
                  banner_service.py, audit_service.py, email_outbox_service.py
  run_web.py      จุดเริ่มเว็บ
  ```
- **Session ต่อ request:** แก้ `core/session.py` เป็น `contextvars` (โค้ดอยู่ในภาคผนวก D.1) — ต้องทำก่อนเปิดเว็บให้หลายคนใช้
- **เซสชันล็อกอิน:** ตาราง `sessions` (เก็บแฮชของ token) แทน dict ในหน่วยความจำ เพื่อให้ Admin ค้างล็อกอินข้ามการรีสตาร์ท
- **ย้ายงานที่ Desktop ทำตอนเปิด/ปิดแอป** ไปทำใน `run_web.py` + ตัวตั้งเวลา: `init_db`, `run_seed`, `clear_all_online`, `auto_cancel_unpaid`, สำรอง DB, ส่งออกรายเดือน
- **ผู้ซื้อบนมือถือ:** responsive (mobile-first) + PWA (manifest + service worker) ต้องใช้ HTTPS เมื่อออกอินเทอร์เน็ต

---

## 5. การเปลี่ยนแปลงฐานข้อมูล (เพิ่มอย่างเดียว ไม่ลบของเดิม)

ทำใน `database/db.py` → `init_db()` ด้วย `_ensure_column` / `CREATE TABLE IF NOT EXISTS` และเพิ่ม repo ที่เกี่ยวข้อง

### 5.1 คอลัมน์เพิ่มในตารางเดิม

| ตาราง | คอลัมน์ | ใช้ทำอะไร |
|---|---|---|
| `users` | `email_verified INTEGER DEFAULT 0` | ยืนยันอีเมลด้วย OTP แล้วหรือยัง |
| `users` | `must_change_password INTEGER DEFAULT 0` | บังคับเปลี่ยนรหัสครั้งแรก (บัญชีเจ้าของจาก seed) |
| `users` | `last_login_at TIMESTAMP` | แสดงในหน้า "ผู้ใช้" ของเจ้าของ (ล็อกอินล่าสุด) |
| `products` | `deleted_at TIMESTAMP`, `deleted_by INTEGER` | Soft delete (OWN-2) |
| `products` | `cost_price REAL` (ไม่บังคับ) | ต้นทุน (D5) |
| `categories` | `deleted_at TIMESTAMP`, `all_brands INTEGER DEFAULT 0` | Soft delete + ธง "ใช้กับทุกแบรนด์รวมแบรนด์ใหม่" |
| `brands` | `deleted_at TIMESTAMP` | Soft delete |
| `coupons` | `owner_user_id INTEGER`, `source_rule_id INTEGER`, `source_order_id INTEGER`, `claimable INTEGER DEFAULT 0`, `max_discount REAL`, `starts_at TIMESTAMP` | คูปองส่วนตัวจากกฎรางวัล, กดรับได้, เพดานส่วนลด, วันเริ่ม |

> `users.username` ยัง `NOT NULL UNIQUE` ในสคีมา: ให้ระบบสร้าง username อัตโนมัติจากอีเมล (เช่น ส่วนหน้า @ + ตัวเลขสุ่มถ้าซ้ำ) และเลิกแสดง/ใช้ในหน้าล็อกอิน เพื่อไม่ต้องแก้ตารางและโค้ดเดิม

### 5.2 ตารางใหม่

```sql
CREATE TABLE IF NOT EXISTS email_otps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK(purpose IN ('register','reset')),   -- register = สมัครอีเมลใหม่ (D3) · reset = ลืมรหัสผ่าน (D13)
  code_hash TEXT NOT NULL,            -- แฮชของรหัส ไม่เก็บรหัสจริง
  attempts INTEGER DEFAULT 0,         -- กรอกผิดได้ไม่เกิน 5 ครั้ง
  expires_at TIMESTAMP NOT NULL,      -- อายุ 10 นาที
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS pending_registrations (   -- ข้อมูลสมัครที่ยังไม่ยืนยันอีเมล
  email TEXT PRIMARY KEY, full_name TEXT, phone TEXT, password_hash TEXT,
  address_json TEXT, created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
  remember INTEGER DEFAULT 0, user_agent TEXT, ip TEXT,
  created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
  last_seen_at TIMESTAMP, expires_at TIMESTAMP NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS category_brands (
  category_id INTEGER NOT NULL, brand_id INTEGER NOT NULL,
  PRIMARY KEY(category_id, brand_id),
  FOREIGN KEY(category_id) REFERENCES categories(id), FOREIGN KEY(brand_id) REFERENCES brands(id)
);
CREATE TABLE IF NOT EXISTS coupon_rules (          -- กฎ "ซื้อครบรับคูปอง" (OWN-1)
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
  trigger_min_spend REAL NOT NULL,                 -- เช่น 3000
  reward_type TEXT NOT NULL CHECK(reward_type IN ('fixed','percent')),
  reward_value REAL NOT NULL,                      -- เช่น 300
  reward_min_order REAL DEFAULT 0,                 -- เช่น 1000
  reward_valid_days INTEGER DEFAULT 30,
  is_active INTEGER DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_coupon_reward_once
  ON coupons(source_rule_id, source_order_id) WHERE source_rule_id IS NOT NULL;  -- กันออกซ้ำ
CREATE TABLE IF NOT EXISTS coupon_claims (         -- D10
  user_id INTEGER NOT NULL, coupon_id INTEGER NOT NULL,
  claimed_at TIMESTAMP DEFAULT (datetime('now','localtime')),
  PRIMARY KEY(user_id, coupon_id)
);
CREATE TABLE IF NOT EXISTS expenses (              -- D5
  id INTEGER PRIMARY KEY AUTOINCREMENT, spent_on DATE NOT NULL,
  category TEXT NOT NULL, amount REAL NOT NULL CHECK(amount >= 0), note TEXT,
  created_by INTEGER, created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS staff_messages (        -- ADM-1 ประวัติอีเมลด่วน
  id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER NOT NULL,
  subject TEXT, body TEXT NOT NULL, sent_ok INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS email_outbox (          -- คิวอีเมลใบเสร็จ/จัดส่ง/สต็อกต่ำ/อีเมลด่วน (SYS-3, E5, E6) ส่งซ้ำและตรวจย้อนหลังได้
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL CHECK(kind IN ('receipt','staff_urgent','shipped','low_stock')),   -- ห้ามเอา OTP เข้าตารางนี้ (จะเก็บรหัสจริงในฐานข้อมูล)
  to_email TEXT NOT NULL, subject TEXT NOT NULL, body_text TEXT, body_html TEXT,
  attachment_path TEXT, related_order_id INTEGER,
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending','sent','failed')),
  attempts INTEGER DEFAULT 0, last_error TEXT,
  created_at TIMESTAMP DEFAULT (datetime('now','localtime')), sent_at TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_outbox_receipt_once
  ON email_outbox(related_order_id) WHERE kind = 'receipt';   -- ใบเสร็จต่อออเดอร์ส่งครั้งเดียว (ส่งซ้ำด้วยมือใช้การอัปเดตแถวเดิม)
CREATE UNIQUE INDEX IF NOT EXISTS ux_outbox_shipped_once            -- E5
  ON email_outbox(related_order_id) WHERE kind = 'shipped';          -- อีเมลจัดส่งต่อออเดอร์ส่งครั้งเดียว; low_stock ใช้ related_order_id = NULL
CREATE TABLE IF NOT EXISTS banners (                -- E2
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  image_path TEXT NOT NULL,                         -- path relative จาก root เช่น assets/images/banners/banner_x.jpg
  link_url TEXT, alt_text TEXT,                     -- link_url: https:// หรือ path ภายในที่ขึ้นต้น / เท่านั้น
  sort_order INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1,
  created_by INTEGER, created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS audit_log (              -- E4 เพิ่มอย่างเดียว ไม่มีฟังก์ชันแก้/ลบ
  id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id INTEGER, actor_role TEXT,
  action TEXT NOT NULL, target_type TEXT, target_id INTEGER,
  detail TEXT,                                      -- JSON; ห้ามมีรหัสผ่าน/OTP/token
  created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_audit_created ON audit_log(created_at);
```

### 5.3 คีย์ใหม่ใน `settings` (ตาราง key/value เดิม)

`shop_phone`, `shop_email`, `facebook_name`, `facebook_url`, `line_name`, `instagram_name`, `instagram_url`, **(v6)** `shop_address`, `shop_hours`, `maps_url`, `line_oa_url`, `tiktok_name`, `tiktok_url`, `last_auto_export` (เดือนล่าสุดที่ส่งออกแล้ว เช่น `2026-09`), `last_low_stock_email` (วันที่ส่งสรุปสต็อกต่ำล่าสุด `YYYY-MM-DD`) · ตรวจรูปแบบ: เบอร์ 9–10 หลัก, ลิงก์ (รวม `maps_url`, `line_oa_url`, `tiktok_url`) ต้องขึ้นต้น `https://` เท่านั้น (กัน `javascript:`); `shop_address`/`shop_hours` ยาวไม่เกิน 300 ตัวอักษร และ escape ทุกครั้งที่แสดง

### 5.4 `.env` ที่เพิ่ม

```env
OWNER_EMAIL=             # อีเมลเจ้าของร้าน (ตายตัว) — ต้องเป็นอีเมลจริง
OWNER_INITIAL_PASSWORD=  # รหัสตั้งต้น ใช้ครั้งแรกแล้วบังคับเปลี่ยน
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=           # Gmail ต้องใช้ App Password (เปิด 2-Step ก่อน)
SMTP_FROM=Badminton Pro Shop <อีเมลเจ้าของร้าน>   # ผู้ส่ง OTP/ใบเสร็จ/อีเมลด่วน (D12)
OTP_DEV_ECHO=0           # 1 = พิมพ์ OTP ลง console (ใช้ตอนพัฒนาเท่านั้น)
RECEIPT_EMAIL_ENABLED=1   # 1 = ส่งใบเสร็จอีเมลหลังตรวจสลิปผ่าน (SYS-3)
SHIPPED_EMAIL_ENABLED=1   # 1 = ส่งอีเมลแจ้งจัดส่ง+เลขพัสดุ (E5)
LOW_STOCK_EMAIL_ENABLED=1 # 1 = ส่งสรุปสต็อกต่ำถึงเจ้าของวันละไม่เกิน 1 ฉบับ (E6)
GOOGLE_SERVICE_ACCOUNT_FILE=  # path ไฟล์กุญแจ service account เช่น secrets/google.json (E7) — ห้าม commit; ว่าง = ปิดปุ่ม Sheets
GOOGLE_SHEET_ID=              # ID สเปรดชีตปลายทาง (E7)
STAFF_ALLOWED_IPS=       # ว่าง = ไม่จำกัด; เช่น 127.0.0.1,192.168.1.10
FLASK_SECRET=
```

---

## 6. ระบบดีไซน์ (Design System) — โค้ดโทเค็นเต็มอยู่ในภาคผนวก A

| หัวข้อ | ค่า/กติกา |
|---|---|
| สีหลัก | เหลือง `#FFB703` → ส้ม `#FB8500` (ไล่สี) คงที่ทุกธีม |
| สีเน้น | แดง `#E63946` (ลดราคา/Flash Sale/ราคา), เขียว `#16A34A` (สำเร็จ), ฟ้า `#0EA5E9` (ข้อมูล), เสริมสีอื่นได้ตามความเหมาะสม (เช่น หมวดหมู่ละสี) |
| ธีม | สลับ `data-theme="light/dark"` เปลี่ยนแค่ `--bg --sf --sf2 --tx --mu --bd --sh` จำใน `localStorage`; ค่าเริ่มต้นตามเครื่อง (`prefers-color-scheme`) |
| ตัวอักษร | Noto Sans Thai / Sarabun (โหลดจาก Google Fonts หรือฝังไฟล์) ช่องกรอก ≥ 16px กัน iOS ซูม |
| ลำดับความเด่น | ชื่อสินค้า + ราคา (ใหญ่ หนา แดง) > ปุ่มสั่งซื้อ > ดาว/จำนวนขาย/สเปก (เล็ก สีจาง) |
| ปุ่ม | สูง ≥ 44px, มุมโค้ง 12px, hover ยกเงา, active ย่อ (scale .96) |
| การ์ดสินค้า | hover ยกขึ้น 6px + เงา; ป้ายลด % มุมซ้ายบน (แดง); ปุ่มหัวใจมุมขวาบน (เด้งตอนกด) |
| แอนิเมชัน | แบนเนอร์เลื่อน 0.7s `cubic-bezier(.65,0,.25,1)`; การ์ดเลื่อนเข้าเมื่อเห็น (fade-up 0.6s); dialog เด้งขึ้น 0.3s; ทุกอย่างปิดเมื่อ `prefers-reduced-motion` |
| Breakpoints | ≤ 600 มือถือ (กริด 2 คอลัมน์) · ≤ 1000 แท็บเล็ต (3) · > 1000 PC (5 คอลัมน์) · ≥ 900 ซ่อนเมนูล่าง |
| มือถือ | เมนูล่าง (หน้าแรก/หมวดหมู่/ตะกร้า/ออเดอร์/ฉัน), ช่องค้นหาเต็มแถว, แถบ Flash Sale เลื่อนแนวนอน, safe-area สำหรับ iPhone |
| แบนเนอร์ | 7–10 ภาพ, อัตราส่วน 21:8 (แนะนำ 1680×640), `.jpg/.webp` ไม่เกิน ~300KB ต่อภาพ, เปลี่ยนทุก 4.5 วินาที, หยุดเมื่อ hover, ปัดนิ้วได้, ลูกศร/จุดบอกตำแหน่ง; จัดการผ่านหน้าเจ้าของ (E2) เก็บไฟล์ใน `assets/images/banners/`; ถ้า DB ไม่มีแบนเนอร์ให้อ่านรูปจากโฟลเดอร์ (เรียงตามชื่อไฟล์); ไม่มีรูปเลยใช้พื้นไล่สี + ข้อความ (ตัวแทน) |
| ส่วนท้าย | พื้นเหลือง วงกลมแดงโลโก้ "เกี่ยวกับเรา" + คอลัมน์ ช่วยเหลือ / ติดต่อเรา / ติดตามเรา; ข้อมูลดึงจาก OWN-6 + E1 (ที่อยู่/เวลาเปิดปิด/แผนที่) + E3 (LINE OA/TikTok) |
| หน้าแอดมิน/เจ้าของ | ใช้โทเค็นสีชุดเดียวกัน แต่เลย์เอาต์ PC: sidebar ซ้าย + ตารางกว้าง; ต่ำกว่า 1000px แสดงข้อความ "กรุณาใช้งานบนคอมพิวเตอร์" |
| การเข้าถึง | `aria-label` บนปุ่มไอคอน, คอนทราสต์พอ, โฟกัสเห็นชัด |

**ต้นแบบหน้าจอ:** ไม่มีโฟลเดอร์ `prototype/` ในซิป — ให้สร้าง `web/static/` ใหม่จากภาคผนวก A (CSS) และ B (โครงหน้า) ได้เลย; รายการต่อไปนี้คือหน้าที่ต้นแบบควรมี
- `index.html` หน้าแรกผู้ซื้อ: แบนเนอร์ 8 ภาพ, Flash Sale + นับถอยหลัง, หมวดหมู่/แบรนด์ (แท็บ), สินค้าแนะนำ 15 ชิ้น, ส่วนท้าย, เมนูล่างมือถือ, ปุ่มสลับธีม, popup หน้าสินค้า (ชื่อ+ราคาเด่น), การกั้นผู้เยี่ยมชม 
- หน้า login/register/verify/reset (ดูภาคผนวก B.4): แบ่งสองฝั่ง ซ้าย = พื้นเหลือง + ภาพสินค้าเปลี่ยนไปเรื่อยๆ, ขวา = ฟอร์ม; หัวข้อเปลี่ยนตามสถานการณ์
- ข้อมูลเป็นตัวอย่างทั้งหมด ยังไม่ต่อ DB; ใช้เป็นแบบ HTML/CSS ให้แปลงเป็น Jinja templates ใน Phase 4–5

---

## 7. ลำดับขั้นตอนการทำงาน (แบ่งเฟส)

> รูปแบบทุกเฟส: เป้าหมาย · ต้องมีก่อน · ไฟล์ที่แตะ · งาน (เช็กลิสต์) · เสร็จเมื่อ (Definition of Done) · สถานะ

### Phase 0 — เตรียมฐาน ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | `database/db.py` · `config.py` · `requirements.txt` · `.gitignore` · [ใหม่] .env.example |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `main.py` · `utils/backup.py` · `tests/ (ทั้ง 4 ไฟล์)` · `README.md` |

ซิปเต็มได้ถ้าโปรเจกต์ยังเล็ก เฟสนี้ต้องรันเทสต์ทั้งหมด จึงแนบ `tests/` ครบ และโค้ดที่เทสต์เรียก (`services/`, `database/`, `core/`, `utils/`)

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** มั่นใจว่าของเดิมผ่านเทสต์ และมีกลไกอัปเดตสคีมาที่ปลอดภัย
- **ต้องมีก่อน:** —
- **ไฟล์:** `database/db.py`, `requirements.txt`, `.env.example`, `.gitignore`
- [X] ตั้ง git (ถ้ายังไม่มี) แล้ว commit สถานะปัจจุบัน; สำรอง `data/shop.db`
- [X] รันเทสต์ทั้ง 4 ชุดให้ผ่าน (บันทึกจำนวนเทสต์ไว้เทียบ)
- [X] เพิ่มไลบรารี: `openpyxl`, `flask`, `waitress` (และ `Flask-WTF`/`Flask-Limiter` ในเฟส 9; `gspread` + `google-auth` สำหรับ E7 ติดตั้งแบบเลือกได้ — โค้ดต้อง import แบบ lazy) ใน `requirements.txt`
- [X] เพิ่มคีย์ใหม่ใน `.env.example` ตามหัวข้อ 5.4 และเพิ่ม `secrets/` ใน `.gitignore` (ที่เก็บไฟล์กุญแจ Google ของ E7)
- [X] **F1:** เพิ่ม `.webp` ใน `config.ALLOWED_IMAGE_EXTENSIONS` · **F2:** ตรวจ `.env` ในซิปไม่มีคีย์จริงหลุด (ถ้ามีให้หมุนคีย์ใหม่)
- [X] จัดระเบียบ `init_db()`: สร้างฟังก์ชันย่อย `_migrate_v2(cursor)` สำหรับสคีมาใหม่ทั้งหมด เรียกท้าย `init_db()`
- [X] **เสร็จเมื่อ:** เทสต์เดิมผ่านทั้งหมด, `python main.py --check` ผ่าน

### Phase 1 — ฐานข้อมูล + ล็อกอินอีเมล/OTP + บัญชีเจ้าของ/แอดมิน (backend) ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | `database/db.py` · `database/repo_users.py` · `database/repo_addresses.py` · `database/seed.py` · `services/auth_service.py` · `services/account_service.py` · `core/permissions.py` · `core/session.py (เฉพาะถ้าต้องเพิ่มฟิลด์)` · `config.py` · `utils/validators.py` · [ใหม่] database/repo_otp.py, repo_sessions.py · [ใหม่] services/email_service.py, otp_service.py, staff_service.py · [ใหม่] tools/reset_password.py · [ใหม่] tests/test_auth_otp.py, test_staff.py |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `database/repo_settings.py` · `database/repo_base.py` · `services/settings_service.py` · `core/constants.py` · `ui/pages/buyer/login.py` · `ui/pages/buyer/register.py` · `tests/test_services_basic.py` · `tests/test_repos.py (ดูวิธีสร้าง DB ชั่วคราวในเทสต์)` · `.env.example (จาก Phase 0)` |

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** SYS-1, OWN-4, BUY-1 (ฝั่ง service), BUY-4 (ที่อยู่ตอนสมัคร)
- **ต้องมีก่อน:** Phase 0
- **ไฟล์:** `database/db.py`, `database/repo_users.py` + repo ใหม่ (`repo_otp.py`, `repo_sessions.py`), `services/auth_service.py`, `services/email_service.py` (ใหม่), `services/otp_service.py` (ใหม่), `services/staff_service.py` (ใหม่), `config.py`, `database/seed.py`, `core/permissions.py`
- [X] เพิ่มคอลัมน์ `users.*` และตาราง `email_otps`, `pending_registrations`, `sessions` (หัวข้อ 5)
- [X] `email_service.send_mail(to, subject, text, html=None, attachments=(), reply_to=None)` ใช้ `smtplib` + TLS อ่านค่าจาก `.env`; ส่งใน thread แยก; รองรับ HTML + ไฟล์แนบ + Reply-To (ใช้กับ SYS-3); ถ้าไม่ได้ตั้ง SMTP และ `OTP_DEV_ECHO=1` ให้พิมพ์ลง console; ถ้าไม่ตั้งทั้งสองให้โยน `ValueError("ระบบส่งอีเมลยังไม่พร้อม")`; **รหัส OTP ห้ามบันทึกลง log หรือ `email_outbox`**
- [X] `otp_service`: สร้างรหัส 6 หลักด้วย `secrets`, เก็บเฉพาะแฮช, อายุ 10 นาที, กรอกผิดเกิน 5 ครั้งให้ใช้ไม่ได้, ส่งซ้ำได้ทุก 60 วินาที และไม่เกิน 5 ครั้ง/ชั่วโมง/อีเมล
- [X] `auth_service.register_start(email, password, full_name, phone, address)` → เก็บ `pending_registrations` + ส่ง OTP; `register_verify(email, code)` → สร้างผู้ใช้ buyer (`email_verified=1`) + ที่อยู่ตั้งต้น (`is_default=1`) ใน transaction เดียว
- [X] ตรวจรูปแบบอีเมล (`utils/validators.py`) แปลงเป็นตัวพิมพ์เล็ก; สร้าง `username` อัตโนมัติ (หัวข้อ 5.1); **อีเมลที่ยืนยันแล้วสมัครซ้ำไม่ได้** ("อีเมลนี้สมัครแล้ว กรุณาเข้าสู่ระบบ"); อีเมลที่ค้างยังไม่ยืนยันสมัครใหม่ได้ (เขียนทับ `pending_registrations`); ผู้ซื้อแก้อีเมลเองไม่ได้ใน v2 (อีเมล = ตัวตนล็อกอิน)
- [X] `auth_service.login(email, password)` อีเมล+รหัสผ่านเท่านั้น **ไม่มี OTP** (D3); ข้อความผิดพลาดเดิม (ไม่บอกว่าอีเมลมีหรือไม่); ถ้า `email_verified=0` ให้แจ้งว่ายังไม่ได้ยืนยันอีเมล; owner/admin ตั้ง `email_verified=1` โดยเจ้าของ จึงไม่ต้อง OTP
- [X] เจ้าของ: `seed` สร้างบัญชี owner จาก `OWNER_EMAIL` + `OWNER_INITIAL_PASSWORD` (`must_change_password=1`); ถ้าไม่ตั้งค่า → โหมดพัฒนาใช้ค่าตัวอย่างพร้อมเตือน; ห้ามสร้าง/ลดสิทธิ์ owner ผ่าน service อื่น
- [X] **ลืมรหัสผ่าน (D13/E9):** `auth_service.reset_start(email)` → ตอบข้อความเดียวกันเสมอ "ถ้าอีเมลนี้มีบัญชี ระบบจะส่งรหัสยืนยันให้" (กันเดาว่าอีเมลมีในระบบ) และส่ง OTP (`purpose='reset'`) **เฉพาะ** บัญชี buyer ที่ `email_verified=1` และไม่ถูกระงับ; `auth_service.reset_verify(email, code, new_password, confirm)` → ตรวจ OTP (กติกาเดียวกับสมัคร: 6 หลัก, 10 นาที, ผิด ≤ 5 ครั้ง, ส่งซ้ำ 60 วิ, ≤ 5/ชม.) → ตรวจความแข็งแรงรหัสผ่านเดิมของระบบ → เปลี่ยนรหัส → **ลบเซสชันทุกเครื่องของผู้ใช้นั้น** + ล้าง `must_change_password` → **ไม่ล็อกอินให้** (ให้กลับไปหน้าล็อกอิน) · อีเมลรีเซ็ตห้ามอยู่ใน `email_outbox` (D12) และไม่บันทึกรหัสลง log
- [X] เทสต์ลืมรหัสผ่าน: อีเมลไม่มี/ไม่ใช่ buyer/ยังไม่ยืนยัน → ข้อความเดียวกันและไม่ส่งอีเมล · OTP ผิด/หมดอายุ/เกิน 5 ครั้ง/ส่งซ้ำเร็วเกิน · รหัสเก่าใช้ไม่ได้หลังเปลี่ยน · เซสชันเก่าถูกเตะ · OTP `reset` ใช้แทน `register` ไม่ได้และกลับกัน
- [X] `staff_service` (เจ้าของเท่านั้น): `list_staff()`, `promote_to_admin(email, new_password, confirm_password)` และ/หรือ `create_admin(email, full_name, password)` (D7), `set_active(user_id, bool)`, `reset_staff_password(user_id, new_password)`, `revoke_sessions(user_id)`, `reset_user_password(user_id, temp_password)` (ผู้ซื้อ/แอดมิน ตั้ง `must_change_password=1`; ใช้กรณี Admin ลืมรหัส D14)
- [X] สคริปต์ CLI `tools/reset_password.py` (รันบนเครื่องร้านเท่านั้น ด้วยมือ ไม่ผูกกับเว็บ): ถามอีเมล → ตรวจว่ามีบัญชี owner/admin → ถามรหัสใหม่ 2 ครั้ง (ไม่แสดงตัวอักษร, ตรวจความแข็งแรง) → ตั้งรหัส bcrypt + `must_change_password=1` + ลบเซสชันทุกเครื่องของบัญชีนั้น + บันทึกเวลา/ผลใน log (ไม่บันทึกรหัส) (D14) พร้อมเทสต์ฟังก์ชันแกนกลาง (แยกฟังก์ชัน `reset_password(email, new_password)` ออกจากส่วนถามผ่านคอนโซล)
- [X] `repo_sessions`: สร้าง/ตรวจ/ต่ออายุ/ลบเซสชัน (เก็บแฮช token); ผู้ซื้อ 7 วัน, staff 90 วัน (ต่ออายุทุกครั้งที่ใช้)
- [X] ย้ายบัญชีตัวอย่างใน seed ให้เป็นอีเมลรูปแบบที่ใช้ได้และ `email_verified=1` (ใช้ทดสอบเท่านั้น)
- [X] เทสต์: สมัคร→OTP ผิด/ถูก/หมดอายุ/ส่งซ้ำเร็วเกิน, อีเมลซ้ำ (ยืนยันแล้ว = ปฏิเสธ), **ล็อกอินหลังยืนยันแล้วไม่ถูกขอ OTP**, เจ้าของเพิ่มแอดมิน, แอดมินเพิ่มแอดมินไม่ได้ (PermissionError), เซสชันหมดอายุ, เจ้าของตั้งรหัสชั่วคราวให้ผู้ซื้อแล้วถูกบังคับเปลี่ยน
- [X] **เสร็จเมื่อ:** เทสต์ใหม่ผ่าน + เทสต์เดิมไม่พัง + เจ้าของล็อกอินด้วย `OWNER_EMAIL` ได้และถูกบังคับเปลี่ยนรหัส

### Phase 2 — Backend ฟีเจอร์เจ้าของร้าน (ยังไม่ทำหน้าจอ) ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | `database/db.py` · `database/repo_products.py` · `database/repo_coupons.py` · `database/repo_orders.py` · `database/repo_settings.py` · `database/repo_reviews.py` · `database/repo_users.py` · `services/product_service.py` · `services/coupon_service.py` · `services/settings_service.py` · `services/order_service.py` · `services/payment_service.py` · `services/review_service.py` · `services/notification_service.py` · `services/shipping_service.py` (ตัวห่อ E5) · `services/staff_service.py` (จาก Phase 1 — เพิ่มบันทึก audit) · `core/constants.py` · `core/permissions.py` (เพิ่ม `BANNER_MANAGE`, `AUDIT_VIEW` เฉพาะ owner) · [ใหม่] services/export_service.py, expense_service.py, contact_service.py, email_outbox_service.py, banner_service.py, audit_service.py · [ใหม่] database/repo_expenses.py, repo_outbox.py, repo_banners.py, repo_audit.py · [ใหม่] tests/test_soft_delete.py, test_category_brand.py, test_coupon_rules.py, test_export.py, test_contact.py, test_receipt_email.py, test_banners.py, test_audit.py, test_shipped_email.py, test_low_stock_email.py, test_google_sheets.py, test_suggest.py |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `services/receipt_service.py (สร้าง PDF ใบเสร็จ)` · `utils/font_installer.py` · `utils/image_utils.py` (banner_service ใช้ `save_upload`) · `assets/fonts/ (ฟอนต์ใบเสร็จ)` · `services/email_service.py (จาก Phase 1)` · `database/repo_payments.py` · `database/repo_notifications.py` · `database/repo_shipping.py` · `database/seed.py` · `utils/backup.py` · `utils/formatters.py` · `config.py` · `tests/test_order_flow.py` · `tests/test_services_basic.py` · `tests/test_repos.py` |

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** OWN-1, OWN-2, OWN-3, OWN-5, OWN-6, ADM-1 (ข้อมูล+ส่งอีเมล), BUY-5 (service), SYS-3 (ใบเสร็จอีเมล), D4 (ค่าคงที่ลำดับสถานะ), **E1–E8 (v6)**
- **ต้องมีก่อน:** Phase 1 (อีเมล/สิทธิ์)
- **ไฟล์:** `services/product_service.py`, `coupon_service.py`, `settings_service.py`, `order_service.py`, `export_service.py` (ใหม่), `expense_service.py` (ใหม่), `banner_service.py` (ใหม่), `audit_service.py` (ใหม่), `email_outbox_service.py` (ใหม่), `shipping_service.py`, `staff_service.py`, `database/repo_*`, `core/permissions.py`

**2A Soft delete สินค้า/หมวด/แบรนด์ (OWN-2, OWN-3)**
- [X] เพิ่ม `deleted_at/deleted_by`; ฟังก์ชัน `delete_product`, `restore_product`, `list_deleted_products()` (พร้อมสรุปประวัติขาย: จำนวนที่ขายได้, รายได้ จาก `order_items` ที่ออเดอร์ไม่ถูกยกเลิก)
- [X] ทุกคิวรีฝั่งผู้ซื้อ/ค้นหา/แนะนำ/เปรียบเทียบ ต้องกัน `deleted_at IS NOT NULL`; ตะกร้าที่มีสินค้านี้ → แจ้ง "สินค้านี้ไม่มีจำหน่ายแล้ว" ผ่าน `problem` ใน `get_cart`; wishlist ซ่อน
- [X] คงออเดอร์เก่าไว้ (ข้อมูลสำเนาใน `order_items` อยู่แล้ว)
- [X] `delete_category/brand`, `restore_*`: ถ้ายังมีสินค้าที่ไม่ถูกลบอยู่ ให้ปฏิเสธพร้อมจำนวน หรือยอมรับ `cascade=True` ที่ลบสินค้าเหล่านั้นด้วย (ต้องยืนยันจาก UI)
- [X] สิทธิ์: เฉพาะ owner (`PRODUCT_DELETE`, `CATEGORY_MANAGE`, `BRAND_MANAGE`)

**2B หมวด↔แบรนด์ (OWN-3)**
- [X] `category_brands`; `save_category(name, ..., brand_ids=None, all_brands=False)` และ `save_brand(..., category_ids=None)`; แบรนด์ใหม่ที่เพิ่มภายหลังเชื่อมกับหมวดที่ `all_brands=1` อัตโนมัติ
- [X] `list_brands(category_id=None)` กรองแบรนด์ตามหมวด; `save_product` ตรวจว่าแบรนด์อยู่ในหมวดนั้น
- [X] migrate ข้อมูลเดิม: สร้างความสัมพันธ์จาก (category_id, brand_id) ที่มีสินค้าอยู่แล้ว

**2C คูปอง (OWN-1, D9, D10)**
- [X] คงฟังก์ชันเดิม (`create_coupon`, `update_coupon`, `toggle_coupon`, `validate_coupon`); เพิ่มฟิลด์ใหม่ (เพดานส่วนลด `max_discount`, `starts_at`, `claimable`) และให้ `update_coupon` แก้เงื่อนไขได้ครบ
- [X] `coupon_rules` + `create_rule/update_rule/toggle_rule/list_rules` (owner)
- [X] `issue_reward_coupons(order_id, conn)` เรียกใน `order_service.complete_delivery`/`apply_status_change` ตอนสถานะเป็น `completed` (ใน transaction เดียวกัน): ถ้ายอดสุทธิของออเดอร์ ≥ `trigger_min_spend` ของกฎที่เปิดอยู่ → สร้างคูปองส่วนตัว (`owner_user_id`, `max_uses=1`, หมดอายุ = วันนี้ + `reward_valid_days`, โค้ดสุ่มเช่น `RWD-XXXXXX`) + แจ้งเตือนผู้ซื้อ; อาศัย unique index กันออกซ้ำ
- [X] `validate_coupon` ตรวจว่าคูปองส่วนตัวใช้ได้เฉพาะ `owner_user_id`; `list_my_coupons(user_id)`, `claim_coupon(user_id, coupon_id)`
- [X] เทสต์: ซื้อ 3,000 → ได้คูปอง 300 (ขั้นต่ำ 1,000); ซื้อ 2,999 → ไม่ได้; ออเดอร์เดียวไม่ออกซ้ำ; ยกเลิกออเดอร์ไม่ได้คูปอง; คนอื่นใช้คูปองไม่ได้

**2D ข้อมูลร้าน/ช่องทางติดต่อ (OWN-6)**
- [X] `settings_service.get_contact_info()` (สาธารณะ — ผู้เยี่ยมชมก็ดูได้) และ `update_contact_info(values)` (owner) พร้อมตรวจรูปแบบ (หัวข้อ 5.3)
- [X] **E1/E3 (v6):** `get_contact_info()`/`update_contact_info()` รองรับคีย์เพิ่ม `shop_address`, `shop_hours`, `maps_url`, `line_oa_url`, `tiktok_name`, `tiktok_url` (ว่างได้ทุกช่อง = ไม่แสดงในหน้าเว็บ; ลิงก์ต้อง `https://`; ข้อความ ≤ 300 ตัวอักษร); เทสต์ใน `test_contact.py` (ลิงก์ผิด/`javascript:` ถูกปฏิเสธ, ค่าว่างผ่าน)

**2E ส่งออก Excel + รายจ่าย (OWN-5, D5, D8)**
- [X] `expense_service`: เพิ่ม/แก้/ลบ/รายการตามช่วงวันที่ (owner)
- [X] `export_service.export_range(start_date, end_date, path)` สร้าง `.xlsx` ด้วย `openpyxl` หลายชีต: **สรุป** (รายรับ, รายจ่าย, กำไรขั้นต้น, จำนวนออเดอร์), **ออเดอร์**, **รายการสินค้าที่ขาย** (วันที่, ออเดอร์, ลูกค้า, สินค้า, จำนวน, ราคาต่อชิ้น, รวม), **ลูกค้า** (ชื่อ, เบอร์, จำนวนออเดอร์, ยอดรวม), **รายจ่าย**, **สต็อกคงเหลือ**
- [X] นับเป็นรายรับเฉพาะออเดอร์สถานะ `paid/shipped/completed`; ระบุเกณฑ์ไว้ในชีตสรุป
- [X] ตัวช่วยช่วงเวลา: `range_last_12_months()`, `range_calendar_year(year)` (1 ม.ค.–31 ธ.ค.), `range_month(year, month)`, ช่วงกำหนดเอง
- [X] ส่งออกอัตโนมัติรายเดือน `auto_export_previous_month()` → `data/exports/monthly/YYYY-MM.xlsx`; ใช้ `settings.last_auto_export` กันซ้ำและ **ย้อนส่งออกเดือนที่พลาด** ถ้าเซิร์ฟเวอร์ปิดอยู่ตอนต้นเดือน
- [X] ห้ามใส่รหัสผ่าน/hash/ข้อมูลบัตรลงไฟล์; เบอร์/ที่อยู่ลูกค้าเป็นข้อมูลส่วนบุคคล เก็บไฟล์ในโฟลเดอร์ที่ไม่เปิดสาธารณะ
- [X] เทสต์: ยอดรวมในไฟล์ตรงกับ `get_dashboard_stats`; ช่วงวันที่ขอบเขตถูกต้อง (รวมวันสุดท้าย 23:59:59)

**2F ติดต่อเจ้าของ (ADM-1)**
- [X] `contact_service.send_urgent_to_owner(admin_user, subject, message)` (เฉพาะ admin/owner): จำกัด 5 ครั้ง/ชั่วโมง, ตัดความยาว, ส่งผ่าน `email_service` ไปที่ `OWNER_EMAIL` ตั้ง `Reply-To` = อีเมลแอดมิน และใส่ชื่อแอดมินในเนื้อหา; บันทึก `staff_messages`

**2G เปรียบเทียบ 2–5 ไม้ (BUY-5)**
- [X] แก้ `compare_products` เป็น 2–5 (ข้อความ `ValueError` ด้วย); ตั้งค่าคงที่ `MAX_COMPARE = 5` ใน `core/constants.py` ใช้ร่วมกับ UI
**2H ใบเสร็จอิเล็กทรอนิกส์ทางอีเมลหลังตรวจสลิปผ่าน (SYS-3, D12)**
- ความหมาย (ยืนยันแล้ว v4): "สลิปออนไลน์" = ใบเสร็จ/ยืนยันการชำระเงินที่ร้านออกให้ **เป็นข้อความในตัวอีเมล และแนบ .pdf ด้วยถ้าสร้างได้** ส่ง **จากอีเมลของร้านในชื่อร้าน** ไปที่อีเมลผู้ซื้อ — **ไม่ใช่** รูปสลิปโอนที่ผู้ซื้อแนบ (ห้ามส่งรูปสลิปโอนกลับ) · ส่งอัตโนมัติจากระบบ ผ่านบัญชีอีเมลของร้านเท่านั้น (ส่งในนามอีเมลของผู้ใช้/แอดมินไม่ได้ ดู D12)
- [X] ตาราง `email_outbox` (หัวข้อ 5.2) + repo
- [X] `queue_receipt_email(order_id)` เรียกผ่านตัวห่อ `verify_payment_and_notify` (ภาคผนวก D.3) ซึ่งเรียก `verify_payment` เดิมก่อน แล้วค่อยเข้าคิว **หลัง commit สำเร็จ** (นอก transaction; อีเมลล้มต้องไม่ทำให้การยืนยันสลิปล้ม): โหลดออเดอร์ + อีเมลผู้ซื้อ (`email_verified=1`) → สร้างเนื้อหา → สร้าง PDF ด้วย `receipt_service.generate_receipt(order_id)` → ใส่คิว → ส่งใน thread แยก
- [X] เนื้ออีเมล (ไทย, HTML + text สำรอง): หัวข้อ "ยืนยันการชำระเงินออเดอร์ #เลข — ชื่อร้าน", เลขออเดอร์, วันเวลาที่ตรวจสลิปผ่าน, รายการสินค้า (ชื่อ/ตัวเลือก/จำนวน/ราคา), ยอดสินค้า, ส่วนลด, ค่าส่ง, **ยอดรวม**, ที่อยู่จัดส่ง, ขั้นตอนต่อไป, ช่องทางติดต่อร้านจาก `get_contact_info()`, แนบ `receipt_<เลข>.pdf` (ถ้าสร้างได้; ถ้าไม่ได้ ตัวอีเมลยังเป็นสลิปครบถ้วนในตัวเอง)
- [X] ผู้ส่ง = บัญชี SMTP ของร้าน (D12) ชื่อผู้ส่ง = ชื่อร้าน, `Reply-To` = `shop_email`; ส่งถึง **อีเมลของผู้ซื้อเจ้าของออเดอร์เท่านั้น** (ห้ามผู้รับอื่น/BCC)
- [X] ส่งเฉพาะเมื่อ `verify_payment` ผ่าน (`reject_payment` ไม่ส่ง); กันส่งซ้ำด้วย unique index ต่อออเดอร์; สร้าง PDF ไม่ได้ (เช่น ไม่มีฟอนต์ไทย) → ส่ง HTML ไม่มีไฟล์แนบ + บันทึก `last_error`
- [X] ส่งล้มเหลว → `status='failed'` + ลองใหม่อัตโนมัติสูงสุด 3 ครั้ง (เว้น 5 นาที / 30 นาที / 2 ชม.) โดยงานตั้งเวลา; `resend_receipt_email(order_id)` (admin/owner) ส่งใหม่ด้วยมือ; `get_receipt_email_status(order_id)` คืน `sent/failed/pending/none` + เวลา
- [X] แจ้งเตือนในแอปถึงผู้ซื้อ ("ส่งใบเสร็จไปที่อีเมลแล้ว") ผ่าน `notification_service`; เปิด/ปิดด้วย `RECEIPT_EMAIL_ENABLED`
- [X] เทสต์ (mock SMTP): ตรวจผ่าน → มีแถว outbox + ส่งถึงอีเมลผู้ซื้อ + มี PDF แนบ; ปฏิเสธสลิป → ไม่ส่ง; ตรวจซ้ำ → ไม่ส่งซ้ำ; SMTP พัง → ยืนยันสลิปยังสำเร็จ, สถานะ failed แล้ว retry ผ่าน; ผู้ซื้อไม่มีอีเมลที่ยืนยัน → ข้ามอย่างปลอดภัย
**2I จัดการแบนเนอร์ (E2)**
- [X] ตาราง `banners` (หัวข้อ 5.2) + `repo_banners.py`
- [X] `banner_service`: `list_active_banners()` (สาธารณะ เรียงตาม `sort_order`), `list_banners()` (owner), `add_banner(src_path, link_url=None, alt_text=None)` (ใช้ `image_utils.save_upload` → `config.BANNER_IMAGES_DIR`; `.jpg/.png/.webp` ≤ 5MB ตามค่าเดิม), `update_banner(id, link_url, alt_text)`, `reorder_banners(ids)`, `set_banner_active(id, bool)`, `delete_banner(id)` (ลบแถว+ไฟล์) — **เฉพาะ owner** (`BANNER_MANAGE`); ลิงก์รับเฉพาะ `https://` หรือ path ภายในที่ขึ้นต้น `/` (กัน `javascript:`)
- [X] เปิดแสดงได้สูงสุด 10 ภาพ (เกิน = `ValueError`); ต่ำกว่า 7 ภาพ = คืนคำเตือนให้ UI แสดง ไม่บล็อก
- [X] เทสต์ `test_banners.py`: admin ทำไม่ได้ (PermissionError), ลิงก์ผิด, เกิน 10, เรียงลำดับ, ซ่อนแล้วไม่ขึ้นฝั่งสาธารณะ, ลบแล้วไฟล์หาย

**2J บันทึกกิจกรรม (E4)**
- [X] ตาราง `audit_log` + `repo_audit.py`; `audit_service.log(action, target_type=None, target_id=None, detail=None, conn=None)` (ใช้ภายใน ไม่ตรวจสิทธิ์; อ่านผู้กระทำจาก Session; `detail` เป็น dict → JSON; **ตัด key ที่ชื่อมี password/otp/token/secret ออกอัตโนมัติ**) · `audit_service.list_logs(filters=None, page=1, page_size=30)` (owner เท่านั้น; กรองตามผู้กระทำ/action/ช่วงวันที่)
- [X] จุดที่ต้องบันทึก (เรียกใน transaction เดียวกับการกระทำเมื่อมี `conn`): ลบ/กู้คืนสินค้า-หมวด-แบรนด์ · แก้ราคา/โปรสินค้า · สร้าง/แก้/เปิดปิดคูปองและกฎซื้อครบรับคูปอง · เพิ่ม/ระงับ/รีเซ็ตรหัส/เตะเซสชัน staff (`staff_service`) · แก้ settings (ชื่อคีย์ + ค่าเก่า→ใหม่ ยกเว้นคีย์ลับ) · แบนเนอร์ · ส่งออกข้อมูล · ยืนยัน/ปฏิเสธสลิป · แอดมินยกเลิกออเดอร์
- [X] แบบเพิ่มอย่างเดียว: ห้ามมีฟังก์ชันแก้/ลบแถว; เก็บตลอด
- [X] เทสต์ `test_audit.py`: แต่ละจุดบันทึกจริง, ไม่มีรหัสผ่านในรายละเอียด, admin เรียก `list_logs` ไม่ได้, rollback ของการกระทำ → ไม่มีแถว audit ค้าง

**2K อีเมลแจ้งจัดส่ง + เลขพัสดุ (E5)**
- [X] `email_outbox` รองรับ `kind='shipped'` (หัวข้อ 5.2); `email_outbox_service.queue_shipped_email(order_id)` สร้างอีเมล HTML+text (ไม่แนบ PDF): "ออเดอร์ #เลข จัดส่งแล้ว" + ขนส่ง + เลขพัสดุ + รายการสินค้าย่อ + ที่อยู่ปลายทาง + ช่องทางติดต่อร้าน; ผู้รับ = อีเมลผู้ซื้อที่ `email_verified=1` เท่านั้น (ห้ามผู้รับอื่น/BCC); **ไม่เดา URL ติดตามของขนส่ง** แสดงเลขพัสดุเป็นข้อความ
- [X] ตัวห่อ `shipping_service.ship_order_and_notify(order_id, carrier, tracking_no)` เรียก `ship_order` เดิมก่อน แล้วเข้าคิว **หลัง commit** (นอก transaction เหมือนภาคผนวก D.3; อีเมลล้มไม่ทำให้การจัดส่งล้ม); UI/route เรียกตัวห่อนี้ — เทสต์เดิมที่เรียก `ship_order` ตรงๆ ไม่เปลี่ยน
- [X] กติกาเดียวกับใบเสร็จ: ส่งครั้งเดียวต่อออเดอร์ (unique index), retry 3 ครั้ง, `resend_shipped_email(order_id)` (admin/owner), เปิดปิดด้วย `SHIPPED_EMAIL_ENABLED`, แจ้งเตือนในแอป "ส่งเลขพัสดุไปที่อีเมลแล้ว"
- [X] ค่าเริ่มต้นที่เลือก: แก้เลขพัสดุภายหลัง (`update_tracking`) **ไม่ส่งซ้ำอัตโนมัติ** ให้แอดมินกด "ส่งอีเมลเลขพัสดุอีกครั้ง" (ส่งด้วยข้อมูลล่าสุด)
- [X] เทสต์ `test_shipped_email.py` (mock SMTP): จัดส่ง → มีแถว outbox + ส่งถึงผู้ซื้อ · ซ้ำ → ไม่ส่งซ้ำ · SMTP พัง → การจัดส่งยังสำเร็จ + retry · ผู้ซื้อไม่มีอีเมลยืนยัน → ข้ามอย่างปลอดภัย · สวิตช์ปิด → ไม่ส่ง

**2L อีเมลสรุปสต็อกต่ำถึงเจ้าของ (E6)**
- [X] `email_outbox_service.send_low_stock_digest()`: ใช้ `product_service.get_low_stock_products()`; ไม่มีรายการ → ไม่ส่ง; ส่ง **วันละไม่เกิน 1 ฉบับ** (กันซ้ำด้วย `settings.last_low_stock_email`) ถึง `OWNER_EMAIL` เท่านั้น (ชื่อสินค้า/ตัวเลือก/สต็อกคงเหลือ/เกณฑ์ — **ไม่มีข้อมูลลูกค้า**); ผ่าน outbox `kind='low_stock'` (`related_order_id` = NULL) + retry; เปิดปิดด้วย `LOW_STOCK_EMAIL_ENABLED`; ตัวตั้งเวลาใน `run_web.py` (Phase 4) เรียกวันละครั้ง
- [X] ค่าเริ่มต้นที่เลือก: สรุปรายวัน ไม่ส่งทุกครั้งที่สต็อกข้ามเกณฑ์ (กันอีเมลท่วม; แจ้งเตือนในแอปแบบเดิมยังทำงานตามปกติ)
- [X] เทสต์ `test_low_stock_email.py`: ไม่มีของใกล้หมด = ไม่ส่ง · มี = ส่งครั้งเดียวต่อวัน · สวิตช์ปิด = ไม่ส่ง · ไม่มี `OWNER_EMAIL` = ข้ามอย่างปลอดภัย

**2M ส่งออกไป Google Sheets (E7)**
- [X] แยก `export_service.build_export_data(start_date, end_date) -> dict` (ชื่อชีต → แถว) ให้ `export_range` (.xlsx) และ Sheets ใช้ร่วมกัน (ยอดต้องตรงกัน)
- [X] `export_service.sync_to_google_sheets(start_date, end_date, include_personal=False)` (owner เท่านั้น): `gspread` + service account นำเข้าแบบ lazy (ไม่ติดตั้ง = `ValueError("ยังไม่ได้ติดตั้งส่วนเสริม Google Sheets")`); อ่าน `GOOGLE_SERVICE_ACCOUNT_FILE` / `GOOGLE_SHEET_ID` จาก `.env` (ไม่ตั้ง = `ValueError("ยังไม่ได้ตั้งค่า Google Sheets")`); สร้าง/ล้างแท็บตามช่วงเวลา (เช่น `2026-09`) แล้วเขียนข้อมูล; ผลลัพธ์บอกจำนวนแถว
- [X] ค่าเริ่มต้นที่เลือก: `include_personal=False` = **ตัดเบอร์โทร/ที่อยู่ลูกค้าออก** (เหลือชื่อ+ยอด) เพราะข้อมูลขึ้นคลาวด์บุคคลที่สาม; ส่งเต็มได้เมื่อ owner ติ๊กยืนยันใน UI
- [X] .xlsx ยังเป็นวิธีหลัก (D8); Sheets เป็นปุ่มกดเอง ไม่ทำงานอัตโนมัติ; ไฟล์กุญแจอยู่ใน `secrets/` (ไม่ commit/ไม่ใส่ซิป)
- [X] เทสต์ `test_google_sheets.py` (mock gspread): ไม่ได้ตั้งค่า · ไม่ได้ติดตั้งไลบรารี · ข้อมูลตรงกับ xlsx · ตัด PII ตามค่าเริ่มต้น · admin เรียกไม่ได้
- [X] **หมายเหตุสำหรับเจ้าของโปรเจกต์:** ก่อนใช้จริงต้องสร้าง service account ใน Google Cloud + เปิด Google Sheets API + แชร์สเปรดชีตให้อีเมลของ service account (AI ทดสอบกับของจริงไม่ได้ ใช้ mock)

**2N ค้นหาแนะนำ + สินค้าที่ดูล่าสุด (E8)**
- [X] `product_service.suggest_products(query, limit=8)` (สาธารณะ): ขั้นต่ำ 2 ตัวอักษร ตัดที่ 50; คืน `[{type: product|brand|category, id, label, price?, image_path?}]` เฉพาะที่เปิดขายและไม่ถูกลบ; ใช้ `like_pattern` กัน wildcard; ไม่คืนข้อมูลผู้ใช้
- [X] `product_service.get_cards_by_ids(ids, limit=10)`: รับ id สูงสุด 20 ตัว ตัดซ้ำ คงลำดับ คืนการ์ดรูปแบบเดียวกับ `search_products` เฉพาะที่ยังเปิดขาย — ใช้กับ "สินค้าที่ดูล่าสุด" (ฝั่งเบราว์เซอร์เก็บ id ใน `localStorage` ไม่เก็บใน DB)
- [X] เทสต์ `test_suggest.py`: ต่ำกว่า 2 ตัวอักษรคืนว่าง · สินค้าที่ลบ/ปิดไม่ขึ้น · `%`/`_` ในคำค้นไม่ทำงานเป็น wildcard · id ซ้ำ/ไม่มีจริงถูกข้าม · ลำดับคงเดิม

- [X] **เสร็จเมื่อ:** เทสต์ของ 2A–2N ผ่านทั้งหมด และเทสต์เดิมไม่พัง

### Phase 3 — AI แชทอัปเกรด (backend) ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | `services/ai_service.py` · `services/chat_service.py` · `services/product_service.py` · `database/repo_chat.py` · `services/settings_service.py (ถ้าเพิ่มคีย์)` · [ใหม่] services/ai_guard.py · [ใหม่] tests/test_ai_guard.py, test_chat_quick.py |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `database/repo_products.py` · `database/repo_users.py (ออนไลน์ของ staff)` · `database/repo_settings.py` · `core/constants.py` · `core/permissions.py` · `config.py` · `ui/pages/buyer/chat.py` · `ui/pages/buyer/racket_finder.py` · `ui/pages/admin/chat.py` · `tests/test_services_basic.py (ส่วนแชท/AI)` |

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** SYS-2a–2d
- **ต้องมีก่อน:** Phase 2G, 2A (สินค้าที่ลบแล้วห้ามถูกแนะนำ)
- **ไฟล์:** `services/ai_service.py`, `services/chat_service.py`, `services/ai_guard.py` (ใหม่), `services/product_service.py` (best sellers + recommend), `database/repo_chat.py`

**3A ตัวกรองคำถาม (guard) ก่อนเรียก Gemini (SYS-2a)**
- [X] `ai_guard.classify(text) → "allow" | "block" | "uncertain"`
  - ตัดข้อความยาวเกิน ~300 ตัวอักษร, ล้างช่องว่าง/ตัวอักษรควบคุม
  - **allow:** มีคำเกี่ยวกับร้าน เช่น แบด/ไม้/เอ็น/ลูก/รองเท้า/กระเป๋า/ราคา/โปร/คูปอง/ส่ง/ชำระ/สลิป/ออเดอร์/สต็อก/รับประกัน + ชื่อแบรนด์/หมวด/สินค้าที่โหลดจาก DB (แคชไว้)
  - **block:** รูปแบบนอกขอบเขต เช่น วันนี้วันอะไร, อากาศ, ราคาทอง/หุ้น, หวย, การเมือง, ให้เขียนโค้ด/การบ้าน, และข้อความสั่งแทรกคำสั่ง ("ignore previous", "ลืมคำสั่งก่อนหน้า", "system prompt", ขอ API key)
  - **uncertain:** ส่งต่อให้ Gemini แต่บังคับด้วย system prompt ว่าตอบเฉพาะเรื่องร้าน ถ้านอกขอบเขตให้ตอบสัญลักษณ์พิเศษ `__OUT_OF_SCOPE__` แล้วระบบแทนที่เป็นข้อความคงที่
- [X] ข้อความปฏิเสธคงที่: "ขออภัยครับ ระบบไม่สามารถตอบคำถามเหล่านี้ได้ เนื่องจากไม่ได้อยู่ในขอบเขตการตอบคำถามของทางร้าน" + แสดงปุ่มคำถามสำเร็จรูปต่อท้าย (3B)
- [X] จำกัดอัตรา: ต่อผู้ใช้ ≤ 10 ข้อความ/นาที และ ≤ 100/วัน; ข้อความที่ถูก block **ไม่เสียโควตา Gemini**
- [X] ไม่ส่งข้อมูลส่วนตัวของผู้ใช้อื่น/ข้อมูลหลังบ้านให้ AI; ส่งเฉพาะข้อมูลสินค้าสาธารณะที่ระบบเลือกแล้ว
- [X] เทสต์ guard: คำถามนอกเรื่อง 10+ แบบ, คำถามร้าน 10+ แบบ, ความพยายามแทรกคำสั่ง

**3B ปุ่มคำถามสำเร็จรูป (SYS-2b)**
- [X] `chat_service.get_quick_replies()` คืนรายการ `{id, label}` เช่น แนะนำไม้ที่ขายดีที่สุด / สินค้าลดราคาตอนนี้ / ค่าส่งและส่งฟรีเมื่อไหร่ / วิธีชำระเงิน / ติดตามพัสดุ / ติดต่อแอดมิน
- [X] `chat_service.answer_quick_reply(customer_id, reply_id)`: ตอบจากข้อมูลจริง **ไม่ผ่าน AI** (เร็ว ถูกต้อง ฟรี) — `product_service.get_best_sellers(limit=5)` (รวมจำนวนจาก `order_items` ของออเดอร์ที่ไม่ถูกยกเลิก, เฉพาะไม้/สินค้าที่ยังขายอยู่), สินค้าลดราคา (`is_on_sale`), ค่าส่ง/ยอดส่งฟรีจาก `settings_service`
- [X] บันทึกลง `chat_messages` เป็นข้อความ `sender_type='ai'` (หรือ 'system' ถ้าจะเพิ่ม) เพื่อให้แชทต่อเนื่อง

**3C ปุ่ม "ถาม AI โดยเฉพาะ" (SYS-2c)**
- [X] `chat_service.send_message(customer_id, text, background=True, force_ai=False)`: ถ้า `force_ai=True` ข้ามเงื่อนไข `should_ai_reply()` (ปกติ AI ไม่ตอบเมื่อมีแอดมินออนไลน์) แต่ยังผ่าน guard + rate limit; ข้อความตอบกลับติดป้าย AI ให้ลูกค้าเห็นว่าเป็น AI
- [X] เทสต์: แอดมินออนไลน์ + `force_ai=True` → AI ตอบ; `force_ai=False` → AI ไม่ตอบ (พฤติกรรมเดิม)

**3D ตัวแนะนำไม้จากสไตล์การเล่น (SYS-2d)**
- [X] ขยาย `product_service.recommend_rackets(level, style, budget, limit, flex=None, balance=None, weight_class=None)` ใช้คอลัมน์ `flex/balance/level/weight_class` ที่มีอยู่ ให้คะแนนความเหมาะสม คืน 3 ไม้ที่เหมาะสุด (เฉพาะไม้ที่เปิดขาย ไม่ถูกลบ มีสต็อก)
- [X] `chat_service.recommend_from_form(customer_id, answers)`: ตัวเลือกฟอร์ม — ระดับฝีมือ (เริ่มต้น/กลาง/สูง), สไตล์ (บุก/รับ/ผสม), ก้าน (อ่อน/กลาง/แข็ง), จุดสมดุล (หนักหัว/สมดุล/เบาหัว), งบประมาณ
- [X] ให้ AI เขียนคำอธิบายสั้นๆ ต่อไม้ **โดยส่งรายการไม้ที่ระบบเลือกเข้าไปและสั่งห้ามพูดถึงสินค้าอื่น**; ถ้า AI ใช้ไม่ได้ ใช้ข้อความจากแม่แบบ (ไม่ล้ม)
- [X] เทสต์: ผลลัพธ์เป็นสินค้าจริงในร้านเท่านั้น, ไม่เกิน 3, ไม่มีสินค้าหมด/ถูกลบ
- [X] **เสร็จเมื่อ:** เทสต์ guard + quick reply + force_ai + recommend ผ่าน; ไม่มีคีย์ Gemini ระบบยังตอบด้วยข้อความสำรองได้

### Phase 4 — โครงเว็บ + ระบบดีไซน์ + หน้าล็อกอิน/สมัคร ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | `core/session.py` · `utils/image_utils.py` · `config.py` · `requirements.txt` · [ใหม่] web/ (app.py, auth.py, routes_buyer.py ส่วนสาธารณะ, templates/auth/*, templates/base.html, static/css/*, static/js/*) · [ใหม่] run_web.py · [ใหม่] tests/test_web_auth.py |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `main.py` · `ui/app.py (ดูงานที่ทำตอนเปิด/ปิดแอป)` · `ui/theme.py (สีเดิม)` · `ui/pages/buyer/login.py` · `ui/pages/buyer/register.py` · `services/auth_service.py` · `services/account_service.py` · `services/settings_service.py` · `services/product_service.py (ข้อมูลภาพสินค้าตัวอย่างหน้า login)` · `services/order_service.py (auto_cancel_unpaid)` · `database/db.py` · `database/repo_users.py, repo_sessions.py, repo_otp.py (จาก Phase 1)` · `utils/backup.py` · `assets/images/ (เฉพาะ banners/ และตัวอย่างสินค้า 5–10 รูป)` · `tests/test_services_basic.py (ตรวจว่าเปลี่ยน session แล้วไม่พัง)` |

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** UX-1, UX-2, UX-5, UX-6, SYS-1 (หน้าจอ), BUY-1, BUY-2 (กั้นผู้เยี่ยมชม)
- **ต้องมีก่อน:** Phase 1 (อย่างน้อย); Phase 2–3 ทำคู่ขนานได้
- **ไฟล์:** `core/session.py`, `utils/image_utils.py`, `web/*` (ใหม่), `run_web.py`
- [X] แก้ `core/session.py` เป็น `contextvars` และรันเทสต์ซ้ำ (ดูภาคผนวก D.1); ย้าย `import customtkinter` ใน `utils/image_utils.py` เป็น lazy
- [X] `web/app.py` (create_app, error handlers: `ValueError`→ข้อความ, `PermissionError`→403), `web/auth.py` (อ่านเซสชันจากตาราง `sessions`, `login_required`, `role_required`)
- [X] `run_web.py`: `init_db` → seed ถ้าว่าง → `clear_all_online` → `auto_cancel_unpaid` → ตั้งเวลา (ยกเลิกออเดอร์ค้างชำระ, สำรอง DB, ส่งออกรายเดือน, retry อีเมล, สรุปสต็อกต่ำรายวัน — E6)
- [X] `static/css/theme.css|base.css|components.css` จากภาคผนวก A ตามหัวข้อ 6; `base.html` (viewport, topbar, bottom-nav, flash messages)
- [X] route สื่อ: `/media/<path>` เฉพาะ `assets/images/**`; **สลิป/ใบเสร็จผ่าน route ตรวจสิทธิ์เท่านั้น**
- [X] หน้า `login` / `register` / `register/verify` / `forgot` / `forgot/verify` ตามภาคผนวก B.4 (เลย์เอาต์แบ่งสองฝั่ง, ซ้ายเหลืองมีภาพสินค้าตัวอย่างเปลี่ยนเรื่อยๆ, หัวข้อเปลี่ยนตามสถานการณ์); ล็อกอิน = อีเมล+รหัสผ่านไม่มี OTP; มีลิงก์ "ลืมรหัสผ่าน?" ใต้ปุ่มเข้าสู่ระบบ; **สมัครสำเร็จ → พากลับหน้า login พร้อมข้อความ "สมัครสำเร็จ เข้าสู่ระบบได้เลย" (ไม่ล็อกอินให้อัตโนมัติ)**; รีเซ็ตรหัสสำเร็จ → กลับหน้า login เช่นกัน; ช่องที่อยู่ตอนสมัคร (ชื่อผู้รับ, เบอร์, ที่อยู่, อำเภอ, จังหวัด, รหัสไปรษณีย์ ให้ตรงกับตาราง `addresses`)
- [X] หน้า `/forgot/staff` (สาธารณะ): แสดงข้อความ "พนักงานลืมรหัสผ่าน ให้ติดต่อเจ้าของร้านเพื่อรีเซ็ต" + ช่องทางติดต่อ Owner จาก `get_contact_info()` (เบอร์ปุ่มโทร/คัดลอก, อีเมล, FB, LINE, IG) — **ห้ามมีช่องกรอกอีเมลหรือส่ง OTP** ในหน้านี้; ลิงก์เข้าจากหน้า login
- [X] `GET /api/login-showcase` คืนรายการภาพสินค้าตัวอย่าง (สินค้าลดราคา/ขายดีที่เปิดขาย ไม่เกิน 8 รายการ: ชื่อ ราคา รูป) สำหรับแผงซ้าย; ไม่มีรูป/ไม่มีสินค้า → ตัวแทนพื้นไล่สี; เป็นข้อมูลสาธารณะเท่านั้น (ห้ามส่งข้อมูลผู้ใช้)
- [X] ผู้เยี่ยมชม: ปุ่มที่ต้องล็อกอิน → โมดัล "กรุณาเข้าสู่ระบบ" + `?next=` กลับมาหน้าเดิมหลังล็อกอิน; **บังคับที่ฝั่งเซิร์ฟเวอร์ด้วย `login_required`** (หน้าแรก/หมวด/สินค้า/ค้นหา/เปรียบเทียบ/ตัวช่วยเลือกไม้/ติดต่อเรา = สาธารณะ; ตะกร้า/หัวใจ/ชำระ/ออเดอร์/แชท/โปรไฟล์/รับคูปอง/รีวิว = ต้องล็อกอิน)
- [X] ปุ่มสลับธีมทุกหน้า; ตั้งค่า cookie `httponly/samesite/secure`
- [X] บล็อกเส้นทาง `/admin/*` จากมือถือ (D2) + หน้าแจ้ง "ใช้งานบนคอมพิวเตอร์"
- [X] **เสร็จเมื่อ:** สมัคร→รับ OTP→**กลับหน้าล็อกอิน**→เข้าสู่ระบบได้จริงบนมือถือและ PC; ล็อกอินครั้งต่อไปไม่ถูกขอ OTP; ลืมรหัสผ่าน→OTP→ตั้งรหัสใหม่→ล็อกอินด้วยรหัสใหม่ได้; 2 เบราว์เซอร์คนละบัญชีไม่ปนกัน; ผู้เยี่ยมชมเข้า `/cart` แล้วถูกพาไปล็อกอิน

### Phase 5 — ฝั่งผู้ซื้อ (หน้าจอทั้งหมด) ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | [ใหม่] web/routes_buyer.py, routes_api.py · [ใหม่] web/templates/buyer/*, partials/* · [ใหม่] web/static/js/* (แบนเนอร์, ตะกร้า, ตัวกรอง) · `services/review_service.py และ services/order_service.py (เฉพาะเพิ่มฟังก์ชัน "รอรีวิว")` |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `web/ ทั้งหมดจาก Phase 4` · `services/product_service.py` · `services/cart_service.py` · `services/order_service.py` · `services/payment_service.py` · `services/coupon_service.py` · `services/review_service.py` · `services/account_service.py` · `services/notification_service.py` · `services/shipping_service.py` · `services/receipt_service.py` · `services/settings_service.py` · `services/banner_service.py` · `utils/formatters.py` · `utils/promptpay.py` · `utils/image_utils.py` · `utils/validators.py` · `core/constants.py (มี ORDER_STATUS_DISPLAY_ORDER จาก Phase 2)` · `ui/pages/buyer/*.py (ฟีเจอร์เดิมที่ต้องพอร์ต)` · `ui/components/product_card.py, order_timeline.py, payment_qr.py, rating.py` · `assets/images/ (ตัวอย่างสินค้า/แบนเนอร์)` |

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** UX-3, UX-4, UX-7, BUY-2, BUY-3, BUY-4, BUY-5, E1, E2, E3, E8
- **ต้องมีก่อน:** Phase 4 (+ Phase 2 สำหรับคูปอง/soft delete/เปรียบเทียบ)
- **ไฟล์:** `web/routes_buyer.py`, `web/templates/buyer/*`, `web/templates/partials/*`, `web/static/js/*`
- สร้างหน้าเป็น Jinja templates ตามโครงในภาคผนวก B โดยเรียก service จริง (แมปหน้า↔service ดูภาคผนวก E)

**5A หน้าแรก (UX-3, UX-7)**
- [X] แบนเนอร์ (E2): อ่านจาก `banner_service.list_active_banners()` (7–10 ภาพ ตามลำดับที่เจ้าของจัด; คลิกแบนเนอร์ไป `link_url` ถ้ามี); ถ้า DB ไม่มี → อ่านรูปจาก `assets/images/banners/` เรียงชื่อ; ไม่มีเลย → ตัวแทนพื้นไล่สี; JS เลื่อนอัตโนมัติ/ปัด/จุด
- [X] Flash Sale: สินค้าที่ `is_on_sale` (+ นับถอยหลังจาก `sale_ends_at` ที่ใกล้สุด), แถวเลื่อนในมือถือ
- [X] หมวดหมู่/แบรนด์: จาก `list_categories()`/`list_brands()` (กรองที่ลบแล้ว) ปุ่มเหลืองเลื่อนแนวนอน; คลิกไปหน้าหมวด
- [X] สินค้าแนะนำ: ตาม `search_products` เรียงตามที่ตกลง (ขายดี/ใหม่) 15 ชิ้น + "ดูทั้งหมด"
- [X] ส่วนท้าย + หน้า `/contact` (E1/E3): ข้อมูลจาก `get_contact_info()` — เบอร์, อีเมล, FB, LINE, IG, **ที่อยู่ร้าน, เวลาเปิดปิด, ปุ่ม "นำทาง" ไป `maps_url`, LINE Official, TikTok** (ช่องที่ว่างไม่แสดง)
- [X] ป้ายคูปอง/โปรบนหน้าแรกให้ผู้เยี่ยมชมเห็น แต่กด "รับ" ต้องล็อกอิน (BUY-1/2, D10)

**5B หมวดหมู่/ค้นหา/สินค้า (UX-4)**
- [X] หน้า category/search: ตัวกรอง (bottom sheet บนมือถือ), เรียง, แบ่งหน้า, สเกเลตันตอนโหลด, สถานะว่าง
- [X] หน้าสินค้า: ชื่อ ~28–32px หนา + ราคา ~36–40px หนา สีแดง (ราคาเดิมขีดฆ่า + ป้าย −%) เด่นสุด; ดาว/จำนวนรีวิว/สเปก/ชิป เล็กและจาง; ตัวเลือก (สี/ด้าม/เอ็น/ไซซ์) เป็นปุ่มเลือก; แกลเลอรีรูปปัดได้; แถบสั่งซื้อติดล่างบนมือถือ; รีวิวอยู่ล่างลงมา; สินค้าซื้อคู่
- [X] เปรียบเทียบ 2–5 ไม้ (ตารางเลื่อนแนวนอน คอลัมน์แรกตรึง), ตัวช่วยเลือกไม้
- [X] **ค้นหาแนะนำ (E8):** ช่องค้นหาแถบบนเรียก `GET /api/search/suggest?q=` (หน่วงพิมพ์ ~250ms, ยกเลิกคำขอเก่า, ใช้คีย์บอร์ดเลือกได้) → แสดงสินค้า/แบรนด์/หมวด; ไม่มีผลลัพธ์แสดง "ไม่พบ"; ข้อความจากเซิร์ฟเวอร์ใส่ผ่าน `textContent` (กัน XSS)
- [X] **สินค้าที่ดูล่าสุด (E8):** หน้าสินค้าบันทึก id ลง `localStorage` (ล่าสุด 20, ห่อ try/catch) → หน้าแรก/หน้าสินค้าเรียก `GET /api/products/by-ids?ids=` แสดงแถว "ดูล่าสุด"; ไม่มีรายการ/ใช้ storage ไม่ได้ = ซ่อนแถว

**5C ตะกร้า → สั่งซื้อ → ชำระเงิน**
- [X] ตะกร้า (`cart_service`), ที่อยู่ (บังคับมี ≥ 1), คูปอง (เลือกจาก "คูปองของฉัน" + พิมพ์โค้ด), สรุปยอด, `order_service.checkout`
- [X] หน้าชำระเงิน: QR จาก `/api/orders/<id>/qr.png`, อัปโหลดสลิป (`accept="image/*"`, ตรวจชนิด/ขนาด)

**5D ออเดอร์ (BUY-3, D4)**
- [X] แท็บสถานะตาม `ORDER_STATUS_DISPLAY_ORDER` (หัวข้อ 3.1): การสั่งซื้อ → รอชำระเงิน → ชำระเงินแล้ว → รอตรวจสลิป → จัดส่งแล้ว → สำเร็จ → รอรีวิว → สินค้าที่ยกเลิก พร้อมจำนวนในแต่ละแท็บและ tooltip อธิบายความหมาย; "รอรีวิว" คำนวณจากออเดอร์ `completed` ที่ยังมีสินค้าไม่ถูกรีวิว (เพิ่มฟังก์ชันใน `review_service`/`order_service`)
- [X] รายละเอียดออเดอร์: timeline (ตามเหตุการณ์จริง), เลขพัสดุ, ยกเลิก (เมื่อยังไม่จัดส่ง), ยืนยันรับของ, ใบเสร็จ PDF; เมื่อ `get_receipt_email_status` = sent แสดง "ส่งใบเสร็จไปที่อีเมล (ซ่อนบางส่วน เช่น ab***@gmail.com) แล้ว"

**5E อื่นๆ**
- [X] โปรไฟล์/เปลี่ยนรหัส, ที่อยู่ (หลายที่อยู่ ตั้งค่าเริ่มต้น), wishlist, แจ้งเตือน, รีวิว, คูปองของฉัน/รับคูปอง
- [X] **เสร็จเมื่อ:** ผู้ซื้อทำครบวงจร (สมัคร → เลือก → ชำระ → สลิป → ติดตาม → รับของ → รีวิว) บนมือถือและ PC ได้ และเทียบหน้าจอกับภาคผนวก B แล้วตรงกัน

### Phase 6 — เว็บเจ้าของ/แอดมิน (PC เท่านั้น) ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | [ใหม่] web/routes_admin.py · [ใหม่] web/templates/admin/* · [ใหม่] web/static/css/admin.css, js/admin.js · `web/auth.py (เฉพาะเพิ่มตัวตรวจ role/PC)` |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `web/ ทั้งหมดจาก Phase 4–5` · `services/ ทั้งโฟลเดอร์ (product, order, payment, coupon, staff, export, expense, contact, email_outbox, banner, audit, settings, shipping, chat, account)` · `database/repo_users.py, repo_sessions.py, repo_coupons.py, repo_products.py` · `core/permissions.py` · `core/constants.py` · `ui/pages/admin/*.py (ลอจิกหน้าเดิมที่ต้องพอร์ต)` · `ui/components/sidebar.py` · `utils/backup.py` · `utils/formatters.py` |

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** OWN-1–6, ADM-0, ADM-1, UX-6 (เมื่อเลือก D1 = A), E1–E7
- **ต้องมีก่อน:** Phase 2, Phase 4
- **ไฟล์:** `web/routes_admin.py`, `web/templates/admin/*`
- หมายเหตุ D1 = B: ให้ทำฟีเจอร์เหล่านี้ใน CustomTkinter (`ui/pages/admin/*`) แทน โดยเรียก service เดียวกัน

- [X] เลย์เอาต์ PC: sidebar + ตารางกว้าง ใช้โทเค็นสีเดียวกัน; ต่ำกว่า 1000px แสดงข้อความให้ใช้คอม
- [X] พอร์ตหน้าเดิม (ลอจิกคงเดิม): dashboard (admin ไม่เห็นรายได้), สินค้า + ฟอร์มสินค้า, ออเดอร์ + รายละเอียด (จัดส่ง/เลขพัสดุ), ตรวจสลิป, แชทลูกค้า, ผู้ใช้
- [X] **ลำดับสถานะหลังบ้าน (D4):** แท็บ/ตัวกรองหน้าออเดอร์แอดมิน, หน้าตรวจสลิป, ตัวนับสถานะบน dashboard, ตัวเลือกสถานะ และคำอธิบาย เรียงตาม `ORDER_STATUS_DISPLAY_ORDER` เหมือนฝั่งผู้ซื้อ (หัวข้อ 3.1)
- [X] **ใบเสร็จอีเมล (SYS-3):** หน้ารายละเอียดออเดอร์ (แอดมิน) แสดงสถานะอีเมลใบเสร็จ (ส่งแล้ว/ล้มเหลว/รอส่ง + เวลา) และปุ่ม "ส่งใบเสร็จอีเมลอีกครั้ง"; หลังกด "ยืนยันสลิป" แสดงว่าระบบส่งใบเสร็จไปอีเมลลูกค้าแล้วหรือจะลองใหม่
- [X] หน้าผู้ใช้ (owner): ปุ่ม "ตั้งรหัสผ่านชั่วคราว" ให้ผู้ซื้อ/แอดมิน (บังคับเปลี่ยนตอนเข้าครั้งแรก, D13/D14) และแสดงล็อกอินล่าสุด
- [X] สินค้า: ปุ่ม "ลบ" (ยืนยัน) + **แท็บ "สินค้าที่ถูกลบ"** แสดงประวัติขาย + กู้คืน (OWN-2)
- [X] หมวดหมู่/แบรนด์: เพิ่ม/แก้/ลบ/กู้คืน; ตอนเพิ่มหมวดเลือก "ทุกแบรนด์" หรือติ๊กเฉพาะบางแบรนด์ (OWN-3)
- [X] คูปอง: ฟอร์มแก้เงื่อนไขได้ครบ + หน้า **"กฎซื้อครบรับคูปอง"** (ยอดที่ต้องซื้อ, ประเภท/มูลค่าคูปอง, ขั้นต่ำ, อายุ, เปิด/ปิด) (OWN-1)
- [X] ผู้ดูแล (owner): รายการ + เพิ่มแอดมิน (เลือกจากอีเมลที่ลงทะเบียน/พิมพ์อีเมล → ตั้งรหัส + ยืนยันรหัส) + ระงับ/รีเซ็ตรหัส/ออกจากระบบทุกเครื่อง (OWN-4)
- [X] ตั้งค่าร้านเดิม (ค่าส่ง, พร้อมเพย์ ฯลฯ) + **ข้อมูลร้านและช่องทางติดต่อ** (OWN-6) + **E1** ที่อยู่ร้าน/เวลาเปิดปิด/ลิงก์ Google Maps + **E3** LINE Official/TikTok
- [X] **สำรอง/ส่งออก** (OWN-5): ปุ่ม "ส่งออก .xlsx ตอนนี้" + ตัวเลือกช่วง (12 เดือนล่าสุด / ปีปฏิทิน 1 ม.ค.–31 ธ.ค. เลือกปี / กำหนดเอง) → ดาวน์โหลดไฟล์; รายการไฟล์ส่งออกรายเดือนอัตโนมัติ; สำรอง/กู้คืน DB เดิม; หน้าบันทึกรายจ่าย (D5)
- [X] **ปุ่ม "ติดต่อเจ้าของร้าน"** ในหัวหน้าแอดมิน (ADM-1): โมดัลแสดงเบอร์ (ปุ่มคัดลอก), ฟอร์มอีเมลด่วน (หัวข้อ+ข้อความ → `send_urgent_to_owner`), ชื่อ/ลิงก์ เฟซบุ๊ก/ไลน์/IG
- [X] แอดมินค้างล็อกอินบนคอมร้าน: ติ๊ก "จำเครื่องนี้" (90 วัน) ตอนล็อกอิน; เจ้าของเห็นรายการเซสชัน
- [X] **แบนเนอร์ (E2, owner):** หน้า `/admin/banners` — อัปโหลด (แนะนำ 1680×640 อัตราส่วน 21:8, ≤ ~300KB), ปุ่มเลื่อนขึ้น/ลงเพื่อเรียง, เปิด-ปิด, ใส่ลิงก์ปลายทาง + ข้อความ alt, ลบ (ยืนยัน), พรีวิวแถบแบนเนอร์; เตือนเมื่อเปิดน้อยกว่า 7 หรือพยายามเกิน 10
- [X] **บันทึกกิจกรรม (E4, owner):** หน้า `/admin/audit-log` — ตาราง วันที่/ผู้กระทำ/การกระทำ/เป้าหมาย/รายละเอียด + ตัวกรอง + แบ่งหน้า (อ่านอย่างเดียว)
- [X] **อีเมลเลขพัสดุ (E5):** ปุ่ม "บันทึกจัดส่ง" เรียก `ship_order_and_notify`; หน้ารายละเอียดออเดอร์แสดงสถานะอีเมลจัดส่ง (ส่งแล้ว/ล้มเหลว/รอส่ง + เวลา) และปุ่ม "ส่งอีเมลเลขพัสดุอีกครั้ง" (หลังแก้เลขพัสดุให้เตือนว่าต้องกดส่งเอง)
- [X] **Google Sheets (E7, owner):** ในหน้าส่งออก — ปุ่ม "ส่งไป Google Sheets" (ตัวเลือกช่วงเวลาเดียวกับ .xlsx) + กล่องเตือนข้อมูลส่วนบุคคล + ช่องติ๊กยืนยันหากต้องการส่งเบอร์/ที่อยู่เต็ม; ถ้ายังไม่ตั้งค่า `.env` ซ่อนปุ่มและแสดงวิธีตั้งค่าสั้นๆ
- [X] **เสร็จเมื่อ:** เจ้าของ/แอดมินทำงานครบตามสิทธิ์เดิม + ฟีเจอร์ใหม่ทุกข้อ (รวม E1–E7); แอดมินเข้าหน้าเจ้าของไม่ได้ (403); ล็อกอินจากมือถือถูกบล็อกตาม D2

### Phase 7 — หน้าจอ AI แชท ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | [ใหม่] web/templates/buyer/chat.html, admin/chat.html · [ใหม่] web/static/js/chat.js · `web/routes_api.py (เพิ่มเส้นทางแชท)` · `web/routes_admin.py (หน้าแชทแอดมิน)` |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `services/chat_service.py` · `services/ai_service.py` · `services/ai_guard.py` · `services/product_service.py (recommend_rackets, get_best_sellers)` · `database/repo_chat.py` · `web/ จาก Phase 4–6 (base.html, auth.py, partials)` · `web/static/css/*` · `ui/pages/buyer/chat.py` · `ui/pages/admin/chat.py` |

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** SYS-2 (ฝั่งหน้าจอ)
- **ต้องมีก่อน:** Phase 3, Phase 5
- [X] หน้าแชทผู้ซื้อ: ฟองข้อความ, ป้าย "AI/แอดมิน", polling `/api/chat/messages?after_id=` ทุก 3 วินาที, แถบปุ่มคำถามสำเร็จรูป (เลื่อนแนวนอนบนมือถือ)
- [X] ปุ่ม "ถาม AI โดยเฉพาะ" (ส่งด้วย `force_ai=True`) แยกจากปุ่มส่งปกติ ชัดเจนว่าเป็น AI
- [X] ปุ่ม/ฟอร์ม "ให้ AI แนะนำไม้" (ตัวเลือกจาก 3D) แสดงผลเป็นการ์ดสินค้า 3 ใบ กดไปหน้าสินค้าได้
- [X] ข้อความเมื่อถูก guard ปฏิเสธ + ปุ่มคำถามแนะนำ
- [X] หน้าแชทฝั่งแอดมิน (พอร์ตจากเดิม) แสดงว่าข้อความใดมาจาก AI
- [X] **เสร็จเมื่อ:** ถามนอกเรื่องแล้วได้ข้อความปฏิเสธโดยไม่เรียก Gemini; ปุ่มสำเร็จรูปตอบถูกจากข้อมูลจริง; แอดมินออนไลน์แต่กด "ถาม AI" แล้ว AI ตอบ

### Phase 8 — มือถือ ภาพเคลื่อนไหว และ PWA ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | `web/static/css/*` · `web/static/js/*` · `web/templates/** (ปรับ responsive/โหลดภาพ)` · [ใหม่] web/static/manifest.json, sw.js, icons/ · `utils/image_utils.py (thumbnail)` |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `web/ ทั้งหมด` · `assets/images/ (ตัวอย่างภาพจริง)` · `config.py` |

เฟสนี้เกือบทั้งหมดอยู่ใน `web/` — แนบ `web/` ทั้งโฟลเดอร์ + `utils/image_utils.py` + `config.py` ก็พอ ไม่ต้องแนบ `services/`

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- **เป้าหมาย:** UX-1, UX-6 (ผู้ซื้อบนมือถือ)
- [X] ตรวจทุกหน้าผู้ซื้อที่ 360 / 390 / 414 / 768 / 1024 / 1440px (ไม่มีเลื่อนข้าง, ปุ่ม ≥ 44px)
- [X] ปรับแอนิเมชันให้ลื่น (ใช้ `transform/opacity`, ไม่กระตุกบนมือถือเก่า), เคารพ `prefers-reduced-motion`, สเกเลตัน/ตัวหมุนตอนโหลด, ภาพ `loading="lazy"` + thumbnail (Pillow)
- [X] PWA: `manifest.json`, ไอคอน 192/512, `sw.js` (แคชเฉพาะไฟล์ static), หน้า offline ธรรมดา, ปุ่ม "เพิ่มลงหน้าจอหลัก"
- [X] ทดสอบ iOS Safari + Android Chrome (โหมดมืด/สว่าง, แป้นพิมพ์ไม่บังช่องกรอก, safe-area)
- [X] **เสร็จเมื่อ:** Lighthouse (มือถือ) Performance/Accessibility ≥ ~85 บนหน้าแรกและหน้าสินค้า (ตัวเลขเป้าหมายประมาณ ปรับได้)

### Phase 9 — ความปลอดภัย QA และนำขึ้นใช้งาน ⬜

**📦 ไฟล์ที่ต้องแนบให้ AI ในเฟสนี้** (แนบ `PROGRESS.md` + `CHANGES_PROGRESS.md` + ซิปของเฟสนี้)

| ประเภท | ไฟล์/โฟลเดอร์ |
|---|---|
| ✏️ **แก้/สร้าง** (AI แก้ได้เฉพาะรายการนี้) | `web/ (CSRF, rate limit, header)` · `run_web.py` · `config.py` · `requirements.txt` · `.env.example` · `.gitignore` · `README.md` · `PROGRESS.md` · [ใหม่] tests/test_web_*.py |
| 📖 **อ้างอิง** (ห้ามแก้ ใช้ดูเพื่อทำให้ตรงกัน) | `services/ ทั้งโฟลเดอร์ (ตรวจสิทธิ์)` · `database/ ทั้งโฟลเดอร์` · `core/` · `utils/backup.py` · `tests/ (ทั้งหมด)` |

**ห้ามแนบ:** `.env` (ความลับ), `secrets/` (กุญแจ Google), `data/` (ฐานข้อมูลลูกค้า), `assets/slips/`, `assets/receipts/` (ข้อมูลส่วนบุคคล)

รายการ `[ใหม่]` ไม่ต้องอยู่ในซิป (AI สร้างให้) · ไฟล์ที่เคยถูกแก้ในเฟสก่อนหน้า ให้แนบเวอร์ชัน **ล่าสุด** · เมื่อจบเฟสให้เก็บเฉพาะไฟล์ที่ AI แก้/สร้างกลับไปรวมในโปรเจกต์หลัก
- [X] CSRF token ทุกฟอร์ม POST (`Flask-WTF`), rate limit (ล็อกอิน, OTP, แชท, อีเมลด่วน, ค้นหาแนะนำ/สินค้าตาม id — `Flask-Limiter`), ปิด debug, header ความปลอดภัย (CSP/`X-Content-Type-Options`)
- [X] ตรวจสิทธิ์: ผู้ซื้อ A เปิดออเดอร์/สลิป/ใบเสร็จของ B ไม่ได้ (ทดสอบ URL ตรงๆ), admin เข้าหน้า owner ไม่ได้, guest เข้าหน้าที่ต้องล็อกอินไม่ได้
- [X] `.env`, `data/`, `assets/slips/`, `assets/receipts/`, `data/exports/` ไม่เปิดสาธารณะ
- [X] เปลี่ยนรหัสบัญชีตัวอย่างทั้งหมด/ลบบัญชี seed ก่อนใช้งานจริง; ตั้งเลขพร้อมเพย์จริง; ตั้ง SMTP จริง
- [X] ตั้ง SMTP จริงแล้วทดสอบส่ง **OTP, ใบเสร็จ, อีเมลเลขพัสดุ (E5) และสรุปสต็อกต่ำ (E6)** ถึงกล่องจดหมายจริง (ตรวจโฟลเดอร์ Junk, ตรวจว่า PDF เปิดได้และภาษาไทยไม่เพี้ยน)
- [X] (E7 ถ้าจะใช้) ตั้ง service account + แชร์สเปรดชีต แล้วทดสอบส่งจริง 1 ช่วงเวลา ตรวจว่าไม่มีเบอร์/ที่อยู่หลุดขึ้นไปตามค่าเริ่มต้น
- [X] ชุดเทสต์เว็บด้วย `app.test_client()`: สมัคร/OTP/ล็อกอิน, ตะกร้า→สั่งซื้อ, สิทธิ์ข้ามผู้ใช้, ห้ามผู้ซื้อเข้า `/admin`
- [X] เลือกที่โฮสต์ตาม D11 + HTTPS; ถ้าโฮสต์ล้างดิสก์ได้ ต้องตั้งที่เก็บถาวรสำหรับ `data/` และ `assets/`
- [X] อัปเดต `README.md` (วิธีรันเว็บ/ตั้ง SMTP/ตั้งเจ้าของ), `PROGRESS.md` (ต่อท้ายเฟสใหม่) และเอกสารนี้
- [X] **เสร็จเมื่อ:** รายการความปลอดภัยข้างต้นผ่าน และทดลองใช้จริงครบทุกบทบาทบนอุปกรณ์จริง

---

## 8. ตารางตรวจสอบย้อนกลับ (PDF → เฟส)

| PDF | รหัส | เฟส backend | เฟสหน้าจอ |
|---|---|---|---|
| ระบบรวม 1 | SYS-1 | 1 | 4 |
| ระบบรวม 2 | SYS-2a–d | 3 | 7 |
| (เพิ่มภายหลัง) | SYS-3 | 2H | 5D, 6 |
| Owner 1 | OWN-1 | 2C | 6 |
| Owner 2 | OWN-2 | 2A | 6 |
| Owner 3 | OWN-3 | 2A, 2B | 6 |
| Owner 4 | OWN-4 | 1 | 4, 6 |
| Owner 5 | OWN-5 | 2E | 6 |
| Owner 6 | OWN-6 | 2D | 5A, 6 |
| Admin 1 | ADM-1 | 2D, 2F | 6 |
| Buyer 1–2 | BUY-1, BUY-2 | 1 | 4, 5 |
| Buyer 3 | BUY-3 | (5D) | 5D |
| Buyer 4 | BUY-4 | 1 | 5E |
| Buyer 5 | BUY-5 | 2G | 5B |
| ตัวอย่างหน้าแอป/สี/ธีม/แบนเนอร์/ล็อกอิน | UX-1–7 | — | 4, 5, 8 |
| (ข้อเสนออนุมัติ v6) ที่อยู่/เวลา/แผนที่, LINE OA/TikTok | E1, E3 | 2D | 5A, 6 |
| (ข้อเสนออนุมัติ v6) จัดการแบนเนอร์ | E2 | 2I | 5A, 6 |
| (ข้อเสนออนุมัติ v6) audit log | E4 | 2J | 6 |
| (ข้อเสนออนุมัติ v6) อีเมลจัดส่ง+เลขพัสดุ | E5 | 2K | 6 |
| (ข้อเสนออนุมัติ v6) อีเมลสรุปสต็อกต่ำ | E6 | 2L | 4 (ตัวตั้งเวลา) |
| (ข้อเสนออนุมัติ v6) Google Sheets | E7 | 2M | 6 |
| (ข้อเสนออนุมัติ v6) ค้นหาแนะนำ + ดูล่าสุด | E8 | 2N | 5A, 5B |

---

## 9. รายการทดสอบ (Test Plan)

**อัตโนมัติ (unittest):** ของเดิมทั้ง 4 ชุด + ชุดใหม่ต่อเฟส — `tests/test_auth_otp.py`, `test_staff.py`, `test_soft_delete.py`, `test_category_brand.py`, `test_coupon_rules.py`, `test_export.py`, `test_contact.py`, `test_receipt_email.py`, `test_banners.py`, `test_audit.py`, `test_shipped_email.py`, `test_low_stock_email.py`, `test_google_sheets.py`, `test_suggest.py`, `test_ai_guard.py`, `test_chat_quick.py`, `test_web_*.py` (Phase 4+)

**ด้วยมือ (ต่อเฟสที่มีหน้าจอ):**
- [X] ผู้เยี่ยมชม: ดูหน้าแรก/สินค้าได้, กดตะกร้า/หัวใจ/รับคูปอง → ไปล็อกอิน
- [X] สมัครอีเมลใหม่: ได้ OTP ครั้งเดียว; ออกจากระบบแล้วล็อกอินใหม่ด้วยอีเมล+รหัสผ่านได้เลยโดยไม่ถูกขอ OTP; สมัครซ้ำด้วยอีเมลเดิมถูกปฏิเสธ
- [X] แอดมินกด "ยืนยันสลิป" → อีเมลใบเสร็จ (HTML + PDF) ถึงกล่องจดหมายผู้ซื้อ; กด "ปฏิเสธสลิป" → ไม่มีอีเมล; กด "ส่งอีกครั้ง" ได้; ลำดับแท็บออเดอร์ตรงหัวข้อ 3.1 ทั้งฝั่งผู้ซื้อและแอดมิน
- [X] ลืมรหัสผ่าน: กรอกอีเมลไม่มีในระบบ → ข้อความเหมือนอีเมลที่มี และไม่มีอีเมลถูกส่ง; อีเมลจริง → ได้ OTP → ตั้งรหัสใหม่ → เซสชันเก่าถูกเตะ → ล็อกอินด้วยรหัสใหม่ได้
- [X] Admin กด "พนักงานลืมรหัสผ่าน" → เห็นช่องทางติดต่อ Owner (ไม่มีช่องกรอกอีเมล/ไม่มี OTP); Owner รัน `tools/reset_password.py` → Admin เข้าด้วยรหัสใหม่ได้ ถูกบังคับเปลี่ยนรหัส และเซสชันเก่าถูกเตะ
- [X] สมัครสำเร็จแล้วถูกพากลับหน้าล็อกอิน (ไม่ล็อกอินให้เอง)
- [X] อีเมลสลิปออนไลน์: ตัวอีเมลอ่านรายการ/ยอดครบโดยไม่ต้องเปิด PDF; ผู้ส่งเป็นชื่อร้าน/อีเมลร้าน; Reply-To = อีเมลร้าน
- [X] สมัคร: OTP ผิด 5 ครั้งถูกล็อก, OTP หมดอายุ, ส่งซ้ำเร็วเกิน, อีเมลซ้ำ
- [X] ซื้อครบ 3,000 แล้วสำเร็จ → ได้คูปอง 300 ใช้ครั้งถัดไปขั้นต่ำ 1,000 → คนอื่นใช้ไม่ได้
- [X] ลบสินค้า → หายจากหน้าผู้ซื้อ/ตะกร้า แต่ออเดอร์เก่าและแท็บ "สินค้าที่ถูกลบ" ยังเห็นประวัติ → กู้คืนได้
- [X] เพิ่มหมวดแบบ "ทุกแบรนด์" แล้วเพิ่มแบรนด์ใหม่ → ผูกอัตโนมัติ; แบบ "เฉพาะบางแบรนด์" → แบรนด์อื่นไม่ขึ้นในหมวดนั้น
- [X] ส่งออก .xlsx ทั้ง 3 แบบช่วงเวลา เปิดด้วย Excel แล้วยอดตรงหน้า dashboard
- [X] ปิดเซิร์ฟเวอร์ข้ามต้นเดือนแล้วเปิดใหม่ → ไฟล์รายเดือนถูกสร้างย้อนหลัง
- [X] แอดมินค้างล็อกอินหลังรีสตาร์ทเซิร์ฟเวอร์; เจ้าของสั่ง "ออกจากระบบทุกเครื่อง" แล้วถูกเตะ
- [X] แชท: ถามนอกเรื่อง → ข้อความปฏิเสธ; ปุ่มสำเร็จรูป; "ถาม AI โดยเฉพาะ" ตอนแอดมินออนไลน์; ฟอร์มแนะนำไม้ได้ 3 ไม้
- [X] เปรียบเทียบ 2, 3, 4, 5 ไม้ผ่าน; 6 ไม้ไม่ผ่าน; 1 ไม้ไม่ผ่าน
- [X] (E1/E3) เจ้าของแก้ที่อยู่/เวลาเปิดปิด/ลิงก์แผนที่/LINE OA/TikTok → แสดงที่ footer และ `/contact`; ลิงก์ที่ไม่ใช่ https ถูกปฏิเสธ; ช่องที่ว่างไม่แสดง
- [X] (E2) แบนเนอร์: อัปโหลด/เรียง/ซ่อน/ใส่ลิงก์/ลบ → หน้าแรกตรงตามที่ตั้ง; ลบหมด → ตัวแทนพื้นไล่สี; admin เปิดหน้านี้ไม่ได้ (403)
- [X] (E4) ลบสินค้า/แก้คูปอง/เพิ่มแอดมิน → เห็นแถวใน audit log; ไม่มีรหัสผ่านในรายละเอียด; admin เปิดหน้า audit ไม่ได้
- [X] (E5) กดบันทึกจัดส่ง → ผู้ซื้อได้อีเมลเลขพัสดุ; แก้เลขพัสดุไม่ส่งเอง; กด "ส่งอีกครั้ง" ได้
- [X] (E6) มีสินค้าใกล้หมด → เจ้าของได้อีเมลสรุปไม่เกินวันละ 1 ฉบับ; ไม่มีของใกล้หมด → ไม่ได้อีเมล
- [X] (E7) ส่งไป Google Sheets → แท็บใหม่ยอดตรงกับ .xlsx; โดยค่าเริ่มต้นไม่มีเบอร์/ที่อยู่
- [X] (E8) พิมพ์ ≥ 2 ตัวอักษรในช่องค้นหาแล้วมีคำแนะนำ; ดูสินค้าแล้วกลับหน้าแรกเห็นแถว "ดูล่าสุด"; สินค้าที่ถูกลบหายจากแถวนี้
- [X] มือถือจริง: ทุกหน้าผู้ซื้อ ทั้งโหมดมืด/สว่าง

---

## 10. ความเสี่ยงและข้อควรระวัง

| ความเสี่ยง | ผลกระทบ | วิธีลด |
|---|---|---|
| `Session` global | ผู้ใช้หลายคนปนสิทธิ์บนเว็บ | ทำ contextvars ใน Phase 4 ก่อนเปิดใช้งานจริง + เทสต์ 2 ผู้ใช้พร้อมกัน |
| โควตา/การตั้งค่า SMTP (Gmail ต้อง App Password) | OTP ไม่ถึง สมัครไม่ได้ | ทดสอบส่งจริงตั้งแต่ Phase 1; `OTP_DEV_ECHO` เฉพาะตอนพัฒนา |
| อีเมลสแปม/ตกกล่อง Junk | ผู้ใช้ไม่เห็น OTP | เนื้อหาสั้นชัดเจน, ใช้ `SMTP_FROM` ที่ถูกต้อง, แจ้งผู้ใช้ให้ดูกล่อง Junk |
| โควตาส่งอีเมลของผู้ให้บริการ (เช่น Gmail จำกัดจำนวนต่อวัน) | OTP/ใบเสร็จตกค้าง | ใช้คิว `email_outbox` + retry; ถ้าลูกค้าเยอะให้ย้ายไปบริการส่งอีเมลเฉพาะ (ตรวจเงื่อนไขล่าสุดของผู้ให้บริการ) |
| ใบเสร็จ PDF ไม่มีฟอนต์ไทยบนเซิร์ฟเวอร์ | แนบ PDF ไม่ได้/ภาษาไทยเพี้ยน | ติดตั้งฟอนต์ไทยบนโฮสต์ (README หัวข้อ 6); fallback ส่ง HTML อย่างเดียว |
| โฮสต์ที่ดิสก์ไม่ถาวร | SQLite/รูป/สลิปหาย | เลือกที่เก็บถาวร หรือสำรองไฟล์รายวันออกนอกเครื่อง |
| SQLite เขียนพร้อมกันหนัก | `database is locked` | WAL + `busy_timeout` มีแล้ว; transaction สั้นๆ; พิจารณา DB อื่นถ้าผู้ใช้เยอะมาก |
| ข้อมูลส่วนบุคคลในไฟล์ส่งออก | รั่วไหล | เก็บในโฟลเดอร์ไม่สาธารณะ, ดาวน์โหลดผ่านสิทธิ์ owner เท่านั้น |
| AI ตอบผิด/หลุดขอบเขต | ลูกค้าเข้าใจผิด | guard + ตอบจากข้อมูลจริง + จำกัดสินค้าที่ส่งให้ AI + ป้ายบอกว่าเป็น AI |
| ปุ่มรางวัลคูปองถูกเอาเปรียบ | ขาดทุน | ออกเมื่อ `completed` เท่านั้น, unique ต่อออเดอร์, จำกัดอายุ/การใช้ครั้งเดียว |
| ตีความ PDF ผิด | ทำผิดทิศ | ตารางหัวข้อ 2–3 ให้เจ้าของโปรเจกต์ตรวจก่อนเริ่มเฟสที่เกี่ยวข้อง |
| ส่งข้อมูลลูกค้าขึ้น Google Sheets (E7) | ข้อมูลส่วนบุคคลอยู่บนคลาวด์บุคคลที่สาม/สเปรดชีตถูกแชร์ผิดคน | ค่าเริ่มต้นตัดเบอร์/ที่อยู่; กุญแจใน `secrets/` ไม่ commit; แชร์สเปรดชีตให้เฉพาะ service account และเจ้าของ |
| ลิงก์แบนเนอร์/ข้อความร้านถูกแทรกสคริปต์ (E1–E3) | XSS บนหน้าแรก | รับเฉพาะ `https://` หรือ path ภายใน; escape ทุกครั้งที่แสดง; ใช้ `textContent` ใน JS |
| อีเมลสต็อกต่ำ/จัดส่งท่วมกล่อง (E5, E6) | โควตาผู้ให้บริการหมด/ถูกตีเป็นสแปม | สรุปสต็อกต่ำรายวัน; จัดส่งส่งครั้งเดียวต่อออเดอร์; ใช้คิว+retry |
| audit log โตเรื่อยๆ (E4) | ฐานข้อมูลบวม | เก็บเฉพาะเหตุการณ์สำคัญ; มี index ตามเวลา; ค่อยเพิ่มระบบเก็บถาวร/ย้ายออกภายหลังถ้าจำเป็น |

---

## 11. ข้อเสนอเพิ่มเติม (✅ อนุมัติทั้งหมดแล้ว — v6)

เจ้าของโปรเจกต์อนุมัติ E1–E9 ครบ จึงเป็นส่วนของแผนหลักและทำตามเฟสในตาราง; ข้อเสนอใหม่ในอนาคตให้ใช้เลข E10 เป็นต้นไป และรออนุมัติก่อนทำ

| # | ข้อเสนอ | สถานะ | ทำที่ |
|---|---|---|---|
| E1 | ที่อยู่ร้าน + เวลาเปิดปิด + ลิงก์ Google Maps ในข้อมูลร้าน (OWN-6) | ✅ อนุมัติ (v6) | 2D, 5A, 6 |
| E2 | จัดการแบนเนอร์ในหน้าเจ้าของ (อัปโหลด/เรียง/ซ่อน/ลิงก์ปลายทาง) | ✅ อนุมัติ (v6) | 2I, 5A, 6 |
| E3 | ลิงก์ LINE Official / TikTok เพิ่มจาก 3 ช่องทางเดิม | ✅ อนุมัติ (v6) | 2D, 5A, 6 |
| E4 | บันทึกกิจกรรมสำคัญ (audit log) | ✅ อนุมัติ (v6) | 2J, 6 |
| E5 | อีเมลแจ้งสถานะ "จัดส่งแล้ว + เลขพัสดุ" ให้ลูกค้า | ✅ อนุมัติ (v6) | 2K, 6 |
| E6 | แจ้งเตือนสต็อกต่ำถึงเจ้าของทางอีเมล (แบบสรุปรายวัน) | ✅ อนุมัติ (v6) | 2L, 4 |
| E7 | เชื่อม Google Sheets เป็นทางเลือกนอกจาก .xlsx (D8) | ✅ อนุมัติ (v6) | 2M, 6 |
| E8 | คำค้นหาแนะนำ (autocomplete) + สินค้าที่ดูล่าสุด | ✅ อนุมัติ (v6) | 2N, 5A, 5B |
| E9 | ลืมรหัสผ่านของผู้ซื้อด้วย OTP ทางอีเมล | ✅ อนุมัติ (v4) — D13 / Phase 1, 4 / หัวข้อ 12.13 | 1, 4 |

---

## 12. แผนผังขั้นตอนการทำงานของทุกระบบ (ตามลำดับจริง)

> ใช้เป็นแบบอ้างอิงตอนเขียนโค้ดและทดสอบ ลูกศร `→` = ลำดับ, `✗` = กรณีผิดพลาด ทุกข้อความที่ผู้ใช้เห็นเป็นภาษาไทย

### 12.1 สมัครสมาชิก (ผู้ซื้อ) — OTP ครั้งเดียวต่ออีเมล
1. ผู้ซื้อเปิดหน้า `/register` → กรอก ชื่อ, เบอร์, อีเมล, รหัสผ่าน (+ยืนยัน), ที่อยู่ตั้งต้น (ชื่อผู้รับ/เบอร์/ที่อยู่/อำเภอ/จังหวัด/รหัสไปรษณีย์)
2. เซิร์ฟเวอร์ตรวจรูปแบบ → แปลงอีเมลเป็นตัวพิมพ์เล็ก
3. อีเมลนี้ **ยืนยันแล้วในระบบ?** → ✗ "อีเมลนี้สมัครแล้ว กรุณาเข้าสู่ระบบ" (ไม่ส่ง OTP)
4. ยังไม่เคย/ค้างไม่ยืนยัน → เขียนทับ `pending_registrations` (รหัสผ่านเก็บเป็น bcrypt hash ทันที) → `otp_service` สร้างรหัส 6 หลัก เก็บเฉพาะแฮช อายุ 10 นาที → `email_service` ส่ง OTP ไปอีเมล
5. หน้าจอ 6 ช่อง: กรอก/วางรหัส; ส่งซ้ำได้ทุก 60 วิ (≤ 5 ครั้ง/ชม.); ผิดครบ 5 ครั้งหรือหมดอายุ → ✗ ต้องขอรหัสใหม่
6. รหัสถูก → transaction เดียว: สร้าง `users` (role=buyer, `email_verified=1`, username อัตโนมัติ) + `addresses` (is_default=1) → ลบ `pending_registrations` → ทำ OTP เป็น used
7. **ไม่ล็อกอินให้อัตโนมัติ** → พากลับ `/login` พร้อมข้อความเขียว "สมัครสำเร็จ! เข้าสู่ระบบด้วยอีเมลและรหัสผ่านได้เลย" (อีเมลถูกกรอกให้ในช่อง) → ผู้ใช้ล็อกอินตามปกติ (12.2) แล้วไปตาม `?next=` หรือหน้าแรก
**หลังจากนี้ล็อกอินไม่มี OTP อีกเลย** (OTP จะมีอีกเฉพาะตอนลืมรหัสผ่าน 12.13)

### 12.2 เข้าสู่ระบบ / ออกจากระบบ
1. `/login` กรอกอีเมล + รหัสผ่าน (+ ติ๊ก "จำเครื่องนี้" สำหรับ staff บนคอมร้าน) · มีลิงก์ "ลืมรหัสผ่าน?" (12.13) และ "ยังไม่มีบัญชี? สมัครสมาชิก"
2. ตรวจ bcrypt → ✗ ข้อความกลางเดียว "อีเมลหรือรหัสผ่านไม่ถูกต้อง" (ไม่บอกว่าอีเมลมีหรือไม่)
3. บัญชีถูกระงับ → ✗ แจ้งระงับ · `email_verified=0` → ✗ แจ้งให้สมัครใหม่/ยืนยันอีเมล
4. role เป็น owner/admin แต่มาจากมือถือ/IP ที่ไม่อนุญาต → ✗ 403 หน้า "กรุณาใช้งานบนคอมพิวเตอร์" (D2)
5. สำเร็จ → สร้างเซสชัน (buyer 7 วัน, staff 90 วัน ต่ออายุทุกครั้งที่ใช้) → `must_change_password=1` ? พาไปหน้าเปลี่ยนรหัสก่อน : ไปหน้าตาม role (buyer = หน้าแรก, staff = แดชบอร์ด)
6. ออกจากระบบ → ลบแถว `sessions` ของ token นั้น; เจ้าของ "ออกจากระบบทุกเครื่อง" = ลบทุกแถวของ user นั้น

### 12.3 ผู้เยี่ยมชม (guest) → สมัคร
ดูหน้าแรก/หมวด/สินค้า/ค้นหา/เปรียบเทียบ/ตัวช่วยเลือกไม้ได้ → กด ตะกร้า/หัวใจ/สั่งซื้อ/รับคูปอง/แชท → โมดัล "กรุณาเข้าสู่ระบบ" (ปุ่ม เข้าสู่ระบบ / สมัครสมาชิก) → ล็อกอินสำเร็จ → กลับมาหน้าเดิมด้วย `?next=` (รับเฉพาะ path ในเว็บเรา กัน open redirect) · เซิร์ฟเวอร์ตรวจ `login_required` ซ้ำเสมอ

### 12.4 สั่งซื้อ → ชำระเงิน → ตรวจสลิป → ส่งใบเสร็จอีเมล → จัดส่ง → สำเร็จ → รีวิว
| ขั้น | ใครทำ | เกิดอะไร | สถานะ DB | ป้ายที่เห็น (ตามหัวข้อ 3.1) |
|---|---|---|---|---|
| 1 | ผู้ซื้อ | เลือกสินค้า/ตัวเลือก → ตะกร้า → เลือกที่อยู่ (ต้องมี ≥ 1) → เลือก/พิมพ์คูปอง → กดสั่งซื้อ (`order_service.checkout`) ตัดสต็อก | `pending` | รอชำระเงิน |
| 2 | ผู้ซื้อ | หน้าชำระเงินแสดง QR พร้อมเพย์ → โอน → อัปโหลดสลิป (`payment_service.submit_slip`) | `checking_slip` | รอตรวจสลิป |
| 3 | แอดมิน/เจ้าของ | หน้าตรวจสลิป กด **ยืนยัน** (`verify_payment`) — transaction: payment=verified, ออเดอร์→paid, สร้าง shipments, แจ้งเตือนผู้ซื้อ | `paid` | ชำระเงินแล้ว |
| 3a | ระบบ (**หลัง commit ขั้น 3**) | `queue_receipt_email(order_id)`: สร้าง PDF ใบเสร็จ → ใส่ `email_outbox` → thread ส่งอีเมลถึงผู้ซื้อ (HTML + PDF) → ล้มเหลว = retry 3 ครั้ง; ผู้ซื้อได้แจ้งเตือนในแอป "ส่งใบเสร็จไปที่อีเมลแล้ว" | ไม่เปลี่ยน | — |
| 3b | แอดมิน | ทางเลือก: กด **ปฏิเสธ** (`reject_payment`) → ผู้ซื้อแนบสลิปใหม่ได้ **ไม่ส่งอีเมลใบเสร็จ** | กลับ `pending` ตามลอจิกเดิม | รอชำระเงิน |
| 4 | แอดมิน | ใส่ขนส่ง + เลขพัสดุ (`shipping_service.ship_order_and_notify`) | `shipped` | จัดส่งแล้ว |
| 4a | ระบบ (**หลัง commit ขั้น 4**) | `queue_shipped_email(order_id)` → อีเมลเลขพัสดุถึงผู้ซื้อ (ส่งครั้งเดียว/ออเดอร์, retry 3 ครั้ง, E5) + แจ้งเตือนในแอป | ไม่เปลี่ยน | — |
| 5 | ผู้ซื้อ | กด "ยืนยันรับของ" (หรือระบบปิดอัตโนมัติถ้าลอจิกเดิมมี) → `issue_reward_coupons` ในธุรกรรมเดียวกัน (D9) | `completed` | สำเร็จ |
| 6 | ผู้ซื้อ | เขียนรีวิวสินค้าที่ยังไม่รีวิว | ไม่เปลี่ยน | รอรีวิว → (รีวิวครบ) หลุดจากแท็บ |
| × | ผู้ซื้อ/ระบบ | ยกเลิกก่อนจัดส่ง / ค้างชำระเกิน `unpaid_cancel_hours` → คืนสต็อก | `cancelled` | สินค้าที่ยกเลิก |

หมายเหตุ: ลำดับป้ายในแท็บ (ชำระเงินแล้ว ก่อน รอตรวจสลิป) เป็นเรื่องการ **แสดงผลเท่านั้น** ตาม D4; สถานะจริงในฐานข้อมูลยังเดินตามคอลัมน์ "สถานะ DB" ด้านบน

### 12.5 การแสดงสถานะในทุกหน้า (D4)
ค่าคงที่ตัวเดียว `ORDER_STATUS_DISPLAY_ORDER` → ใช้ที่: แท็บออเดอร์ผู้ซื้อ · แท็บ/ตัวกรองออเดอร์แอดมิน · หน้าตรวจสลิป · ตัวนับบนแดชบอร์ด · dropdown สถานะ · tooltip; แท็บ "การสั่งซื้อ" = รวมทุกสถานะ; แท็บ "รอรีวิว" = `completed` ที่มีรายการสินค้ายังไม่ถูกรีวิว (คำนวณ ไม่ใช่สถานะ DB)

### 12.6 ซื้อครบรับคูปอง (OWN-1)
เจ้าของตั้งกฎ (เช่น ซื้อ ≥ 3,000 → คูปองลด 300, ใช้เมื่อซื้อขั้นต่ำ 1,000, อายุ 30 วัน) → ผู้ซื้อสั่งซื้อ → ออเดอร์เป็น `completed` → ระบบเทียบยอดสุทธิกับกฎที่เปิดอยู่ → สร้างคูปองส่วนตัว (`RWD-XXXXXX`, ใช้ได้ครั้งเดียว, เฉพาะ owner_user_id) → แจ้งเตือน → ผู้ซื้อเลือกจาก "คูปองของฉัน" ที่หน้าชำระเงินครั้งถัดไป · unique index กันออกซ้ำต่อออเดอร์ · ยกเลิก/ไม่สำเร็จ = ไม่ได้คูปอง

### 12.7 ลบสินค้า / หมวด / แบรนด์ (OWN-2, OWN-3)
เจ้าของกด ลบ → ยืนยัน → ตั้ง `deleted_at` (ไม่ลบแถวจริง) → หายจากฝั่งผู้ซื้อ/ค้นหา/แนะนำ/AI; ตะกร้าที่มีสินค้านั้นขึ้น "สินค้านี้ไม่มีจำหน่ายแล้ว"; ออเดอร์เก่ายังอยู่ → แท็บ "สินค้าที่ถูกลบ" แสดงประวัติขาย + ปุ่มกู้คืน · หมวด/แบรนด์ที่ยังมีสินค้า: ปฏิเสธพร้อมจำนวน หรือ `cascade=True` หลังยืนยัน

### 12.8 เพิ่มผู้ดูแล (OWN-4)
เจ้าของเข้า "จัดการผู้ดูแล" → เลือกจากอีเมลที่ยืนยันแล้ว หรือพิมพ์อีเมลใหม่ → ตั้งรหัสผ่าน + ยืนยันรหัส → เปลี่ยน role เป็น admin (`email_verified=1`) → เจ้าของแจ้งรหัสให้พนักงานเอง → พนักงานล็อกอินที่คอมร้านครั้งเดียว ติ๊ก "จำเครื่องนี้" → เซสชัน 90 วัน ไม่ต้องกรอกรหัสซ้ำ · เจ้าของระงับ/รีเซ็ตรหัส/ออกจากระบบทุกเครื่องได้ · admin เพิ่ม admin ไม่ได้ (403)

### 12.9 ส่งออกและสำรองข้อมูล (OWN-5)
- ด้วยมือ: เจ้าของเลือกช่วง (12 เดือนล่าสุด / ปีปฏิทิน 1 ม.ค.–31 ธ.ค. / กำหนดเอง) → `export_service.export_range` → ดาวน์โหลด `.xlsx` (สรุป, ออเดอร์, รายการสินค้าที่ขาย, ลูกค้า, รายจ่าย, สต็อก)
- อัตโนมัติ: ตอนเปิดเซิร์ฟเวอร์และทุกวัน → ถ้าเดือนก่อนหน้ายังไม่ถูกส่งออก (`last_auto_export`) → สร้าง `data/exports/monthly/YYYY-MM.xlsx` (ย้อนเติมเดือนที่พลาด) → บันทึกเดือนล่าสุด

### 12.10 ติดต่อเจ้าของจากแอดมิน (ADM-1)
แอดมินกด "ติดต่อเจ้าของร้าน" → เห็นเบอร์ (ปุ่มคัดลอก), ชื่อ/ลิงก์ FB, ไลน์, IG → พิมพ์อีเมลด่วน (หัวข้อ+ข้อความ) → `send_urgent_to_owner` (≤ 5/ชม.) → ส่งจากบัญชี SMTP ของร้านไป `OWNER_EMAIL` พร้อม Reply-To = อีเมลแอดมิน → บันทึก `staff_messages`

### 12.11 แชทกับ AI (SYS-2)
```
ผู้ซื้อพิมพ์/กดปุ่ม
 ├─ ปุ่มคำถามสำเร็จรูป → ตอบจากข้อมูลจริงใน DB (ไม่เรียก AI)
 ├─ ฟอร์ม "ให้ AI แนะนำไม้" → recommend_rackets เลือก 3 ไม้ → AI เขียนคำอธิบายเฉพาะ 3 ไม้นั้น (ล้ม = ใช้แม่แบบ)
 └─ ข้อความอิสระ → ai_guard
        block     → ตอบข้อความคงที่ "ขออภัยครับ ระบบไม่สามารถตอบคำถามเหล่านี้ได้ ..." (ไม่เสียโควตา Gemini)
        allow     → should_ai_reply() ? เรียก AI : รอแอดมิน   (ถ้ากด "ถาม AI โดยเฉพาะ" = force_ai ข้ามเงื่อนไขนี้)
        uncertain → เรียก AI พร้อม system prompt บังคับตอบเฉพาะเรื่องร้าน; หลุดขอบเขต → __OUT_OF_SCOPE__ → ข้อความคงที่
```

### 12.12 ลำดับการเริ่มเซิร์ฟเวอร์ (`run_web.py`)
`init_db()` (+ `_migrate_v2`) → seed (ถ้าว่าง/ตาม `OWNER_EMAIL`) → `clear_all_online` → `auto_cancel_unpaid` → สำรอง DB → ส่งออกรายเดือนที่ค้าง → ตัวตั้งเวลา (ยกเลิกค้างชำระ, retry อีเมล, สรุปสต็อกต่ำรายวัน — E6, ล้าง OTP/เซสชันหมดอายุ) → `waitress` เสิร์ฟ

### 12.13 ลืมรหัสผ่าน (E9 / D13) — ผู้ซื้อ
1. หน้า `/login` กด "ลืมรหัสผ่าน?" → `/forgot` กรอกอีเมล
2. ระบบ **ตอบข้อความเดียวกันเสมอ** "ถ้าอีเมลนี้มีบัญชี ระบบจะส่งรหัสยืนยันให้" แล้วไปหน้ากรอก OTP (กันคนเดาว่าอีเมลไหนมีบัญชี)
3. ถ้าเป็นบัญชี buyer ที่ยืนยันอีเมลแล้วและไม่ถูกระงับ → สร้าง OTP (`purpose='reset'`, อายุ 10 นาที, เก็บแฮช) → ส่งอีเมลจากบัญชีร้าน; กรณีอื่น **ไม่ส่งอะไรเลย** (หน้าจอดูเหมือนกัน)
4. กรอก OTP 6 ช่อง (ผิด ≤ 5 ครั้ง, ส่งซ้ำได้ทุก 60 วิ ≤ 5/ชม.) → ถูก → ตั้งรหัสผ่านใหม่ + ยืนยัน
5. เปลี่ยนรหัสสำเร็จ → ลบเซสชันเก่าทุกเครื่อง → พากลับ `/login` พร้อมข้อความ "เปลี่ยนรหัสผ่านแล้ว เข้าสู่ระบบด้วยรหัสใหม่ได้เลย" (ไม่ล็อกอินให้)
6. **พนักงาน (Admin) ลืมรหัส:** หน้า login มีลิงก์ "พนักงาน/แอดมินลืมรหัสผ่าน?" → `/forgot/staff` แสดงช่องทางติดต่อ Owner (ไม่ถามอีเมล ไม่ส่ง OTP จึงไม่เปิดช่องเดาบัญชี) → Owner รันสคริปต์บนเครื่องร้าน (D14); **Owner ลืมรหัส** → รันสคริปต์เดียวกัน

### 12.14 แจ้งจัดส่งทางอีเมล (E5)
1. แอดมินกด "บันทึกจัดส่ง" (ขนส่ง + เลขพัสดุ) → `ship_order_and_notify` → `ship_order` ทำใน transaction → commit
2. หลัง commit → `queue_shipped_email` → ใส่ `email_outbox` (`kind='shipped'`) → thread ส่งไปอีเมลผู้ซื้อที่ยืนยันแล้ว → ล้มเหลว = retry 3 ครั้ง (การจัดส่งไม่ล้มตาม)
3. ผู้ซื้อได้แจ้งเตือนในแอป "ส่งเลขพัสดุไปที่อีเมลแล้ว"
4. แก้เลขพัสดุภายหลัง → **ไม่ส่งเอง** → แอดมินกด "ส่งอีเมลเลขพัสดุอีกครั้ง" (ส่งข้อมูลล่าสุด)

### 12.15 จัดการแบนเนอร์ (E2) และบันทึกกิจกรรม (E4) — owner
- แบนเนอร์: owner เข้า `/admin/banners` → อัปโหลดรูป (ตรวจชนิด/ขนาด) → ใส่ลิงก์ปลายทาง (`https://` หรือ path ภายใน) → เรียง/ซ่อน/ลบ → หน้าแรกแสดงตามลำดับ (DB → โฟลเดอร์ → ตัวแทนพื้นไล่สี)
- audit log: การกระทำสำคัญ (ลบ/กู้คืนสินค้า, แก้คูปอง/กฎ, เพิ่ม-ระงับ-รีเซ็ต staff, แก้ตั้งค่า, แบนเนอร์, ส่งออก, ตรวจสลิป, ยกเลิกออเดอร์โดยแอดมิน) เขียนแถวใน `audit_log` ใน transaction เดียวกับการกระทำ → owner ดูที่ `/admin/audit-log` (อ่านอย่างเดียว; ไม่มีรหัสผ่าน/OTP/token)

### 12.16 สรุปสต็อกต่ำถึงเจ้าของ (E6)
ตัวตั้งเวลาวันละครั้ง → `send_low_stock_digest()` → `get_low_stock_products()` ว่าง = จบ → `last_low_stock_email` = วันนี้แล้ว = จบ → สร้างอีเมลสรุป (ชื่อ/ตัวเลือก/คงเหลือ/เกณฑ์) → outbox `kind='low_stock'` → ส่งถึง `OWNER_EMAIL` → บันทึกวันที่ส่ง

### 12.17 ส่งออกไป Google Sheets (E7) — owner
owner เลือกช่วงเวลา (เหมือน .xlsx) → กด "ส่งไป Google Sheets" (เห็นคำเตือนข้อมูลส่วนบุคคล; ไม่ติ๊กยืนยัน = ตัดเบอร์/ที่อยู่) → `sync_to_google_sheets` → ไม่ได้ติดตั้ง/ไม่ได้ตั้งค่า = ข้อความไทยบอกวิธี → สำเร็จ = สร้าง/ล้างแท็บตามช่วงเวลาแล้วเขียนข้อมูล + แจ้งจำนวนแถว → บันทึก audit

### 12.18 ค้นหาแนะนำและสินค้าที่ดูล่าสุด (E8)
- พิมพ์ในช่องค้นหา ≥ 2 ตัวอักษร → รอ ~250ms → `/api/search/suggest?q=` → แสดงสินค้า/แบรนด์/หมวด (เฉพาะที่เปิดขาย) → เลือก = ไปหน้านั้น / Enter = ค้นหาเต็ม
- เปิดหน้าสินค้า → เบราว์เซอร์เก็บ id ใน `localStorage` (ล่าสุด 20) → หน้าแรก/หน้าสินค้าเรียก `/api/products/by-ids` แสดงแถว "ดูล่าสุด" (สินค้าที่ถูกลบ/ปิดขายถูกข้าม)

---

## 13. บันทึกความคืบหน้า (อัปเดตทุกครั้งที่จบงาน)

| วันที่ | เฟส/งาน | สถานะ | สิ่งที่ทำ / ไฟล์ที่แตะ | เทสต์ | หมายเหตุ / ค่า D ที่ใช้ |
|---|---|---|---|---|---|
| 2026-10-13 | วางแผน (ฉบับ v2) | ✅ | ยืนยัน D3, D4, D12; เพิ่ม SYS-3 / Phase 2H; เพิ่ม D13, E9 | — | แก้เอกสารนี้เท่านั้น ยังไม่แตะโค้ด |
| 2026-10-13 | วางแผน (ฉบับ v3) | ✅ | ตรวจเทียบโค้ดจริง (1.1), เพิ่มหัวข้อ 12 แผนผังขั้นตอน, ภาคผนวก A–F ให้ไฟล์เดียวครบ | — | ไม่แตะโค้ด |
| 2026-10-13 | วางแผน (ฉบับ v4) | ✅ | อนุมัติ E9 (ลืมรหัสผ่าน OTP), ยืนยันสลิปออนไลน์เป็นข้อความ+PDF จากอีเมลร้าน, หน้า login/register แบบใหม่ (B.4), ระบบติ๊ก [ ]→[X] | — | แก้เอกสารเท่านั้น |
| 2026-10-13 | วางแผน (ฉบับ v5) | ✅ | เพิ่มกล่อง 📦 ไฟล์ต่อเฟส + ภาคผนวก G; D14 ยืนยัน (staff ติดต่อ Owner → สคริปต์); หน้า `/forgot/staff` | — | แก้เอกสารเท่านั้น |
| 2026-10-13 | วางแผน (ฉบับ v6) | ✅ | อนุมัติ E1–E9 ทั้งหมด: เพิ่มหัวข้อ 2.6, ตาราง `banners`/`audit_log`, `email_outbox.kind` เพิ่ม `shipped`/`low_stock`, คีย์ settings/.env ใหม่, Phase 2 หัวข้อ 2D/2I–2N, งานหน้าจอใน Phase 5–6, flow 12.14–12.18 | — | แก้เอกสารเท่านั้น ยังไม่แตะโค้ด |
| 2026-10-15 | Phase 0–9 (CustomTkinter v2) | ✅ | อัปเกรดระบบครบทุกเฟสบน Python + SQLite + CustomTkinter 100% (31 ตาราง, 23 repositories, 24 services, 30 หน้าจอ GUI, ธีมเหลือง-แดง-ขาว/ดำ คอนทราสต์สูง) | 146/146 ผ่าน + GUI 30 routes ผ่าน | ยืนยัน Desktop CustomTkinter 100% ไม่มีเว็บเฟรมเวิร์ก |

**ค่า Decision ที่ยืนยันแล้ว:** (กรอกเมื่อเจ้าของโปรเจกต์ตอบ)
ยืนยันโดยเจ้าของโปรเจกต์แล้ว: **D3** (OTP ตอนสมัครครั้งเดียวต่ออีเมล) · **D4** (ลำดับสถานะหัวข้อ 3.1) · **D12** (ใบเสร็จส่งอัตโนมัติผ่านบัญชีอีเมลร้าน/เจ้าของ; v4: เป็นข้อความในอีเมล + แนบ PDF) · **D13/E9** (ลืมรหัสผ่านด้วย OTP) · **SYS-3** (ใบเสร็จอีเมลหลังตรวจสลิปผ่าน) · **E1–E8** (อนุมัติทั้งหมด v6; ค่าเริ่มต้นที่เลือก: E5 = แก้เลขพัสดุไม่ส่งซ้ำอัตโนมัติ · E6 = สรุปรายวัน ไม่ส่งทุกครั้งที่ข้ามเกณฑ์ · E7 = ตัดเบอร์/ที่อยู่ออกโดยค่าเริ่มต้น + กดส่งเอง · E8 = "ดูล่าสุด" เก็บในเบราว์เซอร์ ไม่เก็บใน DB)
ข้ออื่นใช้ค่าแนะนำจนกว่าจะตอบ: D1 = A · D2 = ชั้นแรก+UA · D5 = ค · D6 = ตามแนะนำ · D7 = ทั้งสองแบบ · D8 = .xlsx · D9 = completed · D10 = ตามแนะนำ · D11 = รอตัดสินใจ (Phase 9) · D13 = ทำแล้ว (E9 อนุมัติ) · D14 = ยืนยันแล้ว: staff ติดต่อ Owner → Owner รันสคริปต์ (ไม่มี OTP สำหรับ staff)

---

## ภาคผนวก (ใช้ประกอบการทำ — ไม่ต้องหาไฟล์อื่น)

### ภาคผนวก A — โทเค็นดีไซน์และ CSS หลัก (`web/static/css/theme.css`)

```css
:root{
  /* สีแบรนด์: คงที่ทุกธีม */
  --y1:#FFB703; --y2:#FB8500;          /* เหลือง→ส้ม */
  --brand:linear-gradient(135deg,var(--y1),var(--y2));
  --red:#E63946; --red-d:#C1121F;       /* ลดราคา/Flash Sale/ราคา */
  --green:#16A34A; --blue:#0EA5E9; --purple:#7C3AED; --pink:#EC4899; /* เสริมได้ เช่น หมวดละสี */
  --r:12px; --r-lg:20px; --ease:cubic-bezier(.65,0,.25,1);
}
/* ธีมสว่าง (ค่าเริ่มต้น) — เปลี่ยนเฉพาะพื้นผิว/ตัวอักษร */
:root,[data-theme="light"]{
  --bg:#F4F5F7; --sf:#FFFFFF; --sf2:#F0F1F4; --tx:#16181D; --mu:#6B7280; --bd:#E3E5EA;
  --sh:0 2px 10px rgba(16,24,40,.08);
}
[data-theme="dark"]{
  --bg:#0F1115; --sf:#1A1D24; --sf2:#242831; --tx:#F2F3F5; --mu:#9AA1AD; --bd:#2E333D;
  --sh:0 2px 14px rgba(0,0,0,.5);
}
@media (prefers-color-scheme:dark){ :root:not([data-theme]){ /* ใส่ค่าเดียวกับ dark */ } }

body{margin:0;background:var(--bg);color:var(--tx);font-family:"Noto Sans Thai","Sarabun",system-ui,sans-serif}
input,select,textarea{font-size:16px}                 /* กัน iOS ซูม */
button,.btn{min-height:44px;border-radius:var(--r);transition:transform .15s,box-shadow .2s}
.btn:active{transform:scale(.96)}
.btn-primary{background:var(--brand);color:#2b1a00;font-weight:700;border:0}
.btn-danger{background:var(--red);color:#fff}

/* การ์ดสินค้า */
.card{background:var(--sf);border-radius:var(--r);box-shadow:var(--sh);position:relative;transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-6px);box-shadow:0 10px 24px rgba(0,0,0,.18)}
.badge-sale{position:absolute;left:8px;top:8px;background:var(--red);color:#fff;border-radius:8px;padding:2px 8px;font-weight:700}
.p-name{font-weight:700}                 /* ชื่อ: เด่น */
.p-price{color:var(--red);font-weight:800;font-size:1.25rem}   /* ราคา: เด่นสุด */
.p-old{color:var(--mu);text-decoration:line-through;font-size:.85rem}
.p-meta{color:var(--mu);font-size:.8rem}  /* ดาว/จำนวนขาย/สเปก: เล็กและจาง */

/* กริดสินค้า: 2 / 3 / 5 คอลัมน์ */
.grid{display:grid;gap:12px;grid-template-columns:repeat(2,1fr)}
@media(min-width:601px){.grid{grid-template-columns:repeat(3,1fr)}}
@media(min-width:1001px){.grid{grid-template-columns:repeat(5,1fr)}}

/* แอนิเมชัน */
.reveal{opacity:0;transform:translateY(16px);transition:opacity .6s,transform .6s}
.reveal.in{opacity:1;transform:none}
@keyframes pop{0%{transform:scale(.9);opacity:0}100%{transform:scale(1);opacity:1}}
.dialog{animation:pop .3s var(--ease)}
.heart.on{animation:pop .35s}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
```

JS ธีม (จำค่า, ค่าเริ่มต้นตามเครื่อง): `const t=localStorage.getItem('theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'); document.documentElement.dataset.theme=t;` (ห่อ try/catch เผื่อ localStorage ใช้ไม่ได้)

### ภาคผนวก B — โครงหน้าจอ (จากภาพ "ตัวอย่างหน้าแอป" ใน PDF + ข้อความที่สั่ง)

**B.1 หน้าแรกผู้ซื้อ (PC ≥ 1001px)**
```
┌──────────────────────────────────────────────────────────────┐
│ โลโก้ │ [ ค้นหาสินค้า…………… ] │ เปรียบเทียบ ❤ 🛒 🔔 💬 ☀/🌙 │ เข้าสู่ระบบ │  ← แถบบน (เหลือง/ตามธีม)
├──────────────────────────────────────────────────────────────┤
│ ◀  แบนเนอร์ยาว 21:8 เลื่อนอัตโนมัติ 7–10 ภาพ  ▶   ● ○ ○ ○ ○     │  ← ตัวแทน = พื้นไล่สี+ข้อความ
├──────────────────────────────────────────────────────────────┤
│ ⚡ Flash Sale  เหลือ 02:14:09                       ดูทั้งหมด ›│  ← แถบแดง
│ [สินค้าลดราคา][สินค้า][สินค้า][สินค้า][สินค้า]  ← ป้าย −% แดง  │
├──────────────────────────────────────────────────────────────┤
│ หมวดหมู่ [ไม้แบด][รองเท้า][ลูกแบด][กระเป๋า]… ← ปุ่มเหลือง       │
│ แบรนด์    [Yonex][Li-Ning][Victor]…                           │
├──────────────────────────────────────────────────────────────┤
│ สินค้าแนะนำ   5 คอลัมน์ × 3 แถว = 15 ชิ้น      [ดูทั้งหมด]      │
│ ┌────┐┌────┐┌────┐┌────┐┌────┐                               │
│ │รูป ││รูป ││รูป ││รูป ││รูป │  ชื่อ (หนา)                    │
│ │    ││    ││    ││    ││    │  ฿ราคา (แดงใหญ่)  ~~ราคาเดิม~~ │
│ └────┘└────┘└────┘└────┘└────┘  ★4.8 · ขายแล้ว 120 (เล็กจาง)  │
├──────────────────────────────────────────────────────────────┤
│ ส่วนท้ายพื้นเหลือง: ● เกี่ยวกับเรา │ ช่วยเหลือ │ ติดต่อเรา(เบอร์/อีเมล) │ ติดตามเรา (FB/LINE/IG) │
└──────────────────────────────────────────────────────────────┘
```
**มือถือ ≤ 600px:** แถบบนย่อ + ช่องค้นหาเต็มแถวใต้แถบ · แบนเนอร์ปัดนิ้ว · Flash Sale เลื่อนแนวนอน · หมวดเลื่อนแนวนอน · กริด 2 คอลัมน์ · **เมนูล่างติดจอ** (หน้าแรก / หมวดหมู่ / ตะกร้า / ออเดอร์ / ฉัน) ซ่อนเมื่อ ≥ 900px · เว้น safe-area iPhone

**B.2 หน้าสินค้า (UX-4: ชื่อ+ราคาเด่นสุด)**
```
[แกลเลอรีรูป ปัดได้ + รูปย่อ]   ┌ ป้ายหมวด/แบรนด์ (เล็ก)
                                 │ ชื่อสินค้า        ← 28–32px หนา
                                 │ ฿ 3,290   ~~฿3,990~~  [-18%]   ← ราคา 36–40px หนา สีแดง
                                 │ ★4.8 (126 รีวิว) · ขายแล้ว 540  ← เล็ก (≈13px) สีจาง
                                 │ ตัวเลือก: สี ◉◯◯  ด้าม [G4][G5]  เอ็น [..]   ← ปุ่มเลือก
                                 │ จำนวน [− 1 +]   เหลือ 12 ชิ้น
                                 │ [ ❤ ]  [ ใส่ตะกร้า ]  [ ซื้อเลย (ไล่สีเหลือง) ]   ← มือถือ: แถบติดล่าง
สเปก (ตารางเล็ก: น้ำหนัก/จุดสมดุล/ก้าน/ระดับ) → รายละเอียด → รีวิว (ล่างสุด) → สินค้าซื้อคู่ → สินค้าที่คล้ายกัน
```
**B.3 หน้าออเดอร์ของฉัน (BUY-3)** — แท็บเลื่อนแนวนอน พร้อมตัวเลข: `การสั่งซื้อ` → `รอชำระเงิน` → `ชำระเงินแล้ว` → `รอตรวจสลิป` → `จัดส่งแล้ว` → `สำเร็จ` → `รอรีวิว` → `สินค้าที่ยกเลิก` · การ์ดออเดอร์: เลขที่, วันที่, รูปสินค้า, ยอดรวม, ป้ายสถานะ, ปุ่มตามสถานะ (ชำระเงิน/ติดตามพัสดุ/ยืนยันรับของ/รีวิว/ดูใบเสร็จ)

**B.4 เข้าสู่ระบบ / สมัคร / ลืมรหัสผ่าน (ตาม PDF ฉบับล่าสุด)**
```
PC (≥ 901px)  แบ่ง 2 ฝั่งเต็มจอ
┌───────────────────────┬──────────────────────────────────┐
│  พื้นเหลือง (ไล่สี)    │  WELCOME            ← แดง ตัวใหญ่  │
│  ภาพสินค้าตัวอย่าง     │  to the sign-up process ← เล็ก   │
│  เปลี่ยนไปเรื่อยๆ      │  ┌─ กรอบเหลืองมุมโค้ง ───────────┐  │
│  (ครอสเฟดทุก ~4 วิ)    │  │ หัวข้อการ์ด (เปลี่ยนตามสถานะ)   │  │
│  ชื่อ+ราคาสินค้า       │  │ [ อีเมล ]                      │  │
│  จุดบอกตำแหน่ง ● ○ ○   │  │ [ รหัสผ่าน ]  👁               │  │
│                       │  │ [   ปุ่มเหลืองเต็มกว้าง   ]     │  │
│                       │  │ ยังไม่มีบัญชี? สมัครสมาชิก      │  │
│                       │  │ ลืมรหัสผ่าน? · พนักงานลืมรหัส? │  │
│                       │  └───────────────────────────────┘  │
└───────────────────────┴──────────────────────────────────┘
มือถือ (≤ 900px): แผงเหลืองย่อเป็นแถบบนสูง ~180px (ภาพเปลี่ยนเรื่อยๆ เหมือนกัน) แล้วการ์ดฟอร์มเลื่อนทับลงมา เต็มความกว้าง
```
- **ข้อความหัวข้อเปลี่ยนตามสถานการณ์** (ซ้ายมือภาพเปลี่ยน แต่ส่วนขวาใช้โครงเดียวกันทุกหน้า):

| หน้า | หัวใหญ่ (แดง) | หัวรอง | หัวการ์ด | ปุ่มหลัก |
|---|---|---|---|---|
| `/login` | WELCOME | ยินดีต้อนรับกลับ เข้าสู่ระบบเพื่อเริ่มช้อป | ใส่อีเมลและรหัสผ่าน | เข้าสู่ระบบ |
| `/register` | WELCOME | to the sign-up process | สมัครสมาชิก — กรอกข้อมูลของคุณ | ถัดไป / รับรหัสยืนยัน |
| `/register/verify` | ยืนยันอีเมล | เราส่งรหัส 6 หลักไปที่ ab***@gmail.com | กรอกรหัสยืนยัน | ยืนยันและสมัคร |
| `/login` หลังสมัครสำเร็จ | WELCOME | สมัครสำเร็จแล้ว! | แถบเขียว "เข้าสู่ระบบด้วยอีเมลและรหัสผ่านได้เลย" | เข้าสู่ระบบ |
| `/forgot` | ลืมรหัสผ่าน? | ไม่เป็นไร เราจะส่งรหัสให้ทางอีเมล | ใส่อีเมลที่สมัครไว้ | ส่งรหัสยืนยัน |
| `/forgot/verify` | ตั้งรหัสผ่านใหม่ | กรอกรหัส 6 หลักและรหัสผ่านใหม่ | ยืนยันตัวตน | เปลี่ยนรหัสผ่าน |
| `/forgot/staff` | พนักงานลืมรหัสผ่าน | ติดต่อเจ้าของร้านเพื่อรีเซ็ตให้ | ช่องทางติดต่อเจ้าของร้าน | โทร / คัดลอก / กลับหน้าเข้าสู่ระบบ |
| `/login` หลังรีเซ็ต | WELCOME | เปลี่ยนรหัสผ่านแล้ว | แถบเขียว "เข้าสู่ระบบด้วยรหัสใหม่ได้เลย" | เข้าสู่ระบบ |

- ส่วนสมัครใช้ฟอร์มแบบเดิม (ชื่อ, เบอร์, อีเมล, รหัสผ่าน+ยืนยัน, ที่อยู่ตั้งต้น) **เพิ่มขั้นยืนยันอีเมลด้วย OTP** (ช่อง 6 ช่อง วางโค้ดได้ ส่งใหม่ได้ใน 60 วิ "ไม่ได้รับ? ดูกล่อง Junk") → สำเร็จแล้ว **กลับหน้าล็อกอิน** ไม่ล็อกอินให้เอง
- ตัวบอกขั้นในหน้าสมัคร: 1 ข้อมูล · 2 ยืนยันอีเมล
- ช่องกรอกสูง ≥ 48px มีไอคอน, ปุ่มแสดง/ซ่อนรหัสผ่าน, ข้อความผิดพลาดสีแดงใต้ช่อง, ข้อความเตือนใช้ข้อความกลาง ("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
- แผงภาพซ้าย: ใช้สินค้าจริงจาก `/api/login-showcase` (ชื่อ+ราคาตัวใหญ่เด่น) ถ้าไม่มีให้ใช้ตัวแทนพื้นไล่สี; แอนิเมชันครอสเฟด/สไลด์ ≤ 0.7 วิ ใช้ `opacity/transform`; หยุดเมื่อแท็บไม่ active และเมื่อ `prefers-reduced-motion`; รูปแรกโหลดทันที รูปอื่น `loading="lazy"`
- CSS เสริม (ต่อจากภาคผนวก A):
```css
.auth{display:grid;min-height:100dvh;grid-template-columns:1fr 1fr}
.auth-show{position:relative;background:var(--brand);overflow:hidden}
.auth-show .slide{position:absolute;inset:0;opacity:0;transition:opacity .7s var(--ease)}
.auth-show .slide.on{opacity:1}
.auth-main{display:flex;flex-direction:column;justify-content:center;padding:32px;background:var(--bg)}
.auth-h1{color:var(--red);font-size:2.4rem;font-weight:800;margin:0}
.auth-card{border:2px solid var(--y1);border-radius:var(--r-lg);padding:24px;background:var(--sf);max-width:420px}
.notice-ok{background:#E7F7EC;color:#14532D;border-radius:var(--r);padding:10px 14px}
@media(max-width:900px){.auth{grid-template-columns:1fr;grid-template-rows:180px 1fr}.auth-main{padding:16px;margin-top:-24px}}
```

**B.5 หลังบ้าน (PC เท่านั้น)** — sidebar ซ้าย: แดชบอร์ด · ออเดอร์ · ตรวจสลิป · สินค้า(+ถังลบ) · หมวด/แบรนด์ · คูปอง(+กฎซื้อครบ) · แชท · ผู้ใช้ · [owner] ผู้ดูแล · รายจ่าย · แบนเนอร์ · บันทึกกิจกรรม · ส่งออก/สำรอง (+Google Sheets) · ตั้งค่าร้าน/ช่องทางติดต่อ; แถบบนมี "ติดต่อเจ้าของร้าน" (admin) · ต่ำกว่า 1000px แสดงเฉพาะข้อความ "กรุณาใช้งานบนคอมพิวเตอร์"

### ภาคผนวก C — แผนที่ route (Flask)

| กลุ่ม | Path | สิทธิ์ |
|---|---|---|
| สาธารณะ | `/`, `/category/<id>`, `/search`, `/product/<id>`, `/compare`, `/racket-finder`, `/contact`, `/media/<path>` (เฉพาะ `assets/images/**`) | ทุกคน |
| บัญชี | `/login`, `/register`, `/register/verify`, `/register/resend`, `/forgot`, `/forgot/verify`, `/forgot/resend`, `/forgot/staff`, `/logout`, `/api/login-showcase` | ทุกคน (logout = ล็อกอิน) |
| ผู้ซื้อ | `/cart`, `/checkout`, `/orders`, `/orders/<id>`, `/orders/<id>/pay`, `/orders/<id>/receipt.pdf`, `/wishlist`, `/profile`, `/addresses`, `/coupons`, `/notifications`, `/chat`, `/review/<order_item>` | buyer + เจ้าของข้อมูลเท่านั้น |
| API ผู้ซื้อ | `/api/cart/*`, `/api/wishlist/*`, `/api/coupons/claim`, `/api/orders/<id>/qr.png`, `/api/chat/messages?after_id=`, `/api/chat/send`, `/api/chat/quick/<id>`, `/api/chat/recommend` | buyer |
| หลังบ้าน | `/admin/*` (แดชบอร์ด ออเดอร์ ตรวจสลิป สินค้า หมวด แบรนด์ คูปอง แชท ผู้ใช้) | admin, owner + PC เท่านั้น |
| เจ้าของ | `/admin/staff`, `/admin/coupon-rules`, `/admin/deleted-products`, `/admin/expenses`, `/admin/export`, `/admin/export/google-sheets` (POST), `/admin/banners`, `/admin/audit-log`, `/admin/settings`, `/admin/sessions` | owner เท่านั้น |
| อีเมลใบเสร็จ | `/admin/orders/<id>/receipt-email` (GET สถานะ), `/admin/orders/<id>/receipt-email/resend` (POST) | admin, owner |
| อีเมลจัดส่ง (E5) | `/admin/orders/<id>/shipped-email` (GET สถานะ), `/admin/orders/<id>/shipped-email/resend` (POST) | admin, owner |
| API สาธารณะ (E8) | `/api/search/suggest?q=`, `/api/products/by-ids?ids=` | ทุกคน (rate limit ใน Phase 9) |

ข้อบังคับ: สลิป/ใบเสร็จ/ไฟล์ส่งออกเสิร์ฟผ่าน route ตรวจสิทธิ์เท่านั้น ไม่เปิดเป็นไฟล์สาธารณะ · ทุก POST มี CSRF (Phase 9)

### ภาคผนวก D — โค้ดตัวอย่างสำคัญ

**D.1 `core/session.py` แบบ contextvars (ทำให้หลายคนใช้เว็บพร้อมกันไม่ปนกัน)**
```python
import contextvars
_current = contextvars.ContextVar("current_user", default=None)

class Session:
    @classmethod
    def login(cls, user_row):
        _current.set({"id": user_row["id"], "username": user_row["username"],
                      "role": user_row["role"], "full_name": user_row["full_name"]})
    @classmethod
    def logout(cls): _current.set(None)
    @classmethod
    def is_authenticated(cls): return _current.get() is not None
    @classmethod
    def get_user_id(cls):
        u = _current.get(); return u["id"] if u else None
    @classmethod
    def get_role(cls):
        u = _current.get(); return u["role"] if u else None
    # คง API เดิมไว้ทั้งหมด; เพิ่ม current_user เป็น property/ฟังก์ชันอ่านจาก _current
```
เว็บ: `before_request` อ่านคุกกี้ → ตรวจ `sessions` → `Session.login(user)`; `teardown_request` → `Session.logout()` · เทสต์: 2 thread คนละ user ต้องไม่เห็นสิทธิ์กัน · Desktop (CustomTkinter) ยังทำงานได้เพราะเธรดหลักเดียวกัน

**D.2 `ORDER_STATUS_DISPLAY_ORDER` ใน `core/constants.py`**
```python
# (key, ป้าย, tooltip, db_status|None)  — key "all" และ "to_review" เป็นค่าเสมือน ไม่ใช่สถานะใน DB
ORDER_STATUS_DISPLAY_ORDER = (
    ("all",           "การสั่งซื้อ",     "ทุกออเดอร์",                           None),
    ("pending",       "รอชำระเงิน",      "ยังไม่ชำระ/ยังไม่แนบสลิป",             "pending"),
    ("paid",          "ชำระเงินแล้ว",    "แอดมินยืนยันสลิปแล้ว",                 "paid"),
    ("checking_slip", "รอตรวจสลิป",      "แนบสลิปแล้ว รอแอดมินตรวจ",             "checking_slip"),
    ("shipped",       "จัดส่งแล้ว",      "มีเลขพัสดุ",                            "shipped"),
    ("completed",     "สำเร็จ",          "ยืนยันรับของแล้ว",                      "completed"),
    ("to_review",     "รอรีวิว",         "สำเร็จแล้วแต่ยังมีสินค้าที่ไม่ได้รีวิว", None),
    ("cancelled",     "สินค้าที่ยกเลิก", "ยกเลิกแล้ว",                            "cancelled"),
)
MAX_COMPARE = 5
```

**D.3 จุดเสียบอีเมลใบเสร็จ (ต้องอยู่นอก transaction)**
```python
# services/payment_service.py
def verify_payment(payment_id):
    ...                                   # โค้ดเดิม: with transaction() as conn: ... return detail
def verify_payment_and_notify(payment_id):   # ให้ UI/route เรียกตัวนี้
    detail = verify_payment(payment_id)       # commit เสร็จแล้ว
    try:
        email_outbox_service.queue_receipt_email(detail["id"])   # ห้ามทำให้การยืนยันล้ม
    except Exception as exc:
        logger.warning("queue receipt email failed: %s", exc)
    return detail
```
เพื่อไม่แตะลอจิกเดิมของ `verify_payment` และเทสต์เดิม ให้ route/UI เรียก `verify_payment_and_notify` แทน (เทสต์เดิมที่เรียก `verify_payment` ตรงๆ ไม่เปลี่ยนพฤติกรรม)

**D.4 Hook รางวัลคูปอง:** เรียก `coupon_service.issue_reward_coupons(order_id, conn)` ภายใน `order_service.complete_delivery(conn, order, changed_by, by_buyer)` หลังตั้งสถานะ `completed` (อยู่ใน transaction เดียวกับการยืนยันรับของ)

**D.5 แม่แบบอีเมลใบเสร็จ (ย่อ)** — subject: `ยืนยันการชำระเงินออเดอร์ #{id} — {shop_name}`
```
สวัสดีคุณ {full_name},
ร้านได้ตรวจสอบการชำระเงินออเดอร์ #{id} เมื่อ {verified_at} เรียบร้อยแล้ว
รายการสินค้า: {ชื่อ / ตัวเลือก × จำนวน — ราคา}
ยอดสินค้า {subtotal} · ส่วนลด {discount} · ค่าส่ง {shipping}
ยอดรวมที่ชำระ {total} บาท
จัดส่งไปที่: {address}
ขั้นตอนต่อไป: ร้านกำลังเตรียมพัสดุ จะแจ้งเลขพัสดุในแอป
ติดต่อร้าน: {shop_phone} · {shop_email} · LINE {line_name}
แนบ: receipt_{id}.pdf
```
(อีเมลนี้เป็นใบเสร็จที่ระบบสร้าง ไม่ใช่รูปสลิปโอนของลูกค้า)

### ภาคผนวก E — แมปหน้า ↔ service (ฝั่งเว็บเรียกของเดิม ไม่เขียน SQL ใน route)

| หน้า | service ที่เรียก |
|---|---|
| หน้าแรก/หมวด/ค้นหา | `product_service.search_products`, `list_categories`, `list_brands`, `get_best_sellers` (ใหม่), `suggest_products`/`get_cards_by_ids` (E8), `banner_service.list_active_banners` (E2), `settings_service.get_contact_info` (ใหม่) |
| สินค้า | `product_service.get_product_detail`, `review_service`, `wishlist` |
| เปรียบเทียบ / ตัวช่วยเลือกไม้ | `product_service.compare_products` (2–5), `recommend_rackets` |
| ตะกร้า/ชำระ | `cart_service`, `coupon_service.validate_coupon/list_my_coupons`, `order_service.checkout`, `payment_service.get_payment_info/submit_slip` |
| ออเดอร์ | `order_service.list_my_orders/get_order_detail/get_timeline/cancel_order/confirm_received`, `receipt_service.generate_receipt` |
| ที่อยู่/โปรไฟล์ | `account_service` |
| แชท | `chat_service.send_message/get_messages`, `ai_guard`, `ai_service` |
| หลังบ้าน | `order_service.list_orders_admin/get_dashboard_stats`, `payment_service.list_pending_payments/verify_payment_and_notify/reject_payment`, `shipping_service` (`ship_order_and_notify`), `product_service` (CRUD+delete/restore), `coupon_service`, `staff_service`, `expense_service`, `export_service` (+Sheets), `contact_service`, `banner_service`, `audit_service`, `email_outbox_service` |

### ภาคผนวก F — เช็กลิสต์ตัดสินใจเริ่มงาน (ตอบสั้นๆ ได้)

ค่าเริ่มต้นใช้ได้เลยถ้ายังไม่ตอบ (ห้ามเดาเงียบๆ ให้บันทึกในหัวข้อ 13): **D1** เว็บทั้งหมด (Flask+HTML/CSS/JS) · **D2** กันมือถือ+จอเล็ก (+ IP ถ้าตั้ง) · **D11** โฮสต์ตัดสินใจ Phase 9 · **D14** ยืนยันแล้ว · ข้อเสนอ E1–E9 (หัวข้อ 11) **อนุมัติครบทั้งหมดแล้ว (v6)** — ข้อเสนอใหม่ใช้เลข E10+ และรออนุมัติก่อนทำ

### ภาคผนวก G — วิธีแพ็กซิปต่อเฟส (ไม่ส่งความลับ/ข้อมูลลูกค้า)

รันที่โฟลเดอร์รากโปรเจกต์ (ที่มี `main.py`) แล้วแก้รายการไฟล์ตามกล่อง "📦" ของเฟสนั้น:
```bash
# ตัวอย่าง Phase 1
zip -r phase1.zip database/db.py database/repo_users.py database/repo_addresses.py database/repo_settings.py \
  database/repo_base.py database/seed.py services/auth_service.py services/account_service.py \
  services/settings_service.py core config.py utils/validators.py \
  ui/pages/buyer/login.py ui/pages/buyer/register.py tests .env.example \
  -x "*/__pycache__/*" "*.pyc" "*.db" "*.db-wal" "*.db-shm"
```
(Windows PowerShell: `Compress-Archive -Path <ไฟล์...> -DestinationPath phase1.zip` หรือคลิกขวา → ส่งไปยัง → Compressed folder)

**แนบทุกเฟส:** `PROGRESS.md`, `CHANGES_PROGRESS.md` + ซิปของเฟสนั้น
**ห้ามใส่ในซิปเด็ดขาด:** `.env` · `secrets/` · `data/shop.db` และ `data/backups/` · `assets/slips/` · `assets/receipts/` · `data/exports/`
**ควรใส่เสมอ (ถ้าเฟสนั้นมีการรันเทสต์):** `tests/` + `core/` + `config.py` + `database/db.py` เพราะเทสต์ใช้ร่วมกัน
**ถ้า AI บอกว่าขาดไฟล์:** แนบเพิ่มเฉพาะไฟล์ที่ AI ระบุ แล้วให้ AI อัปเดตกล่อง 📦 ของเฟสนั้นให้ครบ จะได้ใช้ครั้งหน้า
