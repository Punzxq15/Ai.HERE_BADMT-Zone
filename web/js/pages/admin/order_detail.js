// web/js/pages/admin/order_detail.js — รายละเอียดออเดอร์ฝั่งแอดมิน/เจ้าของ (บันทึกเลขพัสดุ+ส่งเมล, VAT 7%, ใบเสร็จ PDF + Toast & Inline Error)
import { api, CARRIERS, esc, formatDateTime, formatPhone, formatPrice, ORDER_STATUS_LABELS, PAYMENT_STATUS_LABELS } from '../../api.js';
import { pillHtml, showImageWindow, thumbHtml } from '../../components/admin_common.js';
import { createOrderTimeline } from '../../components/order_timeline.js';
import { askReason, confirm, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';

const CANCELLABLE = new Set(['pending', 'checking_slip', 'paid']);
const RECEIPT_STATUSES = new Set(['paid', 'shipped', 'completed']);
const TRACKING_RE = /^[A-Za-z0-9-]{4,40}$/;

export async function render(container, router, params = {}) {
  const orderId = params.order_id || params.id;
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  async function load() {
    wrap.innerHTML = '';
    let d = null;
    try {
      d = await api.get(`/api/orders/${orderId}`);
    } catch (err) {
      const em = err.message || 'ไม่พบคำสั่งซื้อ';
      showToast(em, 'error');
      wrap.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <div class="text-h2">ออเดอร์</div>
          <button type="button" class="btn btn-outline btn-sm" data-role="back">← กลับ</button>
        </div>
        <div class="text-danger">⛔ ${esc(em)}</div>
      `;
      wrap.querySelector('[data-role="back"]').addEventListener('click', () => router.go_back('admin_orders'));
      return;
    }

    const status = d.status;
    const stLbl = ORDER_STATUS_LABELS[status] || status;
    const stKind = status === 'completed' || status === 'paid' ? 'success' : (status === 'cancelled' ? 'danger' : 'warning');
    const preVat = d.pre_vat_amount ?? Math.round((Number(d.total || 0) / 1.07) * 100) / 100;
    const vatAmt = d.vat_amount ?? Math.round((Number(d.total || 0) - preVat) * 100) / 100;
    const payment = d.payment;
    const shipment = d.shipment || {};
    const carriers = d.carriers || CARRIERS;

    wrap.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px">
        <div>
          <div class="text-h2">ออเดอร์ #${d.id}</div>
          <div class="text-small text-muted">สั่งเมื่อ ${esc(formatDateTime(d.created_at))}</div>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          ${pillHtml(stLbl, stKind)}
          <button type="button" class="btn btn-outline btn-sm" data-role="back">← กลับ</button>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:3fr 2fr;gap:14px;align-items:start">
        <div style="display:flex;flex-direction:column;gap:12px">
          <div class="card" style="padding:14px 16px">
            <div class="text-h3" style="margin-bottom:8px">รายการสินค้า & สรุปภาษีมูลค่าเพิ่ม (VAT 7%)</div>
            <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:10px">
              ${(d.items || []).map((it) => `
                <div style="display:flex;align-items:center;gap:10px">
                  ${thumbHtml(it.image_path, 44)}
                  <div style="flex:1">
                    <div class="text-body">${esc(it.product_name)}</div>
                    <div class="text-small text-muted">${esc(it.option_label ? `${it.option_label} · ` : '')}${esc(formatPrice(it.price_at_purchase))} × ${it.qty}</div>
                  </div>
                  <div class="text-body-bold">${esc(formatPrice(it.line_total))}</div>
                </div>
              `).join('')}
            </div>
            <div style="border-top:1px solid var(--color-border);padding-top:8px;display:flex;flex-direction:column;gap:3px">
              <div style="display:flex;justify-content:space-between"><span>ราคาสินค้า</span><span>${esc(formatPrice(d.subtotal))}</span></div>
              ${d.discount ? `<div style="display:flex;justify-content:space-between"><span>ส่วนลด${d.coupon_code ? ` (${esc(d.coupon_code)})` : ''}</span><span>-${esc(formatPrice(d.discount))}</span></div>` : ''}
              <div style="display:flex;justify-content:space-between"><span>ค่าจัดส่ง</span><span>${d.shipping_fee ? esc(formatPrice(d.shipping_fee)) : 'ฟรี'}</span></div>
              <div style="display:flex;justify-content:space-between"><span>มูลค่าก่อนภาษี</span><span>${esc(formatPrice(preVat))}</span></div>
              <div style="display:flex;justify-content:space-between"><span>ภาษีมูลค่าเพิ่ม (VAT 7%)</span><span>${esc(formatPrice(vatAmt))}</span></div>
              <div style="display:flex;justify-content:space-between;padding-top:4px" class="text-body-bold"><span>ยอดรวมสุทธิ (รวม VAT 7%)</span><span class="text-price">${esc(formatPrice(d.total))}</span></div>
            </div>
          </div>

          <div class="card" style="padding:14px 16px">
            <div class="text-h3" style="margin-bottom:8px">ความคืบหน้า</div>
            <div data-role="tl-slot"></div>
          </div>
        </div>

        <div style="display:flex;flex-direction:column;gap:12px">
          <div class="card" style="padding:14px 16px">
            <div class="text-h3" style="margin-bottom:6px">ผู้ซื้อ / ที่อยู่จัดส่ง</div>
            <div class="text-small text-muted">บัญชี: ${esc(d.buyer_name || '-')} (@${esc(d.buyer_username || '-')})</div>
            <div class="text-body-bold" style="margin-top:6px">ผู้รับ: ${esc(d.recipient_name || '-')}</div>
            <div class="text-body">โทร ${esc(formatPhone(d.recipient_phone))}</div>
            <div class="text-body" style="margin-top:4px">${esc(d.shipping_address || '-')}</div>
          </div>

          <div class="card" style="padding:14px 16px" data-role="pay-card">
            <div class="text-h3" style="margin-bottom:6px">การชำระเงิน (รวม VAT 7%)</div>
            ${!payment ? `<div class="text-small text-muted">ยังไม่มีการแนบสลิป</div>` : `
              <div style="display:flex;justify-content:space-between;align-items:center">
                ${pillHtml(PAYMENT_STATUS_LABELS[payment.status] || payment.status || '-', payment.status === 'verified' ? 'success' : (payment.status === 'rejected' ? 'danger' : 'warning'))}
                <span class="text-body-bold">ยอด ${esc(formatPrice(payment.amount))}</span>
              </div>
              ${payment.reject_reason ? `<div class="text-small text-danger" style="margin-top:4px">เหตุผลที่ปฏิเสธ: ${esc(payment.reject_reason)}</div>` : ''}
              ${payment.slip_path ? `
                <div style="display:flex;flex-direction:column;align-items:center;margin-top:8px">
                  <img src="/api/orders/${d.id}/slip-image?t=${Date.now()}" alt="สลิป" style="max-width:200px;max-height:240px;object-fit:contain;border-radius:8px;cursor:pointer" data-role="slip-img" />
                  <button type="button" class="btn btn-outline btn-sm" data-role="zoom-slip" style="margin-top:6px">ดูสลิปขยาย</button>
                </div>
              ` : ''}
              ${(status === 'checking_slip' && payment.status !== 'verified') ? `
                <button type="button" class="btn btn-primary btn-sm" data-role="go-verify" style="width:100%;margin-top:8px">ไปหน้าตรวจสลิป (ยืนยัน/ปฏิเสธ)</button>
              ` : ''}
            `}
          </div>

          <div data-role="ship-slot"></div>
          <div data-role="actions-slot"></div>
        </div>
      </div>
    `;

    wrap.querySelector('[data-role="back"]').addEventListener('click', () => router.go_back('admin_orders'));
    wrap.querySelector('[data-role="tl-slot"]').appendChild(createOrderTimeline(d.timeline || [], d.shipment || null).el);

    const slipImg = wrap.querySelector('[data-role="slip-img"]');
    const zoomBtn = wrap.querySelector('[data-role="zoom-slip"]');
    const openSlip = () => showImageWindow(`/api/orders/${d.id}/slip-image?t=${Date.now()}`, `สลิปออเดอร์ #${d.id}`);
    if (slipImg) slipImg.addEventListener('click', openSlip);
    if (zoomBtn) zoomBtn.addEventListener('click', openSlip);
    const goVer = wrap.querySelector('[data-role="go-verify"]');
    if (goVer) goVer.addEventListener('click', () => router.show('admin_payments'));

    // Shipment card
    const shipSlot = wrap.querySelector('[data-role="ship-slot"]');
    if (status === 'paid' || status === 'shipped' || status === 'completed') {
      const shipCard = document.createElement('div');
      shipCard.className = 'card';
      shipCard.style.padding = '14px 16px';
      if (status === 'completed') {
        shipCard.innerHTML = `
          <div class="text-h3" style="margin-bottom:6px">การจัดส่ง & แจ้งเลขพัสดุ</div>
          <div class="text-body">ขนส่ง: ${esc(shipment.carrier || '-')}</div>
          <div class="text-body-bold">เลขพัสดุ: ${esc(shipment.tracking_no || '-')}</div>
          <div class="text-small text-muted" style="margin-top:4px">ส่งถึงผู้รับแล้ว</div>
        `;
      } else {
        const curCarrier = carriers.includes(shipment.carrier) ? shipment.carrier : carriers[0];
        shipCard.innerHTML = `
          <div class="text-h3" style="margin-bottom:6px">การจัดส่ง & แจ้งเลขพัสดุ</div>
          <div class="field-group" style="margin-bottom:8px">
            <div class="text-small text-muted">ขนส่ง</div>
            <select class="select" data-role="carrier">
              ${carriers.map((c) => `<option value="${esc(c)}" ${c === curCarrier ? 'selected' : ''}>${esc(c)}</option>`).join('')}
            </select>
          </div>
          <div class="field-group" style="margin-bottom:10px">
            <div class="text-small text-muted">เลขพัสดุ (A-Z, 0-9, - ยาว 4-40 ตัว)</div>
            <input type="text" class="input" data-role="tracking" value="${esc(shipment.tracking_no || '')}" placeholder="เช่น TH1234567890" />
          </div>
          <div style="display:flex;flex-direction:column;gap:6px">
            ${status === 'paid' ? `
              <button type="button" class="btn btn-primary btn-md" data-role="ship-btn">บันทึกการจัดส่ง + แจ้งเลขพัสดุทางอีเมล</button>
            ` : `
              <button type="button" class="btn btn-outline btn-md" data-role="upd-track">อัปเดตเลขพัสดุ</button>
              <button type="button" class="btn btn-info btn-md" data-role="resend-track">ส่งเลขพัสดุทางอีเมลซ้ำ</button>
              <button type="button" class="btn btn-success btn-md" data-role="delivered">ส่งถึงผู้รับแล้ว</button>
            `}
          </div>
        `;

        const carrierSel = shipCard.querySelector('[data-role="carrier"]');
        const trackingIn = shipCard.querySelector('[data-role="tracking"]');

        trackingIn.addEventListener('input', () => {
          clearFieldError(trackingIn);
        });
        carrierSel.addEventListener('change', () => {
          clearFieldError(carrierSel);
        });

        function validateShippingInputs() {
          clearFieldError(carrierSel);
          clearFieldError(trackingIn);
          const carrier = carrierSel.value.trim();
          const trackingNo = trackingIn.value.trim().replace(/\s+/g, '');
          if (!carrier || !carriers.includes(carrier)) {
            const msg = 'กรุณาเลือกขนส่งจากรายการ';
            setFieldError(carrierSel, msg);
            showToast(`ไม่สามารถบันทึกการจัดส่งได้: ${msg}`, 'error');
            return null;
          }
          if (!trackingNo) {
            const msg = 'กรุณากรอกเลขพัสดุ';
            setFieldError(trackingIn, msg);
            showToast(`ไม่สามารถบันทึกการจัดส่งได้: ${msg}`, 'error');
            trackingIn.focus();
            return null;
          }
          if (!TRACKING_RE.test(trackingNo)) {
            const msg = 'เลขพัสดุต้องเป็นตัวอักษรอังกฤษ ตัวเลข หรือ - ยาว 4-40 ตัว';
            setFieldError(trackingIn, msg);
            showToast(`ข้อมูลเลขพัสดุไม่ถูกต้อง: ${msg}`, 'error');
            trackingIn.focus();
            return null;
          }
          return { carrier, tracking_no: trackingNo };
        }

        const shipBtn = shipCard.querySelector('[data-role="ship-btn"]');
        if (shipBtn) {
          shipBtn.addEventListener('click', async () => {
            const valid = validateShippingInputs();
            if (!valid) return;
            try {
              await api.post(`/api/admin/orders/${d.id}/ship`, valid);
              showToast(`บันทึกการจัดส่งและแจ้งเลขพัสดุออเดอร์ #${d.id} สำเร็จ`, 'success');
              await router.refresh_shell();
              await load();
            } catch (err) {
              const em = err.message || 'ไม่สามารถบันทึกการจัดส่งได้';
              setFieldError(trackingIn, em);
              showToast(em, 'error');
            }
          });
        }
        const updBtn = shipCard.querySelector('[data-role="upd-track"]');
        if (updBtn) {
          updBtn.addEventListener('click', async () => {
            const valid = validateShippingInputs();
            if (!valid) return;
            try {
              await api.put(`/api/admin/orders/${d.id}/tracking`, valid);
              showToast(`อัปเดตเลขพัสดุออเดอร์ #${d.id} สำเร็จ`, 'success');
              await load();
            } catch (err) {
              const em = err.message || 'ไม่สามารถอัปเดตเลขพัสดุได้';
              setFieldError(trackingIn, em);
              showToast(em, 'error');
            }
          });
        }
        const resTrackBtn = shipCard.querySelector('[data-role="resend-track"]');
        if (resTrackBtn) {
          resTrackBtn.addEventListener('click', async () => {
            try {
              const res = await api.post(`/api/admin/orders/${d.id}/send-tracking-email`);
              showToast(res.message || 'ส่งอีเมลแจ้งเลขพัสดุให้ลูกค้าเรียบร้อยแล้ว', 'success');
            } catch (err) {
              const em = err.message || 'ส่งอีเมลเลขพัสดุไม่สำเร็จ';
              setFieldError(trackingIn, em);
              showToast(em, 'error');
            }
          });
        }
        const delivBtn = shipCard.querySelector('[data-role="delivered"]');
        if (delivBtn) {
          delivBtn.addEventListener('click', async () => {
            const ok = await confirm('ส่งถึงผู้รับแล้ว', 'ยืนยันว่าพัสดุถึงผู้รับแล้ว? ออเดอร์จะเปลี่ยนเป็น "สำเร็จ"', { confirmText: 'ยืนยัน' });
            if (!ok) return;
            try {
              await api.post(`/api/admin/orders/${d.id}/delivered`);
              showToast(`ยืนยันจัดส่งสำเร็จสำหรับออเดอร์ #${d.id} เรียบร้อยแล้ว`, 'success');
              await router.refresh_shell();
              await load();
            } catch (err) {
              const em = err.message || 'ไม่สามารถเปลี่ยนสถานะเป็นส่งสำเร็จได้';
              showToast(em, 'error');
            }
          });
        }
      }
      shipSlot.appendChild(shipCard);
    }

    // Actions card
    const actionsSlot = wrap.querySelector('[data-role="actions-slot"]');
    if (status === 'cancelled') {
      actionsSlot.innerHTML = `
        <div class="card" style="padding:14px 16px">
          <div class="text-h3 text-danger">ออเดอร์ถูกยกเลิก</div>
          <div class="text-body" style="margin-top:4px">เหตุผล: ${esc(d.cancel_reason || '-')}</div>
        </div>
      `;
    } else if (RECEIPT_STATUSES.has(status) || CANCELLABLE.has(status)) {
      const actCard = document.createElement('div');
      actCard.className = 'card';
      actCard.style.padding = '14px 16px';
      actCard.innerHTML = `
        <div class="text-h3" style="margin-bottom:8px">ใบเสร็จ & การจัดการ</div>
        <div style="display:flex;flex-direction:column;gap:6px">
          ${RECEIPT_STATUSES.has(status) ? `
            <button type="button" class="btn btn-primary btn-md" data-role="open-pdf">สร้าง/เปิดใบเสร็จ PDF (รวม VAT 7%)</button>
            <button type="button" class="btn btn-outline btn-md" data-role="email-pdf">ส่งใบเสร็จ PDF เข้าอีเมลลูกค้า</button>
          ` : ''}
          ${CANCELLABLE.has(status) ? `
            ${status === 'paid' ? `<div class="text-small text-danger">ออเดอร์นี้ชำระเงินแล้ว — ถ้ายกเลิกต้องคืนเงินลูกค้าด้วยตนเอง</div>` : ''}
            <button type="button" class="btn btn-danger btn-md" data-role="cancel-ord">ยกเลิกออเดอร์</button>
          ` : ''}
        </div>
      `;
      const pdfBtn = actCard.querySelector('[data-role="open-pdf"]');
      if (pdfBtn) pdfBtn.addEventListener('click', () => window.open(`/api/orders/${d.id}/receipt.pdf`, '_blank', 'noopener'));
      const emBtn = actCard.querySelector('[data-role="email-pdf"]');
      if (emBtn) {
        emBtn.addEventListener('click', async () => {
          try {
            const res = await api.post(`/api/orders/${d.id}/send-receipt-email`);
            showToast(res.message || 'ดำเนินการส่งใบเสร็จทางอีเมลเรียบร้อยแล้ว', 'success');
          } catch (err) {
            showToast(err.message || 'ส่งใบเสร็จทางอีเมลไม่สำเร็จ', 'error');
          }
        });
      }
      const canBtn = actCard.querySelector('[data-role="cancel-ord"]');
      if (canBtn) {
        canBtn.addEventListener('click', async () => {
          const reason = await askReason('ยกเลิกออเดอร์', `ระบุเหตุผลที่ยกเลิกออเดอร์ #${d.id}`, { required: true, confirmText: 'ยกเลิกออเดอร์', danger: true });
          if (!reason) return;
          try {
            await api.post(`/api/orders/${d.id}/cancel`, { reason });
            showToast(`ยกเลิกออเดอร์ #${d.id} เรียบร้อยแล้ว`, 'success');
            await router.refresh_shell();
            await load();
          } catch (err) {
            showToast(err.message || 'ยกเลิกออเดอร์ไม่สำเร็จ', 'error');
          }
        });
      }
      actionsSlot.appendChild(actCard);
    }
  }

  await load();
}
