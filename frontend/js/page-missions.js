import { mountLayout, pageHead, loading, errorState } from './core-layout.js';
import { get, post } from './api-client.js';
import { escapeHtml, qs, qsa, formatDate } from './core-dom.js';
import { toast } from './core-toast.js';
import { setBusy } from './core-forms.js';
import { icon } from './core-icons.js';

const { content } = await mountLayout('missions.html');
const params = new URLSearchParams(location.search);
const STATE_AR = { new: 'جديدة', assigned: 'مسندة', investigating: 'قيد التحقيق', evidence_collected: 'أدلة مجموعة', under_review: 'قيد المراجعة', resolved: 'محلولة', closed: 'مغلقة' };
const PRIORITY_AR = { high: 'عالية', medium: 'متوسطة', low: 'منخفضة' };
loading(content);

async function renderList() {
  const data = await get('/api/missions');
  content.innerHTML = pageHead('مهام الشركة', 'سير عمل تحقيق مهني: استلام، تحقيق، أدلة، قرارات، تقرير، إغلاق.') + `
    <div class="table-wrap"><table><thead><tr><th>المعرّف</th><th>المهمة</th><th>الأولوية</th><th>الحالة</th><th>الدرجة</th><th></th></tr></thead><tbody>
    ${(data.items || []).map(m => `<tr><td><code>${escapeHtml(m.identifier)}</code></td><td>${escapeHtml(m.title)}</td><td><span class="badge ${m.priority === 'high' ? 'danger' : m.priority === 'medium' ? 'warn' : ''}">${PRIORITY_AR[m.priority] || m.priority}</span></td><td><span class="badge">${STATE_AR[m.state] || m.state}</span></td><td>${m.score != null ? m.score + '%' : '—'}</td><td><a class="btn small primary" href="missions.html?mission=${m.id}">فتح</a></td></tr>`).join('')}
    </tbody></table></div>`;
}

function evidenceHtml(e) {
  return `<div class="card mb-1"><div class="flex-between"><strong>${escapeHtml(e.title)}</strong><span class="badge ${e.collected ? 'ok' : ''}">${e.collected ? 'مجمع' : 'غير مجمع'}</span></div><pre>${escapeHtml(e.content)}</pre>${e.required ? '<span class="badge warn">مطلوب</span>' : ''} ${!e.collected ? `<button class="btn small" data-collect="${e.id}" type="button">جمع الدليل</button>` : ''}</div>`;
}
function commentHtml(c) {
  const status = { confirmed_evidence: 'دليل مؤكد', hypothesis: 'فرضية', unverified_assumption: 'افتراض غير مؤكد', opinion: 'رأي' }[c.status] || c.status;
  return `<div class="card mb-1"><div class="flex-between"><span class="badge info">${escapeHtml(c.teammate_id)}</span><span class="badge">${status}</span></div><p>${escapeHtml(c.text)}</p><button class="btn small ghost" data-ask="${escapeHtml(c.teammate_id)}" data-topic="${escapeHtml(c.topic || '')}" type="button">طلب مساهمة مسجلة</button></div>`;
}

