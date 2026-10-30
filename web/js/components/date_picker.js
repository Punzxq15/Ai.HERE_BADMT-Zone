// web/js/components/date_picker.js — ตัวเลือกวันที่และวัน-เวลาแบบปฏิทินไทย พ.ศ. + ตารางเลือกเวลาด่วน (คลิกเลือกเวลาได้ทันที)
import { esc, formatDateThai, parseDateTime, THAI_MONTHS_SHORT } from '../api.js';
import { openModal } from './dialogs.js';
import { iconSvg } from './icons.js';

const WEEKDAYS_TH = ['จ.', 'อ.', 'พ.', 'พฤ.', 'ศ.', 'ส.', 'อา.'];

const QUICK_TIME_SLOTS = [
  { label: '00:00 (เที่ยงคืน)', hh: 0, mm: 0, short: '00:00' },
  { label: '06:00 (เช้าตรู่)', hh: 6, mm: 0, short: '06:00' },
  { label: '08:00 (เช้า)', hh: 8, mm: 0, short: '08:00' },
  { label: '09:00 (เปิดร้าน)', hh: 9, mm: 0, short: '09:00' },
  { label: '10:00 (สาย)', hh: 10, mm: 0, short: '10:00' },
  { label: '12:00 (เที่ยงวัน)', hh: 12, mm: 0, short: '12:00' },
  { label: '14:00 (บ่าย)', hh: 14, mm: 0, short: '14:00' },
  { label: '16:00 (เย็น)', hh: 16, mm: 0, short: '16:00' },
  { label: '18:00 (ค่ำ)', hh: 18, mm: 0, short: '18:00' },
  { label: '20:00 (ดึก)', hh: 20, mm: 0, short: '20:00' },
  { label: '22:00 (ก่อนเที่ยงคืน)', hh: 22, mm: 0, short: '22:00' },
  { label: '23:59 (สิ้นวัน)', hh: 23, mm: 59, short: '23:59' },
];

export function createDatePickerField({
  placeholder = 'เลือกวันที่...',
  includeTime = false,
  allowEmpty = true,
  defaultEndOfDay = false,
  width = 240,
  onChange = null,
} = {}) {
  const wrap = document.createElement('div');
  wrap.style.display = 'inline-flex';
  wrap.style.flexDirection = 'column';
  wrap.style.width = typeof width === 'number' ? `${width}px` : width;

  wrap.innerHTML = `
    <div style="display:flex;gap:6px;align-items:center">
      <input type="text" class="input" data-role="entry" placeholder="${esc(placeholder)}" style="flex:1;min-width:110px" />
      <button type="button" class="btn btn-primary btn-sm" data-role="pick-btn" style="height:38px;padding:0 10px;white-space:nowrap">
        ${iconSvg('calendar', 15, '#111318')} <span>${includeTime ? 'ปฏิทิน / ตารางเวลา' : 'ปฏิทิน'}</span>
      </button>
    </div>
    <div class="text-tiny text-info" data-role="hint" style="min-height:15px;margin-top:2px"></div>
  `;

  const entry = wrap.querySelector('[data-role="entry"]');
  const pickBtn = wrap.querySelector('[data-role="pick-btn"]');
  const hint = wrap.querySelector('[data-role="hint"]');

  function refreshHint() {
    const raw = entry.value.trim();
    if (!raw) {
      hint.textContent = '';
      return;
    }
    const dt = parseDateTime(raw);
    if (!dt) {
      hint.textContent = "⛔ รูปแบบวันเวลาไม่ถูกต้อง (กดปุ่ม 'ปฏิทิน' เพื่อเลือกจากตาราง)";
      hint.className = 'text-tiny text-danger';
      return;
    }
    let txt = formatDateThai(dt);
    if (includeTime && raw.length > 10) {
      const hh = String(dt.getHours()).padStart(2, '0');
      const mm = String(dt.getMinutes()).padStart(2, '0');
      txt += ` เวลา ${hh}:${mm} น.`;
    }
    hint.textContent = `ตรงกับ: ${txt}`;
    hint.className = 'text-tiny text-info';
  }

  entry.addEventListener('input', refreshHint);
  entry.addEventListener('blur', refreshHint);

  pickBtn.addEventListener('click', () => {
    if (entry.disabled) return;
    openCalendarPopup({
      initialDt: parseDateTime(entry.value.trim()),
      includeTime,
      allowEmpty,
      defaultEndOfDay,
      onSelect(iso) {
        entry.value = iso;
        refreshHint();
        if (onChange) onChange(iso);
      },
    });
  });

  return {
    el: wrap,
    entry,
    get: () => entry.value.trim(),
    set(val) {
      entry.value = val ? String(val).trim() : '';
      refreshHint();
    },
    setDisabled(disabled) {
      entry.disabled = Boolean(disabled);
      pickBtn.disabled = Boolean(disabled);
    },
  };
}

