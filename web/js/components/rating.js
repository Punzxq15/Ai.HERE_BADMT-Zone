// web/js/components/rating.js — แสดง/เลือกดาวรีวิว (1–5) ตรงกับ ui/components/rating.py
import { esc } from '../api.js';

export function createRatingStars({
  value = 0,
  count = null,
  size = 16,
  interactive = false,
  showValue = true,
  onChange = null,
} = {}) {
  const wrap = document.createElement('div');
  wrap.style.display = 'inline-flex';
  wrap.style.alignItems = 'center';
  wrap.style.gap = '2px';

  let curVal = Math.max(0, Math.min(5, Number(value || 0)));
  let curCount = count;
  let hoverVal = 0;

  const stars = [];
  for (let i = 1; i <= 5; i++) {
    const sp = document.createElement('span');
    sp.textContent = '★';
    sp.style.fontFamily = "'Arimo', sans-serif";
    sp.style.fontSize = `${size}px`;
    sp.style.lineHeight = '1';
    sp.style.userSelect = 'none';
    if (interactive) {
      sp.style.cursor = 'pointer';
      sp.addEventListener('mouseenter', () => { hoverVal = i; paint(); });
      sp.addEventListener('mouseleave', () => { hoverVal = 0; paint(); });
      sp.addEventListener('click', (e) => {
        e.stopPropagation();
        curVal = i;
        hoverVal = 0;
        paint();
        if (onChange) onChange(i);
      });
    }
    stars.push(sp);
    wrap.appendChild(sp);
  }

  const textEl = document.createElement('span');
  textEl.className = 'text-small text-muted';
  textEl.style.marginLeft = '6px';
  wrap.appendChild(textEl);

  function paint() {
    const filled = hoverVal ? hoverVal : Math.round(curVal);
    stars.forEach((s, idx) => {
      s.style.color = idx < filled ? 'var(--color-star)' : 'var(--color-star-off)';
    });
    const parts = [];
    if (showValue && !interactive) {
      parts.push(curVal ? curVal.toFixed(1) : 'ยังไม่มีคะแนน');
    }
    if (curCount !== null && curCount !== undefined && !interactive) {
      parts.push(`(${curCount})`);
    }
    textEl.textContent = parts.join(' ');
    textEl.style.display = parts.length ? 'inline' : 'none';
  }

  paint();

  return {
    el: wrap,
    set(val, cnt = undefined) {
      curVal = Math.max(0, Math.min(5, Number(val || 0)));
      if (cnt !== undefined) curCount = cnt;
      paint();
    },
    get() {
      return Math.round(curVal);
    },
  };
}
