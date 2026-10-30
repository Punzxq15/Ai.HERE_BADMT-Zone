// web/js/pages/buyer/home.js — หน้าแรก (Storefront: แบนเนอร์ 1-10 รูป, คูปองทีละ 3 ใบสลับชุด+โมดัล, Flash Sale เลื่อนอัตโนมัติ, หมวดหมู่, แบรนด์, สินค้ายอดนิยม 5 คอลัมน์ 15 ชิ้น, เพิ่งดูล่าสุด, ฟุตเตอร์)
import { api, esc, formatDateThai, formatPrice, resolveAssetUrl } from '../../api.js';
import { state } from '../../state.js';
import { createProductCard, CARD_WIDTH } from '../../components/product_card.js';
import { toggleWishlist } from '../../components/buyer_common.js';
import { openModal, notifyError, notifySuccess } from '../../components/dialogs.js';
import { iconSvg } from '../../components/icons.js';

const FIRE_COLORS = ['#E63946', '#FF4500', '#DC2626', '#EA580C', '#FF2A2A'];
export const RECOMMEND_COUNT = 15; // 3 แถว × 5 คอลัมน์

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  let currentShopName = state.getShopName ? state.getShopName() : ((state.shop && state.shop.shop_name) || 'AI.HERE BADᴍᴛ-Zone');

  wrap.innerHTML = `
    <!-- แบนเนอร์สไลด์โชว์ -->
    <div class="card" data-role="banner-card" style="background:var(--color-secondary);border:2px solid var(--color-primary);border-radius:16px;padding:20px 26px;display:grid;grid-template-columns:3fr 2fr;gap:20px;align-items:center">
      <div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
          <span class="pill" data-role="banner-tag" style="background:var(--color-primary);color:#111318;border-radius:6px;padding:0 10px">
            ${iconSvg('racket', 14, '#111318')} <span data-role="banner-tag-text" style="margin-left:4px">${esc(currentShopName)} OFFICIAL</span>
          </span>
          <span class="text-small-bold" data-role="banner-counter" style="color:#FDE68A">แบนเนอร์ 1/1</span>
        </div>
        <div class="text-h1" data-role="banner-title" style="color:#FFFFFF;margin-bottom:4px">${esc(currentShopName)}</div>
        <div class="text-body" data-role="banner-sub" style="color:#E2E8F0;margin-bottom:14px">ไม้แบด ลูกแบด รองเท้า และอุปกรณ์ครบ จากแบรนด์ชั้นนำของแท้ 100%</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <button type="button" class="btn btn-primary btn-md" data-role="btn-shop">${iconSvg('cart', 16, '#111318')} <span>เลือกซื้อสินค้า</span></button>
          <button type="button" class="btn btn-danger btn-md" data-role="btn-finder">${iconSvg('target', 16, '#FFFFFF')} <span>ตัวช่วยเลือกไม้</span></button>
          <button type="button" class="btn btn-info btn-md" data-role="btn-compare">${iconSvg('compare', 16, '#FFFFFF')} <span>เปรียบเทียบ 2–5 รุ่น</span></button>
        </div>
        <div data-role="banner-ctrl" style="display:flex;gap:8px;margin-top:12px">
          <button type="button" class="btn btn-sm" data-role="banner-prev" style="background:#252A34;color:#FFFFFF;border:1px solid #FFB703">‹ แบนเนอร์ก่อนหน้า</button>
          <button type="button" class="btn btn-sm" data-role="banner-next" style="background:#252A34;color:#FFFFFF;border:1px solid #FFB703">แบนเนอร์ถัดไป ›</button>
        </div>
      </div>
      <div style="display:flex;justify-content:flex-end">
        <img data-role="banner-img" src="/assets/icons/no_image.svg" alt="banner" style="width:260px;height:150px;object-fit:cover;border-radius:10px;background:#252A34" />
      </div>
    </div>

    <div class="text-small text-danger" data-role="error" style="margin-top:6px"></div>

    <!-- คูปองส่วนลด & โปรโมชันประจำร้าน (แสดงทีละ 3 ใบ สลับชุดช้าๆ) -->
    <div class="card" data-role="coupon-section" style="margin-top:12px;padding:12px 16px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:6px">
        <div class="text-h3 text-danger" style="display:flex;align-items:center;gap:6px">
          ${iconSvg('coupon', 20, 'var(--color-danger)')} <span>คูปองส่วนลด & โปรโมชันประจำร้าน</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px">
          <span class="text-small-bold text-muted" data-role="coupon-page-lbl"></span>
          <button type="button" class="btn btn-info btn-sm" data-role="my-coupons-btn">คูปองของฉันที่เก็บไว้</button>
          <button type="button" class="btn btn-danger btn-sm" data-role="all-coupons-btn">ดูคูปองที่มีทั้งหมดของร้าน</button>
        </div>
      </div>
      <div data-role="coupon-rule-bar" style="margin-bottom:6px"></div>
      <div data-role="coupon-cards-holder" style="display:grid;gap:12px"></div>
    </div>

    <!-- T05: FLASH SALE เลื่อนขวา -> ซ้ายอัตโนมัติ -->
    <div data-role="flash-box" class="hidden" style="margin-top:14px;background:var(--badge-danger-bg);border:2px solid var(--color-danger);border-radius:14px;padding:4px">
      <div style="background:var(--color-danger);border-radius:10px;padding:8px 14px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div class="text-h3" style="color:#FFFFFF;display:flex;align-items:center;gap:8px">
          ${iconSvg('flash', 20, '#FFB703')} <span>FLASH SALE — สินค้าลดราคาทั้งหมด (ชี้เมาส์เพื่อหยุดดู)</span>
        </div>
        <button type="button" class="btn btn-primary btn-sm" data-role="flash-all-btn">ดูสินค้าลดราคาทั้งหมด ›</button>
      </div>
      <div data-role="flash-viewport" style="overflow:hidden;padding:4px 8px 10px;position:relative">
        <div data-role="flash-track" style="display:flex;gap:12px;will-change:transform"></div>
      </div>
    </div>

    <!-- หมวดหมู่สินค้าและแบรนด์ชั้นนำ -->
    <div style="margin-top:18px;margin-bottom:8px;display:flex;align-items:center;gap:8px" class="text-h2">
      ${iconSvg('category', 20, 'var(--color-danger)')} <span>หมวดหมู่สินค้าและแบรนด์ชั้นนำ</span>
    </div>
    <div data-role="category-grid" style="display:flex;flex-wrap:wrap;gap:12px"></div>
    <div data-role="brand-section" style="margin-top:10px"></div>

    <!-- สินค้าแนะนำยอดนิยม (แถวละ 5 ชิ้นเต็มความกว้าง ประมาณ 3 แถว = 15 ชิ้น) -->
    <div style="margin-top:20px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      <div class="text-h2" data-role="popular-title" style="color:#E63946;display:flex;align-items:center;gap:8px">
        ${iconSvg('fire', 24, '#E63946')} <span>สินค้าแนะนำยอดนิยม</span>
      </div>
      <div style="display:flex;gap:8px">
        <button type="button" class="btn btn-outline btn-sm" data-role="reshuffle-btn">${iconSvg('refresh', 15)} <span>สุ่มสินค้าใหม่</span></button>
        <button type="button" class="btn btn-ghost btn-sm" data-role="view-all-btn">ดูสินค้าทั้งหมด ›</button>
      </div>
    </div>
    <div class="wrap-grid wrap-grid--cols-5" data-role="recommend-grid"></div>

    <!-- สินค้าที่คุณเพิ่งดูล่าสุด -->
    <div data-role="recent-box" class="hidden" style="margin-top:20px">
      <div class="text-h2" style="margin-bottom:8px;display:flex;align-items:center;gap:8px">
        ${iconSvg('eye', 20, 'var(--color-danger)')} <span>สินค้าที่คุณเพิ่งดูล่าสุด</span>
      </div>
      <div class="wrap-grid" data-role="recent-grid"></div>
    </div>

    <!-- ฟุตเตอร์เกี่ยวกับร้าน -->
    <div data-role="footer-box" style="margin-top:24px;background:var(--color-secondary);border:2px solid var(--color-primary);border-radius:14px;padding:16px 22px;color:#FFFFFF"></div>
  `;

  const timers = [];
  let banners = [];
  let bannerIdx = 0;
  let publicCoupons = [];
  let couponRules = [];
  let couponPageIdx = 0;
  let couponPaused = false;
  let flashPaused = false;
  let flashOffset = 0;
  let flashSetWidth = 0;

  const errEl = wrap.querySelector('[data-role="error"]');
  const bannerCounter = wrap.querySelector('[data-role="banner-counter"]');
  const bannerTitle = wrap.querySelector('[data-role="banner-title"]');
  const bannerSub = wrap.querySelector('[data-role="banner-sub"]');
  const bannerImg = wrap.querySelector('[data-role="banner-img"]');
  const bannerCtrl = wrap.querySelector('[data-role="banner-ctrl"]');
  const bannerTagText = wrap.querySelector('[data-role="banner-tag-text"]');

  wrap.querySelector('[data-role="btn-shop"]').addEventListener('click', () => router.show('category'));
  wrap.querySelector('[data-role="btn-finder"]').addEventListener('click', () => router.show('racket_finder'));
  wrap.querySelector('[data-role="btn-compare"]').addEventListener('click', () => router.show('compare'));
  wrap.querySelector('[data-role="flash-all-btn"]').addEventListener('click', () => router.show('category', { on_sale: true }));
  wrap.querySelector('[data-role="view-all-btn"]').addEventListener('click', () => router.show('category'));

  function paintBanner() {
    const total = banners.length;
    if (total <= 1) {
      bannerCtrl.classList.add('hidden');
      bannerCounter.classList.add('hidden');
    } else {
      bannerCtrl.classList.remove('hidden');
      bannerCounter.classList.remove('hidden');
    }
    if (!total) {
      bannerTitle.textContent = currentShopName;
      bannerSub.textContent = 'ไม้แบด ลูกแบด รองเท้า และอุปกรณ์ครบ จากแบรนด์ชั้นนำ';
      bannerImg.src = '/assets/icons/no_image.svg';
      return;
    }
    const b = banners[bannerIdx % total];
    bannerTitle.textContent = b.title || currentShopName;
    bannerSub.textContent = b.subtitle || 'โปรโมชันพิเศษสำหรับคนรักแบดมินตัน';
    bannerCounter.textContent = `แบนเนอร์ ${(bannerIdx % total) + 1}/${total}`;
    bannerImg.src = resolveAssetUrl(b.image_path);
  }

  wrap.querySelector('[data-role="banner-prev"]').addEventListener('click', () => {
    if (!banners.length) return;
    bannerIdx = (bannerIdx - 1 + banners.length) % banners.length;
    paintBanner();
  });
  wrap.querySelector('[data-role="banner-next"]').addEventListener('click', () => {
    if (!banners.length) return;
    bannerIdx = (bannerIdx + 1) % banners.length;
    paintBanner();
  });

  // Fire title animation
  let fireIdx = 0;
  const popTitle = wrap.querySelector('[data-role="popular-title"]');
  timers.push(setInterval(() => {
    fireIdx = (fireIdx + 1) % FIRE_COLORS.length;
    popTitle.style.color = FIRE_COLORS[fireIdx];
  }, 550));

  // Coupons section
  const couponSec = wrap.querySelector('[data-role="coupon-section"]');
  const couponPageLbl = wrap.querySelector('[data-role="coupon-page-lbl"]');
  const couponRuleBar = wrap.querySelector('[data-role="coupon-rule-bar"]');
  const couponHolder = wrap.querySelector('[data-role="coupon-cards-holder"]');

  couponSec.addEventListener('mouseenter', () => { couponPaused = true; });
  couponSec.addEventListener('mouseleave', () => { couponPaused = false; });

  function paintCouponSubset() {
    couponHolder.innerHTML = '';
    if (!publicCoupons.length) {
      couponHolder.style.gridTemplateColumns = '1fr';
      couponHolder.innerHTML = `<div class="text-small text-muted" style="padding:8px 0">ขณะนี้ยังไม่มีคูปองสาธารณะที่เปิดให้กดรับ — สามารถกดปุ่ม 'คูปองของฉันที่เก็บไว้' เพื่อตรวจสอบคูปองในบัญชีของคุณได้</div>`;
      couponPageLbl.textContent = '';
      return;
    }
    const perView = 3;
    const totalPages = Math.max(1, Math.ceil(publicCoupons.length / perView));
    couponPageIdx = couponPageIdx % totalPages;
    const subset = publicCoupons.slice(couponPageIdx * perView, (couponPageIdx + 1) * perView);
    couponPageLbl.textContent = totalPages > 1 ? `ชุดคูปอง ${couponPageIdx + 1}/${totalPages}` : `ทั้งหมด ${publicCoupons.length} คูปอง`;

    const cols = Math.max(1, subset.length);
    couponHolder.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

    for (const cp of subset) {
      const catKind = cp.coupon_category === 'free_shipping' ? 'info' : (cp.coupon_category === 'percent' ? 'danger' : 'warning');
      const extraParts = [`ขั้นต่ำ ${formatPrice(cp.min_order || 0)}`];
      if (cp.expires_at) extraParts.push(`ถึง ${formatDateThai(cp.expires_at)}`);
      if (cp.claim_start_time && cp.claim_end_time) extraParts.push(`รับได้ ${cp.claim_start_time}-${cp.claim_end_time} น.`);
      if (cp.daily_reset_12) extraParts.push('รีโค้ดทุก 12:00 น.');

      const claimed = Boolean(cp.is_claimed);
      const used = Boolean(cp.is_used);
      const canClaimNow = cp.can_claim_now !== false;
      let btnText = 'เก็บคูปอง';
      let btnDisabled = false;
      let btnKind = 'btn-primary';
      if (claimed && !used) {
        btnText = '✓ เก็บโค้ดแล้ว';
        btnDisabled = true;
        btnKind = 'btn-success';
      } else if (used && canClaimNow) {
        btnText = 'กดรับโค้ดใหม่';
        btnDisabled = false;
        btnKind = 'btn-primary';
      } else if (!canClaimNow) {
        btnText = 'นอกเวลารับโค้ด';
        btnDisabled = true;
        btnKind = 'btn-outline';
      }

      const box = document.createElement('div');
      box.className = 'card-alt';
      box.style.border = '1px solid var(--color-primary)';
      box.style.padding = '10px 12px';
      box.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <span class="pill pill-${catKind}">${esc(cp.category_label || 'คูปองส่วนลด')}</span>
          <span class="text-tiny ${cp.is_claimed ? 'text-success' : 'text-muted'}">${esc(cp.status_text || 'ใช้ได้')}</span>
        </div>
        <div class="text-body-bold text-danger">${esc(cp.code)} · ${esc(cp.description || '')}</div>
        <div class="text-tiny text-muted" style="margin:2px 0 8px">${esc(extraParts.join(' · '))}</div>
        <div style="display:flex;justify-content:flex-end">
          <button type="button" class="btn ${btnKind} btn-sm" ${btnDisabled ? 'disabled' : ''}>${esc(btnText)}</button>
        </div>
      `;
      const btn = box.querySelector('button');
      btn.addEventListener('click', () => claimCoupon(cp.code));
      couponHolder.appendChild(box);
    }
  }

  async function reloadCoupons() {
    try {
      publicCoupons = await api.get('/api/coupons/public');
      couponRules = await api.get('/api/coupons/rules');
    } catch (e) {
      publicCoupons = [];
      couponRules = [];
    }
    if (couponRules && couponRules.length) {
      const r0 = couponRules[0];
      const discTxt = r0.discount_type === 'percent' ? `${r0.discount_value}%` : formatPrice(r0.discount_value);
      couponRuleBar.innerHTML = `<span class="pill pill-primary" style="background:var(--color-primary);color:#111318">${iconSvg('gift', 14, '#111318')} <span style="margin-left:4px">${esc(r0.name)}: ซื้อครบ ${esc(formatPrice(r0.min_order_trigger))} รับคูปองลด ${esc(discTxt)} สำหรับออเดอร์ถัดไปอัตโนมัติ!</span></span>`;
    } else {
      couponRuleBar.innerHTML = '';
    }
    paintCouponSubset();
  }

  async function claimCoupon(code, onDone = null) {
    if (!state.logged_in) {
      router.show('login', { info_message: `กรุณาเข้าสู่ระบบเพื่อเก็บคูปอง ${code}` });
      return;
    }
    try {
      await api.post('/api/coupons/claim', { code });
      await reloadCoupons();
      notifySuccess(`เก็บคูปอง ${code} เรียบร้อยแล้ว`, { clearInlineEl: errEl });
      if (onDone) onDone();
    } catch (err) {
      notifyError(err.message || 'เก็บคูปองไม่สำเร็จ', { inlineEl: errEl });
    }
  }

  wrap.querySelector('[data-role="my-coupons-btn"]').addEventListener('click', () => openCouponsDialog('my'));
  wrap.querySelector('[data-role="all-coupons-btn"]').addEventListener('click', () => openCouponsDialog('all'));

  function openCouponsDialog(initialTab = 'all') {
    if (initialTab === 'my' && !state.logged_in) {
      router.show('login', { info_message: 'กรุณาเข้าสู่ระบบเพื่อดูคูปองของฉันที่เก็บไว้' });
      return;
    }
    let curMode = initialTab;
    let curCat = 'all';

    openModal({
      title: `ศูนย์รวมคูปองส่วนลด — ${currentShopName}`,
      width: 760,
      render(card, close) {
        card.style.padding = '0';
        card.style.overflow = 'hidden';
        card.innerHTML = `
          <div style="background:var(--color-secondary);padding:14px 22px;display:flex;justify-content:space-between;align-items:center">
            <div>
              <div class="text-h2 text-primary">ศูนย์คูปองส่วนลด & คูปองของฉัน</div>
              <div class="text-small" style="color:#E2E8F0">เลือกดูคูปองทั้งหมดของร้าน ${esc(currentShopName)} หรือคูปองที่คุณเก็บไว้ พร้อมกรองตามหมวดหมู่คูปอง</div>
            </div>
            <button type="button" class="btn btn-outline btn-sm" data-role="close" style="color:#FFFFFF;border-color:#475569">ปิด</button>
          </div>
          <div style="padding:14px 20px">
            <div style="display:flex;gap:8px;margin-bottom:8px" data-role="mode-bar">
              <button type="button" class="btn btn-md" data-mode="all">คูปองทั้งหมดที่ร้านมี</button>
              <button type="button" class="btn btn-md" data-mode="my">คูปองของฉัน (ที่เก็บไว้ทั้งหมด)</button>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px" data-role="cat-bar">
              <button type="button" class="btn btn-sm" data-cat="all">ทั้งหมด</button>
              <button type="button" class="btn btn-sm" data-cat="free_shipping">คูปองส่วนลดค่าส่ง</button>
              <button type="button" class="btn btn-sm" data-cat="percent">คูปองส่วนลดเป็น %</button>
              <button type="button" class="btn btn-sm" data-cat="fixed">คูปองส่วนลดเป็น บาท</button>
              <button type="button" class="btn btn-sm" data-cat="other">และอื่นๆ</button>
            </div>
            <div class="text-small-bold text-danger" data-role="dlg-msg" style="min-height:18px"></div>
            <div data-role="list" style="max-height:360px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;margin-top:6px"></div>
          </div>
        `;

        const listEl = card.querySelector('[data-role="list"]');
        const msgEl = card.querySelector('[data-role="dlg-msg"]');

        async function refreshList() {
          card.querySelectorAll('[data-mode]').forEach((b) => {
            b.className = `btn btn-md ${b.dataset.mode === curMode ? 'btn-primary' : 'btn-outline'}`;
          });
          card.querySelectorAll('[data-cat]').forEach((b) => {
            b.className = `btn btn-sm ${b.dataset.cat === curCat ? 'btn-danger' : 'btn-outline'}`;
          });
          listEl.innerHTML = '';
          msgEl.textContent = '';

          if (curMode === 'my' && !state.logged_in) {
            listEl.innerHTML = `<div class="text-body-bold text-muted" style="text-align:center;padding:40px">กรุณาเข้าสู่ระบบเพื่อดูคูปองที่คุณเก็บไว้</div>`;
            return;
          }

          let items = [];
          try {
            if (curMode === 'my') {
              items = await api.get('/api/coupons/my', { category: curCat });
            } else {
              items = await api.get('/api/coupons/shop', { category: curCat, include_expired: true });
            }
          } catch (err) {
            notifyError(err.message || 'โหลดคูปองไม่สำเร็จ', { inlineEl: msgEl });
            return;
          }

          if (!items || !items.length) {
            listEl.innerHTML = `<div class="text-body-bold text-muted" style="text-align:center;padding:40px">ไม่พบคูปองในหมวดหมู่นี้</div>`;
            return;
          }

          for (const cp of items) {
            const catKind = cp.coupon_category === 'free_shipping' ? 'info' : (cp.coupon_category === 'percent' ? 'danger' : 'warning');
            const statusTxt = cp.status_text || 'ใช้ได้';
            const stKind = statusTxt.includes('ใช้ได้') ? 'success' : (statusTxt.includes('หมด') ? 'danger' : 'muted');
            const meta = [`ยอดสั่งซื้อขั้นต่ำ ${formatPrice(cp.min_order || 0)}`];
            if (cp.expires_at) meta.push(`หมดอายุ ${formatDateThai(cp.expires_at)}`);
            if (cp.remaining != null) meta.push(`คงเหลือ ${cp.remaining} สิทธิ์`);

            const claimed = Boolean(cp.is_claimed);
            const used = Boolean(cp.is_used);
            const expired = Boolean(cp.is_expired);
            const canClaimNow = cp.can_claim_now !== false;
            const full = cp.remaining != null && cp.remaining <= 0;

            let bTxt = 'เก็บคูปอง';
            let bDis = false;
            let bKind = 'btn-primary';
            if (expired) { bTxt = 'หมดอายุแล้ว'; bDis = true; bKind = 'btn-outline'; }
            else if (full) { bTxt = 'สิทธิ์เต็ม'; bDis = true; bKind = 'btn-outline'; }
            else if (claimed && !used) { bTxt = '✓ เก็บแล้ว'; bDis = true; bKind = 'btn-success'; }
            else if (used && canClaimNow && !cp.is_personal_reward) { bTxt = 'กดรับโค้ดใหม่'; bDis = false; bKind = 'btn-primary'; }
            else if (used) { bTxt = 'ใช้แล้ว'; bDis = true; bKind = 'btn-outline'; }
            else if (!canClaimNow) { bTxt = 'นอกเวลารับโค้ด'; bDis = true; bKind = 'btn-outline'; }

            const row = document.createElement('div');
            row.className = 'card';
            row.style.padding = '12px 16px';
            row.style.display = 'flex';
            row.style.justifyContent = 'space-between';
            row.style.alignItems = 'center';
            row.style.gap = '12px';
            row.innerHTML = `
              <div>
                <div style="display:flex;gap:6px;margin-bottom:4px">
                  <span class="pill pill-${catKind}">${esc(cp.category_label || 'คูปอง')}</span>
                  <span class="pill pill-${stKind}">${esc(statusTxt)}</span>
                </div>
                <div class="text-h3 text-danger">${esc(cp.code)}  —  ${esc(cp.description || '')}</div>
                <div class="text-small text-muted">${esc(meta.join(' · '))}</div>
              </div>
              <button type="button" class="btn ${bKind} btn-md" style="min-width:130px" ${bDis ? 'disabled' : ''}>${esc(bTxt)}</button>
            `;
            row.querySelector('button').addEventListener('click', async () => {
              if (!state.logged_in) {
                close();
                router.show('login', { info_message: `กรุณาเข้าสู่ระบบเพื่อเก็บคูปอง ${cp.code}` });
                return;
              }
              try {
                await api.post('/api/coupons/claim', { code: cp.code });
                notifySuccess(`เก็บคูปอง ${cp.code} เรียบร้อยแล้ว`, { clearInlineEl: msgEl });
                await reloadCoupons();
                await refreshList();
              } catch (err) {
                notifyError(err.message || 'เก็บคูปองไม่สำเร็จ', { inlineEl: msgEl });
              }
            });
            listEl.appendChild(row);
          }
        }

        card.querySelectorAll('[data-mode]').forEach((b) => {
          b.addEventListener('click', () => { curMode = b.dataset.mode; refreshList(); });
        });
        card.querySelectorAll('[data-cat]').forEach((b) => {
          b.addEventListener('click', () => { curCat = b.dataset.cat; refreshList(); });
        });
        card.querySelector('[data-role="close"]').addEventListener('click', () => close());
        refreshList();
      },
    });
  }

  // Flash sale auto-scroll
  const flashBox = wrap.querySelector('[data-role="flash-box"]');
  const flashViewport = wrap.querySelector('[data-role="flash-viewport"]');
  const flashTrack = wrap.querySelector('[data-role="flash-track"]');

  flashBox.addEventListener('mouseenter', () => { flashPaused = true; });
  flashBox.addEventListener('mouseleave', () => { flashPaused = false; });

  function renderFlashSale(items = []) {
    flashTrack.innerHTML = '';
    if (!items.length) {
      flashBox.classList.add('hidden');
      return;
    }
    flashBox.classList.remove('hidden');
    const gap = 12;
    flashSetWidth = items.length * (CARD_WIDTH + gap);
    const needLoop = items.length >= 4;
    const displayList = needLoop ? [...items, ...items] : items;
    for (const p of displayList) {
      const card = createProductCard(p, {
        onOpen: (pid) => router.show('product_detail', { product_id: pid }),
        onWishlist: (pid) => toggleWishlist(pid),
      });
      card.style.flexShrink = '0';
      flashTrack.appendChild(card);
    }
    flashOffset = 0;
    if (needLoop) {
      timers.push(setInterval(() => {
        if (flashPaused || !document.body.contains(flashTrack)) return;
        const vw = flashViewport.clientWidth || 800;
        if (flashSetWidth <= vw) {
          flashTrack.style.transform = 'translateX(0px)';
          return;
        }
        flashOffset += 1.6;
        if (flashOffset >= flashSetWidth) flashOffset -= flashSetWidth;
        flashTrack.style.transform = `translateX(${-Math.round(flashOffset)}px)`;
      }, 35));
    }
  }

  function renderCategoriesAndBrands(categories = [], brands = []) {
    const catGrid = wrap.querySelector('[data-role="category-grid"]');
    catGrid.innerHTML = '';
    for (const cat of categories) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.style.width = '195px';
      btn.style.height = '58px';
      btn.style.borderRadius = '14px';
      btn.style.border = '3px solid #141619';
      btn.style.background = 'var(--color-primary)';
      btn.style.color = '#111318';
      btn.style.display = 'flex';
      btn.style.alignItems = 'center';
      btn.style.gap = '8px';
      btn.style.padding = '6px 10px';
      btn.style.cursor = 'pointer';
      btn.innerHTML = `
        ${cat.image_path ? `<img src="${esc(resolveAssetUrl(cat.image_path))}" alt="${esc(cat.name)}" style="width:36px;height:36px;border-radius:6px;object-fit:cover" />` : iconSvg('racket', 22, '#111318')}
        <span class="text-body-bold" style="text-align:left">${esc(cat.name)}</span>
      `;
      btn.addEventListener('click', () => router.show('category', { category_id: cat.id }));
      catGrid.appendChild(btn);
    }

    const brandSec = wrap.querySelector('[data-role="brand-section"]');
    brandSec.innerHTML = '';
    if (brands && brands.length) {
      brandSec.innerHTML = `
        <div class="text-body-bold" style="margin:6px 0;display:flex;align-items:center;gap:6px">
          ${iconSvg('brand', 16, 'var(--color-danger)')} <span>แบรนด์ชั้นนำ (คลิกเลือกดูสินค้าตามแบรนด์):</span>
        </div>
        <div data-role="brand-wrap" style="display:flex;flex-wrap:wrap;gap:10px"></div>
      `;
      const bw = brandSec.querySelector('[data-role="brand-wrap"]');
      for (const br of brands.slice(0, 10)) {
        const bcard = document.createElement('button');
        bcard.type = 'button';
        bcard.className = 'card';
        bcard.style.border = '2px solid var(--color-danger)';
        bcard.style.padding = '6px 12px';
        bcard.style.display = 'inline-flex';
        bcard.style.alignItems = 'center';
        bcard.style.gap = '8px';
        bcard.style.cursor = 'pointer';
        bcard.innerHTML = `
          ${br.logo_path ? `<img src="${esc(resolveAssetUrl(br.logo_path))}" alt="${esc(br.name)}" style="width:38px;height:38px;border-radius:6px;object-fit:cover" />` : `<span class="pill pill-danger">${esc((br.name || '').slice(0, 4).toUpperCase())}</span>`}
          <span class="text-body-bold">${esc(br.name)}</span>
        `;
        bcard.addEventListener('click', () => router.show('category', { brand_id: br.id }));
        bw.appendChild(bcard);
      }
    }
  }

  function renderProductCardsInto(gridEl, items = []) {
    gridEl.innerHTML = '';
    for (const p of items) {
      gridEl.appendChild(createProductCard(p, {
        onOpen: (pid) => router.show('product_detail', { product_id: pid }),
        onWishlist: (pid) => toggleWishlist(pid),
      }));
    }
  }

  const recGrid = wrap.querySelector('[data-role="recommend-grid"]');
  wrap.querySelector('[data-role="reshuffle-btn"]').addEventListener('click', async () => {
    try {
      const res = await api.get('/api/products', { sort: 'popular', page_size: 48 });
      const list = [...(res.items || [])].sort(() => Math.random() - 0.5).slice(0, RECOMMEND_COUNT);
      renderProductCardsInto(recGrid, list);
    } catch (e) {}
  });

  function renderFooter(shop = {}, contact = {}) {
    const fb = wrap.querySelector('[data-role="footer-box"]');
    const sname = (shop.shop_name && String(shop.shop_name).trim())
      ? String(shop.shop_name)
      : ((contact.shop_name && String(contact.shop_name).trim()) ? String(contact.shop_name) : 'AI.HERE BADᴍᴛ-Zone');
    const addr = shop.shop_address || contact.address || '-';
    const hours = shop.shop_hours || contact.open_hours || '-';
    const socials = [
      ['Facebook: ' + (contact.facebook_name || sname), contact.facebook_url || '', 'btn-info'],
      ['Instagram: ' + (contact.instagram_name || '@badmintonpro.th'), contact.instagram_url || '', 'btn-danger'],
      ['TikTok: ' + (contact.tiktok_name || '@badmintonpro.th'), contact.tiktok_url || '', 'btn-secondary'],
    ];

    fb.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:6px">
        <div class="text-h3 text-primary" style="display:flex;align-items:center;gap:8px">
          ${iconSvg('store', 20, '#FFB703')} <span>เกี่ยวกับร้าน ${esc(sname)}</span>
        </div>
      </div>
      <div class="text-body-bold" style="color:#FDE68A;margin-bottom:4px">ที่ตั้งหน้าร้าน: ${esc(addr)}   |   เวลาทำการ: ${esc(hours)}</div>
      <div class="text-small-bold" style="color:#FFFFFF;margin-bottom:10px">โทร: ${esc(contact.phone || '-')}   |   อีเมล: ${esc(contact.email || '-')}   |   LINE: ${esc(contact.line_id || '-')}</div>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        ${socials.filter(([, u]) => u && u.startsWith('https://')).map(([lbl, u, cls]) => `<a href="${esc(u)}" target="_blank" rel="noopener" class="btn ${cls} btn-sm">${esc(lbl)} ↗</a>`).join('')}
      </div>
    `;
  }

  // Initial load from /api/home
  try {
    const data = await api.get('/api/home');
    if (data.shop && data.shop.shop_name && String(data.shop.shop_name).trim()) {
      currentShopName = String(data.shop.shop_name);
      state.shop = { ...(state.shop || {}), ...data.shop };
      if (state.syncDocumentTitle) state.syncDocumentTitle();
    }
    bannerTagText.textContent = `${currentShopName} OFFICIAL`;
    banners = data.banners || [];
    bannerIdx = 0;
    paintBanner();
    if (banners.length > 1) {
      timers.push(setInterval(() => {
        bannerIdx = (bannerIdx + 1) % banners.length;
        paintBanner();
      }, 5000));
    }

    publicCoupons = data.public_coupons || [];
    couponRules = data.coupon_rules || [];
    await reloadCoupons();
    timers.push(setInterval(() => {
      if (!couponPaused && publicCoupons.length > 3) {
        couponPageIdx += 1;
        paintCouponSubset();
      }
    }, 9000));

    renderFlashSale(data.flash_sale || []);
    renderCategoriesAndBrands(data.categories || [], data.brands || []);

    const recItems = [...(data.best_sellers || []), ...(data.newest || [])];
    const seen = new Set();
    const uniqueRec = [];
    for (const it of recItems) {
      if (it && !seen.has(it.id)) {
        seen.add(it.id);
        uniqueRec.push(it);
      }
    }
    if (uniqueRec.length < RECOMMEND_COUNT) {
      try {
        const moreRes = await api.get('/api/products', { sort: 'popular', page_size: RECOMMEND_COUNT * 2 });
        for (const it of (moreRes && moreRes.items) || []) {
          if (it && !seen.has(it.id)) {
            seen.add(it.id);
            uniqueRec.push(it);
          }
          if (uniqueRec.length >= RECOMMEND_COUNT) break;
        }
      } catch (e) {}
    }
    renderProductCardsInto(recGrid, uniqueRec.slice(0, RECOMMEND_COUNT));

    const recent = data.recently_viewed || [];
    const recentBox = wrap.querySelector('[data-role="recent-box"]');
    const recentGrid = wrap.querySelector('[data-role="recent-grid"]');
    if (recent.length) {
      recentBox.classList.remove('hidden');
      renderProductCardsInto(recentGrid, recent);
    } else {
      recentBox.classList.add('hidden');
    }

    renderFooter(data.shop || {}, data.contact || {});
  } catch (err) {
    errEl.textContent = err.message || 'โหลดหน้าแรกไม่สำเร็จ';
  }

  return () => {
    timers.forEach((t) => clearInterval(t));
  };
}
