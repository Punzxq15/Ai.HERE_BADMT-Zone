// web/js/pages/admin/categories.js — จัดการหมวดหมู่ / แบรนด์ / ตัวเลือกประจำหมวดหมู่ 3U-10U (ตรงกับ ui/pages/admin/categories.py)
import { api, esc } from '../../api.js';
import { createSegmented, pillHtml, thumbHtml } from '../../components/admin_common.js';
import { confirm, showMessage, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';
import { createImagePicker } from '../../components/image_picker.js';

const TAB_CATEGORY = 'หมวดหมู่สินค้า';
const TAB_BRAND = 'แบรนด์สินค้า';
const TAB_OPTIONS = 'ตัวเลือกของหมวดหมู่ (3U-10U / สปีด / ไซซ์ / สี)';

export async function render(container) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let curTab = TAB_CATEGORY;
  let selectedCatForOptions = null;

  wrap.innerHTML = `
    <div style="margin-bottom:8px">
      <div class="text-h2">หมวดหมู่ / แบรนด์ / ตัวเลือกประจำหมวดหมู่</div>
      <div class="text-small text-muted">จัดการหมวดหมู่ โลโก้แบรนด์ (1:1) และตั้งค่าตัวเลือกประจำหมวดหมู่ (เช่น 3U–10U, ความเร็วลูกแบด, ไซซ์, สี) — เฉพาะเจ้าของร้าน</div>
    </div>
    <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:4px"></div>
    <div data-role="tabs-slot" style="margin-bottom:10px"></div>
    <div data-role="holder"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const holder = wrap.querySelector('[data-role="holder"]');

  const tabs = createSegmented([TAB_CATEGORY, TAB_BRAND, TAB_OPTIONS], curTab, (val) => {
    curTab = val;
    renderCurrentTab();
  });
  wrap.querySelector('[data-role="tabs-slot"]').appendChild(tabs.el);

  async function renderCurrentTab() {
    errEl.textContent = '';
    holder.innerHTML = '';
    let data = {};
    try {
      data = await api.get('/api/admin/categories');
    } catch (err) {
      const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
      return;
    }

    if (curTab === TAB_CATEGORY) {
      renderCategoryTab(data);
    } else if (curTab === TAB_BRAND) {
      renderBrandTab(data);
    } else {
      renderOptionsTab(data);
    }
  }

  function renderCategoryTab(data) {
    let editItem = null;
    const allBrands = data.brands || [];
    const cats = [...(data.categories || []), ...(data.deleted_categories || [])];

    const panel = document.createElement('div');
    panel.innerHTML = `
      <div class="card" style="padding:14px 16px;margin-bottom:10px" data-role="form"></div>
      <div data-role="list" style="display:flex;flex-direction:column;gap:6px"></div>
    `;
    holder.appendChild(panel);

    const formEl = panel.querySelector('[data-role="form"]');
    const listEl = panel.querySelector('[data-role="list"]');

    function buildForm(item = null) {
      editItem = item;
      const bindAllInit = item ? Boolean(item.bind_all_brands ?? 1) : true;
      const selectedIds = new Set((item && item.brand_ids) || []);

      formEl.innerHTML = `
        <div class="text-h3" style="margin-bottom:8px">${item ? `แก้ไขหมวดหมู่: ${esc(item.name)}` : 'เพิ่มหมวดหมู่ใหม่'}</div>
        <div style="display:flex;gap:14px;align-items:flex-start">
          <div data-role="picker"></div>
          <div style="flex:1">
            <div class="text-small text-muted">ชื่อหมวดหมู่ *</div>
            <input type="text" class="input" data-role="name" value="${esc((item && item.name) || '')}" placeholder="เช่น ไม้แบดมินตัน / รองเท้าแบดมินตัน" style="height:34px;margin-bottom:8px" />
            <div class="card-alt" style="padding:8px 12px;margin-bottom:8px">
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:6px" class="text-small-bold">
                <input type="checkbox" data-role="bind-all" ${bindAllInit ? 'checked' : ''} />
                <span>ผูกกับทุกแบรนด์ในร้าน (ค่าเริ่มต้น)</span>
              </label>
              <div data-role="brands-checks" style="display:flex;flex-wrap:wrap;gap:10px">
                ${allBrands.map((b) => `
                  <label style="display:inline-flex;align-items:center;gap:4px;cursor:pointer" class="text-small">
                    <input type="checkbox" data-brand="${b.id}" ${selectedIds.has(b.id) ? 'checked' : ''} ${bindAllInit ? 'disabled' : ''} />
                    <span>${esc(b.name)}</span>
                  </label>
                `).join('')}
              </div>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <button type="button" class="btn btn-primary btn-sm" data-role="save">บันทึกหมวดหมู่</button>
              ${item ? `
                <button type="button" class="btn btn-outline btn-sm" data-role="cancel">ยกเลิกการแก้ไข</button>
                <button type="button" class="btn btn-info btn-sm" data-role="go-opts">⚙️ ตั้งค่าตัวเลือกในหมวดหมู่นี้</button>
              ` : ''}
            </div>
          </div>
        </div>
      `;

      const picker = createImagePicker({ size: [68, 68], initialPath: item ? item.image_path : null, allowClear: false });
      formEl.querySelector('[data-role="picker"]').appendChild(picker.el);
      const bindAllChk = formEl.querySelector('[data-role="bind-all"]');
      bindAllChk.addEventListener('change', () => {
        formEl.querySelectorAll('[data-brand]').forEach((cb) => { cb.disabled = bindAllChk.checked; });
      });

      formEl.querySelector('[data-role="save"]').addEventListener('click', async () => {
        errEl.textContent = '';
        const name = formEl.querySelector('[data-role="name"]').value.trim();
        if (!name) { errEl.textContent = 'กรุณากรอกชื่อหมวดหมู่'; return; }
        const bindAll = bindAllChk.checked;
        const brandIds = Array.from(formEl.querySelectorAll('[data-brand]:checked')).map((el) => Number(el.dataset.brand));
        if (!bindAll && !brandIds.length) {
          errEl.textContent = "กรุณาเลือกอย่างน้อย 1 แบรนด์ หรือเปิดสวิตช์ 'ผูกกับทุกแบรนด์ในร้าน'";
          return;
        }
        try {
          let imagePath = item ? item.image_path : null;
          if (picker.hasChange() && picker.getSelectedFile()) {
            imagePath = await picker.resolveUploadedPath('category');
          }
          const payload = { name, image_path: imagePath, bind_all_brands: bindAll, brand_ids: brandIds };
          if (editItem) await api.put(`/api/admin/categories/${editItem.id}`, payload);
          else await api.post('/api/admin/categories', payload);
          await renderCurrentTab();
        } catch (err) {
          const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
        }
      });

      const cancelBtn = formEl.querySelector('[data-role="cancel"]');
      if (cancelBtn) cancelBtn.addEventListener('click', () => buildForm(null));
      const goOpts = formEl.querySelector('[data-role="go-opts"]');
      if (goOpts) {
        goOpts.addEventListener('click', () => {
          selectedCatForOptions = item.id;
          curTab = TAB_OPTIONS;
          tabs.set(TAB_OPTIONS);
          renderCurrentTab();
        });
      }
    }

    buildForm(null);

    const seenIds = new Set();
    for (const item of cats) {
      if (seenIds.has(item.id)) continue;
      seenIds.add(item.id);
      const deleted = Boolean(item.deleted_at);
      const active = Boolean(item.is_active ?? 1) && !deleted;
      const bindTxt = item.bind_all_brands !== false && item.bind_all_brands !== 0
        ? 'ผูกทุกแบรนด์'
        : `ผูกเฉพาะ ${(item.brand_ids || []).length} แบรนด์`;
      const prodCnt = Number(item.product_count ?? item.active_product_count ?? 0);

      const r = document.createElement('div');
      r.className = 'card';
      r.style.padding = '8px 12px';
      r.style.display = 'flex';
      r.style.alignItems = 'center';
      r.style.gap = '10px';
      r.innerHTML = `
        ${thumbHtml(item.image_path, 38)}
        <div style="flex:1">
          <div class="text-body-bold">${esc(item.name)}</div>
          <div class="text-tiny text-muted">${esc(bindTxt)} · สินค้าในหมวด ${prodCnt} รายการ</div>
        </div>
        ${deleted ? `
          ${pillHtml('ถูกลบ (เก็บประวัติ)', 'danger')}
          <button type="button" class="btn btn-success btn-sm" data-role="restore">กู้คืน</button>
        ` : `
          ${pillHtml(active ? 'เปิดใช้งาน' : 'ปิดอยู่', active ? 'success' : 'muted')}
          <button type="button" class="btn btn-info btn-sm" data-role="opts">ตั้งค่าตัวเลือก</button>
          <button type="button" class="btn btn-outline btn-sm" data-role="edit">แก้ไข</button>
          <button type="button" class="btn ${active ? 'btn-outline' : 'btn-success'} btn-sm" data-role="tog">${active ? 'ปิด' : 'เปิด'}</button>
          <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
        `}
      `;
      if (deleted) {
        r.querySelector('[data-role="restore"]').addEventListener('click', async () => {
          await api.post(`/api/admin/categories/${item.id}/restore`);
          await renderCurrentTab();
        });
      } else {
        r.querySelector('[data-role="opts"]').addEventListener('click', () => {
          selectedCatForOptions = item.id;
          curTab = TAB_OPTIONS;
          tabs.set(TAB_OPTIONS);
          renderCurrentTab();
        });
        r.querySelector('[data-role="edit"]').addEventListener('click', () => buildForm(item));
        r.querySelector('[data-role="tog"]').addEventListener('click', async () => {
          await api.post(`/api/admin/categories/${item.id}/active`, { active: !active });
          await renderCurrentTab();
        });
        r.querySelector('[data-role="del"]').addEventListener('click', async () => {
          let msg = `ต้องการลบหมวดหมู่ “${item.name}” ใช่หรือไม่?`;
          if (prodCnt > 0) msg += `

มีสินค้าที่เปิดขายอยู่ในหมวดหมู่นี้ ${prodCnt} รายการ หากยืนยัน ระบบจะปิดการแสดงผลสินค้าเหล่านั้นอย่างปลอดภัยโดยไม่ลบประวัติออเดอร์`;
          const ok = await confirm('ยืนยันการลบหมวดหมู่', msg, { confirmText: 'ยืนยันลบ', danger: true });
          if (!ok) return;
          await api.del(`/api/admin/categories/${item.id}?cascade=true`);
          await renderCurrentTab();
        });
      }
      listEl.appendChild(r);
    }
  }

  function renderBrandTab(data) {
    let editItem = null;
    const brands = [...(data.brands || []), ...(data.deleted_brands || [])];

    const panel = document.createElement('div');
    panel.innerHTML = `
      <div class="card" style="padding:14px 16px;margin-bottom:10px" data-role="form"></div>
      <div data-role="list" style="display:flex;flex-direction:column;gap:6px"></div>
    `;
    holder.appendChild(panel);

    const formEl = panel.querySelector('[data-role="form"]');
    const listEl = panel.querySelector('[data-role="list"]');

    function buildForm(item = null) {
      editItem = item;
      formEl.innerHTML = `
        <div class="text-h3" style="margin-bottom:8px">${item ? `แก้ไขแบรนด์: ${esc(item.name)} (โลโก้ 1:1)` : 'เพิ่มแบรนด์ใหม่ (โลโก้แบรนด์อัตราส่วน 1:1)'}</div>
        <div style="display:flex;gap:14px;align-items:flex-start">
          <div data-role="picker"></div>
          <div style="flex:1">
            <div class="text-small text-muted">ชื่อแบรนด์ * (อัปโหลดรูปโลโก้แบรนด์อัตราส่วน 1:1 ด้านซ้าย)</div>
            <input type="text" class="input" data-role="name" value="${esc((item && item.name) || '')}" placeholder="เช่น Yonex / Victor / Li-Ning" style="height:34px;margin-bottom:8px" />
            <div style="display:flex;gap:6px">
              <button type="button" class="btn btn-primary btn-sm" data-role="save">บันทึกแบรนด์</button>
              ${item ? `<button type="button" class="btn btn-outline btn-sm" data-role="cancel">ยกเลิกการแก้ไข</button>` : ''}
            </div>
          </div>
        </div>
      `;
      const picker = createImagePicker({ size: [68, 68], initialPath: item ? item.logo_path : null, allowClear: false });
      formEl.querySelector('[data-role="picker"]').appendChild(picker.el);
      formEl.querySelector('[data-role="save"]').addEventListener('click', async () => {
        errEl.textContent = '';
        const name = formEl.querySelector('[data-role="name"]').value.trim();
        if (!name) { errEl.textContent = 'กรุณากรอกชื่อแบรนด์'; return; }
        try {
          let logoPath = item ? item.logo_path : null;
          if (picker.hasChange() && picker.getSelectedFile()) {
            logoPath = await picker.resolveUploadedPath('brand');
          }
          const payload = { name, logo_path: logoPath };
          if (editItem) await api.put(`/api/admin/brands/${editItem.id}`, payload);
          else await api.post('/api/admin/brands', payload);
          await renderCurrentTab();
        } catch (err) {
          const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
        }
      });
      const cancelBtn = formEl.querySelector('[data-role="cancel"]');
      if (cancelBtn) cancelBtn.addEventListener('click', () => buildForm(null));
    }

    buildForm(null);

    const seenIds = new Set();
    for (const item of brands) {
      if (seenIds.has(item.id)) continue;
      seenIds.add(item.id);
      const deleted = Boolean(item.deleted_at);
      const active = Boolean(item.is_active ?? 1) && !deleted;
      const prodCnt = Number(item.product_count ?? item.active_product_count ?? 0);

      const r = document.createElement('div');
      r.className = 'card';
      r.style.padding = '8px 12px';
      r.style.display = 'flex';
      r.style.alignItems = 'center';
      r.style.gap = '10px';
      r.innerHTML = `
        ${thumbHtml(item.logo_path, 38)}
        <div style="flex:1">
          <div class="text-body-bold">${esc(item.name)}</div>
          <div class="text-tiny text-muted">โลโก้ 1:1 · สินค้าในแบรนด์ ${prodCnt} รายการ</div>
        </div>
        ${deleted ? `
          ${pillHtml('ถูกลบ (เก็บประวัติ)', 'danger')}
          <button type="button" class="btn btn-success btn-sm" data-role="restore">กู้คืน</button>
        ` : `
          ${pillHtml(active ? 'เปิดใช้งาน' : 'ปิดอยู่', active ? 'success' : 'muted')}
          <button type="button" class="btn btn-outline btn-sm" data-role="edit">แก้ไข</button>
          <button type="button" class="btn ${active ? 'btn-outline' : 'btn-success'} btn-sm" data-role="tog">${active ? 'ปิด' : 'เปิด'}</button>
          <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
        `}
      `;
      if (deleted) {
        r.querySelector('[data-role="restore"]').addEventListener('click', async () => {
          await api.post(`/api/admin/brands/${item.id}/restore`);
          await renderCurrentTab();
        });
      } else {
        r.querySelector('[data-role="edit"]').addEventListener('click', () => buildForm(item));
        r.querySelector('[data-role="tog"]').addEventListener('click', async () => {
          await api.post(`/api/admin/brands/${item.id}/active`, { active: !active });
          await renderCurrentTab();
        });
        r.querySelector('[data-role="del"]').addEventListener('click', async () => {
          let msg = `ต้องการลบแบรนด์ “${item.name}” ใช่หรือไม่?`;
          if (prodCnt > 0) msg += `

มีสินค้าที่เปิดขายอยู่ในแบรนด์นี้ ${prodCnt} รายการ หากยืนยัน ระบบจะปิดการแสดงผลสินค้าเหล่านั้นอย่างปลอดภัยโดยไม่ลบประวัติออเดอร์`;
          const ok = await confirm('ยืนยันการลบแบรนด์', msg, { confirmText: 'ยืนยันลบ', danger: true });
          if (!ok) return;
          await api.del(`/api/admin/brands/${item.id}?cascade=true`);
          await renderCurrentTab();
        });
      }
      listEl.appendChild(r);
    }
  }

  async function renderOptionsTab(data) {
    const cats = (data.categories || []).filter((c) => !c.deleted_at);
    if (!selectedCatForOptions && cats.length) {
      const racketCat = cats.find((c) => String(c.name || '').includes('ไม้แบด')) || cats[0];
      selectedCatForOptions = racketCat.id;
    }
    const curCat = cats.find((c) => c.id === selectedCatForOptions);
    const isRacketCat = curCat && String(curCat.name || '').includes('ไม้แบด');

    const panel = document.createElement('div');
    panel.innerHTML = `
      <div class="card" style="padding:12px 14px;margin-bottom:10px">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px">
          <span class="text-body-bold">เลือกหมวดหมู่ที่ต้องการตั้งค่าตัวเลือก:</span>
          <select class="select" data-role="cat-sel" style="width:220px;height:36px">
            ${cats.map((c) => `<option value="${c.id}" ${c.id === selectedCatForOptions ? 'selected' : ''}>${esc(c.name)}</option>`).join('')}
          </select>
          ${isRacketCat ? `<button type="button" class="btn btn-primary btn-sm" data-role="quick-3u">⚡ เพิ่มน้ำหนักไม้ 3U–10U ครบชุด</button>` : ''}
        </div>
        <div class="card-alt" style="padding:8px 10px;display:flex;align-items:center;gap:6px;flex-wrap:wrap">
          <span class="text-small-bold">เพิ่มหัวข้อตัวเลือกใหม่ในหมวดนี้:</span>
          <input type="text" class="input" data-role="grp-key" placeholder="รหัส เช่น weight_class / size / color / speed" style="width:220px;height:32px" />
          <input type="text" class="input" data-role="grp-lbl" placeholder="ชื่อหัวข้อ เช่น น้ำหนักไม้ / ขนาดไซซ์ / สี" style="width:240px;height:32px" />
          <button type="button" class="btn btn-info btn-sm" data-role="add-grp">＋ เพิ่มชุดตัวเลือก</button>
        </div>
      </div>
      <div data-role="groups-list" style="display:flex;flex-direction:column;gap:8px"></div>
    `;
    holder.appendChild(panel);

    panel.querySelector('[data-role="cat-sel"]').addEventListener('change', (e) => {
      selectedCatForOptions = Number(e.target.value);
      renderCurrentTab();
    });

    const qBtn = panel.querySelector('[data-role="quick-3u"]');
    if (qBtn) {
      qBtn.addEventListener('click', async () => {
        try {
          await api.post(`/api/admin/categories/${selectedCatForOptions}/quick-weights`);
          await showMessage('เพิ่มน้ำหนักไม้สำเร็จ', 'เพิ่มตัวเลือกน้ำหนักไม้ 3U, 4U, 5U, 6U, 7U, 8U, 9U, 10U เข้าหมวดหมู่เรียบร้อยแล้ว', 'success');
          await renderCurrentTab();
        } catch (err) {
          const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
        }
      });
    }

    panel.querySelector('[data-role="add-grp"]').addEventListener('click', async () => {
      errEl.textContent = '';
      try {
        await api.post('/api/admin/option-groups', {
          category_id: selectedCatForOptions,
          key: panel.querySelector('[data-role="grp-key"]').value.trim(),
          label: panel.querySelector('[data-role="grp-lbl"]').value.trim(),
        });
        await renderCurrentTab();
      } catch (err) {
        const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
      }
    });

    const groupsList = panel.querySelector('[data-role="groups-list"]');
    let groups = [];
    try {
      groups = await api.get('/api/admin/option-groups', { category_id: selectedCatForOptions });
    } catch (e) {}

    if (!groups.length) {
      groupsList.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">หมวดหมู่นี้ยังไม่มีชุดตัวเลือก — สามารถเพิ่มชุดตัวเลือกด้านบนได้เลย</div>`;
      return;
    }

    for (const g of groups) {
      const gActive = Boolean(g.is_active ?? 1);
      const vals = g.values || [];
      const gCard = document.createElement('div');
      gCard.className = 'card';
      gCard.style.padding = '12px 14px';
      gCard.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <div style="display:flex;align-items:center;gap:8px">
            <span class="text-h3">${esc(g.label)}  (key: ${esc(g.key)})</span>
            ${pillHtml(gActive ? 'เปิดใช้งาน' : 'ปิดใช้งาน', gActive ? 'success' : 'muted')}
          </div>
          <button type="button" class="btn ${gActive ? 'btn-outline' : 'btn-success'} btn-sm" data-role="tog-grp">${gActive ? 'ปิดชุดนี้' : 'เปิดชุดนี้'}</button>
        </div>
        <div class="card-alt" data-role="vals-wrap" style="padding:8px 10px;display:flex;flex-direction:column;gap:4px;margin-bottom:8px"></div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <input type="text" class="input" data-role="v-in" placeholder="ค่าตัวเลือก เช่น 5U / 6U / Head Heavy / Medium-Stiff / 75 / XL" style="width:270px;height:32px" />
          <input type="text" class="input" data-role="l-in" placeholder="คำอธิบายแสดงผล (เว้นว่าง = ใช้ค่าเดียวกัน)" style="width:240px;height:32px" />
          <button type="button" class="btn btn-primary btn-sm" data-role="add-val">＋ เพิ่มค่าตัวเลือก</button>
        </div>
      `;

      gCard.querySelector('[data-role="tog-grp"]').addEventListener('click', async () => {
        await api.post(`/api/admin/option-groups/${g.id}/toggle`);
        await renderCurrentTab();
      });

      const valsWrap = gCard.querySelector('[data-role="vals-wrap"]');
      if (!vals.length) {
        valsWrap.innerHTML = `<div class="text-small text-muted">ยังไม่มีค่าตัวเลือกในหมวดนี้</div>`;
      } else {
        vals.forEach((v, idx) => {
          const vAct = Boolean(v.is_active ?? 1);
          const vr = document.createElement('div');
          vr.style.display = 'flex';
          vr.style.alignItems = 'center';
          vr.style.gap = '8px';
          vr.innerHTML = `
            ${pillHtml(v.value || '-', vAct ? 'primary' : 'muted')}
            <span class="${vAct ? 'text-body-bold' : 'text-body text-muted'}" style="flex:1">${esc(v.label || v.value || '-')}</span>
            ${idx > 0 ? `<button type="button" class="btn btn-outline btn-sm" data-role="up" style="width:32px;padding:0">↑</button>` : ''}
            ${idx < vals.length - 1 ? `<button type="button" class="btn btn-outline btn-sm" data-role="down" style="width:32px;padding:0">↓</button>` : ''}
            <button type="button" class="btn ${vAct ? 'btn-danger' : 'btn-success'} btn-sm" data-role="tog-val">${vAct ? 'ปิดใช้' : 'เปิดใช้'}</button>
          `;
          const move = async (delta) => {
            const ids = vals.map((x) => x.id);
            const ni = idx + delta;
            [ids[idx], ids[ni]] = [ids[ni], ids[idx]];
            await api.post(`/api/admin/option-groups/${g.id}/reorder`, { value_ids: ids });
            await renderCurrentTab();
          };
          const upBtn = vr.querySelector('[data-role="up"]');
          if (upBtn) upBtn.addEventListener('click', () => move(-1));
          const downBtn = vr.querySelector('[data-role="down"]');
          if (downBtn) downBtn.addEventListener('click', () => move(1));
          vr.querySelector('[data-role="tog-val"]').addEventListener('click', async () => {
            await api.post(`/api/admin/option-values/${v.id}/toggle`);
            await renderCurrentTab();
          });
          valsWrap.appendChild(vr);
        });
      }

      const addVal = async () => {
        errEl.textContent = '';
        try {
          await api.post('/api/admin/option-values', {
            group_id: g.id,
            value: gCard.querySelector('[data-role="v-in"]').value.trim(),
            label: gCard.querySelector('[data-role="l-in"]').value.trim() || null,
          });
          await renderCurrentTab();
        } catch (err) {
          const _em = err.message || 'ดำเนินการไม่สำเร็จ'; errEl.textContent = `⛔ ${_em}`; showToast(_em, 'error');
        }
      };
      gCard.querySelector('[data-role="add-val"]').addEventListener('click', addVal);
      gCard.querySelector('[data-role="v-in"]').addEventListener('keydown', (e) => { if (e.key === 'Enter') addVal(); });
      groupsList.appendChild(gCard);
    }
  }

  await renderCurrentTab();
}
