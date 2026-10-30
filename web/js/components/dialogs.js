// web/js/components/dialogs.js — กล่องโต้ตอบโมดัลตรงกับ ui/components/dialogs.py + เชื่อมต่อระบบ Toast สำหรับผลลัพธ์สำเร็จ/ผิดพลาด
import { esc, resolveAssetUrl } from '../api.js';
// web/js/components/toast.js — คอมโพเนนต์แจ้งเตือน Toast มุมขวาบน (ค้าง 5 วินาที) + ข้อความผิดพลาดสีแดงใต้ช่องกรอก (Inline Field Error)


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

const ICONS = {
  info: 'ℹ️',
  success: '✅',
  error: '⛔',
  warning: '⚠️',
  question: '❓',
};

function getModalRoot() {
  let root = document.getElementById('modal-root');
  if (!root) {
    root = document.createElement('div');
    root.id = 'modal-root';
    document.body.appendChild(root);
  }
  return root;
}

export function openModal({ title = '', width = 440, render, onClose = null }) {
  const root = getModalRoot();
  const backdrop = document.createElement('div');
  backdrop.className = 'modal-backdrop';

  const card = document.createElement('div');
  card.className = 'modal-card';
  card.style.maxWidth = `${width}px`;
  backdrop.appendChild(card);

  let closed = false;
  const close = (val) => {
    if (closed) return;
    closed = true;
    document.removeEventListener('keydown', onKey);
    backdrop.remove();
    if (onClose) onClose(val);
  };

  const onKey = (e) => {
    if (e.key === 'Escape') {
      close(null);
    }
  };
  document.addEventListener('keydown', onKey);
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) close(null);
  });

  root.appendChild(backdrop);
  render(card, close);
  return { close, card, backdrop };
}

export function showMessage(title, message, kind = 'info', buttonText = 'ตกลง') {
  // กติกาข้อ 5.3: showMessage ที่เป็นแค่ "สำเร็จ" -> Toast เขียว; ที่เป็น "ผิดพลาด/คำเตือน" -> Toast แดง;
  // ส่วนชนิด 'info' ที่มีเนื้อหาให้อ่านจริงจัง ให้คงเป็น modal เดิม
  if (kind === 'success') {
    const combined = message && title && !String(message).includes(title)
      ? `${title}: ${message}`
      : (message || title || 'ดำเนินการสำเร็จ');
    showToast(combined, 'success');
    return Promise.resolve(true);
  }
  if (kind === 'error' || kind === 'warning') {
    const combined = message && title && !String(message).includes(title)
      ? `${title}: ${message}`
      : (message || title || 'ไม่สามารถดำเนินการได้');
    showToast(combined, 'error');
    return Promise.resolve(true);
  }
  return new Promise((resolve) => {
    openModal({
      title,
      width: 420,
      onClose: () => resolve(),
      render(card, close) {
        const icon = ICONS[kind] || 'ℹ️';
        card.innerHTML = `
          <div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:18px">
            <div style="font-size:30px;line-height:1">${icon}</div>
            <div style="flex:1;min-width:0">
              <div class="text-h3" style="margin-bottom:6px">${esc(title)}</div>
              <div class="text-body text-muted" style="white-space:pre-line;word-break:break-word">${esc(message)}</div>
            </div>
          </div>
          <div style="display:flex;justify-content:flex-end;gap:10px">
            <button type="button" class="btn btn-primary btn-md" data-role="ok" style="min-width:110px">${esc(buttonText)}</button>
          </div>
        `;
        const okBtn = card.querySelector('[data-role="ok"]');
        okBtn.addEventListener('click', () => close(true));
        setTimeout(() => okBtn.focus(), 20);
      },
    });
  });
}

