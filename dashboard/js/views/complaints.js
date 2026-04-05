// ══════════════════════════════════════════════
//  PAGE: COMPLAINTS & REQUESTS
// ══════════════════════════════════════════════
let compTab = 'complaints';
const SLA_FIRST_RESPONSE_MINUTES = 15;
const SLA_RESOLUTION_HOURS = 4;
async function loadComplaints() {
  if (!HOTEL_ID) return;
  
  // Show temporary loading if it's the first render
  if(!document.getElementById('comp-content')) {
      document.getElementById('content').innerHTML = '<div class="loading-text" style="text-align:center;padding:40px">جاري جلب البيانات...</div>';
  }

  const [comps, reqs] = await Promise.all([
    apiFetch(`/hotels/${HOTEL_ID}/complaints?limit=100`, { useCache: false }).catch(() => ({ complaints: [] })),
    apiFetch(`/hotels/${HOTEL_ID}/guest-requests?limit=100`, { useCache: false }).catch(() => ({ requests: [] }))
  ]);
  const complaints = comps.complaints || []; const requests = reqs.requests || [];
  GLOBAL_DATA.all_comps = complaints; GLOBAL_DATA.all_reqs = requests;
  
  renderCompReqUI();
}

function renderCompReqUI() {
  const openC = GLOBAL_DATA.all_comps.filter(c => c.status === 'open').length;
  const openR = GLOBAL_DATA.all_reqs.filter(r => r.status === 'open').length;
  const complaintBreaches = GLOBAL_DATA.all_comps.filter(isComplaintSlaBreached).length;
  const requestBreaches = GLOBAL_DATA.all_reqs.filter(isRequestSlaBreached).length;

  document.getElementById('content').innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:12px">
      <div class="stat-card" style="padding:10px 12px;border:1px solid rgba(239,68,68,.25)">
        <div style="font-size:12px;color:var(--text-muted)">تجاوزات SLA للشكاوى</div>
        <div style="font-size:22px;font-weight:700;color:var(--danger)">${complaintBreaches}</div>
      </div>
      <div class="stat-card" style="padding:10px 12px;border:1px solid rgba(245,158,11,.25)">
        <div style="font-size:12px;color:var(--text-muted)">تجاوزات SLA للطلبات</div>
        <div style="font-size:22px;font-weight:700;color:#f59e0b">${requestBreaches}</div>
      </div>
      <div class="stat-card" style="padding:10px 12px;border:1px solid rgba(16,185,129,.2)">
        <div style="font-size:12px;color:var(--text-muted)">هدف الاستجابة الأولى</div>
        <div style="font-size:18px;font-weight:700;color:#10b981">${SLA_FIRST_RESPONSE_MINUTES} دقيقة</div>
      </div>
      <div class="stat-card" style="padding:10px 12px;border:1px solid rgba(59,130,246,.2)">
        <div style="font-size:12px;color:var(--text-muted)">هدف الإغلاق</div>
        <div style="font-size:18px;font-weight:700;color:#3b82f6">${SLA_RESOLUTION_HOURS} ساعات</div>
      </div>
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
      <div class="comp-tabs" style="margin-bottom:0">
        <button class="comp-tab ${compTab === 'complaints' ? 'active' : ''}" onclick="setCompTab('complaints')">
          ⚠️ الشكاوى ${openC > 0 ? `<span class="nav-badge" style="display:inline-block">${openC}</span>` : ''}</button>
        <button class="comp-tab ${compTab === 'requests' ? 'active' : ''}" onclick="setCompTab('requests')">
          🔔 طلبات الخدمة ${openR > 0 ? `<span class="nav-badge" style="display:inline-block">${openR}</span>` : ''}</button>
      </div>
      <input type="text" class="search-input" id="comp-search" placeholder="🔍 بحث..." oninput="filterCompReq(this.value)">
    </div>
    <div id="comp-content">${compTab === 'complaints' ? renderComplaints(GLOBAL_DATA.all_comps) : renderRequests(GLOBAL_DATA.all_reqs)}</div>`;
    
  // Re-apply search filter if any
  const q = document.getElementById('comp-search')?.value;
  if(q) filterCompReq(q);
}

function filterCompReq(q) {
  const query = q.toLowerCase();
  if (compTab === 'complaints') {
    const filtered = GLOBAL_DATA.all_comps.filter(c => (c.text || '').toLowerCase().includes(query) || statusLabel(c.status).includes(query));
    document.getElementById('comp-content').innerHTML = renderComplaints(filtered);
  } else {
    const filtered = GLOBAL_DATA.all_reqs.filter(r => (r.request_type || '').toLowerCase().includes(query) || (r.details || '').toLowerCase().includes(query) || statusLabel(r.status).includes(query));
    document.getElementById('comp-content').innerHTML = renderRequests(filtered);
  }
}

function renderComplaints(list) {
  const canSeeActor = CURRENT_USER && ['admin', 'supervisor'].includes(CURRENT_USER.role);
  if (!list.length) return '<div class="empty-state"><div class="emoji">🎉</div>لا توجد شكاوى</div>';
  return `<div class="table-card"><table><thead><tr><th>الغرفة والضيف</th><th>النص</th><th>التاريخ</th><th>الحالة</th><th>SLA</th>${canSeeActor ? '<th>تم الحل بواسطة</th>' : ''}<th>تحديث</th></tr></thead>
    <tbody>${list.map(c => {
      let guestInfo = '<span style="color:var(--text-muted);font-size:12px">غير محدد</span>';
      if (c.guest_name) {
          guestInfo = `<strong>${c.guest_name}</strong>`;
          if (c.room_number) guestInfo += `<br><span style="background:var(--danger);color:#fff;padding:2px 6px;border-radius:4px;font-size:11px">غرفة ${c.room_number}</span>`;
          else guestInfo += `<br><span style="color:var(--text-muted);font-size:11px">بدون غرفة حالياً</span>`;
      }
      const sla = complaintSlaBadge(c);
      return `<tr>
      <td>${guestInfo}</td>
      <td style="max-width:300px">${c.text}</td><td>${fmtDate(c.created_at)}</td>
      <td>${badgeHtml(c.status)}</td>
      <td>${sla}</td>
      ${canSeeActor ? `<td>${c.resolved_by_name || '—'}</td>` : ''}
      <td><select onchange="updateComplaint('${c.id}', this.value)" style="font-size:11px">
        <option value="open" ${c.status === 'open' ? 'selected' : ''}>مفتوح</option>
        <option value="in_progress" ${c.status === 'in_progress' ? 'selected' : ''}>جاري</option>
        <option value="resolved" ${c.status === 'resolved' ? 'selected' : ''}>تم الحل</option>
      </select></td></tr>`
    }).join('')}</tbody></table></div>`;
}

function renderRequests(list) {
  if (!list.length) return '<div class="empty-state"><div class="emoji">✅</div>لا توجد طلبات</div>';
  return `<div class="table-card"><table><thead><tr><th>نوع الطلب</th><th>التفاصيل</th><th>التاريخ</th><th>الحالة</th><th>SLA</th></tr></thead>
    <tbody>${list.map(r => `<tr>
      <td><strong>${r.request_type}</strong></td><td>${r.details || '—'}</td>
      <td>${fmtDate(r.created_at)}</td><td>${badgeHtml(r.status)}</td><td>${requestSlaBadge(r)}</td></tr>`).join('')}</tbody></table></div>`;
}

function hoursBetween(start, end) {
  if (!start || !end) return null;
  const diff = (new Date(end).getTime() - new Date(start).getTime()) / 3600000;
  return Number.isFinite(diff) ? diff : null;
}

function complaintSlaBadge(c) {
  const firstResponseHours = hoursBetween(c.created_at, c.acknowledged_at);
  const resolutionHours = hoursBetween(c.created_at, c.resolved_at);
  const firstResponseOk = firstResponseHours !== null && firstResponseHours <= (SLA_FIRST_RESPONSE_MINUTES / 60);
  const resolutionOk = resolutionHours !== null && resolutionHours <= SLA_RESOLUTION_HOURS;

  if (c.status === 'open') {
    const ageHours = hoursBetween(c.created_at, new Date().toISOString()) || 0;
    if (ageHours > (SLA_FIRST_RESPONSE_MINUTES / 60)) {
      return '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">متأخر استجابة</span>';
    }
    return '<span class="badge" style="background:rgba(245,158,11,.2);color:#f59e0b;border:1px solid rgba(245,158,11,.35)">قيد المتابعة</span>';
  }

  if (c.status === 'in_progress') {
    return firstResponseOk
      ? '<span class="badge" style="background:rgba(16,185,129,.2);color:#34d399;border:1px solid rgba(16,185,129,.35)">استجابة ضمن SLA</span>'
      : '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">استجابة متأخرة</span>';
  }

  if (c.status === 'resolved') {
    if (firstResponseOk && resolutionOk) {
      return '<span class="badge" style="background:rgba(16,185,129,.2);color:#34d399;border:1px solid rgba(16,185,129,.35)">ملتزم SLA</span>';
    }
    return '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">تجاوز SLA</span>';
  }

  return '<span class="badge">—</span>';
}

function requestSlaBadge(r) {
  const firstResponseHours = hoursBetween(r.created_at, r.acknowledged_at);
  const completionHours = hoursBetween(r.created_at, r.completed_at);
  const firstResponseOk = firstResponseHours !== null && firstResponseHours <= (SLA_FIRST_RESPONSE_MINUTES / 60);
  const completionOk = completionHours !== null && completionHours <= SLA_RESOLUTION_HOURS;

  if (r.status === 'open') {
    const ageHours = hoursBetween(r.created_at, new Date().toISOString()) || 0;
    if (ageHours > (SLA_FIRST_RESPONSE_MINUTES / 60)) {
      return '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">متأخر استجابة</span>';
    }
    return '<span class="badge" style="background:rgba(245,158,11,.2);color:#f59e0b;border:1px solid rgba(245,158,11,.35)">بانتظار الاستجابة</span>';
  }

  if (r.status === 'in_progress') {
    return firstResponseOk
      ? '<span class="badge" style="background:rgba(16,185,129,.2);color:#34d399;border:1px solid rgba(16,185,129,.35)">استجابة ضمن SLA</span>'
      : '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">استجابة متأخرة</span>';
  }

  if (r.status === 'completed') {
    if (firstResponseOk && completionOk) {
      return '<span class="badge" style="background:rgba(16,185,129,.2);color:#34d399;border:1px solid rgba(16,185,129,.35)">ملتزم SLA</span>';
    }
    return '<span class="badge" style="background:rgba(239,68,68,.2);color:#f87171;border:1px solid rgba(239,68,68,.35)">تجاوز SLA</span>';
  }

  return '<span class="badge">—</span>';
}

function isComplaintSlaBreached(c) {
  const firstResponseHours = hoursBetween(c.created_at, c.acknowledged_at);
  const resolutionHours = hoursBetween(c.created_at, c.resolved_at);

  if (c.status === 'open') {
    const ageHours = hoursBetween(c.created_at, new Date().toISOString()) || 0;
    return ageHours > (SLA_FIRST_RESPONSE_MINUTES / 60);
  }

  if (firstResponseHours !== null && firstResponseHours > (SLA_FIRST_RESPONSE_MINUTES / 60)) {
    return true;
  }

  if (c.status === 'resolved' && resolutionHours !== null && resolutionHours > SLA_RESOLUTION_HOURS) {
    return true;
  }

  return false;
}

function isRequestSlaBreached(r) {
  const firstResponseHours = hoursBetween(r.created_at, r.acknowledged_at);
  const completionHours = hoursBetween(r.created_at, r.completed_at);

  if (r.status === 'open') {
    const ageHours = hoursBetween(r.created_at, new Date().toISOString()) || 0;
    return ageHours > (SLA_FIRST_RESPONSE_MINUTES / 60);
  }

  if (firstResponseHours !== null && firstResponseHours > (SLA_FIRST_RESPONSE_MINUTES / 60)) {
    return true;
  }

  if (r.status === 'completed' && completionHours !== null && completionHours > SLA_RESOLUTION_HOURS) {
    return true;
  }

  return false;
}

function setCompTab(t) { 
    compTab = t; 
    renderCompReqUI(); 
}
async function updateComplaint(id, status) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/complaints/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
    showToast('تم تحديث حالة الشكوى'); 

    // Refresh from backend so actor/status metadata stays accurate.
    if(typeof clearApiCache === 'function') clearApiCache();
    await loadComplaints();
    loadBadges();
  } catch (e) { showToast('فشل التحديث', 'error'); }
}

