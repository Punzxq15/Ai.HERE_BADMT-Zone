// web/js/components/auth_layout.js — UI หน้า LOGIN & SIGN UP ใหม่ตามดีไซน์ PDF (1456×819 / การ์ดหลัก 1294×657)
import { api, esc, resolveAssetUrl } from '../api.js';
import { openModal, showToast, setFieldError, clearFieldError } from './dialogs.js';
import { state } from '../state.js';

const KEY_ICON_SVG = `<svg width="15" height="12" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><circle cx="5.5" cy="7" r="4" stroke="#111111" stroke-width="2"/><path d="M9.5 7H18.5M15.5 7V10.5M18 7V9.5" stroke="#111111" stroke-width="2" stroke-linecap="round"/></svg>`;

const SHIELD_CHECK_SVG = `<svg width="13" height="14" viewBox="0 0 16 18" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><path d="M8 1.5L2 4V8.5C2 12.6 4.56 16.36 8 17.5C11.44 16.36 14 12.6 14 8.5V4L8 1.5Z" stroke="#111111" stroke-width="1.5" stroke-linejoin="round"/><path d="M5.5 9L7.3 10.8L10.8 7.3" stroke="#111111" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

const MAIL_ICON_SVG = `<svg width="13" height="11" viewBox="0 0 16 13" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><rect x="1" y="1" width="14" height="11" rx="2" stroke="#111111" stroke-width="1.5"/><path d="M1.5 2L8 7L14.5 2" stroke="#111111" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

const BG_WORDS = [
  'BADMINTON',
  'AI.HERE BADM',
  'LEGEND',
  'WELCOME',
  'BAD ZONE',
];

function maskEmailClient(email) {
  const clean = String(email || '').trim().toLowerCase();
  if (!clean.includes('@')) return clean;
  const [local, domain] = clean.split('@');
  const maskedLocal = local.length <= 2 ? `${local.slice(0, 1)}***` : `${local.slice(0, 2)}***`;
  return `${maskedLocal}@${domain}`;
}

function buildDiagonalBgHtml() {
  const rows = [];
  const numRows = 22;
  const wordsPerHalf = 14;
  for (let r = 0; r < numRows; r++) {
    const seq = [];
    let prev = '';
    for (let i = 0; i < wordsPerHalf; i++) {
      const choices = BG_WORDS.filter((w) => w !== prev);
      const pick = choices[Math.floor(Math.random() * choices.length)];
      seq.push(pick);
      prev = pick;
    }
    const halfText = seq.map((w) => `<span class="auth2-bg-word">${w}</span>`).join('');
    const dirClass = r % 2 === 0 ? 'auth2-bg-track-up' : 'auth2-bg-track-down';
    rows.push(
      `<div class="auth2-bg-row"><div class="auth2-bg-track ${dirClass}"><div class="auth2-bg-half">${halfText}</div><div class="auth2-bg-half">${halfText}</div></div></div>`
    );
  }
  return `<div class="auth2-bg-pattern" data-role="bg-pattern" aria-hidden="true"><div class="auth2-bg-rotator">${rows.join('')}</div></div>`;
}

