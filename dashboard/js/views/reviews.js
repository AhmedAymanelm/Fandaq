// ══════════════════════════════════════════════
//  PAGE: REVIEWS
// ══════════════════════════════════════════════
async function loadReviews() {
  if (!HOTEL_ID) return;
  document.getElementById('content').innerHTML = `
    <div id="reviews-stats" style="margin-bottom:20px"></div>
    <div class="table-card">
      <div class="table-header">
        <h3>⭐ التقييمات</h3>
      </div>
      <div id="reviews-list" style="padding:16px">
        <div class="loading-text">جاري جلب التقييمات...</div>
      </div>
    </div>`;

  try {
    const data = await apiFetch(`/hotels/${HOTEL_ID}/reviews?limit=100`);
    const reviews = data.reviews || [];
    const avg = data.average_rating;
    const total = data.total || 0;

    // Stats bar
    document.getElementById('reviews-stats').innerHTML = `
      <div class="kpi-grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr))">
        <div class="kpi-card orange">
          <div class="kpi-icon">⭐</div>
          <div class="kpi-label">متوسط التقييم</div>
          <div class="kpi-value">${avg ? avg.toFixed(1) : '—'} / 5</div>
          <div class="kpi-sub">${renderStars(avg || 0)}</div>
        </div>
        <div class="kpi-card blue">
          <div class="kpi-icon">📊</div>
          <div class="kpi-label">عدد التقييمات</div>
          <div class="kpi-value">${total}</div>
          <div class="kpi-sub">تقييم</div>
        </div>
      </div>`;

    const list = document.getElementById('reviews-list');
    if (reviews.length === 0) {
      list.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-dim)">لا توجد تقييمات بعد</div>';
      return;
    }

    list.innerHTML = reviews.map(r => {
      // Map category to Arabic and color
      const catMap = {
        'cleanliness': { ar: '🧼 نظافة', class: 'badge green' },
        'service': { ar: '🤵 خدمة', class: 'badge blue' },
        'maintenance': { ar: '🔧 صيانة', class: 'badge red' },
        'general': { ar: '⭐ عام', class: 'badge gray' }
      };
      const catInfo = catMap[r.category] || catMap['general'];
      const statusHtml = reviewReplyStatusBadge(r.reply_status);
      const sentimentHtml = reviewSentimentBadge(r.sentiment);
      const canModerate = CURRENT_USER && ['admin', 'supervisor'].includes(CURRENT_USER.role);
      const replyText = r.final_reply_text || r.ai_reply_suggestion;
      
      return `
      <div style="border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px;background:var(--bg)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <div>
            <strong style="font-size:15px">${r.guest_name || 'ضيف'}</strong>
            <span style="margin-right:10px;color:var(--text-dim);font-size:12px">${fmtDate(r.created_at)}</span>
          </div>
          <div style="display:flex;align-items:center;gap:10px;">
            <span class="${catInfo.class}">${catInfo.ar}</span>
            <div style="font-size:18px">${renderStars(r.rating)}</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
          ${sentimentHtml}
          ${statusHtml}
        </div>
        ${r.comment ? `<p style="margin:0;color:var(--text);line-height:1.6">${r.comment}</p>` : '<p style="margin:0;color:var(--text-dim);font-style:italic">بدون تعليق</p>'}
        ${replyText ? `
        <div style="margin-top:12px;padding:12px;background:rgba(59, 130, 246, 0.1);border-left:3px solid var(--primary);border-radius:0 8px 8px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:12px;font-weight:bold;color:var(--primary)">🤖 رد مقترح من الذكاء الاصطناعي</span>
            <button onclick="navigator.clipboard.writeText('${replyText.replace(/'/g, "\\'").replace(/\n/g, '\\n')}'); showToast('تم نسخ الرد بنجاح');" 
              style="background:var(--primary);color:#fff;border:none;border-radius:4px;padding:4px 8px;font-size:12px;cursor:pointer;">
              نسخ 📋
            </button>
          </div>
          <p style="margin:0;color:var(--text);font-size:13px;line-height:1.5">${replyText.replace(/\n/g, '<br>')}</p>
          ${r.reply_approved_by_name ? `<div style="margin-top:6px;font-size:11px;color:var(--text-dim)">اعتمد بواسطة: ${r.reply_approved_by_name}</div>` : ''}
        </div>` : ''}
        ${canModerate ? renderReviewWorkflowActions(r) : ''}
      </div>
    `;}).join('');
  } catch (e) {
    document.getElementById('reviews-list').innerHTML =
      '<div style="text-align:center;padding:30px;color:var(--text-dim)">فشل تحميل التقييمات</div>';
  }
}

