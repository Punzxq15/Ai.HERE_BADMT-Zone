// web/js/pages/buyer/addresses.js — หน้าที่อยู่จัดส่ง (รายการ + เพิ่ม/แก้ไขพร้อมตรวจจับข้อผิดพลาดรายช่องแบบเรียลไทม์บอกสาเหตุทันที + ลบ + ตั้งเป็นค่าเริ่มต้น)
import { api, esc, formatPhone } from '../../api.js';
import {
  confirm,
  setFieldError,
  clearFieldError,
  clearAllFieldErrors,
  notifyError,
  notifySuccess,
} from '../../components/dialogs.js';
import { pageTitleHtml } from '../../components/buyer_common.js';

/**
 * ตรวจสอบความถูกต้องของแต่ละช่องในฟอร์มที่อยู่จัดส่ง พร้อมบอกสาเหตุที่ผิดอย่างชัดเจนเพื่อให้ผู้ใช้แก้ได้ทันที
 * @param {string} fieldName ชื่อฟิลด์
 * @param {string} rawValue ค่าที่ผู้ใช้พิมพ์
 * @param {boolean} requireNonEmpty บังคับไม่ให้ว่างหรือไม่ (true ตอน blur/กดบันทึก, false ตอนกำลังพิมพ์แล้วลบจนว่าง)
 * @returns {string} ข้อความผิดพลาด (ว่าง '' = ถูกต้อง)
 */