export function renderAuthExperience(container, router, {
  initialMode = 'login',
  params = {},
} = {}) {
  container.innerHTML = '';

  let mode = initialMode === 'signup' || initialMode === 'register' ? 'signup' : 'login';
  let isAnimating = false;
  let otpPendingEmail = null;
  let signupCooldownRemaining = 0;
  let signupCooldownInterval = null;
  const timers = [];

  // Stage 1456×819 reference with automatic proportional scaling
  const stage = document.createElement('div');
  stage.className = 'auth2-stage';
  stage.dataset.mode = mode;

  stage.innerHTML = `
    ${buildDiagonalBgHtml()}
    <div class="auth2-scale-shell" data-role="scale-shell">
      <div class="auth2-main-card" data-role="main-card" data-mode="${mode}">

        <!-- แบรนด์มุมบนขวา (แสดงเฉพาะหน้า LOGIN) -->
        <div class="auth2-brand-corner" data-role="brand-corner">
          <span>AI.HERE Bad</span><span class="auth2-m-circle">M</span><span>-Zone</span>
        </div>

        <!-- โซนฟอร์ม LOGIN (ฝั่งขวา x: 647..1294) -->
        <div class="auth2-zone-login" data-role="zone-login">
          <div class="auth2-logo-box auth2-logo-login" data-role="logo-login"></div>

          <div class="auth2-login-card" data-role="login-card">
            <div class="auth2-card-notice hidden" data-role="login-notice"></div>

            <div class="auth2-title" style="top:22px;left:18px">เข้าสู่ระบบ</div>
            <div class="auth2-subtitle" style="top:50px;left:18px">เข้าสู่ระบบเพื่อสั่งซื้อสินค้า เก็บคูปอง ส่วนลด และติดตามสถานะพัสดุ</div>

            <label class="auth2-label" style="top:84px;left:18px">ชื่อผู้ใช้ หรือ อีเมล</label>
            <input type="text" class="auth2-input" data-role="identifier" autocomplete="username" style="top:102px;left:18px;width:414px;height:33px" />

            <label class="auth2-label" style="top:164px;left:18px">รหัสผ่าน</label>
            <input type="password" class="auth2-input" data-role="password" autocomplete="current-password" style="top:182px;left:18px;width:414px;height:33px" />

            <div class="auth2-help-row" style="top:225px;left:18px;width:414px">
              <button type="button" class="auth2-link-btn" data-role="forgot-otp">
                ${KEY_ICON_SVG}
                <span>ลืมรหัสผ่าน? (รับรหัส OTP)</span>
              </button>
              <button type="button" class="auth2-link-btn" data-role="owner-contact">
                ${SHIELD_CHECK_SVG}
                <span>แอดมินลืมรหัส / ติดต่อเจ้าของ</span>
              </button>
            </div>

            <div class="auth2-floating-err" data-role="login-error" style="top:246px;left:18px;width:414px"></div>

            <button type="button" class="auth2-btn auth2-btn-yellow" data-role="login-btn" style="top:269px;left:18px;width:414px;height:34px">ยืนยัน</button>
            <button type="button" class="auth2-btn auth2-btn-red" data-role="go-signup-btn" style="top:314px;left:18px;width:414px;height:34px">ยังไม่มีบัญชี? สมัครสมาชิกใหม่</button>
            <button type="button" class="auth2-btn auth2-btn-outline" data-role="guest-btn" style="top:359px;left:18px;width:414px;height:34px">เข้าชมสินค้าในร้านโดยไม่ล็อกอิน</button>
          </div>
        </div>

        <!-- โซนฟอร์ม SIGN UP (ฝั่งซ้าย x: 0..647, เลื่อนขึ้นลงได้) -->
        <div class="auth2-zone-signup" data-role="zone-signup">
          <div class="auth2-signup-scroll-inner">
            <div class="auth2-logo-box auth2-logo-signup" data-role="logo-signup"></div>

            <div class="auth2-signup-card" data-role="signup-card">
              <div class="auth2-title" style="top:24px;left:18px">สมัครสมาชิกใหม่</div>
              <div class="auth2-subtitle" style="top:54px;left:18px">กรอกข้อมูลบัญชี และยืนยัน OTP เพื่อสมัครบัญชี</div>

              <div class="auth2-sec-title" style="top:80px;left:18px;font-size:13px">กรอกข้อมูลบัญชี</div>

              <label class="auth2-label" style="top:102px;left:18px">ชื่อผู้ใช้ (Username) *</label>
              <input type="text" class="auth2-input" data-field="username" autocomplete="off" style="top:117px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:159px;left:18px">อีเมล (E-mail) *</label>
              <input type="email" class="auth2-input" data-field="email" autocomplete="off" style="top:174px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:216px;left:18px">ชื่อ-นามสกุล *</label>
              <input type="text" class="auth2-input" data-field="full_name" autocomplete="off" style="top:231px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:273px;left:18px">เบอร์โทรศัพท์มือถือ</label>
              <input type="tel" class="auth2-input" data-field="phone" autocomplete="off" style="top:288px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:331px;left:18px">รหัสผ่าน (อย่างน้อย 8 ตัวอักษร) *</label>
              <input type="password" class="auth2-input" data-field="password" autocomplete="new-password" style="top:346px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:389px;left:18px">ยืนยันรหัสผ่านอีกครั้ง *</label>
              <input type="password" class="auth2-input" data-field="confirm" autocomplete="new-password" style="top:404px;left:18px;width:415px;height:34px" />

              <div class="auth2-sec-title" style="top:472px;left:18px;font-size:14px">ที่อยู่จัดส่งเริ่มต้น (แก้ไขหรือเพิ่มภายหลังได้)</div>

              <label class="auth2-label" style="top:496px;left:18px">บ้านเลขที่ / ซอย / ถนน</label>
              <input type="text" class="auth2-input" data-field="address_line" autocomplete="off" style="top:511px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:553px;left:18px">เขต / อำเภอ</label>
              <input type="text" class="auth2-input" data-field="district" autocomplete="off" style="top:568px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:610px;left:18px">จังหวัด</label>
              <input type="text" class="auth2-input" data-field="province" autocomplete="off" style="top:625px;left:18px;width:415px;height:34px" />

              <label class="auth2-label" style="top:667px;left:18px">รหัสไปรษณีย์</label>
              <input type="text" class="auth2-input" data-field="postcode" autocomplete="off" style="top:682px;left:18px;width:415px;height:34px" />

              <!-- กล่อง OTP (732→809) -->
              <div class="auth2-otp-box" style="top:732px;left:18px;width:415px;height:77px">
                <div class="auth2-otp-title">ยืนยันอีเมลด้วยรหัส OTP</div>
                <div class="auth2-otp-mid">
                  <button type="button" class="auth2-otp-send-btn" data-role="send-otp">
                    ${MAIL_ICON_SVG}
                    <span data-role="send-otp-text">ส่งรหัส OTP ไปที่อีเมล</span>
                  </button>
                  <input type="text" class="auth2-otp-input" data-role="otp" maxlength="6" />
                </div>
                <div class="auth2-otp-hint" data-role="otp-hint">กด “ส่งรหัส OTP ไปที่อีเมล” จากนั้นนำรหัส 6 หลักมากรอกเพื่อยืนยันอีเมล</div>
              </div>

              <div class="auth2-floating-err" data-role="signup-error" style="top:816px;left:18px;width:415px"></div>

              <button type="button" class="auth2-btn auth2-btn-red" data-role="verify-btn" style="top:842px;left:18px;width:415px;height:34px">ยืนยันรหัส OTP และสร้างบัญชีสมาชิก</button>
              <button type="button" class="auth2-btn auth2-btn-outline" data-role="back-login-btn" style="top:887px;left:18px;width:415px;height:34px">มีบัญชีอยู่แล้ว? กลับไปหน้าเข้าสู่ระบบ</button>
            </div>
          </div>
        </div>

        <!-- โซนแบนเนอร์สีเหลือง (647 × 657) ไม่เลื่อนตาม scroll -->
        <div class="auth2-banner-zone" data-role="banner-zone">
          <div class="auth2-banner-glow"></div>
          <div class="auth2-ground-shadow-oval" data-role="shoe-oval-shadow"></div>
          <div class="auth2-shoe-stage" data-role="shoe-stage">
            <img class="auth2-shoe-img auth2-shoe-float hidden" data-role="shoe-img-a" alt="" draggable="false" />
            <img class="auth2-shoe-img auth2-shoe-float hidden" data-role="shoe-img-b" alt="" draggable="false" />
          </div>
        </div>

        <!-- ปุ่มสลับ LOGIN / SIGN UP (Pill) กึ่งกลางรอยต่อ (517→777, 67→127) คำไม่สลับฝั่ง เปลี่ยนเฉพาะสีพื้นหลัง -->
        <div class="auth2-pill" data-role="pill">
          <button type="button" class="auth2-pill-half auth2-pill-left" data-role="pill-left">
            <span data-role="pill-left-text">SIGN UP</span>
          </button>
          <button type="button" class="auth2-pill-half auth2-pill-right" data-role="pill-right">
            <span data-role="pill-right-text">LOGIN</span>
          </button>
        </div>
      </div>
    </div>
  `;

  container.appendChild(stage);

  const scaleShell = stage.querySelector('[data-role="scale-shell"]');
  const mainCard = stage.querySelector('[data-role="main-card"]');
  const zoneSignup = stage.querySelector('[data-role="zone-signup"]');
  const pillLeft = stage.querySelector('[data-role="pill-left"]');
  const pillRight = stage.querySelector('[data-role="pill-right"]');
  const logoLogin = stage.querySelector('[data-role="logo-login"]');
  const logoSignup = stage.querySelector('[data-role="logo-signup"]');
  const shoeImgA = stage.querySelector('[data-role="shoe-img-a"]');
  const shoeImgB = stage.querySelector('[data-role="shoe-img-b"]');

  function updateScale() {
    const vw = window.innerWidth || 1456;
    const vh = window.innerHeight || 819;
    const sx = vw / 1456;
    const sy = vh / 819;
    const s = Math.max(0.55, Math.min(sx, sy, 1.45));
    scaleShell.style.setProperty('--auth-scale', s.toFixed(4));
  }
  updateScale();
  window.addEventListener('resize', updateScale);

  function renderStoreLogo(logoPath) {
    const clean = (logoPath || '').trim();
    [logoLogin, logoSignup].forEach((box) => {
      box.innerHTML = '';
      if (!clean) return;
      const img = document.createElement('img');
      img.className = 'auth2-logo-img';
      img.src = resolveAssetUrl(clean, '');
      img.alt = 'Store Logo';
      img.draggable = false;
      img.addEventListener('error', () => {
        img.remove();
      });
      box.appendChild(img);
    });
  }

  let bannerFiles = [];
  let currentBannerIdx = -1;
  let activeShoeSlot = 'a';
  let rotateIntervalId = null;
  let shoeLeaveTimer = null;
  let showcaseSeconds = 5;

  function showShoeImage(filePath, animate = true) {
    if (shoeLeaveTimer) {
      clearTimeout(shoeLeaveTimer);
      shoeLeaveTimer = null;
    }
    const incoming = activeShoeSlot === 'a' ? shoeImgB : shoeImgA;
    const outgoing = activeShoeSlot === 'a' ? shoeImgA : shoeImgB;

    const ovalShadow = stage.querySelector('[data-role="shoe-oval-shadow"]');
    if (!filePath) {
      shoeImgA.classList.add('hidden');
      shoeImgB.classList.add('hidden');
      shoeImgA.removeAttribute('src');
      shoeImgB.removeAttribute('src');
      if (ovalShadow) ovalShadow.classList.add('hidden');
      return;
    }
    if (ovalShadow) ovalShadow.classList.remove('hidden');

    const url = resolveAssetUrl(filePath, '');
    incoming.src = url;
    incoming.classList.remove('hidden', 'auth2-shoe-leave');
    if (animate && !outgoing.classList.contains('hidden')) {
      incoming.classList.add('auth2-shoe-enter');
      outgoing.classList.remove('auth2-shoe-enter');
      outgoing.classList.add('auth2-shoe-leave');
      shoeLeaveTimer = setTimeout(() => {
        outgoing.classList.add('hidden');
        outgoing.classList.remove('auth2-shoe-leave');
        incoming.classList.remove('auth2-shoe-enter');
        shoeLeaveTimer = null;
      }, 700);
      timers.push(shoeLeaveTimer);
    } else {
      outgoing.classList.add('hidden');
      outgoing.classList.remove('auth2-shoe-leave');
      incoming.classList.remove('auth2-shoe-enter');
    }
    activeShoeSlot = activeShoeSlot === 'a' ? 'b' : 'a';
  }

  function pickNextRandomBanner(animate = true) {
    if (!bannerFiles.length) {
      currentBannerIdx = -1;
      showShoeImage(null, false);
      return;
    }
    if (bannerFiles.length === 1) {
      if (currentBannerIdx !== 0) {
        currentBannerIdx = 0;
        showShoeImage(bannerFiles[0], animate);
      }
      return;
    }
    const candidates = [];
    for (let i = 0; i < bannerFiles.length; i++) {
      if (i !== currentBannerIdx) candidates.push(i);
    }
    const nextIdx = candidates[Math.floor(Math.random() * candidates.length)];
    currentBannerIdx = nextIdx;
    showShoeImage(bannerFiles[nextIdx], animate);
  }

  function startBannerRotation(seconds = 5) {
    showcaseSeconds = Math.max(5, Number(seconds || 5));
    if (rotateIntervalId) {
      clearInterval(rotateIntervalId);
      rotateIntervalId = null;
    }
    if (bannerFiles.length < 2) return;
    const ms = showcaseSeconds * 1000;
    rotateIntervalId = setInterval(() => {
      if (!document.body.contains(stage)) {
        clearInterval(rotateIntervalId);
        return;
      }
      pickNextRandomBanner(true);
    }, ms);
    timers.push(rotateIntervalId);
  }

  (async () => {
    const initialShop = state.shop || {};
    const initialLogo = initialShop.store_logo_path || initialShop.shop_logo_path || '';
    renderStoreLogo(initialLogo);

    if (Array.isArray(state.login_banners) && state.login_banners.length) {
      bannerFiles = state.login_banners
        .map((b) => (typeof b === 'string' ? b : b.file_path))
        .filter(Boolean)
        .slice(0, 7);
      if (bannerFiles.length) {
        currentBannerIdx = mode === 'signup' && bannerFiles.length > 1 ? 1 : 0;
        showShoeImage(bannerFiles[currentBannerIdx], false);
      }
    }

    try {
      const cfg = await api.get('/api/auth/ui-config');
      if (!document.body.contains(stage)) return;
      renderStoreLogo(cfg.store_logo_path || cfg.shop_logo_path || '');
      const fetched = Array.isArray(cfg.login_banners)
        ? cfg.login_banners.map((b) => (typeof b === 'string' ? b : b.file_path)).filter(Boolean).slice(0, 7)
        : [];
      const changed = JSON.stringify(fetched) !== JSON.stringify(bannerFiles);
      bannerFiles = fetched;
      if (!bannerFiles.length) {
        showShoeImage(null, false);
      } else if (changed || currentBannerIdx < 0) {
        currentBannerIdx = mode === 'signup' && bannerFiles.length > 1 ? 1 : 0;
        showShoeImage(bannerFiles[currentBannerIdx], false);
      }
      startBannerRotation(cfg.login_showcase_seconds || 5);
    } catch (e) {
      startBannerRotation(5);
    }
  })();

  function switchMode(targetMode) {
    if (targetMode === mode) return;
    mode = targetMode;

    if (mode === 'signup') {
      zoneSignup.scrollTop = 0;
    }

    stage.dataset.mode = mode;
    mainCard.dataset.mode = mode;

    if (bannerFiles.length >= 2) {
      pickNextRandomBanner(true);
      startBannerRotation(showcaseSeconds);
    }

    const nextRoute = mode === 'signup' ? 'register' : 'login';
    state.current_page = nextRoute;
    const targetHash = `#/${nextRoute}`;
    if (window.location.hash !== targetHash) {
      try {
        window.history.replaceState(null, '', targetHash);
      } catch (e) {}
    }
  }

  pillLeft.addEventListener('click', () => {
    switchMode('signup');
  });
  pillRight.addEventListener('click', () => {
    switchMode('login');
  });

  stage.querySelector('[data-role="go-signup-btn"]').addEventListener('click', () => switchMode('signup'));
  stage.querySelector('[data-role="back-login-btn"]').addEventListener('click', () => switchMode('login'));

  const idIn = stage.querySelector('[data-role="identifier"]');
  const pwIn = stage.querySelector('[data-role="password"]');
  const loginErrEl = stage.querySelector('[data-role="login-error"]');
  const loginNoticeEl = stage.querySelector('[data-role="login-notice"]');
  const loginBtn = stage.querySelector('[data-role="login-btn"]');

  function showLoginNotice(txt, kind = 'success') {
    if (!txt) {
      loginNoticeEl.classList.add('hidden');
      loginNoticeEl.textContent = '';
      return;
    }
    loginNoticeEl.textContent = String(txt);
    loginNoticeEl.dataset.kind = kind;
    loginNoticeEl.classList.remove('hidden');
  }

  if (params.registered_message) {
    showLoginNotice(params.registered_message, 'success');
  } else if (params.info_message) {
    showLoginNotice(params.info_message, 'info');
  }

  async function handleLogin() {
    const identifier = idIn.value.trim();
    const password = pwIn.value;
    loginErrEl.textContent = '';
    if (!identifier || !password) {
      const msg = 'กรุณากรอกชื่อผู้ใช้และรหัสผ่านให้ครบถ้วน';
      loginErrEl.textContent = msg;
      showToast(msg, 'error');
      return;
    }
    loginBtn.disabled = true;
    try {
      await api.post('/api/auth/login', { identifier, password });
      showToast('เข้าสู่ระบบสำเร็จ', 'success');
      await router.after_login_success();
    } catch (err) {
      const em = err.message || 'เข้าสู่ระบบไม่สำเร็จ';
      loginErrEl.textContent = em;
      showToast(em, 'error');
    } finally {
      loginBtn.disabled = false;
    }
  }

  loginBtn.addEventListener('click', handleLogin);
  idIn.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleLogin(); });
  pwIn.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleLogin(); });

  stage.querySelector('[data-role="guest-btn"]').addEventListener('click', async () => {
    try { await api.post('/api/auth/guest'); } catch (e) {}
    await api.refreshSession();
    router.show('home');
  });

  stage.querySelector('[data-role="forgot-otp"]').addEventListener('click', () => {
    openForgotPasswordDialog((msg) => showLoginNotice(msg, 'success'));
  });

  stage.querySelector('[data-role="owner-contact"]').addEventListener('click', () => {
    openOwnerContactDialog();
  });

  const otpIn = stage.querySelector('[data-role="otp"]');
  const otpHint = stage.querySelector('[data-role="otp-hint"]');
  const signupErrEl = stage.querySelector('[data-role="signup-error"]');
  const sendOtpBtn = stage.querySelector('[data-role="send-otp"]');
  const sendOtpTextEl = stage.querySelector('[data-role="send-otp-text"]');
  const verifyBtn = stage.querySelector('[data-role="verify-btn"]');

  function startSignupOtpCooldown(seconds = 60) {
    if (signupCooldownInterval) {
      clearInterval(signupCooldownInterval);
      signupCooldownInterval = null;
    }
    signupCooldownRemaining = Math.max(0, Math.floor(Number(seconds) || 60));
    const updateBtn = () => {
      if (!document.body.contains(stage)) {
        clearInterval(signupCooldownInterval);
        signupCooldownInterval = null;
        return;
      }
      if (signupCooldownRemaining > 0) {
        sendOtpBtn.disabled = true;
        if (sendOtpTextEl) {
          sendOtpTextEl.textContent = `ขอรหัสใหม่ (${signupCooldownRemaining}s)`;
        }
      } else {
        sendOtpBtn.disabled = false;
        if (sendOtpTextEl) {
          sendOtpTextEl.textContent = otpPendingEmail ? 'ส่งรหัส OTP อีกครั้ง' : 'ส่งรหัส OTP ไปที่อีเมล';
        }
        if (signupCooldownInterval) {
          clearInterval(signupCooldownInterval);
          signupCooldownInterval = null;
        }
      }
    };
    updateBtn();
    signupCooldownInterval = setInterval(() => {
      signupCooldownRemaining -= 1;
      updateBtn();
    }, 1000);
    timers.push(signupCooldownInterval);
  }

  function getSignupValues() {
    const out = {};
    stage.querySelectorAll('[data-field]').forEach((el) => {
      out[el.dataset.field] = el.value;
    });
    return out;
  }

  function validateSignupFields(v) {
    if (!v.username.trim()) return 'กรุณากรอกชื่อผู้ใช้ (Username)';
    if (!/^[a-zA-Z0-9_]+$/.test(v.username.trim())) return 'ชื่อผู้ใช้ใช้ได้เฉพาะภาษาอังกฤษ ตัวเลข และ _ (ห้ามเว้นวรรค)';
    if (!v.email.trim()) return 'กรุณากรอกอีเมล (E-mail)';
    if (!v.full_name.trim()) return 'กรุณากรอกชื่อ-นามสกุล';
    if (v.phone.trim()) {
      const digits = v.phone.trim().replace(/[\s-]/g, '');
      if (!/^0\d{9}$/.test(digits)) return 'เบอร์โทรศัพท์ไม่ถูกต้อง: ต้องขึ้นต้นด้วย 0 และเป็นตัวเลข 10 หลัก';
    }
    if (!v.password) return 'กรุณากรอกรหัสผ่าน';
    if (v.password.length < 8) return 'รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร';
    if (v.password !== v.confirm) return 'รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน';

    const anyAddr = v.address_line.trim() || v.district.trim() || v.province.trim() || v.postcode.trim();
    if (anyAddr) {
      if (!v.address_line.trim()) return 'ที่อยู่จัดส่ง: กรุณากรอกบ้านเลขที่ / ซอย / ถนนให้ครบถ้วน';
      if (v.address_line.trim().length < 4) return 'ที่อยู่จัดส่ง: บ้านเลขที่ / ซอย / ถนนสั้นเกินไป (อย่างน้อย 4 ตัวอักษร)';
      if (!v.district.trim()) return 'ที่อยู่จัดส่ง: กรุณากรอกเขต / อำเภอ';
      if (!v.province.trim()) return 'ที่อยู่จัดส่ง: กรุณากรอกจังหวัด';
      if (!v.postcode.trim()) return 'ที่อยู่จัดส่ง: กรุณากรอกรหัสไปรษณีย์ 5 หลัก';
      if (!/^\d{5}$/.test(v.postcode.trim())) return 'ที่อยู่จัดส่ง: รหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลักพอดี (เช่น 10110)';
    }
    return '';
  }

  // Real-time feedback when typing shipping address or account fields on Sign Up
  stage.querySelectorAll('[data-field]').forEach((el) => {
    el.addEventListener('input', () => {
      const f = el.dataset.field;
      const val = el.value.trim();
      if (f === 'postcode' && val && !/^\d{5}$/.test(val)) {
        signupErrEl.textContent = /^\d+$/.test(val)
          ? `รหัสไปรษณีย์ต้องมี 5 หลัก (ขณะนี้ ${val.length} หลัก)`
          : 'รหัสไปรษณีย์ต้องเป็นตัวเลข 0-9 เท่านั้น';
        el.style.borderColor = '#E63946';
      } else if (f === 'phone' && val && !/^0\d{9}$/.test(val.replace(/[\s-]/g, ''))) {
        signupErrEl.textContent = 'เบอร์โทรศัพท์ต้องขึ้นต้นด้วย 0 และเป็นตัวเลข 10 หลัก';
        el.style.borderColor = '#E63946';
      } else if (f === 'address_line' && val && val.length < 4) {
        signupErrEl.textContent = 'บ้านเลขที่ / ซอย / ถนนสั้นเกินไป (อย่างน้อย 4 ตัวอักษร)';
        el.style.borderColor = '#E63946';
      } else {
        el.style.borderColor = '';
        signupErrEl.textContent = '';
      }
    });
  });

  sendOtpBtn.addEventListener('click', async () => {
    if (signupCooldownRemaining > 0) return;
    const v = getSignupValues();
    signupErrEl.textContent = '';
    const vErr = validateSignupFields(v);
    if (vErr) {
      signupErrEl.textContent = vErr;
      showToast(vErr, 'error');
      return;
    }
    sendOtpBtn.disabled = true;
    try {
      const res = await api.post('/api/auth/register/start', {
        username: v.username.trim(),
        email: v.email.trim(),
        password: v.password,
        full_name: v.full_name.trim(),
        phone: v.phone.trim(),
        address_line: v.address_line.trim(),
        district: v.district.trim(),
        province: v.province.trim(),
        postcode: v.postcode.trim(),
      });
      otpPendingEmail = v.email.trim().toLowerCase();
      const masked = res.masked_email || maskEmailClient(otpPendingEmail);
      const hint = `ส่งรหัสไปที่ ${masked} แล้ว (อายุรหัส ${res.expires_in_minutes || 10} นาที)`;
      otpHint.textContent = hint;
      otpHint.style.color = '#15803D';
      otpHint.style.fontWeight = '700';
      showToast(`ส่งรหัสไปที่ ${masked} แล้ว`, 'success');
      startSignupOtpCooldown(res.cooldown_seconds || 60);
      otpIn.focus();
    } catch (err) {
      const em = err.message || 'ส่งรหัส OTP ไม่สำเร็จ';
      signupErrEl.textContent = em;
      showToast(em, 'error');
      sendOtpBtn.disabled = false;
    }
  });

  async function handleSignupVerify() {
    const v = getSignupValues();
    signupErrEl.textContent = '';
    const vErr = validateSignupFields(v);
    if (vErr) {
      signupErrEl.textContent = vErr;
      showToast(vErr, 'error');
      return;
    }
    const otpCode = otpIn.value.trim();
    const email = (otpPendingEmail || v.email || '').trim();
    if (!otpCode) {
      const msg = 'กรุณากด “ส่งรหัส OTP ไปที่อีเมล” และกรอกรหัส 6 หลักก่อนยืนยัน';
      signupErrEl.textContent = msg;
      showToast(msg, 'error');
      return;
    }
    verifyBtn.disabled = true;
    try {
      await api.post('/api/auth/register/verify', { email, otp_code: otpCode });
      const msg = `สมัครสมาชิกและยืนยันอีเมล (${email}) สำเร็จแล้ว! กรุณาเข้าสู่ระบบ`;
      showLoginNotice(msg, 'success');
      showToast(msg, 'success');
      idIn.value = v.username.trim() || email;
      pwIn.value = '';
      switchMode('login');
    } catch (err) {
      const em = err.message || 'ยืนยัน OTP ไม่สำเร็จ';
      signupErrEl.textContent = em;
      showToast(em, 'error');
    } finally {
      verifyBtn.disabled = false;
    }
  }

  verifyBtn.addEventListener('click', handleSignupVerify);
  otpIn.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleSignupVerify(); });

  return () => {
    window.removeEventListener('resize', updateScale);
    if (rotateIntervalId) clearInterval(rotateIntervalId);
    if (signupCooldownInterval) clearInterval(signupCooldownInterval);
    timers.forEach((t) => { clearTimeout(t); clearInterval(t); });
  };
}

