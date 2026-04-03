// ══════════════════════════════════════════════
//  PAGE: GUESTS
// ══════════════════════════════════════════════
async function loadGuests() {
  if (!HOTEL_ID) return;
  document.getElementById('content').innerHTML = `
    <div class="table-card">
      <div class="table-header">
        <h3>👥 الضيوف</h3>
        <div style="display:flex;gap:10px;align-items:center">
          <input type="text" id="guest-search" placeholder="بحث بالاسم أو الرقم..."
            style="padding:8px 14px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);width:220px"
            oninput="searchGuests(this.value)" />
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>الاسم</th><th>الجوال</th><th>الجنسية</th><th>رقم الهوية</th><th>عدد الزيارات</th><th>تاريخ التسجيل</th><th>إجراء</th>
          </tr>
        </thead>
        <tbody id="guests-tbody">
          <tr><td colspan="7"><div class="loading-text">جاري جلب بيانات الضيوف...</div></td></tr>
        </tbody>
      </table>
    </div>`;

  await fetchGuests('');
}

async function fetchGuests(search) {
  try {
    const url = `/hotels/${HOTEL_ID}/guests?limit=100${search ? '&search=' + encodeURIComponent(search) : ''}`;
    const data = await apiFetch(url);
    const guests = data.guests || [];
    const tbody = document.getElementById('guests-tbody');
    if (!tbody) return;

    if (guests.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:30px;color:var(--text-dim)">لا يوجد ضيوف بعد</td></tr>';
      return;
    }

    tbody.innerHTML = guests.map(g => `
      <tr>
        <td><strong>${g.name || '—'}</strong></td>
        <td style="direction:ltr;text-align:right">${g.phone || '—'}</td>
        <td>${g.nationality || '—'}</td>
        <td>${g.id_number || '—'}</td>
        <td><span class="badge badge-confirmed">${g.total_stays || 0} زيارة</span></td>
        <td>${fmtDate(g.created_at)}</td>
        <td>
          <button class="btn btn-sm btn-primary" onclick="showGuestDetails('${g.id}')">👁️ تفاصيل</button>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    showToast('فشل تحميل الضيوف', 'error');
  }
}

let guestSearchTimer;
function searchGuests(val) {
  clearTimeout(guestSearchTimer);
  guestSearchTimer = setTimeout(() => fetchGuests(val), 400);
}

async function showGuestDetails(guestId) {
  try {
    const g = await apiFetch(`/hotels/${HOTEL_ID}/guests/${guestId}`);
    const body = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div class="form-group">
          <label>الاسم</label>
          <input type="text" id="ge-name" value="${g.name || ''}" />
        </div>
        <div class="form-group">
          <label>الجوال</label>
          <input type="text" value="${g.phone || ''}" disabled style="opacity:0.6" />
        </div>
        <div class="form-group">
          <label>الجنسية</label>
          <input type="text" id="ge-nat" value="${g.nationality || ''}" />
        </div>
        <div class="form-group">
          <label>نوع المستند</label>
          <select id="ge-idtype">
            <option value="" ${!g.id_type ? 'selected' : ''}>— اختر —</option>
            <option value="هوية" ${g.id_type === 'هوية' ? 'selected' : ''}>هوية وطنية</option>
            <option value="جواز" ${g.id_type === 'جواز' ? 'selected' : ''}>جواز سفر</option>
            <option value="إقامة" ${g.id_type === 'إقامة' ? 'selected' : ''}>إقامة</option>
          </select>
        </div>
        <div class="form-group">
          <label>رقم المستند</label>
          <input type="text" id="ge-idnum" value="${g.id_number || ''}" />
        </div>
        <div class="form-group">
          <label>البريد الإلكتروني</label>
          <input type="email" id="ge-email" value="${g.email || ''}" />
        </div>
        <div class="form-group" style="grid-column:1/-1">
          <label>ملاحظات</label>
          <textarea id="ge-notes" rows="3" style="width:100%;padding:10px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);resize:vertical">${g.notes || ''}</textarea>
        </div>
      </div>
      <div style="margin-top:16px;display:flex;gap:16px;flex-wrap:wrap">
        <div class="kpi-card blue" style="flex:1;min-width:140px">
          <div class="kpi-icon">🔢</div>
          <div class="kpi-label">عدد الزيارات</div>
          <div class="kpi-value">${g.total_stays || 0}</div>
        </div>
        <div class="kpi-card purple" style="flex:1;min-width:140px">
          <div class="kpi-icon">📅</div>
          <div class="kpi-label">تاريخ التسجيل</div>
          <div class="kpi-value" style="font-size:14px">${fmtDate(g.created_at)}</div>
        </div>
      </div>`;
    const foot = `
      <div style="display:flex; justify-content:space-between; width:100%">
        <button class="btn btn-danger" onclick="deleteGuest('${guestId}')">🗑️ مسح الضيف</button>
        <div style="display:flex; gap:8px">
          <button class="btn" onclick="closeModal()">إلغاء</button>
          <button class="btn btn-primary" onclick="saveGuest('${guestId}')">💾 حفظ التعديلات</button>
        </div>
      </div>`;
    openModal('👤 بيانات الضيف', body, foot);
  } catch (e) {
    showToast('فشل تحميل بيانات الضيف', 'error');
  }
}

async function saveGuest(guestId) {
  const data = {
    name: document.getElementById('ge-name').value,
    nationality: document.getElementById('ge-nat').value,
    id_type: document.getElementById('ge-idtype').value,
    id_number: document.getElementById('ge-idnum').value,
    email: document.getElementById('ge-email').value,
    notes: document.getElementById('ge-notes').value,
  };
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/guests/${guestId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    showToast('تم حفظ بيانات الضيف بنجاح');
    closeModal();
    loadGuests();
  } catch (e) {
    showToast('فشل حفظ البيانات', 'error');
  }
}

function deleteGuest(guestId) {
  confirmAction('مسح الضيف؟', 'هل أنت متأكد من مسح بيانات هذا الضيف نهائياً؟', 'نعم، امسح', async () => {
    try {
      await apiFetch(`/hotels/${HOTEL_ID}/guests/${guestId}`, { method: 'DELETE' });
      showToast('تم مسح الضيف بنجاح');
      closeModal();
      loadGuests();
    } catch (e) {
      showToast('فشل في مسح الضيف', 'error');
    }
  });
}


