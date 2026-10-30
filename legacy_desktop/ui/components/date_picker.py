"""
ui/components/date_picker.py
คอมโพเนนต์ตัวเลือกวันที่และวัน-เวลาแบบปฏิทิน (T08 — DatePickerField / DateTimePickerField):
- สร้างด้วย CustomTkinter + โมดูล calendar มาตรฐานของ Python (ไม่ต้องติดตั้งไลบรารีภายนอกเพิ่ม)
- คืนค่าในรูปแบบมาตรฐาน ISO ('YYYY-MM-DD' หรือ 'YYYY-MM-DD HH:MM:SS') เหมือนเดิม 100%
- แสดงวันที่รูปแบบไทย พ.ศ. อ่านง่ายควบคู่กัน (เช่น 16 ต.ค. 2569)
- รองรับเมธอด .get(), .set(), .delete(), .insert(), .configure() เพื่อให้ใช้งานแทน CTkEntry เดิมได้ทันที
"""

import calendar
from datetime import date, datetime

import customtkinter as ctk

from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils
from utils.formatters import THAI_MONTHS_SHORT, format_date_thai, parse_datetime

_WEEKDAYS_TH = ("จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา.")


class _CalendarPopup(ctk.CTkToplevel):
    """หน้าต่างป๊อปอัปปฏิทินเลือกวัน (และเวลา ถ้าระบุ include_time=True)"""

    def __init__(
        self,
        parent,
        initial_dt: datetime | None,
        include_time: bool = False,
        allow_empty: bool = True,
        default_end_of_day: bool = False,
        on_select=None,
    ):
        super().__init__(parent)
        self.title("เลือกวันและเวลา" if include_time else "เลือกวันที่")
        self.geometry("350x420" if include_time else "350x365")
        self.resizable(False, False)
        self.configure(fg_color=ThemeManager.get_color_pair("surface"))
        self.transient(parent.winfo_toplevel())

        self._include_time = include_time
        self._allow_empty = allow_empty
        self._default_eod = default_end_of_day
        self._on_select = on_select

        now = datetime.now()
        base = initial_dt or now
        self._year = base.year
        self._month = base.month
        self._selected_day = base.day
        self._hour = base.hour if initial_dt else (23 if default_end_of_day else now.hour)
        self._minute = base.minute if initial_dt else (59 if default_end_of_day else 0)

        self._build_ui()
        self._render_month()
        self.after(80, self._focus_popup)

    def _focus_popup(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:  # noqa: BLE001
            pass

    def _build_ui(self):
        # แถบหัวเลือกเดือน/ปี
        hdr = ctk.CTkFrame(self, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
        hdr.pack(fill="x")

        nav = ctk.CTkFrame(hdr, fg_color="transparent")
        nav.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            nav, text="« ปี", width=44,
            command=lambda: self._shift_month(-12),
            **ThemeManager.button_style("outline", "sm"),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            nav, text="‹", width=32,
            command=lambda: self._shift_month(-1),
            **ThemeManager.button_style("primary", "sm"),
        ).pack(side="left")

        self.month_year_lbl = ctk.CTkLabel(
            nav, text="", font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("primary"),
        )
        self.month_year_lbl.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            nav, text="›", width=32,
            command=lambda: self._shift_month(1),
            **ThemeManager.button_style("primary", "sm"),
        ).pack(side="right")

        ctk.CTkButton(
            nav, text="ปี »", width=44,
            command=lambda: self._shift_month(12),
            **ThemeManager.button_style("outline", "sm"),
        ).pack(side="right", padx=(4, 0))

        # หัวคอลัมน์วันในสัปดาห์
        wk_frame = ctk.CTkFrame(self, fg_color=ThemeManager.get_color_pair("surface_alt"), corner_radius=0)
        wk_frame.pack(fill="x", padx=12, pady=(8, 2))
        for col, wname in enumerate(_WEEKDAYS_TH):
            wk_frame.grid_columnconfigure(col, weight=1, uniform="wk")
            ctk.CTkLabel(
                wk_frame, text=wname, font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("danger" if col >= 5 else "text_main"),
            ).grid(row=0, column=col, pady=4)

        # ตารางวันที่ 6 แถว x 7 คอลัมน์
        self.days_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.days_grid.pack(fill="both", expand=True, padx=12, pady=4)
        for col in range(7):
            self.days_grid.grid_columnconfigure(col, weight=1, uniform="day")

        # แถวเลือกเวลา (เฉพาะ DateTimePickerField)
        if self._include_time:
            t_frame = ctk.CTkFrame(self, fg_color=ThemeManager.get_color_pair("surface_alt"), corner_radius=8)
            t_frame.pack(fill="x", padx=12, pady=(2, 6))
            ctk.CTkLabel(
                t_frame, text="เวลา (ชั่วโมง : นาที):",
                font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(side="left", padx=(12, 8), pady=6)

            hours = [f"{h:02d}" for h in range(24)]
            mins = [f"{m:02d}" for m in range(0, 60, 5)]
            if f"{self._minute:02d}" not in mins:
                mins = sorted(set(mins + [f"{self._minute:02d}"]))

            self.hour_var = ctk.StringVar(value=f"{self._hour:02d}")
            self.min_var = ctk.StringVar(value=f"{self._minute:02d}")

            ctk.CTkOptionMenu(
                t_frame, values=hours, variable=self.hour_var, width=68, height=28,
                font=ThemeManager.get_font("small_bold"),
                fg_color=ThemeManager.get_color_pair("surface"),
                button_color=ThemeManager.get_color_pair("primary"),
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(side="left", padx=2, pady=6)
            ctk.CTkLabel(t_frame, text=":", font=ThemeManager.get_font("body_bold")).pack(side="left", padx=2)
            ctk.CTkOptionMenu(
                t_frame, values=mins, variable=self.min_var, width=68, height=28,
                font=ThemeManager.get_font("small_bold"),
                fg_color=ThemeManager.get_color_pair("surface"),
                button_color=ThemeManager.get_color_pair("primary"),
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(side="left", padx=2, pady=6)

        # ปุ่มด้านล่าง: วันนี้ / ล้างค่า / ตกลง
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=12, pady=(4, 10))

        ctk.CTkButton(
            foot, text="วันนี้", width=70,
            command=self._pick_today,
            **ThemeManager.button_style("info", "sm"),
        ).pack(side="left")

        if self._allow_empty:
            ctk.CTkButton(
                foot, text="ล้างค่า", width=72,
                command=self._clear_date,
                **ThemeManager.button_style("outline", "sm"),
            ).pack(side="left", padx=6)

        ctk.CTkButton(
            foot, text="ยืนยันวันที่", width=110,
            command=self._confirm_current,
            **ThemeManager.button_style("primary", "sm"),
        ).pack(side="right")

    def _shift_month(self, delta_months: int):
        total = (self._year * 12 + (self._month - 1)) + delta_months
        self._year = max(1970, min(2100, total // 12))
        self._month = (total % 12) + 1
        max_day = calendar.monthrange(self._year, self._month)[1]
        self._selected_day = min(self._selected_day, max_day)
        self._render_month()

    def _render_month(self):
        for child in self.days_grid.winfo_children():
            child.destroy()

        be_year = self._year + 543
        m_name = THAI_MONTHS_SHORT[self._month - 1]
        self.month_year_lbl.configure(text=f"{m_name} {be_year} ({self._year})")

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self._year, self._month)
        today = date.today()

        for r_idx, week in enumerate(weeks):
            for c_idx, day_num in enumerate(week):
                if day_num == 0:
                    ctk.CTkLabel(self.days_grid, text="", height=30).grid(row=r_idx, column=c_idx, padx=2, pady=2)
                    continue
                is_selected = (day_num == self._selected_day)
                is_today = (today.year == self._year and today.month == self._month and today.day == day_num)
                if is_selected:
                    fg = ThemeManager.get_color_pair("primary")
                    tc = ON_PRIMARY
                    bw = 2
                    bc = ("#111318", "#FFFFFF")
                elif is_today:
                    fg = ThemeManager.get_color_pair("blue_soft")
                    tc = ThemeManager.get_color_pair("info")
                    bw = 1
                    bc = ThemeManager.get_color_pair("info")
                else:
                    fg = ThemeManager.get_color_pair("surface_alt")
                    tc = ThemeManager.get_color_pair("text_main")
                    bw = 0
                    bc = ThemeManager.get_color_pair("border")

                btn = ctk.CTkButton(
                    self.days_grid,
                    text=str(day_num),
                    width=36,
                    height=30,
                    corner_radius=6,
                    fg_color=fg,
                    hover_color=ThemeManager.get_color_pair("primary_hover"),
                    text_color=tc,
                    border_width=bw,
                    border_color=bc,
                    font=ThemeManager.get_font("small_bold" if (is_selected or is_today) else "small"),
                    command=lambda d=day_num: self._on_day_clicked(d),
                )
                btn.grid(row=r_idx, column=c_idx, padx=2, pady=2, sticky="nsew")

    def _on_day_clicked(self, day_num: int):
        self._selected_day = day_num
        if not self._include_time:
            self._confirm_current()
        else:
            self._render_month()

    def _pick_today(self):
        now = datetime.now()
        self._year, self._month, self._selected_day = now.year, now.month, now.day
        if self._include_time:
            self.hour_var.set(f"{now.hour:02d}")
            self.min_var.set(f"{now.minute:02d}")
        self._confirm_current()

    def _clear_date(self):
        if callable(self._on_select):
            self._on_select("")
        self.destroy()

    def _confirm_current(self):
        max_day = calendar.monthrange(self._year, self._month)[1]
        day = min(max(1, self._selected_day), max_day)
        if self._include_time:
            try:
                hh = int(self.hour_var.get())
                mm = int(self.min_var.get())
            except (TypeError, ValueError):
                hh, mm = 23, 59
            sec = 59 if (hh == 23 and mm == 59) else 0
            iso = f"{self._year:04d}-{self._month:02d}-{day:02d} {hh:02d}:{mm:02d}:{sec:02d}"
        else:
            iso = f"{self._year:04d}-{self._month:02d}-{day:02d}"
        if callable(self._on_select):
            self._on_select(iso)
        self.destroy()


class DatePickerField(ctk.CTkFrame):
    """
    ช่องเลือกวันที่แบบปฏิทิน (T08):
    - .get() คืนค่า ISO 'YYYY-MM-DD' (หรือ 'YYYY-MM-DD HH:MM:SS' เมื่อ include_time=True)
    - .set(val) / .insert(0, val) / .delete(0, 'end') ทำงานเข้ากันได้กับ CTkEntry เดิมทั้งหมด
    - แสดงป้ายวันที่ภาษาไทย พ.ศ. ให้อ่านเข้าใจง่ายควบคู่กับปุ่มเปิดปฏิทิน
    """

    def __init__(
        self,
        parent,
        placeholder_text: str = "เลือกวันที่...",
        include_time: bool = False,
        allow_empty: bool = True,
        default_end_of_day: bool = False,
        width: int = 240,
        height: int = 38,
        on_change=None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", width=width, height=height)
        self._include_time = bool(include_time)
        self._allow_empty = bool(allow_empty)
        self._default_eod = bool(default_end_of_day)
        self._on_change = on_change
        self._popup = None

        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder_text,
            width=max(120, width - 82),
            **ThemeManager.entry_style(height),
        )
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind("<FocusOut>", lambda _e: self._refresh_thai_hint())
        self.entry.bind("<KeyRelease>", lambda _e: self._refresh_thai_hint())

        self._cal_ic = icon_utils.get_icon("calendar", 15, ON_PRIMARY, ON_PRIMARY)
        self.pick_btn = ctk.CTkButton(
            self,
            text=" ปฏิทิน",
            image=self._cal_ic,
            compound="left",
            width=76,
            command=self.open_calendar,
            **{**ThemeManager.button_style("primary", "sm"), "height": height},
        )
        self.pick_btn.grid(row=0, column=1, padx=(6, 0))

        self.thai_hint_lbl = ctk.CTkLabel(
            self,
            text="",
            font=ThemeManager.get_font("tiny"),
            text_color=ThemeManager.get_color_pair("info"),
            anchor="w",
        )
        self.thai_hint_lbl.grid(row=1, column=0, columnspan=2, sticky="w", pady=(1, 0))

    def open_calendar(self):
        if str(self.entry.cget("state")) == "disabled":
            return
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.lift()
            return
        cur_dt = parse_datetime(self.get())
        self._popup = _CalendarPopup(
            self,
            initial_dt=cur_dt,
            include_time=self._include_time,
            allow_empty=self._allow_empty,
            default_end_of_day=self._default_eod,
            on_select=self._on_picked,
        )

    def _on_picked(self, iso_value: str):
        self.set(iso_value)
        if callable(self._on_change):
            self._on_change(iso_value)

    def _refresh_thai_hint(self):
        raw = self.entry.get().strip()
        if not raw:
            self.thai_hint_lbl.configure(text="")
            return
        dt = parse_datetime(raw)
        if dt is None:
            self.thai_hint_lbl.configure(
                text="รูปแบบวันที่ไม่ถูกต้อง (กดปุ่ม 'ปฏิทิน' เพื่อเลือก)",
                text_color=ThemeManager.get_color_pair("danger"),
            )
            return
        thai_txt = format_date_thai(dt)
        if self._include_time and len(raw) > 10:
            thai_txt += f" เวลา {dt.strftime('%H:%M')} น."
        self.thai_hint_lbl.configure(
            text=f"ตรงกับ: {thai_txt}",
            text_color=ThemeManager.get_color_pair("info"),
        )

    # ---------- เมธอดความเข้ากันได้กับ CTkEntry ----------
    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: str | None) -> None:
        prev_state = str(self.entry.cget("state"))
        if prev_state == "disabled":
            self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        if value:
            self.entry.insert(0, str(value).strip())
        if prev_state == "disabled":
            self.entry.configure(state="disabled")
        self._refresh_thai_hint()

    def delete(self, first, last=None) -> None:
        self.entry.delete(first, last)
        self._refresh_thai_hint()

    def insert(self, index, string: str) -> None:
        self.entry.insert(index, string)
        self._refresh_thai_hint()

    def configure(self, **kwargs):
        if "state" in kwargs:
            st = kwargs.pop("state")
            self.entry.configure(state=st)
            self.pick_btn.configure(state=st)
        if kwargs:
            super().configure(**kwargs)

    config = configure
    set_value = set


class DateTimePickerField(DatePickerField):
    """ช่องเลือกวันและเวลาแบบปฏิทิน (คืนค่า YYYY-MM-DD HH:MM:SS)"""

    def __init__(self, parent, placeholder_text: str = "เลือกวัน-เวลา...", **kwargs):
        kwargs.setdefault("include_time", True)
        super().__init__(parent, placeholder_text=placeholder_text, **kwargs)
