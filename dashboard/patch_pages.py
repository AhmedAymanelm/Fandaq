import re

with open('js/pages.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Rooms
room_target = """    <div class="section-title">🛏️ جميع الغرف (${rooms.length})</div>
    <div class="rooms-grid">${rooms.map(r => `
      <div class="room-card ${r.status}" id="rcard-${r.id}">
        <div class="room-number">غرفة ${r.room_number}</div>
        <div class="room-type">${r.room_type ? roomTypeLabel(r.room_type.name) : '—'}</div>
        ${badgeHtml(r.status)}
        <select class="room-status-select" style="margin-top:10px" onchange="changeRoomStatus('${r.id}', this.value)">
          <option value="available" ${r.status==='available'?'selected':''}>متاح</option>
          <option value="occupied" ${r.status==='occupied'?'selected':''}>مشغول</option>
          <option value="maintenance" ${r.status==='maintenance'?'selected':''}>صيانة</option>
        </select>
      </div>`).join('')}
    ${!rooms.length ? '<div class="empty-state"><div class="emoji">🛏️</div>لا توجد غرف مسجلة</div>' : ''}</div>`;
}"""

room_replacement = """    <div class="table-header" style="background:none; border:none; padding: 0 0 16px 0">
      <div class="section-title" style="margin:0">🛏️ جميع الغرف (${rooms.length})</div>
      <input type="text" class="search-input" placeholder="🔍 بحث عن غرفة أو نوع..." oninput="filterRooms(this.value)">
    </div>
    <div class="rooms-grid" id="rooms-grid-container">
      ${renderRoomsMarkup(rooms)}
    </div>`;
}
function filterRooms(q) {
  const query = q.toLowerCase();
  const filtered = GLOBAL_DATA.all_rooms.filter(r => 
    String(r.room_number).toLowerCase().includes(query) || 
    (r.room_type && roomTypeLabel(r.room_type.name).includes(query)) ||
    (r.room_type && r.room_type.name.toLowerCase().includes(query))
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
          <option value="available" ${r.status==='available'?'selected':''}>متاح</option>
          <option value="occupied" ${r.status==='occupied'?'selected':''}>مشغول</option>
          <option value="maintenance" ${r.status==='maintenance'?'selected':''}>صيانة</option>
        </select>
      </div>`).join('');
}"""

code = code.replace("  const avail = rooms.filter(r=>r.status==='available').length;", "  GLOBAL_DATA.all_rooms = rooms;\n  const avail = rooms.filter(r=>r.status==='available').length;")
code = code.replace(room_target, room_replacement)

# 2. Reservations
res_target = """      <div class="table-header">
        <div><h3>جميع الحجوزات</h3><span style="color:var(--muted);font-size:13px">${all.length} حجز</span></div>
        <button class="btn btn-primary btn-sm" onclick="showAddReservationModal()">➕ إضافة حجز يدوي</button>
      </div>
      <table><thead><tr><th>رقم الحجز</th><th>تاريخ الإنشاء</th><th>الدخول</th><th>الخروج</th><th>السعر</th><th>الحالة</th><th>إجراء</th></tr></thead>
      <tbody>${all.length ? all.map(r => `
        <tr><td style="font-family:monospace;color:var(--accent)">#${String(r.id).slice(0,6).toUpperCase()}</td>
        <td>${fmtDate(r.created_at)}</td><td>${fmtDate(r.check_in)}</td><td>${fmtDate(r.check_out)}</td>
        <td>${fmtMoney(r.total_price)}</td><td>${badgeHtml(r.status)}</td>
        <td>${r.status==='pending' ? `<button class="btn btn-success btn-sm" onclick="confirmRes('${r.id}')">✅</button>
          <button class="btn btn-danger btn-sm" onclick="rejectRes('${r.id}')">❌</button>` :
          r.status==='confirmed' ? `<button class="btn btn-danger btn-sm" onclick="cancelRes('${r.id}')">إلغاء</button>` : '—'}</td></tr>`).join('')
        : '<tr><td colspan="7"><div class="empty-state"><div class="emoji">📭</div>لا توجد حجوزات</div></td></tr>'}</tbody></table></div>`;
}"""

res_replacement = """      <div class="table-header">
        <div><h3>جميع الحجوزات</h3><span style="color:var(--muted);font-size:13px" id="res-count">${all.length} حجز</span></div>
        <div style="display:flex;gap:10px">
          <input type="text" class="search-input" style="width:200px" placeholder="🔍 بحث..." oninput="filterReservations(this.value)">
          <button class="btn btn-primary btn-sm" onclick="showAddReservationModal()">➕ إضافة حجز يدوي</button>
        </div>
      </div>
      <table><thead><tr><th>رقم الحجز</th><th>تاريخ الإنشاء</th><th>الدخول</th><th>الخروج</th><th>السعر</th><th>الحالة</th><th>إجراء</th></tr></thead>
      <tbody id="res-tbody">${renderResMarkup(all)}</tbody></table></div>`;
}
function filterReservations(q) {
  const query = q.toLowerCase();
  const filtered = GLOBAL_DATA.all_res.filter(r => 
    String(r.id).toLowerCase().includes(query) ||
    roomTypeLabel(r.room_type_id||'').includes(query) ||
    String(r.total_price).includes(query) ||
    fmtDate(r.check_in).includes(query)
  );
  document.getElementById('res-tbody').innerHTML = renderResMarkup(filtered);
  document.getElementById('res-count').textContent = filtered.length + ' حجز';
}
function renderResMarkup(all) {
  if (!all.length) return '<tr><td colspan="7"><div class="empty-state"><div class="emoji">📭</div>لا توجد حجوزات مطابقة</div></td></tr>';
  return all.map(r => `
    <tr><td style="font-family:monospace;color:var(--accent)">#${String(r.id).slice(0,6).toUpperCase()}</td>
    <td>${fmtDate(r.created_at)}</td><td>${fmtDate(r.check_in)}</td><td>${fmtDate(r.check_out)}</td>
    <td>${fmtMoney(r.total_price)}</td><td>${badgeHtml(r.status)}</td>
    <td>${r.status==='pending' ? `<button class="btn btn-success btn-sm" onclick="confirmRes('${r.id}')">✅</button>
      <button class="btn btn-danger btn-sm" onclick="rejectRes('${r.id}')">❌</button>` :
      r.status==='confirmed' ? `<button class="btn btn-danger btn-sm" onclick="cancelRes('${r.id}')">إلغاء</button>` : '—'}</td></tr>`).join('');
}"""

code = code.replace("const all = data.reservations || [];", "const all = data.reservations || [];\n  GLOBAL_DATA.all_res = all;")
code = code.replace(res_target, res_replacement)

with open('js/pages.js', 'w', encoding='utf-8') as f:
    f.write(code)
print('Phase 1 done')
