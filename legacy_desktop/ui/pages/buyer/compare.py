"""
ui/pages/buyer/compare.py
หน้าเปรียบเทียบไม้แบดมินตัน 2–5 รุ่น (BUY-4 + T02, T03):
- รองรับการเลือกเปรียบเทียบตั้งแต่ 2 ถึง 5 รุ่นพร้อมกัน
- รองรับไม้แบดทุกน้ำหนักที่ Owner ตั้งค่าไว้ (เช่น 3U–10U)
- แสดง Technical Specifications ครบทั้ง 7 หัวข้อตาม T03
"""

import tkinter as tk

import customtkinter as ctk

from core.constants import MAX_COMPARE, MIN_COMPARE
from services import product_service
from ui.components.rating import RatingStars
from ui.pages.buyer import common
from ui.theme import ThemeManager
from utils import validators
from utils.formatters import format_price
from utils.image_utils import load_ctk_image

SLOTS = MAX_COMPARE  # 5 รุ่น
EMPTY = "— เลือกไม้แบดมินตัน —"

_ROWS = (
    ("ราคาขายสุทธิ", "price"),
    ("Material", "spec_material"),
    ("Weight Class / Grip", "weight_grip_display"),
    ("Balance Point", "balance_point_display"),
    ("Shaft Flexibility", "flex"),
    ("Max String Tension", "spec_max_tension"),
    ("Length", "spec_length"),
    ("Skill Level", "level"),
    ("คะแนนรีวิว", "rating"),
    ("สถานะสต็อก", "stock"),
)


class ComparePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=ThemeManager.get_color_pair("background"))
        self.controller = controller
        self._label_to_id = {}
        self._id_to_label = {}
        self._images = []

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        common.page_title(
            body,
            f"⚖️ เปรียบเทียบไม้แบดมินตัน ({MIN_COMPARE}–{MAX_COMPARE} รุ่น)",
            f"เลือกไม้แบดมินตันตั้งแต่ {MIN_COMPARE} ถึง {MAX_COMPARE} รุ่นเพื่อเปรียบเทียบ Technical Specifications และราคาแบบเคียงข้างกัน",
        ).pack(fill="x")

        pick = ThemeManager.make_card(body)
        pick.pack(fill="x", pady=12)

        slots_grid = ctk.CTkFrame(pick, fg_color="transparent")
        slots_grid.pack(fill="x", padx=16, pady=(14, 8))
        for col in range(3):
            slots_grid.grid_columnconfigure(col, weight=1)

        self.slot_vars, self.slot_menus = [], []
        for idx in range(SLOTS):
            r, c = divmod(idx, 3)
            cell = ctk.CTkFrame(slots_grid, fg_color="transparent")
            cell.grid(row=r, column=c, sticky="ew", padx=6, pady=4)
            ctk.CTkLabel(
                cell, text=f"ไม้รุ่นที่ {idx + 1}" + (" (บังคับ)" if idx < 2 else " (เพิ่มเติม)"),
                font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("danger" if idx < 2 else "text_muted"),
                anchor="w",
            ).pack(fill="x")
            var = ctk.StringVar(value=EMPTY)
            menu = ctk.CTkOptionMenu(
                cell, values=[EMPTY], variable=var, width=250, height=36,
                font=ThemeManager.get_font("small"), dropdown_font=ThemeManager.get_font("small"),
                fg_color=ThemeManager.get_color_pair("surface_alt"),
                button_color=ThemeManager.get_color_pair("primary"),
                button_hover_color=ThemeManager.get_color_pair("primary_hover"),
                text_color=ThemeManager.get_color_pair("text_main"),
                dropdown_fg_color=ThemeManager.get_color_pair("surface"),
                dropdown_text_color=ThemeManager.get_color_pair("text_main"),
                dropdown_hover_color=ThemeManager.get_color_pair("surface_alt"),
            )
            menu.pack(fill="x", pady=(2, 0))
            self.slot_vars.append(var)
            self.slot_menus.append(menu)

        actions = ctk.CTkFrame(pick, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(6, 14))
        ctk.CTkButton(
            actions, text="⚖️ เปรียบเทียบสเปกทันที", width=170, command=self._compare,
            **ThemeManager.button_style("primary", "md"),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions, text="ล้างการเลือกทั้งหมด", width=140, command=self._clear_all,
            **ThemeManager.button_style("outline", "md"),
        ).pack(side="left")
        self.error_label = common.error_label(actions)
        self.error_label.pack(side="left", padx=12)

        self.result_box = ctk.CTkFrame(body, fg_color="transparent")
        self.result_box.pack(fill="both", expand=True)

    def on_show(self, ids=None, **kwargs):
        self._load_choices()
        wanted = []
        for raw in ids or []:
            try:
                wanted.append(int(raw))
            except (TypeError, ValueError):
                continue
        for index, var in enumerate(self.slot_vars):
            pid = wanted[index] if index < len(wanted) else None
            var.set(self._id_to_label.get(pid, EMPTY))
        self.error_label.configure(text="")
        self._clear_result()
        if len([w for w in wanted if w in self._id_to_label]) >= MIN_COMPARE:
            self._compare()
        else:
            self._show_hint()

    def _load_choices(self):
        self._label_to_id, self._id_to_label = {}, {}
        try:
            all_items = product_service.search_products(
                sort="name", page_size=60, user_id=common.user_id(),
            )["items"]
            items = [it for it in all_items if it.get("is_racket")]
        except (ValueError, PermissionError) as exc:
            self.error_label.configure(text=str(exc))
            items = []
        for item in items:
            label = f"{item.get('brand_name') or ''} {item['name']}".strip()
            if label in self._label_to_id:
                label = f"{label} (#{item['id']})"
            self._label_to_id[label] = item["id"]
            self._id_to_label[item["id"]] = label
        for menu in self.slot_menus:
            menu.configure(values=[EMPTY] + list(self._label_to_id))

    def _clear_all(self):
        for var in self.slot_vars:
            var.set(EMPTY)
        self.error_label.configure(text="")
        self._clear_result()
        self._show_hint()

    def _clear_result(self):
        for child in self.result_box.winfo_children():
            child.destroy()
        self._images = []

    def _show_hint(self):
        ctk.CTkLabel(
            self.result_box,
            text=f"เลือกไม้แบดมินตันอย่างน้อย {MIN_COMPARE} รุ่น (สูงสุด {MAX_COMPARE} รุ่น) แล้วกด \"เปรียบเทียบสเปกทันที\"",
            font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("text_muted"),
        ).pack(pady=40)

    def _compare(self):
        ids = []
        for var in self.slot_vars:
            pid = self._label_to_id.get(var.get())
            if pid is not None and pid not in ids:
                ids.append(pid)
        self.error_label.configure(text="")
        try:
            products = product_service.compare_products(ids)
        except (ValueError, PermissionError) as exc:
            self.error_label.configure(text=str(exc))
            self._clear_result()
            return
        self._render(products)

    def _render(self, products):
        self._clear_result()
        outer_card = ThemeManager.make_card(self.result_box)
        outer_card.pack(fill="both", expand=True)

        canvas_bg = ThemeManager.get_color("surface")
        canvas = tk.Canvas(outer_card, bg=canvas_bg, highlightthickness=0, height=680)
        hbar = ctk.CTkScrollbar(outer_card, orientation="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=hbar.set)
        canvas.pack(fill="both", expand=True, padx=6, pady=(6, 0))
        hbar.pack(fill="x", padx=6, pady=(2, 6))

        card = ctk.CTkFrame(canvas, fg_color=ThemeManager.get_color_pair("surface"), corner_radius=0)
        win_id = canvas.create_window((0, 0), window=card, anchor="nw")

        min_col_w = 215
        total_min_w = 180 + len(products) * min_col_w

        def _sync_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            cw = max(canvas.winfo_width(), total_min_w)
            canvas.itemconfigure(win_id, width=cw)

        card.bind("<Configure>", _sync_scroll)
        canvas.bind("<Configure>", _sync_scroll)

        card.grid_columnconfigure(0, minsize=180)
        for col in range(1, len(products) + 1):
            card.grid_columnconfigure(col, weight=1, minsize=min_col_w, uniform="cmp")

        head_corner = ctk.CTkFrame(card, fg_color=ThemeManager.get_color_pair("secondary"), corner_radius=0)
        head_corner.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        ctk.CTkLabel(
            head_corner, text="Technical Specs / รุ่นไม้",
            font=ThemeManager.get_font("body_bold"),
            text_color=ThemeManager.get_color_pair("primary"),
        ).pack(expand=True, padx=10, pady=16)

        for col, p in enumerate(products, start=1):
            cell = ctk.CTkFrame(card, fg_color=ThemeManager.get_color_pair("surface"), corner_radius=0)
            cell.grid(row=0, column=col, sticky="nsew", padx=6, pady=10)
            image = load_ctk_image(p.get("image_path"), (135, 135))
            self._images.append(image)
            ctk.CTkLabel(cell, text="", image=image).pack()
            ctk.CTkLabel(
                cell, text=(p.get("brand_name") or "").upper(),
                font=ThemeManager.get_font("tiny"),
                text_color=ThemeManager.get_color_pair("info"),
            ).pack(pady=(4, 0))
            ctk.CTkLabel(
                cell, text=p["name"], font=ThemeManager.get_font("body_bold"),
                wraplength=min_col_w - 20, justify="center",
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(pady=(2, 4))
            ctk.CTkButton(
                cell, text="ดูรายละเอียด ›", width=120,
                command=lambda pid=p["id"]: self.controller.show("product_detail", product_id=pid),
                **ThemeManager.button_style("primary", "sm"),
            ).pack(pady=(2, 4))

        prices = [float(p["effective_price"]) for p in products]
        cheapest = min(prices) if len(set(prices)) > 1 else None

        for row, (label, key) in enumerate(_ROWS, start=1):
            bg = ThemeManager.get_color_pair("surface_alt") if row % 2 else ThemeManager.get_color_pair("surface")
            head = ctk.CTkFrame(card, fg_color=bg, corner_radius=0)
            head.grid(row=row, column=0, sticky="nsew", pady=1)
            ctk.CTkLabel(
                head, text=label, font=ThemeManager.get_font("small_bold"), anchor="w",
                text_color=ThemeManager.get_color_pair("text_main"),
            ).pack(fill="x", padx=14, pady=10)
            for col, p in enumerate(products, start=1):
                cell = ctk.CTkFrame(card, fg_color=bg, corner_radius=0)
                cell.grid(row=row, column=col, sticky="nsew", pady=1)
                self._fill_cell(cell, key, p, cheapest, min_col_w)

    def _fill_cell(self, cell, key, p, cheapest, min_col_w):
        text_main = ThemeManager.get_color_pair("text_main")
        if key == "price":
            best = cheapest is not None and float(p["effective_price"]) == cheapest
            ctk.CTkLabel(
                cell, text=format_price(p["effective_price"]), font=ThemeManager.get_font("price"),
                text_color=ThemeManager.get_color_pair("danger" if p.get("is_on_sale") else ("success" if best else "text_main")),
            ).pack(pady=(6, 0))
            if best:
                ThemeManager.make_badge(cell, "★ คุ้มค่าที่สุด", "success").pack(pady=2)
            if p.get("is_on_sale"):
                ctk.CTkLabel(
                    cell, text=f"ปกติ {format_price(p['price'])}", font=ThemeManager.get_font("tiny"),
                    text_color=ThemeManager.get_color_pair("text_muted"),
                ).pack(pady=(0, 4))
            else:
                ctk.CTkFrame(cell, fg_color="transparent", height=6).pack()
        elif key == "rating":
            stars = RatingStars(cell, value=p.get("avg_rating") or 0, count=p.get("review_count") or 0, size=13)
            stars.pack(pady=10)
        elif key == "stock":
            ok = bool(p.get("in_stock"))
            ctk.CTkLabel(
                cell, text="✓ พร้อมส่ง" if ok else "⛔ สินค้าหมด",
                font=ThemeManager.get_font("small_bold"),
                text_color=ThemeManager.get_color_pair("success" if ok else "danger"),
            ).pack(pady=10)
        elif key == "weight_grip_display":
            val = p.get("spec_weight_grip") or p.get("weight_class") or "-"
            ctk.CTkLabel(
                cell, text=str(val), font=ThemeManager.get_font("body_bold"),
                text_color=text_main, wraplength=min_col_w - 20, justify="center",
            ).pack(pady=10, padx=6)
        elif key == "balance_point_display":
            val = validators.format_balance_point_display(
                p.get("spec_balance_mm"), p.get("spec_balance_type") or p.get("balance")
            ) or "-"
            ctk.CTkLabel(
                cell, text=str(val), font=ThemeManager.get_font("body_bold"),
                text_color=text_main, wraplength=min_col_w - 20, justify="center",
            ).pack(pady=10, padx=6)
        else:
            ctk.CTkLabel(
                cell, text=str(p.get(key) or "-"), font=ThemeManager.get_font("body_bold"),
                text_color=text_main, wraplength=min_col_w - 20, justify="center",
            ).pack(pady=10, padx=6)
