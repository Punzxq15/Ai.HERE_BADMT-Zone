// web/js/components/navbar.js — แถบนำทางบนของฝั่งผู้ซื้อ (ตรงกับ ui/components/navbar.py)
import { api, esc } from '../api.js';
import { state } from '../state.js';
import { iconSvg } from './icons.js';
import { createSearchBar } from './search_bar.js';
import { openModal } from './dialogs.js';

export function renderNavbar(slot, router) {
  slot.innerHTML = '';
  const nav = document.createElement('div');
  nav.className = 'navbar';

  const left = document.createElement('div');
  left.className = 'navbar-left';

  const shopName = state.getShopName ? state.getShopName() : ((state.shop && state.shop.shop_name) || 'AI.HERE BADᴍᴛ-Zone');
  if (typeof document !== 'undefined') {
    document.title = shopName;
  }

  const logoBtn = document.createElement('button');
  logoBtn.type = 'button';
  logoBtn.className = 'navbar-logo';
  logoBtn.title = shopName;
  logoBtn.innerHTML = `${iconSvg('racket', 20, '#FFB703')} <span data-role="navbar-shop-name">${esc(shopName)}</span>`;
  logoBtn.addEventListener('click', () => router.show('home'));
  left.appendChild(logoBtn);

  const navLinks = [
    { text: 'หน้าแรก', icon: null, action: () => router.show('home') },
    { text: 'หมวดหมู่', icon: 'category', action: () => router.show('category') },
    { text: 'ค้นหาไม้ที่ใช่', icon: 'target', action: () => router.show('racket_finder') },
    { text: 'เปรียบเทียบ', icon: 'compare', action: () => router.show('compare') },
    { text: 'ตำแหน่งร้าน', icon: 'map_pin', action: () => showLocationPopup() },
  ];
  for (const item of navLinks) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'navbar-nav-btn';
    b.innerHTML = `${item.icon ? iconSvg(item.icon, 16, '#FFFFFF') : ''}<span>${esc(item.text)}</span>`;
    b.addEventListener('click', item.action);
    left.appendChild(b);
  }
  nav.appendChild(left);

  // กลาง: ช่องค้นหา
  const searchBar = createSearchBar({
    width: 360,
    onSubmit: (q) => router.show('category', { search: q }),
    onSelectSuggestion: (pid) => router.show('product_detail', { product_id: pid }),
  });
  nav.appendChild(searchBar.el);

  // ขวา: ปุ่มไอคอน + ปุ่มบัญชี
  const right = document.createElement('div');
  right.className = 'navbar-right';

  const makeIconBtn = (iconName, iconColor, route, count = 0, title = '') => {
    const wrap = document.createElement('div');
    wrap.className = 'navbar-icon-wrap';
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'navbar-nav-btn';
    b.style.width = '40px';
    b.style.justifyContent = 'center';
    b.title = title;
    b.innerHTML = iconSvg(iconName, 18, iconColor);
    b.addEventListener('click', () => router.show(route));
    wrap.appendChild(b);
    if (count > 0) {
      const badge = document.createElement('span');
      badge.className = 'navbar-badge';
      badge.textContent = count > 99 ? '99+' : String(count);
      wrap.appendChild(badge);
    }
    return wrap;
  };

  right.appendChild(makeIconBtn('heart', '#FF6B81', 'wishlist', 0, 'รายการโปรด'));
  right.appendChild(makeIconBtn('cart', '#FFB703', 'cart', state.badges.cart_count || 0, 'ตะกร้าสินค้า'));
  right.appendChild(makeIconBtn('bell', '#FDE047', 'notifications', state.badges.unread_notifications || 0, 'การแจ้งเตือน'));
  right.appendChild(makeIconBtn('chat', '#38BDF8', 'chat', state.badges.unread_chat_for_buyer || 0, 'แชทกับร้าน'));

  const themeBtn = document.createElement('button');
  themeBtn.type = 'button';
  themeBtn.className = 'navbar-nav-btn';
  themeBtn.style.width = '38px';
  themeBtn.style.justifyContent = 'center';
  themeBtn.title = 'สลับโหมดสี';
  themeBtn.innerHTML = iconSvg('theme', 18, '#FDE047');
  themeBtn.addEventListener('click', async () => {
    const mode = state.toggleTheme();
    if (state.logged_in) {
      try { await api.put('/api/buyer/profile/theme', { theme_mode: mode }); } catch (e) {}
    }
  });
  right.appendChild(themeBtn);

  if (state.logged_in && state.user) {
    const orderBtn = document.createElement('button');
    orderBtn.type = 'button';
    orderBtn.className = 'navbar-nav-btn';
    orderBtn.innerHTML = `${iconSvg('order', 16, '#FFFFFF')}<span>คำสั่งซื้อ</span>`;
    orderBtn.addEventListener('click', () => router.show('orders'));
    right.appendChild(orderBtn);

    if (state.is_staff) {
      const adminBtn = document.createElement('button');
      adminBtn.type = 'button';
      adminBtn.className = 'btn btn-primary btn-sm';
      adminBtn.textContent = 'หลังบ้าน';
      adminBtn.addEventListener('click', () => router.show('admin_dashboard'));
      right.appendChild(adminBtn);
    }

    const name = (state.user.full_name || state.user.username || 'บัญชี').slice(0, 14);
    const profBtn = document.createElement('button');
    profBtn.type = 'button';
    profBtn.className = 'navbar-nav-btn';
    profBtn.innerHTML = `${iconSvg('user', 16, '#FFB703')}<span>${esc(name)}</span>`;
    profBtn.addEventListener('click', () => router.show('profile'));
    right.appendChild(profBtn);

    const outBtn = document.createElement('button');
    outBtn.type = 'button';
    outBtn.className = 'navbar-nav-btn';
    outBtn.style.color = '#CBD5E1';
    outBtn.innerHTML = `${iconSvg('logout', 16, '#F87171')}<span>ออก</span>`;
    outBtn.addEventListener('click', () => router.logout());
    right.appendChild(outBtn);
  } else {
    const loginBtn = document.createElement('button');
    loginBtn.type = 'button';
    loginBtn.className = 'btn btn-primary btn-sm';
    loginBtn.textContent = 'เข้าสู่ระบบ';
    loginBtn.addEventListener('click', () => router.show('login'));
    right.appendChild(loginBtn);

    const regBtn = document.createElement('button');
    regBtn.type = 'button';
    regBtn.className = 'navbar-nav-btn';
    regBtn.textContent = 'สมัครสมาชิก';
    regBtn.addEventListener('click', () => router.show('register'));
    right.appendChild(regBtn);
  }

  nav.appendChild(right);
  slot.appendChild(nav);
  return { searchBar };
}

