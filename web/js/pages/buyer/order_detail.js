// web/js/pages/buyer/order_detail.js — หน้ารายละเอียดคำสั่งซื้อ (ไทม์ไลน์, ขนส่ง, สินค้า, VAT 7%, PDF ใบเสร็จ, ส่งเมล)
import { api, esc, formatDateTime, formatPhone, formatPrice, ORDER_STATUS_LABELS, resolveAssetUrl, SHIPMENT_STATUS_LABELS } from '../../api.js';
import { createOrderTimeline } from '../../components/order_timeline.js';
import { askReason, confirm, showToast } from '../../components/dialogs.js';

const RECEIPT_STATUSES = new Set(['paid', 'shipped', 'completed']);

export async function render(container, router, params = {}) {
  const orderId = params.order_id || params.id;
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  async function load(message = '', ok = false) {
    wrap.innerHTML = '';
    let order = null;
    try {
      if (!orderId) throw new Error('ไม่พบคำสั่งซื้อ');
      order = await api.get(`/api/orders/${orderId}`);
    } catch (err) {
      wrap.innerHTML = `
        <div style="text-align:center;padding:40px 20px">
          <div class="text-body text-danger" style="margin-bottom:10px">⛔ ${esc(err.message || 'ไม่พบคำสั่งซื้อ')}</div>
          <button type="button" class="btn btn-primary btn-md" data-role="go-orders">ไปหน้าออเดอร์ของฉัน</button>
        </div>
      `;
      wrap.querySelector('[data-role="go-orders"]').addEventListener('click', () => router.show('orders'));
      return;
    }

    const status = order.status;
    const stLbl = ORDER_STATUS_LABELS[status] || status;
    const stKind = status === 'completed' || status === 'paid' ? 'success' : (status === 'cancelled' ? 'danger' : 'warning');
    const items = order.items || [];
    const itemCnt = items.reduce((a, b) => a + Number(b.qty || 0), 0);
    const preVat = order.pre_vat_amount ?? Math.round((Number(order.total || 0) / 1.07) * 100) / 100;
    const vatAmt = order.vat_amount ?? Math.round((Number(order.total || 0) - preVat) * 100) / 100;
    const shipment = order.shipment;

    wrap.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div style="display:flex;align-items:center;gap:10px">
          <button type="button" class="btn btn-outline btn-sm" data-role="back">‹ ย้อนกลับ</button>
          <span class="text-h2">คำสั่งซื้อ #${order.id}</span>
          <span class="pill pill-${stKind}">${esc(stLbl)}</span>
        </div>
        <span class="text-small text-muted">สั่งซื้อเมื่อ ${esc(formatDateTime(order.created_at))}</span>
      </div>

      <div class="text-small ${ok ? 'text-success' : 'text-danger'}" data-role="msg" style="min-height:18px;margin-top:6px">${esc(ok ? '' : message)}</div>
      ${(status === 'cancelled' && order.cancel_reason) ? `<div class="text-body-bold text-danger" style="margin-bottom:6px">เหตุผลที่ยกเลิก: ${esc(order.cancel_reason)}</div>` : ''}

      <div style="display:grid;grid-template-columns:1fr 350px;gap:14px;align-items:start;margin-top:6px">
        <div style="display:flex;flex-direction:column;gap:12px">
          <div class="card" style="padding:14px 18px">
            <div class="text-h3" style="margin-bottom:8px">สถานะคำสั่งซื้อ</div>
            <div data-role="timeline-slot"></div>
          </div>

          ${(shipment && (shipment.carrier || shipment.tracking_no)) ? `
            <div class="card" style="padding:14px 18px">
              <div class="text-h3" style="margin-bottom:6px">ข้อมูลการจัดส่ง</div>
              <div class="text-body-bold">บริษัทขนส่ง: ${esc(shipment.carrier || '-')}</div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-top:4px">
                <div style="display:flex;align-items:center;gap:10px">
                  <span class="text-body-bold text-info">เลขพัสดุ: ${esc(shipment.tracking_no || '-')}</span>
                  ${shipment.tracking_no ? `<button type="button" class="btn btn-outline btn-sm" data-role="copy-track">คัดลอก</button>` : ''}
                </div>
                <span class="pill pill-info">${esc(SHIPMENT_STATUS_LABELS[shipment.status] || shipment.status || '')}</span>
              </div>
            </div>
          ` : ''}

          <div class="card" style="padding:14px 18px">
            <div class="text-h3" style="margin-bottom:8px">รายการสินค้า (${itemCnt.toLocaleString()} ชิ้น)</div>
            <div data-role="items-list" style="display:flex;flex-direction:column;gap:10px"></div>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:12px">
          <div class="card" style="padding:14px 18px">
            <div class="text-h3" style="margin-bottom:8px">สรุปยอดชำระ & ใบเสร็จ (VAT 7%)</div>
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span class="text-small text-muted">ยอดสินค้า</span><span class="text-small-bold">${esc(formatPrice(order.subtotal))}</span></div>
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span class="text-small text-muted">${esc(order.coupon_code ? `ส่วนลด (${order.coupon_code})` : 'ส่วนลด')}</span><span class="text-small-bold">${order.discount ? `-${esc(formatPrice(order.discount))}` : '-'}</span></div>
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span class="text-small text-muted">ค่าจัดส่ง</span><span class="text-small-bold">${!order.shipping_fee ? 'ฟรี' : esc(formatPrice(order.shipping_fee))}</span></div>
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span class="text-small text-muted">มูลค่าก่อนภาษี</span><span class="text-small-bold">${esc(formatPrice(preVat))}</span></div>
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span class="text-small text-muted">ภาษีมูลค่าเพิ่ม (VAT 7%)</span><span class="text-small-bold">${esc(formatPrice(vatAmt))}</span></div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;border-top:1px solid var(--color-border);margin-top:4px"><span class="text-body-bold">ยอดรวมสุทธิ (รวม VAT 7%)</span><span class="text-price text-danger">${esc(formatPrice(order.total))}</span></div>
            ${order.payment ? `<div class="text-small-bold text-muted" style="margin-top:6px">การชำระเงิน: ${esc(order.payment.status_label || '')}${order.payment.status === 'rejected' && order.payment.reject_reason ? ` — ${esc(order.payment.reject_reason)}` : ''}</div>` : ''}
          </div>

          <div class="card" style="padding:14px 18px">
            <div class="text-h3" style="margin-bottom:6px">ที่อยู่จัดส่ง</div>
            <div class="text-body-bold">${esc(order.recipient_name)}</div>
            <div class="text-small text-muted">${esc(formatPhone(order.recipient_phone))}</div>
            <div class="text-body" style="margin-top:4px">${esc(order.shipping_address)}</div>
          </div>

          <div class="card" style="padding:14px 18px;display:flex;flex-direction:column;gap:6px" data-role="actions"></div>
        </div>
      </div>
    `;

    const msgEl = wrap.querySelector('[data-role="msg"]');
    wrap.querySelector('[data-role="back"]').addEventListener('click', () => router.go_back('orders'));

    const tl = createOrderTimeline(order.timeline || [], order.shipment || null);
    wrap.querySelector('[data-role="timeline-slot"]').appendChild(tl.el);

    const copyBtn = wrap.querySelector('[data-role="copy-track"]');
    if (copyBtn && shipment && shipment.tracking_no) {
      copyBtn.addEventListener('click', async () => {
        try { await navigator.clipboard.writeText(shipment.tracking_no); } catch (e) {}
        showToast('คัดลอกเลขพัสดุเรียบร้อยแล้ว', 'success');
      });
    }

    const itemsList = wrap.querySelector('[data-role="items-list"]');
    for (const item of items) {
      const r = document.createElement('div');
      r.style.display = 'grid';
      r.style.gridTemplateColumns = '60px 1fr auto';
      r.style.gap = '12px';
      r.style.alignItems = 'center';
      r.innerHTML = `
        <img src="${esc(resolveAssetUrl(item.image_path))}" alt="${esc(item.product_name)}" style="width:60px;height:80px;border-radius:6px;object-fit:cover;background:var(--color-surface-alt)" />
        <div>
          <div class="text-body-bold" data-role="pname" style="cursor:pointer">${esc(item.product_name)}</div>
          ${item.option_label ? `<div class="text-small text-muted">${esc(item.option_label)}</div>` : ''}
          <div class="text-small text-muted">${esc(formatPrice(item.price_at_purchase))} × ${item.qty}</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
          <span class="text-body-bold">${esc(formatPrice(item.line_total))}</span>
          <span data-role="rev-slot"></span>
        </div>
      `;
      if (item.product_id) {
        r.querySelector('[data-role="pname"]').addEventListener('click', () => router.show('product_detail', { product_id: item.product_id }));
      }
      const isReviewed = Boolean(item.is_reviewed || item.reviewed);
      const isSkipped = Boolean(item.is_review_skipped);
      if (status === 'completed') {
        if (isReviewed) {
          const pill = document.createElement('span');
          pill.className = 'pill pill-success';
          pill.style.fontSize = '11px';
          pill.textContent = '✓ รีวิวแล้ว';
          r.querySelector('[data-role="rev-slot"]').appendChild(pill);
        } else if (isSkipped) {
          const pill = document.createElement('span');
          pill.className = 'pill pill-neutral';
          pill.style.fontSize = '11px';
          pill.textContent = 'ไม่รีวิว';
          r.querySelector('[data-role="rev-slot"]').appendChild(pill);
        }
      }
      itemsList.appendChild(r);
    }

    const actionsEl = wrap.querySelector('[data-role="actions"]');
    const addAction = (txt, cls, fn) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = `btn ${cls} btn-md`;
      b.style.width = '100%';
      b.textContent = txt;
      b.addEventListener('click', fn);
      actionsEl.appendChild(b);
      return b;
    };

    if (status === 'pending') {
      addAction('ชำระเงิน / แนบสลิป', 'btn-primary', () => router.show('payment', { order_id: order.id }));
      addAction('ยกเลิกคำสั่งซื้อ', 'btn-danger', async () => {
        const reason = await askReason('ยกเลิกคำสั่งซื้อ', 'ระบุเหตุผลที่ต้องการยกเลิก (สินค้าจะถูกคืนเข้าสต็อก)', { required: true, confirmText: 'ยกเลิกคำสั่งซื้อ', danger: true });
        if (reason === null) return;
        try {
          await api.post(`/api/orders/${order.id}/cancel`, { reason });
          await router.refresh_shell();
          showToast('ยกเลิกคำสั่งซื้อเรียบร้อยแล้ว', 'success');
          await load('', true);
        } catch (err) {
          const em = err.message || 'ยกเลิกคำสั่งซื้อไม่สำเร็จ';
          showToast(em, 'error');
          await load(`⛔ ${em}`, false);
        }
      });
    } else if (status === 'checking_slip') {
      addAction('ดูสถานะการชำระเงิน / สลิป', 'btn-outline', () => router.show('payment', { order_id: order.id }));
    } else if (status === 'shipped') {
      addAction('✓ ได้รับสินค้าแล้ว', 'btn-success', async () => {
        const okConfirm = await confirm('ยืนยันการรับสินค้า', 'ยืนยันว่าได้รับสินค้าครบถ้วนแล้วใช่ไหม?', { confirmText: 'ได้รับแล้ว' });
        if (!okConfirm) return;
        try {
          await api.post(`/api/orders/${order.id}/confirm-received`);
          await router.refresh_shell();
          showToast('ยืนยันการรับสินค้าสำเร็จ — คุณสามารถเขียนรีวิวสินค้าได้จากหน้าออเดอร์ของฉัน', 'success');
          await load('', true);
        } catch (err) {
          const em = err.message || 'ไม่สามารถยืนยันการรับสินค้าได้';
          showToast(em, 'error');
          await load(`⛔ ${em}`, false);
        }
      });
    }
    if (RECEIPT_STATUSES.has(status)) {
      addAction('เปิดใบเสร็จ PDF (รวม VAT 7%)', 'btn-primary', () => {
        window.open(`/api/orders/${order.id}/receipt.pdf`, '_blank', 'noopener');
      });
      addAction('ส่งใบเสร็จเข้าอีเมล', 'btn-info', async () => {
        try {
          const res = await api.post(`/api/orders/${order.id}/send-receipt-email`);
          msgEl.textContent = '';
          showToast(`${res.message || 'ดำเนินการส่งใบเสร็จทางอีเมลแล้ว'} (สถานะ: ${res.status || 'sent'})`, 'success');
        } catch (err) {
          const em = err.message || 'ส่งใบเสร็จไม่สำเร็จ';
          msgEl.className = 'text-small text-danger';
          msgEl.textContent = `⛔ ${em}`;
          showToast(em, 'error');
        }
      });
    }
    addAction('ไปหน้าออเดอร์ของฉัน', 'btn-ghost', () => router.show('orders'));
  }

  await load();
}
