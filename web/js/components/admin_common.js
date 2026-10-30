// web/js/components/admin_common.js — ตัวช่วยร่วมของหน้าแอดมิน (ตรงกับ ui/pages/admin/common.py)
import { esc, resolveAssetUrl } from '../api.js';
import { showImageWindow, openFileUrl } from './dialogs.js';

export function pillHtml(text, kind = 'muted') {
  return `<span class="pill pill-${esc(kind)}">${esc(text)}</span>`;
}

export function createSegmented(values = [], currentValue = null, onChange = null) {
  const wrap = document.createElement('div');
  wrap.className = 'segmented';
  let activeVal = currentValue !== null ? currentValue : (values[0] || '');

  function render() {
    wrap.innerHTML = '';
    for (const item of values) {
      const val = Array.isArray(item) ? item[0] : item;
      const lbl = Array.isArray(item) ? item[1] : item;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `segmented-btn ${val === activeVal ? 'active' : ''}`;
      btn.textContent = lbl;
      btn.addEventListener('click', () => {
        if (activeVal === val) return;
        activeVal = val;
        render();
        if (onChange) onChange(val);
      });
      wrap.appendChild(btn);
    }
  }
  render();

  return {
    el: wrap,
    get: () => activeVal,
    set(val) {
      activeVal = val;
      render();
    },
  };
}

export function createPager(onChange) {
  const wrap = document.createElement('div');
  wrap.style.display = 'inline-flex';
  wrap.style.alignItems = 'center';
  wrap.style.gap = '14px';
  wrap.style.marginTop = '10px';

  wrap.innerHTML = `
    <button type="button" class="btn btn-outline btn-sm" data-role="prev">‹ ก่อนหน้า</button>
    <span class="text-small text-muted" data-role="info">หน้า 1 / 1</span>
    <button type="button" class="btn btn-outline btn-sm" data-role="next">ถัดไป ›</button>
  `;

  let page = 1;
  let pages = 1;
  const prevBtn = wrap.querySelector('[data-role="prev"]');
  const nextBtn = wrap.querySelector('[data-role="next"]');
  const infoEl = wrap.querySelector('[data-role="info"]');

  prevBtn.addEventListener('click', () => { if (page > 1 && onChange) onChange(page - 1); });
  nextBtn.addEventListener('click', () => { if (page < pages && onChange) onChange(page + 1); });

  return {
    el: wrap,
    set(p, pgs, total = null) {
      page = Math.max(1, Number(p || 1));
      pages = Math.max(1, Number(pgs || 1));
      const extra = total !== null && total !== undefined ? `  ·  ทั้งหมด ${Number(total).toLocaleString()} รายการ` : '';
      infoEl.textContent = `หน้า ${page} / ${pages}${extra}`;
      prevBtn.disabled = page <= 1;
      nextBtn.disabled = page >= pages;
    },
  };
}

export function thumbHtml(path, size = 48) {
  const url = resolveAssetUrl(path);
  return `<img src="${esc(url)}" alt="thumb" style="width:${size}px;height:${size}px;border-radius:8px;object-fit:cover;background:var(--color-surface-alt);flex-shrink:0" onerror="this.onerror=null;this.src='/assets/icons/no_image.svg'" />`;
}

export function parseMoney(text, labelText, { required = false, minimum = 0.0 } = {}) {
  const clean = String(text || '').trim().replace(/,/g, '');
  if (!clean) {
    if (required) throw new Error(`กรุณากรอก${labelText}`);
    return null;
  }
  const val = Number(clean);
  if (!Number.isFinite(val)) throw new Error(`${labelText}ต้องเป็นตัวเลข`);
  if (val < minimum) throw new Error(`${labelText}ต้องไม่ต่ำกว่า ${minimum}`);
  return Math.round(val * 100) / 100;
}

export function parseIntField(text, labelText, { required = true, minimum = 0 } = {}) {
  const clean = String(text || '').trim().replace(/,/g, '');
  if (!clean) {
    if (required) throw new Error(`กรุณากรอก${labelText}`);
    return null;
  }
  if (!/^-?\d+$/.test(clean)) throw new Error(`${labelText}ต้องเป็นจำนวนเต็ม`);
  const val = parseInt(clean, 10);
  if (val < minimum) throw new Error(`${labelText}ต้องไม่ต่ำกว่า ${minimum}`);
  return val;
}

export { showImageWindow, openFileUrl };
