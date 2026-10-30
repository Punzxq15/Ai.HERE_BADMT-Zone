// web/js/pages/buyer/wishlist.js — หน้ารายการโปรด (ตรงกับ ui/pages/buyer/wishlist.py)
import { api, esc } from '../../api.js';
import { createProductCard } from '../../components/product_card.js';
import { pageTitleHtml, toggleWishlist } from '../../components/buyer_common.js';

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  wrap.innerHTML = `
    <div style="display:flex;align-items:center;gap:16px">
      ${pageTitleHtml('♥ รายการโปรด', 'สินค้าที่คุณกดหัวใจเก็บไว้')}
      <span class="text-small text-danger" data-role="err"></span>
    </div>
    <div data-role="grid-area"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const gridArea = wrap.querySelector('[data-role="grid-area"]');

  async function load() {
    errEl.textContent = '';
    gridArea.innerHTML = '';
    try {
      const items = await api.get('/api/wishlist');
      if (!items || !items.length) {
        gridArea.innerHTML = `<div class="text-h3 text-muted" style="text-align:center;padding:60px 20px;white-space:pre-line">ยังไม่มีสินค้าในรายการโปรด
กดหัวใจที่สินค้าเพื่อเก็บไว้ดูภายหลัง</div>`;
        return;
      }
      const grid = document.createElement('div');
      grid.className = 'wrap-grid';
      for (const p of items) {
        const card = createProductCard(p, {
          onOpen: (pid) => router.show('product_detail', { product_id: pid }),
          inWishlist: true,
          onWishlist: async (pid) => {
            const st = await toggleWishlist(pid);
            if (st === false) {
              setTimeout(() => load(), 150);
            }
            return st;
          },
        });
        grid.appendChild(card);
      }
      gridArea.appendChild(grid);
    } catch (err) {
      errEl.textContent = err.message || 'โหลดรายการโปรดไม่สำเร็จ';
    }
  }

  await load();
}
