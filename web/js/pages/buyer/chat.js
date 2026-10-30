// web/js/pages/buyer/chat.js — หน้าแชทกับร้านและผู้ช่วย AI (Quick Replies, โหมดถาม AI, ให้ AI แนะนำไม้ 3 รุ่น, ส่งรูปภาพได้)
import { api, BALANCES, esc, FLEXES, LEVELS, WEIGHT_CLASSES } from '../../api.js';
import { createChatMessageList } from '../../components/chat_bubble.js';
import { openModal, showToast } from '../../components/dialogs.js';
import { pageTitleHtml } from '../../components/buyer_common.js';

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  wrap.style.display = 'flex';
  wrap.style.flexDirection = 'column';
  wrap.style.height = 'calc(100vh - 76px)';
  container.appendChild(wrap);

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      ${pageTitleHtml('💬 แชทกับร้าน & ผู้ช่วย AI แบดมินตัน', 'สอบถามข้อมูลสินค้า ส่งรูปภาพ โปรโมชัน การสั่งซื้อ หรือให้ AI ช่วยคัดเลือกไม้แบดมินตันที่เหมาะกับคุณ')}
      <div class="text-small-bold text-info" data-role="mode-lbl"></div>
    </div>

    <div class="card" style="padding:10px 14px;margin-bottom:8px">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px">
        <span class="text-small-bold">🤖 บริการผู้ช่วย AI:</span>
        <button type="button" class="btn btn-danger btn-sm" data-role="ai-racket-btn">🎯 ให้ AI แนะนำไม้ 3 รุ่นตามสไตล์คุณ</button>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer" class="text-small-bold">
          <input type="checkbox" data-role="force-ai" />
          <span>ถาม AI ทันที (แม้มีแอดมินออนไลน์)</span>
        </label>
      </div>
      <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap" data-role="quick-row">
        <span class="text-tiny text-muted">คำถามยอดฮิต:</span>
      </div>
    </div>

    <div class="card" data-role="msg-holder" style="flex:1;display:flex;flex-direction:column;min-height:280px;overflow:hidden;margin-bottom:8px"></div>

    <div class="chat-attach-preview hidden" data-role="attach-preview" style="margin-bottom:6px">
      <img data-role="attach-thumb" src="" alt="preview" />
      <span class="text-small-bold" data-role="attach-name" style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>
      <button type="button" class="btn btn-danger btn-sm" data-role="attach-clear" style="height:26px;padding:0 8px">✕ ลบรูป</button>
    </div>

    <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:4px"></div>

    <div style="display:flex;gap:8px;align-items:center">
      <input type="file" data-role="file-input" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" style="display:none" />
      <button type="button" class="btn btn-outline btn-md" data-role="attach-btn" style="height:42px;padding:0 12px;white-space:nowrap" title="แนบรูปภาพส่งในแชท">📷 ส่งรูป</button>
      <input type="text" class="input" data-role="entry" placeholder="พิมพ์ข้อความหรือแนบรูปภาพสอบถามร้าน..." style="flex:1;height:42px" />
      <button type="button" class="btn btn-primary btn-md" data-role="send-btn" style="height:42px;min-width:105px">ส่งข้อความ</button>
      <button type="button" class="btn btn-info btn-md" data-role="ask-ai-btn" style="height:42px;min-width:105px">🤖 ถาม AI</button>
    </div>
  `;

  const modeLbl = wrap.querySelector('[data-role="mode-lbl"]');
  const forceAiChk = wrap.querySelector('[data-role="force-ai"]');
  const quickRow = wrap.querySelector('[data-role="quick-row"]');
  const errEl = wrap.querySelector('[data-role="err"]');
  const entry = wrap.querySelector('[data-role="entry"]');
  const fileInput = wrap.querySelector('[data-role="file-input"]');
  const attachBtn = wrap.querySelector('[data-role="attach-btn"]');
  const attachPreview = wrap.querySelector('[data-role="attach-preview"]');
  const attachThumb = wrap.querySelector('[data-role="attach-thumb"]');
  const attachName = wrap.querySelector('[data-role="attach-name"]');
  const attachClearBtn = wrap.querySelector('[data-role="attach-clear"]');
  const sendBtn = wrap.querySelector('[data-role="send-btn"]');

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
    entry.focus();
  });

  attachClearBtn.addEventListener('click', clearAttachedImage);

  const msgList = createChatMessageList({ viewer: 'customer' });
  wrap.querySelector('[data-role="msg-holder"]').appendChild(msgList.el);

  function updateModeText(shouldAi) {
    modeLbl.textContent = shouldAi
      ? '🤖 ไม่มีแอดมินออนไลน์ — AI พร้อมตอบทันที (หรือกดปุ่ม 🤖 ถาม AI ได้ตลอดเวลา)'
      : "🟢 แอดมินออนไลน์ — ส่งแชทหรือส่งรูปหาแอดมิน หรือกด '🤖 ถาม AI' เพื่อถาม AI ทันที";
  }

  // Load quick replies & initial history
  try {
    const [qrs, hist] = await Promise.all([
      api.get('/api/chat/quick-replies'),
      api.get('/api/chat/messages', { limit: 100 }),
    ]);
    for (const qr of qrs || []) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-outline btn-sm';
      b.textContent = qr.label;
      b.addEventListener('click', async () => {
        errEl.textContent = '';
        try {
          const res = await api.post('/api/chat/quick-reply', { reply_id: qr.id });
          msgList.appendMessages([res.question, res.answer].filter(Boolean));
        } catch (err) {
          const em = err.message || 'ไม่สามารถส่งคำถามด่วนได้';
          errEl.textContent = `⛔ ${em}`;
          showToast(em, 'error');
        }
      });
      quickRow.appendChild(b);
    }
    msgList.setMessages((hist && hist.messages) || []);
    updateModeText(Boolean(hist && hist.should_ai_reply));
    await router.refresh_shell();
  } catch (err) {
    errEl.textContent = `⛔ ${err.message}`;
  }

  async function sendMessage(forceAi = false) {
    const text = entry.value.trim();
    const imgFile = selectedImageFile;
    if (!text && !imgFile) {
      const msg = 'กรุณาพิมพ์ข้อความหรือเลือกรูปภาพก่อนส่ง';
      errEl.textContent = `⛔ ${msg}`;
      showToast(msg, 'error');
      return;
    }
    const useAi = Boolean(forceAi || forceAiChk.checked);
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
      entry.value = '';
      clearAttachedImage();

      const res = await api.post('/api/chat/messages', {
        text,
        image_path: imagePath,
        force_ai: useAi,
      });
      const newMsgs = [res.message];
      if (res.ai_message) newMsgs.push(res.ai_message);
      msgList.appendMessages(newMsgs.filter(Boolean));
      if (res.ai_pending) {
        msgList.showTyping();
      }
    } catch (err) {
      const em = err.message || 'ส่งข้อความไม่สำเร็จ';
      errEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
    } finally {
      sendBtn.disabled = false;
      attachBtn.disabled = false;
    }
  }

  sendBtn.addEventListener('click', () => sendMessage(false));
  wrap.querySelector('[data-role="ask-ai-btn"]').addEventListener('click', () => sendMessage(true));
  entry.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage(false);
    }
  });

  wrap.querySelector('[data-role="ai-racket-btn"]').addEventListener('click', () => {
    const anyOpt = 'ไม่ระบุ (เลือกได้ทุกแบบ)';
    openModal({
      title: '🎯 ให้ AI แนะนำไม้แบดมินตัน 3 รุ่นที่เหมาะกับคุณ',
      width: 460,
      render(card, close) {
        card.style.padding = '0';
        card.style.overflow = 'hidden';
        card.innerHTML = `
          <div style="background:var(--color-secondary);padding:14px 20px">
            <div class="text-h3 text-primary">🎯 วิเคราะห์และแนะนำไม้แบดมินตัน 3 รุ่น</div>
            <div class="text-small" style="color:#FFFFFF">เลือกสเปกที่คุณต้องการ (หรือเว้นว่างให้ระบบคัดรุ่นคุ้มค่าที่สุดในร้าน)</div>
          </div>
          <div style="padding:14px 22px 18px;display:flex;flex-direction:column;gap:8px">
            <div>
              <div class="text-small-bold">น้ำหนักไม้ (Weight Class)</div>
              <select class="select" data-role="w"><option value="">${anyOpt}</option>${WEIGHT_CLASSES.map((v) => `<option value="${v}">${v}</option>`).join('')}</select>
            </div>
            <div>
              <div class="text-small-bold">จุดสมดุล / สไตล์การเล่น (Balance)</div>
              <select class="select" data-role="b"><option value="">${anyOpt}</option>${BALANCES.map((v) => `<option value="${v}">${v}</option>`).join('')}</select>
            </div>
            <div>
              <div class="text-small-bold">ความแข็งก้าน (Flex)</div>
              <select class="select" data-role="f"><option value="">${anyOpt}</option>${FLEXES.map((v) => `<option value="${v}">${v}</option>`).join('')}</select>
            </div>
            <div>
              <div class="text-small-bold">ระดับผู้เล่น (Level)</div>
              <select class="select" data-role="l"><option value="">${anyOpt}</option>${LEVELS.map((v) => `<option value="${v}">${v}</option>`).join('')}</select>
            </div>
            <div>
              <div class="text-small-bold">งบประมาณสูงสุด (บาท — ไม่บังคับ)</div>
              <input type="text" class="input" data-role="budget" placeholder="เช่น 3500" />
            </div>
            <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">
              <button type="button" class="btn btn-outline btn-md" data-role="cancel">ยกเลิก</button>
              <button type="button" class="btn btn-danger btn-md" data-role="submit">🤖 ให้ AI แนะนำ 3 รุ่นเลย</button>
            </div>
          </div>
        `;
        card.querySelector('[data-role="cancel"]').addEventListener('click', () => close());
        card.querySelector('[data-role="submit"]').addEventListener('click', async () => {
          const wVal = card.querySelector('[data-role="w"]').value || null;
          const bVal = card.querySelector('[data-role="b"]').value || null;
          const fVal = card.querySelector('[data-role="f"]').value || null;
          const lVal = card.querySelector('[data-role="l"]').value || 'Beginner';
          const budget = card.querySelector('[data-role="budget"]').value.trim() || null;
          const styleMap = { 'Heavy Head': 'attack', 'Light Head': 'speed', 'Even Balance': 'control' };
          try {
            const res = await api.post('/api/chat/recommend-rackets', {
              level: lVal,
              style: styleMap[bVal] || 'attack',
              budget,
              flex: fVal,
              balance: bVal,
              weight_class: wVal,
              post_to_chat: true,
            });
            close();
            if (res.messages) msgList.appendMessages(res.messages);
          } catch (err) {
            const em = err.message || 'ไม่สามารถขอคำแนะนำได้';
            errEl.textContent = `⛔ ${em}`;
            showToast(em, 'error');
            close();
          }
        });
      },
    });
  });

  // Poll new messages every 3s
  const pollIv = setInterval(async () => {
    if (!document.body.contains(wrap)) return;
    try {
      const res = await api.get('/api/chat/messages', { after_id: msgList.lastId });
      const newMsgs = (res && res.messages) || [];
      if (newMsgs.length) {
        msgList.appendMessages(newMsgs);
        if (newMsgs.some((m) => m.sender_type !== 'user')) {
          msgList.hideTyping();
          updateModeText(Boolean(res.should_ai_reply));
          await router.refresh_shell();
        }
      }
    } catch (e) {}
  }, 3000);

  return () => {
    clearInterval(pollIv);
    clearAttachedImage();
  };
}
