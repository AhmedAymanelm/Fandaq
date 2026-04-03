// ══════════════════════════════════════════════
//  PAGE: OVERVIEW
// ══════════════════════════════════════════════
async function loadOverview() {
  if (!HOTEL_ID) return;
  const pendCount = (GLOBAL_DATA.pending_res || []).length;
  const compCount = (GLOBAL_DATA.open_comps || []).length;

  destroyCharts();
  document.getElementById('content').innerHTML = `
    <div class="kpi-grid">
      <div class="kpi-card purple" id="kpi-income"><div class="kpi-icon">💰</div><div class="kpi-label">الدخل الشهري</div>
        <div class="kpi-value"><span class="skeleton pulse" style="display:inline-block;width:90px;height:24px"></span></div>
        <div class="kpi-sub"><span class="skeleton pulse" style="display:inline-block;width:110px;height:12px"></span></div></div>
      <div class="kpi-card blue" id="kpi-occ"><div class="kpi-icon">📊</div><div class="kpi-label">نسبة الإشغال</div>
        <div class="kpi-value"><span class="skeleton pulse" style="display:inline-block;width:60px;height:24px"></span></div>
        <div class="kpi-sub">هذا الشهر</div></div>
      <div class="kpi-card orange"><div class="kpi-icon">⏳</div><div class="kpi-label">حجوزات معلقة</div>
        <div class="kpi-value">${pendCount}</div><div class="kpi-sub">تنتظر موافقة</div></div>
      <div class="kpi-card red"><div class="kpi-icon">⚠️</div><div class="kpi-label">شكاوى مفتوحة</div>
        <div class="kpi-value">${compCount}</div><div class="kpi-sub">تحتاج متابعة</div></div>
    </div>
    <div class="charts-grid">
      <div class="chart-card"><h3>📈 توزيع الدخل بنوع الغرفة</h3>
        <div class="chart-wrap" id="wrap-income"><div class="loading-text">جاري تحميل البيانات...</div><canvas id="chart-income-type"></canvas></div></div>
      <div class="chart-card"><h3>💸 المصروفات بالفئة</h3>
        <div class="chart-wrap" id="wrap-exp"><div class="loading-text">جاري تحميل البيانات...</div><canvas id="chart-expenses"></canvas></div></div>
    </div>
    <div class="table-card">
      <div class="table-header"><h3>🕐 آخر الحجوزات</h3>
        <button class="btn btn-primary btn-sm" onclick="nav('reservations')">عرض الكل</button></div>
      <table><thead><tr><th>رقم الحجز</th><th>نوع الغرفة</th><th>الدخول</th><th>الخروج</th><th>السعر</th><th>الحالة</th></tr></thead>
      <tbody id="ov-res-tbody"><tr><td colspan="6"><div class="loading-text">جاري جلب الحجوزات...</div></td></tr></tbody></table>
    </div>`;

  const COLORS = ['#7c3aed', '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

  // Background: monthly report (KPIs + charts)
  apiFetch(`/hotels/${HOTEL_ID}/reports/monthly`).then(res => {
    const md = res?.data || {};
    const ki = document.getElementById('kpi-income');
    if (ki) ki.innerHTML = `<div class="kpi-icon">💰</div><div class="kpi-label">الدخل الشهري</div><div class="kpi-value">${fmtMoney(md.total_income)}</div><div class="kpi-sub">صافي: ${fmtMoney(md.net_profit)}</div>`;
    const ko = document.getElementById('kpi-occ');
    if (ko) ko.innerHTML = `<div class="kpi-icon">📊</div><div class="kpi-label">نسبة الإشغال</div><div class="kpi-value">${(md.occupancy_rate || 0).toFixed(1)}%</div><div class="kpi-sub">هذا الشهر</div>`;

    const ibt = md.income_by_room_type || {};
    const tL = Object.keys(ibt).map(roomTypeLabel), tV = Object.values(ibt);
    const w1 = document.getElementById('wrap-income');
    if (w1) w1.querySelector('.loading-text')?.remove();
    if (tL.length > 0) {
      charts.incomeType = new Chart(document.getElementById('chart-income-type'), {
        type: 'doughnut', data: { labels: tL, datasets: [{ data: tV, backgroundColor: COLORS, borderColor: 'transparent', borderWidth: 0, hoverOffset: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#8b949e', font: { family: 'IBM Plex Sans Arabic', size: 11 }, padding: 12 } } } }
      });
    } else { if (w1) w1.innerHTML = '<div class="empty-state"><div class="emoji">📊</div>لا توجد بيانات</div>'; }

    const ebc = md.expenses_by_category || {};
    const cL = Object.keys(ebc), cV = Object.values(ebc);
    const w2 = document.getElementById('wrap-exp');
    if (w2) w2.querySelector('.loading-text')?.remove();
    if (cL.length > 0) {
      charts.expenses = new Chart(document.getElementById('chart-expenses'), {
        type: 'bar', data: { labels: cL, datasets: [{ data: cV, backgroundColor: 'rgba(239,68,68,.6)', borderColor: 'rgba(239,68,68,1)', borderWidth: 1, borderRadius: 6 }] },
        options: {
          responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#8b949e', font: { family: 'IBM Plex Sans Arabic' } }, grid: { color: 'rgba(48,54,61,.5)' } },
            y: { ticks: { color: '#8b949e', font: { family: 'IBM Plex Sans Arabic' } }, grid: { color: 'rgba(48,54,61,.5)' } }
          }
        }
      });
    } else { if (w2) w2.innerHTML = '<div class="empty-state"><div class="emoji">💸</div>لا توجد مصروفات</div>'; }
  }).catch(() => {
    const w1 = document.getElementById('wrap-income');
    if (w1) w1.innerHTML = '<div class="empty-state">فشل تحميل التقرير</div>';
    const w2 = document.getElementById('wrap-exp');
    if (w2) w2.innerHTML = '<div class="empty-state">فشل تحميل التقرير</div>';
  });

  // Background: recent reservations
  apiFetch(`/hotels/${HOTEL_ID}/reservations?limit=6`).then(data => {
    const list = (data.reservations || []).slice(0, 6);
    const tb = document.getElementById('ov-res-tbody');
    if (!tb) return;
    tb.innerHTML = list.length ? list.map(r => `
      <tr><td style="font-family:monospace;color:var(--accent)">#${String(r.id).slice(0, 6).toUpperCase()}</td>
      <td>${roomTypeLabel(r.room_type_id || '')}</td>
      <td>${fmtDate(r.check_in)}</td><td>${fmtDate(r.check_out)}</td>
      <td>${fmtMoney(r.total_price)}</td><td>${badgeHtml(r.status)}</td></tr>`).join('')
      : '<tr><td colspan="6"><div class="empty-state"><div class="emoji">📭</div>لا توجد حجوزات</div></td></tr>';
  }).catch(() => {
    const tb = document.getElementById('ov-res-tbody');
    if (tb) tb.innerHTML = '<tr><td colspan="6"><div class="empty-state">فشل تحميل الحجوزات</div></td></tr>';
  });
}


