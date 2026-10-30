// web/js/pages/admin/orders.js — รายการออเดอร์ทั้งหมดฝั่งแอดมิน/เจ้าของ (ตรงกับ ui/pages/admin/orders.py)
import { api, esc, formatDateTime, formatPrice, ORDER_STATUS_DISPLAY_ORDER, ORDER_STATUS_LABELS } from '../../api.js';
import { createPager, pillHtml } from '../../components/admin_common.js';
import { createSearchBar } from '../../components/search_bar.js';

const PAGE_SIZE = 15;

export async function render(container, router, params = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let page = 1;
  let search = '';
  let statusFilter = params.status || '';

  const statusOptions = ORDER_STATUS_DISPLAY_ORDER.filter(([k]) => k && k !== 'all');

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">จัดการคำสั่งซื้อ (Orders)</div>
        <div class="text-small text-muted">รายการสั่งซื้อทั้งหมดตามลำดับสถานะ</div>
      </div>
      <button type="button" class="btn btn-outline btn-sm" data-role="refresh">🔄 รีเฟรช</button>
    </div>

    <div class="text-small text-danger" data-role="err"></div>

    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
      <div data-role="search-slot"></div>
      <select class="select" data-role="status" style="width:190px;height:36px">
        <option value="">การสั่งซื้อ (ทั้งหมด)</option>
        ${statusOptions.map(([k, lbl]) => `<option value="${esc(k)}" ${k === statusFilter ? 'selected' : ''}>${esc(lbl)}</option>`).join('')}
      </select>
    </div>

    <div class="admin-table-header" style="grid-template-columns:90px 2fr 1.3fr 1fr 130px 115px">
      <span>เลขที่</span><span>ผู้ซื้อ</span><span>วันที่สั่ง</span><span>ยอดรวม</span><span>สถานะ</span><span></span>
    </div>
    <div data-role="list"></div>
    <div data-role="pager-slot"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const statusSel = wrap.querySelector('[data-role="status"]');
  const listEl = wrap.querySelector('[data-role="list"]');
  const pager = createPager((p) => { page = p; load(); });
  wrap.querySelector('[data-role="pager-slot"]').appendChild(pager.el);

  const searchBar = createSearchBar({
    placeholder: 'ค้นหาเลขออเดอร์ / ชื่อผู้ซื้อ',
    width: 280,
    enableSuggestions: false,
    onSubmit(q) {
      search = q;
      page = 1;
      load();
    },
  });
  wrap.querySelector('[data-role="search-slot"]').appendChild(searchBar.el);

  statusSel.addEventListener('change', () => {
    statusFilter = statusSel.value;
    page = 1;
    load();
  });
  wrap.querySelector('[data-role="refresh"]').addEventListener('click', () => { page = 1; load(); });

  async function load() {
    errEl.textContent = '';
    listEl.innerHTML = '';
    try {
      const res = await api.get('/api/admin/orders', {
        status: statusFilter || undefined,
        search: search || undefined,
        page,
        page_size: PAGE_SIZE,
      });
      const items = res.items || [];
      if (!items.length) {
        listEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">ไม่พบออเดอร์ตามเงื่อนไขที่เลือก</div>`;
      }
      for (const o of items) {
        const st = o.status;
        const stLbl = ORDER_STATUS_LABELS[st] || st;
        const stKind = st === 'completed' || st === 'paid' ? 'success' : (st === 'cancelled' ? 'danger' : 'warning');

        const r = document.createElement('div');
        r.className = 'admin-table-row';
        r.style.gridTemplateColumns = '90px 2fr 1.3fr 1fr 130px 115px';
        r.innerHTML = `
          <div class="text-body-bold">#${o.id}</div>
          <div>
            <div class="text-body">${esc(o.buyer_name || o.recipient_name || '-')}</div>
            <div class="text-tiny text-muted">${Number(o.item_count || 0)} ชิ้น · @${esc(o.buyer_username || '-')}</div>
          </div>
          <div class="text-small text-muted">${esc(formatDateTime(o.created_at))}</div>
          <div class="text-body-bold">${esc(formatPrice(o.total))}</div>
          <div>${pillHtml(stLbl, stKind)}</div>
          <div style="display:flex;justify-content:flex-end">
            <button type="button" class="btn btn-outline btn-sm">ดูรายละเอียด</button>
          </div>
        `;
        r.querySelector('button').addEventListener('click', () => router.show('admin_order_detail', { order_id: o.id }));
        listEl.appendChild(r);
      }
      pager.set(res.page || 1, res.pages || 1, res.total);
    } catch (err) {
      errEl.textContent = err.message || 'โหลดรายการออเดอร์ไม่สำเร็จ';
    }
  }

  await load();
}
