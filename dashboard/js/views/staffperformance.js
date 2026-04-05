// ══════════════════════════════════════════════
//  PAGE: STAFF PERFORMANCE
// ══════════════════════════════════════════════
let staffPerfDays = 30;

async function loadStaffPerformance() {
  if (!HOTEL_ID) return;

  document.getElementById('content').innerHTML = '<div class="loading"><div class="spinner"></div> جاري تحميل تقييم الموظفين...</div>';

  const data = await apiFetch(`/hotels/${HOTEL_ID}/reports/staff-performance?days=${staffPerfDays}`)
    .catch(() => ({ summary: null, leaderboard: [] }));

  const summary = data.summary || {
    total_staff: 0,
    active_staff: 0,
    total_complaints_resolved: 0,
    total_reservations_approved: 0,
    total_requests_completed: 0,
    avg_response_hours: 0,
    avg_approval_hours: 0,
    first_response_sla_rate: 0,
    resolution_sla_rate: 0,
    first_response_sla_breached: 0,
    resolution_sla_breached: 0,
    sla_first_response_target_minutes: 15,
    sla_resolution_target_hours: 4,
  };
  const leaderboard = data.leaderboard || [];

  document.getElementById('content').innerHTML = `
    <div class="filter-bar" style="justify-content:space-between;align-items:center;margin-bottom:16px">
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="filter-btn ${staffPerfDays === 7 ? 'active' : ''}" onclick="setStaffPerfDays(7)">آخر 7 أيام</button>
        <button class="filter-btn ${staffPerfDays === 30 ? 'active' : ''}" onclick="setStaffPerfDays(30)">آخر 30 يوم</button>
        <button class="filter-btn ${staffPerfDays === 90 ? 'active' : ''}" onclick="setStaffPerfDays(90)">آخر 90 يوم</button>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <div style="font-size:12px;color:var(--muted)">الفترة: ${data.period_start || '—'} إلى ${data.period_end || '—'}</div>
        <button class="btn btn-sm btn-success" onclick="exportStaffPerformanceExcel()">📥 تصدير Excel</button>
      </div>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card purple">
        <div class="kpi-icon">👥</div>
        <div class="kpi-label">إجمالي الموظفين</div>
        <div class="kpi-value">${summary.total_staff || 0}</div>
        <div class="kpi-sub">موظف/مشرف</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-icon">🔥</div>
        <div class="kpi-label">الموظفين النشطين</div>
        <div class="kpi-value">${summary.active_staff || 0}</div>
        <div class="kpi-sub">لهم عمليات خلال الفترة</div>
      </div>
      <div class="kpi-card blue">
        <div class="kpi-icon">✅</div>
        <div class="kpi-label">مشاكل تم حلها</div>
        <div class="kpi-value">${summary.total_complaints_resolved || 0}</div>
        <div class="kpi-sub">إجمالي الشكاوى المغلقة</div>
      </div>
      <div class="kpi-card blue">
        <div class="kpi-icon">🛎️</div>
        <div class="kpi-label">طلبات مكتملة</div>
        <div class="kpi-value">${summary.total_requests_completed || 0}</div>
        <div class="kpi-sub">طلبات خدمة تم إنجازها</div>
      </div>
      <div class="kpi-card orange">
        <div class="kpi-icon">⚡</div>
        <div class="kpi-label">متوسط زمن الحل</div>
        <div class="kpi-value">${Number(summary.avg_response_hours || 0).toFixed(1)} س</div>
        <div class="kpi-sub">كل ما قل كان أفضل</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-icon">🎯</div>
        <div class="kpi-label">التزام SLA للاستجابة</div>
        <div class="kpi-value">${Number(summary.first_response_sla_rate || 0).toFixed(1)}%</div>
        <div class="kpi-sub">هدف ${summary.sla_first_response_target_minutes || 15} دقيقة</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-icon">🧩</div>
        <div class="kpi-label">التزام SLA للحل</div>
        <div class="kpi-value">${Number(summary.resolution_sla_rate || 0).toFixed(1)}%</div>
        <div class="kpi-sub">هدف ${summary.sla_resolution_target_hours || 4} ساعات</div>
      </div>
      <div class="kpi-card blue">
        <div class="kpi-icon">🕒</div>
        <div class="kpi-label">متوسط اعتماد الحجز</div>
        <div class="kpi-value">${Number(summary.avg_approval_hours || 0).toFixed(1)} س</div>
        <div class="kpi-sub">من وقت الإنشاء حتى الاعتماد</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-icon">🚫</div>
        <div class="kpi-label">معدل الرفض</div>
        <div class="kpi-value">${Number(summary.rejection_rate || 0).toFixed(1)}%</div>
        <div class="kpi-sub">نسبة الحجوزات المرفوضة</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-icon">⏱️</div>
        <div class="kpi-label">تجاوزات SLA</div>
        <div class="kpi-value">${(summary.first_response_sla_breached || 0) + (summary.resolution_sla_breached || 0)}</div>
        <div class="kpi-sub">استجابة: ${summary.first_response_sla_breached || 0} | حل: ${summary.resolution_sla_breached || 0}</div>
      </div>
    </div>

    <div class="table-card">
      <div class="table-header">
        <div>
          <h3>لوحة تقييم الموظفين</h3>
          <span style="color:var(--muted);font-size:12px">الترتيب حسب النقاط ثم النشاط</span>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>الترتيب</th>
            <th>الموظف</th>
            <th>الدور</th>
            <th>حل الشكاوى</th>
            <th>تأكيد الحجوزات</th>
            <th>إكمال الطلبات</th>
            <th>إجمالي العمليات</th>
            <th>متوسط زمن الحل (س)</th>
            <th>متوسط اعتماد الحجز (س)</th>
            <th>التزام SLA استجابة</th>
            <th>التزام SLA حل</th>
            <th>اتجاه 6 أسابيع</th>
            <th>آخر نشاط</th>
            <th>النقاط</th>
          </tr>
        </thead>
        <tbody>
          ${renderStaffLeaderboardRows(leaderboard)}
        </tbody>
      </table>
    </div>
  `;
}

