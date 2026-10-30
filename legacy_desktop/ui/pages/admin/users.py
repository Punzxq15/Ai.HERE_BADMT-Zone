"""
ui/pages/admin/users.py
จัดการผู้ใช้และบัญชีพนักงานแอดมิน (เจ้าของร้านเท่านั้น — ปรับปรุงตามข้อ 12 และ T13):
- T13:
  1. ปุ่ม "ดูข้อมูล" ของแถวเจ้าของร้าน (และปุ่มท้ายแถวอื่นๆ) เว้นระยะห่างจากขอบขวา (padding) พอดี ไม่ชิดขอบขวาเกินไป
  2. สถานะแสดงเป็น badge สีชัดเจน:
     * ออฟไลน์ = สีเทา (offline)
     * ออนไลน์ = สีเขียว (online)
     * ถูกระงับ = สีแดง (suspended)
- ปุ่มตั้งรหัส / ระงับ และการกำหนดสิทธิ์แอดมินเดิม คงเดิมทั้งหมด
"""

import customtkinter as ctk

from core.constants import ROLE_ADMIN, ROLE_BUYER, ROLE_LABELS, ROLE_OWNER
from core.session import Session
from services import auth_service, staff_service
from ui.components import dialogs
from ui.components.search_bar import SearchBar
from ui.pages.admin.common import (
    AdminPage, Pager, as_dict, btn, card, color, empty_state, entry, font, label,
    option_menu, page_header, pill, table_header, table_row, thumb,
)
from ui.theme import ThemeManager
from utils.formatters import format_date_thai, format_datetime, format_phone, format_price

PAGE_SIZE = 15
ALL_ROLES = "ทุกบทบาท"
ROLE_KINDS = {ROLE_OWNER: "warning", ROLE_ADMIN: "info", ROLE_BUYER: "muted"}
# ผู้ใช้ | อีเมล/เบอร์ | บทบาท | สถานะ | สมัครเมื่อ | ปุ่มจัดการ (เว้นระยะขอบขวาชัดเจนตาม T13)
COLS = [(3, 170), (3, 180), (0, 95), (0, 110), (1, 100), (0, 310)]


def role_label(role):
    labels = ROLE_LABELS if isinstance(ROLE_LABELS, dict) else {}
    return labels.get(role, role or "-")


