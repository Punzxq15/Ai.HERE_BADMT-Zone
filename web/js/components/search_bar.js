// web/js/components/search_bar.js — ช่องค้นหาพร้อมระบบแนะนำคำค้นอัตโนมัติ (ข้อ 15)
import { api, esc } from '../api.js';
import { iconSvg } from './icons.js';

export function createSearchBar({
  placeholder = 'ค้นหาไม้แบดมินตัน รองเท้า ลูกแบด...',
  width = 360,
  onSubmit = null,
  onSelectSuggestion = null,
  enableSuggestions = true,
} = {}) {
  const wrap = document.createElement('div');
  wrap.className = 'searchbar-wrap';

  const shellW = Math.max(120, width - 44);
  wrap.innerHTML = `
    <div class="searchbar-shell" style="width:${shellW}px">
      <span class="searchbar-ic" style="cursor:pointer;display:inline-flex">${iconSvg('search', 16, 'var(--color-text-muted)')}</span>
      <input type="text" class="searchbar-input" placeholder="${esc(placeholder)}" autocomplete="off" />
    </div>
    <button type="button" class="searchbar-btn" title="ค้นหา">
      ${iconSvg('search', 18, '#111318')}
    </button>
    <div class="searchbar-suggestions hidden"></div>
  `;

  const input = wrap.querySelector('.searchbar-input');
  const btn = wrap.querySelector('.searchbar-btn');
  const ic = wrap.querySelector('.searchbar-ic');
  const popup = wrap.querySelector('.searchbar-suggestions');
  let timer = null;

  const hideSuggestions = () => {
    popup.classList.add('hidden');
    popup.innerHTML = '';
  };

  const submit = () => {
    hideSuggestions();
    if (onSubmit) onSubmit(input.value.trim());
  };

  ic.addEventListener('click', () => input.focus());
  btn.addEventListener('click', submit);

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      submit();
    } else if (e.key === 'Escape') {
      hideSuggestions();
    }
  });

  if (enableSuggestions) {
    input.addEventListener('input', () => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(async () => {
        const q = input.value.trim();
        if (!q) {
          hideSuggestions();
          return;
        }
        try {
          const res = await api.get('/api/products/suggest', { q, limit: 6 });
          const items = Array.isArray(res) ? res : ((res && res.items) || []);
          if (!items.length) {
            hideSuggestions();
            return;
          }
          popup.innerHTML = items.slice(0, 6).map((item, idx) => {
            const brand = item.brand_name ? `[${item.brand_name}] ` : '';
            let label = `${brand}${item.name || ''}`;
            if (label.length > 48) label = label.slice(0, 46) + '…';
            return `
              <button type="button" class="searchbar-suggestion-item" data-idx="${idx}">
                ${iconSvg('racket', 14, 'var(--color-accent)')}
                <span>${esc(label)}</span>
              </button>
            `;
          }).join('');
          popup.classList.remove('hidden');
          popup.querySelectorAll('.searchbar-suggestion-item').forEach((el) => {
            el.addEventListener('mousedown', (ev) => {
              ev.preventDefault();
              const item = items[Number(el.dataset.idx)];
              hideSuggestions();
              if (onSelectSuggestion && item && item.id != null) {
                onSelectSuggestion(item.id, item);
              } else if (item) {
                input.value = item.name || '';
                submit();
              }
            });
          });
        } catch (err) {
          hideSuggestions();
        }
      }, 220);
    });

    input.addEventListener('blur', () => {
      setTimeout(hideSuggestions, 180);
    });
  }

  return {
    el: wrap,
    get: () => input.value.trim(),
    set: (val) => { input.value = val ? String(val) : ''; },
    clear: () => { hideSuggestions(); input.value = ''; },
    focus: () => input.focus(),
    hideSuggestions,
  };
}
