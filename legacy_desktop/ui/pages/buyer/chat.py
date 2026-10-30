"""
ui/pages/buyer/chat.py
หน้าแชทกับร้านและผู้ช่วย AI อัจฉริยะ (AI-1, AI-2, AI-3, AI-4):
- ปุ่มคำถามแนะนำล่วงหน้า (Quick Replies) อิงข้อมูลยอดขายจริงและโปรโมชันปัจจุบัน (AI-2)
- ปุ่ม/โหมด "🤖 ถาม AI โดยเฉพาะ" ที่ใช้งานได้ทันทีแม้มีแอดมินออนไลน์ (AI-4)
- ปุ่ม "🎯 ให้ AI แนะนำไม้ 3 รุ่น" ตามน้ำหนัก จุดสมดุล ก้าน ระดับฝีมือ และงบประมาณ จากสินค้าจริงในร้าน (AI-3)
- ระบบคัดกรองคำถามนอกขอบเขตร้านแบดมินตันอัตโนมัติ (AI-1)
"""

import time

import customtkinter as ctk

from core.constants import BALANCES, FLEXES, LEVELS, SENDER_TYPE_USER, WEIGHT_CLASSES
from services import chat_service
from ui.components.chat_bubble import ChatMessageList
from ui.pages.buyer import common
from ui.theme import ON_PRIMARY, ThemeManager

POLL_MS = 3000
HISTORY_LIMIT = 100
TYPING_TIMEOUT_SEC = 60


class ChatPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._poll_job = None
        self._typing_until = 0.0
        self._force_ai_var = ctk.BooleanVar(value=False)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(14, 4))
        common.page_title(
            head, "💬 แชทกับร้าน & ผู้ช่วย AI แบดมินตัน",
            "สอบถามข้อมูลสินค้า โปรโมชัน การสั่งซื้อ หรือให้ AI ช่วยคัดเลือกไม้แบดมินตันที่เหมาะกับคุณ",
        ).pack(side="left")

        right_head = ctk.CTkFrame(head, fg_color="transparent")
        right_head.pack(side="right")
        self.mode_label = ctk.CTkLabel(
            right_head, text="", font=ThemeManager.get_font("small_bold"),
            anchor="e", justify="right", wraplength=340,
            text_color=ThemeManager.get_color_pair("info"),
        )
        self.mode_label.pack(anchor="e")

        # แถบเครื่องมือ AI & คำถามด่วน (Quick Replies + แนะนำไม้ 3 รุ่น + โหมดถาม AI เฉพาะ)
        ai_toolbar = ThemeManager.make_card(self)
        ai_toolbar.pack(fill="x", padx=16, pady=(2, 4))

        top_bar = ctk.CTkFrame(ai_toolbar, fg_color="transparent")
        top_bar.pack(fill="x", padx=14, pady=(8, 4))
        ctk.CTkLabel(
            top_bar, text="🤖 บริการผู้ช่วย AI:", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            top_bar, text="🎯 ให้ AI แนะนำไม้ 3 รุ่นตามสไตล์คุณ", width=220,
            command=self._open_racket_ai_dialog,
            **ThemeManager.button_style("danger", "sm"),
        ).pack(side="left", padx=(0, 10))

        self.force_ai_switch = ctk.CTkSwitch(
            top_bar, text="ถาม AI ทันที (แม้มีแอดมินออนไลน์)",
            variable=self._force_ai_var,
            font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
            progress_color=ThemeManager.get_color_pair("primary"),
        )
        self.force_ai_switch.pack(side="left", padx=6)

        quick_row = ctk.CTkFrame(ai_toolbar, fg_color="transparent")
        quick_row.pack(fill="x", padx=14, pady=(2, 8))
        ctk.CTkLabel(
            quick_row, text="คำถามยอดฮิต:", font=ThemeManager.get_font("tiny"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(side="left", padx=(0, 6))
        for qr in chat_service.get_quick_replies():
            ctk.CTkButton(
                quick_row, text=qr["label"],
                command=lambda rid=qr["id"]: self._send_quick(rid),
                **ThemeManager.button_style("outline", "sm"),
            ).pack(side="left", padx=3)

        self.messages = ChatMessageList(self, viewer="customer")
        self.messages.pack(fill="both", expand=True, padx=(16, 8), pady=(4, 4))

        self.msg_label = common.error_label(self, wraplength=700)
        self.msg_label.pack(fill="x", padx=20)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(2, 14))
        bar.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(
            bar, placeholder_text="พิมพ์คำถามเกี่ยวกับไม้แบดมินตัน สินค้า โปรโมชัน หรือการสั่งซื้อ...",
            **ThemeManager.entry_style(42),
        )
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<Return>", lambda _e: self._send())
        self.send_btn = ctk.CTkButton(
            bar, text="ส่งข้อความ", width=105, command=lambda: self._send(force_ai=False),
            **ThemeManager.button_style("primary", "md"),
        )
        self.send_btn.grid(row=0, column=1, padx=(8, 4))
        self.ask_ai_btn = ctk.CTkButton(
            bar, text="🤖 ถาม AI", width=105, command=lambda: self._send(force_ai=True),
            **ThemeManager.button_style("info", "md"),
        )
        self.ask_ai_btn.grid(row=0, column=2, padx=(4, 0))

    def on_show(self, **kwargs):
        self.msg_label.configure(text="")
        self.messages.hide_typing()
        self._typing_until = 0.0
        try:
            history = chat_service.get_messages(common.user_id(), limit=HISTORY_LIMIT)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            history = []
        self.messages.set_messages(history)
        self.controller.refresh_shell()
        self._update_mode()
        self._schedule()
        self.entry.focus_set()

    def _update_mode(self):
        try:
            ai_mode = chat_service.should_ai_reply()
        except Exception:  # noqa: BLE001
            return
        self.mode_label.configure(
            text="🤖 ไม่มีแอดมินออนไลน์ — AI พร้อมตอบทันที (หรือกดปุ่ม 🤖 ถาม AI ได้ตลอดเวลา)" if ai_mode
            else "🟢 แอดมินออนไลน์ — ส่งแชทหาแอดมิน หรือกด '🤖 ถาม AI' เพื่อถาม AI ทันที",
        )

    def _schedule(self):
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except Exception:  # noqa: BLE001
                pass
        self._poll_job = self.after(POLL_MS, self._poll)

    def _poll(self):
        self._poll_job = None
        try:
            if not self.winfo_exists():
                return
            if self.winfo_ismapped() and common.user_id() is not None:
                self._fetch_new()
        except Exception:  # noqa: BLE001
            pass
        try:
            self._schedule()
        except Exception:  # noqa: BLE001
            pass

    def _fetch_new(self):
        new = chat_service.get_messages(common.user_id(), after_id=self.messages.last_id)
        if self._typing_until and time.time() > self._typing_until:
            self.messages.hide_typing()
            self._typing_until = 0.0
        if not new:
            return
        self.messages.append_messages(new)
        if any(m["sender_type"] != SENDER_TYPE_USER for m in new):
            self.messages.hide_typing()
            self._typing_until = 0.0
            self._update_mode()
            self.controller.refresh_shell()

    def _send_quick(self, reply_id: str):
        self.msg_label.configure(text="")
        try:
            res = chat_service.answer_quick_reply(common.user_id(), reply_id)
            self.messages.append_messages([res["question"], res["answer"]])
        except Exception as exc:  # noqa: BLE001
            self.msg_label.configure(text=f"⛔ {exc}")

    def _send(self, force_ai: bool = False):
        text = self.entry.get().strip()
        if not text:
            return
        use_ai = bool(force_ai or self._force_ai_var.get())
        self.msg_label.configure(text="")
        try:
            result = chat_service.send_message(common.user_id(), text, force_ai=use_ai)
        except (ValueError, PermissionError) as exc:
            self.msg_label.configure(text=f"⛔ {exc}")
            return
        self.entry.delete(0, "end")
        new_msgs = [result["message"]]
        if result.get("ai_message"):
            new_msgs.append(result["ai_message"])
        self.messages.append_messages(new_msgs)
        if result["ai_pending"]:
            self.messages.show_typing()
            self._typing_until = time.time() + TYPING_TIMEOUT_SEC

    def _open_racket_ai_dialog(self):
        """หน้าต่างให้ผู้ซื้อเลือกสไตล์การเล่น แล้วให้ AI แนะนำไม้แบดมินตัน 3 รุ่นในร้าน (AI-3)"""
        dlg = ctk.CTkToplevel(self)
        dlg.title("🎯 ให้ AI แนะนำไม้แบดมินตัน 3 รุ่นที่เหมาะกับคุณ")
        dlg.geometry("460x470")
        dlg.resizable(False, False)
        dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
        dlg.transient(self.winfo_toplevel())

        hdr = ctk.CTkFrame(dlg, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="🎯 วิเคราะห์และแนะนำไม้แบดมินตัน 3 รุ่น",
            font=ThemeManager.get_font("h3"), text_color=ThemeManager.get_color_pair("primary"),
        ).pack(anchor="w", padx=20, pady=(14, 2))
        ctk.CTkLabel(
            hdr, text="เลือกสเปกที่คุณต้องการ (หรือเว้นว่างให้ระบบคัดรุ่นคุ้มค่าที่สุดในร้าน)",
            font=ThemeManager.get_font("small"), text_color="#FFFFFF",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=22, pady=12)

        any_opt = "ไม่ระบุ (เลือกได้ทุกแบบ)"
        w_var = ctk.StringVar(value=any_opt)
        b_var = ctk.StringVar(value=any_opt)
        f_var = ctk.StringVar(value=any_opt)
        l_var = ctk.StringVar(value=any_opt)

        fields = [
            ("น้ำหนักไม้ (Weight Class)", [any_opt] + list(WEIGHT_CLASSES), w_var),
            ("จุดสมดุล / สไตล์การเล่น (Balance)", [any_opt] + list(BALANCES), b_var),
            ("ความแข็งก้าน (Flex)", [any_opt] + list(FLEXES), f_var),
            ("ระดับผู้เล่น (Level)", [any_opt] + list(LEVELS), l_var),
        ]
        for label, values, var in fields:
            ctk.CTkLabel(
                form, text=label, font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(anchor="w", pady=(4, 1))
            ctk.CTkOptionMenu(
                form, values=values, variable=var, height=34,
                font=ThemeManager.get_font("small"), dropdown_font=ThemeManager.get_font("small"),
                fg_color=ThemeManager.get_color_pair("surface_alt"),
                button_color=ThemeManager.get_color_pair("primary"),
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            form, text="งบประมาณสูงสุด (บาท — ไม่บังคับ)", font=ThemeManager.get_font("small_bold"),
            text_color=ThemeManager.get_color_pair("text_main"),
        ).pack(anchor="w", pady=(4, 1))
        budget_entry = ctk.CTkEntry(form, placeholder_text="เช่น 3500", **ThemeManager.entry_style(36))
        budget_entry.pack(fill="x", pady=(0, 8))

        def submit():
            budget = None
            raw_b = budget_entry.get().strip()
            if raw_b:
                try:
                    budget = float(raw_b)
                except ValueError:
                    pass
            bal_val = None if b_var.get() == any_opt else b_var.get()
            lvl_val = "มือใหม่" if l_var.get() == any_opt else l_var.get()
            style_map = {"หัวหนัก": "attack", "หัวเบา": "speed", "สมดุล": "all_round"}
            style_val = style_map.get(bal_val, "all_round")
            try:
                res = chat_service.recommend_from_form(
                    common.user_id(),
                    level=lvl_val,
                    style=style_val,
                    budget=budget,
                    flex=None if f_var.get() == any_opt else f_var.get(),
                    balance=bal_val,
                    weight_class=None if w_var.get() == any_opt else w_var.get(),
                    post_to_chat=True,
                )
                dlg.destroy()
                if res.get("messages"):
                    self.messages.append_messages(res["messages"])
            except Exception as exc:  # noqa: BLE001
                self.msg_label.configure(text=f"⛔ {exc}")
                dlg.destroy()

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(
            btn_row, text="🤖 ให้ AI แนะนำ 3 รุ่นเลย", command=submit,
            **ThemeManager.button_style("danger", "md"),
        ).pack(side="right")
        ctk.CTkButton(
            btn_row, text="ยกเลิก", width=90, command=dlg.destroy,
            **ThemeManager.button_style("outline", "md"),
        ).pack(side="right", padx=(0, 8))
        dlg.after(120, lambda: dlg.lift())

    def destroy(self):
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except Exception:  # noqa: BLE001
                pass
            self._poll_job = None
        super().destroy()
