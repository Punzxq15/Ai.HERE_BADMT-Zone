// web/js/pages/buyer/racket_finder.js — ตัวช่วยเลือกไม้แบดมินตัน (ตรงกับ ui/pages/buyer/racket_finder.py)
import { api, esc, LEVELS } from '../../api.js';
import { createProductCard } from '../../components/product_card.js';
import { pageTitleHtml, toggleWishlist } from '../../components/buyer_common.js';
import { showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';

const LEVEL_LABELS = {
  Beginner: 'มือใหม่',
  Intermediate: 'ปานกลาง',
  Advanced: 'ฝีมือดี',
  Professional: 'มืออาชีพ',
};

const STYLES = [
  ['attack',  'สายบุก (ตบหนัก)',      'เน้นตบหนัก ทำแต้มเร็ว → ไม้หัวหนัก ก้านแข็ง'],
  ['control', 'สายคอนโทรล (แม่นยำ)',   'วางลูกแม่น คุมจังหวะเกม → ไม้สมดุล ก้านกลาง'],
  ['speed',   'สายสปีด (หน้าเน็ตไว)', 'ตอบโต้ไว เปลี่ยนจังหวะเร็ว → ไม้หัวเบา ก้านยืดหยุ่น'],
];

const MAX_SCORE = 8;

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  let selectedLevel = null;
  let selectedStyle = null;

  wrap.innerHTML = `
    ${pageTitleHtml('🎯 ตัวช่วยเลือกไม้', 'ตอบ 3 ข้อสั้น ๆ แล้วเราจะแนะนำไม้ที่เหมาะกับคุณ')}
    <div class="card" style="padding:18px 20px;margin-bottom:14px">
      <div class="text-body-bold" style="margin-bottom:6px">1. ระดับฝีมือของคุณ</div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px" data-role="level-row">
        ${LEVELS.map((lv) => `<button type="button" class="btn btn-outline btn-md" data-level="${esc(lv)}" style="min-width:110px">${esc(LEVEL_LABELS[lv] || lv)}</button>`).join('')}
      </div>

      <div class="text-body-bold" style="margin-bottom:6px">2. สไตล์การเล่น</div>
      <div style="display:flex;flex-wrap:wrap;gap:8px" data-role="style-row">
        ${STYLES.map(([k, lbl]) => `<button type="button" class="btn btn-outline btn-md" data-style="${esc(k)}">${esc(lbl)}</button>`).join('')}
      </div>
      <div class="text-small text-muted" data-role="style-hint" style="min-height:18px;margin-top:4px;margin-bottom:12px"></div>

      <div class="text-body-bold" style="margin-bottom:6px">3. งบประมาณต่อไม้ (บาท — เว้นว่างได้ถ้าไม่จำกัด)</div>
      <input type="text" class="input" data-role="budget" placeholder="เช่น 3000" style="width:200px;height:40px;margin-bottom:18px" />

      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <button type="button" class="btn btn-primary btn-lg" data-role="find-btn">ค้นหาไม้ที่เหมาะกับฉัน</button>
        <button type="button" class="btn btn-outline btn-lg" data-role="reset-btn">ล้างคำตอบ</button>
        <span class="text-small text-danger" data-role="err"></span>
      </div>
    </div>

    <div class="text-h3" data-role="result-title" style="margin-bottom:8px"></div>
    <div class="wrap-grid" data-role="result-grid"></div>
    <div class="text-body text-muted" data-role="empty" style="text-align:center;padding:12px 0"></div>
  `;

  const styleHint = wrap.querySelector('[data-role="style-hint"]');
  const budgetIn = wrap.querySelector('[data-role="budget"]');
  const errEl = wrap.querySelector('[data-role="err"]');
  const resTitle = wrap.querySelector('[data-role="result-title"]');
  const resGrid = wrap.querySelector('[data-role="result-grid"]');
  const emptyEl = wrap.querySelector('[data-role="empty"]');

  function paintChoices() {
    wrap.querySelectorAll('[data-level]').forEach((b) => {
      b.className = `btn btn-md ${b.dataset.level === selectedLevel ? 'btn-primary' : 'btn-outline'}`;
    });
    wrap.querySelectorAll('[data-style]').forEach((b) => {
      b.className = `btn btn-md ${b.dataset.style === selectedStyle ? 'btn-primary' : 'btn-outline'}`;
    });
    const stObj = STYLES.find(([k]) => k === selectedStyle);
    styleHint.textContent = stObj ? stObj[2] : '';
  }

  wrap.querySelectorAll('[data-level]').forEach((b) => {
    b.addEventListener('click', () => { selectedLevel = b.dataset.level; paintChoices(); });
  });
  wrap.querySelectorAll('[data-style]').forEach((b) => {
    b.addEventListener('click', () => { selectedStyle = b.dataset.style; paintChoices(); });
  });

  async function doRecommend() {
    errEl.textContent = '';
    const budget = budgetIn.value.trim().replace(/,/g, '') || undefined;
    try {
      const rackets = await api.get('/api/products/recommend', {
        level: selectedLevel || '',
        style: selectedStyle || '',
        budget,
      });
      resGrid.innerHTML = '';
      if (!rackets || !rackets.length) {
        resTitle.textContent = '';
        emptyEl.textContent = 'ไม่พบไม้ที่ตรงกับเงื่อนไข ลองเพิ่มงบหรือเปลี่ยนสไตล์การเล่นดูนะครับ';
        return;
      }
      emptyEl.textContent = '';
      resTitle.textContent = `ไม้ที่แนะนำสำหรับคุณ (${rackets.length} รุ่น)`;
      for (const racket of rackets) {
        const box = document.createElement('div');
        box.style.display = 'flex';
        box.style.flexDirection = 'column';
        box.style.alignItems = 'center';
        const card = createProductCard(racket, {
          onOpen: (pid) => router.show('product_detail', { product_id: pid }),
          onWishlist: (pid) => toggleWishlist(pid),
        });
        box.appendChild(card);
        const badge = document.createElement('span');
        badge.className = 'pill pill-success';
        badge.style.margin = '6px 0 4px';
        badge.textContent = `เหมาะสม ${racket.match_score}/${MAX_SCORE}`;
        box.appendChild(badge);
        for (const reason of racket.match_reasons || []) {
          const r = document.createElement('div');
          r.className = 'text-small text-muted';
          r.style.width = '210px';
          r.textContent = `✓ ${reason}`;
          box.appendChild(r);
        }
        resGrid.appendChild(box);
      }
    } catch (err) {
      const _em = err.message || 'ค้นหาไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; setFieldError(budgetIn, _em); showToast(_em, 'error');
    }
  }

  wrap.querySelector('[data-role="find-btn"]').addEventListener('click', doRecommend);
  budgetIn.addEventListener('keydown', (e) => { if (e.key === 'Enter') doRecommend(); });
  wrap.querySelector('[data-role="reset-btn"]').addEventListener('click', () => {
    selectedLevel = null;
    selectedStyle = null;
    paintChoices();
    budgetIn.value = '';
    errEl.textContent = '';
    resTitle.textContent = '';
    emptyEl.textContent = '';
    resGrid.innerHTML = '';
  });
}
