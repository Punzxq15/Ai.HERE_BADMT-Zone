// web/js/pages/admin/coupon_form.js — ฟอร์มเพิ่ม/แก้ไขคูปอง (T06 หมวดหมู่คูปอง, T08 ปฏิทินวันเริ่ม/หมดอายุ, ตารางเลือกเวลารับโค้ด, รีโค้ด 12:00 น.)
import { api, esc, formatDateThai } from '../../api.js';
import { parseIntField, parseMoney } from '../../components/admin_common.js';
import { createDatePickerField, openTimeTablePopup } from '../../components/date_picker.js';
import { confirm, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';

export async function render(container, router, params = {}) {
  const couponId = params.coupon_id || params.id || null;
  const editing = couponId !== null;
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let c = {};
  let categories = [];
  try {
    categories = await api.get('/api/coupons/categories');
    if (editing) {
      c = await api.get(`/api/admin/coupons/${couponId}`);
    }
  } catch (err) {
    wrap.innerHTML = `<div class="text-danger">${esc(err.message)}</div>`;
    return;
  }

  const initType = editing && c.is_free_shipping ? 'free_shipping' : (c.discount_type || 'percent');
  const initCat = editing ? (c.coupon_category || 'percent') : 'percent';

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">${editing ? `แก้ไขคูปอง ${esc(c.code || '')}` : 'เพิ่มคูปองใหม่'}</div>
        <div class="text-small text-muted">ตั้งค่าเงื่อนไขส่วนลด หมวดหมู่คูปอง ปฏิทินวันเริ่ม/หมดอายุ ตารางเลือกเวลารับโค้ด และรีโค้ดอัตโนมัติเวลา 12:00 น.</div>
      </div>
      <div style="display:flex;gap:8px">
        ${editing ? `<button type="button" class="btn btn-danger btn-sm" data-role="del">ลบคูปองนี้</button>` : ''}
        <button type="button" class="btn btn-outline btn-sm" data-role="back">← กลับ</button>
      </div>
    </div>

    <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:6px"></div>

    <div class="card" style="padding:16px 20px">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px">
        <div class="field-group">
          <div class="text-small text-muted">โค้ดคูปอง *</div>
          <input type="text" class="input" data-field="code" value="${esc(c.code || '')}" placeholder="เช่น NEWYEAR50 หรือ FREESHIP (ภาษาอังกฤษ/ตัวเลข 3-20 ตัว)" />
        </div>
        <div class="field-group">
          <div class="text-small text-muted">หมวดหมู่คูปอง (T06) *</div>
          <select class="select" data-field="coupon_category">
            ${categories.map((cat) => `<option value="${esc(cat.key)}" ${cat.key === initCat ? 'selected' : ''}>${esc(cat.label)}</option>`).join('')}
          </select>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:12px;margin-bottom:10px">
        <div class="field-group">
          <div class="text-small text-muted">ประเภทส่วนลด *</div>
          <select class="select" data-field="type">
            <option value="percent" ${initType === 'percent' ? 'selected' : ''}>เปอร์เซ็นต์ (%)</option>
            <option value="fixed" ${initType === 'fixed' ? 'selected' : ''}>จำนวนเงินคงที่ (บาท)</option>
            <option value="free_shipping" ${initType === 'free_shipping' ? 'selected' : ''}>ส่งฟรี (ส่วนลดค่าจัดส่ง)</option>
          </select>
        </div>
        <div class="field-group">
          <div class="text-small text-muted" data-role="val-lbl">ส่วนลด *</div>
          <input type="text" class="input" data-field="value" value="${c.value != null ? c.value : ''}" />
        </div>
        <div class="field-group">
          <div class="text-small text-muted">เพดานส่วนลดสูงสุด (บาท)</div>
          <input type="text" class="input" data-field="max_discount" value="${c.max_discount != null ? c.max_discount : ''}" placeholder="ว่าง = ไม่จำกัดเพดาน" />
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px">
        <div class="field-group">
          <div class="text-small text-muted">ยอดสั่งซื้อขั้นต่ำเพื่อใช้คูปอง (บาท)</div>
          <input type="text" class="input" data-field="min_order" value="${c.min_order != null ? c.min_order : ''}" placeholder="ว่าง = ไม่มีขั้นต่ำ" />
        </div>
        <div class="field-group">
          <div class="text-small text-muted">จำนวนสิทธิ์ทั้งหมด (ครั้ง)</div>
          <input type="text" class="input" data-field="max_uses" value="${c.max_uses != null ? c.max_uses : ''}" placeholder="ว่าง = ไม่จำกัด" />
          ${editing ? `<div class="text-tiny text-muted">ใช้ไปแล้ว ${Number(c.used_count || 0)} ครั้ง</div>` : ''}
        </div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div>
          <div class="text-small text-muted">วันเริ่มต้นรับ/ใช้งาน (เลือกจากปฏิทิน)</div>
          <div data-role="starts-slot"></div>
        </div>
        <div>
          <div class="text-small text-muted">วันหมดอายุ (เลือกจากปฏิทิน)</div>
          <div data-role="expiry-slot"></div>
          ${(editing && c.expires_at) ? `<div class="text-tiny text-muted">ปัจจุบัน: หมดอายุ ${esc(formatDateThai(c.expires_at))}</div>` : ''}
        </div>
      </div>

      <div class="card-alt" style="padding:12px 14px;margin-bottom:12px">
        <div class="text-body-bold" style="margin-bottom:8px">ตั้งช่วงเวลารับโค้ด (คลิกเลือกจากตารางเวลา) & รีเซ็ตโค้ดอัตโนมัติเวลา 12:00 น.</div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px">
          <span class="text-small">เวลารับได้ตั้งแต่ (HH:MM):</span>
          <div style="display:inline-flex;gap:4px;align-items:center">
            <input type="text" class="input" data-field="claim_start" value="${esc(c.claim_start_time || '')}" placeholder="เช่น 10:00" style="width:92px;height:34px" />
            <button type="button" class="btn btn-primary btn-sm" data-role="pick-start-time" style="height:34px;padding:0 8px">🕒 ตารางเวลา</button>
          </div>
          <span class="text-small">ถึงเวลา (HH:MM):</span>
          <div style="display:inline-flex;gap:4px;align-items:center">
            <input type="text" class="input" data-field="claim_end" value="${esc(c.claim_end_time || '')}" placeholder="เช่น 12:00" style="width:92px;height:34px" />
            <button type="button" class="btn btn-primary btn-sm" data-role="pick-end-time" style="height:34px;padding:0 8px">🕒 ตารางเวลา</button>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:8px">
          <span class="text-tiny text-muted">ช่วงเวลาด่วน:</span>
          <button type="button" class="btn btn-outline btn-sm" data-preset="09:00,12:00">09:00 - 12:00</button>
          <button type="button" class="btn btn-outline btn-sm" data-preset="10:00,12:00">10:00 - 12:00</button>
          <button type="button" class="btn btn-outline btn-sm" data-preset="12:00,14:00">12:00 - 14:00</button>
          <button type="button" class="btn btn-outline btn-sm" data-preset="18:00,22:00">18:00 - 22:00</button>
          <button type="button" class="btn btn-ghost btn-sm" data-preset=",">รับได้ทั้งวัน (ไม่จำกัดเวลา)</button>
        </div>

        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:8px" class="text-small-bold">
          <input type="checkbox" data-field="repeat_daily" ${(editing ? c.repeat_daily : true) ? 'checked' : ''} />
          <span>เปิดให้รับได้ทุกวันในช่วงเวลานั้น (ถ้าปิด จะอ้างอิงตามช่วงวันเริ่มต้น - วันหมดอายุ)</span>
        </label>

        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer" class="text-small-bold">
            <input type="checkbox" data-field="daily_reset_12" ${c.daily_reset_12 ? 'checked' : ''} />
            <span>รีโค้ดให้กดรับได้ใหม่ทุกๆ เวลา 12:00 น. ของทุกวัน (ลบโค้ดเก่าที่ไม่ได้รับและแทนด้วยโค้ดใหม่)</span>
          </label>
          <span class="text-small text-muted">คำนำหน้าโค้ดใหม่:</span>
          <input type="text" class="input" data-field="code_prefix" value="${esc(c.code_prefix || '')}" placeholder="เช่น NOON50" style="width:130px;height:34px" />
        </div>
      </div>

      <div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:14px">
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer" class="text-body">
          <input type="checkbox" data-field="is_active" ${(editing ? c.is_active : true) ? 'checked' : ''} />
          <span>เปิดใช้งานคูปองนี้</span>
        </label>
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer" class="text-body">
          <input type="checkbox" data-field="claimable" ${(editing ? c.claimable : true) ? 'checked' : ''} />
          <span>แสดงให้ลูกค้ากดเก็บที่หน้าแรกและหน้าชำระเงิน</span>
        </label>
      </div>

      <div style="display:flex;gap:8px">
        <button type="button" class="btn btn-primary btn-md" data-role="save">บันทึกคูปอง</button>
        <button type="button" class="btn btn-outline btn-md" data-role="cancel">ยกเลิก</button>
      </div>
    </div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const codeIn = wrap.querySelector('[data-field="code"]');
  const typeSel = wrap.querySelector('[data-field="type"]');
  const catSel = wrap.querySelector('[data-field="coupon_category"]');
  const valLbl = wrap.querySelector('[data-role="val-lbl"]');
  const valIn = wrap.querySelector('[data-field="value"]');
  const claimStartIn = wrap.querySelector('[data-field="claim_start"]');
  const claimEndIn = wrap.querySelector('[data-field="claim_end"]');

  [codeIn, valIn, claimStartIn, claimEndIn].forEach((el) => {
    if (el) el.addEventListener('input', () => clearFieldError(el));
  });

  const startsPicker = createDatePickerField({ placeholder: 'ว่าง = เริ่มได้ทันที', allowEmpty: true, width: '100%' });
  if (editing && c.starts_at) startsPicker.set(String(c.starts_at).slice(0, 10));
  wrap.querySelector('[data-role="starts-slot"]').appendChild(startsPicker.el);

  const expiryPicker = createDatePickerField({ placeholder: 'ว่าง = ไม่หมดอายุ', allowEmpty: true, width: '100%' });
  if (editing && c.expires_at) expiryPicker.set(String(c.expires_at).slice(0, 10));
  wrap.querySelector('[data-role="expiry-slot"]').appendChild(expiryPicker.el);

  wrap.querySelector('[data-role="pick-start-time"]').addEventListener('click', () => {
    openTimeTablePopup({
      initialTime: claimStartIn.value.trim() || '10:00',
      title: 'เลือกเวลาเริ่มต้นรับโค้ด (HH:MM)',
      allowEmpty: true,
      onSelect(val) {
        claimStartIn.value = val;
        clearFieldError(claimStartIn);
      },
    });
  });

  wrap.querySelector('[data-role="pick-end-time"]').addEventListener('click', () => {
    openTimeTablePopup({
      initialTime: claimEndIn.value.trim() || '12:00',
      title: 'เลือกเวลาสิ้นสุดรับโค้ด (HH:MM)',
      allowEmpty: true,
      onSelect(val) {
        claimEndIn.value = val;
        clearFieldError(claimEndIn);
      },
    });
  });

  function syncType() {
    const t = typeSel.value;
    if (t === 'free_shipping') {
      valLbl.textContent = 'วงเงินลดค่าจัดส่งสูงสุด (บาท) *';
      valIn.placeholder = 'เช่น 50';
      if (!valIn.value.trim()) valIn.value = '50';
      catSel.value = 'free_shipping';
    } else if (t === 'percent') {
      valLbl.textContent = 'ส่วนลด (1–100 %) *';
      valIn.placeholder = 'เช่น 10 หรือ 50';
      catSel.value = 'percent';
    } else {
      valLbl.textContent = 'ส่วนลด (บาท) *';
      valIn.placeholder = 'เช่น 200';
      catSel.value = 'fixed';
    }
  }
  typeSel.addEventListener('change', syncType);
  syncType();

  wrap.querySelectorAll('[data-preset]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const [st, et] = btn.dataset.preset.split(',');
      claimStartIn.value = st || '';
      claimEndIn.value = et || '';
      clearFieldError(claimStartIn);
      clearFieldError(claimEndIn);
    });
  });

  const goBack = () => router.go_back('admin_coupons');
  wrap.querySelector('[data-role="back"]').addEventListener('click', goBack);
  wrap.querySelector('[data-role="cancel"]').addEventListener('click', goBack);

  const delBtn = wrap.querySelector('[data-role="del"]');
  if (delBtn) {
    delBtn.addEventListener('click', async () => {
      const ok = await confirm('ยืนยันการลบคูปอง', `ต้องการลบคูปอง “${c.code}” ใช่หรือไม่?`, { confirmText: 'ลบคูปอง', danger: true });
      if (!ok) return;
      try {
        await api.del(`/api/admin/coupons/${couponId}`);
        showToast(`ลบคูปอง “${c.code}” เรียบร้อยแล้ว`, 'success');
        goBack();
      } catch (err) {
        showToast(err.message || 'ลบคูปองไม่สำเร็จ', 'error');
      }
    });
  }

  wrap.querySelector('[data-role="save"]').addEventListener('click', async () => {
    errEl.textContent = '';
    clearFieldError(codeIn);
    clearFieldError(valIn);
    clearFieldError(claimStartIn);
    clearFieldError(claimEndIn);
    try {
      const code = codeIn.value.trim().toUpperCase();
      if (!code) {
        setFieldError(codeIn, 'กรุณากรอกโค้ดคูปอง');
        throw new Error('กรุณากรอกโค้ดคูปอง');
      }
      if (/\s/.test(code)) {
        setFieldError(codeIn, 'โค้ดคูปองต้องไม่มีช่องว่าง');
        throw new Error('โค้ดคูปองต้องไม่มีช่องว่าง');
      }

      const t = typeSel.value;
      const isFreeShip = t === 'free_shipping';
      const discountType = isFreeShip ? 'fixed' : t;
      const rawVal = valIn.value.trim();
      const val = isFreeShip && !rawVal ? 50 : parseMoney(rawVal, 'ส่วนลด', { required: true, minimum: 0 });
      if (val <= 0) {
        setFieldError(valIn, 'ส่วนลดต้องมากกว่า 0');
        throw new Error('ส่วนลดต้องมากกว่า 0');
      }
      if (discountType === 'percent' && val > 100) {
        setFieldError(valIn, 'ส่วนลดแบบเปอร์เซ็นต์ต้องไม่เกิน 100');
        throw new Error('ส่วนลดแบบเปอร์เซ็นต์ต้องไม่เกิน 100');
      }

      const minOrder = parseMoney(wrap.querySelector('[data-field="min_order"]').value, 'ยอดสั่งซื้อขั้นต่ำ') || 0;
      const maxDisc = parseMoney(wrap.querySelector('[data-field="max_discount"]').value, 'เพดานส่วนลดสูงสุด');
      const maxUses = parseIntField(wrap.querySelector('[data-field="max_uses"]').value, 'จำนวนสิทธิ์', { required: false, minimum: 1 });
      const claimSt = claimStartIn.value.trim() || null;
      const claimEt = claimEndIn.value.trim() || null;
      if (Boolean(claimSt) !== Boolean(claimEt)) {
        const msg = 'กรุณาระบุทั้งเวลาเริ่มและเวลาสิ้นสุดการรับโค้ด (เช่น 10:00 ถึง 12:00)';
        setFieldError(claimSt ? claimEndIn : claimStartIn, msg);
        throw new Error(msg);
      }

      const payload = {
        code,
        discount_type: discountType,
        is_free_shipping: isFreeShip,
        coupon_category: catSel.value || 'other',
        value: val,
        min_order: minOrder,
        max_discount: maxDisc,
        max_uses: maxUses,
        starts_at: startsPicker.get() || null,
        expires_at: expiryPicker.get() || null,
        claim_start_time: claimSt,
        claim_end_time: claimEt,
        repeat_daily: wrap.querySelector('[data-field="repeat_daily"]').checked,
        daily_reset_12: wrap.querySelector('[data-field="daily_reset_12"]').checked,
        code_prefix: wrap.querySelector('[data-field="code_prefix"]').value.trim().toUpperCase() || null,
        claimable: wrap.querySelector('[data-field="claimable"]').checked,
        is_active: wrap.querySelector('[data-field="is_active"]').checked ? 1 : 0,
      };

      if (editing) await api.put(`/api/admin/coupons/${couponId}`, payload);
      else await api.post('/api/admin/coupons', payload);

      showToast('บันทึกคูปองเรียบร้อยแล้ว', 'success');
      goBack();
    } catch (err) {
      const em = err.message || 'บันทึกคูปองไม่สำเร็จ';
      errEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
    }
  });
}
