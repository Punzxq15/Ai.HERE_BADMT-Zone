"""
ui/components/chat_bubble.py
- ChatBubble      : ฟองข้อความเดียว (ของเรา = เหลืองชิดขวา, ของอีกฝ่าย = ขาวชิดซ้าย, AI = ฟ้า)
- ChatMessageList : รายการข้อความที่เลื่อนได้ + ต่อข้อความใหม่แบบไม่ซ้ำ (ใช้กับการโพลทุก 3 วินาที)

ข้อความ (dict จาก chat_service.get_messages): id, sender_type ('user'|'admin'|'ai'), sender_name, message, created_at

ใช้งาน:
    chat = ChatMessageList(parent, viewer="customer")      # หน้าผู้ซื้อ  (หน้าแอดมิน: viewer="staff")
    chat.set_messages(chat_service.get_messages(uid))       # โหลดครั้งแรก
    # ทุก 3 วินาที:
    chat.append_messages(chat_service.get_messages(uid, after_id=chat.last_id))
    chat.show_typing("🤖 AI กำลังพิมพ์...") / chat.hide_typing()

ทดสอบเดี่ยว:  python -m ui.components.chat_bubble   (รันจาก root โปรเจกต์)
"""

import customtkinter as ctk

from ui.theme import ThemeManager
from utils.formatters import format_datetime

SENDER_USER, SENDER_ADMIN, SENDER_AI = "user", "admin", "ai"


