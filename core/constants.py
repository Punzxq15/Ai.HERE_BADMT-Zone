"""
core/constants.py
ศูนย์รวมค่าคงที่ (Constants) สำหรับทั้งระบบ เช่น Role, Status ต่างๆ
อ้างอิงตรงกับ Schema ใน database/db.py
"""

# ==========================================
# 1. บทบาทผู้ใช้งาน (User Roles)
# ==========================================
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_BUYER = "buyer"
ROLE_GUEST = "guest"

ALL_ROLES = (ROLE_OWNER, ROLE_ADMIN, ROLE_BUYER)

# ==========================================
# 2. สถานะคำสั่งซื้อ (Order Status)
# ==========================================
ORDER_STATUS_PENDING = "pending"              # รอชำระเงิน
ORDER_STATUS_CHECKING_SLIP = "checking_slip"  # แนบสลิปแล้ว / รอตรวจสอบ
ORDER_STATUS_PAID = "paid"                    # ตรวจสอบแล้ว / ชำระสำเร็จ
ORDER_STATUS_SHIPPED = "shipped"              # จัดส่งสินค้าแล้ว
ORDER_STATUS_COMPLETED = "completed"          # คำสั่งซื้อเสร็จสิ้น
ORDER_STATUS_CANCELLED = "cancelled"          # ยกเลิกคำสั่งซื้อ

ORDER_STATUSES = (
    ORDER_STATUS_PENDING,
    ORDER_STATUS_CHECKING_SLIP,
    ORDER_STATUS_PAID,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_CANCELLED,
)

# ลำดับแท็บแสดงสถานะตามข้อกำหนด PDF (D4):
# การสั่งซื้อ -> รอชำระเงิน -> ชำระเงินแล้ว -> รอตรวจสลิป -> จัดส่งแล้ว -> สำเร็จ -> รอรีวิว -> สินค้าที่คุณยกเลิก
# (key, ป้ายภาษาไทย, คำอธิบาย tooltip, db_status หรือ None สำหรับแท็บคำนวณพิเศษ)
ORDER_STATUS_DISPLAY_ORDER = (
    ("all",           "การสั่งซื้อ",         "คำสั่งซื้อทั้งหมด",                           None),
    ("pending",       "รอชำระเงิน",          "ยังไม่ชำระเงินหรือรอแนบสลิปใหม่",             ORDER_STATUS_PENDING),
    ("paid",          "ชำระเงินแล้ว",        "ตรวจสอบสลิปผ่านแล้ว รอจัดส่ง",                 ORDER_STATUS_PAID),
    ("checking_slip", "รอตรวจสลิป",          "ผู้ซื้อแนบสลิปแล้ว รอแอดมินตรวจสอบ",          ORDER_STATUS_CHECKING_SLIP),
    ("shipped",       "จัดส่งแล้ว",          "ร้านส่งมอบให้ขนส่งพร้อมเลขพัสดุแล้ว",          ORDER_STATUS_SHIPPED),
    ("completed",     "สำเร็จ",              "ผู้ซื้อได้รับสินค้าเรียบร้อยแล้ว",             ORDER_STATUS_COMPLETED),
    ("to_review",     "รอรีวิว",             "คำสั่งซื้อสำเร็จที่ยังมีสินค้ายังไม่ได้เขียนรีวิว", None),
    ("cancelled",     "สินค้าที่คุณยกเลิก",  "รายการคำสั่งซื้อที่ถูกยกเลิก",                 ORDER_STATUS_CANCELLED),
)

# จำนวนไม้สูงสุดที่เปรียบเทียบได้ตามข้อกำหนด PDF (2 ถึง 5 ไม้)
MIN_COMPARE = 2
MAX_COMPARE = 5

# ==========================================
# 3. สถานะการชำระเงิน (Payment Status)
# ==========================================
PAYMENT_STATUS_PENDING = "pending"    # รอตรวจสลิป
PAYMENT_STATUS_VERIFIED = "verified"  # สลิปถูกต้อง
PAYMENT_STATUS_REJECTED = "rejected"  # สลิปไม่ถูกต้อง / ปฏิเสธ

# ==========================================
# 4. สถานะการจัดส่ง (Shipment Status)
# ==========================================
SHIPMENT_STATUS_PREPARING = "preparing"  # กำลังเตรียมพัสดุ
SHIPMENT_STATUS_SHIPPED = "shipped"      # ส่งมอบให้ขนส่งแล้ว
SHIPMENT_STATUS_DELIVERED = "delivered"  # พัสดุส่งถึงปลายทางแล้ว

# ==========================================
# 5. ผู้ส่งข้อความแชท (Chat Sender Types)
# ==========================================
SENDER_TYPE_USER = "user"
SENDER_TYPE_ADMIN = "admin"
SENDER_TYPE_AI = "ai"

