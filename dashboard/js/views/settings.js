// ══════════════════════════════════════════════
//  PAGE: SETTINGS
// ══════════════════════════════════════════════

async function loadSettings() {
  const u = CURRENT_USER;
  if (!u) return;

  const roleMap = { admin: '🏨 مدير عام', supervisor: '👔 مشرف', employee: '👤 موظف' };
  const roleName = roleMap[u.role] || u.role;

  // Find hotel name
  let hotelName = '—';
  if (u.hotel_id && GLOBAL_DATA.all_hotels_list) {
    const h = GLOBAL_DATA.all_hotels_list.find(x => x.id === u.hotel_id);
    if (h) hotelName = h.name;
  }

  document.getElementById('content').innerHTML = `
    <div class="settings-grid fade-in">
      
      <!-- ═══ Profile Card ═══ -->
      <div class="settings-card settings-profile-card">
        <div class="settings-card-header">
          <div class="settings-icon-circle" style="background: linear-gradient(135deg, #6366f1, #8b5cf6);">
            <span style="font-size:28px">👤</span>
          </div>
          <div>
            <h3>الملف الشخصي</h3>
            <p class="settings-subtitle">معلوماتك الشخصية وبيانات حسابك</p>
          </div>
        </div>
        <div class="settings-card-body">
          <div class="settings-info-grid">
            <div class="settings-info-item">
              <span class="settings-label">الاسم الكامل</span>
              <span class="settings-value" id="profile-display-name">${u.full_name}</span>
            </div>
            <div class="settings-info-item">
              <span class="settings-label">اسم المستخدم</span>
              <span class="settings-value"><code style="background:rgba(99,102,241,0.15);padding:4px 12px;border-radius:6px;color:#a78bfa">${u.username}</code></span>
            </div>
            <div class="settings-info-item">
              <span class="settings-label">الصلاحية</span>
              <span class="settings-value">${roleName}</span>
            </div>
            <div class="settings-info-item">
              <span class="settings-label">الفندق الحالي</span>
              <span class="settings-value">${hotelName}</span>
            </div>
            <div class="settings-info-item">
              <span class="settings-label">تاريخ إنشاء الحساب</span>
              <span class="settings-value">${fmtDate(u.created_at)}</span>
            </div>
          </div>
          <div class="settings-divider"></div>
          <div style="display:flex;flex-direction:column;gap:12px">
            <label class="settings-label" style="margin-bottom:0">تعديل الاسم</label>
            <div style="display:flex;gap:10px">
              <input type="text" id="s-fullname" class="settings-input" value="${u.full_name}" placeholder="الاسم الكامل">
              <button class="btn btn-primary" onclick="saveProfile()" style="white-space:nowrap">
                💾 حفظ
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ Security Card ═══ -->
      <div class="settings-card">
        <div class="settings-card-header">
          <div class="settings-icon-circle" style="background: linear-gradient(135deg, #ef4444, #f97316);">
            <span style="font-size:28px">🔐</span>
          </div>
          <div>
            <h3>الأمان</h3>
            <p class="settings-subtitle">تغيير كلمة المرور والحماية</p>
          </div>
        </div>
        <div class="settings-card-body">
          <div style="display:flex;flex-direction:column;gap:16px">
            <div class="form-group" style="margin:0">
              <label class="settings-label">كلمة المرور الحالية</label>
              <div class="settings-password-wrap">
                <input type="password" id="s-cur-pass" class="settings-input" placeholder="••••••••" autocomplete="current-password">
                <button class="settings-eye-btn" onclick="togglePassVis('s-cur-pass', this)" type="button">👁️</button>
              </div>
            </div>
            <div class="form-group" style="margin:0">
              <label class="settings-label">كلمة المرور الجديدة</label>
              <div class="settings-password-wrap">
                <input type="password" id="s-new-pass" class="settings-input" placeholder="6 أحرف أو أرقام على الأقل" autocomplete="new-password">
                <button class="settings-eye-btn" onclick="togglePassVis('s-new-pass', this)" type="button">👁️</button>
              </div>
            </div>
            <div class="form-group" style="margin:0">
              <label class="settings-label">تأكيد كلمة المرور الجديدة</label>
              <div class="settings-password-wrap">
                <input type="password" id="s-conf-pass" class="settings-input" placeholder="أعد كتابة كلمة المرور الجديدة" autocomplete="new-password">
                <button class="settings-eye-btn" onclick="togglePassVis('s-conf-pass', this)" type="button">👁️</button>
              </div>
            </div>
            <div id="pass-strength" class="settings-pass-strength" style="display:none">
              <div class="settings-pass-bar"><div class="settings-pass-fill" id="pass-fill"></div></div>
              <span id="pass-strength-text"></span>
            </div>
            <button class="btn btn-danger" onclick="changePassword()" style="align-self:flex-start;margin-top:4px">
              🔑 تغيير كلمة المرور
            </button>
          </div>
        </div>
      </div>

      <!-- ═══ Preferences Card ═══ -->
      <div class="settings-card">
        <div class="settings-card-header">
          <div class="settings-icon-circle" style="background: linear-gradient(135deg, #10b981, #059669);">
            <span style="font-size:28px">🎨</span>
          </div>
          <div>
            <h3>التفضيلات</h3>
            <p class="settings-subtitle">خيارات الواجهة والإشعارات</p>
          </div>
        </div>
        <div class="settings-card-body">
          <div class="settings-pref-list">
            <div class="settings-pref-item">
              <div>
                <div class="settings-pref-title">🔊 أصوات التنبيه</div>
                <div class="settings-pref-desc">تشغيل صوت عند وصول إشعار أو تحديث</div>
              </div>
              <label class="settings-toggle">
                <input type="checkbox" id="pref-sound" onchange="savePref('sound', this.checked)">
                <span class="settings-toggle-slider"></span>
              </label>
            </div>
            <div class="settings-pref-item">
              <div>
                <div class="settings-pref-title">📊 التحديث التلقائي</div>
                <div class="settings-pref-desc">تحديث البيانات تلقائياً كل 15 ثانية</div>
              </div>
              <label class="settings-toggle">
                <input type="checkbox" id="pref-autorefresh" checked onchange="savePref('autorefresh', this.checked)">
                <span class="settings-toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ About Card ═══ -->
      <div class="settings-card settings-about-card">
        <div class="settings-card-header">
          <div class="settings-icon-circle" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
            <span style="font-size:28px">ℹ️</span>
          </div>
          <div>
            <h3>حول النظام</h3>
            <p class="settings-subtitle">معلومات عن الإصدار والنظام</p>
          </div>
        </div>
        <div class="settings-card-body">
          <div class="settings-info-grid">
            <div class="settings-info-item">
              <span class="settings-label">اسم النظام</span>
              <span class="settings-value">X — نظام إدارة الفنادق</span>
            </div>
            <div class="settings-info-item">
              <span class="settings-label">الإصدار</span>
              <span class="settings-value"><code style="background:rgba(245,158,11,0.15);padding:4px 12px;border-radius:6px;color:#fbbf24">v2.0.0</code></span>
            </div>
            <div class="settings-info-item">
              <span class="settings-label">آخر تحديث</span>
              <span class="settings-value">${new Date().toLocaleDateString('ar-SA', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  `;

  // Load saved prefs
  loadSavedPrefs();

  // Password strength meter
  document.getElementById('s-new-pass').addEventListener('input', function () {
    updatePasswordStrength(this.value);
  });
}

