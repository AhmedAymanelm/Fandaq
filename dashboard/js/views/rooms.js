// ══════════════════════════════════════════════
//  PAGE: ROOMS
// ══════════════════════════════════════════════

let roomFilterStatus = 'all';
async function loadRooms() {
  if (!HOTEL_ID) return;
  const rooms = await apiFetch(`/hotels/${HOTEL_ID}/rooms`).catch(() => []);
  GLOBAL_DATA.all_rooms = rooms;
  const avail = rooms.filter(r => r.status === 'available').length;
  const occ = rooms.filter(r => r.status === 'occupied').length;
  const maint = rooms.filter(r => r.status === 'maintenance').length;

  document.getElementById('content').innerHTML = `
    <div class="rooms-summary">
      <div class="kpi-card green"><div class="kpi-icon">🟢</div><div class="kpi-label">متاحة</div>
        <div class="kpi-value">${avail}</div></div>
      <div class="kpi-card red"><div class="kpi-icon">🔴</div><div class="kpi-label">مشغولة</div>
        <div class="kpi-value">${occ}</div></div>
      <div class="kpi-card orange"><div class="kpi-icon">🟡</div><div class="kpi-label">صيانة</div>
        <div class="kpi-value">${maint}</div></div>
    </div>
    
    <div class="filter-bar" style="margin-bottom:16px">
      <button id="rf-all" class="filter-btn room-filter-btn ${roomFilterStatus === 'all' ? 'active' : ''}" onclick="setRoomFilter('all')">الكل</button>
      <button id="rf-available" class="filter-btn room-filter-btn ${roomFilterStatus === 'available' ? 'active' : ''}" onclick="setRoomFilter('available')">🟢 متاح (${avail})</button>
      <button id="rf-occupied" class="filter-btn room-filter-btn ${roomFilterStatus === 'occupied' ? 'active' : ''}" onclick="setRoomFilter('occupied')">🔴 مشغول (${occ})</button>
      <button id="rf-maintenance" class="filter-btn room-filter-btn ${roomFilterStatus === 'maintenance' ? 'active' : ''}" onclick="setRoomFilter('maintenance')">🟡 صيانة (${maint})</button>
    </div>
    
    <div class="table-header" style="background:none; border:none; padding: 0 0 16px 0">
      <div class="section-title" style="margin:0">🛏️ جميع الغرف (${rooms.length})</div>
      <input type="text" id="search-room" class="search-input" placeholder="🔍 بحث عن غرفة أو نوع..." oninput="filterRooms(this.value)">
    </div>
    <div class="rooms-grid" id="rooms-grid-container">
      ${renderRoomsMarkup(rooms)}
    </div>`;
}
function setRoomFilter(f) {
  roomFilterStatus = f;
  document.querySelectorAll('.room-filter-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('rf-' + f)?.classList.add('active');
  filterRooms(document.getElementById('search-room')?.value || '');
}
function filterRooms(q) {
  const query = (q || '').toLowerCase();
  const filtered = GLOBAL_DATA.all_rooms.filter(r =>
    (roomFilterStatus === 'all' || r.status === roomFilterStatus) &&
    (String(r.room_number).toLowerCase().includes(query) ||
      (r.room_type && roomTypeLabel(r.room_type.name).includes(query)) ||
      (r.room_type && r.room_type.name.toLowerCase().includes(query)))
  );
  document.getElementById('rooms-grid-container').innerHTML = renderRoomsMarkup(filtered);
}
function renderRoomsMarkup(rooms) {
  if (!rooms.length) return '<div class="empty-state" style="grid-column:1/-1"><div class="emoji">🛏️</div>لا توجد غرف للبحث المطلوب</div>';
  return rooms.map(r => `
      <div class="room-card ${r.status}" id="rcard-${r.id}">
        <div class="room-number">غرفة ${r.room_number}</div>
        <div class="room-type">${r.room_type ? roomTypeLabel(r.room_type.name) : '—'}</div>
        ${badgeHtml(r.status)}
        <select class="room-status-select" style="margin-top:10px" onchange="changeRoomStatus('${r.id}', this.value)">
          <option value="available" ${r.status === 'available' ? 'selected' : ''}>متاح</option>
          <option value="occupied" ${r.status === 'occupied' ? 'selected' : ''}>مشغول</option>
          <option value="maintenance" ${r.status === 'maintenance' ? 'selected' : ''}>صيانة</option>
        </select>
      </div>`).join('');
}
async function changeRoomStatus(id, status) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/rooms/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
    showToast('تم تحديث حالة الغرفة'); setTimeout(loadRooms, 300);
  } catch (e) { showToast('فشل التحديث', 'error'); }
}

