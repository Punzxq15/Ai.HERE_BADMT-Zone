// web/js/components/product_card.js — การ์ดสินค้า 3:4 (220x305) รูป 1:1 ตรงกับ ui/components/product_card.py
import { esc, formatPrice, parseDateTime, resolveAssetUrl } from '../api.js';
import { iconSvg } from './icons.js';
import { createRatingStars } from './rating.js';

export const CARD_WIDTH = 220;
export const CARD_HEIGHT = 305;

export function createProductCard(product, {
  onOpen = null,
  onWishlist = null,
  inWishlist = undefined,
} = {}) {
  const pid = product.id;
  let liked = inWishlist !== undefined ? Boolean(inWishlist) : Boolean(product.in_wishlist);
  const onSale = Boolean(product.on_sale);
  const price = Number(product.price || 0);
  const effective = Number(product.effective_price ?? product.sale_price ?? price);
  let discount = Number(product.discount_percent || 0);
  if (!discount && onSale && price > 0) {
    discount = Math.round((1 - effective / price) * 100);
  }
  const stock = Number(product.stock || 0);

  const card = document.createElement('div');
  card.className = 'product-card';
  card.dataset.productId = String(pid);

  const imgUrl = resolveAssetUrl(product.image_path);
  card.innerHTML = `
    <div class="product-card-img-wrap">
      <img class="product-card-img" src="${esc(imgUrl)}" alt="${esc(product.name || '')}" loading="lazy" />
      ${(onSale && discount > 0) ? `<span class="product-card-discount">-${discount}%</span>` : ''}
      ${onWishlist ? `<button type="button" class="product-card-heart" data-role="heart" title="รายการโปรด"></button>` : ''}
      ${stock <= 0 ? `<span class="product-card-out">สินค้าหมด</span>` : ''}
    </div>
    <div class="product-card-brand">${esc(product.brand_name || '')}</div>
    <div class="product-card-name" title="${esc(product.name || '')}">${esc(product.name || '')}</div>
    <div data-role="rating-slot" style="margin-top:2px"></div>
    <div class="product-card-price-row">
      <span class="${onSale ? 'product-card-price' : 'product-card-price-normal'}">${esc(formatPrice(onSale ? effective : price))}</span>
      ${(onSale && effective < price) ? `<span class="product-card-price-old">${esc(formatPrice(price))}</span>` : ''}
    </div>
    <div class="product-card-countdown hidden" data-role="countdown"></div>
  `;

  const imgEl = card.querySelector('.product-card-img');
  imgEl.addEventListener('error', () => {
    if (!imgEl.src.endsWith('/assets/icons/no_image.svg')) {
      imgEl.src = '/assets/icons/no_image.svg';
    }
  });

  const ratingSlot = card.querySelector('[data-role="rating-slot"]');
  const ratingComp = createRatingStars({
    value: product.avg_rating || 0,
    count: product.review_count || 0,
    size: 13,
  });
  ratingSlot.appendChild(ratingComp.el);

  const heartBtn = card.querySelector('[data-role="heart"]');
  const paintHeart = () => {
    if (!heartBtn) return;
    heartBtn.innerHTML = liked
      ? iconSvg('heart_filled', 16, '#E63946')
      : iconSvg('heart', 16, 'var(--color-text-muted)');
  };
  if (heartBtn) {
    paintHeart();
    heartBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const res = await onWishlist(pid);
      if (res === true || res === false) {
        liked = res;
      } else {
        liked = !liked;
      }
      paintHeart();
    });
  }

  // Flash Sale Countdown
  const saleEndDt = onSale ? parseDateTime(product.sale_end) : null;
  const cdEl = card.querySelector('[data-role="countdown"]');
  if (saleEndDt && cdEl) {
    const tick = () => {
      if (!document.body.contains(card)) return false;
      const secs = Math.floor((saleEndDt.getTime() - Date.now()) / 1000);
      if (secs <= 0) {
        cdEl.textContent = 'หมดเวลาโปร';
        cdEl.classList.remove('hidden');
        return false;
      }
      const days = Math.floor(secs / 86400);
      const rem1 = secs % 86400;
      const hours = Math.floor(rem1 / 3600);
      const rem2 = rem1 % 3600;
      const mins = Math.floor(rem2 / 60);
      const s = rem2 % 60;
      const hh = String(hours).padStart(2, '0');
      const mm = String(mins).padStart(2, '0');
      const ss = String(s).padStart(2, '0');
      const prefix = days > 0 ? `${days} วัน ` : '';
      cdEl.textContent = `⏰ เหลือ ${prefix}${hh}:${mm}:${ss}`;
      cdEl.classList.remove('hidden');
      return true;
    };
    if (tick()) {
      const iv = setInterval(() => {
        if (!tick()) clearInterval(iv);
      }, 1000);
    }
  }

  card.addEventListener('click', () => {
    if (onOpen) onOpen(pid);
  });

  return card;
}