function renderStaffLeaderboardRows(rows) {
  if (!rows.length) {
    return '<tr><td colspan="13"><div class="empty-state"><div class="emoji">📭</div>لا توجد بيانات أداء في الفترة المحددة</div></td></tr>';
  }

  return rows.map((r, idx) => {
    const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : '•';
    const roleLabel = r.role === 'supervisor' ? 'مشرف' : r.role === 'employee' ? 'موظف' : r.role;
    return `
      <tr>
        <td><strong>${medal} #${r.rank}</strong></td>
        <td>
          <div style="font-weight:700">${r.full_name || '—'}</div>
          <div style="font-size:11px;color:var(--muted)">@${r.username || '—'}</div>
        </td>
        <td>${roleLabel}</td>
        <td>${r.complaints_resolved || 0}</td>
        <td>${r.reservations_approved || 0}</td>
        <td>${r.requests_completed || 0}</td>
        <td>${r.total_actions || 0}</td>
        <td>${Number(r.avg_resolution_hours || 0).toFixed(2)}</td>
        <td>${Number(r.avg_approval_hours || 0).toFixed(2)}</td>
        <td>${Number(r.first_response_sla_rate || 0).toFixed(1)}%</td>
        <td>${Number(r.resolution_sla_rate || 0).toFixed(1)}%</td>
        <td>${renderWeeklyTrend(r.weekly_trend || [])}</td>
        <td>${r.last_activity_at ? fmtDate(r.last_activity_at) : '—'}</td>
        <td><span class="badge" style="background:rgba(124,58,237,.2);color:#c4b5fd;border:1px solid rgba(124,58,237,.35)">${r.score || 0}</span></td>
      </tr>
    `;
  }).join('');
}

function setStaffPerfDays(days) {
  if (staffPerfDays === days) return;
  staffPerfDays = days;
  loadStaffPerformance();
}

function renderWeeklyTrend(points) {
  if (!points.length) return '—';
  return `<div style="display:flex;gap:4px;flex-wrap:wrap">${points.map(p => {
    const level = p.actions >= 5 ? '#10b981' : p.actions >= 2 ? '#f59e0b' : '#6b7280';
    return `<span title="${p.week_start}: ${p.actions}" style="display:inline-block;min-width:20px;padding:2px 6px;border-radius:6px;background:${level};color:#fff;font-size:10px;text-align:center">${p.actions}</span>`;
  }).join('')}</div>`;
}

function exportStaffPerformanceExcel() {
  const token = sessionStorage.getItem('token');
  fetch(`${API}/hotels/${HOTEL_ID}/reports/staff-performance/export?days=${staffPerfDays}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
    .then(res => {
      if (!res.ok) throw new Error('Network response was not ok');
      return res.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `staff_performance_${staffPerfDays}d.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    })
    .catch(() => showToast('فشل تصدير التقرير', 'error'));
}
