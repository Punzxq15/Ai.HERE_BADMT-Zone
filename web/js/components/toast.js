// web/js/components/toast.js — คอมโพเนนต์แจ้งเตือน Toast มุมขวาบน (ค้าง 5 วินาที) + ข้อความผิดพลาดสีแดงใต้ช่องกรอก (Inline Field Error)
import { esc } from '../api.js';

const TOAST_DURATION_MS = 5000;
const LEAVE_ANIM_MS = 320;

const CHECK_SVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" fill="rgba(255,255,255,0.22)"/><path d="M8 12.5L10.8 15.3L16.5 9.5" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const ERROR_SVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" fill="rgba(255,255,255,0.22)"/><path d="M12 7.5V13M12 16.5H12.01" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round"/></svg>`;

function getToastContainer() {
  let container = document.getElementById('toast-root');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-root';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

/**
 * แสดงกล่องแจ้งเตือนมุมขวาบน เลื่อนเข้าจากขวา ค้างไว้ 5 วินาที แล้วเลื่อนกลับทางเดิม
 * @param {string} message ข้อความภาษาไทยที่ต้องการแสดง
 * @param {'success'|'error'} kind ชนิดการแจ้งเตือน ('success' = สีเขียว, 'error' = สีแดง)
 */
export function showToast(message, kind = 'success') {
  const cleanMsg = String(message || '').replace(/^[⛔✓✅⚠️\s]+/u, '').trim();
  if (!cleanMsg) return null;

  const normalizedKind = kind === 'error' ? 'error' : 'success';
  const container = getToastContainer();

  const item = document.createElement('div');
  item.className = `toast-item toast-item--${normalizedKind}`;
  item.setAttribute('role', normalizedKind === 'error' ? 'alert' : 'status');
  item.setAttribute('aria-live', normalizedKind === 'error' ? 'assertive' : 'polite');

  const prefixText = normalizedKind === 'error'
    ? (cleanMsg.startsWith('ไม่สามารถ') || cleanMsg.startsWith('ผิดพลาด') || cleanMsg.startsWith('กรุณา') || cleanMsg.includes('ไม่ถูกต้อง') || cleanMsg.includes('ไม่สำเร็จ')
        ? cleanMsg
        : `ไม่สามารถดำเนินการได้: ${cleanMsg}`)
    : cleanMsg;

  item.innerHTML = `
    <span class="toast-item__icon">${normalizedKind === 'error' ? ERROR_SVG : CHECK_SVG}</span>
    <div class="toast-item__body">${esc(prefixText)}</div>
  `;

  container.appendChild(item);

  // Trigger slide-in on next animation frame
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      item.classList.add('toast-item--visible');
    });
  });

  let removed = false;
  const dismiss = () => {
    if (removed) return;
    removed = true;
    item.classList.remove('toast-item--visible');
    item.classList.add('toast-item--leaving');
    setTimeout(() => {
      item.remove();
    }, LEAVE_ANIM_MS);
  };

  const timer = setTimeout(dismiss, TOAST_DURATION_MS);
  item.addEventListener('click', () => {
    clearTimeout(timer);
    dismiss();
  });

  return { el: item, dismiss };
}

/**
 * แสดงข้อความสีแดงใต้ช่องกรอกข้อมูล พร้อมตีกรอบสีแดง และล้างออกอัตโนมัติเมื่อผู้ใช้เริ่มพิมพ์แก้ไข
 * @param {HTMLElement|null} inputEl ช่อง input/select/textarea
 * @param {string} message ข้อความแจ้งสาเหตุที่ผิดพลาด
 */
export function setFieldError(inputEl, message) {
  if (!inputEl) return;
  const cleanMsg = String(message || '').replace(/^[⛔⚠️\s]+/u, '').trim();
  if (!cleanMsg) {
    clearFieldError(inputEl);
    return;
  }

  inputEl.classList.add('input-error');
  inputEl.setAttribute('aria-invalid', 'true');

  // หาหรือสร้าง element แสดงข้อความสีแดงใต้ช่อง
  let errEl = inputEl._inlineErrorEl;
  if (!errEl || !document.body.contains(errEl)) {
    const parent = inputEl.parentElement;
    if (parent) {
      errEl = parent.querySelector(':scope > .field-inline-error[data-auto-inline="1"]');
    }
    if (!errEl) {
      errEl = document.createElement('div');
      errEl.className = 'field-inline-error';
      errEl.setAttribute('data-auto-inline', '1');
      if (inputEl.nextSibling) {
        inputEl.parentNode.insertBefore(errEl, inputEl.nextSibling);
      } else if (inputEl.parentNode) {
        inputEl.parentNode.appendChild(errEl);
      }
    }
    inputEl._inlineErrorEl = errEl;
  }

  errEl.textContent = `⛔ ${cleanMsg}`;
  errEl.classList.remove('hidden');

  if (!inputEl._hasInlineErrorClearHook) {
    inputEl._hasInlineErrorClearHook = true;
    const onEdit = () => clearFieldError(inputEl);
    inputEl.addEventListener('input', onEdit);
    inputEl.addEventListener('change', onEdit);
  }
}

/**
 * ล้างข้อความผิดพลาดสีแดงใต้ช่องกรอก
 * @param {HTMLElement|null} inputEl
 */
export function clearFieldError(inputEl) {
  if (!inputEl) return;
  inputEl.classList.remove('input-error');
  inputEl.removeAttribute('aria-invalid');
  const errEl = inputEl._inlineErrorEl;
  if (errEl) {
    errEl.textContent = '';
    errEl.classList.add('hidden');
  }
}

/**
 * ล้างข้อความผิดพลาดสีแดงทั้งหมดภายในฟอร์ม/คอนเทนเนอร์
 * @param {HTMLElement|null} rootEl
 */
export function clearAllFieldErrors(rootEl) {
  if (!rootEl) return;
  rootEl.querySelectorAll('.input-error').forEach((el) => {
    clearFieldError(el);
  });
  rootEl.querySelectorAll('.field-inline-error[data-auto-inline="1"]').forEach((el) => {
    el.textContent = '';
    el.classList.add('hidden');
  });
}

/**
 * แจ้งเตือนกรณีผิดพลาดครบทั้ง 2 แบบพร้อมกัน (Inline สีแดงใต้ช่อง + Toast สีแดงมุมขวาบน 5 วินาที)
 */
export function notifyError(message, fieldEl = null, inlineBannerEl = null) {
  const cleanMsg = String(message || 'ไม่สามารถดำเนินการได้ กรุณาตรวจสอบข้อมูลอีกครั้ง').replace(/^[⛔⚠️\s]+/u, '').trim();
  if (fieldEl) {
    setFieldError(fieldEl, cleanMsg);
  }
  if (inlineBannerEl) {
    inlineBannerEl.className = 'text-small text-danger';
    inlineBannerEl.textContent = `⛔ ${cleanMsg}`;
  }
  return showToast(cleanMsg, 'error');
}

/**
 * แจ้งเตือนกรณีทำรายการสำเร็จ (Toast สีเขียว 5 วินาที อย่างเดียว)
 */
export function notifySuccess(message, inlineBannerEl = null) {
  if (inlineBannerEl) {
    inlineBannerEl.textContent = '';
  }
  const cleanMsg = String(message || 'ทำรายการสำเร็จ').replace(/^[✓✅\s]+/u, '').trim();
  return showToast(cleanMsg, 'success');
}
