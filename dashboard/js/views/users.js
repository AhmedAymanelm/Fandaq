// ══════════════════════════════════════════════
//  USERS MANAGEMENT (ADMIN ONLY)
// ══════════════════════════════════════════════

async function loadUsers() {
  const content = document.getElementById('content');
  if (CURRENT_USER.role !== 'admin') {
      content.innerHTML = '<div class="alert alert-error">عذراً، هذه الصفحة مخصصة لمدير النظام فقط.</div>';
      return;
  }
  
  content.innerHTML = `
    <div class="card fade-in">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <h2>👥 الإدارة والموظفين</h2>
        <button class="btn btn-primary" onclick="showAddUserForm()">+ إضافة مستخدم جديد</button>
      </div>
      <div id="users-container" style="display:grid; gap:1rem;">
        <div class="loading"><div class="spinner"></div> جاري تحميل المستخدمين...</div>
      </div>
    </div>
  `;

  try {
    const res = await apiFetch(`/auth/users`);
    const users = res.users || [];
    
    let html = `
      <table class="table" style="width:100%; text-align:right;">
        <thead>
          <tr>
            <th>الاسم</th>
            <th>اسم المستخدم</th>
            <th>الإيميل</th>
            <th>الدور</th>
            <th>الفندق المربوط</th>
            <th>حالة الحساب</th>
            <th>إجراءات</th>
          </tr>
        </thead>
        <tbody>
    `;
    
    if (users.length === 0) {
      html += '<tr><td colspan="7" style="text-align:center">لا يوجد مستخدمون</td></tr>';
    } else {
      users.forEach(u => {
        let roleBadge = '';
        if (u.role === 'admin') roleBadge = '<span style="background:var(--primary);color:#000;padding:2px 8px;border-radius:12px;font-size:12px;">مدير عام</span>';
        else if (u.role === 'supervisor') roleBadge = '<span style="background:#3b82f6;color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;">مشرف</span>';
        else roleBadge = '<span style="background:#f59e0b;color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;">موظف</span>';
        
        let hotelName = 'الكل';
        if (u.hotel_id) {
             const h = GLOBAL_DATA.all_hotels_list?.find(x => x.id === u.hotel_id);
             if (h) hotelName = h.name;
        }

        html += `
          <tr>
            <td><strong>${u.full_name}</strong></td>
            <td><code>${u.username}</code></td>
            <td>${u.email || '—'}</td>
            <td>${roleBadge}</td>
            <td>${hotelName}</td>
            <td>${u.is_active ? '✅ نشط' : '❌ موقوف'}</td>
            <td>
              ${u.username === 'admin' ? '' : `
                <div style="display:flex; gap:8px;">
                  <button class="btn btn-sm" style="background:#3b82f6" onclick="editUserEmail('${u.id}', '${(u.email || '').replace(/'/g, "&#39;")}')">✉️ إيميل</button>
                  <button class="btn btn-sm" style="background:${u.is_active ? '#f59e0b' : '#10b981'}" onclick="toggleUserStatus('${u.id}')">
                    ${u.is_active ? '⏸️ إيقاف' : '▶️ تفعيل'}
                  </button>
                  <button class="btn btn-sm" style="background:#ef4444" onclick="deleteUser('${u.id}')">🗑️ حذف نهائي</button>
                </div>
              `}
            </td>
          </tr>
        `;
      });
    }
    html += `</tbody></table>`;
    document.getElementById('users-container').innerHTML = html;
  } catch (e) {
    document.getElementById('users-container').innerHTML = '<div class="alert alert-error">فشل تحميل المستخدمين</div>';
  }
}

