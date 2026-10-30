// web/js/components/product_filter.js — แถบกรองสินค้าแบบละเอียด (ตรงกับ ui/components/product_filter.py)
import { esc, WEIGHT_CLASSES, BALANCES, FLEXES, LEVELS } from '../api.js';

const ALL = 'ทั้งหมด';
const SORTS = [
  ['newest',     'มาใหม่ล่าสุด'],
  ['bestseller', 'ขายดี'],
  ['price_asc',  'ราคา: ต่ำ → สูง'],
  ['price_desc', 'ราคา: สูง → ต่ำ'],
  ['rating',     'คะแนนรีวิวสูงสุด'],
  ['discount',   'ส่วนลดสูงสุด'],
];

export function createProductFilter({
  categories = [],
  brands = [],
  onChange = null,
  showCategory = true,
  showRacketSpecs = true,
} = {}) {
  const card = document.createElement('div');
  card.className = 'card';
  card.style.width = '240px';
  card.style.padding = '16px 14px';
  card.style.flexShrink = '0';

  let catMap = new Map(categories.map((c) => [c.name, c.id]));
  let brandMap = new Map(brands.map((b) => [b.name, b.id]));

  card.innerHTML = `
    <div class="text-h3" style="margin-bottom:10px">ตัวกรองสินค้า</div>

    <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">เรียงตาม</div>
    <select class="select" data-role="sort">
      ${SORTS.map(([k, lbl]) => `<option value="${esc(k)}">${esc(lbl)}</option>`).join('')}
    </select>

    <div data-role="cat-wrap" class="${showCategory ? '' : 'hidden'}">
      <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">หมวดหมู่</div>
      <select class="select" data-role="cat"></select>
    </div>

    <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">แบรนด์</div>
    <select class="select" data-role="brand"></select>

    <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">ช่วงราคา (บาท)</div>
    <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:6px;align-items:center">
      <input type="text" class="input" data-role="min-price" placeholder="ต่ำสุด" style="height:34px;padding:0 8px" />
      <span>–</span>
      <input type="text" class="input" data-role="max-price" placeholder="สูงสุด" style="height:34px;padding:0 8px" />
    </div>

    <div data-role="specs-wrap" class="${showRacketSpecs ? '' : 'hidden'}">
      <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">น้ำหนักไม้ (Weight)</div>
      <select class="select" data-role="weight">
        <option value="">${ALL}</option>
        ${WEIGHT_CLASSES.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join('')}
      </select>

      <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">จุดสมดุล (Balance)</div>
      <select class="select" data-role="balance">
        <option value="">${ALL}</option>
        ${BALANCES.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join('')}
      </select>

      <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">ความแข็งก้าน (Flex)</div>
      <select class="select" data-role="flex">
        <option value="">${ALL}</option>
        ${FLEXES.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join('')}
      </select>

      <div class="text-small-bold text-muted" style="margin-top:8px;margin-bottom:2px">ระดับผู้เล่น (Level)</div>
      <select class="select" data-role="level">
        <option value="">${ALL}</option>
        ${LEVELS.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join('')}
      </select>
    </div>

    <label style="display:flex;align-items:center;gap:8px;margin-top:12px;cursor:pointer" class="text-body">
      <input type="checkbox" data-role="in-stock" />
      <span>เฉพาะที่มีสินค้า</span>
    </label>
    <label style="display:flex;align-items:center;gap:8px;margin-top:6px;cursor:pointer" class="text-body">
      <input type="checkbox" data-role="on-sale" />
      <span>เฉพาะสินค้าลดราคา</span>
    </label>

    <button type="button" class="btn btn-primary btn-md" data-role="apply" style="width:100%;margin-top:14px">ใช้ตัวกรอง</button>
    <button type="button" class="btn btn-outline btn-sm" data-role="reset" style="width:100%;margin-top:6px">ล้างตัวกรอง</button>
  `;

  const sortSel = card.querySelector('[data-role="sort"]');
  const catSel = card.querySelector('[data-role="cat"]');
  const brandSel = card.querySelector('[data-role="brand"]');
  const minPriceIn = card.querySelector('[data-role="min-price"]');
  const maxPriceIn = card.querySelector('[data-role="max-price"]');
  const weightSel = card.querySelector('[data-role="weight"]');
  const balanceSel = card.querySelector('[data-role="balance"]');
  const flexSel = card.querySelector('[data-role="flex"]');
  const levelSel = card.querySelector('[data-role="level"]');
  const inStockChk = card.querySelector('[data-role="in-stock"]');
  const onSaleChk = card.querySelector('[data-role="on-sale"]');

  function populateLists(cats, brs) {
    catMap = new Map((cats || []).map((c) => [String(c.id), c]));
    brandMap = new Map((brs || []).map((b) => [String(b.id), b]));
    catSel.innerHTML = `<option value="">${ALL}</option>` +
      (cats || []).map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join('');
    brandSel.innerHTML = `<option value="">${ALL}</option>` +
      (brs || []).map((b) => `<option value="${b.id}">${esc(b.name)}</option>`).join('');
  }

  populateLists(categories, brands);

  function parseNum(el) {
    const raw = el.value.trim().replace(/,/g, '');
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) ? n : null;
  }

  function getFilters() {
    return {
      category_id: catSel && showCategory && catSel.value ? Number(catSel.value) : null,
      brand_id: brandSel && brandSel.value ? Number(brandSel.value) : null,
      min_price: parseNum(minPriceIn),
      max_price: parseNum(maxPriceIn),
      weight_class: showRacketSpecs && weightSel.value ? weightSel.value : null,
      balance: showRacketSpecs && balanceSel.value ? balanceSel.value : null,
      flex: showRacketSpecs && flexSel.value ? flexSel.value : null,
      level: showRacketSpecs && levelSel.value ? levelSel.value : null,
      in_stock_only: Boolean(inStockChk.checked),
      on_sale_only: Boolean(onSaleChk.checked),
      sort: sortSel.value || 'newest',
    };
  }

  function emit() {
    if (onChange) onChange(getFilters());
  }

  [sortSel, catSel, brandSel, weightSel, balanceSel, flexSel, levelSel, inStockChk, onSaleChk].forEach((el) => {
    if (el) el.addEventListener('change', emit);
  });
  [minPriceIn, maxPriceIn].forEach((el) => {
    el.addEventListener('keydown', (e) => { if (e.key === 'Enter') emit(); });
  });
  card.querySelector('[data-role="apply"]').addEventListener('click', emit);
  card.querySelector('[data-role="reset"]').addEventListener('click', () => {
    reset({ notify: true });
  });

  function reset({ notify = true } = {}) {
    sortSel.value = 'newest';
    if (catSel) catSel.value = '';
    if (brandSel) brandSel.value = '';
    minPriceIn.value = '';
    maxPriceIn.value = '';
    if (weightSel) weightSel.value = '';
    if (balanceSel) balanceSel.value = '';
    if (flexSel) flexSel.value = '';
    if (levelSel) levelSel.value = '';
    inStockChk.checked = false;
    onSaleChk.checked = false;
    if (notify) emit();
  }

  return {
    el: card,
    getFilters,
    reset,
    setOptions({ categories: c, brands: b }) {
      populateLists(c || [], b || []);
    },
    setValues(vals = {}) {
      if (vals.category_id != null && catSel) catSel.value = String(vals.category_id);
      if (vals.brand_id != null && brandSel) brandSel.value = String(vals.brand_id);
      if (vals.sort) sortSel.value = vals.sort;
      if (vals.on_sale_only !== undefined) onSaleChk.checked = Boolean(vals.on_sale_only);
      if (vals.in_stock_only !== undefined) inStockChk.checked = Boolean(vals.in_stock_only);
    },
  };
}
