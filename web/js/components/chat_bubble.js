// web/js/components/chat_bubble.js — ChatBubble & ChatMessageList (รองรับทั้งข้อความและรูปภาพในแชท)
import { esc, formatDateTime, resolveAssetUrl } from '../api.js';
import { showImageWindow } from './dialogs.js';

function senderLabel(msg, sender) {
  const name = msg.sender_name || '';
  if (sender === 'ai') return '🤖 ผู้ช่วย AI';
  if (sender === 'admin') return `ผู้ดูแลร้าน${name ? ` · ${name}` : ''}`;
  return name || 'ลูกค้า';
}

export function createChatBubble(msg, isMine = false) {
  const sender = msg.sender_type || 'user';
  const row = document.createElement('div');
  row.style.display = 'flex';
  row.style.justifyContent = isMine ? 'flex-end' : 'flex-start';
  row.style.padding = '3px 8px';

  let bg = 'var(--color-surface)';
  let fg = 'var(--color-text-main)';
  let meta = 'var(--color-text-muted)';
  let border = 'var(--color-border)';

  if (isMine) {
    bg = 'var(--color-primary)';
    fg = '#1A1A1A';
    meta = '#4A4A4A';
    border = 'var(--color-primary)';
  } else if (sender === 'ai') {
    bg = 'var(--badge-info-bg)';
    fg = 'var(--badge-info-fg)';
    meta = 'var(--badge-info-fg)';
    border = 'var(--badge-info-bg)';
  }

  const bubble = document.createElement('div');
  bubble.style.background = bg;
  bubble.style.color = fg;
  bubble.style.border = `1px solid ${border}`;
  bubble.style.borderRadius = '14px';
  bubble.style.padding = '8px 12px 6px';
  bubble.style.maxWidth = '420px';
  bubble.style.minWidth = '110px';
  bubble.style.wordBreak = 'break-word';

  const hasText = Boolean(msg.message && String(msg.message).trim());
  const hasImage = Boolean(msg.image_path && String(msg.image_path).trim());
  const imgUrl = hasImage ? resolveAssetUrl(msg.image_path) : '';

  bubble.innerHTML = `
    ${!isMine ? `<div class="text-small-bold" style="color:${meta};margin-bottom:2px">${esc(senderLabel(msg, sender))}</div>` : ''}
    ${hasImage ? `<img src="${esc(imgUrl)}" alt="รูปภาพในแชท" class="chat-bubble-image" data-role="chat-img" loading="lazy" />` : ''}
    ${hasText ? `<div class="text-body" style="white-space:pre-line;color:${fg}">${esc(msg.message || '')}</div>` : ''}
    <div class="text-tiny" style="color:${meta};text-align:right;margin-top:2px">${esc(formatDateTime(msg.created_at))}</div>
  `;

  if (hasImage) {
    const imgEl = bubble.querySelector('[data-role="chat-img"]');
    if (imgEl) {
      imgEl.addEventListener('click', () => {
        showImageWindow('รูปภาพในแชท', imgUrl);
      });
    }
  }

  row.appendChild(bubble);
  return row;
}

export function createChatMessageList({
  viewer = 'customer',
  emptyText = 'ยังไม่มีข้อความ — เริ่มสนทนาได้เลย',
} = {}) {
  const box = document.createElement('div');
  box.style.display = 'flex';
  box.style.flexDirection = 'column';
  box.style.overflowY = 'auto';
  box.style.flex = '1';
  box.style.padding = '8px 4px';

  const seen = new Set();
  let lastId = 0;
  let emptyEl = null;
  let typingEl = null;

  function showEmpty() {
    emptyEl = document.createElement('div');
    emptyEl.className = 'text-small text-muted';
    emptyEl.style.textAlign = 'center';
    emptyEl.style.padding = '30px 12px';
    emptyEl.textContent = emptyText;
    box.appendChild(emptyEl);
  }

  function isMine(msg) {
    const sender = msg.sender_type || 'user';
    return sender === (viewer === 'customer' ? 'user' : 'admin');
  }

  function scrollToBottom() {
    setTimeout(() => {
      box.scrollTop = box.scrollHeight;
    }, 30);
  }

  function keepTypingLast() {
    if (typingEl && typingEl.parentNode === box) {
      box.appendChild(typingEl);
    }
  }

  function appendMessages(messages = []) {
    let added = 0;
    for (const msg of messages || []) {
      const id = msg.id != null ? Number(msg.id) : null;
      if (id !== null) {
        if (seen.has(id)) continue;
        seen.add(id);
        if (id > lastId) lastId = id;
      }
      if (emptyEl) {
        emptyEl.remove();
        emptyEl = null;
      }
      box.appendChild(createChatBubble(msg, isMine(msg)));
      added += 1;
    }
    if (added > 0) {
      keepTypingLast();
      scrollToBottom();
    }
    return added;
  }

  function clear() {
    box.innerHTML = '';
    seen.clear();
    lastId = 0;
    typingEl = null;
    emptyEl = null;
    showEmpty();
  }

  function setMessages(messages = []) {
    clear();
    appendMessages(messages);
  }

  function showTyping(text = '🤖 AI กำลังพิมพ์...') {
    if (!typingEl) {
      typingEl = document.createElement('div');
      typingEl.className = 'text-small text-muted';
      typingEl.style.padding = '4px 12px';
      box.appendChild(typingEl);
    }
    typingEl.textContent = text;
    keepTypingLast();
    scrollToBottom();
  }

  function hideTyping() {
    if (typingEl) {
      typingEl.remove();
      typingEl = null;
    }
  }

  showEmpty();

  return {
    el: box,
    get lastId() { return lastId; },
    setMessages,
    appendMessages,
    clear,
    showTyping,
    hideTyping,
    scrollToBottom,
  };
}
