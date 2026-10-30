"""
core/session.py
จัดการข้อมูล Session ผู้ใช้งานปัจจุบันด้วย contextvars.ContextVar (แยกอิสระต่อคำขอ/ต่อผู้ใช้บนเว็บ)
พร้อมคง API เดิมทุกตัวสำหรับชั้น services/permissions/tests:
- ล็อกอินปกติ (buyer / admin / owner)
- โหมดผู้เยี่ยมชม (guest_mode) สำหรับเปิดดูหน้าร้านสาธารณะโดยยังไม่ล็อกอิน
- ติดตามเวลาใช้งานล่าสุด (last_activity_at) และการล็อกหน้าจอชั่วคราว (is_locked) สำหรับเครื่องร้านที่ใช้ร่วมกัน
- เก็บ session_token สำหรับเซสชันถาวรและซิงค์สถานะ lock/idle ข้ามคำขอ HTTP ตาม session_token
"""
import contextvars
import threading
import time

_cv_current_user: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "session_current_user", default=None
)
_cv_guest_mode: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "session_guest_mode", default=False
)
_cv_is_locked: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "session_is_locked", default=False
)
_cv_session_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "session_token", default=None
)
_cv_last_activity_at: contextvars.ContextVar[float] = contextvars.ContextVar(
    "session_last_activity_at", default=0.0
)

# เก็บสถานะ runtime (is_locked, last_activity_at) ต่อ session_token เพื่อให้คงอยู่ข้าม HTTP request
_TOKEN_STATE_LOCK = threading.Lock()
_TOKEN_RUNTIME_STATE: dict[str, dict] = {}


def _sync_to_token_store() -> None:
    token = _cv_session_token.get()
    if not token:
        return
    with _TOKEN_STATE_LOCK:
        _TOKEN_RUNTIME_STATE[token] = {
            "is_locked": bool(_cv_is_locked.get()),
            "last_activity_at": float(_cv_last_activity_at.get() or 0.0),
        }


class _SessionMeta(type):
    @property
    def current_user(cls) -> dict | None:
        return _cv_current_user.get()

    @current_user.setter
    def current_user(cls, value: dict | None) -> None:
        _cv_current_user.set(dict(value) if isinstance(value, dict) else value)

    @property
    def guest_mode(cls) -> bool:
        return bool(_cv_guest_mode.get())

    @guest_mode.setter
    def guest_mode(cls, value: bool) -> None:
        _cv_guest_mode.set(bool(value))

    @property
    def is_locked(cls) -> bool:
        return bool(_cv_is_locked.get())

    @is_locked.setter
    def is_locked(cls, value: bool) -> None:
        _cv_is_locked.set(bool(value))
        _sync_to_token_store()

    @property
    def session_token(cls) -> str | None:
        return _cv_session_token.get()

    @session_token.setter
    def session_token(cls, value: str | None) -> None:
        _cv_session_token.set(value)

    @property
    def last_activity_at(cls) -> float:
        return float(_cv_last_activity_at.get() or 0.0)

    @last_activity_at.setter
    def last_activity_at(cls, value: float) -> None:
        _cv_last_activity_at.set(float(value or 0.0))
        _sync_to_token_store()