def _get(msg, key, default=None):
    try:
        value = msg[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if value is None else value


class ChatBubble(ctk.CTkFrame):
    def __init__(self, parent, message, is_mine=False, wraplength=380):
        super().__init__(parent, fg_color="transparent")
        sender = _get(message, "sender_type", SENDER_USER)

        if is_mine:
            bg, fg, meta = ThemeManager.get_color_pair("primary"), "#1A1A1A", "#4A4A4A"
            border = bg
        elif sender == SENDER_AI:
            bg, fg = ThemeManager.badge_colors("info")
            meta = fg
            border = bg
        else:
            bg = ThemeManager.get_color_pair("surface")
            fg = ThemeManager.get_color_pair("text_main")
            meta = ThemeManager.get_color_pair("text_muted")
            border = ThemeManager.get_color_pair("border")

        bubble = ctk.CTkFrame(self, fg_color=bg, corner_radius=14, border_width=1, border_color=border)
        bubble.pack(anchor="e" if is_mine else "w", padx=(60 if is_mine else 0, 0 if is_mine else 60))

        if not is_mine:
            ctk.CTkLabel(
                bubble, text=self._sender_text(message, sender), font=ThemeManager.get_font("small_bold"),
                text_color=meta, anchor="w",
            ).pack(fill="x", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            bubble, text=str(_get(message, "message", "")), font=ThemeManager.get_font("body"),
            text_color=fg, justify="left", anchor="w", wraplength=wraplength,
        ).pack(fill="x", padx=12, pady=(6 if is_mine else 2, 0))

        ctk.CTkLabel(
            bubble, text=format_datetime(_get(message, "created_at")), font=ThemeManager.get_font("tiny"),
            text_color=meta, anchor="e",
        ).pack(fill="x", padx=12, pady=(2, 6))

    @staticmethod
    def _sender_text(message, sender):
        name = _get(message, "sender_name")
        if sender == SENDER_AI:
            return "🤖 ผู้ช่วย AI"
        if sender == SENDER_ADMIN:
            return f"ผู้ดูแลร้าน{f' · {name}' if name else ''}"
        return name or "ลูกค้า"


class ChatMessageList(ctk.CTkScrollableFrame):
    def __init__(self, parent, viewer="customer", empty_text="ยังไม่มีข้อความ — เริ่มสนทนาได้เลย", **kwargs):
        """viewer: 'customer' (ข้อความของ user = ของเรา) | 'staff' (ข้อความของ admin = ของเรา)"""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(parent, **kwargs)
        self._viewer = viewer
        self._empty_text = empty_text
        self._seen = set()
        self.last_id = 0
        self._empty_label = None
        self._typing_label = None
        self._show_empty()

    # ------------------------------------------------------------------ API
    def set_messages(self, messages):
        """แทนที่ทั้งรายการ"""
        self.clear()
        self.append_messages(messages)

    def append_messages(self, messages) -> int:
        """เพิ่มเฉพาะข้อความที่ยังไม่เคยแสดง — คืนจำนวนที่เพิ่ม"""
        added = 0
        for msg in messages or []:
            msg_id = _get(msg, "id")
            if msg_id is not None:
                if msg_id in self._seen:
                    continue
                self._seen.add(msg_id)
                self.last_id = max(self.last_id, int(msg_id))
            if self._empty_label is not None:
                self._empty_label.destroy()
                self._empty_label = None
            ChatBubble(self, msg, is_mine=self._is_mine(msg)).pack(fill="x", padx=8, pady=3)
            added += 1
        if added:
            self._keep_typing_last()
            self.scroll_to_bottom()
        return added

    def clear(self):
        for child in self.winfo_children():
            child.destroy()
        self._seen.clear()
        self.last_id = 0
        self._typing_label = None
        self._empty_label = None
        self._show_empty()

    def show_typing(self, text="🤖 AI กำลังพิมพ์..."):
        if self._typing_label is None:
            self._typing_label = ctk.CTkLabel(
                self, text=text, font=ThemeManager.get_font("small"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_muted"))
        else:
            self._typing_label.configure(text=text)
        self._keep_typing_last()
        self.scroll_to_bottom()

    def hide_typing(self):
        if self._typing_label is not None:
            self._typing_label.destroy()
            self._typing_label = None

    def scroll_to_bottom(self):
        # รอให้ layout คำนวณขนาดก่อน แล้วค่อยเลื่อน
        self.after(60, self._scroll_now)

    # ------------------------------------------------------------------ ภายใน
    def _is_mine(self, msg) -> bool:
        sender = _get(msg, "sender_type", SENDER_USER)
        return sender == (SENDER_USER if self._viewer == "customer" else SENDER_ADMIN)

    def _show_empty(self):
        self._empty_label = ctk.CTkLabel(
            self, text=self._empty_text, font=ThemeManager.get_font("small"),
            text_color=ThemeManager.get_color_pair("text_muted"))
        self._empty_label.pack(pady=30)

    def _keep_typing_last(self):
        if self._typing_label is not None:
            self._typing_label.pack_forget()
            self._typing_label.pack(fill="x", padx=12, pady=(2, 6))

    def _scroll_now(self):
        try:
            if self.winfo_exists():
                self._parent_canvas.yview_moveto(1.0)
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    ThemeManager.setup()
    root = ctk.CTk()
    root.geometry("520x560")
    chat = ChatMessageList(root, viewer="customer")
    chat.pack(fill="both", expand=True, padx=10, pady=10)
    chat.set_messages([
        dict(id=1, sender_type="user", sender_name="buyer1", message="สวัสดีครับ ไม้ Astrox 99 Pro มีของไหม", created_at="2026-10-12 10:00:00"),
        dict(id=2, sender_type="ai", message="สวัสดีค่ะ ขณะนี้มีสินค้าพร้อมส่งค่ะ", created_at="2026-10-12 10:00:05"),
        dict(id=3, sender_type="admin", sender_name="admin1", message="แอดมินเข้ามาแล้วครับ ต้องการน้ำหนักกี่ U?", created_at="2026-10-12 10:02:00"),
    ])
    chat.append_messages([dict(id=3, sender_type="admin", message="ซ้ำ ไม่ควรแสดง", created_at="2026-10-12 10:02:00")])
    chat.show_typing()
    root.mainloop()
