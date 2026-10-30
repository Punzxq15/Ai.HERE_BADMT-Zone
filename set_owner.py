import sqlite3
import config
from services.auth_service import hash_password

if not config.OWNER_EMAIL or not config.OWNER_INITIAL_PASSWORD:
    raise SystemExit("ยังไม่ได้ตั้ง OWNER_EMAIL / OWNER_INITIAL_PASSWORD ใน .env")

c = sqlite3.connect(config.DB_PATH)
n = c.execute(
    "UPDATE users SET email = ?, password_hash = ?, must_change_password = 1 "
    "WHERE username = 'owner' AND role = 'owner'",
    (config.OWNER_EMAIL, hash_password(config.OWNER_INITIAL_PASSWORD)),
).rowcount
c.commit()
c.close()
print("อัปเดตบัญชี owner แล้ว" if n else "ไม่พบบัญชี owner")