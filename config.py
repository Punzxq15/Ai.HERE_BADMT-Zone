"""
config.py
ศูนย์รวม path, การโหลด .env และค่าตั้งต้นของระบบ
ทุกโมดูลต้องอ่าน path จากไฟล์นี้ (ห้ามประกาศ path เอง)
"""
import os
import secrets
from pathlib import Path

# โหลด .env (ถ้าไม่ได้ติดตั้ง python-dotenv ก็ข้ามไป แอปยังรันได้ แค่ไม่มีคีย์ AI/SMTP)
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

# ==========================================
# 1. Path ต่าง ๆ (อิงจากตำแหน่งไฟล์นี้ = root โปรเจกต์)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent

if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "shop.db"
BACKUP_DIR = DATA_DIR / "backups"
EXPORTS_DIR = DATA_DIR / "exports"
MONTHLY_EXPORTS_DIR = EXPORTS_DIR / "monthly"

ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"
BANNER_IMAGES_DIR = IMAGES_DIR / "banners"
LOGIN_BANNERS_DIR = IMAGES_DIR / "login_banners"
CATEGORY_IMAGES_DIR = IMAGES_DIR / "categories"
PRODUCT_IMAGES_DIR = ASSETS_DIR / "images" / "products"
USER_IMAGES_DIR = IMAGES_DIR / "users"
CHAT_IMAGES_DIR = IMAGES_DIR / "chat"
REVIEWS_DIR = ASSETS_DIR / "reviews"
SLIPS_DIR = ASSETS_DIR / "slips"
RECEIPTS_DIR = ASSETS_DIR / "receipts"

WEB_DIR = BASE_DIR / "web"

DEFAULT_LOGIN_BANNER_FILES = (
    "assets/images/login_banners/vs169.png",
    "assets/images/login_banners/power_cushion_shb101cr.png",
)

_ALL_DIRS = (
    DATA_DIR, BACKUP_DIR, EXPORTS_DIR, MONTHLY_EXPORTS_DIR,
    FONTS_DIR, ICONS_DIR, BANNER_IMAGES_DIR, LOGIN_BANNERS_DIR,
    CATEGORY_IMAGES_DIR, PRODUCT_IMAGES_DIR, USER_IMAGES_DIR,
    CHAT_IMAGES_DIR, REVIEWS_DIR, SLIPS_DIR, RECEIPTS_DIR,
)


def ensure_dirs() -> None:
    """สร้างโฟลเดอร์ที่โปรแกรมต้องใช้ (เรียกซ้ำได้)"""
    for folder in _ALL_DIRS:
        folder.mkdir(parents=True, exist_ok=True)
    gitkeep = REVIEWS_DIR / ".gitkeep"
    if not gitkeep.exists():
        try:
            gitkeep.write_text("", encoding="utf-8")
        except OSError:
            pass


# ==========================================
# 2. AI (Gemini) — อ่านจาก .env
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.5-flash"

# ==========================================
# 3. บัญชีเจ้าของร้านและระบบอีเมล (SMTP / OTP) — อ่านจาก .env
#    รองรับทั้ง SMTP_PASSWORD และ SMTP_PASS (เพื่อความเข้ากันได้ย้อนหลัง)
# ==========================================
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "").strip().lower()
OWNER_INITIAL_PASSWORD = os.getenv("OWNER_INITIAL_PASSWORD", "").strip()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip() or "smtp.gmail.com"
try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587").strip() or 587)
except ValueError:
    SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or "").strip()
SMTP_PASS = SMTP_PASSWORD
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "").strip()
SMTP_FROM_EXPLICIT = os.getenv("SMTP_FROM", "").strip()
_default_from_name = SMTP_FROM_NAME or "AI.HERE BADᴍᴛ-Zone"
_default_from_addr = SMTP_USER or OWNER_EMAIL or "noreply@badmintonshop.local"
if SMTP_FROM_EXPLICIT:
    if "<" in SMTP_FROM_EXPLICIT and ">" in SMTP_FROM_EXPLICIT:
        SMTP_FROM = SMTP_FROM_EXPLICIT
    elif SMTP_FROM_NAME:
        SMTP_FROM = f"{SMTP_FROM_NAME} <{SMTP_FROM_EXPLICIT}>"
    else:
        SMTP_FROM = f"{_default_from_name} <{SMTP_FROM_EXPLICIT}>"
else:
    SMTP_FROM = f"{_default_from_name} <{_default_from_addr}>"

