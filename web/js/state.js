// web/js/state.js — สถานะฝั่งเบราว์เซอร์ (ซิงก์กับ /api/bootstrap)
export const state = {
  user: null,
  role: 'guest',
  logged_in: false,
  guest_mode: false,
  is_staff: false,
  is_owner: false,
  is_locked: false,
  must_change_password: false,
  shop: {},
  login_banners: [],
  contact: {},
  badges: {
    cart_count: 0,
    unread_notifications: 0,
    unread_chat: 0,
    unread_chat_for_buyer: 0,
    unread_chat_for_staff: 0,
    pending_slips: 0,
  },
  pending_after_login: null, // [page_name, params]
  compare_ids: [],
  current_page: null,
  current_params: {},
  theme: document.documentElement.getAttribute('data-theme') || 'light',
  _listeners: new Set(),

  updateFromSession(data) {
    if (!data) return;
    this.user = data.user || null;
    this.logged_in = Boolean(data.is_authenticated ?? data.logged_in);
    this.guest_mode = Boolean(data.is_guest ?? data.guest_mode);
    this.role = (this.user && this.user.role) || data.role || 'guest';
    this.is_staff = this.role === 'admin' || this.role === 'owner';
    this.is_owner = this.role === 'owner';
    this.is_locked = Boolean(data.is_locked);
    this.must_change_password = Boolean(
      (this.user && this.user.must_change_password) ?? data.must_change_password
    );
    if (data.shop) this.shop = data.shop;
    if (Array.isArray(data.login_banners)) {
      this.login_banners = data.login_banners;
    } else if (data.shop && Array.isArray(data.shop.login_banners)) {
      this.login_banners = data.shop.login_banners;
    }
    if (data.contact) this.contact = data.contact;
    if (data.badges) {
      const uc = Number(data.badges.unread_chat || 0);
      this.badges = {
        ...this.badges,
        ...data.badges,
        unread_chat_for_buyer: this.role === 'buyer' ? uc : (data.badges.unread_chat_for_buyer || 0),
        unread_chat_for_staff: this.is_staff ? uc : (data.badges.unread_chat_for_staff || 0),
      };
    }
    this.syncDocumentTitle();
    this.notify();
  },

  getShopName() {
    const raw = this.shop && typeof this.shop.shop_name === "string"
      ? this.shop.shop_name.trim()
      : "";
    return raw || "AI.HERE BADᴍᴛ-Zone";
  },

  syncDocumentTitle(customShopName) {
    if (typeof customShopName === "string" && customShopName.trim()) {
      if (!this.shop) this.shop = {};
      this.shop.shop_name = customShopName.trim();
    }
    if (typeof document !== "undefined") {
      document.title = this.getShopName();
    }
  },

  setTheme(mode, saveLocal = true) {
    const m = mode === 'dark' ? 'dark' : 'light';
    this.theme = m;
    document.documentElement.setAttribute('data-theme', m);
    if (saveLocal) {
      try {
        localStorage.setItem('badminton_theme', m);
      } catch (e) {}
    }
    this.notify();
  },

  toggleTheme() {
    const next = this.theme === 'dark' ? 'light' : 'dark';
    this.setTheme(next, true);
    return next;
  },

  subscribe(fn) {
    this._listeners.add(fn);
    return () => this._listeners.delete(fn);
  },

  notify() {
    for (const fn of this._listeners) {
      try { fn(this); } catch (e) {}
    }
  }
};

export function syncDocumentTitle(shopName) {
  state.syncDocumentTitle(shopName);
}
