// web/js/components/sidebar.js — แถบเมนูซ้ายของหลังบ้าน (แอดมิน / เจ้าของร้าน)
import { api, esc, ROLE_LABELS } from '../api.js';
import { state } from '../state.js';
import { iconSvg } from './icons.js';
import { openModal, showToast, setFieldError, clearFieldError } from './dialogs.js';

const MENU = [
  ['แดชบอร์ด',        'admin_dashboard',  false, 'chart'],
  ['สินค้า',           'admin_products',   false, 'racket'],
  ['หมวดหมู่ / แบรนด์', 'admin_categories', false, 'category'],
  ['คำสั่งซื้อ',        'admin_orders',     false, 'order'],
  ['ตรวจสลิป',         'admin_payments',   false, 'check'],
  ['คูปอง',           'admin_coupons',    false, 'coupon'],
  ['แชทลูกค้า',        'admin_chat',       false, 'chat'],
  ['ผู้ใช้และสิทธิ์',    'admin_users',      true,  'users'],
  ['ตั้งค่าร้าน',       'admin_settings',   true,  'settings'],
];

export async function renderSidebar(slot, router) {
  let publicSettings = {};
  if (!state.is_owner) {
    try {
      const c = await api.get('/api/settings/contact'); publicSettings = { owner_contact_name: c.owner_name, owner_contact_phone: c.phone, owner_contact_email: c.email, owner_contact_line: c.line_id, owner_contact_note: c.note, shop_name: c.shop_name };
    } catch (e) {}
  }

  slot.innerHTML = '';
  const aside = document.createElement('div');
  aside.className = 'sidebar';

  const top = document.createElement('div');
  const brandWrap = document.createElement('div');
  brandWrap.className = 'sidebar-top';
  const roleLabel = ROLE_LABELS[state.role] || '';
  const uname = (state.user && (state.user.full_name || state.user.username)) || '';
  brandWrap.innerHTML = `
    <div class="sidebar-brand">${iconSvg('racket', 20, '#FFB703')} <span>ระบบจัดการร้าน</span></div>
    <div class="sidebar-role">${esc(roleLabel)}${uname ? ` · ${esc(uname)}` : ''}</div>
  `;
  top.appendChild(brandWrap);

  const div1 = document.createElement('div');
  div1.className = 'sidebar-divider';
  top.appendChild(div1);

  const menuWrap = document.createElement('div');
  menuWrap.className = 'sidebar-menu';

  const curRoute = state.current_page;
  const chatBadge = state.badges.unread_chat_for_staff || 0;

  for (const [text, route, ownerOnly, iconName] of MENU) {
    if (ownerOnly && !state.is_owner) continue;
    const isActive = (curRoute === route) ||
      (route === 'admin_products' && curRoute === 'admin_product_form') ||
      (route === 'admin_orders' && curRoute === 'admin_order_detail') ||
      (route === 'admin_coupons' && curRoute === 'admin_coupon_form');
    const b = document.createElement('button');
    b.type = 'button';
    b.className = `sidebar-btn ${isActive ? 'active' : ''}`;
    const label = (route === 'admin_chat' && chatBadge > 0) ? `${text} (${chatBadge})` : text;
    b.innerHTML = `
      ${iconSvg(iconName, 16, isActive ? '#111318' : '#FFB703')}
      <span>${esc(label)}</span>
    `;
    b.addEventListener('click', () => router.show(route));
    menuWrap.appendChild(b);
  }
  top.appendChild(menuWrap);
  aside.appendChild(top);

  const bottom = document.createElement('div');
  bottom.className = 'sidebar-bottom';

  // การ์ดติดต่อเจ้าของร้าน (สำหรับแอดมิน ข้อ 4)
  if (!state.is_owner) {
    const ownerName = publicSettings.owner_contact_name || publicSettings.shop_name || 'เจ้าของร้าน';
    const ownerPhone = publicSettings.owner_contact_phone || publicSettings.shop_phone || '-';
    const ownerEmail = publicSettings.owner_contact_email || publicSettings.shop_email || '-';
    const ownerLine = publicSettings.owner_contact_line || '-';
    const ownerNote = publicSettings.owner_contact_note || '';

    const contactCard = document.createElement('div');
    contactCard.className = 'sidebar-contact-card';
    contactCard.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;color:#FFB703;font-size:12px;font-weight:700;margin-bottom:4px">
        ${iconSvg('phone', 14, '#FFB703')}
        <span>ติดต่อเจ้าของร้าน</span>
      </div>
      <div class="text-tiny" style="color:#E2E8F0;white-space:pre-line">ผู้ดูแล: ${esc(ownerName)}
โทร: ${esc(ownerPhone)}
อีเมล: ${esc(ownerEmail)}${ownerLine && ownerLine !== '-' ? `
LINE: ${esc(ownerLine)}` : ''}${ownerNote ? `
(${esc(ownerNote)})` : ''}</div>
      ${ownerEmail && ownerEmail !== '-' ? `
        <button type="button" class="btn btn-primary btn-sm" style="width:100%;height:28px;margin-top:6px" data-role="email-owner">
          ${iconSvg('mail', 14, '#111318')} <span>ส่งเมลหาเจ้าของร้าน</span>
        </button>
      ` : ''}
    `;
    const emailBtn = contactCard.querySelector('[data-role="email-owner"]');
    if (emailBtn) {
      emailBtn.addEventListener('click', () => openEmailOwnerDialog(ownerName, ownerEmail));
    }
    bottom.appendChild(contactCard);
  }

  const div2 = document.createElement('div');
  div2.className = 'sidebar-divider';
  bottom.appendChild(div2);

  const addBottomBtn = (iconName, iconColor, label, onClick, textColor = '#FFFFFF') => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'sidebar-btn';
    b.style.height = '34px';
    b.style.color = textColor;
    b.innerHTML = `${iconSvg(iconName, 16, iconColor)} <span>${esc(label)}</span>`;
    b.addEventListener('click', onClick);
    bottom.appendChild(b);
  };

  addBottomBtn('bell', '#FDE047', 'การแจ้งเตือน', () => router.show('notifications'));
  addBottomBtn('user', '#FFB703', 'โปรไฟล์ของฉัน', () => router.show('profile'));
  addBottomBtn('theme', '#FDE047', 'สลับโหมดสว่าง / มืด', async () => {
    const mode = state.toggleTheme();
    if (state.logged_in) {
      try { await api.put('/api/buyer/profile/theme', { theme_mode: mode }); } catch (e) {}
    }
  });
  addBottomBtn('logout', '#F87171', 'ออกจากระบบ', () => router.logout(), '#FF8A8A');

  aside.appendChild(bottom);
  slot.appendChild(aside);
}

function openEmailOwnerDialog(ownerName, ownerEmail) {
  const senderName = (state.user && (state.user.full_name || state.user.username)) || 'Admin';
  openModal({
    title: 'ส่งอีเมลติดต่อเจ้าของร้าน',
    width: 480,
    render(card, close) {
      card.innerHTML = `
        <div class="text-h3" style="margin-bottom:4px">✉️ ส่งอีเมลถึง ${esc(ownerName)}</div>
        <div class="text-small text-muted" style="margin-bottom:12px">ผู้รับ: ${esc(ownerEmail)}  |  จากแอดมิน: ${esc(senderName)}</div>
        <div class="text-small-bold" style="margin-bottom:4px">หัวข้อเรื่อง</div>
        <input type="text" class="input" data-role="subj" value="[แจ้งเรื่องด่วนจากแอดมิน] โดย ${esc(senderName)}" placeholder="ระบุหัวข้อเรื่อง..." style="margin-bottom:10px" />
        <div class="text-small-bold" style="margin-bottom:4px">รายละเอียดข้อความ</div>
        <textarea class="textarea" data-role="body" rows="5" placeholder="พิมพ์ข้อความที่ต้องการแจ้งเจ้าของร้าน..."></textarea>
        <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-top:4px"></div>
        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">
          <button type="button" class="btn btn-outline btn-sm" data-role="cancel">ยกเลิก</button>
          <button type="button" class="btn btn-primary btn-sm" data-role="send">ส่งอีเมล</button>
        </div>
      `;
      const subj = card.querySelector('[data-role="subj"]');
      const body = card.querySelector('[data-role="body"]');
      const err = card.querySelector('[data-role="err"]');
      subj.addEventListener('input', () => clearFieldError(subj));
      body.addEventListener('input', () => clearFieldError(body));
      card.querySelector('[data-role="cancel"]').addEventListener('click', () => close());
      card.querySelector('[data-role="send"]').addEventListener('click', async () => {
        err.textContent = '';
        clearFieldError(subj);
        clearFieldError(body);
        const sVal = subj.value.trim();
        const bVal = body.value.trim();
        if (!sVal) {
          const msg = 'กรุณาระบุหัวข้อเรื่อง';
          setFieldError(subj, msg);
          showToast(msg, 'error');
          return;
        }
        if (!bVal) {
          const msg = 'กรุณากรอกรายละเอียดข้อความ';
          setFieldError(body, msg);
          showToast(msg, 'error');
          return;
        }
        try {
          await api.post('/api/contact/urgent-email', { subject: sVal, message: bVal });
          close();
          showToast(`ส่งอีเมลถึง ${ownerEmail} เรียบร้อยแล้ว`, 'success');
        } catch (ex) {
          const em = ex.message || 'ส่งอีเมลไม่สำเร็จ';
          err.textContent = `⛔ ${em}`;
          showToast(em, 'error');
        }
      });
    },
  });
}