# ค่าลับสำหรับทำ HMAC-SHA256 ของรหัส OTP (ควรยาวอย่างน้อย 32 ตัวอักษรใน .env)
OTP_SECRET_RAW = os.getenv("OTP_SECRET", "").strip()
OTP_SECRET_CONFIGURED = len(OTP_SECRET_RAW) >= 32
OTP_SECRET = OTP_SECRET_RAW if OTP_SECRET_RAW else secrets.token_urlsafe(48)

RECEIPT_EMAIL_ENABLED = os.getenv("RECEIPT_EMAIL_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")
SHIPPED_EMAIL_ENABLED = os.getenv("SHIPPED_EMAIL_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")
LOW_STOCK_EMAIL_ENABLED = os.getenv("LOW_STOCK_EMAIL_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")

GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()

# ==========================================
# 4. เว็บเซิร์ฟเวอร์ & หน้าต่างแอป & ความปลอดภัยเครื่องร้าน
# ==========================================
HOST = os.getenv("HOST", "127.0.0.1").strip() or "127.0.0.1"
try:
    PORT = int(os.getenv("PORT", "8000").strip() or 8000)
except ValueError:
    PORT = 8000

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "badminton_session").strip() or "badminton_session"
GUEST_COOKIE_NAME = os.getenv("GUEST_COOKIE_NAME", "badminton_guest").strip() or "badminton_guest"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0").strip().lower() in ("1", "true", "yes", "on")
ALLOW_INSECURE_DEFAULTS = os.getenv("ALLOW_INSECURE_DEFAULTS", "0").strip().lower() in ("1", "true", "yes", "on")

WINDOW_DEFAULT_WIDTH = 1280
WINDOW_DEFAULT_HEIGHT = 800
WINDOW_MIN_WIDTH = 1024
WINDOW_MIN_HEIGHT = 660
try:
    STAFF_IDLE_TIMEOUT_MINUTES = max(1, int(os.getenv("STAFF_IDLE_TIMEOUT_MINUTES", "30").strip() or 30))
except ValueError:
    STAFF_IDLE_TIMEOUT_MINUTES = 30
ADMIN_IDLE_TIMEOUT_MINUTES = STAFF_IDLE_TIMEOUT_MINUTES

# ==========================================
# 5. ไฟล์อัปโหลด (รูปทั่วไป และรูป/วิดีโอรีวิวสินค้า)
# ==========================================
ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
UPLOAD_MAX_SIDE = 1200               # ย่อรูปให้ด้านยาวไม่เกินค่านี้ (พิกเซล)
LOGO_MAX_SIDE = 1024                 # ย่อโลโก้ร้านให้ด้านยาวไม่เกิน 1024 px ตอนบันทึก

# ข้อกำหนดไฟล์รีวิวสินค้า (0–5 ไฟล์รวมกัน รูป + วิดีโอ)
MAX_REVIEW_FILES = 5
ALLOWED_REVIEW_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
ALLOWED_REVIEW_VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov")
MAX_REVIEW_IMAGE_BYTES = 5 * 1024 * 1024    # 5 MB ต่อรูป
MAX_REVIEW_VIDEO_BYTES = 50 * 1024 * 1024   # 50 MB ต่อวิดีโอ

# ==========================================
# 6. สำรองข้อมูล
# ==========================================
BACKUP_KEEP_COUNT = 10  # เก็บไฟล์สำรองล่าสุดกี่ไฟล์

# ==========================================
# 7. ค่าตั้งต้นของตาราง settings (seed และ settings_service ใช้ร่วมกัน)
#    ค่าทุกตัวเก็บเป็นข้อความ (TEXT) ใน DB
# ==========================================
DEFAULT_SETTINGS = {
    "shop_name": "AI.HERE BADᴍᴛ-Zone",
    "promptpay_no": "0812345678",
    "promptpay_name": "นายใจดี รักแบดมินตัน",
    "shipping_fee": "50",               # ค่าส่ง (บาท)
    "free_shipping_min": "0",           # ซื้อครบเท่านี้ส่งฟรี (0 = ไม่เปิดใช้)
    "low_stock_threshold": "5",         # สต็อก <= ค่านี้ = ใกล้หมด
    "unpaid_cancel_hours": "24",        # ออเดอร์ pending เกินกี่ชั่วโมงให้ยกเลิกอัตโนมัติ
    "ai_enabled": "1",                  # 1 = เปิดให้ AI ตอบแชทเมื่อไม่มีแอดมินออนไลน์
    "flash_sale_scroll_speed": "2",     # ความเร็วเลื่อนแถบ Flash Sale (1-10)
    "coupon_rotate_seconds": "9",       # เวลาสลับชุดคูปองหน้าหลัก (วินาที)
    "home_coupons_per_view": "3",       # จำนวนคูปองที่แสดงต่อชุดในหน้าหลัก (1-6)
    "login_showcase_seconds": "5",      # เวลาสุ่มสลับรูปสินค้าหน้า Login (วินาที)
    "custom_coupon_categories": "",     # หมวดหมู่คูปองเพิ่มเติมที่ Owner ตั้งเอง (คั่นด้วยจุลภาค)
    "custom_option_types": "",          # ประเภทตัวเลือกสินค้าเพิ่มเติมที่ Owner ตั้งเอง (คั่นด้วยจุลภาค)
}

