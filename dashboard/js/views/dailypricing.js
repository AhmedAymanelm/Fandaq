// ══════════════════════════════════════════════
//  DAILY PRICING
// ══════════════════════════════════════════════


async function loadDailyPricing() {
  const content = document.getElementById('content');
  if (!HOTEL_ID) {
    content.innerHTML = '<div style="padding:20px">الرجاء اختيار فندق أولاً.</div>';
    return;
  }

  content.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
      <h3>📊 أسعار السوق (التسعير اليومي)</h3>
      <button class="btn btn-primary" onclick="showAddPricingModal()">+ إضافة تسعيرة</button>
    </div>
    
    <div class="card">
      <div class="table-responsive">
        <table class="table" style="width:100%">
          <thead>
            <tr>
              <th>تاريخ التسعيرة</th>
              <th>اسم الفندق المنافس</th>
              <th>سعر منافسنا</th>
              <th>سعر فندقنا</th>
              <th>الفرق</th>
              <th>إجراء</th>
            </tr>
          </thead>
          <tbody id="pricing-body">
            <tr><td colspan="6" style="text-align:center;">جاري التحميل...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;

  try {
    const data = await apiFetch('/hotels/' + HOTEL_ID + '/daily-pricing');
    const tbody = document.getElementById('pricing-body');
    const items = data.items || [];

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">لا يوجد تسعيرات مسجلة.</td></tr>';
      return;
    }

    tbody.innerHTML = items.map(p => {
      const diff = p.competitor_price - p.my_price;
      const diffLabel = diff > 0
        ? `<span class="badge" style="background:#10b981;color:white">أرخص من المنافس بـ ${diff}</span>`
        : diff < 0
          ? `<span class="badge" style="background:#ef4444;color:white">أغلى من المنافس بـ ${Math.abs(diff)}</span>`
          : `<span class="badge" style="background:#6b7280;color:white">نفس السعر</span>`;

      return `
      <tr>
        <td>${fmtDate(p.date)}</td>
        <td><strong>${p.competitor_hotel_name}</strong></td>
        <td style="color:#ef4444; font-weight:bold">${p.competitor_price}</td>
        <td style="color:#10b981; font-weight:bold">${p.my_price}</td>
        <td>${diffLabel}</td>
        <td>
          <button class="btn btn-sm btn-danger" onclick="deletePricing('${p.id}')">مسح</button>
        </td>
      </tr>
      `;
    }).join('');
  } catch (e) {
    document.getElementById('pricing-body').innerHTML = '<tr><td colspan="6" style="text-align:center; color:red">حدث خطأ أثناء تحميل البيانات.</td></tr>';
  }
}

function showAddPricingModal() {
  const body = `
    <div class="form-group">
      <label>اسم الفندق المنافس</label>
      <input type="text" id="dp-comp-name" class="input" placeholder="اسم الفندق...">
    </div>
    <div style="display:flex; gap:10px;">
      <div class="form-group" style="flex:1">
        <label>سعر المنافس (لليوم)</label>
        <input type="number" id="dp-comp-price" class="input" placeholder="0">
      </div>
      <div class="form-group" style="flex:1">
        <label>سعر فندقنا (لليوم)</label>
        <input type="number" id="dp-my-price" class="input" placeholder="0">
      </div>
    </div>
  `;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="savePricing()">💾 حفظ التسعيرة</button>
  `;
  openModal("➕ تسجيل تسعيرة منافس", body, foot);
}

async function savePricing() {
  const cName = document.getElementById('dp-comp-name').value;
  const cPrice = document.getElementById('dp-comp-price').value;
  const mPrice = document.getElementById('dp-my-price').value;

  if (!cName || !cPrice || !mPrice) {
    showToast('الرجاء إدخال جميع البيانات', 'error');
    return;
  }

  try {
    await apiFetch('/hotels/' + HOTEL_ID + '/daily-pricing', {
      method: 'POST',
      body: JSON.stringify({
        competitor_hotel_name: cName,
        competitor_price: parseFloat(cPrice),
        my_price: parseFloat(mPrice)
      })
    });
    showToast('تمت إضافة التسعيرة بنجاح!');
    closeModal();
    loadDailyPricing();
  } catch (e) {
    showToast('ربما توجد تسعيرة اليوم لنفس الفندق!', 'error');
  }
}

async function deletePricing(id) {
  confirmAction(
    '🗑️ مسح التسعيرة؟', 
    'هل تريد فعلاً مسح هذه التسعيرة؟ لن تتمكن من التراجع عن هذا الإجراء.', 
    'نعم، امسح', 
    async () => {
      try {
        await apiFetch('/hotels/' + HOTEL_ID + '/daily-pricing/' + id, { method: 'DELETE' });
        showToast('تم مسح التسعيرة بنجاح.');
        loadDailyPricing();
      } catch (e) {
        showToast('خطأ أثناء عملية المسح.', 'error');
      }
    }
  );
}
