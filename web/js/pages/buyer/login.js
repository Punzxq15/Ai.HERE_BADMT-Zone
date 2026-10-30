// web/js/pages/buyer/login.js — หน้าเข้าสู่ระบบโฉมใหม่ (AI.HERE Bad🅜-Zone)
import { renderAuthExperience } from '../../components/auth_layout.js';

export async function render(container, router, params = {}) {
  return renderAuthExperience(container, router, {
    initialMode: 'login',
    params,
  });
}