async function renderMission(id) {
  const { mission } = await get(`/api/missions/${id}`);
  const sub = mission.submission || {};
  const state = sub.state || 'new';
  const decisions = sub.decisions || [];
  const actions = [];
  if (state === 'new') actions.push(`<button class="btn primary" data-action="assign" type="button">استلام المهمة</button>`);
  if (state === 'assigned') actions.push(`<button class="btn primary" data-action="transition" data-state="investigating" type="button">بدء التحقيق</button>`);
  if (state === 'investigating') actions.push(`<button class="btn primary" data-action="transition" data-state="evidence_collected" type="button">تأكيد جمع الأدلة</button>`);
  if (state === 'evidence_collected') actions.push(`<button class="btn primary" data-action="transition" data-state="under_review" type="button">إرسال للمراجعة</button>`);
  if (state === 'under_review') actions.push(`<button class="btn primary" data-action="transition" data-state="resolved" type="button">اعتماد الحل</button>`, `<button class="btn" data-action="transition" data-state="investigating" type="button">عودة للتحقيق</button>`);
  if (state === 'resolved') actions.push(`<button class="btn primary" data-action="transition" data-state="closed" type="button">إغلاق المهمة</button>`);
  content.innerHTML = pageHead(mission.title, `${mission.identifier} · ${PRIORITY_AR[mission.priority] || mission.priority} · ${STATE_AR[state] || state}`, `<a class="btn" href="missions.html">كل المهام</a>`) + `
    <div class="grid grid-2">
      <section class="card"><h2>وصف الحادث</h2><p>${escapeHtml(mission.incident_description)}</p><h3>خلفية الشركة</h3><p class="muted">${escapeHtml(mission.company_background)}</p><h3>النطاق والتفويض</h3><div class="alert info">${escapeHtml(mission.scope_authorization)}</div></section>
      <section class="card"><h2>الإجراءات</h2><div class="flex wrap">${actions.join('') || '<span class="muted">لا إجراء متاحاً في هذه الحالة.</span>'}</div><div class="divider"></div><h3>سجل الحالات</h3><ul class="timeline">${(sub.history || []).map(h => `<li>${STATE_AR[h.state] || h.state}<small class="muted"> · ${formatDate(h.at)}</small></li>`).join('') || '<li class="muted">لم تبدأ بعد.</li>'}</ul></section>
    </div>
    <section class="card mt-2"><h2>الأدلة</h2>${state === 'new' ? '<div class="empty">استلم المهمة لعرض الأدلة.</div>' : (mission.evidence || []).map(evidenceHtml).join('')}</section>
    <section class="card mt-2"><h2>الزملاء الافتراضيون</h2><div class="alert warn mb-1">هذه شخصيات محاكاة تعليمية. بعض الافتراضات ناقصة أو غير مؤكدة عمداً؛ تحقق بالدليل.</div>${state === 'new' ? '' : (mission.teammate_comments || []).map(commentHtml).join('')}</section>
    <section class="card mt-2"><h2>أسئلة التحقيق والقرارات</h2><form id="decisionForm">
      ${(mission.investigation_questions || []).map(q => {
        const saved = decisions.find(d => d.question_id === q.id);
        return `<div class="question"><div class="q-title">${escapeHtml(q.prompt)}</div>${(q.options || []).map(o => `<label class="radio"><input type="radio" name="${q.id}" value="${o.id}" ${saved?.choice_id === o.id ? 'checked' : ''}><span>${escapeHtml(o.text)}</span></label>`).join('')}<div class="field"><label>مبرر القرار</label><textarea name="just_${q.id}" placeholder="استند إلى دليل محدد">${escapeHtml(saved?.justification || '')}</textarea></div>${saved ? `<div class="feedback ${saved.correct ? 'correct' : 'incorrect'}">${saved.correct ? 'قرار صحيح' : 'يحتاج مراجعة'} · ${escapeHtml(saved.feedback || '')}</div>` : ''}</div>`;
      }).join('')}
      <button class="btn primary" type="submit" ${['investigating', 'evidence_collected', 'under_review'].includes(state) ? '' : 'disabled'}>حفظ القرارات</button>
    </form></section>
    <section class="card mt-2"><h2>النتائج والإجراءات المقترحة</h2><form id="findingsForm"><div class="field"><label>النتائج</label><textarea name="findings" data-validate="required|min:30">${escapeHtml(sub.findings?.findings || '')}</textarea><div class="error"></div></div><div class="field"><label>الإجراءات</label><textarea name="actions" data-validate="required|min:30">${escapeHtml(sub.findings?.actions || '')}</textarea><div class="error"></div></div><button class="btn" type="submit" ${['investigating', 'evidence_collected', 'under_review'].includes(state) ? '' : 'disabled'}>حفظ النتائج</button></form></section>
    <section class="card mt-2"><h2>التقرير والإغلاق</h2><p class="muted">أرفق تقريراً من صفحة التقارير بهذه المهمة قبل الإغلاق.</p>${sub.report_id ? `<span class="badge ok">تقرير مرفق: ${escapeHtml(sub.report_id)}</span>` : '<span class="badge warn">لا تقرير مرفق</span>'} <a class="btn small" href="reports.html?mission=${id}">كتابة تقرير</a>${sub.evaluation ? `<div class="alert ${sub.evaluation.passed ? 'success' : 'warn'} mt-1">درجة المهمة: ${sub.evaluation.percentage}%</div>` : ''}</section>`;

  qsa('[data-action]').forEach(btn => btn.addEventListener('click', async () => {
    setBusy(btn, true);
    try {
      if (btn.dataset.action === 'assign') await post(`/api/missions/${id}/assign`, {});
      else await post(`/api/missions/${id}/transition`, { state: btn.dataset.state });
      toast('تم تحديث الحالة', 'success'); await renderMission(id);
    } catch { setBusy(btn, false); }
  }));
  qsa('[data-collect]').forEach(btn => btn.addEventListener('click', async () => {
    setBusy(btn, true);
    try { await post(`/api/missions/${id}/evidence`, { evidence_id: btn.dataset.collect }); toast('تم جمع الدليل', 'success'); await renderMission(id); }
    catch { setBusy(btn, false); }
  }));
  qsa('[data-ask]').forEach(btn => btn.addEventListener('click', async () => {
    setBusy(btn, true);
    try { await post(`/api/missions/${id}/ask`, { teammate_id: btn.dataset.ask, topic: btn.dataset.topic }); toast('سُجلت مساهمة الزميل', 'success'); await renderMission(id); }
    catch { setBusy(btn, false); }
  }));
  const decisionForm = qs('#decisionForm');
  decisionForm.addEventListener('submit', async e => {
    e.preventDefault(); const btn = decisionForm.querySelector('button[type=submit]'); setBusy(btn, true);
    try {
      for (const q of mission.investigation_questions || []) {
        const choice = qs(`input[name="${q.id}"]:checked`, decisionForm)?.value;
        const justification = qs(`[name="just_${q.id}"]`, decisionForm)?.value || '';
        if (!choice) { toast('اختر إجابة لكل سؤال', 'error'); setBusy(btn, false); return; }
        if (justification.trim().length < 15) { toast('المبرر قصير جداً؛ استند إلى دليل', 'error'); setBusy(btn, false); return; }
        await post(`/api/missions/${id}/decisions`, { question_id: q.id, choice_id: choice, justification });
      }
      toast('تم حفظ القرارات', 'success'); await renderMission(id);
    } catch { setBusy(btn, false); }
  });
  const findingsForm = qs('#findingsForm');
  findingsForm.addEventListener('submit', async e => {
    e.preventDefault(); const btn = findingsForm.querySelector('button[type=submit]'); setBusy(btn, true);
    try {
      const findings = qs('[name=findings]', findingsForm).value, actions = qs('[name=actions]', findingsForm).value;
      if (findings.trim().length < 30 || actions.trim().length < 30) { toast('النص قصير جداً', 'error'); setBusy(btn, false); return; }
      await post(`/api/missions/${id}/findings`, { findings, actions }); toast('تم حفظ النتائج', 'success'); await renderMission(id);
    } catch { setBusy(btn, false); }
  });
}

try { if (params.get('mission')) await renderMission(params.get('mission')); else await renderList(); }
catch (err) { errorState(content, err.message || 'تعذر تحميل المهام'); }
