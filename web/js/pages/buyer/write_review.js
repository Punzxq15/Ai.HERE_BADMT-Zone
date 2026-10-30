// web/js/pages/buyer/write_review.js — หน้าเขียนรีวิวสินค้า (เลย์เอาต์กึ่งกลางกระชับ + อัปโหลดรูป/วิดีโอ 0–5 ไฟล์ + ปุ่มไม่รีวิว)
import { api, esc, resolveAssetUrl } from '../../api.js';
import { createRatingStars } from '../../components/rating.js';
import { showToast, setFieldError, clearFieldError } from '../../components/dialogs.js';
import { pageTitleHtml } from '../../components/buyer_common.js';

const RATING_TEXT = {
  0: 'แตะดาวเพื่อให้คะแนน',
  1: 'แย่มาก',
  2: 'พอใช้',
  3: 'ปานกลาง',
  4: 'ดี',
  5: 'ดีมาก',
};

const ALLOWED_IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.webp'];
const ALLOWED_VIDEO_EXTS = ['.mp4', '.webm', '.mov'];

export async function render(container, router, params = {}) {
  const productId = Number(params.product_id);
  const orderId = Number(params.order_id);
  const wrap = document.createElement('div');
  wrap.className = 'buyer-container';
  container.appendChild(wrap);

  wrap.innerHTML = `
    <div style="max-width:760px;margin:0 auto">
      ${pageTitleHtml('⭐ เขียนรีวิวสินค้า', 'แบ่งปันประสบการณ์ใช้งานจริง พร้อมแนบรูปภาพหรือวิดีโอได้สูงสุด 5 ไฟล์')}
      <div class="card review-card-centered" style="padding:20px 24px">
        <!-- แถบสลับสินค้าในคำสั่งซื้อเดียวกัน (กรณีมีสินค้าที่ยังไม่ได้รีวิวหลายชิ้น) -->
        <div data-role="product-switcher" class="hidden" style="margin-bottom:12px;padding-bottom:10px;border-bottom:1px dashed var(--color-border)">
          <div class="text-small-bold text-muted" style="margin-bottom:6px">สินค้าที่รอรีวิวในคำสั่งซื้อนี้:</div>
          <div data-role="switcher-btns" style="display:flex;flex-wrap:wrap;gap:6px"></div>
        </div>

        <!-- ส่วนหัวสินค้า -->
        <div style="display:flex;gap:14px;align-items:center;padding-bottom:12px;border-bottom:1px solid var(--color-border);margin-bottom:12px">
          <img data-role="img" src="/assets/icons/no_image.svg" alt="product" style="width:76px;height:76px;border-radius:10px;object-fit:cover;background:var(--color-surface-alt);border:1px solid var(--color-border);flex-shrink:0" />
          <div style="min-width:0;flex:1">
            <div class="text-h3" data-role="name" style="margin-bottom:2px">-</div>
            <div class="text-small text-muted" data-role="opt"></div>
          </div>
        </div>

        <!-- ให้คะแนนดาว -->
        <div style="margin-bottom:12px">
          <div class="text-body-bold" style="margin-bottom:4px">ให้คะแนนสินค้า <span class="text-danger">*</span></div>
          <div style="display:flex;align-items:center;gap:12px">
            <div data-role="stars-slot"></div>
            <span class="text-body-bold text-primary" data-role="rate-txt">${RATING_TEXT[0]}</span>
          </div>
          <div class="field-inline-error hidden" data-role="rating-err"></div>
        </div>

        <!-- ความเห็น -->
        <div style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px">
            <span class="text-body-bold">ความเห็นเกี่ยวกับสินค้า (ไม่บังคับ)</span>
            <span class="text-tiny text-muted" data-role="counter">0/1000</span>
          </div>
          <textarea class="textarea" data-role="comment" rows="3" style="min-height:82px" placeholder="เล่าความประทับใจ เช่น ฟีลลิ่งการตี ความคุ้มค่า หรือการจัดส่ง..."></textarea>
        </div>

        <!-- อัปโหลดรูปภาพ / วิดีโอ (0–5 ไฟล์) -->
        <div style="margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:6px">
            <div>
              <span class="text-body-bold">แนบรูปภาพ / วิดีโอ (ไม่บังคับ)</span>
              <span class="text-tiny text-muted" style="margin-left:6px">รองรับ .jpg, .png, .webp (≤ 5 MB) และ .mp4, .webm, .mov (≤ 50 MB)</span>
            </div>
            <span class="pill pill-neutral" data-role="media-counter">0/5 ไฟล์</span>
          </div>

          <div class="review-upload-zone" data-role="dropzone">
            <input type="file" data-role="file-input" multiple accept=".jpg,.jpeg,.png,.webp,.mp4,.webm,.mov,image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime" style="display:none" />
            <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
              <div class="text-small text-muted" data-role="drop-hint">📷 คลิกปุ่มเพื่อเลือกรูปภาพหรือวิดีโอ หรือลากไฟล์มาวางที่นี่ (รวมสูงสุด 5 ไฟล์)</div>
              <button type="button" class="btn btn-outline btn-sm" data-role="pick-btn">+ เลือกรูป / วิดีโอ</button>
            </div>
            <div class="review-media-grid" data-role="media-grid"></div>
          </div>
          <div class="field-inline-error hidden" data-role="media-err"></div>
        </div>

        <div class="text-small text-danger" data-role="msg" style="min-height:18px;margin-bottom:6px"></div>

        <div style="display:flex;gap:10px;justify-content:space-between;align-items:center;flex-wrap:wrap">
          <button type="button" class="btn btn-ghost btn-md" data-role="skip" title="ไม่รีวิวสินค้านี้และนำออกจากช่องรอรีวิว">ไม่รีวิวสินค้านี้</button>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <button type="button" class="btn btn-outline btn-md" data-role="cancel" style="min-width:110px">ย้อนกลับ</button>
            <button type="button" class="btn btn-primary btn-md" data-role="submit" style="min-width:160px" disabled>ส่งรีวิว</button>
          </div>
        </div>
      </div>
    </div>
  `;

  const switcherEl = wrap.querySelector('[data-role="product-switcher"]');
  const switcherBtnsEl = wrap.querySelector('[data-role="switcher-btns"]');
  const imgEl = wrap.querySelector('[data-role="img"]');
  const nameEl = wrap.querySelector('[data-role="name"]');
  const optEl = wrap.querySelector('[data-role="opt"]');
  const rateTxt = wrap.querySelector('[data-role="rate-txt"]');
  const ratingErrEl = wrap.querySelector('[data-role="rating-err"]');
  const commentBox = wrap.querySelector('[data-role="comment"]');
  const counterEl = wrap.querySelector('[data-role="counter"]');
  const dropzone = wrap.querySelector('[data-role="dropzone"]');
  const fileInput = wrap.querySelector('[data-role="file-input"]');
  const pickBtn = wrap.querySelector('[data-role="pick-btn"]');
  const dropHint = wrap.querySelector('[data-role="drop-hint"]');
  const mediaGrid = wrap.querySelector('[data-role="media-grid"]');
  const mediaCounter = wrap.querySelector('[data-role="media-counter"]');
  const mediaErrEl = wrap.querySelector('[data-role="media-err"]');
  const msgEl = wrap.querySelector('[data-role="msg"]');
  const skipBtn = wrap.querySelector('[data-role="skip"]');
  const submitBtn = wrap.querySelector('[data-role="submit"]');

  let maxLen = 1000;
  let maxFiles = 5;
  let maxImageBytes = 5 * 1024 * 1024;
  let maxVideoBytes = 50 * 1024 * 1024;
  let canSubmitReview = false;
  let otherUnreviewedPids = [];

  // รายการไฟล์ที่เลือก: [{ file, kind: 'image'|'video', previewUrl }]
  const selectedMedia = [];

  function setInlineError(el, message) {
    if (!el) return;
    if (message) {
      el.textContent = `⛔ ${message}`;
      el.classList.remove('hidden');
    } else {
      el.textContent = '';
      el.classList.add('hidden');
    }
  }

  const stars = createRatingStars({
    value: 0,
    size: 34,
    interactive: true,
    onChange(v) {
      rateTxt.textContent = RATING_TEXT[v] || '';
      setInlineError(ratingErrEl, '');
      msgEl.textContent = '';
    },
  });
  wrap.querySelector('[data-role="stars-slot"]').appendChild(stars.el);

  commentBox.addEventListener('input', () => {
    clearFieldError(commentBox);
    const len = commentBox.value.trim().length;
    counterEl.textContent = `${len}/${maxLen}`;
    counterEl.className = `text-tiny ${len > maxLen ? 'text-danger' : 'text-muted'}`;
  });

  function renderMediaPreviews() {
    mediaGrid.innerHTML = '';
    mediaCounter.textContent = `${selectedMedia.length}/${maxFiles} ไฟล์`;
    const isFull = selectedMedia.length >= maxFiles;
    pickBtn.disabled = isFull || !canSubmitReview;
    pickBtn.textContent = isFull ? 'ครบ 5 ไฟล์แล้ว' : '+ เลือกรูป / วิดีโอ';
    dropHint.textContent = isFull
      ? 'เลือกครบ 5 ไฟล์แล้ว (กด ✕ บนรูป/วิดีโอหากต้องการเปลี่ยนไฟล์)'
      : '📷 คลิกปุ่มเพื่อเลือกรูปภาพหรือวิดีโอ หรือลากไฟล์มาวางที่นี่ (รวมสูงสุด 5 ไฟล์)';

    selectedMedia.forEach((item, idx) => {
      const box = document.createElement('div');
      box.className = 'review-media-thumb';
      if (item.kind === 'video') {
        box.innerHTML = `
          <video src="${esc(item.previewUrl)}" muted preload="metadata" playsinline></video>
          <span class="review-media-badge">▶ วิดีโอ</span>
          <button type="button" class="review-media-remove" title="ลบไฟล์นี้">✕</button>
        `;
      } else {
        box.innerHTML = `
          <img src="${esc(item.previewUrl)}" alt="${esc(item.file.name)}" />
          <span class="review-media-badge">รูปภาพ</span>
          <button type="button" class="review-media-remove" title="ลบไฟล์นี้">✕</button>
        `;
      }
      box.querySelector('.review-media-remove').addEventListener('click', (e) => {
        e.stopPropagation();
        const removed = selectedMedia.splice(idx, 1)[0];
        if (removed && removed.previewUrl) {
          try { URL.revokeObjectURL(removed.previewUrl); } catch (_) {}
        }
        setInlineError(mediaErrEl, '');
        renderMediaPreviews();
      });
      mediaGrid.appendChild(box);
    });
  }

  function handleIncomingFiles(fileList) {
    if (!canSubmitReview) return;
    const incoming = Array.from(fileList || []);
    if (!incoming.length) return;
    setInlineError(mediaErrEl, '');

    if (selectedMedia.length + incoming.length > maxFiles) {
      const errMsg = `อัปโหลดรูปภาพและวิดีโอรวมกันได้ไม่เกิน ${maxFiles} ไฟล์ (ปัจจุบันเลือกแล้ว ${selectedMedia.length} ไฟล์)`;
      setInlineError(mediaErrEl, errMsg);
      showToast(errMsg, 'error');
      return;
    }

    const imgMb = Math.round(maxImageBytes / (1024 * 1024));
    const vidMb = Math.round(maxVideoBytes / (1024 * 1024));

    for (const file of incoming) {
      const name = String(file.name || '').toLowerCase();
      const dotIdx = name.lastIndexOf('.');
      const ext = dotIdx >= 0 ? name.slice(dotIdx) : '';
      const isImg = ALLOWED_IMAGE_EXTS.includes(ext);
      const isVid = ALLOWED_VIDEO_EXTS.includes(ext);

      if (!isImg && !isVid) {
        const errMsg = `ไฟล์ "${file.name}" ไม่รองรับ กรุณาเลือกเฉพาะรูปภาพ (.jpg, .png, .webp) หรือวิดีโอ (.mp4, .webm, .mov)`;
        setInlineError(mediaErrEl, errMsg);
        showToast(errMsg, 'error');
        return;
      }
      if (file.size <= 0) {
        const errMsg = `ไฟล์ "${file.name}" ว่างเปล่าหรือไม่ถูกต้อง`;
        setInlineError(mediaErrEl, errMsg);
        showToast(errMsg, 'error');
        return;
      }
      if (isImg && file.size > maxImageBytes) {
        const errMsg = `รูปภาพ "${file.name}" มีขนาดเกิน ${imgMb} MB`;
        setInlineError(mediaErrEl, errMsg);
        showToast(errMsg, 'error');
        return;
      }
      if (isVid && file.size > maxVideoBytes) {
        const errMsg = `วิดีโอ "${file.name}" มีขนาดเกิน ${vidMb} MB`;
        setInlineError(mediaErrEl, errMsg);
        showToast(errMsg, 'error');
        return;
      }

      const previewUrl = URL.createObjectURL(file);
      selectedMedia.push({
        file,
        kind: isVid ? 'video' : 'image',
        previewUrl,
      });
    }

    renderMediaPreviews();
  }

  pickBtn.addEventListener('click', () => {
    if (selectedMedia.length < maxFiles && canSubmitReview) {
      fileInput.value = '';
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', () => {
    handleIncomingFiles(fileInput.files);
    fileInput.value = '';
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    if (canSubmitReview && selectedMedia.length < maxFiles) {
      dropzone.classList.add('dragover');
    }
  });
  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer && e.dataTransfer.files) {
      handleIncomingFiles(e.dataTransfer.files);
    }
  });

  function cleanupObjectUrls() {
    while (selectedMedia.length) {
      const m = selectedMedia.pop();
      if (m && m.previewUrl) {
        try { URL.revokeObjectURL(m.previewUrl); } catch (_) {}
      }
    }
  }

  const goAfterComplete = () => {
    cleanupObjectUrls();
    if (otherUnreviewedPids.length > 0) {
      router.show('write_review', {
        product_id: Number(otherUnreviewedPids[0]),
        order_id: orderId,
      });
    } else {
      router.show('orders');
    }
  };

  const goBack = () => {
    cleanupObjectUrls();
    router.go_back('orders');
  };
  wrap.querySelector('[data-role="cancel"]').addEventListener('click', goBack);

  try {
    if (!productId || !orderId) throw new Error('ไม่พบสินค้าที่ต้องการรีวิว');
    const res = await api.get('/api/reviews/can-review', { product_id: productId, order_id: orderId });
    maxLen = res.max_comment_length || 1000;
    maxFiles = res.max_review_files || 5;
    maxImageBytes = res.max_image_bytes || (5 * 1024 * 1024);
    maxVideoBytes = res.max_video_bytes || (50 * 1024 * 1024);
    counterEl.textContent = `0/${maxLen}`;
    mediaCounter.textContent = `0/${maxFiles} ไฟล์`;

    const order = res.order || {};
    const allOrderItems = order.items || [];
    const prodItems = allOrderItems.filter((i) => Number(i.product_id) === productId);
    if (!prodItems.length) throw new Error('ไม่พบสินค้านี้ในคำสั่งซื้อ');

    // รวบรวมสินค้าทั้งหมดที่ยังไม่ได้รีวิวในออเดอร์นี้
    const unrevMap = new Map();
    for (const it of allOrderItems) {
      const pid = Number(it.product_id || 0);
      const isRev = Boolean(it.is_reviewed || it.reviewed);
      const isSkip = Boolean(it.is_review_skipped);
      if (pid && !isRev && !isSkip && !unrevMap.has(pid)) {
        unrevMap.set(pid, it);
      }
    }
    otherUnreviewedPids = Array.from(unrevMap.keys()).filter((pid) => pid !== productId);

    if (unrevMap.size > 1) {
      switcherEl.classList.remove('hidden');
      switcherBtnsEl.innerHTML = '';
      for (const [pid, it] of unrevMap.entries()) {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = `btn btn-sm ${pid === productId ? 'btn-primary' : 'btn-outline'}`;
        b.textContent = it.product_name || `สินค้า #${pid}`;
        if (pid !== productId) {
          b.addEventListener('click', () => {
            cleanupObjectUrls();
            router.show('write_review', { product_id: pid, order_id: orderId });
          });
        }
        switcherBtnsEl.appendChild(b);
      }
    }

    const firstItem = prodItems[0];
    imgEl.src = resolveAssetUrl(firstItem.image_path);
    nameEl.textContent = firstItem.product_name || '-';

    const optLabels = [];
    for (const it of prodItems) {
      const lbl = String(it.option_label || '').trim();
      if (lbl && lbl !== '-' && !optLabels.includes(lbl)) {
        optLabels.push(lbl);
      }
    }
    optEl.textContent = optLabels.length ? `ตัวเลือกที่สั่ง: ${optLabels.join(', ')}` : `คำสั่งซื้อ #${orderId}`;

    if (res.can_review) {
      canSubmitReview = true;
      submitBtn.disabled = false;
      pickBtn.disabled = false;
      skipBtn.disabled = false;
    } else {
      canSubmitReview = false;
      submitBtn.disabled = true;
      pickBtn.disabled = true;
      skipBtn.disabled = true;
      const errMsg = 'ไม่สามารถรีวิวสินค้านี้ได้ — อาจรีวิวไปแล้ว หรือคำสั่งซื้อยังไม่สำเร็จ';
      msgEl.textContent = `⛔ ${errMsg}`;
      showToast(errMsg, 'error');
    }
  } catch (err) {
    const errMsg = err.message || 'ไม่สามารถโหลดข้อมูลรีวิวได้';
    msgEl.textContent = `⛔ ${errMsg}`;
    showToast(errMsg, 'error');
  }

  skipBtn.addEventListener('click', async () => {
    if (!canSubmitReview) return;
    skipBtn.disabled = true;
    submitBtn.disabled = true;
    try {
      await api.post('/api/reviews/skip', {
        order_id: orderId,
        product_id: productId,
      });
      showToast('นำสินค้าออกจากรายการรอรีวิวเรียบร้อยแล้ว', 'success');
      goAfterComplete();
    } catch (err) {
      skipBtn.disabled = false;
      submitBtn.disabled = false;
      const errMsg = err.message || 'ไม่สามารถดำเนินการได้';
      msgEl.textContent = `⛔ ${errMsg}`;
      showToast(errMsg, 'error');
    }
  });

  submitBtn.addEventListener('click', async () => {
    const rating = stars.get();
    if (rating < 1) {
      const errMsg = 'กรุณาให้คะแนน 1-5 ดาวก่อนส่งรีวิว';
      setInlineError(ratingErrEl, errMsg);
      showToast(errMsg, 'error');
      return;
    }
    const commentText = commentBox.value.trim();
    if (commentText.length > maxLen) {
      const errMsg = `ความเห็นยาวเกินไป (ไม่เกิน ${maxLen} ตัวอักษร)`;
      setFieldError(commentBox, errMsg);
      showToast(errMsg, 'error');
      return;
    }

    setInlineError(ratingErrEl, '');
    setInlineError(mediaErrEl, '');
    msgEl.textContent = '';

    submitBtn.disabled = true;
    pickBtn.disabled = true;
    skipBtn.disabled = true;
    const origBtnText = submitBtn.textContent;
    submitBtn.textContent = 'กำลังบันทึก...';

    try {
      if (selectedMedia.length === 0) {
        await api.post('/api/reviews', {
          product_id: productId,
          order_id: orderId,
          rating,
          comment: commentText,
        });
      } else {
        const formData = new FormData();
        formData.append('product_id', String(productId));
        formData.append('order_id', String(orderId));
        formData.append('rating', String(rating));
        formData.append('comment', commentText);
        for (const item of selectedMedia) {
          formData.append('files', item.file, item.file.name);
        }
        await api.uploadForm('/api/reviews', formData);
      }
      showToast('บันทึกรีวิวของคุณเรียบร้อยแล้ว ขอบคุณสำหรับรีวิวครับ', 'success');
      goAfterComplete();
    } catch (err) {
      submitBtn.disabled = false;
      skipBtn.disabled = false;
      pickBtn.disabled = selectedMedia.length >= maxFiles;
      submitBtn.textContent = origBtnText;
      const errMsg = err.message || 'ไม่สามารถบันทึกรีวิวได้';
      msgEl.textContent = `⛔ ${errMsg}`;
      showToast(errMsg, 'error');
    }
  });

  return () => {
    cleanupObjectUrls();
  };
}