export function createDateTimePickerField(opts = {}) {
  return createDatePickerField({
    placeholder: 'เลือกวัน-เวลาจากตาราง...',
    ...opts,
    includeTime: true,
  });
}

export function openTimeTablePopup({
  initialTime = '12:00',
  title = 'ตารางเลือกเวลา (คลิกเลือกได้ทันที)',
  allowEmpty = false,
  onSelect = null,
} = {}) {
  const m = /^(\d{1,2}):(\d{2})/.exec(String(initialTime || '').trim());
  let selHour = m ? Math.min(23, Math.max(0, Number(m[1]))) : 12;
  let selMin = m ? Math.min(59, Math.max(0, Number(m[2]))) : 0;

  openModal({
    title,
    width: 440,
    render(card, close) {
      const hours = Array.from({ length: 24 }, (_, h) => String(h).padStart(2, '0'));
      const minsSet = new Set(['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55', '59']);
      minsSet.add(String(selMin).padStart(2, '0'));
      const mins = Array.from(minsSet).sort();

      card.innerHTML = `
        <div class="text-small text-muted" style="margin-bottom:8px">คลิกเลือกเวลาจากตารางด้านล่าง หรือปรับชั่วโมง/นาทีได้ตามต้องการ</div>
        <div class="text-small-bold" style="margin-bottom:6px">⚡ ตารางเวลาด่วน (คลิกเดียวเลือกทันที):</div>
        <div class="time-slot-grid" data-role="quick-grid" style="grid-template-columns:repeat(4,1fr);margin-bottom:12px">
          ${QUICK_TIME_SLOTS.map((slot) => `
            <button type="button" class="time-slot-btn" data-hh="${slot.hh}" data-mm="${slot.mm}">
              <div style="font-weight:700">${esc(slot.short)} น.</div>
            </button>
          `).join('')}
        </div>

        <div class="text-small-bold" style="margin-bottom:6px">🕒 ตารางชั่วโมง (00 - 23 น.):</div>
        <div class="time-slot-grid" data-role="hour-grid" style="grid-template-columns:repeat(6,1fr);margin-bottom:10px">
          ${hours.map((h) => `
            <button type="button" class="time-slot-btn" data-hour-pick="${Number(h)}">${h}:00</button>
          `).join('')}
        </div>

        <div class="card-alt" style="padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:8px">
          <span class="text-small-bold">เวลาที่เลือก:</span>
          <div style="display:flex;align-items:center;gap:6px">
            <select class="select" data-role="hh" style="width:72px;height:32px;padding:0 6px">
              ${hours.map((h) => `<option value="${h}" ${Number(h) === selHour ? 'selected' : ''}>${h}</option>`).join('')}
            </select>
            <strong>:</strong>
            <select class="select" data-role="mm" style="width:72px;height:32px;padding:0 6px">
              ${mins.map((mn) => `<option value="${mn}" ${Number(mn) === selMin ? 'selected' : ''}>${mn}</option>`).join('')}
            </select>
            <span class="text-small-bold">น.</span>
          </div>
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px">
          <div>
            ${allowEmpty ? `<button type="button" class="btn btn-outline btn-sm" data-role="clear">ล้างเวลา</button>` : ''}
          </div>
          <div style="display:flex;gap:8px">
            <button type="button" class="btn btn-outline btn-sm" data-role="cancel">ยกเลิก</button>
            <button type="button" class="btn btn-primary btn-sm" data-role="ok">ยืนยันเวลา</button>
          </div>
        </div>
      `;

      const hhSel = card.querySelector('[data-role="hh"]');
      const mmSel = card.querySelector('[data-role="mm"]');

      function syncHighlight() {
        const curH = Number(hhSel.value);
        const curM = Number(mmSel.value);
        card.querySelectorAll('[data-hh]').forEach((btn) => {
          const active = Number(btn.dataset.hh) === curH && Number(btn.dataset.mm) === curM;
          btn.classList.toggle('active', active);
        });
        card.querySelectorAll('[data-hour-pick]').forEach((btn) => {
          const active = Number(btn.dataset.hourPick) === curH && curM === 0;
          btn.classList.toggle('active', active);
        });
      }

      function commitTime() {
        const hh = String(Number(hhSel.value)).padStart(2, '0');
        const mm = String(Number(mmSel.value)).padStart(2, '0');
        if (onSelect) onSelect(`${hh}:${mm}`);
        close(true);
      }

      card.querySelectorAll('[data-hh]').forEach((btn) => {
        btn.addEventListener('click', () => {
          hhSel.value = String(Number(btn.dataset.hh)).padStart(2, '0');
          mmSel.value = String(Number(btn.dataset.mm)).padStart(2, '0');
          syncHighlight();
          commitTime();
        });
      });

      card.querySelectorAll('[data-hour-pick]').forEach((btn) => {
        btn.addEventListener('click', () => {
          hhSel.value = String(Number(btn.dataset.hourPick)).padStart(2, '0');
          mmSel.value = '00';
          syncHighlight();
          commitTime();
        });
      });

      hhSel.addEventListener('change', syncHighlight);
      mmSel.addEventListener('change', syncHighlight);
      syncHighlight();

      const clrBtn = card.querySelector('[data-role="clear"]');
      if (clrBtn) {
        clrBtn.addEventListener('click', () => {
          if (onSelect) onSelect('');
          close(true);
        });
      }
      card.querySelector('[data-role="cancel"]').addEventListener('click', () => close(false));
      card.querySelector('[data-role="ok"]').addEventListener('click', commitTime);
    },
  });
}

