// web/js/components/product_grid.js — กริดการ์ดสินค้า + แถบเปลี่ยนหน้า (ตรงกับ ui/components/product_grid.py)
import { esc } from '../api.js';
import { createProductCard } from './product_card.js';

export function createProductGrid({
  onOpen = null,
  onWishlist = null,
  onPage = null,
  emptyText = 'ไม่พบสินค้าที่ตรงกับเงื่อนไข',
} = {}) {
  const wrap = document.createElement('div');
  wrap.style.display = 'flex';
  wrap.style.flexDirection = 'column';
  wrap.style.gap = '12px';
  wrap.style.width = '100%';

  const gridArea = document.createElement('div');
  gridArea.className = 'wrap-grid';
  wrap.appendChild(gridArea);

  const pagerBar = document.createElement('div');
  pagerBar.style.display = 'flex';
  pagerBar.style.alignItems = 'center';
  pagerBar.style.justifyContent = 'center';
  pagerBar.style.gap = '16px';
  pagerBar.style.padding = '8px 0';
  pagerBar.innerHTML = `
    <button type="button" class="btn btn-outline btn-sm" data-role="prev" style="width:110px">‹ ก่อนหน้า</button>
    <span class="text-body text-muted" data-role="page-info">หน้า 1 / 1</span>
    <button type="button" class="btn btn-outline btn-sm" data-role="next" style="width:110px">ถัดไป ›</button>
  `;
  wrap.appendChild(pagerBar);

  const prevBtn = pagerBar.querySelector('[data-role="prev"]');
  const nextBtn = pagerBar.querySelector('[data-role="next"]');
  const pageInfo = pagerBar.querySelector('[data-role="page-info"]');

  let curPage = 1;
  let totalPages = 1;

  prevBtn.addEventListener('click', () => {
    if (curPage > 1 && onPage) onPage(curPage - 1);
  });
  nextBtn.addEventListener('click', () => {
    if (curPage < totalPages && onPage) onPage(curPage + 1);
  });

  function setItems(items = [], { page = 1, pages = 1, total = null, wishlistIds = null } = {}) {
    curPage = Math.max(1, Number(page || 1));
    totalPages = Math.max(1, Number(pages || 1));
    gridArea.innerHTML = '';

    if (!items || !items.length) {
      gridArea.style.display = 'block';
      gridArea.innerHTML = `<div class="text-h3 text-muted" style="text-align:center;padding:60px 20px">${esc(emptyText)}</div>`;
    } else {
      gridArea.style.display = 'grid';
      const wishSet = wishlistIds ? new Set(wishlistIds) : null;
      for (const p of items) {
        const inWish = wishSet !== null ? wishSet.has(p.id) : p.in_wishlist;
        const card = createProductCard(p, { onOpen, onWishlist, inWishlist: inWish });
        gridArea.appendChild(card);
      }
    }

    const totalTxt = total !== null && total !== undefined ? `  (${total} รายการ)` : '';
    pageInfo.textContent = `หน้า ${curPage} / ${totalPages}${totalTxt}`;
    prevBtn.disabled = curPage <= 1;
    nextBtn.disabled = curPage >= totalPages;
  }

  return {
    el: wrap,
    setItems,
    setResult(res = {}, wishlistIds = null) {
      setItems(res.items || [], {
        page: res.page || 1,
        pages: res.pages || 1,
        total: res.total,
        wishlistIds,
      });
    },
  };
}
