// ══════════════════════════════════════════════
//  AUTH
// ══════════════════════════════════════════════
async function doLogin() {
  const u = document.getElementById('inp-user').value.trim();
  const p = document.getElementById('inp-pass').value;
  const err = document.getElementById('login-error');
  const btn = document.getElementById('btn-login');

  btn.disabled = true;
  btn.textContent = 'جاري التحقق...';

  try {
      const res = await apiFetch('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ username: u, password: p })
      });

      // Save to session start
      sessionStorage.setItem('token', res.access_token);
      sessionStorage.setItem('user', JSON.stringify(res.user));
      CURRENT_USER = res.user;

      err.style.display = 'none';
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('app').style.display = 'flex';
      
      // Setup role based UI
      applyRoleUI();
      initApp();

  } catch (e) {
      let msg = '❌ حدث خطأ في الاتصال';
      try {
          const errObj = JSON.parse(e.message);
          msg = '❌ ' + (errObj.detail || 'اسم المستخدم أو كلمة المرور غير صحيحة');
      } catch (ex) {
           msg = '❌ اسم المستخدم أو كلمة المرور غير صحيحة';
      }
      err.textContent = msg;
      err.style.display = 'block';
  } finally {
      btn.disabled = false;
      btn.textContent = 'دخول ←';
  }
}

function doLogout() {
  sessionStorage.removeItem('token');
  sessionStorage.removeItem('user');
  location.reload();
}

document.getElementById('inp-pass').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
document.getElementById('inp-user').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });

function applyRoleUI() {
    if (!CURRENT_USER) return;
    const role = CURRENT_USER.role;
    
    // Add user info to sidebar
    const hotelNameEl = document.querySelector('.hotel-name');
    if (hotelNameEl) {
        hotelNameEl.textContent = CURRENT_USER.full_name;
    }
    const hotelSubEl = document.querySelector('.hotel-sub');
    if (hotelSubEl) {
        let roleName = role === 'admin' ? 'مدير' : role === 'supervisor' ? 'مشرف' : 'موظف';
        hotelSubEl.innerHTML = `<span style="display:inline-block;padding:2px 6px;border-radius:4px;background:var(--primary);color:#000;font-size:10px">${roleName}</span>`;
    }

    // Hide navigation items based on role
    const items = document.querySelectorAll('.nav-item');
    items.forEach(item => {
        const rolesAttr = item.getAttribute('data-roles');
        if (rolesAttr) {
            const allowed = rolesAttr.split(',');
            if (!allowed.includes(role)) {
                item.style.display = 'none';
            }
        }
    });
}

// Auto-login if session exists
const savedUser = sessionStorage.getItem('user');
const savedToken = sessionStorage.getItem('token');
if (savedToken && savedUser) {
  try {
      CURRENT_USER = JSON.parse(savedUser);
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('app').style.display = 'flex';
      applyRoleUI();
      initApp();
  } catch(e) {
      doLogout();
  }
}
