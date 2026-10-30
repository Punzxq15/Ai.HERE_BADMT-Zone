// web/js/pages/buyer/register.js — หน้าสมัครสมาชิกพร้อม OTP โฉมใหม่ (AI.HERE Bad🅜-Zone)
import { renderAuthExperience } from '../../components/auth_layout.js';

export async function render(container, router, params = {}) {
  return renderAuthExperience(container, router, {
    initialMode: 'signup',
    params,
  });
}
