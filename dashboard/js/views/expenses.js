// ══════════════════════════════════════════════
//  PAGE: EXPENSES
// ══════════════════════════════════════════════
async function loadExpenses() {
  if (!HOTEL_ID) return;
  const data = await apiFetch(`/hotels/${HOTEL_ID}/expenses?limit=100`).catch(() => ({ expenses: [] }));
  const exps = data.expenses || [];
  GLOBAL_DATA.all_exps = exps;

  document.getElementById('content').innerHTML = `
    <div class="table-header" style="background:var(--card);border-radius:12px 12px 0 0;margin-bottom:0;border:1px solid var(--border);border-bottom:none;flex-wrap:wrap;gap:10px">
      <div><h3>💸 المصروفات المسجلة (<span id="expenses-count">${exps.length}</span>)</h3></div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:flex-end">
        <input type="date" id="exp-date-start" class="search-input" style="width:130px;padding:8px;background-position:calc(100% - 10px)" onchange="filterExpenses(document.getElementById('exp-search')?.value)">
        <span style="color:var(--muted);font-size:12px">إلى</span>
        <input type="date" id="exp-date-end" class="search-input" style="width:130px;padding:8px;background-position:calc(100% - 10px)" onchange="filterExpenses(document.getElementById('exp-search')?.value)">
        <input type="text" id="exp-search" class="search-input" placeholder="🔍 بحث عن مصروف..." oninput="filterExpenses(this.value)">
        <button class="btn btn-primary btn-sm" onclick="showAddExpenseModal()">➕ سند صرف جديد</button>
      </div>
    </div>
    <div class="table-card" style="border-radius:0 0 12px 12px;border-top:none">
      <table><thead><tr><th>التاريخ</th><th>الفئة</th><th>المبلغ</th><th>البيان</th></tr></thead>
      <tbody id="expenses-tbody">${renderExpensesMarkup(exps)}</tbody></table>
    </div>
  `;
}
function filterExpenses(q) {
  const query = (q || '').toLowerCase();
  const dStart = document.getElementById('exp-date-start')?.value;
  const dEnd = document.getElementById('exp-date-end')?.value;

  const f = GLOBAL_DATA.all_exps.filter(e => {
    const textMatch = e.category.toLowerCase().includes(query) || (e.description || '').toLowerCase().includes(query) || String(e.amount).includes(query);
    let dateMatch = true;
    const eDate = e.expense_date.split('T')[0];
    if (dStart && eDate < dStart) dateMatch = false;
    if (dEnd && eDate > dEnd) dateMatch = false;
    return textMatch && dateMatch;
  });
  document.getElementById('expenses-tbody').innerHTML = renderExpensesMarkup(f);
  document.getElementById('expenses-count').textContent = f.length;
}
function renderExpensesMarkup(exps) {
  if (!exps.length) return '<tr><td colspan="4"><div class="empty-state">لا توجد مصروفات مطابقة</div></td></tr>';
  return exps.map(e => `
        <tr><td>${fmtDate(e.expense_date)}</td>
        <td><span class="badge" style="background:var(--surface);color:var(--text);border:1px solid var(--border)">${e.category}</span></td>
        <td style="color:var(--danger);font-weight:600">${fmtMoney(e.amount)}</td>
        <td>${e.description || '—'}</td></tr>`).join('');
}
function showAddExpenseModal() {
  const body = `
    <div class="form-group"><label>فئة المصروف</label><input type="text" id="m-e-cat" placeholder="كهرباء، نظافة، صيانة..."></div>
    <div class="form-group"><label>المبلغ (ريال)</label><input type="number" id="m-e-amt"></div>
    <div class="form-group"><label>البيان والتفاصيل</label><input type="text" id="m-e-desc"></div>
    <div class="form-group"><label>التاريخ</label><input type="date" id="m-e-date" value="${new Date().toISOString().split('T')[0]}"></div>`;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="submitExpense()">حفظ السند</button>`;
  openModal('➕ سند صرف جديد', body, foot);
}
function submitExpense() {
  const cat = document.getElementById('m-e-cat').value;
  const amt = document.getElementById('m-e-amt').value;
  const desc = document.getElementById('m-e-desc').value;
  const d = document.getElementById('m-e-date').value;
  if (!cat || !amt || !d) return showToast('أكمل البيانات المطلوبة', 'error');
  closeModal();
  addExpense({ category: cat, amount: parseFloat(amt), description: desc, expense_date: d });
}
async function addExpense(data) {
  try {
    await apiFetch(`/hotels/${HOTEL_ID}/expenses`, { method: 'POST', body: JSON.stringify(data) });
    showToast('تم تسجيل المصروف بنجاح'); loadExpenses();
  } catch (e) { showToast('فشل تسجيل المصروف', 'error'); }
}

