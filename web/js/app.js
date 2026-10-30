// web/js/app.js — บูตแอป, สลับเปลือกหน้า (Auth / Buyer Navbar / Admin Sidebar), และหน้าจอล็อกอัตโนมัติของแอดมิน
import { api, esc, setOnIdleLocked } from './api.js';
import { state } from './state.js';
import { createRouter } from './router.js';
import { renderNavbar } from './components/navbar.js';
import { renderSidebar } from './components/sidebar.js';
import { iconSvg } from './components/icons.js';

const AUTH_FULLSCREEN_PAGES = new Set(['login', 'register']);

const navbarSlot = document.getElementById('navbar-slot');
const sidebarSlot = document.getElementById('sidebar-slot');
const pageSlot = document.getElementById('page-slot');
const lockRoot = document.getElementById('lock-root');

function shellKindFor(pageName) {
  if (AUTH_FULLSCREEN_PAGES.has(pageName)) return 'auth';
  if (state.logged_in && state.is_staff) return 'admin';
  if (String(pageName || '').startsWith('admin_')) return 'admin';
  return 'buyer';
}

const router = createRouter({
  pageSlot,
  async onBeforeShow(pageName) {
    try {
      await api.refreshSession();
    } catch (e) {}
    await syncShell(pageName);
    syncLockOverlay();
  },
});

async function syncShell(pageName) {
  const kind = shellKindFor(pageName || state.current_page);
  if (kind === 'auth') {
    navbarSlot.classList.add('hidden');
    navbarSlot.innerHTML = '';
    sidebarSlot.classList.add('hidden');
    sidebarSlot.innerHTML = '';
  } else if (kind === 'admin') {
    navbarSlot.classList.add('hidden');
    navbarSlot.innerHTML = '';
    sidebarSlot.classList.remove('hidden');
    await renderSidebar(sidebarSlot, router);
  } else {
    sidebarSlot.classList.add('hidden');
    sidebarSlot.innerHTML = '';
    navbarSlot.classList.remove('hidden');
    renderNavbar(navbarSlot, router);
  }
}

function syncLockOverlay() {
  if (!state.is_locked || !state.logged_in) {
    lockRoot.classList.add('hidden');
    lockRoot.innerHTML = '';
    return;
  }
  if (!lockRoot.classList.contains('hidden') && lockRoot.children.length > 0) {
    return;
  }
  const uname = (state.user && (state.user.full_name || state.user.username)) || '';
  lockRoot.classList.remove('hidden');
  lockRoot.innerHTML = `
    <div class="idle-lock-overlay">
      <div class="card" style="width:420px;padding:28px 32px;text-align:center">
        <div style="margin-bottom:8px">${iconSvg('lock', 36, 'var(--color-primary)')}</div>
        <div class="text-h2" style="margin-bottom:4px">หน้าจอถูกล็อก</div>
        <div class="text-small text-muted" style="margin-bottom:18px">ไม่มีการใช้งานเกินเวลาที่กำหนด กรุณาใส่รหัสผ่านของ ${esc(uname)} เพื่อทำรายการต่อ</div>
        <input type="password" class="input" data-role="pw" placeholder="รหัสผ่าน" style="margin-bottom:6px" />
        <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:10px"></div>
        <button type="button" class="btn btn-primary btn-md" data-role="unlock" style="width:100%;margin-bottom:8px">ปลดล็อก</button>
        <button type="button" class="btn btn-ghost btn-sm" data-role="logout" style="width:100%">ออกจากระบบ</button>
      </div>
    </div>
  `;

  const pwIn = lockRoot.querySelector('[data-role="pw"]');
  const errEl = lockRoot.querySelector('[data-role="err"]');
  const unlockBtn = lockRoot.querySelector('[data-role="unlock"]');
  const logoutBtn = lockRoot.querySelector('[data-role="logout"]');

  const doUnlock = async () => {
    const pw = pwIn.value;
    if (!pw) {
      errEl.textContent = 'กรุณากรอกรหัสผ่าน';
      return;
    }
    try {
      await api.post('/api/auth/unlock', { password: pw });
      await api.refreshSession();
      lockRoot.classList.add('hidden');
      lockRoot.innerHTML = '';
    } catch (err) {
      errEl.textContent = err.message || 'รหัสผ่านไม่ถูกต้อง';
      pwIn.value = '';
      pwIn.focus();
    }
  };

  unlockBtn.addEventListener('click', doUnlock);
  pwIn.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doUnlock();
  });
  logoutBtn.addEventListener('click', async () => {
    lockRoot.classList.add('hidden');
    lockRoot.innerHTML = '';
    await router.logout();
  });
  setTimeout(() => pwIn.focus(), 50);
}

setOnIdleLocked(() => {
  syncLockOverlay();
});

// Idle detection & heartbeat for staff
let lastActivityPing = 0;
function onUserActivity() {
  if (!state.logged_in || state.is_locked) return;
  const now = Date.now();
  if (now - lastActivityPing > 30000) {
    lastActivityPing = now;
    api.post('/api/auth/heartbeat').catch(() => {});
  }
}
['mousemove', 'mousedown', 'keydown', 'touchstart'].forEach((ev) => {
  window.addEventListener(ev, onUserActivity, { passive: true });
});

// Periodic session check (detects idle lock & updates badges)
setInterval(async () => {
  if (!state.logged_in && !state.guest_mode) return;
  try {
    await api.refreshSession();
    syncLockOverlay();
  } catch (e) {}
}, 20000);

// Boot application
(async function boot() {
  try {
    await api.refreshSession();
  } catch (e) {}

  const parsed = router.parseHash();
  if (parsed) {
    const [route, params] = parsed;
    await router.show(route, params, { pushHistory: false });
  } else if (state.logged_in) {
    if (state.is_staff) {
      await router.show('admin_dashboard', {}, { pushHistory: false });
    } else {
      await router.show('home', {}, { pushHistory: false });
    }
  } else if (state.guest_mode) {
    await router.show('home', {}, { pushHistory: false });
  } else {
    await router.show('login', {}, { pushHistory: false });
  }
})();
