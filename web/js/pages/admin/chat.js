// web/js/pages/admin/chat.js — แชทกับลูกค้าฝั่งแอดมิน/เจ้าของ (รายการห้องซ้าย + ห้องแชทขวา โพลทุก 3 วินาที + ส่งรูปภาพได้)
import { api, esc, formatDateTime } from '../../api.js';
import { pillHtml, thumbHtml } from '../../components/admin_common.js';
import { createChatMessageList } from '../../components/chat_bubble.js';
import { showToast } from '../../components/dialogs.js';

function displayName(t) {
  return t.full_name || t.username || `ลูกค้า #${t.customer_id}`;
}

function previewText(t) {
  let text = String(t.last_message || '').replace(/\s+/g, ' ').trim();
  if (!text && t.last_image_path) text = '📷 [ส่งรูปภาพ]';
  if (text.length > 32) text = text.slice(0, 32) + '…';
  if (t.last_sender_type === 'ai') return `AI: ${text}`;
  if (t.last_sender_type === 'admin') return `ร้าน: ${text}`;
  return text;
}

export async function render(container, router, params = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let selectedCustomerId = params.customer_id ? Number(params.customer_id) : null;
  let threads = [];

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">แชทลูกค้า</div>
        <div class="text-small text-muted">ตอบข้อความและส่งรูปภาพให้ลูกค้าได้ทันที (ทั้งแอดมินและเจ้าของร้าน) — ถ้าไม่มีแอดมินออนไลน์ AI จะตอบแทน</div>
      </div>
      <button type="button" class="btn btn-outline btn-sm" data-role="refresh">🔄 รีเฟรช</button>
    </div>

    <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:4px"></div>

    <div style="display:grid;grid-template-columns:310px 1fr;gap:10px;height:560px">
      <div class="card" style="padding:10px;display:flex;flex-direction:column;overflow:hidden">
        <input type="text" class="input" data-role="search" placeholder="ค้นหาชื่อลูกค้า / ข้อความ" style="margin-bottom:8px;height:36px" />
        <div data-role="thread-list" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:4px"></div>
      </div>

      <div class="card" style="padding:10px 14px;display:flex;flex-direction:column;overflow:hidden">
        <div class="text-h3" data-role="chat-title" style="margin-bottom:6px">เลือกห้องแชททางซ้าย</div>
        <div data-role="msg-holder" style="flex:1;display:flex;flex-direction:column;overflow:hidden;border:1px solid var(--color-border);border-radius:10px;margin-bottom:8px">
          <div data-role="placeholder" class="text-body text-muted" style="margin:auto;text-align:center;white-space:pre-line">ยังไม่ได้เลือกห้องแชท
คลิกชื่อลูกค้าทางซ้ายเพื่อเริ่มตอบ</div>
        </div>

        <div class="chat-attach-preview hidden" data-role="attach-preview" style="margin-bottom:6px">
          <img data-role="attach-thumb" src="" alt="preview" />
          <span class="text-small-bold" data-role="attach-name" style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>
          <button type="button" class="btn btn-danger btn-sm" data-role="attach-clear" style="height:26px;padding:0 8px">✕ ลบรูป</button>
        </div>

        <div style="display:flex;gap:8px;align-items:center">
          <input type="file" data-role="file-input" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" style="display:none" />
          <button type="button" class="btn btn-outline btn-md" data-role="attach-btn" style="height:40px;padding:0 12px;white-space:nowrap" disabled title="แนบรูปภาพส่งให้ลูกค้า">📷 ส่งรูป</button>
          <input type="text" class="input" data-role="input" placeholder="พิมพ์ข้อความหรือแนบรูปตอบลูกค้า แล้วกด Enter" style="flex:1;height:40px" disabled />
          <button type="button" class="btn btn-primary btn-md" data-role="send" style="width:96px;height:40px" disabled>ส่ง ➤</button>
        </div>
      </div>
    </div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const searchIn = wrap.querySelector('[data-role="search"]');
  const threadListEl = wrap.querySelector('[data-role="thread-list"]');
  const chatTitle = wrap.querySelector('[data-role="chat-title"]');
  const msgHolder = wrap.querySelector('[data-role="msg-holder"]');
  const placeholder = wrap.querySelector('[data-role="placeholder"]');
  const fileInput = wrap.querySelector('[data-role="file-input"]');
  const attachBtn = wrap.querySelector('[data-role="attach-btn"]');
  const attachPreview = wrap.querySelector('[data-role="attach-preview"]');
  const attachThumb = wrap.querySelector('[data-role="attach-thumb"]');
  const attachName = wrap.querySelector('[data-role="attach-name"]');
  const attachClearBtn = wrap.querySelector('[data-role="attach-clear"]');
  const inputEl = wrap.querySelector('[data-role="input"]');
  const sendBtn = wrap.querySelector('[data-role="send"]');

  let selectedImageFile = null;
  let selectedPreviewUrl = null;

  function clearAttachedImage() {
    selectedImageFile = null;
    if (selectedPreviewUrl) {
      try { URL.revokeObjectURL(selectedPreviewUrl); } catch (_) {}
      selectedPreviewUrl = null;
    }
    attachThumb.src = '';
    attachName.textContent = '';
    attachPreview.classList.add('hidden');
    fileInput.value = '';
  }

  attachBtn.addEventListener('click', () => {
    if (!selectedCustomerId) return;
    fileInput.value = '';
    fileInput.click();
  });

  fileInput.addEventListener('change', () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
      const msg = 'รองรับเฉพาะไฟล์รูปภาพ .jpg, .png และ .webp เท่านั้น';
      errEl.textContent = `⛔ ${msg}`;
      showToast(msg, 'error');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      const msg = 'ไฟล์รูปภาพใหญ่เกินไป (ไม่เกิน 5 MB)';
      errEl.textContent = `⛔ ${msg}`;
      showToast(msg, 'error');
      return;
    }
    clearAttachedImage();
    selectedImageFile = file;
    selectedPreviewUrl = URL.createObjectURL(file);
    attachThumb.src = selectedPreviewUrl;
    attachName.textContent = file.name;
    attachPreview.classList.remove('hidden');
    errEl.textContent = '';
    inputEl.focus();
  });

  attachClearBtn.addEventListener('click', clearAttachedImage);

  const msgList = createChatMessageList({ viewer: 'staff' });
  msgList.el.classList.add('hidden');
  msgHolder.appendChild(msgList.el);

  function renderThreads() {
    threadListEl.innerHTML = '';
    const needle = searchIn.value.trim().toLowerCase();
    const shown = threads.filter((t) => {
      if (!needle) return true;
      return displayName(t).toLowerCase().includes(needle) ||
        String(t.username || '').toLowerCase().includes(needle) ||
        String(t.last_message || '').toLowerCase().includes(needle);
    });
    if (!shown.length) {
      threadListEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:24px">${threads.length ? 'ไม่พบห้องที่ค้นหา' : 'ยังไม่มีการสนทนา'}</div>`;
      return;
    }
    for (const t of shown) {
      const cid = t.customer_id;
      const sel = cid === selectedCustomerId;
      const unread = Number(t.unread_count || 0);
      const r = document.createElement('div');
      r.style.background = sel ? 'var(--color-surface-alt)' : 'transparent';
      r.style.borderRadius = '10px';
      r.style.padding = '8px';
      r.style.display = 'flex';
      r.style.alignItems = 'center';
      r.style.gap = '8px';
      r.style.cursor = 'pointer';
      r.innerHTML = `
        ${thumbHtml(t.avatar_path, 38)}
        <div style="flex:1;min-width:0">
          <div class="text-body-bold" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(displayName(t))}</div>
          <div class="text-small text-muted" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(previewText(t))}</div>
          <div class="text-tiny text-muted">${esc(formatDateTime(t.last_at))}</div>
        </div>
        ${unread > 0 ? pillHtml(unread < 100 ? String(unread) : '99+', 'danger') : ''}
      `;
      r.addEventListener('click', () => selectThread(cid));
      threadListEl.appendChild(r);
    }
  }

  async function fetchThreads() {
    try {
      const res = await api.get('/api/admin/chat/threads');
      threads = res.threads || [];
      renderThreads();
    } catch (err) {
      errEl.textContent = err.message || '';
    }
  }

  async function selectThread(customerId) {
    errEl.textContent = '';
    clearAttachedImage();
    try {
      const res = await api.get('/api/chat/messages', { customer_id: customerId, limit: 200 });
      selectedCustomerId = customerId;
      const t = threads.find((x) => x.customer_id === customerId);
      chatTitle.textContent = `💬 ${t ? displayName(t) : `ลูกค้า #${customerId}`}`;
      placeholder.classList.add('hidden');
      msgList.el.classList.remove('hidden');
      msgList.setMessages(res.messages || []);
      inputEl.disabled = false;
      sendBtn.disabled = false;
      attachBtn.disabled = false;
      inputEl.focus();
      await fetchThreads();
      await router.refresh_shell();
    } catch (err) {
      const em = err.message || 'ไม่สามารถเปิดห้องแชทได้';
      errEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
    }
  }

  async function fetchNewMessages() {
    if (!selectedCustomerId) return;
    try {
      const res = await api.get('/api/chat/messages', {
        customer_id: selectedCustomerId,
        after_id: msgList.lastId,
      });
      const added = msgList.appendMessages(res.messages || []);
      if (added) await router.refresh_shell();
    } catch (e) {}
  }

  async function sendReply() {
    if (!selectedCustomerId) return;
    const text = inputEl.value.trim();
    const imgFile = selectedImageFile;
    if (!text && !imgFile) {
      const msg = 'กรุณาพิมพ์ข้อความหรือเลือกรูปภาพก่อนส่ง';
      errEl.textContent = `⛔ ${msg}`;
      showToast(msg, 'error');
      return;
    }
    errEl.textContent = '';
    sendBtn.disabled = true;
    attachBtn.disabled = true;
    try {
      let imagePath = null;
      if (imgFile) {
        const fd = new FormData();
        fd.append('file', imgFile, imgFile.name);
        const upRes = await api.upload('/api/chat/upload-image', fd);
        imagePath = upRes.path;
      }
      await api.post('/api/admin/chat/reply', {
        customer_id: selectedCustomerId,
        text,
        image_path: imagePath,
      });
      inputEl.value = '';
      clearAttachedImage();
      await fetchNewMessages();
      await fetchThreads();
    } catch (err) {
      const em = err.message || 'ส่งข้อความตอบกลับไม่สำเร็จ';
      errEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
    } finally {
      sendBtn.disabled = false;
      attachBtn.disabled = false;
    }
  }

  searchIn.addEventListener('input', renderThreads);
  sendBtn.addEventListener('click', sendReply);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendReply();
    }
  });
  wrap.querySelector('[data-role="refresh"]').addEventListener('click', async () => {
    await fetchNewMessages();
    await fetchThreads();
  });

  await fetchThreads();
  if (selectedCustomerId) {
    await selectThread(selectedCustomerId);
  }

  const pollIv = setInterval(async () => {
    if (!document.body.contains(wrap)) return;
    if (selectedCustomerId) await fetchNewMessages();
    await fetchThreads();
  }, 3000);

  return () => {
    clearInterval(pollIv);
    clearAttachedImage();
  };
}