export function validateShippingAddressField(fieldName, rawValue, requireNonEmpty = true) {
  const val = String(rawValue ?? '');
  const trimmed = val.trim();

  if (fieldName === 'recipient') {
    if (!trimmed) return requireNonEmpty ? 'กรุณากรอกชื่อ-นามสกุลผู้รับสินค้า' : '';
    if (trimmed.length < 2) return 'ชื่อผู้รับสั้นเกินไป (ต้องมีอย่างน้อย 2 ตัวอักษร)';
    if (trimmed.length > 100) return `ชื่อผู้รับยาวเกินไป (${trimmed.length}/100 ตัวอักษร — ต้องไม่เกิน 100 ตัวอักษร)`;
    return '';
  }

  if (fieldName === 'phone') {
    const clean = trimmed.replace(/[-\s]/g, '');
    if (!clean) return requireNonEmpty ? 'กรุณากรอกเบอร์โทรศัพท์ผู้รับ (ตัวเลข 10 หลัก ขึ้นต้นด้วย 0)' : '';
    if (/[^0-9]/.test(clean)) return 'เบอร์โทรศัพท์ต้องเป็นตัวเลข 0-9 เท่านั้น (พบตัวอักษรหรือสัญลักษณ์ที่ไม่อนุญาต)';
    if (!clean.startsWith('0')) return 'เบอร์โทรศัพท์ต้องขึ้นต้นด้วยเลข 0 เท่านั้น (เช่น 0812345678)';
    if (clean.length < 10) return `เบอร์โทรศัพท์ยังไม่ครบ 10 หลัก (กรอกแล้ว ${clean.length}/10 หลัก)`;
    if (clean.length > 10) return `เบอร์โทรศัพท์เกิน 10 หลัก (กรอกแล้ว ${clean.length}/10 หลัก — ต้องมี 10 หลักพอดี)`;
    return '';
  }

  if (fieldName === 'address_line') {
    if (!trimmed) return requireNonEmpty ? 'กรุณากรอกที่อยู่ (บ้านเลขที่ หมู่บ้าน ซอย ถนน)' : '';
    if (trimmed.length < 4) return 'ที่อยู่สั้นเกินไป กรุณาระบุบ้านเลขที่และซอย/ถนนให้ชัดเจน';
    if (trimmed.length > 200) return `ที่อยู่ยาวเกินไป (${trimmed.length}/200 ตัวอักษร — ต้องไม่เกิน 200 ตัวอักษร)`;
    return '';
  }

  if (fieldName === 'district') {
    if (!trimmed) return requireNonEmpty ? 'กรุณากรอกแขวง/เขต หรือ ตำบล/อำเภอ' : '';
    if (trimmed.length < 2) return 'ชื่อแขวง/เขต หรือ ตำบล/อำเภอสั้นเกินไป (ต้องมีอย่างน้อย 2 ตัวอักษร)';
    if (trimmed.length > 80) return `ชื่อแขวง/เขต หรือ ตำบล/อำเภอยาวเกินไป (${trimmed.length}/80 ตัวอักษร)`;
    return '';
  }

  if (fieldName === 'province') {
    if (!trimmed) return requireNonEmpty ? 'กรุณากรอกชื่อจังหวัด (เช่น กรุงเทพมหานคร, เชียงใหม่)' : '';
    if (trimmed.length < 2) return 'ชื่อจังหวัดสั้นเกินไป (ต้องมีอย่างน้อย 2 ตัวอักษร)';
    if (trimmed.length > 80) return `ชื่อจังหวัดยาวเกินไป (${trimmed.length}/80 ตัวอักษร)`;
    return '';
  }

  if (fieldName === 'postcode') {
    if (!trimmed) return requireNonEmpty ? 'กรุณากรอกรหัสไปรษณีย์ 5 หลัก (เช่น 10110)' : '';
    if (/[^0-9]/.test(trimmed)) return 'รหัสไปรษณีย์ต้องเป็นตัวเลข 0-9 เท่านั้น (ห้ามใส่ตัวอักษรหรือขีด)';
    if (trimmed.length < 5) return `รหัสไปรษณีย์ยังไม่ครบ 5 หลัก (กรอกแล้ว ${trimmed.length}/5 หลัก)`;
    if (trimmed.length > 5) return `รหัสไปรษณีย์เกิน 5 หลัก (กรอกแล้ว ${trimmed.length}/5 หลัก — ต้องมี 5 หลักพอดี)`;
    return '';
  }

  return '';
}

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  let editingId = null;

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      ${pageTitleHtml('📍 ที่อยู่จัดส่ง', 'จัดการที่อยู่สำหรับรับสินค้า (เพิ่มได้หลายที่)')}
      <button type="button" class="btn btn-primary btn-md" data-role="add-btn">+ เพิ่มที่อยู่ใหม่</button>
    </div>

    <div class="text-small text-danger" data-role="msg" style="min-height:18px;margin-top:4px"></div>

    <div class="card hidden" data-role="form-card" style="padding:18px 20px;margin-top:8px">
      <div class="text-h3" data-role="form-title" style="margin-bottom:4px">เพิ่มที่อยู่ใหม่</div>
      <div class="text-tiny text-muted" style="margin-bottom:10px">กรอกข้อมูลให้ครบทุกช่อง ระบบจะตรวจสอบความถูกต้องและแจ้งจุดที่ต้องแก้ไขให้ทราบทันทีขณะพิมพ์</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div>
          <div class="text-small text-muted">ชื่อผู้รับ *</div>
          <input type="text" class="input" data-field="recipient" placeholder="เช่น สมชาย ใจดี" />
        </div>
        <div>
          <div class="text-small text-muted">เบอร์โทรศัพท์ (10 หลัก ขึ้นต้นด้วย 0) *</div>
          <input type="tel" class="input" data-field="phone" placeholder="เช่น 0812345678" maxlength="12" />
        </div>
        <div style="grid-column:span 2">
          <div class="text-small text-muted">ที่อยู่ (บ้านเลขที่ หมู่บ้าน ถนน ซอย) *</div>
          <input type="text" class="input" data-field="address_line" placeholder="เช่น 99/9 หมู่บ้านสุขสันต์ ซอยสุขุมวิท 21 ถนนสุขุมวิท" />
        </div>
        <div>
          <div class="text-small text-muted">แขวง/เขต หรือ ตำบล/อำเภอ *</div>
          <input type="text" class="input" data-field="district" placeholder="เช่น คลองเตยเหนือ เขตวัฒนา" />
        </div>
        <div>
          <div class="text-small text-muted">จังหวัด *</div>
          <input type="text" class="input" data-field="province" placeholder="เช่น กรุงเทพมหานคร" />
        </div>
        <div>
          <div class="text-small text-muted">รหัสไปรษณีย์ (ตัวเลข 5 หลัก) *</div>
          <input type="text" class="input" data-field="postcode" placeholder="เช่น 10110" maxlength="6" />
        </div>
        <div style="display:flex;align-items:flex-end;padding-bottom:8px">
          <label style="display:flex;align-items:center;gap:8px;cursor:pointer" class="text-small">
            <input type="checkbox" data-role="default-chk" />
            <span>ตั้งเป็นที่อยู่เริ่มต้น</span>
          </label>
        </div>
      </div>
      <div class="text-small text-danger" data-role="form-err" style="min-height:18px;margin-top:8px"></div>
      <div style="display:flex;gap:8px;margin-top:8px">
        <button type="button" class="btn btn-primary btn-md" data-role="save-btn">บันทึกที่อยู่</button>
        <button type="button" class="btn btn-outline btn-md" data-role="cancel-btn">ยกเลิก</button>
      </div>
    </div>

    <div data-role="list" style="display:flex;flex-direction:column;gap:8px;margin-top:10px"></div>
  `;

  const msgEl = wrap.querySelector('[data-role="msg"]');
  const formCard = wrap.querySelector('[data-role="form-card"]');
  const formTitle = wrap.querySelector('[data-role="form-title"]');
  const formErr = wrap.querySelector('[data-role="form-err"]');
  const defaultChk = wrap.querySelector('[data-role="default-chk"]');
  const listEl = wrap.querySelector('[data-role="list"]');

  // ติดตั้งตัวตรวจจับความผิดพลาดแบบทันที (Real-time validation) บนทุกช่องของที่อยู่จัดส่ง
  wrap.querySelectorAll('[data-field]').forEach((el) => {
    const fieldName = el.dataset.field;
    el.addEventListener('input', () => {
      formErr.textContent = '';
      const errMsg = validateShippingAddressField(fieldName, el.value, false);
      if (errMsg) {
        setFieldError(el, errMsg);
      } else {
        clearFieldError(el);
      }
    });
    el.addEventListener('blur', () => {
      const errMsg = validateShippingAddressField(fieldName, el.value, true);
      if (errMsg) {
        setFieldError(el, errMsg);
      } else {
        clearFieldError(el);
      }
    });
  });

  function showForm(addr = null) {
    msgEl.textContent = '';
    formErr.textContent = '';
    clearAllFieldErrors(formCard);
    editingId = addr ? addr.id : null;
    formTitle.textContent = addr ? 'แก้ไขที่อยู่' : 'เพิ่มที่อยู่ใหม่';
    wrap.querySelectorAll('[data-field]').forEach((el) => {
      const k = el.dataset.field;
      el.value = addr && addr[k] != null ? String(addr[k]) : '';
    });
    defaultChk.checked = Boolean(addr && addr.is_default);
    formCard.classList.remove('hidden');
    wrap.querySelector('[data-field="recipient"]').focus();
  }

  function hideForm() {
    clearAllFieldErrors(formCard);
    formErr.textContent = '';
    formCard.classList.add('hidden');
    editingId = null;
  }

  async function saveForm() {
    formErr.textContent = '';
    const payload = { is_default: defaultChk.checked };
    let firstInvalidEl = null;
    const errorMessages = [];

    wrap.querySelectorAll('[data-field]').forEach((el) => {
      const k = el.dataset.field;
      const val = el.value.trim();
      payload[k] = val;
      const errMsg = validateShippingAddressField(k, val, true);
      if (errMsg) {
        setFieldError(el, errMsg);
        errorMessages.push(errMsg);
        if (!firstInvalidEl) firstInvalidEl = el;
      } else {
        clearFieldError(el);
      }
    });

    if (errorMessages.length > 0) {
      const summary = errorMessages[0];
      notifyError(summary, { inlineEl: formErr });
      if (firstInvalidEl) firstInvalidEl.focus();
      return;
    }

    try {
      let done = '';
      if (editingId === null) {
        await api.post('/api/addresses', payload);
        done = 'เพิ่มที่อยู่จัดส่งเรียบร้อยแล้ว';
      } else {
        await api.put(`/api/addresses/${editingId}`, payload);
        done = 'บันทึกการแก้ไขที่อยู่จัดส่งเรียบร้อยแล้ว';
      }
      hideForm();
      await loadList();
      notifySuccess(done, { clearInlineEl: msgEl });
    } catch (err) {
      const msg = err.message || 'บันทึกที่อยู่ไม่สำเร็จ';
      let targetEl = null;
      if (msg.includes('ชื่อผู้รับ')) targetEl = wrap.querySelector('[data-field="recipient"]');
      else if (msg.includes('เบอร์โทร')) targetEl = wrap.querySelector('[data-field="phone"]');
      else if (msg.includes('รหัสไปรษณีย์')) targetEl = wrap.querySelector('[data-field="postcode"]');
      else if (msg.includes('แขวง') || msg.includes('อำเภอ')) targetEl = wrap.querySelector('[data-field="district"]');
      else if (msg.includes('จังหวัด')) targetEl = wrap.querySelector('[data-field="province"]');
      else if (msg.includes('ที่อยู่') && !msg.includes('สูงสุด')) targetEl = wrap.querySelector('[data-field="address_line"]');
      notifyError(msg, { field: targetEl, inlineEl: formErr });
    }
  }

  async function loadList() {
    listEl.innerHTML = '';
    try {
      const addresses = await api.get('/api/addresses');
      if (!addresses || !addresses.length) {
        listEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:50px 20px;white-space:pre-line">📍
ยังไม่มีที่อยู่จัดส่ง กดปุ่ม "เพิ่มที่อยู่ใหม่" เพื่อเริ่มต้น</div>`;
        return;
      }
      for (const addr of addresses) {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.padding = '12px 16px';
        card.style.display = 'flex';
        card.style.justifyContent = 'space-between';
        card.style.alignItems = 'center';
        card.style.gap = '12px';

        card.innerHTML = `
          <div>
            <div style="display:flex;align-items:center;gap:10px">
              <span class="text-body-bold">${esc(addr.recipient)}</span>
              <span class="text-small text-muted">${esc(formatPhone(addr.phone))}</span>
              ${addr.is_default ? `<span class="pill pill-success">ค่าเริ่มต้น</span>` : ''}
            </div>
            <div class="text-body" style="margin-top:4px">${esc(addr.full_address)}</div>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <button type="button" class="btn btn-outline btn-sm" data-role="edit">แก้ไข</button>
            ${!addr.is_default ? `<button type="button" class="btn btn-outline btn-sm" data-role="set-def">ตั้งเป็นค่าเริ่มต้น</button>` : ''}
            <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
          </div>
        `;

        card.querySelector('[data-role="edit"]').addEventListener('click', () => showForm(addr));
        const defBtn = card.querySelector('[data-role="set-def"]');
        if (defBtn) {
          defBtn.addEventListener('click', async () => {
            try {
              await api.post(`/api/addresses/${addr.id}/default`);
              notifySuccess('ตั้งเป็นที่อยู่เริ่มต้นแล้ว', { clearInlineEl: msgEl });
              await loadList();
            } catch (err) {
              notifyError(err.message || 'ตั้งที่อยู่เริ่มต้นไม่สำเร็จ', { inlineEl: msgEl });
            }
          });
        }
        card.querySelector('[data-role="del"]').addEventListener('click', async () => {
          const ok = await confirm('ลบที่อยู่', `ต้องการลบที่อยู่ของ "${addr.recipient}" ใช่ไหม?`, {
            confirmText: 'ลบ',
            danger: true,
          });
          if (!ok) return;
          try {
            await api.del(`/api/addresses/${addr.id}`);
            if (editingId === addr.id) hideForm();
            notifySuccess('ลบที่อยู่เรียบร้อยแล้ว', { clearInlineEl: msgEl });
            await loadList();
          } catch (err) {
            notifyError(err.message || 'ลบที่อยู่ไม่สำเร็จ', { inlineEl: msgEl });
          }
        });
        listEl.appendChild(card);
      }
    } catch (err) {
      notifyError(err.message || 'โหลดที่อยู่ไม่สำเร็จ', { inlineEl: msgEl });
    }
  }

  wrap.querySelector('[data-role="add-btn"]').addEventListener('click', () => showForm(null));
  wrap.querySelector('[data-role="save-btn"]').addEventListener('click', saveForm);
  wrap.querySelector('[data-role="cancel-btn"]').addEventListener('click', hideForm);

  await loadList();
}
