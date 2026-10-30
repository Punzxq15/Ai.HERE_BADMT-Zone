// web/js/pages/buyer/compare.py -> compare.js — หน้าเปรียบเทียบไม้แบดมินตัน 2–5 รุ่น (ตรงกับ ui/pages/buyer/compare.py)
import { api, esc, formatPrice, resolveAssetUrl } from '../../api.js';
import { createRatingStars } from '../../components/rating.js';
import { pageTitleHtml } from '../../components/buyer_common.js';
import { showToast } from '../../components/dialogs.js';

const MIN_COMPARE = 2;
const MAX_COMPARE = 5;
const EMPTY = '— เลือกไม้แบดมินตัน —';

const ROWS = [
  ['ราคาขายสุทธิ',       'price'],
  ['Material',           'spec_material'],
  ['Weight Class / Grip','weight_grip_display'],
  ['Balance Point',      'balance_point_display'],
  ['Shaft Flexibility',  'flex'],
  ['Max String Tension', 'spec_max_tension'],
  ['Length',             'spec_length'],
  ['Skill Level',        'level'],
  ['คะแนนรีวิว',          'rating'],
  ['สถานะสต็อก',         'stock'],
];

export async function render(container, router, params = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  wrap.innerHTML = `
    ${pageTitleHtml(`⚖️ เปรียบเทียบไม้แบดมินตัน (${MIN_COMPARE}–${MAX_COMPARE} รุ่น)`, `เลือกไม้แบดมินตันตั้งแต่ ${MIN_COMPARE} ถึง ${MAX_COMPARE} รุ่นเพื่อเปรียบเทียบ Technical Specifications และราคาแบบเคียงข้างกัน`)}
    <div class="card" style="padding:14px 16px;margin-bottom:14px">
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px" data-role="slots-grid"></div>
      <div style="display:flex;align-items:center;gap:8px;margin-top:12px;flex-wrap:wrap">
        <button type="button" class="btn btn-primary btn-md" data-role="cmp-btn">⚖️ เปรียบเทียบสเปกทันที</button>
        <button type="button" class="btn btn-outline btn-md" data-role="clr-btn">ล้างการเลือกทั้งหมด</button>
        <span class="text-small text-danger" data-role="err"></span>
      </div>
    </div>
    <div data-role="result-box"></div>
  `;

  const slotsGrid = wrap.querySelector('[data-role="slots-grid"]');
  const errEl = wrap.querySelector('[data-role="err"]');
  const resultBox = wrap.querySelector('[data-role="result-box"]');

  let racketItems = [];
  try {
    const res = await api.get('/api/products', { sort: 'name', page_size: 60 });
    racketItems = (res.items || []).filter((it) => it.is_racket);
  } catch (err) {
    errEl.textContent = err.message || '';
  }

  const selects = [];
  for (let i = 0; i < MAX_COMPARE; i++) {
    const cell = document.createElement('div');
    cell.innerHTML = `
      <div class="text-small-bold ${i < 2 ? 'text-danger' : 'text-muted'}" style="margin-bottom:2px">ไม้รุ่นที่ ${i + 1}${i < 2 ? ' (บังคับ)' : ' (เพิ่มเติม)'}</div>
      <select class="select">
        <option value="">${EMPTY}</option>
        ${racketItems.map((it) => `<option value="${it.id}">${esc(`${it.brand_name || ''} ${it.name}`.trim())}</option>`).join('')}
      </select>
    `;
    const sel = cell.querySelector('select');
    selects.push(sel);
    slotsGrid.appendChild(cell);
  }

  // Pre-populate from params.ids
  const rawIds = Array.isArray(params.ids)
    ? params.ids
    : String(params.ids || '').split(',').filter(Boolean);
  rawIds.forEach((idVal, idx) => {
    if (idx < selects.length) selects[idx].value = String(idVal);
  });

  function showHint() {
    resultBox.innerHTML = `<div class="text-body-bold text-muted" style="text-align:center;padding:40px 16px">เลือกไม้แบดมินตันอย่างน้อย ${MIN_COMPARE} รุ่น (สูงสุด ${MAX_COMPARE} รุ่น) แล้วกด "เปรียบเทียบสเปกทันที"</div>`;
  }

  async function doCompare() {
    const ids = [];
    for (const sel of selects) {
      const v = sel.value ? Number(sel.value) : null;
      if (v && !ids.includes(v)) ids.push(v);
    }
    errEl.textContent = '';
    try {
      const products = await api.get('/api/products/compare', { ids: ids.join(',') });
      renderTable(products);
    } catch (err) {
      const _em = err.message || 'เปรียบเทียบไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
      resultBox.innerHTML = '';
    }
  }

  function renderTable(products = []) {
    resultBox.innerHTML = '';
    const outer = document.createElement('div');
    outer.className = 'card';
    outer.style.overflowX = 'auto';

    const prices = products.map((p) => Number(p.effective_price));
    const cheapest = new Set(prices).size > 1 ? Math.min(...prices) : null;

    const cols = products.length;
    const gridStyle = `display:grid;grid-template-columns:190px repeat(${cols}, minmax(215px, 1fr));`;

    let html = `
      <div style="${gridStyle};border-bottom:1px solid var(--color-border)">
        <div style="background:var(--color-secondary);color:var(--color-primary);padding:16px 12px;display:flex;align-items:center;justify-content:center" class="text-body-bold">Technical Specs / รุ่นไม้</div>
        ${products.map((p) => `
          <div style="padding:14px 10px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:4px">
            <img src="${esc(resolveAssetUrl(p.image_path))}" alt="${esc(p.name)}" style="width:130px;height:130px;object-fit:contain;border-radius:8px;background:var(--color-surface-alt)" />
            <div class="text-tiny text-info">${esc(String(p.brand_name || '').toUpperCase())}</div>
            <div class="text-body-bold">${esc(p.name)}</div>
            <button type="button" class="btn btn-primary btn-sm" data-open="${p.id}" style="margin-top:4px">ดูรายละเอียด ›</button>
          </div>
        `).join('')}
      </div>
    `;

    ROWS.forEach(([label, key], idx) => {
      const bg = idx % 2 === 0 ? 'var(--color-surface-alt)' : 'var(--color-surface)';
      html += `<div style="${gridStyle};background:${bg}">`;
      html += `<div class="text-small-bold" style="padding:10px 14px;display:flex;align-items:center">${esc(label)}</div>`;
      for (const p of products) {
        let cellHtml = '';
        if (key === 'price') {
          const best = cheapest !== null && Number(p.effective_price) === cheapest;
          const pColor = p.is_on_sale ? 'text-danger' : (best ? 'text-success' : 'text-main');
          cellHtml = `
            <div class="text-price ${pColor}">${esc(formatPrice(p.effective_price))}</div>
            ${best ? `<span class="pill pill-success" style="margin-top:2px">★ คุ้มค่าที่สุด</span>` : ''}
            ${p.is_on_sale ? `<div class="text-tiny text-muted">ปกติ ${esc(formatPrice(p.price))}</div>` : ''}
          `;
        } else if (key === 'rating') {
          cellHtml = `<div data-rating-for="${p.id}"></div>`;
        } else if (key === 'stock') {
          const ok = Boolean(p.in_stock);
          cellHtml = `<span class="text-small-bold ${ok ? 'text-success' : 'text-danger'}">${ok ? '✓ พร้อมส่ง' : '⛔ สินค้าหมด'}</span>`;
        } else if (key === 'weight_grip_display') {
          cellHtml = `<span class="text-body-bold">${esc(p.spec_weight_grip || p.weight_class || '-')}</span>`;
        } else if (key === 'balance_point_display') {
          const mm = p.spec_balance_mm ? `${p.spec_balance_mm} mm` : '';
          const btype = p.spec_balance_type || p.balance || '';
          const disp = mm && btype ? `${mm} (${btype})` : (mm || btype || '-');
          cellHtml = `<span class="text-body-bold">${esc(disp)}</span>`;
        } else {
          cellHtml = `<span class="text-body-bold">${esc(p[key] || '-')}</span>`;
        }
        html += `<div style="padding:10px 8px;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center">${cellHtml}</div>`;
      }
      html += `</div>`;
    });

    outer.innerHTML = html;
    outer.querySelectorAll('[data-open]').forEach((btn) => {
      btn.addEventListener('click', () => router.show('product_detail', { product_id: Number(btn.dataset.open) }));
    });
    for (const p of products) {
      const slot = outer.querySelector(`[data-rating-for="${p.id}"]`);
      if (slot) {
        slot.appendChild(createRatingStars({ value: p.avg_rating || 0, count: p.review_count || 0, size: 13 }).el);
      }
    }
    resultBox.appendChild(outer);
  }

  wrap.querySelector('[data-role="cmp-btn"]').addEventListener('click', doCompare);
  wrap.querySelector('[data-role="clr-btn"]').addEventListener('click', () => {
    selects.forEach((s) => { s.value = ''; });
    errEl.textContent = '';
    showHint();
  });

  if (rawIds.length >= MIN_COMPARE) {
    await doCompare();
  } else {
    showHint();
  }
}
