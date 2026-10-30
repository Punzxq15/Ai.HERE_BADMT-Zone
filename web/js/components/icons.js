// web/js/components/icons.js — ไอคอนเวกเตอร์ SVG คมชัดตรงกับ utils/icon_utils.py
export function iconSvg(name = 'racket', size = 18, color = 'currentColor') {
  const s = Number(size) || 18;
  const c = color || 'currentColor';
  const n = String(name || 'racket').trim().toLowerCase();

  const wrap = (inner) =>
    `<svg class="ui-icon ui-icon-${n}" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;display:inline-block;vertical-align:middle">${inner}</svg>`;

  switch (n) {
    case 'search':
      return wrap(`<circle cx="9.5" cy="9.5" r="6" stroke="${c}" stroke-width="2.2"/><line x1="14" y1="14" x2="20.5" y2="20.5" stroke="${c}" stroke-width="2.5" stroke-linecap="round"/>`);
    case 'heart':
      return wrap(`<path d="M12 20.5C12 20.5 3.5 15 3.5 8.8C3.5 5.8 5.8 3.8 8.5 3.8C10.2 3.8 11.5 4.7 12 5.8C12.5 4.7 13.8 3.8 15.5 3.8C18.2 3.8 20.5 5.8 20.5 8.8C20.5 15 12 20.5 12 20.5Z" stroke="${c}" stroke-width="2" stroke-linejoin="round"/>`);
    case 'heart_filled':
      return wrap(`<path d="M12 20.5C12 20.5 3.5 15 3.5 8.8C3.5 5.8 5.8 3.8 8.5 3.8C10.2 3.8 11.5 4.7 12 5.8C12.5 4.7 13.8 3.8 15.5 3.8C18.2 3.8 20.5 5.8 20.5 8.8C20.5 15 12 20.5 12 20.5Z" fill="${c}" stroke="${c}" stroke-width="1.8" stroke-linejoin="round"/>`);
    case 'cart':
      return wrap(`<path d="M2.5 4.5H5.5L8.2 15H18.8L21 7.5H6.5" stroke="${c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9.1" cy="18.8" r="1.7" fill="${c}"/><circle cx="17.8" cy="18.8" r="1.7" fill="${c}"/>`);
    case 'bell':
      return wrap(`<path d="M5.5 10.2C5.5 6.5 8.4 3.5 12 3.5C15.6 3.5 18.5 6.5 18.5 10.2V16L20.2 17.5H3.8L5.5 16V10.2Z" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><path d="M9.8 17.8C9.8 19.2 10.8 20.5 12 20.5C13.2 20.5 14.2 19.2 14.2 17.8" fill="${c}"/>`);
    case 'chat':
      return wrap(`<rect x="3" y="4" width="18" height="12.5" rx="3.5" stroke="${c}" stroke-width="2"/><polygon points="7,16.5 5.5,20.8 11.5,16.5" fill="${c}"/><circle cx="8.4" cy="10.1" r="1" fill="${c}"/><circle cx="12" cy="10.1" r="1" fill="${c}"/><circle cx="15.6" cy="10.1" r="1" fill="${c}"/>`);
    case 'user':
      return wrap(`<circle cx="12" cy="7.5" r="4" stroke="${c}" stroke-width="2"/><path d="M4 20.5C4 16.5 7.6 13.5 12 13.5C16.4 13.5 20 16.5 20 20.5" stroke="${c}" stroke-width="2" stroke-linecap="round"/>`);
    case 'users':
      return wrap(`<circle cx="10" cy="7.5" r="3.8" stroke="${c}" stroke-width="2"/><path d="M3 20C3 16.3 6.2 13.5 10 13.5C13.8 13.5 17 16.3 17 20" stroke="${c}" stroke-width="2" stroke-linecap="round"/><circle cx="17.5" cy="7.5" r="2.7" stroke="${c}" stroke-width="1.8"/><path d="M16.5 13.8C19.3 14.2 21.5 16.5 21.5 19.8" stroke="${c}" stroke-width="1.8" stroke-linecap="round"/>`);
    case 'key':
      return wrap(`<circle cx="8" cy="12" r="4.5" stroke="${c}" stroke-width="2"/><path d="M12.5 12H21M17.5 12V16M20.2 12V15.2" stroke="${c}" stroke-width="2" stroke-linecap="round"/>`);
    case 'lock':
      return wrap(`<rect x="5" y="10.5" width="14" height="10" rx="2.5" stroke="${c}" stroke-width="2"/><path d="M7.5 10.5V7.5C7.5 5 9.5 3.5 12 3.5C14.5 3.5 16.5 5 16.5 7.5V10.5" stroke="${c}" stroke-width="2"/><circle cx="12" cy="15.4" r="1.4" fill="${c}"/>`);
    case 'shield':
      return wrap(`<polygon points="12,2.8 19.8,5.8 19,13.2 12,21.2 5,13.2 4.2,5.8" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><polyline points="8.8,12 11.2,14.5 15.8,9.5" stroke="${c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`);
    case 'store':
      return wrap(`<polygon points="3,9.5 5.2,4 18.8,4 21,9.5" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><rect x="4.8" y="9.5" width="14.4" height="10.7" stroke="${c}" stroke-width="2"/><rect x="9.8" y="13.5" width="4.4" height="6.7" stroke="${c}" stroke-width="2"/>`);
    case 'map_pin':
      return wrap(`<path d="M12 21.2C12 21.2 18 14.2 18 9C18 5.7 15.3 3 12 3C8.7 3 6 5.7 6 9C6 14.2 12 21.2 12 21.2Z" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><circle cx="12" cy="9" r="2.4" stroke="${c}" stroke-width="1.8"/>`);
    case 'phone':
      return wrap(`<rect x="6.5" y="2.8" width="11" height="18.4" rx="2.5" stroke="${c}" stroke-width="2"/><circle cx="12" cy="18.2" r="1.2" fill="${c}"/>`);
    case 'mail':
      return wrap(`<rect x="3" y="5.5" width="18" height="13" rx="2" stroke="${c}" stroke-width="2"/><polyline points="3.5,6.5 12,13 20.5,6.5" stroke="${c}" stroke-width="2" stroke-linejoin="round"/>`);
    case 'flash':
      return wrap(`<polygon points="13.5,2.2 5.5,13.2 11.8,13.2 10.2,21.8 18.8,10.5 12.5,10.5" fill="${c}"/>`);
    case 'fire':
      return wrap(`<polygon points="12.2,2.2 16.8,7.8 19.2,12.8 17.5,18.8 12,21.5 6.5,18.8 5,13.2 8.2,8.5 10.2,11.2" fill="${c}"/>`);
    case 'star':
      return wrap(`<polygon points="12,2.7 14.5,8.8 21,9.3 16,13.6 17.6,20 12,16.5 6.4,20 8,13.6 3,9.3 9.5,8.8" fill="${c}"/>`);
    case 'coupon':
    case 'gift':
      return wrap(`<rect x="2.8" y="6.2" width="18.4" height="11.6" rx="2.2" stroke="${c}" stroke-width="2"/><line x1="9.5" y1="6.5" x2="9.5" y2="17.5" stroke="${c}" stroke-width="1.8" stroke-dasharray="2 2"/><circle cx="15" cy="12" r="2" fill="${c}"/>`);
    case 'truck':
      return wrap(`<rect x="2.5" y="6.5" width="12" height="9.7" stroke="${c}" stroke-width="2"/><polygon points="14.5,9.5 18.8,9.5 21.2,12.8 21.2,16.2 14.5,16.2" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><circle cx="7.5" cy="18" r="2" fill="${c}"/><circle cx="17.8" cy="18" r="2" fill="${c}"/>`);
    case 'category':
      return wrap(`<rect x="3.5" y="3.5" width="7.5" height="7.5" rx="1.8" stroke="${c}" stroke-width="2"/><rect x="13" y="3.5" width="7.5" height="7.5" rx="1.8" stroke="${c}" stroke-width="2"/><rect x="3.5" y="13" width="7.5" height="7.5" rx="1.8" stroke="${c}" stroke-width="2"/><rect x="13" y="13" width="7.5" height="7.5" rx="1.8" stroke="${c}" stroke-width="2"/>`);
    case 'brand':
      return wrap(`<polygon points="12,2.8 19.8,8.5 16.8,19.8 7.2,19.8 4.2,8.5" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><circle cx="12" cy="12" r="2.2" fill="${c}"/>`);
    case 'compare':
      return wrap(`<path d="M4 8H19.5M15.5 4.5L19.8 8L15.5 11.5M20 16H4.5M8.5 12.5L4.2 16L8.5 19.5" stroke="${c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`);
    case 'target':
      return wrap(`<circle cx="12" cy="12" r="9" stroke="${c}" stroke-width="2"/><circle cx="12" cy="12" r="4.8" stroke="${c}" stroke-width="1.6"/><circle cx="12" cy="12" r="1.8" fill="${c}"/>`);
    case 'refresh':
      return wrap(`<path d="M19.5 10C18.6 6.5 15.6 4 12 4C7.6 4 4 7.6 4 12C4 16.4 7.6 20 12 20C15.7 20 18.8 17.5 19.7 14" stroke="${c}" stroke-width="2" stroke-linecap="round"/><polygon points="16.2,2.8 21.2,6.5 15.5,8.8" fill="${c}"/>`);
    case 'trash':
      return wrap(`<line x1="4" y1="6.5" x2="20" y2="6.5" stroke="${c}" stroke-width="2" stroke-linecap="round"/><rect x="8.8" y="3.5" width="6.4" height="3" stroke="${c}" stroke-width="1.6"/><rect x="6.2" y="6.5" width="11.6" height="14" rx="1.8" stroke="${c}" stroke-width="2"/><line x1="10" y1="10.2" x2="10" y2="17.2" stroke="${c}" stroke-width="1.6"/><line x1="14" y1="10.2" x2="14" y2="17.2" stroke="${c}" stroke-width="1.6"/>`);
    case 'edit':
      return wrap(`<polygon points="14.8,4.2 19.8,9.2 8.8,20.2 3.8,20.2 3.8,15.2" stroke="${c}" stroke-width="2" stroke-linejoin="round"/>`);
    case 'check':
      return wrap(`<polyline points="4.2,12.5 9.8,18 20,6.5" stroke="${c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`);
    case 'eye':
      return wrap(`<path d="M2.5 12C4.5 7.5 8 5.2 12 5.2C16 5.2 19.5 7.5 21.5 12C19.5 16.5 16 18.8 12 18.8C8 18.8 4.5 16.5 2.5 12Z" stroke="${c}" stroke-width="2" stroke-linejoin="round"/><circle cx="12" cy="12" r="2.5" fill="${c}"/>`);
    case 'theme':
      return wrap(`<path d="M20 15.2C18.8 15.7 17.5 16 16.1 16C10.6 16 6.1 11.5 6.1 6C6.1 4.6 6.4 3.3 6.9 2.1C4 3.6 2 6.6 2 10.2C2 15.6 6.4 20 11.8 20C15.4 20 18.4 18 20 15.2Z" fill="${c}"/>`);
    case 'logout':
      return wrap(`<polyline points="10.5,4 4.5,4 4.5,20 10.5,20" stroke="${c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="9.5" y1="12" x2="20.2" y2="12" stroke="${c}" stroke-width="2" stroke-linecap="round"/><polyline points="16,8 20.5,12 16,16" stroke="${c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`);
    case 'chart':
      return wrap(`<line x1="3.5" y1="20" x2="20.5" y2="20" stroke="${c}" stroke-width="2" stroke-linecap="round"/><rect x="5.2" y="12" width="3.3" height="8" fill="${c}"/><rect x="10.5" y="7.5" width="3.3" height="12.5" fill="${c}"/><rect x="15.8" y="4.5" width="3.3" height="15.5" fill="${c}"/>`);
    case 'order':
    case 'receipt':
      return wrap(`<rect x="5" y="3.2" width="14" height="17.6" rx="2" stroke="${c}" stroke-width="2"/><line x1="8.2" y1="8.2" x2="15.8" y2="8.2" stroke="${c}" stroke-width="1.8"/><line x1="8.2" y1="12.2" x2="15.8" y2="12.2" stroke="${c}" stroke-width="1.8"/><line x1="8.2" y1="16.2" x2="13.2" y2="16.2" stroke="${c}" stroke-width="1.8"/>`);
    case 'settings':
      return wrap(`<circle cx="12" cy="12" r="5.5" stroke="${c}" stroke-width="2"/><circle cx="12" cy="12" r="2.2" fill="${c}"/><line x1="12" y1="2.5" x2="12" y2="5.5" stroke="${c}" stroke-width="2"/><line x1="12" y1="18.5" x2="12" y2="21.5" stroke="${c}" stroke-width="2"/><line x1="2.5" y1="12" x2="5.5" y2="12" stroke="${c}" stroke-width="2"/><line x1="18.5" y1="12" x2="21.5" y2="12" stroke="${c}" stroke-width="2"/>`);
    case 'calendar':
      return wrap(`<rect x="3.5" y="5" width="17" height="15.5" rx="2" stroke="${c}" stroke-width="2"/><line x1="3.5" y1="9.5" x2="20.5" y2="9.5" stroke="${c}" stroke-width="2"/><line x1="8" y1="3" x2="8" y2="6.5" stroke="${c}" stroke-width="2" stroke-linecap="round"/><line x1="16" y1="3" x2="16" y2="6.5" stroke="${c}" stroke-width="2" stroke-linecap="round"/>`);
    default: // racket
      return wrap(`<ellipse cx="14.4" cy="9.2" rx="6.8" ry="6.6" stroke="${c}" stroke-width="2"/><line x1="11" y1="6" x2="18" y2="12.5" stroke="${c}" stroke-width="1.2"/><line x1="18" y1="6" x2="11" y2="12.5" stroke="${c}" stroke-width="1.2"/><line x1="10" y1="13.8" x2="3.5" y2="20.5" stroke="${c}" stroke-width="2.5" stroke-linecap="round"/>`);
  }
}
