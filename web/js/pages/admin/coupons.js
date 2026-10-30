// web/js/pages/admin/coupons.js — จัดการคูปองส่วนลด & กฎซื้อครบรับคูปองอัตโนมัติ (ตรงกับ ui/pages/admin/coupons.py)
import { api, esc, formatDateThai, formatPrice } from '../../api.js';
import { createSegmented, parseIntField, parseMoney, pillHtml } from '../../components/admin_common.js';
import { confirm, showMessage, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';
import { createSearchBar } from '../../components/search_bar.js';

const TAB_COUPONS = 'คูปองส่วนลดทั้งหมด';
const TAB_RULES = 'กฎซื้อครบรับคูปองอัตโนมัติ (ออเดอร์ถัดไป)';
const STATUS_LABELS = { active: 'ใช้งานได้', inactive: 'ปิดอยู่', expired: 'หมดอายุ', full: 'ครบสิทธิ์' };
const STATUS_KINDS = { active: 'success', inactive: 'muted', expired: 'danger', full: 'warning' };

function couponStatus(c) {
  if (!c.is_active) return 'inactive';
  if (c.is_expired) return 'expired';
  if (c.remaining != null && c.remaining <= 0) return 'full';
  return 'active';
}

function discountText(c) {
  const val = c.value || 0;
  if (c.is_free_shipping) return `ส่งฟรี (สูงสุด ${formatPrice(val)})`;
  if (c.discount_type === 'percent') return `${val}%`;
  return formatPrice(val);
}

function scheduleSummaryText(c) {
  const parts = [];
  parts.push(c.expires_at ? formatDateThai(c.expires_at) : 'ไม่มีวันหมดอายุ');
  if (c.claim_start_time && c.claim_end_time) {
    parts.push(`รับได้ ${c.claim_start_time}-${c.claim_end_time} (${c.repeat_daily ? 'ทุกวัน' : 'ตามวันที่'})`);
  }
  if (c.daily_reset_12) parts.push('รีโค้ดทุก 12:00 น.');
  return parts.join('\n');
}

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let mode = TAB_COUPONS;
  let search = '';
  let statusFilter = '';
  let allCoupons = [];
  let allRules = [];
  let editRuleId = null;

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">คูปองส่วนลด & กฎแจกคูปองอัตโนมัติ</div>
        <div class="text-small text-muted">กำหนดเงื่อนไขคูปอง โค้ดส่งฟรี ตั้งเวลารับโค้ด และรีโค้ดอัตโนมัติเวลา 12:00 น. — เฉพาะเจ้าของร้าน</div>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button type="button" class="btn btn-outline btn-md" data-role="refresh">รีเฟรช</button>
        <button type="button" class="btn btn-info btn-md" data-role="quick-freeship">＋ สร้างโค้ดส่งฟรีด่วน</button>
        <button type="button" class="btn btn-primary btn-md" data-role="add-coupon">＋ เพิ่มคูปองใหม่</button>
      </div>
    </div>

    <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:4px"></div>
    <div data-role="mode-slot" style="margin-bottom:8px"></div>
    <div data-role="holder"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const holder = wrap.querySelector('[data-role="holder"]');

  const modeSeg = createSegmented([TAB_COUPONS, TAB_RULES], mode, (val) => {
    mode = val;
    load();
  });
  wrap.querySelector('[data-role="mode-slot"]').appendChild(modeSeg.el);

  wrap.querySelector('[data-role="refresh"]').addEventListener('click', () => load());
  wrap.querySelector('[data-role="add-coupon"]').addEventListener('click', () => router.show('admin_coupon_form'));
  wrap.querySelector('[data-role="quick-freeship"]').addEventListener('click', async () => {
    errEl.textContent = '';
    try {
      let code = 'FREESHIP';
      const existing = allCoupons.filter((c) => String(c.code || '').toUpperCase().startsWith('FREESHIP'));
      if (existing.length) code = `FREESHIP${existing.length + 1}`;
      const created = await api.post('/api/admin/coupons', {
        code,
        discount_type: 'free_shipping',
        value: 50,
        min_order: 0,
        is_free_shipping: true,
        daily_reset_12: true,
        code_prefix: 'FREESHIP',
        claimable: true,
        is_active: true,
      });
      await showMessage(
        'สร้างโค้ดส่งฟรีแล้ว',
        `สร้างโค้ดส่งฟรี “${created.code}” (ลดค่าจัดส่งสูงสุด 50 บาท · รีเซ็ตให้กดรับใหม่ทุก 12:00 น.) เรียบร้อยแล้ว`,
        'success'
      );
      await load();
    } catch (err) {
      const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
    }
  });

  async function load() {
    errEl.textContent = '';
    try {
      const res = await api.get('/api/admin/coupons');
      allCoupons = res.coupons || [];
      allRules = res.rules || [];
    } catch (err) {
      errEl.textContent = err.message || 'โหลดคูปองไม่สำเร็จ';
      return;
    }
    if (mode === TAB_COUPONS) {
      renderCouponsView();
    } else {
      renderRulesView();
    }
  }

  function renderCouponsView() {
    holder.innerHTML = `
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
        <div data-role="search-slot"></div>
        <select class="select" data-role="status" style="width:160px;height:36px">
          <option value="">ทุกสถานะ</option>
          ${Object.entries(STATUS_LABELS).map(([k, lbl]) => `<option value="${k}" ${k === statusFilter ? 'selected' : ''}>${esc(lbl)}</option>`).join('')}
        </select>
      </div>
      <div class="admin-table-header" style="grid-template-columns:1.2fr 1.3fr 1fr 1fr 1.5fr 100px 195px">
        <span>โค้ด</span><span>ส่วนลด / เงื่อนไข</span><span>ขั้นต่ำที่ใช้</span><span>ใช้แล้ว</span><span>วันหมดอายุ / ช่วงเวลารับ</span><span>สถานะ</span><span>จัดการ</span>
      </div>
      <div data-role="list"></div>
    `;

    const searchBar = createSearchBar({
      placeholder: 'ค้นหาโค้ดคูปอง',
      width: 240,
      enableSuggestions: false,
      onSubmit(q) {
        search = (q || '').trim().toUpperCase();
        paintRows();
      },
    });
    searchBar.set(search);
    holder.querySelector('[data-role="search-slot"]').appendChild(searchBar.el);

    const statusSel = holder.querySelector('[data-role="status"]');
    statusSel.addEventListener('change', () => {
      statusFilter = statusSel.value;
      paintRows();
    });

    const listEl = holder.querySelector('[data-role="list"]');
    function paintRows() {
      listEl.innerHTML = '';
      const shown = allCoupons.filter((c) => {
        const matchQ = !search || String(c.code || '').toUpperCase().includes(search);
        const matchSt = !statusFilter || couponStatus(c) === statusFilter;
        return matchQ && matchSt;
      });
      if (!shown.length) {
        listEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">${allCoupons.length ? 'ไม่พบคูปองตามเงื่อนไขที่เลือก' : 'ยังไม่มีคูปอง'}</div>`;
        return;
      }
      for (const c of shown) {
        const st = couponStatus(c);
        const used = Number(c.used_count || 0);
        const isActive = Boolean(c.is_active);
        const r = document.createElement('div');
        r.className = 'admin-table-row';
        r.style.gridTemplateColumns = '1.2fr 1.3fr 1fr 1fr 1.5fr 100px 195px';
        r.innerHTML = `
          <div class="text-body-bold">${esc(c.code)}</div>
          <div class="text-body">${esc(discountText(c))}</div>
          <div class="text-small text-muted">${c.min_order ? esc(formatPrice(c.min_order)) : 'ไม่มี'}</div>
          <div class="text-small text-muted">${c.max_uses ? `${used} / ${c.max_uses}` : `${used} / ไม่จำกัด`}</div>
          <div class="text-tiny text-muted" style="white-space:pre-line">${esc(scheduleSummaryText(c))}</div>
          <div>${pillHtml(STATUS_LABELS[st], STATUS_KINDS[st])}</div>
          <div style="display:flex;justify-content:flex-end;gap:4px">
            <button type="button" class="btn btn-outline btn-sm" data-role="edit">แก้ไข</button>
            <button type="button" class="btn ${isActive ? 'btn-outline' : 'btn-success'} btn-sm" data-role="tog">${isActive ? 'ปิด' : 'เปิด'}</button>
            <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
          </div>
        `;
        r.querySelector('[data-role="edit"]').addEventListener('click', () => router.show('admin_coupon_form', { coupon_id: c.id }));
        r.querySelector('[data-role="tog"]').addEventListener('click', async () => {
          await api.post(`/api/admin/coupons/${c.id}/toggle`, { active: !isActive });
          await load();
        });
        r.querySelector('[data-role="del"]').addEventListener('click', async () => {
          const ok = await confirm('ยืนยันการลบคูปอง', `ต้องการลบคูปอง “${c.code}” ออกจากระบบใช่หรือไม่?
(ประวัติออเดอร์เดิมที่เคยใช้คูปองนี้จะยังคงอยู่ครบถ้วน)`, { confirmText: 'ลบคูปอง', danger: true });
          if (!ok) return;
          await api.del(`/api/admin/coupons/${c.id}`);
          await load();
        });
        listEl.appendChild(r);
      }
    }
    paintRows();
  }

  function renderRulesView() {
    const curRule = allRules.find((r) => r.id === editRuleId) || null;
    holder.innerHTML = `
      <div class="card" style="padding:14px 16px;margin-bottom:10px">
        <div class="text-h3" style="margin-bottom:8px">${curRule ? `แก้ไขกฎแจกคูปอง #${curRule.id}: ${esc(curRule.name)}` : 'เพิ่มกฎซื้อครบรับคูปองอัตโนมัติ (สำหรับใช้ออเดอร์ถัดไป)'}</div>
        <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:10px">
          <div>
            <div class="text-small text-muted">ชื่อแคมเปญ *</div>
            <input type="text" class="input" data-r="name" value="${esc((curRule && curRule.name) || '')}" placeholder="เช่น ซื้อครบ 3,000 รับส่วนลด 10%" />
          </div>
          <div>
            <div class="text-small text-muted">ยอดซื้อขั้นต่ำเพื่อรับคูปอง (บาท) *</div>
            <input type="text" class="input" data-r="trigger" value="${curRule ? curRule.min_order_trigger : ''}" placeholder="3000" />
          </div>
          <div>
            <div class="text-small text-muted">คำนำหน้าโค้ดคูปอง *</div>
            <input type="text" class="input" data-r="prefix" value="${esc((curRule && curRule.code_prefix) || 'NEXT')}" placeholder="NEXT" />
          </div>
          <div>
            <div class="text-small text-muted">ประเภทส่วนลด *</div>
            <select class="select" data-r="type">
              <option value="percent" ${(!curRule || curRule.discount_type === 'percent') ? 'selected' : ''}>percent</option>
              <option value="fixed" ${(curRule && curRule.discount_type === 'fixed') ? 'selected' : ''}>fixed</option>
            </select>
          </div>
          <div>
            <div class="text-small text-muted">มูลค่าส่วนลด (% หรือ บาท) *</div>
            <input type="text" class="input" data-r="val" value="${curRule ? curRule.discount_value : ''}" placeholder="10" />
          </div>
          <div>
            <div class="text-small text-muted">ยอดขั้นต่ำเพื่อใช้ในออเดอร์ถัดไป (บาท)</div>
            <input type="text" class="input" data-r="next_min" value="${curRule ? curRule.min_order_next : '0'}" placeholder="1000" />
          </div>
          <div>
            <div class="text-small text-muted">อายุคูปอง (วัน)</div>
            <input type="text" class="input" data-r="days" value="${curRule ? curRule.valid_days : '30'}" placeholder="30" />
          </div>
          <div style="display:flex;align-items:flex-end;padding-bottom:8px">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer" class="text-body">
              <input type="checkbox" data-r="active" ${(!curRule || curRule.is_active) ? 'checked' : ''} />
              <span>เปิดใช้งานกฎนี้</span>
            </label>
          </div>
        </div>
        <div style="display:flex;gap:8px;margin-top:10px">
          <button type="button" class="btn btn-primary btn-md" data-role="save-rule">บันทึกกฎแจกคูปอง</button>
          <button type="button" class="btn btn-outline btn-md" data-role="reset-rule">ล้างฟอร์ม</button>
        </div>
      </div>
      <div data-role="rules-list" style="display:flex;flex-direction:column;gap:6px"></div>
    `;

    holder.querySelector('[data-role="save-rule"]').addEventListener('click', async () => {
      errEl.textContent = '';
      try {
        const getR = (k) => holder.querySelector(`[data-r="${k}"]`).value.trim();
        const payload = {
          rule_id: editRuleId,
          name: getR('name'),
          min_order_trigger: parseMoney(getR('trigger'), 'ยอดซื้อขั้นต่ำเพื่อรับคูปอง', { required: true, minimum: 0 }),
          code_prefix: getR('prefix').toUpperCase() || 'NEXT',
          discount_type: getR('type'),
          discount_value: parseMoney(getR('val'), 'มูลค่าส่วนลด', { required: true, minimum: 0 }),
          min_order_next: parseMoney(getR('next_min'), 'ยอดขั้นต่ำออเดอร์ถัดไป', { required: false, minimum: 0 }) || 0,
          valid_days: parseIntField(getR('days'), 'อายุคูปอง', { required: false, minimum: 1 }) || 30,
          is_active: holder.querySelector('[data-r="active"]').checked,
        };
        await api.post('/api/admin/coupon-rules', payload);
        editRuleId = null;
        await load();
      } catch (err) {
        const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
      }
    });

    holder.querySelector('[data-role="reset-rule"]').addEventListener('click', () => {
      editRuleId = null;
      renderRulesView();
    });

    const rList = holder.querySelector('[data-role="rules-list"]');
    if (!allRules.length) {
      rList.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">ยังไม่มีกฎซื้อครบรับคูปองอัตโนมัติ</div>`;
      return;
    }
    for (const r of allRules) {
      const active = Boolean(r.is_active ?? 1);
      const disc = r.discount_type === 'percent' ? `${r.discount_value}%` : formatPrice(r.discount_value);
      const card = document.createElement('div');
      card.className = 'card';
      card.style.padding = '10px 14px';
      card.style.display = 'flex';
      card.style.alignItems = 'center';
      card.style.gap = '10px';
      card.innerHTML = `
        <div style="flex:1">
          <div class="text-body-bold">${esc(r.name)}</div>
          <div class="text-small text-muted">เมื่อซื้อครบ ${esc(formatPrice(r.min_order_trigger))} → แจกโค้ด ${esc(r.code_prefix)}-XXXX ลด ${esc(disc)} (ขั้นต่ำครั้งถัดไป ${esc(formatPrice(r.min_order_next))}, อายุ ${r.valid_days} วัน)</div>
        </div>
        ${pillHtml(active ? 'เปิดใช้งาน' : 'ปิดอยู่', active ? 'success' : 'muted')}
        <button type="button" class="btn btn-outline btn-sm" data-role="edit">แก้ไข</button>
        <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
      `;
      card.querySelector('[data-role="edit"]').addEventListener('click', () => {
        editRuleId = r.id;
        renderRulesView();
      });
      card.querySelector('[data-role="del"]').addEventListener('click', async () => {
        const ok = await confirm('ลบกฎแจกคูปอง', 'ต้องการลบกฎแจกคูปองอัตโนมัตินี้ใช่หรือไม่?', { danger: true });
        if (!ok) return;
        await api.del(`/api/admin/coupon-rules/${r.id}`);
        await load();
      });
      rList.appendChild(card);
    }
  }

  await load();
}
