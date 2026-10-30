// web/js/pages/buyer/profile.js — หน้าโปรไฟล์ของฉัน (ข้อ 3: โหมดอ่านอย่างเดียวเป็นค่าเริ่มต้น กดแก้ไขถึงปลดล็อก + ยืนยันรหัสผ่านปัจจุบันก่อนบันทึก + การ์ดสถิติ 3 สี)
import { api, esc, formatDateThai } from '../../api.js';
import { createImagePicker } from '../../components/image_picker.js';
import { pageTitleHtml } from '../../components/buyer_common.js';
import { iconSvg } from '../../components/icons.js';
import {
  openModal,
  showToast,
  setFieldError,
  clearFieldError,
  clearAllFieldErrors,
  notifyError,
  notifySuccess,
} from '../../components/dialogs.js';

function maskEmailClient(email) {
  const clean = String(email || '').trim().toLowerCase();
  if (!clean.includes('@')) return clean;
  const [local, domain] = clean.split('@');
  const maskedLocal = local.length <= 2 ? `${local.slice(0, 1)}***` : `${local.slice(0, 2)}***`;
  return `${maskedLocal}@${domain}`;
}

export async function render(container, router) {
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  let currentProfile = null;
  let editMode = false;
  let pendingOtpVerifiedEmail = null;
  let emailOtpCooldownLeft = 0;
  let emailOtpCooldownTimer = null;

  wrap.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
      ${pageTitleHtml('👤 โปรไฟล์ของฉัน', 'จัดการข้อมูลบัญชี อีเมล และรหัสผ่านของคุณ')}
      <button type="button" class="btn btn-primary btn-md" data-role="toggle-edit">
        ${iconSvg('edit', 16, '#111318')} <span data-role="toggle-edit-text">แก้ไขข้อมูลของฉัน</span>
      </button>
    </div>

    <div class="card" data-role="profile-card" style="padding:18px 22px;margin-bottom:12px;display:grid;grid-template-columns:160px 1fr;gap:22px;align-items:start">
      <div data-role="avatar-slot"></div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="display:grid;grid-template-columns:160px 1fr;align-items:start;gap:10px">
          <span class="text-small text-muted" style="padding-top:8px">ชื่อผู้ใช้ (Username)</span>
          <div>
            <input type="text" class="input" data-field="username" style="max-width:320px;height:36px" readonly disabled />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:160px 1fr;align-items:start;gap:10px">
          <span class="text-small text-muted" style="padding-top:8px">อีเมล (ต้องยืนยัน OTP)</span>
          <div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <input type="email" class="input" data-field="email" style="width:250px;height:36px" readonly disabled />
              <button type="button" class="btn btn-info btn-sm" data-role="send-email-otp" style="height:36px" disabled>ส่ง OTP ยืนยันอีเมลใหม่</button>
            </div>
          </div>
        </div>

        <div data-role="otp-row" class="hidden" style="margin-left:170px;background:var(--color-blue-soft);border:1px solid var(--color-info);border-radius:8px;padding:8px 12px;display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap">
          <span class="text-small-bold text-info">รหัส OTP 6 หลัก (จากอีเมลใหม่):</span>
          <input type="text" class="input" data-role="email-otp" placeholder="กรอก OTP 6 หลัก" maxlength="6" style="width:140px;height:32px" />
          <span class="text-tiny text-muted" data-role="email-otp-hint">กรอก OTP แล้วกด "บันทึกโปรไฟล์" เพื่อยืนยันพร้อมรหัสผ่านปัจจุบัน</span>
        </div>

        <div style="display:grid;grid-template-columns:160px 1fr;align-items:center;gap:10px">
          <span class="text-small text-muted">ประเภทบัญชี</span>
          <span class="text-body-bold" data-role="role-lbl">-</span>
        </div>

        <div style="display:grid;grid-template-columns:160px 1fr;align-items:center;gap:10px">
          <span class="text-small text-muted">สมัครเมื่อ</span>
          <span class="text-body-bold" data-role="since-lbl">-</span>
        </div>

        <div style="display:grid;grid-template-columns:160px 1fr;align-items:start;gap:10px">
          <span class="text-small text-muted" style="padding-top:8px">ชื่อ-นามสกุล</span>
          <div>
            <input type="text" class="input" data-field="full_name" style="max-width:320px;height:36px" readonly disabled />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:160px 1fr;align-items:start;gap:10px">
          <span class="text-small text-muted" style="padding-top:8px">เบอร์โทรศัพท์</span>
          <div>
            <input type="text" class="input" data-field="phone" style="max-width:320px;height:36px" readonly disabled />
          </div>
        </div>

        <div class="text-small text-danger" data-role="prof-msg" style="min-height:18px;margin-top:2px"></div>
        <div data-role="save-actions" class="hidden" style="display:flex;gap:8px;align-items:center">
          <button type="button" class="btn btn-primary btn-md" data-role="save-prof" style="width:165px" disabled>บันทึกโปรไฟล์</button>
          <button type="button" class="btn btn-outline btn-md" data-role="cancel-prof" style="width:140px">ยกเลิกการแก้ไข</button>
        </div>
      </div>
    </div>

    <!-- T11: การ์ดสถิติ 3 ใบ (เหลือง, ฟ้า, ชมพู) -->
    <div data-role="stats-row" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:12px"></div>

    <!-- เปลี่ยนรหัสผ่าน -->
    <div class="card" data-role="pw-card" style="padding:18px 22px;margin-bottom:12px">
      <div class="text-h3" style="margin-bottom:10px">เปลี่ยนรหัสผ่าน (ยืนยันด้วยรหัสผ่านเดิม)</div>
      <div style="display:flex;flex-direction:column;gap:8px;max-width:380px">
        <div>
          <div class="text-small text-muted">รหัสผ่านเดิม</div>
          <input type="password" class="input" data-pw="old" />
        </div>
        <div>
          <div class="text-small text-muted">รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร)</div>
          <input type="password" class="input" data-pw="new" />
        </div>
        <div>
          <div class="text-small text-muted">ยืนยันรหัสผ่านใหม่</div>
          <input type="password" class="input" data-pw="confirm" />
        </div>
      </div>
      <div class="text-small text-danger" data-role="pw-msg" style="min-height:18px;margin-top:6px"></div>
      <button type="button" class="btn btn-secondary btn-md" data-role="change-pw" style="width:160px;margin-top:6px">เปลี่ยนรหัสผ่าน</button>
    </div>

    <button type="button" class="btn btn-outline btn-md" data-role="logout-btn" style="width:160px">🚪 ออกจากระบบ</button>
  `;

  const avatarPicker = createImagePicker({
    size: [130, 130],
    allowClear: false,
    buttonText: 'เปลี่ยนรูป...',
  });
  wrap.querySelector('[data-role="avatar-slot"]').appendChild(avatarPicker.el);

  const profileCard = wrap.querySelector('[data-role="profile-card"]');
  const toggleEditBtn = wrap.querySelector('[data-role="toggle-edit"]');
  const usernameIn = wrap.querySelector('[data-field="username"]');
  const emailIn = wrap.querySelector('[data-field="email"]');
  const fullNameIn = wrap.querySelector('[data-field="full_name"]');
  const phoneIn = wrap.querySelector('[data-field="phone"]');
  const sendOtpBtn = wrap.querySelector('[data-role="send-email-otp"]');
  const roleLbl = wrap.querySelector('[data-role="role-lbl"]');
  const sinceLbl = wrap.querySelector('[data-role="since-lbl"]');
  const otpRow = wrap.querySelector('[data-role="otp-row"]');
  const emailOtpIn = wrap.querySelector('[data-role="email-otp"]');
  const emailOtpHint = wrap.querySelector('[data-role="email-otp-hint"]');
  const profMsg = wrap.querySelector('[data-role="prof-msg"]');
  const saveActions = wrap.querySelector('[data-role="save-actions"]');
  const saveProfBtn = wrap.querySelector('[data-role="save-prof"]');
  const cancelProfBtn = wrap.querySelector('[data-role="cancel-prof"]');
  const statsRow = wrap.querySelector('[data-role="stats-row"]');
  const pwCard = wrap.querySelector('[data-role="pw-card"]');
  const pwMsg = wrap.querySelector('[data-role="pw-msg"]');

  function updateSendEmailOtpBtnState() {
    if (!editMode) {
      sendOtpBtn.disabled = true;
      return;
    }
    if (emailOtpCooldownLeft > 0) {
      sendOtpBtn.disabled = true;
      sendOtpBtn.textContent = `ขอรหัสใหม่ (${emailOtpCooldownLeft}s)`;
    } else {
      sendOtpBtn.disabled = false;
      sendOtpBtn.textContent = pendingOtpVerifiedEmail ? 'ส่ง OTP ยืนยันอีกครั้ง' : 'ส่ง OTP ยืนยันอีเมลใหม่';
    }
  }

  function startEmailOtpCooldown(seconds = 60) {
    if (emailOtpCooldownTimer) {
      clearInterval(emailOtpCooldownTimer);
      emailOtpCooldownTimer = null;
    }
    emailOtpCooldownLeft = Math.max(0, Math.floor(Number(seconds) || 60));
    updateSendEmailOtpBtnState();
    emailOtpCooldownTimer = setInterval(() => {
      if (!document.body.contains(wrap)) {
        clearInterval(emailOtpCooldownTimer);
        emailOtpCooldownTimer = null;
        return;
      }
      emailOtpCooldownLeft -= 1;
      if (emailOtpCooldownLeft <= 0) {
        emailOtpCooldownLeft = 0;
        clearInterval(emailOtpCooldownTimer);
        emailOtpCooldownTimer = null;
      }
      updateSendEmailOtpBtnState();
    }, 1000);
  }

  function applyEditMode(enabled, restoreValues = false) {
    editMode = Boolean(enabled);
    clearAllFieldErrors(profileCard);
    profMsg.textContent = '';

    if (restoreValues && currentProfile) {
      avatarPicker.setImage(currentProfile.avatar_path);
      usernameIn.value = currentProfile.username || '';
      emailIn.value = currentProfile.email || '';
      fullNameIn.value = currentProfile.full_name || '';
      phoneIn.value = currentProfile.phone || '';
      emailOtpIn.value = '';
      pendingOtpVerifiedEmail = null;
    }

    [usernameIn, emailIn, fullNameIn, phoneIn].forEach((inp) => {
      inp.readOnly = !editMode;
      inp.disabled = !editMode;
    });
    updateSendEmailOtpBtnState();
    avatarPicker.setDisabled(!editMode);

    if (editMode) {
      toggleEditBtn.className = 'btn btn-outline btn-md';
      toggleEditBtn.innerHTML = `<span>ยกเลิกการแก้ไข</span>`;
      saveActions.classList.remove('hidden');
      saveProfBtn.disabled = false;
      setTimeout(() => usernameIn.focus(), 20);
    } else {
      toggleEditBtn.className = 'btn btn-primary btn-md';
      toggleEditBtn.innerHTML = `${iconSvg('edit', 16, '#111318')} <span data-role="toggle-edit-text">แก้ไขข้อมูลของฉัน</span>`;
      saveActions.classList.add('hidden');
      saveProfBtn.disabled = true;
      otpRow.classList.add('hidden');
    }
  }

  toggleEditBtn.addEventListener('click', () => {
    if (editMode) {
      applyEditMode(false, true);
    } else {
      applyEditMode(true, false);
    }
  });

  cancelProfBtn.addEventListener('click', () => {
    applyEditMode(false, true);
  });

  async function loadProfile() {
    try {
      const profile = await api.get('/api/account/profile');
      currentProfile = profile;
      avatarPicker.setImage(profile.avatar_path);
      roleLbl.textContent = profile.role_label || profile.role || '-';
      sinceLbl.textContent = formatDateThai(profile.created_at);
      usernameIn.value = profile.username || '';
      emailIn.value = profile.email || '';
      fullNameIn.value = profile.full_name || '';
      phoneIn.value = profile.phone || '';
      applyEditMode(false, false);

      statsRow.innerHTML = '';
      if (profile.role === 'buyer') {
        statsRow.classList.remove('hidden');
        const stats = [
          ['📦 คำสั่งซื้อ', profile.order_count || 0, 'orders', '#FEF3C7', '#F59E0B', '#92400E'],
          ['📍 ที่อยู่จัดส่ง', profile.address_count || 0, 'addresses', '#E0F2FE', '#0284C7', '#075985'],
          ['♥ รายการโปรด', profile.wishlist_count || 0, 'wishlist', '#FCE7F3', '#E11D48', '#9D174D'],
        ];
        for (const [lbl, cnt, route, bg, border, fg] of stats) {
          const card = document.createElement('div');
          card.style.background = bg;
          card.style.border = `2px solid ${border}`;
          card.style.color = fg;
          card.style.borderRadius = '14px';
          card.style.padding = '12px';
          card.style.textAlign = 'center';
          card.style.cursor = 'pointer';
          card.innerHTML = `
            <div class="text-price-big">${Number(cnt).toLocaleString()}</div>
            <div class="text-body-bold">${esc(lbl)}</div>
            <div class="text-tiny">คลิกเพื่อเปิดดู ›</div>
          `;
          card.addEventListener('click', () => router.show(route));
          statsRow.appendChild(card);
        }
      } else {
        statsRow.classList.add('hidden');
      }
    } catch (err) {
      notifyError(err.message || 'โหลดโปรไฟล์ไม่สำเร็จ', null, profMsg);
    }
  }

  sendOtpBtn.addEventListener('click', async () => {
    if (!editMode || emailOtpCooldownLeft > 0) return;
    clearFieldError(emailIn);
    profMsg.textContent = '';
    const newEmail = emailIn.value.trim().toLowerCase();
    const curEmail = ((currentProfile && currentProfile.email) || '').trim().toLowerCase();
    if (!newEmail) {
      notifyError('กรุณากรอกอีเมลใหม่ที่ต้องการเปลี่ยน', emailIn, profMsg);
      return;
    }
    if (newEmail === curEmail) {
      notifyError('อีเมลใหม่ตรงกับอีเมลปัจจุบันอยู่แล้ว', emailIn, profMsg);
      return;
    }
    sendOtpBtn.disabled = true;
    try {
      const res = await api.post('/api/account/email/request-otp', { new_email: newEmail });
      otpRow.classList.remove('hidden');
      pendingOtpVerifiedEmail = newEmail;
      const masked = res.masked_email || maskEmailClient(res.email || newEmail);
      const msg = res.message || `ส่งรหัสไปที่ ${masked} แล้ว`;
      if (emailOtpHint) {
        emailOtpHint.textContent = `${msg} — กรอกรหัส OTP แล้วกด "บันทึกโปรไฟล์" เพื่อยืนยันพร้อมรหัสผ่านปัจจุบัน`;
      }
      notifySuccess(msg, profMsg);
      startEmailOtpCooldown(res.cooldown_seconds || 60);
      emailOtpIn.focus();
    } catch (err) {
      updateSendEmailOtpBtnState();
      notifyError(err.message || 'ส่งรหัส OTP ไม่สำเร็จ', emailIn, profMsg);
    }
  });

  function mapProfileErrorField(msg) {
    const m = String(msg || '');
    if (m.includes('ชื่อผู้ใช้')) return usernameIn;
    if (m.includes('ชื่อ-นามสกุล')) return fullNameIn;
    if (m.includes('เบอร์โทร')) return phoneIn;
    if (m.includes('OTP')) return emailOtpIn;
    if (m.includes('อีเมล')) return emailIn;
    return null;
  }

  function promptCurrentPasswordAndSave({ newUsername, newFullName, newPhone, newEmail, emailChanged, otpCode, newAvatarFile }) {
    openModal({
      title: 'ยืนยันรหัสผ่านปัจจุบันเพื่อบันทึกการแก้ไข',
      width: 430,
      render(card, close) {
        card.innerHTML = `
          <div class="text-h3" style="margin-bottom:4px">🔒 ยืนยันตัวตนด้วยรหัสผ่านปัจจุบัน</div>
          <div class="text-small text-muted" style="margin-bottom:12px">กรุณากรอกรหัสผ่านปัจจุบันของคุณ 1 ครั้งเพื่อยืนยันการบันทึกข้อมูลโปรไฟล์</div>
          <div>
            <div class="text-small text-muted" style="margin-bottom:4px">รหัสผ่านปัจจุบัน *</div>
            <input type="password" class="input" data-role="confirm-cur-pw" placeholder="กรอกรหัสผ่านปัจจุบัน" autocomplete="current-password" />
          </div>
          <div class="text-small text-danger" data-role="modal-err" style="min-height:18px;margin-top:6px"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px">
            <button type="button" class="btn btn-outline btn-md" data-role="cancel">ยกเลิก</button>
            <button type="button" class="btn btn-primary btn-md" data-role="confirm">ยืนยันและบันทึก</button>
          </div>
        `;
        const pwInput = card.querySelector('[data-role="confirm-cur-pw"]');
        const modalErr = card.querySelector('[data-role="modal-err"]');
        const confirmBtn = card.querySelector('[data-role="confirm"]');
        const cancelBtn = card.querySelector('[data-role="cancel"]');

        const doConfirmSave = async () => {
          clearFieldError(pwInput);
          modalErr.textContent = '';
          const curPw = pwInput.value;
          if (!curPw) {
            notifyError('กรุณากรอกรหัสผ่านปัจจุบันเพื่อยืนยันการแก้ไขโปรไฟล์', pwInput, modalErr);
            pwInput.focus();
            return;
          }

          confirmBtn.disabled = true;
          try {
            await api.put('/api/account/profile', {
              username: newUsername,
              full_name: newFullName,
              phone: newPhone,
              current_password: curPw,
            });

            if (emailChanged) {
              await api.post('/api/account/email/confirm-otp', {
                new_email: newEmail,
                otp_code: otpCode,
                current_password: curPw,
              });
            }

            if (newAvatarFile) {
              const fd = new FormData();
              fd.append('file', newAvatarFile);
              fd.append('current_password', curPw);
              await api.uploadForm('/api/account/avatar', fd);
            }

            close(true);
            await router.refresh_shell();
            await loadProfile();
            notifySuccess('บันทึกข้อมูลโปรไฟล์เรียบร้อยแล้ว');
          } catch (err) {
            confirmBtn.disabled = false;
            const errMsg = err.message || 'บันทึกข้อมูลโปรไฟล์ไม่สำเร็จ';
            if (errMsg.includes('รหัสผ่าน')) {
              notifyError(errMsg, pwInput, modalErr);
              pwInput.select();
              pwInput.focus();
            } else {
              close(false);
              const targetField = mapProfileErrorField(errMsg);
              notifyError(errMsg, targetField, profMsg);
            }
          }
        };

        confirmBtn.addEventListener('click', doConfirmSave);
        pwInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') doConfirmSave();
        });
        cancelBtn.addEventListener('click', () => close(false));
        setTimeout(() => pwInput.focus(), 30);
      },
    });
  }

  saveProfBtn.addEventListener('click', async () => {
    if (!editMode || !currentProfile) return;
    clearAllFieldErrors(profileCard);
    profMsg.textContent = '';

    const newUsername = usernameIn.value.trim();
    const newFullName = fullNameIn.value.trim();
    const newPhone = phoneIn.value.trim().replace(/[-\s]/g, '');
    const newEmail = emailIn.value.trim().toLowerCase();
    const curEmail = String(currentProfile.email || '').trim().toLowerCase();
    const emailChanged = Boolean(newEmail && newEmail !== curEmail);
    const otpCode = emailOtpIn.value.trim();
    const newAvatarFile = avatarPicker.getSelectedFile();

    const unchanged =
      newUsername === String(currentProfile.username || '').trim() &&
      newFullName === String(currentProfile.full_name || '').trim() &&
      newPhone === String(currentProfile.phone || '').trim().replace(/[-\s]/g, '') &&
      !emailChanged &&
      !newAvatarFile;

    if (unchanged) {
      applyEditMode(false, true);
      showToast('ไม่มีข้อมูลที่เปลี่ยนแปลง', 'success');
      return;
    }

    // 1. ตรวจสอบความถูกต้องของช่องข้อมูลฝั่งไคลเอนต์และเซิร์ฟเวอร์ก่อนถามรหัสผ่าน
    if (!newUsername || !/^[a-zA-Z0-9_]{3,30}$/.test(newUsername)) {
      notifyError('รูปแบบชื่อผู้ใช้ไม่ถูกต้อง (อนุญาตเฉพาะภาษาอังกฤษ ตัวเลข และ _ ความยาว 3-30 ตัวอักษร)', usernameIn, profMsg);
      return;
    }
    if (!newFullName) {
      notifyError('กรุณากรอกชื่อ-นามสกุล', fullNameIn, profMsg);
      return;
    }
    if (newPhone && !/^0\d{9}$/.test(newPhone)) {
      notifyError('รูปแบบเบอร์โทรศัพท์ไม่ถูกต้อง (ต้องเป็นตัวเลข 10 หลักและขึ้นต้นด้วย 0)', phoneIn, profMsg);
      return;
    }
    if (emailChanged) {
      otpRow.classList.remove('hidden');
      if (!otpCode || otpCode.length !== 6 || !/^\d{6}$/.test(otpCode)) {
        notifyError("การเปลี่ยนอีเมลต้องกด 'ส่ง OTP ยืนยันอีเมลใหม่' และกรอกรหัส OTP 6 หลักก่อนบันทึก", emailOtpIn, profMsg);
        return;
      }
    }

    try {
      await api.post('/api/account/profile/validate', {
        username: newUsername,
        full_name: newFullName,
        phone: newPhone,
      });
    } catch (err) {
      const targetField = mapProfileErrorField(err.message);
      notifyError(err.message || 'ข้อมูลไม่ถูกต้อง', targetField, profMsg);
      return;
    }

    // 2. เปิดกล่องยืนยันรหัสผ่านปัจจุบัน 1 ครั้งก่อนบันทึก
    promptCurrentPasswordAndSave({
      newUsername,
      newFullName,
      newPhone,
      newEmail,
      emailChanged,
      otpCode,
      newAvatarFile,
    });
  });

  wrap.querySelector('[data-role="change-pw"]').addEventListener('click', async () => {
    clearAllFieldErrors(pwCard);
    pwMsg.textContent = '';
    const oldIn = wrap.querySelector('[data-pw="old"]');
    const newIn = wrap.querySelector('[data-pw="new"]');
    const confirmIn = wrap.querySelector('[data-pw="confirm"]');
    const oldPw = oldIn.value;
    const newPw = newIn.value;
    const confirmPw = confirmIn.value;

    if (!oldPw) {
      notifyError('กรุณากรอกรหัสผ่านเดิม', oldIn, pwMsg);
      return;
    }
    if (!newPw || newPw.length < 8) {
      notifyError('รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 8 ตัวอักษร', newIn, pwMsg);
      return;
    }
    if (newPw !== confirmPw) {
      notifyError('รหัสผ่านใหม่และการยืนยันไม่ตรงกัน', confirmIn, pwMsg);
      return;
    }
    try {
      await api.post('/api/auth/change-password', {
        old_password: oldPw,
        new_password: newPw,
        confirm_password: confirmPw,
      });
      wrap.querySelectorAll('[data-pw]').forEach((el) => { el.value = ''; });
      await router.refresh_shell();
      notifySuccess('เปลี่ยนรหัสผ่านเรียบร้อยแล้ว', pwMsg);
    } catch (err) {
      const msg = err.message || 'เปลี่ยนรหัสผ่านไม่สำเร็จ';
      const targetField = msg.includes('รหัสผ่านเดิม') ? oldIn : newIn;
      notifyError(msg, targetField, pwMsg);
    }
  });

  wrap.querySelector('[data-role="logout-btn"]').addEventListener('click', () => router.logout());

  await loadProfile();
}
