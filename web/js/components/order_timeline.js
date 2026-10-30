// web/js/components/order_timeline.js — ไทม์ไลน์สถานะออเดอร์ + ข้อมูลขนส่ง (ตรงกับ ui/components/order_timeline.py)
import { esc, formatDateTime, ORDER_STATUS_LABELS } from '../api.js';

export function createOrderTimeline(timeline = [], shipment = null) {
  const wrap = document.createElement('div');
  wrap.style.display = 'flex';
  wrap.style.flexDirection = 'column';
  wrap.style.gap = '4px';

  function setData(tl = [], ship = null) {
    wrap.innerHTML = '';
    if (ship && (ship.carrier || ship.tracking_no)) {
      const shipBox = document.createElement('div');
      shipBox.className = 'card-alt';
      shipBox.style.padding = '10px 14px';
      shipBox.style.marginBottom = '10px';
      shipBox.innerHTML = `
        <div class="text-body-bold" style="margin-bottom:2px">🚚 ข้อมูลการจัดส่ง</div>
        <div class="text-body">ขนส่ง: ${esc(ship.carrier || '-')}<br/>เลขพัสดุ: ${esc(ship.tracking_no || '-')}</div>
      `;
      wrap.appendChild(shipBox);
    }

    const entries = Array.isArray(tl) ? tl : [];
    if (!entries.length) {
      const empty = document.createElement('div');
      empty.className = 'text-small text-muted';
      empty.textContent = 'ยังไม่มีความเคลื่อนไหว';
      wrap.appendChild(empty);
      return;
    }

    entries.forEach((entry, idx) => {
      const isLast = idx === entries.length - 1;
      const status = entry.status || '';
      const cancelled = status === 'cancelled';
      const dotColor = cancelled
        ? 'var(--color-danger)'
        : (isLast ? 'var(--color-primary)' : 'var(--color-star-off)');
      const titleClass = isLast ? 'text-body-bold' : 'text-body';
      const titleColor = isLast
        ? (cancelled ? 'var(--color-danger)' : 'var(--color-text-main)')
        : 'var(--color-text-muted)';

      let meta = formatDateTime(entry.created_at);
      if (entry.changed_by_name) {
        meta += ` · โดย ${entry.changed_by_name}`;
      }

      const row = document.createElement('div');
      row.style.display = 'grid';
      row.style.gridTemplateColumns = '22px 1fr';
      row.style.gap = '8px';

      row.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center">
          <span style="color:${dotColor};font-size:${isLast ? '16px' : '12px'};line-height:1.2">●</span>
          ${!isLast ? `<div style="width:2px;flex:1;background:var(--color-border);min-height:18px"></div>` : ''}
        </div>
        <div style="padding-bottom:10px">
          <div class="${titleClass}" style="color:${titleColor}">${esc(ORDER_STATUS_LABELS[status] || status)}</div>
          <div class="text-small text-muted">${esc(meta)}</div>
          ${entry.note ? `<div class="text-small text-main" style="margin-top:2px;white-space:pre-line">${esc(entry.note)}</div>` : ''}
        </div>
      `;
      wrap.appendChild(row);
    });
  }

  setData(timeline, shipment);

  return {
    el: wrap,
    setData,
    setOrder(order) {
      if (!order) return setData([], null);
      setData(order.timeline || [], order.shipment || null);
    },
  };
}