async function showLocationPopup() {
  let s = {};
  try {
    s = { ...(state.shop || {}), ...(state.contact || {}) };
    if (!s.shop_name || !String(s.shop_name).trim()) {
      s = await api.get('/api/settings/shop');
    }
  } catch (e) {}

  const shopName = (s.shop_name && String(s.shop_name).trim()) ? String(s.shop_name) : 'AI.HERE BADᴍᴛ-Zone';
  const addr = s.shop_address || 'ยังไม่ได้ระบุที่อยู่ร้าน';
  const phone = s.shop_phone || '-';
  const email = s.shop_email || '-';
  const hours = s.shop_hours || s.shop_open_hours || 'เปิดบริการทุกวัน 10:00 - 20:00 น.';
  const mapsUrl = (s.maps_url || s.shop_maps_url || '').trim();
  const lat = s.shop_lat || '';
  const lng = s.shop_lng || '';

  openModal({
    title: 'ตำแหน่งที่ตั้งร้านค้า',
    width: 520,
    render(card, close) {
      card.innerHTML = `
        <div class="text-h2" style="margin-bottom:4px">📍 ตำแหน่งร้านค้า</div>
        <div class="text-body-bold text-primary" style="margin-bottom:12px">${esc(shopName)}</div>
        <div class="card-alt" style="padding:14px 16px;margin-bottom:16px">
          <div style="margin-bottom:6px"><strong>ที่อยู่:</strong> ${esc(addr)}</div>
          <div style="margin-bottom:6px"><strong>เวลาทำการ:</strong> ${esc(hours)}</div>
          <div style="margin-bottom:6px"><strong>โทรศัพท์:</strong> ${esc(phone)}</div>
          <div><strong>อีเมล:</strong> ${esc(email)}</div>
          ${(lat && lng) ? `<div class="text-small text-muted" style="margin-top:6px">พิกัด GPS: ${esc(lat)}, ${esc(lng)}</div>` : ''}
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center">
          ${mapsUrl ? `<a href="${esc(mapsUrl)}" target="_blank" rel="noopener" class="btn btn-info btn-md">🗺️ เปิดใน Google Maps</a>` : `<span></span>`}
          <button type="button" class="btn btn-outline btn-md" data-role="close">ปิด</button>
        </div>
      `;
      card.querySelector('[data-role="close"]').addEventListener('click', () => close());
    },
  });
}
