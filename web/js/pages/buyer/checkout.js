// web/js/pages/buyer/checkout.js — หน้ายืนยันคำสั่งซื้อและใส่โค้ดส่วนลด + โค้ดส่งฟรี (ตรงกับ ui/pages/buyer/checkout.py)
import { api, esc, formatPhone, formatPrice, resolveAssetUrl } from '../../api.js';
import { pageTitleHtml } from '../../components/buyer_common.js';
import { iconSvg } from '../../components/icons.js';
import { showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  let selectedAddressId = 0;
  let couponCode = '';
  let shippingCouponCode = '';
  let checkoutData = null;
  let busy = false;

  wrap.innerHTML = `
    ${pageTitleHtml('ยืนยันคำสั่งซื้อ', 'ตรวจที่อยู่จัดส่ง เลือกใช้คูปอง และตรวจสอบยอดชำระก่อนสั่งซื้อ')}
    <div style="display:grid;grid-template-columns:1fr 395px;gap:16px;align-items:start">
      <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <span class="text-h3">ที่อยู่จัดส่ง</span>
          <button type="button" class="btn btn-ghost btn-sm" data-role="manage-addr">จัดการที่อยู่ ›</button>
        </div>
        <div data-role="addr-box" style="display:flex;flex-direction:column;gap:6px;margin-bottom:16px"></div>

        <div class="text-h3" style="margin-bottom:6px">รายการสินค้าที่เลือกชำระเงิน</div>
        <div class="card" data-role="items-box" style="padding:12px 16px"></div>
      </div>

      <div class="card" style="padding:16px 18px">
        <div class="text-h3" style="margin-bottom:8px">โค้ดส่วนลด & โค้ดส่งฟรี</div>
        <div style="display:flex;gap:6px">
          <input type="text" class="input" data-role="coupon-in" placeholder="กรอกโค้ด เช่น WELCOME10" style="flex:1;height:36px" />
          <button type="button" class="btn btn-secondary btn-sm" data-role="coupon-btn" style="height:36px;min-width:76px">ใช้โค้ด</button>
        </div>
        <div class="text-small" data-role="coupon-msg" style="min-height:18px;margin-top:4px"></div>

        <div class="text-small-bold text-muted" style="margin:10px 0 4px">โค้ดของคุณ & โค้ดที่กดรับได้ (1 โค้ดใช้ได้ 1 ครั้ง จนกว่าจะกดรับใหม่)</div>
        <div data-role="coupons-list" style="display:flex;flex-direction:column;gap:6px;max-height:260px;overflow-y:auto;margin-bottom:10px"></div>

        <div class="text-h3" style="margin:10px 0 6px">สรุปคำสั่งซื้อ</div>
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span class="text-small text-muted">ยอดสินค้า</span><span class="text-small-bold" data-role="sum-sub">-</span></div>
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span class="text-small text-muted">ส่วนลดสินค้า</span><span class="text-small-bold" data-role="sum-disc">-</span></div>
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span class="text-small text-muted">ส่วนลดค่าจัดส่ง</span><span class="text-small-bold" data-role="sum-sdisc">-</span></div>
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span class="text-small text-muted">ค่าจัดส่งสุทธิ</span><span class="text-small-bold" data-role="sum-ship">-</span></div>
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span class="text-small text-muted">รวม VAT 7% (ในยอดชำระ)</span><span class="text-small-bold" data-role="sum-vat">-</span></div>
        <div style="display:flex;justify-content:space-between;padding:6px 0;border-top:1px solid var(--color-border);margin-top:4px"><span class="text-body-bold">ยอดชำระสุทธิ</span><span class="text-price text-danger" data-role="sum-total">-</span></div>

        <div class="text-small text-danger" data-role="msg" style="min-height:18px;margin-top:6px"></div>
        <button type="button" class="btn btn-primary btn-lg" data-role="confirm-btn" style="width:100%;margin-top:8px">ยืนยันสั่งซื้อ</button>
        <button type="button" class="btn btn-outline btn-md" data-role="back-cart" style="width:100%;margin-top:6px">‹ กลับไปตะกร้า</button>
      </div>
    </div>
  `;

  const addrBox = wrap.querySelector('[data-role="addr-box"]');
  const itemsBox = wrap.querySelector('[data-role="items-box"]');
  const couponIn = wrap.querySelector('[data-role="coupon-in"]');
  const couponBtn = wrap.querySelector('[data-role="coupon-btn"]');
  const couponMsg = wrap.querySelector('[data-role="coupon-msg"]');
  const couponsList = wrap.querySelector('[data-role="coupons-list"]');
  const sumSub = wrap.querySelector('[data-role="sum-sub"]');
  const sumDisc = wrap.querySelector('[data-role="sum-disc"]');
  const sumSdisc = wrap.querySelector('[data-role="sum-sdisc"]');
  const sumShip = wrap.querySelector('[data-role="sum-ship"]');
  const sumVat = wrap.querySelector('[data-role="sum-vat"]');
  const sumTotal = wrap.querySelector('[data-role="sum-total"]');
  const msgEl = wrap.querySelector('[data-role="msg"]');
  const confirmBtn = wrap.querySelector('[data-role="confirm-btn"]');

  wrap.querySelector('[data-role="manage-addr"]').addEventListener('click', () => router.show('addresses'));
  wrap.querySelector('[data-role="back-cart"]').addEventListener('click', () => router.show('cart'));

  async function loadCheckout() {
    try {
      const info = await api.get('/api/checkout/info', {
        coupon_code: couponCode || undefined,
        shipping_coupon_code: shippingCouponCode || undefined,
      });
      checkoutData = info;

      const addresses = info.addresses || [];
      if (!addresses.some((a) => a.id === selectedAddressId)) {
        const def = addresses.find((a) => a.is_default) || addresses[0];
        selectedAddressId = def ? def.id : 0;
      }

      // Render addresses
      addrBox.innerHTML = '';
      if (!addresses.length) {
        addrBox.innerHTML = `
          <div class="card" style="padding:16px;text-align:center">
            <div class="text-body text-muted" style="margin-bottom:8px">ยังไม่มีที่อยู่จัดส่ง กรุณาเพิ่มที่อยู่ก่อนสั่งซื้อ</div>
            <button type="button" class="btn btn-primary btn-md" data-role="go-addr">+ เพิ่มที่อยู่จัดส่ง</button>
          </div>
        `;
        addrBox.querySelector('[data-role="go-addr"]').addEventListener('click', () => router.show('addresses'));
      } else {
        for (const a of addresses) {
          const card = document.createElement('label');
          card.className = 'card';
          card.style.padding = '12px 14px';
          card.style.display = 'flex';
          card.style.gap = '10px';
          card.style.alignItems = 'flex-start';
          card.style.cursor = 'pointer';
          card.innerHTML = `
            <input type="radio" name="checkout_addr" value="${a.id}" ${a.id === selectedAddressId ? 'checked' : ''} style="margin-top:4px" />
            <div>
              <div style="display:flex;align-items:center;gap:8px">
                <span class="text-body-bold">${esc(a.recipient)}</span>
                <span class="text-small text-muted">${esc(formatPhone(a.phone))}</span>
                ${a.is_default ? `<span class="pill pill-success">ค่าเริ่มต้น</span>` : ''}
              </div>
              <div class="text-body" style="margin-top:2px">${esc(a.full_address)}</div>
            </div>
          `;
          card.querySelector('input').addEventListener('change', () => {
            selectedAddressId = a.id;
          });
          addrBox.appendChild(card);
        }
      }

      // Render items
      itemsBox.innerHTML = '';
      const items = info.selected_items || [];
      if (!items.length) {
        itemsBox.innerHTML = `
          <div style="text-align:center;padding:20px">
            <div class="text-body text-muted" style="margin-bottom:10px">ยังไม่มีสินค้าที่เลือกสำหรับชำระเงิน — กรุณาเลือกในตะกร้า</div>
            <button type="button" class="btn btn-primary btn-md" data-role="back-to-cart">กลับไปเลือกในตะกร้า</button>
          </div>
        `;
        itemsBox.querySelector('[data-role="back-to-cart"]').addEventListener('click', () => router.show('cart'));
      } else {
        for (const it of items) {
          const r = document.createElement('div');
          r.style.display = 'grid';
          r.style.gridTemplateColumns = '54px 1fr auto';
          r.style.gap = '10px';
          r.style.alignItems = 'center';
          r.style.padding = '6px 0';
          r.innerHTML = `
            <img src="${esc(resolveAssetUrl(it.image_path))}" alt="${esc(it.product_name)}" style="width:54px;height:72px;border-radius:6px;object-fit:cover;background:var(--color-surface-alt)" />
            <div>
              <div class="text-body-bold">${esc(it.product_name)}</div>
              <div class="text-small text-muted">${esc(it.option_label ? `${it.option_label} · ` : '')}${esc(formatPrice(it.unit_price))} × ${it.qty}</div>
              ${it.problem ? `<div class="text-small text-danger">แจ้งเตือน: ${esc(it.problem)}</div>` : ''}
            </div>
            <div class="text-body-bold">${esc(formatPrice(it.line_total))}</div>
          `;
          itemsBox.appendChild(r);
        }
      }

      // Coupon banner & list
      if (info.coupon_error || info.shipping_coupon_error) {
        const _cerr = info.coupon_error || info.shipping_coupon_error;
        couponMsg.className = 'text-small text-danger';
        couponMsg.textContent = `⛔ ${_cerr}`;
        setFieldError(couponIn, _cerr);
        showToast(_cerr, 'error');
      } else {
        const parts = [];
        if (info.applied_coupon) parts.push(`${info.applied_coupon.code} (${info.applied_coupon.description || ''})`);
        if (info.applied_shipping_coupon) parts.push(`${info.applied_shipping_coupon.code} (${info.applied_shipping_coupon.description || ''})`);
        if (parts.length) {
          couponMsg.className = 'text-small text-success';
          couponMsg.textContent = '✓ ใช้โค้ดแล้ว: ' + parts.join(' + ');
        } else {
          couponMsg.textContent = '';
        }
      }

      couponsList.innerHTML = '';
      const coupons = info.coupons || [];
      if (!coupons.length) {
        couponsList.innerHTML = `<div class="text-tiny text-muted" style="padding:4px 0">ยังไม่มีคูปองในระบบ</div>`;
      } else {
        const activeCode = (info.applied_coupon && info.applied_coupon.code) || '';
        const activeShipCode = (info.applied_shipping_coupon && info.applied_shipping_coupon.code) || '';
        for (const cp of coupons) {
          const isFreeShip = Boolean(cp.is_free_shipping);
          const canUse = Boolean(cp.can_use);
          const canClaim = Boolean(cp.can_claim);
          const isApplied = cp.code === activeCode || cp.code === activeShipCode;
          const badgeKind = isApplied || canUse ? 'success' : (canClaim ? 'warning' : 'muted');
          const statusTxt = isApplied ? 'กำลังใช้งาน' : (cp.status_text || '');

          const row = document.createElement('div');
          row.className = 'card-alt';
          row.style.border = isApplied ? '2px solid var(--color-success)' : (canUse ? '1px solid var(--color-primary)' : '1px solid var(--color-border)');
          row.style.padding = '6px 10px';
          row.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">
              <span class="text-small-bold" style="display:flex;align-items:center;gap:4px">
                ${iconSvg(isFreeShip ? 'truck' : 'coupon', 15, 'var(--color-danger)')}
                <span>${esc(cp.code)} · ${esc(cp.description || '')}</span>
              </span>
              <span class="pill pill-${badgeKind}">${esc(statusTxt)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;gap:6px">
              <span class="text-tiny text-muted">${esc(cp.reason || '')}</span>
              <span data-role="cp-act"></span>
            </div>
          `;
          const actSlot = row.querySelector('[data-role="cp-act"]');
          if (isApplied) {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'btn btn-outline btn-sm';
            b.textContent = 'ยกเลิก';
            b.addEventListener('click', () => {
              if (cp.code === couponCode) { couponCode = ''; couponIn.value = ''; }
              if (cp.code === shippingCouponCode) shippingCouponCode = '';
              loadCheckout();
            });
            actSlot.appendChild(b);
          } else if (canUse) {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'btn btn-primary btn-sm';
            b.textContent = 'กดใช้โค้ด';
            b.addEventListener('click', () => {
              if (isFreeShip) shippingCouponCode = cp.code;
              else couponCode = cp.code;
              loadCheckout();
            });
            actSlot.appendChild(b);
          } else if (canClaim) {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'btn btn-danger btn-sm';
            b.textContent = cp.is_used ? 'กดรับใหม่' : 'กดรับโค้ด';
            b.addEventListener('click', async () => {
              try {
                await api.post('/api/coupons/claim', { coupon_id: cp.id });
                showToast(`เก็บโค้ดส่วนลด ${cp.code} สำเร็จ`, 'success');
                await loadCheckout();
              } catch (err) {
                const _cerr = err.message || 'เก็บโค้ดไม่สำเร็จ';
                couponMsg.className = 'text-small text-danger';
                couponMsg.textContent = `⛔ ${_cerr}`;
                showToast(_cerr, 'error');
              }
            });
            actSlot.appendChild(b);
          }
          couponsList.appendChild(row);
        }
      }

      // Totals
      sumSub.textContent = formatPrice(info.subtotal);
      sumDisc.textContent = info.discount ? `-${formatPrice(info.discount)}` : '-';
      sumSdisc.textContent = info.shipping_discount ? `-${formatPrice(info.shipping_discount)}` : '-';
      sumShip.textContent = items.length && info.shipping_fee === 0 ? 'ฟรี' : formatPrice(info.shipping_fee);
      sumVat.textContent = formatPrice(info.vat_amount || 0);
      sumTotal.textContent = formatPrice(info.total);

      const hasProb = items.some((i) => i.problem);
      confirmBtn.disabled = !(items.length > 0 && !hasProb && addresses.length > 0 && !busy);
    } catch (err) {
      msgEl.textContent = `⛔ ${err.message}`;
    }
  }

  async function applyManualCoupon() {
    const raw = couponIn.value.trim();
    if (!raw) return;
    couponMsg.textContent = '';
    try {
      const sub = (checkoutData && checkoutData.subtotal) || 0;
      const ship = (checkoutData && checkoutData.base_shipping_fee) || 0;
      const validated = await api.post('/api/coupons/validate', {
        code: raw,
        subtotal: sub,
        shipping_fee: ship,
      });
      if (validated.is_free_shipping) {
        shippingCouponCode = validated.code;
        couponIn.value = '';
      } else {
        couponCode = validated.code;
      }
      await loadCheckout();
    } catch (err) {
      const _cerr = err.message || 'โค้ดไม่ถูกต้อง';
      couponMsg.className = 'text-small text-danger';
      couponMsg.textContent = `⛔ ${_cerr}`;
      setFieldError(couponIn, _cerr);
      showToast(_cerr, 'error');
    }
  }

  couponIn.addEventListener('input', () => clearFieldError(couponIn));
  couponBtn.addEventListener('click', applyManualCoupon);
  couponIn.addEventListener('keydown', (e) => { if (e.key === 'Enter') applyManualCoupon(); });

  confirmBtn.addEventListener('click', async () => {
    if (busy) return;
    if (!selectedAddressId) {
      msgEl.textContent = '⛔ กรุณาเลือกที่อยู่จัดส่ง';
      showToast('กรุณาเลือกที่อยู่จัดส่งก่อนยืนยันคำสั่งซื้อ', 'error');
      return;
    }
    const items = (checkoutData && checkoutData.selected_items) || [];
    if (!items.length) {
      msgEl.textContent = '⛔ กรุณาเลือกสินค้าในตะกร้าอย่างน้อย 1 รายการ';
      showToast('กรุณาเลือกสินค้าในตะกร้าอย่างน้อย 1 รายการ', 'error');
      return;
    }
    let cCode = couponCode || null;
    let sCode = shippingCouponCode || null;
    if (!cCode && sCode) {
      cCode = sCode;
      sCode = null;
    }
    busy = true;
    confirmBtn.disabled = true;
    msgEl.textContent = '';
    try {
      const order = await api.post('/api/orders', {
        address_id: selectedAddressId,
        coupon_code: cCode,
        shipping_coupon_code: sCode,
        selected_item_ids: items.map((i) => i.cart_item_id),
      });
      showToast(`สร้างคำสั่งซื้อ #${order.id} สำเร็จ กรุณาชำระเงิน`, 'success');
      await router.refresh_shell();
      router.show('payment', { order_id: order.id });
    } catch (err) {
      busy = false;
      const _em = err.message || 'สั่งซื้อไม่สำเร็จ';
      msgEl.textContent = `⛔ ${_em}`;
      showToast(_em, 'error');
      await loadCheckout();
    }
  });

  await loadCheckout();
}