// ── Profile Update ──
async function saveProfile() {
  const fullName = document.getElementById('s-fullname').value.trim();
  if (!fullName || fullName.length < 2) return showToast('الاسم يجب أن يكون حرفين على الأقل', 'error');

  try {
    const res = await apiFetch('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify({ full_name: fullName })
    });
    CURRENT_USER.full_name = fullName;
    sessionStorage.setItem('user', JSON.stringify(CURRENT_USER));
    document.getElementById('profile-display-name').textContent = fullName;
    showToast('تم تحديث الاسم بنجاح ✅');
  } catch (e) { showToast('فشل تحديث الاسم', 'error'); }
}

// ── Password Change ──
async function changePassword() {
  const cur = document.getElementById('s-cur-pass').value;
  const newP = document.getElementById('s-new-pass').value;
  const conf = document.getElementById('s-conf-pass').value;

  if (!cur) return showToast('أدخل كلمة المرور الحالية', 'error');
  if (!newP || newP.length < 6) return showToast('كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل', 'error');
  if (newP !== conf) return showToast('كلمة المرور الجديدة غير متطابقة!', 'error');
  if (cur === newP) return showToast('كلمة المرور الجديدة يجب أن تختلف عن الحالية', 'error');

  try {
    await apiFetch('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: cur,
        new_password: newP
      })
    });

    // Clear fields
    document.getElementById('s-cur-pass').value = '';
    document.getElementById('s-new-pass').value = '';
    document.getElementById('s-conf-pass').value = '';
    document.getElementById('pass-strength').style.display = 'none';

    Swal.fire({
      icon: 'success',
      title: '🎉 تم تغيير كلمة المرور',
      text: 'كلمة المرور الجديدة فعّالة الآن. سيتم تسجيل خروجك لإعادة الدخول.',
      background: 'rgba(23, 23, 23, 0.85)',
      color: 'var(--text)',
      confirmButtonText: 'تسجيل الخروج',
      customClass: { popup: 'creative-swal-popup', confirmButton: 'btn btn-primary' },
      buttonsStyling: false,
      allowOutsideClick: false
    }).then(() => {
      doLogout();
    });

  } catch (e) {
    let msg = 'فشل تغيير كلمة المرور';
    try {
      const err = JSON.parse(e.message);
      if (err.detail) msg = err.detail;
    } catch (_) { }
    showToast(msg, 'error');
  }
}

