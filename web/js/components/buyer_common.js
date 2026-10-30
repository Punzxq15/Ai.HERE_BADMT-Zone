// web/js/components/buyer_common.js — ตัวช่วยร่วมของหน้าผู้ซื้อ (ตรงกับ ui/pages/buyer/common.py)
import { api, esc } from '../api.js';
import { showToast } from './dialogs.js';

export async function toggleWishlist(productId) {
  try {
    const res = await api.post('/api/wishlist/toggle', { product_id: productId });
    const inWish = Boolean(res.in_wishlist);
    showToast(inWish ? 'เพิ่มลงในรายการโปรดแล้ว' : 'นำออกจากรายการโปรดแล้ว', 'success');
    return inWish;
  } catch (err) {
    showToast(err.message || 'กรุณาเข้าสู่ระบบก่อนทำรายการ', 'error');
    return null;
  }
}

export function pageTitleHtml(text, subtitle = null) {
  return `
    <div style="margin-bottom:12px">
      <div class="text-h2">${esc(text)}</div>
      ${subtitle ? `<div class="text-small text-muted">${esc(subtitle)}</div>` : ''}
    </div>
  `;
}
