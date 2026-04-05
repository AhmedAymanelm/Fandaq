// ══════════════════════════════════════════════
//  PAGE: ROOM SETUP
// ══════════════════════════════════════════════
async function loadRoomSetup() {
  if (!HOTEL_ID) return;
  const [types, rooms] = await Promise.all([
    apiFetch(`/hotels/${HOTEL_ID}/room-types`).catch(() => []),
    apiFetch(`/hotels/${HOTEL_ID}/rooms`).catch(() => [])
  ]);
  GLOBAL_DATA.all_types = types;
  GLOBAL_DATA.all_rooms = rooms;

  destroyCharts();
  document.getElementById('content').innerHTML = `
    <div class="charts-grid" style="display:block;margin-bottom:24px">
      <div class="table-header" style="background:var(--card);border-radius:12px 12px 0 0;border:1px solid var(--border);border-bottom:none">
        <div><h3>🗂️ أنواع الغرف (<span id="types-count">${types.length}</span>)</h3></div>
        <div style="display:flex;gap:10px">
          <input type="text" class="search-input" placeholder="🔍 بحث عن نوع..." oninput="filterTypes(this.value)">
          <button class="btn btn-primary btn-sm" onclick="showAddRoomTypeModal()">➕ نوع جديد</button>
        </div>
      </div>
      <div class="table-card" style="border-radius:0 0 12px 12px;border-top:none">
        <table><thead><tr><th>النوع</th><th>السعة</th><th>السعر اليومي</th><th>السعر الشهري</th><th>العدد الكلي</th><th>إجراء</th></tr></thead>
        <tbody id="types-tbody">${renderTypesMarkup(types)}</tbody></table>
      </div>
    </div>
    
    <div class="charts-grid" style="display:block">
      <div class="table-header" style="background:var(--card);border-radius:12px 12px 0 0;border:1px solid var(--border);border-bottom:none">
        <div><h3>🛏️ الغرف الفعلية (<span id="setup-rooms-count">${rooms.length}</span>)</h3></div>
        <div style="display:flex;gap:10px">
          <input type="text" class="search-input" placeholder="🔍 بحث عن غرفة..." oninput="filterSetupRooms(this.value)">
          <button class="btn btn-primary btn-sm" onclick="showAddRoomModal()">➕ إضافة غرفة</button>
        </div>
      </div>
      <div class="table-card" style="border-radius:0 0 12px 12px;border-top:none">
        <table><thead><tr><th>رقم الغرفة</th><th>النوع</th><th>الحالة الحالية</th><th>إجراء</th></tr></thead>
        <tbody id="setup-rooms-tbody">${renderSetupRoomsMarkup(rooms)}</tbody></table>
      </div>
    </div>
  `;
}
function filterTypes(q) {
  const query = q.toLowerCase();
  const f = GLOBAL_DATA.all_types.filter(t => t.name.toLowerCase().includes(query) || nameToAr(t.name).includes(query));
  document.getElementById('types-tbody').innerHTML = renderTypesMarkup(f);
  document.getElementById('types-count').textContent = f.length;
}
function renderTypesMarkup(types) {
  if (!types.length) return '<tr><td colspan="6"><div class="empty-state">لا توجد نتائج</div></td></tr>';
  return types.map(t => `
    <tr><td><strong>${nameToAr(t.name)}</strong> <span style="font-size:10px;color:var(--muted)">(${t.name})</span></td>
    <td>${t.capacity} أفراد</td>
    <td>${fmtMoney(t.daily_rate)}</td>
    <td>${fmtMoney(t.monthly_rate)}</td>
    <td>${t.total_units}</td>
    <td style="display:flex;gap:4px">
      <button class="btn btn-primary btn-sm" onclick="showEditRoomTypeModal('${t.id}')">✏️</button>
      <button class="btn btn-danger btn-sm" onclick="removeRoomType('${t.id}')">🗑️</button>
    </td></tr>`).join('');
}
function filterSetupRooms(q) {
  const query = q.toLowerCase();
  const f = GLOBAL_DATA.all_rooms.filter(r => String(r.room_number).toLowerCase().includes(query) || (r.room_type && nameToAr(r.room_type.name).includes(query)));
  document.getElementById('setup-rooms-tbody').innerHTML = renderSetupRoomsMarkup(f);
  document.getElementById('setup-rooms-count').textContent = f.length;
}
function renderSetupRoomsMarkup(rooms) {
  if (!rooms.length) return '<tr><td colspan="4"><div class="empty-state">لا توجد نتائج</div></td></tr>';
  return rooms.map(r => `
    <tr><td style="font-family:monospace;font-size:15px"><strong>${r.room_number}</strong></td>
    <td>${r.room_type ? nameToAr(r.room_type.name) : '—'}</td>
    <td>${badgeHtml(r.status)}</td>
    <td><button class="btn btn-danger btn-sm" onclick="removeRoom('${r.id}')">🗑️</button></td></tr>`).join('');
}