class AdminUsersPage(AdminPage):
    OWNER_ONLY = True

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self._page = 1
        self._search = ""
        self._users = []
        self._role_by_label = {role_label(r): r for r in (ROLE_OWNER, ROLE_ADMIN, ROLE_BUYER)}

        _header, actions = page_header(
            self.content, "ผู้ใช้ & การกำหนดสิทธิ์แอดมิน",
            "ดูข้อมูลรายละเอียดของลูกค้าและแอดมินทุกคน กำหนดสิทธิ์แอดมิน และตั้งรหัสผ่าน — เฉพาะเจ้าของร้าน",
        )
        btn(actions, "＋ เพิ่มแอดมินใหม่", self._toggle_form, kind="primary", size="md").pack(side="right")
        btn(actions, "แต่งตั้งแอดมินจากอีเมล", self._toggle_assign_box, kind="danger", size="md").pack(
            side="right", padx=6,
        )
        btn(actions, "รีเฟรช", self._reload_from_start, kind="outline", size="md").pack(side="right", padx=6)

        self.assign_box = card(self.content)
        self._assign_visible = False
        self._build_assign_box()

        self.form_box = card(self.content)
        self._form_visible = False
        self._build_form()

        bar = ctk.CTkFrame(self.content, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 8))
        self.search_bar = SearchBar(bar, command=self._on_search, placeholder="ค้นหาชื่อ / ชื่อผู้ใช้ / อีเมล",
                                    width=280, height=36)
        self.search_bar.pack(side="left", padx=(0, 8))
        self.role_var = ctk.StringVar(value=ALL_ROLES)
        option_menu(bar, [ALL_ROLES] + list(self._role_by_label), self.role_var, self._on_filter,
                    width=160).pack(side="left")

        table_header(self.content, COLS, ["ผู้ใช้", "อีเมล / เบอร์", "บทบาท", "สถานะ", "สมัครเมื่อ", "จัดการ"])
        self.list_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.list_frame.pack(fill="x")
        self.pager = Pager(self.content, self._goto)
        self.pager.pack(pady=12)

    def on_show(self, **kwargs):
        if not self.allowed():
            return
        self._load()

    def _reload_from_start(self):
        self._page = 1
        self._load()

    def _on_search(self, text):
        self._search = (text or "").strip()
        self._page = 1
        self._load()

    def _on_filter(self, _value=None):
        self._page = 1
        self._load()

    def _goto(self, page):
        self._page = page
        self._render()

    def _load(self):
        self.set_error("")
        role = self._role_by_label.get(self.role_var.get())
        ok, rows = self.call(auth_service.list_users, role=role, search=self._search or None)
        self._users = [as_dict(r) for r in (rows if ok else [])]
        self._refresh_email_choices()
        self._render(failed=not ok)

    def _refresh_email_choices(self):
        if not hasattr(self, "assign_email_menu"):
            return
        emails = [u.get("email") for u in self._users if u.get("email") and u.get("role") != ROLE_OWNER]
        choices = ["- เลือกจากอีเมลในระบบ -"] + emails
        self.assign_email_menu.configure(values=choices)

    def _render(self, failed=False):
        for child in self.list_frame.winfo_children():
            child.destroy()
        if failed:
            empty_state(self.list_frame, "โหลดรายการผู้ใช้ไม่สำเร็จ")
            self.pager.set(1, 1)
            return
        total = len(self._users)
        pages = max(1, -(-total // PAGE_SIZE))
        self._page = min(max(1, self._page), pages)
        start = (self._page - 1) * PAGE_SIZE
        chunk = self._users[start:start + PAGE_SIZE]
        if not chunk:
            empty_state(self.list_frame, "ไม่พบผู้ใช้ตามเงื่อนไขที่เลือก")
        for user in chunk:
            self._add_row(user)
        self.pager.set(self._page, pages, total)

    def _add_row(self, u):
        row = table_row(self.list_frame, COLS)
        user_id = u.get("id")
        role = u.get("role")
        active = bool(u.get("is_active", 1))
        is_me = user_id == Session.get_user_id()

        who = ctk.CTkFrame(row, fg_color="transparent")
        who.grid(row=0, column=0, sticky="w", padx=8, pady=8)
        thumb(who, u.get("avatar_path"), 36).pack(side="left", padx=(0, 8))
        names = ctk.CTkFrame(who, fg_color="transparent")
        names.pack(side="left")
        name_lbl = ctk.CTkLabel(
            names, text=(u.get("full_name") or "-") + ("  (คุณ)" if is_me else ""),
            font=font("body_bold"), anchor="w",
        )
        name_lbl.pack(anchor="w")
        label(names, f"@{u.get('username') or '-'}", "small", muted=True).pack(anchor="w")

        # คลิกที่ชื่อผู้ใช้เพื่อดูข้อมูลรายละเอียดได้ทันที
        for w in (who, name_lbl):
            w.bind("<Button-1>", lambda _e, usr=u: self._open_user_detail_dialog(usr))
            try:
                w.configure(cursor="hand2")
            except Exception:  # noqa: BLE001
                pass

        contact = ctk.CTkFrame(row, fg_color="transparent")
        contact.grid(row=0, column=1, sticky="w", padx=8)
        ctk.CTkLabel(contact, text=u.get("email") or "-", font=font("small"), anchor="w").pack(anchor="w")
        label(contact, format_phone(u.get("phone")), "small", muted=True).pack(anchor="w")

        pill(row, role_label(role), ROLE_KINDS.get(role, "muted")).grid(row=0, column=2, sticky="w", padx=8)

        # T13: สถานะ ออฟไลน์ = สีเทา, ออนไลน์ = สีเขียว, ถูกระงับ = สีแดง
        if not active:
            status = pill(row, "ถูกระงับ", "suspended")
        elif u.get("is_online"):
            status = pill(row, "ออนไลน์", "online")
        else:
            status = pill(row, "ออฟไลน์", "offline")
        status.grid(row=0, column=3, sticky="w", padx=8)

        label(row, format_date_thai(u.get("created_at")), "small", muted=True).grid(
            row=0, column=4, sticky="w", padx=8)

        # T13: เว้นระยะห่างจากขอบขวา (padx=(8, 18)) ไม่ให้ปุ่ม "ดูข้อมูล" ของเจ้าของร้านหรือปุ่มท้ายแถวชิดฝั่งขวาเกินไป
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=(8, 18), pady=6)

        btn(actions, "ดูข้อมูล", lambda usr=u: self._open_user_detail_dialog(usr),
            kind="info", width=72).pack(side="left", padx=3)
        if role != ROLE_OWNER and not is_me:
            btn(actions, "ตั้งรหัส", lambda usr=u: self._open_reset_pw_dialog(usr),
                kind="outline", width=66).pack(side="left", padx=3)
            if u.get("is_online"):
                btn(actions, "เตะออก", lambda usr=u: self._revoke_user_sessions(usr),
                    kind="warning", width=60).pack(side="left", padx=3)
            btn(actions, "ระงับ" if active else "เปิดใช้", lambda usr=u: self._toggle_active(usr),
                kind="danger" if active else "success", width=64).pack(side="left", padx=3)

    # ------------------------------------------------------------------ ดูข้อมูลผู้ใช้/แอดมิน (ข้อ 12)
    def _open_user_detail_dialog(self, u):
        uid = int(u) if isinstance(u, (int, str)) else u["id"]
        ok, detail = self.call(staff_service.get_user_full_detail, uid)
        if not ok or not detail:
            return
        usr = detail.get("user") or {}
        addrs = detail.get("addresses") or []
        orders = detail.get("orders") or []
        stats = detail.get("stats") or {}

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"ข้อมูลบัญชีผู้ใช้: {usr.get('full_name')} (@{usr.get('username')})")
        dlg.geometry("680x620")
        dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
        dlg.transient(self.winfo_toplevel())

        hdr = ctk.CTkFrame(dlg, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
        hdr.pack(fill="x")
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=20, pady=14)
        thumb(hdr_inner, usr.get("avatar_path"), 52).pack(side="left", padx=(0, 12))
        hcol = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        hcol.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            hcol, text=f"{usr.get('full_name') or '-'}  (@{usr.get('username') or '-'})",
            font=font("h2"), text_color=ThemeManager.get_color_pair("primary"), anchor="w",
        ).pack(fill="x")
        st_label = "ถูกระงับ" if not usr.get("is_active") else ("ออนไลน์" if usr.get("is_online") else "ออฟไลน์")
        ctk.CTkLabel(
            hcol,
            text=f"บทบาท: {usr.get('role_label')}  ·  สถานะ: {st_label}",
            font=font("small_bold"), text_color="#FFFFFF", anchor="w",
        ).pack(fill="x")

        body = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=12)

        # 1. ข้อมูลโปรไฟล์
        p_card = card(body)
        p_card.pack(fill="x", pady=(0, 10))
        label(p_card, "ข้อมูลโปรไฟล์และสถิติบัญชี (ไม่แสดงรหัสผ่าน)", "h3").pack(fill="x", padx=16, pady=(12, 6))
        info_rows = [
            ("รหัสผู้ใช้ (User ID)", f"#{usr.get('id')}"),
            ("ชื่อ-นามสกุล", usr.get("full_name") or "-"),
            ("ชื่อผู้ใช้ (Username)", f"@{usr.get('username') or '-'}"),
            ("อีเมล", f"{usr.get('email') or '-'} ({'ยืนยันอีเมลแล้ว' if usr.get('email_verified') else 'ยังไม่ยืนยัน'})"),
            ("เบอร์โทรศัพท์", format_phone(usr.get("phone"))),
            ("วันที่สมัครสมาชิก", format_datetime(usr.get("created_at"))),
            ("เข้าสู่ระบบล่าสุด", format_datetime(usr.get("last_login_at")) if usr.get("last_login_at") else "-"),
            ("จำนวนคำสั่งซื้อทั้งหมด", f"{stats.get('total_orders', 0):,} รายการ (ชำระแล้ว {stats.get('paid_orders', 0):,} รายการ)"),
            ("ยอดซื้อสะสมรวม", format_price(stats.get("total_spent", 0.0))),
            ("เซสชันที่ล็อกอินอยู่", f"{stats.get('active_sessions', 0)} เครื่อง"),
        ]
        for k_txt, v_txt in info_rows:
            r = ctk.CTkFrame(p_card, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=2)
            label(r, k_txt, "small_bold", muted=True, width=180).pack(side="left")
            label(r, str(v_txt), "body_bold").pack(side="left", fill="x", expand=True)
        ctk.CTkFrame(p_card, height=8, fg_color="transparent").pack()

        # 2. ที่อยู่จัดส่ง
        a_card = card(body)
        a_card.pack(fill="x", pady=(0, 10))
        label(a_card, f"ที่อยู่จัดส่งที่บันทึกไว้ ({len(addrs)} ที่อยู่)", "h3").pack(fill="x", padx=16, pady=(12, 6))
        if not addrs:
            label(a_card, "ยังไม่มีที่อยู่จัดส่งที่บันทึกไว้", "small", muted=True).pack(fill="x", padx=16, pady=(0, 12))
        else:
            for ad in addrs:
                ar = ctk.CTkFrame(a_card, fg_color=color("surface_alt"), corner_radius=8)
                ar.pack(fill="x", padx=16, pady=3)
                full_addr = f"{ad.get('address_line') or ''} {ad.get('district') or ''} {ad.get('province') or ''} {ad.get('postcode') or ''}".strip()
                def_tag = " [ค่าเริ่มต้น]" if ad.get("is_default") else ""
                ctk.CTkLabel(
                    ar, text=f"{ad.get('recipient')} ({format_phone(ad.get('phone'))}){def_tag}\n{full_addr}",
                    font=font("small"), anchor="w", justify="left", wraplength=580,
                ).pack(fill="x", padx=12, pady=6)
            ctk.CTkFrame(a_card, height=8, fg_color="transparent").pack()

        # 3. ประวัติคำสั่งซื้อล่าสุด
        o_card = card(body)
        o_card.pack(fill="x", pady=(0, 10))
        label(o_card, f"ประวัติคำสั่งซื้อล่าสุด ({len(orders)} รายการ)", "h3").pack(fill="x", padx=16, pady=(12, 6))
        if not orders:
            label(o_card, "ยังไม่มีประวัติคำสั่งซื้อ", "small", muted=True).pack(fill="x", padx=16, pady=(0, 12))
        else:
            for od in orders:
                orow = ctk.CTkFrame(o_card, fg_color=color("surface_alt"), corner_radius=8)
                orow.pack(fill="x", padx=16, pady=3)
                ctk.CTkLabel(
                    orow,
                    text=f"ออเดอร์ #{od.get('id')}  ·  {format_datetime(od.get('created_at'))}  ·  ยอด {format_price(od.get('total'))}  ({od.get('status_label')})",
                    font=font("small_bold"), anchor="w",
                ).pack(side="left", padx=12, pady=6)
                btn(
                    orow, "ดูออเดอร์ ›",
                    lambda oid=od.get("id"): (dlg.destroy(), self.controller.show("admin_order_detail", order_id=oid)),
                    kind="outline", width=90,
                ).pack(side="right", padx=10, pady=4)
            ctk.CTkFrame(o_card, height=8, fg_color="transparent").pack()

        btn(dlg, "ปิดหน้าต่าง", dlg.destroy, kind="outline", size="sm", width=130).pack(pady=(0, 12))
        dlg.after(120, lambda: (dlg.lift(), dlg.focus_force()))

    def _toggle_active(self, u):
        active = bool(u.get("is_active", 1))
        name = u.get("full_name") or u.get("username")
        if active and not dialogs.confirm(
            self, "ระงับบัญชี",
            f"ระงับบัญชีของ “{name}” ใช่ไหม?\nผู้ใช้นี้จะเข้าสู่ระบบไม่ได้จนกว่าจะเปิดใช้งานอีกครั้ง",
            confirm_text="ระงับบัญชี", danger=True,
        ):
            return
        self.set_error("")
        ok, _ = self.call(auth_service.set_user_active, u.get("id"), not active)
        if ok:
            self._load()

    def _revoke_user_sessions(self, u):
        ok, _ = self.call(staff_service.revoke_sessions, u.get("id"))
        if ok:
            dialogs.show_message(self, "เพิกถอนเซสชันแล้ว", f"บังคับออกจากระบบของบัญชี {u.get('username')} เรียบร้อยแล้ว", kind="success")
            self._load()

    def _open_reset_pw_dialog(self, u):
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"ตั้งรหัสผ่านใหม่ให้ @{u.get('username')}")
        dlg.geometry("420x300")
        dlg.resizable(False, False)
        dlg.configure(fg_color=ThemeManager.get_color_pair("surface"))
        dlg.transient(self.winfo_toplevel())

        ctk.CTkLabel(dlg, text=f"ตั้งรหัสผ่านใหม่: @{u.get('username')}", font=font("h3")).pack(
            anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(dlg, text=f"อีเมล: {u.get('email') or '-'} ({role_label(u.get('role'))})",
                     font=font("small"), text_color=color("text_muted")).pack(anchor="w", padx=20, pady=(0, 10))

        pw1 = entry(dlg, "รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร)", show="•")
        pw1.pack(fill="x", padx=20, pady=4)
        pw2 = entry(dlg, "ยืนยันรหัสผ่านใหม่อีกครั้ง", show="•")
        pw2.pack(fill="x", padx=20, pady=4)
        err = ctk.CTkLabel(dlg, text="", font=font("small"), text_color=color("danger"))
        err.pack(fill="x", padx=20)

        def save():
            try:
                staff_service.reset_user_password(u.get("id"), pw1.get(), pw2.get())
                dlg.destroy()
                dialogs.show_message(self, "เปลี่ยนรหัสผ่านสำเร็จ", f"ตั้งรหัสผ่านใหม่ให้ @{u.get('username')} เรียบร้อยแล้ว", kind="success")
                self._load()
            except Exception as exc:  # noqa: BLE001
                err.configure(text=str(exc))

        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=12)
        btn(row, "บันทึกรหัสผ่านใหม่", save, kind="primary", size="md").pack(side="right")
        btn(row, "ยกเลิก", dlg.destroy, kind="outline", size="md").pack(side="right", padx=8)
        dlg.after(120, lambda: (dlg.lift(), pw1.focus_set()))

    # ------------------------------------------------------------------ แต่งตั้งแอดมินจากอีเมล (STAFF-2)
    def _build_assign_box(self):
        box = self.assign_box
        label(box, "แต่งตั้งแอดมินจากอีเมลผู้ใช้ (Assign Admin by Email)", "h3").pack(
            fill="x", padx=16, pady=(12, 2))
        label(box, "เลือกอีเมลของผู้ใช้ที่มีอยู่ในระบบ หรือพิมพ์อีเมลเพื่อกำหนดบทบาทเป็นแอดมิน พร้อมตั้งรหัสผ่านสำหรับใช้งาน",
              "small", muted=True).pack(fill="x", padx=16, pady=(0, 8))

        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 4))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="af")

        c0 = ctk.CTkFrame(grid, fg_color="transparent")
        c0.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        label(c0, "เลือกจากอีเมลผู้ใช้ที่มีอยู่", "small", muted=True).pack(fill="x")
        self.assign_pick_var = ctk.StringVar(value="- เลือกจากอีเมลในระบบ -")
        self.assign_email_menu = option_menu(
            c0, ["- เลือกจากอีเมลในระบบ -"], self.assign_pick_var,
            command=self._on_pick_email, width=220,
        )
        self.assign_email_menu.pack(fill="x")

        c1 = ctk.CTkFrame(grid, fg_color="transparent")
        c1.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        label(c1, "อีเมลที่ต้องการแต่งตั้งเป็นแอดมิน *", "small", muted=True).pack(fill="x")
        self.a_email = entry(c1, "name@example.com")
        self.a_email.pack(fill="x")

        c2 = ctk.CTkFrame(grid, fg_color="transparent")
        c2.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        label(c2, "ตั้งรหัสผ่านแอดมิน *", "small", muted=True).pack(fill="x")
        self.a_pw = entry(c2, "อย่างน้อย 8 ตัวอักษร", show="•")
        self.a_pw.pack(fill="x")

        c3 = ctk.CTkFrame(grid, fg_color="transparent")
        c3.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        label(c3, "ยืนยันรหัสผ่านแอดมิน *", "small", muted=True).pack(fill="x")
        self.a_confirm = entry(c3, "พิมพ์รหัสผ่านอีกครั้ง", show="•")
        self.a_confirm.pack(fill="x")

        btns = ctk.CTkFrame(box, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(6, 12))
        btn(btns, "ยืนยันแต่งตั้งเป็นแอดมิน", self._submit_assign_admin, kind="primary", size="md").pack(side="left")
        btn(btns, "ปิดแผงนี้", self._toggle_assign_box, kind="outline", size="md").pack(side="left", padx=8)

    def _on_pick_email(self, value):
        if value and not value.startswith("-"):
            self.a_email.delete(0, "end")
            self.a_email.insert(0, value)

    def _toggle_assign_box(self):
        if self._assign_visible:
            self.assign_box.pack_forget()
        else:
            self.assign_box.pack(fill="x", pady=(0, 10), after=self.content.winfo_children()[0])
            self.a_email.focus_set()
        self._assign_visible = not self._assign_visible

    def _submit_assign_admin(self):
        self.set_error("")
        email = self.a_email.get().strip()
        pw = self.a_pw.get()
        cf = self.a_confirm.get()
        ok, user = self.call(staff_service.assign_admin_by_email, email, pw, cf)
        if not ok:
            return
        user = as_dict(user)
        for w in (self.a_email, self.a_pw, self.a_confirm):
            w.delete(0, "end")
        self._toggle_assign_box()
        dialogs.show_message(
            self, "แต่งตั้งแอดมินสำเร็จ",
            f"กำหนดสิทธิ์แอดมินให้กับอีเมล {user.get('email')} (ชื่อผู้ใช้: @{user.get('username')}) เรียบร้อยแล้ว",
            kind="success",
        )
        self._reload_from_start()

    # ------------------------------------------------------------------ ฟอร์มเพิ่มแอดมินใหม่
    def _build_form(self):
        box = self.form_box
        label(box, "เพิ่มบัญชีแอดมินใหม่", "h3").pack(fill="x", padx=16, pady=(12, 0))
        label(box, "แอดมินตรวจสลิป/ตอบแชท/จัดการออเดอร์และสินค้าได้ แต่เข้าเมนูของเจ้าของร้านไม่ได้", "small",
              muted=True).pack(fill="x", padx=16, pady=(0, 6))
        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 4))
        grid.grid_columnconfigure((0, 1), weight=1, uniform="f")

        def field(row, col, title, placeholder, **kw):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
            label(cell, title, "small", muted=True).pack(fill="x")
            widget = entry(cell, placeholder, **kw)
            widget.pack(fill="x")
            return widget

        self.f_username = field(0, 0, "ชื่อผู้ใช้ *", "ตัวอักษรอังกฤษ/ตัวเลข")
        self.f_email = field(0, 1, "อีเมล *", "name@example.com")
        self.f_name = field(1, 0, "ชื่อ-นามสกุล *", "เช่น สมชาย ใจดี")
        self.f_phone = field(1, 1, "เบอร์โทร *", "0812345678")
        self.f_password = field(2, 0, "รหัสผ่าน *", "อย่างน้อย 8 ตัวอักษร", show="•")
        self.f_confirm = field(2, 1, "ยืนยันรหัสผ่าน *", "พิมพ์รหัสผ่านอีกครั้ง", show="•")
        self.f_confirm.bind("<Return>", lambda _e: self._create_staff())

        btns = ctk.CTkFrame(box, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(4, 14))
        btn(btns, "สร้างบัญชีแอดมิน", self._create_staff, kind="primary", size="md").pack(side="left")
        btn(btns, "ปิดฟอร์ม", self._toggle_form, kind="outline", size="md").pack(side="left", padx=8)

    def _toggle_form(self):
        if self._form_visible:
            self.form_box.pack_forget()
        else:
            self.form_box.pack(fill="x", pady=(0, 10), after=self.content.winfo_children()[0])
            self.f_username.focus_set()
        self._form_visible = not self._form_visible

    def _clear_form(self):
        for widget in (self.f_username, self.f_email, self.f_name, self.f_phone, self.f_password, self.f_confirm):
            widget.delete(0, "end")

    def _create_staff(self):
        self.set_error("")
        password = self.f_password.get()
        if password != self.f_confirm.get():
            self.set_error("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
            return
        ok, user = self.call(auth_service.create_staff, self.f_username.get().strip(), self.f_email.get().strip(),
                             password, self.f_name.get().strip(), self.f_phone.get().strip(), role=ROLE_ADMIN)
        if not ok:
            return
        user = as_dict(user)
        self._clear_form()
        self._toggle_form()
        dialogs.show_message(self, "สร้างบัญชีแล้ว",
                             f"สร้างบัญชีแอดมิน “{user.get('username') or ''}” เรียบร้อย",
                             kind="success")
        self._reload_from_start()

    _open_user_detail = _open_user_detail_dialog