function reviewSentimentBadge(sentiment) {
  if (sentiment === 'positive') {
    return '<span class="badge" style="background:rgba(16,185,129,.2);color:#34d399;border:1px solid rgba(16,185,129,.35)">إيجابي</span>';
  }
  if (sentiment === 'negative') {
    return '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">سلبي</span>';
  }
  return '<span class="badge" style="background:rgba(245,158,11,.2);color:#f59e0b;border:1px solid rgba(245,158,11,.35)">محايد</span>';
}

function reviewReplyStatusBadge(status) {
  const map = {
    auto_sent: '<span class="badge" style="background:rgba(16,185,129,.2);color:#34d399;border:1px solid rgba(16,185,129,.35)">إرسال تلقائي</span>',
    pending_approval: '<span class="badge" style="background:rgba(245,158,11,.2);color:#f59e0b;border:1px solid rgba(245,158,11,.35)">بانتظار الاعتماد</span>',
    approved: '<span class="badge" style="background:rgba(59,130,246,.2);color:#93c5fd;border:1px solid rgba(59,130,246,.35)">معتمد</span>',
    sent: '<span class="badge" style="background:rgba(16,185,129,.2);color:#34d399;border:1px solid rgba(16,185,129,.35)">تم الإرسال</span>',
    rejected: '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">مرفوض</span>'
  };
  return map[status] || '<span class="badge">غير معروف</span>';
}

function renderReviewWorkflowActions(r) {
  if (r.reply_status === 'pending_approval') {
    return `
      <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
        <button class="btn btn-sm btn-success" onclick="approveReviewReply('${r.id}')">اعتماد الرد</button>
        <button class="btn btn-sm btn-danger" onclick="rejectReviewReply('${r.id}')">رفض الرد</button>
      </div>
    `;
  }
  if (r.reply_status === 'approved') {
    return `
      <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
        <button class="btn btn-sm btn-primary" onclick="sendReviewReply('${r.id}')">تأكيد الإرسال</button>
      </div>
    `;
  }
  return '';
}

async function approveReviewReply(reviewId) {
  const result = await Swal.fire({
    title: 'اعتماد الرد',
    text: 'يمكنك تعديل نص الرد قبل الاعتماد أو تركه كما هو.',
    input: 'textarea',
    inputPlaceholder: 'اكتب النص المعدل هنا (اختياري)',
    icon: 'question',
    showCancelButton: true,
    confirmButtonText: 'اعتماد الرد',
    cancelButtonText: 'إلغاء',
    background: 'var(--surface)',
    color: 'var(--text)',
    confirmButtonColor: 'var(--primary)',
  });

  if (!result.isConfirmed) return;

  const payload = { action: 'approve' };
  const customReply = (result.value || '').trim();
  if (customReply) {
    payload.final_reply_text = customReply;
  }

  try {
    await apiFetch(`/hotels/${HOTEL_ID}/reviews/${reviewId}/reply-decision`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    showToast('تم اعتماد الرد');
    loadReviews();
  } catch (e) {
    showToast('فشل اعتماد الرد', 'error');
  }
}

async function rejectReviewReply(reviewId) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/reviews/${reviewId}/reply-decision`, {
      method: 'PATCH',
      body: JSON.stringify({ action: 'reject' }),
    });
    showToast('تم رفض الرد');
    loadReviews();
  } catch (e) {
    showToast('فشل رفض الرد', 'error');
  }
}

async function sendReviewReply(reviewId) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/reviews/${reviewId}/reply-decision`, {
      method: 'PATCH',
      body: JSON.stringify({ action: 'send' }),
    });
    showToast('تم تسجيل الإرسال');
    loadReviews();
  } catch (e) {
    showToast('فشل تسجيل الإرسال', 'error');
  }
}

function renderStars(rating) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty);
}

