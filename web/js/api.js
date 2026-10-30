// web/js/api.js — ตัวช่วยเรียก Backend API + จัดรูปแบบราคา/วันที่/ป้องกัน XSS
import { state } from './state.js';

export const THAI_MONTHS_SHORT = [
  'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
  'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.',
];

export const ORDER_STATUS_LABELS = {
  pending: 'รอชำระเงิน',
  checking_slip: 'รอตรวจสลิป',
  paid: 'ชำระเงินแล้ว',
  shipped: 'จัดส่งแล้ว',
  completed: 'สำเร็จ',
  cancelled: 'ยกเลิก',
};

export const ORDER_STATUS_DISPLAY_ORDER = [
  ['all',           'การสั่งซื้อ',         'คำสั่งซื้อทั้งหมด',                           null],
  ['pending',       'รอชำระเงิน',          'ยังไม่ชำระเงินหรือรอแนบสลิปใหม่',             'pending'],
  ['paid',          'ชำระเงินแล้ว',        'ตรวจสอบสลิปผ่านแล้ว รอจัดส่ง',                 'paid'],
  ['checking_slip', 'รอตรวจสลิป',          'ผู้ซื้อแนบสลิปแล้ว รอแอดมินตรวจสอบ',          'checking_slip'],
  ['shipped',       'จัดส่งแล้ว',          'ร้านส่งมอบให้ขนส่งพร้อมเลขพัสดุแล้ว',          'shipped'],
  ['completed',     'สำเร็จ',              'ผู้ซื้อได้รับสินค้าเรียบร้อยแล้ว',             'completed'],
  ['to_review',     'รอรีวิว',             'คำสั่งซื้อสำเร็จที่ยังมีสินค้ายังไม่ได้เขียนรีวิว', null],
  ['cancelled',     'สินค้าที่คุณยกเลิก',  'รายการคำสั่งซื้อที่ถูกยกเลิก',                 'cancelled'],
];

export const PAYMENT_STATUS_LABELS = {
  pending: 'รอตรวจสอบ',
  verified: 'ตรวจสอบแล้ว',
  rejected: 'สลิปไม่ถูกต้อง',
};

export const SHIPMENT_STATUS_LABELS = {
  preparing: 'กำลังเตรียมพัสดุ',
  shipped: 'ส่งมอบขนส่งแล้ว',
  delivered: 'ส่งถึงปลายทางแล้ว',
};

export const ROLE_LABELS = {
  owner: 'เจ้าของร้าน',
  admin: 'แอดมิน',
  buyer: 'ผู้ซื้อ',
  guest: 'ผู้เยี่ยมชม',
};

export const COUPON_CATEGORY_LABELS = {
  all: 'ทั้งหมด',
  free_shipping: 'คูปองส่วนลดค่าส่ง',
  percent: 'คูปองส่วนลดเป็น %',
  fixed: 'คูปองส่วนลดเป็น บาท',
  other: 'และอื่นๆ',
};

export const CARRIERS = ['Kerry Express', 'Flash Express', 'J&T Express', 'ไปรษณีย์ไทย', 'Best Express'];
export const OPTION_TYPES = ['สี', 'สไตล์', 'สี/สไตล์', 'ด้าม', 'เอ็น', 'ไซซ์', 'ความเร็ว', 'การปรับแต่งไม้'];
export const WEIGHT_CLASSES = ['3U', '4U'];
export const BALANCES = ['Heavy Head', 'Even Balance', 'Light Head'];
export const FLEXES = ['Stiff', 'Medium', 'Flexible'];
export const LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'Professional'];
export const RACKET_TECH_SPEC_FIELDS = [
  ['spec_material', 'Material'],
  ['spec_weight_grip', 'Weight Class / Grip'],
  ['spec_balance_point', 'Balance Point'],
  ['flex', 'Shaft Flexibility'],
  ['spec_max_tension', 'Max String Tension'],
  ['spec_length', 'Length'],
  ['level', 'Skill Level'],
];

export function esc(val) {
  if (val === null || val === undefined) return '';
  return String(val)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function formatPrice(amount) {
  let num = Number(amount || 0);
  if (!Number.isFinite(num)) num = 0;
  num = Math.round(num * 100) / 100;
  if (Math.floor(num) === num) {
    return `${num.toLocaleString('en-US', { maximumFractionDigits: 0 })} บาท`;
  }
  return `${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} บาท`;
}

export function parseDateTime(value) {
  if (!value) return null;
  if (value instanceof Date) return isNaN(value.getTime()) ? null : value;
  const text = String(value).trim();
  if (!text) return null;
  const normalized = text.includes('T') ? text : text.replace(' ', 'T');
  const d = new Date(normalized);
  if (!isNaN(d.getTime())) return d;
  const m = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/);
  if (!m) return null;
  return new Date(
    Number(m[1]),
    Number(m[2]) - 1,
    Number(m[3]),
    Number(m[4] || 0),
    Number(m[5] || 0),
    Number(m[6] || 0)
  );
}

