// ══════════════════════════════════════════════
//  PAGE: HOTELS
// ══════════════════════════════════════════════
async function loadHotels() {
  const data = await apiFetch(`/hotels`).catch(() => ({ hotels: [] }));
  const hotels = data.hotels || [];
  GLOBAL_DATA.all_hotels = hotels;

  document.getElementById('content').innerHTML = `
    <div class="table-header" style="background:var(--card);border-radius:12px 12px 0 0;margin-bottom:0;border:1px solid var(--border);border-bottom:none">
      <div><h3>🌍 الفنادق المسجلة (<span id="hotels-count">${hotels.length}</span>)</h3></div>
      <div style="display:flex;gap:10px">
        <input type="text" class="search-input" placeholder="🔍 بحث عن فندق..." oninput="filterHotels(this.value)">
        <button class="btn btn-primary btn-sm" onclick="showAddHotelModal()">➕ إضافة فندق</button>
      </div>
    </div>
    <div class="table-card" style="border-radius:0 0 12px 12px;border-top:none">
      <table><thead><tr><th>الاسم</th><th>رقم الواتساب</th><th>رقم المالك</th><th>تاريخ الإنشاء</th><th>إجراء</th></tr></thead>
      <tbody id="hotels-tbody">${renderHotelsMarkup(hotels)}</tbody></table>
    </div>
  `;
}
function filterHotels(q) {
  const val = q.toLowerCase();
  const f = GLOBAL_DATA.all_hotels.filter(h => h.name.toLowerCase().includes(val) || (h.whatsapp_number || '').includes(val) || (h.owner_whatsapp || '').includes(val));
  document.getElementById('hotels-tbody').innerHTML = renderHotelsMarkup(f);
  document.getElementById('hotels-count').textContent = f.length;
}
function renderHotelsMarkup(hotels) {
  return hotels.length ? hotels.map(h => `
        <tr><td><strong>${h.name}</strong></td>
        <td style="direction:ltr;text-align:right">${h.whatsapp_number}</td>
        <td style="direction:ltr;text-align:right">${h.owner_whatsapp}</td>
        <td>${fmtDate(h.created_at)}</td>
        <td style="display:flex;gap:4px">
          <button class="btn btn-primary btn-sm" onclick="showEditHotelModal('${h.id}')">✏️</button>
          <button class="btn btn-danger btn-sm" onclick="deleteHotel('${h.id}','${h.name}')">🗑️</button>
        </td></tr>`).join('') :
    '<tr><td colspan="5"><div class="empty-state">لا توجد فنادق مطابقة</div></td></tr>';
}
function deleteHotel(id, name) {
  confirmAction('حذف فندق ' + name + '؟', 'سيتم حذف الفندق وجميع بياناته نهائياً. هل أنت متأكد؟', 'نعم، احذف', async () => {
    try {
      await apiFetch(`/hotels/${id}`, { method: 'DELETE' });
      showToast('تم حذف الفندق بنجاح');
      loadHotels();
    } catch (e) { showToast('فشل الحذف', 'error'); }
  });
}
function showAddHotelModal() {
  const body = `
    <div class="form-group"><label>اسم الفندق / الفرع</label><input type="text" id="m-h-name"></div>
    <div class="form-group"><label>رقم هاتف المالك (للإشعارات)</label><input type="text" id="m-h-owner" placeholder="مثال: 2010..."></div>
    <div class="form-group"><label>رقم واتساب الفندق</label><input type="text" id="m-h-wa" placeholder="مثال: 966500000000"></div>
    <div class="form-group"><label>WhatsApp Phone Number ID</label><input type="text" id="m-h-wid" placeholder="من إعدادات Meta Business"></div>
    <div class="form-group"><label>WhatsApp API Token</label><input type="text" id="m-h-wa-token" placeholder="توكن واتساب الخاص بالفندق"></div>
    <div class="form-group"><label>Telegram Bot Token</label><input type="text" id="m-h-tg-token" placeholder="توكن بوت التيلجرام الخاص بالفندق"></div>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitHotel()">حفظ الفندق</button>`;
  openModal('➕ إضافة فندق جديد', body, foot);
}
function submitHotel() {
  const name = document.getElementById('m-h-name').value;
  const owner = document.getElementById('m-h-owner').value;
  const wa = document.getElementById('m-h-wa').value || GLOBAL_DATA.all_hotels_list[0]?.whatsapp_number || "966500000000";
  const wid = document.getElementById('m-h-wid').value || GLOBAL_DATA.all_hotels_list[0]?.whatsapp_phone_number_id || "1065524859976957";
  const waToken = document.getElementById('m-h-wa-token').value || null;
  const tgToken = document.getElementById('m-h-tg-token').value || null;

  if (!name || !owner) return showToast('أكمل جميع الحقول', 'error');
  closeModal();
  addHotel({ name, whatsapp_number: wa, whatsapp_phone_number_id: wid, owner_whatsapp: owner, whatsapp_api_token: waToken, telegram_bot_token: tgToken });
}
async function addHotel(data) {
  try {
    await apiFetch('/hotels', { method: 'POST', body: JSON.stringify(data) });
    showToast('تم حفظ الفندق بنجاح'); loadHotels();
  } catch (e) { showToast('فشل حفظ الفندق', 'error'); }
}

function showEditHotelModal(id) {
  const h = GLOBAL_DATA.all_hotels.find(x => x.id === id);
  if (!h) return;
  const body = `
    <div class="form-group"><label>اسم الفندق</label><input type="text" id="e-h-name" value="${h.name}"></div>
    <div class="form-group"><label>رقم هاتف المالك</label><input type="text" id="e-h-owner" value="${h.owner_whatsapp}"></div>
    <div class="form-group"><label>رقم واتساب الفندق</label><input type="text" id="e-h-wa" value="${h.whatsapp_number}"></div>
    <div class="form-group"><label>WhatsApp Phone Number ID</label><input type="text" id="e-h-wid" value="${h.whatsapp_phone_number_id}"></div>
    <div class="form-group"><label>WhatsApp API Token</label><input type="text" id="e-h-wa-token" value="${h.whatsapp_api_token || ''}"></div>
    <div class="form-group"><label>Telegram Bot Token</label><input type="text" id="e-h-tg-token" value="${h.telegram_bot_token || ''}"></div>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitEditHotel('${id}')">حفظ التعديلات</button>`;
  openModal('✏️ تعديل بيانات الفندق', body, foot);
}

async function submitEditHotel(id) {
  const data = {
    name: document.getElementById('e-h-name').value,
    owner_whatsapp: document.getElementById('e-h-owner').value,
    whatsapp_number: document.getElementById('e-h-wa').value,
    whatsapp_phone_number_id: document.getElementById('e-h-wid').value,
    whatsapp_api_token: document.getElementById('e-h-wa-token').value || null,
    telegram_bot_token: document.getElementById('e-h-tg-token').value || null,
  };
  if (!data.name) return showToast('اسم الفندق مطلوب', 'error');
  closeModal();
  try {
    await apiFetch(`/hotels/${id}`, { method: 'PUT', body: JSON.stringify(data) });
    showToast('تم تعديل بيانات الفندق بنجاح');
    loadHotels();
  } catch (e) { showToast('فشل التعديل', 'error'); }
}