export function openCalendarPopup({ initialDt, includeTime, allowEmpty, defaultEndOfDay, onSelect }) {
  const now = new Date();
  const base = initialDt || now;
  let year = base.getFullYear();
  let month = base.getMonth() + 1;
  let selectedDay = base.getDate();
  let hour = initialDt ? base.getHours() : (defaultEndOfDay ? 23 : now.getHours());
  let minute = initialDt ? base.getMinutes() : (defaultEndOfDay ? 59 : 0);

  openModal({
    title: includeTime ? 'ปฏิทินและตารางเลือกเวลา' : 'เลือกวันที่จากปฏิทิน',
    width: includeTime ? 430 : 360,
    render(card, close) {
      card.style.padding = '0';
      card.style.overflow = 'hidden';

      const hours = Array.from({ length: 24 }, (_, h) => String(h).padStart(2, '0'));
      const minsSet = new Set(Array.from({ length: 12 }, (_, i) => String(i * 5).padStart(2, '0')));
      minsSet.add('59');
      minsSet.add(String(minute).padStart(2, '0'));
      const mins = Array.from(minsSet).sort();

      card.innerHTML = `
        <div style="background:var(--color-secondary);padding:10px;display:flex;align-items:center;gap:4px">
          <button type="button" class="btn btn-outline btn-sm" data-role="prev-yr" style="color:#FFFFFF;border-color:#475569;padding:0 8px">« ปี</button>
          <button type="button" class="btn btn-primary btn-sm" data-role="prev-mo" style="padding:0 10px">‹</button>
          <div class="text-body-bold text-primary" data-role="mo-yr" style="flex:1;text-align:center"></div>
          <button type="button" class="btn btn-primary btn-sm" data-role="next-mo" style="padding:0 10px">›</button>
          <button type="button" class="btn btn-outline btn-sm" data-role="next-yr" style="color:#FFFFFF;border-color:#475569;padding:0 8px">ปี »</button>
        </div>
        <div style="padding:10px 12px">
          <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px">
            <button type="button" class="btn btn-outline btn-sm" data-day-offset="0" style="height:26px;padding:0 8px;font-size:12px">วันนี้</button>
            <button type="button" class="btn btn-outline btn-sm" data-day-offset="1" style="height:26px;padding:0 8px;font-size:12px">พรุ่งนี้</button>
            <button type="button" class="btn btn-outline btn-sm" data-day-offset="3" style="height:26px;padding:0 8px;font-size:12px">+3 วัน</button>
            <button type="button" class="btn btn-outline btn-sm" data-day-offset="7" style="height:26px;padding:0 8px;font-size:12px">+7 วัน</button>
            <button type="button" class="btn btn-outline btn-sm" data-day-offset="30" style="height:26px;padding:0 8px;font-size:12px">+30 วัน</button>
          </div>
          <div style="display:grid;grid-template-columns:repeat(7,1fr);background:var(--color-surface-alt);padding:4px 0;text-align:center;margin-bottom:4px;border-radius:6px">
            ${WEEKDAYS_TH.map((w, idx) => `<span class="text-small-bold ${idx >= 5 ? 'text-danger' : 'text-main'}">${w}</span>`).join('')}
          </div>
          <div data-role="days-grid" style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;min-height:184px"></div>
          ${includeTime ? `
            <div class="card-alt" style="padding:8px 10px;margin-top:8px">
              <div class="text-tiny text-muted" style="margin-bottom:4px;font-weight:600">🕒 ตารางเวลาด่วน (คลิกเลือกเวลาได้ทันที):</div>
              <div class="time-slot-grid" data-role="slot-grid">
                ${QUICK_TIME_SLOTS.map((slot) => `
                  <button type="button" class="time-slot-btn" data-slot-hh="${slot.hh}" data-slot-mm="${slot.mm}">
                    ${esc(slot.short)} น.
                  </button>
                `).join('')}
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;padding-top:6px;border-top:1px solid var(--color-border)">
                <span class="text-small-bold">ปรับเวลาละเอียด (ชม. : นาที):</span>
                <div style="display:flex;align-items:center;gap:4px">
                  <select class="select" data-role="hh" style="width:68px;height:30px;padding:0 6px">
                    ${hours.map((h) => `<option value="${h}" ${Number(h) === hour ? 'selected' : ''}>${h}</option>`).join('')}
                  </select>
                  <strong>:</strong>
                  <select class="select" data-role="mm" style="width:68px;height:30px;padding:0 6px">
                    ${mins.map((m) => `<option value="${m}" ${Number(m) === minute ? 'selected' : ''}>${m}</option>`).join('')}
                  </select>
                </div>
              </div>
            </div>
          ` : ''}
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px">
            <div style="display:flex;gap:6px">
              <button type="button" class="btn btn-info btn-sm" data-role="today">เลือกตอนนี้</button>
              ${allowEmpty ? `<button type="button" class="btn btn-outline btn-sm" data-role="clear">ล้างค่า</button>` : ''}
            </div>
            <button type="button" class="btn btn-primary btn-sm" data-role="confirm">${includeTime ? 'ยืนยันวันและเวลา' : 'ยืนยันวันที่'}</button>
          </div>
        </div>
      `;

      const moYrEl = card.querySelector('[data-role="mo-yr"]');
      const daysGrid = card.querySelector('[data-role="days-grid"]');
      const hhSel = card.querySelector('[data-role="hh"]');
      const mmSel = card.querySelector('[data-role="mm"]');

      function daysInMonth(y, m) {
        return new Date(y, m, 0).getDate();
      }

      function syncSlotButtons() {
        if (!includeTime || !hhSel || !mmSel) return;
        const curH = Number(hhSel.value);
        const curM = Number(mmSel.value);
        card.querySelectorAll('[data-slot-hh]').forEach((btn) => {
          const isMatch = Number(btn.dataset.slotHh) === curH && Number(btn.dataset.slotMm) === curM;
          btn.classList.toggle('active', isMatch);
        });
      }

      if (includeTime && hhSel && mmSel) {
        card.querySelectorAll('[data-slot-hh]').forEach((btn) => {
          btn.addEventListener('click', () => {
            hhSel.value = String(Number(btn.dataset.slotHh)).padStart(2, '0');
            mmSel.value = String(Number(btn.dataset.slotMm)).padStart(2, '0');
            syncSlotButtons();
          });
        });
        hhSel.addEventListener('change', syncSlotButtons);
        mmSel.addEventListener('change', syncSlotButtons);
        syncSlotButtons();
      }

      card.querySelectorAll('[data-day-offset]').forEach((btn) => {
        btn.addEventListener('click', () => {
          const offset = Number(btn.getAttribute('data-day-offset') || 0);
          const target = new Date(Date.now() + offset * 86400000);
          year = target.getFullYear();
          month = target.getMonth() + 1;
          selectedDay = target.getDate();
          renderMonth();
          if (!includeTime) {
            confirmCurrent();
          }
        });
      });

      function shiftMonth(delta) {
        const total = year * 12 + (month - 1) + delta;
        year = Math.max(1970, Math.min(2100, Math.floor(total / 12)));
        month = ((total % 12) + 12) % 12 + 1;
        const maxD = daysInMonth(year, month);
        if (selectedDay > maxD) selectedDay = maxD;
        renderMonth();
      }

      function confirmCurrent() {
        const maxD = daysInMonth(year, month);
        const d = Math.min(Math.max(1, selectedDay), maxD);
        const yStr = String(year).padStart(4, '0');
        const mStr = String(month).padStart(2, '0');
        const dStr = String(d).padStart(2, '0');
        let iso = `${yStr}-${mStr}-${dStr}`;
        if (includeTime) {
          const hh = hhSel ? Number(hhSel.value) : 23;
          const mm = mmSel ? Number(mmSel.value) : 59;
          const sec = (hh === 23 && mm === 59) ? '59' : '00';
          iso += ` ${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${sec}`;
        }
        onSelect(iso);
        close();
      }

      function renderMonth() {
        const be = year + 543;
        moYrEl.textContent = `${THAI_MONTHS_SHORT[month - 1]} ${be} (${year})`;
        daysGrid.innerHTML = '';

        // First weekday Monday=0 .. Sunday=6
        const firstJsDay = new Date(year, month - 1, 1).getDay();
        const leadEmpty = (firstJsDay + 6) % 7;
        const maxD = daysInMonth(year, month);
        const today = new Date();

        for (let i = 0; i < leadEmpty; i++) {
          const sp = document.createElement('div');
          daysGrid.appendChild(sp);
        }
        for (let dayNum = 1; dayNum <= maxD; dayNum++) {
          const isSel = dayNum === selectedDay;
          const isToday = today.getFullYear() === year && (today.getMonth() + 1) === month && today.getDate() === dayNum;
          const b = document.createElement('button');
          b.type = 'button';
          b.className = 'btn btn-sm';
          b.style.height = '30px';
          b.style.padding = '0';
          if (isSel) {
            b.style.background = 'var(--color-primary)';
            b.style.color = '#111318';
            b.style.border = '2px solid var(--color-text-main)';
          } else if (isToday) {
            b.style.background = 'var(--color-blue-soft)';
            b.style.color = 'var(--color-info)';
            b.style.border = '1px solid var(--color-info)';
          } else {
            b.style.background = 'var(--color-surface-alt)';
            b.style.color = 'var(--color-text-main)';
          }
          b.textContent = String(dayNum);
          b.addEventListener('click', () => {
            selectedDay = dayNum;
            if (!includeTime) {
              confirmCurrent();
            } else {
              renderMonth();
            }
          });
          daysGrid.appendChild(b);
        }
      }

      card.querySelector('[data-role="prev-yr"]').addEventListener('click', () => shiftMonth(-12));
      card.querySelector('[data-role="prev-mo"]').addEventListener('click', () => shiftMonth(-1));
      card.querySelector('[data-role="next-mo"]').addEventListener('click', () => shiftMonth(1));
      card.querySelector('[data-role="next-yr"]').addEventListener('click', () => shiftMonth(12));

      card.querySelector('[data-role="today"]').addEventListener('click', () => {
        const t = new Date();
        year = t.getFullYear();
        month = t.getMonth() + 1;
        selectedDay = t.getDate();
        if (includeTime && hhSel && mmSel) {
          hhSel.value = String(t.getHours()).padStart(2, '0');
          const m5 = Math.floor(t.getMinutes() / 5) * 5;
          mmSel.value = String(m5).padStart(2, '0');
          syncSlotButtons();
        }
        confirmCurrent();
      });

      const clrBtn = card.querySelector('[data-role="clear"]');
      if (clrBtn) {
        clrBtn.addEventListener('click', () => {
          onSelect('');
          close();
        });
      }

      card.querySelector('[data-role="confirm"]').addEventListener('click', confirmCurrent);
      renderMonth();
    },
  });
}
