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
        ${r.comment ? `<p style="margin:0;color:var(--text);line-height:1.6">${r.comment}</p>` : '<p style="margin:0;color:var(--text-dim);font-style:italic">بدون تعليق</p>'}
        ${r.ai_reply_suggestion ? `
        <div style="margin-top:12px;padding:12px;background:rgba(59, 130, 246, 0.1);border-left:3px solid var(--primary);border-radius:0 8px 8px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:12px;font-weight:bold;color:var(--primary)">🤖 رد مقترح من الذكاء الاصطناعي</span>
            <button onclick="navigator.clipboard.writeText('${r.ai_reply_suggestion.replace(/'/g, "\\'").replace(/\n/g, '\\n')}'); showToast('تم نسخ الرد بنجاح');" 
              style="background:var(--primary);color:#fff;border:none;border-radius:4px;padding:4px 8px;font-size:12px;cursor:pointer;">
              نسخ 📋
            </button>
          </div>
          <p style="margin:0;color:var(--text);font-size:13px;line-height:1.5">${r.ai_reply_suggestion.replace(/\n/g, '<br>')}</p>
        </div>` : ''}
      </div>
    `;}).join('');
  } catch (e) {
    document.getElementById('reviews-list').innerHTML =
      '<div style="text-align:center;padding:30px;color:var(--text-dim)">فشل تحميل التقييمات</div>';
  }
}

function renderStars(rating) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty);
}

