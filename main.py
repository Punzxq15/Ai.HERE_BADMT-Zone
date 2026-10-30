"""
main.py
จุดเริ่มโปรแกรม AI.HERE BADᴍᴛ-Zone (เวอร์ชันเว็บ HTML/CSS/JS + FastAPI + SQLite)

    python main.py                          เตรียมฐานข้อมูล + เริ่มเว็บเซิร์ฟเวอร์ + เปิดเบราว์เซอร์อัตโนมัติ
    python main.py --no-browser             เริ่มเว็บเซิร์ฟเวอร์โดยไม่เปิดเบราว์เซอร์
    python main.py --check                  ตรวจความพร้อมก่อนรัน (ไลบรารี, ฐานข้อมูล, ทุก route/หน้าเว็บ, ฟอนต์ไทย, พร้อมเพย์, AI, SMTP)
    python main.py --allow-insecure-defaults อนุญาตให้ bind ภายนอกแม้ยังไม่ได้เปลี่ยนรหัสผ่านเริ่มต้น (ไม่แนะนำ)
"""
import os
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# รองรับโฟลเดอร์ไลบรารีเสริมของสภาพแวดล้อม VM (ถ้ามี)
_PYLIBS = ROOT.parent.parent / "pylibs"
if _PYLIBS.is_dir() and str(_PYLIBS) not in sys.path:
    sys.path.insert(1, str(_PYLIBS))
_LEGACY_DESKTOP = ROOT / "legacy_desktop"
if _LEGACY_DESKTOP.is_dir() and str(_LEGACY_DESKTOP) not in sys.path:
    sys.path.append(str(_LEGACY_DESKTOP))
os.chdir(ROOT)

# (ชื่อ import, ชื่อที่ใช้ติดตั้งด้วย pip)
REQUIRED_LIBS = (
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("multipart", "python-multipart"),
    ("bcrypt", "bcrypt"),
    ("PIL", "pillow"),
    ("qrcode", "qrcode[pil]"),
    ("reportlab", "reportlab"),
    ("openpyxl", "openpyxl"),
    ("dotenv", "python-dotenv"),
)
OPTIONAL_LIBS = (("google.genai", "google-genai"),)

# บัญชีตัวอย่างจาก seed (ใช้ทดสอบเท่านั้น — ต้องเปลี่ยนรหัสผ่านก่อนนำเสนอ/ส่งงาน: FIX-16)
SEED_ACCOUNTS = (("owner", "owner123"), ("admin1", "admin123"), ("buyer1", "buyer123"))
STAFF_SEED_ACCOUNTS = (("owner", "owner123"), ("admin1", "admin123"))


def _missing_libs(libs):
    import importlib
    missing = []
    for module, pip_name in libs:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(pip_name)
    return missing


def _fail(title: str, message: str) -> None:
    """แจ้งข้อผิดพลาดตอนเริ่มระบบลง stderr"""
    print(f"\n[{title}]\n{message}\n", file=sys.stderr)


def prepare_database() -> bool:
    """สร้างโฟลเดอร์ + ตาราง และใส่ข้อมูลตัวอย่างถ้ายังไม่มีผู้ใช้ — คืน True ถ้าเพิ่ง seed"""
    import config
    from database import db, repo_users
    from database.seed import run_seed

    config.ensure_dirs()
    db.init_db()
    if repo_users.list_users():
        return False
    print("ยังไม่มีข้อมูลในระบบ — กำลังใส่ข้อมูลตัวอย่างครั้งแรก...")
    return bool(run_seed(assume_yes=True))


def warn_default_passwords() -> list:
    """เตือนบน console ถ้าบัญชีตัวอย่างยังใช้รหัสผ่านตั้งต้น (FIX-16) — คืนรายชื่อบัญชีที่ยังไม่เปลี่ยน"""
    weak = []
    try:
        from database import repo_users
        from services import auth_service
        for username, password in SEED_ACCOUNTS:
            row = repo_users.get_by_username(username)
            if row and auth_service.verify_password(password, row["password_hash"]):
                weak.append(username)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    if weak:
        print(
            "\n⚠ บัญชีตัวอย่าง " + ", ".join(weak) + " ยังใช้รหัสผ่านตั้งต้น — "
            "ก่อนนำเสนอ/เปิดให้เครื่องอื่นเข้าถึง ให้ล็อกอินแล้วเปลี่ยนรหัสผ่านที่หน้าโปรไฟล์ (ดู README.md)\n"
        )
    return weak


def _has_weak_staff_passwords() -> list[str]:
    weak = []
    try:
        from database import repo_users
        from services import auth_service
        for username, password in STAFF_SEED_ACCOUNTS:
            row = repo_users.get_by_username(username)
            if row and auth_service.verify_password(password, row["password_hash"]):
                weak.append(username)
    except Exception:  # noqa: BLE001
        pass
    return weak


