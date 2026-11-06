import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, post } from './api-client.js';
import { escapeHtml, qs, formatDate } from './core-dom.js';
import { validateForm, formData, setBusy } from './core-forms.js';
import { toast } from './core-toast.js';
import { icon } from './core-icons.js';

const { content } = await mountLayout('team.html');
loading(content);
async function render() {
  const data = await get('/api/teams/mine');
  const team = data.team;
  if (!team) {
    content.innerHTML = pageHead('فريقك الدائم', 'اسم الفريق يُنشأ مرة واحدة ويبقى عبر الفصول الخمسة عشر.') + `
      <section class="card" style="max-width:560px">
        <form id="teamForm" novalidate>
          <div class="field"><label>اسم الفريق</label><input class="input" name="name" data-validate="required|min:3|max:60" placeholder="مثال: فريق أسيوط السيبراني"><div class="hint">لا يمكن تغيير الاسم بعد الإنشاء.</div><div class="error"></div></div>
          <button class="btn primary" type="submit">إنشاء الفريق</button>
        </form>
      </section>`;
    const form = qs('#teamForm');
    form.addEventListener('submit', async e => {
      e.preventDefault(); if (!validateForm(form)) return;
      const btn = form.querySelector('button'); setBusy(btn, true);
      try { await post('/api/teams', formData(form)); toast('تم إنشاء الفريق', 'success'); await render(); }
      catch { setBusy(btn, false); }
    });
    return;
  }
  const teammates = data.teammates || [];
  content.innerHTML = pageHead(team.name, 'أنت العضو الرابع. الزملاء الثلاثة شخصيات محاكاة تعليمية وليسوا وكلاء ذكاء اصطناعي.') + `
    <div class="grid grid-3">${teammates.map(t => `<article class="card"><div class="flex">${icon('team')}<h3>${escapeHtml(t.name)}</h3></div><span class="badge info">${escapeHtml(t.role)}</span><p class="mt-1">${escapeHtml(t.profile)}</p><p class="muted"><strong>أسلوب التواصل:</strong> ${escapeHtml(t.communication_style)}</p><p class="muted"><strong>المسؤولية:</strong> ${escapeHtml(t.responsibility)}</p></article>`).join('')}</div>
    <section class="card mt-3"><h2>سجل المساهمات</h2>${(team.contributions || []).length ? `<ul class="timeline">${team.contributions.slice().reverse().map(c => `<li><strong>${escapeHtml(c.teammate_id)}</strong> · <span class="badge">${escapeHtml(c.kind)}</span><p>${escapeHtml(c.text)}</p><small class="muted">${formatDate(c.created_at)} · محاكاة</small></li>`).join('')}</ul>` : '<div class="empty">ستظهر مساهمات الزملاء عند التفاعل معهم في المهام.</div>'}</section>`;
}
try { await render(); } catch (err) { errorState(content, err.message); }