// ── Password Strength ──
function updatePasswordStrength(pass) {
  const el = document.getElementById('pass-strength');
  const fill = document.getElementById('pass-fill');
  const text = document.getElementById('pass-strength-text');

  if (!pass) { el.style.display = 'none'; return; }
  el.style.display = 'flex';

  let score = 0;
  if (pass.length >= 6) score++;
  if (pass.length >= 10) score++;
  if (/[A-Z]/.test(pass)) score++;
  if (/[0-9]/.test(pass)) score++;
  if (/[^A-Za-z0-9]/.test(pass)) score++;

  const levels = [
    { label: '⚠️ ضعيفة جداً', color: '#ef4444', width: '20%' },
    { label: '🟠 ضعيفة', color: '#f97316', width: '40%' },
    { label: '🟡 متوسطة', color: '#eab308', width: '60%' },
    { label: '🟢 جيدة', color: '#22c55e', width: '80%' },
    { label: '🛡️ قوية جداً', color: '#10b981', width: '100%' }
  ];

  const lvl = levels[Math.min(score, 4)];
  fill.style.width = lvl.width;
  fill.style.background = lvl.color;
  text.textContent = lvl.label;
  text.style.color = lvl.color;
}

// ── Toggle Password Visibility ──
function togglePassVis(inputId, btn) {
  const inp = document.getElementById(inputId);
  if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '🙈'; }
  else { inp.type = 'password'; btn.textContent = '👁️'; }
}

// ── Notifications (Removed) ──
// ── Preferences Storage ──
function savePref(key, value) {
  const prefs = JSON.parse(localStorage.getItem('dashboard_prefs') || '{}');
  prefs[key] = value;
  localStorage.setItem('dashboard_prefs', JSON.stringify(prefs));
  showToast('تم حفظ التفضيل');
  // Play demo sound when enabling sound
  if (key === 'sound' && value) {
    playNotificationSound();
  }
}

function loadSavedPrefs() {
  const prefs = JSON.parse(localStorage.getItem('dashboard_prefs') || '{}');
  if (prefs.sound) document.getElementById('pref-sound').checked = true;
  if (prefs.autorefresh !== undefined) document.getElementById('pref-autorefresh').checked = prefs.autorefresh;
}