class Session(metaclass=_SessionMeta):
    """
    คลาสจัดการ Session ที่เก็บสถานะใน ContextVar ต่อคำขอ
    รองรับการเข้าถึงทั้งแบบเมธอด (Session.login, Session.get_user_id, ...)
    และแบบ attribute (Session.current_user, Session.is_locked, ...) เหมือนเดิมทุกประการ
    """

    @classmethod
    def login(cls, user_row, session_token: str | None = None):
        """
        ตั้งค่า current_user เมื่อเข้าสู่ระบบสำเร็จ
        :param user_row: ข้อมูลจากฐานข้อมูล (sqlite3.Row หรือ dict)
        :param session_token: โทเค็นเซสชันในตาราง sessions (ถ้ามี)
        """
        def _val(key, default=None):
            try:
                return user_row[key]
            except (KeyError, IndexError, TypeError):
                return default

        now = time.time()
        _cv_current_user.set({
            "id": _val("id"),
            "username": _val("username"),
            "email": _val("email"),
            "role": _val("role"),
            "full_name": _val("full_name"),
            "phone": _val("phone"),
            "avatar_path": _val("avatar_path"),
            "must_change_password": bool(_val("must_change_password", 0)),
        })
        _cv_guest_mode.set(False)
        _cv_is_locked.set(False)
        _cv_session_token.set(session_token)
        _cv_last_activity_at.set(now)
        _sync_to_token_store()

    @classmethod
    def bind_request_session(cls, user_row, session_token: str | None = None, touch: bool = False):
        """
        ผูกข้อมูลผู้ใช้จากคุกกี้เข้ากับ ContextVar ของคำขอปัจจุบัน โดยคงค่า is_locked และ last_activity_at เดิมของ token
        """
        def _val(key, default=None):
            try:
                return user_row[key]
            except (KeyError, IndexError, TypeError):
                return default

        now = time.time()
        saved = None
        if session_token:
            with _TOKEN_STATE_LOCK:
                saved = _TOKEN_RUNTIME_STATE.get(session_token)

        is_locked = bool(saved["is_locked"]) if saved else False
        last_act = float(saved["last_activity_at"]) if saved and saved.get("last_activity_at") else now
        if touch and not is_locked:
            last_act = now

        _cv_current_user.set({
            "id": _val("id"),
            "username": _val("username"),
            "email": _val("email"),
            "role": _val("role"),
            "full_name": _val("full_name"),
            "phone": _val("phone"),
            "avatar_path": _val("avatar_path"),
            "must_change_password": bool(_val("must_change_password", 0)),
        })
        _cv_guest_mode.set(False)
        _cv_is_locked.set(is_locked)
        _cv_session_token.set(session_token)
        _cv_last_activity_at.set(last_act)
        _sync_to_token_store()

    @classmethod
    def enter_guest(cls):
        """เข้าสู่โหมดผู้เยี่ยมชม (ดูสินค้า/คูปอง/เปรียบเทียบไม้ได้ แต่ทำธุรกรรมบัญชีไม่ได้)"""
        _cv_current_user.set(None)
        _cv_guest_mode.set(True)
        _cv_is_locked.set(False)
        _cv_session_token.set(None)
        _cv_last_activity_at.set(time.time())

    @classmethod
    def logout(cls):
        """ล้างค่าผู้ใช้ปัจจุบันและสถานะทั้งหมดเมื่อออกจากระบบ"""
        old_token = _cv_session_token.get()
        if old_token:
            with _TOKEN_STATE_LOCK:
                _TOKEN_RUNTIME_STATE.pop(old_token, None)
        cls.clear_context()

    @classmethod
    def clear_context(cls):
        """ล้างเฉพาะ ContextVar ของคำขอปัจจุบัน (ไม่ลบสถานะใน _TOKEN_RUNTIME_STATE)"""
        _cv_current_user.set(None)
        _cv_guest_mode.set(False)
        _cv_is_locked.set(False)
        _cv_session_token.set(None)
        _cv_last_activity_at.set(0.0)

    @classmethod
    def touch(cls):
        """บันทึกเวลาที่ผู้ใช้ขยับเมาส์หรือกดแป้นพิมพ์ล่าสุด (ใช้ตรวจ idle timeout)"""
        _cv_last_activity_at.set(time.time())
        _sync_to_token_store()

    @classmethod
    def lock(cls):
        """ล็อกหน้าจอชั่วคราว (ใช้กับเครื่องในร้านเมื่อไม่มีการใช้งานเกินกำหนด หรือกดล็อกหน้าจอ)"""
        if _cv_current_user.get() is not None:
            _cv_is_locked.set(True)
            _sync_to_token_store()

    @classmethod
    def unlock(cls):
        """ปลดล็อกหน้าจอหลังยืนยันรหัสผ่านถูกต้อง"""
        _cv_is_locked.set(False)
        _cv_last_activity_at.set(time.time())
        _sync_to_token_store()

    @classmethod
    def idle_seconds(cls) -> float:
        """จำนวนวินาทีที่ไม่มีการใช้งานนับจาก touch() ล่าสุด"""
        last = float(_cv_last_activity_at.get() or 0.0)
        if not last:
            return 0.0
        return max(0.0, time.time() - last)

    @classmethod
    def is_authenticated(cls) -> bool:
        """
        ตรวจสอบสถานะการล็อกอินจริง (ผู้เยี่ยมชม guest_mode ไม่นับว่าล็อกอิน)
        :return: True ถ้ามีผู้ใช้งานล็อกอินอยู่, False ถ้าไม่มี
        """
        return _cv_current_user.get() is not None

    @classmethod
    def is_guest(cls) -> bool:
        """อยู่ในโหมดผู้เยี่ยมชมหรือไม่"""
        return _cv_current_user.get() is None and bool(_cv_guest_mode.get())

    @classmethod
    def get_user_id(cls) -> int | None:
        """
        ดึง id ของผู้ใช้งานปัจจุบัน
        :return: int หรือ None ถ้ายังไม่ล็อกอิน
        """
        user = _cv_current_user.get()
        if user is not None:
            return user.get("id")
        return None

    @classmethod
    def get_role(cls) -> str | None:
        """
        ดึงบทบาท (Role) ของผู้ใช้งานปัจจุบัน
        :return: string ('owner', 'admin', 'buyer') หรือ None
        """
        user = _cv_current_user.get()
        if user is not None:
            return user.get("role")
        return None