# ==========================================
# 6. ประเภทส่วนลดคูปอง และหมวดหมู่คูปอง (Discount Type & Coupon Category)
# ==========================================
DISCOUNT_PERCENT = "percent"  # ลดเป็นเปอร์เซ็นต์
DISCOUNT_FIXED = "fixed"      # ลดเป็นจำนวนเงินคงที่ (บาท)
DISCOUNT_TYPES = (DISCOUNT_PERCENT, DISCOUNT_FIXED)

COUPON_CAT_ALL = "all"
COUPON_CAT_FREE_SHIPPING = "free_shipping"
COUPON_CAT_SHIPPING = COUPON_CAT_FREE_SHIPPING
COUPON_CAT_PERCENT = "percent"
COUPON_CAT_FIXED = "fixed"
COUPON_CAT_OTHER = "other"

COUPON_CATEGORIES = (
    COUPON_CAT_FREE_SHIPPING,
    COUPON_CAT_PERCENT,
    COUPON_CAT_FIXED,
    COUPON_CAT_OTHER,
)

COUPON_CATEGORY_LABELS = {
    COUPON_CAT_ALL: "ทั้งหมด",
    COUPON_CAT_FREE_SHIPPING: "คูปองส่วนลดค่าส่ง",
    COUPON_CAT_PERCENT: "คูปองส่วนลดเป็น %",
    COUPON_CAT_FIXED: "คูปองส่วนลดเป็น บาท",
    COUPON_CAT_OTHER: "และอื่นๆ",
}

# ==========================================
# 7. วิธีชำระเงิน
# ==========================================
PAYMENT_METHOD_PROMPTPAY = "promptpay"

# ==========================================
# 8. ขนส่ง และประเภทตัวเลือกสินค้า
# ==========================================
CARRIERS = ("Kerry Express", "Flash Express", "J&T Express", "ไปรษณีย์ไทย", "Best Express")

OPTION_TYPES = ("สี", "สไตล์", "สี/สไตล์", "ด้าม", "เอ็น", "ไซซ์", "ความเร็ว", "การปรับแต่งไม้")

# ==========================================
# 9. ค่าสเปกไม้แบดเริ่มต้น (Owner ตั้งค่าเพิ่มใน option_groups/option_values ได้)
# ==========================================
WEIGHT_CLASSES = ("3U", "4U")
BALANCES = ("Heavy Head", "Even Balance", "Light Head")
FLEXES = ("Stiff", "Medium", "Flexible")
LEVELS = ("Beginner", "Intermediate", "Advanced", "Professional")

# หัวข้อ Technical Specifications ของไม้แบดมินตัน (T03)
RACKET_TECH_SPEC_FIELDS = (
    ("spec_material", "Material"),
    ("spec_weight_grip", "Weight Class / Grip"),
    ("spec_balance_point", "Balance Point"),
    ("flex", "Shaft Flexibility"),
    ("spec_max_tension", "Max String Tension"),
    ("spec_length", "Length"),
    ("level", "Skill Level"),
)

# ==========================================
# 10. ป้ายข้อความภาษาไทยของสถานะ (แสดงบนหน้าจอ)
# ==========================================
ORDER_STATUS_LABELS = {
    ORDER_STATUS_PENDING: "รอชำระเงิน",
    ORDER_STATUS_CHECKING_SLIP: "รอตรวจสลิป",
    ORDER_STATUS_PAID: "ชำระเงินแล้ว",
    ORDER_STATUS_SHIPPED: "จัดส่งแล้ว",
    ORDER_STATUS_COMPLETED: "สำเร็จ",
    ORDER_STATUS_CANCELLED: "ยกเลิก",
}

PAYMENT_STATUS_LABELS = {
    PAYMENT_STATUS_PENDING: "รอตรวจสอบ",
    PAYMENT_STATUS_VERIFIED: "ตรวจสอบแล้ว",
    PAYMENT_STATUS_REJECTED: "สลิปไม่ถูกต้อง",
}

SHIPMENT_STATUS_LABELS = {
    SHIPMENT_STATUS_PREPARING: "กำลังเตรียมพัสดุ",
    SHIPMENT_STATUS_SHIPPED: "ส่งมอบขนส่งแล้ว",
    SHIPMENT_STATUS_DELIVERED: "ส่งถึงปลายทางแล้ว",
}

ROLE_LABELS = {
    ROLE_OWNER: "เจ้าของร้าน",
    ROLE_ADMIN: "แอดมิน",
    ROLE_BUYER: "ผู้ซื้อ",
    ROLE_GUEST: "ผู้เยี่ยมชม",
}

ORDER_TAB_AWAITING_REVIEW = "to_review"