export function confirm(title, message, { confirmText = 'ยืนยัน', cancelText = 'ยกเลิก', danger = false } = {}) {
  return new Promise((resolve) => {
    openModal({
      title,
      width: 420,
      onClose: (val) => resolve(Boolean(val)),
      render(card, close) {
        const btnKind = danger ? 'btn-danger' : 'btn-primary';
        card.innerHTML = `
          <div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:18px">
            <div style="font-size:30px;line-height:1">❓</div>
            <div style="flex:1;min-width:0">
              <div class="text-h3" style="margin-bottom:6px">${esc(title)}</div>
              <div class="text-body text-muted" style="white-space:pre-line;word-break:break-word">${esc(message)}</div>
            </div>
          </div>
          <div style="display:flex;justify-content:flex-end;gap:10px">
            <button type="button" class="btn btn-outline btn-md" data-role="cancel" style="min-width:110px">${esc(cancelText)}</button>
            <button type="button" class="btn ${btnKind} btn-md" data-role="ok" style="min-width:110px">${esc(confirmText)}</button>
          </div>
        `;
        card.querySelector('[data-role="cancel"]').addEventListener('click', () => close(false));
        const okBtn = card.querySelector('[data-role="ok"]');
        okBtn.addEventListener('click', () => close(true));
        setTimeout(() => okBtn.focus(), 20);
      },
    });
  });
}

export function askReason(title, message = '', { required = true, confirmText = 'ยืนยัน', placeholder = '', danger = false } = {}) {
  return new Promise((resolve) => {
    openModal({
      title,
      width: 460,
      onClose: (val) => resolve(val === undefined ? null : val),
      render(card, close) {
        const btnKind = danger ? 'btn-danger' : 'btn-primary';
        card.innerHTML = `
          <div class="text-h3" style="margin-bottom:4px">${esc(title)}</div>
          ${message ? `<div class="text-body text-muted" style="margin-bottom:10px;white-space:pre-line">${esc(message)}</div>` : ''}
          <textarea class="textarea" data-role="reason" rows="4" placeholder="${esc(placeholder)}"></textarea>
          <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-top:4px"></div>
          ${placeholder ? `<div class="text-small text-muted" style="margin-bottom:8px">${esc(placeholder)}</div>` : ''}
          <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:10px">
            <button type="button" class="btn btn-outline btn-md" data-role="cancel" style="min-width:110px">ยกเลิก</button>
            <button type="button" class="btn ${btnKind} btn-md" data-role="ok" style="min-width:110px">${esc(confirmText)}</button>
          </div>
        `;
        const ta = card.querySelector('[data-role="reason"]');
        const err = card.querySelector('[data-role="err"]');
        ta.addEventListener('input', () => {
          ta.classList.remove('input-error');
          err.textContent = '';
        });
        card.querySelector('[data-role="cancel"]').addEventListener('click', () => close(null));
        card.querySelector('[data-role="ok"]').addEventListener('click', () => {
          const text = ta.value.trim();
          if (required && !text) {
            ta.classList.add('input-error');
            err.textContent = 'กรุณาระบุเหตุผล';
            showToast('กรุณาระบุเหตุผลก่อนยืนยัน', 'error');
            return;
          }
          close(text);
        });
        setTimeout(() => ta.focus(), 20);
      },
    });
  });
}

export function showImageWindow(path, title = 'ดูรูป') {
  const url = resolveAssetUrl(path, '');
  openModal({
    title,
    width: 700,
    render(card, close) {
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <div class="text-h3">${esc(title)}</div>
          <button type="button" class="btn btn-outline btn-sm" data-role="close">ปิด</button>
        </div>
        <div style="display:flex;justify-content:center;align-items:center;min-height:260px;background:var(--color-surface-alt);border-radius:10px;padding:12px;overflow:hidden">
          ${url ? `<img src="${esc(url)}" alt="${esc(title)}" style="max-width:100%;max-height:70vh;object-fit:contain;border-radius:8px" data-role="img" />` : `<div class="text-danger">ไม่พบไฟล์รูป หรือเปิดไฟล์ไม่ได้</div>`}
        </div>
      `;
      const img = card.querySelector('[data-role="img"]');
      if (img) {
        img.addEventListener('error', () => {
          img.replaceWith(Object.assign(document.createElement('div'), {
            className: 'text-danger',
            textContent: 'ไม่พบไฟล์รูป หรือเปิดไฟล์ไม่ได้',
          }));
        });
      }
      card.querySelector('[data-role="close"]').addEventListener('click', () => close(null));
    },
  });
}

export function openFileUrl(path) {
  if (!path) return false;
  const url = resolveAssetUrl(path, '');
  if (!url) return false;
  window.open(url, '_blank', 'noopener');
  return true;
}



export const dialogs = {
  confirm,
  showMessage,
  askReason,
  openModal,
  showImageWindow,
  openFileUrl,
  showToast,
  setFieldError,
  clearFieldError,
  clearAllFieldErrors,
  notifyError,
  notifySuccess,
};
