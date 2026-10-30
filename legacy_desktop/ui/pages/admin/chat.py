"""
ui/pages/admin/chat.py
แชทกับลูกค้า (แอดมิน/เจ้าของ) — route `admin_chat` → AdminChatPage
on_show(customer_id=None)  — ส่ง customer_id มาเพื่อเปิดห้องนั้นทันที

ซ้าย: รายการห้องแชท (ใหม่สุดก่อน, ค้นหาได้, ตัวเลขสีแดง = ข้อความที่ยังไม่อ่าน)
ขวา: ข้อความของห้องที่เลือก (ChatMessageList viewer="staff") + ช่องพิมพ์ตอบ (Enter ส่ง)

โพลทุก 3 วินาทีด้วย after() เฉพาะตอนหน้าแสดงอยู่ (winfo_ismapped) — ห้องที่เปิดอยู่ถูกทำเครื่องหมายอ่านให้เองเมื่อโหลดข้อความ
รายการห้องวาดใหม่เฉพาะเมื่อข้อมูลเปลี่ยน (กันกะพริบ) · destroy() ยกเลิกตัวโพลให้
หมายเหตุ: ถ้ามีแอดมิน/เจ้าของออนไลน์ AI จะไม่ตอบแทน — ถ้าไม่มี AI จะตอบลูกค้าเอง (ข้อความ AI แสดงเป็นป้าย AI)
"""

import customtkinter as ctk

from core.constants import SENDER_TYPE_ADMIN, SENDER_TYPE_AI
from services import chat_service
from ui.components.chat_bubble import ChatMessageList
from ui.pages.admin.common import (AdminPage, as_dict, btn, card, color, entry, font, label, page_header, pill, thumb)
from utils.formatters import format_datetime

POLL_MS = 3000
HISTORY_LIMIT = 200
LIST_HEIGHT = 470
PREVIEW_CHARS = 32


def preview_text(thread):
    """ข้อความล่าสุดแบบย่อ มีคำนำหน้าบอกว่าใครพูด"""
    text = " ".join(str(thread.get("last_message") or "").split())
    if len(text) > PREVIEW_CHARS:
        text = text[:PREVIEW_CHARS] + "…"
    sender = thread.get("last_sender_type")
    if sender == SENDER_TYPE_AI:
        return f"AI: {text}"
    if sender == SENDER_TYPE_ADMIN:
        return f"ร้าน: {text}"
    return text


def display_name(thread):
    return thread.get("full_name") or thread.get("username") or f"ลูกค้า #{thread.get('customer_id')}"


