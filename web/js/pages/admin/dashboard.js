// web/js/pages/admin/dashboard.js — หน้าแดชบอร์ดจัดการร้าน (กราฟแท่งรายวัน SVG/Canvas, สลิปรอตรวจ, รายได้เฉพาะ Owner, ออเดอร์ตามสถานะ, สินค้าขายดี, สต็อกต่ำ)
import { api, esc, formatPrice, ORDER_STATUS_LABELS } from '../../api.js';
import { state } from '../../state.js';
import { createSegmented } from '../../components/admin_common.js';
import { openModal, showMessage } from '../../components/dialogs.js';

const PERIODS = [
  [7,  '7 วัน'],
  [14, '14 วัน'],
  [30, '30 วัน'],
];
const ORDER_STATUSES = ['pending', 'checking_slip', 'paid', 'shipped', 'completed', 'cancelled'];
const LIST_LIMIT = 8;

function renderBarChartSvg(series = [], isMoney = false) {
  if (!series.length) {
    return `<div class="text-small text-muted" style="text-align:center;padding:70px 0">ยังไม่มีข้อมูล</div>`;
  }
  const W = 780;
  const H = 220;
  const padL = 16;
  const padR = 16;
  const padT = 26;
  const padB = 30;
  const baseY = H - padB;
  const plotH = baseY - padT;
  const n = series.length;
  const top = Math.max(...series.map(([, v]) => Number(v || 0)), 1);
  const slot = (W - padL - padR) / n;
  const barW = Math.max(6, slot * 0.58);
  const step = n <= 10 ? 1 : (n <= 20 ? 2 : 5);

  let bars = `<line x1="${padL}" y1="${baseY}" x2="${W - padR}" y2="${baseY}" stroke="var(--color-border)" stroke-width="1"/>`;
  series.forEach(([day, rawVal], i) => {
    const val = Number(rawVal || 0);
    const cx = padL + slot * i + slot / 2;
    const barH = val > 0 ? (val / top) * plotH : 0;
    if (barH > 0) {
      bars += `<rect x="${(cx - barW / 2).toFixed(1)}" y="${(baseY - barH).toFixed(1)}" width="${barW.toFixed(1)}" height="${barH.toFixed(1)}" rx="3" fill="var(--color-primary)"/>`;
    }
    if (n <= 14 && val > 0) {
      bars += `<text x="${cx.toFixed(1)}" y="${(baseY - barH - 6).toFixed(1)}" text-anchor="middle" font-family="Arimo, sans-serif" font-size="10" fill="var(--color-text-muted)">${Math.round(val).toLocaleString()}</text>`;
    }
    if (i % step === 0) {
      const label = String(day).slice(5) || String(day);
      bars += `<text x="${cx.toFixed(1)}" y="${baseY + 15}" text-anchor="middle" font-family="Arimo, sans-serif" font-size="10" fill="var(--color-text-muted)">${esc(label)}</text>`;
    }
  });

  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:220px;display:block">${bars}</svg>`;
}

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let days = 7;

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">แดชบอร์ดจัดการร้าน</div>
        <div class="text-small text-muted">ภาพรวมออเดอร์ สต็อก และยอดขาย</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap" data-role="actions">
        <span data-role="seg-slot"></span>
        <button type="button" class="btn btn-danger btn-sm" data-role="contact-owner">📞 ติดต่อเจ้าของร้าน</button>
        <button type="button" class="btn btn-outline btn-sm" data-role="refresh">🔄 รีเฟรช</button>
      </div>
    </div>
    <div class="text-small text-danger" data-role="err"></div>
    <div data-role="dynamic"></div>
  `;

  const seg = createSegmented(PERIODS, days, (val) => {
    days = Number(val);
    load();
  });
  wrap.querySelector('[data-role="seg-slot"]').appendChild(seg.el);
  const errEl = wrap.querySelector('[data-role="err"]');
  const dynEl = wrap.querySelector('[data-role="dynamic"]');

  wrap.querySelector('[data-role="refresh"]').addEventListener('click', () => load());
  wrap.querySelector('[data-role="contact-owner"]').addEventListener('click', () => openContactOwnerDialog());

  async function load() {
    errEl.textContent = '';
    dynEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">กำลังโหลด...</div>`;
    try {
      const data = await api.get('/api/admin/dashboard', { days });
      const owner = state.is_owner;
      const counts = data.counts || {};
      const pending = Array.isArray(data.pending_slips) ? data.pending_slips.length : Number(data.pending_slips || 0);
      const low = data.low_stock || {};

      const daily = (data.daily_sales || []).map((d) => [
        d.day || '',
        owner ? Number(d.revenue || 0) : Number(d.orders || 0),
      ]);

      const lowEntries = [];
      for (const p of low.products || []) {
        lowEntries.push({ name: p.name || '-', stock: p.stock || 0, product_id: p.id });
      }
      for (const o of low.options || []) {
        const nm = o.product_name || o.name || '-';
        const opt = `${o.option_type || ''} ${o.option_value || ''}`.trim();
        lowEntries.push({ name: opt ? `${nm} — ${opt}` : nm, stock: o.stock || 0, product_id: o.product_id });
      }

      const topProducts = data.top_products || [];

      dynEl.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(${owner ? 4 : 2}, 1fr);gap:10px">
          <div class="card" data-role="card-pending" style="padding:12px 14px;cursor:pointer">
            <div class="text-small text-muted">สลิปรอตรวจ</div>
            <div class="text-h2 ${pending > 0 ? 'text-danger' : ''}">${pending}</div>
            <div class="text-tiny text-muted">คลิกเพื่อไปตรวจสลิป</div>
          </div>
          ${owner ? `
            <div class="card" style="padding:12px 14px">
              <div class="text-small text-muted">รายได้วันนี้</div>
              <div class="text-h2">${esc(formatPrice(data.revenue_today))}</div>
            </div>
            <div class="card" style="padding:12px 14px">
              <div class="text-small text-muted">รายได้เดือนนี้</div>
              <div class="text-h2">${esc(formatPrice(data.revenue_month))}</div>
            </div>
            <div class="card" data-role="card-export" style="padding:12px 14px;cursor:pointer">
              <div class="text-small text-muted">รายได้รวม (คลิกส่งออก .xlsx)</div>
              <div class="text-h2">${esc(formatPrice(data.revenue_total))}</div>
            </div>
          ` : `
            <div class="card" style="padding:12px 14px">
              <div class="text-small text-muted">รายได้</div>
              <div class="text-h2">—</div>
              <div class="text-tiny text-muted">แสดงเฉพาะเจ้าของร้าน</div>
            </div>
          `}
        </div>

        <div class="text-h3" style="margin:14px 0 4px">ออเดอร์ตามสถานะ</div>
        <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:10px">
          ${ORDER_STATUSES.map((st) => `
            <div class="card" data-status="${st}" style="padding:12px 14px;cursor:pointer">
              <div class="text-small text-muted">${esc(ORDER_STATUS_LABELS[st] || st)}</div>
              <div class="text-h2">${Number(counts[st] || 0).toLocaleString()}</div>
            </div>
          `).join('')}
        </div>

        <div class="text-h3" style="margin:14px 0 4px">${owner ? `ยอดขายรายวัน (${days} วันล่าสุด)` : `จำนวนออเดอร์รายวัน (${days} วันล่าสุด)`}</div>
        <div class="card" style="padding:10px">
          ${renderBarChartSvg(daily, owner)}
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px">
          <div class="card" style="padding:12px 14px">
            <div class="text-h3" style="margin-bottom:6px">🏆 สินค้าขายดี</div>
            ${!topProducts.length ? `<div class="text-small text-muted">ยังไม่มีข้อมูลการขาย</div>` : topProducts.slice(0, LIST_LIMIT).map((it, idx) => `
              <div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;gap:8px">
                <span class="text-body"><strong>${idx + 1}.</strong> ${esc(it.product_name || '-')}</span>
                <span class="text-small text-muted">${Number(it.total_qty || 0).toLocaleString()} ชิ้น${owner ? `  ·  ${esc(formatPrice(it.total_sales))}` : ''}</span>
              </div>
            `).join('')}
          </div>

          <div class="card" style="padding:12px 14px">
            <div class="text-h3" style="margin-bottom:6px">⚠️ สินค้าสต็อกต่ำ${low.threshold != null ? ` (≤ ${low.threshold})` : ''}</div>
            ${!lowEntries.length ? `<div class="text-small text-muted">ไม่มีสินค้าใกล้หมด 👍</div>` : lowEntries.slice(0, LIST_LIMIT).map((e) => `
              <div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;gap:8px">
                <span class="text-body" style="flex:1">${esc(e.name)}</span>
                <span class="text-small-bold text-danger">${!e.stock ? 'หมด' : `เหลือ ${e.stock}`}</span>
                ${e.product_id != null ? `<button type="button" class="btn btn-outline btn-sm" data-edit-prod="${e.product_id}" style="height:28px">แก้ไข</button>` : ''}
              </div>
            `).join('')}
            ${lowEntries.length > LIST_LIMIT ? `<div class="text-tiny text-muted" style="margin-top:4px">และอีก ${lowEntries.length - LIST_LIMIT} รายการ — ดูทั้งหมดที่หน้าสินค้า</div>` : ''}
          </div>
        </div>
      `;

      dynEl.querySelector('[data-role="card-pending"]').addEventListener('click', () => router.show('admin_payments'));
      const expCard = dynEl.querySelector('[data-role="card-export"]');
      if (expCard) expCard.addEventListener('click', () => router.show('admin_settings'));
      dynEl.querySelectorAll('[data-status]').forEach((el) => {
        el.addEventListener('click', () => router.show('admin_orders', { status: el.dataset.status }));
      });
      dynEl.querySelectorAll('[data-edit-prod]').forEach((el) => {
        el.addEventListener('click', () => router.show('admin_product_form', { product_id: Number(el.dataset.editProd) }));
      });
    } catch (err) {
      errEl.textContent = err.message || 'โหลดข้อมูลไม่สำเร็จ';
      dynEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">โหลดข้อมูลไม่สำเร็จ</div>`;
    }
  }

  await load();
}

