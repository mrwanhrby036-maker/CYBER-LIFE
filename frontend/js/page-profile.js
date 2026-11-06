import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, patch } from './api-client.js';
import { escapeHtml, formatDate, qs } from './core-dom.js';
import { validateForm, formData, setBusy } from './core-forms.js';
import { toast } from './core-toast.js';
import { cacheUser } from './auth.js';

const { content, user } = await mountLayout('profile.html');
loading(content);
try {
  const me = await get('/api/auth/me');
  const u = me.user;
  content.innerHTML = pageHead('الملف الشخصي', 'بيانات حسابك ودورك وصلاحياتك.') + `
    <div class="grid grid-2">
      <section class="card">
        <h2>بيانات الحساب</h2>
        <dl class="kv"><dt>الاسم</dt><dd>${escapeHtml(u.display_name)}</dd><dt>البريد</dt><dd>${escapeHtml(u.email)}</dd><dt>الدور</dt><dd><span class="badge ${u.role === 'admin' ? 'info' : ''}">${u.role === 'admin' ? 'مدير' : 'طالب'}</span></dd><dt>آخر دخول</dt><dd>${formatDate(u.last_login_at)}</dd><dt>الفريق</dt><dd>${u.team_id ? escapeHtml(u.team_id) : 'لم ينشأ'}</dd></dl>
      </section>
      <section class="card">
        <h2>تعديل الملف</h2>
        <form id="profileForm" novalidate>
          <div class="field"><label>الاسم الظاهر</label><input class="input" name="display_name" data-validate="required|min:2|max:80" value="${escapeHtml(u.display_name)}"><div class="error"></div></div>
          <div class="field"><label>المدرسة / الجهة</label><input class="input" name="school" data-validate="max:120" value="${escapeHtml(u.school || '')}"><div class="error"></div></div>
          <div class="field"><label>المحافظة</label><input class="input" name="governorate" data-validate="max:80" value="${escapeHtml(u.governorate || '')}"><div class="error"></div></div>
          <button class="btn primary" type="submit">حفظ التعديلات</button>
        </form>
      </section>
    </div>`;
  const form = qs('#profileForm');
  form.addEventListener('submit', async e => {
    e.preventDefault(); if (!validateForm(form)) return;
    const btn = form.querySelector('button'); setBusy(btn, true);
    try { const data = formData(form); const res = await patch('/api/auth/profile', data); cacheUser(res.user); toast('تم حفظ الملف', 'success'); }
    catch { setBusy(btn, false); }
  });
} catch (err) { errorState(content, err.message); }
