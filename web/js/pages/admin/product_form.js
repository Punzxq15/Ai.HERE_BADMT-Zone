// web/js/pages/admin/product_form.js — ฟอร์มเพิ่ม/แก้ไขสินค้า (T02, T03 Tech Specs 7 หัวข้อ, T04 แกลเลอรีหลายรูปผูกสี, ตัวเลือกสินค้า, สินค้าเสริมขายคู่ + ตารางเวลา Flash Sale + Toast/Inline Error)
import { api, BALANCES, esc, FLEXES, formatPrice, LEVELS, OPTION_TYPES, WEIGHT_CLASSES } from '../../api.js';
import { state } from '../../state.js';
import { parseIntField, parseMoney, pillHtml, thumbHtml } from '../../components/admin_common.js';
import { createDateTimePickerField } from '../../components/date_picker.js';
import { confirm, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';
import { createImagePicker } from '../../components/image_picker.js';
import { createSearchBar } from '../../components/search_bar.js';

export async function render(container, router, params = {}) {
  let productId = params.product_id || params.id || null;
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  let optionEditId = null;

  async function build() {
    wrap.innerHTML = '';
    const isNew = !productId;
    const owner = state.is_owner;

    let meta = {};
    try {
      meta = await api.get('/api/admin/products/form-meta', { product_id: productId || undefined });
    } catch (err) {
      wrap.innerHTML = `<div class="text-danger">${esc(err.message)}</div>`;
      return;
    }

    const d = meta.product || {};
    const categories = meta.categories || [];
    const brands = meta.all_brands || meta.brands || [];
    const allowedSpecs = meta.allowed_racket_specs || {};
    const allowedOptTypes = meta.allowed_option_types || OPTION_TYPES;
    const hasOptions = Boolean(d.options && d.options.length);
    const active = Boolean(d.is_active ?? 1);

    wrap.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px">
        <div class="text-h2">${isNew ? 'เพิ่มสินค้าใหม่' : `แก้ไขสินค้า #${productId}`}</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          ${(!isNew && owner) ? `
            <button type="button" class="btn ${d.deleted_at ? 'btn-success' : 'btn-danger'} btn-sm" data-role="del-restore">${d.deleted_at ? '♻️ กู้คืนสินค้า' : '🗑️ ลบเก็บประวัติ'}</button>
            <button type="button" class="btn ${active ? 'btn-outline' : 'btn-success'} btn-sm" data-role="tog-active">${active ? 'ปิดขายสินค้า' : 'เปิดขายสินค้า'}</button>
          ` : ''}
          <button type="button" class="btn btn-outline btn-sm" data-role="back">← กลับ</button>
        </div>
      </div>

      ${!owner ? `<div class="text-small text-muted" style="margin-bottom:8px">ℹ️ ${isNew ? 'แอดมินตั้งได้เฉพาะ "ราคาปกติ" — ราคาลด/Flash Sale ให้เจ้าของร้านตั้งภายหลัง' : 'แอดมินแก้ราคา/โปรโมชันไม่ได้ (เจ้าของร้านเท่านั้น) — แก้ข้อมูลอื่นและสต็อกได้'}</div>` : ''}
      <div class="text-small text-danger" data-role="err" style="min-height:18px;margin-bottom:6px"></div>

      <!-- การ์ดข้อมูลหลัก & Technical Specs -->
      <div class="card" style="padding:16px 20px;margin-bottom:12px">
        <div class="text-h3" style="margin-bottom:10px">ข้อมูลสินค้าและ Technical Specifications</div>
        <div style="display:grid;grid-template-columns:190px 1fr;gap:18px;align-items:start">
          <div style="display:flex;flex-direction:column;align-items:center">
            <div data-role="main-picker-slot"></div>
            <div class="text-tiny text-muted" style="margin-top:4px">รูปสินค้าหลัก 1:1 (jpg/png)</div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
            <div class="field-group" style="grid-column:span 2">
              <div class="text-small text-muted">ชื่อสินค้า *</div>
              <input type="text" class="input" data-field="name" value="${esc(d.name || '')}" />
            </div>
            <div class="field-group">
              <div class="text-small text-muted">หมวดหมู่ *</div>
              <select class="select" data-field="category_id">
                <option value="">- เลือก -</option>
                ${categories.map((c) => `<option value="${c.id}" ${c.id === d.category_id ? 'selected' : ''}>${esc(c.name)}</option>`).join('')}
              </select>
            </div>
            <div class="field-group">
              <div class="text-small text-muted">แบรนด์ *</div>
              <select class="select" data-field="brand_id">
                <option value="">- เลือก -</option>
                ${brands.map((b) => `<option value="${b.id}" ${b.id === d.brand_id ? 'selected' : ''}>${esc(b.name)}</option>`).join('')}
              </select>
            </div>
            <div class="field-group">
              <div class="text-small text-muted">ราคาปกติ (บาท) *</div>
              <input type="text" class="input" data-field="price" value="${d.price != null ? d.price : ''}" placeholder="เช่น 2990" ${(owner || isNew) ? '' : 'disabled'} />
            </div>
            <div class="field-group">
              <div class="text-small text-muted">สต็อก (ชิ้น)</div>
              <input type="text" class="input" data-field="stock" value="${d.stock != null ? d.stock : 0}" ${hasOptions ? 'disabled' : ''} />
            </div>
            <div class="field-group">
              <div class="text-small text-muted">ราคาลด (บาท) — เว้นว่าง = ไม่ลด</div>
              <input type="text" class="input" data-field="sale_price" value="${d.sale_price != null ? d.sale_price : ''}" ${owner ? '' : 'disabled'} />
            </div>
            <div class="field-group">
              <div class="text-small text-muted">โปรสิ้นสุด (Flash Sale) — เลือกวัน-เวลาจากปฏิทิน/ตารางเวลา</div>
              <div data-role="sale-end-slot"></div>
            </div>
            <div class="field-group">
              <div class="text-small text-muted">ต้นทุนต่อชิ้น (บาท — สำหรับรายงานกำไร/ต้นทุน)</div>
              <input type="text" class="input" data-field="cost_price" value="${d.cost_price != null ? d.cost_price : ''}" placeholder="0" ${owner ? '' : 'disabled'} />
            </div>

            <!-- T02 & T03: Technical Specifications -->
            <div class="card-alt" style="grid-column:span 2;padding:12px 14px;margin-top:4px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <span class="text-body-bold">Technical Specifications สำหรับไม้แบดมินตัน (T02 & T03 — เว้นว่างได้สำหรับหมวดอื่น)</span>
                ${owner ? `<button type="button" class="btn btn-outline btn-sm" data-role="go-cat-opts">⚙️ เพิ่มค่า 3U–10U / ตั้งค่าตัวเลือกหมวดหมู่</button>` : ''}
              </div>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px">
                <div>
                  <div class="text-tiny text-muted">Weight Class (ตัวกรอง)</div>
                  <select class="select" data-spec="weight_class">
                    <option value="">- ไม่ระบุ -</option>
                    ${(allowedSpecs.weight_class || WEIGHT_CLASSES).map((v) => `<option value="${esc(v)}" ${d.weight_class === v ? 'selected' : ''}>${esc(v)}</option>`).join('')}
                  </select>
                </div>
                <div>
                  <div class="text-tiny text-muted">Balance Type (เช่น Head Heavy)</div>
                  <select class="select" data-spec="balance">
                    <option value="">- ไม่ระบุ -</option>
                    ${(allowedSpecs.balance || BALANCES).map((v) => `<option value="${esc(v)}" ${(d.balance || d.spec_balance_type) === v ? 'selected' : ''}>${esc(v)}</option>`).join('')}
                  </select>
                </div>
                <div>
                  <div class="text-tiny text-muted">Shaft Flexibility *</div>
                  <select class="select" data-spec="flex">
                    <option value="">- ไม่ระบุ -</option>
                    ${(allowedSpecs.flex || FLEXES).map((v) => `<option value="${esc(v)}" ${d.flex === v ? 'selected' : ''}>${esc(v)}</option>`).join('')}
                  </select>
                </div>
                <div>
                  <div class="text-tiny text-muted">Skill Level *</div>
                  <select class="select" data-spec="level">
                    <option value="">- ไม่ระบุ -</option>
                    ${(allowedSpecs.level || LEVELS).map((v) => `<option value="${esc(v)}" ${d.level === v ? 'selected' : ''}>${esc(v)}</option>`).join('')}
                  </select>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
                <div>
                  <div class="text-small text-muted">Material (เจ้าของพิมพ์เอง)</div>
                  <input type="text" class="input" data-field="spec_material" value="${esc(d.spec_material || '')}" placeholder="เช่น 46T Mitsubishi Carbon Sheet + M40X Carbon" />
                </div>
                <div>
                  <div class="text-small text-muted">Weight Class / Grip (เจ้าของพิมพ์เอง)</div>
                  <input type="text" class="input" data-field="spec_weight_grip" value="${esc(d.spec_weight_grip || '')}" placeholder="เช่น 4U (82±2 grams) / G6 grip size" />
                </div>
                <div>
                  <div class="text-small text-muted">Balance Point ตัวเลข (mm — จะรวมกับ Balance Type อัตโนมัติ)</div>
                  <input type="text" class="input" data-field="spec_balance_mm" value="${esc(d.spec_balance_mm || '')}" placeholder="เช่น 305±3 mm" />
                </div>
                <div>
                  <div class="text-small text-muted">Max String Tension (เจ้าของพิมพ์เอง)</div>
                  <input type="text" class="input" data-field="spec_max_tension" value="${esc(d.spec_max_tension || '')}" placeholder="เช่น Up to 35 lbs" />
                </div>
                <div>
                  <div class="text-small text-muted">Length (ความยาวไม้ — เจ้าของพิมพ์เอง)</div>
                  <input type="text" class="input" data-field="spec_length" value="${esc(d.spec_length || '')}" placeholder="เช่น 675 mm" />
                </div>
              </div>
            </div>

            <div style="grid-column:span 2">
              <div class="text-small text-muted">คำอธิบายสินค้า</div>
              <textarea class="textarea" data-field="description" rows="4">${esc(d.description || '')}</textarea>
            </div>
          </div>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px">
          <button type="button" class="btn btn-outline btn-md" data-role="cancel-btn">ยกเลิก</button>
          <button type="button" class="btn btn-primary btn-md" data-role="save-btn">💾 บันทึกสินค้า</button>
        </div>
      </div>

      <div data-role="extra-sections"></div>
    `;

    const errEl = wrap.querySelector('[data-role="err"]');
    wrap.querySelector('[data-role="back"]').addEventListener('click', () => router.go_back('admin_products'));
    wrap.querySelector('[data-role="cancel-btn"]').addEventListener('click', () => router.go_back('admin_products'));
    const goCatOpts = wrap.querySelector('[data-role="go-cat-opts"]');
    if (goCatOpts) goCatOpts.addEventListener('click', () => router.show('admin_categories'));

    wrap.querySelectorAll('[data-field]').forEach((el) => {
      el.addEventListener('input', () => clearFieldError(el));
      el.addEventListener('change', () => clearFieldError(el));
    });

    const mainPicker = createImagePicker({
      size: [170, 170],
      initialPath: d.image_path,
      allowClear: true,
    });
    wrap.querySelector('[data-role="main-picker-slot"]').appendChild(mainPicker.el);

    const saleEndPicker = createDateTimePickerField({
      placeholder: 'เว้นว่าง = ลดตลอด',
      defaultEndOfDay: true,
      width: '100%',
    });
    saleEndPicker.set(String(d.sale_ends_at || '').slice(0, 19));
    if (!owner) saleEndPicker.setDisabled(true);
    wrap.querySelector('[data-role="sale-end-slot"]').appendChild(saleEndPicker.el);

    const togBtn = wrap.querySelector('[data-role="tog-active"]');
    if (togBtn) {
      togBtn.addEventListener('click', async () => {
        if (active) {
          const ok = await confirm('ปิดขายสินค้า', 'ผู้ซื้อจะมองไม่เห็นสินค้านี้ (ประวัติออเดอร์ยังอยู่ครบ) ปิดขายใช่ไหม?', { confirmText: 'ปิดขาย', danger: true });
          if (!ok) return;
        }
        try {
          await api.post(`/api/admin/products/${productId}/active`, { active: !active });
          showToast(`${!active ? 'เปิดขาย' : 'ปิดขาย'}สินค้าเรียบร้อยแล้ว`, 'success');
          await build();
        } catch (err) {
          showToast(err.message || 'เปลี่ยนสถานะไม่สำเร็จ', 'error');
        }
      });
    }

    const delRestBtn = wrap.querySelector('[data-role="del-restore"]');
    if (delRestBtn) {
      delRestBtn.addEventListener('click', async () => {
        if (d.deleted_at) {
          await api.post(`/api/admin/products/${productId}/restore`);
          showToast('กู้คืนสินค้าเรียบร้อยแล้ว', 'success');
          await build();
        } else {
          const ok = await confirm('ลบสินค้าแบบเก็บประวัติ', 'ย้ายสินค้านี้ไปที่รายการสินค้าที่ถูกลบใช่ไหม? (ประวัติยอดขายและออเดอร์เดิมยังอยู่ครบ)', { confirmText: 'ลบเก็บประวัติ', danger: true });
          if (!ok) return;
          await api.del(`/api/admin/products/${productId}`);
          showToast('ย้ายสินค้าไปที่ถังขยะเรียบร้อยแล้ว', 'success');
          router.show('admin_products');
        }
      });
    }

    wrap.querySelector('[data-role="save-btn"]').addEventListener('click', async () => {
      errEl.textContent = '';
      try {
        const getEl = (k) => wrap.querySelector(`[data-field="${k}"]`);
        const getF = (k) => getEl(k).value.trim();
        const name = getF('name');
        const catVal = getF('category_id');
        const brVal = getF('brand_id');
        if (!name) {
          setFieldError(getEl('name'), 'กรุณากรอกชื่อสินค้า');
          throw new Error('กรุณากรอกชื่อสินค้า');
        }
        if (!catVal) {
          setFieldError(getEl('category_id'), 'กรุณาเลือกหมวดหมู่');
          throw new Error('กรุณาเลือกหมวดหมู่');
        }
        if (!brVal) {
          setFieldError(getEl('brand_id'), 'กรุณาเลือกแบรนด์');
          throw new Error('กรุณาเลือกแบรนด์');
        }

        const payload = {
          name,
          category_id: Number(catVal),
          brand_id: Number(brVal),
          description: getF('description'),
          spec_material: getF('spec_material') || null,
          spec_weight_grip: getF('spec_weight_grip') || null,
          spec_balance_mm: getF('spec_balance_mm') || null,
          spec_max_tension: getF('spec_max_tension') || null,
          spec_length: getF('spec_length') || null,
        };
        wrap.querySelectorAll('[data-spec]').forEach((el) => {
          payload[el.dataset.spec] = el.value || null;
        });
        payload.spec_balance_type = payload.balance;

        if (owner || isNew) {
          const pVal = parseMoney(getF('price'), 'ราคาปกติ', { required: true });
          if (pVal <= 0) {
            setFieldError(getEl('price'), 'ราคาปกติต้องมากกว่า 0');
            throw new Error('ราคาปกติต้องมากกว่า 0');
          }
          payload.price = pVal;
        }
        if (owner) {
          const sale = parseMoney(getF('sale_price'), 'ราคาลด');
          const saleEnd = saleEndPicker.get() || null;
          if (sale !== null && sale >= payload.price) {
            setFieldError(getEl('sale_price'), 'ราคาลดต้องน้อยกว่าราคาปกติ');
            throw new Error('ราคาลดต้องน้อยกว่าราคาปกติ');
          }
          if (sale === null && saleEnd) {
            setFieldError(getEl('sale_price'), 'ตั้งวันสิ้นสุดโปรแล้ว กรุณากรอกราคาลดด้วย');
            throw new Error('ตั้งวันสิ้นสุดโปรแล้ว กรุณากรอกราคาลดด้วย');
          }
          payload.sale_price = sale;
          payload.sale_ends_at = sale !== null ? saleEnd : null;
          payload.cost_price = parseMoney(getF('cost_price'), 'ต้นทุนต่อชิ้น') || 0;
        }
        if (!hasOptions) {
          payload.stock = parseIntField(getF('stock'), 'สต็อก', { required: false, minimum: 0 }) || 0;
        }
        if (mainPicker.hasChange()) {
          payload.image_path = await mainPicker.resolveUploadedPath('product');
        }

        let saved = null;
        if (isNew) {
          saved = await api.post('/api/admin/products', payload);
          productId = saved.id;
        } else {
          saved = await api.put(`/api/admin/products/${productId}`, payload);
        }
        showToast(
          isNew ? 'เพิ่มสินค้าเรียบร้อย — เลื่อนลงเพื่อเพิ่มรูปภาพหลายรูป ตัวเลือกสี/สไตล์ และสินค้าเสริมได้' : 'บันทึกการแก้ไขสินค้าเรียบร้อยแล้ว',
          'success'
        );
        await router.refresh_shell();
        await build();
      } catch (err) {
        const em = err.message || 'บันทึกสินค้าไม่สำเร็จ';
        errEl.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
    });

    const extraSlot = wrap.querySelector('[data-role="extra-sections"]');
    if (isNew) {
      extraSlot.innerHTML = `<div class="text-small text-muted" style="padding:8px 0">💡 บันทึกสินค้าก่อน แล้วจะสามารถเพิ่มรูปภาพหลายรูป (แกลเลอรี), ตัวเลือก (สี/สไตล์/ด้าม/เอ็น/ไซซ์) และสินค้าเสริมขายคู่ได้</div>`;
      return;
    }

    // 1. T04: Gallery Card
    const images = d.images || [];
    const galCard = document.createElement('div');
    galCard.className = 'card';
    galCard.style.padding = '14px 18px';
    galCard.style.marginBottom = '12px';
    galCard.innerHTML = `
      <div class="text-h3">รูปภาพภายในสินค้า (T04 — เพิ่มได้หลายรูป & ผูกรูปกับสี/สไตล์)</div>
      <div class="text-tiny text-muted" style="margin-bottom:8px">รูปแรกสุดจะเป็นรูปหลักของการ์ดสินค้าอัตโนมัติ · สามารถระบุสี/สไตล์ของแต่ละรูปเพื่อให้เปลี่ยนรูปตามสีที่ลูกค้าเลือกได้</div>
      <div data-role="gal-list" style="display:flex;flex-direction:column;gap:6px;margin-bottom:10px"></div>
      <div class="card-alt" style="padding:10px 12px;display:flex;gap:12px;align-items:center;flex-wrap:wrap">
        <div data-role="gal-picker"></div>
        <div style="flex:1;min-width:240px">
          <div class="text-body-bold" style="margin-bottom:4px">เพิ่มรูปภาพใหม่ในแกลเลอรีสินค้า</div>
          <div class="text-small text-muted">ผูกกับสี/สไตล์ (เว้นว่างได้ ถ้าเป็นรูปมุมอื่นทั่วไป):</div>
          <div style="display:flex;gap:8px;margin-top:4px;flex-wrap:wrap">
            <input type="text" class="input" data-role="gal-color" placeholder="เช่น แดง / น้ำเงิน / ขาว-ทอง" style="width:260px;height:34px" />
            <button type="button" class="btn btn-primary btn-sm" data-role="gal-add">＋ อัปโหลดเพิ่มเข้าแกลเลอรี</button>
          </div>
        </div>
      </div>
    `;
    extraSlot.appendChild(galCard);

    const galList = galCard.querySelector('[data-role="gal-list"]');
    images.forEach((img, idx) => {
      const r = document.createElement('div');
      r.className = 'card-alt';
      r.style.padding = '6px 10px';
      r.style.display = 'flex';
      r.style.alignItems = 'center';
      r.style.gap = '10px';
      r.innerHTML = `
        ${thumbHtml(img.path, 50)}
        <div style="flex:1;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          ${idx === 0 ? pillHtml('★ รูปหลัก (การ์ดสินค้า)', 'primary') : pillHtml(`รูปที่ ${idx + 1}`, 'muted')}
          ${img.color_value ? pillHtml(`สี/สไตล์: ${img.color_value}`, 'info') : `<span class="text-small text-muted">(ไม่ได้ผูกสีเฉพาะ)</span>`}
        </div>
        ${img.id > 0 ? `
          ${idx > 0 ? `<button type="button" class="btn btn-primary btn-sm" data-role="set-prim">ตั้งเป็นรูปหลัก</button>` : ''}
          <button type="button" class="btn btn-danger btn-sm" data-role="del-img">ลบ</button>
        ` : ''}
      `;
      const primBtn = r.querySelector('[data-role="set-prim"]');
      if (primBtn) {
        primBtn.addEventListener('click', async () => {
          await api.put(`/api/admin/products/${productId}/images/${img.id}/primary`);
          showToast('เปลี่ยนรูปหลักของสินค้าเรียบร้อยแล้ว', 'success');
          await build();
        });
      }
      const delImgBtn = r.querySelector('[data-role="del-img"]');
      if (delImgBtn) {
        delImgBtn.addEventListener('click', async () => {
          const ok = await confirm('ลบรูปภาพ', 'ต้องการลบรูปภาพนี้ออกจากสินค้าใช่หรือไม่?', { danger: true });
          if (!ok) return;
          await api.del(`/api/admin/product-images/${img.id}`);
          showToast('ลบรูปภาพออกจากแกลเลอรีเรียบร้อยแล้ว', 'success');
          await build();
        });
      }
      galList.appendChild(r);
    });

    const galPicker = createImagePicker({ size: [68, 68], allowClear: true, buttonText: 'เลือกรูปเพิ่ม...' });
    galCard.querySelector('[data-role="gal-picker"]').appendChild(galPicker.el);
    galCard.querySelector('[data-role="gal-add"]').addEventListener('click', async () => {
      errEl.textContent = '';
      if (!galPicker.getSelectedFile()) {
        const msg = 'กรุณาเลือกไฟล์รูปภาพที่ต้องการเพิ่ม';
        errEl.textContent = `⛔ ${msg}`;
        showToast(msg, 'error');
        return;
      }
      try {
        const upPath = await galPicker.resolveUploadedPath('product');
        const colVal = galCard.querySelector('[data-role="gal-color"]').value.trim() || null;
        await api.post(`/api/admin/products/${productId}/images`, { path: upPath, color_value: colVal });
        showToast('เพิ่มรูปภาพเข้าแกลเลอรีเรียบร้อยแล้ว', 'success');
        await build();
      } catch (err) {
        const em = err.message || 'อัปโหลดรูปภาพไม่สำเร็จ';
        errEl.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
    });

    // 2. Options Card
    const options = d.options || [];
    const curOpt = options.find((o) => o.id === optionEditId) || {};
    const optCard = document.createElement('div');
    optCard.className = 'card';
    optCard.style.padding = '14px 18px';
    optCard.style.marginBottom = '12px';
    optCard.innerHTML = `
      <div class="text-h3">ตัวเลือกสินค้า (สี / สไตล์ / ด้าม / เอ็น / ไซซ์ / ความเร็วลูก)</div>
      <div class="text-tiny text-muted" style="margin-bottom:8px">ถ้ามีตัวเลือก สต็อกสินค้ารวมจะคำนวณจากตัวเลือกให้อัตโนมัติ</div>
      <div data-role="opt-list" style="display:flex;flex-direction:column;gap:4px;margin-bottom:10px"></div>
      <div class="card-alt" style="padding:10px 12px">
        <div class="text-body-bold" style="margin-bottom:6px">${optionEditId ? 'แก้ไขตัวเลือก' : 'เพิ่มตัวเลือกใหม่'}</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:flex-start">
          <select class="select" data-role="opt-type" style="width:130px;height:36px">
            ${allowedOptTypes.map((t) => `<option value="${esc(t)}" ${curOpt.option_type === t ? 'selected' : ''}>${esc(t)}</option>`).join('')}
          </select>
          <div class="field-group">
            <input type="text" class="input" data-role="opt-val" value="${esc(curOpt.option_value || '')}" placeholder="ชื่อตัวเลือก เช่น แดง / ขาว-ทอง / 42 / XL / สปีด 75" style="width:260px;height:36px" />
          </div>
          <input type="text" class="input" data-role="opt-extra" value="${curOpt.extra_price != null ? curOpt.extra_price : ''}" placeholder="ราคาเพิ่ม" style="width:100px;height:36px" />
          <input type="text" class="input" data-role="opt-stock" value="${curOpt.stock != null ? curOpt.stock : ''}" placeholder="สต็อก" style="width:80px;height:36px" />
          <button type="button" class="btn btn-primary btn-sm" data-role="opt-save" style="height:36px">${optionEditId ? 'บันทึก' : '➕ เพิ่ม'}</button>
          ${optionEditId ? `<button type="button" class="btn btn-outline btn-sm" data-role="opt-cancel" style="height:36px">ยกเลิก</button>` : ''}
        </div>
      </div>
    `;
    extraSlot.appendChild(optCard);

    const optList = optCard.querySelector('[data-role="opt-list"]');
    if (!options.length) {
      optList.innerHTML = `<div class="text-small text-muted">ยังไม่มีตัวเลือก (สินค้าชิ้นเดียวใช้สต็อกด้านบนได้เลย)</div>`;
    } else {
      for (const o of options) {
        const st = Number(o.stock || 0);
        const r = document.createElement('div');
        r.style.display = 'flex';
        r.style.alignItems = 'center';
        r.style.gap = '10px';
        r.style.padding = '3px 0';
        r.innerHTML = `
          ${pillHtml(o.option_type || '-', 'info')}
          <span class="text-body" style="flex:1">${esc(o.option_value || '-')}</span>
          ${o.extra_price ? `<span class="text-small text-muted">+${esc(formatPrice(o.extra_price))}</span>` : ''}
          <span class="text-small-bold ${st === 0 ? 'text-danger' : ''}" style="min-width:70px">${st === 0 ? 'หมด' : `สต็อก ${st}`}</span>
          <button type="button" class="btn btn-outline btn-sm" data-role="edit-opt">แก้ไข</button>
          <button type="button" class="btn btn-danger btn-sm" data-role="del-opt">ลบ</button>
        `;
        r.querySelector('[data-role="edit-opt"]').addEventListener('click', () => { optionEditId = o.id; build(); });
        r.querySelector('[data-role="del-opt"]').addEventListener('click', async () => {
          const ok = await confirm('ลบตัวเลือก', `ลบตัวเลือก “${o.option_type}: ${o.option_value}” ใช่ไหม?`, { confirmText: 'ลบ', danger: true });
          if (!ok) return;
          await api.del(`/api/admin/options/${o.id}`);
          showToast(`ลบตัวเลือก “${o.option_value}” เรียบร้อยแล้ว`, 'success');
          await build();
        });
        optList.appendChild(r);
      }
    }

    const optValIn = optCard.querySelector('[data-role="opt-val"]');
    optValIn.addEventListener('input', () => clearFieldError(optValIn));

    optCard.querySelector('[data-role="opt-save"]').addEventListener('click', async () => {
      errEl.textContent = '';
      clearFieldError(optValIn);
      try {
        const val = optValIn.value.trim();
        if (!val) {
          setFieldError(optValIn, 'กรุณากรอกชื่อตัวเลือก');
          throw new Error('กรุณากรอกชื่อตัวเลือก');
        }
        const extra = parseMoney(optCard.querySelector('[data-role="opt-extra"]').value, 'ราคาเพิ่ม') || 0;
        const st = parseIntField(optCard.querySelector('[data-role="opt-stock"]').value, 'สต็อก', { required: false, minimum: 0 }) || 0;
        const oType = optCard.querySelector('[data-role="opt-type"]').value;
        await api.post(`/api/admin/products/${productId}/options`, {
          option_id: optionEditId,
          option_type: oType,
          option_value: val,
          extra_price: extra,
          stock: st,
        });
        showToast(optionEditId ? 'บันทึกตัวเลือกสินค้าเรียบร้อยแล้ว' : 'เพิ่มตัวเลือกสินค้าเรียบร้อยแล้ว', 'success');
        optionEditId = null;
        await build();
      } catch (err) {
        const em = err.message || 'บันทึกตัวเลือกไม่สำเร็จ';
        errEl.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
    });
    const optCancel = optCard.querySelector('[data-role="opt-cancel"]');
    if (optCancel) optCancel.addEventListener('click', () => { optionEditId = null; build(); });

    // 3. Addons Card
    const addons = d.addons || [];
    const addonIds = addons.map((a) => a.id ?? a.addon_product_id);
    const addonCard = document.createElement('div');
    addonCard.className = 'card';
    addonCard.style.padding = '14px 18px';
    addonCard.innerHTML = `
      <div class="text-h3" style="margin-bottom:6px">สินค้าเสริมขายคู่ (แสดงเป็น "ซื้อคู่กัน" ในหน้าสินค้า)</div>
      <div data-role="addon-list" style="display:flex;flex-direction:column;gap:4px;margin-bottom:10px"></div>
      <div class="text-small text-muted" style="margin-bottom:4px">เพิ่มสินค้าเสริม: ค้นหาแล้วกด เพิ่ม</div>
      <div data-role="addon-search"></div>
      <div data-role="addon-results" style="margin-top:6px;display:flex;flex-direction:column;gap:4px"></div>
    `;
    extraSlot.appendChild(addonCard);

    const addonList = addonCard.querySelector('[data-role="addon-list"]');
    if (!addons.length) {
      addonList.innerHTML = `<div class="text-small text-muted">ยังไม่มีสินค้าเสริม</div>`;
    } else {
      for (const a of addons) {
        const aid = a.id ?? a.addon_product_id;
        const r = document.createElement('div');
        r.style.display = 'flex';
        r.style.alignItems = 'center';
        r.style.gap = '10px';
        r.innerHTML = `
          <span class="text-body" style="flex:1">${esc(a.name || a.addon_name || '-')}</span>
          <span class="text-small text-muted">${esc(formatPrice(a.effective_price ?? a.price))}</span>
          <button type="button" class="btn btn-outline btn-sm">✕ เอาออก</button>
        `;
        r.querySelector('button').addEventListener('click', async () => {
          const nextIds = addonIds.filter((id) => id !== aid);
          await api.put(`/api/admin/products/${productId}/addons`, { addon_ids: nextIds });
          showToast('นำสินค้าเสริมออกเรียบร้อยแล้ว', 'success');
          await build();
        });
        addonList.appendChild(r);
      }
    }

    const addonResults = addonCard.querySelector('[data-role="addon-results"]');
    const addonSearch = createSearchBar({
      placeholder: 'ค้นหาชื่อสินค้า',
      width: 300,
      enableSuggestions: false,
      async onSubmit(q) {
        addonResults.innerHTML = '';
        if (!q) return;
        const res = await api.get('/api/admin/products', { search: q, page: 1, page_size: 6, show_inactive: false });
        const candidates = (res.items || []).filter((p) => p.id !== Number(productId) && !addonIds.includes(p.id));
        if (!candidates.length) {
          addonResults.innerHTML = `<div class="text-small text-muted">ไม่พบสินค้าที่เพิ่มได้</div>`;
          return;
        }
        for (const p of candidates) {
          const r = document.createElement('div');
          r.style.display = 'flex';
          r.style.alignItems = 'center';
          r.style.gap = '10px';
          r.innerHTML = `
            <span class="text-body" style="flex:1">${esc(p.name)}</span>
            <span class="text-small text-muted">${esc(formatPrice(p.effective_price ?? p.price))}</span>
            <button type="button" class="btn btn-primary btn-sm">เพิ่ม</button>
          `;
          r.querySelector('button').addEventListener('click', async () => {
            await api.put(`/api/admin/products/${productId}/addons`, { addon_ids: [...addonIds, p.id] });
            showToast(`เพิ่ม “${p.name}” เป็นสินค้าเสริมเรียบร้อยแล้ว`, 'success');
            await build();
          });
          addonResults.appendChild(r);
        }
      },
    });
    addonCard.querySelector('[data-role="addon-search"]').appendChild(addonSearch.el);
  }

  await build();
}