function removeRoom(id) {
  confirmAction('حذف الغرفة؟', 'سيؤدي هذا إلى حذف الغرفة نهائياً من النظام.', 'نعم، احذف', () => {
    apiFetch(`/hotels/${HOTEL_ID}/rooms/${id}`, { method: 'DELETE' })
      .then(() => {
        showToast('تم حذف الغرفة');
        loadRoomSetup();
      }).catch(e => showToast('فشل الحذف، قد يكون لها حجوزات نشطة', 'error'));
  });
}

function showAddRoomTypeModal() {
  const presetOptions = [
    { value: 'single', icon: '🛏️', title: 'فردية', subtitle: 'سرير واحد' },
    { value: 'double', icon: '🛌', title: 'دبل', subtitle: 'سريرين' },
    { value: 'suite', icon: '👑', title: 'جناح', subtitle: 'Premium Suite' },
    { value: 'one-bedroom', icon: '🏠', title: 'غرفة وصالة', subtitle: 'One-bedroom' },
    { value: 'two-bedroom', icon: '🏢', title: 'غرفتين وصالة', subtitle: 'Two-bedroom' },
    { value: 'three-bedroom', icon: '🏘️', title: 'ثلاث غرف وصالة', subtitle: 'Three-bedroom' },
    { value: '__custom__', icon: '✨', title: 'مخصص', subtitle: 'اكتب اسم النوع بنفسك' },
  ];

  const cardsHtml = presetOptions.map((o, idx) => `
    <button
      type="button"
      data-room-preset="${o.value}"
      onclick="selectRoomTypePreset('${o.value}')"
      style="
        border:1px solid ${idx === 0 ? 'var(--primary)' : 'var(--border)'};
        background:${idx === 0 ? 'rgba(124,58,237,0.18)' : 'rgba(255,255,255,0.02)'};
        border-radius:12px;
        padding:10px;
        text-align:right;
        cursor:pointer;
        color:var(--text);
        transition:all .2s ease;
      "
    >
      <div style="display:flex;align-items:center;gap:8px;font-weight:700">
        <span>${o.icon}</span>
        <span>${o.title}</span>
      </div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:4px">${o.subtitle}</div>
    </button>
  `).join('');

  const body = `
    <div class="form-group">
      <label>نوع الغرفة</label>
      <input type="hidden" id="m-rt-preset" value="single">
      <div style="
        display:grid;
        grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
        gap:10px;
      ">${cardsHtml}</div>
    </div>
    <div class="form-group" id="m-rt-custom-wrap" style="display:none">
      <label>اسم النوع المخصص</label>
      <input type="text" id="m-rt-custom-name" placeholder="مثال: family-suite أو جناح عائلي">
    </div>
    <div class="form-group"><label>السعة (عدد الأفراد)</label><input type="number" id="m-rt-cap" value="2"></div>
    <div class="form-group"><label>السعر اليومي</label><input type="number" id="m-rt-d" value="500"></div>
    <div class="form-group"><label>السعر الشهري</label><input type="number" id="m-rt-m" value="12000"></div>
    <div class="form-group"><label>عدد الوحدات المتوفرة</label><input type="number" id="m-rt-u" value="5"></div>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitRoomType()">حفظ النوع</button>`;
  openModal('➕ إضافة نوع غرف جديد', body, foot);
  onRoomTypePresetChange();
}

function selectRoomTypePreset(preset) {
  const hiddenPreset = document.getElementById('m-rt-preset');
  if (!hiddenPreset) return;
  hiddenPreset.value = preset;

  document.querySelectorAll('[data-room-preset]').forEach(el => {
    const isActive = el.getAttribute('data-room-preset') === preset;
    el.style.borderColor = isActive ? 'var(--primary)' : 'var(--border)';
    el.style.background = isActive ? 'rgba(124,58,237,0.18)' : 'rgba(255,255,255,0.02)';
  });

  onRoomTypePresetChange();
}

function onRoomTypePresetChange() {
  const presetEl = document.getElementById('m-rt-preset');
  const customWrapEl = document.getElementById('m-rt-custom-wrap');
  const capEl = document.getElementById('m-rt-cap');
  if (!presetEl || !customWrapEl || !capEl) return;

  const preset = presetEl.value;
  customWrapEl.style.display = preset === '__custom__' ? 'block' : 'none';

  const capacityDefaults = {
    single: 1,
    double: 2,
    suite: 3,
    'one-bedroom': 2,
    'two-bedroom': 4,
    'three-bedroom': 6,
  };

  if (capacityDefaults[preset]) {
    capEl.value = capacityDefaults[preset];
  }
}

