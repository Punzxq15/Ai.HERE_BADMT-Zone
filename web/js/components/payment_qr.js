// web/js/components/payment_qr.js — การ์ดแสดง PromptPay QR + ปุ่มบันทึกรูป QR (ตรงกับ ui/components/payment_qr.py)
import { esc, formatPrice } from '../api.js';

export function createPaymentQR({ size = 240 } = {}) {
  const card = document.createElement('div');
  card.className = 'card';
  card.style.padding = '16px 20px';
  card.style.display = 'flex';
  card.style.flexDirection = 'column';
  card.style.alignItems = 'center';
  card.style.textAlign = 'center';

  card.innerHTML = `
    <div class="text-h3" style="margin-bottom:10px">สแกนเพื่อชำระเงิน (PromptPay)</div>
    <div style="width:${size + 20}px;height:${size + 20}px;background:#FFFFFF;border-radius:10px;display:flex;align-items:center;justify-content:center;padding:10px;border:1px solid #E2E8F0" data-role="qr-frame">
      <span class="text-small" style="color:#555555;white-space:pre-line" data-role="qr-text">ยังไม่มีข้อมูลการชำระเงิน</span>
      <img data-role="qr-img" class="hidden" alt="PromptPay QR" style="width:${size}px;height:${size}px;object-fit:contain" />
    </div>
    <div class="text-price-big" data-role="amount" style="margin-top:12px"></div>
    <div class="text-body-bold" data-role="name"></div>
    <div class="text-small text-muted" data-role="number"></div>
    <button type="button" class="btn btn-outline btn-sm" data-role="save" style="width:140px;margin-top:10px" disabled>บันทึกรูป QR</button>
  `;

  const qrText = card.querySelector('[data-role="qr-text"]');
  const qrImg = card.querySelector('[data-role="qr-img"]');
  const amountEl = card.querySelector('[data-role="amount"]');
  const nameEl = card.querySelector('[data-role="name"]');
  const numEl = card.querySelector('[data-role="number"]');
  const saveBtn = card.querySelector('[data-role="save"]');

  let currentOrderId = null;
  let currentQrUrl = null;

  function showText(txt) {
    currentQrUrl = null;
    qrImg.classList.add('hidden');
    qrImg.removeAttribute('src');
    qrText.textContent = txt;
    qrText.classList.remove('hidden');
    saveBtn.disabled = true;
  }

  function clear(txt = 'ยังไม่มีข้อมูลการชำระเงิน') {
    amountEl.textContent = '';
    nameEl.textContent = '';
    numEl.textContent = '';
    showText(txt);
  }

  function setInfo(info, orderId = null) {
    currentOrderId = orderId || (info && info.order_id) || null;
    if (!info) {
      return clear('ไม่พบข้อมูลการชำระเงิน');
    }
    amountEl.textContent = formatPrice(info.amount);
    nameEl.textContent = info.promptpay_name || info.shop_name || '';
    numEl.textContent = info.promptpay_no ? `พร้อมเพย์ ${info.promptpay_no}` : '';

    if (!info.payload) {
      return showText('ร้านยังไม่ได้ตั้งค่าเลขพร้อมเพย์\nกรุณาติดต่อร้านค้า');
    }
    const url = info.qr_png_url || (currentOrderId ? `/api/orders/${currentOrderId}/promptpay-qr?size=${size}` : null);
    if (!url) {
      return showText('สร้าง QR ไม่สำเร็จ');
    }
    currentQrUrl = url;
    qrText.classList.add('hidden');
    qrImg.src = url;
    qrImg.classList.remove('hidden');
    saveBtn.disabled = false;
  }

  qrImg.addEventListener('error', () => {
    showText('สร้าง QR ไม่สำเร็จ');
  });

  saveBtn.addEventListener('click', () => {
    if (!currentQrUrl) return;
    const a = document.createElement('a');
    a.href = currentQrUrl;
    a.download = 'promptpay_qr.png';
    document.body.appendChild(a);
    a.click();
    a.remove();
  });

  return {
    el: card,
    setInfo,
    clear,
  };
}
