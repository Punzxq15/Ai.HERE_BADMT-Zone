// web/js/pages/buyer/orders.js — หน้าออเดอร์ของฉัน 8 แท็บ (ปุ่มดูรายละเอียด, เขียนรีวิวสินค้าโดยตรง และปุ่มไม่รีวิวบนการ์ดออเดอร์)
import { api, esc, formatDateTime, formatPrice, ORDER_STATUS_DISPLAY_ORDER, ORDER_STATUS_LABELS, resolveAssetUrl } from '../../api.js';
import { confirm, showToast } from '../../components/dialogs.js';
import { pageTitleHtml } from '../../components/buyer_common.js';

const PAGE_SIZE = 6;
const MAX_LINES = 2;

export async function render(container, router, params = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  let curStatus = params.status || 'all';
  let curPage = 1;
  let totalPages = 1;

  wrap.innerHTML = `
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      ${pageTitleHtml('📦 ออเดอร์ของฉัน', 'ติดตามสถานะคำสั่งซื้อ การชำระเงิน การจัดส่ง การรีวิว และรายการสินค้าที่ยกเลิก')}
      <span class="text-small" data-role="msg"></span>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:4px;margin:8px 0 12px" data-role="tabs"></div>
    <div data-role="list" style="display:flex;flex-direction:column;gap:10px"></div>
    <div style="display:flex;align-items:center;gap:12px;margin-top:14px">
      <button type="button" class="btn btn-outline btn-sm" data-role="prev" style="width:100px">‹ ก่อนหน้า</button>
      <span class="text-small-bold text-muted" data-role="page-lbl"></span>
      <button type="button" class="btn btn-outline btn-sm" data-role="next" style="width:100px">ถัดไป ›</button>
    </div>
  `;

  const msgEl = wrap.querySelector('[data-role="msg"]');
  const tabsEl = wrap.querySelector('[data-role="tabs"]');
  const listEl = wrap.querySelector('[data-role="list"]');
  const prevBtn = wrap.querySelector('[data-role="prev"]');
  const nextBtn = wrap.querySelector('[data-role="next"]');
  const pageLbl = wrap.querySelector('[data-role="page-lbl"]');

  async function load() {
    listEl.innerHTML = '';
    try {
      const res = await api.get('/api/orders/my', {
        status: curStatus,
        page: curPage,
        page_size: PAGE_SIZE,
      });
      const counts = res.counts || {};
      curPage = res.page || 1;
      totalPages = res.pages || 1;

      tabsEl.innerHTML = '';
      for (const [key, label] of ORDER_STATUS_DISPLAY_ORDER) {
        const cnt = counts[key] || 0;
        const txt = cnt ? `${label} (${cnt})` : label;
        const active = key === curStatus;
        const isCancel = key === 'cancelled';
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `btn btn-sm ${active ? (isCancel ? 'btn-danger' : 'btn-primary') : 'btn-outline'}`;
        btn.textContent = txt;
        btn.addEventListener('click', () => {
          curStatus = key;
          curPage = 1;
          msgEl.textContent = '';
          load();
        });
        tabsEl.appendChild(btn);
      }

      const items = res.items || [];
      if (!items.length) {
        const emptyTxt = curStatus === 'cancelled'
          ? 'ยังไม่มีรายการสินค้าที่คุณยกเลิก'
          : (curStatus === 'to_review' ? 'ไม่มีรายการคำสั่งซื้อที่รอรีวิว' : 'ยังไม่มีคำสั่งซื้อในหมวดนี้');
        listEl.innerHTML = `
          <div class="card" style="padding:50px 20px;text-align:center">
            <div class="text-body-bold text-muted" style="margin-bottom:10px;white-space:pre-line">📦
${esc(emptyTxt)}</div>
            <button type="button" class="btn btn-primary btn-md" data-role="go-shop">🛒 เลือกซื้อสินค้า</button>
          </div>
        `;
        listEl.querySelector('[data-role="go-shop"]').addEventListener('click', () => router.show('category'));
      } else {
        for (const order of items) {
          const card = document.createElement('div');
          card.className = 'card';
          card.style.padding = '12px 16px';
          const oItems = order.items || [];
          const firstImg = oItems[0] ? oItems[0].image_path : null;

          // รวบรวมสินค้าที่ยังไม่ได้รีวิวและยังไม่ได้กดไม่รีวิว (แยกตาม product_id ไม่ให้ซ้ำ)
          const unreviewedProducts = [];
          const seenUnrevPid = new Set();
          for (const it of oItems) {
            const isRev = Boolean(it.is_reviewed || it.reviewed);
            const isSkip = Boolean(it.is_review_skipped);
            if (order.status === 'completed' && it.product_id && !isRev && !isSkip && !seenUnrevPid.has(Number(it.product_id))) {
              seenUnrevPid.add(Number(it.product_id));
              unreviewedProducts.push(it);
            }
          }
          const awaitingRev = order.status === 'completed'
            ? (order.awaiting_review_count !== undefined ? Number(order.awaiting_review_count) : unreviewedProducts.length)
            : 0;

          const stLbl = ORDER_STATUS_LABELS[order.status] || order.status;
          const stKind = order.status === 'completed' || order.status === 'paid' ? 'success' : (order.status === 'cancelled' ? 'danger' : 'warning');

          const visibleItems = oItems.slice(0, MAX_LINES);
          const renderedRowRevPid = new Set();

          const itemRowsHtml = visibleItems.map((it) => {
            const isRev = Boolean(it.is_reviewed || it.reviewed);
            const isSkip = Boolean(it.is_review_skipped);
            const pid = Number(it.product_id || 0);
            let rowBadgeHtml = '';
            if (order.status === 'completed' && pid) {
              if (isRev) {
                rowBadgeHtml = `<span class="pill pill-success" style="font-size:11px;padding:1px 8px">✓ รีวิวแล้ว</span>`;
              } else if (isSkip) {
                rowBadgeHtml = `<span class="pill pill-neutral" style="font-size:11px;padding:1px 8px">ไม่รีวิว</span>`;
              } else if (unreviewedProducts.length > 1 && !renderedRowRevPid.has(pid)) {
                renderedRowRevPid.add(pid);
                rowBadgeHtml = `<button type="button" class="btn btn-primary btn-sm" data-row-review-pid="${pid}" style="height:26px;padding:0 10px;font-size:12px">⭐ เขียนรีวิวสินค้า</button>`;
              }
            }
            return `
              <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:3px">
                <div class="text-body-bold">${esc(it.product_name)}${it.option_label ? ` (${esc(it.option_label)})` : ''} × ${it.qty}</div>
                ${rowBadgeHtml}
              </div>
            `;
          }).join('');

          const hiddenItemsCount = Math.max(0, oItems.length - MAX_LINES);

          card.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <div style="display:flex;align-items:center;gap:12px">
                <span class="text-body-bold">คำสั่งซื้อ #${order.id}</span>
                <span class="text-small text-muted">${esc(formatDateTime(order.created_at))}</span>
              </div>
              <div style="display:flex;gap:6px">
                <span class="pill pill-${stKind}">${esc(stLbl)}</span>
                ${(order.status === 'completed' && awaitingRev > 0) ? `<span class="pill pill-primary">รอรีวิว (${awaitingRev})</span>` : ''}
              </div>
            </div>
            <div style="display:grid;grid-template-columns:64px 1fr auto;gap:12px;align-items:start">
              <img src="${esc(resolveAssetUrl(firstImg))}" alt="item" style="width:64px;height:64px;border-radius:8px;object-fit:cover;background:var(--color-surface-alt)" />
              <div>
                ${itemRowsHtml}
                ${hiddenItemsCount > 0 ? `<div class="text-small text-muted">และอีก ${hiddenItemsCount} รายการ</div>` : ''}
                ${(order.status === 'cancelled' && order.cancel_reason) ? `<div class="text-small-bold text-danger" style="margin-top:2px">เหตุผลที่ยกเลิก: ${esc(order.cancel_reason)}</div>` : ''}
              </div>
              <div style="text-align:right">
                <div class="text-small text-muted">${order.item_count || oItems.length} ชิ้น</div>
                <div class="text-price text-danger">${esc(formatPrice(order.total))}</div>
              </div>
            </div>
            <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px;flex-wrap:wrap">
              ${(order.status === 'completed' && awaitingRev > 0) ? `
                <button type="button" class="btn btn-ghost btn-sm" data-role="skip-review" title="นำออกจากช่องรอรีวิวโดยไม่เขียนรีวิว">ไม่รีวิว</button>
                <button type="button" class="btn btn-primary btn-sm" data-role="review">⭐ เขียนรีวิวสินค้า</button>
              ` : ''}
              <button type="button" class="btn btn-outline btn-sm" data-role="detail">ดูรายละเอียด</button>
              ${order.status === 'shipped' ? `<button type="button" class="btn btn-success btn-sm" data-role="received">✓ ได้รับสินค้าแล้ว</button>` : ''}
              ${order.status === 'pending' ? `<button type="button" class="btn btn-primary btn-sm" data-role="pay">💳 ชำระเงิน</button>` : ''}
            </div>
          `;

          card.querySelector('[data-role="detail"]').addEventListener('click', () => router.show('order_detail', { order_id: order.id }));

          card.querySelectorAll('[data-row-review-pid]').forEach((btn) => {
            btn.addEventListener('click', () => {
              const pid = Number(btn.getAttribute('data-row-review-pid'));
              router.show('write_review', { product_id: pid, order_id: order.id });
            });
          });

          const revBtn = card.querySelector('[data-role="review"]');
          if (revBtn) {
            revBtn.addEventListener('click', () => {
              const targetItem = unreviewedProducts[0] || oItems.find((it) => it.product_id);
              if (targetItem && targetItem.product_id) {
                router.show('write_review', {
                  product_id: Number(targetItem.product_id),
                  order_id: order.id,
                });
              }
            });
          }

          const skipBtn = card.querySelector('[data-role="skip-review"]');
          if (skipBtn) {
            skipBtn.addEventListener('click', async () => {
              skipBtn.disabled = true;
              try {
                await api.post('/api/reviews/skip', { order_id: order.id });
                msgEl.textContent = '';
                showToast(`นำคำสั่งซื้อ #${order.id} ออกจากช่องรอรีวิวเรียบร้อยแล้ว`, 'success');
                await load();
              } catch (err) {
                skipBtn.disabled = false;
                const em = err.message || 'ไม่สามารถดำเนินการได้';
                msgEl.className = 'text-small text-danger';
                msgEl.textContent = `⛔ ${em}`;
                showToast(em, 'error');
              }
            });
          }

          const payBtn = card.querySelector('[data-role="pay"]');
          if (payBtn) payBtn.addEventListener('click', () => router.show('payment', { order_id: order.id }));

          const recBtn = card.querySelector('[data-role="received"]');
          if (recBtn) {
            recBtn.addEventListener('click', async () => {
              const ok = await confirm('ยืนยันการรับสินค้า', `ยืนยันว่าได้รับสินค้าของคำสั่งซื้อ #${order.id} เรียบร้อยแล้วใช่ไหม?`, { confirmText: 'ได้รับแล้ว' });
              if (!ok) return;
              try {
                await api.post(`/api/orders/${order.id}/confirm-received`);
                await router.refresh_shell();
                msgEl.textContent = '';
                showToast(`ยืนยันรับสินค้าคำสั่งซื้อ #${order.id} สำเร็จ — เขียนรีวิวสินค้าได้ทันที`, 'success');
                await load();
              } catch (err) {
                const em = err.message || 'ไม่สามารถยืนยันการรับสินค้าได้';
                msgEl.className = 'text-small text-danger';
                msgEl.textContent = `⛔ ${em}`;
                showToast(em, 'error');
              }
            });
          }
          listEl.appendChild(card);
        }
      }

      pageLbl.textContent = `หน้า ${curPage}/${totalPages} · ทั้งหมด ${Number(res.total || 0).toLocaleString()} รายการ`;
      prevBtn.disabled = curPage <= 1;
      nextBtn.disabled = curPage >= totalPages;
    } catch (err) {
      const em = err.message || 'โหลดรายการคำสั่งซื้อไม่สำเร็จ';
      msgEl.className = 'text-small text-danger';
      msgEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
    }
  }

  prevBtn.addEventListener('click', () => { if (curPage > 1) { curPage -= 1; load(); } });
  nextBtn.addEventListener('click', () => { if (curPage < totalPages) { curPage += 1; load(); } });

  await load();
}
