// web/js/pages/admin/users.js — จัดการผู้ใช้ & การกำหนดสิทธิ์แอดมิน (T13 ป้ายสถานะออนไลน์/ออฟไลน์/ถูกระงับ, ดูข้อมูล, ตั้งรหัส, เตะออก, แต่งตั้งแอดมิน)
import { api, esc, formatDateThai, formatDateTime, formatPhone, formatPrice, ROLE_LABELS } from '../../api.js';
import { createPager, pillHtml, thumbHtml } from '../../components/admin_common.js';
import { confirm, openModal, showMessage, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';
import { createSearchBar } from '../../components/search_bar.js';

const PAGE_SIZE = 15;
const ROLE_KINDS = { owner: 'warning', admin: 'info', buyer: 'muted' };

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let page = 1;
  let search = '';
  let roleFilter = '';
  let allUsers = [];
  let currentUserId = null;

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">ผู้ใช้ & การกำหนดสิทธิ์แอดมิน</div>
        <div class="text-small text-muted">ดูข้อมูลรายละเอียดของลูกค้าและแอดมินทุกคน กำหนดสิทธิ์แอดมิน และตั้งรหัสผ่าน — เฉพาะเจ้าของร้าน</div>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button type="button" class="btn btn-outline btn-md" data-role="refresh">รีเฟรช</button>
        <button type="button" class="btn btn-danger btn-md" data-role="tog-assign">แต่งตั้งแอดมินจากอีเมล</button>
        <button type="button" class="btn btn-primary btn-md" data-role="tog-form">＋ เพิ่มแอดมินใหม่</button>
      </div>
    </div>

    <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:4px"></div>

    <!-- กล่องแต่งตั้งแอดมินจากอีเมล -->
    <div class="card hidden" data-role="assign-box" style="padding:14px 16px;margin-bottom:10px">
      <div class="text-h3">แต่งตั้งแอดมินจากอีเมลผู้ใช้ (Assign Admin by Email)</div>
      <div class="text-small text-muted" style="margin-bottom:8px">เลือกอีเมลของผู้ใช้ที่มีอยู่ในระบบ หรือพิมพ์อีเมลเพื่อกำหนดบทบาทเป็นแอดมิน พร้อมตั้งรหัสผ่านสำหรับใช้งาน</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div>
          <div class="text-small text-muted">เลือกจากอีเมลผู้ใช้ที่มีอยู่</div>
          <select class="select" data-role="assign-pick"><option value="">- เลือกจากอีเมลในระบบ -</option></select>
        </div>
        <div>
          <div class="text-small text-muted">อีเมลที่ต้องการแต่งตั้งเป็นแอดมิน *</div>
          <input type="email" class="input" data-role="a-email" placeholder="name@example.com" />
        </div>
        <div>
          <div class="text-small text-muted">ตั้งรหัสผ่านแอดมิน *</div>
          <input type="password" class="input" data-role="a-pw" placeholder="อย่างน้อย 8 ตัวอักษร" />
        </div>
        <div>
          <div class="text-small text-muted">ยืนยันรหัสผ่านแอดมิน *</div>
          <input type="password" class="input" data-role="a-cf" placeholder="พิมพ์รหัสผ่านอีกครั้ง" />
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button type="button" class="btn btn-primary btn-md" data-role="submit-assign">ยืนยันแต่งตั้งเป็นแอดมิน</button>
        <button type="button" class="btn btn-outline btn-md" data-role="close-assign">ปิดแผงนี้</button>
      </div>
    </div>

    <!-- ฟอร์มเพิ่มบัญชีแอดมินใหม่ -->
    <div class="card hidden" data-role="form-box" style="padding:14px 16px;margin-bottom:10px">
      <div class="text-h3">เพิ่มบัญชีแอดมินใหม่</div>
      <div class="text-small text-muted" style="margin-bottom:8px">แอดมินตรวจสลิป/ตอบแชท/จัดการออเดอร์และสินค้าได้ แต่เข้าเมนูของเจ้าของร้านไม่ได้</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><div class="text-small text-muted">ชื่อผู้ใช้ *</div><input type="text" class="input" data-f="username" placeholder="ตัวอักษรอังกฤษ/ตัวเลข" /></div>
        <div><div class="text-small text-muted">อีเมล *</div><input type="email" class="input" data-f="email" placeholder="name@example.com" /></div>
        <div><div class="text-small text-muted">ชื่อ-นามสกุล *</div><input type="text" class="input" data-f="full_name" placeholder="เช่น สมชาย ใจดี" /></div>
        <div><div class="text-small text-muted">เบอร์โทร *</div><input type="text" class="input" data-f="phone" placeholder="0812345678" /></div>
        <div><div class="text-small text-muted">รหัสผ่าน *</div><input type="password" class="input" data-f="password" placeholder="อย่างน้อย 8 ตัวอักษร" /></div>
        <div><div class="text-small text-muted">ยืนยันรหัสผ่าน *</div><input type="password" class="input" data-f="confirm" placeholder="พิมพ์รหัสผ่านอีกครั้ง" /></div>
      </div>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button type="button" class="btn btn-primary btn-md" data-role="create-staff">สร้างบัญชีแอดมิน</button>
        <button type="button" class="btn btn-outline btn-md" data-role="close-form">ปิดฟอร์ม</button>
      </div>
    </div>

    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
      <div data-role="search-slot"></div>
      <select class="select" data-role="role" style="width:160px;height:36px">
        <option value="">ทุกบทบาท</option>
        <option value="owner">เจ้าของร้าน</option>
        <option value="admin">แอดมิน</option>
        <option value="buyer">ผู้ซื้อ</option>
      </select>
    </div>

    <div class="admin-table-header" style="grid-template-columns:1.6fr 1.6fr 100px 110px 110px 300px">
      <span>ผู้ใช้</span><span>อีเมล / เบอร์</span><span>บทบาท</span><span>สถานะ</span><span>สมัครเมื่อ</span><span>จัดการ</span>
    </div>
    <div data-role="list"></div>
    <div data-role="pager-slot"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const assignBox = wrap.querySelector('[data-role="assign-box"]');
  const formBox = wrap.querySelector('[data-role="form-box"]');
  const assignPick = wrap.querySelector('[data-role="assign-pick"]');
  const aEmail = wrap.querySelector('[data-role="a-email"]');
  const roleSel = wrap.querySelector('[data-role="role"]');
  const listEl = wrap.querySelector('[data-role="list"]');
  const pager = createPager((p) => { page = p; paintRows(); });
  wrap.querySelector('[data-role="pager-slot"]').appendChild(pager.el);

  const searchBar = createSearchBar({
    placeholder: 'ค้นหาชื่อ / ชื่อผู้ใช้ / อีเมล',
    width: 280,
    enableSuggestions: false,
    onSubmit(q) {
      search = q;
      page = 1;
      load();
    },
  });
  wrap.querySelector('[data-role="search-slot"]').appendChild(searchBar.el);

  wrap.querySelector('[data-role="tog-assign"]').addEventListener('click', () => assignBox.classList.toggle('hidden'));
  wrap.querySelector('[data-role="close-assign"]').addEventListener('click', () => assignBox.classList.add('hidden'));
  wrap.querySelector('[data-role="tog-form"]').addEventListener('click', () => formBox.classList.toggle('hidden'));
  wrap.querySelector('[data-role="close-form"]').addEventListener('click', () => formBox.classList.add('hidden'));
  wrap.querySelector('[data-role="refresh"]').addEventListener('click', () => { page = 1; load(); });

  assignPick.addEventListener('change', () => {
    if (assignPick.value) aEmail.value = assignPick.value;
  });
  roleSel.addEventListener('change', () => {
    roleFilter = roleSel.value;
    page = 1;
    load();
  });

  wrap.querySelector('[data-role="submit-assign"]').addEventListener('click', async () => {
    errEl.textContent = '';
    try {
      const user = await api.post('/api/admin/users/assign-admin', {
        email: aEmail.value.trim(),
        password: wrap.querySelector('[data-role="a-pw"]').value,
        confirm_password: wrap.querySelector('[data-role="a-cf"]').value,
      });
      assignBox.classList.add('hidden');
      await showMessage('แต่งตั้งแอดมินสำเร็จ', `กำหนดสิทธิ์แอดมินให้กับอีเมล ${user.email} (ชื่อผู้ใช้: @${user.username}) เรียบร้อยแล้ว`, 'success');
      await load();
    } catch (err) {
      const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
    }
  });

  wrap.querySelector('[data-role="create-staff"]').addEventListener('click', async () => {
    errEl.textContent = '';
    const getF = (k) => wrap.querySelector(`[data-f="${k}"]`).value;
    if (getF('password') !== getF('confirm')) {
      errEl.textContent = 'รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน';
      return;
    }
    try {
      const user = await api.post('/api/admin/users/staff', {
        username: getF('username').trim(),
        email: getF('email').trim(),
        full_name: getF('full_name').trim(),
        phone: getF('phone').trim(),
        password: getF('password'),
      });
      wrap.querySelectorAll('[data-f]').forEach((el) => { el.value = ''; });
      formBox.classList.add('hidden');
      await showMessage('สร้างบัญชีแล้ว', `สร้างบัญชีแอดมิน “${user.username || ''}” เรียบร้อย`, 'success');
      await load();
    } catch (err) {
      const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
    }
  });

  async function load() {
    errEl.textContent = '';
    try {
      const res = await api.get('/api/admin/users', {
        role: roleFilter || undefined,
        search: search || undefined,
      });
      allUsers = res.users || [];
      currentUserId = res.current_user_id;
      const emails = allUsers.filter((u) => u.email && u.role !== 'owner').map((u) => u.email);
      assignPick.innerHTML = `<option value="">- เลือกจากอีเมลในระบบ -</option>` +
        emails.map((em) => `<option value="${esc(em)}">${esc(em)}</option>`).join('');
      paintRows();
    } catch (err) {
      errEl.textContent = err.message || 'โหลดรายการผู้ใช้ไม่สำเร็จ';
    }
  }

  function paintRows() {
    listEl.innerHTML = '';
    const total = allUsers.length;
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    page = Math.min(Math.max(1, page), pages);
    const chunk = allUsers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

    if (!chunk.length) {
      listEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">ไม่พบผู้ใช้ตามเงื่อนไขที่เลือก</div>`;
    }

    for (const u of chunk) {
      const active = Boolean(u.is_active ?? 1);
      const isMe = u.id === currentUserId;
      let statusBadge = pillHtml('ออฟไลน์', 'offline');
      if (!active) statusBadge = pillHtml('ถูกระงับ', 'suspended');
      else if (u.is_online) statusBadge = pillHtml('ออนไลน์', 'online');

      const r = document.createElement('div');
      r.className = 'admin-table-row';
      r.style.gridTemplateColumns = '1.6fr 1.6fr 100px 110px 110px 300px';
      r.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;cursor:pointer" data-role="open-detail">
          ${thumbHtml(u.avatar_path, 36)}
          <div>
            <div class="text-body-bold">${esc(u.full_name || '-')}${isMe ? '  (คุณ)' : ''}</div>
            <div class="text-small text-muted">@${esc(u.username || '-')}</div>
          </div>
        </div>
        <div>
          <div class="text-small">${esc(u.email || '-')}</div>
          <div class="text-small text-muted">${esc(formatPhone(u.phone))}</div>
        </div>
        <div>${pillHtml(ROLE_LABELS[u.role] || u.role || '-', ROLE_KINDS[u.role] || 'muted')}</div>
        <div>${statusBadge}</div>
        <div class="text-small text-muted">${esc(formatDateThai(u.created_at))}</div>
        <div style="display:flex;justify-content:flex-end;gap:4px;padding-right:8px;flex-wrap:wrap">
          <button type="button" class="btn btn-info btn-sm" data-role="detail">ดูข้อมูล</button>
          ${(u.role !== 'owner' && !isMe) ? `
            <button type="button" class="btn btn-outline btn-sm" data-role="reset-pw">ตั้งรหัส</button>
            ${u.is_online ? `<button type="button" class="btn btn-outline btn-sm" data-role="kick">เตะออก</button>` : ''}
            <button type="button" class="btn ${active ? 'btn-danger' : 'btn-success'} btn-sm" data-role="tog">${active ? 'ระงับ' : 'เปิดใช้'}</button>
          ` : ''}
        </div>
      `;

      r.querySelector('[data-role="open-detail"]').addEventListener('click', () => openUserDetailModal(u.id, router));
      r.querySelector('[data-role="detail"]').addEventListener('click', () => openUserDetailModal(u.id, router));

      const rstBtn = r.querySelector('[data-role="reset-pw"]');
      if (rstBtn) rstBtn.addEventListener('click', () => openResetPwModal(u));

      const kickBtn = r.querySelector('[data-role="kick"]');
      if (kickBtn) {
        kickBtn.addEventListener('click', async () => {
          await api.post(`/api/admin/users/${u.id}/revoke-sessions`);
          await showMessage('เพิกถอนเซสชันแล้ว', `บังคับออกจากระบบของบัญชี ${u.username} เรียบร้อยแล้ว`, 'success');
          await load();
        });
      }

      const togBtn = r.querySelector('[data-role="tog"]');
      if (togBtn) {
        togBtn.addEventListener('click', async () => {
          if (active) {
            const ok = await confirm('ระงับบัญชี', `ระงับบัญชีของ “${u.full_name || u.username}” ใช่ไหม?
ผู้ใช้นี้จะเข้าสู่ระบบไม่ได้จนกว่าจะเปิดใช้งานอีกครั้ง`, { confirmText: 'ระงับบัญชี', danger: true });
            if (!ok) return;
          }
          await api.post(`/api/admin/users/${u.id}/active`, { active: !active });
          await load();
        });
      }

      listEl.appendChild(r);
    }
    pager.set(page, pages, total);
  }

  function openResetPwModal(u) {
    openModal({
      title: `ตั้งรหัสผ่านใหม่ให้ @${u.username}`,
      width: 420,
      render(card, close) {
        card.innerHTML = `
          <div class="text-h3">ตั้งรหัสผ่านใหม่: @${esc(u.username)}</div>
          <div class="text-small text-muted" style="margin-bottom:10px">อีเมล: ${esc(u.email || '-')} (${esc(ROLE_LABELS[u.role] || u.role)})</div>
          <input type="password" class="input" data-role="pw1" placeholder="รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร)" style="margin-bottom:6px" />
          <input type="password" class="input" data-role="pw2" placeholder="ยืนยันรหัสผ่านใหม่อีกครั้ง" style="margin-bottom:6px" />
          <div class="text-small text-danger" data-role="err" style="min-height:18px"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">
            <button type="button" class="btn btn-outline btn-md" data-role="cancel">ยกเลิก</button>
            <button type="button" class="btn btn-primary btn-md" data-role="save">บันทึกรหัสผ่านใหม่</button>
          </div>
        `;
        card.querySelector('[data-role="cancel"]').addEventListener('click', () => close());
        card.querySelector('[data-role="save"]').addEventListener('click', async () => {
          const err = card.querySelector('[data-role="err"]');
          try {
            await api.post(`/api/admin/users/${u.id}/reset-password`, {
              temp_password: card.querySelector('[data-role="pw1"]').value,
              confirm_password: card.querySelector('[data-role="pw2"]').value,
            });
            close();
            await showMessage('เปลี่ยนรหัสผ่านสำเร็จ', `ตั้งรหัสผ่านใหม่ให้ @${u.username} เรียบร้อยแล้ว`, 'success');
            await load();
          } catch (ex) {
            err.textContent = ex.message || '';
          }
        });
      },
    });
  }

  async function openUserDetailModal(uid, router) {
    let detail = null;
    try {
      detail = await api.get(`/api/admin/users/${uid}`);
    } catch (err) {
      const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
      return;
    }
    const usr = detail.user || {};
    const addrs = detail.addresses || [];
    const orders = detail.orders || [];
    const stats = detail.stats || {};
    const stLabel = !usr.is_active ? 'ถูกระงับ' : (usr.is_online ? 'ออนไลน์' : 'ออฟไลน์');

    openModal({
      title: `ข้อมูลบัญชีผู้ใช้: ${usr.full_name} (@${usr.username})`,
      width: 680,
      render(card, close) {
        card.style.padding = '0';
        card.style.overflow = 'hidden';
        card.innerHTML = `
          <div style="background:var(--color-secondary);padding:14px 20px;display:flex;align-items:center;gap:12px">
            ${thumbHtml(usr.avatar_path, 52)}
            <div style="flex:1">
              <div class="text-h2 text-primary">${esc(usr.full_name || '-')}  (@${esc(usr.username || '-')})</div>
              <div class="text-small-bold" style="color:#FFFFFF">บทบาท: ${esc(usr.role_label || usr.role)}  ·  สถานะ: ${esc(stLabel)}</div>
            </div>
          </div>
          <div style="padding:14px 18px;max-height:460px;overflow-y:auto;display:flex;flex-direction:column;gap:10px">
            <div class="card" style="padding:12px 16px">
              <div class="text-h3" style="margin-bottom:6px">ข้อมูลโปรไฟล์และสถิติบัญชี (ไม่แสดงรหัสผ่าน)</div>
              <div style="display:grid;grid-template-columns:180px 1fr;gap:4px">
                <span class="text-small-bold text-muted">รหัสผู้ใช้ (User ID)</span><span class="text-body-bold">#${usr.id}</span>
                <span class="text-small-bold text-muted">ชื่อ-นามสกุล</span><span class="text-body-bold">${esc(usr.full_name || '-')}</span>
                <span class="text-small-bold text-muted">ชื่อผู้ใช้ (Username)</span><span class="text-body-bold">@${esc(usr.username || '-')}</span>
                <span class="text-small-bold text-muted">อีเมล</span><span class="text-body-bold">${esc(usr.email || '-')} (${usr.email_verified ? 'ยืนยันอีเมลแล้ว' : 'ยังไม่ยืนยัน'})</span>
                <span class="text-small-bold text-muted">เบอร์โทรศัพท์</span><span class="text-body-bold">${esc(formatPhone(usr.phone))}</span>
                <span class="text-small-bold text-muted">วันที่สมัครสมาชิก</span><span class="text-body-bold">${esc(formatDateTime(usr.created_at))}</span>
                <span class="text-small-bold text-muted">จำนวนคำสั่งซื้อทั้งหมด</span><span class="text-body-bold">${Number(stats.total_orders || 0).toLocaleString()} รายการ (ชำระแล้ว ${Number(stats.paid_orders || 0).toLocaleString()} รายการ)</span>
                <span class="text-small-bold text-muted">ยอดซื้อสะสมรวม</span><span class="text-body-bold">${esc(formatPrice(stats.total_spent || 0))}</span>
                <span class="text-small-bold text-muted">เซสชันที่ล็อกอินอยู่</span><span class="text-body-bold">${stats.active_sessions || 0} เครื่อง</span>
              </div>
            </div>

            <div class="card" style="padding:12px 16px">
              <div class="text-h3" style="margin-bottom:6px">ที่อยู่จัดส่งที่บันทึกไว้ (${addrs.length} ที่อยู่)</div>
              ${!addrs.length ? `<div class="text-small text-muted">ยังไม่มีที่อยู่จัดส่งที่บันทึกไว้</div>` : addrs.map((ad) => `
                <div class="card-alt" style="padding:6px 10px;margin-bottom:4px" class="text-small">
                  <strong>${esc(ad.recipient)}</strong> (${esc(formatPhone(ad.phone))})${ad.is_default ? ' [ค่าเริ่มต้น]' : ''}<br/>
                  ${esc(`${ad.address_line || ''} ${ad.district || ''} ${ad.province || ''} ${ad.postcode || ''}`.trim())}
                </div>
              `).join('')}
            </div>

            <div class="card" style="padding:12px 16px">
              <div class="text-h3" style="margin-bottom:6px">ประวัติคำสั่งซื้อล่าสุด (${orders.length} รายการ)</div>
              ${!orders.length ? `<div class="text-small text-muted">ยังไม่มีประวัติคำสั่งซื้อ</div>` : orders.map((od) => `
                <div class="card-alt" style="padding:6px 10px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center">
                  <span class="text-small-bold">ออเดอร์ #${od.id}  ·  ${esc(formatDateTime(od.created_at))}  ·  ยอด ${esc(formatPrice(od.total))}  (${esc(od.status_label || od.status)})</span>
                  <button type="button" class="btn btn-outline btn-sm" data-open-ord="${od.id}">ดูออเดอร์ ›</button>
                </div>
              `).join('')}
            </div>
          </div>
          <div style="padding:10px 18px;display:flex;justify-content:center">
            <button type="button" class="btn btn-outline btn-sm" data-role="close" style="min-width:130px">ปิดหน้าต่าง</button>
          </div>
        `;
        card.querySelectorAll('[data-open-ord]').forEach((b) => {
          b.addEventListener('click', () => {
            close();
            router.show('admin_order_detail', { order_id: Number(b.dataset.openOrd) });
          });
        });
        card.querySelector('[data-role="close"]').addEventListener('click', () => close());
      },
    });
  }

  await load();
}
