// web/js/components/image_picker.js — ตัวเลือกรูปพร้อมพรีวิว + ลากวาง + อัปโหลด (ตรงกับ ui/components/image_picker.py)
import { api, esc, resolveAssetUrl } from '../api.js';
import { showToast } from './dialogs.js';

const ALLOWED_EXTS = ['.jpg', '.jpeg', '.png', '.webp'];
const MAX_BYTES = 5 * 1024 * 1024;

export function createImagePicker({
  size = [160, 160],
  initialPath = null,
  onChange = null,
  buttonText = 'เลือกรูป...',
  allowClear = true,
} = {}) {
  const [w, h] = Array.isArray(size) ? size : [Number(size), Number(size)];
  let existingPath = initialPath || null;
  let selectedFile = null;
  let previewDataUrl = null;
  let cleared = false;
  let isDisabled = false;

  const wrap = document.createElement('div');
  wrap.style.display = 'inline-flex';
  wrap.style.flexDirection = 'column';
  wrap.style.alignItems = 'center';

  wrap.innerHTML = `
    <div data-role="preview-box" style="width:${w}px;height:${h}px;border-radius:10px;background:var(--color-surface-alt);border:1px dashed var(--color-border);display:flex;align-items:center;justify-content:center;overflow:hidden;cursor:pointer" title="คลิกหรือลากไฟล์รูปมาวาง">
      <img data-role="preview-img" src="${esc(resolveAssetUrl(existingPath))}" alt="preview" style="max-width:100%;max-height:100%;object-fit:contain" />
    </div>
    <input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" class="hidden" data-role="file-in" />
    <div style="display:flex;gap:6px;margin-top:8px">
      <button type="button" class="btn btn-outline btn-sm" data-role="choose" style="min-width:110px">${esc(buttonText)}</button>
      ${allowClear ? `<button type="button" class="btn btn-ghost btn-sm" data-role="clear" style="min-width:70px">ลบรูป</button>` : ''}
    </div>
    <div class="text-small text-danger" data-role="err" style="max-width:${Math.max(w, 180)}px;text-align:center;margin-top:4px;min-height:18px"></div>
  `;

  const previewBox = wrap.querySelector('[data-role="preview-box"]');
  const previewImg = wrap.querySelector('[data-role="preview-img"]');
  const fileIn = wrap.querySelector('[data-role="file-in"]');
  const chooseBtn = wrap.querySelector('[data-role="choose"]');
  const clearBtn = wrap.querySelector('[data-role="clear"]');
  const errEl = wrap.querySelector('[data-role="err"]');

  function refreshPreview() {
    if (previewDataUrl) {
      previewImg.src = previewDataUrl;
    } else if (cleared) {
      previewImg.src = '/assets/icons/no_image.svg';
    } else {
      previewImg.src = resolveAssetUrl(existingPath);
    }
  }

  previewImg.addEventListener('error', () => {
    if (!previewImg.src.endsWith('/assets/icons/no_image.svg')) {
      previewImg.src = '/assets/icons/no_image.svg';
    }
  });

  function handleFile(file) {
    if (!file || isDisabled) return;
    const name = (file.name || '').toLowerCase();
    const extOk = ALLOWED_EXTS.some((ext) => name.endsWith(ext));
    if (!extOk) {
      const msg = 'รองรับเฉพาะไฟล์ ' + ALLOWED_EXTS.join(', ');
      errEl.textContent = msg;
      showToast(msg, 'error');
      return;
    }
    if (file.size > MAX_BYTES) {
      const msg = `ไฟล์ใหญ่เกิน ${Math.floor(MAX_BYTES / (1024 * 1024))}MB`;
      errEl.textContent = msg;
      showToast(msg, 'error');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      selectedFile = file;
      previewDataUrl = reader.result;
      cleared = false;
      errEl.textContent = '';
      refreshPreview();
      if (onChange) onChange(apiObj);
    };
    reader.onerror = () => {
      const msg = 'ไฟล์นี้ไม่ใช่รูปภาพที่เปิดได้';
      errEl.textContent = msg;
      showToast(msg, 'error');
    };
    reader.readAsDataURL(file);
  }

  chooseBtn.addEventListener('click', () => { if (!isDisabled) fileIn.click(); });
  previewBox.addEventListener('click', () => { if (!isDisabled) fileIn.click(); });
  fileIn.addEventListener('change', () => {
    if (fileIn.files && fileIn.files[0]) {
      handleFile(fileIn.files[0]);
    }
    fileIn.value = '';
  });

  previewBox.addEventListener('dragover', (e) => {
    if (isDisabled) return;
    e.preventDefault();
    previewBox.style.borderColor = 'var(--color-primary)';
  });
  previewBox.addEventListener('dragleave', () => {
    previewBox.style.borderColor = 'var(--color-border)';
  });
  previewBox.addEventListener('drop', (e) => {
    if (isDisabled) return;
    e.preventDefault();
    previewBox.style.borderColor = 'var(--color-border)';
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (isDisabled) return;
      selectedFile = null;
      previewDataUrl = null;
      cleared = true;
      errEl.textContent = '';
      refreshPreview();
      if (onChange) onChange(apiObj);
    });
  }

  const apiObj = {
    el: wrap,
    getSelectedFile: () => selectedFile,
    getExistingPath: () => (cleared ? null : existingPath),
    isCleared: () => Boolean(cleared && !selectedFile),
    hasChange: () => Boolean(selectedFile || (cleared && !selectedFile)),
    setDisabled(disabled) {
      isDisabled = Boolean(disabled);
      chooseBtn.disabled = isDisabled;
      if (clearBtn) clearBtn.disabled = isDisabled;
      previewBox.style.cursor = isDisabled ? 'not-allowed' : 'pointer';
      previewBox.style.opacity = isDisabled ? '0.78' : '1';
    },
    setImage(path) {
      existingPath = path || null;
      selectedFile = null;
      previewDataUrl = null;
      cleared = false;
      errEl.textContent = '';
      refreshPreview();
    },
    async resolveUploadedPath(folder = 'products', prefix = 'img') {
      if (selectedFile) {
        const uploaded = await api.uploadImage(selectedFile, folder, prefix);
        existingPath = uploaded;
        selectedFile = null;
        return uploaded;
      }
      if (cleared) return null;
      return existingPath;
    },
  };
  apiObj.reset = apiObj.setImage;
  apiObj.setInitial = apiObj.setImage;
  return apiObj;
}