async function openContactOwnerDialog() {
  let c = {};
  try { c = await api.get('/api/settings/contact'); } catch (e) {}
  const senderName = (state.user && (state.user.full_name || state.user.username)) || 'Admin';
  openModal({
    title: 'ติดต่อเจ้าของร้าน / ส่งข้อความด่วน',
    width: 480,
    render(card, close) {
      card.innerHTML = `
        <div class="text-h3" style="margin-bottom:4px">📞 ติดต่อเจ้าของร้าน</div>
        <div class="card-alt" style="padding:10px 12px;margin-bottom:10px">
          <div><strong>ผู้ดูแล:</strong> ${esc(c.owner_name || c.shop_name || 'เจ้าของร้าน')}</div>
          <div><strong>โทร:</strong> ${esc(c.phone || '-')}   |   <strong>อีเมล:</strong> ${esc(c.email || '-')}</div>
          ${c.line_id ? `<div><strong>LINE:</strong> ${esc(c.line_id)}</div>` : ''}
        </div>
        <div class="text-small-bold" style="margin-bottom:4px">ส่งข้อความด่วนถึงเจ้าของร้าน</div>
        <input type="text" class="input" data-role="subj" value="[แจ้งเรื่องด่วนจากแอดมิน] โดย ${esc(senderName)}" style="margin-bottom:6px" />
        <textarea class="textarea" data-role="body" rows="4" placeholder="ระบุข้อความที่ต้องการแจ้ง..."></textarea>
        <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-top:4px"></div>
        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">
          <button type="button" class="btn btn-outline btn-sm" data-role="cancel">ปิด</button>
          <button type="button" class="btn btn-primary btn-sm" data-role="send">ส่งข้อความ</button>
        </div>
      `;
      card.querySelector('[data-role="cancel"]').addEventListener('click', () => close());
      card.querySelector('[data-role="send"]').addEventListener('click', async () => {
        const subj = card.querySelector('[data-role="subj"]').value.trim();
        const body = card.querySelector('[data-role="body"]').value.trim();
        const err = card.querySelector('[data-role="err"]');
        if (!subj || !body) { err.textContent = 'กรุณากรอกทั้งหัวข้อและข้อความ'; return; }
        try {
          await api.post('/api/contact/urgent-email', { subject: subj, message: body });
          close();
          await showMessage('ส่งข้อความแล้ว', 'บันทึกข้อความด่วนถึงเจ้าของร้านเรียบร้อยแล้ว', 'success');
        } catch (ex) {
          err.textContent = ex.message || 'ส่งไม่สำเร็จ';
        }
      });
    },
  });
}
