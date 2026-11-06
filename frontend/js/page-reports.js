import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, post } from './api-client.js';
import { escapeHtml, qs, formatDate } from './core-dom.js';
import { validateForm, formData, setBusy } from './core-forms.js';
import { toast } from './core-toast.js';

const { content } = await mountLayout('reports.html');
const params = new URLSearchParams(location.search);
loading(content);
async function render() {
  const [reports, missions] = await Promise.all([get('/api/reports'), get('/api/missions')]);
  const missionId = params.get('mission') || '';
  content.innerHTML = pageHead('تقارير الحوادث', 'تقييم آلي بمعيار معلن، مع مراجعة إدارية بشرية عند الحاجة. لا يوجد تقييم ذكاء اصطناعي غير مهيأ.') + `
    <div class="grid grid-2">
      <section class="card">
        <h2>تقرير جديد</h2>
        <form id="reportForm" novalidate>
          <div class="field"><label>العنوان</label><input class="input" name="title" data-validate="required|min:5|max:160"><div class="error"></div></div>
          <div class="field"><label>المهمة المرتبطة (اختياري)</label><select name="mission_id"><option value="">بدون مهمة</option>${(missions.items || []).map(m => `<option value="${m.id}" ${m.id === missionId ? 'selected' : ''}>${escapeHtml(m.identifier)} · ${escapeHtml(m.title)}</option>`).join('')}</select></div>
          <div class="field"><label>الملخص</label><textarea name="summary" data-validate="required|min:30|max:4000"></textarea><div class="error"></div></div>
          <div class="field"><label>الأدلة</label><textarea name="evidence" data-validate="required|min:30|max:6000"></textarea><div class="error"></div></div>
          <div class="field"><label>التحليل</label><textarea name="analysis" data-validate="required|min:50|max:6000"></textarea><div class="error"></div></div>
          <div class="field"><label>الإجراءات</label><textarea name="actions" data-validate="required|min:30|max:4000"></textarea><div class="error"></div></div>
          <button class="btn primary" type="submit">تسليم التقرير</button>
        </form>
      </section>
      <section class="card">
        <h2>تقاريري</h2>
        ${(reports.items || []).map(r => `<div class="card mb-1"><div class="flex-between"><strong>${escapeHtml(r.title)}</strong><span class="badge ${r.evaluation?.passed ? 'ok' : 'warn'}">${r.evaluation?.percentage ?? 0}%</span></div><small class="muted">${formatDate(r.created_at)} · مراجعة: ${escapeHtml(r.review?.status || 'pending')}</small><p>${escapeHtml(r.summary)}</p>${r.review?.comment ? `<div class="alert info">${escapeHtml(r.review.comment)}</div>` : ''}<details><summary>معيار التقييم</summary><ul>${(r.evaluation?.criteria || []).map(c => `<li>${escapeHtml(c.label)}: ${c.met ? 'مستوفى' : 'ناقص'}</li>`).join('')}</ul></details></div>`).join('') || '<div class="empty">لا تقارير بعد.</div>'}
      </section>
    </div>`;
  const form = qs('#reportForm');
  form.addEventListener('submit', async e => {
    e.preventDefault(); if (!validateForm(form)) return;
    const btn = form.querySelector('button'); setBusy(btn, true);
    try { const data = formData(form); const res = await post('/api/reports', data); toast(`تم التسليم · الدرجة ${res.report.evaluation.percentage}%`, 'success'); await render(); }
    catch { setBusy(btn, false); }
  });
}
try { await render(); } catch (err) { errorState(content, err.message); }