export function renderAuthSplitPage(container, router, options = {}) {
  return renderAuthExperience(container, router, options);
}

function openForgotPasswordDialog(onResetSuccess) {
  let resetCooldownTimer = null;
  openModal({
    title: 'ลืมรหัสผ่าน — รับรหัส OTP ทางอีเมล',
    width: 460,
    onClose() {
      if (resetCooldownTimer) {
        clearInterval(resetCooldownTimer);
        resetCooldownTimer = null;
      }
    },
    render(card, close) {
      card.style.padding = '0';
      card.style.overflow = 'hidden';
      card.innerHTML = `
        <div style="background:#141619;padding:14px 20px">
          <div class="text-h3" style="color:#FFB600">ตั้งรหัสผ่านใหม่ด้วย OTP</div>
          <div class="text-small" style="color:#FFFFFF">สำหรับผู้ซื้อ — กรอกอีเมลที่สมัครไว้เพื่อรับรหัส OTP 6 หลัก</div>
        </div>
        <div style="padding:16px 22px 20px">
          <div class="text-small-bold">อีเมลบัญชีของคุณ</div>
          <div style="display:flex;gap:8px;margin:2px 0 8px">
            <input type="email" class="input" data-role="email" placeholder="name@example.com" style="flex:1" />
            <button type="button" class="btn btn-primary btn-sm" data-role="send-otp" style="min-width:110px;height:38px">ส่ง OTP</button>
          </div>
          <div class="text-small-bold">รหัส OTP 6 หลัก</div>
          <input type="text" class="input" data-role="otp" maxlength="6" placeholder="กรอกรหัส OTP 6 หลัก" style="margin:2px 0 8px" />
          <div class="text-small-bold">รหัสผ่านใหม่ (อย่างน้อย 8 ตัวอักษร)</div>
          <input type="password" class="input" data-role="pw" placeholder="รหัสผ่านใหม่" style="margin:2px 0 8px" />
          <div class="text-small-bold" data-role="msg" style="min-height:18px;margin:4px 0"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px">
            <button type="button" class="btn btn-outline btn-md" data-role="cancel">ยกเลิก</button>
            <button type="button" class="btn btn-danger btn-md" data-role="confirm">ยืนยันเปลี่ยนรหัสผ่าน</button>
          </div>
        </div>
      `;
      const emailIn = card.querySelector('[data-role="email"]');
      const otpIn = card.querySelector('[data-role="otp"]');
      const pwIn = card.querySelector('[data-role="pw"]');
      const msgEl = card.querySelector('[data-role="msg"]');
      const sendBtn = card.querySelector('[data-role="send-otp"]');
      const confirmBtn = card.querySelector('[data-role="confirm"]');

      let cooldownLeft = 0;
      function startCooldown(seconds = 60) {
        if (resetCooldownTimer) {
          clearInterval(resetCooldownTimer);
          resetCooldownTimer = null;
        }
        cooldownLeft = Math.max(0, Math.floor(Number(seconds) || 60));
        const tick = () => {
          if (!document.body.contains(card)) {
            clearInterval(resetCooldownTimer);
            resetCooldownTimer = null;
            return;
          }
          if (cooldownLeft > 0) {
            sendBtn.disabled = true;
            sendBtn.textContent = `ขอใหม่ (${cooldownLeft}s)`;
          } else {
            sendBtn.disabled = false;
            sendBtn.textContent = 'ส่ง OTP ซ้ำ';
            if (resetCooldownTimer) {
              clearInterval(resetCooldownTimer);
              resetCooldownTimer = null;
            }
          }
        };
        tick();
        resetCooldownTimer = setInterval(() => {
          cooldownLeft -= 1;
          tick();
        }, 1000);
      }

      sendBtn.addEventListener('click', async () => {
        if (cooldownLeft > 0) return;
        const email = emailIn.value.trim();
        clearFieldError(emailIn);
        msgEl.textContent = '';
        if (!email) {
          const errMsg = 'กรุณากรอกอีเมลบัญชีของคุณ';
          setFieldError(emailIn, errMsg);
          msgEl.className = 'text-small-bold text-danger';
          msgEl.textContent = errMsg;
          showToast(errMsg, 'error');
          return;
        }
        sendBtn.disabled = true;
        try {
          const res = await api.post('/api/auth/reset/start', { email });
          const masked = res.masked_email || maskEmailClient(email);
          const txt = res.message || `ส่งรหัสไปที่ ${masked} แล้ว`;
          msgEl.className = 'text-small-bold text-success';
          msgEl.textContent = txt;
          showToast(`ส่งรหัสไปที่ ${masked} แล้ว`, 'success');
          startCooldown(res.cooldown_seconds || 60);
          otpIn.focus();
        } catch (err) {
          const em = err.message || 'ส่งรหัส OTP ไม่สำเร็จ';
          setFieldError(emailIn, em);
          msgEl.className = 'text-small-bold text-danger';
          msgEl.textContent = em;
          showToast(em, 'error');
          sendBtn.disabled = false;
        }
      });

      confirmBtn.addEventListener('click', async () => {
        clearFieldError(emailIn);
        clearFieldError(otpIn);
        clearFieldError(pwIn);
        msgEl.textContent = '';
        confirmBtn.disabled = true;
        try {
          const res = await api.post('/api/auth/reset/verify', {
            email: emailIn.value.trim(),
            otp_code: otpIn.value.trim(),
            new_password: pwIn.value,
          });
          const successMsg = res.message || 'ตั้งรหัสผ่านใหม่สำเร็จ กรุณาเข้าสู่ระบบ';
          showToast(successMsg, 'success');
          close();
          if (onResetSuccess) onResetSuccess(successMsg, 'success');
        } catch (err) {
          const em = err.message || 'เปลี่ยนรหัสผ่านไม่สำเร็จ';
          if (em.includes('รหัสผ่าน')) {
            setFieldError(pwIn, em);
          } else {
            setFieldError(otpIn, em);
          }
          msgEl.className = 'text-small-bold text-danger';
          msgEl.textContent = em;
          showToast(em, 'error');
        } finally {
          confirmBtn.disabled = false;
        }
      });

      card.querySelector('[data-role="cancel"]').addEventListener('click', () => close());
      setTimeout(() => emailIn.focus(), 40);
    },
  });
}

