"""
ui/components/search_bar.py
ช่องค้นหาพร้อมไอคอนแว่นขยายในช่องค้นหา + ปุ่มค้นหาสีเหลืองสปอร์ต พร้อมระบบแนะนำคำค้นอัตโนมัติ (ข้อ 15)
"""

import customtkinter as ctk

from ui.theme import ON_PRIMARY, ThemeManager
from utils import icon_utils


class SearchBar(ctk.CTkFrame):
    def __init__(self, parent, command=None, placeholder="ค้นหาไม้แบดมินตัน รองเท้า ลูกแบด...",
                 width=380, height=38, suggest_fn=None, on_select_suggestion=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._command = command
        self._suggest_fn = suggest_fn
        self._on_select_suggestion = on_select_suggestion
        self._after_id = None
        self._popup = None

        # กรอบช่องค้นหาที่มีไอคอนแว่นขยายด้านในฝั่งซ้าย (ข้อ 15)
        entry_wrap_w = max(110, width - height - 8)
        self.input_shell = ctk.CTkFrame(
            self, width=entry_wrap_w, height=height,
            corner_radius=height // 2, border_width=1,
            fg_color=ThemeManager.get_color_pair("surface"),
            border_color=ThemeManager.get_color_pair("border"),
        )
        self.input_shell.pack(side="left")
        self.input_shell.pack_propagate(False)

        self._search_icon_in = icon_utils.get_icon("search", 16, "#475569", "#CBD5E1")
        self.icon_label = ctk.CTkLabel(
            self.input_shell, text="", image=self._search_icon_in, width=22,
        )
        self.icon_label.pack(side="left", padx=(10, 2))
        self.icon_label.bind("<Button-1>", lambda _e: self.focus())

        self.entry = ctk.CTkEntry(
            self.input_shell, placeholder_text=placeholder,
            height=height - 6, border_width=0, corner_radius=0,
            font=ThemeManager.get_font("body"),
            fg_color="transparent",
            text_color=ThemeManager.get_color_pair("text_main"),
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=2)
        self.entry.bind("<Return>", lambda _e: self.submit())
        self.entry.bind("<Escape>", lambda _e: self.hide_suggestions())
        if self._suggest_fn is not None:
            self.entry.bind("<KeyRelease>", self._on_key_release, add="+")
            self.entry.bind("<FocusOut>", lambda _e: self.after(180, self.hide_suggestions), add="+")

        self._search_btn_icon = icon_utils.get_icon("search", 18, ON_PRIMARY, ON_PRIMARY)
        self.button = ctk.CTkButton(
            self, text="", image=self._search_btn_icon,
            width=height, height=height, corner_radius=height // 2,
            fg_color=ThemeManager.get_color_pair("primary"),
            hover_color=ThemeManager.get_color_pair("primary_hover"),
            text_color=ON_PRIMARY, command=self.submit,
        )
        self.button.pack(side="left", padx=(6, 0))

    def _on_key_release(self, event):
        if event.keysym in ("Return", "Escape", "Up", "Down", "Tab"):
            return
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:  # noqa: BLE001
                pass
        self._after_id = self.after(220, self._update_suggestions)

    def _update_suggestions(self):
        self._after_id = None
        if not self.winfo_exists() or self._suggest_fn is None:
            return
        q = self.get()
        if len(q) < 1:
            self.hide_suggestions()
            return
        try:
            items = self._suggest_fn(q) or []
        except Exception:  # noqa: BLE001
            items = []
        if not items:
            self.hide_suggestions()
            return
        self._show_popup(items[:6])

    def _show_popup(self, items: list[dict]):
        self.hide_suggestions()
        try:
            top = self.winfo_toplevel()
            popup = ctk.CTkToplevel(top)
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(fg_color=ThemeManager.get_color_pair("surface"))
            x = self.input_shell.winfo_rootx()
            y = self.input_shell.winfo_rooty() + self.input_shell.winfo_height() + 4
            w = max(260, self.input_shell.winfo_width() + 44)
            row_h = 34
            popup.geometry(f"{w}x{len(items) * row_h + 8}+{x}+{y}")

            box = ctk.CTkFrame(
                popup, fg_color=ThemeManager.get_color_pair("surface"),
                border_width=1, border_color=ThemeManager.get_color_pair("primary"), corner_radius=8,
            )
            box.pack(fill="both", expand=True)

            ic = icon_utils.get_icon("racket", 14, "#E63946", "#FFB703")
            for item in items:
                pid = item.get("id")
                name = str(item.get("name") or "")
                brand = str(item.get("brand_name") or "")
                label = f" [{brand}] {name}" if brand else f" {name}"
                if len(label) > 48:
                    label = label[:46] + "…"
                btn = ctk.CTkButton(
                    box, text=label, image=ic, compound="left", anchor="w", height=30, corner_radius=6,
                    font=ThemeManager.get_font("small"),
                    fg_color="transparent",
                    hover_color=ThemeManager.get_color_pair("surface_alt"),
                    text_color=ThemeManager.get_color_pair("text_main"),
                    command=lambda i=item, p=pid: self._pick_suggestion(i, p),
                )
                btn.pack(fill="x", padx=4, pady=1)
            self._popup = popup
        except Exception:  # noqa: BLE001
            self.hide_suggestions()

    def _pick_suggestion(self, item: dict, product_id):
        self.hide_suggestions()
        if callable(self._on_select_suggestion) and product_id is not None:
            self._on_select_suggestion(product_id, item)
        else:
            self.set(str(item.get("name") or ""))
            self.submit()

    def hide_suggestions(self):
        if self._popup is not None:
            try:
                self._popup.destroy()
            except Exception:  # noqa: BLE001
                pass
            self._popup = None

    def submit(self):
        self.hide_suggestions()
        if self._command:
            self._command(self.get())

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, text: str):
        self.entry.delete(0, "end")
        if text:
            self.entry.insert(0, text)

    def clear(self):
        self.hide_suggestions()
        self.set("")

    def focus(self):
        self.entry.focus_set()

    def destroy(self):
        self.hide_suggestions()
        super().destroy()
