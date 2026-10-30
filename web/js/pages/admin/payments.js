// web/js/pages/admin/payments.js — ตรวจสลิปโอนเงิน (ยืนยันสลิปออกใบเสร็จ PDF + ส่งเมล + แจกคูปองตามกฎ, ปฏิเสธสลิปพร้อมเหตุผล)
import { api, esc, formatDateTime, formatPrice } from '../../api.js';
import { pillHtml, showImageWindow } from '../../components/admin_common.js';
import { askReason, confirm, showToast } from '../../components/dialogs.js';

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">ตรวจสลิปโอนเงิน</div>
        <div class="text-small text-muted">สลิปโอนเงินที่รอการตรวจสอบ (เก่าสุดก่อน)</div>
      </div>
      <button type="button" class="btn btn-outline btn-sm" data-role="refresh">🔄 รีเฟรช</button>
    </div>

    <div class="text-small text-danger" data-role="err"></div>
    <div class="text-small-bold text-success" data-role="notice" style="margin-bottom:6px"></div>
    <div data-role="list" style="display:flex;flex-direction:column;gap:8px"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const noticeEl = wrap.querySelector('[data-role="notice"]');
  const listEl = wrap.querySelector('[data-role="list"]');

  wrap.querySelector('[data-role="refresh"]').addEventListener('click', () => {
    noticeEl.textContent = '';
    load();
  });

  async function load(keepError = false) {
    if (!keepError) errEl.textContent = '';
    listEl.innerHTML = '';
    try {
      const rows = await api.get('/api/admin/payments/pending');
      await router.refresh_shell();
      if (!rows || !rows.length) {
        listEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">🎉 ไม่มีสลิปที่รอตรวจ</div>`;
        return;
      }

      const hdr = document.createElement('div');
      hdr.className = 'text-body-bold';
      hdr.textContent = `รอตรวจ ${rows.length} รายการ`;
      listEl.appendChild(hdr);

      for (const p of rows) {
        const paymentId = p.id;
        const orderId = p.order_id;
        const amount = Number(p.amount || 0);
        const orderTotal = Number(p.order_total || 0);
        const mismatch = Math.abs(amount - orderTotal) > 0.005;
        const slipUrl = `/api/files/slips/${paymentId}?t=${Date.now()}`;
        const title = `สลิปออเดอร์ #${orderId}`;

        const card = document.createElement('div');
        card.className = 'card';
        card.style.padding = '12px 14px';
        card.style.display = 'grid';
        card.style.gridTemplateColumns = '160px 1fr 160px';
        card.style.gap = '14px';
        card.style.alignItems = 'center';

        card.innerHTML = `
          <div style="display:flex;flex-direction:column;align-items:center">
            ${p.slip_path ? `
              <img src="${esc(slipUrl)}" alt="${esc(title)}" style="width:150px;height:200px;object-fit:contain;border-radius:8px;background:var(--color-surface-alt);cursor:pointer" data-role="slip-img" />
              <button type="button" class="btn btn-outline btn-sm" data-role="zoom" style="width:150px;margin-top:6px">🔍 ดูขยาย</button>
            ` : `<div class="text-small text-danger" style="width:150px;height:200px;display:flex;align-items:center;justify-content:center">ไม่พบรูปสลิป</div>`}
          </div>
          <div>
            <div style="display:flex;align-items:center;gap:10px">
              <span class="text-h3">ออเดอร์ #${orderId}</span>
              ${pillHtml('รอตรวจสลิป', 'warning')}
            </div>
            <div class="text-body" style="margin-top:4px">ผู้ซื้อ: ${esc(p.buyer_name || '-')} (@${esc(p.buyer_username || '-')})</div>
            <div class="text-small text-muted">แนบเมื่อ ${esc(formatDateTime(p.created_at))}</div>
            <div class="text-price-big" style="margin-top:8px">ยอดที่โอน ${esc(formatPrice(amount))}</div>
            <div class="text-small text-muted">ยอดออเดอร์ ${esc(formatPrice(orderTotal))}</div>
            ${mismatch ? `<div class="text-small text-danger" style="margin-top:4px">⚠️ ยอดในระบบไม่ตรงกับยอดออเดอร์ — ตรวจสลิปให้ละเอียด</div>` : ''}
            <div class="text-tiny text-muted" style="margin-top:6px">ตรวจชื่อผู้รับ ยอดเงิน และวันเวลาในสลิปให้ตรงกับออเดอร์ก่อนกดยืนยัน</div>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px">
            <button type="button" class="btn btn-success btn-md" data-role="verify">✅ ยืนยันสลิป</button>
            <button type="button" class="btn btn-danger btn-md" data-role="reject">❌ ปฏิเสธสลิป</button>
            <button type="button" class="btn btn-outline btn-md" data-role="view-order">ดูออเดอร์</button>
          </div>
        `;

        const imgEl = card.querySelector('[data-role="slip-img"]');
        const zoomBtn = card.querySelector('[data-role="zoom"]');
        if (imgEl) imgEl.addEventListener('click', () => showImageWindow(slipUrl, title));
        if (zoomBtn) zoomBtn.addEventListener('click', () => showImageWindow(slipUrl, title));

        card.querySelector('[data-role="verify"]').addEventListener('click', async () => {
          const ok = await confirm(
            'ยืนยันสลิป',
            `ยืนยันว่าได้รับเงิน ${formatPrice(amount)} ของออเดอร์ #${orderId} แล้วใช่ไหม?
ออเดอร์จะเปลี่ยนเป็น “ชำระแล้ว” พร้อมออกใบเสร็จ PDF และพร้อมให้บันทึกการจัดส่ง`,
            { confirmText: 'ยืนยันสลิป' }
          );
          if (!ok) return;
          errEl.textContent = '';
          try {
            await api.post(`/api/admin/payments/${paymentId}/verify`);
            noticeEl.textContent = '';
            showToast(`ยืนยันสลิปออเดอร์ #${orderId} สำเร็จ — ออกใบเสร็จและแจ้งลูกค้าเรียบร้อย`, 'success');
            await load();
          } catch (err) {
            const em = err.message || 'ยืนยันสลิปไม่สำเร็จ';
            errEl.textContent = `⛔ ${em}`;
            showToast(em, 'error');
            await load(true);
          }
        });

        card.querySelector('[data-role="reject"]').addEventListener('click', async () => {
          const reason = await askReason(
            'ปฏิเสธสลิป',
            `ระบุเหตุผลที่ปฏิเสธสลิปของออเดอร์ #${orderId} (ผู้ซื้อจะเห็นข้อความนี้)`,
            {
              required: true,
              confirmText: 'ปฏิเสธสลิป',
              placeholder: 'เช่น ยอดเงินไม่ตรง / สลิปไม่ชัด / ไม่ใช่สลิปของร้านนี้',
              danger: true,
            }
          );
          if (!reason) return;
          errEl.textContent = '';
          try {
            await api.post(`/api/admin/payments/${paymentId}/reject`, { reason });
            noticeEl.textContent = '';
            showToast(`ปฏิเสธสลิปออเดอร์ #${orderId} แล้ว — แจ้งเตือนผู้ซื้อเรียบร้อย`, 'success');
            await load();
          } catch (err) {
            const em = err.message || 'ปฏิเสธสลิปไม่สำเร็จ';
            errEl.textContent = `⛔ ${em}`;
            showToast(em, 'error');
            await load(true);
          }
        });

        card.querySelector('[data-role="view-order"]').addEventListener('click', () => router.show('admin_order_detail', { order_id: orderId }));
        listEl.appendChild(card);
      }
    } catch (err) {
      errEl.textContent = err.message || 'โหลดรายการสลิปไม่สำเร็จ';
    }
  }

  await load();
}