class AdminChatPage(AdminPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._customer_id = None
        self._customer_name = ""
        self._threads = []
        self._thread_sig = None
        self._poll_job = None
        self._messages_shown = False

        _header, actions = page_header(self.content, "แชทลูกค้า", "ตอบลูกค้าได้ทันที — ถ้าไม่มีแอดมินออนไลน์ AI จะตอบแทน")
        btn(actions, "🔄 รีเฟรช", self._manual_refresh, kind="outline").pack(side="right")

        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="x")
        body.grid_columnconfigure(0, weight=0, minsize=310)
        body.grid_columnconfigure(1, weight=1)

        # ---- ซ้าย: รายการห้อง
        left = card(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.search_entry = entry(left, "ค้นหาชื่อลูกค้า / ข้อความ")
        self.search_entry.pack(fill="x", padx=10, pady=(10, 6))
        self.search_entry.bind("<KeyRelease>", lambda _e: self._render_threads(force=True))
        self.thread_list = ctk.CTkScrollableFrame(left, fg_color="transparent", height=LIST_HEIGHT, width=270)
        self.thread_list.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        # ---- ขวา: ห้องแชท
        right = card(body)
        right.grid(row=0, column=1, sticky="nsew")
        head = ctk.CTkFrame(right, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(10, 4))
        self.chat_title = ctk.CTkLabel(head, text="เลือกห้องแชททางซ้าย", font=font("h3"), anchor="w")
        self.chat_title.pack(side="left")

        # กรอบสูงคงที่ — ไม่ผูกกับชนิดของ ChatMessageList (เลื่อนในตัวเอง)
        self.holder = ctk.CTkFrame(right, fg_color="transparent", height=LIST_HEIGHT - 70)
        self.holder.pack(fill="x", padx=10)
        self.holder.pack_propagate(False)
        self.placeholder = ctk.CTkLabel(self.holder, text="ยังไม่ได้เลือกห้องแชท\nคลิกชื่อลูกค้าทางซ้ายเพื่อเริ่มตอบ",
                                        font=font("body"), text_color=color("text_muted"), justify="center")
        self.placeholder.pack(expand=True)
        self.messages = ChatMessageList(self.holder, viewer="staff")  # ยังไม่ pack จนกว่าจะเลือกห้อง

        send_row = ctk.CTkFrame(right, fg_color="transparent")
        send_row.pack(fill="x", padx=10, pady=10)
        self.input = entry(send_row, "พิมพ์ข้อความตอบลูกค้า แล้วกด Enter", height=40)
        self.input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input.bind("<Return>", lambda _e: self._send())
        self.send_btn = btn(send_row, "ส่ง ➤", self._send, kind="primary", size="md", width=90)
        self.send_btn.pack(side="left")
        self._set_input_enabled(False)

    # ------------------------------------------------------------------ วงจรหน้า
    def on_show(self, customer_id=None, **kwargs):
        if not self.allowed():
            return
        self.set_error("")
        if customer_id is None and self._customer_id is not None:
            self._fetch_new()  # กลับมาหน้านี้อีกครั้ง → ดึงข้อความที่เข้ามาระหว่างอยู่หน้าอื่น (และทำเครื่องหมายอ่าน)
        self._fetch_threads(force=True)
        if customer_id is not None:
            self._select(customer_id)
        self._start_poll()

    def destroy(self):
        self._cancel_poll()
        super().destroy()

    # ------------------------------------------------------------------ โพล
    def _start_poll(self):
        self._cancel_poll()
        self._poll_job = self.after(POLL_MS, self._poll)

    def _cancel_poll(self):
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except Exception:  # noqa: BLE001
                pass
            self._poll_job = None

    def _poll(self):
        self._poll_job = None
        try:
            if not self.winfo_exists() or not self.winfo_ismapped():
                return  # หน้าไม่ได้แสดงอยู่ → หยุดโพล (on_show จะเริ่มใหม่เมื่อกลับมา)
        except Exception:  # noqa: BLE001
            return
        try:
            # ดึงข้อความใหม่ก่อน (ทำเครื่องหมายอ่านให้ห้องที่เปิดอยู่) แล้วค่อยโหลดรายการห้อง → ป้ายแดงของห้องนี้ไม่ค้าง
            if self._customer_id is not None:
                self._fetch_new()
            self._fetch_threads()
        except Exception:  # noqa: BLE001 - โพลพลาดครั้งเดียวไม่ควรทำให้หน้าพัง
            pass
        self._poll_job = self.after(POLL_MS, self._poll)

    def _manual_refresh(self):
        self.set_error("")
        if self._customer_id is not None:
            self._fetch_new()
        self._fetch_threads(force=True)

    # ------------------------------------------------------------------ รายการห้อง
    def _fetch_threads(self, force=False):
        try:
            rows = chat_service.list_threads()
        except (ValueError, PermissionError) as exc:
            if force:
                self.set_error(str(exc))
            return
        self._threads = [as_dict(r) for r in (rows or [])]
        self._render_threads(force=force)

    def _filtered_threads(self):
        needle = (self.search_entry.get() or "").strip().lower()
        if not needle:
            return self._threads
        return [t for t in self._threads
                if needle in display_name(t).lower() or needle in str(t.get("username") or "").lower()
                or needle in str(t.get("last_message") or "").lower()]

    def _render_threads(self, force=False):
        shown = self._filtered_threads()
        sig = (self._customer_id, tuple((t.get("customer_id"), t.get("last_at"), t.get("unread_count"),
                                         t.get("last_message")) for t in shown))
        if not force and sig == self._thread_sig:
            return
        self._thread_sig = sig
        for child in self.thread_list.winfo_children():
            child.destroy()
        if not shown:
            ctk.CTkLabel(self.thread_list, text="ยังไม่มีการสนทนา" if not self._threads else "ไม่พบห้องที่ค้นหา",
                         font=font("body"), text_color=color("text_muted")).pack(pady=24)
            return
        for thread in shown:
            self._thread_row(thread)

    def _thread_row(self, t):
        customer_id = t.get("customer_id")
        selected = customer_id == self._customer_id
        row = ctk.CTkFrame(self.thread_list, corner_radius=10,
                           fg_color=color("surface_alt") if selected else "transparent")
        row.pack(fill="x", pady=2)
        avatar = thumb(row, t.get("avatar_path"), 38)
        avatar.pack(side="left", padx=(8, 8), pady=8)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=6)
        name = ctk.CTkLabel(info, text=display_name(t), font=font("body_bold"), anchor="w")
        name.pack(fill="x")
        prev = label(info, preview_text(t), "small", muted=True)
        prev.pack(fill="x")
        when = label(info, format_datetime(t.get("last_at")), "tiny", muted=True)
        when.pack(fill="x")
        widgets = [row, avatar, info, name, prev, when]
        unread = int(t.get("unread_count") or 0)
        if unread > 0:
            badge = pill(row, str(unread) if unread < 100 else "99+", "danger")
            badge.pack(side="right", padx=8)
            widgets.append(badge)
        for widget in widgets:
            try:
                widget.configure(cursor="hand2")
            except Exception:  # noqa: BLE001
                pass
            widget.bind("<Button-1>", lambda _e, cid=customer_id: self._select(cid))

    # ------------------------------------------------------------------ ห้องที่เลือก
    def _select(self, customer_id):
        self.set_error("")
        ok, history = self.call(chat_service.get_messages, customer_id, limit=HISTORY_LIMIT)
        if not ok:
            return
        self._customer_id = customer_id
        thread = next((t for t in self._threads if t.get("customer_id") == customer_id), None)
        self._customer_name = display_name(thread) if thread else f"ลูกค้า #{customer_id}"
        self.chat_title.configure(text=f"💬 {self._customer_name}")
        self.placeholder.pack_forget()
        if not self._messages_shown:
            self.messages.pack(fill="both", expand=True)
            self._messages_shown = True
        self.messages.set_messages([as_dict(m) for m in (history or [])])
        self._set_input_enabled(True)
        try:
            self.input.focus_set()
        except Exception:  # noqa: BLE001
            pass
        # ข้อความถูกทำเครื่องหมายอ่านแล้ว → โหลดรายการห้องใหม่ (ตัวเลขแดงหาย) และอัปเดตตัวเลขเมนูข้าง
        self._fetch_threads(force=True)
        self.refresh_shell()

    def _fetch_new(self):
        """ดึงข้อความใหม่ของห้องที่เปิดอยู่ต่อท้าย (ไม่ซ้ำ)"""
        if self._customer_id is None:
            return
        try:
            new_messages = chat_service.get_messages(self._customer_id, after_id=self.messages.last_id)
        except (ValueError, PermissionError):
            return
        added = self.messages.append_messages([as_dict(m) for m in (new_messages or [])])
        if added:
            self.refresh_shell()

    def _set_input_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.input.configure(state=state)
        self.send_btn.configure(state=state)

    # ------------------------------------------------------------------ ส่งข้อความ
    def _send(self):
        if self._customer_id is None:
            return
        text = (self.input.get() or "").strip()
        if not text:
            return
        self.set_error("")
        ok, _ = self.call(chat_service.staff_reply, self._customer_id, text)
        if not ok:
            return  # ข้อความผิดพลาด (เช่น ยาวเกิน) แสดงแล้ว คงข้อความในช่องไว้ให้แก้
        self.input.delete(0, "end")
        self._fetch_new()
        self._fetch_threads(force=True)
