// web/js/pages/buyer/notifications.js — หน้าการแจ้งเตือน (พรีวิวรายละเอียด, กดเปิดหน้าที่เกี่ยวข้อง, อ่านทั้งหมด)
import { api, esc, formatDateTime } from '../../api.js';
import { state } from '../../state.js';
import { pageTitleHtml } from '../../components/buyer_common.js';
import { iconSvg } from '../../components/icons.js';

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  let expandedId = null;

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      ${pageTitleHtml('การแจ้งเตือน', 'คลิกที่รายการเพื่อดูรายละเอียดคร่าวๆ หรือกดเปิดหน้าที่เกี่ยวข้อง (เก็บ 10 รายการล่าสุดสำหรับผู้ซื้อ)')}
      <button type="button" class="btn btn-outline btn-sm" data-role="read-all">อ่านทั้งหมด</button>
    </div>
    <div class="text-small text-danger" data-role="msg"></div>
    <div data-role="list" style="display:flex;flex-direction:column;gap:8px;margin-top:8px"></div>
  `;

  const readAllBtn = wrap.querySelector('[data-role="read-all"]');
  const msgEl = wrap.querySelector('[data-role="msg"]');
  const listEl = wrap.querySelector('[data-role="list"]');

  async function load() {
    listEl.innerHTML = '';
    try {
      const res = await api.get('/api/notifications', { limit: 100 });
      const items = res.items || [];
      const unread = items.filter((n) => !n.is_read).length;
      readAllBtn.disabled = unread === 0;

      if (!items.length) {
        listEl.innerHTML = `<div class="text-body-bold text-muted" style="text-align:center;padding:60px 20px">ยังไม่มีการแจ้งเตือน</div>`;
        return;
      }

      if (state.role === 'buyer') {
        const cap = document.createElement('div');
        cap.className = 'text-tiny text-muted';
        cap.textContent = `แสดงการแจ้งเตือน ${items.length} รายการล่าสุด (ระบบเก็บสูงสุด 10 ครั้งล่าสุดสำหรับบัญชีผู้ซื้อ)`;
        listEl.appendChild(cap);
      }

      for (const item of items) {
        const isUnread = !item.is_read;
        const isExp = expandedId === item.id;
        const card = document.createElement('div');
        card.className = 'card';
        card.style.border = isUnread ? '2px solid var(--color-primary)' : (isExp ? '2px solid var(--color-info)' : '1px solid var(--color-border)');
        card.style.padding = '12px 16px';
        card.style.cursor = 'pointer';

        card.innerHTML = `
          <div style="display:grid;grid-template-columns:28px 1fr auto;gap:10px;align-items:center">
            <div>${iconSvg('bell', 18, isUnread ? '#FFB703' : '#64748B')}</div>
            <div>
              <div class="${isUnread ? 'text-body-bold' : 'text-body'}">${esc(item.title)}${isUnread ? '  [ใหม่]' : ''}</div>
              ${item.message ? `<div class="text-small text-muted" style="margin-top:2px">${esc(item.message)}</div>` : ''}
              <div class="text-tiny text-muted" style="margin-top:4px">${esc(formatDateTime(item.created_at))}  ·  คลิกเพื่อดูแบบคร่าวๆ</div>
            </div>
            <button type="button" class="btn ${isUnread ? 'btn-primary' : 'btn-outline'} btn-sm" data-role="open-target">${esc(item.action_label || 'เปิดดู ›')}</button>
          </div>
          ${isExp ? `
            <div class="card-alt" style="margin-top:10px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;gap:12px">
              <div class="text-small" style="white-space:pre-line">พรีวิวรายละเอียด: ${esc(item.title)}
${esc(item.message || '-')}
เวลาแจ้งเตือน: ${esc(formatDateTime(item.created_at))}</div>
              <button type="button" class="btn btn-danger btn-sm" data-role="preview-go">${esc(item.action_label || 'ไปยังหน้านี้ ›')}</button>
            </div>
          ` : ''}
        `;

        const openTarget = async (e) => {
          e.stopPropagation();
          if (!item.is_read) {
            try { await api.post(`/api/notifications/${item.id}/read`); await router.refresh_shell(); } catch (ex) {}
          }
          const route = item.target_route || 'orders';
          const params = item.target_params || {};
          router.show(route, typeof params === 'object' ? params : {});
        };

        card.querySelector('[data-role="open-target"]').addEventListener('click', openTarget);
        const pGo = card.querySelector('[data-role="preview-go"]');
        if (pGo) pGo.addEventListener('click', openTarget);

        card.addEventListener('click', async () => {
          if (!item.is_read) {
            try { await api.post(`/api/notifications/${item.id}/read`); await router.refresh_shell(); } catch (ex) {}
          }
          expandedId = expandedId === item.id ? null : item.id;
          await load();
        });

        listEl.appendChild(card);
      }
    } catch (err) {
      msgEl.textContent = `⛔ ${err.message}`;
    }
  }

  readAllBtn.addEventListener('click', async () => {
    try {
      await api.post('/api/notifications/read-all');
      await router.refresh_shell();
      await load();
    } catch (err) {
      msgEl.textContent = `⛔ ${err.message}`;
    }
  });

  await load();
}
