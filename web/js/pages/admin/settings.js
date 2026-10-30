// web/js/pages/admin/settings.js — หน้าตั้งค่าร้าน 5 แท็บ (ตั้งค่าร้าน & โลโก้ & แบนเนอร์ Login/Sign Up, ข้อมูลติดต่อ & โซเชียล, รายงาน .xlsx & รายจ่าย, แบนเนอร์หน้าแรก & Audit, สำรองฐานข้อมูล)
import { api, esc, formatDateTime, formatPrice, resolveAssetUrl } from '../../api.js';
import { createSegmented, parseMoney, pillHtml, thumbHtml } from '../../components/admin_common.js';
import { renderAuthExperience } from '../../components/auth_layout.js';
import { createDatePickerField } from '../../components/date_picker.js';
import { confirm, openModal, showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';
import { createImagePicker } from '../../components/image_picker.js';
import { state, syncDocumentTitle } from '../../state.js';

const TAB_STORE = 'ตั้งค่าร้าน & โลโก้ 1:1';
const TAB_CONTACT = 'ข้อมูลติดต่อ & โซเชียล';
const TAB_EXPORT = 'รายงาน .xlsx & รายจ่าย';
const TAB_BANNER_AUDIT = 'แบนเนอร์ (1-10 รูป) & Audit';
const TAB_BACKUP = 'สำรองฐานข้อมูล';

const MAX_LOGIN_BANNERS = 7;
const ALLOWED_LOGO_BANNER_EXTS = ['.png', '.webp', '.jpg', '.jpeg'];
const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

const STORE_SECTIONS = [
  ['โลโก้ร้าน (No BG) · แบนเนอร์หน้า Login & Sign Up · ชื่อร้าน · ที่ตั้งหน้าร้าน', [
    ['shop_name',    'ชื่อร้าน *',                                      'เช่น AI.HERE BADᴍᴛ-Zone',                        'แสดงบนหัวเว็บ (Header) ใบเสร็จ และตอนลูกค้าชำระเงิน'],
    ['shop_address', 'ที่อยู่หน้าร้าน (ตั้งอยู่ตรงไหน ให้ลูกค้าดูได้) *',     'เช่น 99/9 ถนนสุขุมวิท แขวงคลองเตย กรุงเทพฯ 10110', 'แสดงในปุ่มที่ตั้งร้านบน Header ท้ายหน้าแรก และใบเสร็จ PDF'],
    ['shop_hours',   'เวลาเปิด-ปิดหน้าร้าน',                             'เช่น เปิดทุกวัน 10:00 - 20:00 น.',                 'แสดงให้ลูกค้าดูพร้อมที่อยู่หน้าร้าน'],
    ['shop_phone',   'เบอร์โทรศัพท์หน้าร้าน',                            '0812345678',                                    'แสดงให้ลูกค้าติดต่อและบนใบเสร็จ'],
    ['maps_url',     'ลิงก์แผนที่หน้าร้าน Google Maps (https://...)',     'https://maps.google.com/...',                   'ลูกค้าสามารถกดเปิดดูแผนที่หน้าร้านได้ทันที'],
  ]],
  ['พร้อมเพย์ (รับชำระเงิน)', [
    ['promptpay_no',   'เลขพร้อมเพย์ *',      'เบอร์โทร 10 หลัก / เลขบัตร 13 หลัก', 'ใช้สร้าง QR รับเงิน (ใส่เฉพาะตัวเลข)'],
    ['promptpay_name', 'ชื่อบัญชีพร้อมเพย์ *',  'ชื่อที่จะแสดงให้ลูกค้าตรวจก่อนโอน',   'ควรตรงกับชื่อบัญชีจริงของร้าน'],
  ]],
  ['การจัดส่ง', [
    ['shipping_fee',      'ค่าจัดส่ง (บาท)',               'เช่น 50',        'คิดต่อออเดอร์'],
    ['free_shipping_min', 'ฟรีค่าส่งเมื่อซื้อครบ (บาท)',      '0 = ไม่เปิดใช้',  'นับจากราคาสินค้าก่อนหักส่วนลด'],
  ]],
  ['สต็อกและออเดอร์', [
    ['low_stock_threshold', 'เกณฑ์สต็อกใกล้หมด (ชิ้น)',            'เช่น 5',  'เหลือเท่านี้หรือน้อยกว่า → แจ้งเตือนและขึ้นในแดชบอร์ด'],
    ['unpaid_cancel_hours', 'ยกเลิกออเดอร์ที่ไม่ชำระใน (ชั่วโมง)', 'เช่น 24', '0 = ไม่ยกเลิกอัตโนมัติ'],
  ]],
  ['การปรับแต่งหน้าร้าน คูปอง สไลด์ และตัวเลือกสินค้า (Owner Customization)', [
    ['flash_sale_scroll_speed',  'ความเร็วเลื่อนแถบ Flash Sale หน้าแรก (1-10)',       'เช่น 2',                       'ค่าน้อย = เลื่อนช้าๆ นุ่มนวล, ค่ามาก = เลื่อนเร็วขึ้น'],
    ['home_coupons_per_view',    'จำนวนคูปองที่แสดงต่อชุดในหน้าหลัก (1-6 ใบ)',         'เช่น 3',                       'จำนวนคูปองที่โชว์พร้อมกันในแถบหน้าหลัก (ค่าเริ่มต้น 3 ใบ)'],
    ['coupon_rotate_seconds',    'เวลาสลับชุดคูปองหน้าหลัก (วินาที)',                  'เช่น 9',                       'ระยะเวลาเปลี่ยนชุดคูปองในหน้าหลัก'],
    ['login_showcase_seconds',   'เวลาสุ่มเปลี่ยนภาพแบนเนอร์หน้า Login & Sign Up (วินาที)', 'เช่น 5',                   'ระยะเวลาสุ่มเปลี่ยนรูปรองเท้าแบนเนอร์หน้า Login & Sign Up (ค่าเริ่มต้น 5 วินาที)'],
    ['custom_coupon_categories', 'หมวดหมู่คูปองเพิ่มเติม (คั่นด้วยจุลภาค ,)',           'เช่น คูปองสมาชิก VIP, คูปองวันเกิด', 'เพิ่มหมวดหมู่คูปองนอกเหนือจาก ส่วนลดค่าส่ง / % / บาท / อื่นๆ'],
    ['custom_option_types',      'ประเภทตัวเลือกสินค้าเพิ่มเติม (คั่นด้วยจุลภาค ,)',      'เช่น ความตึงเอ็น, รุ่นซองไม้',     'เพิ่มประเภทตัวเลือกสินค้าในฟอร์มจัดการสินค้า'],
  ]],
];

const CONTACT_FIELDS = [
  ['owner_phone',     'เบอร์โทรเจ้าของร้าน / ร้าน *',                            '0812345678'],
  ['owner_email',     'อีเมลเจ้าของร้าน (รับข้อความด่วนจากแอดมิน) *',               'owner@badmintonpro.th'],
  ['shop_address',    'ที่อยู่หน้าร้าน (แสดงให้ลูกค้าดูได้และในใบเสร็จ)',              'เช่น 99/9 ถ.สุขุมวิท คลองเตย กรุงเทพฯ 10110'],
  ['shop_open_hours', 'เวลาทำการหน้าร้าน',                                      'เช่น เปิดทุกวัน 10:00 - 20:00 น.'],
  ['line_id',         'ชื่อ LINE Official / LINE ID',                           '@badmintonpro'],
  ['facebook_name',   'ชื่อเพจ Facebook',                                       'Badminton Pro Shop TH'],
  ['facebook_url',    'ลิงก์ Facebook (https://...)',                            'https://www.facebook.com/badmintonproshop'],
  ['instagram_name',  'ชื่อ Instagram',                                         '@badmintonpro.th'],
  ['instagram_url',   'ลิงก์ Instagram (https://...)',                           'https://www.instagram.com/badmintonpro.th'],
  ['tiktok_name',     'ชื่อ TikTok',                                            '@badmintonpro.th'],
  ['tiktok_url',      'ลิงก์ TikTok (https://...)',                              'https://www.tiktok.com/@badmintonpro.th'],
];

function fmtSize(size) {
  let s = Number(size);
  if (!Number.isFinite(s)) return '-';
  for (const unit of ['B', 'KB', 'MB', 'GB']) {
    if (s < 1024 || unit === 'GB') {
      return unit === 'B' ? `${Math.round(s)} B` : `${s.toFixed(1)} ${unit}`;
    }
    s /= 1024;
  }
  return '-';
}

function openLoginPreviewModal(router) {
  let cleanupPreview = null;
  openModal({
    title: 'ตัวอย่างหน้า Login & Sign Up (แสดงผลจริง)',
    width: 1120,
    onClose() {
      if (cleanupPreview) {
        try { cleanupPreview(); } catch (e) {}
      }
    },
    render(card, close) {
      card.style.maxWidth = '1120px';
      card.style.width = '95vw';
      card.style.padding = '14px 16px';
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div>
            <div class="text-h3">ตัวอย่างหน้า Login & Sign Up (AI.HERE Bad🅜-Zone)</div>
            <div class="text-small text-muted">ทดลองกดสลับปุ่ม LOGIN / SIGN UP และดูการสุ่มเปลี่ยนรูปรองเท้าแบนเนอร์ได้ทันที</div>
          </div>
          <button type="button" class="btn btn-outline btn-sm" data-role="close-preview">ปิดตัวอย่าง</button>
        </div>
        <div data-role="preview-stage-wrap" style="width:100%;height:560px;border-radius:16px;overflow:hidden;border:1px solid var(--color-border);position:relative;background:#E9E9E9;display:flex;align-items:center;justify-content:center"></div>
      `;
      card.querySelector('[data-role="close-preview"]').addEventListener('click', () => close());
      const wrap = card.querySelector('[data-role="preview-stage-wrap"]');
      cleanupPreview = renderAuthExperience(wrap, router, { initialMode: 'login' });
      const stageEl = wrap.querySelector('.auth2-stage');
      const shellEl = wrap.querySelector('.auth2-scale-shell');
      if (stageEl && shellEl) {
        stageEl.style.width = '100%';
        stageEl.style.height = '100%';
        stageEl.style.minHeight = '100%';
        shellEl.style.setProperty('--auth-scale', '0.76');
      }
    },
  });
}

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'admin-container';
  container.appendChild(wrap);

  if (!state.is_owner && state.role !== 'owner') {
    wrap.innerHTML = `<div class="card" style="padding:24px"><div class="text-h3 text-danger">เฉพาะเจ้าของร้าน (Owner) เท่านั้นที่สามารถเข้าถึงการตั้งค่าร้านได้</div></div>`;
    return;
  }

  let curTab = TAB_STORE;
  let editBannerId = null;

  wrap.innerHTML = `
    <div style="margin-bottom:6px">
      <div class="text-h2">ตั้งค่าร้าน · โลโก้ & แบนเนอร์ Login/Sign Up · รายงาน .xlsx · ข้อมูลติดต่อ · ระบบ</div>
      <div class="text-small text-muted">ศูนย์ควบคุมการตั้งค่าทุกอย่างในร้าน โลโก้ร้าน (No BG) แบนเนอร์รองเท้าหน้า Login & Sign Up (สูงสุด 7 รูป) และรายงานรายรับ/รายจ่าย (Owner Only)</div>
    </div>
    <div class="text-small text-danger" data-role="err" style="min-height:18px"></div>
    <div class="text-body-bold text-success" data-role="notice" style="margin-bottom:4px"></div>
    <div data-role="tabs-slot" style="margin-bottom:10px"></div>
    <div data-role="panel-holder"></div>
  `;

  const errEl = wrap.querySelector('[data-role="err"]');
  const noticeEl = wrap.querySelector('[data-role="notice"]');
  const panelHolder = wrap.querySelector('[data-role="panel-holder"]');

  const tabs = createSegmented([TAB_STORE, TAB_CONTACT, TAB_EXPORT, TAB_BANNER_AUDIT, TAB_BACKUP], curTab, (val) => {
    curTab = val;
    noticeEl.textContent = '';
    renderCurrentTab();
  });
  wrap.querySelector('[data-role="tabs-slot"]').appendChild(tabs.el);

  async function renderCurrentTab() {
    errEl.textContent = '';
    panelHolder.innerHTML = '';
    if (curTab === TAB_STORE) await renderStoreTab();
    else if (curTab === TAB_CONTACT) await renderContactTab();
    else if (curTab === TAB_EXPORT) await renderExportTab();
    else if (curTab === TAB_BANNER_AUDIT) await renderBannerAuditTab();
    else await renderBackupTab();
  }

  async function renderStoreTab() {
    let settings = {};
    let loginBanners = [];
    try {
      const res = await api.get('/api/admin/settings');
      settings = res.shop || res.all || {};
      loginBanners = res.login_banners || [];
    } catch (err) {
      errEl.textContent = err.message || '';
      return;
    }

    let currentLogoPath = (settings.store_logo_path || settings.shop_logo_path || '').trim();

    const box = document.createElement('div');
    box.className = 'card';
    box.style.padding = '16px 20px';

    let html = `<div class="text-h3" style="margin-bottom:10px">ตั้งค่าร้านค้า โลโก้ร้าน (No BG) แบนเนอร์หน้า Login & Sign Up ที่อยู่หน้าร้าน และการรับชำระเงิน</div>`;
    STORE_SECTIONS.forEach(([secTitle, fields], idx) => {
      html += `
        <div class="text-body-bold" style="margin-top:10px">${esc(secTitle)}</div>
        <div style="height:1px;background:var(--color-border);margin:4px 0 10px"></div>
      `;
      if (idx === 0) {
        html += `
          <!-- ส่วน A: โลโก้ร้าน (Owner เท่านั้น, No BG 115×115) -->
          <div class="card-alt" style="padding:14px 16px;margin-bottom:12px" data-role="owner-logo-section">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">
              <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">
                <div class="checkerboard-preview" data-role="logo-preview-box" style="width:115px;height:115px;border-radius:8px;border:1px dashed var(--color-border);display:flex;align-items:center;justify-content:center;overflow:hidden;flex-shrink:0;cursor:pointer" title="คลิกเพื่ออัปโหลดโลโก้ร้าน">
                  <img data-role="logo-preview-img" src="${currentLogoPath ? esc(resolveAssetUrl(currentLogoPath)) : ''}" alt="Store Logo" class="${currentLogoPath ? '' : 'hidden'}" style="max-width:115px;max-height:115px;width:100%;height:100%;object-fit:contain;background:transparent;border:none;box-shadow:none" />
                  <span data-role="logo-empty-label" class="text-tiny text-muted ${currentLogoPath ? 'hidden' : ''}" style="text-align:center;padding:6px">ยังไม่มีโลโก้<br>(No BG 115×115)</span>
                </div>
                <div>
                  <div class="text-body-bold">ส่วน A: โลโก้ร้านสำหรับหน้า Login & Sign Up และหน้าร้าน (Owner Only)</div>
                  <div class="text-small text-muted" style="margin-top:2px">แสดงเป็นพื้นที่ No BG ไร้ขอบ ไร้วงกลม ไร้พื้นหลัง ขนาด 115 × 115 px แบบรักษาสัดส่วน (contain)</div>
                  <div class="text-tiny text-muted" style="margin-top:2px">แนะนำไฟล์ PNG หรือ WEBP พื้นหลังโปร่งใส (รองรับ JPG) ขนาดแนะนำ ≥ 512 × 512 px ไม่เกิน 5 MB (ย่อด้านยาวไม่เกิน 1024 px อัตโนมัติ)</div>
                  <input type="file" accept=".png,.webp,.jpg,.jpeg,image/png,image/webp,image/jpeg" class="hidden" data-role="logo-file-in" />
                  <div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap">
                    <button type="button" class="btn btn-primary btn-sm" data-role="upload-logo-btn">อัปโหลดโลโก้</button>
                    <button type="button" class="btn btn-danger btn-sm" data-role="delete-logo-btn" ${currentLogoPath ? '' : 'disabled'}>ลบโลโก้</button>
                  </div>
                </div>
              </div>
              <button type="button" class="btn btn-outline btn-sm" data-role="preview-login-btn">ดูตัวอย่างหน้า Login & Sign Up</button>
            </div>
          </div>

          <!-- ส่วน B: ตั้งค่าแบนเนอร์ส่วน Login & Sign Up (สูงสุด 7 รูป) -->
          <div class="card-alt" style="padding:14px 16px;margin-bottom:14px" data-role="owner-login-banners-section">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:6px">
              <div>
                <div style="display:flex;align-items:center;gap:8px">
                  <span class="text-body-bold">ส่วน B: แบนเนอร์หน้า Login & Sign Up (สุ่มเปลี่ยนรูปรองเท้าอัตโนมัติ)</span>
                  <span class="pill pill-primary" data-role="login-banner-counter">${loginBanners.length} / ${MAX_LOGIN_BANNERS}</span>
                </div>
                <div class="text-tiny text-muted" style="margin-top:2px">แนะนำไฟล์ PNG พื้นหลังโปร่งใส (ตัดพื้นหลังรองเท้าออก) ด้านยาว ≈ 1000 px สูงสุดไม่เกิน 7 รูป (เลือกเพิ่มหลายไฟล์พร้อมกันได้)</div>
              </div>
              <div style="display:flex;gap:8px;align-items:center">
                <input type="file" multiple accept=".png,.webp,.jpg,.jpeg,image/png,image/webp,image/jpeg" class="hidden" data-role="login-banner-file-in" />
                <button type="button" class="btn btn-primary btn-sm" data-role="add-login-banner-btn" ${loginBanners.length >= MAX_LOGIN_BANNERS ? 'disabled' : ''}>＋ เพิ่มรูป (${loginBanners.length}/${MAX_LOGIN_BANNERS})</button>
              </div>
            </div>
            <div data-role="login-banner-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(165px,1fr));gap:10px;margin-top:10px"></div>
          </div>
        `;
      }
      for (const [key, title, ph, hint] of fields) {
        const val = settings[key] != null ? settings[key] : '';
        html += `
          <div style="margin-bottom:6px">
            <div class="text-small text-muted">${esc(title)}</div>
            <input type="text" class="input" data-skey="${esc(key)}" value="${esc(val)}" placeholder="${esc(ph)}" style="height:34px" />
            ${hint ? `<div class="text-tiny text-muted">${esc(hint)}</div>` : ''}
          </div>
        `;
      }
    });

    html += `
      <div class="text-body-bold" style="margin-top:10px">AI ตอบแชท</div>
      <div style="height:1px;background:var(--color-border);margin:4px 0 8px"></div>
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:12px" class="text-body">
        <input type="checkbox" data-role="ai-enabled" ${settings.ai_enabled !== false && settings.ai_enabled !== '0' ? 'checked' : ''} />
        <span>ให้ AI ตอบแชทแทนเมื่อไม่มีแอดมินออนไลน์</span>
      </label>
      <div style="display:flex;gap:8px">
        <button type="button" class="btn btn-primary btn-md" data-role="save">บันทึกการตั้งค่าร้านทั้งหมด</button>
        <button type="button" class="btn btn-outline btn-md" data-role="cancel">ยกเลิกการแก้ไข</button>
      </div>
    `;
    box.innerHTML = html;
    panelHolder.appendChild(box);

    // ----- ส่วน A: จัดการโลโก้ร้าน (อัปโหลด / ลบ / พรีวิวตารางหมากรุก 115×115) -----
    const logoPreviewBox = box.querySelector('[data-role="logo-preview-box"]');
    const logoPreviewImg = box.querySelector('[data-role="logo-preview-img"]');
    const logoEmptyLbl = box.querySelector('[data-role="logo-empty-label"]');
    const logoFileIn = box.querySelector('[data-role="logo-file-in"]');
    const uploadLogoBtn = box.querySelector('[data-role="upload-logo-btn"]');
    const deleteLogoBtn = box.querySelector('[data-role="delete-logo-btn"]');

    function syncLogoPreview(pathStr) {
      currentLogoPath = (pathStr || '').trim();
      if (currentLogoPath) {
        logoPreviewImg.src = resolveAssetUrl(currentLogoPath);
        logoPreviewImg.classList.remove('hidden');
        logoEmptyLbl.classList.add('hidden');
        deleteLogoBtn.disabled = false;
      } else {
        logoPreviewImg.removeAttribute('src');
        logoPreviewImg.classList.add('hidden');
        logoEmptyLbl.classList.remove('hidden');
        deleteLogoBtn.disabled = true;
      }
    }

    uploadLogoBtn.addEventListener('click', () => logoFileIn.click());
    logoPreviewBox.addEventListener('click', () => logoFileIn.click());

    logoFileIn.addEventListener('change', async () => {
      const file = logoFileIn.files && logoFileIn.files[0];
      logoFileIn.value = '';
      if (!file) return;
      errEl.textContent = '';
      const lower = (file.name || '').toLowerCase();
      if (!ALLOWED_LOGO_BANNER_EXTS.some((ext) => lower.endsWith(ext))) {
        errEl.textContent = 'รองรับเฉพาะไฟล์โลโก้ .png, .webp และ .jpg เท่านั้น';
        return;
      }
      if (file.size > MAX_UPLOAD_BYTES) {
        errEl.textContent = 'ไฟล์โลโก้มีขนาดใหญ่เกิน 5 MB';
        return;
      }
      uploadLogoBtn.disabled = true;
      try {
        const uploadedPath = await api.uploadImage(file, 'logo');
        await api.post('/api/admin/settings/logo', { store_logo_path: uploadedPath });
        syncLogoPreview(uploadedPath);
        noticeEl.textContent = ''; showToast('อัปโหลดและบันทึกโลโก้ร้านเรียบร้อยแล้ว', 'success');
        await router.refresh_shell();
      } catch (err) {
        errEl.textContent = err.message || 'อัปโหลดโลโก้ไม่สำเร็จ';
      } finally {
        uploadLogoBtn.disabled = false;
      }
    });

    deleteLogoBtn.addEventListener('click', async () => {
      if (!currentLogoPath) return;
      errEl.textContent = '';
      deleteLogoBtn.disabled = true;
      try {
        await api.del('/api/admin/settings/logo');
        syncLogoPreview('');
        noticeEl.textContent = ''; showToast('ลบโลโก้ร้านเรียบร้อยแล้ว', 'success');
        await router.refresh_shell();
      } catch (err) {
        errEl.textContent = err.message || 'ลบโลโก้ไม่สำเร็จ';
        deleteLogoBtn.disabled = false;
      }
    });

    box.querySelector('[data-role="preview-login-btn"]').addEventListener('click', () => {
      openLoginPreviewModal(router);
    });

    // ----- ส่วน B: จัดการแบนเนอร์หน้า Login & Sign Up (สูงสุด 7 รูป) -----
    const bannerCounterEl = box.querySelector('[data-role="login-banner-counter"]');
    const bannerFileIn = box.querySelector('[data-role="login-banner-file-in"]');
    const addBannerBtn = box.querySelector('[data-role="add-login-banner-btn"]');
    const bannerGridEl = box.querySelector('[data-role="login-banner-grid"]');

    function renderLoginBannersList() {
      const n = loginBanners.length;
      bannerCounterEl.textContent = `${n} / ${MAX_LOGIN_BANNERS}`;
      addBannerBtn.textContent = `＋ เพิ่มรูป (${n}/${MAX_LOGIN_BANNERS})`;
      addBannerBtn.disabled = n >= MAX_LOGIN_BANNERS;
      bannerGridEl.innerHTML = '';

      if (!n) {
        bannerGridEl.innerHTML = `
          <div class="text-small text-muted" style="grid-column:1/-1;padding:12px;text-align:center;border:1px dashed var(--color-border);border-radius:10px">
            ยังไม่มีรูปแบนเนอร์รองเท้า (0 / 7) — หน้า Login & Sign Up จะแสดงพื้นสีเหลือง + แสง Glow + เงาพื้นโดยไม่มีรูปรองเท้า
          </div>
        `;
        return;
      }

      loginBanners.forEach((b, idx) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.padding = '8px';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.gap = '6px';
        const fname = String(b.file_path || '').split('/').pop() || `banner_${b.id}`;
        card.innerHTML = `
          <div style="position:relative;height:112px;border-radius:10px;background:radial-gradient(circle at 50% 48%, #FFE08A 0%, #FFB600 72%);display:flex;align-items:center;justify-content:center;overflow:hidden">
            <span class="pill pill-secondary" style="position:absolute;top:6px;left:6px;height:20px;font-size:11px">#${idx + 1}</span>
            <img src="${esc(resolveAssetUrl(b.file_path))}" alt="${esc(fname)}" style="max-width:86%;max-height:84%;object-fit:contain;filter:drop-shadow(0 8px 10px rgba(0,0,0,0.28))" />
          </div>
          <div class="text-tiny text-muted" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(fname)}">${esc(fname)}</div>
          <div style="display:flex;gap:4px;justify-content:space-between">
            <div style="display:flex;gap:4px">
              <button type="button" class="btn btn-outline btn-sm" data-role="move-prev" style="height:26px;padding:0 8px" ${idx === 0 ? 'disabled' : ''} title="เลื่อนขึ้น/ซ้าย">◀</button>
              <button type="button" class="btn btn-outline btn-sm" data-role="move-next" style="height:26px;padding:0 8px" ${idx === n - 1 ? 'disabled' : ''} title="เลื่อนลง/ขวา">▶</button>
            </div>
            <button type="button" class="btn btn-danger btn-sm" data-role="del-login-banner" style="height:26px;padding:0 10px">ลบ</button>
          </div>
        `;

        card.querySelector('[data-role="move-prev"]').addEventListener('click', async () => {
          if (idx <= 0) return;
          const ids = loginBanners.map((item) => item.id);
          [ids[idx - 1], ids[idx]] = [ids[idx], ids[idx - 1]];
          try {
            const res = await api.post('/api/admin/login-banners/reorder', { ordered_ids: ids });
            loginBanners = res.items || [];
            state.login_banners = loginBanners;
            renderLoginBannersList();
          } catch (err) {
            errEl.textContent = err.message || '';
          }
        });

        card.querySelector('[data-role="move-next"]').addEventListener('click', async () => {
          if (idx >= loginBanners.length - 1) return;
          const ids = loginBanners.map((item) => item.id);
          [ids[idx], ids[idx + 1]] = [ids[idx + 1], ids[idx]];
          try {
            const res = await api.post('/api/admin/login-banners/reorder', { ordered_ids: ids });
            loginBanners = res.items || [];
            state.login_banners = loginBanners;
            renderLoginBannersList();
          } catch (err) {
            errEl.textContent = err.message || '';
          }
        });

        card.querySelector('[data-role="del-login-banner"]').addEventListener('click', async () => {
          errEl.textContent = '';
          try {
            const res = await api.del(`/api/admin/login-banners/${b.id}`);
            loginBanners = res.items || [];
            state.login_banners = loginBanners;
            noticeEl.textContent = ''; showToast(`ลบรูปแบนเนอร์แล้ว (คงเหลือ ${loginBanners.length} / ${MAX_LOGIN_BANNERS} รูป)`, 'success');
            renderLoginBannersList();
          } catch (err) {
            errEl.textContent = err.message || 'ลบรูปแบนเนอร์ไม่สำเร็จ';
          }
        });

        bannerGridEl.appendChild(card);
      });
    }

    renderLoginBannersList();

    addBannerBtn.addEventListener('click', () => bannerFileIn.click());
    bannerFileIn.addEventListener('change', async () => {
      const files = Array.from(bannerFileIn.files || []);
      bannerFileIn.value = '';
      if (!files.length) return;
      errEl.textContent = '';

      if (loginBanners.length + files.length > MAX_LOGIN_BANNERS) {
        const msg = `สามารถใส่รูปแบนเนอร์หน้า Login & Sign Up ได้สูงสุดไม่เกิน ${MAX_LOGIN_BANNERS} รูป (ปัจจุบันมี ${loginBanners.length} รูป เลือกเพิ่ม ${files.length} รูป — ระบบจะไม่เพิ่มรูปที่เกิน)`;
        errEl.textContent = msg;
        showToast(msg, 'error');
        return;
      }

      for (const f of files) {
        const lower = (f.name || '').toLowerCase();
        if (!ALLOWED_LOGO_BANNER_EXTS.some((ext) => lower.endsWith(ext))) {
          errEl.textContent = `ไฟล์ "${f.name}" ไม่รองรับ (รองรับเฉพาะ .png, .webp, .jpg)`;
          return;
        }
        if (f.size > MAX_UPLOAD_BYTES) {
          errEl.textContent = `ไฟล์ "${f.name}" มีขนาดใหญ่เกิน 5 MB`;
          return;
        }
      }

      addBannerBtn.disabled = true;
      try {
        const uploadedPaths = [];
        for (const f of files) {
          const p = await api.uploadImage(f, 'login_banner');
          uploadedPaths.push(p);
        }
        const res = await api.post('/api/admin/login-banners', { file_paths: uploadedPaths });
        loginBanners = res.items || [];
        state.login_banners = loginBanners;
        noticeEl.textContent = ''; showToast(`เพิ่มรูปแบนเนอร์หน้า Login & Sign Up สำเร็จ (${loginBanners.length} / ${MAX_LOGIN_BANNERS} รูป)`, 'success');
        renderLoginBannersList();
      } catch (err) {
        errEl.textContent = err.message || 'เพิ่มรูปแบนเนอร์ไม่สำเร็จ';
        renderLoginBannersList();
      }
    });

    box.querySelector('[data-role="cancel"]').addEventListener('click', () => renderStoreTab());
    box.querySelector('[data-role="save"]').addEventListener('click', async () => {
      errEl.textContent = '';
      const values = {};
      box.querySelectorAll('[data-skey]').forEach((el) => {
        clearFieldError(el);
        if (el.dataset.skey === 'shop_name') {
          values.shop_name = el.value.trim() ? el.value : '';
        } else {
          values[el.dataset.skey] = el.value.trim();
        }
      });
      if (!values.shop_name) {
        const shopEl = box.querySelector('[data-skey="shop_name"]');
        const msg = 'กรุณาระบุชื่อร้าน';
        setFieldError(shopEl, msg);
        showToast(msg, 'error');
        return;
      }
      values.ai_enabled = box.querySelector('[data-role="ai-enabled"]').checked ? '1' : '0';
      values.store_logo_path = currentLogoPath;
      values.shop_logo_path = currentLogoPath;
      try {
        const saved = await api.put('/api/admin/settings', values);
        if (saved && saved.shop) {
          state.shop = { ...(state.shop || {}), ...saved.shop };
          syncDocumentTitle(saved.shop.shop_name);
        } else {
          state.shop = { ...(state.shop || {}), shop_name: values.shop_name };
          syncDocumentTitle(values.shop_name);
        }
        noticeEl.textContent = '';
        showToast('บันทึกการตั้งค่าร้าน โลโก้ร้าน และแบนเนอร์เรียบร้อยแล้ว (มีผลทันที)', 'success');
        await router.refresh_shell();
      } catch (err) {
        const em = err.message || 'บันทึกการตั้งค่าไม่สำเร็จ';
        errEl.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
    });
  }

  async function renderContactTab() {
    let allSettings = {};
    let staffMsgs = [];
    try {
      const [sRes, mRes] = await Promise.all([
        api.get('/api/admin/settings'),
        api.get('/api/admin/staff-messages', { limit: 20 }),
      ]);
      allSettings = sRes.all || {};
      staffMsgs = mRes || [];
    } catch (err) {
      errEl.textContent = err.message || '';
      return;
    }

    const mapping = {
      owner_phone: allSettings.shop_phone || allSettings.owner_phone || '',
      owner_email: allSettings.shop_email || allSettings.owner_email || '',
      shop_address: allSettings.shop_address || '',
      shop_open_hours: allSettings.shop_hours || allSettings.shop_open_hours || '',
      line_id: allSettings.line_name || allSettings.line_id || '',
      facebook_name: allSettings.facebook_name || '',
      facebook_url: allSettings.facebook_url || '',
      instagram_name: allSettings.instagram_name || '',
      instagram_url: allSettings.instagram_url || '',
      tiktok_name: allSettings.tiktok_name || '',
      tiktok_url: allSettings.tiktok_url || '',
    };

    panelHolder.innerHTML = `
      <div class="card" style="padding:14px 18px;margin-bottom:10px">
        <div class="text-h3">ข้อมูลติดต่อเจ้าของร้าน ที่อยู่หน้าร้าน & ช่องทางโซเชียล (Facebook / LINE / Instagram / TikTok)</div>
        <div class="text-small text-muted" style="margin-bottom:10px">ข้อมูลนี้จะแสดงให้ลูกค้าดูที่ตั้งหน้าร้าน และให้แอดมินกดติดต่อในกรณีฉุกเฉิน</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          ${CONTACT_FIELDS.map(([key, title, ph]) => `
            <div>
              <div class="text-small text-muted">${esc(title)}</div>
              <input type="text" class="input" data-ckey="${esc(key)}" value="${esc(mapping[key] || '')}" placeholder="${esc(ph)}" style="height:34px" />
            </div>
          `).join('')}
        </div>
        <button type="button" class="btn btn-primary btn-md" data-role="save-contact" style="margin-top:10px">บันทึกข้อมูลติดต่อเจ้าของร้าน</button>
      </div>

      <div class="card" style="padding:14px 18px">
        <div class="text-h3" style="margin-bottom:8px">ข้อความด่วนที่แอดมินส่งถึงเจ้าของร้าน</div>
        ${!staffMsgs.length ? `<div class="text-small text-muted">ยังไม่มีข้อความด่วนจากแอดมิน</div>` : staffMsgs.map((m) => `
          <div class="card-alt" style="padding:8px 12px;margin-bottom:6px">
            <div class="text-small-bold">${esc(m.subject)} — จาก ${esc(m.sender_name || m.sender_email || '-')} (${esc(formatDateTime(m.created_at))})</div>
            <div class="text-small" style="margin-top:2px;white-space:pre-line">${esc(m.message || '')}</div>
          </div>
        `).join('')}
      </div>
    `;

    panelHolder.querySelector('[data-role="save-contact"]').addEventListener('click', async () => {
      errEl.textContent = '';
      const payload = {};
      panelHolder.querySelectorAll('[data-ckey]').forEach((el) => {
        payload[el.dataset.ckey] = el.value.trim();
      });
      try {
        await api.put('/api/admin/settings/contact', payload);
        noticeEl.textContent = '';
        showToast('บันทึกข้อมูลติดต่อเจ้าของร้าน ที่ตั้งหน้าร้าน และโซเชียลมีเดียเรียบร้อยแล้ว', 'success');
        await router.refresh_shell();
        await renderContactTab();
      } catch (err) {
        const em = err.message || 'บันทึกข้อมูลติดต่อไม่สำเร็จ';
        errEl.textContent = `⛔ ${em}`;
        showToast(em, 'error');
      }
    });
  }

  async function renderExportTab() {
    const today = new Date();
    const yStr = String(today.getFullYear());
    const mStr = String(today.getMonth() + 1).padStart(2, '0');
    const dStr = String(today.getDate()).padStart(2, '0');
    const yStart = `${yStr}-01-01`;
    const yEnd = `${yStr}-12-31`;
    const mStart = `${yStr}-${mStr}-01`;
    const todayIso = `${yStr}-${mStr}-${dStr}`;

    let sdata = {};
    let expenses = [];
    try {
      const [sRes, eRes] = await Promise.all([
        api.get('/api/admin/settings'),
        api.get('/api/admin/expenses'),
      ]);
      sdata = sRes.all || {};
      expenses = eRes.items || [];
    } catch (e) {}

    panelHolder.innerHTML = `
      <div class="card" style="padding:14px 18px;margin-bottom:10px">
        <div class="text-h3">ส่งออกรายงานรายรับ/รายจ่าย/สินค้า/ลูกค้า เป็นไฟล์ Excel (.xlsx แยกสีรายรับเขียว/รายจ่ายแดง)</div>
        <div class="text-small text-muted" style="margin-bottom:10px">เลือกช่วงวันที่จากปฏิทินได้สูงสุด 1 ปีเต็ม (รวมถึง 1 ม.ค. – 31 ธ.ค.) จัดหน้าสวยงามพร้อมแถวสรุปรวม</div>
        <div style="display:flex;align-items:flex-start;gap:10px;flex-wrap:wrap;margin-bottom:8px">
          <span class="text-small-bold" style="padding-top:8px">ตั้งแต่วันที่:</span>
          <div data-role="exp-start"></div>
          <span class="text-small-bold" style="padding-top:8px">ถึงวันที่:</span>
          <div data-role="exp-end"></div>
          <button type="button" class="btn btn-outline btn-sm" data-role="yr-btn" style="height:38px">ทั้งปี ${yStr} (1 ม.ค.–31 ธ.ค.)</button>
          <button type="button" class="btn btn-outline btn-sm" data-role="mo-btn" style="height:38px">เดือนปัจจุบัน</button>
        </div>
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
          <button type="button" class="btn btn-primary btn-md" data-role="export-now">ส่งออกรายงาน Excel (.xlsx)...</button>
          <span class="text-small-bold" data-role="export-sum"></span>
        </div>
      </div>

      <div class="card" style="padding:14px 18px;margin-bottom:10px">
        <div class="text-h3" style="margin-bottom:6px">ตั้งค่าส่งออกรายงานและสำรองข้อมูลรายเดือนอัตโนมัติ</div>
        <label style="display:flex;align-items:center;gap:8px;cursor:pointer;margin-bottom:8px" class="text-body">
          <input type="checkbox" data-role="auto-exp" ${String(sdata.export_auto_monthly_enabled ?? '1') !== '0' ? 'checked' : ''} />
          <span>ส่งออกรายงาน .xlsx ของเดือนก่อนหน้าอัตโนมัติเมื่อเปิดแอปในเดือนใหม่</span>
        </label>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <span class="text-small-bold">โฟลเดอร์ปลายทาง:</span>
          <input type="text" class="input" data-role="auto-folder" value="${esc(sdata.export_auto_folder || 'data/exports')}" style="width:340px;height:34px" />
          <button type="button" class="btn btn-primary btn-sm" data-role="save-auto">บันทึกตั้งค่าส่งออกอัตโนมัติ</button>
        </div>
      </div>

      <div class="card" style="padding:14px 18px">
        <div class="text-h3" style="margin-bottom:8px">บันทึกรายจ่ายร้านค้า (แสดงเป็นสีแดงอ่อนในรายงานรายรับ/รายจ่าย .xlsx)</div>
        <div style="display:flex;align-items:flex-start;gap:8px;flex-wrap:wrap;margin-bottom:10px">
          <input type="text" class="input" data-role="ex-title" placeholder="รายการรายจ่าย เช่น ค่าเช่าร้าน / ค่ากล่องพัสดุ" style="width:230px;height:38px" />
          <input type="text" class="input" data-role="ex-cat" placeholder="หมวดหมู่ เช่น ค่าเช่า/วัสดุ" style="width:150px;height:38px" />
          <input type="text" class="input" data-role="ex-amt" placeholder="จำนวนเงิน (บาท)" style="width:130px;height:38px" />
          <div data-role="ex-date"></div>
          <button type="button" class="btn btn-danger btn-sm" data-role="add-ex" style="height:38px">＋ เพิ่มรายจ่าย</button>
        </div>
        <div data-role="ex-list" style="display:flex;flex-direction:column;gap:4px"></div>
      </div>
    `;

    const expStart = createDatePickerField({ placeholder: yStart, allowEmpty: false, width: 215 });
    expStart.set(yStart);
    panelHolder.querySelector('[data-role="exp-start"]').appendChild(expStart.el);

    const expEnd = createDatePickerField({ placeholder: yEnd, allowEmpty: false, width: 215 });
    expEnd.set(yEnd);
    panelHolder.querySelector('[data-role="exp-end"]').appendChild(expEnd.el);

    const exDate = createDatePickerField({ placeholder: todayIso, allowEmpty: false, width: 205 });
    exDate.set(todayIso);
    panelHolder.querySelector('[data-role="ex-date"]').appendChild(exDate.el);

    panelHolder.querySelector('[data-role="yr-btn"]').addEventListener('click', () => {
      expStart.set(yStart);
      expEnd.set(yEnd);
    });
    panelHolder.querySelector('[data-role="mo-btn"]').addEventListener('click', () => {
      expStart.set(mStart);
      expEnd.set(todayIso);
    });

    panelHolder.querySelector('[data-role="export-now"]').addEventListener('click', async () => {
      errEl.textContent = '';
      try {
        const res = await api.post('/api/admin/export/xlsx', {
          start_date: expStart.get(),
          end_date: expEnd.get(),
        });
        noticeEl.textContent = ''; showToast(`ส่งออกไฟล์รายงานสำเร็จ: ${res.filename || res.path}`, 'success');
        panelHolder.querySelector('[data-role="export-sum"]').textContent =
          `รายรับรวม ${formatPrice(res.gross_revenue)} | กำไรสุทธิ ${formatPrice(res.net_profit)} | ลูกค้า ${res.customer_count || 0} ราย`;
        if (res.download_url) {
          window.open(res.download_url, '_blank', 'noopener');
        }
      } catch (err) {
        errEl.textContent = err.message || '';
      }
    });

    panelHolder.querySelector('[data-role="save-auto"]').addEventListener('click', async () => {
      try {
        await api.post('/api/admin/export/auto-config', {
          enabled: panelHolder.querySelector('[data-role="auto-exp"]').checked,
          folder_path: panelHolder.querySelector('[data-role="auto-folder"]').value.trim(),
        });
        noticeEl.textContent = ''; showToast('บันทึกการตั้งค่าส่งออกรายเดือนอัตโนมัติแล้ว', 'success');
      } catch (err) {
        errEl.textContent = err.message || '';
      }
    });

    panelHolder.querySelector('[data-role="add-ex"]').addEventListener('click', async () => {
      errEl.textContent = '';
      try {
        const amt = parseMoney(panelHolder.querySelector('[data-role="ex-amt"]').value, 'จำนวนเงินรายจ่าย', { required: true, minimum: 0 });
        await api.post('/api/admin/expenses', {
          spent_on: exDate.get(),
          category: panelHolder.querySelector('[data-role="ex-cat"]').value.trim() || 'ทั่วไป',
          amount: amt,
          note: panelHolder.querySelector('[data-role="ex-title"]').value.trim(),
        });
        await renderExportTab();
      } catch (err) {
        errEl.textContent = err.message || '';
      }
    });

    const exList = panelHolder.querySelector('[data-role="ex-list"]');
    if (!expenses.length) {
      exList.innerHTML = `<div class="text-small text-muted">ยังไม่มีรายการรายจ่ายที่บันทึกไว้</div>`;
    } else {
      for (const r of expenses.slice(0, 15)) {
        const row = document.createElement('div');
        row.className = 'card-alt';
        row.style.padding = '6px 10px';
        row.style.display = 'flex';
        row.style.alignItems = 'center';
        row.style.gap = '10px';
        row.innerHTML = `
          <span class="text-small-bold" style="flex:1">${esc(r.expense_date || r.spent_on)} · [${esc(r.category)}] ${esc(r.title || r.note || '')}</span>
          <span class="text-small-bold text-danger">${esc(formatPrice(r.amount))}</span>
          <button type="button" class="btn btn-danger btn-sm">ลบ</button>
        `;
        row.querySelector('button').addEventListener('click', async () => {
          await api.del(`/api/admin/expenses/${r.id}`);
          await renderExportTab();
        });
        exList.appendChild(row);
      }
    }
  }

  async function renderBannerAuditTab() {
    let banners = [];
    let logs = [];
    try {
      const [bRes, aRes] = await Promise.all([
        api.get('/api/admin/banners'),
        api.get('/api/admin/audit-logs', { page_size: 25 }),
      ]);
      banners = bRes || [];
      logs = (aRes && aRes.items) || [];
    } catch (e) {}

    const editingB = banners.find((b) => b.id === editBannerId) || null;

    panelHolder.innerHTML = `
      <div class="card" style="padding:14px 18px;margin-bottom:10px">
        <div class="text-h3" style="margin-bottom:8px">${editingB ? `แก้ไขแบนเนอร์ #${editingB.id}: ${esc(editingB.title || '')}` : 'จัดการแบนเนอร์สไลด์โชว์หน้าแรก (ใส่ได้ตั้งแต่ 1 – 10 รูป พร้อมปรับแต่งหัวข้อและคำโปรย)'}</div>
        <div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:10px">
          <div data-role="b-picker"></div>
          <div style="flex:1;display:flex;flex-direction:column;gap:6px">
            <input type="text" class="input" data-role="b-title" value="${esc((editingB && editingB.title) || '')}" placeholder="หัวข้อแบนเนอร์ * เช่น ตัวช่วยเลือกไม้ & AI แนะนำไม้แบดคู่ใจ 3 รุ่น" style="height:34px" />
            <input type="text" class="input" data-role="b-sub" value="${esc((editingB && editingB.subtitle) || '')}" placeholder="คำอธิบายเพิ่มเติม เช่น วิเคราะห์ตามระดับฝีมือ สไตล์การเล่น และงบประมาณของคุณ" style="height:34px" />
            <div style="display:flex;gap:6px">
              <button type="button" class="btn btn-primary btn-sm" data-role="b-save">${editingB ? 'บันทึกการแก้ไขแบนเนอร์' : '＋ เพิ่มแบนเนอร์ใหม่'}</button>
              ${editingB ? `<button type="button" class="btn btn-outline btn-sm" data-role="b-cancel">ยกเลิกแก้ไข</button>` : ''}
            </div>
          </div>
        </div>
        <div data-role="b-list" style="display:flex;flex-direction:column;gap:4px"></div>
      </div>

      <div class="card" style="padding:14px 18px">
        <div class="text-h3" style="margin-bottom:8px">บันทึกกิจกรรมผู้ใช้งานและแอดมิน (Audit Log)</div>
        ${!logs.length ? `<div class="text-small text-muted">ยังไม่มีประวัติกิจกรรม</div>` : logs.map((lg) => `
          <div class="card-alt" style="padding:4px 10px;margin-bottom:3px" class="text-tiny">
            [${esc(formatDateTime(lg.created_at))}] ${esc(lg.username || 'system')} (${esc(lg.user_role || lg.actor_role || '-')}) → ${esc(lg.action)} (${esc(lg.target_type || '')}:${esc(lg.target_id || '')}) ${esc(lg.detail || '')}
          </div>
        `).join('')}
      </div>
    `;

    const bPicker = createImagePicker({
      size: [80, 80],
      initialPath: editingB ? editingB.image_path : null,
      allowClear: true,
    });
    panelHolder.querySelector('[data-role="b-picker"]').appendChild(bPicker.el);

    panelHolder.querySelector('[data-role="b-save"]').addEventListener('click', async () => {
      errEl.textContent = '';
      const title = panelHolder.querySelector('[data-role="b-title"]').value.trim();
      const sub = panelHolder.querySelector('[data-role="b-sub"]').value.trim();
      if (!title && !bPicker.getSelectedFile()) {
        errEl.textContent = 'กรุณากรอกหัวข้อแบนเนอร์ หรือเลือกรูปภาพแบนเนอร์';
        return;
      }
      try {
        const payload = { title: title || 'โปรโมชันพิเศษ', subtitle: sub, is_active: true };
        if (bPicker.hasChange()) {
          payload.image_path = (await bPicker.resolveUploadedPath('banner')) || '';
        }
        if (editBannerId) await api.put(`/api/admin/banners/${editBannerId}`, payload);
        else await api.post('/api/admin/banners', payload);
        editBannerId = null;
        await renderBannerAuditTab();
      } catch (err) {
        errEl.textContent = err.message || '';
      }
    });

    const bCan = panelHolder.querySelector('[data-role="b-cancel"]');
    if (bCan) bCan.addEventListener('click', () => { editBannerId = null; renderBannerAuditTab(); });

    const bList = panelHolder.querySelector('[data-role="b-list"]');
    if (!banners.length) {
      bList.innerHTML = `<div class="text-small text-muted">ยังไม่ได้อัปโหลดแบนเนอร์ที่กำหนดเอง (หน้าแรกกำลังแสดงแบนเนอร์มาตรฐานของร้าน — สามารถเพิ่มได้ตั้งแต่ 1 ถึง 10 รูป)</div>`;
    } else {
      banners.forEach((b, idx) => {
        const act = Boolean(b.is_active ?? 1);
        const r = document.createElement('div');
        r.className = 'card-alt';
        r.style.padding = '6px 10px';
        r.style.display = 'flex';
        r.style.alignItems = 'center';
        r.style.gap = '8px';
        r.innerHTML = `
          ${thumbHtml(b.image_path, 42)}
          <div style="flex:1">
            <div class="text-small-bold">#${idx + 1} ${esc(b.title || '-')}</div>
            <div class="text-tiny text-muted">${esc(b.subtitle || '(ไม่มีคำอธิบายรอง)')}</div>
          </div>
          ${pillHtml(act ? 'แสดงอยู่' : 'ซ่อน', act ? 'success' : 'muted')}
          <button type="button" class="btn btn-info btn-sm" data-role="edit">แก้ไข</button>
          <button type="button" class="btn btn-outline btn-sm" data-role="tog">${act ? 'ซ่อน' : 'แสดง'}</button>
          <button type="button" class="btn btn-danger btn-sm" data-role="del">ลบ</button>
        `;
        r.querySelector('[data-role="edit"]').addEventListener('click', () => { editBannerId = b.id; renderBannerAuditTab(); });
        r.querySelector('[data-role="tog"]').addEventListener('click', async () => {
          await api.post(`/api/admin/banners/${b.id}/active`, { active: !act });
          await renderBannerAuditTab();
        });
        r.querySelector('[data-role="del"]').addEventListener('click', async () => {
          const ok = await confirm('ลบแบนเนอร์', 'ต้องการลบแบนเนอร์รายการนี้ใช่หรือไม่?', { danger: true });
          if (!ok) return;
          await api.del(`/api/admin/banners/${b.id}`);
          if (editBannerId === b.id) editBannerId = null;
          await renderBannerAuditTab();
        });
        bList.appendChild(r);
      });
    }
  }

  async function renderBackupTab() {
    let rows = [];
    try {
      rows = await api.get('/api/admin/backups');
    } catch (err) {
      errEl.textContent = err.message || '';
    }

    panelHolder.innerHTML = `
      <div class="card" style="padding:14px 18px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <div class="text-h3">สำรอง / กู้คืนฐานข้อมูล SQLite</div>
          <button type="button" class="btn btn-primary btn-md" data-role="backup-now">สำรองข้อมูลตอนนี้</button>
        </div>
        <div class="text-small text-muted" style="margin-bottom:10px">ไฟล์สำรองเก็บในโฟลเดอร์ data/backups (แยกจากไฟล์รายงาน .xlsx) — การกู้คืนจะสำรองข้อมูลปัจจุบันไว้ให้ก่อนเสมอ</div>
        <div class="admin-table-header" style="grid-template-columns:2fr 1.2fr 100px 180px">
          <span>ไฟล์</span><span>สร้างเมื่อ</span><span>ขนาด</span><span></span>
        </div>
        <div data-role="backup-list"></div>
      </div>
    `;

    panelHolder.querySelector('[data-role="backup-now"]').addEventListener('click', async () => {
      errEl.textContent = '';
      try {
        const res = await api.post('/api/admin/backups');
        noticeEl.textContent = ''; showToast(`สำรองข้อมูลแล้ว: ${res.name}`, 'success');
        await renderBackupTab();
      } catch (err) {
        errEl.textContent = err.message || '';
      }
    });

    const bList = panelHolder.querySelector('[data-role="backup-list"]');
    if (!rows || !rows.length) {
      bList.innerHTML = `<div class="text-body text-muted" style="text-align:center;padding:20px">ยังไม่มีไฟล์สำรอง</div>`;
      return;
    }
    for (const item of rows) {
      const r = document.createElement('div');
      r.className = 'admin-table-row';
      r.style.gridTemplateColumns = '2fr 1.2fr 100px 180px';
      r.innerHTML = `
        <div class="text-small">${esc(item.name || '-')}</div>
        <div class="text-small text-muted">${esc(formatDateTime(item.created_at))}</div>
        <div class="text-small text-muted">${esc(fmtSize(item.size))}</div>
        <div style="display:flex;justify-content:flex-end;gap:6px">
          <a href="/api/admin/backups/${encodeURIComponent(item.name)}/download" class="btn btn-outline btn-sm">ดาวน์โหลด</a>
          <button type="button" class="btn btn-danger btn-sm" data-role="restore">กู้คืน</button>
        </div>
      `;
      r.querySelector('[data-role="restore"]').addEventListener('click', async () => {
        const ok = await confirm(
          'กู้คืนข้อมูล',
          `กู้คืนข้อมูลจากไฟล์\n${item.name}\nใช่ไหม?\n\nข้อมูลปัจจุบันทั้งหมดจะถูกแทนที่ด้วยข้อมูลในไฟล์นี้ (ระบบสำรองข้อมูลปัจจุบันไว้ให้ก่อน)`,
          { confirmText: 'กู้คืนข้อมูล', danger: true }
        );
        if (!ok) return;
        try {
          await api.post('/api/admin/backups/restore', { name: item.name });
          noticeEl.textContent = '';
          showToast('กู้คืนฐานข้อมูลเรียบร้อยแล้ว', 'success');
          await renderBackupTab();
        } catch (err) {
          errEl.textContent = err.message || '';
        }
      });
      bList.appendChild(r);
    }
  }

  await renderCurrentTab();
}