async function openOwnerContactDialog() {
  let c = {};
  try { c = await api.get('/api/settings/contact'); } catch (e) {}
  openModal({
    title: 'ติดต่อเจ้าของร้าน / แอดมินลืมรหัสผ่าน',
    width: 460,
    render(card, close) {
      card.innerHTML = `
        <div class="text-h3" style="margin-bottom:6px">🛡️ ติดต่อเจ้าของร้าน (สำหรับแอดมิน / ลูกค้า)</div>
        <div class="text-small text-muted" style="margin-bottom:12px">กรณีแอดมินลืมรหัสผ่านหรือบัญชีถูกล็อก กรุณาติดต่อเจ้าของร้านเพื่อรีเซ็ตรหัสผ่านชั่วคราว</div>
        <div class="card-alt" style="padding:12px 14px;margin-bottom:14px">
          <div><strong>เจ้าของร้าน:</strong> ${esc(c.owner_name || c.shop_name || 'เจ้าของร้าน')}</div>
          <div><strong>โทรศัพท์:</strong> ${esc(c.phone || c.shop_phone || '-')}</div>
          <div><strong>อีเมล:</strong> ${esc(c.email || c.shop_email || '-')}</div>
          <div><strong>LINE ID:</strong> ${esc(c.line_id || c.line_name || '-')}</div>
          ${c.note ? `<div class="text-small text-muted" style="margin-top:4px">${esc(c.note)}</div>` : ''}
        </div>
        <div style="display:flex;justify-content:flex-end">
          <button type="button" class="btn btn-primary btn-md" data-role="close">ตกลง</button>
        </div>
      `;
      card.querySelector('[data-role="close"]').addEventListener('click', () => close());
    },
  });
}
