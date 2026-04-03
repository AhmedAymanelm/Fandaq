// ══════════════════════════════════════════════
//  PAGE: COMPLAINTS & REQUESTS
// ══════════════════════════════════════════════
let compTab = 'complaints';
async function loadComplaints() {
  if (!HOTEL_ID) return;
  
  // Show temporary loading if it's the first render
  if(!document.getElementById('comp-content')) {
      document.getElementById('content').innerHTML = '<div class="loading-text" style="text-align:center;padding:40px">جاري جلب البيانات...</div>';
  }

  const [comps, reqs] = await Promise.all([
    apiFetch(`/hotels/${HOTEL_ID}/complaints?limit=100`, { useCache: true }).catch(() => ({ complaints: [] })),
    apiFetch(`/hotels/${HOTEL_ID}/guest-requests?limit=100`, { useCache: true }).catch(() => ({ requests: [] }))
  ]);
  const complaints = comps.complaints || []; const requests = reqs.requests || [];
  GLOBAL_DATA.all_comps = complaints; GLOBAL_DATA.all_reqs = requests;
  
  renderCompReqUI();
}

function renderCompReqUI() {
  const openC = GLOBAL_DATA.all_comps.filter(c => c.status === 'open').length;
  const openR = GLOBAL_DATA.all_reqs.filter(r => r.status === 'open').length;

  document.getElementById('content').innerHTML = `
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
  if (!list.length) return '<div class="empty-state"><div class="emoji">🎉</div>لا توجد شكاوى</div>';
  return `<div class="table-card"><table><thead><tr><th>الغرفة والضيف</th><th>النص</th><th>التاريخ</th><th>الحالة</th><th>تحديث</th></tr></thead>
    <tbody>${list.map(c => {
      let guestInfo = '<span style="color:var(--text-muted);font-size:12px">غير محدد</span>';
      if (c.guest_name) {
          guestInfo = `<strong>${c.guest_name}</strong>`;
          if (c.room_number) guestInfo += `<br><span style="background:var(--danger);color:#fff;padding:2px 6px;border-radius:4px;font-size:11px">غرفة ${c.room_number}</span>`;
          else guestInfo += `<br><span style="color:var(--text-muted);font-size:11px">بدون غرفة حالياً</span>`;
      }
      return `<tr>
      <td>${guestInfo}</td>
      <td style="max-width:300px">${c.text}</td><td>${fmtDate(c.created_at)}</td>
      <td>${badgeHtml(c.status)}</td>
      <td><select onchange="updateComplaint('${c.id}', this.value)" style="font-size:11px">
        <option value="open" ${c.status === 'open' ? 'selected' : ''}>مفتوح</option>
        <option value="in_progress" ${c.status === 'in_progress' ? 'selected' : ''}>جاري</option>
        <option value="resolved" ${c.status === 'resolved' ? 'selected' : ''}>تم الحل</option>
      </select></td></tr>`
    }).join('')}</tbody></table></div>`;
}

function renderRequests(list) {
  if (!list.length) return '<div class="empty-state"><div class="emoji">✅</div>لا توجد طلبات</div>';
  return `<div class="table-card"><table><thead><tr><th>نوع الطلب</th><th>التفاصيل</th><th>التاريخ</th><th>الحالة</th></tr></thead>
    <tbody>${list.map(r => `<tr>
      <td><strong>${r.request_type}</strong></td><td>${r.details || '—'}</td>
      <td>${fmtDate(r.created_at)}</td><td>${badgeHtml(r.status)}</td></tr>`).join('')}</tbody></table></div>`;
}

function setCompTab(t) { 
    compTab = t; 
    renderCompReqUI(); 
}
async function updateComplaint(id, status) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/complaints/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
    showToast('تم تحديث حالة الشكوى'); 
    
    // Update local state instantly to avoid delays and clears cache
    if(typeof clearApiCache === 'function') clearApiCache();
    const c = GLOBAL_DATA.all_comps.find(x => x.id === id);
    if(c) c.status = status;
    
    renderCompReqUI();
    loadBadges();
  } catch (e) { showToast('فشل التحديث', 'error'); }
}

