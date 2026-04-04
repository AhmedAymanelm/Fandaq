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
      <table><thead><tr><th>الاسم</th><th>القنوات</th><th>رقم المالك</th><th>تاريخ الإنشاء</th><th>إجراء</th></tr></thead>
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
  return hotels.length ? hotels.map(h => {
    const channels = [];
    if (h.whatsapp_number) channels.push('<span style="background:#25d366;color:#fff;padding:2px 8px;border-radius:10px;font-size:0.8em">💬 واتساب</span>');
    if (h.telegram_bot_token) channels.push('<span style="background:#0088cc;color:#fff;padding:2px 8px;border-radius:10px;font-size:0.8em">🤖 تيليجرام</span>');
    if (!channels.length) channels.push('<span style="background:var(--danger);color:#fff;padding:2px 8px;border-radius:10px;font-size:0.8em">⚠️ بدون قناة</span>');
    return `
        <tr><td><strong>${h.name}</strong></td>
        <td>${channels.join(' ')}</td>
        <td style="direction:ltr;text-align:right">${h.owner_whatsapp}</td>
        <td>${fmtDate(h.created_at)}</td>
        <td style="display:flex;gap:4px">
          <button class="btn btn-primary btn-sm" onclick="showEditHotelModal('${h.id}')">✏️</button>
          <button class="btn btn-danger btn-sm" onclick="deleteHotel('${h.id}','${h.name}')">🗑️</button>
        </td></tr>`;
  }).join('') :
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
    
    <div style="margin:16px 0 8px;padding:8px 12px;background:rgba(255,255,255,0.05);border-radius:8px;border:1px solid var(--border)">
      <p style="margin:0 0 4px;font-size:0.85em;color:var(--text-muted)">📱 قنوات التواصل — <strong>يكفي تفعّل قناة وحدة على الأقل</strong></p>
    </div>

    <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:8px;padding:8px 12px;background:rgba(255,255,255,0.03)">
      <summary style="cursor:pointer;font-weight:600;color:var(--primary)">💬 واتساب (اختياري)</summary>
      <div class="form-group" style="margin-top:8px"><label>رقم واتساب الفندق</label><input type="text" id="m-h-wa" placeholder="مثال: 966500000000"></div>
      <div class="form-group"><label>WhatsApp Phone Number ID</label><input type="text" id="m-h-wid" placeholder="من إعدادات Meta Business"></div>
      <div class="form-group"><label>WhatsApp API Token</label><input type="text" id="m-h-wa-token" placeholder="توكن واتساب الخاص بالفندق"></div>
    </details>

    <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:8px;padding:8px 12px;background:rgba(255,255,255,0.03)">
      <summary style="cursor:pointer;font-weight:600;color:var(--primary)">🤖 تيليجرام (اختياري)</summary>
      <div class="form-group" style="margin-top:8px"><label>Telegram Bot Token</label><input type="text" id="m-h-tg-token" placeholder="توكن بوت التيلجرام الخاص بالفندق"></div>
    </details>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitHotel()">حفظ الفندق</button>`;
  openModal('➕ إضافة فندق جديد', body, foot);
}
function submitHotel() {
  const name = document.getElementById('m-h-name').value.trim();
  const owner = document.getElementById('m-h-owner').value.trim();
  const wa = document.getElementById('m-h-wa').value.trim() || null;
  const wid = document.getElementById('m-h-wid').value.trim() || null;
  const waToken = document.getElementById('m-h-wa-token').value.trim() || null;
  const tgToken = document.getElementById('m-h-tg-token').value.trim() || null;

  if (!name || !owner) return showToast('الاسم ورقم المالك مطلوبين', 'error');
  if (!wa && !wid && !tgToken) return showToast('لازم تفعّل قناة واحدة على الأقل (واتساب أو تيليجرام)', 'error');
  if ((wa || wid) && (!wa || !wid)) return showToast('إذا تبي واتساب، لازم تحط الرقم + Phone Number ID', 'error');

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

    <div style="margin:16px 0 8px;padding:8px 12px;background:rgba(255,255,255,0.05);border-radius:8px;border:1px solid var(--border)">
      <p style="margin:0 0 4px;font-size:0.85em;color:var(--text-muted)">📱 قنوات التواصل — <strong>يكفي قناة وحدة على الأقل</strong></p>
    </div>

    <details ${h.whatsapp_number ? 'open' : ''} style="margin-bottom:12px;border:1px solid var(--border);border-radius:8px;padding:8px 12px;background:rgba(255,255,255,0.03)">
      <summary style="cursor:pointer;font-weight:600;color:var(--primary)">💬 واتساب (اختياري)</summary>
      <div class="form-group" style="margin-top:8px"><label>رقم واتساب الفندق</label><input type="text" id="e-h-wa" value="${h.whatsapp_number || ''}"></div>
      <div class="form-group"><label>WhatsApp Phone Number ID</label><input type="text" id="e-h-wid" value="${h.whatsapp_phone_number_id || ''}"></div>
      <div class="form-group"><label>WhatsApp API Token</label><input type="text" id="e-h-wa-token" value="${h.whatsapp_api_token || ''}"></div>
    </details>

    <details ${h.telegram_bot_token ? 'open' : ''} style="margin-bottom:12px;border:1px solid var(--border);border-radius:8px;padding:8px 12px;background:rgba(255,255,255,0.03)">
      <summary style="cursor:pointer;font-weight:600;color:var(--primary)">🤖 تيليجرام (اختياري)</summary>
      <div class="form-group" style="margin-top:8px"><label>Telegram Bot Token</label><input type="text" id="e-h-tg-token" value="${h.telegram_bot_token || ''}"></div>
    </details>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitEditHotel('${id}')">حفظ التعديلات</button>`;
  openModal('✏️ تعديل بيانات الفندق', body, foot);
}

async function submitEditHotel(id) {
  const wa = document.getElementById('e-h-wa').value.trim() || null;
  const wid = document.getElementById('e-h-wid').value.trim() || null;
  const tgToken = document.getElementById('e-h-tg-token').value.trim() || null;

  if ((wa || wid) && (!wa || !wid)) return showToast('إذا تبي واتساب، لازم تحط الرقم + Phone Number ID', 'error');

  const data = {
    name: document.getElementById('e-h-name').value.trim(),
    owner_whatsapp: document.getElementById('e-h-owner').value.trim(),
    whatsapp_number: wa,
    whatsapp_phone_number_id: wid,
    whatsapp_api_token: document.getElementById('e-h-wa-token').value.trim() || null,
    telegram_bot_token: tgToken,
  };
  if (!data.name) return showToast('اسم الفندق مطلوب', 'error');
  closeModal();
  try {
    await apiFetch(`/hotels/${id}`, { method: 'PUT', body: JSON.stringify(data) });
    showToast('تم تعديل بيانات الفندق بنجاح');
    loadHotels();
  } catch (e) { showToast('فشل التعديل', 'error'); }
}