# ---------------------------------------------------------------------------------- --check
def run_check() -> int:
    """ตรวจความพร้อมก่อนรันจริง คืน 0 = ไม่มีข้อผิดพลาด, 1 = มีรายการที่ต้องแก้"""
    problems, notes = [], []

    def ok(msg):
        print(f"  ✔ {msg}")

    def bad(msg):
        problems.append(msg)
        print(f"  ✘ {msg}")

    def note(msg):
        notes.append(msg)
        print(f"  ! {msg}")

    print(f"Python {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        bad("ต้องใช้ Python 3.10 ขึ้นไป")

    print("\n[1] ไลบรารี")
    missing = _missing_libs(REQUIRED_LIBS)
    for pip_name in missing:
        bad(f"ยังไม่ได้ติดตั้ง {pip_name}  →  pip install -r requirements.txt")
    if not missing:
        ok("ไลบรารีหลักครบ (FastAPI, Uvicorn, Pillow, QRCode, ReportLab, OpenPyXL, Bcrypt)")
    for pip_name in _missing_libs(OPTIONAL_LIBS):
        note(f"ไม่มี {pip_name} — แชท AI จะตอบด้วยข้อความสำรอง")
    if missing:
        return 1

    print("\n[2] ฐานข้อมูล")
    try:
        import sqlite3
        import config
        from database import db
        existed = Path(config.DB_PATH).exists()
        config.ensure_dirs()
        db.init_db()
        conn = db.get_connection()
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            fk_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchone()[0]
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        finally:
            conn.close()
        ok(f"{'พบ' if existed else 'สร้างใหม่'} {Path(config.DB_PATH).name}: {tables} ตาราง, ผู้ใช้ {users}, สินค้า {products}")
        if integrity != "ok":
            bad(f"integrity_check: {integrity}")
        if fk_issues:
            bad(f"foreign_key_check พบข้อมูลอ้างอิงเสีย {len(fk_issues)} แถว")
        if users == 0:
            note("ยังไม่มีผู้ใช้ — รัน python main.py ครั้งแรกจะ seed ให้เอง")
    except sqlite3.Error as exc:
        bad(f"เปิดฐานข้อมูลไม่ได้: {exc}")
    except Exception as exc:  # noqa: BLE001
        bad(f"ตรวจฐานข้อมูลไม่สำเร็จ: {exc}")

    print("\n[3] ระบบ API และหน้าเว็บทั้ง 30 หน้า (ROUTE_TABLE)")
    try:
        import config
        from server.app import app
        from server.deps import ROUTE_ROLES, ROUTE_TABLE

        api_routes = [r for r in app.routes if getattr(r, "path", "").startswith("/api/")]
        if len(ROUTE_TABLE) != 30:
            bad(f"ROUTE_TABLE มี {len(ROUTE_TABLE)} หน้า (ต้องมี 30 หน้า)")
        else:
            ok(f"ลงทะเบียนครบ {len(ROUTE_TABLE)} หน้า (กำหนดสิทธิ์เฉพาะ role {len(ROUTE_ROLES)} หน้า) และ {len(api_routes)} API endpoints")

        index_html = config.WEB_DIR / "index.html"
        if not index_html.is_file():
            bad("ไม่พบไฟล์ web/index.html")
        else:
            missing_pages = []
            for route, (js_rel_path, _cls_name) in ROUTE_TABLE.items():
                if not (ROOT / js_rel_path).is_file():
                    missing_pages.append(f"{route} ({js_rel_path})")
            if missing_pages:
                bad(f"ไฟล์หน้าเว็บยังไม่ครบ {len(missing_pages)} หน้า: {', '.join(missing_pages[:5])}")
            else:
                ok("ไฟล์ web/index.html และโมดูล JS ทั้ง 30 หน้าครบถ้วน")
    except Exception as exc:  # noqa: BLE001
        bad(f"ตรวจระบบเว็บ/API ไม่สำเร็จ: {exc}")

    print("\n[4] ตั้งค่าร้าน & PromptPay QR")
    try:
        from services import settings_service
        from utils import promptpay
        info = settings_service.get_shop_info()
        payload = promptpay.build_payload(info["promptpay_no"], 1)
        promptpay.make_qr_image(payload, 120)
        ok(f"พร้อมเพย์ {info['promptpay_no']} สร้าง QR ได้ (ชื่อบัญชี: {info['promptpay_name']})")
        if info["promptpay_no"] == "0812345678":
            note("เลขพร้อมเพย์ยังเป็นค่าตัวอย่าง 0812345678 — เปลี่ยนที่เมนู 'ตั้งค่าร้าน' ก่อนนำเสนอ")
    except Exception as exc:  # noqa: BLE001
        bad(f"ตั้งค่าพร้อมเพย์มีปัญหา: {exc}")

    print("\n[5] ฟอนต์ (Kanit/Arimo สำหรับเว็บและใบเสร็จ PDF), AI และ SMTP")
    try:
        import config
        from services import ai_service, email_service, receipt_service
        from utils.font_installer import get_project_font_status
        fstatus = get_project_font_status()
        if fstatus["kanit_ready"] and fstatus["arimo_ready"]:
            ok(f"พบฟอนต์เว็บใน assets/fonts/ ครบ (Kanit {len(fstatus['kanit_files'])} ไฟล์, Arimo {len(fstatus['arimo_files'])} ไฟล์)")
        else:
            bad("ไม่พบฟอนต์ Kanit หรือ Arimo ใน assets/fonts/")
        font = receipt_service.find_thai_font()
        if font:
            ok("พบฟอนต์ไทยสำหรับออกใบเสร็จ PDF")
        else:
            note("ไม่พบฟอนต์ไทยในเครื่อง — ใบเสร็จ PDF จะออกไม่ได้")
        if ai_service.is_configured():
            ok("ตั้ง GEMINI_API_KEY แล้ว")
        else:
            note("ยังไม่ได้ใส่ GEMINI_API_KEY ใน .env — แชทจะตอบด้วยข้อความสำรองเมื่อไม่มีแอดมินออนไลน์")
        if config.OTP_SECRET_CONFIGURED:
            ok("ตั้งค่า OTP_SECRET (ความยาว >= 32 ตัวอักษร) แล้ว")
        else:
            note("ยังไม่ได้ตั้งค่า OTP_SECRET (>= 32 ตัวอักษร) ใน .env — ระบบใช้คีย์สุ่มชั่วคราวสำหรับโปรเซสนี้")
        if email_service.is_smtp_configured():
            ok("ตั้งค่า SMTP สำหรับส่งอีเมลจริงแล้ว")
        else:
            note("ยังไม่ได้ตั้งค่า SMTP_USER/SMTP_PASSWORD ใน .env — การส่งอีเมล OTP จะแจ้งข้อผิดพลาดจนกว่าจะตั้งค่า SMTP")
    except Exception as exc:  # noqa: BLE001
        bad(f"ตรวจฟอนต์/AI/SMTP ไม่สำเร็จ: {exc}")

    print("\n[6] รหัสผ่านบัญชีตัวอย่าง")
    try:
        from database import repo_users
        from services import auth_service
        weak = [
            u for u, p in SEED_ACCOUNTS
            if (row := repo_users.get_by_username(u)) and auth_service.verify_password(p, row["password_hash"])
        ]
        if weak:
            note("ยังใช้รหัสผ่านตั้งต้น: " + ", ".join(weak) + " — ต้องเปลี่ยนก่อนนำเสนอ/เปิดให้เครื่องอื่นเข้า")
        else:
            ok("ไม่พบบัญชีตัวอย่างที่ใช้รหัสผ่านตั้งต้น")
    except Exception as exc:  # noqa: BLE001
        note(f"ตรวจรหัสผ่านไม่ได้: {exc}")

    print()
    if problems:
        print(f"✘ พบข้อผิดพลาด {len(problems)} รายการ — แก้ก่อนรัน")
        return 1
    print("✔ พร้อมรัน" + (f" (มีข้อควรทราบ {len(notes)} ข้อ)" if notes else ""))
    return 0


# ---------------------------------------------------------------------------------- เปิดเว็บเซิร์ฟเวอร์
def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--check" in argv:
        return run_check()

    missing = _missing_libs(REQUIRED_LIBS)
    if missing:
        _fail(
            "ยังไม่ได้ติดตั้งไลบรารี",
            "ติดตั้งก่อนด้วยคำสั่ง:\n    pip install -r requirements.txt\n\nที่ขาด: " + ", ".join(missing),
        )
        return 1

    try:
        prepare_database()
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        _fail("เริ่มระบบไม่สำเร็จ", f"เตรียมฐานข้อมูลไม่สำเร็จ\n\n{exc}")
        return 1

    import config
    warn_default_passwords()
    config.check_otp_and_smtp_startup_warnings()

    host = config.HOST
    port = config.PORT
    allow_insecure = ("--allow-insecure-defaults" in argv) or config.ALLOW_INSECURE_DEFAULTS
    is_loopback = host in ("127.0.0.1", "localhost", "::1")

    if not is_loopback:
        weak_staff = _has_weak_staff_passwords()
        if weak_staff and not allow_insecure:
            _fail(
                "ปฏิเสธการเปิดเซิร์ฟเวอร์ออกสู่เครือข่ายภายนอก",
                f"คุณตั้งค่า HOST={host} (ไม่ใช่ 127.0.0.1) แต่บัญชีพนักงาน ({', '.join(weak_staff)}) "
                "ยังใช้รหัสผ่านเริ่มต้น (owner123 / admin123)\n"
                "กรุณาเปลี่ยนรหัสผ่านก่อนเปิดให้เครื่องอื่นเข้าถึง หรือใช้ HOST=127.0.0.1",
            )
            return 1

    open_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    url = f"http://{open_host}:{port}"
    print(f"\n🏸 AI.HERE BADᴍᴛ-Zone พร้อมใช้งานที่: {url}\n")

    if "--no-browser" not in argv and os.getenv("NO_BROWSER", "0") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    project_root = str(Path(__file__).resolve().parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    import uvicorn
    from server.app import app as web_app
    uvicorn.run(web_app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
