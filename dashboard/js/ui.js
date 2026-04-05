// ══════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════
function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = (type === 'success' ? '✅ ' : '❌ ') + msg;
  t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 3000);
}
function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('ar-SA', {year:'numeric', month:'short', day:'numeric'});
}
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if(sidebar) sidebar.classList.toggle('open');
  if(overlay) overlay.classList.toggle('show');
}
function fmtMoney(n) { return (Number(n) || 0).toLocaleString('ar-SA') + ' ر.س'; }
function badgeHtml(status) { return `<span class="badge badge-${status}">${statusLabel(status)}</span>`; }
function statusLabel(s) {
  const m = {pending:'معلق', confirmed:'مؤكد', checked_in:'داخل', checked_out:'مغادر',
    cancelled:'ملغى', rejected:'مرفوض', open:'مفتوح', in_progress:'جاري', resolved:'تم الحل',
    available:'متاح', occupied:'مشغول', maintenance:'صيانة'};
  return m[s] || s;
}
function roomTypeLabel(t) {
  // t could be a UUID (from room_type_id) or a name string
  if (ROOM_TYPES[t]) return nameToAr(ROOM_TYPES[t]);
  return nameToAr(t);
}
function nameToAr(n) {
  const key = String(n || '').trim().toLowerCase().replace(/_/g, '-');
  const m = {
    'single': 'فردية',
    'double': 'دبل',
    'triple': 'ثلاثية',
    'suite': 'جناح',
    'family': 'عائلية',
    'family-suite': 'جناح عائلي',
    'one-bedroom': 'غرفة وصالة',
    'two-bedroom': 'غرفتين وصالة',
    'three-bedroom': 'ثلاث غرف وصالة',
    'standard': 'قياسية',
    'deluxe': 'ديلوكس',
  };
  return m[key] || n || '—';
}

// ══════════════════════════════════════════════
//  MODAL SYSTEM
// ══════════════════════════════════════════════
function openModal(title, bodyHtml, buttonsHtml) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHtml;
  document.getElementById('modal-footer').innerHTML = buttonsHtml;
  document.getElementById('modal-overlay').classList.add('show');
}
function closeModal() {
  document.getElementById('modal-overlay').classList.remove('show');
}

function confirmAction(title, text, confirmBtnText, actionCallback) {
  if (typeof Swal !== 'undefined') {
    Swal.fire({
      title: `<h3 style="margin:0; font-weight:700; background:linear-gradient(90deg, #ef4444, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${title || 'هل أنت متأكد؟'}</h3>`,
      text: text || 'لن تتمكن من التراجع عن هذا الإجراء!',
      icon: 'warning',
      iconColor: '#ef4444',
      showCancelButton: true,
      confirmButtonText: confirmBtnText || 'تأكيد',
      cancelButtonText: 'إلغاء',
      background: 'rgba(23, 23, 23, 0.85)',
      backdrop: 'rgba(0,0,0,0.6)',
      color: 'var(--text)',
      customClass: {
        popup: 'creative-swal-popup',
        confirmButton: 'btn btn-danger',
        cancelButton: 'btn btn-secondary',
        actions: 'creative-swal-actions'
      },
      showClass: {
        popup: `
          swal2-show
          swal2-creative-show
        `
      },
      buttonsStyling: false
    }).then((result) => {
      if (result.isConfirmed && actionCallback) actionCallback();
    });
  } else {
    // fallback if swal failed to load
    if (confirm(title + '\n' + text)) {
      if (actionCallback) actionCallback();
    }
  }
}