function showAddUserForm() {
  const hotelOptions = (GLOBAL_DATA.all_hotels_list || []).map(h => `<option value="${h.id}">${h.name}</option>`).join('');
  const body = `
    <div style="display:flex;flex-direction:column;gap:1rem;">
      <div class="form-group">
        <label>الاسم الكامل</label>
        <input type="text" id="usr-name" class="input">
      </div>
      <div class="form-group">
        <label>اسم الدخول (Username)</label>
        <input type="text" id="usr-user" class="input">
      </div>
      <div class="form-group">
        <label>الإيميل (مطلوب للمدير/المشرف)</label>
        <input type="email" id="usr-email" class="input" placeholder="example@domain.com">
      </div>
      <div class="form-group">
        <label>كلمة المرور</label>
        <input type="password" id="usr-pass" class="input" placeholder="6 أحرف على الأقل">
      </div>
      <div class="form-group">
        <label>الدور (الصلاحية)</label>
        <select id="usr-role" class="input">
          <option value="employee">👤 موظف (حجوزات، غرف، شكاوى فقط)</option>
          <option value="supervisor">👔 مشرف (بدون تقارير مالية)</option>
          <option value="admin">🏨 مدير (صلاحيات كاملة)</option>
        </select>
      </div>
      <div class="form-group">
        <label>الفندق التابع له</label>
        <select id="usr-hotel" class="input">
          ${hotelOptions}
        </select>
      </div>
    </div>
  `;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="saveNewUser()">💾 إضافة</button>
  `;
  openModal('➕ إضافة مستخدم جديد', body, foot);
}

async function saveNewUser() {
  const full_name = document.getElementById('usr-name').value;
  const username = document.getElementById('usr-user').value;
  const email = document.getElementById('usr-email').value.trim();
  const password = document.getElementById('usr-pass').value;
  const role = document.getElementById('usr-role').value;
  const hotel_id = document.getElementById('usr-hotel').value;

  if (!full_name || !username || !password || !hotel_id) {
      showToast('الرجاء إدخال جميع البيانات الأساسية', 'error');
      return;
  }
  
  if (password.length < 6) {
      showToast('كلمة المرور يجب أن تكون 6 أحرف أو أرقام على الأقل', 'error');
      return;
  }

    if ((role === 'admin' || role === 'supervisor') && !email) {
      showToast('إيميل المدير/المشرف مطلوب لإرسال التقارير', 'error');
      return;
    }

  try {
      await apiFetch('/auth/register', {
          method: 'POST',
        body: JSON.stringify({ username, email: email || null, password, full_name, role, hotel_id })
      });
      showToast('تم إضافة المستخدم بنجاح');
      closeModal();
      loadUsers();
  } catch (e) {
      let msg = 'فشل إضافة المستخدم';
      try {
          const errData = JSON.parse(e.message);
          if (Array.isArray(errData.detail)) {
              msg = errData.detail[0].msg;
          } else if (errData.detail) {
              msg = errData.detail;
          }
      } catch (ex) {
          msg = e.message;
      }
      showToast('فشل: ' + msg, 'error');
  }
}

async function deleteUser(id) {
  confirmAction(
    '🚫 حذف المستخدم؟', 
    'هل تريد فعلاً حذف هذا المستخدم ومنعه من الدخول؟ النظام لا يسمح بالتراجع عن هذا الإجراء.', 
    'نعم، احذف فوراً', 
    async () => {
      try {
          await apiFetch('/auth/users/' + id, { method: 'DELETE' });
          showToast('تم حذف المستخدم نهائياً');
          loadUsers();
      } catch(e) {
          showToast('خطأ أثناء عملية الحذف', 'error');
      }
    }
  );
}

async function toggleUserStatus(id) {
  try {
      await apiFetch('/auth/users/' + id + '/toggle-status', { method: 'PATCH' });
      showToast('تم تحديث حالة المستخدم بنجاح');
      loadUsers();
  } catch(e) {
      showToast('خطأ أثناء تحديث الحالة', 'error');
  }
}

function editUserEmail(userId, currentEmail) {
  const body = `
    <div class="form-group">
      <label>إيميل المستخدم</label>
      <input type="email" id="usr-edit-email" class="input" value="${currentEmail || ''}" placeholder="example@domain.com">
      <small style="color:var(--muted)">يُستخدم هذا الإيميل في إرسال التقارير للمدير/المشرف.</small>
    </div>
  `;
  const foot = `
    <button class="btn" onclick="closeModal()">إلغاء</button>
    <button class="btn btn-primary" onclick="saveUserEmail('${userId}')">💾 حفظ الإيميل</button>
  `;
  openModal('✉️ تعديل إيميل المستخدم', body, foot);
}

async function saveUserEmail(userId) {
  const email = document.getElementById('usr-edit-email').value.trim();
  if (!email) {
    showToast('الرجاء إدخال الإيميل', 'error');
    return;
  }
  try {
    await apiFetch('/auth/users/' + userId + '/email', {
      method: 'PATCH',
      body: JSON.stringify({ email })
    });
    showToast('تم تحديث الإيميل بنجاح');
    closeModal();
    loadUsers();
  } catch (e) {
    let msg = 'فشل تحديث الإيميل';
    try {
      const err = JSON.parse(e.message);
      if (err.detail) msg = err.detail;
    } catch (_) {}
    showToast(msg, 'error');
  }
}