function submitRoomType() {
  const preset = document.getElementById('m-rt-preset').value;
  const customName = (document.getElementById('m-rt-custom-name')?.value || '').trim();
  const name = preset === '__custom__' ? customName : preset;
  const cap = document.getElementById('m-rt-cap').value;
  const dRate = document.getElementById('m-rt-d').value;
  const mRate = document.getElementById('m-rt-m').value;
  const units = document.getElementById('m-rt-u').value;
  if (!name || !cap || !dRate || !mRate || !units) return showToast('أكمل جميع الحقول', 'error');
  closeModal();
  addRoomType({ name, capacity: parseInt(cap), daily_rate: parseFloat(dRate), monthly_rate: parseFloat(mRate), total_units: parseInt(units) });
}
async function addRoomType(data) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/room-types`, { method: 'POST', body: JSON.stringify(data) });
    showToast('تمت إضافة النوع');
    ROOM_TYPES = {}; // invalidate cache to fetch next time, or just update it
    const rtRes = await fetch(`${API}/hotels/${HOTEL_ID}/room-types`);
    const rtData = await rtRes.json();
    if (Array.isArray(rtData)) rtData.forEach(rt => { ROOM_TYPES[rt.id] = rt.name; });
    loadRoomSetup();
  } catch (e) { showToast('فشل الإضافة', 'error'); }
}

function showEditRoomTypeModal(id) {
  const rt = GLOBAL_DATA.all_types.find(x => x.id === id);
  if (!rt) return;
  const body = `
    <div class="form-group"><label>السعة (عدد الأفراد)</label><input type="number" id="e-rt-cap" value="${rt.capacity}"></div>
    <div class="form-group"><label>السعر اليومي</label><input type="number" id="e-rt-d" value="${rt.daily_rate}"></div>
    <div class="form-group"><label>السعر الشهري</label><input type="number" id="e-rt-m" value="${rt.monthly_rate}"></div>
    <div class="form-group"><label>عدد الوحدات المتوفرة</label><input type="number" id="e-rt-u" value="${rt.total_units}"></div>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitEditRoomType('${id}')">حفظ التعديلات</button>`;
  openModal('✏️ تعديل بيانات النوع', body, foot);
}

async function submitEditRoomType(id) {
  const cap = document.getElementById('e-rt-cap').value;
  const dRate = document.getElementById('e-rt-d').value;
  const mRate = document.getElementById('e-rt-m').value;
  const units = document.getElementById('e-rt-u').value;
  if (!cap || !dRate || !mRate || !units) return showToast('أكمل جميع الحقول', 'error');
  closeModal();
  
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/room-types/${id}`, { 
      method: 'PUT', 
      body: JSON.stringify({ 
        capacity: parseInt(cap), 
        daily_rate: parseFloat(dRate), 
        monthly_rate: parseFloat(mRate), 
        total_units: parseInt(units) 
      }) 
    });
    showToast('تم تعديل بيانات النوع بنجاح');
    loadRoomSetup();
  } catch (e) { showToast('فشل التعديل', 'error'); }
}

function removeRoomType(id) {
  confirmAction('حذف نوع الغرفة؟', 'سيؤدي هذا إلى حذف النوع نهائياً. تأكد أنه غير مرتبط بغرف أو حجوزات نشطة.', 'نعم، احذف', () => {
    apiFetch(`/hotels/${HOTEL_ID}/room-types/${id}`, { method: 'DELETE' })
      .then(() => {
        showToast('تم حذف نوع الغرفة');
        // invalidate cache 
        ROOM_TYPES = {};
        fetch(`${API}/hotels/${HOTEL_ID}/room-types`).then(r => r.json()).then(rtData => {
          if (Array.isArray(rtData)) rtData.forEach(rt => { ROOM_TYPES[rt.id] = rt.name; });
        });
        loadRoomSetup();
      }).catch(e => showToast('فشل الحذف، قد يكون مرتبط بحجوزات أو غرف', 'error'));
  });
}

async function showAddRoomModal() {
  const rts = await apiFetch(`/hotels/${HOTEL_ID}/room-types`).catch(() => []);
  if (!rts.length) { showToast('يجب إضافة أنواع غرف أولاً', 'error'); return; }

  const opts = rts.map(rt => `<option value="${rt.id}">${nameToAr(rt.name)}</option>`).join('');
  const body = `
    <div class="form-group"><label>رقم الغرفة</label><input type="text" id="m-r-num" placeholder="مثال: 101"></div>
    <div class="form-group"><label>نوع الغرفة</label>
      <select id="m-r-type" style="width:100%;padding:10px">${opts}</select>
    </div>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitRoom()">إضافة</button>`;
  openModal('➕ إضافة غرفة فعلية', body, foot);
}
function submitRoom() {
  const num = document.getElementById('m-r-num').value;
  const typeId = document.getElementById('m-r-type').value;
  if (!num) return showToast('أدخل رقم الغرفة', 'error');
  closeModal(); addRoom(typeId, num);
}
async function addRoom(typeId, num) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/rooms`, { method: 'POST', body: JSON.stringify({ room_type_id: typeId, room_number: num }) });
    showToast('تم إضافة الغرفة'); loadRoomSetup();
  } catch (e) { showToast('فشل الإضافة', 'error'); }
}

