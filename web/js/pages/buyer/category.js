// web/js/pages/buyer/category.js — หน้ารายการสินค้า + ตัวกรอง + ค้นหา + เรียงลำดับ + แบ่งหน้า (ตรงกับ ui/pages/buyer/category.py)
import { api, esc } from '../../api.js';
import { createProductFilter } from '../../components/product_filter.js';
import { createProductGrid } from '../../components/product_grid.js';
import { createSearchBar } from '../../components/search_bar.js';
import { toggleWishlist } from '../../components/buyer_common.js';

const PAGE_SIZE = 12;
const SORTS = [
  ['newest',     'ใหม่ล่าสุด'],
  ['popular',    'ยอดนิยม'],
  ['price_asc',  'ราคา: ต่ำ → สูง'],
  ['price_desc', 'ราคา: สูง → ต่ำ'],
  ['name',       'ชื่อ A–Z'],
];

export async function render(container, router, params = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  wrap.style.display = 'grid';
  wrap.style.gridTemplateColumns = '240px 1fr';
  wrap.style.gap = '16px';
  wrap.style.alignItems = 'start';
  container.appendChild(wrap);

  let categories = [];
  let brands = [];
  let categoryNames = {};
  try {
    [categories, brands] = await Promise.all([
      api.get('/api/categories'),
      api.get('/api/brands'),
    ]);
    for (const c of categories || []) categoryNames[c.id] = c.name;
  } catch (e) {}

  let query = String(params.search || '').trim();
  let sort = 'newest';
  let curFilters = {
    category_id: params.category_id ? Number(params.category_id) : null,
    brand_id: params.brand_id ? Number(params.brand_id) : null,
    on_sale_only: Boolean(params.on_sale),
  };

  const filterComp = createProductFilter({
    categories,
    brands,
    showCategory: true,
    showRacketSpecs: true,
    onChange(f) {
      curFilters = f;
      if (f.sort) sort = f.sort;
      loadPage(1);
    },
  });
  filterComp.setValues(curFilters);
  wrap.appendChild(filterComp.el);

  const main = document.createElement('div');
  main.style.display = 'flex';
  main.style.flexDirection = 'column';
  main.style.gap = '10px';
  main.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      <div class="text-h2" data-role="title">สินค้าทั้งหมด</div>
      <select class="select" data-role="sort" style="width:160px;height:34px">
        ${SORTS.map(([k, lbl]) => `<option value="${esc(k)}">${esc(lbl)}</option>`).join('')}
      </select>
    </div>
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap" data-role="search-row">
      <div data-role="search-slot"></div>
      <div class="text-small text-danger" data-role="err"></div>
    </div>
    <div data-role="grid-slot"></div>
  `;
  wrap.appendChild(main);

  const titleEl = main.querySelector('[data-role="title"]');
  const sortSel = main.querySelector('[data-role="sort"]');
  const errEl = main.querySelector('[data-role="err"]');

  const searchBar = createSearchBar({
    width: 420,
    onSubmit(q) {
      query = q;
      loadPage(1);
    },
    onSelectSuggestion(pid) {
      router.show('product_detail', { product_id: pid });
    },
  });
  searchBar.set(query);
  main.querySelector('[data-role="search-slot"]').appendChild(searchBar.el);

  const grid = createProductGrid({
    onOpen: (pid) => router.show('product_detail', { product_id: pid }),
    onWishlist: (pid) => toggleWishlist(pid),
    onPage: (p) => loadPage(p),
  });
  main.querySelector('[data-role="grid-slot"]').appendChild(grid.el);

  sortSel.addEventListener('change', () => {
    sort = sortSel.value;
    loadPage(1);
  });

  async function loadPage(page = 1) {
    errEl.textContent = '';
    const f = filterComp.getFilters();
    try {
      const res = await api.get('/api/products', {
        query: query || undefined,
        category_id: f.category_id || undefined,
        brand_id: f.brand_id || undefined,
        min_price: f.min_price ?? undefined,
        max_price: f.max_price ?? undefined,
        weight_class: f.weight_class || undefined,
        balance: f.balance || undefined,
        flex: f.flex || undefined,
        level: f.level || undefined,
        in_stock: f.in_stock_only ? 'true' : undefined,
        on_sale: f.on_sale_only ? 'true' : undefined,
        sort: sort || f.sort || 'newest',
        page,
        page_size: PAGE_SIZE,
      });
      grid.setResult(res);
      const catName = f.category_id ? categoryNames[f.category_id] : null;
      let text = 'สินค้าทั้งหมด';
      if (query) text = `ผลการค้นหา "${query}"`;
      else if (catName) text = catName;
      else if (f.on_sale_only) text = 'สินค้าลดราคา';
      titleEl.textContent = `${text}  (${Number(res.total || 0).toLocaleString()})`;
    } catch (err) {
      errEl.textContent = err.message || 'โหลดรายการสินค้าไม่สำเร็จ';
    }
  }

  await loadPage(1);
}
