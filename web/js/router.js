// web/js/router.js — ตัวจัดการเปลี่ยนหน้าและตรวจสิทธิ์ตาม ROUTE_TABLE / ROUTE_ROLES (ตรงกับ ui/router.py)
import { api } from './api.js';
import { state } from './state.js';

export const ROUTE_TABLE = {
  // ฝั่งผู้ซื้อ (18 หน้า)
  login:              () => import('./pages/buyer/login.js'),
  register:           () => import('./pages/buyer/register.js'),
  home:               () => import('./pages/buyer/home.js'),
  category:           () => import('./pages/buyer/category.js'),
  product_detail:     () => import('./pages/buyer/product_detail.js'),
  compare:            () => import('./pages/buyer/compare.js'),
  racket_finder:      () => import('./pages/buyer/racket_finder.js'),
  wishlist:           () => import('./pages/buyer/wishlist.js'),
  cart:               () => import('./pages/buyer/cart.js'),
  addresses:          () => import('./pages/buyer/addresses.js'),
  checkout:           () => import('./pages/buyer/checkout.js'),
  payment:            () => import('./pages/buyer/payment.js'),
  orders:             () => import('./pages/buyer/orders.js'),
  order_detail:       () => import('./pages/buyer/order_detail.js'),
  write_review:       () => import('./pages/buyer/write_review.js'),
  profile:            () => import('./pages/buyer/profile.js'),
  notifications:      () => import('./pages/buyer/notifications.js'),
  chat:               () => import('./pages/buyer/chat.js'),
  // ฝั่งแอดมิน / เจ้าของร้าน (12 หน้า)
  admin_dashboard:    () => import('./pages/admin/dashboard.js'),
  admin_products:     () => import('./pages/admin/products.js'),
  admin_product_form: () => import('./pages/admin/product_form.js'),
  admin_categories:   () => import('./pages/admin/categories.js'),
  admin_orders:       () => import('./pages/admin/orders.js'),
  admin_order_detail: () => import('./pages/admin/order_detail.js'),
  admin_payments:     () => import('./pages/admin/payments.js'),
  admin_coupons:      () => import('./pages/admin/coupons.js'),
  admin_coupon_form:  () => import('./pages/admin/coupon_form.js'),
  admin_chat:         () => import('./pages/admin/chat.js'),
  admin_users:        () => import('./pages/admin/users.js'),
  admin_settings:     () => import('./pages/admin/settings.js'),
};

const BUYER_ONLY = new Set(['buyer']);
const ALL_LOGGED_IN = new Set(['buyer', 'admin', 'owner']);
const STAFF_ROLES = new Set(['admin', 'owner']);
const OWNER_ONLY = new Set(['owner']);

export const PUBLIC_ROUTES = new Set(['login', 'register']);

export const GUEST_STOREFRONT_ROUTES = new Set([
  'home', 'category', 'product_detail', 'compare', 'racket_finder',
]);

export const ROUTE_ROLES = {
  home:               BUYER_ONLY,
  category:           BUYER_ONLY,
  product_detail:     BUYER_ONLY,
  compare:            BUYER_ONLY,
  racket_finder:      BUYER_ONLY,
  wishlist:           BUYER_ONLY,
  cart:               BUYER_ONLY,
  addresses:          BUYER_ONLY,
  checkout:           BUYER_ONLY,
  payment:            BUYER_ONLY,
  orders:             BUYER_ONLY,
  order_detail:       BUYER_ONLY,
  write_review:       BUYER_ONLY,
  chat:               BUYER_ONLY,
  profile:            ALL_LOGGED_IN,
  notifications:      ALL_LOGGED_IN,
  admin_dashboard:    STAFF_ROLES,
  admin_products:     STAFF_ROLES,
  admin_product_form: STAFF_ROLES,
  admin_orders:       STAFF_ROLES,
  admin_order_detail: STAFF_ROLES,
  admin_payments:     STAFF_ROLES,
  admin_chat:         STAFF_ROLES,
  admin_categories:   OWNER_ONLY,
  admin_coupons:      OWNER_ONLY,
  admin_coupon_form:  OWNER_ONLY,
  admin_users:        OWNER_ONLY,
  admin_settings:     OWNER_ONLY,
};

