// web/js/pages/buyer/product_detail.js — หน้ารายละเอียดสินค้า (T03 Tech Specs 7 หัวข้อ, T04 แกลเลอรีหลายรูปผูกสี, Bundle Deal, รีวิวพร้อมตัวเลือกที่สั่ง + รูป/วิดีโอแนบ)
import { api, esc, formatDateTime, formatPrice, resolveAssetUrl } from '../../api.js';
import { state } from '../../state.js';
import { createRatingStars } from '../../components/rating.js';
import { openModal, showToast } from '../../components/dialogs.js';
import { toggleWishlist } from '../../components/buyer_common.js';
import { iconSvg } from '../../components/icons.js';

const REVIEW_PAGE_SIZE = 5;

function formatCountdown(secs) {
  const s = Math.max(0, Math.floor(secs));
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const hh = String(h).padStart(2, '0');
  const mm = String(m).padStart(2, '0');
  const ss = String(sec).padStart(2, '0');
  return d > 0 ? `${d} วัน ${hh}:${mm}:${ss}` : `${hh}:${mm}:${ss}`;
}

function openReviewImageLightbox(imgUrl, reviewerName = '') {
  openModal({
    title: reviewerName ? `รูปภาพรีวิวจาก ${reviewerName}` : 'รูปภาพรีวิวสินค้า',
    width: 680,
    render(body, close) {
      body.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;gap:12px">
          <div style="width:100%;max-height:72vh;display:flex;align-items:center;justify-content:center;background:var(--color-surface-alt);border-radius:12px;overflow:hidden;border:1px solid var(--color-border)">
            <img src="${esc(imgUrl)}" alt="review-photo" style="max-width:100%;max-height:70vh;object-fit:contain" />
          </div>
          <div style="display:flex;justify-content:flex-end;width:100%">
            <button type="button" class="btn btn-primary btn-sm" data-role="close">ปิด</button>
          </div>
        </div>
      `;
      body.querySelector('[data-role="close"]').addEventListener('click', () => close(true));
    },
  });
}

export async function render(container, router, params = {}) {
  const productId = params.product_id || params.id;
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  const backBtn = document.createElement('button');
  backBtn.type = 'button';
  backBtn.className = 'btn btn-outline btn-sm';
  backBtn.textContent = '‹ ย้อนกลับ';
  backBtn.addEventListener('click', () => router.go_back('home'));
  wrap.appendChild(backBtn);

  let product = null;
  try {
    product = await api.get(`/api/products/${productId}`);
  } catch (err) {
    const errDiv = document.createElement('div');
    errDiv.className = 'text-body text-danger';
    errDiv.style.padding = '40px 0';
    errDiv.textContent = err.message || 'ไม่พบสินค้า';
    wrap.appendChild(errDiv);
    return;
  }

  let inWishlist = Boolean(product.in_wishlist);
  let qty = 1;
  let galleryIdx = 0;
  let reviewPage = 0;
  let reviewPages = 1;
  const timers = [];

  // Prepare gallery items
  const galleryItems = [...(product.images || [])];
  const seenPaths = new Set(galleryItems.map((g) => g.path).filter(Boolean));
  for (const opt of product.options || []) {
    if (opt.image_path && !seenPaths.has(opt.image_path)) {
      seenPaths.add(opt.image_path);
      galleryItems.push({
        id: -Number(opt.id),
        product_id: product.id,
        path: opt.image_path,
        sort_order: 999,
        color_value: opt.option_value,
      });
    }
  }
  if (!galleryItems.length) {
    galleryItems.push({ id: 0, product_id: product.id, path: product.image_path, sort_order: 1, color_value: null });
  }

  // Options map
  const options = product.options || [];
  const multiType = new Set(options.map((o) => o.option_type)).size > 1;
  const optionMap = new Map();
  for (const o of options) {
    let text = multiType ? `${o.option_type}: ${o.option_value}` : o.option_value;
    if (o.extra_price) text += `  (+${formatPrice(o.extra_price)})`;
    if (!o.in_stock) text += '  — หมด';
    optionMap.set(text, o);
  }
  let selectedOptionKey = null;
  for (const [k, o] of optionMap.entries()) {
    if (o.in_stock) { selectedOptionKey = k; break; }
  }
  if (!selectedOptionKey && optionMap.size) {
    selectedOptionKey = optionMap.keys().next().value;
  }

  // Main card
  const mainCard = document.createElement('div');
  mainCard.className = 'card';
  mainCard.style.margin = '10px 0 14px';
  mainCard.style.padding = '20px 24px';
  mainCard.style.display = 'grid';
  mainCard.style.gridTemplateColumns = '380px 1fr';
  mainCard.style.gap = '24px';
  wrap.appendChild(mainCard);

  mainCard.innerHTML = `
    <!-- ซ้าย: แกลเลอรีรูปภาพ -->
    <div style="display:flex;flex-direction:column;align-items:center">
      <div style="width:360px;height:380px;border-radius:16px;border:2px solid var(--color-border);background:var(--color-surface-alt);display:flex;align-items:center;justify-content:center;overflow:hidden">
        <img data-role="main-img" src="${esc(resolveAssetUrl(galleryItems[0].path))}" alt="${esc(product.name)}" style="max-width:100%;max-height:100%;object-fit:contain" />
      </div>
      <div class="text-small-bold text-info" data-role="img-caption" style="margin-top:6px;min-height:18px"></div>
      ${galleryItems.length > 1 ? `
        <div style="display:flex;align-items:center;justify-content:space-between;width:100%;margin-top:4px">
          <button type="button" class="btn btn-outline btn-sm" data-role="gal-prev">‹ รูปก่อนหน้า</button>
          <span class="text-small-bold" data-role="gal-counter"></span>
          <button type="button" class="btn btn-outline btn-sm" data-role="gal-next">รูปถัดไป ›</button>
        </div>
        <div data-role="thumb-bar" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:6px"></div>
      ` : ''}
    </div>

    <!-- ขวา: ข้อมูลสินค้า -->
    <div>
      <div style="display:flex;gap:6px;margin-bottom:6px">
        ${product.brand_name ? `<span class="pill" style="background:#DBEAFE;color:#1D4ED8;border-radius:6px">${esc(String(product.brand_name).toUpperCase())}</span>` : ''}
        ${product.category_name ? `<span class="pill" style="background:#18181B;color:#FFB703;border-radius:6px">${esc(product.category_name)}</span>` : ''}
      </div>
      <div class="text-h1" style="margin-bottom:8px">${esc(product.name)}</div>

      <div style="display:inline-flex;flex-direction:column;background:var(--badge-accent-bg);border:2px solid var(--color-danger);border-radius:12px;padding:10px 16px;margin-bottom:8px">
        <div class="text-small-bold text-danger hidden" data-role="countdown" style="margin-bottom:4px"></div>
        <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap">
          <span class="text-price-big text-danger" data-role="price"></span>
          <span class="text-body text-muted hidden" data-role="old-price" style="text-decoration:line-through"></span>
          <span class="pill pill-danger hidden" data-role="discount-badge"></span>
        </div>
      </div>

      <div data-role="rating-row" style="margin-bottom:10px"></div>

      ${options.length ? `
        <div class="text-body-bold" style="margin-bottom:6px">${esc(multiType ? 'เลือกสี / สไตล์ / ตัวเลือกสินค้า' : `เลือก${options[0].option_type}`)}</div>
        <div data-role="chips-wrap" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px"></div>
        <select class="select" data-role="option-select" style="max-width:300px;margin-bottom:4px">
          ${Array.from(optionMap.keys()).map((k) => `<option value="${esc(k)}">${esc(k)}</option>`).join('')}
        </select>
        <div class="text-small text-muted" data-role="option-hint" style="min-height:18px"></div>
      ` : '<div data-role="option-hint"></div>'}

      <div style="display:flex;align-items:center;gap:10px;margin-top:12px">
        <span class="text-body-bold">จำนวน</span>
        <button type="button" class="btn btn-outline btn-md" data-role="qty-minus" style="width:36px;padding:0">−</button>
        <span class="text-body-bold" data-role="qty-lbl" style="min-width:36px;text-align:center">1</span>
        <button type="button" class="btn btn-outline btn-md" data-role="qty-plus" style="width:36px;padding:0">+</button>
        <span class="pill" data-role="stock-badge"></span>
      </div>

      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:16px">
        <button type="button" class="btn btn-primary btn-lg" data-role="add-cart">${iconSvg('cart', 18, '#111318')} <span>เพิ่มลงตะกร้า</span></button>
        <button type="button" class="btn btn-danger btn-lg" data-role="buy-now">${iconSvg('flash', 18, '#FFFFFF')} <span>ซื้อเลย</span></button>
        <button type="button" class="btn btn-lg" data-role="wish-btn" style="background:#DB2777;color:#FFFFFF"></button>
        ${product.is_racket ? `<button type="button" class="btn btn-info btn-lg" data-role="compare-btn">${iconSvg('compare', 16, '#FFFFFF')} <span>เปรียบเทียบ</span></button>` : ''}
      </div>

      <div class="text-small-bold" data-role="msg" style="margin-top:8px;min-height:18px"></div>
    </div>
  `;

  const mainImg = mainCard.querySelector('[data-role="main-img"]');
  const imgCaption = mainCard.querySelector('[data-role="img-caption"]');
  const galCounter = mainCard.querySelector('[data-role="gal-counter"]');
  const thumbBar = mainCard.querySelector('[data-role="thumb-bar"]');

  mainCard.querySelector('[data-role="rating-row"]').appendChild(
    createRatingStars({ value: product.review_avg || 0, count: product.review_count || 0, size: 14 }).el
  );

  function renderGallery() {
    const g = galleryItems[galleryIdx % galleryItems.length];
    mainImg.src = resolveAssetUrl(g.path);
    imgCaption.textContent = g.color_value ? `สี/สไตล์ที่แสดง: ${g.color_value}` : '';
    if (galCounter) {
      galCounter.textContent = `รูปที่ ${(galleryIdx % galleryItems.length) + 1} / ${galleryItems.length}`;
    }
    if (thumbBar) {
      thumbBar.innerHTML = '';
      galleryItems.slice(0, 6).forEach((item, idx) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.style.width = '62px';
        b.style.height = '62px';
        b.style.borderRadius = '8px';
        b.style.padding = '2px';
        b.style.background = 'var(--color-surface-alt)';
        b.style.border = idx === galleryIdx ? '3px solid var(--color-primary)' : '1px solid var(--color-border)';
        b.style.cursor = 'pointer';
        b.innerHTML = `<img src="${esc(resolveAssetUrl(item.path))}" alt="thumb" style="width:100%;height:100%;object-fit:cover;border-radius:6px" />`;
        b.addEventListener('click', () => { galleryIdx = idx; renderGallery(); });
        thumbBar.appendChild(b);
      });
    }
  }

  const galPrev = mainCard.querySelector('[data-role="gal-prev"]');
  const galNext = mainCard.querySelector('[data-role="gal-next"]');
  if (galPrev) galPrev.addEventListener('click', () => { galleryIdx = (galleryIdx - 1 + galleryItems.length) % galleryItems.length; renderGallery(); });
  if (galNext) galNext.addEventListener('click', () => { galleryIdx = (galleryIdx + 1) % galleryItems.length; renderGallery(); });

  const optSelect = mainCard.querySelector('[data-role="option-select"]');
  const chipsWrap = mainCard.querySelector('[data-role="chips-wrap"]');
  const priceEl = mainCard.querySelector('[data-role="price"]');
  const oldPriceEl = mainCard.querySelector('[data-role="old-price"]');
  const discBadge = mainCard.querySelector('[data-role="discount-badge"]');
  const stockBadge = mainCard.querySelector('[data-role="stock-badge"]');
  const qtyLbl = mainCard.querySelector('[data-role="qty-lbl"]');
  const optHint = mainCard.querySelector('[data-role="option-hint"]');
  const addBtn = mainCard.querySelector('[data-role="add-cart"]');
  const buyBtn = mainCard.querySelector('[data-role="buy-now"]');
  const wishBtn = mainCard.querySelector('[data-role="wish-btn"]');
  const msgEl = mainCard.querySelector('[data-role="msg"]');

  function currentOption() {
    return selectedOptionKey ? optionMap.get(selectedOptionKey) : null;
  }
  function unitPrice() {
    const o = currentOption();
    return o ? Number(o.final_price) : Number(product.effective_price);
  }
  function currentStock() {
    const o = currentOption();
    return o ? Number(o.stock || 0) : Number(product.stock || 0);
  }

  function paintWishBtn() {
    wishBtn.innerHTML = inWishlist
      ? `${iconSvg('heart_filled', 16, '#FFFFFF')} <span>อยู่ในรายการโปรด</span>`
      : `${iconSvg('heart', 16, '#FFFFFF')} <span>เพิ่มในรายการโปรด</span>`;
  }
  paintWishBtn();

  function refreshOption() {
    const opt = currentOption();
    const unit = unitPrice();
    priceEl.textContent = formatPrice(unit);

    if (optSelect && selectedOptionKey) optSelect.value = selectedOptionKey;
    if (chipsWrap) {
      chipsWrap.innerHTML = '';
      for (const [k, o] of optionMap.entries()) {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = `btn btn-sm ${k === selectedOptionKey ? 'btn-primary' : 'btn-outline'}`;
        b.textContent = o.option_value + (o.extra_price ? ` (+${Math.round(o.extra_price)})` : '');
        b.addEventListener('click', () => {
          selectedOptionKey = k;
          refreshOption();
        });
        chipsWrap.appendChild(b);
      }
    }

    // Sync gallery to option
    if (opt) {
      const optVal = String(opt.option_value || '').trim().toLowerCase();
      const optImg = String(opt.image_path || '').trim();
      const foundIdx = galleryItems.findIndex((g) => {
        const gCol = String(g.color_value || '').trim().toLowerCase();
        const gPath = String(g.path || '').trim();
        return (optImg && gPath === optImg) || (optVal && gCol && (optVal === gCol || gCol.includes(optVal)));
      });
      if (foundIdx >= 0) galleryIdx = foundIdx;
    }
    renderGallery();

    let pct = 0;
    if (product.is_on_sale) {
      const full = Number(product.price || 0) + (opt ? Number(opt.extra_price || 0) : 0);
      if (full > unit) pct = Math.round((1 - unit / full) * 100);
      if (pct > 0) {
        oldPriceEl.textContent = formatPrice(full);
        oldPriceEl.classList.remove('hidden');
        discBadge.textContent = `ลด ${pct}%`;
        discBadge.classList.remove('hidden');
      } else {
        oldPriceEl.classList.add('hidden');
        discBadge.classList.add('hidden');
      }
    } else {
      oldPriceEl.classList.add('hidden');
      discBadge.classList.add('hidden');
    }

    const stock = currentStock();
    if (stock > 0) {
      stockBadge.className = 'pill pill-success';
      stockBadge.textContent = `✓ มีสินค้าพร้อมส่ง ${stock.toLocaleString()} ชิ้น`;
      qty = Math.max(1, Math.min(qty, stock, 99));
      addBtn.disabled = false;
      buyBtn.disabled = false;
    } else {
      stockBadge.className = 'pill pill-danger';
      stockBadge.textContent = '⛔ สินค้าหมดชั่วคราว';
      qty = 1;
      addBtn.disabled = true;
      buyBtn.disabled = true;
    }
    qtyLbl.textContent = String(qty);

    if (opt && opt.option_type === 'เอ็น' && String(opt.option_value).includes('ขึ้นเอ็น')) {
      optHint.textContent = 'ต้องการระบุความตึงเอ็น (lbs)? แจ้งร้านทางแชทหลังสั่งซื้อได้เลย';
    } else {
      optHint.textContent = '';
    }
    updateBundleTotal();
  }

  if (optSelect) {
    optSelect.addEventListener('change', () => {
      selectedOptionKey = optSelect.value;
      refreshOption();
    });
  }

  mainCard.querySelector('[data-role="qty-minus"]').addEventListener('click', () => {
    if (qty > 1) { qty -= 1; qtyLbl.textContent = String(qty); updateBundleTotal(); }
  });
  mainCard.querySelector('[data-role="qty-plus"]').addEventListener('click', () => {
    const limit = Math.min(currentStock(), 99);
    if (qty < limit) { qty += 1; qtyLbl.textContent = String(qty); updateBundleTotal(); }
  });

  async function addToCart(buyNow = false) {
    if (!state.logged_in) {
      state.pending_after_login = ['product_detail', { product_id: product.id }];
      router.show('login', { info_message: 'กรุณาเข้าสู่ระบบก่อนเพิ่มสินค้าลงตะกร้าหรือสั่งซื้อ' });
      return;
    }
    const opt = currentOption();
    try {
      const res = await api.post('/api/cart/items', {
        product_id: product.id,
        option_id: opt ? opt.id : null,
        qty,
      });
      await router.refresh_shell();
      if (buyNow) {
        router.show('cart');
        return;
      }
      msgEl.textContent = '';
      showToast(`เพิ่มลงตะกร้าสำเร็จ (ในตะกร้ามี ${Number(res.cart_count || 0).toLocaleString()} ชิ้น)`, 'success');
    } catch (err) {
      const em = err.message || 'เพิ่มลงตะกร้าไม่สำเร็จ';
      msgEl.className = 'text-small-bold text-danger';
      msgEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
    }
  }

  addBtn.addEventListener('click', () => addToCart(false));
  buyBtn.addEventListener('click', () => addToCart(true));
  wishBtn.addEventListener('click', async () => {
    if (!state.logged_in) {
      state.pending_after_login = ['product_detail', { product_id: product.id }];
      router.show('login', { info_message: 'กรุณาเข้าสู่ระบบก่อนเพิ่มรายการโปรด' });
      return;
    }
    const st = await toggleWishlist(product.id);
    if (st !== null) {
      inWishlist = st;
      paintWishBtn();
    }
  });
  const cmpBtn = mainCard.querySelector('[data-role="compare-btn"]');
  if (cmpBtn) {
    cmpBtn.addEventListener('click', () => router.show('compare', { ids: String(product.id) }));
  }

  // Countdown
  const cdEl = mainCard.querySelector('[data-role="countdown"]');
  if (product.is_on_sale && product.sale_seconds_left != null) {
    const deadline = Date.now() + Number(product.sale_seconds_left) * 1000;
    const tickCd = () => {
      const left = Math.floor((deadline - Date.now()) / 1000);
      cdEl.classList.remove('hidden');
      if (left <= 0) {
        cdEl.textContent = 'Flash Sale สิ้นสุดแล้ว';
        return;
      }
      cdEl.textContent = `⚡ FLASH SALE เหลือเวลา ${formatCountdown(left)}`;
    };
    tickCd();
    timers.push(setInterval(tickCd, 1000));
  }

  // T03: Technical Specifications (7 หัวข้อ ซ่อนแถวว่าง)
  const techSpecs = product.technical_specs || [];
  if (techSpecs.length) {
    const specCard = document.createElement('div');
    specCard.style.background = '#18181B';
    specCard.style.border = '2px solid #FFB703';
    specCard.style.borderRadius = '14px';
    specCard.style.padding = '14px 18px';
    specCard.style.marginBottom = '14px';
    specCard.innerHTML = `
      <div style="background:#27272A;border-radius:10px;padding:8px 12px;margin-bottom:10px;display:flex;align-items:center;gap:8px;color:#FFB703" class="text-h3">
        ${iconSvg('racket', 18, '#FFB703')} <span>Technical Specifications (ข้อมูลจำเพาะทางเทคนิค)</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:4px">
        ${techSpecs.map((item, idx) => `
          <div style="display:grid;grid-template-columns:220px 1fr;padding:6px 12px;border-radius:6px;background:${idx % 2 === 0 ? '#232329' : 'transparent'}">
            <span class="text-body-bold" style="color:#FDE68A">• ${esc(item.label)}:</span>
            <span class="text-body-bold" style="color:#FFFFFF">${esc(item.value)}</span>
          </div>
        `).join('')}
      </div>
    `;
    wrap.appendChild(specCard);
  }

  // Bundle Deals (addons)
  const addons = product.addons || [];
  const addonRows = [];
  let bundleTotalLbl = null;
  let bundleBtn = null;
  let bundleMsg = null;

  function updateBundleTotal() {
    if (!addonRows.length || !bundleTotalLbl) return;
    const selected = addonRows.filter((r) => r.chk.checked);
    for (const r of addonRows) {
      const opt = r.sel ? r.optionsMap.get(r.sel.value) : null;
      const p = opt ? Number(opt.final_price) : Number(r.addon.effective_price);
      r.priceEl.textContent = formatPrice(p);
    }
    const sumAddons = selected.reduce((acc, r) => {
      const opt = r.sel ? r.optionsMap.get(r.sel.value) : null;
      return acc + (opt ? Number(opt.final_price) : Number(r.addon.effective_price));
    }, 0);
    const total = unitPrice() * qty + sumAddons;
    bundleTotalLbl.textContent = `รวมชุดที่เลือก: ${formatPrice(total)}`;
    bundleBtn.disabled = !(selected.length > 0 && currentStock() > 0);
  }

  if (addons.length) {
    const addonCard = document.createElement('div');
    addonCard.className = 'card';
    addonCard.style.padding = '14px 20px';
    addonCard.style.marginBottom = '14px';
    addonCard.innerHTML = `
      <div style="background:var(--badge-success-bg);color:var(--badge-success-fg);border-radius:8px;padding:6px 12px;margin-bottom:6px" class="text-h3">ซื้อคู่กันคุ้มกว่า (Bundle Deal)</div>
      <div class="text-small text-muted" style="margin-bottom:8px">เลือกสินค้าเสริมแล้วเพิ่มลงตะกร้าพร้อมกันได้ในคลิกเดียว</div>
      <div data-role="addon-list" style="display:flex;flex-direction:column;gap:6px"></div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px">
        <span class="text-body-bold" data-role="bundle-total"></span>
        <button type="button" class="btn btn-primary btn-md" data-role="bundle-btn">เพิ่มชุดนี้ลงตะกร้า</button>
      </div>
      <div class="text-small" data-role="bundle-msg" style="margin-top:6px"></div>
    `;
    wrap.appendChild(addonCard);

    const listEl = addonCard.querySelector('[data-role="addon-list"]');
    bundleTotalLbl = addonCard.querySelector('[data-role="bundle-total"]');
    bundleBtn = addonCard.querySelector('[data-role="bundle-btn"]');
    bundleMsg = addonCard.querySelector('[data-role="bundle-msg"]');

    for (const addon of addons) {
      let detailOpts = [];
      try {
        const d = await api.get(`/api/products/${addon.id}`);
        detailOpts = d.options || [];
      } catch (e) {}
      const optionsMap = new Map();
      for (const o of detailOpts) {
        const t = o.option_value + (o.in_stock ? '' : '  — หมด');
        optionsMap.set(t, o);
      }
      const row = document.createElement('div');
      row.style.display = 'flex';
      row.style.alignItems = 'center';
      row.style.justifyContent = 'space-between';
      row.style.gap = '10px';
      row.innerHTML = `
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;flex:1">
          <input type="checkbox" ${addon.in_stock === false ? 'disabled' : ''} />
          <span class="text-body">${esc(addon.name)}</span>
        </label>
        <span class="text-body-bold" data-role="aprice"></span>
        ${optionsMap.size ? `<select class="select" style="width:170px;height:34px">${Array.from(optionsMap.keys()).map((k) => `<option value="${esc(k)}">${esc(k)}</option>`).join('')}</select>` : ''}
      `;
      const chk = row.querySelector('input');
      const sel = row.querySelector('select');
      const priceSpan = row.querySelector('[data-role="aprice"]');
      chk.addEventListener('change', updateBundleTotal);
      if (sel) sel.addEventListener('change', updateBundleTotal);
      addonRows.push({ addon, chk, sel, optionsMap, priceEl: priceSpan });
      listEl.appendChild(row);
    }

    bundleBtn.addEventListener('click', async () => {
      if (!state.logged_in) {
        router.show('login', { info_message: 'กรุณาเข้าสู่ระบบก่อนเพิ่มชุดสินค้าลงตะกร้า' });
        return;
      }
      const selected = addonRows.filter((r) => r.chk.checked);
      if (!selected.length) return;
      const opt = currentOption();
      const addonIds = selected.map((r) => r.addon.id);
      const addonOptions = {};
      for (const r of selected) {
        if (r.sel && r.optionsMap.has(r.sel.value)) {
          addonOptions[r.addon.id] = r.optionsMap.get(r.sel.value).id;
        }
      }
      try {
        const res = await api.post('/api/cart/items-with-addons', {
          product_id: product.id,
          addon_ids: addonIds,
          option_id: opt ? opt.id : null,
          qty,
          addon_options: addonOptions,
        });
        await router.refresh_shell();
        bundleMsg.textContent = '';
        showToast(`เพิ่มชุดสินค้าลงตะกร้าแล้ว (ในตะกร้ามี ${Number(res.cart_count || 0).toLocaleString()} ชิ้น)`, 'success');
      } catch (err) {
        const em = err.message || 'เพิ่มชุดสินค้าไม่สำเร็จ';
        bundleMsg.className = 'text-small text-danger';
        bundleMsg.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
    });
  }

  // Description card
  const descCard = document.createElement('div');
  descCard.className = 'card';
  descCard.style.padding = '14px 20px';
  descCard.style.marginBottom = '14px';
  descCard.innerHTML = `
    <div style="background:var(--badge-info-bg);color:var(--badge-info-fg);border-radius:8px;padding:6px 12px;margin-bottom:8px" class="text-h3">รายละเอียดสินค้า</div>
    <div class="text-body" style="white-space:pre-line">${esc(product.description || 'ไม่มีรายละเอียดเพิ่มเติม')}</div>
  `;
  wrap.appendChild(descCard);

  // Reviews card
  const revCard = document.createElement('div');
  revCard.className = 'card';
  revCard.style.padding = '14px 20px';
  revCard.innerHTML = `
    <div style="background:#FCE7F3;color:#9D174D;border-radius:8px;padding:6px 12px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
      <div style="display:flex;align-items:center;gap:12px">
        <span class="text-h3">รีวิวจากลูกค้าจริง</span>
        <span data-role="rev-stars"></span>
      </div>
      ${product.reviewable_order_id ? `<button type="button" class="btn btn-primary btn-sm" data-role="write-rev-btn">⭐ เขียนรีวิวสินค้า</button>` : ''}
    </div>
    <div data-role="rev-list" style="display:flex;flex-direction:column;gap:8px"></div>
    <div style="margin-top:8px">
      <button type="button" class="btn btn-outline btn-sm hidden" data-role="rev-more">ดูรีวิวเพิ่มเติม</button>
    </div>
    <div class="text-small text-danger" data-role="rev-err"></div>
  `;
  revCard.querySelector('[data-role="rev-stars"]').appendChild(
    createRatingStars({ value: product.review_avg || 0, count: product.review_count || 0, size: 16 }).el
  );
  const writeRevBtn = revCard.querySelector('[data-role="write-rev-btn"]');
  if (writeRevBtn && product.reviewable_order_id) {
    writeRevBtn.addEventListener('click', () => {
      router.show('write_review', {
        product_id: product.id,
        order_id: product.reviewable_order_id,
      });
    });
  }
  wrap.appendChild(revCard);

  const revList = revCard.querySelector('[data-role="rev-list"]');
  const revMoreBtn = revCard.querySelector('[data-role="rev-more"]');
  const revErr = revCard.querySelector('[data-role="rev-err"]');

  async function loadReviews() {
    const nextP = reviewPage + 1;
    try {
      const res = await api.get(`/api/products/${product.id}/reviews`, { page: nextP, page_size: REVIEW_PAGE_SIZE });
      if (res.total === 0 && nextP === 1) {
        revList.innerHTML = `<div class="text-body text-muted" style="padding:8px 0">ยังไม่มีรีวิวสำหรับสินค้านี้</div>`;
      }
      for (const item of res.items || []) {
        const row = document.createElement('div');
        row.className = 'card-alt';
        row.style.padding = '10px 14px';

        const optLabel = String(item.option_label || '').trim();
        const showOpt = optLabel && optLabel !== '-';

        row.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span class="text-small-bold">${esc(item.reviewer_name || 'ผู้ใช้')}</span>
              <span data-role="item-stars"></span>
            </div>
            <span class="text-tiny text-muted">${esc(formatDateTime(item.created_at))}</span>
          </div>
          ${showOpt ? `<div class="text-tiny text-muted" style="margin-top:3px">ตัวเลือกที่สั่ง: <strong style="color:var(--color-text)">${esc(optLabel)}</strong></div>` : ''}
          ${item.comment ? `<div class="text-body" style="margin-top:5px;white-space:pre-line">${esc(item.comment)}</div>` : ''}
          <div class="review-display-media hidden" data-role="item-media"></div>
        `;
        row.querySelector('[data-role="item-stars"]').appendChild(
          createRatingStars({ value: item.rating, size: 13, showValue: false }).el
        );

        const mediaItems = Array.isArray(item.media) ? item.media : [];
        if (mediaItems.length > 0) {
          const mediaBox = row.querySelector('[data-role="item-media"]');
          mediaBox.classList.remove('hidden');
          for (const m of mediaItems) {
            const url = resolveAssetUrl(m.file_path);
            if (m.kind === 'video') {
              const vid = document.createElement('video');
              vid.className = 'review-display-video';
              vid.src = url;
              vid.controls = true;
              vid.preload = 'metadata';
              vid.playsInline = true;
              mediaBox.appendChild(vid);
            } else {
              const img = document.createElement('img');
              img.className = 'review-display-img';
              img.src = url;
              img.alt = 'รูปรีวิวสินค้า';
              img.loading = 'lazy';
              img.addEventListener('click', () => openReviewImageLightbox(url, item.reviewer_name || 'ลูกค้า'));
              mediaBox.appendChild(img);
            }
          }
        }

        revList.appendChild(row);
      }
      reviewPage = res.page;
      reviewPages = res.pages;
      revMoreBtn.classList.toggle('hidden', reviewPage >= reviewPages);
    } catch (err) {
      revErr.textContent = err.message || 'โหลดรีวิวไม่สำเร็จ';
    }
  }

  revMoreBtn.addEventListener('click', loadReviews);
  refreshOption();
  await loadReviews();

  return () => {
    timers.forEach((t) => clearInterval(t));
  };
}
