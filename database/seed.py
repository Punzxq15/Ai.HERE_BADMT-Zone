"""
database/seed.py
ใส่ข้อมูลตัวอย่างสำหรับทดสอบ/นำเสนอ
รันจาก root โปรเจกต์เท่านั้น:
    python -m database.seed            # ใส่ข้อมูลตัวอย่าง (ข้ามถ้ามีผู้ใช้ในระบบแล้ว — ไม่ลบข้อมูลจริง)
    python -m database.seed --reset    # ล้างข้อมูลทั้งหมดแล้วใส่ใหม่ (สำรอง DB ให้ก่อน และถามยืนยัน)
ชั้น database ห้าม import services จึงเข้ารหัสผ่านด้วย bcrypt ในไฟล์นี้โดยตรง
"""
import argparse
from datetime import datetime, timedelta

import bcrypt

import config
from config import DEFAULT_SETTINGS
from core.constants import (
    BALANCES, DISCOUNT_FIXED, DISCOUNT_PERCENT, FLEXES, LEVELS, WEIGHT_CLASSES,  # noqa: F401
)
from database.db import _migrate_v3, get_connection, init_db


def hash_password(password: str) -> str:
    """bcrypt แบบเดียวกับ services.auth_service.hash_password (ผ่านการ verify ร่วมกันได้)"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _now_plus(**delta) -> str:
    """เวลาปัจจุบัน + ช่วงเวลา ในรูปแบบ YYYY-MM-DD HH:MM:SS (เวลาท้องถิ่น)"""
    return (datetime.now() + timedelta(**delta)).strftime("%Y-%m-%d %H:%M:%S")


def seed_users(cursor):
    """เพิ่มข้อมูลผู้ใช้เริ่มต้น 3 แบบ: owner, admin, buyer (รองรับ OWNER_EMAIL/OWNER_INITIAL_PASSWORD จาก .env)"""
    print("Seeding users...")
    owner_email = (config.OWNER_EMAIL or "owner@shop.com").strip().lower()
    owner_pwd = config.OWNER_INITIAL_PASSWORD or "owner123"
    must_change = 1 if config.OWNER_INITIAL_PASSWORD else 0
    users_data = [
        ('owner', owner_email, hash_password(owner_pwd), 'Shop Owner', '0811111111', 'owner', 1, must_change),
        ('admin1', 'admin@shop.com', hash_password('admin123'), 'Shop Admin', '0822222222', 'admin', 1, 0),
        ('buyer1', 'buyer@shop.com', hash_password('buyer123'), 'General Buyer', '0833333333', 'buyer', 1, 0),
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO users
        (username, email, password_hash, full_name, phone, role, email_verified, must_change_password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', users_data)


def seed_categories(cursor):
    """เพิ่มข้อมูลหมวดหมู่สินค้า"""
    print("Seeding categories...")
    categories = ['ไม้แบดมินตัน', 'ลูกแบดมินตัน', 'รองเท้า', 'เสื้อผ้า', 'กระเป๋า', 'เอ็น/ด้ามพัน']
    for cat in categories:
        cursor.execute('INSERT OR IGNORE INTO categories (name, all_brands) VALUES (?, 1)', (cat,))


def seed_brands(cursor):
    """เพิ่มข้อมูลแบรนด์สินค้า"""
    print("Seeding brands...")
    brands = ['Yonex', 'Victor', 'Li-Ning', 'Apacs', 'FZ Forza', 'Venson (VS)']
    for brand in brands:
        cursor.execute('INSERT OR IGNORE INTO brands (name) VALUES (?)', (brand,))


def get_id(cursor, table, name):
    """ฟังก์ชันช่วยเหลือสำหรับดึง ID ของ Category หรือ Brand"""
    cursor.execute(f'SELECT id FROM {table} WHERE name = ?', (name,))
    row = cursor.fetchone()
    return row['id'] if row else None


def seed_products(cursor):
    """เพิ่มข้อมูลสินค้าตัวอย่างประมาณ 25 ชิ้น พร้อมสเปกสำหรับไม้แบดมินตัน"""
    print("Seeding products...")

    badminton_rackets = [
        ('Yonex', 'Astrox 99 Pro', 'ไม้สายบุก หัวหนัก ก้านแข็ง ตบหนักหน่วง', 5200, 4800, _now_plus(days=2), '4U', 'Heavy Head', 'Stiff', 'Advanced'),
        ('Yonex', 'Nanoflare 800', 'ไม้สายสปีด หัวเบา ก้านแข็งปานกลาง สวนกลับเร็ว', 4500, None, None, '3U', 'Light Head', 'Medium', 'Advanced'),
        ('Yonex', 'ArCSaber 11 Pro', 'ไม้คอนโทรล สมดุลทุกด้าน ตีง่าย', 5000, 4700, None, '4U', 'Even Balance', 'Stiff', 'Professional'),
        ('Victor', 'TK Ryuga II Pro', 'ไม้บุกก้านแข็งปานกลาง หัวหนัก', 4900, 4500, _now_plus(days=5), '4U', 'Heavy Head', 'Medium', 'Advanced'),
        ('Victor', 'Auraspeed 100X', 'ไม้สายสปีดหน้าไม้ไวมาก เหมาะกับเล่นคู่', 4800, None, None, '3U', 'Light Head', 'Stiff', 'Advanced'),
        ('Li-Ning', 'Axforce Cannon', 'ไม้บุกคุ้มราคา ตีง่าย ก้านกลาง', 1500, 1290, _now_plus(days=7), '4U', 'Heavy Head', 'Medium', 'Beginner'),
        ('Li-Ning', 'Tectonic 9', 'ไม้หัวหนักปานกลาง ก้านยืดหยุ่นสูง สร้างพลังสปริง', 5500, 5200, None, '4U', 'Heavy Head', 'Flexible', 'Professional'),
        ('Apacs', 'Z-Ziggler', 'ไม้ขวัญใจคนงบน้อย ตบมันส์ ก้านกลาง', 1200, 990, _now_plus(days=-1), '4U', 'Heavy Head', 'Medium', 'Intermediate'),
        ('FZ Forza', 'HT Power 30 V2', 'ไม้บุกจากเดนมาร์ก น้ำหนักดี ก้านกลาง', 2200, None, None, '3U', 'Heavy Head', 'Medium', 'Intermediate'),
        ('Venson (VS)', 'Dragon P', 'ไม้บุกสไตล์ดุดัน สีสันสวยงาม', 1800, 1500, None, '4U', 'Heavy Head', 'Stiff', 'Intermediate'),
    ]

    cat_racket_id = get_id(cursor, 'categories', 'ไม้แบดมินตัน')
    for brand, name, desc, price, sale_price, sale_ends, weight, balance, flex, level in badminton_rackets:
        brand_id = get_id(cursor, 'brands', brand)
        cursor.execute('''
            INSERT INTO products
            (category_id, brand_id, name, description, price, sale_price, sale_ends_at, stock,
             weight_class, balance, flex, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cat_racket_id, brand_id, name, desc, price, sale_price, sale_ends, 50, weight, balance, flex, level))

    shuttlecocks = [
        ('Yonex', 'Aerosensa 30 (AS-30)', 'ลูกขนไก่เกรดแข่งขัน ทนทาน วิถีเป๊ะ', 1050),
        ('Victor', 'Master No.3', 'ลูกขนไก่ยอดฮิตสำหรับซ้อมและแข่ง', 850),
        ('Li-Ning', 'A+ 300', 'ลูกแบดทนทาน วิถีดี', 890),
        ('Venson (VS)', 'VS 100', 'ลูกแบดซ้อมราคาประหยัด', 550),
    ]
    cat_shuttle_id = get_id(cursor, 'categories', 'ลูกแบดมินตัน')
    for brand, name, desc, price in shuttlecocks:
        brand_id = get_id(cursor, 'brands', brand)
        cursor.execute('''
            INSERT INTO products (category_id, brand_id, name, description, price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cat_shuttle_id, brand_id, name, desc, price, 100))

    shoes = [
        ('Yonex', 'Power Cushion 65Z 3', 'รองเท้าแบดมินตันสายสมดุลย์ ยอดฮิต', 3500),
        ('Victor', 'P9200II', 'รองเท้าสายซัพพอร์ต นุ่มกระชับ', 3200),
        ('Li-Ning', 'Ranger 4.0', 'รองเท้าดีไซน์สวย ระบายอากาศดี', 2800),
    ]
    cat_shoes_id = get_id(cursor, 'categories', 'รองเท้า')
    for brand, name, desc, price in shoes:
        brand_id = get_id(cursor, 'brands', brand)
        cursor.execute('''
            INSERT INTO products (category_id, brand_id, name, description, price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cat_shoes_id, brand_id, name, desc, price, 30))

    others = [
        ('เสื้อผ้า', 'Yonex', 'เสื้อแข่งทีมชาติญี่ปุ่น', 'ผ้าระบายอากาศได้ดีเยี่ยม แห้งไว', 1200),
        ('เสื้อผ้า', 'Victor', 'เสื้อซ้อมแบดคอกลม', 'ผ้ากีฬาใส่สบาย', 590),
        ('กระเป๋า', 'Yonex', 'กระเป๋าแบดมินตัน 2 ช่อง BA92226EX', 'ใส่ไม้ได้ 6 ไม้ มีช่องใส่รองเท้า', 2500),
        ('กระเป๋า', 'Li-Ning', 'กระเป๋าเป้สะพายหลัง', 'กระเป๋าเป้ใส่ไม้แบดได้ 2 ไม้', 1500),
        ('เอ็น/ด้ามพัน', 'Yonex', 'เอ็น BG65', 'เอ็นสายทนทานยอดฮิต ขนาด 0.70mm', 220),
        ('เอ็น/ด้ามพัน', 'Yonex', 'เอ็น BG80', 'เอ็นสายบุก เด้งดี ขนาด 0.68mm', 250),
        ('เอ็น/ด้ามพัน', 'Yonex', 'ด้ามพัน AC102EX (แพ็ค 3)', 'กริปพันด้ามหนึบ ยอดนิยมตลอดกาล', 200),
        ('เอ็น/ด้ามพัน', 'Victor', 'ด้ามพัน GR233 (แพ็ค 3)', 'กริปพันด้ามแบบบาง', 180),
    ]
    for cat_name, brand, name, desc, price in others:
        cat_id = get_id(cursor, 'categories', cat_name)
        brand_id = get_id(cursor, 'brands', brand)
        cursor.execute('''
            INSERT INTO products (category_id, brand_id, name, description, price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cat_id, brand_id, name, desc, price, 200))

    cursor.execute('''
        INSERT OR IGNORE INTO category_brands (category_id, brand_id)
        SELECT c.id, b.id FROM categories c CROSS JOIN brands b
    ''')


def get_product_id(cursor, name):
    """ดึง id สินค้าจากชื่อ (ชื่อสินค้าใน seed ไม่ซ้ำกัน)"""
    cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
    row = cursor.fetchone()
    return row['id'] if row else None


def seed_settings(cursor):
    """เพิ่มข้อมูลการตั้งค่าเริ่มต้นของร้าน (ไม่ทับค่าที่ตั้งไว้แล้ว)"""
    print("Seeding settings...")
    cursor.executemany(
        'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
        list(DEFAULT_SETTINGS.items()),
    )


def seed_product_options(cursor):
    """ตัวเลือกสินค้า"""
    print("Seeding product options...")
    options = {
        'Astrox 99 Pro': ('เอ็น', [('ไม่ขึ้นเอ็น', 0, 20), ('ขึ้นเอ็น BG65', 220, 20), ('ขึ้นเอ็น BG80', 250, 10)]),
        'Nanoflare 800': ('สี', [('แดง', 0, 15), ('น้ำเงิน', 0, 15)]),
        'ArCSaber 11 Pro': ('ด้าม', [('G4', 0, 25), ('G5', 0, 25)]),
        'Tectonic 9': ('สี', [('ดำ/ทอง', 0, 3), ('ขาว/แดง', 0, 0)]),
        'Dragon P': ('สี', [('ชมพู', 0, 20), ('เขียว', 0, 20)]),
        'Power Cushion 65Z 3': ('ไซซ์', [('40', 0, 6), ('41', 0, 8), ('42', 0, 8), ('43', 0, 5), ('44', 0, 3)]),
        'P9200II': ('ไซซ์', [('39', 0, 5), ('40', 0, 8), ('41', 0, 8), ('42', 0, 6), ('43', 0, 3)]),
        'Ranger 4.0': ('ไซซ์', [('40', 0, 6), ('41', 0, 8), ('42', 0, 8), ('43', 0, 5), ('44', 0, 3)]),
        'เสื้อแข่งทีมชาติญี่ปุ่น': ('ไซซ์', [('S', 0, 40), ('M', 0, 60), ('L', 0, 60), ('XL', 0, 40)]),
        'เสื้อซ้อมแบดคอกลม': ('ไซซ์', [('M', 0, 70), ('L', 0, 70), ('XL', 0, 60)]),
        'กระเป๋าแบดมินตัน 2 ช่อง BA92226EX': ('สี', [('ดำ', 0, 100), ('น้ำเงิน', 100, 100)]),
    }
    for product_name, (opt_type, items) in options.items():
        product_id = get_product_id(cursor, product_name)
        if product_id is None:
            continue
        for value, extra, stock in items:
            cursor.execute(
                '''INSERT INTO product_options (product_id, option_type, option_value, extra_price, stock)
                   VALUES (?, ?, ?, ?, ?)''',
                (product_id, opt_type, value, extra, stock),
            )
        cursor.execute(
            'UPDATE products SET stock = (SELECT COALESCE(SUM(stock), 0) FROM product_options WHERE product_id = ?) WHERE id = ?',
            (product_id, product_id),
        )


def seed_addons(cursor):
    """สินค้าเสริมขายคู่ ("ซื้อคู่กัน"): ไม้ทุกอันคู่กับเอ็น BG65, ด้ามพัน AC102EX และลูกแบด Master No.3"""
    print("Seeding product addons...")
    addon_ids = [get_product_id(cursor, n) for n in ('เอ็น BG65', 'ด้ามพัน AC102EX (แพ็ค 3)', 'Master No.3')]
    cursor.execute(
        "SELECT p.id FROM products p JOIN categories c ON c.id = p.category_id WHERE c.name = 'ไม้แบดมินตัน'"
    )
    for row in cursor.fetchall():
        for addon_id in addon_ids:
            if addon_id:
                cursor.execute(
                    'INSERT OR IGNORE INTO product_addons (product_id, addon_product_id) VALUES (?, ?)',
                    (row['id'], addon_id),
                )


def seed_coupons(cursor):
    """คูปองตัวอย่าง 3 ใบ"""
    print("Seeding coupons...")
    coupons = [
        ('WELCOME10', DISCOUNT_PERCENT, 10, 500, 100, _now_plus(days=90), 1, 'percent'),
        ('SAVE200', DISCOUNT_FIXED, 200, 2000, 50, _now_plus(days=60), 1, 'fixed'),
        ('OLD50', DISCOUNT_PERCENT, 50, 0, None, _now_plus(days=-1), 0, 'percent'),
    ]
    cursor.executemany(
        '''INSERT OR IGNORE INTO coupons (code, discount_type, value, min_order, max_uses, expires_at, claimable, coupon_category)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        coupons,
    )
    cursor.execute("SELECT COUNT(*) AS n FROM coupon_rules")
    if cursor.fetchone()["n"] == 0:
        cursor.execute(
            '''INSERT INTO coupon_rules
               (name, trigger_min_spend, reward_type, reward_value, reward_min_order, reward_valid_days, is_active)
               VALUES (?, ?, ?, ?, ?, ?, 1)''',
            ('ซื้อครบ 3,000 รับส่วนลด 300 บาท', 3000, DISCOUNT_FIXED, 300, 1000, 30),
        )


def seed_addresses(cursor):
    """ที่อยู่จัดส่งตัวอย่าง 2 ที่ของ buyer1"""
    print("Seeding addresses...")
    cursor.execute("SELECT id FROM users WHERE username = 'buyer1'")
    row = cursor.fetchone()
    if row is None:
        return
    cursor.executemany(
        '''INSERT INTO addresses (user_id, recipient, phone, address_line, district, province, postcode, is_default)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        [
            (row['id'], 'สมชาย รักแบด', '0833333333', '123/45 ซ.สุขใจ ถ.ลาดพร้าว', 'จตุจักร', 'กรุงเทพมหานคร', '10900', 1),
            (row['id'], 'สมชาย (ที่ทำงาน)', '0833333333', '88 อาคารสปอร์ต ชั้น 5 ถ.รัชดาภิเษก', 'ห้วยขวาง', 'กรุงเทพมหานคร', '10310', 0),
        ],
    )


_TABLES_DELETE_ORDER = [
    'login_banners', 'product_images', 'option_values', 'option_groups', 'email_change_otps',
    'coupon_claims', 'coupon_usages', 'coupon_rules', 'category_brands',
    'email_outbox', 'staff_messages', 'expenses', 'banners', 'audit_log',
    'sessions', 'email_otps', 'pending_registrations',
    'product_addons', 'order_status_log', 'order_items', 'payments',
    'shipments', 'reviews', 'wishlist', 'cart_items', 'chat_messages', 'notifications',
    'addresses', 'orders', 'coupons', 'product_options', 'products', 'brands',
    'categories', 'users', 'settings',
]


def clear_existing_data(cursor):
    """ล้างข้อมูลทุกตารางตามลำดับ 'ลูกก่อนแม่' และรีเซ็ต Auto Increment — ใช้เฉพาะ --reset"""
    for table in _TABLES_DELETE_ORDER:
        cursor.execute(f'DELETE FROM {table}')
    cursor.execute(
        "DELETE FROM sqlite_sequence WHERE name IN ({})".format(','.join('?' * len(_TABLES_DELETE_ORDER))),
        _TABLES_DELETE_ORDER,
    )


def run_seed(reset: bool = False, assume_yes: bool = False) -> bool:
    """ใส่ข้อมูลตัวอย่าง คืน True ถ้าใส่ข้อมูลจริง, False ถ้าข้าม/ยกเลิก"""
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT COUNT(*) AS n FROM users')
        has_data = cursor.fetchone()['n'] > 0

        if has_data and not reset:
            print("ข้าม: มีข้อมูลผู้ใช้อยู่ในระบบแล้ว (ไม่ลบข้อมูลเดิม) — ถ้าต้องการล้างแล้วใส่ใหม่ ให้ใช้ --reset")
            return False

        if has_data and reset:
            if not assume_yes:
                print("คำเตือน: --reset จะลบข้อมูลทั้งหมด (ผู้ใช้ สินค้า ออเดอร์ ฯลฯ) แล้วใส่ข้อมูลตัวอย่างใหม่")
                if input("พิมพ์ YES (ตัวพิมพ์ใหญ่) เพื่อยืนยัน: ").strip() != "YES":
                    print("ยกเลิกแล้ว ไม่มีการเปลี่ยนแปลงข้อมูล")
                    return False
            from utils.backup import backup_db
            conn.commit()
            print(f"สำรองฐานข้อมูลไว้ที่ {backup_db()}")
            clear_existing_data(cursor)

        seed_users(cursor)
        seed_categories(cursor)
        seed_brands(cursor)
        seed_products(cursor)
        seed_product_options(cursor)
        seed_addons(cursor)
        seed_coupons(cursor)
        seed_addresses(cursor)
        seed_settings(cursor)
        _migrate_v3(cursor)

        conn.commit()
        print("Seed data successfully inserted into the database!")
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ใส่ข้อมูลตัวอย่างลงฐานข้อมูล")
    parser.add_argument("--reset", action="store_true", help="ล้างข้อมูลทั้งหมดแล้วใส่ใหม่ (ถามยืนยัน)")
    args = parser.parse_args()
    run_seed(reset=args.reset)
