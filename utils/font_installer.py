"""
utils/font_installer.py
ติดตั้งฟอนต์จาก assets/fonts/ (Arimo สำหรับภาษาอังกฤษ/ตัวเลข และ Kanit สำหรับภาษาไทย — T01)
ให้เครื่องผู้ใช้อัตโนมัติตอนเปิดแอปครั้งแรก
รองรับ Windows (per-user ไม่ต้องขอสิทธิ์ Admin), macOS และ Linux

วิธีใช้ (เรียกครั้งเดียวตอนเริ่มโปรแกรม ก่อน ThemeManager.setup()):
    from utils.font_installer import install_project_fonts
    install_project_fonts()
"""
import hashlib
import platform
import shutil
from pathlib import Path

from config import BASE_DIR, FONTS_DIR

PROJECT_ROOT = BASE_DIR
FONTS_SOURCE_DIR = FONTS_DIR

_MARKER_FILE = PROJECT_ROOT / "data" / ".fonts_installed"

ARIMO_WEIGHTS = (
    "Arimo-Regular.ttf",
    "Arimo-Medium.ttf",
    "Arimo-SemiBold.ttf",
    "Arimo-Bold.ttf",
    "Arimo-Italic.ttf",
    "Arimo-MediumItalic.ttf",
    "Arimo-SemiBoldItalic.ttf",
    "Arimo-BoldItalic.ttf",
)

KANIT_WEIGHTS = (
    "Kanit-Regular.ttf",
    "Kanit-Medium.ttf",
    "Kanit-SemiBold.ttf",
    "Kanit-Bold.ttf",
    "Kanit-Light.ttf",
    "Kanit-Italic.ttf",
    "Kanit-MediumItalic.ttf",
    "Kanit-SemiBoldItalic.ttf",
    "Kanit-BoldItalic.ttf",
)


def get_project_font_status() -> dict:
    """ตรวจสอบว่าไฟล์ฟอนต์ Arimo และ Kanit ใน assets/fonts/ มีครบพร้อมใช้งานหรือไม่"""
    arimo_found = [name for name in ARIMO_WEIGHTS if (FONTS_SOURCE_DIR / name).is_file()]
    kanit_found = [name for name in KANIT_WEIGHTS if (FONTS_SOURCE_DIR / name).is_file()]
    return {
        "arimo_ready": (FONTS_SOURCE_DIR / "Arimo-Regular.ttf").is_file(),
        "kanit_ready": (FONTS_SOURCE_DIR / "Kanit-Regular.ttf").is_file(),
        "arimo_files": arimo_found,
        "kanit_files": kanit_found,
    }


def _signature(font_files: list[Path]) -> str:
    """ลายเซ็นของ (เครื่อง + ผู้ใช้ + รายชื่อ/ขนาดไฟล์ฟอนต์)"""
    parts = [platform.node(), platform.system(), str(Path.home())]
    parts += [f"{f.name}:{f.stat().st_size}" for f in font_files]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def _marker_matches(signature: str) -> bool:
    try:
        first_line = _MARKER_FILE.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError):
        return False
    return first_line.strip() == f"signature={signature}"


def install_project_fonts(force: bool = False) -> list[str]:
    """
    ติดตั้งไฟล์ .ttf / .otf ทั้งหมดใน assets/fonts/ (รวมทั้ง Arimo และ Kanit) ให้เครื่องผู้ใช้ปัจจุบัน
    คืนค่า: รายชื่อไฟล์ที่ติดตั้งสำเร็จในรอบนี้ (list ว่างถ้าไม่มีอะไรต้องทำ)
    """
    if not FONTS_SOURCE_DIR.exists():
        return []

    font_files = sorted(
        p for p in FONTS_SOURCE_DIR.iterdir() if p.suffix.lower() in (".ttf", ".otf")
    )
    if not font_files:
        return []

    signature = _signature(font_files)

    if not force and _marker_matches(signature):
        return []

    system = platform.system()
    installed = []

    if system == "Windows":
        installed = _install_fonts_windows(font_files)
    elif system == "Darwin":
        installed = _install_fonts_mac(font_files)
    elif system == "Linux":
        installed = _install_fonts_linux(font_files)
    else:
        return []

    if installed and len(installed) == len(font_files):
        _MARKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        _MARKER_FILE.write_text(
            f"signature={signature}\n" + "\n".join(installed), encoding="utf-8"
        )

    return installed


def _install_fonts_windows(font_files: list[Path]) -> list[str]:
    import ctypes
    import os
    import winreg

    installed = []

    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        return []

    user_fonts_dir = Path(local_appdata) / "Microsoft" / "Windows" / "Fonts"
    user_fonts_dir.mkdir(parents=True, exist_ok=True)

    reg_path = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"

    for font_path in font_files:
        try:
            dest_path = user_fonts_dir / font_path.name
            if not dest_path.exists():
                shutil.copy2(font_path, dest_path)

            kind = "OpenType" if font_path.suffix.lower() == ".otf" else "TrueType"
            font_display_name = f"{font_path.stem} ({kind})"

            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_path) as key:
                winreg.SetValueEx(key, font_display_name, 0, winreg.REG_SZ, str(dest_path))

            ctypes.windll.gdi32.AddFontResourceW(str(dest_path))
            installed.append(font_path.name)
        except Exception as e:  # noqa: BLE001
            print(f"[font_installer] ติดตั้งฟอนต์ {font_path.name} ไม่สำเร็จ: {e}")

    if installed:
        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D
        ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)

    return installed


def _install_fonts_mac(font_files: list[Path]) -> list[str]:
    installed = []
    user_fonts_dir = Path.home() / "Library" / "Fonts"
    user_fonts_dir.mkdir(parents=True, exist_ok=True)

    for font_path in font_files:
        try:
            dest_path = user_fonts_dir / font_path.name
            if not dest_path.exists():
                shutil.copy2(font_path, dest_path)
            installed.append(font_path.name)
        except Exception as e:  # noqa: BLE001
            print(f"[font_installer] ติดตั้งฟอนต์ {font_path.name} ไม่สำเร็จ: {e}")

    return installed


def _install_fonts_linux(font_files: list[Path]) -> list[str]:
    import subprocess

    installed = []
    user_fonts_dir = Path.home() / ".local" / "share" / "fonts"
    user_fonts_dir.mkdir(parents=True, exist_ok=True)

    for font_path in font_files:
        try:
            dest_path = user_fonts_dir / font_path.name
            if not dest_path.exists():
                shutil.copy2(font_path, dest_path)
            installed.append(font_path.name)
        except Exception as e:  # noqa: BLE001
            print(f"[font_installer] ติดตั้งฟอนต์ {font_path.name} ไม่สำเร็จ: {e}")

    if installed:
        try:
            subprocess.run(["fc-cache", "-f", str(user_fonts_dir)], check=False)
        except FileNotFoundError:
            pass

    return installed