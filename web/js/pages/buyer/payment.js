// web/js/pages/buyer/payment.js — หน้าชำระเงิน PromptPay QR + แนบสลิป + VAT 7% (ตรงกับ ui/pages/buyer/payment.py)
import { api, esc, formatPrice, ORDER_STATUS_LABELS } from '../../api.js';
import { createPaymentQR } from '../../components/payment_qr.js';
import { createImagePicker } from '../../components/image_picker.js';
import { askReason, showMessage, showToast } from '../../components/dialogs.js';

export async function render(container, router, params = {}) {
  const orderId = params.order_id || params.id;
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  wrap.style.display = 'flex';
  wrap.style.justifyContent = 'center';
  container.appendChild(wrap);

  const center = document.createElement('div');
  center.style.maxWidth = '860px';
  center.style.width = '100%';
  wrap.appendChild(center);

  center.innerHTML = `
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
      <div class="text-h2" data-role="title">ชำระเงิน</div>
      <span data-role="status-badge"></span>
    </div>
    <div style="display:grid;grid-template-columns:auto 1fr;gap:18px;align-items:start">
      <div data-role="qr-slot"></div>
      <div class="card" style="padding:18px 22px" data-role="state-frame"></div>
    </div>
  `;

  const titleEl = center.querySelector('[data-role="title"]');
  const badgeSlot = center.querySelector('[data-role="status-badge"]');
  const stateFrame = center.querySelector('[data-role="state-frame"]');

  const qrComp = createPaymentQR({ size: 250 });
  center.querySelector('[data-role="qr-slot"]').appendChild(qrComp.el);

  async function load() {
    stateFrame.innerHTML = '';
    badgeSlot.innerHTML = '';
    if (!orderId) {
      titleEl.textContent = 'ชำระเงิน';
      qrComp.clear('ไม่พบคำสั่งซื้อ');
      stateFrame.innerHTML = `<div class="text-body text-danger">⛔ ไม่พบคำสั่งซื้อที่ต้องการชำระเงิน</div>`;
      return;
    }
    titleEl.textContent = `ชำระเงิน · คำสั่งซื้อ #${orderId}`;
    let info = null;
    try {
      info = await api.get(`/api/orders/${orderId}/payment-info`);
    } catch (err) {
      qrComp.clear('ไม่สามารถแสดง QR ได้');
      stateFrame.innerHTML = `<div class="text-body text-danger">⛔ ${esc(err.message)}</div>`;
      return;
    }

    const status = info.order_status;
    const statusLbl = ORDER_STATUS_LABELS[status] || info.order_status_label || status;
    badgeSlot.innerHTML = `<span class="pill pill-${status === 'paid' || status === 'completed' ? 'success' : (status === 'cancelled' ? 'danger' : 'warning')}">${esc(statusLbl)}</span>`;

    if (status === 'pending' || status === 'checking_slip') {
      qrComp.setInfo(info, orderId);
    } else if (status === 'cancelled') {
      qrComp.clear('คำสั่งซื้อนี้ถูกยกเลิกแล้ว');
    } else {
      qrComp.clear('ชำระเงินเรียบร้อยแล้ว');
    }

    const items = info.items || [];
    const preVat = info.pre_vat_amount ?? Math.round((Number(info.amount || 0) / 1.07) * 100) / 100;
    const vatAmt = info.vat_amount ?? Math.round((Number(info.amount || 0) - preVat) * 100) / 100;

    let html = `
      <div class="text-small-bold text-muted">ยอดที่ต้องชำระ (รวม VAT 7%)</div>
      <div class="text-price-big text-danger" style="margin-bottom:8px">${esc(formatPrice(info.amount))}</div>

      <div class="card-alt" style="padding:10px 12px;margin-bottom:10px">
        <div class="text-small-bold" style="margin-bottom:4px">รายการสินค้าที่สั่งซื้อ (${items.length} รายการ)</div>
        ${items.map((it) => `
          <div style="display:flex;justify-content:space-between;padding:2px 0">
            <span class="text-small-bold">• ${esc(it.product_name)} × ${it.qty}</span>
            <span class="text-small-bold text-danger">${esc(formatPrice(it.line_total))}</span>
          </div>
          <div class="text-tiny text-muted" style="margin-bottom:2px">   สเปก/ตัวเลือก: ${esc(it.spec_summary || it.option_label || '-')}</div>
        `).join('')}
        <div class="text-tiny text-muted" style="margin-top:6px;padding-top:6px;border-top:1px solid var(--color-border)">
          มูลค่าก่อนภาษี: ${esc(formatPrice(preVat))}   |   ภาษีมูลค่าเพิ่ม (VAT 7%): ${esc(formatPrice(vatAmt))}
        </div>
      </div>
      <div data-role="status-content"></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px" data-role="btn-row">
        <button type="button" class="btn btn-outline btn-md" data-role="go-detail">ดูรายละเอียดคำสั่งซื้อ</button>
        <button type="button" class="btn btn-outline btn-md" data-role="go-orders">ออเดอร์ของฉัน</button>
        ${status === 'pending' ? `<button type="button" class="btn btn-danger btn-md" data-role="cancel-btn">ยกเลิกคำสั่งซื้อ</button>` : ''}
      </div>
    `;
    stateFrame.innerHTML = html;

    const statusContent = stateFrame.querySelector('[data-role="status-content"]');

    if (status === 'pending') {
      const payment = info.payment;
      let rejectHtml = '';
      if (payment && payment.status === 'rejected') {
        rejectHtml = `<div class="text-body text-danger" style="margin-bottom:8px;white-space:pre-line">⚠ สลิปครั้งก่อนถูกปฏิเสธ: ${esc(payment.reject_reason || 'ไม่ระบุเหตุผล')}
กรุณาตรวจสอบแล้วแนบสลิปใหม่อีกครั้ง</div>`;
      }
      const hours = Number(info.unpaid_cancel_hours || 24);
      statusContent.innerHTML = `
        ${rejectHtml}
        <div class="text-body-bold" style="margin-top:6px">วิธีชำระเงิน & แนบสลิปโอนเงิน</div>
        <div class="text-small text-muted" style="white-space:pre-line">1) สแกน QR ด้วยแอปธนาคาร และโอนตามยอดข้างต้น
2) บันทึกสลิปการโอนเป็นรูป (jpg / png ไม่เกิน 5 MB)
3) แนบสลิปด้านล่าง แล้วกด "ส่งสลิป"</div>
        ${hours > 0 ? `<div class="text-small text-muted" style="margin-top:2px">* กรุณาชำระภายใน ${hours} ชั่วโมง มิฉะนั้นระบบจะยกเลิกคำสั่งซื้ออัตโนมัติ</div>` : ''}
        <div data-role="picker-wrap" style="display:flex;justify-content:center;margin-top:10px"></div>
        <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-top:6px"></div>
        <div style="display:flex;justify-content:center;margin-top:8px">
          <button type="button" class="btn btn-primary btn-lg" data-role="submit-slip" style="min-width:220px">ส่งสลิปชำระเงิน</button>
        </div>
      `;

      const slipPicker = createImagePicker({
        size: [220, 240],
        buttonText: 'เลือกสลิป...',
        allowClear: false,
      });
      statusContent.querySelector('[data-role="picker-wrap"]').appendChild(slipPicker.el);
      const errEl = statusContent.querySelector('[data-role="err"]');
      const subBtn = statusContent.querySelector('[data-role="submit-slip"]');

      subBtn.addEventListener('click', async () => {
        const file = slipPicker.getSelectedFile();
        if (!file) {
          errEl.textContent = '⛔ กรุณาเลือกไฟล์สลิปก่อนกดส่ง'; showToast('กรุณาเลือกไฟล์สลิปก่อนกดส่ง', 'error');
          return;
        }
        errEl.textContent = '';
        subBtn.disabled = true;
        try {
          const fd = new FormData();
          fd.append('file', file);
          await api.uploadForm(`/api/orders/${orderId}/slip`, fd);
          await router.refresh_shell();
          await showMessage('ส่งสลิปเรียบร้อย', 'ระบบแจ้งแอดมินให้ตรวจสอบสลิปของคุณแล้ว', 'success');
          await load();
        } catch (err) {
          subBtn.disabled = false;
          errEl.textContent = `⛔ ${err.message}`; showToast(err.message || 'อัปโหลดสลิปไม่สำเร็จ', 'error');
        }
      });
    } else if (status === 'checking_slip') {
      statusContent.innerHTML = `
        <div class="text-body-bold" style="margin-top:8px">ส่งสลิปแล้ว — รอแอดมินตรวจสอบ</div>
        <div class="text-small text-muted">เมื่อตรวจสลิปเรียบร้อย ระบบจะแจ้งเตือนคุณ และสถานะคำสั่งซื้อจะเปลี่ยนเป็น "ชำระเงินแล้ว" พร้อมออกใบเสร็จ (รวม VAT 7%)</div>
        <div style="display:flex;flex-direction:column;align-items:center;margin-top:12px">
          <img src="/api/orders/${orderId}/slip-image?t=${Date.now()}" alt="สลิปที่ส่ง" style="max-width:180px;max-height:240px;object-fit:contain;border-radius:8px;border:1px solid var(--color-border)" />
          <span class="text-tiny text-muted" style="margin-top:4px">สลิปที่ส่ง</span>
        </div>
      `;
    } else if (status === 'cancelled') {
      statusContent.innerHTML = `<div class="text-body text-danger" style="margin-top:10px">คำสั่งซื้อนี้ถูกยกเลิกแล้ว ไม่ต้องชำระเงิน</div>`;
    } else {
      statusContent.innerHTML = `<div class="text-body-bold text-success" style="margin-top:10px">✓ ชำระเงินเรียบร้อยแล้ว (สถานะ: ${esc(statusLbl)})</div>`;
    }

    stateFrame.querySelector('[data-role="go-detail"]').addEventListener('click', () => router.show('order_detail', { order_id: orderId }));
    stateFrame.querySelector('[data-role="go-orders"]').addEventListener('click', () => router.show('orders'));
    const cancelBtn = stateFrame.querySelector('[data-role="cancel-btn"]');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', async () => {
        const reason = await askReason(
          'ยกเลิกคำสั่งซื้อ',
          'ระบุเหตุผลที่ต้องการยกเลิก (สินค้าจะถูกคืนเข้าสต็อก)',
          { required: true, confirmText: 'ยกเลิกคำสั่งซื้อ', danger: true }
        );
        if (reason === null) return;
        try {
          await api.post(`/api/orders/${orderId}/cancel`, { reason });
          await router.refresh_shell();
          await load();
        } catch (err) {
          await showMessage('ยกเลิกไม่ได้', err.message || '', 'error');
          await load();
        }
      });
    }
  }

  await load();
}
