// web/js/pages/admin/products.js — จัดการสินค้า · Flash Sale (พร้อมปฏิทินและตารางเวลา) · แบนเนอร์หน้าร้าน + ถังขยะกู้คืน
import { api, esc, formatDateTime, formatPrice } from '../../api.js';
import { state } from '../../state.js';
import { createPager, createSegmented, parseMoney, pillHtml, thumbHtml } from '../../components/admin_common.js';
import { confirm, openModal, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';
import { createDateTimePickerField } from '../../components/date_picker.js';
import { createImagePicker } from '../../components/image_picker.js';
import { createSearchBar } from '../../components/search_bar.js';

const PAGE_SIZE = 20;
const TAB_ACTIVE = 'สินค้าในระบบ';
const TAB_DELETED = 'สินค้าที่ถูกลบ (ประวัติยอดขาย & กู้คืน)';

function formatIsoLocal(dt) {
  const y = dt.getFullYear();
  const m = String(dt.getMonth() + 1).padStart(2, '0');
  const d = String(dt.getDate()).padStart(2, '0');
  const hh = String(dt.getHours()).padStart(2, '0');
  const mm = String(dt.getMinutes()).padStart(2, '0');
  const ss = String(dt.getSeconds()).padStart(2, '0');
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`;
}

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let mode = TAB_ACTIVE;
  let page = 1;
  let search = '';
  let catId = '';
  let brandId = '';
  let statusFilter = 'all';
  let sort = 'newest';
  let threshold = 5;

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:8px">
      <div>
        <div class="text-h2">จัดการสินค้า · Flash Sale · แบนเนอร์หน้าร้าน</div>
        <div class="text-small text-muted">จัดการสินค้า สต็อก แบนเนอร์ 1–10 รูป และตั้งเวลา Flash Sale จากปฏิทิน/ตารางเวลา (เฉพาะ Owner)</div>
      </div>
      <div style="display:flex;gap:6px">
        <button type="button" class="btn btn-info btn-md" data-role="banner-mgr">จัดการแบนเนอร์ (1-10 รูป)</button>
        <button type="button" class="btn btn-primary btn-md" data-role="add-prod">＋ เพิ่มสินค้าใหม่</button>
      </div>
    </div>

    <div class="text-small text-danger" data-role="err" style="margin-bottom:4px"></div>
    <div data-role="mode-slot" style="margin-bottom:8px"></div>

    <div data-role="filter-bar" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px">
      <div data-role="search-slot"></div>
      <select class="select" data-role="cat" style="width:150px;height:36px"><option value="">ทุกหมวดหมู่</option></select>
      <select class="select" data-role="brand" style="width:140px;height:36px"><option value="">ทุกแบรนด์</option></select>
      <select class="select" data-role="status" style="width:165px;height:36px">
        <option value="all">ทุกสถานะ</option>
        <option value="active">เฉพาะที่ขายอยู่</option>
        <option value="flash">เฉพาะสินค้า Flash Sale</option>
      </select>
      <select class="select" data-role="sort" style="width:140px;height:36px">
        <option value="newest">ใหม่ล่าสุด</option>
        <option value="price_asc">ราคา ต่ำ → สูง</option>
        <option value="price_desc">ราคา สูง → ต่ำ</option>
        <option value="name">ชื่อ A → Z</option>
        <option value="popular">ขายดี</option>
      </select>
    </div>

    <div data-role="table-head"></div>
    <div data-role="list"></div>
    <div data-role="pager-slot"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const filterBar = wrap.querySelector('[data-role="filter-bar"]');
  const catSel = wrap.querySelector('[data-role="cat"]');
  const brandSel = wrap.querySelector('[data-role="brand"]');
  const statusSel = wrap.querySelector('[data-role="status"]');
  const sortSel = wrap.querySelector('[data-role="sort"]');
  const tableHead = wrap.querySelector('[data-role="table-head"]');
  const listEl = wrap.querySelector('[data-role="list"]');
  const pagerSlot = wrap.querySelector('[data-role="pager-slot"]');

  const modeSeg = createSegmented([TAB_ACTIVE, TAB_DELETED], mode, (val) => {
    mode = val;
    page = 1;
    load();
  });
  wrap.querySelector('[data-role="mode-slot"]').appendChild(modeSeg.el);

  const searchBar = createSearchBar({
    placeholder: 'ค้นหาชื่อสินค้า/แบรนด์',
    width: 250,
    enableSuggestions: false,
    onSubmit(q) {
      search = q;
      page = 1;
      load();
    },
  });
  wrap.querySelector('[data-role="search-slot"]').appendChild(searchBar.el);

  const pager = createPager((p) => { page = p; load(); });
  pagerSlot.appendChild(pager.el);

  wrap.querySelector('[data-role="add-prod"]').addEventListener('click', () => router.show('admin_product_form'));
  wrap.querySelector('[data-role="banner-mgr"]').addEventListener('click', () => openBannerManagerModal());

  [catSel, brandSel, statusSel, sortSel].forEach((el) => {
    el.addEventListener('change', () => {
      catId = catSel.value;
      brandId = brandSel.value;
      statusFilter = statusSel.value;
      sort = sortSel.value;
      page = 1;
      load();
    });
  });

  // Load categories & brands
  try {
    const meta = await api.get('/api/admin/categories');
    for (const c of meta.categories || []) {
      const opt = document.createElement('option');
      opt.value = String(c.id);
      opt.textContent = c.name;
      catSel.appendChild(opt);
    }
    for (const b of meta.brands || []) {
      const opt = document.createElement('option');
      opt.value = String(b.id);
      opt.textContent = b.name;
      brandSel.appendChild(opt);
    }
  } catch (e) {}

  async function load() {
    errEl.textContent = '';
    tableHead.innerHTML = '';
    listEl.innerHTML = '';

    if (mode === TAB_DELETED) {
      filterBar.classList.add('hidden');
      pagerSlot.classList.add('hidden');
      const gridSpec = '56px 2fr 1.2fr 1fr 1.3fr 1.2fr 130px';
      tableHead.innerHTML = `
        <div class="admin-table-header" style="grid-template-columns:${gridSpec}">
          <span></span><span>สินค้าที่ถูกลบ</span><span>หมวด / แบรนด์</span><span>ราคา</span><span>ยอดขายสะสม</span><span>ลบเมื่อ</span><span>จัดการ</span>
        </div>
      `;
      try {
        const rows = await api.get('/api/admin/products/deleted', { search: search || undefined });
        if (!rows || !rows.length) {
          listEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">ยังไม่มีสินค้าในถังขยะ</div>`;
          return;
        }
        for (const p of rows) {
          const r = document.createElement('div');
          r.className = 'admin-table-row';
          r.style.gridTemplateColumns = gridSpec;
          r.innerHTML = `
            ${thumbHtml(p.image_path, 44)}
            <div>
              <div class="text-body-bold">${esc(p.name || '-')}</div>
              <div class="text-tiny text-muted">รหัส #${p.id}</div>
            </div>
            <div class="text-small text-muted" style="white-space:pre-line">${esc(p.category_name || '-')}
${esc(p.brand_name || '-')}</div>
            <div class="text-body-bold">${esc(formatPrice(p.price))}</div>
            <div class="text-small" style="white-space:pre-line">ขายแล้ว ${Number(p.total_sold_qty || 0).toLocaleString()} ชิ้น
รวม ${esc(formatPrice(p.total_sold_revenue || 0))}</div>
            <div class="text-tiny text-muted">${esc(formatDateTime(p.deleted_at))}</div>
            <div style="display:flex;justify-content:flex-end">
              ${state.is_owner ? `<button type="button" class="btn btn-success btn-sm" data-role="restore">กู้คืนสินค้า</button>` : ''}
            </div>
          `;
          const restBtn = r.querySelector('[data-role="restore"]');
          if (restBtn) {
            restBtn.addEventListener('click', async () => {
              try {
                await api.post(`/api/admin/products/${p.id}/restore`);
                showToast(`กู้คืนสินค้า “${p.name}” กลับมาเปิดขายเรียบร้อยแล้ว`, 'success');
                await load();
              } catch (err) {
                const em = err.message || 'กู้คืนสินค้าไม่สำเร็จ';
                errEl.textContent = `⛔ ${em}`;
                showToast(em, 'error');
              }
            });
          }
          listEl.appendChild(r);
        }
      } catch (err) {
        const em = err.message || 'โหลดรายการสินค้าที่ถูกลบไม่สำเร็จ';
        errEl.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
      return;
    }

    filterBar.classList.remove('hidden');
    pagerSlot.classList.remove('hidden');
    const gridSpec = '56px 2.2fr 1.2fr 1fr 70px 90px 290px';
    tableHead.innerHTML = `
      <div class="admin-table-header" style="grid-template-columns:${gridSpec}">
        <span></span><span>สินค้า</span><span>หมวด / แบรนด์</span><span>ราคา</span><span>สต็อก</span><span>สถานะ</span><span>จัดการ</span>
      </div>
    `;

    try {
      const res = await api.get('/api/admin/products', {
        search: search || undefined,
        category_id: catId || undefined,
        brand_id: brandId || undefined,
        on_sale: statusFilter === 'flash' ? 'true' : undefined,
        show_inactive: statusFilter !== 'active',
        sort,
        page,
        page_size: PAGE_SIZE,
      });
      threshold = Number(res.low_stock_threshold ?? 5);
      const items = res.items || [];
      if (!items.length) {
        listEl.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:30px">ไม่พบสินค้าตามเงื่อนไขที่เลือก</div>`;
      }
      for (const p of items) {
        const stock = Number(p.stock || 0);
        const low = stock <= threshold;
        const active = Boolean(p.is_active ?? 1);
        const onSale = Boolean(p.is_on_sale);

        const r = document.createElement('div');
        r.className = 'admin-table-row';
        r.style.gridTemplateColumns = gridSpec;
        r.innerHTML = `
          ${thumbHtml(p.image_path, 44)}
          <div>
            <div class="text-body-bold">${esc(p.name || '-')}</div>
            <div class="text-tiny text-muted">รหัส #${p.id}</div>
          </div>
          <div class="text-small text-muted" style="white-space:pre-line">${esc(p.category_name || '-')}
${esc(p.brand_name || '-')}</div>
          <div>
            <div class="text-body-bold">${esc(formatPrice(p.effective_price ?? p.price))}</div>
            ${onSale ? `<div class="text-tiny text-danger">FLASH SALE ลดราคา</div>` : ''}
          </div>
          <div class="text-body-bold ${low ? 'text-danger' : ''}">${stock === 0 ? 'หมด' : stock}</div>
          <div>${pillHtml(active ? 'ขายอยู่' : 'ปิดขาย', active ? 'success' : 'muted')}</div>
          <div style="display:flex;justify-content:flex-end;gap:4px;flex-wrap:wrap">
            <button type="button" class="btn btn-outline btn-sm" data-role="edit">แก้ไข</button>
            ${state.is_owner ? `
              <button type="button" class="btn ${onSale ? 'btn-danger' : 'btn-primary'} btn-sm" data-role="flash">${onSale ? 'ลบ Flash' : '+Flash Sale'}</button>
              <button type="button" class="btn ${active ? 'btn-outline' : 'btn-success'} btn-sm" data-role="toggle">${active ? 'ปิดขาย' : 'เปิดขาย'}</button>
              <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
            ` : ''}
          </div>
        `;

        r.querySelector('[data-role="edit"]').addEventListener('click', () => router.show('admin_product_form', { product_id: p.id }));
        const flashBtn = r.querySelector('[data-role="flash"]');
        if (flashBtn) flashBtn.addEventListener('click', () => manageFlashSale(p));
        const togBtn = r.querySelector('[data-role="toggle"]');
        if (togBtn) {
          togBtn.addEventListener('click', async () => {
            if (active) {
              const ok = await confirm('ปิดขายสินค้า', `ปิดขาย “${p.name}” ใช่ไหม?
ผู้ซื้อจะมองไม่เห็นสินค้านี้ (ประวัติออเดอร์ยังอยู่ครบ)`, { confirmText: 'ปิดขาย', danger: true });
              if (!ok) return;
            }
            try {
              await api.post(`/api/admin/products/${p.id}/active`, { active: !active });
              showToast(`${!active ? 'เปิดขาย' : 'ปิดขาย'}สินค้า “${p.name}” เรียบร้อยแล้ว`, 'success');
              await load();
            } catch (err) {
              const em = err.message || 'ไม่สามารถเปลี่ยนสถานะสินค้าได้';
              errEl.textContent = `⛔ ${em}`;
              showToast(em, 'error');
            }
          });
        }
        const delBtn = r.querySelector('[data-role="del"]');
        if (delBtn) {
          delBtn.addEventListener('click', async () => {
            const ok = await confirm(
              'ลบสินค้าแบบเก็บประวัติ (Soft Delete)',
              `ย้ายสินค้า “${p.name}” ไปที่รายการสินค้าที่ถูกลบใช่ไหม?
• สินค้าจะถูกซ่อนจากหน้าร้าน
• ประวัติคำสั่งซื้อ รีวิว และรายงานยอดขายเดิมจะยังคงอยู่ครบถ้วน
• สามารถกดกู้คืนได้ทุกเมื่อที่แท็บ 'สินค้าที่ถูกลบ'`,
              { confirmText: 'ลบเก็บประวัติ', danger: true }
            );
            if (!ok) return;
            try {
              await api.del(`/api/admin/products/${p.id}`);
              showToast(`ย้ายสินค้า “${p.name}” ไปที่ถังขยะเรียบร้อยแล้ว`, 'success');
              await load();
            } catch (err) {
              const em = err.message || 'ลบสินค้าไม่สำเร็จ';
              errEl.textContent = `⛔ ${em}`;
              showToast(em, 'error');
            }
          });
        }
        listEl.appendChild(r);
      }
      pager.set(res.page || 1, res.pages || 1, res.total);
    } catch (err) {
      const em = err.message || 'โหลดรายการสินค้าไม่สำเร็จ';
      errEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
    }
  }

  async function manageFlashSale(p) {
    let full = null;
    try {
      full = await api.get(`/api/admin/products/${p.id}/edit`);
    } catch (err) {
      const em = err.message || 'โหลดข้อมูลสินค้าไม่สำเร็จ';
      errEl.textContent = `⛔ ${em}`;
      showToast(em, 'error');
      return;
    }
    if (p.is_on_sale) {
      const ok = await confirm(
        'นำออกจาก Flash Sale',
        `ต้องการนำ “${p.name}” ออกจากโปรโมชัน Flash Sale กลับไปใช้ราคาปกติ ${formatPrice(full.price)} ใช่หรือไม่?`,
        { confirmText: 'นำออกจาก Flash Sale', danger: true }
      );
      if (!ok) return;
      try {
        await api.put(`/api/admin/products/${p.id}`, {
          ...full,
          sale_price: null,
          sale_ends_at: null,
        });
        showToast(`นำ “${p.name}” ออกจาก Flash Sale เรียบร้อยแล้ว`, 'success');
        await load();
      } catch (err) {
        const em = err.message || 'นำออกจาก Flash Sale ไม่สำเร็จ';
        errEl.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
      return;
    }

    const basePrice = Number(full.price || 100);
    const defSale = Math.max(1, Math.round(basePrice * 0.85));
    const dEnd = new Date(Date.now() + 3 * 86400000);
    dEnd.setHours(23, 59, 59, 0);
    const defEnd = formatIsoLocal(dEnd);

    openModal({
      title: `⚡ ตั้งค่า Flash Sale — ${full.name}`,
      width: 500,
      render(card, close) {
        card.innerHTML = `
          <div class="text-h3" style="margin-bottom:2px">เพิ่มเข้า Flash Sale: ${esc(full.name)}</div>
          <div class="text-body-bold text-primary" style="margin-bottom:10px">ราคาปกติ: ${esc(formatPrice(full.price))}</div>

          <div class="field-group" style="margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;flex-wrap:wrap;gap:4px">
              <span class="text-small-bold">ราคาลดพิเศษ Flash Sale (บาท) <span class="text-danger">*</span></span>
              <div style="display:flex;gap:4px">
                <button type="button" class="btn btn-outline btn-sm" data-disc-pct="10" style="height:24px;padding:0 8px;font-size:11px">ลด 10%</button>
                <button type="button" class="btn btn-outline btn-sm" data-disc-pct="15" style="height:24px;padding:0 8px;font-size:11px">ลด 15%</button>
                <button type="button" class="btn btn-outline btn-sm" data-disc-pct="20" style="height:24px;padding:0 8px;font-size:11px">ลด 20%</button>
                <button type="button" class="btn btn-outline btn-sm" data-disc-pct="30" style="height:24px;padding:0 8px;font-size:11px">ลด 30%</button>
              </div>
            </div>
            <input type="text" class="input" data-role="sp" value="${defSale}" />
          </div>

          <div class="field-group" style="margin-bottom:10px">
            <div class="text-small-bold" style="margin-bottom:4px">วันเวลาสิ้นสุด Flash Sale (เลือกจากปฏิทิน / ตารางเวลา) <span class="text-danger">*</span></div>
            <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px">
              <button type="button" class="btn btn-outline btn-sm" data-dur="today_end" style="height:26px;padding:0 8px;font-size:12px">⚡ วันนี้ 23:59</button>
              <button type="button" class="btn btn-outline btn-sm" data-dur="24h" style="height:26px;padding:0 8px;font-size:12px">⚡ +24 ชั่วโมง</button>
              <button type="button" class="btn btn-outline btn-sm" data-dur="3d" style="height:26px;padding:0 8px;font-size:12px">⚡ +3 วัน (23:59)</button>
              <button type="button" class="btn btn-outline btn-sm" data-dur="7d" style="height:26px;padding:0 8px;font-size:12px">⚡ +7 วัน (23:59)</button>
            </div>
            <div data-role="end-picker-slot"></div>
          </div>

          <div class="text-small text-danger" data-role="err" style="min-height:18px"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px">
            <button type="button" class="btn btn-outline btn-md" data-role="cancel">ยกเลิก</button>
            <button type="button" class="btn btn-primary btn-md" data-role="save">บันทึกเข้า Flash Sale</button>
          </div>
        `;

        const spIn = card.querySelector('[data-role="sp"]');
        const err = card.querySelector('[data-role="err"]');

        const endPicker = createDateTimePickerField({
          placeholder: 'คลิกปุ่ม ปฏิทิน / ตารางเวลา...',
          defaultEndOfDay: true,
          allowEmpty: false,
          width: '100%',
        });
        endPicker.set(defEnd);
        card.querySelector('[data-role="end-picker-slot"]').appendChild(endPicker.el);

        spIn.addEventListener('input', () => clearFieldError(spIn));
        endPicker.entry.addEventListener('input', () => clearFieldError(endPicker.entry));

        card.querySelectorAll('[data-disc-pct]').forEach((btn) => {
          btn.addEventListener('click', () => {
            const pct = Number(btn.getAttribute('data-disc-pct') || 15);
            spIn.value = String(Math.max(1, Math.round(basePrice * (1 - pct / 100))));
            clearFieldError(spIn);
          });
        });

        card.querySelectorAll('[data-dur]').forEach((btn) => {
          btn.addEventListener('click', () => {
            const modeDur = btn.getAttribute('data-dur');
            const dt = new Date();
            if (modeDur === 'today_end') {
              dt.setHours(23, 59, 59, 0);
            } else if (modeDur === '24h') {
              dt.setTime(Date.now() + 24 * 3600 * 1000);
            } else if (modeDur === '3d') {
              dt.setTime(Date.now() + 3 * 86400 * 1000);
              dt.setHours(23, 59, 59, 0);
            } else if (modeDur === '7d') {
              dt.setTime(Date.now() + 7 * 86400 * 1000);
              dt.setHours(23, 59, 59, 0);
            }
            endPicker.set(formatIsoLocal(dt));
            clearFieldError(endPicker.entry);
          });
        });

        card.querySelector('[data-role="cancel"]').addEventListener('click', () => close());
        card.querySelector('[data-role="save"]').addEventListener('click', async () => {
          err.textContent = '';
          clearFieldError(spIn);
          clearFieldError(endPicker.entry);
          try {
            const sp = parseMoney(spIn.value, 'ราคาลดพิเศษ', { required: true, minimum: 1 });
            if (sp >= basePrice) {
              const msg = `ราคาลดพิเศษต้องน้อยกว่าราคาปกติ (${formatPrice(basePrice)})`;
              setFieldError(spIn, msg);
              showToast(msg, 'error');
              return;
            }
            const endVal = endPicker.get();
            if (!endVal) {
              const msg = 'กรุณาเลือกวันเวลาสิ้นสุด Flash Sale จากปฏิทิน/ตารางเวลา';
              setFieldError(endPicker.entry, msg);
              showToast(msg, 'error');
              return;
            }
            await api.put(`/api/admin/products/${p.id}`, {
              ...full,
              sale_price: sp,
              sale_ends_at: endVal,
            });
            showToast(`เพิ่ม “${full.name}” เข้าโปรโมชัน Flash Sale สำเร็จ`, 'success');
            close();
            await load();
          } catch (ex) {
            const em = ex.message || 'บันทึก Flash Sale ไม่สำเร็จ';
            err.textContent = `⛔ ${em}`;
            showToast(em, 'error');
          }
        });
      },
    });
  }

  function openBannerManagerModal() {
    let editId = null;
    openModal({
      title: 'จัดการแบนเนอร์หน้าแรก (1–10 รูป พร้อมปรับแต่งข้อความ)',
      width: 680,
      render(card, close) {
        card.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div class="text-h3" data-role="form-lbl">เพิ่ม/แก้ไขแบนเนอร์หน้าแรก (รองรับ 1 – 10 รูป)</div>
            <button type="button" class="btn btn-outline btn-sm" data-role="close">ปิด</button>
          </div>
          <div class="card-alt" style="padding:12px;margin-bottom:10px;display:flex;gap:12px;align-items:flex-start">
            <div data-role="picker-slot"></div>
            <div style="flex:1;display:flex;flex-direction:column;gap:6px">
              <input type="text" class="input" data-role="b-title" placeholder="หัวข้อแบนเนอร์ * เช่น ตัวช่วยเลือกไม้ & AI แนะนำไม้แบดคู่ใจ 3 รุ่น" style="height:34px" />
              <input type="text" class="input" data-role="b-sub" placeholder="คำอธิบายเพิ่มเติม เช่น วิเคราะห์ตามระดับฝีมือ สไตล์การเล่น และงบประมาณ" style="height:34px" />
              <div class="text-small text-danger" data-role="err" style="min-height:16px"></div>
              <div style="display:flex;gap:6px">
                <button type="button" class="btn btn-primary btn-sm" data-role="save">＋ เพิ่มแบนเนอร์</button>
                <button type="button" class="btn btn-outline btn-sm" data-role="reset">ล้างฟอร์ม</button>
              </div>
            </div>
          </div>
          <div data-role="list" style="max-height:320px;overflow-y:auto;display:flex;flex-direction:column;gap:6px"></div>
        `;

        const bPicker = createImagePicker({ size: [76, 76], allowClear: true });
        card.querySelector('[data-role="picker-slot"]').appendChild(bPicker.el);
        const formLbl = card.querySelector('[data-role="form-lbl"]');
        const bTitle = card.querySelector('[data-role="b-title"]');
        const bSub = card.querySelector('[data-role="b-sub"]');
        const err = card.querySelector('[data-role="err"]');
        const saveBtn = card.querySelector('[data-role="save"]');
        const list = card.querySelector('[data-role="list"]');

        bTitle.addEventListener('input', () => clearFieldError(bTitle));

        function resetForm() {
          editId = null;
          formLbl.textContent = 'เพิ่ม/แก้ไขแบนเนอร์หน้าแรก (รองรับ 1 – 10 รูป)';
          bTitle.value = '';
          bSub.value = '';
          clearFieldError(bTitle);
          bPicker.setImage(null);
          saveBtn.textContent = '＋ เพิ่มแบนเนอร์';
          err.textContent = '';
        }

        async function reloadList() {
          list.innerHTML = '';
          let rows = [];
          try { rows = await api.get('/api/admin/banners'); } catch (e) {}
          if (!rows.length) {
            list.innerHTML = `<div class="text-small text-muted" style="text-align:center;padding:12px">ยังไม่มีแบนเนอร์ที่อัปโหลดเอง (ใส่ได้ตั้งแต่ 1 – 10 รูป)</div>`;
            return;
          }
          rows.forEach((b, idx) => {
            const act = Boolean(b.is_active ?? 1);
            const r = document.createElement('div');
            r.className = 'card';
            r.style.padding = '6px 10px';
            r.style.display = 'flex';
            r.style.alignItems = 'center';
            r.style.gap = '8px';
            r.innerHTML = `
              ${thumbHtml(b.image_path, 42)}
              <div style="flex:1">
                <div class="text-small-bold">#${idx + 1} ${esc(b.title || '-')}</div>
                <div class="text-tiny text-muted">${esc(b.subtitle || '')}</div>
              </div>
              ${pillHtml(act ? 'แสดง' : 'ซ่อน', act ? 'success' : 'muted')}
              <button type="button" class="btn btn-info btn-sm" data-role="edit">แก้ไข</button>
              <button type="button" class="btn btn-outline btn-sm" data-role="tog">${act ? 'ซ่อน' : 'แสดง'}</button>
              <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
            `;
            r.querySelector('[data-role="edit"]').addEventListener('click', () => {
              editId = b.id;
              formLbl.textContent = `แก้ไขแบนเนอร์ #${b.id}`;
              bTitle.value = b.title || '';
              bSub.value = b.subtitle || '';
              bPicker.setImage(b.image_path);
              saveBtn.textContent = 'บันทึกการแก้ไข';
            });
            r.querySelector('[data-role="tog"]').addEventListener('click', async () => {
              try {
                await api.post(`/api/admin/banners/${b.id}/active`, { active: !act });
                showToast(`${!act ? 'แสดง' : 'ซ่อน'}แบนเนอร์ #${b.id} เรียบร้อยแล้ว`, 'success');
                await reloadList();
              } catch (ex) {
                showToast(ex.message || 'เปลี่ยนสถานะแบนเนอร์ไม่สำเร็จ', 'error');
              }
            });
            r.querySelector('[data-role="del"]').addEventListener('click', async () => {
              try {
                await api.del(`/api/admin/banners/${b.id}`);
                showToast(`ลบแบนเนอร์ #${b.id} เรียบร้อยแล้ว`, 'success');
                await reloadList();
              } catch (ex) {
                showToast(ex.message || 'ลบแบนเนอร์ไม่สำเร็จ', 'error');
              }
            });
            list.appendChild(r);
          });
        }

        saveBtn.addEventListener('click', async () => {
          err.textContent = '';
          clearFieldError(bTitle);
          const t = bTitle.value.trim();
          const s = bSub.value.trim();
          if (!t && !bPicker.getSelectedFile()) {
            const msg = 'กรุณากรอกหัวข้อแบนเนอร์ หรือเลือกรูปแบนเนอร์';
            setFieldError(bTitle, msg);
            showToast(msg, 'error');
            return;
          }
          try {
            const payload = { title: t || 'โปรโมชันพิเศษ', subtitle: s, is_active: true };
            if (bPicker.hasChange()) {
              payload.image_path = (await bPicker.resolveUploadedPath('banner')) || '';
            }
            if (editId) await api.put(`/api/admin/banners/${editId}`, payload);
            else await api.post('/api/admin/banners', payload);
            showToast(editId ? 'บันทึกการแก้ไขแบนเนอร์สำเร็จ' : 'เพิ่มแบนเนอร์ใหม่สำเร็จ', 'success');
            resetForm();
            await reloadList();
          } catch (ex) {
            const em = ex.message || 'บันทึกแบนเนอร์ไม่สำเร็จ';
            err.textContent = `⛔ ${em}`;
            showToast(em, 'error');
          }
        });

        card.querySelector('[data-role="reset"]').addEventListener('click', resetForm);
        card.querySelector('[data-role="close"]').addEventListener('click', () => close());
        reloadList();
      },
    });
  }

  await load();
}