export function createRouter({ pageSlot, onBeforeShow, onAfterShow }) {
  const historyStack = [];
  let cleanupCurrentPage = null;
  let suppressHashListener = false;

  function canAccess(pageName) {
    if (PUBLIC_ROUTES.has(pageName)) return true;
    if (!state.logged_in && GUEST_STOREFRONT_ROUTES.has(pageName) && state.guest_mode) {
      return true;
    }
    if (!state.logged_in) return false;
    const allowed = ROUTE_ROLES[pageName];
    if (!allowed) return true;
    return allowed.has(state.role);
  }

  function resolveGuard(pageName, params) {
    if (canAccess(pageName)) {
      if (state.logged_in && state.must_change_password && pageName !== 'profile') {
        return ['profile', { force_change_pw: true }];
      }
      return [pageName, params];
    }
    if (!state.logged_in) {
      if (!PUBLIC_ROUTES.has(pageName)) {
        state.pending_after_login = [pageName, params];
      }
      const loginParams = state.guest_mode ? { info_message: 'กรุณาเข้าสู่ระบบเพื่อใช้งานฟังก์ชันนี้' } : {};
      return ['login', loginParams];
    }
    if (state.is_staff) {
      return ['admin_dashboard', {}];
    }
    return ['home', {}];
  }

  function updateUrlHash(pageName, params = {}) {
    const usp = new URLSearchParams();
    for (const [k, v] of Object.entries(params || {})) {
      if (v !== undefined && v !== null && v !== '' && typeof v !== 'object' && typeof v !== 'function') {
        usp.set(k, String(v));
      }
    }
    const qs = usp.toString();
    const nextHash = `#/${pageName}${qs ? `?${qs}` : ''}`;
    if (window.location.hash !== nextHash) {
      suppressHashListener = true;
      window.location.hash = nextHash;
      setTimeout(() => { suppressHashListener = false; }, 20);
    }
  }

  function parseHash() {
    const raw = (window.location.hash || '').replace(/^#\/?/, '');
    if (!raw) return null;
    const [routePart, qsPart] = raw.split('?');
    const route = routePart.trim();
    if (!ROUTE_TABLE[route]) return null;
    const params = {};
    if (qsPart) {
      const usp = new URLSearchParams(qsPart);
      for (const [k, v] of usp.entries()) {
        if (/^\d+$/.test(v)) params[k] = Number(v);
        else if (v === 'true') params[k] = true;
        else if (v === 'false') params[k] = false;
        else params[k] = v;
      }
    }
    return [route, params];
  }

  async function show(pageName, params = {}, { pushHistory = true, syncHash = true } = {}) {
    if (!ROUTE_TABLE[pageName]) {
      console.error(`ไม่พบหน้า '${pageName}' ใน ROUTE_TABLE`);
      pageName = 'home';
    }

    const [target, targetParams] = resolveGuard(pageName, params || {});

    if (pushHistory && state.current_page && state.current_page !== target) {
      historyStack.push([state.current_page, state.current_params]);
      if (historyStack.length > 30) historyStack.shift();
    }

    if (cleanupCurrentPage) {
      try { cleanupCurrentPage(); } catch (e) {}
      cleanupCurrentPage = null;
    }

    state.current_page = target;
    state.current_params = targetParams || {};

    if (syncHash) {
      updateUrlHash(target, targetParams);
    }

    if (onBeforeShow) {
      await onBeforeShow(target, targetParams);
    }

    pageSlot.innerHTML = '';
    pageSlot.scrollTop = 0;

    try {
      const mod = await ROUTE_TABLE[target]();
      const renderFn = mod.render || mod.default;
      if (typeof renderFn === 'function') {
        const cleanup = await renderFn(pageSlot, routerApi, targetParams || {});
        if (typeof cleanup === 'function') {
          cleanupCurrentPage = cleanup;
        }
      }
    } catch (err) {
      console.error('เกิดข้อผิดพลาดขณะโหลดหน้า', target, err);
      pageSlot.innerHTML = `<div class="buyer-container"><div class="card" style="padding:24px"><div class="text-h3 text-danger">โหลดหน้า ${target} ไม่สำเร็จ</div><div class="text-small text-muted" style="margin-top:6px">${err.message || err}</div></div></div>`;
    }

    if (onAfterShow) {
      await onAfterShow(target, targetParams);
    }
  }

  function goBack(fallback = 'home') {
    while (historyStack.length) {
      const [prevPage, prevParams] = historyStack.pop();
      if (prevPage !== state.current_page && canAccess(prevPage)) {
        return show(prevPage, prevParams || {}, { pushHistory: false });
      }
    }
    return show(fallback, {}, { pushHistory: false });
  }

  async function afterLoginSuccess() {
    await api.refreshSession();
    const pending = state.pending_after_login;
    state.pending_after_login = null;
    if (state.must_change_password) {
      return show('profile', { force_change_pw: true });
    }
    if (pending) {
      const [pPage, pParams] = pending;
      if (canAccess(pPage)) {
        return show(pPage, pParams || {});
      }
    }
    if (state.is_staff) {
      return show('admin_dashboard');
    }
    return show('home');
  }

  async function logout() {
    try {
      await api.post('/api/auth/logout');
    } catch (e) {}
    state.pending_after_login = null;
    await api.refreshSession();
    return show('login');
  }

  window.addEventListener('hashchange', () => {
    if (suppressHashListener) return;
    const parsed = parseHash();
    if (parsed) {
      const [r, p] = parsed;
      show(r, p, { pushHistory: true, syncHash: false });
    }
  });

  const routerApi = {
    show,
    go_back: goBack,
    goBack,
    after_login_success: afterLoginSuccess,
    afterLoginSuccess,
    logout,
    parseHash,
    refresh_shell: async () => {
      await api.refreshSession();
      if (onBeforeShow) await onBeforeShow(state.current_page, state.current_params);
    },
    refreshShell: async () => {
      await api.refreshSession();
      if (onBeforeShow) await onBeforeShow(state.current_page, state.current_params);
    },
  };

  return routerApi;
}