export function formatDateThai(value) {
  if (value === null || value === undefined || value === '') return '-';
  const dt = parseDateTime(value);
  if (!dt) return String(value);
  return `${dt.getDate()} ${THAI_MONTHS_SHORT[dt.getMonth()]} ${dt.getFullYear() + 543}`;
}

export function formatDateTime(value) {
  if (value === null || value === undefined || value === '') return '-';
  const dt = parseDateTime(value);
  if (!dt) return String(value);
  const hh = String(dt.getHours()).padStart(2, '0');
  const mm = String(dt.getMinutes()).padStart(2, '0');
  return `${dt.getDate()} ${THAI_MONTHS_SHORT[dt.getMonth()]} ${dt.getFullYear() + 543} ${hh}:${mm}`;
}

export function formatPhone(phone) {
  if (!phone) return '-';
  const digits = String(phone).replace(/\D/g, '');
  if (digits.length === 10) {
    return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  return String(phone);
}

export function resolveAssetUrl(relPath, placeholder = '/assets/icons/no_image.svg') {
  if (!relPath) return placeholder;
  let clean = String(relPath).trim().replace(/\\/g, '/');
  if (!clean) return placeholder;
  if (clean.startsWith('http://') || clean.startsWith('https://') || clean.startsWith('data:')) {
    return clean;
  }
  if (clean.startsWith('/')) return clean;
  if (clean.startsWith('assets/')) return '/' + clean;
  return '/assets/' + clean;
}

let _onIdleLockedCallback = null;
export function setOnIdleLocked(cb) {
  _onIdleLockedCallback = cb;
}

async function request(method, path, { params = null, body = undefined, isForm = false } = {}) {
  let url = path;
  if (params && typeof params === 'object') {
    const usp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') {
        usp.append(k, String(v));
      }
    }
    const qs = usp.toString();
    if (qs) url += (url.includes('?') ? '&' : '?') + qs;
  }

  const headers = {};
  let payload = undefined;
  if (body !== undefined) {
    if (isForm) {
      payload = body;
    } else {
      headers['Content-Type'] = 'application/json';
      payload = JSON.stringify(body);
    }
  }

  const res = await fetch(url, {
    method,
    headers,
    body: payload,
    credentials: 'same-origin',
  });

  let data = null;
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
  } else {
    const txt = await res.text();
    data = { message: txt };
  }

  if (res.status === 423 || (data && data.locked)) {
    state.is_locked = true;
    state.notify();
    if (_onIdleLockedCallback) _onIdleLockedCallback();
    const err = new Error((data && data.error) || 'หน้าจอถูกล็อกเนื่องจากไม่มีการใช้งาน');
    err.status = 423;
    throw err;
  }

  if (!res.ok) {
    const msg = (data && (data.error || data.detail || data.message)) || `เกิดข้อผิดพลาด (${res.status})`;
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

export const api = {
  get: (path, params) => request('GET', path, { params }),
  post: (path, body) => request('POST', path, { body: body ?? {} }),
  put: (path, body) => request('PUT', path, { body: body ?? {} }),
  patch: (path, body) => request('PATCH', path, { body: body ?? {} }),
  del: (path, body) => request('DELETE', path, { body }),
  async uploadImage(file, target = 'product') {
    const targetMap = {
      products: 'product', product: 'product',
      categories: 'category', category: 'category',
      brands: 'brand', brand: 'brand',
      banners: 'banner', banner: 'banner',
      login_banners: 'login_banner', login_banner: 'login_banner',
      logo: 'logo',
      users: 'avatar', avatar: 'avatar',
      slips: 'slip', slip: 'slip',
    };
    const fd = new FormData();
    fd.append('target', targetMap[target] || 'product');
    fd.append('file', file);
    const res = await request('POST', '/api/uploads/image', { body: fd, isForm: true });
    return res.path;
  },
  async uploadForm(path, formData) {
    return request('POST', path, { body: formData, isForm: true });
  },
  async upload(path, formData) {
    return request('POST', path, { body: formData, isForm: true });
  },
  async refreshSession() {
    const data = await request('GET', '/api/bootstrap');
    state.updateFromSession(data);
    return data;
  },
};
