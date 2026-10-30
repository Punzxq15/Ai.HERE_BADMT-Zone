// web/js/pages/buyer/cart.js — หน้าตะกร้าสินค้า (Checkbox เลือกรายการ, เลือกทั้งหมด, ลบที่เลือก, สรุปยอดเฉพาะที่เลือก)
import { api, esc, formatPrice, resolveAssetUrl } from '../../api.js';
import { confirm, showToast } from '../../components/dialogs.js';
import { pageTitleHtml } from '../../components/buyer_common.js';
import { iconSvg } from '../../components/icons.js';

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  wrap.innerHTML = `
    ${pageTitleHtml('ตะกร้าสินค้า')}
    <div style="display:grid;grid-template-columns:1fr 320px;gap:16px;align-items:start">
      <div>
        <div class="card" data-role="toolbar" style="padding:10px 14px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;align-items:center;gap:12px">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer" class="text-body-bold">
              <input type="checkbox" data-role="select-all" checked />
              <span data-role="select-all-txt">เลือกทั้งหมด</span>
            </label>
            <span class="text-small-bold text-muted" data-role="sel-info"></span>
          </div>
          <button type="button" class="btn btn-danger btn-sm" data-role="del-selected">
            ${iconSvg('trash', 15, '#FFFFFF')} <span>ลบสินค้าที่เลือก</span>
          </button>
        </div>
        <div data-role="items-list" style="display:flex;flex-direction:column;gap:8px"></div>
      </div>

      <div class="card" style="padding:16px 18px">
        <div class="text-h3" style="margin-bottom:10px">สรุปคำสั่งซื้อ (เฉพาะที่เลือก)</div>
        <div style="display:flex;justify-content:space-between;padding:4px 0">
          <span class="text-body text-muted">จำนวนสินค้าที่เลือก</span>
          <span class="text-body-bold" data-role="sum-count">-</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0">
          <span class="text-body text-muted">ยอดสินค้า</span>
          <span class="text-body-bold" data-role="sum-sub">-</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:4px 0">
          <span class="text-body text-muted">ค่าจัดส่ง (โดยประมาณ)</span>
          <span class="text-body-bold" data-role="sum-ship">-</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:6px 0;border-top:1px solid var(--color-border);margin-top:4px">
          <span class="text-body-bold">รวมโดยประมาณ</span>
          <span class="text-price text-danger" data-role="sum-total">-</span>
        </div>
        <div class="text-tiny text-muted" style="margin-top:6px">ส่วนลดจากคูปองและโค้ดส่งฟรี เลือกใช้ได้ในขั้นตอนชำระเงิน</div>
        <div class="text-small text-danger" data-role="msg" style="min-height:18px;margin-top:6px"></div>
        <button type="button" class="btn btn-primary btn-lg" data-role="checkout-btn" style="width:100%;margin-top:10px">ไปชำระเงิน</button>
        <button type="button" class="btn btn-outline btn-md" data-role="continue-btn" style="width:100%;margin-top:6px">เลือกซื้อสินค้าต่อ</button>
      </div>
    </div>
  `;

  let currentCart = null;
  const toolbar = wrap.querySelector('[data-role="toolbar"]');
  const selectAllCb = wrap.querySelector('[data-role="select-all"]');
  const selectAllTxt = wrap.querySelector('[data-role="select-all-txt"]');
  const selInfo = wrap.querySelector('[data-role="sel-info"]');
  const delSelectedBtn = wrap.querySelector('[data-role="del-selected"]');
  const itemsList = wrap.querySelector('[data-role="items-list"]');
  const sumCount = wrap.querySelector('[data-role="sum-count"]');
  const sumSub = wrap.querySelector('[data-role="sum-sub"]');
  const sumShip = wrap.querySelector('[data-role="sum-ship"]');
  const sumTotal = wrap.querySelector('[data-role="sum-total"]');
  const msgEl = wrap.querySelector('[data-role="msg"]');
  const checkoutBtn = wrap.querySelector('[data-role="checkout-btn"]');

  wrap.querySelector('[data-role="continue-btn"]').addEventListener('click', () => router.show('category'));

  function renderCart(cart) {
    currentCart = cart;
    itemsList.innerHTML = '';
    const items = cart.items || [];
    if (!items.length) {
      toolbar.classList.add('hidden');
      itemsList.innerHTML = `
        <div class="card" style="padding:50px 20px;text-align:center">
          <div class="text-body-bold text-muted" style="margin-bottom:12px">ตะกร้าของคุณยังว่างอยู่</div>
          <button type="button" class="btn btn-primary btn-md" data-role="empty-shop">เลือกซื้อสินค้า</button>
        </div>
      `;
      itemsList.querySelector('[data-role="empty-shop"]').addEventListener('click', () => router.show('category'));
    } else {
      toolbar.classList.remove('hidden');
      const allSel = Boolean(cart.all_selected ?? true);
      selectAllCb.checked = allSel;
      selectAllTxt.textContent = allSel ? 'ยกเลิกเลือกทั้งหมด' : 'เลือกทั้งหมด';
      const selRows = (cart.selected_items || []).length;
      selInfo.textContent = `(เลือก ${selRows} จาก ${items.length} รายการ)`;
      delSelectedBtn.disabled = selRows <= 0;
    }

    for (const item of items) {
      const isSel = Boolean(item.is_selected ?? true);
      const row = document.createElement('div');
      row.className = 'card';
      row.style.border = isSel ? '2px solid var(--color-primary)' : '1px solid var(--color-border)';
      row.style.padding = '12px 14px';
      row.style.display = 'grid';
      row.style.gridTemplateColumns = '28px 72px 1fr auto';
      row.style.gap = '12px';
      row.style.alignItems = 'center';

      row.innerHTML = `
        <input type="checkbox" data-role="item-cb" ${isSel ? 'checked' : ''} style="width:18px;height:18px;cursor:pointer" />
        <img src="${esc(resolveAssetUrl(item.image_path))}" alt="${esc(item.product_name)}" style="width:72px;height:96px;border-radius:8px;object-fit:cover;background:var(--color-surface-alt)" />
        <div>
          <div class="text-body-bold" data-role="pname" style="cursor:pointer">${esc(item.product_name)}</div>
          ${item.option_label ? `<div class="text-small text-muted">${esc(item.option_label)}</div>` : ''}
          <div class="text-small text-muted">ราคาต่อชิ้น ${esc(formatPrice(item.unit_price))}</div>
          ${item.problem ? `<div class="text-small-bold text-danger" style="margin-top:4px">แจ้งเตือน: ${esc(item.problem)}</div>` : ''}
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
          <div style="display:flex;align-items:center;gap:4px">
            <button type="button" class="btn btn-outline btn-sm" data-role="minus" style="width:32px;padding:0" ${item.qty <= 1 ? 'disabled' : ''}>−</button>
            <span class="text-body-bold" style="min-width:34px;text-align:center">${item.qty}</span>
            <button type="button" class="btn btn-outline btn-sm" data-role="plus" style="width:32px;padding:0">+</button>
          </div>
          <div class="text-price ${isSel ? 'text-danger' : 'text-muted'}">${esc(formatPrice(item.line_total))}</div>
          <button type="button" class="btn btn-ghost btn-sm text-danger" data-role="del" style="height:26px">
            ${iconSvg('trash', 14, 'var(--color-danger)')} <span>ลบ</span>
          </button>
        </div>
      `;

      row.querySelector('[data-role="pname"]').addEventListener('click', () => {
        router.show('product_detail', { product_id: item.product_id });
      });
      row.querySelector('[data-role="item-cb"]').addEventListener('change', async (e) => {
        msgEl.textContent = '';
        try {
          const updated = await api.patch(`/api/cart/items/${item.cart_item_id}`, { selected: e.target.checked });
          renderCart(updated);
        } catch (err) {
          msgEl.textContent = `⛔ ${err.message}`; showToast(err.message || 'ดำเนินการไม่สำเร็จ', 'error');
        }
      });
      row.querySelector('[data-role="minus"]').addEventListener('click', () => changeQty(item, -1));
      row.querySelector('[data-role="plus"]').addEventListener('click', () => changeQty(item, 1));
      row.querySelector('[data-role="del"]').addEventListener('click', () => removeSingle(item));
      itemsList.appendChild(row);
    }

    // Summary
    const selItems = cart.selected_items || [];
    const selCount = Number(cart.selected_item_count ?? cart.item_count ?? 0);
    const selSub = Number(cart.selected_subtotal ?? cart.subtotal ?? 0);
    const selProblem = Boolean(cart.selected_has_problem ?? cart.has_problem);
    const shipping = selItems.length ? Number(cart.shipping_fee || 0) : 0;

    sumCount.textContent = `${selCount.toLocaleString()} ชิ้น`;
    sumSub.textContent = formatPrice(selSub);
    sumShip.textContent = selItems.length && shipping === 0 ? 'ฟรี' : formatPrice(shipping);
    sumTotal.textContent = formatPrice(selSub + shipping);

    const blocked = !selItems.length || selProblem;
    checkoutBtn.disabled = blocked;
    if (items.length && !selItems.length) {
      msgEl.textContent = 'กรุณาติ๊กเลือกสินค้าอย่างน้อย 1 รายการเพื่อชำระเงิน';
    } else if (selItems.length && selProblem) {
      msgEl.textContent = 'สินค้าที่เลือกมีปัญหาสต็อก กรุณาแก้ไขหรือเอาติ๊กออกก่อนชำระเงิน';
    } else if (!msgEl.textContent.startsWith('⛔')) {
      msgEl.textContent = '';
    }
  }

  async function changeQty(item, delta) {
    const newQty = item.qty + delta;
    if (newQty < 1) return;
    msgEl.textContent = '';
    try {
      const updated = await api.patch(`/api/cart/items/${item.cart_item_id}`, { qty: newQty });
      await router.refresh_shell();
      renderCart(updated);
    } catch (err) {
      msgEl.textContent = `⛔ ${err.message}`; showToast(err.message || 'ดำเนินการไม่สำเร็จ', 'error');
    }
  }

  async function removeSingle(item) {
    const ok = await confirm('ลบสินค้า', `ต้องการลบ "${item.product_name}" ออกจากตะกร้าใช่ไหม?`, {
      confirmText: 'ลบ',
      danger: true,
    });
    if (!ok) return;
    try {
      const updated = await api.del(`/api/cart/items/${item.cart_item_id}`);
      await router.refresh_shell();
      renderCart(updated);
    } catch (err) {
      msgEl.textContent = `⛔ ${err.message}`; showToast(err.message || 'ดำเนินการไม่สำเร็จ', 'error');
    }
  }

  selectAllCb.addEventListener('change', async () => {
    msgEl.textContent = '';
    try {
      const updated = await api.post('/api/cart/select-all', { selected: selectAllCb.checked });
      renderCart(updated);
    } catch (err) {
      msgEl.textContent = `⛔ ${err.message}`; showToast(err.message || 'ดำเนินการไม่สำเร็จ', 'error');
    }
  });

  delSelectedBtn.addEventListener('click', async () => {
    const selItems = (currentCart && currentCart.selected_items) || [];
    if (!selItems.length) return;
    const ok = await confirm(
      'ลบสินค้าที่เลือก',
      `ต้องการลบสินค้าที่ติ๊กเลือกไว้ทั้ง ${selItems.length} รายการออกจากตะกร้าใช่หรือไม่?`,
      { confirmText: 'ลบที่เลือก', danger: true }
    );
    if (!ok) return;
    try {
      const updated = await api.del('/api/cart/selected');
      await router.refresh_shell();
      renderCart(updated);
    } catch (err) {
      msgEl.textContent = `⛔ ${err.message}`; showToast(err.message || 'ดำเนินการไม่สำเร็จ', 'error');
    }
  });

  checkoutBtn.addEventListener('click', () => {
    const selItems = (currentCart && currentCart.selected_items) || [];
    if (!selItems.length) {
      msgEl.textContent = 'กรุณาติ๊กเลือกสินค้าอย่างน้อย 1 รายการเพื่อชำระเงิน';
      return;
    }
    router.show('checkout');
  });

  try {
    const cart = await api.get('/api/cart');
    renderCart(cart);
  } catch (err) {
    msgEl.textContent = err.message || 'โหลดตะกร้าสินค้าไม่สำเร็จ';
  }
}