CONTACT_DEFAULT_SETTINGS = {
    "shop_logo_path": "",
    "store_logo_path": "",
    "shop_phone": "0812345678",
    "shop_email": "contact@badmintonproshop.com",
    "facebook_name": "Badminton Pro Shop TH",
    "facebook_url": "https://www.facebook.com/badmintonproshop",
    "line_name": "@badmintonpro",
    "instagram_name": "badmintonproshop.th",
    "instagram_url": "https://www.instagram.com/badmintonproshop",
    "shop_address": "99/9 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร 10110",
    "shop_hours": "เปิดทุกวัน 10:00 - 20:00 น.",
    "maps_url": "https://maps.google.com",
    "line_oa_url": "https://line.me",
    "tiktok_name": "@badmintonproshop",
    "tiktok_url": "https://www.tiktok.com",
    "auto_export_dir": "",
    "last_auto_export": "",
    "last_low_stock_email": "",
}


def check_otp_and_smtp_startup_warnings(print_fn=print) -> list[str]:
    """
    ตรวจสอบความพร้อมของ OTP_SECRET และ SMTP ตอนเริ่มระบบ:
    - โหมดจริง (COOKIE_SECURE=1): แจ้งเตือนระดับสำคัญชัดเจนหาก OTP_SECRET หรือ SMTP ยังไม่ได้ตั้งค่า
    - โหมดทดสอบในเครื่อง (COOKIE_SECURE=0): แจ้งเตือนให้ทราบแต่ยังรันเซิร์ฟเวอร์ต่อไปได้ (เมื่อส่งจริงจะตอบข้อผิดพลาด)
    ห้ามพิมพ์ค่าลับลง console เด็ดขาด
    """
    warnings: list[str] = []
    smtp_ready = bool(SMTP_HOST and SMTP_USER and (SMTP_PASSWORD or SMTP_PASS))
    otp_secret_ready = bool(OTP_SECRET_RAW and len(OTP_SECRET_RAW) >= 32)

    if COOKIE_SECURE:
        if not otp_secret_ready:
            warnings.append(
                "[คำเตือนสำคัญ - โหมดใช้งานจริง (COOKIE_SECURE=1)] ยังไม่ได้ตั้งค่า OTP_SECRET (ต้องยาวอย่างน้อย 32 ตัวอักษร) ในไฟล์ .env"
            )
        if not smtp_ready:
            warnings.append(
                "[คำเตือนสำคัญ - โหมดใช้งานจริง (COOKIE_SECURE=1)] ยังไม่ได้ตั้งค่า SMTP_HOST / SMTP_USER / SMTP_PASSWORD ในไฟล์ .env ระบบส่งอีเมล OTP จะไม่สามารถส่งอีเมลได้"
            )
    else:
        if not otp_secret_ready:
            warnings.append(
                "[แจ้งเตือนโหมดทดสอบ (COOKIE_SECURE=0)] ยังไม่ได้ตั้งค่า OTP_SECRET ใน .env (อย่างน้อย 32 ตัวอักษร) — ระบบใช้ค่าสุ่มชั่วคราวสำหรับโปรเซสนี้เท่านั้น"
            )
        if not smtp_ready:
            warnings.append(
                "[แจ้งเตือนโหมดทดสอบ (COOKIE_SECURE=0)] ยังไม่ได้ตั้งค่า SMTP_USER / SMTP_PASSWORD ใน .env — การขอรหัส OTP จะตอบข้อความว่าส่งอีเมลไม่สำเร็จจนกว่าจะตั้งค่า SMTP"
            )

    if print_fn is not None and warnings:
        for w in warnings:
            print_fn(f"⚠ {w}")
    return warnings
